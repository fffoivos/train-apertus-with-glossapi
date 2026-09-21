#!/usr/bin/env python3
"""Round 3 (generator 0.2 release) RLHF staging.
build    : round3_all.jsonl = active generated prompts from generator_v02/runs/*/prompts.jsonl + manifest forum maths selections; n=32 sampled up front.
split S  : write the judging subset for stage S (1: k 0-7 for all; 2: k 8-15 for prompts without an eligible positive after stage 1; 3: k 16-31 after stage 2).
           Routing: purpose math -> maths reviewer prompt (judge_rank4_maths_en.txt); every other prompt, including embedded maths -> judge_rank4_v2_en.txt. Same runner, schema and pair rule.
Usage: python3 data/rlhf/round3/stage.py build | split <1|2|3>"""
import collections, hashlib, json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent; RL = HERE.parent
J = lambda p: [json.loads(l) for l in open(p) if l.strip()] if pathlib.Path(p).exists() else []
def build():
    rows = []
    for f in sorted((RL / 'generator_v02' / 'runs').glob('*/prompts.jsonl')):
        for r in J(f):
            if r['status'] != 'active': continue
            rows.append(dict(id=r['slot_id'], logical_id='sp:' + __import__('hashlib').sha256(r['instance_key'].encode()).hexdigest()[:16], messages=r['messages'], n=32, source='seeded', generator_version=r['generator_version'],
                             purpose=r['purpose'], subtype=r['subtype'], language=r['language'], difficulty=r['difficulty'], attitude=r['attitude'], register=r['register'], detail=r['detail'],
                             person=r['person'], situation=r['situation'], topic=r['topic'], scenario=(r['instance'] or {}).get('scenario'), story=r['story'], maths_content=r['maths_content'], maths_ambiguity=r['maths_ambiguity'], run=r['run']))
    man = json.load(open(RL / 'generator_v02' / 'manifest_round3.json'))
    for f in man['forum_slots']:
        rows.append(dict(id=f['slot_id'], logical_id='fp:' + f['source_id'][3:], messages=[{'role': 'user', 'content': f['message']}], n=32, source='forum:' + f['forum'], generator_version='0.2',
                         purpose=f['purpose'], subtype=f['task_type'], language=f['language'], maths_content='maths', maths_ambiguity=f.get('maths_ambiguity'), false_premise=f.get('false_premise')))
    ids = [r['id'] for r in rows]; assert len(ids) == len(set(ids))
    with open(HERE / 'round3_all.jsonl', 'w') as h:
        for r in rows: h.write(json.dumps(r, ensure_ascii=False) + '\n')
    print('round3_all', len(rows), dict(collections.Counter(r['purpose'] for r in rows)), dict(collections.Counter(r['language'] for r in rows)), 'maths routed', sum(r['maths_content'] in ('maths', 'embedded') for r in rows))
def positives(pid):
    """True if any judged batch so far (general or maths rubric) holds a reinforce AND a non-reinforce reply (the pair rule can be met)."""
    for f in list(HERE.glob('judged_general_s*.jsonl')) + list(HERE.glob('judged_maths_s*.jsonl')):
        for r in J(f):
            if r['id'] == pid and any(v.get('verdict') == 'reinforce' for v in r['by_k'].values() if isinstance(v, dict)) and any(v.get('verdict') != 'reinforce' for v in r['by_k'].values() if isinstance(v, dict)): return True
    return False
def split(stage):
    rows = J(HERE / 'round3_all.jsonl'); samples = collections.defaultdict(dict)
    for s in J(HERE / 'round3_samples.jsonl'):
        if s.get('k', -1) >= 0: samples[s['id']][s['k']] = s
    lo, hi = {1: (0, 8), 2: (8, 16), 3: (16, 32)}[stage]; gen, mat = [], []
    # Escalation policy (disclosed, evidence-based): generated prompts escalate to 16 and then 32 replies while they have no usable positive.
    # Forum maths posts produced 0 eligible positives out of 41 pre-existing items under the specialist judge, so only a fixed sample of 8 of them
    # escalates, to measure whether more replies would help; the rest stop after 8 replies. See maths_judge/calibration_report.md.
    forum = sorted(r['id'] for r in rows if str(r.get('source', '')).startswith('forum'))
    esc_forum = set(sorted(forum, key=lambda i: hashlib.sha256(i.encode()).hexdigest())[:8])
    for r in rows:
        m = r['purpose'] == 'math'; g = not m          # owner, 17 Sept: maths rubric only where maths is the task; embedded maths stays on v2.4
        if stage > 1:
            if positives(r['id']): continue
            if str(r.get('source', '')).startswith('forum') and r['id'] not in esc_forum: continue
        ks = [k for k in range(lo, hi) if k in samples[r['id']]]
        if len(ks) < hi - lo: print('incomplete samples', r['id'], len(ks), file=sys.stderr); ks = ks[: len(ks) // 4 * 4]
        if not ks: continue
        if g: gen.append((r, ks))
        if m: mat.append((r, ks))
    for name, sel in (('general', gen), ('maths', mat)):
        with open(HERE / f'{name}_s{stage}_prompts.jsonl', 'w') as hp, open(HERE / f'{name}_s{stage}_samples.jsonl', 'w') as hs:
            for r, ks in sel:
                hp.write(json.dumps(dict(id=r['id'], messages=r['messages']), ensure_ascii=False) + '\n')
                for k in ks: hs.write(json.dumps(dict(id=r['id'], k=k, text=samples[r['id']][k]['text']), ensure_ascii=False) + '\n')
        print(name, 'stage', stage, 'prompts', len(sel))
if __name__ == '__main__':
    if sys.argv[1] == 'build': build()
    else: split(int(sys.argv[2]))
