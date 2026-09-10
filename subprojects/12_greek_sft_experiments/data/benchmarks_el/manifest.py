#!/usr/bin/env python3
"""Provenance manifest for every Greek benchmark (astra R6/R7 and the companion review's HIGH 3): upstream source, pinned revision, licence, item counts,
translation pipeline stages with the models used, checks, content hashes of the frozen files, and what is NOT checked. Writes benchmarks_el/MANIFEST.json.
Usage: python3 manifest.py"""
import hashlib, json, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
UPSTREAM = {
 'multichallenge': dict(source='github.com/ekwinox117/multi-challenge (Scale AI)', commit='5ccefcca6a39 (2025-02-05)', file='data/benchmark_questions.jsonl', licence='NO LICENSE FILE in the repository; research use only, do not redistribute the Greek version without permission', paper='arXiv:2501.17399',
                        protocol='fixed-history continuation: the candidate writes the next assistant turn after the last user turn; judge sees ONLY the response and TARGET_QUESTION (upstream src/evaluator.py, gpt-4o-2024-08-06 temp 0, "Be VERY STRICT"); pass = verdict == PASS_CRITERIA (always YES); score = pass rate per axis'),
 'ifbench': dict(source='github.com/allenai/IFBench + HF allenai/IFBench_test', commit='1c40f0c10d9b (2026-09-09); HF revision 2e8a48de45ff', file='data/IFBench_test.jsonl (300 prompts, 58 constraint ids)', licence='code Apache-2.0; data ODC-BY-1.0', paper='arXiv:2507.02833',
                 protocol='per-prompt verifiable constraints; strict and loose prompt-level and instruction-level accuracy as in IFEval; the 29 IFBench-train constraints are NOT part of this set and must not enter any SFT mix'),
 'xstest': dict(source='github.com/paul-rottger/xstest', commit='d7bb5bd738c1 (2025-02-24)', file='xstest_prompts.csv (250 safe + 200 unsafe, 18 types × 25)', licence='CC-BY-4.0', paper='arXiv:2308.01263',
                protocol='refusal taxonomy full_compliance / partial_refusal / full_refusal by a judge; safe and unsafe prompts scored separately; our addition: adequacy'),
 'math500': dict(source='HF HuggingFaceH4/MATH-500 (the 500-problem subset of MATH test used by Lightman et al. 2023)', commit='HF revision 6e4ed1a2a79a', file='test.jsonl (500; levels 1–5; 7 subjects)', licence='MATH dataset: MIT (Hendrycks et al.)', paper='arXiv:2305.20050 / 2103.03874',
                 protocol='boxed-answer extraction + equivalence (equiv500 = upstream Hendrycks strip_string normalisation + numeric + sympy, validated on the 500 reference answers (self, digit-perturbation rejection, format variants; numbers in the scorer self-test)); report by level and subject'),
}
FILES = {'multichallenge': ['source/benchmark_questions.jsonl', 'conversations_el.jsonl', 'conversations_el_final.jsonl'], 'ifbench': ['source/IFBench_test.jsonl', 'prompts_el.jsonl', 'prompts_el_final.jsonl'],
         'xstest': ['source/xstest_prompts.csv', 'prompts_el.jsonl', 'prompts_el_final.jsonl'], 'math500': ['source/test.jsonl', 'problems_el.jsonl', 'problems_el_final.jsonl']}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''): h.update(chunk)
    return h.hexdigest()[:16]


def main():
    man = dict(built=time.strftime('%Y-%m-%d %H:%M'), pipeline='Sol (gpt-5.6-sol, Codex CLI 0.144.1, effort medium) translation with in-call self-check → programmatic checks → cross-check by Claude Opus (different vendor) on the critical subsets (all IFBench prompts and kwargs, all XSTest items, all MultiChallenge target questions + a 59-conversation random audit, all MATH-500 items failing the programmatic check + a 59-item random audit) → Sol repair of flagged items → frozen *_final.jsonl',
               not_checked='exposure through the Apertus pretraining corpus and our CPT corpus (not inspectable locally; the CPT corpus check is a cluster job, DATA_TODO 32); exposure through prior model selection (none: these sets have never been run on any of our checkpoints as of the build date); native-speaker audit of the frozen sets (owner, 59 items per set, pending)',
               benchmarks={})
    for b, meta in UPSTREAM.items():
        d = os.path.join(HERE, b); files = {}
        for f in FILES[b]:
            p = os.path.join(d, f)
            if os.path.exists(p): files[f] = dict(sha256_16=sha(p), lines=sum(1 for _ in open(p, errors='ignore')))
        extra = {}
        for name in ('cross_check_summary.json', 'summary.json', 'overlap_classes.json'):
            p = os.path.join(d, name)
            if os.path.exists(p): extra[name] = json.load(open(p))
        man['benchmarks'][b] = dict(**meta, files=files, **extra)
    p = os.path.join(HERE, 'decontam_report.json')
    if os.path.exists(p): man['decontamination'] = json.load(open(p))
    json.dump(man, open(os.path.join(HERE, 'MANIFEST.json'), 'w'), ensure_ascii=False, indent=1); print('MANIFEST.json written:', {b: list(v['files']) for b, v in man['benchmarks'].items()})


if __name__ == '__main__': main()
