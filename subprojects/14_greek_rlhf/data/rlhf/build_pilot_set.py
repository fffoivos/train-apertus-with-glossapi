#!/usr/bin/env python3
"""Pilot prompt set for the RLHF grader (owner, 16 Sept): 50 prompts across every slice of docs/RLHF_PLAN_20260916.md §1.
Local sources only (the corpus download and the forum gate run in parallel): maths from our labelled pools, IF from a fresh generator draw,
multi-turn prefixes cut from THIS model's own simulator dialogues of 16 Sept, forum posts from the Lexilogia shard (raw, crude filter),
safety items from XSTest-el (EVAL items, pilot only), English prompts from the SFT manifest (SEEN in training, pilot only, flagged).
Usage: python3 data/rlhf/build_pilot_set.py <if_draw.jsonl> → data/rlhf/pilot/prompts.jsonl"""
import json, sys, random, re, gzip, hashlib, pathlib, collections
HERE = pathlib.Path(__file__).resolve().parent.parent; rng = random.Random(916); out = []
def add(slice_, source, messages, **meta):
    out.append(dict(id=f'{slice_}:{len([o for o in out if o["slice"] == slice_]):03d}', slice=slice_, source=source, messages=messages, **meta))
# maths, Greek (translated pool, Sol blind answer as label)
solve = {json.loads(l)['id']: json.loads(l) for l in open(HERE / 'math/cut2/out/independent_solve.jsonl')}
tr = [json.loads(l) for l in open(HERE / 'math/cut2/prep/translations_with_reference.jsonl')]
rng.shuffle(tr); picked = collections.Counter()
for r in tr:
    lvl = 'gsm' if r['src'] == 'gsm8k' else 'math'
    if r['id'] in solve and picked[lvl] < (2 if lvl == 'gsm' else 3):
        picked[lvl] += 1; add('math_el', f"translations_with_reference:{r['id']}", [dict(role='user', content=r['problem_el'])], label=solve[r['id']]['answer'], source_label=r['ref'], level=str(r.get('level')))
# maths, English (GSM8K dedup pool + published MATH)
gsm = [json.loads(l) for l in open(HERE / 'math/en/gsm8k_dedup3.jsonl')]; rng.shuffle(gsm); seen = set()
for r in gsm:
    if r['problem'] in seen or len([o for o in out if o['slice'] == 'math_en']) >= 3: continue
    seen.add(r['problem']); k = 'gsmen_' + hashlib.sha256(r['problem'].encode()).hexdigest()[:12]
    add('math_en', f"gsm8k_dedup3:{r['_row']}", [dict(role='user', content=r['problem'])], label=(solve.get(k) or {}).get('answer', r['expected_answer']), source_label=r['expected_answer'], level='gsm')
mt = [json.loads(l) for l in open(HERE / 'math/en/math_train_published.jsonl')]; rng.shuffle(mt)
for r in mt[:2]:
    ans = r.get('expected_answer') or r.get('answer') or ''
    add('math_en', f"math_train_published:{r['id']}", [dict(role='user', content=r['problem'])], label=ans, source_label=ans, level=str(r.get('level', '?')))
# instruction following (fresh generator draw)
for r in [json.loads(l) for l in open(sys.argv[1])][:10]:
    add('if', 'gen_prompts draw seed 916', [dict(role='user', content=r['prompt'])], checks=r.get('constraints') or r.get('checks') or r.get('families'), level=str(r.get('level')))
# multi-turn prefixes from this model's own dialogues (16 Sept, simulator v2)
dl = [json.loads(l) for l in open(HERE.parent / 'results/R4_full/r_R4/R4.jsonl')]; rng.shuffle(dl); n_greeklish = 0
for d in dl:
    turns = d['turns']
    if len(turns) < 4: continue
    if d.get('surface') == 'greeklish':
        if n_greeklish >= 2: continue
        n_greeklish += 1
    k = rng.choice([2, 3, min(4, len(turns) - 1)])
    msgs = []
    for t in turns[:k]: msgs += [dict(role='user', content=t['user']), dict(role='assistant', content=t['answer'])]
    msgs.append(dict(role='user', content=turns[k]['user']))
    add('multiturn', f"r_R4 dialogue {d['id']} cut at turn {k}", msgs, profile=d.get('profile'), move=turns[k].get('move'), surface=d.get('surface'))
    if len([o for o in out if o['slice'] == 'multiturn']) >= 8: break
# forum (Lexilogia shard, raw opening posts through the crude filter; the gate + rewrite is track A)
f = next(pathlib.Path.home().glob('.cache/huggingface/hub/datasets--fffoivos--greek-forum-discussions/snapshots/*/data/lexilogia/w00.jsonl.gz'), None) or next(pathlib.Path.home().glob('.cache/huggingface/hub/datasets--Greekpt--greek-forum-discussions/snapshots/*/data/lexilogia/w00.jsonl.gz'))
cands = []
with gzip.open(f, 'rt') as h:
    for line in h:
        d = json.loads(line); ir = d.get('initial_request') or {}; t = (ir.get('prompt_text') or '').strip(); w = len(t.split())
        if not (15 <= w <= 200) or not ('?' in t or ';' in t) or ir.get('referenced_images') or ir.get('referenced_links') or ir.get('quote_references'): continue
        if len(re.findall(r'[Ͱ-Ͽ]', t)) < 3 * len(re.findall(r'[A-Za-z]', t)) or int(d.get('post_count') or 0) < 2: continue
        if re.search(r'παραπάνω|στο άλλο νήμα|όπως είπα|συνημμ', t): continue
        cands.append((d.get('canonical_url'), t))
rng.shuffle(cands)
for url, t in cands[:10]: add('forum', f'lexilogia raw opening post {url}', [dict(role='user', content=t)], raw=True)
# safety (XSTest-el eval items; pilot only)
xs = [json.loads(l) for l in open(HERE / 'benchmarks_el/xstest/prompts_el_final.jsonl')]; rng.shuffle(xs)
for lab, n in (('safe', 3), ('unsafe', 2)):
    for r in [x for x in xs if x['label'] == lab][:n]: add('safety', f"xstest_el eval item {r['id']} ({lab})", [dict(role='user', content=r['prompt_el'])], expected=lab, eval_item=True)
# English (SFT manifest rows, SEEN in training; pilot only)
n_en = 0
for line in open(HERE / 'arms/R4_full/train.jsonl'):
    if n_en >= 7: break
    if '"config": "nemotron_chat_a"' not in line and '"config": "dolci_chat"' not in line: continue
    r = json.loads(line); u = [m for m in r['messages'] if m['role'] == 'user']
    if not u or not (20 <= len(u[0]['content'].split()) <= 120): continue
    if re.search(r'[ąćęłńóśźżäöüßéèêàçùñ¿¡\u0400-\u04ff\u3040-\u30ff\u4e00-\u9fff\u0600-\u06ff]', u[0]['content']): continue   # the Nemotron/Dolci blocks are ~8 % non-English (Polish, CJK, Cyrillic, …); the English slice must be English (owner, 16 Sept: english:002 was Polish)
    if rng.random() < 0.02: n_en += 1; add('english', f"SFT manifest row {r['id']} (seen in training)", [dict(role='user', content=u[0]['content'])], seen_in_sft=True)
p = HERE / 'rlhf/pilot/prompts.jsonl'; p.parent.mkdir(parents=True, exist_ok=True)
with open(p, 'w') as h:
    for o in out: h.write(json.dumps(o, ensure_ascii=False) + '\n')
print('pilot prompts:', len(out), dict(collections.Counter(o['slice'] for o in out)), '->', p)
