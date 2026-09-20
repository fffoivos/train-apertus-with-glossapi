#!/usr/bin/env python3
"""Assemble the round-1 prompt pool under the programme distribution (Codex design: dialogue 35 / everyday 25 / IF 15 / factual 10 / safety 10 / maths 5;
languages el 70 / en 20 / fr,de,es,it,pt 2 each). Forum credits first (natural Greek requests, provenance kept), then generated prompts from the
generator release, then our own verifiable pools for maths and IF where the release does not cover them. Reports target vs filled per cell.
Usage: python3 data/rlhf/assemble_round1_pool.py <out.jsonl> --size 300 [--forum data/rlhf/pool/forum_pilot_v3.jsonl] [--generated <release output.jsonl>] [--if <if prompts>] [--math <math prompts>] [--safety <safety prompts>] [--seed 916]"""
import json, argparse, random, collections, hashlib, math
from fractions import Fraction
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--size', type=int, default=300); ap.add_argument('--forum', default='data/rlhf/pool/forum_pilot_v3.jsonl'); ap.add_argument('--generated'); ap.add_argument('--if_', dest='if_file'); ap.add_argument('--math'); ap.add_argument('--safety'); ap.add_argument('--seed', type=int, default=916); a = ap.parse_args()
rng = random.Random(a.seed)
PURPOSES = {'dialogue': 35, 'everyday': 25, 'if': 15, 'factual': 10, 'safety': 10, 'math': 5}; LANGS = {'el': 70, 'en': 20, 'fr': 2, 'de': 2, 'es': 2, 'it': 2, 'pt': 2}
def apportion(w, n):
    tot = sum(w.values()); raw = {k: Fraction(v) * n / tot for k, v in w.items()}; out = {k: int(v) for k, v in raw.items()}
    for k in sorted(w, key=lambda k: -(raw[k] - out[k]))[:n - sum(out.values())]: out[k] += 1
    return out
targets = {}
for p, n in apportion(PURPOSES, a.size).items():
    for l, m in apportion(LANGS, n).items(): targets[(p, l)] = m
# forum credits: Greek natural requests → everyday or factual by task_type (proposal on the board; Codex may override the mapping)
MAP = {'advice': 'everyday', 'opinion': 'everyday', 'share': 'everyday', 'translation': 'everyday', 'other': 'everyday', 'question': 'factual', 'explanation': 'factual', 'calculation': 'factual'}
pools = collections.defaultdict(list)
for l in open(a.forum):
    r = json.loads(l); cell = (MAP.get(r.get('task_type') or 'other', 'everyday'), 'el'); pools[cell].append(dict(r, provenance='forum', n=4))
def load(path, purpose_key='purpose', lang_key='language', default_n=4):
    if not path: return
    for l in open(path):
        r = json.loads(l); cell = (r.get(purpose_key) or r.get('slice') or '?', r.get(lang_key) or 'el'); pools[cell].append(dict(r, n=r.get('n', default_n)))
load(a.generated); load(a.if_file, default_n=8); load(a.math, default_n=16); load(a.safety)
out = []; fill = {}; deficit = {}
for cell, m in targets.items():
    rows = pools.get(cell, []); rng.shuffle(rows); take = rows[:m]; out += [dict(r, cell=f'{cell[0]}/{cell[1]}') for r in take]; fill[cell] = len(take); deficit[cell] = m - len(take)
with open(a.out, 'w') as h:
    for r in out: h.write(json.dumps(r, ensure_ascii=False) + '\n')
rep = dict(size=a.size, seed=a.seed, targets={f'{p}/{l}': n for (p, l), n in targets.items()}, filled={f'{p}/{l}': n for (p, l), n in fill.items()}, deficit={f'{p}/{l}': n for (p, l), n in deficit.items() if n}, sources=dict(collections.Counter(r.get('provenance') or r.get('slice') for r in out)), sha256=hashlib.sha256(open(a.out, 'rb').read()).hexdigest()[:16])
json.dump(rep, open(a.out.replace('.jsonl', '_receipt.json'), 'w'), indent=1, ensure_ascii=False)
print(f"written {len(out)} of {a.size} → {a.out}; deficit {sum(deficit.values())}: {rep['deficit']}")
