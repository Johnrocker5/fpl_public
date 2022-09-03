
import streamlit as st
import pandas as pd
import requests
import datetime
import numpy as np
import seaborn as sns

league_id = 526103

@st.cache(allow_output_mutation=True)
def get_gw_months(by):
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url).json()
    gws = response['events']
    df_gw = pd.DataFrame(gws)
    df_times = df_gw[['id', 'deadline_time_epoch']]
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    gw = []
    time = []
    month = []
    for i in df_times.index:
        gw.append(df_times['id'][i])
        ts = df_times['deadline_time_epoch'][i]
        t = datetime.datetime.fromtimestamp(ts)
        time.append(t)
        month.append(months[t.month - 1])
    df = pd.DataFrame({'Game week': gw, 'Deadline': time, 'Month of deadline': month})
    if by == 'Game weeks':
        df2 = df
    if by == 'Months':
        mnths = np.array(df['Month of deadline'].drop_duplicates())
        gws = []
        for i in mnths:
            mnth_df = df.loc[df['Month of deadline'] == i]
            gws_in_mnth = np.array(mnth_df['Game week'])
            gws.append(gws_in_mnth)
        df2 = pd.DataFrame({'Month': mnths, 'Game weeks': gws})
    return df2

@st.cache(allow_output_mutation=True)
def get_league_info():
    url = f'https://fantasy.premierleague.com/api/leagues-classic/{str(league_id)}/standings'
    res = requests.get(url).json()
    if res['standings']['has_next'] == False:
        data = pd.DataFrame(res['standings']['results'])
    elif res['standings']['has_next'] == True:
        df1 = pd.DataFrame(res['standings']['results'])
        url1 = f'https://fantasy.premierleague.com/api/leagues-classic/{str(league_id)}/standings?page_standings=2'
        res1 = requests.get(url1).json()
        df2 = pd.DataFrame(res1['standings']['results'])
        data = pd.concat([df1, df2], ignore_index=True).drop_duplicates()
    id = np.array(data['entry'])
    rank = np.array(data['rank'])
    manager = np.array(data['player_name'])
    name = np.array(data['entry_name'])
    total = np.array(data['total'])
    last_rank = np.array(data['last_rank'])
    df = pd.DataFrame({'id': id, 'Rank': rank, 'Manager': manager, 'Team name': name,
                       'Total points': total, 'Last rank': last_rank})
    return df

@st.cache(allow_output_mutation=True)
def get_months_played():
    gw_data = get_gw_months(by='Game weeks')
    now = datetime.datetime.now()
    data = gw_data.loc[gw_data['Deadline'] < now]
    months = np.array(data['Month of deadline'].drop_duplicates())
    return months

@st.cache(allow_output_mutation=True)
def get_gws_of_month_played(month):
    gw_data = get_gw_months(by='Game weeks')
    df = gw_data.loc[gw_data['Month of deadline'] == month]
    gws = np.array(df['Game week'])
    return gws

@st.cache(allow_output_mutation=True)
def chip_col(val):
    if val == 'None':
        color = 'white'
    elif val != 'None':
        color = 'yellow'
    return f'background-color: {color}'

@st.cache(allow_output_mutation=True)
def get_monthly_standings(month, gameweek, color):
    gw_data = get_gw_months(by='Game weeks')
    month_gws_df = gw_data.loc[gw_data['Month of deadline'] == month]
    now = datetime.datetime.now()
    gws_played_df = month_gws_df.loc[month_gws_df['Deadline'] < now]
    gws = np.array(gws_played_df['Game week'])
    indicator = gws <= gameweek
    gws = gws[indicator]
    manager_data = get_league_info()
    ids = np.array(manager_data['id'])
    manager = np.array(manager_data['Manager'])
    points = np.zeros(len(ids), dtype=int)
    transfers = np.zeros(len(ids), dtype=int)
    transfer_costs = np.zeros(len(ids), dtype=int)
    chips_played_df = pd.DataFrame()
    captain_points = np.zeros(len(ids), dtype=int)
    bench_points = np.zeros(len(ids), dtype=int)
    number_of_chips = []
    for i in gws:
        points_in_gw = np.array([], dtype=int)
        transfers_in_gw = np.array([], dtype=int)
        transfer_cost_in_gw = np.array([], dtype=int)
        chips_played_in_gw = []
        captain_points_in_gw = np.array([], dtype=int)
        bench_points_in_gw = np.array([], dtype=int)
        for j in ids:
            url = 'https://fantasy.premierleague.com/api/entry/' + str(j) + '/event/' + str(i) + '/picks/'
            response = requests.get(url).json()
            if response != {'detail': 'Not found.'}:
                points_in_gw = np.append(points_in_gw, response['entry_history']['points']
                                         - response['entry_history']['event_transfers_cost'])
                transfers_in_gw = np.append(transfers_in_gw, response['entry_history']['event_transfers'])
                transfer_cost_in_gw = np.append(transfer_cost_in_gw, response['entry_history']['event_transfers_cost'])
                chips_played_in_gw.append(response['active_chip'])
                bench_points_in_gw = np.append(bench_points_in_gw, response['entry_history']['points_on_bench'])
                captain_df = pd.DataFrame(response['picks'])
                captain_id = captain_df.loc[captain_df['multiplier'] > 1]\
                    ['element'][captain_df.loc[captain_df['multiplier'] > 1].index[0]]
                multiplier = captain_df.loc[captain_df['multiplier'] > 1]\
                    ['multiplier'][captain_df.loc[captain_df['multiplier'] > 1].index[0]]
                url1 = f'https://fantasy.premierleague.com/api/element-summary/{str(captain_id)}/'
                res = requests.get(url1).json()
                captain_df = pd.DataFrame(res['history'])
                captain_df = captain_df.loc[captain_df['round'] == i]
                captain_points_in_gw = np.append(captain_points_in_gw, sum(captain_df['total_points']) * multiplier)
        points = points + points_in_gw
        transfers = transfers + transfers_in_gw
        transfer_costs = transfer_costs + transfer_cost_in_gw
        captain_points = captain_points + captain_points_in_gw
        bench_points = bench_points + bench_points_in_gw
        chips_played_in_gw_df = pd.DataFrame({f'{str(i)}': chips_played_in_gw})
        chips_played_df = pd.concat([chips_played_df, chips_played_in_gw_df], axis=1)
    chips_played = []
    for k in chips_played_df.index:
        player_chips = np.array(chips_played_df[chips_played_df.index == k])[0]
        match = player_chips != None
        chips_used = player_chips[match]
        t = len(chips_used)
        number_of_chips.append(t)
        if t == 0:
            chips_played.append('None')
        if t == 1:
            chips_played.append(chips_used[0])
        if t == 2:
            chips_played.append(f'{chips_used[0]} & {chips_used[1]}')
        if t == 3:
            chips_played.append(f'{chips_used[0]}, {chips_used[1]} & {chips_used[2]}')
        if t == 4:
            chips_played.append(f'{chips_used[0]}, {chips_used[1]}, {chips_used[2]} & {chips_used[3]}')
    df = pd.DataFrame({'Manager': manager, 'Points': points, 'Transfers': transfers,
                       'Cost of transfers': transfer_costs, 'Captain points': captain_points,
                       'Bench points': bench_points, 'Number of chips': number_of_chips,
                       'Chips used': chips_played})
    df = df.sort_values(by=['Points', 'Number of chips', 'Cost of transfers', 'Bench points', 'Captain points'],
                        ignore_index=True, ascending=[False, True, False, False, False])
    df = df.drop('Number of chips', axis=1)
    if color == 'yes':
        cm = sns.color_palette('vlag', as_cmap=True)
        df = df.style.background_gradient(cmap=cm, subset=df.columns[1:6]).applymap(chip_col, subset=['Chips used'])
    return df

@st.cache(allow_output_mutation=True)
def get_overall_standings_gws(gws_back):
    manager_data = get_league_info()
    ids = np.array(manager_data['id'])
    managers = np.array(manager_data['Manager'])
    points = pd.DataFrame()
    for i in ids:
        url = f'https://fantasy.premierleague.com/api/entry/{i}/history/'
        response = requests.get(url).json()
        data = pd.DataFrame(response['current'])
        df1 = data['points'] - data['event_transfers_cost']
        points = pd.concat([points, df1], ignore_index=True, axis=1)
    points = points.transpose()
    points = points[points.columns[::-1]]
    column_names = []
    for k in range(0, len(points.columns)):
        column_names.append(f'GW{len(points.columns) - k}')
    points.columns = column_names
    points = points.astype(int)
    points.insert(0, 'Total points', points.sum(axis=1))
    points.insert(0, 'Manager', managers)
    if gws_back == 100:
        df = points
    elif gws_back != 100:
        if len(points.columns) <= gws_back + 2:
            df = points
        elif len(points.columns) > gws_back + 2:
            df = points[points.columns[0:(2 + gws_back)]]
        cm = sns.color_palette('vlag', as_cmap=True)
        df = df.style.background_gradient(cmap=cm, subset=df.columns[1:])
    return df

@st.cache(allow_output_mutation=True)
def get_chip_plays():
    manager_data = get_league_info()
    ids = np.array(manager_data['id'])
    managers = np.array(manager_data['Manager'])
    chips = []
    for i in ids:
        url = f'https://fantasy.premierleague.com/api/entry/{i}/history/'
        response = requests.get(url).json()
        player_chips = response['chips']
        if player_chips == []:
            chips.append('None')
        elif player_chips != []:
            chips.append(player_chips)
    data = pd.DataFrame({'id': ids, 'Manager': managers, 'Chips': chips})
    data = data.loc[data['Chips'] != 'None']
    id = []
    manager = []
    chip = []
    gw = []
    for i in data.index:
        new_data = pd.DataFrame(data['Chips'][i])
        for j in new_data.index:
            id.append(data['id'][i])
            manager.append(data['Manager'][i])
            chip.append(new_data['name'][j])
            gw.append(new_data['event'][j])
    df = pd.DataFrame({'id': id, 'Manager': manager, 'Chip': chip, 'Game week': gw})
    return df

@st.cache(allow_output_mutation=True)
def fetch_player_name(player_id):
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url).json()
    data = response['elements']
    df = pd.DataFrame(data)
    df = df.loc[df['id'] == player_id]
    name = df['web_name'][df.index[0]]
    return name

@st.cache(allow_output_mutation=True)
def get_triple_cap():
    data = get_chip_plays()
    data = data.loc[data['Chip'] == '3xc']
    if len(data.index) == 0:
        df = data
    elif len(data.index) > 0:
        manager = np.array(data['Manager'])
        gw = np.array(data['Game week'])
        selection = []
        points = []
        for i in data.index:
            url = 'https://fantasy.premierleague.com/api/entry/' + str(data['id'][i]) + \
                  '/event/' + str(data['Game week'][i]) + '/picks/'
            response = requests.get(url).json()
            picks = pd.DataFrame(response['picks'])
            captain_df = picks.loc[picks['multiplier'] == 3]
            captain_id = captain_df['element'][captain_df.index[0]]
            url1 = f'https://fantasy.premierleague.com/api/element-summary/{str(captain_id)}/'
            res = requests.get(url1).json()
            capt_df = pd.DataFrame(res['history'])
            capt_df = capt_df.loc[capt_df['round'] == data['Game week'][i]]
            cap_pts = sum(capt_df['total_points']) * 3
            points.append(cap_pts)
            selection.append(fetch_player_name(captain_id))
        df = pd.DataFrame({'Manager': manager, 'Captain points': points, 'Selection': selection,
                           'Game week': gw})
        df = df.sort_values(by=['Captain points'], ascending=False, ignore_index=True)
        cm = sns.color_palette('vlag', as_cmap=True)
        df = df.style.background_gradient(cmap=cm, subset=['Captain points'])
    return df

@st.cache(allow_output_mutation=True)
def get_bboosts():
    data = get_chip_plays()
    data = data.loc[data['Chip'] == 'bboost']
    if len(data.index) == 0:
        df = data
    elif len(data.index) > 0:
        manager = np.array(data['Manager'])
        gw = np.array(data['Game week'])
        points = []
        for i in data.index:
            url = f'https://fantasy.premierleague.com/api/entry/' + str(data['id'][i]) + '/history/'
            response = requests.get(url).json()
            new_data = pd.DataFrame(response['current'])
            new_data = new_data.loc[new_data['event'] == data['Game week'][i]]
            pts = new_data['points_on_bench'][new_data.index[0]]
            points.append(pts)
        df = pd.DataFrame({'Manager': manager, 'Bench points': points, 'Game week': gw})
        df = df.sort_values(by=['Bench points'], ascending=False, ignore_index=True)
        cm = sns.color_palette('vlag', as_cmap=True)
        df = df.style.background_gradient(cmap=cm, subset=['Bench points'])
    return df

@st.cache(allow_output_mutation=True)
def fetch_gw_stats(gw_id):
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url).json()
    data = response['events']
    df = pd.DataFrame(data)
    df = df[['id', 'finished', 'average_entry_score', 'highest_score', 'most_captained']]
    df = df.loc[df['id'] == gw_id]
    return df

@st.cache(allow_output_mutation=True)
def fh_col(val):
    if val == 'True':
        color = 'lime'
    elif val != 'True':
        color = 'red'
    return f'background-color: {color}'

@st.cache(allow_output_mutation=True)
def get_freehit():
    data = get_chip_plays()
    data = data.loc[data['Chip'] == 'freehit']
    if len(data.index) == 0:
        df = data
    elif len(data.index) > 0:
        manager = np.array(data['Manager'])
        gw = np.array(data['Game week'])
        half = []
        points = []
        fpl_average = []
        vml_average = []
        fpl_ind = []
        vml_ind = []
        vml_df = get_overall_standings_gws(gws_back=100)
        for i in data.index:
            url = f'https://fantasy.premierleague.com/api/entry/' + str(data['id'][i]) + '/history/'
            response = requests.get(url).json()
            new_data = pd.DataFrame(response['current'])
            new_data = new_data.loc[new_data['event'] == data['Game week'][i]]
            pts = new_data['points'][new_data.index[0]]
            points.append(pts)
            fpl_df = fetch_gw_stats(data['Game week'][i])
            fpl_average.append(fpl_df['average_entry_score'][fpl_df.index[0]])
            column = 'GW' + str(data['Game week'][i])
            vml_average.append(vml_df[column].mean())
            if pts > fpl_df['average_entry_score'][fpl_df.index[0]]:
                fpl_ind.append('True')
            elif pts <= fpl_df['average_entry_score'][fpl_df.index[0]]:
                fpl_ind.append('False')
            if pts > vml_df[column].mean():
                vml_ind.append('True')
            elif pts <= vml_df[column].mean():
                vml_ind.append('False')
        df = pd.DataFrame({'Manager': manager, ' GW points': points, 'Game week': gw,
                           'FPL average': fpl_average, 'Higher (FPL)': fpl_ind,
                           'VML average': vml_average, 'Higher (VML)': vml_ind})
        df = df.sort_values(by=['GW points'], ascending=False, ignore_index=True)
        cm = sns.color_palette('vlag', as_cmap=True)
        df = df.style.background_gradient(cmap=cm, subset=['GW points']).applymap(fh_col,
                                                                                  subset=['Higher (FPL)',
                                                                                          'Higher (VML)'])
    return df

@st.cache(allow_output_mutation=True)
def get_last_gw():
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    res = requests.get(url).json()
    df = pd.DataFrame(res['events'])
    df = df.loc[df['is_current'] == True]
    last_gw = df['id'][df.index[0]]
    return last_gw

@st.cache(allow_output_mutation=True)
def get_wildcard(season, gws=1):
    last_gw1 = 16        # The last gw that first wildcard can be played
    first_gw2 = 18       # the first gw that the second wildcard can be played
    ### Both above need to be checked for next season
    data = get_chip_plays()
    data = data.loc[data['Chip'] == 'wildcard']
    if season == 'First':
        data = data.loc[data['Game week'] <= 16]
    if season == 'Second':
        data = data.loc[data['Game week'] >= 18]
    if len(data.index) == 0:
        df = data
    elif len(data.index) > 0:
        manager = np.array(data['Manager'])
        gw = np.array(data['Game week'])
        points = []
        fpl_average = []
        vml_average = []
        fpl_ind = []
        vml_ind = []
        gws_avg = []
        vml_df = get_overall_standings_gws(gws_back=100)
        for i in data.index:
            gameweeks = min(gws, len(vml_df.columns) - 2 - data['Game week'][i] + 1)
            gws_avg.append(gameweeks)
            columns = []
            fpl_avg = np.array([], dtype=int)
            for j in range(data['Game week'][i], data['Game week'][i] + gameweeks):
                columns.append('GW' + str(j))
                fpl_df = fetch_gw_stats(j)
                fpl_avg = np.append(fpl_avg, fpl_df['average_entry_score'][fpl_df.index[0]])
            fpl_average.append((fpl_avg.mean()))
            vml_average.append(vml_df[columns].mean().mean())
            vml = vml_df.loc[vml_df['Manager'] == data['Manager'][i]]
            points.append(vml[columns].mean().mean())
        for i in range(0, len(points)):
            if points[i] > fpl_average[i]:
                fpl_ind.append('True')
            else:
                fpl_ind.append('False')
            if points[i] > vml_average[i]:
                vml_ind.append('True')
            else:
                vml_ind.append('False')
        df = pd.DataFrame({'Manager': manager, 'Game week': gw, 'GWs in avg': gws_avg, 'Avg points': points,
                           'FPL avg': fpl_average, 'Higher (FPL)': fpl_ind, 'VML avg': vml_average,
                           'Higher (VML)': vml_ind})
        df = df.sort_values(by=['Avg points'], ignore_index=True, ascending=False)
        cm = sns.color_palette('vlag', as_cmap=True)
        df = df.style.background_gradient(cmap=cm, subset=['Avg points']).applymap(fh_col,
                                                                                  subset=['Higher (FPL)',
                                                                                          'Higher (VML)'])
    return df

sa_league_id = 218

@st.cache(allow_output_mutation=True)
def get_general_info():
    manager_data = get_league_info()
    ids = np.array(manager_data['id'])
    managers = np.array(manager_data['Manager'])
    rank = np.array(manager_data['Rank'])
    points = []
    prev_rank = np.array(manager_data['Last rank'])
    rank_overall = []
    rank_sa = []
    transfers = []
    transfer_costs = []
    bench_points = []
    chips_played = []
    team_value = []
    chips_df = get_chip_plays()
    for i in ids:
        url = f'https://fantasy.premierleague.com/api/entry/{i}/history/'
        response = requests.get(url).json()
        data = pd.DataFrame(response['current'])
        points.append(sum(data['points'] - data['event_transfers_cost']))
        transfers.append(sum(data['event_transfers']))
        transfer_costs.append(sum(data['event_transfers_cost']))
        bench_points.append(sum(data['points_on_bench']))
        rank_overall.append(data['overall_rank'][max(data.index)])
        team_value.append(round(data['value'][max(data.index)] / 10, 1))
        chips_data = chips_df.loc[chips_df['id'] == i]
        t = len(chips_data.index)
        chips = []
        if t == 0:
            chips = np.array(['None'])
            chips_played.append(chips)
        if t > 0:
            for j in chips_data.index:
                chips.append(chips_data['Chip'][j])
            chips = np.array(chips)
            chips_played.append(chips)
        url1 = 'https://fantasy.premierleague.com/api/entry/' + str(i) + '/'
        res = requests.get(url1).json()
        data_sa = pd.DataFrame(res['leagues']['classic'])
        data_sa = data_sa.loc[data_sa['id'] == sa_league_id]
        if len(data_sa.index) == 0:
            rank_sa.append('NA')
        elif len(data_sa.index) > 0:
            rank_sa.append(str(data_sa['entry_rank'][data_sa.index[0]]))
    df = pd.DataFrame({'Manager': managers, 'Points': points, 'Rank': rank, "Prev. rank": prev_rank,
                       'Overall rank': rank_overall, 'Rank (SA)': rank_sa, 'Team value': team_value,
                       'Transfers': transfers, 'Cost of transfers': transfer_costs, 'Bench points': bench_points,
                       'Chips played': chips_played})
    cm = sns.color_palette('vlag', as_cmap=True)
    df = df.style.background_gradient(cmap=cm, subset=['Team value', 'Transfers', 'Cost of transfers', 'Bench points'])
    return df

@st.cache(allow_output_mutation=True)
def get_monthly_winners():
    months = get_months_played()
    first = []
    second = []
    third = []
    fourth = []
    finalised = []
    mon = []
    gws = get_gw_months(by='Game weeks')
    for i in months:
        gw_data = gws.loc[gws['Month of deadline'] == i]
        last_gw = max(gw_data['Game week'])
        first_gw = min(gw_data['Game week'])
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        res = requests.get(url).json()
        data = pd.DataFrame(res['events'])
        data = data.loc[data['finished'] == True]
        gw_finished = max(data['id'])
        if gw_finished >= first_gw:
            if gw_finished >= last_gw:
                finalised.append('Yes')
            elif gw_finished < last_gw:
                finalised.append('No')
            data = get_monthly_standings(month=i, gameweek=min(last_gw, gw_finished), color='no')
            mon.append(i)
            first.append(data['Manager'][0])
            second.append(data['Manager'][1])
            third.append(data['Manager'][2])
            fourth.append(data['Manager'][3])
    df = pd.DataFrame({'Month': mon, 'Complete?': finalised, 'First': first, 'Second': second,
                       'Third': third, 'Fourth': fourth})
    return df

@st.cache(allow_output_mutation=True)
def get_prize_winners():
    data = get_monthly_winners()
    final_data = data.loc[data['Complete?'] == "Yes"]
    pred_data = data.loc[data['Complete?'] == 'No']
    manager = []
    final = []
    prediction = []
    if len(pred_data.index) > 0:
        for i in pred_data.index:
            manager.append(pred_data['First'][i])
            manager.append(pred_data['Second'][i])
            manager.append(pred_data['Third'][i])
            manager.append(pred_data['Fourth'][i])
            prediction.append(600)
            prediction.append(200)
            prediction.append(100)
            prediction.append(100)
            final.append(0)
            final.append(0)
            final.append(0)
            final.append(0)
    if len(final_data.index) > 0:
        for i in final_data.index:
            manager.append(pred_data['First'][i])
            manager.append(pred_data['Second'][i])
            manager.append(pred_data['Third'][i])
            manager.append(pred_data['Fourth'][i])
            prediction.append(0)
            prediction.append(0)
            prediction.append(0)
            prediction.append(0)
            final.append(600)
            final.append(200)
            final.append(100)
            final.append(100)
    final = np.array(final)
    prediction = np.array(prediction)
    final = final.astype(int)
    prediction = prediction.astype(int)
    total = np.array(final) + np.array(prediction)
    total = total.astype(int)
    df = pd.DataFrame({'Manager': manager, 'Total': total, 'Finalised': final, 'Prediction': prediction})
    managers = pd.array(df["Manager"].drop_duplicates())
    fin = []
    pred = []
    tot = []
    for i in managers:
        man_df = df.loc[df['Manager'] == i]
        tot.append(sum(man_df['Total']))
        fin.append(sum(man_df['Finalised']))
        pred.append(sum(man_df['Prediction']))
    df = pd.DataFrame({'Manager': managers, 'Total': tot, 'Finalised': fin, 'Prediction': pred})
    df = df.sort_values(by=['Total'], ignore_index=True, ascending=False)
    cm = sns.color_palette('vlag', as_cmap=True)
    df = df.style.background_gradient(cmap=cm, subset=['Total'])
    return df







def app():
    st.title('Victor Moses Lawn')
    password = 'vmlfpl22/23'
    intro = st.empty()
    intro.markdown('This page is only available to Victor Moses Lawn managers')
    text_input_container = st.empty()
    vml_pass = text_input_container.text_input('Insert password below:', type='password',
                                               help='If you are in the VML league and' +
                            ' you do not have the password, ' +
                            "send an email to joshhjohnstone@gmail.com with your name, surname and cell number.")
    if vml_pass != password and vml_pass != '':
        st.markdown('Incorrect password. Please make sure you entered the password in correctly.')
    if vml_pass == password:
        text_input_container.empty()
        intro.empty()
        st.header('Monthly standings')
        months_played = get_months_played()
        months_standings = st.selectbox('Which month do you want to view standings for?', months_played)
        st.markdown(f'The table below is showing information for the month of {months_standings}:')
        gws_monthly_standings = get_gws_of_month_played(month=months_standings)
        month_gws = st.slider(f'Select which game weeks to include in the month of {months_standings}:'
                              , int(min(gws_monthly_standings)), int(max(gws_monthly_standings)),
                              int(max(gws_monthly_standings)))
        standings = get_monthly_standings(month=months_standings, gameweek=month_gws, color='yes')
        st.table(standings)
        st.header('Monthly game weeks')
        st.markdown('The table below shows all GWs and the month which they fall under based on ' +
                    'the deadline for team selection of that GW.')
        gws_or_months = st.selectbox('Do you want to view by game weeks or by month?', ['Months', 'Game weeks'])
        if gws_or_months == 'Game weeks' or gws_or_months == 'Months':
            gws_month = get_gw_months(by=gws_or_months)
            st.table(gws_month)
        st.header('Overall standings')
        overall_gws_back = st.slider('Select how many of the latest GWs you wish to include', 1, 38, 10,
                                     help='Changing GWs back will not affect the Total points column. ' +
                                     'It may only indicate who has been on a good/poor run during the' +
                                     ' time period selected.')
        st.markdown('The following table shows the current league table as well as points scored in the ' +
                    f'last {overall_gws_back} GWs:')
        overall_standings = get_overall_standings_gws(gws_back=overall_gws_back)
        st.table(overall_standings)
        st.header('General information')
        st.markdown('The table below gives general information of all managers in VML:')
        general_info = get_general_info()
        st.table(general_info)
        st.header('Chips activated')
        st.markdown('The section below gives information on the chips that have been used, as well as' +
                    ' the effectiveness of the activation of that chip. ')
        st.subheader('Triple captain')
        triple_cap_df = get_triple_cap()
        if len(triple_cap_df.index) == 0:
            st.markdown('There have been no triple captains played during this season so far.')
        elif len(triple_cap_df.index) > 0:
            st.markdown('The following table shows when different triple captain chips have been played as well' +
                        ' as the points earned from doing so:')
            st.table(triple_cap_df)
        st.subheader('Wildcard')
        season = st.selectbox('Do you want to view first or second wildcards played?', ['All',
                                                                                        'First', 'Second'])
        wildcard_df = get_wildcard(season=season)
        if len(wildcard_df.index) == 0:
            st.markdown('There have been no wildcards played during the period selected so far.')
        elif len(wildcard_df.index) > 0:
            st.markdown('The table below shows when different wild card chips have been played as well' +
                        ' as the average GW points earned during a select period of GWs after the wildcard '+
                        'was activated. It also indicates what the FPL average and VML average was for the ' +
                        'selected period of GWs after the chip was played and whether or not the manager scored ' +
                        'higher or lower than ' +
                        'these two averages.')
            gameweeks_wildcard = st.slider('Select the length of GWs to be included in the average points calculations',
                                           1, 10, 5)
            st.table(get_wildcard(season=season, gws=gameweeks_wildcard))
        st.subheader('Bench boost')
        bboost_df = get_bboosts()
        if len(bboost_df.index) == 0:
            st.markdown('There have been no bench boosts played during this season so far.')
        elif len(bboost_df.index) > 0:
            st.markdown('The following table shows when different bench boost chips have been played as well' +
                        ' as the points earned from doing so:')
            st.table(bboost_df)
        st.subheader('Free hit')
        freehit_df = get_freehit()
        if len(freehit_df.index) == 0:
            st.markdown('There have been no free hits played during this season so far.')
        elif len(freehit_df.index) > 0:
            st.markdown('The table below shows when different free hit chips have been played as well' +
                        ' as the points earned during the GW it was played. It also indicates what the '
                        'FPL average and VML ' + 'average was for the GW the chip was played and ' +
                        'whether or not the manager scored higher' + ' or lower than these two averages.')
            st.table(freehit_df)
        st.header('Winnings')
        st.subheader('Monthly winners')
        st.markdown('The table below shows the monthly prize winners for each month.')
        winners = get_monthly_winners()
        st.table(winners)
        st.subheader('Total winnings')
        st.markdown('The table below shows the total winnings of all monthly prize winners.')
        total_winnings = get_prize_winners()
        st.table(total_winnings)
