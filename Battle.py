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
from BattleMove import BattleMove

class Battle():
    

    def __init__(self, id):
        self.id = id
        self.info = {}
        self.opp_pokemon = []
        self.pok_map = {}
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
        if 'move' in command:
            print('Expected damage: ', self.calculate_damage(self.info['pokemon'][self.info['active']], self.info['opp_pokemon'][self.info['opp_active']], self.info['active_pokemon']['moves'][int(command.split(' ')[-1])-1]['id'], PredictionType.EXPECTED))
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
        # else:
        #     for i in range(len(self.info['pokemon'])):
        #         if self.info['pokemon'][i]['active'] == False and self.info['pokemon'][i]['condition'] != 0:
        #             moves.append('switch ' + self.ret_pok_map[self.info['pokemon'][i]['orig_ident']])
        # 
        return moves
            

    def update_battle_info(self, message):
       
        if 'Can\'t switch:' in message:
            print('error--------------------')
        if '|request|{' in message:
                        
            json_message = json.loads(message.split('request|')[1])
            
            #get original order for sending commands
            self.ret_pok_map = {}
            for k in range(len(json_message['side']['pokemon'])):
                self.ret_pok_map[json_message['side']['pokemon'][k]['ident']] = str(k+1)
                
            #maintain relative order for maintaining state
            json_message['side']['pokemon'].sort(key=lambda x: x['ident'])
            
            if not self.first_info:                

                self.info['pokemon'] =  json_message['side']['pokemon'].copy()                  
                self.info['id'] = self.info['pokemon'][0]['ident'][1]
                
                for k in range(len(self.info['pokemon'])):
                    self.info['pokemon'][k]['orig_ident'] = json_message['side']['pokemon'][k]['ident']
                    ident = json_message['side']['pokemon'][k]['ident'][4:].lower().replace(' ', '').replace('-', '').replace('.', '')
                    self.info['pokemon'][k]['ident'] = ident
                    ind = self.info['pokemon'][k]['details'].index(', L') + 3
                    self.info['pokemon'][k]['level']  = int(self.info['pokemon'][k]['details'][ind:ind+2])
                    self.info['pokemon'][k]['type'] = Battle.pokemon_stats[self.info['pokemon'][k]['ident']]['types']
                    self.info['pokemon'][k]['status'] = set([])
                    
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
                        self.info['active'] = k
                        
            if '|switch|p' + self.info['opp_id'] in message or '|drag|p' + self.info['opp_id'] in message:
                if '|switch|p' + self.info['opp_id'] in message:
                    line = message.split('|switch|p' + self.info['opp_id']+'a: ')[1].lower()
                else:
                    line = message.split('|drag|p' + self.info['opp_id']+'a: ')[1].lower()
                    
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
                    self.info['opp_pokemon'][self.info['opp_active']]['status'].add(line[:line.index('\n')].split('|')[1])
                    
            if '|-end|p' + self.info['opp_id'] in message:
                status_message = message.split('|-end|p' + self.info['opp_id'])[1:]
                for line in status_message:
                    self.info['opp_pokemon'][self.info['opp_active']]['status'].remove(line[:line.index('\n')].split('|')[1])
             
            if '|-status|p' + self.info['id'] in message:
                status_message = message.split('|-status|p' + self.info['id'])[1:]
                for line in status_message:
                    self.info['pokemon'][self.info['active']]['status'].add(line[:line.index('\n')].split('|')[1])
               
            if '|-start|p' + self.info['id'] in message:
                status_message = message.split('|-start|p' + self.info['id'])[1:]
                for line in status_message:
                    self.info['pokemon'][self.info['active']]['status'].add(line[:line.index('\n')].split('|')[1])
                    
            if '|-end|p' + self.info['id'] in message:
                status_message = message.split('|-end|p' + self.info['id'])[1:]
                for line in status_message:
                    self.info['pokemon'][self.info['active']]['status'].remove(line[:line.index('\n')].split('|')[1])
            
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
        
    def calculate_damage(self, attacker, defender, move, pred_type):
        #returns damage done as a percentage of defender's hp
        
        category = BattleMove.effects[move]['category']
    
        if category == 'Physical':
            
            atk = attacker['stats']['atk']
            de = defender['stats']['def']
            
        elif category == 'Special':   
                 
            atk = attacker['stats']['spa']
            de = defender['stats']['spd']
            
        else:
            #non-damaging move
            return 0
            
        power = BattleMove.effects[move]['basePower']
        typ = BattleMove.effects[move]['type']
        
        type_multi = 1
        
        for t in defender['type']:
            type_multi *= BattleMove.typechart[t][typ]
        
        ##To be implemented    
        weather_multi = 1
        other_multi = 1
        
        if 'burn' in attacker['status'] and category == 'Physical':
            burn_multi = 0.5
        else:
            burn_multi = 1
            
        if pred_type == PredictionType.MAX_DAMAGE:
            crit_multi = 2
            random_multi = 1
            
        elif pred_type == PredictionType.MIN_DAMAGE:
            crit_multi = 1
            random_multi = 0.85
            
        elif pred_type == PredictionType.RANDOM:
            val = random.randint(0, 15)
            random_multi = (85+val)/100
            val = random.randint(0, 15)
            if val == 0:
                crit_multi = 2
            else:
                crit_multi = 1
                
        elif pred_type == PredictionType.EXPECTED:
            random_multi = 0.925
            
            ##Need to implement accounting for increased crit chance in some situations
            crit_multi = 1.0625
                        
        if typ in attacker['type']:
            STAB_multi = 1.5
        else:
            STAB_multi = 1
            
        multiplier = weather_multi*crit_multi*random_multi*STAB_multi*type_multi*burn_multi*other_multi
        damage = (((((((2*attacker['level'])/5)+2)*atk*power)/de)/50)+2)*multiplier
        
        percentage = min(defender['condition'], (100*damage)//defender['stats']['hp'])
        return percentage
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        
        