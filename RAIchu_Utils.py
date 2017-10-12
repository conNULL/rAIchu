import random
import json
from enum import Enum
from RAIchu_Enums import MoveType, AIType, PredictionType
from Battle_Resources import Battle_Resources

class RAIchu_Utils():
    


    def load_resources(DATA_DIRECTORY):
        

        RAIchu_Utils.BOOST_DICT = {'atk': 0, 'def': 0, 'spd': 0, 'spa': 0, 'spe': 0, 'accuracy': 0}
        RAIchu_Utils.BOOST_MULTI = {-6: 0.25, -5: 0.2857, -4: 0.3333, -3: 0.4, -2: 0.5, -1: 0.66, \
        0: 1, 1: 1.5, 2: 2, 3:2.5, 4: 3, 5: 3.5, 6: 4}

        RAIchu_Utils.NUM_POKEMON = 6
        RAIchu_Utils.NUM_MOVES = 4
        
        f = open(DATA_DIRECTORY + '/move_dict.txt', 'r')
        RAIchu_Utils.possible_moves = json.load(f)
        f.close()
        
        f = open(DATA_DIRECTORY + '/pokemon_stats_dict.txt', 'r')
        RAIchu_Utils.pokemon_stats = json.load(f)
        f.close()
        
    def calculate_stats(base_stats, level):
        #returns an estimate (expected value) of the stats of a pokemon based on their base stats and level
        
        stats = {}
        for k in base_stats:
            if k == 'hp':
                stats[k] = ((2*base_stats[k] + 52)*level//100) + level + 10
            else:
                stats[k] = ((2*base_stats[k] + 52)*level//100) + 5
                
        return stats
        
    def calculate_damage(attacker, defender, move, pred_type):
        #returns damage done as a percentage of defender's total hp
        
        
        power = Battle_Resources.effects[move]['basePower']
        typ = Battle_Resources.effects[move]['type']
        category = Battle_Resources.effects[move]['category']
    
        if category == 'Physical':
            
            atk = RAIchu_Utils.get_stat(attacker, 'atk')
            de = RAIchu_Utils.get_stat(defender, 'def')
            
        elif category == 'Special':   
                 
            atk = RAIchu_Utils.get_stat(attacker, 'spa')
            de = RAIchu_Utils.get_stat(defender, 'spd')
            
        else:
            #non-damaging move
            return 0
            
        
        type_multi = 1
        
        for t in defender['type']:
            type_multi *= Battle_Resources.typechart[t][typ]
        
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
            
            
            
    def get_stat(pokemon, stat):
        #returns the value of the stat of the pokemon with active boosts taken into account
        
        return pokemon['stats'][stat]*RAIchu_Utils.BOOST_MULTI[pokemon['boosts'][stat]]
        
    
    def simulate_move(attacker, defender, move, pred_type):
        
        #Simulates the effect of attacker using move on defender and returns defender state after execution.
        
        #these moves have inconsistent formats from the server messages
        if move != 'rest':
            
            if 'hiddenpower' in move:
                move = 'hiddenpower'
                
            damage = RAIchu_Utils.calculate_damage(attacker, defender, move, pred_type)
            
            defender['condition'] -= damage
            
            if 'status' in Battle_Resources.effects[move].keys():
                defender['status'].add(Battle_Resources.effects[move]['status'])
                
            if 'volatileStatus' in Battle_Resources.effects[move].keys():
                defender['volatileStatus'].add(Battle_Resources.effects[move]['volatileStatus'])
        
            if 'boosts' in Battle_Resources.effects[move].keys():
                
        
                if Battle_Resources.effects[move]['target'] == 'self':
                    RAIchu_Utils.apply_boosts(attacker, Battle_Resources.effects[move]['boosts'])
                        
                else:
                    RAIchu_Utils.apply_boosts(defender, Battle_Resources.effects[move]['boosts'])
                    
            if 'self' in Battle_Resources.effects[move].keys() and 'boosts' in Battle_Resources.effects[move]['self'].keys():
                
                RAIchu_Utils.apply_boosts(attacker, Battle_Resources.effects[move]['self']['boosts'])
                
        
        
        
        
    def apply_boosts(pokemon, boost_dict):
        
        #Applies boosts in boost_dict to pokemon.
                
        for boost in boost_dict.keys():                        
            pokemon['boosts'][boost] += boost_dict[boost]
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        