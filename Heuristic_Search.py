from RAIchu_Utils import RAIchu_Utils
from Battle_State import Battle_State
from RAIchu_Enums import MoveType, PredictionType

class Heuristic_Search():
    MAX_SCORE = 2401
    MAX_DEPTH = 3
    
    def get_move(state, move_required, pred_type):
        
        game_state = Battle_State(state, move_required, (-2, -2))
        score, move = Heuristic_Search.evaluate_game_state(game_state, 0, Heuristic_Search.MAX_DEPTH, pred_type, Heuristic_Search.MAX_SCORE)
        # if move >= RAIchu_Utils.NUM_POKEMON:
            
        #     return ('move ' + str(move+RAIchu_Utils.NUM_POKEMON))
        # return ('switch ' + str(move))
        
        print('SCORE', score)
        return move
    
    
    
    def evaluate_game_state(state, depth, max_depth, pred_type, cur_min_score):
        
        #Returns the value of a game state based on reachable states and heuristics of the current state and the move used to get there.
        
        if depth == max_depth:
            return Heuristic_Search.get_score(state), state.prev_action[0]
            
        
        next_states = state.generate_next_game_states(pred_type)
        
        #the best score for the moving player is the maximum one if we are moving, and the minimum if the opponent is moving
        if state.move_required == MoveType.BATTLE_SWITCH:
            
            max_score = -1
            best_index = -1
            for i in range(len(next_states)):
                if next_states[i] != -1:
                    score, index = Heuristic_Search.evaluate_game_state(next_states[i], depth+1, max_depth, pred_type, Heuristic_Search.MAX_SCORE)
                    if score > max_score:
                        max_score = score
                        best_index = i
                        
                        if score > cur_min_score:
                            return Heuristic_Search.MAX_SCORE, -1
            
            if best_index == -1:
                return Heuristic_Search.get_score(state), state.prev_action[0]
            return max_score, best_index
            
            
        if state.opp_move_required == MoveType.BATTLE_SWITCH:
            min_score = Heuristic_Search.MAX_SCORE
            best_index = -1
            for i in range(len(next_states)):
                if next_states[i] != -1:
                    score, index = Heuristic_Search.evaluate_game_state(next_states[i], depth+1, max_depth, pred_type, min_score)
                    if score < min_score:
                        min_score = score
                        best_index = i
            
            if best_index == -1:
                return Heuristic_Search.get_score(state), state.prev_action[0]
            return min_score, best_index
        
        #If both players are moving, the best score is the minimum score possible if we choose a move to maximize the minimum possible score given any opponent move.
        max_min_score = -1
        max_min_index = -1
        
        for i in range(len(next_states)):
            min_score = Heuristic_Search.MAX_SCORE
            for j in range(len(next_states[0])):
                
                if next_states[i][j] != -1:
                    
                    score, index = Heuristic_Search.evaluate_game_state(next_states[i][j], depth+1, max_depth, pred_type, min_score)

                    if score < min_score:
                        min_score = score
                        
                    #found a move the opponent can make that would give a worse score than the minimum score we got get from making another more. This move can't be the best so dont bother checking other possibilities.
                    if score < max_min_score:
                        break
                        
            if min_score > max_min_score and min_score < Heuristic_Search.MAX_SCORE:
                max_min_score = min_score
                max_min_index = i
                
            #Found an action takeable from this state that results in a higher score in the previous state than the minimum score possible from taking the same action.
            #Since we only care about choosing the move that maximizes the minimum possible score, and this state does not result in the minimum score our selected action, it is not worth considering this path. It relies on the opponent playing non-optimally. 
            if max_min_score > cur_min_score:
                return Heuristic_Search.MAX_SCORE, -1
                
                
        #no possible moves left to check, the game is over or there is too much uncertainty to make further predictions
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
        
        
        
        
        
        
        
        
        
        
            
    
    