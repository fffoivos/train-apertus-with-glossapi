#!/usr/bin/env python3
"""Judge prompts whose sample budget exceeds four: split each prompt's samples into batches of four (by k), judge every
batch as its own 4-way comparison with judge_rank4.py, then merge back with the original k values.
Usage: python3 data/rlhf/judge_batches.py <prompts.jsonl> <samples.jsonl> <out judged.jsonl> [judge_rank4 args...]
Output rows carry the original prompt id, `batch` (0-based), `ranking_k` in original k, `by_k` keyed by original k."""
import json, sys, subprocess, pathlib, collections, os
HERE = pathlib.Path(__file__).resolve().parent
prompts_f, samples_f, out_f, *rest = sys.argv[1:]
prompts = {json.loads(l)['id']: json.loads(l) for l in open(prompts_f) if l.strip()}
samples = collections.defaultdict(dict)
for l in open(samples_f):
    if not l.strip(): continue
    s = json.loads(l)
    if s.get('k', -1) >= 0 and s['id'] in prompts: samples[s['id']][s['k']] = s
work = pathlib.Path(out_f).with_suffix(''); work.mkdir(exist_ok=True)
pf, sf = work / 'batched_prompts.jsonl', work / 'batched_samples.jsonl'; keymap = {}
with open(pf, 'w') as hp, open(sf, 'w') as hs:
    for pid, ks in samples.items():
        ks = sorted(ks)
        for b in range(len(ks) // 4):
            bid = f'{pid}#b{b}'; hp.write(json.dumps(dict(prompts[pid], id=bid), ensure_ascii=False) + '\n')
            for j, k in enumerate(ks[b * 4:(b + 1) * 4]):
                hs.write(json.dumps(dict(samples[pid][k], id=bid, k=j), ensure_ascii=False) + '\n'); keymap[(bid, j)] = k
        if len(ks) % 4: print(f'{pid}: {len(ks) % 4} sample(s) left over (not a multiple of 4)', file=sys.stderr)
jf = work / 'batched_judged.jsonl'
subprocess.run([sys.executable, str(HERE / 'judge_rank4.py'), str(pf), str(sf), str(jf), *rest], check=True)
n = 0
with open(out_f, 'w') as h:
    for l in open(jf):
        r = json.loads(l); bid = r['id']; pid, b = bid.rsplit('#b', 1); r['id'] = pid; r['batch'] = int(b)
        if 'ranking_k' in r:
            r['order'] = [keymap[(bid, j)] for j in r['order']]; r['ranking_k'] = [keymap[(bid, j)] for j in r['ranking_k']]
            r['by_k'] = {str(keymap[(bid, int(j))]): v for j, v in r['by_k'].items()}
        h.write(json.dumps(r, ensure_ascii=False) + '\n'); n += 1
print(f'MERGED {n} judged batches -> {out_f}')
