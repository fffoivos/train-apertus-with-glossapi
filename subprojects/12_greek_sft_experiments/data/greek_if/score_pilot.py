#!/usr/bin/env python3
"""Score pilot answers with the constraint checkers and print the readouts of plan §5 (E1–E6) plus prompt-diversity metrics.
Usage: python3 score_pilot.py <answers.jsonl> <scores.jsonl> <summary.json> <prompts.jsonl> [more ...]"""
import collections, itertools, json, os, random, re, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import constraints as C
def ngrams(s, n=5): s = re.sub(r'\s+', ' ', s.lower()); return {s[i:i+n] for i in range(max(0, len(s)-n+1))}
def jacc(a, b): return len(a & b) / max(1, len(a | b))
def rate(xs): return round(sum(xs) / len(xs), 3) if xs else None
def main():
    ans_path, scores_path, summ_path, files = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    rows = {json.loads(l)['id']: json.loads(l) for fn in files for l in open(fn)}; ans = {json.loads(l)['id']: json.loads(l)['answer'] for l in open(ans_path)} if os.path.exists(ans_path) else {}
    scored = []
    for rid, r in rows.items():
        if rid not in ans: continue
        res = C.check_all(ans[rid], r['constraints'], r['request']); chk = [x for x in res if x['checkable']]
        scored.append(dict(id=rid, design=rid.split('_')[0], level=r['level'], domain=r['domain'], form=r['form'], persona_style=r['persona_style'], pair_id=r.get('pair_id'), variant=r.get('variant'),
                           results=res, all_pass=all(x['ok'] for x in chk) if chk else None, n_words=len(C.words(ans[rid])), answer=ans[rid]))
    with open(scores_path, 'w') as f:
        for s in scored: f.write(json.dumps(s, ensure_ascii=False) + '\n')
    by = lambda key: {k: dict(n=len(v), prompt_pass=rate([s['all_pass'] for s in v if s['all_pass'] is not None]), mean_words=round(statistics.mean(s['n_words'] for s in v))) for k, v in sorted(collections.defaultdict(list, {k: [s for s in scored if key(s) == k] for k in {key(s) for s in scored}}).items())}
    fam = collections.defaultdict(list); famlvl = collections.defaultdict(list)
    for s in scored:
        for x in s['results']:
            if x['checkable']: fam[x['family']].append(x['ok']); famlvl[(x['family'], s['level'])].append(x['ok'])
    per_family = {k: dict(n=len(v), pass_rate=rate(v), level1=rate(famlvl.get((k, 1), []))) for k, v in sorted(fam.items(), key=lambda kv: rate(kv[1]) or 0)}
    # E6 wording invariance: agreement of prompt-level pass across the 3 phrasings of a pair
    pairs = collections.defaultdict(list)
    for s in scored:
        if s['pair_id'] is not None: pairs[s['pair_id']].append(s['all_pass'])
    invariance = dict(pairs=len(pairs), unanimous=rate([len(set(v)) == 1 for v in pairs.values() if len(v) == 3])) if pairs else None
    # diversity of the prompts (all prompts, answered or not)
    P = list(rows.values()); rng = random.Random(0); samp = rng.sample(P, min(400, len(P))); grams = [ngrams(r['prompt']) for r in samp]
    pair_j = [jacc(a, b) for a, b in itertools.combinations(grams, 2)]; toks = [w for r in P for w in C.words(r['prompt'])]
    pref = collections.Counter(' '.join(C.words(r['prompt'])[:12]) for r in P); shared_prefix = sum(c for c in pref.values() if c > 1) / len(P)
    within = {}
    for d in {r['domain'] for r in P}:
        g = [ngrams(r['prompt']) for r in P if r['domain'] == d][:60]; js = [jacc(a, b) for a, b in itertools.combinations(g, 2)]; within[d] = rate([j > 0.5 for j in js]) if js else None
    diversity = dict(prompts=len(P), answered=len(scored), domains=len({r['domain'] for r in P}), subtopics=len({r['subtopic'] for r in P}), forms=len({r['form'] for r in P}), form_family_cells=len({(r['form'], c['family']) for r in P for c in r['constraints']}),
                     mean_pairwise_5gram_jaccard=round(statistics.mean(pair_j), 4), type_token_ratio=round(len(set(toks)) / len(toks), 4), shared_12token_prefix_share=round(shared_prefix, 4), near_duplicate_rate_within_domain=within)
    summ = dict(overall=dict(n=len(scored), prompt_pass=rate([s['all_pass'] for s in scored if s['all_pass'] is not None])), by_design=by(lambda s: s['design']), by_level=by(lambda s: s['level']), by_domain=by(lambda s: s['domain']), by_form=by(lambda s: s['form']), by_persona_style=by(lambda s: s['persona_style']), per_family=per_family, wording_invariance=invariance, diversity=diversity)
    json.dump(summ, open(summ_path, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(dict(overall=summ['overall'], by_level=summ['by_level'], worst_families={k: v for k, v in list(per_family.items())[:8]}, invariance=invariance, diversity={k: v for k, v in diversity.items() if k != 'near_duplicate_rate_within_domain'}), ensure_ascii=False, indent=1))
if __name__ == '__main__': main()
