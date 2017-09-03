from pyquery import PyQuery as pq
import os
import requests
from enum import Enum
import time

class SearchType(Enum):
    
    #Can save a lot but very slowly
    LINEAR_UP = 0
    LINEAR_DOWN = 1
    
    #Saves 50 replays very quickly (some ids are available on the website)
    RECENT = 2
    
def save_replay_text(battle_id, base_url, base_ofile):
    
    id = str(battle_id)
    r = requests.get(base_url + id)
    
    if r.status_code != 200:
        #print('replay for', battle_id, 'does not exist!')
        return False
    filename = base_ofile + id + '.txt'
    if os.path.isfile(filename):
        print(filename, 'already exists!')
        return False
    
    log = pq(base_url + id)[0].find_class('log')[0].text.split('|turn|')
    file = open(filename, 'w', encoding = 'utf-8')
    for line in log:
        if line[0] != '|':
            file.write('\n')
        file.write(line)
    file.close()
    print('replay for', battle_id, 'saved!')
    return True


BASE_URL = 'https://replay.pokemonshowdown.com/gen7randombattle-'
OUTPUT_FILE_BASE = 'REPLAY_RAW_'
OUTPUT_DIRECTORY = 'gen_7_random_battle_replays'

#Starting point for linear searches
START_BATTLE_ID = 624870638

#Recent or Linear
TYPE = SearchType.RECENT

NUM_TO_SAVE = 10 #minimum

#Time to wait before doing recent check again
WAIT_TIME = 90 #15 minutes

#Maximum number of ids to try in a linear search
MAX_TO_CHECK = 10000

REPLAYS_TO_SAVE = 100

if not os.path.exists(OUTPUT_DIRECTORY):
    os.mkdir(OUTPUT_DIRECTORY)

        
saved = 0
if TYPE == SearchType.LINEAR_UP or TYPE == SearchType.LINEAR_DOWN:
    if TYPE == SearchType.LINEAR_UP:
        inc = 1
    else:
        inc = -1
        
    tried = 0
    replay_id = START_BATTLE_ID
    while saved < NUM_TO_SAVE and tried < MAX_TO_CHECK:
        
        tried += 1
        if save_replay_text(replay_id, BASE_URL, OUTPUT_DIRECTORY+'/'+OUTPUT_FILE_BASE):
            saved += 1
        replay_id += inc
 
elif TYPE == SearchType.RECENT:
    done = False
    while not done:
        args = {'output': 'html', 'format' : 'gen7randombattle'}
        html = requests.get('https://replay.pokemonshowdown.com/search/', params=args)
        
        ids = [k[:9] for k in html.text.split('href="/gen7randombattle-')[1:]]
        
        for replay_id in ids:
            if save_replay_text(replay_id, BASE_URL, OUTPUT_DIRECTORY+'/'+OUTPUT_FILE_BASE):
                saved += 1
            else:
                replay_id = ids[saved-1]
                break
        #Only wait if there more replays need to be saved.
        if saved < NUM_TO_SAVE:
            time.sleep(WAIT_TIME)
        else:
            done = True
        
            
        
print('done! Last Saved Replay: ', replay_id)
#update the START_BATTLE_ID when finished to continue next time. 