import webbrowser
import websocket
import ssl
import time
import _thread
import ujson as json
import random
from enum import Enum
import requests
from Battle import Battle
from RAIchu_Enums import MoveType, AIType
from Battle_Resources import Battle_Resources

          
def on_message(ws, message):
    global in_battle
    global battle_tag
    global move_required
    global username
    global logged_in
    global battles
    
    print(message)
    if logged_in and Battle.tag in message:
        
        battle_tag = message.split('\n')[0]
        battle_id = battle_tag.split(Battle.tag)[1]
        if len(battle_id) == 9 and not '|error|[Invalid choice] There\'s nothing to choose' in message:
            
            print('BATTLE:', battle_id)
            
            if battle_id not in battles.keys():
                
                new_battle = Battle(battle_id)        
                battles[battle_id] = new_battle
            elif username + ' has' in message and 'seconds left' in message:

                battles[battle_id].move_required = MoveType.BATTLE_ACTION
            elif '|choice|move batonpass|' in message or '|choice||move uturn' in message:
                battles[battle_id].move_required = MoveType.BATTLE_SWITCH
                
            elif (username + '\'s rating:') in message and battle_tag in message:
                ws.send('|/leave ' + battle_tag)
                battles[battle_id].reset_battle_info()
                ws.send('|/battle!')
            
            battles[battle_id].update_battle_info(message)
            
    elif '|challstr|' in message:
        challstr = message[10:]
        print(challstr)
        logged_in = login(challstr, ws)
    print('--------------------------------')
    

def login(challstr, ws):
    
    global username
    
    f = open('login.txt', 'r').readlines()
    username = f[0][:-1]
    password = f[1]
    
    r = requests.post('https://play.pokemonshowdown.com/action.php', data={'act': 'login', 'name': username, 'pass' : password, 'challstr' : challstr})
    print(r.status_code, r.reason)
    assertion = r.text.split('"assertion":"')[1][:-2]
    ws.send('|/trn ' + username + ',0,' + assertion)
    if r.status_code == 200:
        return True
    return False
    
def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    
    
    
    def run(*args):
        global in_battle
        global battle_info
        global move_required
        global NUM_BATTLES
        global logged_in
        
        logged_in = False
        
        while not logged_in:
            time.sleep(1)
         
        for i in range(NUM_BATTLES):
            time.sleep(5)
            ws.send('|/battle!')
            
        for i in range(100000):
            
            
                
            time.sleep(1)
            
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    _thread.start_new_thread(run, ())


    
if __name__ == "__main__":
    global random_move
    global manual
    global battles
    
    manual = False
    random_move = True
    NUM_BATTLES = 1
    TAG = 'battle-gen7randombattle-'
    AI = AIType.HEURISTIC_SEARCH
    DATA_DIRECTORY = 'Battle_data'
    
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://sim2.psim.us/showdown/websocket",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    battles = {}
    Battle.initialize(ws, AI,TAG, DATA_DIRECTORY)
    Battle_Resources.initialize(DATA_DIRECTORY)
    ws.run_forever()