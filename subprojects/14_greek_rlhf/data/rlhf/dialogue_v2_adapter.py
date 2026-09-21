#!/usr/bin/env python3
"""Write the dialogue v2 run into the pilot's measurement layout, so `dialogue_page.py` renders it in exactly the same page.
Usage: python3 data/rlhf/dialogue_v2_adapter.py <out runtime dir> [v2|c60|<runtime dir>]"""
import collections, json, pathlib, sys
RL = pathlib.Path(__file__).resolve().parent
SET = sys.argv[2] if len(sys.argv) > 2 else 'v2'
ROOTS = ([RL / 'dialogue_v2' / 'collection60' / 'runtime'] if SET == 'c60' else [pathlib.Path(SET)] if SET not in ('v2',)
         else [RL / 'dialogue_v2' / 'runtime', RL / 'reference_guided_dialogue_demo' / 'runtime'])
def J(p): return [json.loads(l) for l in open(p) if l.strip()] if p.exists() else []
def rows(name): return [r for root in ROOTS for r in J(root / name)]
out = pathlib.Path(sys.argv[1]) / 'measurement'; out.mkdir(parents=True, exist_ok=True)
traj = {}
for t in rows('trajectories.jsonl'): traj[t['case_id']] = t
EV = collections.defaultdict(dict)
for e in rows('turn_evaluations.jsonl'): EV[e['case_id']][e['assistant_turn']] = e
UT = collections.defaultdict(dict)
for u in rows('user_turns.jsonl'):
    if u.get('mode') == 'next_turn': UT[u['case_id']][u.get('user_turn_index')] = u
PTS = collections.defaultdict(list)
for p in rows('sampling_points.jsonl'):
    for x in (p.get('possible_points') or p.get('points') or []): PTS[p['case_id']].append(dict(x, selected=x.get('point_id') in (p.get('selected_point_ids') or [])))
BP = {b['point_id'] for b in rows('branch_points.jsonl')}
PAIRS = rows('branch_pairs.jsonl')
KIND = {'prevention': 'P', 'supported_recovery': 'R', 'healthy_continuation': 'C', 'A': 'A', 'B': 'B'}
cases = sorted(traj, key=lambda c: (0 if c.startswith('DVI') else 1, c))
def w(name, records):
    with open(out / name, 'w') as h:
        for r in records: h.write(json.dumps(r, ensure_ascii=False) + '\n')
# trajectories + annotations
T, A, UE, SEL = [], [], [], []
for c in cases:
    t = traj[c]; ev = EV[c]; n = max(ev) if ev else 0
    T.append(dict(trajectory_id=c, assistant_turns=n, messages=t.get('messages') or [], terminal_code=(t.get('ending_reason') or 'unknown').replace('_', ' '),
                  task=t.get('purpose'), language=t.get('language')))
    for k in sorted(ev):
        e = ev[k]; prev_serious = any(ev[j]['local_quality'] == 'serious' for j in range(1, k))
        tags = []
        if e.get('repeats_earlier_failed_reply'): tags.append('repeats rejected reply')
        if e.get('maths_content'): tags.append('maths hold')
        if e.get('used_latest_guidance') in ('no', 'partly'): tags.append('ignored guidance')
        evidence = [x for x in [e.get('error_summary'), e.get('decisive_evidence')] if x] + list(e.get('factual_or_subject_errors') or [])
        A.append(dict(annotation_id=f'{c}:a{k}', trajectory_id=c, turn_index=k, local_quality=e['local_quality'], task=t.get('purpose'), language=t.get('language'),
                      issue_tags=tags, evidence=evidence[:6], recovery_opportunity=prev_serious, recovery_success=(e['local_quality'] in ('good', 'minor') and e.get('used_latest_guidance') == 'yes')))
    for i, u in sorted(UT[c].items()):
        UE.append(dict(trajectory_id=c, turn_index=i, message=dict(role='user', content=u.get('message', '')), move=u.get('move')))
    for p in PTS.get(c, []):
        if p.get('selected') or p.get('point_id') in BP: SEL.append(dict(trajectory_id=c, depth=p.get('before_assistant_turn'), selection_kind=KIND.get(p.get('kind'), '?')))
# branch candidates and their verdicts, one row per sampled alternative reply
JUD = {j['point_id']: j for j in rows('branch_judgements.jsonl')}
VERD = {}
for pid, j in JUD.items():
    for bt in j.get('batches', []):
        r = bt.get('ranking') or {}
        for letter, cid in (r.get('letter_to_candidate_id') or {}).items():
            VERD[cid] = dict(verdict=(r.get('verdicts') or {}).get(letter) or (r.get('verdicts') or {}).get(cid),
                             issues=(r.get('issues') or {}).get(cid) or (r.get('issues') or {}).get(letter) or [],
                             note=(r.get('notes') or {}).get(cid) or (r.get('notes') or {}).get(letter) or '',
                             chosen=(bt.get('chosen') == cid), rejected=(bt.get('rejected') == cid))
for pid, j in JUD.items():                      # 60-dialogue collection: one ranking per point, exact duplicates share a verdict
    r = j.get('ranking')
    if not r or j.get('batches'):
        continue
    for cid in r.get('letter_to_candidate_id', {}).values():
        VERD[cid] = dict(verdict=r['verdicts'].get(cid), issues=r['issues'].get(cid, []), note=r['notes'].get(cid, ''),
                         chosen=(j.get('chosen') == cid and j.get('result') == 'pair_accepted'), rejected=(j.get('rejected') == cid and j.get('result') == 'pair_accepted'))
    for dup, original in (j.get('duplicate_of') or {}).items():
        VERD[dup] = dict(VERD.get(original, {}), note='exact duplicate of reply ' + original.rsplit(':c', 1)[-1] + ' (judged once)', chosen=False, rejected=False)
CANDS = []
for cd in rows('branch_candidates.jsonl'):
    pid = cd['point_id']; j = JUD.get(pid, {}); v = VERD.get(cd['candidate_id'], {})
    CANDS.append(dict(trajectory_id=cd['case_id'], point_id=pid, depth=j.get('before_assistant_turn'), kind=j.get('kind'),
                      candidate_index=cd.get('candidate_index'), text=cd.get('text'), **v))
BJROWS = [dict(trajectory_id=j['case_id'], point_id=pid, depth=j.get('before_assistant_turn'), kind=j.get('kind'),
               samples_judged=j.get('samples_judged', j.get('unique_texts')), found_within_4=j.get('found_within_4', j.get('paired')),
               found_within_8=j.get('found_within_8'), result=j.get('result'),
               report_phrase=j.get('report_phrase') or f"{j.get('acceptable_unique') or 0} acceptable of {j.get('unique_texts')} distinct replies ({j.get('sampled')} sampled): {j.get('result', '').replace('_', ' ')}")
          for pid, j in JUD.items()]
w('branch_candidates.jsonl', CANDS); w('branch_judgements.jsonl', BJROWS)
w('trajectories.jsonl', T); w('annotations.jsonl', A); w('user_events.jsonl', UE); w('selection.jsonl', SEL); w('adjudications.jsonl', [])
w('preferences.jsonl', [dict(trajectory_id=p['case_id'], depth=p.get('depth'), pair_id=p.get('pair_id'), chosen=p.get('chosen'), rejected=p.get('rejected')) for p in PAIRS])
# collection counters (amendment deliverable): groups, endings, A/B eligibility and absence, change types, candidates, calls, cost
if SET != 'v2':                                   # the collection (or a collection dry run given by path)
    SEEDS = {s['case_id']: s for s in json.load(open(RL / 'dialogue_v2' / 'collection60' / 'seeds.json'))['seeds']}
    SP = {r['case_id']: r for r in rows('sampling_points.jsonl')}
    groups = collections.defaultdict(collections.Counter)
    for c in SEEDS:
        g = SEEDS[c]['group']; groups[g]['planned'] += 1
        if c in traj: groups[g]['collected'] += 1; groups[g]['ending:' + (traj[c].get('ending_reason') or 'unknown')] += 1
    ab = collections.Counter(); absent = collections.Counter(); change_types = collections.Counter(); change_quality = collections.Counter()
    for c, r in SP.items():
        kinds = {p['kind'] for p in r.get('possible_points', [])}
        for k in ('A', 'B'):
            ab[f"{SEEDS.get(c, {}).get('group', '?')}:{k}:{'present' if k in kinds else 'absent'}"] += 1
        for k, why in (r.get('absent') or {}).items(): absent[f'{k}: {why}'] += 1
        for cp in r.get('change_points', []):
            if cp.get('instruction_change'): change_types[cp.get('change_type') or cp.get('move')] += 1; change_quality[cp.get('change_quality') or 'unlabelled'] += 1
    cand = dict(points=len(JUD), sampled=sum(j.get('sampled', 0) for j in JUD.values()), distinct=sum(j.get('unique_texts', 0) for j in JUD.values()),
                acceptable=sum(j.get('acceptable_unique') or 0 for j in JUD.values()), pairs=len(PAIRS),
                by_kind={k: dict(points=sum(1 for j in JUD.values() if j.get('kind') == k), pairs=sum(1 for p in PAIRS if p.get('point_kind') == k)) for k in ('A', 'B')})
    calls = collections.Counter()
    for root in ROOTS:
        reserved = {r['call_id']: r for r in J(root / 'call_ledger.jsonl') if r.get('record') == 'call_reserved'}
        for r in J(root / 'call_ledger.jsonl'):
            if r.get('record') == 'call_completed' and r.get('status') == 'complete' and r['call_id'] in reserved:
                calls[f"{reserved[r['call_id']].get('provider')}:{reserved[r['call_id']].get('phase')}"] += 1
    gpu = [r for r in J(RL / 'dialogue_v2' / 'runtime' / 'gpu_ledger.jsonl') if r.get('record') == 'gpu_stop' and (r.get('api_created_at') or '') >= '2026-09-17T16:28']
    opening_calls = sum(sum(json.load(open(f))['sol_calls'].values()) for f in (RL / 'dialogue_v2' / 'collection60' / 'runs').glob('C60-*/receipt.json'))
    json.dump(dict(groups={g: dict(v) for g, v in groups.items()}, ab=dict(ab), absent=dict(absent), change_types=dict(change_types),
                   change_quality=dict(change_quality), candidates=cand, calls=dict(calls),
                   gpu_sessions=[dict(pod=r.get('pod_id'), stage=r.get('stage'), eur=r.get('cost_eur_charged')) for r in gpu],
                   opening_generation_sol_calls=opening_calls,
                   independent_conversations=len(traj)), open(out / 'collection_counters.json', 'w'), indent=1, ensure_ascii=False)
# report: quality by depth, new-failure risk, endings
first = {c: next((k for k in sorted(EV[c]) if EV[c][k]['local_quality'] == 'serious'), None) for c in cases}
maxd = max((max(EV[c]) for c in cases if EV[c]), default=1)
qbd, nfr = {}, {}
for d in range(1, maxd + 1):
    reached = [c for c in cases if d in EV[c]]
    q = collections.Counter(EV[c][d]['local_quality'] for c in reached)
    qbd[str(d)] = dict(quality={k: q.get(k, 0) for k in ('good', 'minor', 'serious')}, denominator_reached=len(reached))
    at_risk = [c for c in reached if (first[c] is None or first[c] >= d)]
    new_serious = [c for c in at_risk if first[c] == d]
    nfr[str(d)] = dict(at_risk=len(at_risk), new_serious=len(new_serious), risk=(len(new_serious) / len(at_risk) if at_risk else 0.0))
json.dump(dict(quality_by_depth=qbd, new_failure_risk=nfr,
               ending_reasons=dict(collections.Counter((traj[c].get('ending_reason') or 'unknown') for c in cases))),
          open(out / 'quality_depth_report.json', 'w'), indent=1, ensure_ascii=False)
print('wrote', out, len(T), 'chats,', len(A), 'annotations,', len(SEL), 'selected prefixes,', len(CANDS), 'alternative replies,', len(PAIRS), 'pairs')
