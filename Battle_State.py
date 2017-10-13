import json
import random
from enum import Enum
from RAIchu_Enums import MoveType, AIType, PredictionType, Player
from Battle_Resources import Battle_Resources
from RAIchu_Utils import RAIchu_Utils
import copy

class Battle_State():
    
    def __init__(self, current_state, move_required, prev_action):
        
        self.info = copy.deepcopy(current_state)
        self.move_required = move_required
        self.opp_move_required = MoveType.BATTLE_ACTION
        
        #prev_action is the set of actions (player, opponent) taken to reach this state. Both are -1 if this is the root
        #of the search tree.
        self.prev_action = prev_action
      
        
    def generate_player_moves(self):
        
        if self.move_required == MoveType.NONE:
            return []
            
        moves = [0] *(RAIchu_Utils.NUM_MOVES + RAIchu_Utils.NUM_POKEMON)
    
        if self.move_required == MoveType.BATTLE_ACTION or self.move_required == MoveType.BATTLE_SWITCH:
            
            for i in range(len(self.info['pokemon'])):
                if i != self.info['active'] and self.info['pokemon'][i]['condition'] != 0:
                    moves[i] = 1
        if self.move_required == MoveType.BATTLE_ACTION:
            for i in range(len(self.info['pokemon'][self.info['active']]['moves'])):
                moves[RAIchu_Utils.NUM_POKEMON+i] = 1
        return moves
        
    def generate_opponent_moves(self):
        #Generates all moves the opponent could make from the current game state. Considers all possible moves
        #of all pokemon the opponent is known to have.
        
        if self.opp_move_required == MoveType.NONE:
            return []
            
        moves = [0] *(len(self.info['opp_pokemon'][self.info['opp_active']]['possible_moves']) + RAIchu_Utils.NUM_POKEMON)
    
        if self.opp_move_required == MoveType.BATTLE_ACTION or self.opp_move_required == MoveType.BATTLE_SWITCH:
            
            for i in range(len(self.info['opp_pokemon'])):
                if i != self.info['opp_active']:
                    if len(self.info['opp_pokemon'][i]) == 0:
                        #Unknown state
                        moves[i] = -1
                    elif self.info['opp_pokemon'][i]['condition'] != 0:
                        moves[i] = 1
                            
        if self.opp_move_required == MoveType.BATTLE_ACTION:
            for i in range(len(self.info['opp_pokemon'][self.info['opp_active']]['possible_moves'])):
                moves[RAIchu_Utils.NUM_POKEMON+i] = 1
        return moves
        
    def generate_next_game_states(self, pred_type):
        
        #Generates all the game states reachable from a single valid action from the current game state
        
        
        next_states = []
        #on a forced switch, only one player will take an action
        if self.move_required == MoveType.BATTLE_SWITCH:
            
            switches = self.generate_player_moves()
            next_states = [-1 for k in range(len(switches))]
            
            for i in range(len(switches)):
                if switches[i] == 1:
                    next_states[i] = self.simulate_action_sequence(i, -1, pred_type)
                    
            
        if self.opp_move_required == MoveType.BATTLE_SWITCH: 
                   
            switches = self.generate_opponent_moves()
            next_states = [-1 for k in range(len(switches))]
            
            for i in range(len(switches)):
                if switches[i] == 1:
                    next_states[i] = self.simulate_action_sequence(-1, i, pred_type)
          
        if self.move_required == MoveType.BATTLE_ACTION and self.opp_move_required == MoveType.BATTLE_ACTION:
            action_sequences = self.generate_action_sequences()
            next_states = action_sequences.copy()
            
            for i in range(len(action_sequences)):
                for j in range(len(action_sequences[0])):
                    
                    if action_sequences[i][j] == 1:
                        next_states[i][j] = self.simulate_action_sequence(i, j, pred_type)
                    else:
                        next_states[i][j] = -1
            
        return next_states
        
    def generate_action_sequences(self):
        
        move_vec = self.generate_player_moves()
        opp_move_vec = self.generate_opponent_moves()
        
        
            
        actions = [[-1]*(len(opp_move_vec)) for k in range((RAIchu_Utils.NUM_MOVES + RAIchu_Utils.NUM_POKEMON))]
        
        for i in range((RAIchu_Utils.NUM_MOVES + RAIchu_Utils.NUM_POKEMON)):
            for j in range(len(opp_move_vec)):
                
                if move_vec[i] == 1:
                    actions[i][j] = opp_move_vec[j]
                    
        return actions
        
        
        
    def simulate_action_sequence(self, move, opp_move, pred_type):
        #Simulate what the game state will be the next turn if the given actions are taken. Returns a new Battle_State
        
        next_state = Battle_State(self.info, MoveType.BATTLE_ACTION, (move, opp_move))
        
        #Switches always happen first. Relative order of switches does not matter.
        if move < RAIchu_Utils.NUM_POKEMON and move >= 0:
            RAIchu_Utils.apply_switch(next_state, Player.SELF, move)
            
            if opp_move >= RAIchu_Utils.NUM_POKEMON:
                RAIchu_Utils.simulate_move(next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']]['possible_moves'][opp_move-RAIchu_Utils.NUM_POKEMON], pred_type)
                
                    
        if opp_move < RAIchu_Utils.NUM_POKEMON and opp_move >= 0:
            RAIchu_Utils.apply_switch(next_state, Player.OPPONENT, opp_move)
            
            
            if move >= RAIchu_Utils.NUM_POKEMON:
                RAIchu_Utils.simulate_move(next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']]['moves'][move-RAIchu_Utils.NUM_POKEMON], pred_type)
                
          #if both sides attack, the pokemon with a higher speed stat acts first. If the pokemon with lower speed has no hp left after
          #the pokemon with higher speed attacks, they will not get to attack and will need to switch.
          
        if move >= RAIchu_Utils.NUM_POKEMON and opp_move >= RAIchu_Utils.NUM_POKEMON:
            if next_state.info['opp_pokemon'][next_state.info['opp_active']]['stats']['spe'] > next_state.info['pokemon'][next_state.info['active']]['stats']['spe']:
                
                 RAIchu_Utils.simulate_move(next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']]['possible_moves'][opp_move-RAIchu_Utils.NUM_POKEMON], pred_type)
                 
                 if next_state.info['pokemon'][next_state.info['active']]['condition'] != 0:
                    RAIchu_Utils.simulate_move(next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']]['moves'][move-RAIchu_Utils.NUM_POKEMON], pred_type)
                    
            else:
                
                RAIchu_Utils.simulate_move(next_state.info['pokemon'][next_state.info['active']], next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']]['moves'][move-RAIchu_Utils.NUM_POKEMON], pred_type)
                 
                if next_state.info['opp_pokemon'][next_state.info['opp_active']]['condition'] != 0: 
                    RAIchu_Utils.simulate_move(next_state.info['opp_pokemon'][next_state.info['opp_active']], next_state.info['pokemon'][next_state.info['active']],next_state.info['opp_pokemon'][next_state.info['opp_active']]['possible_moves'][opp_move-RAIchu_Utils.NUM_POKEMON], pred_type)
                    
        if next_state.info['pokemon'][next_state.info['active']]['condition'] == 0:
            next_state.move_required = MoveType.BATTLE_SWITCH
            next_state.opp_move_required = MoveType.NONE
        
        if next_state.info['opp_pokemon'][next_state.info['opp_active']]['condition'] == 0:
            next_state.move_required = MoveType.NONE
            next_state.opp_move_required = MoveType.BATTLE_SWITCH
            
            #If both pokemon faint on the same turn due to status or recoil
            if next_state.info['pokemon'][next_state.info['active']]['condition'] == 0:
                next_state.move_required = MoveType.BATTLE_SWITCH
            
            
        return next_state
                
            
    
    
        
        
        
        
        
        
        
        
        
        
        
        
        
    
        
        
        