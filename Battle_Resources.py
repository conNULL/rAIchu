import json

class Battle_Resources():
    
      
    def __init__(self, name):
        self.name = name
        
    def initialize(BASE):
        f = open(BASE + '/move_effects_enum_dict.txt', 'r')
        Battle_Resources.effects_enum = json.load(f)
        f.close()
        
        f = open(BASE + '/move_effects_dict.txt', 'r')
        Battle_Resources.effects = json.load(f)
        f.close()
        
        f = open(BASE + '/typechart.txt', 'r')
        Battle_Resources.typechart = json.load(f)
        f.close()
        
    def get_move_vector(move):
        
        vec = [0] * len(Battle_Resources.effects_enum)
        flags = Battle_Resources.effects[move]['flags']
        for flag in flags:
            vec[Battle_Resources.effects_enum[flag]] = 1
        
        vec[Battle_Resources.effects_enum['priority']] = Battle_Resources.effects[move]['priority']        
        vec[Battle_Resources.effects_enum['pp']] = Battle_Resources.effects[move]['pp']
        
        #probabilstic effects
        if 'status' in Battle_Resources.effects[move]:
            vec[Battle_Resources.effects_enum[Battle_Resources.effects[move]['status']]] = 100
        if 'volatileStatus' in Battle_Resources.effects[move]:
            vec[Battle_Resources.effects_enum[Battle_Resources.effects[move]['volatileStatus']]] = 100
        if 'sideCondition' in Battle_Resources.effects[move]:
            vec[Battle_Resources.effects_enum[Battle_Resources.effects[move]['sideCondition']]] = 100
            
        #guatanteed effects
        if 'weather' in Battle_Resources.effects[move]:
            vec[Battle_Resources.effects_enum[Battle_Resources.effects[move]['weather']]] = 1
        if 'terrain' in Battle_Resources.effects[move]:
            vec[Battle_Resources.effects_enum[Battle_Resources.effects[move]['terrain']]] = 1
        if 'pseudoWeather' in Battle_Resources.effects[move]:
            vec[Battle_Resources.effects_enum[Battle_Resources.effects[move]['pseudoWeather']]] = 1
            
        vec[Battle_Resources.effects_enum[Battle_Resources.effects[move]['type']]] = Battle_Resources.effects[move]['basePower']
        if (Battle_Resources.effects[move]['secondary']):
            effects = json.loads(str(Battle_Resources.effects[move]['secondary']).replace('\'', '"'))
            
            if len(effects) > 2:
                for effect in effects:
                    if 'status' in effect:
                        vec[Battle_Resources.effects_enum[effect['status']]] = int(effect['chance'])
                    if 'volatileStatus' in effect:
                        vec[Battle_Resources.effects_enum[effect['volatileStatus']]] = int(effect['chance'])
                    if 'sideCondition' in effect:
                        vec[Battle_Resources.effects_enum[effect['sideCondition']]] = int(effect['chance'])
            else:
                if 'status' in effects:
                    vec[Battle_Resources.effects_enum[effects['status']]] = int(effects['chance'])
                elif 'volatileStatus' in effects:
                    vec[Battle_Resources.effects_enum[effects['volatileStatus']]] = int(effects['chance'])
                elif 'sideCondition' in effects:
                    vec[Battle_Resources.effects_enum[effects['sideCondition']]] = int(effects['chance'])
                    
        return vec