import json

class BattleMove():
    
      
    def initialize():
        f = open('move_effects_enum_dict.txt', 'r')
        BattleMove.effects_enum = json.load(f)
        f.close()
        
        f = open('move_effects_dict.txt', 'r')
        BattleMove.effects = json.load(f)
        f.close()
        