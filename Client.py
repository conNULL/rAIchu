import webbrowser
import websocket
import ssl
import time
import _thread
import json
import random


def generate_moves(battle_info):
    
    moves = []

    for i in range(len(battle_info['pokemon'])):
        if battle_info['pokemon'][i]['active'] == False and battle_info['pokemon'][i]['condition'].split('\/')[0] != 0:
            moves.append('switch ' + str(i+1))
    for i in range(4):
        if battle_info['active']['moves'][i]['pp'] > 0 and not battle_info['active']['moves'][i]['disabled']:
            moves.append('move ' + str(i+1))
            
    return moves
            

def update_battle_info(message):
    global battle_info
    
    json_message = json.loads(message.split('request|')[1])
    battle_info['pokemon'] =  json_message['side']['pokemon']
    battle_info['active'] = json_message['active'][0]
    
def on_message(ws, message):
    global in_battle
    global battle_tag
    
    
    if not in_battle:
        response = message.split(battle_tag)
        battle_tag += response[1].split('\n')[0]
        webbrowser.open("https://play.pokemonshowdown.com/" + battle_tag)
        in_battle = True
    
    if 'moves' in message and 'baseAbility' in message:
        update_battle_info(message)
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    
    global in_battle
    global battle_info
    global manual
    global random_move
    
    def run(*args):
        while not in_battle:
            time.sleep(1)
            ws.send('|/battle!')
        for i in range(100):
            time.sleep(10)
            if manual:
                command = input('|\/'+ battle_tag + ' : ')
            elif random_move:
                moves = generate_moves(battle_info)
                command = moves[random.randint(0, len(moves)-1)]
            
            ws.send(battle_tag + '|/' + command)
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