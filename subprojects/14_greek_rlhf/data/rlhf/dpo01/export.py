#!/usr/bin/env python3
"""DPO01 exporter (DPO01_EXECUTION_PLAN_20260918.md §4): existing eligible preference pairs, no maths task, one pair per logical prompt,
group-frozen 10% dev split. Reads only; writes train/dev/provenance/exclusions/manifest under data/rlhf/dpo01/.
No model calls. Training text is preserved byte for byte; normalisation is used for duplicate detection only.
Usage: python3 data/rlhf/dpo01/export.py [--out data/rlhf/dpo01] [--keep-round1]"""
import argparse, collections, hashlib, json, pathlib, re, sqlite3, sys, unicodedata
HERE = pathlib.Path(__file__).resolve().parent; RL = HERE.parent; ROOT = RL.parent.parent
def J(p): return [json.loads(l) for l in open(p) if l.strip()]
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def norm(s): return ' '.join(unicodedata.normalize('NFKC', s or '').split())
def fsha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()[:16]
def full(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
ap = argparse.ArgumentParser(); ap.add_argument('--out', default=str(HERE)); ap.add_argument('--keep-round1', action='store_true')
ap.add_argument('--registry', default=str(RL / 'registry' / 'registry.sqlite')); a = ap.parse_args()
OUT = pathlib.Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
excl = []                      # every dropped record, with its reason
def drop(rec, why, **extra): excl.append(dict(rec, exclusion=why, **extra))
# ---------------------------------------------------------------- inputs
c = sqlite3.connect(f'file:{a.registry}?mode=ro', uri=True)
prompts = {r[0]: dict(logical_id=r[0], messages=json.loads(r[1]), source_kind=r[2], generator_version=r[3], round_first=r[4],
                      purpose=r[5], task_type=r[6], language=r[7], forum=r[8], seed_id=r[9], source_id=r[10], keepable=r[11],
                      status=r[12], maths_content=r[13], labels=json.loads(r[14] or '{}'))
           for r in c.execute("""SELECT logical_id, messages, source_kind, generator_version, round_first, primary_purpose, task_type,
                                        language, forum, seed_id, source_id, keepable, status, maths_content, labels FROM prompts""")}
judge = {r[0]: dict(judgement_id=r[0], logical_id=r[1], alias=r[2], batch=r[3], rubric_sha=r[4], file=r[5]) for r in
         c.execute("SELECT judgement_id, logical_id, alias, batch, rubric_sha, file FROM judgements")}
alias_of = collections.defaultdict(list)
for al, lid in c.execute("SELECT alias, logical_id FROM aliases"): alias_of[lid].append(al)
credits = [dict(logical_id=r[0], judgement_id=r[1], chosen_k=r[2], rejected_k=r[3]) for r in
           c.execute("SELECT logical_id, judgement_id, chosen_k, rejected_k FROM pair_credit WHERE eligible=1")]
samples = {}                   # (pool file, alias, k) -> text
for f in sorted((RL / 'pool').glob('round?_all_samples.jsonl')):
    for s in J(f):
        if s.get('k', -1) >= 0: samples[(f.name, s['id'], s['k'])] = s['text']
pool_prompt = {}
for f in sorted((RL / 'pool').glob('round?_all.jsonl')):
    for p in J(f): pool_prompt[(f.name, p['id'])] = p
# ---------------------------------------------------------------- 1. banked pairs (rounds 1-2)
records = []
for cr in credits:
    p = prompts.get(cr['logical_id']); j = judge.get(cr['judgement_id'])
    base = dict(source='registry', logical_id=cr['logical_id'], purpose=(p or {}).get('purpose'), language=(p or {}).get('language'),
                round=(p or {}).get('round_first'), alias=(j or {}).get('alias'))
    if not p or not j: drop(base, 'missing_provenance'); continue
    if not p['keepable'] or p['status'] != 'active': drop(base, f"not_keepable:{p['status']}"); continue
    j_round = 'round1' if 'round1' in j['file'] else ('round2' if 'round2' in j['file'] else p['round_first'])
    base['round'] = j_round
    if (j_round == 'round1' or p['round_first'] == 'round1') and not a.keep_round1:
        drop(base, 'round1_excluded_by_owner'); continue      # the judged pair itself must not come from round 1
    if p['purpose'] == 'math' or p['task_type'] == 'math' or p['maths_content'] == 'maths': drop(base, 'maths_task_excluded'); continue
    sfile = j['file'].split('/')[-1].replace('_judged', '_samples')
    ch = samples.get((sfile, j['alias'], cr['chosen_k'])); rj = samples.get((sfile, j['alias'], cr['rejected_k']))
    if ch is None or rj is None: drop(base, 'sample_text_missing', file=sfile); continue
    if norm(ch) == norm(rj) or not norm(ch) or not norm(rj): drop(base, 'identical_or_empty_completion'); continue
    src = pool_prompt.get((sfile.replace('_samples', ''), j['alias'])) or {}
    base['round'] = j_round
    records.append(dict(base, messages=p['messages'], chosen=ch, rejected=rj, chosen_k=cr['chosen_k'], rejected_k=cr['rejected_k'],
                        judgement_id=j['judgement_id'], judgement_file=j['file'], judgement_batch=j['batch'], judgement_pass=None,
                        rubric_sha=j['rubric_sha'], source_file=sfile, source_id=p['source_id'],
                        seed_id=p['seed_id'], forum=p['forum'], maths_content=p['maths_content'], embedded_maths=p['maths_content'] == 'embedded',
                        task_type=p['task_type'], slice=src.get('slice')))
# ---------------------------------------------------------------- 2. round 3
r3_rows = {x['id']: x for x in J(RL / 'round3' / 'round3_all.jsonl')}
r3_samples = collections.defaultdict(dict)
for s in J(RL / 'round3' / 'round3_samples.jsonl'):
    if s.get('k', -1) >= 0: r3_samples[s['id']][s['k']] = s['text']
for x in J(RL / 'round3' / 'round3_pairs.jsonl'):
    r = r3_rows.get(x['id']); pair = x.get('pair')
    base = dict(source='round3', logical_id=x.get('logical_id'), purpose=x.get('purpose'), language=x.get('language'), round='round3', alias=x['id'])
    if not pair or x['status'] != 'eligible': drop(base, f"no_pair:{x['status']}"); continue
    if not r: drop(base, 'missing_provenance'); continue
    if r['purpose'] == 'math' or pair.get('route') == 'maths' or r.get('maths_content') == 'maths': drop(base, 'maths_task_excluded'); continue
    ch = r3_samples[x['id']].get(pair['chosen_k']); rj = r3_samples[x['id']].get(pair['rejected_k'])
    if ch is None or rj is None: drop(base, 'sample_text_missing'); continue
    if norm(ch) == norm(rj) or not norm(ch) or not norm(rj): drop(base, 'identical_or_empty_completion'); continue
    records.append(dict(base, messages=r['messages'], chosen=ch, rejected=rj, chosen_k=pair['chosen_k'], rejected_k=pair['rejected_k'],
                        judgement_id=f"round3:{x['id']}:s{pair['stage']}b{pair['batch']}", rubric_sha=None, source_file='round3_samples.jsonl',
                        judgement_stage=pair['stage'], judgement_batch=pair['batch'], judgement_route=pair.get('route'),
                        source_id=r.get('source_id') or r.get('logical_id'), seed_id=(f"seed:0.2:{x['id']}" if r['source'] == 'seeded' else None),
                        run=r.get('run'), forum=(r['source'] if str(r['source']).startswith('forum') else None),
                        maths_content=r.get('maths_content'), embedded_maths=r.get('maths_content') == 'embedded', task_type=r.get('subtype'),
                        slice=r.get('source'), labels={k: r.get(k) for k in ('difficulty', 'detail', 'register', 'attitude') if r.get(k)}))
# ---------------------------------------------------------------- 3. one pair per logical prompt / prefix
def prefix_key(rec): return sha(json.dumps([[m['role'], norm(m['content'])] for m in rec['messages']], ensure_ascii=False))
best = {}
for rec in records:
    k = rec.get('logical_id') or prefix_key(rec)
    rec['prefix_key'] = prefix_key(rec)
    prev = best.get(k) or best.get(rec['prefix_key'])
    if prev is None: best[k] = best[rec['prefix_key']] = rec
    else:                                                  # round 3 is the currently active sampled version: it wins
        keep, dropped = (rec, prev) if (rec['source'] == 'round3' and prev['source'] != 'round3') else (prev, rec)
        best[k] = best[rec['prefix_key']] = keep
        drop(dict(source=dropped['source'], logical_id=dropped['logical_id'], alias=dropped['alias'], purpose=dropped['purpose'],
                  language=dropped['language'], round=dropped['round']), 'duplicate_prompt', kept=keep['alias'])
kept = list({id(v): v for v in best.values()}.values())
# ---------------------------------------------------------------- 4. groups and the frozen split
parent = {}
def find(x):
    while parent.setdefault(x, x) != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry: parent[rx] = ry
for rec in kept:
    node = 'row:' + rec['alias']
    for other in [f"src:{rec['source_id']}" if rec.get('source_id') else None, f"seed:{rec['seed_id']}" if rec.get('seed_id') else None,
                  f"lid:{rec['logical_id']}" if rec.get('logical_id') else None, 'pfx:' + rec['prefix_key']]:
        if other: union(node, other)
for rec in kept:
    root = find('row:' + rec['alias'])
    rec['group_key'] = root
    rec['split'] = 'dev' if int(sha('20260918|' + root), 16) % 10 == 0 else 'train'
groups = collections.defaultdict(list)
for rec in kept: groups[rec['group_key']].append(rec)
dev_groups = [g for g, rs in groups.items() if rs[0]['split'] == 'dev']
if len(dev_groups) < 10:                                   # plan §4: top up dev by lowest hash until ten groups
    order = sorted((g for g in groups if g not in dev_groups), key=lambda g: int(sha('20260918|' + g), 16))
    for g in order[: 10 - len(dev_groups)]:
        for r in groups[g]: r['split'] = 'dev'
        dev_groups.append(g)
# ---------------------------------------------------------------- 5. write
def row(rec):
    return dict(prompt=[{'role': m['role'], 'content': m['content']} for m in rec['messages']],
                chosen=[{'role': 'assistant', 'content': rec['chosen']}], rejected=[{'role': 'assistant', 'content': rec['rejected']}])
train = [r for r in kept if r['split'] == 'train']; dev = [r for r in kept if r['split'] == 'dev']
for name, rs in (('train', train), ('dev', dev)):
    with open(OUT / f'{name}.jsonl', 'w') as h:
        for r in rs: h.write(json.dumps(row(r), ensure_ascii=False) + '\n')
with open(OUT / 'provenance.jsonl', 'w') as h:
    for r in kept:
        h.write(json.dumps({k: v for k, v in r.items() if k != 'messages'} | dict(
            prompt_sha=sha(json.dumps([[m['role'], m['content']] for m in r['messages']], ensure_ascii=False)),
            chosen_sha=sha(r['chosen']), rejected_sha=sha(r['rejected']), turns=len(r['messages'])), ensure_ascii=False) + '\n')
with open(OUT / 'exclusions.jsonl', 'w') as h:
    for e in excl: h.write(json.dumps(e, ensure_ascii=False) + '\n')
def words(s): return len(re.findall(r'\w+', s))
man = dict(
    plan='docs/RLHF_COORDINATION/DPO01_EXECUTION_PLAN_20260918.md', experiment='G4F6P1--DPO01', created_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
    rows=dict(train=len(train), dev=len(dev), total=len(kept)), groups=dict(total=len(groups), dev=len(dev_groups)),
    split_algorithm='dev if int(sha256("20260918|"+group_key),16) % 10 == 0, group-frozen, topped up to ten dev groups by lowest hash',
    exclusions=dict(collections.Counter(e['exclusion'] for e in excl)),
    by_purpose=dict(collections.Counter(r['purpose'] for r in kept)), by_language=dict(collections.Counter(r['language'] for r in kept)),
    by_round=dict(collections.Counter(r['round'] for r in kept)), by_source=dict(collections.Counter(r['source'] for r in kept)),
    purpose_by_language=dict(collections.Counter(f"{r['purpose']}/{r['language']}" for r in kept)),
    embedded_maths=sum(1 for r in kept if r.get('embedded_maths')),
    maths_excluded=sum(1 for e in excl if e['exclusion'] == 'maths_task_excluded'),
    round1_excluded=sum(1 for e in excl if e['exclusion'] == 'round1_excluded_by_owner'),
    multi_turn=sum(1 for r in kept if len(r['messages']) > 1),
    lengths=dict(prompt_words=sorted(words(' '.join(m['content'] for m in r['messages'])) for r in kept)[len(kept) // 2],
                 chosen_words_median=sorted(words(r['chosen']) for r in kept)[len(kept) // 2],
                 rejected_words_median=sorted(words(r['rejected']) for r in kept)[len(kept) // 2],
                 chosen_over_rejected_ratio=round(sum(words(r['chosen']) for r in kept) / max(1, sum(words(r['rejected']) for r in kept)), 3)),
    sources={str(pathlib.Path(p).relative_to(ROOT)): full(p) for p in
             [a.registry, __file__, RL / 'round3' / 'round3_pairs.jsonl', RL / 'round3' / 'round3_all.jsonl', RL / 'round3' / 'round3_samples.jsonl']
             + sorted(str(x) for x in (RL / 'pool').glob('round?_all*.jsonl'))
             + sorted(str(x) for x in (RL / 'round3').glob('judged_*_s?.jsonl'))},
    decisions=['round 1 excluded (owner, 18 Sept: round 1 was not considered good; round 2 carried the improvements)',
               'maths task excluded (plan §1): purpose=math, task_type=math, maths-route pairs, maths_content=maths; embedded maths kept and counted',
               'dialogue development pairs excluded (training_eligible=false)',
               'one pair per logical prompt and per normalised prefix; round 3 wins a tie as the active sampled version'],
    outputs={})
man['by_output_language'] = dict(collections.Counter(
    ('el' if sum('\u0370' <= c <= '\u03ff' or '\u1f00' <= c <= '\u1fff' for c in r['chosen']) > 20 else 'non-el') for r in kept))
man['outputs'] = {name: full(OUT / name) for name in ('train.jsonl', 'dev.jsonl', 'provenance.jsonl', 'exclusions.jsonl')}
man['split_check'] = dict(dev_rounds=dict(collections.Counter(r['round'] for r in dev)), dev_purposes=dict(collections.Counter(r['purpose'] for r in dev)),
                          groups_spanning_both_splits=sum(1 for g, rs in groups.items() if len({r['split'] for r in rs}) > 1))
json.dump(man, open(OUT / 'manifest.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps({k: man[k] for k in ('rows', 'groups', 'by_purpose', 'by_language', 'by_round', 'embedded_maths', 'maths_excluded', 'round1_excluded', 'multi_turn', 'exclusions')}, ensure_ascii=False, indent=1))
