import json
import random
from enum import Enum
from RAIchu_Enums import MoveType, AIType, PredictionType
from BattleMove import BattleMove
from RAIchu_Utils import RAIchu_Utils

class RAIchu_Utils_State():
    
    def __init__(self, game_id, current_state, depth, max_depth, move_required, prev_action):
        
        self.info = current_state
        self.id = game_id
        self.depth = depth
        self.max_depth = max_depth
        self.move_required = move_required
        self.opp_move_required = MoveType.RAIchu_Utils_ACTION
        
        #prev_action is the set of actions (player, opponent) taken to reach this state. Both are -1 if this is the root
        #of the search tree.
        self.prev_action = prev_action
      
        
    def generate_player_moves(self):
        
        if self.opp_move_required == MoveType.RAIchu_Utils_SWITCH:
            return []
            
        moves = [0] *(RAIchu_Utils.NUM_MOVES + RAIchu_Utils.NUM_POKEMON-1)
    
        if self.move_required == MoveType.RAIchu_Utils_ACTION or self.move_required == MoveType.RAIchu_Utils_SWITCH:
            
            for i in range(len(self.info['pokemon'])):
                if i != self.info['active'] and self.info['pokemon'][i]['condition'] != 0:
                    moves[i] = 1
        if self.move_required == MoveType.RAIchu_Utils_ACTION:
            for i in range(len(self.info['pokemon'][self.info['active']]['moves'])):
                moves[RAIchu_Utils.NUM_POKEMON-1+i] = 1
        return moves
    def generate_opponent_moves(self):
        #Generates all moves the opponent could make from the current game state. Considers all possible moves
        #of all pokemon the opponent is known to have.
        
        if self.move_required == MoveType.RAIchu_Utils_SWITCH:
            return []
            
        moves = [0] *(len(self.info['opp_pokemon'][self.info['active']]['possible_moves']) + RAIchu_Utils.NUM_POKEMON-1)
    
        if self.opp_move_required == MoveType.RAIchu_Utils_ACTION or self.opp_move_required == MoveType.RAIchu_Utils_SWITCH:
            
            for i in range(len(self.info['opp_pokemon'])):
                if i != self.info['active']:
                    if len(self.info['opp_pokemon'][i]) == 0:
                        #Unknown state
                        moves[i] = -1
                    elif self.info['opp_pokemon'][i]['condition'] != 0:
                        moves[i] = 1
                            
        if self.opp_move_required == MoveType.RAIchu_Utils_ACTION:
            for i in range(len(self.info['opp_pokemon'][self.info['active']]['possible_moves'])):
                moves[RAIchu_Utils.NUM_POKEMON-1+i] = 1
        return moves, switches
        
    def generate_next_game_states(self, pred_type):
        
        #Generates all the game states reachable from a single valid action from the current game state
        
        
        next_states = []
        #on a forced switch, only one player will take an action
        if self.move_required == MoveType.RAIchu_Utils_SWITCH:
            
            switches = self.generate_player_moves()
            
            for n in range(len(switches)):
                if switches[i] == 1:
                    next_states.append(self.simulate_action_sequence(i, -1, pred_type))
            
        elif self.opp_move_required == MoveType.RAIchu_Utils_SWITCH: 
                   
            switches = self.generate_opponent_moves()
            
            for i in range(len(switches)):
                if switches[i] == 1:
                    next_states.append(self.simulate_action_sequence(-1, i, pred_type))
          
        else:
            action_sequences = self.generate_action_sequences()
            next_states = action_sequences.copy()
            
            for i in range(len(action_sequences)):
                for j in range(len(action_sequences[0])):
                    
                    if action_sequences[i][j] == 1:
                        next_states[i][j] = self.simulate_action_sequence(i, j, pred_type)
                    else:
                        next_states[i][j] = 0
            
        return next_states
        
    def generate_action_sequences(self):
        
        move_vec = self.generate_player_moves()
        opp_move_vec = self.generate_opponent_moves()
        
        
            
        actions = [[0]*(len(opp_move_vec)) for k in range((RAIchu_Utils.NUM_MOVES + RAIchu_Utils.NUM_POKEMON-1))]
        
        for i in range((RAIchu_Utils.NUM_MOVES + RAIchu_Utils.NUM_POKEMON-1)):
            for j in range(len(opp_move_vec)):
                
                if move_vec[i] == 1:
                    actions[i][j] = opp_move_vec[j]
                    
        return actions
        
        
        
    def simulate_action_sequence(self, move, opp_move, pred_type):
        #Simulate what the game state will be the next turn if the given actions are taken. Returns a new Battle_State
        
        next_state = RAIchu_Utils_State(game_id, self.info, self.depth+1, max_depth, MoveType.RAIchu_Utils_ACTION, (move, opp_move))
        
        #Switches always happen first. Relative order of switches does not matter.
        if move < RAIchu_Utils.NUM_POKEMON and move >= 0:
            next_state.info['active'] = move
            
            if opp_move >= RAIchu_Utils.NUM_POKEMON:
                next_state.info['pokemon'][next_state.info['active']] = RAIchu_Utils.simulate_move(next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']]['possible_moves'][opp_move], pred_type)
            
                if next_state.info['pokemon'][next_state.info['active']]['condition'] == 0:
                    self.move_required = MoveType.RAIchu_Utils_SWITCH
                    
        if opp_move < RAIchu_Utils.NUM_POKEMON and opp_move >= 0:
            next_state.info['opp_active'] = move
            
            
            if opp_move >= RAIchu_Utils.NUM_POKEMON:
                next_state.info['opp_pokemon'][next_state.info['opp_active']] = RAIchu_Utils.simulate_move(next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']]['moves'][move], pred_type)
                
                if next_state.info['opp_pokemon'][next_state.info['opp_active']]['condition'] == 0:
                    self.opp_move_required = MoveType.RAIchu_Utils_SWITCH
                
          #if both sides attack, the pokemon with a higher speed stat acts first. If the pokemon with lower speed has no hp left after
          #the pokemon with higher speed attacks, they will not get to attack and will need to switch.
          
        if move >= RAIchu_Utils.NUM_POKEMON and opp_move >= RAIchu_Utils.NUM_POKEMON:
            if next_state.info['opp_pokemon'][next_state.info['opp_active']]['stats']['spe'] > next_state.info['pokemon'][next_state.info['active']]['stats']['spe']:
                
                 next_state.info['pokemon'][next_state.info['active']] = RAIchu_Utils.simulate_move(next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']]['possible_moves'][opp_move], pred_type)
                 
                 if next_state.info['pokemon'][next_state.info['active']]['condition'] == 0:
                    self.move_required = MoveType.RAIchu_Utils_SWITCH
                 else:
                        
                    next_state.info['opp_pokemon'][next_state.info['opp_active']] = RAIchu_Utils.simulate_move(next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']]['moves'][move], pred_type)
                    
                    if next_state.info['opp_pokemon'][next_state.info['opp_active']]['condition'] == 0:
                        self.opp_move_required = MoveType.RAIchu_Utils_SWITCH
                
            else:
                
                 next_state.info['opp_pokemon'][next_state.info['opp_active']] = RAIchu_Utils.simulate_move(next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']]['moves'][move], pred_type)
                 
                 if next_state.info['opp_pokemon'][next_state.info['opp_active']]['condition'] == 0:
                    self.opp_move_required = MoveType.RAIchu_Utils_SWITCH
                 else:
                        
                    next_state.info['pokemon'][next_state.info['iactive']] = RAIchu_Utils.simulate_move(next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']],next_state.info['opp_pokemon'][next_state.info['opp_active']]['possible_moves'][opp_move], pred_type)
                    if next_state.info['pokemon'][next_state.info['active']]['condition'] == 0:
                        self.move_required = MoveType.RAIchu_Utils_SWITCH
                
        return next_state
                
            
    
    
        
        
        
        
        
        
        
        
        
        
        
        
        
    
        
        
        