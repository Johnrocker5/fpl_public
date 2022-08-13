import pandas as pd
import streamlit as st
import requests
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


@st.cache(allow_output_mutation=True)
def get_basic_info(id):
    url = 'https://fantasy.premierleague.com/api/entry/' + str(id) + '/'
    res = requests.get(url).json()
    manager_name = res['player_first_name'] + ' ' + res['player_last_name']
    region = res['player_region_name']
    team_name = res['name']
    total_points = res['summary_overall_points']
    overall_rank = res['summary_overall_rank']
    url2 = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url2).json()
    total_players = response['total_players']
    percentile = round((overall_rank / total_players) * 100, 2)
    df = pd.DataFrame({'Team info': ['Manager', 'Country', 'Team name', 'Total points',
                                          'Overall rank', 'Percentile'],
                  'Result for manager ID': [manager_name, region, team_name, total_points,
                                                  overall_rank, percentile]})
    df = df.astype(str)
    return df

def rank_col(val):
    if val == 1:
        color = 'gold'
    else:
        color = 'white'
    return f'background-color: {color}'

def mov_col(val):
    if val == 0:
        color = 'lime'
    if val < 0:
        color = 'red'
    else:
        color = 'white'
    return f'background-color: {color}'

def get_leagues(id):
    url = 'https://fantasy.premierleague.com/api/entry/' + str(id) + '/'
    res = requests.get(url).json()
    data = pd.DataFrame(res['leagues']['classic'])
    names = np.array(data['name'])
    prev_rank = np.array(data['entry_last_rank'])
    rank = np.array(data['entry_rank'])
    movement = prev_rank - rank
    type = []
    for i in data.index:
        if data['league_type'][i] == 's':
            type.append('Public')
        if data['league_type'][i] == 'x':
            type.append('Private')
    df = pd.DataFrame({'League name': names, 'Type': type, 'Rank': rank,
                       'Previous rank': prev_rank, 'Movement': movement})
    df = df.loc[df['Rank'] > 0]
    df = df.style.applymap(rank_col, subset=['Rank']).applymap(mov_col, subset=['Movement'])
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
def fetch_gw_stats():
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url).json()
    data = response['events']
    df = pd.DataFrame(data)
    df = df[['id', 'finished', 'average_entry_score', 'highest_score', 'most_captained']]
    df = df.loc[df['finished'] == True]
    return df

@st.cache(allow_output_mutation=True)
def fetch_my_team_gw_stats(id):
    last_gw = max(fetch_gw_stats()['id'])
    game_week = []
    points = []
    average = []
    highest = []
    total_points = []
    rank = []
    overall_rank = []
    bank = []
    value = []
    transfers = []
    transfers_cost = []
    points_on_bench = []
    captain_pts = []
    captain = []
    most_captained_pts = []
    most_cpt = []
    for i in range(1, last_gw + 1):
        url = 'https://fantasy.premierleague.com/api/entry/' + str(id) + '/event/' + str(i) + '/picks/'
        response = requests.get(url).json()
        game_week.append('GW' + str(response['entry_history']['event']))
        points.append(response['entry_history']['points'])
        total_points.append(response['entry_history']['total_points'])
        rank.append(response['entry_history']['rank'])
        overall_rank.append(response['entry_history']['overall_rank'])
        bank.append(response['entry_history']['bank'])
        value.append(response['entry_history']['value'])
        transfers.append(response['entry_history']['event_transfers'])
        transfers_cost.append(response['entry_history']['event_transfers_cost'])
        points_on_bench.append(response['entry_history']['points_on_bench'])
        df1 = pd.DataFrame(response['picks'])
        captain_id = df1.loc[df1['multiplier'] > 1]['element'][df1.loc[df1['multiplier'] > 1].index[0]]
        captain.append(fetch_player_name(player_id=captain_id))
        url1 = f'https://fantasy.premierleague.com/api/element-summary/{str(captain_id)}/'
        res = requests.get(url1).json()
        captain_df = pd.DataFrame(res['history'])
        captain_df = captain_df.loc[captain_df['round'] == i]
        captain_pts.append(sum(captain_df['total_points']))
        data = fetch_gw_stats()
        average.append(int(data['average_entry_score'][i-1]))
        highest.append(int(data['highest_score'][i-1]))
        most_captain_id = int(data['most_captained'][i-1])
        most_cpt.append(fetch_player_name(player_id=most_captain_id))
        url2 = f'https://fantasy.premierleague.com/api/element-summary/{str(most_captain_id)}/'
        res1 = requests.get(url2).json()
        mst_captain_df = pd.DataFrame(res1['history'])
        mst_captain_df = mst_captain_df.loc[mst_captain_df['round'] == i]
        most_captained_pts.append(sum(mst_captain_df['total_points']))
    df = pd.DataFrame({'Game week': game_week, 'Points': points, 'Average': average, 'Highest': highest,
                        'Total points': total_points, 'GW rank': rank, 'Overall rank': overall_rank,
                        'Bank value': bank, 'Total value': value, 'GW transfers': transfers,
                        'GW transfers cost': transfers_cost, 'Points on bench': points_on_bench,
                        'Captain points': captain_pts, 'Most captained points': most_captained_pts,
                       'Captain': captain, 'Most captained': most_cpt})
    return df

gameweek = np.arange(1, max(fetch_gw_stats()['id']) + 1)

### Team points vs average and highest

@st.cache(allow_output_mutation=True)
def get_fig1(y):
    points = np.array(fetch_my_team_gw_stats(id=y)['Points'])
    average = np.array(fetch_my_team_gw_stats(id=y)['Average'])
    highest = np.array(fetch_my_team_gw_stats(id=y)['Highest'])
    fig, ax1 = plt.subplots(figsize=(11.69, 8.27))
    ax1.plot(gameweek, points, color='b', label='Team FPL points')
    ax1.plot(gameweek, average, color='black', label='Average FPL points')
    ax1.plot(gameweek, highest, color='r', label='Highest FPL points')
    ax1.set_xlabel('Game week')
    ax1.set_ylabel('FPL points')
    ax1.legend(loc='best', frameon=True, prop={'size': 15})
    return fig


### Team rank overall and game week

@st.cache(allow_output_mutation=True)
def get_fig2(y):
    rank = np.array(fetch_my_team_gw_stats(id=y)['GW rank'])
    overall_rank = np.array(fetch_my_team_gw_stats(id=y)['Overall rank'])
    fig2, ax2 = plt.subplots(figsize=(11.69, 8.27))
    ax2.bar(gameweek, rank, color='b', label='GW rank', width=0.5)
    ax2.plot(gameweek, overall_rank, color='r', label='Overall rank')
    ax2.set_ylim(ymin=0)
    ax2.set_ylim(ymax=max(rank + 400000))
    ax2.get_yaxis().get_major_formatter().set_scientific(False)
    ax2.set_xlabel('Game week')
    ax2.set_ylabel('Rank')
    ax2.legend(loc='best', frameon=True, prop={'size': 15})
    rects = ax2.patches
    for rect in rects:
        height = rect.get_height()
        ax2.text(rect.get_x() + rect.get_width() / 2, height + 100000, height, ha='center', va='bottom', size=10)
    return fig2

### Team value

@st.cache(allow_output_mutation=True)
def get_fig3(y):
    value = np.array(fetch_my_team_gw_stats(id=y)['Total value'])
    fig3, ax3 = plt.subplots(figsize=(11.69, 8.27))
    ax3.bar(gameweek, list(map(lambda x: x/10, value)), width=0.5, color='b')
    ax3.set_ylim(ymin=min(list(map(lambda x: x/10, value))) - 0.5)
    ax3.set_ylim(ymax=max(list(map(lambda x: x/10, value))) + 0.5)
    ax3.set_xlabel('Game week')
    ax3.set_ylabel('Team value (incl. bank)')
    rects = ax3.patches
    labels = [sum(x) for x in zip(list(map(lambda x: round(x/10, 1), value)))]
    for rect, label in zip(rects, labels):
        height = rect.get_height()
        ax3.text(rect.get_x() + rect.get_width() / 2, height + 0.1, label, ha='center', va='bottom', size=10)
    return fig3
### Team transfers

@st.cache(allow_output_mutation=True)
def get_fig4(y):
    transfers = np.array(fetch_my_team_gw_stats(id=y)['GW transfers'])
    transfers_cost = np.array(fetch_my_team_gw_stats(id=y)['GW transfers cost'])
    fig4, ax4 = plt.subplots(figsize=(11.69, 8.27))
    ax44 = ax4.twinx()
    ax4.bar(gameweek, transfers, color='b', label='Number of transfers', width=0.5)
    ax44.plot(gameweek, transfers_cost, color='r', label='Transfers cost')
    ax4.set_xlabel('Game week')
    ax4.set_ylabel('Number of transfers')
    ax44.set_ylabel('Transfers cost')
    ax4.legend(loc=2, frameon=True, prop={'size': 15})
    ax44.legend(loc=1, frameon=True, prop={'size': 15})
    ax44.set_ylim(ymin=0)
    ax44.set_ylim(ymax=max(transfers_cost) + 1)
    ax4.set_ylim(ymin=0)
    ax4.set_ylim(ymax=max(transfers) + 1)
    ax4.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax44.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    return fig4

# Captain points

@st.cache(allow_output_mutation=True)
def get_fig5(y):
    captain_points = np.array(fetch_my_team_gw_stats(id=y)['Captain points'])
    captains = np.array(fetch_my_team_gw_stats(id=y)['Captain'])
    most_captain_pts = np.array(fetch_my_team_gw_stats(id=y)['Most captained points'])
    mask1 = captain_points > most_captain_pts
    mask2 = captain_points == most_captain_pts
    mask3 = captain_points < most_captain_pts
    fig5, ax5 = plt.subplots(figsize=(11.69, 8.27))
    ax5.bar(gameweek[mask1], list(map(lambda x: x*2, captain_points[mask1])), width=0.5, color='lime',
            label='Greater than the most selected captain')
    ax5.bar(gameweek[mask2], list(map(lambda x: x*2, captain_points[mask2])), width=0.5, color='b',
            label='Equal to the most selected captain')
    ax5.bar(gameweek[mask3], list(map(lambda x: x*2, captain_points[mask3])), width=0.5, color='r',
            label='Less than the most selected captain')
    ax5.set_ylim(ymin=0)
    max_pts = max(captain_points)
    ax5.set_ylim(ymax=max_pts*2 + 5)
    ax5.set_xlabel('Game week')
    ax5.set_ylabel('Captain points')
    rects = ax5.patches
    x = 0
    for rect in rects:
        height = rect.get_height()
        ax5.text(rect.get_x() + rect.get_width() / 2, height + 1, captains[x], ha='center', va='bottom', size=10)
        x = x + 1
    return fig5

def get_fig6(y):
    bench = np.array(fetch_my_team_gw_stats(id=y)['Points on bench'])
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    ax.bar(gameweek, bench, width=0.5, color='b')
    ax.set_xlabel('Game week')
    ax.set_ylabel('Total points on the bench')
    ax.set_ylim(ymin=min(min(bench), 0))
    ax.set_ylim(ymax=max(bench) + 4)
    rects = ax.patches
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, height + 1, height, ha='center', va='bottom', size=10)
    return fig



def app():
    st.title('My Team')
    manager_id = st.text_input('Please insert your manager ID below:', help='To find your ID, log into' +
                    ' FPL and navigate to the' +
                  " 'Points' page. The URL should read something like:  https://fantasy." +
                'premierleague.com/entry/4670327/event/1, where 1 is the GW and 4670327 is the ID.')
    if manager_id == '':
        st.markdown("Your must enter your manager ID (e.g., 4670327) first to see your team's data.")
    else:
        st.header('Team info')
        st.markdown('You are currently viewing team information for:')
        basic_info = get_basic_info(id=manager_id)
        st.table(basic_info)
        st.header('My classic leagues')
        st.markdown('These are the leagues you are involved in along with your ranking in each of these leagues:')
        leagues = get_leagues(id=manager_id)
        st.table(leagues)
        st.header('Season progress')
        fig_1 = get_fig1(y=manager_id)
        st.subheader('Game week points')
        st.markdown("The figure below shows your game week (GW) performances against the average and the " +
                    'highest points of each GW:')
        st.pyplot(fig_1)
        st.subheader('Ranking')
        st.markdown("The figure below shows your ranking for each GW as well as your overall rank " +
                    'after each GW:')
        fig_2 = get_fig2(y=manager_id)
        st.pyplot(fig_2)
        fig_3 = get_fig3(y=manager_id)
        st.subheader('Team value')
        st.markdown("The figure below shows your team value inclusive of your money in the bank  " +
                    'after each GW:')
        st.pyplot(fig_3)
        fig_4 = get_fig4(y=manager_id)
        st.subheader('Transfers')
        st.markdown("The figure below shows your number of transfers for each GW as well as the " +
                    'costs incurred as a result of your transfers for each GW:')
        st.pyplot(fig_4)
        st.subheader('Captain selection')
        st.markdown("The figure below shows your captain's points tally for each GW. Green (red) bars indicate" +
                    ' that your captain scored more (less) points than the captain selected by majority ' +
                    'of FPL managers. Blue bars indicate that you captain scored the same number of points ' +
                    'as the most captained player for that GW.')
        fig_5 = get_fig5(y=manager_id)
        st.pyplot(fig_5)
        st.subheader('Points left on the bench')
        st.markdown('The figure below shows the number of points you left on the bench for each GW:')
        fig_6 = get_fig6(y=manager_id)
        st.pyplot(fig_6)
