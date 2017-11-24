import webbrowser
import websocket
import ssl
import time
import _thread
import ujson as json
import random
from enum import Enum
import requests
from RAIchu_Enums import MoveType, AIType, PredictionType, Player
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
        self.locked = False
        self.info['field'] = {'side': set([]), 'opp_side': set([]), 'global': set([])}
        self.active_disabled = [0 for k in range(4)]
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
        elif self.locked:
            command = 'move 1'
            self.locked = False
        elif self.ai == AIType.RANDOM:
            moves = self.generate_moves()
            command = moves[random.randint(0, len(moves)-1)]
        elif self.ai == AIType.MINIMAX:
            action = Heuristic_Search.get_move(json.dumps(self.info), self.move_required, PredictionType.MOST_LIKELY)
            print('ACTION', action)
            if action >= RAIchu_Utils.NUM_POKEMON:
                command = 'move ' + str(action+1 - RAIchu_Utils.NUM_POKEMON)
            else:
                command = 'switch ' + self.ret_pok_map[self.info['pokemon'][action]['orig_ident']]
        
        command = Battle.tag + self.id + '|/'+ command
        if 'move' in command:
            print('Expected damage: ', RAIchu_Utils.calculate_damage(self.info['pokemon'][self.info['active']], self.info['opp_pokemon'][self.info['opp_active']], Player.SELF, self.info['field'], self.info['pokemon'][self.info['active']]['moves'][int(command.split(' ')[-1])-1], PredictionType.MOST_LIKELY))
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
            for i in range(len(self.info['pokemon'][self.info['active']]['moves'])):
                if self.info['pokemon'][self.info['active']]['disabled'][i] == 0:
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
                    self.info['pokemon'][k]['possible_moves'] = self.info['pokemon'][k]['moves']
                    self.info['pokemon'][k]['volatileStatus'] = set([])                    
                    self.info['pokemon'][k]['disabled'] = [0 for k in range(len(self.info['pokemon'][k]['moves']))]
                    self.info['pokemon'][k]['stats']['hp'] = int(json_message['side']['pokemon'][k]['condition'].split('/')[1].split(' ')[0])
                    self.info['active'] = 0
                    self.info['opp_active'] = 0
                    
                self.info['opp_id'] = str(3-int(self.info['id']))
                self.info['opp_pokemon'] = [{} for k in range(6)]
            if 'active' in json_message.keys():
                
                #inconsistent message from server. Only one choice in this situation. (after Outrage, thrash, etc.)
                if len(json_message['active'][0]['moves']) == 1 and 'trapped' in json_message['active'][0]:
                    self.locked = True
                else:
                    for i in range(len(json_message['active'][0]['moves'])):
                        if json_message['active'][0]['moves'][i]['disabled'] == True:
                            self.active_disabled[i] = 1
                        else:
                            self.active_disabled[i] = 0
                        
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
             
            #Active pokemon switches
            if '|switch|p' + self.info['id'] in message or '|drag|p' + self.info['id'] in message:
                if '|switch|p' + self.info['id'] in message:
                    line = message.split('|switch|p' + self.info['id']+'a: ')[1].lower()
                else:
                    line = message.split('|drag|p' + self.info['id']+'a: ')[1].lower()
                    
                active = line[:line.index('\n')].split('|')[0]
                for k in range(len(self.info['pokemon'])):
                    if active == self.info['pokemon'][k]['ident']:
                        RAIchu_Utils.apply_switch(self, Player.SELF, k)
                        
                        
            if '|detailschange|p' + self.info['opp_id'] in message:  

                line = message.split('|detailschange|p' + self.info['opp_id']+'a: ')[1].lower()                    
                opp_active = line[:line.index('\n')].split('|')
                name_id = opp_active[1].split(', ')[0].lower().replace(' ', '').replace('-', '').replace('.', '').replace('\'', '')
                self.info['opp_pokemon'][self.info['opp_active']]['ident'] = name_id
                self.info['opp_pokemon'][self.info['opp_active']]['stats'] = RAIchu_Utils.calculate_stats(RAIchu_Utils.pokemon_stats[name_id]['baseStats'], self.info['opp_pokemon'][self.info['opp_active']]['level'])
                self.info['opp_pokemon'][self.info['opp_active']]['type'] = RAIchu_Utils.pokemon_stats[name_id]['types']
                
            if '|switch|p' + self.info['opp_id'] in message or '|drag|p' + self.info['opp_id'] in message:  
            
                if '|switch|p' + self.info['opp_id'] in message:
                    line = message.split('|switch|p' + self.info['opp_id']+'a: ')[1].lower()
                else:
                    line = message.split('|drag|p' + self.info['opp_id']+'a: ')[1].lower()
                    
                opp_active = line[:line.index('\n')].split('|')
                level = int(opp_active[1].split(', ')[1][1:])
                
                name = opp_active[0].lower().replace(' ', '').replace('-', '').replace('.', '').replace('\'', '')
                name_id = opp_active[1].split(', ')[0].lower().replace(' ', '').replace('-', '').replace('.', '').replace('\'', '')
                
                if name in self.opp_pokemon:

                    index = self.opp_pokemon.index(name)
                else:

                    index = len(self.opp_pokemon)
                    self.opp_pokemon.append(name)
                    self.info['opp_pokemon'][index]['ident'] = ''
                    
                if not name_id == self.info['opp_pokemon'][index]['ident']:
                    self.info['opp_pokemon'][index]['ident'] = name_id
                    self.info['opp_pokemon'][index]['moves'] = set([])
                    self.info['opp_pokemon'][index]['status'] = set([])
                    self.info['opp_pokemon'][index]['ability'] = ''
                    self.info['opp_pokemon'][index]['item'] = ''
                    self.info['opp_pokemon'][index]['volatileStatus'] = set([])
                    self.info['opp_pokemon'][index]['boosts'] = RAIchu_Utils.BOOST_DICT.copy()
                    self.info['opp_pokemon'][index]['level'] = level
                    self.info['opp_pokemon'][index]['type'] = RAIchu_Utils.pokemon_stats[name_id]['types']
                    self.info['opp_pokemon'][index]['stats'] = RAIchu_Utils.calculate_stats(RAIchu_Utils.pokemon_stats[name_id]['baseStats'], level)
                    if name_id in RAIchu_Utils.possible_moves.keys():
                        self.info['opp_pokemon'][index]['possible_moves'] = RAIchu_Utils.possible_moves[name_id]
                cond = opp_active[2]
                
                self.info['opp_pokemon'][index]['condition'] = int(cond.split('/')[0])
                RAIchu_Utils.apply_switch(self, Player.OPPONENT, index)
            
            #Changes in Condition, damage or heal.    
            if '|-damage|p' + self.info['opp_id'] in message or '|-heal|p' + self.info['opp_id'] in message:
                cond = message[max(message.rfind('|-damage|p' + self.info['opp_id']), message.rfind('|-heal|p' + self.info['opp_id']))+10:].split('|')[1]
                
                if 'fnt' in cond:
                    self.info['opp_pokemon'][self.info['opp_active']]['condition'] = 0
                else:
                    self.info['opp_pokemon'][self.info['opp_active']]['condition'] = int(cond.split('/')[0])
             
            #Status and Volatile Status
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
             
            #Side status and effects
            if '|-sidestart|p' + self.info['opp_id'] in message:
                status_message = message.split('|-sidestart|p' + self.info['opp_id'])[1:]
                for line in status_message:
                    self.info['field']['opp_side'].add(line[:line.index('\n')].split('|')[1].replace('move:', '').replace(' ', '').lower())
                    
            if '|-sideend|p' + self.info['opp_id'] in message:
                status_message = message.split('|-sideend|p' + self.info['opp_id'])[1:]
                for line in status_message:
                    self.info['field']['opp_side'].remove(line[:line.index('\n')].split('|')[1].replace('move:', '').replace(' ', '').lower())
             
               
            if '|-sidestart|p' + self.info['id'] in message:
                status_message = message.split('|-sidestart|p' + self.info['id'])[1:]
                for line in status_message:
                    self.info['field']['side'].add(line[:line.index('\n')].split('|')[1].replace('move:', '').replace(' ', '').lower())
                    
            if '|-sideend|p' + self.info['id'] in message:
                status_message = message.split('|-sideend|p' + self.info['id'])[1:]
                for line in status_message:
                    self.info['field']['side'].remove(line[:line.index('\n')].split('|')[1].replace('move:', '').replace(' ', '').lower())
            #Stat boosts
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
                boost_message = message.split('|-unboost|p' + self.info['id'])[1:]
                for line in boost_message:
                    boostline = line[:line.index('\n')].split('|')
                    stat = boostline[1]
                    val = int(boostline[2])
                    self.info['pokemon'][self.info['active']]['boosts'][stat] -= val
                    
            #items, we only need to track the opponent's items as we know what our own are
            if self.info['opp_pokemon'][self.info['opp_active']]['item'] == '' and 'item: ' in message:
                item_list = message.split('item: ')
                for i in range(len(item_list)-1):
                    ind = item_list[i].rfind('a: ')-1
                    if item_list[i][ind] == self.info['opp_id']:
                        self.info['opp_pokemon'][self.info['opp_active']]['item'] = item_list[i+1][:item_list[i+1].index('\n')].lower().replace(' ', '')
                        break
                        
            if '|-enditem|p' + self.info['opp_id'] in message:
                self.info['opp_pokemon'][self.info['opp_active']]['item'] = 'None'
          
         
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
            
            
        if self.first_info:
            #need to reset disabled status before making a move
            self.info['pokemon'][self.info['active']]['disabled'] = self.active_disabled.copy()
        
        #Make a valid move based on action state
        start = time.time()
        self.make_move()
        finish = time.time()
        print('Move Time:', finish - start)
        
    def reset_battle_info(self):
        
        self.battle_info = {}
        
    
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        
        