#!/usr/bin/env python3
"""Turn a zebra_check.py log into a verified keep-list of puzzle row ids.
Usage: python3 puzzle_keep_list.py <puzzles.jsonl> <check.log> <out_dir>
Writes keep_ids.txt (checker agrees), wrong_ids.txt (checker disagrees), unchecked_ids.txt (unparsed or ambiguous) and a summary."""
import json, sys, re, os, collections
rows = [json.loads(l) for l in open(sys.argv[1])]; log = open(sys.argv[2]).read().splitlines(); out = sys.argv[3]; os.makedirs(out, exist_ok=True)
flag = {}
for l in log:
    m = re.match(r'^(\d+) (DISAGREE|unparsed|\d+ solutions|agree)', l)
    if m: flag[int(m.group(1))] = 'wrong' if m.group(2) == 'DISAGREE' else ('keep' if m.group(2) == 'agree' else 'unchecked')
# rows that pass print nothing unless a label file was given, so absent = keep
status = {i: flag.get(i, 'keep') for i in range(len(rows))}
c = collections.Counter(status.values()); print(dict(c), 'of', len(rows))
for k in ('keep', 'wrong', 'unchecked'):
    with open(f'{out}/{k}_ids.txt', 'w') as f:
        for i, s in status.items():
            if s == k: f.write(rows[i]['id'] + '\n')
json.dump(dict(counts=dict(c), total=len(rows), source=sys.argv[1]), open(f'{out}/summary.json', 'w'), indent=1)
