#!/usr/bin/env python3
"""Core-subset annotation driver: Luna (rubric v3) over exported blocks, resumable, one output line per row.
Usage: python3 annotate_core.py <export_dir> <out_dir> <workers> block1 [block2 ...]
Env: TERRA_MODEL/TERRA_EFFORT/TERRA_TIER as in terra_probe.py (defaults: gpt-5.6-luna, medium, default tier)."""
import json, sys, os, time, collections, concurrent.futures as cf, threading
os.environ.setdefault('TERRA_TIER', 'default')
sys.argv, _argv = [sys.argv[0], '/dev/null', '/tmp/annotate_core_probe_tmp'], sys.argv  # terra_probe reads argv at import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'terra_probe.py')).read()
exec(_src[:_src.index('rows = [json.loads(l)')])  # RUBRIC, SCHEMA, MODEL, EFFORT, TIER, label()
sys.argv = _argv
EXP, OUT, W = sys.argv[1], sys.argv[2], int(sys.argv[3]); BLOCKS = sys.argv[4:]
os.makedirs(OUT, exist_ok=True); lock = threading.Lock()

for block in BLOCKS:
    src = f'{EXP}/{block}.jsonl'; dst = f'{OUT}/{block}.labels.jsonl'
    done = set()
    if os.path.exists(dst):
        for l in open(dst):
            try: done.add(json.loads(l)['id'])
            except Exception: pass
    rows = []
    for l in open(src):
        r = json.loads(l)
        if r['id'] not in done: rows.append(r)
    print(f'== {block}: {len(done)} done, {len(rows)} to go, {W} workers, {MODEL}/{EFFORT}/{TIER}', flush=True)
    if not rows: continue
    t0 = time.time(); n = 0; stats = collections.Counter()
    def work(r):
        j = label(r); j['id'] = r['id']; return j
    with open(dst, 'a') as fh, cf.ThreadPoolExecutor(W) as ex:
        for j in ex.map(work, rows):
            with lock:
                fh.write(json.dumps(j, ensure_ascii=False) + '\n'); fh.flush(); n += 1
                stats[j.get('disposition') or 'PARSE_FAIL'] += 1
                if n % 200 == 0 or n == len(rows):
                    el = time.time() - t0
                    print(f'{block}: {n}/{len(rows)} {round(3600*n/el)} rows/h {dict(stats)} elapsed {round(el/60)} min', flush=True)
    print(f'== {block} DONE {n} rows in {round((time.time()-t0)/60)} min', flush=True)
print('ALL DONE', flush=True)
