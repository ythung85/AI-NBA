import numpy as np 
import pandas as pd
import sys
import argparse


class State():
    quarter = 1
    
    time_in_qtr = 12.00
    home_team = [] # needs to be a df probably with their: minutes in game, fatigue-adjusted-plusminus, "real plus/minus" & maybe Names
    away_team = []
    home_players_on = [] # this can just be a list of the 5 players who the coach has put in the game... maybe use their names for convenience
    away_players_on = [] 
    home_strategy = "Normal"
    away_strategy = "Normal"
    first_poss = ''
    home_score = 0
    away_score = 0
    momentum = 0 # lets say positive means home has scored last, negative means away scored last
    momentum_queue = 0 # so we can track maybe the last 5 baskets or so... rather than just streak
    possession_of_ball = "Neither" # or "Away" or "Home"
    home_timeouts_left = 6 # is this correct for nba? i think
    away_timeouts_left = 6

def consider_timeout(team, state):
    probability_of_calling_timeout = 0.50 # we can totally arbitrarily redefine this, so that it makes sense such that teams don't...
    # ... waste all their timeouts early and so that they dont save them all up too long... but it's mainly based on momentum
    if state.possession_of_ball == team:
        if team == "Home":
              if state.home_timeouts_left > 0:
                    if state.momentum < -5:
                        # away team has momentum
                        u = np.random.uniform()
                        if u > probability_of_calling_timeout:
                            return True
    elif team == "Away":
        if state.away_timeouts_left > 0:
            if state.momentum > 5:
              # home team has momentum
                u = np.random.uniform()
                if u > probability_of_calling_timeout:
                    return True
    return False

def donothing():
    return 'donothing'
    # literally do nothing
def simulate_points(state):
      # account for who has ball, FAPM of both teams, time in game, strategies, momentum
    
    ##
    ##
    
    home_fapm = sum(state.home_team[state.home_team.NAME.isin(state.home_players_on.NAME)]['FAPM'])
    away_fapm = sum(state.away_team[state.away_team.NAME.isin(state.away_players_on.NAME)]['FAPM'])
    
    '''
    
    try to find you the best setting for value of "u > 0.50 + home_fapm - away_fapm"
    
    '''
    if(state.possession_of_ball == "Home"):
        u = np.random.uniform()
        #print('Home team Turns')
        if(u >  0.7 - (away_fapm - home_fapm)/away_fapm):
          # 0 points - turnover
            #print('donothing')
            donothing()
        else:
            #print('try to shoot the ball')
            u = np.random.uniform()
            if(u < 2/5):
                state.home_score += 2
                #print('2 points get.')
            elif(2/5 < u < 0.1+(2/5)):
                state.home_score += 3
                #print('3 points get.')
            else:
                state.home_score += 1
                #print('1 points get.')
        #print('--------------------------------------------------------')
        state.possession_of_ball = "Away"
        
    elif(state.possession_of_ball == "Away"):
        u = np.random.uniform()
        #print('Away team Turns')
        if(u > 0.7 -(away_fapm - home_fapm)/away_fapm):
            # 0 points - turnover
            #print('donothing')
            donothing()
        else:
            u = np.random.uniform()
            #print('try to shoot the ball')
            if(u < 2/5):
                state.away_score += 2
                #print('2 points get.')
            elif(2/5 < u < 0.1+(2/5)):
                state.away_score += 3
                #print('3 points get.')
            else:
                state.away_score += 1
                #print('1 points get.')
        #print('--------------------------------------------------------')
        state.possession_of_ball = "Home"
        
def substitution(team, state):
    if team == "Home":
        tmp = state.home_players_on
        state.home_players_on = state.home_team.sort_values(by=['FAPM'], ascending=False).iloc[0:5]
        if len(set(tmp) - set(state.home_players_on)) > 0 and len(set(state.home_players_on) - set(tmp)):
            print(', '.join(set(tmp) - set(state.home_players_on)) + " is substituted by " + ', '.join(set(state.home_players_on) - set(tmp)))
    

    elif team == "Away":
        tmp = state.away_players_on
        state.away_players_on = state.away_team.sort_values(by=['FAPM'], ascending=False).iloc[0:5]
        if len(set(tmp) - set(state.away_players_on)) > 0 and len(set(state.away_players_on) - set(tmp)):
            print(', '.join(set(tmp) - set(state.away_players_on)) + " is substituted by " + ', '.join(set(state.away_players_on) - set(tmp)))
            
            
            
def simulate_time(state, home_avg, away_avg):
    if(state.possession_of_ball == "Home"):
        u = np.random.exponential(1/home_avg)[0]
    elif(state.possession_of_ball == "Away"):
        u = np.random.exponential(1/away_avg)[0]
        # for all players on court, update minutes played
    state.home_players_on['Minutes in Game'] = 0
    state.away_players_on['Minutes in Game'] = 0
    
    state.home_players_on['Minutes in Game'] = state.home_players_on['Minutes in Game'].add(u) # for every row in the column
    state.away_players_on['Minutes in Game'] = state.away_players_on['Minutes in Game'].add(u) # for every row in the column
    if(state.time_in_qtr - u < 0):
        state.quarter += 1
        state.time_in_qtr = 12.00
        if(state.first_poss == "Home"):
            if(state.quarter%2 == 0):
                state.possession_of_ball = "Away"
            else:
                state.possession_of_ball = "Home"
        elif(state.first_poss == "Away"):
            if(state.quarter%2 != 0):
                state.possession_of_ball = "Away"
            else:
                state.possession_of_ball = "Home"
        return False # false means do not simulate points
    else:
        state.time_in_qtr -= u
        return True  
    
def update_time(state):
    state.home_team.loc[state.home_team.NAME.isin(state.home_players_on.NAME), 'Minutes in Game'] += state.home_players_on['Minutes in Game']
    state.away_team.loc[state.away_team.NAME.isin(state.away_players_on.NAME), 'Minutes in Game'] += state.away_players_on['Minutes in Game']
    
def update_fapm(state):
    
    #discuss
    state.home_team.loc[state.home_team.NAME.isin(state.home_players_on.NAME), 'FAPM'] -= 0.005
    state.away_team.loc[state.away_team.NAME.isin(state.away_players_on.NAME), 'FAPM'] -= 0.005   
    
    state.home_team.loc[~state.home_team.NAME.isin(state.home_players_on.NAME), 'FAPM'] += 0.005
    state.away_team.loc[~state.away_team.NAME.isin(state.away_players_on.NAME), 'FAPM'] += 0.005


parser = argparse.ArgumentParser(description='AINBA')
parser.add_argument("--home_team", type=str, default="nan")
parser.add_argument("--away_team", type=str, default="nan")
nba = parser.parse_args()

def main():
    print('Starting simulation the game...')
    print(' ')
    print('home team: ', nba.home_team, ' play against ','away team: ', nba.away_team)

    state = State()

    all_players = pd.read_csv("NBA_RPM.csv")
    home_tm = nba.home_team
    temp = all_players[all_players['TEAM'] == home_tm].sort_values(by=['MPG'], ascending=False)[0:10]

    home = {}
    home['NAME'] = temp['NAME'] 
    home['RPM'] = temp['RPM'] 
    home['Minutes in Game'] = 0
    home['FAPM'] = temp['RPM']

    state.home_team = []
    state.home_team.append(home)
    state.home_team = pd.DataFrame.from_dict(state.home_team[0], orient='columns')

    away_tm = nba.away_team
    temp = all_players[all_players['TEAM'] == away_tm].sort_values(by=['MPG'], ascending=False)[0:10]

    away = {}
    away['NAME'] = temp['NAME'] 
    away['RPM'] = temp['RPM'] 
    away['Minutes in Game'] = 0
    away['FAPM'] = temp['RPM']

    state.away_team = []
    state.away_team.append(away)
    state.away_team = pd.DataFrame.from_dict(state.away_team[0], orient='columns')

    poss_times = pd.read_csv("NBA_Poss.csv")
    home_tm_poss_secs = poss_times[poss_times['TEAM'] == home_tm]['SPP']
    away_tm_poss_secs = poss_times[poss_times['TEAM'] == away_tm]['SPP']

    u = np.random.uniform()
    if(u < 0.5):
        state.possession_of_ball = "Home"
        state.first_poss = "Home"
    else:
        state.possession_of_ball = "Away"
        state.first_poss = "Away"
        
    count = state.quarter
    
    while(state.quarter < 5):
        
        consider_timeout("Home", state)
        consider_timeout("Away", state)
        substitution("Home", state)
        substitution("Away", state)
        #consider_strategy("Home", state)
        #consider_strategy("Away", state)
        
        try_score = simulate_time(state, home_tm_poss_secs, away_tm_poss_secs)

        if(try_score):
            simulate_points(state)
            
        update_time(state)    
        update_fapm(state)
        
        if state.quarter == (count + 1):
            print('--------------------------------------------------')
            print('Quarter ' + str(count) + ' end')
            print(home_tm,': ', state.home_score, ' | ', away_tm,': ', state.away_score)
            count = state.quarter
    print('*******************************************')
    print(nba.home_team,'players statistics:')
    print(state.home_team)
    print('*******************************************')
    print(nba.away_team,'players statistics:')
    print(state.away_team)



if __name__ == '__main__':
	main()