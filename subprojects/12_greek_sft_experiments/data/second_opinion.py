#!/usr/bin/env python3
"""Sol second opinion on Luna's "wrong answer" drops (quality 1, no identity frame). Resumable, one line per row.
Usage: python3 second_opinion.py <export_dir> <labels_dir> <workers> block1 [block2 ...]
Env: SOL_MODEL (default gpt-5.6-sol), SOL_EFFORT (default medium)."""
import json, sys, os, time, collections, concurrent.futures as cf, threading
os.environ['TERRA_MODEL'] = os.environ.get('SOL_MODEL', 'gpt-5.6-sol'); os.environ['TERRA_EFFORT'] = os.environ.get('SOL_EFFORT', 'medium'); os.environ.setdefault('TERRA_TIER', 'default')
sys.argv, _argv = [sys.argv[0], '/dev/null', '/tmp/second_opinion_tmp'], sys.argv
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'terra_probe.py')).read()
exec(_src[:_src.index('rows = [json.loads(l)')])  # RUBRIC, SCHEMA, MODEL, EFFORT, TIER, label()
sys.argv = _argv
EXP, LAB, W = sys.argv[1], sys.argv[2], int(sys.argv[3]); BLOCKS = sys.argv[4:]; lock = threading.Lock()
for block in BLOCKS:
    luna = {}
    for l in open(f'{LAB}/{block}.labels.jsonl'):
        j = json.loads(l)
        if j.get('quality') == 1 and j.get('frame_type') in (None, 'none') and j.get('disposition') == 'drop': luna[j['id']] = j
    dst = f'{LAB}/{block}.sol.jsonl'; done = set()
    if os.path.exists(dst):
        for l in open(dst): done.add(json.loads(l)['id'])
    rows = [r for r in (json.loads(l) for l in open(f'{EXP}/{block}.jsonl')) if r['id'] in luna and r['id'] not in done]
    print(f'== {block}: {len(luna)} Luna quality-1 drops, {len(done)} already re-judged, {len(rows)} to go, {W} workers, {MODEL}/{EFFORT}/{TIER}', flush=True)
    if not rows: continue
    t0 = time.time(); n = 0; stats = collections.Counter()
    def work(r):
        j = label(r); j['id'] = r['id']; j['luna_why'] = luna[r['id']].get('why'); return j
    with open(dst, 'a') as fh, cf.ThreadPoolExecutor(W) as ex:
        for j in ex.map(work, rows):
            with lock:
                fh.write(json.dumps(j, ensure_ascii=False) + '\n'); fh.flush(); n += 1
                stats['sol_confirms_drop' if j.get('quality') == 1 else ('sol_overturns' if j.get('quality') in (2, 3) else 'parse_fail')] += 1
                if n % 50 == 0 or n == len(rows):
                    el = time.time() - t0; print(f'{block}: {n}/{len(rows)} {round(3600*n/el)} rows/h {dict(stats)} elapsed {round(el/60)} min', flush=True)
    print(f'== {block} DONE', flush=True)
print('ALL DONE', flush=True)
