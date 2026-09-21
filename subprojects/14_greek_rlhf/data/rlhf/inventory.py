#!/usr/bin/env python3
"""Register every pre-existing RLHF prompt and dialogue with one record each, and compare the realised distribution with the target.
Usage: python3 data/rlhf/inventory.py [--size N]   (N = first-run size in accepted pairs, for the deficit table; default 500 as a checkpoint)
Writes data/rlhf/pool/inventory.jsonl (one row per prompt or chat) and data/rlhf/pool/inventory_summary.json; prints the tables."""
import json, collections, re, argparse, hashlib, pathlib
ROOT = pathlib.Path(__file__).resolve().parent; POOL = ROOT / 'pool'; DQD = ROOT / 'dialogue_quality_depth' / 'runtime'
ap = argparse.ArgumentParser(); ap.add_argument('--size', type=int, default=500); a = ap.parse_args()
J = lambda p: [json.loads(l) for l in open(p) if l.strip()]
T = json.load(open(ROOT / 'target_distribution_v1.json'))
def verdicts(path):
    V = collections.defaultdict(list)
    for r in J(path):
        if r.get('error') or r.get('pass', 1) != 1: continue
        V[r['id']] += [c.get('verdict') for c in r['by_k'].values()]
    return V
def pair_state(v):
    if not v: return 'unjudged'
    if 'reinforce' in v and any(x != 'reinforce' for x in v): return 'pairable'
    if 'reinforce' not in v: return 'no_reinforce'
    return 'all_reinforce'
MATHS_FORUMS = {'mathematica'}
rows = []
excl = set(json.load(open(POOL / 'round1_excluded_json_leak.json')))
for rnd, pool, judged in (('round1', 'round1_all.jsonl', 'round1_all_judged.jsonl'), ('round2', 'round2_all.jsonl', 'round2_all_judged.jsonl')):
    V = verdicts(POOL / judged)
    for r in J(POOL / pool):
        forum = r['slice'] == 'forum'
        gen = 'forum-gate-v3' if forum else ('0.1' if rnd == 'round1' else '0.2')
        text = r['messages'][-1]['content']
        maths = r['purpose'] == 'math' or (forum and (r.get('task_type') == 'calculation' or r['id'].split(':')[1] in MATHS_FORUMS))
        rows.append(dict(id=r['id'], round=rnd, source_kind='forum' if forum else 'seeded', generator_version=gen,
                         defunct_generator=gen == '0.1', excluded=r['id'] in excl, excluded_reason='json_leak' if r['id'] in excl else None,
                         primary_purpose=r['purpose'], task_type=r.get('task_type') or r.get('family'), language=r['language'],
                         forum=r['id'].split(':')[1] if forum else None, detail=r.get('detail'), register=r.get('register'), attitude=r.get('attitude'),
                         words=len(re.findall(r'\w+', text)), replies=r.get('n'), pair_state=pair_state(V.get(r['id'], [])),
                         maths_content=bool(maths), maths_rejudge_required=bool(maths), prompt_sha16=hashlib.sha256(text.encode()).hexdigest()[:16]))
man = {s['trajectory_id']: s for s in json.load(open(DQD / 'manifest.json'))['seeds']}
traj = {}
for t in J(DQD / 'measurement' / 'trajectories.jsonl'): traj[t['trajectory_id']] = t
prefs = collections.Counter(p['trajectory_id'] for p in J(DQD / 'measurement' / 'preferences.jsonl'))
for tid, t in sorted(traj.items()):
    s = man[tid]
    rows.append(dict(id=f'dialogue:{tid}', round='dialogue-pilot-v1', source_kind='dialogue', generator_version='dialogue-quality-depth-v1 (0.1 seeds)',
                     defunct_generator=True, excluded=False, excluded_reason=None, primary_purpose='dialogue', task_type=f"{s['task']}/{s['family']}",
                     language=s['language'], forum=None, detail=None, register=s['register'], attitude=s['attitude'], words=None,
                     replies=t['assistant_turns'], pair_state='pairable' if prefs[tid] else 'no_pair', pairs=prefs[tid],
                     maths_content=s['task'] == 'math' or s['family'].startswith('e_plan'), maths_rejudge_required=s['task'] == 'math' or s['family'].startswith('e_plan'),
                     prompt_sha16=None))
with open(POOL / 'inventory.jsonl', 'w') as h:
    for r in rows: h.write(json.dumps(r, ensure_ascii=False) + '\n')
def dist(subset, key, shares):
    n = len(subset); pairs = [r for r in subset if r['pair_state'] == 'pairable']
    c = collections.Counter(r[key] for r in subset); pc = collections.Counter(r[key] for r in pairs)
    out = {}
    for k, share in shares.items():
        tgt = round(a.size * share / 100)
        out[k] = dict(prompts=c[k], prompts_share=round(c[k] / max(1, n) * 100, 1), with_pair=pc[k], target_share=share, target_pairs_at_size=tgt, deficit_pairs=max(0, tgt - pc[k]))
    return out
live = [r for r in rows if not r['excluded']]
keep = [r for r in live if not r['defunct_generator']]
summary = dict(target=T['version'], size_for_deficits=a.size, rows=len(rows), excluded=len(rows) - len(live),
               by_source=dict(collections.Counter(f"{r['source_kind']} / {r['generator_version']}" for r in live)),
               keepable_by_purpose=dist(keep, 'primary_purpose', T['primary_purpose_shares_percent']),
               keepable_by_language=dist(keep, 'language', T['language_shares_percent']),
               including_defunct_by_purpose=dist(live, 'primary_purpose', T['primary_purpose_shares_percent']),
               maths_rejudge_required=sum(r['maths_rejudge_required'] for r in live))
json.dump(summary, open(POOL / 'inventory_summary.json', 'w'), indent=1, ensure_ascii=False)
for name in ('keepable_by_purpose', 'keepable_by_language'):
    print(f"\n{name} (keepable = not from a defunct generator; size {a.size} accepted pairs)")
    for k, v in summary[name].items(): print(f"  {k:12} prompts {v['prompts']:4} ({v['prompts_share']:5.1f}%)  pairs {v['with_pair']:4}  target {v['target_share']:>3}% = {v['target_pairs_at_size']:4}  deficit {v['deficit_pairs']:4}")
print('\nby source:', summary['by_source']); print('maths rejudge required:', summary['maths_rejudge_required'])
