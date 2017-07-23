import webbrowser
import websocket
import ssl
import time
import _thread


def on_message(ws, message):
    global in_battle
    global battle_tag
    
    if not message == '':
        if not in_battle:
            response = message.split(battle_tag)
            battle_tag += response[1].split('\n')[0]
            webbrowser.open("https://play.pokemonshowdown.com/" + battle_tag)
            in_battle = True
        
        print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    
    global in_battle
    
    def run(*args):
        while not in_battle:
            time.sleep(1)
            ws.send('|/battle!')
        for i in range(100):
            time.sleep(1)
            command = input('|\/'+ battle_tag + ' : ')
            ws.send(battle_tag + '|/' + command)
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    _thread.start_new_thread(run, ())


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://sim2.psim.us/showdown/websocket",
    #ws = websocket.WebSocketApp("ws://sim.smogon.com:8000/showdown/websocket",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    in_battle = False
    battle_tag = "battle-gen7randombattle-"
    ws.run_forever()