from pyquery import PyQuery as pq
from os import path
import requests


def save_replay_text(battle_id, base_url, base_ofile):
    
    id = str(battle_id)
    filename = base_ofile + id + '.txt'
    if path.isfile(filename):
        print(filename, 'already exists!')
        return
    
    log = pq(base_url + id)[0].find_class('log')[0].text.split('|turn|')
    file = open(filename, 'w', encoding = 'utf-8')
    for line in log:
        if line[0] != '|':
            file.write('\n')
        file.write(line)
    file.close()
    


BASE_URL = 'https://replay.pokemonshowdown.com/gen7randombattle-'
OUTPUT_FILE_BASE = 'REPLAY_RAW_'
START_BATTLE_ID = 624883091

save_replay_text(START_BATTLE_ID, BASE_URL, OUTPUT_FILE_BASE)