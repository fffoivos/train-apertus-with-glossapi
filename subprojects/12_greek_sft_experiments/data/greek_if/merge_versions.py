#!/usr/bin/env python3
"""Merge the built versions (v1, v2, …) into one set: exact-duplicate prompts dropped, near-duplicate requests reported, distributions summarised.
Usage: python3 merge_versions.py <out_dir> <version_dir> [<version_dir> ...]   (each holds out/greek_if_sft.jsonl, out/greek_if_dpo.jsonl)"""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import constraints as C
out, versions = sys.argv[1], sys.argv[2:]; os.makedirs(out, exist_ok=True)
sys.path.insert(0, HERE); from build_dataset import fidelity_ok, FIDELITY_FORMS
sft, dpo, seen, dup, fid = [], [], set(), 0, 0
for v in versions:
    for r in (json.loads(l) for l in open(f'{v}/out/greek_if_sft.jsonl')):
        key = re.sub(r'\s+', ' ', r['user']).strip().lower()
        if key in seen: dup += 1; continue
        if r['meta']['form'] in FIDELITY_FORMS and not fidelity_ok(r['user'], r['assistant']): fid += 1; continue   # v1/v2 rows built before the fidelity filter
        seen.add(key); r['version'] = os.path.basename(v.rstrip('/')); sft.append(r)
    for r in (json.loads(l) for l in open(f'{v}/out/greek_if_dpo.jsonl')): r['version'] = os.path.basename(v.rstrip('/')); dpo.append(r)
for name, rows in (('greek_if_sft.jsonl', sft), ('greek_if_dpo.jsonl', dpo)):
    with open(f'{out}/{name}', 'w') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
# near-duplicate requests across versions: same first 12 words
pref = collections.Counter(' '.join(C.words(r['user'])[:12]) for r in sft); shared = sum(c for c in pref.values() if c > 1) / max(1, len(sft))
fam = collections.Counter(c['family'] for r in sft for c in r['meta']['constraints']); lvl = collections.Counter(r['meta']['level'] for r in sft); form = collections.Counter(r['meta']['form'] for r in sft); ver = collections.Counter(r['version'] for r in sft)
summ = dict(sft_rows=len(sft), dpo_pairs=len(dpo), exact_duplicates_dropped=dup, fidelity_dropped=fid, shared_12word_prefix_share=round(shared, 4), by_version=dict(ver), by_level=dict(sorted(lvl.items())), by_form=dict(form), families=len(fam), min_family_rows=min(fam.values()), max_family_rows=max(fam.values()),
            mean_answer_words=round(sum(len(C.words(r['assistant'])) for r in sft) / max(1, len(sft))), authored_share=round(sum(bool(r['meta'].get('authored')) for r in sft) / max(1, len(sft)), 3))
json.dump(summ, open(f'{out}/summary.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))
