import numpy as np
import pandas as pd
import sys
import argparse
import os


class State():
    quarter = 1
    time_in_qtr = 12.00
    home_team = []  # needs to be a df probably with their: minutes in game, fatigue-adjusted-plusminus, "real plus/minus" & maybe Names
    away_team = []
    home_players_on = []  # this can just be a list of the 5 players who the coach has put in the game... maybe use their names for convenience
    away_players_on = []
    home_strategy = "Normal"
    away_strategy = "Normal"
    home_score = 0
    away_score = 0
    momentum = 0  # lets say positive means home has scored last, negative means away scored last
    # so we can track maybe the last 5 baskets or so... rather than just streak
    momentum_queue = 0
    possession_of_ball = "Neither"  # or "Away" or "Home"
    home_timeouts_left = 6  # is this correct for nba? i think
    away_timeouts_left = 6
    subs_allowed = True
    home_pos_count = 0
    away_pos_count = 0


def consider_timeout(team, state):
    # we can totally arbitrarily redefine this, so that it makes sense such that teams don't...
    probability_of_calling_timeout = 0.50
    # ... waste all their timeouts early and so that they dont save them all up too long... but it's mainly based on momentum
    if state.possession_of_ball == team:
        if team == "Home":
            if state.home_timeouts_left > 0:
                if state.momentum < -5:
                    # away team has momentum
                    u = np.random.uniform()
                    if u > probability_of_calling_timeout:
                        state.home_players_on['Curr_Shift'] = 0
                        state.away_players_on['Curr_Shift'] = 0
                        state.home_timeouts_left -= 1
                        return True
    elif team == "Away":
        if state.away_timeouts_left > 0:
            if state.momentum > 5:
                # home team has momentum
                u = np.random.uniform()
                if u > probability_of_calling_timeout:
                    state.home_players_on['Curr_Shift'] = 0
                    state.away_players_on['Curr_Shift'] = 0
                    state.away_timeouts_left -= 1
                    return True
    return False


def substitution_baseline(team, state):
    if team == "Home":
        tmp = state.home_players_on
        if len(tmp) == 0:
            print('starting five: ')
            state.home_players_on = state.home_team.iloc[0:5]
            print(list(state.home_players_on.NAME))
        else:
            if state.time_in_qtr <= 3 and (state.quarter == 1 or state.quarter == 3):
                state.home_players_on = state.home_team.iloc[5:10]

            elif state.time_in_qtr >= 9 and (state.quarter == 2 or state.quarter == 4):
                state.home_players_on = state.home_team.iloc[5:10]

            elif state.time_in_qtr <= 9 and (state.quarter == 2 or state.quarter == 4):
                state.home_players_on = state.home_team.iloc[0:5]

            poc = set(tmp.NAME)
            cp = set(state.home_players_on.NAME)

            if len(poc-cp) != 0:
                for i in range(len(poc-cp)):
                    print(list(poc-cp)[i] + " is substituted by " + list(cp-poc)[i] + " at " + str(
                        state.time_in_qtr) + " in quarter " + str(state.quarter))

    elif team == "Away":
        tmp = state.away_players_on
        if len(tmp) == 0:
            print('starting five: ')
            state.away_players_on = state.away_team.iloc[0:5]
            print(list(state.away_players_on.NAME))
        else:
            if state.time_in_qtr <= 3 and (state.quarter == 1 or state.quarter == 3):
                state.away_players_on = state.away_team.iloc[5:10]

            elif state.time_in_qtr >= 9 and (state.quarter == 2 or state.quarter == 4):
                state.away_players_on = state.away_team.iloc[5:10]

            elif state.time_in_qtr <= 9 and (state.quarter == 2 or state.quarter == 4):
                state.away_players_on = state.away_team.iloc[0:5]
            poc = set(tmp.NAME)
            cp = set(state.away_players_on.NAME)

            if len(poc-cp) != 0:
                for i in range(len(poc-cp)):
                    print(list(poc-cp)[i] + " is substituted by " + list(cp-poc)[i] + " at " + str(
                        state.time_in_qtr) + " in quarter " + str(state.quarter))


def donothing(state):
    state.subs_allowed = False
    return 'donothing'
    # literally do nothing


def simulate_points(state):
    # account for who has ball, FAPM of both teams, time in game, strategies, momentum
    home_fapm = sum(state.home_team[state.home_team.NAME.isin(
        state.home_players_on.NAME)]['FAPM'])
    away_fapm = sum(state.away_team[state.away_team.NAME.isin(
        state.away_players_on.NAME)]['FAPM'])
    home_fapm = np.sign(home_fapm)*np.sqrt(abs(home_fapm))
    away_fapm = np.sign(away_fapm)*np.sqrt(abs(away_fapm))
    if (state.possession_of_ball == "Home"):
        state.home_pos_count += 1
        u = np.random.uniform()
        #print('Home team Turns')
        if (u < 0.50 - (home_fapm - away_fapm)/100):
            # 0 points - turnover
            # print('donothing')
            donothing(state)
        else:
            #print('try to shoot the ball')
            u = np.random.uniform()
            if (u < (0.29/0.50)):
                state.home_score += 2
                #print('2 points get.')
            elif ((0.29/0.50) < u < (0.29/0.50)+(0.12/0.50)):
                state.home_score += 3
                #print('3 points get.')
            else:
                # free throw case
                u2 = np.random.uniform()
                if (u2 < 0.25*0.25):
                    donothing(state)
                elif (0.25*0.25 < u2 < 0.75*0.75):
                    state.home_score += 1
                else:
                    state.home_score += 2

        state.possession_of_ball = "Away"

    elif (state.possession_of_ball == "Away"):
        u = np.random.uniform()
        state.away_pos_count += 1
        #print('Away team Turns')
        if (u < 0.50 - (away_fapm - home_fapm)/100):
            # 0 points - turnover
            # print('donothing')
            donothing(state)
        else:
            #print('try to shoot the ball')
            u = np.random.uniform()
            if (u < (0.29/0.50)):
                state.away_score += 2
                #print('2 points get.')
            elif ((0.29/0.50) < u < (0.29/0.50)+(0.12/0.50)):
                state.away_score += 3
                #print('3 points get.')
            else:
                # free throw case
                u2 = np.random.uniform()
                if (u2 < 0.25*0.25):
                    donothing(state)
                elif (0.25*0.25 < u2 < 0.75*0.75):
                    state.away_score += 1
                else:
                    state.away_score += 2
        state.possession_of_ball = "Home"


def substitution(team, state):
    if team == "Home":
        tmp = state.home_players_on
        if len(tmp) == 0:
            print('starting five: ')
            state.home_players_on = state.home_team.sort_values(
                by=['FAPM'], ascending=False).iloc[0:5]
            print(list(state.home_players_on.NAME))
        else:

            state.home_players_on = state.home_team.sort_values(
                by=['FAPM'], ascending=False).iloc[0:5]
            poc = set(tmp.NAME)
            cp = set(state.home_players_on.NAME)

            if len(poc-cp) != 0:
                for i in range(len(poc-cp)):
                    print(list(poc-cp)[i] + " is substituted by " + list(cp-poc)[i] + " at " + str(
                        state.time_in_qtr) + " in quarter " + str(state.quarter))

    elif team == "Away":
        tmp = state.away_players_on
        if len(tmp) == 0:
            print('starting five: ')
            state.away_players_on = state.away_team.sort_values(
                by=['FAPM'], ascending=False).iloc[0:5]
            print(list(state.away_players_on.NAME))
        else:
            state.away_players_on = state.away_team.sort_values(
                by=['FAPM'], ascending=False).iloc[0:5]
            poc = set(tmp.NAME)
            cp = set(state.away_players_on.NAME)

            if len(poc-cp) != 0:
                for i in range(len(poc-cp)):
                    print(list(poc-cp)[i] + " is substituted by " + list(cp-poc)[i] + " at " + str(
                        state.time_in_qtr) + " in quarter " + str(state.quarter))


def simulate_time(state, home_avg, away_avg):
    sd = 3/60
    if (state.possession_of_ball == "Home"):
        u = np.random.normal(home_avg/60, sd)[0]
    elif (state.possession_of_ball == "Away"):
        u = np.random.normal(away_avg/60, sd)[0]
    print("current possession time = ", str(u))
    # for all players on court, update minutes played
    if (state.time_in_qtr - u < 0):
        state.home_players_on['Minutes in Game'] = state.home_players_on['Minutes in Game'].add(
            state.time_in_qtr)  # for every row in the column
        state.away_players_on['Minutes in Game'] = state.away_players_on['Minutes in Game'].add(
            state.time_in_qtr)  # for every row in the column
        # quarter is over - so a timeout occurs - all players current shift set to 0
        state.home_players_on['Curr_Shift'] = 0
        state.away_players_on['Curr_Shift'] = 0
        state.quarter += 1
        state.time_in_qtr = 12.00
        if (state.first_poss == "Home"):
            if (state.quarter % 2 == 0):
                state.possession_of_ball = "Away"
            else:
                state.possession_of_ball = "Home"
        elif (state.first_poss == "Away"):
            if (state.quarter % 2 != 0):
                state.possession_of_ball = "Away"
            else:
                state.possession_of_ball = "Home"
        return False  # false means do not simulate points
    else:
        state.time_in_qtr -= u
        state.home_players_on['Minutes in Game'] = state.home_players_on['Minutes in Game'].add(
            u)  # for every row in the column
        state.away_players_on['Minutes in Game'] = state.away_players_on['Minutes in Game'].add(
            u)  # for every row in the column
        state.home_players_on['Curr_Shift'] = state.home_players_on['Curr_Shift'].add(
            u)  # for every row in the column
        state.away_players_on['Curr_Shift'] = state.away_players_on['Curr_Shift'].add(
            u)  # for every row in the column
        if (u > 24/60):
            donothing(state)
            return False
        return True


def update_time(state):

    state.home_team.loc[state.home_team.NAME.isin(
        state.home_players_on.NAME), 'Minutes in Game'] = state.home_players_on['Minutes in Game']
    state.away_team.loc[state.away_team.NAME.isin(
        state.away_players_on.NAME), 'Minutes in Game'] = state.away_players_on['Minutes in Game']


def update_fapm(state):

    # discuss
    state.home_team.loc[state.home_team.NAME.isin(state.home_players_on.NAME), 'FAPM'] = state.home_players_on['RPM']-(
        state.home_players_on['Minutes in Game']/2.5+state.home_players_on['Curr_Shift'])
    state.away_team.loc[state.away_team.NAME.isin(state.away_players_on.NAME), 'FAPM'] = state.away_players_on['RPM']-(
        state.away_players_on['Minutes in Game']/2.5+state.away_players_on['Curr_Shift'])

    #state.home_team.loc[~state.home_team.NAME.isin(state.home_players_on.NAME), 'FAPM'] += 0
    #state.away_team.loc[~state.away_team.NAME.isin(state.away_players_on.NAME), 'FAPM'] += 0


parser = argparse.ArgumentParser(description='AINBA')
parser.add_argument("--home_team", type=str, default="nan")
parser.add_argument("--away_team", type=str, default="nan")
# AI for our strategy and BL for baseline strategy
parser.add_argument("--strategy_home", type=str, default="nan")
parser.add_argument("--strategy_away", type=str, default="nan")
nba = parser.parse_args()


def main():
    print('Starting simulation the game...')
    print(' ')
    print('home team: ', nba.home_team,
          ' play against ', 'away team: ', nba.away_team)

    state = State()

    all_players = pd.read_csv("NBA_RPM.csv")
    home_tm = nba.home_team
    temp = all_players[all_players['TEAM'] == home_tm].sort_values(
        by=['MPG'], ascending=False)[0:10]

    home = {}
    home['NAME'] = temp['NAME']
    home['RPM'] = temp['RPM']
    home['Minutes in Game'] = 0
    home['FAPM'] = temp['RPM']
    home['Curr_Shift'] = 0

    state.home_team = []
    state.home_team.append(home)
    state.home_team = pd.DataFrame.from_dict(
        state.home_team[0], orient='columns')
    state.home_team = state.home_team.sort_values(
        by=['FAPM'], ascending=False)

    away_tm = nba.away_team
    temp = all_players[all_players['TEAM'] == away_tm].sort_values(
        by=['MPG'], ascending=False)[0:10]

    away = {}
    away['NAME'] = temp['NAME']
    away['RPM'] = temp['RPM']
    away['Minutes in Game'] = 0
    away['FAPM'] = temp['RPM']
    away['Curr_Shift'] = 0

    state.away_team = []
    state.away_team.append(away)
    state.away_team = pd.DataFrame.from_dict(
        state.away_team[0], orient='columns')
    state.away_team = state.away_team.sort_values(
        by=['FAPM'], ascending=False)

    poss_times = pd.read_csv("NBA_Poss.csv")
    home_tm_poss_secs = poss_times[poss_times['TEAM'] == home_tm]['SPP']
    away_tm_poss_secs = poss_times[poss_times['TEAM'] == away_tm]['SPP']

    u = np.random.uniform()
    if (u < 0.5):
        state.possession_of_ball = "Home"
        state.first_poss = "Home"
    else:
        state.possession_of_ball = "Away"
        state.first_poss = "Away"

    count = state.quarter

    while (state.quarter < 5):
        if (state.subs_allowed):
            consider_timeout("Home", state)
            consider_timeout("Away", state)
            if nba.strategy_home == 'AI':
                substitution("Home", state)

            elif nba.strategy_home == 'BL':
                substitution_baseline("Home", state)

            if nba.strategy_away == 'AI':
                substitution("Away", state)

            elif nba.strategy_away == 'BL':
                substitution_baseline("Away", state)

            #consider_strategy("Home", state)
            #consider_strategy("Away", state)
        else:
            state.subs_allowed = True
            # if we were not allowed to sub on this loop iteration, then we wont let the agent consider it
            # however we will set subs_allowed back to true, so that we can do it on next iteration, UNLESS
            # if they miss the basket then it will be set to false again

        try_score = simulate_time(state, home_tm_poss_secs, away_tm_poss_secs)

        if (try_score):
            simulate_points(state)

        update_time(state)
        update_fapm(state)

        if state.quarter == (count + 1):
            print('--------------------------------------------------')
            print('Quarter ' + str(count) + ' end')
            print(home_tm, ': ', state.home_score,
                  ' | ', away_tm, ': ', state.away_score)
            print('home poss count: ', state.home_pos_count,
                  ' away poss count: ', state.away_pos_count)
            count = state.quarter
    print('*******************************************')
    print(nba.home_team, 'players statistics:')
    print(state.home_team)
    print('*******************************************')
    print(nba.away_team, 'players statistics:')
    print(state.away_team)


if __name__ == '__main__':
    main()
