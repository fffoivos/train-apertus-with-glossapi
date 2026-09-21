#!/usr/bin/env python3
"""Round 3 pairs and summary.
Pair rule (plan §24, CK4; maths plan A3): inside one judged batch of four,
- general route (maths_content none): chosen = highest-ranked reinforce; rejected = lowest-ranked non-reinforce; batch margin best_vs_worst = clear; texts differ.
- maths route (purpose math only): the same rule on batches judged with the maths reviewer prompt (judge_rank4_maths_en.txt); embedded maths is on the general route.
Batches are scanned in stage order (replies 0-7, 8-15, 16-31); the first batch meeting the rule gives the prompt's pair (one pair per prompt).
Usage: python3 data/rlhf/round3/pairs.py [--dir data/rlhf/round3]"""
import argparse, collections, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
def J(p): return [json.loads(l) for l in open(p) if l.strip()] if pathlib.Path(p).exists() else []
def norm(s): return ' '.join((s or '').split())
def load(d):
    rows = J(d / 'round3_all.jsonl'); samples = collections.defaultdict(dict)
    for s in J(d / 'round3_samples.jsonl'):
        if s.get('k', -1) >= 0: samples[s['id']][s['k']] = s['text']
    gen, mat = collections.defaultdict(list), collections.defaultdict(list)
    for st in (1, 2, 3):
        for r in J(d / f'judged_general_s{st}.jsonl'):
            if 'ranking_k' in r: gen[r['id']].append(dict(r, stage=st))
        for r in J(d / f'judged_maths_s{st}.jsonl'):
            if 'ranking_k' in r: mat[r['id']].append(dict(r, stage=st))
    refs = {r['id']: r for r in J(d / 'maths_references.jsonl')}
    return rows, samples, gen, mat, refs
def pair_for(r, samples, gen, mat, refs):
    """Ordinary pair rule on the prompt's own rubric: top-ranked reinforce vs lowest-ranked non-reinforce inside one batch, clear margin, distinct texts."""
    pid = r['id']; S = samples[pid]
    batches = mat[pid] if r.get('purpose') == 'math' else gen[pid]          # maths rubric only where maths is the task
    for b in sorted(batches, key=lambda x: (x['stage'], x['batch'])):
        rk = b['ranking_k']; v = {int(k): x for k, x in b['by_k'].items()}
        ch = next((k for k in rk if v[k].get('verdict') == 'reinforce'), None); rj = next((k for k in reversed(rk) if v[k].get('verdict') != 'reinforce'), None)
        if ch is None or rj is None or (b.get('verdict') or {}).get('best_vs_worst') != 'clear' or norm(S.get(ch)) == norm(S.get(rj)): continue
        return dict(chosen_k=ch, rejected_k=rj, stage=b['stage'], batch=b['batch'], route='maths' if batches is mat[pid] else 'general', rubric_sha=b.get('rubric_sha')), 'eligible'
    return None, 'no_batch_meets_pair_rule' if batches else 'not_judged'
def superseded_ids(d, rows):
    """Prompts whose SAMPLED version later failed verification and was regenerated: those must not produce a pair.
    A slot whose sampled version is the regenerated one is fine, even though an older version of it was superseded."""
    import glob
    status = {}
    for f in glob.glob(str(d.parent / 'generator_v02' / 'runs' / '*' / 'prompts.jsonl')):
        for l in open(f):
            x = json.loads(l); status[(x['slot_id'], x['run'])] = x['status']
    return {r['id'] for r in rows if status.get((r['id'], r.get('run'))) == 'superseded'}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--dir', default=str(HERE)); a = ap.parse_args(); d = pathlib.Path(a.dir)
    rows, samples, gen, mat, refs = load(d); out = []; cells = collections.defaultdict(collections.Counter)
    dropped = superseded_ids(d, rows)
    for r in rows:
        p, why = pair_for(r, samples, gen, mat, refs)
        if r['id'] in dropped: p, why = None, 'held:superseded_after_verification'
        verdicts = [x.get('verdict') for b in gen[r['id']] for x in b['by_k'].values()]
        verdicts += [x.get('verdict') for b in mat[r['id']] for x in b['by_k'].values()]
        judged = len(set(int(k) for b in gen[r['id']] + mat[r['id']] for k in b['by_k']))
        any_pos = 'reinforce' in verdicts
        out.append(dict(id=r['id'], logical_id=r['logical_id'], purpose=r['purpose'], language=r['language'], maths_content=r.get('maths_content'), replies_sampled=len(samples[r['id']]), replies_judged=judged, has_positive=any_pos, pair=p, status=why))
        c = cells[f"{r['purpose']}/{r['language']}"]; c['prompts'] += 1; c['with_positive'] += any_pos; c['eligible_pairs'] += bool(p); c['held'] += why.startswith('held')
    with open(d / 'round3_pairs.jsonl', 'w') as h:
        for x in out: h.write(json.dumps(x, ensure_ascii=False) + '\n')
    summary = dict(prompts=len(out), superseded_after_verification=len(dropped), eligible_pairs=sum(bool(x['pair']) for x in out), held=sum(x['status'].startswith('held') for x in out), with_positive=sum(x['has_positive'] for x in out),
                   by_status=dict(collections.Counter(x['status'] for x in out)), by_cell={k: dict(v) for k, v in sorted(cells.items())},
                   by_stage=dict(collections.Counter(x['pair']['stage'] for x in out if x['pair'])))
    json.dump(summary, open(d / 'round3_summary.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps({k: summary[k] for k in ('prompts', 'eligible_pairs', 'held', 'with_positive', 'by_status', 'by_stage')}, ensure_ascii=False))
if __name__ == '__main__': main()
