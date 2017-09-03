import webbrowser
import websocket
import ssl
import time
import _thread
import json
import random
from enum import Enum
import requests
from RAIchu_Enums import MoveType, AIType

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
            for i in range(len(self.info['active']['moves'])):
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