import webbrowser
import websocket
import ssl
import time
import _thread
import json
import random
from enum import Enum
import requests
from RAIchu_Enums import MoveType, AIType, PredictionType
from Battle_Resources import Battle_Resources
from RAIchu_Utils import RAIchu_Utils
from Heuristic_Search import Heuristic_Search

class Battle():
    

    def __init__(self, id):
        self.id = id
        self.info = {}
        self.opp_pokemon = []
        self.pok_map = {}
        self.move_required = MoveType.NONE
        self.first_info = False
        webbrowser.open("https://play.pokemonshowdown.com/" + Battle.tag + id)
        Battle.ws.send(Battle.tag + self.id + '|/timer on')
        
    def initialize(web_socket, ai, tag, DATA_DIRECTORY):
        #Class initialization
        Battle.ws = web_socket
        Battle.ai = ai
        Battle.tag = tag
        RAIchu_Utils.load_resources(DATA_DIRECTORY)
        
    def make_move(self):
        
        if self.move_required == MoveType.NONE:
            return
            
        if self.ai == AIType.MANUAL:
            command = input('|/'+ Battle.tag + self.id + ' : ')
        elif self.ai == AIType.RANDOM:
            moves = self.generate_moves()
            command = moves[random.randint(0, len(moves)-1)]
        elif self.ai == AIType.HEURISTIC_SEARCH:
            action = Heuristic_Search.get_move(self.info, self.move_required, PredictionType.EXPECTED)
            print('ACTION', action)
            if action >= RAIchu_Utils.NUM_POKEMON:
                command = 'move ' + str(action+1 - RAIchu_Utils.NUM_POKEMON)
            else:
                command = 'switch ' + self.ret_pok_map[self.info['pokemon'][action]['orig_ident']]
        
        command = Battle.tag + self.id + '|/'+ command
        if 'move' in command:
            print('Expected damage: ', RAIchu_Utils.calculate_damage(self.info['pokemon'][self.info['active']], self.info['opp_pokemon'][self.info['opp_active']], self.info['active_pokemon']['moves'][int(command.split(' ')[-1])-1]['id'], PredictionType.EXPECTED))
        print('COMMAND', command)
        Battle.ws.send(command)
        self.move_required = MoveType.NONE
        
    def generate_moves(self):
        
        moves = []
    
        if self.move_required == MoveType.BATTLE_ACTION or self.move_required == MoveType.BATTLE_SWITCH:
            
            for i in range(len(self.info['pokemon'])):
                if i != self.info['active'] and self.info['pokemon'][i]['condition'] != 0:
                    moves.append('switch ' + self.ret_pok_map[self.info['pokemon'][i]['orig_ident']])
        if self.move_required == MoveType.BATTLE_ACTION:
            for i in range(len(self.info['active_pokemon']['moves'])):
                if not self.info['active_pokemon']['moves'][i]['disabled']:
                    moves.append('move ' + str(i+1))
        return moves
            

    def update_battle_info(self, message):
       
            
        if '|request|{' in message:
            #update game state for player
                        
            json_message = json.loads(message.split('request|')[1])
            
            #get original order for sending commands
            self.ret_pok_map = {}
            for k in range(len(json_message['side']['pokemon'])):
                self.ret_pok_map[json_message['side']['pokemon'][k]['ident']] = str(k+1)
                
            #maintain relative order for maintaining state
            json_message['side']['pokemon'].sort(key=lambda x: x['ident'])
            
            if not self.first_info:                
            
                #initalize game state
                self.info['pokemon'] =  json_message['side']['pokemon'].copy()                  
                self.info['id'] = self.info['pokemon'][0]['ident'][1]
                
                for k in range(len(self.info['pokemon'])):
                    self.info['pokemon'][k]['orig_ident'] = json_message['side']['pokemon'][k]['ident']
                    ident = json_message['side']['pokemon'][k]['ident'][4:].lower().replace(' ', '').replace('-', '').replace('.', '').replace('\'', '')
                    self.info['pokemon'][k]['ident'] = ident
                    ind = self.info['pokemon'][k]['details'].index(', L') + 3
                    self.info['pokemon'][k]['level']  = int(self.info['pokemon'][k]['details'][ind:ind+2])
                    self.info['pokemon'][k]['type'] = RAIchu_Utils.pokemon_stats[self.info['pokemon'][k]['ident']]['types']
                    self.info['pokemon'][k]['boosts'] = RAIchu_Utils.BOOST_DICT.copy()
                    self.info['pokemon'][k]['status'] = set([])
                    self.info['pokemon'][k]['volatileStatus'] = set([])
                    self.info['pokemon'][k]['stats']['hp'] = int(json_message['side']['pokemon'][k]['condition'].split('/')[1].split(' ')[0])
                    self.info['active'] = 0
                    self.info['opp_active'] = 0
                    
                self.info['opp_id'] = str(3-int(self.info['id']))
                self.info['opp_pokemon'] = [{} for k in range(6)]
            if 'active' in json_message.keys():
                
                self.info['active_pokemon'] = json_message['active'][0]
                for i in range(len(self.info['pokemon'])):
                    cond = json_message['side']['pokemon'][i]['condition']
                    if cond != '0 fnt':
                        cur = (100*int(cond.split('/')[0]))//int(cond.split('/')[1].split(' ')[0])
                        self.info['pokemon'][i]['condition'] = cur
                    else:
                        self.info['pokemon'][i]['condition'] = 0
                    
                    if json_message['side']['pokemon'][i]['active'] == True:
                        self.info['active'] = i
                        
            if 'forceSwitch' in json_message.keys():
                self.move_required = MoveType.BATTLE_SWITCH
                

            self.first_info = True
            
        if '|choice|' in message or '|start' in message:
            
            #update game state for turn execution. Message is parsed for |keywords| indicating a change in state.
            if '|move|p' + self.info['opp_id'] in message:
                line = message.split('|move|p' + self.info['opp_id']+'a: ')[1]
                move = line.split('|')[1].lower().replace(' ', '')
                self.info['opp_pokemon'][self.info['opp_active']]['moves'].add(move)
                
            if '|switch|p' + self.info['id'] in message or '|drag|p' + self.info['id'] in message:
                if '|switch|p' + self.info['id'] in message:
                    line = message.split('|switch|p' + self.info['id']+'a: ')[1].lower()
                else:
                    line = message.split('|drag|p' + self.info['id']+'a: ')[1].lower()
                    
                active = line[:line.index('\n')].split('|')[0]
                for k in range(len(self.info['pokemon'])):
                    if active == self.info['pokemon'][k]['ident']:
                        
                        #volatileStatus clears on switching out
                        self.info['pokemon'][self.info['active']]['volatileStatus'] = set([])
                        self.info['active'] = k
                        
            if '|switch|p' + self.info['opp_id'] in message or '|drag|p' + self.info['opp_id'] in message:                        
                #volatileStatus clears on switching out
                self.info['opp_pokemon'][self.info['opp_active']]['volatileStatus'] = set([])
                if '|switch|p' + self.info['opp_id'] in message:
                    line = message.split('|switch|p' + self.info['opp_id']+'a: ')[1].lower()
                else:
                    line = message.split('|drag|p' + self.info['opp_id']+'a: ')[1].lower()
                    
                opp_active = line[:line.index('\n')].split('|')
                level = int(opp_active[1].split(', ')[1][1:])
                
                name = opp_active[0].lower().replace(' ', '').replace('-', '').replace('.', '').replace('\'', '')
                name_id = opp_active[1].split(', ')[0].lower().replace(' ', '').replace('-', '').replace('.', '').replace('\'', '')
                
                if name in self.opp_pokemon:

                    index = self.opp_pokemon.index(opp_active[0])
                else:

                    index = len(self.opp_pokemon)
                    self.opp_pokemon.append(name)
                    self.info['opp_pokemon'][index]['ident'] = ''
                    
                if not name_id == self.info['opp_pokemon'][index]['ident']:
                    self.info['opp_pokemon'][index]['ident'] = name_id
                    self.info['opp_pokemon'][index]['moves'] = set([])
                    self.info['opp_pokemon'][index]['status'] = set([])
                    self.info['opp_pokemon'][index]['volatileStatus'] = set([])
                    self.info['opp_pokemon'][index]['ability'] = ''
                    self.info['opp_pokemon'][index]['level'] = level
                    self.info['opp_pokemon'][index]['type'] = RAIchu_Utils.pokemon_stats[name_id]['types']
                    self.info['opp_pokemon'][index]['boosts'] = RAIchu_Utils.BOOST_DICT.copy()
                    self.info['opp_pokemon'][index]['stats'] = RAIchu_Utils.calculate_stats(RAIchu_Utils.pokemon_stats[name_id]['baseStats'], level)
                    if name_id in RAIchu_Utils.possible_moves.keys():
                        self.info['opp_pokemon'][index]['possible_moves'] = RAIchu_Utils.possible_moves[name_id]
                cond = opp_active[2]
                
                self.info['opp_pokemon'][index]['condition'] = int(cond.split('/')[0])
                self.info['opp_active'] = index
                
            if '|-damage|p' + self.info['opp_id'] in message or '|-heal|p' + self.info['opp_id'] in message:
                cond = message[max(message.rfind('|-damage|p' + self.info['opp_id']), message.rfind('|-heal|p' + self.info['opp_id']))+10:].split('|')[1]
                
                if 'fnt' in cond:
                    self.info['opp_pokemon'][self.info['opp_active']]['condition'] = 0
                else:
                    self.info['opp_pokemon'][self.info['opp_active']]['condition'] = int(cond.split('/')[0])
                
            if '|-status|p' + self.info['opp_id'] in message:
                status_message = message.split('|-status|p' + self.info['opp_id'])[1:]
                for line in status_message:
                    self.info['opp_pokemon'][self.info['opp_active']]['status'].add(line[:line.index('\n')].split('|')[1])
                    
            if '|-start|p' + self.info['opp_id'] in message:
                status_message = message.split('|-start|p' + self.info['opp_id'])[1:]
                for line in status_message:
                    self.info['opp_pokemon'][self.info['opp_active']]['volatileStatus'].add(line[:line.index('\n')].split('|')[1])
                    
            if '|-end|p' + self.info['opp_id'] in message:
                status_message = message.split('|-end|p' + self.info['opp_id'])[1:]
                for line in status_message:
                    self.info['opp_pokemon'][self.info['opp_active']]['volatileStatus'].remove(line[:line.index('\n')].split('|')[1])
             
            if '|-status|p' + self.info['id'] in message:
                status_message = message.split('|-status|p' + self.info['id'])[1:]
                for line in status_message:
                    self.info['pokemon'][self.info['active']]['status'].add(line[:line.index('\n')].split('|')[1])
               
            if '|-start|p' + self.info['id'] in message:
                status_message = message.split('|-start|p' + self.info['id'])[1:]
                for line in status_message:
                    self.info['pokemon'][self.info['active']]['volatileStatus'].add(line[:line.index('\n')].split('|')[1])
                    
            if '|-end|p' + self.info['id'] in message:
                status_message = message.split('|-end|p' + self.info['id'])[1:]
                for line in status_message:
                    self.info['pokemon'][self.info['active']]['volatileStatus'].remove(line[:line.index('\n')].split('|')[1])
                    
            if '|-boost|p' + self.info['opp_id'] in message:
                boost_message = message.split('|-boost|p' + self.info['opp_id'])[1:]
                for line in boost_message:
                    boostline = line[:line.index('\n')].split('|')
                    stat = boostline[1]
                    val = int(boostline[2])
                    self.info['opp_pokemon'][self.info['opp_active']]['boosts'][stat] += val
                    
            if '|-boost|p' + self.info['id'] in message:
                boost_message = message.split('|-boost|p' + self.info['id'])[1:]
                for line in boost_message:
                    boostline = line[:line.index('\n')].split('|')
                    stat = boostline[1]
                    val = int(boostline[2])
                    self.info['pokemon'][self.info['active']]['boosts'][stat] += val
                    
            if '|-unboost|p' + self.info['opp_id'] in message:
                boost_message = message.split('|-unboost|p' + self.info['opp_id'])[1:]
                for line in boost_message:
                    boostline = line[:line.index('\n')].split('|')
                    stat = boostline[1]
                    val = int(boostline[2])
                    self.info['opp_pokemon'][self.info['opp_active']]['boosts'][stat] -= val
                    
            if '|-unboost|p' + self.info['id'] in message:
                boost_message = message.split('|-unboost|p' + self.info['opp_id'])[1:]
                for line in boost_message:
                    boostline = line[:line.index('\n')].split('|')
                    stat = boostline[1]
                    val = int(boostline[2])
                    self.info['pokemon'][self.info['active']]['boosts'][stat] -= val
          
         
        #update action state
        if '|turn|' in message:
            self.move_required = MoveType.BATTLE_ACTION
            
        if '|faint|' in message:
            id = message.split('faint|p')[1].split('a')[0]
            if id == self.info['id']:
                self.move_required = MoveType.BATTLE_SWITCH
                pokemon = message.split('faint|')[1].split('|0 fnt')[0]
                ident = pokemon[4:pokemon.index('\n')].lower().replace(' ', '').replace('-', '').replace('.', '')
                print(ident)
                self.info['pokemon'][self.info['active']]['condition'] = 0
                
        #Make a valid move based on action state
        self.make_move()
        
    def reset_battle_info(self):
        
        self.battle_info = {}
        
    
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        
        