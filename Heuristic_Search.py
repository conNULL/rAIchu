from RAIchu_Utils import RAIchu_Utils
from Battle_State import Battle_State
from RAIchu_Enums import MoveType, PredictionType

class Heuristic_Search():
    
    MAX_SCORE = 2401
    MAX_DEPTH = 2
    
    def get_move(state, move_required, pred_type):
        
        game_state = Battle_State(state, move_required, (-1, -1))
        score, move = Heuristic_Search.evaluate_game_state(game_state, 0, Heuristic_Search.MAX_DEPTH, pred_type)
        # if move >= RAIchu_Utils.NUM_POKEMON:
            
        #     return ('move ' + str(move+RAIchu_Utils.NUM_POKEMON))
        # return ('switch ' + str(move))
        
        print('SCORE', score)
        return move
    
    
    
    def evaluate_game_state(state, depth, max_depth, pred_type):
        
        #Returns the value of a game state based on reachable states and heuristics of the current state and the move used to get there.
        
        if depth == max_depth:
            return Heuristic_Search.get_score(state), state.prev_action[0]
            
        
        next_states = state.generate_next_game_states(pred_type)
        
        #the best score for the moving player is the maximum one if we are moving, and the minimum if the opponent is moving
        if state.move_required == MoveType.BATTLE_SWITCH:
            
            max_score = -1
            for i in range(len(next_states)):
                score, index = Heuristic_Search.evaluate_game_state(next_states[i], depth+1, max_depth, pred_type)
                if score > max_score:
                    max_score = score
                    best_index = i
                    
            return max_score, best_index
            
            
        if state.opp_move_required == MoveType.BATTLE_SWITCH:
            
            min_score = Heuristic_Search.MAX_SCORE
            for i in range(len(next_states)):
                score, index = Heuristic_Search.evaluate_game_state(next_states[i], depth+1, max_depth, pred_type)
                if score < min_score:
                    min_score = score
                    best_index = i
                    
            return min_score, best_index
        
        #If both players are moving, the best score is the minimum score possible if we choose a move to maximize the minimum possible score given any opponent move.
        max_min_score = -1
        max_min_index = -1
        for i in range(len(next_states)):
            min_score = Heuristic_Search.MAX_SCORE
            for j in range(len(next_states[0])):
                
                if next_states[i][j] != -1:
                    
                    score, index = Heuristic_Search.evaluate_game_state(next_states[i][j], depth+1, max_depth, pred_type)
                    
                    if score < min_score:
                        min_score = score
                    
            if min_score > max_min_score and min_score < Heuristic_Search.MAX_SCORE:
                max_min_score = min_score
                max_min_index = i
                
            #no possible moves left, the game is over or there is too much uncertainty to make further predictions
            if max_min_index == -1:
                return Heuristic_Search.get_score(state), state.prev_action[0]
        return max_min_score, max_min_index
        
    def get_score(state):
        
        score = 1200
        for pok in state.info['opp_pokemon']:
            if len(pok) == 0:
                score -= 200
            elif pok['condition'] != 0:
                score -= 100 + pok['condition']
                
        for pok in state.info['pokemon']:
            
            if pok['condition'] != 0:
                score += 100 + pok['condition']
            
            
        return score
        
        
        
        
        
        
        
        
        
        
            
    
    