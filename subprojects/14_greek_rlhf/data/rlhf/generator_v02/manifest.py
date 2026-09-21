#!/usr/bin/env python3
"""Generator 0.2: dry-run quota manifest for about 500 new slots (ingestion plan §4–§5; spec v1.0).
Single-turn cells take the conservative new-prompt need from the registry frontier at the planning size; dialogue starting seeds are reserved
for the rest of the slot budget and are not generated here. Within the single-turn slots: subtypes evenly per category (largest remainder),
then difficulty, attitude, register and detail from the agreed defaults (detail from the round-2 profile), with compatibility repair, then
person/situation/topic ingredients drawn without reuse. Deterministic for a given seed.
Usage: python3 data/rlhf/generator_v02/manifest.py [--size 500] [--budget 500] [--seed 20260917]"""
import argparse, collections, hashlib, json, math, pathlib, random
HERE = pathlib.Path(__file__).resolve().parent; RL = HERE.parent
TARGET = json.load(open(RL / 'target_distribution_v1.json')); KINDS = json.load(open(HERE / 'task_kinds.json'))
DETAIL = {'bare': 30, 'terse': 20, 'short': 20, 'medium': 20, 'detailed': 5, 'rambling': 5}
def sha16(s): return hashlib.sha256(s.encode()).hexdigest()[:16]
def lr(total, shares):
    tot = sum(shares.values()); raw = {k: total * v / tot for k, v in shares.items()}; base = {k: math.floor(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: (raw[k] - base[k], k), reverse=True)[: total - sum(base.values())]: base[k] += 1
    return base
def build(size, budget, seed):
    rep = json.load(open(RL / 'registry' / 'registry_report.json'))
    cells = rep['frontier'][str(size)]['cells']; rng = random.Random(seed)
    ylow = {c: v['low'] for c, v in rep['yield_by_cell'].items()}
    single, forum_sel = {}, {}
    for c, row in cells.items():
        if c.startswith('dialogue'): continue
        need = max(0, row['target'] - row['E'])
        if not need: continue
        a_ = row.get('A', 0); y_ = ylow.get(c) or 0
        take = min(a_, math.ceil(need / 2 / y_)) if (a_ and y_) else 0          # forum pool may fill at most half of a cell's need (owner method: part forum, rest seeded)
        rest = max(0, need - take * y_)
        if take: forum_sel[c] = take
        if rest and y_: single[c] = math.ceil(rest / y_)
    n_single = sum(single.values()) + sum(forum_sel.values())
    if n_single > budget:
        single = lr(budget - sum(forum_sel.values()), single); n_single = budget
    slots = []
    for cell, n in sorted(single.items()):
        purpose, lang = cell.split('/')
        for sub, k in lr(n, {s: 1 for s in KINDS[purpose]}).items():
            for _ in range(k): slots.append(dict(purpose=purpose, language=lang, subtype=sub, packet=KINDS[purpose][sub]['packet']))
    rng.shuffle(slots)
    def assign(axis, shares, ok=lambda s, v: True):
        values = [v for v, k in lr(len(slots), shares).items() for _ in range(k)]; rng.shuffle(values)
        for s, v in zip(slots, values): s[axis] = v
        for i, s in enumerate(slots):                     # compatibility repair by swapping with a compatible slot
            if ok(s, s[axis]): continue
            for t in slots:
                if t is not s and ok(s, t[axis]) and ok(t, s[axis]): s[axis], t[axis] = t[axis], s[axis]; break
    assign('difficulty', TARGET['within_seeded_defaults_percent']['difficulty'])
    assign('attitude', TARGET['within_seeded_defaults_percent']['attitude'])
    assign('register', TARGET['within_seeded_defaults_percent']['register'], ok=lambda s, v: v != 'greeklish' or s['language'] == 'el')
    NO_BARE = {'multi_constraint_composition'}   # 3–5 interacting constraints cannot be stated in 12 words
    assign('detail', DETAIL, ok=lambda s, v: not (s['packet'] and v == 'short') and not (v == 'bare' and s['subtype'] in NO_BARE))
    ax = {n: json.load(open(HERE / 'axes' / f'{n}.json'))['items'] for n in ('situations', 'topics')}
    people = {l: json.load(open(HERE / 'axes' / f'people_{l}.json'))['items'] for l in TARGET['language_shares_percent']}
    used = collections.defaultdict(set)
    for i, s in enumerate(slots):
        s['slot_id'] = f'R3-{i + 1:04d}'
        pool = [p for p in people[s['language']] if p not in used['person_' + s['language']]] or people[s['language']]
        s['person'] = rng.choice(pool); used['person_' + s['language']].add(s['person'])
        s['situation'] = rng.choice(ax['situations']); s['topic'] = rng.choice(ax['topics'])
    problems = [s['slot_id'] for s in slots if (s['register'] == 'greeklish' and s['language'] != 'el') or (s['packet'] and s['detail'] == 'short') or (s['detail'] == 'bare' and s['subtype'] in NO_BARE)]
    # forum selections: unused gate-accepted posts in the cell, relabelled task type, astrovox at most 3 % of selected forum posts, deterministic
    import sqlite3
    reg = sqlite3.connect(RL / 'registry' / 'registry.sqlite'); relabel = {json.loads(l)['id']: json.loads(l) for l in open(RL / 'registry' / 'relabel_v1.jsonl')}
    FP = {'question': 'factual', 'explanation': 'factual', 'calculation': 'math', 'advice': 'everyday', 'opinion': 'everyday', 'share': 'everyday', 'translation': 'everyday', 'other': 'everyday', 'create': 'everyday'}
    used_urls = {u for (u,) in reg.execute("SELECT s.url FROM prompts p JOIN sources s ON s.source_id=p.source_id WHERE p.source_kind='forum'")}
    forum_slots = []
    total_forum = sum(forum_sel.values()); astro_cap = max(0, math.floor(total_forum * 0.03))
    for cell, k in sorted(forum_sel.items()):
        purpose, lang = cell.split('/')
        cands = []
        for sid, url, forum, payload in reg.execute("SELECT source_id, url, forum, payload FROM sources WHERE kind='forum_post' AND status='gate_accepted'"):
            rl = relabel.get(sid)
            if url in used_urls or not rl or FP.get(rl['task_type']) != purpose: continue
            if rl['maths_content'] and purpose != 'math': continue
            cands.append((sha16(sid + str(seed)), sid, forum, json.loads(payload), rl))
        cands.sort(); astro = 0
        for _, sid, forum, pl, rl in cands:
            if len([f for f in forum_slots if f['purpose'] == purpose]) >= k: break
            if forum == 'astrovox':
                if astro >= astro_cap: continue
                astro += 1
            forum_slots.append(dict(slot_id=f'R3F-{len(forum_slots) + 1:04d}', source_kind='forum', purpose=purpose, language=lang, source_id=sid, forum=forum, task_type=rl['task_type'], maths_content=rl['maths_content'], maths_ambiguity=rl['maths_ambiguity'], message=pl['prompt_el'], false_premise=pl.get('false_premise')))
    out = dict(version='round3-manifest-v2', forum_cap_rule='forum posts fill at most half of a cell need (generator 0.2 = part forum, rest seeded); for math/el this keeps generated slots for maths kinds beyond forum homework calculations (R-PG3 finding 3 answered, not adopted)', planning_size_pairs=size, slot_budget=budget, single_turn_slots=len(slots), forum_selected_slots=len(forum_slots), dialogue_starting_seeds_reserved=budget - len(slots) - len(forum_slots),
               seed=seed, target=TARGET['version'], registry_report_sha16=hashlib.sha256(open(RL / 'registry' / 'registry_report.json', 'rb').read()).hexdigest()[:16],
               axes_sha16={f.name: hashlib.sha256(f.read_bytes()).hexdigest()[:16] for f in sorted((HERE / 'axes').glob('*.json'))},
               task_kinds_sha16=hashlib.sha256((HERE / 'task_kinds.json').read_bytes()).hexdigest()[:16],
               cell_totals=dict(sorted(collections.Counter(f"{s['purpose']}/{s['language']}" for s in slots).items())),
               purpose_totals=dict(collections.Counter(s['purpose'] for s in slots)), language_totals=dict(collections.Counter(s['language'] for s in slots)),
               subtype_totals=dict(collections.Counter(f"{s['purpose']}/{s['subtype']}" for s in slots)), axis_totals={a: dict(collections.Counter(s[a] for s in slots)) for a in ('difficulty', 'attitude', 'register', 'detail')},
               compatibility_violations=problems, forum_by_cell=dict(collections.Counter(f"{f['purpose']}/{f['language']}" for f in forum_slots)), forum_by_forum=dict(collections.Counter(f['forum'] for f in forum_slots)), slots=slots, forum_slots=forum_slots)
    return out
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--size', type=int, default=500); ap.add_argument('--budget', type=int, default=500); ap.add_argument('--seed', type=int, default=20260917); a = ap.parse_args()
    m = build(a.size, a.budget, a.seed); json.dump(m, open(HERE / 'manifest_round3.json', 'w'), ensure_ascii=False, indent=1)
    print({k: m[k] for k in ('single_turn_slots', 'forum_selected_slots', 'forum_by_cell', 'forum_by_forum', 'dialogue_starting_seeds_reserved', 'purpose_totals', 'language_totals', 'axis_totals', 'compatibility_violations')})
