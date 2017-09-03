import webbrowser
import websocket
import ssl
import time
import _thread
import json
import random
from enum import Enum
import requests

class MoveType(Enum):
    NONE = 0
    BATTLE_ACTION = 1
    BATTLE_SWITCH = 2
    
class AIType(Enum):
    RANDOM = 0
    MANUAL = 1
    
    
class Battle():
    

    def __init__(self, id):
        self.id = id
        self.info = {}
        self.move_required = MoveType.BATTLE_ACTION
        webbrowser.open("https://play.pokemonshowdown.com/" + Battle.tag + id)
        
    def initialize(web_socket, ai, tag):
        Battle.ws = web_socket
        Battle.ai = ai
        Battle.tag = tag


    def make_move(self):
        
        if self.move_required == MoveType.NONE:
            return
            
        if self.ai == AIType.MANUAL:
            command = input('|/'+ Battle.tag + self.id + ' : ')
        elif self.ai == AIType.RANDOM:
            moves = self.generate_moves()
            command = moves[random.randint(0, len(moves)-1)]
        
        command = Battle.tag + self.id + '|/'+ command
        Battle.ws.send(command)
        print('COMMAND', command)
        self.move_required == MoveType.NONE
        
    def generate_moves(self):
        
        moves = []
    
        if self.move_required == MoveType.BATTLE_ACTION or self.move_required == MoveType.BATTLE_SWITCH:
            
            for i in range(len(self.info['pokemon'])):
                if self.info['pokemon'][i]['active'] == False and self.info['pokemon'][i]['condition'] != '0 fnt':
                    moves.append('switch ' + str(i+1))
        if self.move_required == MoveType.BATTLE_ACTION:
            for i in range(4):
                if self.info['active']['moves'][i]['pp'] > 0 and not self.info['active']['moves'][i]['disabled']:
                    moves.append('move ' + str(i+1))
                
        return moves
            

    def update_battle_info(self, message):
       
        if 'moves' in message and 'baseAbility' in message:
            json_message = json.loads(message.split('request|')[1])
            self.info['pokemon'] =  json_message['side']['pokemon']
            self.info['active'] = json_message['active'][0]
            self.info['id'] = self.info['pokemon'][0]['ident'][1]
    
        if '|turn|' in message:
            print('turn-----------')
            self.move_required = MoveType.BATTLE_ACTION
        if '|faint|' in message:
            id = message.split('faint|p')[1].split('a')[0]
            if id == self.info['id']:
                self.move_required = MoveType.BATTLE_SWITCH
                pokemon = message.split('faint|')[1].split('|0 fnt')[0]
                ident = pokemon[:2] + pokemon[3:]
                print(ident)
                for i in range(6):    
                    if self.info['pokemon'][i]['ident'] == ident:
                        self.info['pokemon'][i]['condition'] = '0 fnt'
        self.make_move()
    def reset_battle_info(self):
        
        self.battle_info = {}
            
def on_message(ws, message):
    global in_battle
    global battle_tag
    global move_required
    global username
    global logged_in
    global battles
    
        
    if logged_in:
            
        battle_tag = message.split('\n')[0]
        battle_id = battle_tag.split(Battle.tag)[1]
        if len(battle_id == 9):
            
            print('BATTLE:', battle_id)
            
            if battle_id not in battles.keys():
                
                new_battle = Battle(battle_id)        
                battles[battle_id] = new_battle
                
            elif '|choice|move batonpass|' in message or '|choice||move uturn' in message:
                battles[battle_id].move_required = MoveType.BATTLE_SWITCH
                
            elif (username + '\'s rating:') in message and battle_tag in message:
                ws.send('|/leave ' + battle_tag)
                del battles[battle_id]
                ws.send('|/battle!')
            
            battles[battle_id].update_battle_info(message)
            
    elif '|challstr|' in message:
        challstr = message[10:]
        print(challstr)
        logged_in = login(challstr, ws)
        
    print(message)

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
    AI = AIType.RANDOM
    
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://sim2.psim.us/showdown/websocket",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    battles = {}
    Battle.initialize(ws, AI,TAG)
    ws.run_forever()