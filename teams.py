import pandas as pd
import streamlit as st
import requests
from understatapi import UnderstatClient
import datetime
import seaborn as sns
import matplotlib

understat = UnderstatClient()

#################################

@st.cache
def get_gw_deadlines():
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url).json()
    gws = response['events']
    df_gw = pd.DataFrame(gws)
    df_times = df_gw[['id', 'deadline_time_epoch']]
    gw = []
    time = []
    for i in df_times.index:
        gw.append('GW' + df_times['id'][i].astype('str'))
        ts = df_times['deadline_time_epoch'][i]
        t = datetime.datetime.fromtimestamp(ts)
        time.append(t)
    df = pd.DataFrame({'Event': gw, 'Deadline': time})
    return df

#########################################

@st.cache
def get_remaining_gws():
    data = get_gw_deadlines()
    time_now = datetime.datetime.now()
    remaining = data.loc[data['Deadline'] > time_now]
    return remaining.index

################################

@st.cache
def get_teams():
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url).json()
    teams = response['teams']
    teams_df = pd.DataFrame(teams)
    df1 = teams_df[['id', 'name', 'short_name', 'strength', 'form', 'strength_overall_home',
                    'strength_overall_away', 'strength_attack_home', 'strength_attack_away',
                    'strength_defence_home', 'strength_defence_away']]
    team_data = understat.league(league='EPL').get_team_data(season='2023')
    df2 = pd.DataFrame(team_data.values())
    xG = []
    xGHome = []
    xGAway = []
    xGA = []
    xGAHome = []
    xGAAway = []
    for i in df1.index:
        name = df1['name'][i]
        if name == 'Spurs':
            df3 = df2.loc[df2['title'] == 'Tottenham']
        if name == 'Newcastle':
            df3 = df2.loc[df2['title'] == 'Newcastle United']
        if name == 'Wolves':
            df3 = df2.loc[df2['title'] == 'Wolverhampton Wanderers']
        if name == "Nott'm Forest":
            df3 = df2.loc[df2['title'] == 'Nottingham Forest']
        if name == 'Man City':
            df3 = df2.loc[df2['title'] == 'Manchester City']
        if name == 'Man Utd':
            df3 = df2.loc[df2['title'] == 'Manchester United']
        elif name != 'Spurs' and name != 'Newcastle' and \
        name != 'Wolves' and name != "Nott'm Forest" and \
        name != 'Man City' and name != 'Man Utd':
            df3 = df2.loc[df2['title'] == name]
        df4 = pd.DataFrame(df3['history'][df3.index[0]])
        xG.append(df4['xG'].mean())
        xGA.append(df4['xGA'].mean())
        home_df = df4.loc[df4['h_a'] == 'h']
        away_df = df4.loc[df4['h_a'] == 'a']
        xGHome.append(home_df['xG'].mean())
        xGAHome.append(home_df['xGA'].mean())
        xGAway.append(away_df['xG'].mean())
        xGAAway.append(away_df['xGA'].mean())
    xdf = pd.DataFrame({'xG': xG, 'xG (H)': xGHome, 'xG (A)': xGAway,
                        'xGA': xGA, 'xGA (H)': xGAHome,
                        'xGA (A)': xGAAway})
    df = pd.concat([df1, xdf], axis=1)
    return df

###################################################

@st.cache
def fetch_fixtures():
    url = 'https://fantasy.premierleague.com/api/fixtures/'
    response = requests.get(url).json()
    df = pd.DataFrame(response)
    gameWeek = pd.array(df['event'])
    finished = pd.array(df['finished'])
    homeGoals = pd.array(df['team_h_score'])
    awayGoals = pd.array(df['team_a_score'])
    teams = get_teams()
    homeAttack = []
    homeDefence = []
    homeTeam = []
    awayTeam = []
    xGHome = []
    xGAway = []
    xGAHome = []
    xGAAway = []
    xxGHome = []
    xxGAway = []
    for i in df.index:
        home_id = df['team_h'][i]
        home_df = teams.loc[teams['id'] == home_id]
        home_team = home_df['short_name'][home_df.index[0]]
        away_id = df['team_a'][i]
        away_df = teams.loc[teams['id'] == away_id]
        away_team = away_df['short_name'][away_df.index[0]]
        home_att = home_df['strength_attack_home'][home_df.index[0]] - away_df['strength_defence_away'][away_df.index[0]]
        home_def = home_df['strength_defence_home'][home_df.index[0]] - away_df['strength_attack_away'][away_df.index[0]]
        if pd.isna(home_df['xG (H)'][home_df.index[0]]):
            home_xG = home_df['xG'][home_df.index[0]]
            home_xGA = home_df['xGA'][home_df.index[0]]
        else:
            home_xG = (home_df['xG'][home_df.index[0]] + home_df['xG (H)'][home_df.index[0]]) / 2
            home_xGA = (home_df['xGA'][home_df.index[0]] + home_df['xGA (H)'][home_df.index[0]]) / 2
        if pd.isna(away_df['xG (A)'][away_df.index[0]]):
            away_xG = away_df['xG'][away_df.index[0]]
            away_xGA = away_df['xGA'][away_df.index[0]]
        else:
            away_xG = (away_df['xG'][away_df.index[0]] + away_df['xG (A)'][away_df.index[0]]) / 2
            away_xGA = (away_df['xGA'][away_df.index[0]] + away_df['xGA (A)'][away_df.index[0]]) / 2
        xGHome.append(home_xG)
        xGAHome.append(home_xGA)
        xGAway.append(away_xG)
        xGAAway.append(away_xGA)
        xxGHome.append((home_xG + away_xGA) / 2)
        xxGAway.append((away_xG + home_xGA) / 2)
        homeAttack.append(home_att)
        homeDefence.append(home_def)
        homeTeam.append(home_team)
        awayTeam.append(away_team)
    fixtures = {'Game Week': gameWeek, 'Finished': finished, 'Home': homeTeam, 'Away': awayTeam,
                'Home Goals': homeGoals, 'Away Goals': awayGoals, 'Net Home Attack': homeAttack,
                'Home Net Defence': homeDefence, 'xG (H)': xGHome, 'xGA (H)': xGAHome,
                'xG (A)': xGAway, 'xGA (A)': xGAAway, 'Prediction (H)': xxGHome, 'Prediction (A)': xxGAway}
    df = pd.DataFrame(fixtures)
    return df

###########################################

@st.cache
def fixture_colours(str):
    data = get_teams()
    df = data[['short_name', 'strength']]
    symbol = str[0:3]
    df_symbol = df.loc[df['short_name'] == symbol]
    fdr = df_symbol['strength'][df_symbol.index[0]]
    if fdr == 5:
        color = 'red'
    if fdr == 4:
        color = 'orange'
    if fdr == 3:
        color = 'white'
    if fdr == 2:
        color = 'lime'
    if fdr == 1:
        color = 'green'
    return f'background-color: {color}'

##############################################

@st.cache(allow_output_mutation=True)
def get_fixtures(select='All', weeks=11):
    teams = get_teams()
    fixtures = fetch_fixtures()
    df = pd.DataFrame()
    for i in teams.index:
        team = teams['name'][i]
        symbol = teams['short_name'][i]
        team_home_fixtures = fixtures.loc[fixtures['Home'] == symbol]
        team_away_fixtures = fixtures.loc[fixtures['Away'] == symbol]
        all_data = pd.concat([team_home_fixtures, team_away_fixtures]).sort_values('Game Week')
        df_team = pd.DataFrame({'Name': [team], 'GW1': [None], 'GW2': [None], 'GW3': [None], 'GW4': [None],
                                'GW5': [None], 'GW6': [None], 'GW7': [None], 'GW8': [None], 'GW9': [None],
                                'GW10': [None], 'GW11': [None], 'GW12': [None], 'GW13': [None], 'GW14': [None],
                                'GW15': [None], 'GW16': [None], 'GW17': [None], 'GW18': [None], 'GW19': [None],
                                'GW20': [None], 'GW21': [None], 'GW22': [None], 'GW23': [None], 'GW24': [None],
                                'GW25': [None], 'GW26': [None], 'GW27': [None], 'GW28': [None], 'GW29': [None],
                                'GW30': [None], 'GW31': [None], 'GW32': [None], 'GW33': [None], 'GW34': [None],
                                'GW35': [None], 'GW36': [None], 'GW37': [None], 'GW38': [None]})
        for j in range(0, len(all_data.index)):
            home = all_data['Home'][all_data.index[j]]
            away = all_data['Away'][all_data.index[j]]
            if home == symbol:
                df_team[df_team.columns[j+1]][0] = away + ' (H)'
            elif home != symbol:
                df_team[df_team.columns[j+1]][0] = home + ' (A)'
        df = pd.concat([df, df_team], ignore_index=True)
    index = get_remaining_gws()
    df1 = df[df.columns[0]]
    df2 = df[df.columns[index + 1]]
    weeks = min(weeks, len(df2.columns))
    df = pd.concat([df1, df2[df2.columns[0:weeks]]], axis=1)
    if 'All' not in select:
        df = df[df['Name'].isin(select)]
    df = df.style.applymap(fixture_colours, subset=df.columns[1:])
    return df

#############################################

@st.cache(allow_output_mutation=True)
def fdr_colours(fdr):
    if fdr == 5:
        color = 'red'
    if fdr == 4:
        color = 'orange'
    if fdr == 3:
        color = 'white'
    if fdr == 2:
        color = 'lime'
    if fdr == 1:
        color = 'green'
    return f'background-color: {color}'

############################################

@st.cache(allow_output_mutation=True)
def get_fdr(select='All', weeks=11):
    teams = get_teams()
    fixtures = fetch_fixtures()
    df = pd.DataFrame()
    for i in teams.index:
        team = teams['name'][i]
        symbol = teams['short_name'][i]
        team_home_fixtures = fixtures.loc[fixtures['Home'] == symbol]
        team_away_fixtures = fixtures.loc[fixtures['Away'] == symbol]
        all_data = pd.concat([team_home_fixtures, team_away_fixtures]).sort_values('Game Week')
        df_team = pd.DataFrame({'Name': [team], 'GW1': [None], 'GW2': [None], 'GW3': [None], 'GW4': [None],
                                'GW5': [None], 'GW6': [None], 'GW7': [None], 'GW8': [None], 'GW9': [None],
                                'GW10': [None], 'GW11': [None], 'GW12': [None], 'GW13': [None], 'GW14': [None],
                                'GW15': [None], 'GW16': [None], 'GW17': [None], 'GW18': [None], 'GW19': [None],
                                'GW20': [None], 'GW21': [None], 'GW22': [None], 'GW23': [None], 'GW24': [None],
                                'GW25': [None], 'GW26': [None], 'GW27': [None], 'GW28': [None], 'GW29': [None],
                                'GW30': [None], 'GW31': [None], 'GW32': [None], 'GW33': [None], 'GW34': [None],
                                'GW35': [None], 'GW36': [None], 'GW37': [None], 'GW38': [None]})
        for j in range(0, len(all_data.index)):
            home = all_data['Home'][all_data.index[j]]
            away = all_data['Away'][all_data.index[j]]
            home_df = teams.loc[teams['short_name'] == home]
            away_df = teams.loc[teams['short_name'] == away]
            home_fdr = home_df['strength'][home_df.index[0]]
            away_fdr = away_df['strength'][away_df.index[0]]
            if home == symbol:
                df_team[df_team.columns[j+1]][0] = away_fdr
            elif home != symbol:
                df_team[df_team.columns[j+1]][0] = home_fdr
        df = pd.concat([df, df_team], ignore_index=True)
    index = get_remaining_gws()
    df1 = df[df.columns[0]]
    df2 = df[df.columns[index + 1]]
    weeks = min(weeks, len(df2.columns))
    df2 = df2[df2.columns[0:weeks]]
    df2.insert(0, 'Average', df2.mean(axis=1))
    df = pd.concat([df1, df2[df2.columns[0:weeks+1]]], axis=1)
    df = df.sort_values(by=['Average'], ignore_index=True)
    if 'All' not in select:
        df = df[df['Name'].isin(select)]
    cm = sns.color_palette('vlag', as_cmap=True)
    df = df.style.background_gradient(cmap=cm, subset=['Average']).applymap(fdr_colours, subset=df.columns[2:])
    return df

###########################################

@st.cache(allow_output_mutation=True)
def fixtures_net_attack(select='All', weeks=11):
    teams = get_teams()
    fixtures = fetch_fixtures()
    df = pd.DataFrame()
    for i in teams.index:
        team = teams['name'][i]
        symbol = teams['short_name'][i]
        team_home_fixtures = fixtures.loc[fixtures['Home'] == symbol]
        team_away_fixtures = fixtures.loc[fixtures['Away'] == symbol]
        all_data = pd.concat([team_home_fixtures, team_away_fixtures]).sort_values('Game Week')
        df_team = pd.DataFrame({'Name': [team], 'GW1': [None], 'GW2': [None], 'GW3': [None], 'GW4': [None],
                                'GW5': [None], 'GW6': [None], 'GW7': [None], 'GW8': [None], 'GW9': [None],
                                'GW10': [None], 'GW11': [None], 'GW12': [None], 'GW13': [None], 'GW14': [None],
                                'GW15': [None], 'GW16': [None], 'GW17': [None], 'GW18': [None], 'GW19': [None],
                                'GW20': [None], 'GW21': [None], 'GW22': [None], 'GW23': [None], 'GW24': [None],
                                'GW25': [None], 'GW26': [None], 'GW27': [None], 'GW28': [None], 'GW29': [None],
                                'GW30': [None], 'GW31': [None], 'GW32': [None], 'GW33': [None], 'GW34': [None],
                                'GW35': [None], 'GW36': [None], 'GW37': [None], 'GW38': [None]})
        for j in range(0, len(all_data.index)):
            home = all_data['Home'][all_data.index[j]]
            homeNetA = all_data['Net Home Attack'][all_data.index[j]]
            homeNetD = all_data['Home Net Defence'][all_data.index[j]]
            if home == symbol:
                df_team[df_team.columns[j+1]][0] = homeNetA
            elif home != symbol:
                df_team[df_team.columns[j+1]][0] = -homeNetD
        df = pd.concat([df, df_team], ignore_index=True)
    index = get_remaining_gws()
    df1 = df[df.columns[0]]
    df2 = df[df.columns[index + 1]]
    weeks = min(weeks, len(df2.columns))
    df2 = df2[df2.columns[0:weeks]]
    df2.insert(0, 'Average', df2.mean(axis=1))
    df = pd.concat([df1, df2[df2.columns[0:weeks+1]]], axis=1)
    df = df.sort_values(by=['Average'], ignore_index=True, ascending=False)
    if 'All' not in select:
        df = df[df['Name'].isin(select)]
    cm = sns.color_palette('vlag', as_cmap=True)
    df = df.style.background_gradient(cmap=cm, axis=None, subset=df.columns[1:])
    return df

########################################################

@st.cache(allow_output_mutation=True)
def fixtures_pred_attack(select='All', weeks=11):
    teams = get_teams()
    fixtures = fetch_fixtures()
    df = pd.DataFrame()
    for i in teams.index:
        team = teams['name'][i]
        symbol = teams['short_name'][i]
        team_home_fixtures = fixtures.loc[fixtures['Home'] == symbol]
        team_away_fixtures = fixtures.loc[fixtures['Away'] == symbol]
        all_data = pd.concat([team_home_fixtures, team_away_fixtures]).sort_values('Game Week')
        df_team = pd.DataFrame({'Name': [team], 'GW1': [None], 'GW2': [None], 'GW3': [None], 'GW4': [None],
                                'GW5': [None], 'GW6': [None], 'GW7': [None], 'GW8': [None], 'GW9': [None],
                                'GW10': [None], 'GW11': [None], 'GW12': [None], 'GW13': [None], 'GW14': [None],
                                'GW15': [None], 'GW16': [None], 'GW17': [None], 'GW18': [None], 'GW19': [None],
                                'GW20': [None], 'GW21': [None], 'GW22': [None], 'GW23': [None], 'GW24': [None],
                                'GW25': [None], 'GW26': [None], 'GW27': [None], 'GW28': [None], 'GW29': [None],
                                'GW30': [None], 'GW31': [None], 'GW32': [None], 'GW33': [None], 'GW34': [None],
                                'GW35': [None], 'GW36': [None], 'GW37': [None], 'GW38': [None]})
        for j in range(0, len(all_data.index)):
            home = all_data['Home'][all_data.index[j]]
            pred_home = all_data['Prediction (H)'][all_data.index[j]]
            pred_away = all_data['Prediction (A)'][all_data.index[j]]
            if home == symbol:
                df_team[df_team.columns[j+1]][0] = pred_home
            elif home != symbol:
                df_team[df_team.columns[j+1]][0] = pred_away
        df = pd.concat([df, df_team], ignore_index=True)
    index = get_remaining_gws()
    df1 = df[df.columns[0]]
    df2 = df[df.columns[index + 1]]
    weeks = min(weeks, len(df2.columns))
    df2 = df2[df2.columns[0:weeks]]
    df2.insert(0, 'Average', df2.mean(axis=1))
    df = pd.concat([df1, df2[df2.columns[0:weeks+1]]], axis=1)
    df = df.sort_values(by=['Average'], ignore_index=True, ascending=False)
    if 'All' not in select:
        df = df[df['Name'].isin(select)]
    cm = sns.color_palette('vlag', as_cmap=True)
    df = df.style.background_gradient(cmap=cm, axis=None, subset=df.columns[1:])
    return df

##########################################################

@st.cache(allow_output_mutation=True)
def fixtures_net_defence(select='All', weeks=11):
    teams = get_teams()
    fixtures = fetch_fixtures()
    df = pd.DataFrame()
    for i in teams.index:
        team = teams['name'][i]
        symbol = teams['short_name'][i]
        team_home_fixtures = fixtures.loc[fixtures['Home'] == symbol]
        team_away_fixtures = fixtures.loc[fixtures['Away'] == symbol]
        all_data = pd.concat([team_home_fixtures, team_away_fixtures]).sort_values('Game Week')
        df_team = pd.DataFrame({'Name': [team], 'GW1': [None], 'GW2': [None], 'GW3': [None], 'GW4': [None],
                                'GW5': [None], 'GW6': [None], 'GW7': [None], 'GW8': [None], 'GW9': [None],
                                'GW10': [None], 'GW11': [None], 'GW12': [None], 'GW13': [None], 'GW14': [None],
                                'GW15': [None], 'GW16': [None], 'GW17': [None], 'GW18': [None], 'GW19': [None],
                                'GW20': [None], 'GW21': [None], 'GW22': [None], 'GW23': [None], 'GW24': [None],
                                'GW25': [None], 'GW26': [None], 'GW27': [None], 'GW28': [None], 'GW29': [None],
                                'GW30': [None], 'GW31': [None], 'GW32': [None], 'GW33': [None], 'GW34': [None],
                                'GW35': [None], 'GW36': [None], 'GW37': [None], 'GW38': [None]})
        for j in range(0, len(all_data.index)):
            home = all_data['Home'][all_data.index[j]]
            homeNetA = all_data['Net Home Attack'][all_data.index[j]]
            homeNetD = all_data['Home Net Defence'][all_data.index[j]]
            if home == symbol:
                df_team[df_team.columns[j+1]][0] = homeNetD
            elif home != symbol:
                df_team[df_team.columns[j+1]][0] = -homeNetA
        df = pd.concat([df, df_team], ignore_index=True)
    index = get_remaining_gws()
    df1 = df[df.columns[0]]
    df2 = df[df.columns[index + 1]]
    weeks = min(weeks, len(df2.columns))
    df2 = df2[df2.columns[0:weeks]]
    df2.insert(0, 'Average', df2.mean(axis=1))
    df = pd.concat([df1, df2[df2.columns[0:weeks+1]]], axis=1)
    df = df.sort_values(by=['Average'], ignore_index=True, ascending=False)
    if 'All' not in select:
        df = df[df['Name'].isin(select)]
    cm = sns.color_palette('vlag', as_cmap=True)
    df = df.style.background_gradient(cmap=cm, axis=None, subset=df.columns[1:])
    return df

##########################################################

@st.cache(allow_output_mutation=True)
def fixtures_pred_defence(select='All', weeks=11):
    teams = get_teams()
    fixtures = fetch_fixtures()
    df = pd.DataFrame()
    for i in teams.index:
        team = teams['name'][i]
        symbol = teams['short_name'][i]
        team_home_fixtures = fixtures.loc[fixtures['Home'] == symbol]
        team_away_fixtures = fixtures.loc[fixtures['Away'] == symbol]
        all_data = pd.concat([team_home_fixtures, team_away_fixtures]).sort_values('Game Week')
        df_team = pd.DataFrame({'Name': [team], 'GW1': [None], 'GW2': [None], 'GW3': [None], 'GW4': [None],
                                'GW5': [None], 'GW6': [None], 'GW7': [None], 'GW8': [None], 'GW9': [None],
                                'GW10': [None], 'GW11': [None], 'GW12': [None], 'GW13': [None], 'GW14': [None],
                                'GW15': [None], 'GW16': [None], 'GW17': [None], 'GW18': [None], 'GW19': [None],
                                'GW20': [None], 'GW21': [None], 'GW22': [None], 'GW23': [None], 'GW24': [None],
                                'GW25': [None], 'GW26': [None], 'GW27': [None], 'GW28': [None], 'GW29': [None],
                                'GW30': [None], 'GW31': [None], 'GW32': [None], 'GW33': [None], 'GW34': [None],
                                'GW35': [None], 'GW36': [None], 'GW37': [None], 'GW38': [None]})
        for j in range(0, len(all_data.index)):
            home = all_data['Home'][all_data.index[j]]
            pred_home = all_data['Prediction (H)'][all_data.index[j]]
            pred_away = all_data['Prediction (A)'][all_data.index[j]]
            if home == symbol:
                df_team[df_team.columns[j+1]][0] = pred_away
            elif home != symbol:
                df_team[df_team.columns[j+1]][0] = pred_home
        df = pd.concat([df, df_team], ignore_index=True)
    index = get_remaining_gws()
    df1 = df[df.columns[0]]
    df2 = df[df.columns[index + 1]]
    weeks = min(weeks, len(df2.columns))
    df2 = df2[df2.columns[0:weeks]]
    df2.insert(0, 'Average', df2.mean(axis=1))
    df = pd.concat([df1, df2[df2.columns[0:weeks+1]]], axis=1)
    df = df.sort_values(by=['Average'], ignore_index=True)
    if 'All' not in select:
        df = df[df['Name'].isin(select)]
    cm = sns.color_palette('vlag', as_cmap=True)
    df = df.style.background_gradient(cmap=cm, axis=None, subset=df.columns[1:])
    return df

example_fdr = pd.DataFrame({'Name': ['ARS', 'TOT'], 'ATT Strength (H)': [100, 90],
                        'ATT Strength (A)': [95, 88], 'DEF Strength (H)': [105, 110],
                        'DEF Strength (A)': [108, 100]})

ex_xG1 = pd.DataFrame({'Name': ['ARS', 'TOT', 'ARS', 'TOT', 'ARS', 'TOT', 'ARS', 'TOT'],
                       'Game week': [1, 1, 2, 2, 3, 3, 4, 4],
                       'Opponent': ['CRY', 'LEI', 'MUN', 'LIV', 'WHU', 'SOU', 'BHA', 'CHE'],
                       'Home/Away': ['H', 'A', 'A', 'H', 'A', 'H', 'H', 'A'],
                       'xGoals': [1.2, 1.8, 1.1, 0.7, 2.1, 2.8, 2.5, 0.6],
                       'xGoals against': [0.9, 1.2, 1.0, 2.3, 1.2, 0.5, 0.9, 1.9]})

ex_xG2 = pd.DataFrame({'Name': ['ARS', 'TOT'], 'xG': [1.725, 1.475], 'xG (H)': [1.85, 1.75], 'xG (A)': [1.6, 2.3],
                       'xGA': [1.0, 1.475], 'xGA (H)': [0.9, 1.4], 'xGA (A)': [1.1, 1.55]})

def app():
    st.title('Team Data')
    st.markdown('Please note that the tables relating to expected goals and expected goals conceded' +
                " are based on this season's data, and may therefore, only truly serve as accurate" +
                ' indicators after there have been enough games played from which a sufficient number ' +
                'of data points can be collected.')
    st.header('Looking at the fixtures ahead')
    st.subheader('Team fixtures')
    st.markdown('The following table shows the fixtures ahead for all teams. The fixtures are colour coded ' +
                'according to the fixture difficult ratings (FDR) given by FPL. FPL gives a strength rating to all' +
                ' teams ranging from 1 to 5, with 1 being the weakest and 5 being the strongest.')
    gws_fixtures = st.slider('Select how many game weeks ahead you would like to view for team fixtures:', 1, 10, 6)
    teams_fixtures = st.multiselect('Select which teams to include:', ['All', 'Arsenal', 'Aston Villa', 'Bournemouth',
                                                                       'Brentford', 'Brighton', 'Chelsea',
                                                                       'Crystal Palace', 'Everton', 'Fulham',
                                                                       'Leicester', 'Leeds', 'Liverpool', 'Man City',
                                                                       'Man Utd', 'Newcastle', "Nott'm Forest",
                                                                       'Southhampton', 'Spurs', 'West Ham', 'Wolves'],
                                    default='All', key=1)
    fixtures = get_fixtures(select=teams_fixtures, weeks=gws_fixtures)
    st.table(fixtures)
    st.subheader('Fixture difficulty ratings')
    st.markdown('The following table shows the up coming FDRs for each team. The teams are then ranked according' +
                ' to their average FDR over the selected period.')
    gws_fdr = st.slider('Select how many game weeks ahead you would like to view for team ' +
                        'fixture difficulty ratings:', 1, 10, 6)
    teams_fdr = st.multiselect('Select which teams to include:', ['All', 'Arsenal', 'Aston Villa', 'Bournemouth',
                                                                       'Brentford', 'Brighton', 'Chelsea',
                                                                       'Crystal Palace', 'Everton', 'Fulham',
                                                                       'Leicester', 'Leeds', 'Liverpool', 'Man City',
                                                                       'Man Utd', 'Newcastle', "Nott'm Forest",
                                                                       'Southhampton', 'Spurs', 'West Ham', 'Wolves'],
                                    default='All', key=2)
    fdrs = get_fdr(select=teams_fdr, weeks=gws_fdr)
    st.table(fdrs)
    st.subheader('Attacking strength')
    st.markdown('The following table shows the net attacking strength of each team for each coming fixture ' +
                'over the selected period. FPL has given all teams both home and away attacking and ' +
                "defence strength scores. Net attacking strength for each team's fixture has been" +
                " calculated as  the team's attacking strength minus the opponents defensive strength." +
                ' The teams have then been ranked based on their average attacking strength over the' +
                ' selected period.')
    st.markdown('For example, given the following data:')
    st.table(example_fdr)
    st.markdown('The fixture ARS (H) vs TOT (A) will give:')
    st.markdown('''
    - Net attacking strength of 100 - 100 = 0 for ARS (H)
    - Net attacking strength of 88 - 105 = -17 for TOT (A)
    ''')
    gws_att_strength = st.slider('Select how many game weeks ahead you would like to view for team' +
                                 ' attacking strength:', 1, 10, 6)
    teams_att = st.multiselect('Select which teams to include:', ['All', 'Arsenal', 'Aston Villa', 'Bournemouth',
                                                                       'Brentford', 'Brighton', 'Chelsea',
                                                                       'Crystal Palace', 'Everton', 'Fulham',
                                                                       'Leicester', 'Leeds', 'Liverpool', 'Man City',
                                                                       'Man Utd', 'Newcastle', "Nott'm Forest",
                                                                       'Southhampton', 'Spurs', 'West Ham', 'Wolves'],
                                    default='All', key=3)
    att_strength = fixtures_net_attack(select=teams_att, weeks=gws_att_strength)
    st.table(att_strength)
    st.subheader('Expected goals')
    st.markdown('The following table ranks each team based on their expected goals in each of their next fixtures' +
                ' over the selected period. Expected goals as well as expected goals conceded for each team in ' +
                'each match of the season has been taken from Understat.')
    st.markdown('The following example demonstrates how expected goals has been calculated for each' +
                " team's fixtures:")
    st.table(ex_xG1)
    st.markdown('Given the table above, we arrive at the following:')
    st.table(ex_xG2)
    st.markdown('Now, assume the fixture ARS (H) vs TOT (A) is to happen in GW5, based on the above table:')
    st.markdown('''
    - ARS expected goals is set equal to (1.725 + 1.85 + 1.475 + 1.55) / 4 = 1.65
    - TOT expected goals is set equal to (1.475 + 2.3 + 1 + 0.9) / 4 = 1.41875
    ''')
    st.markdown('The above method has been used to allow for both a teams form either home or away as well as' +
                ' the oppositions defence record (both home and away).')
    gws_xG = st.slider('Select how many game weeks ahead you would like to view for team ' +
                        'expected goals scored:', 1, 10, 6)
    teams_xG = st.multiselect('Select which teams to include:', ['All', 'Arsenal', 'Aston Villa', 'Bournemouth',
                                                                       'Brentford', 'Brighton', 'Chelsea',
                                                                       'Crystal Palace', 'Everton', 'Fulham',
                                                                       'Leicester', 'Leeds', 'Liverpool', 'Man City',
                                                                       'Man Utd', 'Newcastle', "Nott'm Forest",
                                                                       'Southhampton', 'Spurs', 'West Ham', 'Wolves'],
                                    default='All', key=4)
    xG = fixtures_pred_attack(select=teams_xG, weeks=gws_xG)
    st.table(xG)
    st.subheader('Defensive strength')
    st.markdown('The table below ranks the net defensive strengths of all the teams based on the selected' +
                ' fixtures ahead. Net defensive strengths have been calculated similarly to net attacking strengths.')
    gws_def_strength = st.slider('Select how many game weeks ahead you would like to view for team ' +
                                 'defensive strength:', 1, 10, 6)
    teams_def = st.multiselect('Select which teams to include:', ['All', 'Arsenal', 'Aston Villa', 'Bournemouth',
                                                                       'Brentford', 'Brighton', 'Chelsea',
                                                                       'Crystal Palace', 'Everton', 'Fulham',
                                                                       'Leicester', 'Leeds', 'Liverpool', 'Man City',
                                                                       'Man Utd', 'Newcastle', "Nott'm Forest",
                                                                       'Southhampton', 'Spurs', 'West Ham', 'Wolves'],
                                    default='All', key=5)
    def_strength = fixtures_net_defence(select=teams_def, weeks=gws_def_strength)
    st.table(def_strength)
    st.subheader('Expected goals conceded')
    st.markdown('The table below ranks teams according to the average number of expected goals conceded' +
                'in their upcoming fixtures. Expected goals conceded has been calculated in the same way as' +
                ' expected goals for.')
    gws_xGA = st.slider('Select how many game weeks ahead you would like to view for team ' +
                        'expected goals conceded:', 1, 10, 6)
    teams_xGA = st.multiselect('Select which teams to include:', ['All', 'Arsenal', 'Aston Villa', 'Bournemouth',
                                                                       'Brentford', 'Brighton', 'Chelsea',
                                                                       'Crystal Palace', 'Everton', 'Fulham',
                                                                       'Leicester', 'Leeds', 'Liverpool', 'Man City',
                                                                       'Man Utd', 'Newcastle', "Nott'm Forest",
                                                                       'Southhampton', 'Spurs', 'West Ham', 'Wolves'],
                                    default='All', key=6)
    xGA = fixtures_pred_defence(select=teams_xGA, weeks=gws_xGA)
    st.table(xGA)





