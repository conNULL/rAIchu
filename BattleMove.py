import json

class BattleMove():
    
      
    def __init__(self, name):
        self.name = name
        
    def initialize(BASE):
        f = open(BASE + '/move_effects_enum_dict.txt', 'r')
        BattleMove.effects_enum = json.load(f)
        f.close()
        
        f = open(BASE + '/move_effects_dict.txt', 'r')
        BattleMove.effects = json.load(f)
        f.close()
        
    def get_move_vector(move):
        
        vec = [0] * len(BattleMove.effects_enum)
        flags = BattleMove.effects[move]['flags']
        for flag in flags:
            vec[BattleMove.effects_enum[flag]] = 1
        
        vec[BattleMove.effects_enum['priority']] = BattleMove.effects[move]['priority']        
        vec[BattleMove.effects_enum['pp']] = BattleMove.effects[move]['pp']
        
        #probabilstic effects
        if 'status' in BattleMove.effects[move]:
            vec[BattleMove.effects_enum[BattleMove.effects[move]['status']]] = 100
        if 'volatileStatus' in BattleMove.effects[move]:
            vec[BattleMove.effects_enum[BattleMove.effects[move]['volatileStatus']]] = 100
        if 'sideCondition' in BattleMove.effects[move]:
            vec[BattleMove.effects_enum[BattleMove.effects[move]['sideCondition']]] = 100
            
        #guatanteed effects
        if 'weather' in BattleMove.effects[move]:
            vec[BattleMove.effects_enum[BattleMove.effects[move]['weather']]] = 1
        if 'terrain' in BattleMove.effects[move]:
            vec[BattleMove.effects_enum[BattleMove.effects[move]['terrain']]] = 1
        if 'pseudoWeather' in BattleMove.effects[move]:
            vec[BattleMove.effects_enum[BattleMove.effects[move]['pseudoWeather']]] = 1
            
        vec[BattleMove.effects_enum[BattleMove.effects[move]['type']]] = BattleMove.effects[move]['basePower']
        if (BattleMove.effects[move]['secondary']):
            effects = json.loads(str(BattleMove.effects[move]['secondary']).replace('\'', '"'))
            
            if len(effects) > 2:
                for effect in effects:
                    if 'status' in effect:
                        vec[BattleMove.effects_enum[effect['status']]] = int(effect['chance'])
                    if 'volatileStatus' in effect:
                        vec[BattleMove.effects_enum[effect['volatileStatus']]] = int(effect['chance'])
                    if 'sideCondition' in effect:
                        vec[BattleMove.effects_enum[effect['sideCondition']]] = int(effect['chance'])
            else:
                if 'status' in effects:
                    vec[BattleMove.effects_enum[effects['status']]] = int(effects['chance'])
                elif 'volatileStatus' in effects:
                    vec[BattleMove.effects_enum[effects['volatileStatus']]] = int(effects['chance'])
                elif 'sideCondition' in effects:
                    vec[BattleMove.effects_enum[effects['sideCondition']]] = int(effects['chance'])
                    
        return vec