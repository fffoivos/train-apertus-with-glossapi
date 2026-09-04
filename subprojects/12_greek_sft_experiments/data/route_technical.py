#!/usr/bin/env python3
"""Category routing: rows that Luna labelled as code, math or reasoning inside a Luna block are judged again by Sol,
and Sol's label replaces Luna's for those rows (written to <block>.sol_routed.jsonl; the merge step prefers it).
Resumable. Usage: python3 route_technical.py <export_dir> <labels_dir> <workers> block1 [block2 ...]"""
import json, sys, os, time, collections, concurrent.futures as cf, threading
os.environ['TERRA_MODEL'] = os.environ.get('SOL_MODEL', 'gpt-5.6-sol'); os.environ['TERRA_EFFORT'] = os.environ.get('SOL_EFFORT', 'medium'); os.environ.setdefault('TERRA_TIER', 'default')
sys.argv, _argv = [sys.argv[0], '/dev/null', '/tmp/route_technical_tmp'], sys.argv
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'terra_probe.py')).read()
exec(_src[:_src.index('rows = [json.loads(l)')])
sys.argv = _argv
EXP, LAB, W = sys.argv[1], sys.argv[2], int(sys.argv[3]); BLOCKS = sys.argv[4:]; lock = threading.Lock()
TECH = {'code', 'math', 'reasoning'}
for block in BLOCKS:
    src = f'{LAB}/{block}.labels.jsonl'
    if not os.path.exists(src): print(f'== {block}: no Luna labels yet', flush=True); continue
    want = {}
    for l in open(src):
        j = json.loads(l)
        if j.get('skill') in TECH and j.get('judge', 'gpt-5.6-luna') != 'gpt-5.6-sol': want[j['id']] = j
    dst = f'{LAB}/{block}.sol_routed.jsonl'; done = set()
    if os.path.exists(dst):
        for l in open(dst): done.add(json.loads(l)['id'])
    rows = [r for r in (json.loads(l) for l in open(f'{EXP}/{block}.jsonl')) if r['id'] in want and r['id'] not in done]
    print(f'== {block}: {len(want)} technical rows by Luna, {len(done)} already Sol-judged, {len(rows)} to go', flush=True)
    if not rows: continue
    t0 = time.time(); n = 0; stats = collections.Counter()
    def work(r):
        j = label(r); j['id'] = r['id']; j['judge'] = MODEL; j['luna_disposition'] = want[r['id']].get('disposition'); return j
    with open(dst, 'a') as fh, cf.ThreadPoolExecutor(W) as ex:
        for j in ex.map(work, rows):
            with lock:
                fh.write(json.dumps(j, ensure_ascii=False) + '\n'); fh.flush(); n += 1
                stats[f"luna={j['luna_disposition']}->sol={j.get('disposition')}"] += 1
                if n % 100 == 0 or n == len(rows):
                    el = time.time() - t0; print(f'{block}: {n}/{len(rows)} {round(3600*n/el)} rows/h {dict(stats)} elapsed {round(el/60)} min', flush=True)
    print(f'== {block} DONE', flush=True)
print('ALL DONE', flush=True)
