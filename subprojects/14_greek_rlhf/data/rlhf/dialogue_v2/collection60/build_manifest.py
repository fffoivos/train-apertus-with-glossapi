#!/usr/bin/env python3
"""Frozen allocation for the 60-dialogue collection (DIALOGUE_COLLECTION_60_AMENDMENT_20260917.md): 30 correction/revision,
15 troubleshooting, 15 learning. Slots use the generator 0.2 slot schema so openings are produced by generator_v02/generate.py
(--manifest this file). Languages follow the approved shares (el 70 / en 20 / others 10); difficulty, attitude and register
follow target_distribution_v1 within-seeded defaults; detail follows the generator manifest's shares. Deterministic.
Usage: python3 data/rlhf/dialogue_v2/collection60/build_manifest.py"""
import collections, hashlib, json, pathlib, random, sys
HERE = pathlib.Path(__file__).resolve().parent; RL = HERE.parents[1]; GEN = RL / 'generator_v02'
sys.path.insert(0, str(GEN))
from manifest import lr, DETAIL                                   # same largest-remainder and detail shares as the generator manifest
TARGET = json.load(open(RL / 'target_distribution_v1.json')); KINDS = json.load(open(GEN / 'task_kinds.json'))
SEED = 20260917
GROUPS = {   # group -> (category, case prefix, {(purpose, subtype): count}, {language: count})
    'correction': ('existing_type', 'C60C', {('everyday', 'write_or_rewrite_message'): 4, ('everyday', 'rewrite_supplied_draft'): 4,
                   ('everyday', 'plan_or_organise'): 4, ('everyday', 'summarise_supplied_text'): 3, ('instruction', 'edit_preserving_values'): 4,
                   ('instruction', 'multi_constraint_composition'): 4, ('instruction', 'strict_format'): 3, ('factual', 'grounded_in_supplied_text'): 4},
                   {'el': 21, 'en': 6, 'fr': 1, 'de': 1, 'es': 1}),
    'troubleshooting': ('troubleshooting', 'C60T', {('everyday', 'troubleshoot'): 15}, {'el': 11, 'en': 3, 'it': 1}),
    'learning': ('learning', 'C60L', {('everyday', 'explain_simply'): 8, ('math', 'explanation_and_learning'): 7}, {'el': 10, 'en': 3, 'fr': 1, 'pt': 1}),
}
NO_BARE = {'multi_constraint_composition'}
def main():
    rng = random.Random(SEED); slots = []
    people = {l: json.load(open(GEN / 'axes' / f'people_{l}.json'))['items'] for l in TARGET['language_shares_percent']}
    situations = json.load(open(GEN / 'axes' / 'situations.json'))['items']; topics = json.load(open(GEN / 'axes' / 'topics.json'))['items']
    used = collections.defaultdict(set)
    for group, (category, prefix, subtypes, langs) in GROUPS.items():
        g = [dict(group=group, category=category, purpose=p, subtype=s, packet=KINDS[p][s]['packet']) for (p, s), n in subtypes.items() for _ in range(n)]
        rng.shuffle(g)
        lang_values = [l for l, n in langs.items() for _ in range(n)]; rng.shuffle(lang_values)
        for s, l in zip(g, lang_values): s['language'] = l
        def assign(axis, shares, ok=lambda s, v: True):
            values = [v for v, k in lr(len(g), shares).items() for _ in range(k)]; rng.shuffle(values)
            for s, v in zip(g, values): s[axis] = v
            for s in g:                                            # compatibility repair by swapping, as in the generator manifest
                if ok(s, s[axis]): continue
                for t in g:
                    if t is not s and ok(s, t[axis]) and ok(t, s[axis]): s[axis], t[axis] = t[axis], s[axis]; break
        d = TARGET['within_seeded_defaults_percent']
        assign('difficulty', d['difficulty']); assign('attitude', d['attitude'])
        assign('register', d['register'], ok=lambda s, v: v != 'greeklish' or s['language'] == 'el')
        assign('detail', DETAIL, ok=lambda s, v: not (s['packet'] and v == 'short') and not (v == 'bare' and s['subtype'] in NO_BARE))
        for i, s in enumerate(g, 1):
            s['slot_id'] = s['case_id'] = f'{prefix}{i:02d}'
            pool = [p for p in people[s['language']] if p not in used['person_' + s['language']]] or people[s['language']]
            s['person'] = rng.choice(pool); used['person_' + s['language']].add(s['person'])
            s['situation'] = rng.choice(situations); s['topic'] = rng.choice(topics)
        slots += g
    problems = [s['slot_id'] for s in slots if (s['register'] == 'greeklish' and s['language'] != 'el') or (s['packet'] and s['detail'] == 'short') or (s['detail'] == 'bare' and s['subtype'] in NO_BARE)]
    out = dict(version='dialogue-collection60-manifest-v1', amendment='DIALOGUE_COLLECTION_60_AMENDMENT_20260917.md', seed=SEED, frozen=True,
               group_totals={g: sum(1 for s in slots if s['group'] == g) for g in GROUPS},
               language_totals=dict(collections.Counter(s['language'] for s in slots)),
               subtype_totals=dict(collections.Counter(f"{s['group']}/{s['purpose']}/{s['subtype']}" for s in slots)),
               axis_totals={a: dict(collections.Counter(s[a] for s in slots)) for a in ('difficulty', 'attitude', 'register', 'detail')},
               compatibility_violations=problems, task_kinds_sha16=hashlib.sha256((GEN / 'task_kinds.json').read_bytes()).hexdigest()[:16], slots=slots)
    json.dump(out, open(HERE / 'manifest.json', 'w'), ensure_ascii=False, indent=1)
    print({k: out[k] for k in ('group_totals', 'language_totals', 'axis_totals', 'compatibility_violations')})
if __name__ == '__main__': main()
