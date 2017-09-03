from pyquery import PyQuery as pq
import os
import requests
from enum import Enum

class Direction(Enum):
    UP = 0
    DOWN = 1
    
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
START_BATTLE_ID = 624883091
DIRECTION = Direction.DOWN
NUM_TO_SAVE = 100
REPLAYS_TO_SAVE = 100

if not os.path.exists(OUTPUT_DIRECTORY):
    os.mkdir(OUTPUT_DIRECTORY)
    
if DIRECTION == Direction.UP:
    inc = 1
else:
    inc = -1
    
saved = 0
replay_id = START_BATTLE_ID
while saved < NUM_TO_SAVE:
    
    if save_replay_text(replay_id, BASE_URL, OUTPUT_DIRECTORY+'/'+OUTPUT_FILE_BASE):
        saved += 1
    replay_id += inc
    
print('done! Last Saved Replay: ', replay_id)
#update the START_BATTLE_ID when finished to continue next time. 