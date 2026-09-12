#!/usr/bin/env python3
"""Math cut 2, preparation only (no Sol calls; the Sol batches are WRITTEN here and run after the weekly reset).
Owner rules (13 Sept): trust the verifiable source; verify TRANSLATIONS by fidelity to the English on a sample (the 2% rule), never by solvability;
no weaker-model agreement filter; keep Level 5; targets = the reference derivations at the source's length, translated, with \\boxed kept.
Steps: (1) join cut 1's 9,999 translations with the cached English sources (openai/gsm8k, EleutherAI/hendrycks_math) by problem text to recover the
reference solution; (2) sample NEW English MATH Level-5 problems (quota) to be translated; (3) write three Sol batch files: fidelity sample (300),
solution translations (all), Level-5 problem translations; (4) an acceptance checker for the assembled rows (length distribution vs the source,
\\boxed present, level quotas, decimal comma). Usage: python3 prepare_cut2.py [--level5 1500] [--fidelity-sample 300]  (needs the sfttrain venv: datasets)."""
import argparse, json, os, random, re, collections, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); CUT1 = os.path.join(HERE, '..', 'cut1')
def load_jsonl(p): return [json.loads(l) for l in open(p) if l.strip()]
def norm(t): return re.sub(r'\s+', ' ', (t or '')).strip()
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--level5', type=int, default=1500); ap.add_argument('--fidelity-sample', type=int, default=300); ap.add_argument('--seed', type=int, default=42); a = ap.parse_args()
    rng = random.Random(a.seed); out = os.path.join(HERE, 'prep'); os.makedirs(out, exist_ok=True)
    from datasets import load_dataset
    gsm = load_dataset('openai/gsm8k', 'main', split='train'); gsm_by = {norm(r['question']): r for r in gsm}
    math_rows = []
    for cfg in ('algebra', 'counting_and_probability', 'geometry', 'intermediate_algebra', 'number_theory', 'prealgebra', 'precalculus'):
        for r in load_dataset('EleutherAI/hendrycks_math', cfg, split='train'): r = dict(r); r['subject'] = cfg; math_rows.append(r)
    math_by = {norm(r['problem']): r for r in math_rows}
    tr = load_jsonl(os.path.join(CUT1, 'translated', 'translated.jsonl')); joined = []; miss = 0
    for r in tr:
        src = gsm_by.get(norm(r['problem_en'])) if r['src'] == 'gsm8k' else math_by.get(norm(r['problem_en']))
        if not src: miss += 1; continue
        sol_en = src['answer'] if r['src'] == 'gsm8k' else src['solution']
        joined.append(dict(r, solution_en=sol_en, subject=src.get('subject'), level_src=src.get('level')))
    print(f'joined {len(joined)} of {len(tr)} translations with their English reference solution ({miss} unmatched)')
    w = [len(j['solution_en'].split()) for j in joined]; print('reference solution words: median', st.median(w), 'p90', sorted(w)[int(len(w) * .9)])
    json.dump(dict(joined=len(joined), unmatched=miss, solution_words_median=st.median(w)), open(f'{out}/join_summary.json', 'w'), indent=1)
    with open(f'{out}/translations_with_reference.jsonl', 'w') as f: [f.write(json.dumps(j, ensure_ascii=False) + '\n') for j in joined]
    # Level-5 candidates (new; need translation)
    used = {norm(j['problem_en']) for j in joined}
    l5 = [r for r in math_rows if r['level'] == 'Level 5' and norm(r['problem']) not in used]; rng.shuffle(l5); l5 = l5[:a.level5]
    by_subj = collections.Counter(r['subject'] for r in l5); print('Level-5 candidates', len(l5), dict(by_subj))
    with open(f'{out}/level5_candidates_en.jsonl', 'w') as f: [f.write(json.dumps(dict(id=f"math5_{i}", problem_en=r['problem'], solution_en=r['solution'], subject=r['subject'], level='Level 5'), ensure_ascii=False) + '\n') for i, r in enumerate(l5)]
    # Sol batch 1: fidelity sample (translation vs English), to measure the error rate; the 2% rule decides whether the pool enters unfiltered
    samp = rng.sample(joined, min(a.fidelity_sample, len(joined)))
    with open(f'{out}/batch_fidelity_sample.jsonl', 'w') as f:
        for j in samp: f.write(json.dumps(dict(id=j['id'], task='fidelity', problem_en=j['problem_en'], problem_el=j['problem_el'], instruction='Compare the Greek problem with the English one. Report faithful=true only if every number, condition, quantity and question is preserved (localisation of names, currency and decimal comma is allowed). List every discrepancy.'), ensure_ascii=False) + '\n')
    # Sol batch 2: solution translations (reference derivation -> Greek, full length, \\boxed kept, decimal comma, euro after the number)
    with open(f'{out}/batch_solution_translations.jsonl', 'w') as f:
        for j in joined: f.write(json.dumps(dict(id=j['id'], task='translate_solution', problem_el=j['problem_el'], solution_en=j['solution_en'], ref=j['ref'], instruction='Translate the reference solution into natural Greek at the SAME length and step structure; keep every equation; end with the final answer in \\boxed{} exactly as the reference; decimal comma; euro after the number; do not shorten.'), ensure_ascii=False) + '\n')
    # Sol batch 3: Level-5 problem translations (fidelity-checked later by batch 1's rule on a sample)
    with open(f'{out}/batch_level5_translations.jsonl', 'w') as f:
        for r in load_jsonl(f'{out}/level5_candidates_en.jsonl'): f.write(json.dumps(dict(id=r['id'], task='translate_problem', problem_en=r['problem_en'], instruction='Translate the problem into natural Greek preserving every number, condition and the question; localise names and currency only when it does not change the mathematics.'), ensure_ascii=False) + '\n')
    print('batches written to', out, ': fidelity', len(samp), 'solutions', len(joined), 'level5', len(l5))
if __name__ == '__main__': main()
