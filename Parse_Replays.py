import os

RAW_FILE_BASE = 'REPLAY_RAW_'
RAW_DIRECTORY = 'gen_7_random_battle_replays'

NUM_TO_PARSE = 1

replays = os.listdir(RAW_DIRECTORY)
 
for i in range(NUM_TO_PARSE):
    replay = replays[i]
    lines = open(RAW_DIRECTORY + '/' + replay, 'r').readlines()
    log = ''
    for line in lines:
        log += line
    temp = log.count('p1a')
    temp2 = []
    ind = 0
    prev = 0
    for j in range(temp):
        prev = ind
        ind = log.index('p1a', prev)+4
        temp2.append(log[ind:log.index('|', ind)].replace('\n', ''))
    temp2 = list(set(temp2))
    turns = log.split('\n\n')
    for turn in turns:
        print(turn)