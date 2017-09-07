
from enum import Enum

class MoveType(Enum):
    NONE = 0
    BATTLE_ACTION = 1
    BATTLE_SWITCH = 2
    
class AIType(Enum):
    RANDOM = 0
    MANUAL = 1
    
class SearchType(Enum):
    
    #Can save a lot but very slowly
    LINEAR_UP = 0
    LINEAR_DOWN = 1
    
    #Saves 50 replays very quickly (some ids are available on the website)
    RECENT = 2
    
class ScrapeReturnCode(Enum):
    
    NOT_FOUND = 0
    ALREADY_EXISTS = 1
    NOT_ENOUGH_TURNS = 2
    SAVED = 3