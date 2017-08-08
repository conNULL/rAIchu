import webbrowser
import websocket
import ssl
import time
import _thread
import json
import random
from enum import Enum

class MoveType(Enum):
    NONE = 0
    BATTLE_ACTION = 1
    BATTLE_SWITCH = 2


def make_move(ws, battle_info):

    global manual
    global random_move
    
    if manual:
        command = input('|\/'+ battle_tag + ' : ')
    elif random_move:
        moves = generate_moves(battle_info)
        command = moves[random.randint(0, len(moves)-1)]
    
    return command
def generate_moves(battle_info):
    global move_required
    
    moves = []

    if move_required == MoveType.BATTLE_ACTION or move_required == MoveType.BATTLE_SWITCH:
        
        for i in range(len(battle_info['pokemon'])):
            if battle_info['pokemon'][i]['active'] == False and battle_info['pokemon'][i]['condition'] != '0 fnt':
                moves.append('switch ' + str(i+1))
    if move_required == MoveType.BATTLE_ACTION:
        for i in range(4):
            if battle_info['active']['moves'][i]['pp'] > 0 and not battle_info['active']['moves'][i]['disabled']:
                moves.append('move ' + str(i+1))
            
    return moves
            

def update_battle_info(message):
    global battle_info
    global move_required

    if 'moves' in message and 'baseAbility' in message:
        json_message = json.loads(message.split('request|')[1])
        battle_info['pokemon'] =  json_message['side']['pokemon']
        battle_info['active'] = json_message['active'][0]
        battle_info['id'] = battle_info['pokemon'][0]['ident'][1]

    if '|turn|' in message:
        move_required = MoveType.BATTLE_ACTION
    if '|faint|' in message:
        print('-------------------------------------')
        print(message)
        print('-------------------------------------')
        id = message.split('faint|p')[1].split('a')[0]
        if id == battle_info['id']:
            move_required = MoveType.BATTLE_SWITCH
            pokemon = message.split('faint|')[1].split('|0 fnt')[0]
            ident = pokemon[:2] + pokemon[3:]
            print(ident)
            for i in range(6):    
                if battle_info['pokemon'][i]['ident'] == ident:
                    battle_info['pokemon'][i]['condition'] = '0 fnt'
        
    
def on_message(ws, message):
    global in_battle
    global battle_tag
    global move_required
    
    
    if not in_battle:
        response = message.split(battle_tag)
        battle_tag += response[1].split('\n')[0]
        webbrowser.open("https://play.pokemonshowdown.com/" + battle_tag)
        in_battle = True
        move_required = MoveType.BATTLE_ACTION

    else:
        update_battle_info(message)
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    
    
    
    def run(*args):
        global in_battle
        global battle_info
        global move_required
        
        while not in_battle:
            time.sleep(1)
            ws.send('|/battle!')
        for i in range(100):
            time.sleep(10)
            if move_required != MoveType.NONE:
                command = make_move(ws, battle_info)
                ws.send(battle_tag + '|/' + command)
                move_required = MoveType.NONE
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    _thread.start_new_thread(run, ())


if __name__ == "__main__":
    global battle_info
    global random_move
    global manual
    
    manual = False
    random_move = True
    
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://sim2.psim.us/showdown/websocket",
    #ws = websocket.WebSocketApp("ws://sim.smogon.com:8000/showdown/websocket",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    in_battle = False
    battle_info = {}
    battle_tag = "battle-gen7randombattle-"
    ws.run_forever()