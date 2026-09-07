#!/usr/bin/env python3
"""Stage-2 Greek pass arm (SFT_ROUND2_PLAN §4 stage 2): our Greek rows + the personality set + a 10% replay of stage 1, all drawn from the
already screened, decontaminated stage-1 arm (so no new judging or contamination pass is needed) plus personality_v3.
Usage: python3 data/assemble_stage2.py [replay_frac=0.10] [seed=2026]  → data/arms/R2_stage2/{train,dev}.jsonl + summary.md
Exact token counts come from the trainer's --dry-run afterwards (cluster/sft_train.py), which also validates every row."""
import json, random, sys, os, collections
frac = float(sys.argv[1]) if len(sys.argv) > 1 else 0.10; seed = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
rng = random.Random(seed); A = 'data/arms/R2_stage1'; O = 'data/arms/R2_stage2'; os.makedirs(O, exist_ok=True)
GREEK = {'greek_ours', 'greek_rewrite'}
seen = set(); train = []; replay_pool = collections.defaultdict(list)
for l in open(f'{A}/train.jsonl'):
    r = json.loads(l)
    if r['config'] in GREEK:
        if r['id'] in seen: continue  # weight-2 duplicates collapse: stage 2 is a low-LR pass, one copy each
        seen.add(r['id']); train.append(r)
    else: replay_pool[r['config']].append(r)
replay = []
for cfg, rows in sorted(replay_pool.items()):
    k = int(round(len(rows) * frac)); replay += rng.sample(rows, k)
pers = [json.loads(l) for l in open('data/personality/v3/full_20260906/edited.jsonl')]
rng.shuffle(pers); n_dev = int(round(len(pers) * 0.05)); pers_dev, pers_train = pers[:n_dev], pers[n_dev:]
P = lambda r: dict(messages=r['messages'], config='personality_v3', id=r['id'])
train += replay + [P(r) for r in pers_train]; rng.shuffle(train)
dev = [json.loads(l) for l in open(f'{A}/dev.jsonl')] + [P(r) for r in pers_dev]
with open(f'{O}/train.jsonl', 'w') as f:
    for r in train: f.write(json.dumps(dict(messages=r['messages'], config=r['config'], id=r['id']), ensure_ascii=False) + '\n')
with open(f'{O}/dev.jsonl', 'w') as f:
    for r in dev: f.write(json.dumps(dict(messages=r['messages'], config=r['config'], id=r['id']), ensure_ascii=False) + '\n')
c = collections.Counter(r['config'] for r in train)
md = f"# R2_stage2 (Greek pass)\n\nreplay fraction {frac}, seed {seed}. train {len(train)} rows, dev {len(dev)} rows (stage-1 dev + {n_dev} personality rows held out).\n\n| block | rows |\n|---|---|\n" + ''.join(f'| {k} | {v} |\n' for k, v in sorted(c.items(), key=lambda x: -x[1]))
md += "\nSources: greek_ours and greek_rewrite = every unique row of the stage-1 arm (weight-2 duplicates collapsed); replay = a seeded 10% of each other stage-1 block; personality_v3 = data/personality/v3/full_20260906/edited.jsonl. Aya Greek left out (owner decision open, plan §7.4).\n"
open(f'{O}/summary.md', 'w').write(md); print(md)
