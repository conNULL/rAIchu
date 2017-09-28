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
from BattleMove import BattleMove

class Battle():
    

    def __init__(self, id):
        self.id = id
        self.info = {}
        self.opp_pokemon = []
        self.move_required = MoveType.NONE
        self.first_info = False
        webbrowser.open("https://play.pokemonshowdown.com/" + Battle.tag + id)
        
    def initialize(web_socket, ai, tag, DATA_DIRECTORY):
        Battle.ws = web_socket
        Battle.ai = ai
        Battle.tag = tag
        Battle.load_resources(DATA_DIRECTORY)

    def load_resources(DATA_DIRECTORY):
        f = open(DATA_DIRECTORY + '/move_dict.txt', 'r')
        Battle.possible_moves = json.load(f)
        f.close()
        
        f = open(DATA_DIRECTORY + '/pokemon_stats_dict.txt', 'r')
        Battle.pokemon_stats = json.load(f)
        f.close()
        
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
        self.move_required = MoveType.NONE
        
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

            for k in range(len(self.info['pokemon'])):
                self.info['pokemon'][k]['type'] = Battle.pokemon_stats[self.info['pokemon'][k]['ident']]['types']
                
            if not self.first_info:
                self.info['id'] = self.info['pokemon'][0]['ident'][1]
                self.info['opp_id'] = str(3-int(self.info['id']))
                self.info['opp_pokemon'] = [{} for k in range(6)]
                self.first_info = True
    
        if '|turn|' in message or '|start' in message:
            
            if '|move|p' + self.info['opp_id'] in message:
                line = message.split('|move|p' + self.info['opp_id']+'a: ')[1]
                move = line.split('|')[1].lower().replace(' ', '')
                self.info['opp_pokemon'][self.info['opp_active']]['moves'].add(move)
                
            if '|switch|p' + self.info['opp_id'] in message:
                line = message.split('|switch|p' + self.info['opp_id']+'a: ')[1].lower()
                opp_active = line[:line.index('\n')].split('|')
                level = int(opp_active[1].split(', ')[1][1:])
                
                if not opp_active[0] in self.opp_pokemon:
                    index = len(self.opp_pokemon)
                    self.opp_pokemon.append(opp_active[0])
                    self.info['opp_pokemon'][index]['ident'] = opp_active[0]
                    #self.info['opp_pokemon'][index]['details'] = opp_active[1]
                    self.info['opp_pokemon'][index]['moves'] = set([])
                    self.info['opp_pokemon'][index]['status'] = set([])
                    self.info['opp_pokemon'][index]['ability'] = ''
                    self.info['opp_pokemon'][index]['level'] = level
                    self.info['opp_pokemon'][index]['type'] = Battle.pokemon_stats[opp_active[0]]['types']
                    self.info['opp_pokemon'][index]['stats'] = Battle.calculate_stats(Battle.pokemon_stats[opp_active[0]]['baseStats'], level)
                    name = opp_active[0].lower().replace(' ', '')
                    if name in Battle.possible_moves.keys():
                        self.info['opp_pokemon'][index]['possible_moves'] = Battle.possible_moves[name]
                else:  
                    index = self.opp_pokemon.index(opp_active[0])
                    
                self.info['opp_pokemon'][index]['condition'] = opp_active[2]
                self.info['opp_active'] = index
                
            if '|-damage|p' + self.info['opp_id'] in message or '|heal|p' + self.info['opp_id'] in message:
                cond = message[max(message.rfind('|-damage|p' + self.info['opp_id']), message.rfind('|-damage|p' + self.info['opp_id']))+10:].split('|')[1]
                self.info['opp_pokemon'][self.info['opp_active']]['condition'] = cond
            if '|-start|p' + self.info['opp_id'] in message:
                status_message = message.split('|-start|p' + self.info['opp_id'])[1:]
                for line in status_message:
                    self.info['opp_pokemon'][self.info['opp_active']]['status'].add(line[10:line.index('\n')].split('|')[1])
                    
            if '|-end|p' + self.info['opp_id'] in message:
                status_message = message.split('|-end|p' + self.info['opp_id'])[1:]
                for line in status_message:
                    self.info['opp_pokemon'][self.info['opp_active']]['status'].remove(line[10:line.index('\n')].split('|')[2])
            print(self.info['opp_pokemon'])
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
        
    def calculate_stats(base_stats, level):
        
        stats = {}
        for k in base_stats:
            if k == 'hp':
                stats[k] = ((2*base_stats[k] + 52)*level//100) + level + 10
            else:
                stats[k] = ((2*base_stats[k] + 52)*level//100) + 5
                
        return stats
        
    
            
        
                