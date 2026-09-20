Review target: GATE 1 RE-REVIEW (checkpoint R3b) for the three pilot continuations 1-G4F6P0--00/--01/--02 (legacy M0/M1/M2), after your HOLD (docs/reviews/ASTRA_gate1_pilots_20260914.md). This pack answers each of your findings with the artifacts you asked for, inlined below (you have no filesystem access in this session). Judge only whether the HOLD items are closed; the plan and datasets were reviewed earlier.
Your findings and what is supplied: BLOCKER (dry-runs, preflight, decision rule, readout fixture) -> §A, §B, §F, §G. HIGH validity coverage -> §C (the sample headers' 'validity none' was the severity enum value meaning no issue; the ledger below is keyed by the exact exported text hash and records the validator effort). HIGH replay contradiction -> §D (my brief line was wrong; the receipts govern). HIGH per-ID byte attestation -> §E. HIGH two Level-5 prompts -> §H (English sources shown; both ambiguities are source-inherited; both prompts clarified and re-exported identically to all arms). MEDIUM drop interpretation + GSM slots -> §I. MEDIUM clipped excerpts -> §J (the seven rows unabridged). LOW -> logged.

=== §A TRAINER DRY-RUNS (frozen configs, PLAN lines verbatim) ===
--- M0: {"arm": "M0", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 16, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 1, "eval_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M0/dev.jsonl", "eval_rows": 370, "eval_tokens": 93254, "expected_full_train_tokens": null, "gradient_accumulation_steps": 4, "learning_rate": 1e-05, "lr_scheduler_type": "cosine_with_min_lr", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": 0.1, "model": "/iopsstor/scratch/cscs/fffoivos/sft_round1/runs/R2_stage1/epoch1", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 7332, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 459, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "M0_lr1e-5_1ep_cos", "steps_per_epoch": 459, "train_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M0/train.jsonl", "train_rows": 71717, "train_tokens": 29963435, "warmup_ratio": 0.03, "world_size": 4}
DRY_RUN_OK
--- M1: {"arm": "M1", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 16, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 1, "eval_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M1/dev.jsonl", "eval_rows": 370, "eval_tokens": 105789, "expected_full_train_tokens": null, "gradient_accumulation_steps": 4, "learning_rate": 1e-05, "lr_scheduler_type": "cosine_with_min_lr", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": 0.1, "model": "/iopsstor/scratch/cscs/fffoivos/sft_round1/runs/R2_stage1/epoch1", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 7653, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 479, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "M1_lr1e-5_1ep_cos", "steps_per_epoch": 479, "train_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M1/train.jsonl", "train_rows": 71717, "train_tokens": 31280850, "warmup_ratio": 0.03, "world_size": 4}
DRY_RUN_OK
--- M2: {"arm": "M2", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 16, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 1, "eval_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M2/dev.jsonl", "eval_rows": 383, "eval_tokens": 114383, "expected_full_train_tokens": null, "gradient_accumulation_steps": 4, "learning_rate": 1e-05, "lr_scheduler_type": "cosine_with_min_lr", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": 0.1, "model": "/iopsstor/scratch/cscs/fffoivos/sft_round1/runs/R2_stage1/epoch1", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 7875, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 493, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "M2_lr1e-5_1ep_cos", "steps_per_epoch": 493, "train_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M2/train.jsonl", "train_rows": 73075, "train_tokens": 32185559, "warmup_ratio": 0.03, "world_size": 4}
DRY_RUN_OK

=== §B PREFLIGHT (budget) ===
preflight pilots_M0_M1_M2: used 67.412 nh + projected 4.5 nh = CHF 193.44 of cap 230.0 -> OK

=== §C COVERAGE LEDGER SUMMARY (data/math/cut2/final/coverage_summary.json) ===
{
 "exported_translated_rows": 10306,
 "fully_covered": 10306,
 "problems": {},
 "audit_flags_adjudicated": 5,
 "audit_flags_total": 5,
 "first_stage_flagged_adjudicated": 722,
 "first_stage_flagged": 722,
 "validity_effort_counts": {
  "high": 10306
 },
 "repaired_rows": 51,
 "polish": {
  "unchanged": 7348,
  "edited": 2945,
  "reverted": 13
 },
 "severity": {
  "none": 10281,
  "minor": 25
 }
}
First 12 ledger rows:
{"id": "c2_gsm_40", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_40|9caa28c6", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "unchanged", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_41", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_41|6ee8426b", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "unchanged", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_42", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_42|e0599d86", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "unchanged", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_43", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_43|3851d0b4", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "edited", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_44", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_44|9b5eb8f1", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "unchanged", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_45", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_45|eafd6249", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "unchanged", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_46", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_46|714bb4ea", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "unchanged", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_47", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_47|e4ad9b08", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "unchanged", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_48", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_48|c58ca9a2", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "edited", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_49", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_49|7e94d986", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "unchanged", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_70", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_70|80598f3a", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "unchanged", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}
{"id": "c2_gsm_71", "file": "rows_M1.jsonl", "level": "gsm", "fidelity_first_stage": true, "audit_flag": null, "adjudicated": false, "adjudication": null, "validity_key": "gsm_71|84832564", "validity_present": true, "validity_effort": "high", "validity_valid": true, "validity_severity": "none", "polish_status": "unchanged", "generation_file": "solutions_el.jsonl", "repaired": false, "problems": []}

=== §D REPLAY RECONCILIATION (from the arm receipts; one convention: tokenizer content tokens + 8 per turn) ===
M0: total 28.55M (sup 18.36M) | english 8.94M (sup 5.93M) | greek 3.28M (sup 1.61M) | replay 16.33M = 57.2% of tokens (58.9% of supervised); replay rows 21,467 = 29.9% of rows (10% of every non-maths parent config)
M1: total 30.32M (sup 20.14M) | english 8.94M | greek 5.06M (sup 3.38M) | replay 16.33M = 53.9% (53.7% sup)
M2: total 31.33M (sup 20.93M) | english 8.94M | greek 6.06M (sup 4.18M) | replay 16.33M = 52.1% (51.7% sup)
The earlier '≈19M / 65%' line in the first brief was a rough figure and is withdrawn; the recipe is unchanged.

=== §E BYTE-LEVEL ATTESTATION (results/pilots/attestation.json) ===
{
 "arms": [
  "M0",
  "M1",
  "M2"
 ],
 "attestation": {
  "pairs_checked": 14038,
  "user_mismatch": 0,
  "native_mismatch": 0,
  "m1_in_m2_mismatch": 0
 },
 "manifests": {
  "M0": "aa8a9c815e6f509c310acfb54ea133059c8ecf92c5cb3319fb177d881a77c780",
  "M1": "fd72f69983e93099c4cea454fbd72ac4bafc1761f7d21e6463c8d4077203dd77",
  "M2": "634c6e3429182197ee870d56a67226a000eaaae0285f7701e2298d080d3c13e6"
 }
}
Checker output:
caches: english_originals.mmlu_arc_hellaswag_truthfulqa_20260905.jsonl:28449:1fb6d835, greek_mmlu.6a03aa06b68beb932fb75edff3a34e50b3674649.jsonl:16632:52395e62, gsm8k.740312add88f781978c0658806c59bc2815b9866.jsonl:1319:12d2145d, ifbench_el.jsonl:586:607ae20f, ifeval.966cd89545d6b6acfd7638bc708b98261ca58e84.jsonl:541:e0c1fda7, math200_confirm.jsonl:400:000148d2, math500_el.jsonl:1000:e29827dc, mgsm_el.jsonl:250:b96a9dd2, multichallenge_el.jsonl:3308:72468f1e, native_asep_mcqa.jsonl:2346:f8230d12, native_demosqa.jsonl:600:3d769837, native_gpcr.jsonl:208:ae256518, native_medical_mcqa.jsonl:432:ae4f9346, xstest_el.jsonl:900:b3a910ef
M0: 71717 train rows, 28.5M tokens (18.4M supervised), ≈436 updates, greek train 13898 / dev 140, blocks {'greek_math': 13898, 'math_en_math': 14348, 'math_en_gsm': 22004, 'replay': 21467}, benchmark hits 8-gram 0 / 13-gram 0
M1: 71717 train rows, 30.3M tokens (20.1M supervised), ≈463 updates, greek train 13898 / dev 140, blocks {'greek_math': 13898, 'math_en_math': 14348, 'math_en_gsm': 22004, 'replay': 21467}, benchmark hits 8-gram 0 / 13-gram 0
M2: 73075 train rows, 31.3M tokens (20.9M supervised), ≈478 updates, greek train 15256 / dev 153, blocks {'math_en_gsm': 22004, 'greek_math': 15256, 'math_en_math': 14348, 'replay': 21467}, benchmark hits 8-gram 0 / 13-gram 0
OK: M0 and M1 carry the same 13898 Greek maths prompts (multiset)
OK: M0/M1 Greek ids are exactly paired
OK: M2 = M1 + 1358 Level-5 rows
OK: replay identical multisets across arms (21467 rows)
OK: math_en_gsm identical multisets across arms (22004 rows)
OK: math_en_math identical multisets across arms (14348 rows)
OK: Greek dev sets paired (140 problems)
OK: no English training row shares a problem with the 102 dev problems
OK: byte-level attestation {'pairs_checked': 14038, 'user_mismatch': 0, 'native_mismatch': 0, 'm1_in_m2_mismatch': 0}
RESULT PASS

=== §F FROZEN DECISION RULE (plan §4, verbatim) ===
Decision rule, frozen before launch (astra F1/F5), hierarchical: primary contrast M1−M0, secondary M2−M1 (acted on only if the primary qualifies; a negative primary stops Phase C without any secondary recommendation),
each on MATH-500-el paired items with a one-sided 90% bootstrap lower bound (4,000 resamples, seed 1).
Measured discordance between our existing checkpoints on this benchmark is 9–15% of items
(`data/math/en/discordance_math500_el.txt`), so at q≈15% the SE of a paired difference is ≈1.7 pp: the screen
detects effects of ≥5 pp reliably (stage 1 vs R3, +4.8 pp, has LB +2.6) and passes a true 3-pp effect only
about half the time. It is a screen for the large effect H9 predicts, not a test of small gains.

| Outcome | Rule | Action |
|---|---|---|
| guardrail failure | IFEval-el or MGSM-el more than 2 pp below M0, or greedy loops (content line ×5) or truncations (finish_reason=length) on MATH-500-el above M0 by **more than 5 of 500** (frozen band, 14 Sept 12:05: 1-G2F1P1's 7 loops / 29 truncations and stage 1's 23 / 60 differ by far more than 5, so 5 is inside the run-to-run noise we have seen on identical data), or any part of the readout missing (English MATH-500, IFEval, MGSM, loops) | that arm cannot advance, whatever its maths score |
| qualified improvement | observed gain ≥3 pp and one-sided 90% LB > 0, no guardrail failure | advance the eligible arm (M2 only if M2−M1 also qualifies, else M1) |
| positive but inconclusive | gain > 0, LB ≤ 0 or gain < 3 pp, no guardrail failure | keep the checkpoint; spend ≤1 nh of the reserve on the predefined dose check: continue that checkpoint for a second epoch over the maths blocks only, re-read |
| negative | gain ≤ 0 | H9 is not supported by this screen; stop Phase C, write up, re-plan the maths lane |

Guardrail tolerances are screening tolerances with paired intervals reported ("no observed breach", not
"retention established"); single seed, stated. No arm advances by default.


=== §G READOUT IMPLEMENTATION (data/pilot_summary.py, verbatim) + FIXTURE OUTPUT ===
#!/usr/bin/env python3
"""Pilot readout under the frozen rule (R4 plan §4): MATH-500-el paired contrasts M1-M0 (primary) and M2-M1 (secondary), one-sided 90% bootstrap LB
(4,000 resamples, seed 1), guardrails IFEval-el (langdetect-rescored, prompt strict) and MGSM-el within 2 pp of M0, truncations (finish_reason=length)
reported, English MATH-500 as safeguard, stage 1 as the zero-exposure reference. Usage: python3 pilot_summary.py M0 M1 M2 -> results/pilots/summary.md"""
import json, os, sys, random, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from gfp_names import label as gfp
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OUT = f'{ROOT}/results/pilots'; arms = sys.argv[1:]
if arms[:2] != ['M0', 'M1'] or (len(arms) == 3 and arms[2] != 'M2') or len(arms) not in (2, 3): raise SystemExit('arms must be M0 M1 [M2] in this order (the experiment hierarchy)')
EXPECTED = set(json.load(open(f'{ROOT}/data/benchmarks_el/math500/ids_frozen.json')))
assert len(EXPECTED) == 500, 'frozen MATH-500 id list must hold exactly 500 ids'
def score(path):
    if not os.path.exists(path): return None
    sc = json.load(open(path)); ids = [r['id'] for r in sc['rows']]
    if len(ids) != len(set(ids)) or set(ids) != EXPECTED: raise SystemExit(f'{path}: expected exactly the {len(EXPECTED)} MATH-500 ids, got {len(set(ids))} unique of {len(ids)} rows; no partial outputs in the readout')
    adj = path.replace('_score.json', '_adjudicated.jsonl')   # optional Sol adjudication of unresolved rows (data/benchmarks_el/math500/adjudicate_unresolved.py)
    if os.path.exists(adj):
        import hashlib; resp = {json.loads(l)['id']: json.loads(l) for l in open(path.replace('_score.json', '.jsonl'))}
        upd = {json.loads(l)['id']: json.loads(l) for l in open(adj)}
        for r in sc['rows']:
            u = upd.get(r['id'])
            if u and r['extracted'] in (None, '') and u.get('equivalent') is True and u.get('response_sha256') == hashlib.sha256((resp.get(r['id'], {}).get('response') or '').encode('utf-8')).hexdigest() and u.get('reference') == r['answer']: r['adjudicated'] = True
        sc['adjudication_coverage'] = dict(unresolved=sum(1 for r in sc['rows'] if r['extracted'] in (None, '')), adjudicated=sum(1 for r in sc['rows'] if r['id'] in upd), accepted=sum(1 for r in sc['rows'] if r.get('adjudicated')))
        sc['adjudicated_acc'] = sum(1 for r in sc['rows'] if r['equiv500'] or r.get('adjudicated')) / len(sc['rows'])
    return sc
def items(sc): return {r['id']: bool(r['equiv500']) for r in sc['rows']} if sc else {}   # PRIMARY = deterministic equiv500 (the scorer every comparator was scored with); adjudicated accuracy is reported alongside
def ifeval(label):
    p = f'{ROOT}/results/{label}/ifeval_el_rescored.json'
    if os.path.exists(p): d = json.load(open(p)); return d.get('prompt_strict') or d.get('prompt_level_strict_acc') or d
    return None
def mgsm(label):
    for p in glob.glob(f'{ROOT}/results/{label}/ilsp/*mgsm*.json'):
        d = json.load(open(p)); r = d.get('results', d); k = next((k for k in r if 'mgsm' in k), None)
        if k: return r[k].get('exact_match,flexible-extract') or r[k].get('exact_match') or r[k]
    return None
def loops(a):
    """R3 diagnosis rule: a Greek MATH-500 response 'loops' when one content line (>12 chars) repeats 5+ times (stage 1 23/500, arm B 7/500, R3 35/500)."""
    import collections; p = f'{OUT}/bench_{a}/math500_el.jsonl'
    if not os.path.exists(p): return None
    n = 0
    for l in open(p):
        r = json.loads(l); c = collections.Counter(x.strip() for x in (r.get('response') or '').splitlines() if len(x.strip()) > 12)
        n += any(v >= 5 for v in c.values())
    return n
def lb(a, b, n_boot=4000, seed=1):
    ids = sorted(set(a) & set(b)); d = [int(a[i]) - int(b[i]) for i in ids]
    if not d: return None
    rng = random.Random(seed); bs = sorted(sum(d[rng.randrange(len(d))] for _ in d) / len(d) for _ in range(n_boot))
    return dict(n=len(d), delta=100 * sum(d) / len(d), q=100 * sum(1 for x in d if x) / len(d), lb90=100 * bs[int(0.10 * n_boot)])
S = {a: score(f'{OUT}/bench_{a}/math500_el_score.json') for a in arms}; E = {a: score(f'{OUT}/bench_{a}/math500_en_score.json') for a in arms}
S1 = score(f'{ROOT}/results/R3_single/bench_S1/math500_el_score.json'); E1 = score(f'{ROOT}/results/R3_single/bench_S1/math500_en_score.json')
lines = ['# Pilot readout (frozen rule, plan §4)', '', '| arm | MATH-500-el | loops (line x5) | truncated | MATH-500-en | IFEval-el (rescored) | MGSM-el |', '|---|---:|---:|---:|---:|---:|---:|']
lines.append(f"| G2F1P0@epoch1 (reference) | {S1['equiv500_acc']*100:.1f} | 23 | {S1['truncated']} | {E1['equiv500_acc']*100:.1f} | 62.85 | 48.8 |")
for a in arms:
    s, e = S[a], E[a]; lines.append(f"| {gfp(a)} | {s['equiv500_acc']*100:.1f} | {loops(a)} | {s['truncated']} | {e['equiv500_acc']*100:.1f} | {ifeval(a + '_ep1')} | {mgsm(a + '_ep1')} |" if s and e else f'| {a} | missing ||||||')
lines += ['', '| contrast | n | delta (pp) | discordant % | one-sided 90% LB | verdict |', '|---|---:|---:|---:|---:|---|']
def verdict(r):
    if r is None: return 'missing'
    if r['delta'] >= 3 and r['lb90'] > 0: return 'qualified improvement (guardrails to check)'
    if r['delta'] > 0: return 'positive but inconclusive -> dose check'
    return 'negative'
pairs = [(arms[i + 1], arms[i]) for i in range(len(arms) - 1)]
for x, y in pairs:
    r = lb(items(S[x]), items(S[y])); lines.append(f"| {x}-{y} (el) | {r['n']} | {r['delta']:+.1f} | {r['q']:.1f} | {r['lb90']:+.1f} | {verdict(r)} |" if r else f'| {x}-{y} | missing |||||')
    r = lb(items(E[x]), items(E[y])); lines.append(f"| {x}-{y} (en, safeguard) | {r['n']} | {r['delta']:+.1f} | {r['q']:.1f} | {r['lb90']:+.1f} | — |" if r else '')
# guardrails evaluated, not just printed: eligibility per candidate arm vs M0 (frozen tolerances, plan §4: IFEval/MGSM −2 pp, loops and truncations ≤ M0 + 5 of 500)
def num(x):
    try: return float(x)
    except Exception: return None
def fmt_gate(a):
    p = f'{ROOT}/results/{a}_ep1/light_results.json'
    if os.path.exists(p): return json.load(open(p)).get('format_gate_dev50')
    return None
base = arms[0]; g0 = dict(ifeval=num(ifeval(base + '_ep1')), mgsm=num(mgsm(base + '_ep1')), loops=loops(base), trunc=S[base]['truncated'] if S[base] else None)
lines += ['', '| arm | IFEval-el vs M0 | MGSM-el vs M0 | loops vs M0 | truncated vs M0 | unresolved (no extracted answer) | format gate | guardrails |', '|---|---:|---:|---:|---:|---:|---|---|']
elig = {}
def pp(x, y):   # difference in percentage points whatever the scale
    return (x - y) * (100 if max(x, y) <= 1 else 1)
for a in arms:
    unres = sum(1 for r in S[a]['rows'] if r['extracted'] in (None, '')) if S[a] else None
    if a == base: lines.append(f"| {a} | — | — | {g0['loops']} | {g0['trunc']} | {unres} | {fmt_gate(a)} | baseline |"); continue
    gi, gm, gl, gt = num(ifeval(a + '_ep1')), num(mgsm(a + '_ep1')), loops(a), (S[a]['truncated'] if S[a] else None)
    checks = []
    if S[a] is None or E[a] is None: checks.append('MATH-500 el/en missing')
    if gi is None or g0['ifeval'] is None: checks.append('ifeval missing')
    elif pp(gi, g0['ifeval']) < -2: checks.append('IFEval breach')
    if gm is None or g0['mgsm'] is None: checks.append('mgsm missing')
    elif pp(gm, g0['mgsm']) < -2: checks.append('MGSM breach')
    if gl is None or g0['loops'] is None: checks.append('loops missing')
    elif gl > g0['loops'] + 5: checks.append('loops breach')
    if gt is None or g0['trunc'] is None: checks.append('truncations missing')
    elif gt > g0['trunc'] + 5: checks.append('truncation breach')
    elig[a] = not checks; lines.append(f"| {a} | {gi} vs {g0['ifeval']} | {gm} vs {g0['mgsm']} | {gl} vs {g0['loops']} | {gt} vs {g0['trunc']} | {unres} | {fmt_gate(a)} | {'PASS' if not checks else 'FAIL: ' + ', '.join(checks)} |")
def outcome(x, y):
    r = lb(items(S[x]), items(S[y]))
    if r is None: return 'missing'
    if not elig.get(x, False): return 'cannot advance (guardrail failure or missing readout)'
    if r['delta'] >= 3 and r['lb90'] > 0: return 'qualified improvement'
    if r['delta'] > 0: return 'positive but inconclusive -> dose check on this checkpoint'
    return 'negative -> stop Phase C, write up, re-plan the maths lane'
lines += ['', '## Decision (frozen rule, plan §4; hierarchical: the secondary contrast is acted on only if the primary qualifies)', '']
prim = outcome('M1', 'M0'); lines.append(f'- primary {gfp("M1")} vs {gfp("M0")}: **{prim}**')
adv = 'M1' if prim == 'qualified improvement' else None
if 'M2' in arms:
    sec = outcome('M2', 'M1') if adv else 'not evaluated for action (hierarchy: the primary contrast did not qualify)'
    lines.append(f'- secondary {gfp("M2")} vs {gfp("M1")}: **{sec}**')
    if adv and sec == 'qualified improvement': adv = 'M2'
lines.append(f"- advancing arm: **{gfp(adv) if adv else 'none'}** (no arm advances by default)")
adjs = {a: S[a].get('adjudicated_acc') for a in arms if S[a]}
if any(v is not None for v in adjs.values()): lines.append(f"- adjudicated accuracies (Sol, unresolved rows, response-bound; secondary): {adjs}; coverage {{a: S[a].get('adjudication_coverage') for a in arms if S[a]}}")
# guardrail uncertainty: approximate unpaired binomial SE on the difference (paired item files are not available for every guardrail); reported, not a gate
def se(p, n): return (p * (1 - p) / n) ** 0.5 if p is not None and n else None
lines += ['', 'Guardrail uncertainty (approximate, unpaired binomial): IFEval-el n≈541 prompts → SE of a difference ≈ 2.9 pp at 65%; MGSM-el n=250 → ≈ 4.4 pp at 50%. Tolerances are screening tolerances, not demonstrated non-inferiority. Primary scorer = equiv500 for every arm and comparator.']
open(f'{OUT}/summary.md', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))

--- fixture (results/pilots/readout_fixture.md) ---
# Readout fixture (fabricated scores from the stage-1 prediction files; deleted after the run)

Case A: M1 +~4 pp over M0, M2 +~0.6 over M1, IFEval/MGSM results MISSING -> must not advance.

exit 0
# Pilot readout (frozen rule, plan §4)

| arm | MATH-500-el | loops (line x5) | truncated | MATH-500-en | IFEval-el (rescored) | MGSM-el |
|---|---:|---:|---:|---:|---:|---:|
| G2F1P0@epoch1 (reference) | 12.8 | 23 | 60 | 16.4 | 62.85 | 48.8 |
| 1-G4F6P0--00 (M0) | 12.8 | 27 | 60 | 16.4 | None | None |
| 1-G4F6P0--01 (M1) | 17.0 | 27 | 60 | 16.4 | None | None |
| 1-G4F6P0--02 (M2) | 17.6 | 27 | 60 | 16.4 | None | None |

| contrast | n | delta (pp) | discordant % | one-sided 90% LB | verdict |
|---|---:|---:|---:|---:|---|
| M1-M0 (el) | 500 | +4.2 | 4.2 | +3.0 | qualified improvement (guardrails to check) |
| M1-M0 (en, safeguard) | 500 | +0.0 | 0.0 | +0.0 | — |
| M2-M1 (el) | 500 | +0.6 | 8.6 | -1.2 | positive but inconclusive -> dose check |
| M2-M1 (en, safeguard) | 500 | +0.0 | 0.0 | +0.0 | — |

| arm | IFEval-el vs M0 | MGSM-el vs M0 | loops vs M0 | truncated vs M0 | unresolved (no extracted answer) | format gate | guardrails |
|---|---:|---:|---:|---:|---:|---|---|
| M0 | — | — | 27 | 60 | 0 | None | baseline |
| M1 | None vs None | None vs None | 27 vs 27 | 60 vs 60 | 0 | None | FAIL: ifeval missing, mgsm missing |
| M2 | None vs None | None vs None | 27 vs 27 | 60 vs 60 | 0 | None | FAIL: ifeval missing, mgsm missing |

## Decision (frozen rule, plan §4; hierarchical: the secondary contrast is acted on only if the primary qualifies)

- primary 1-G4F6P0--01 (M1) vs 1-G4F6P0--00 (M0): **cannot advance (guardrail failure or missing readout)**
- secondary 1-G4F6P0--02 (M2) vs 1-G4F6P0--01 (M1): **not evaluated for action (hierarchy: the primary contrast did not qualify)**
- advancing arm: **none** (no arm advances by default)

Guardrail uncertainty (approximate, unpaired binomial): IFEval-el n≈541 prompts → SE of a difference ≈ 2.9 pp at 65%; MGSM-el n=250 → ≈ 4.4 pp at 50%. Tolerances are screening tolerances, not demonstrated non-inferiority. Primary scorer = equiv500 for every arm and comparator.


Case B: a 499-row score file -> must refuse.

exit 1
/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/pilots/bench_M1/math500_el_score.json: expected exactly the 500 MATH-500 ids, got 499 unique of 499 rows; no partial outputs in the readout


=== §H THE TWO LEVEL-5 PROMPTS: English source, original Greek, repaired Greek ===
--- math5_269
EN source: Joe wants to find all the four-letter words that begin and end with the same letter. How many combinations of letters satisfy this property?
EL original: Ο Γιάννης θέλει να βρει όλες τις λέξεις τεσσάρων γραμμάτων που αρχίζουν και τελειώνουν με το ίδιο γράμμα. Πόσοι συνδυασμοί γραμμάτων ικανοποιούν αυτή την ιδιότητα;
EL repaired: Ο Γιάννης θέλει να βρει όλες τις λέξεις τεσσάρων γραμμάτων (οποιεσδήποτε ακολουθίες γραμμάτων από τα 26 γράμματα του λατινικού αλφαβήτου, όχι μόνο λέξεις λεξικού) που αρχίζουν και τελειώνουν με το ίδιο γράμμα. Πόσοι συνδυασμοί γραμμάτων ικανοποιούν αυτή την ιδιότητα;
reason: source-inherited ambiguity (the English says 'four-letter words' with no alphabet; the published solution uses 26 letters); clarified so the Greek prompt is self-consistent with its target (astra gate 1, 14 Sept)
--- math5_946
EN source: Let $f(n)$ be a function that, given an integer $n$, returns an integer $k$, where $k$ is the smallest possible integer such that $k!$ is divisible by $n$. Given that $n$ is a multiple of 15, what is the smallest value of $n$ such that $f(n) > 15$?
EL original: Έστω $f(n)$ μια συνάρτηση η οποία, για έναν ακέραιο $n$, επιστρέφει έναν ακέραιο $k$, όπου $k$ είναι ο μικρότερος δυνατός ακέραιος τέτοιος ώστε το $k!$ να διαιρείται με το $n$. Δεδομένου ότι το $n$ είναι πολλαπλάσιο του 15, ποια είναι η μικρότερη τιμή του $n$ τέτοια ώστε $f(n) > 15$;
EL repaired: Έστω $f(n)$ μια συνάρτηση η οποία, για έναν θετικό ακέραιο $n$, επιστρέφει έναν θετικό ακέραιο $k$, όπου $k$ είναι ο μικρότερος δυνατός θετικός ακέραιος τέτοιος ώστε το $k!$ να διαιρείται με το $n$. Δεδομένου ότι το $n$ είναι θετικό πολλαπλάσιο του 15, ποια είναι η μικρότερη τιμή του $n$ τέτοια ώστε $f(n) > 15$;
reason: source-inherited ambiguity (the English says 'an integer n'; the published solution assumes positive integers); clarified to positive integers (astra gate 1, 14 Sept)

=== §I DROPS AND GSM SLOTS ===
Cut-2 drop reasons (final receipt):
{"translated_gsm8k:unfaithful_both_stages": 75, "translated_gsm8k:invalid_derivation": 81, "translated_gsm8k:no_cut1_pair": 96, "translated_gsm8k:length_short": 2, "translated_gsm8k:repeated_lines": 9, "translated_gsm8k:unpolished": 2, "translated_math:no_cut1_pair": 647, "translated_math:unfaithful_both_stages": 14, "translated_math:invalid_derivation": 23, "translated_math:math500_13gram": 87, "translated_math:no_solution": 9, "translated_math:length_short": 10, "translated_math:boxed_not_equivalent": 9, "translated_math:repeated_lines": 5, "translated_math5:invalid_derivation": 20, "translated_math5:unfaithful_both_stages": 47, "translated_math5:math500_13gram": 47, "translated_math5:no_solution": 3, "translated_math5:repeated_lines": 3}
no_cut1_pair = the pairing rule (the round-one editor had dropped those problems' terse rows), an availability exclusion, not a quality failure; the contrast concerns the retained paired population (8,930 problems).
GSM8K: 7,417 problems; 7,390 have >=3 distinct solutions, 14 have two, 13 have one -> 22,211 slots; 7 identical-solution collapses.
Loop rule corrected before the final assembly: the earlier rule flagged LaTeX delimiters and case analyses; the corrected rule (content lines, 5+ repeats) drops 17 runaways.

=== §J THE SEVEN CLIPPED SAMPLE ROWS, UNABRIDGED (exported text; all are training rows; dev membership noted) ===
--- c2_math_2469 dev=False validity_severity=none polished=edited
PROBLEM: Να βρεις τη μικρότερη λύση της εξίσωσης
\[\frac{2x}{x-2}+\frac{2x^2-24}{x}=11.\]
TARGET: Αρχικά εξετάζουμε τους περιορισμούς της εξίσωσης. Οι παρονομαστές δεν πρέπει να μηδενίζονται, άρα
\[
x\neq 0 \quad \text{και} \quad x\neq 2.
\]

Πολλαπλασιάζουμε και τα δύο μέλη με τον κοινό παρονομαστή $x(x-2)$:
\[
x(x-2)\left(\frac{2x}{x-2}+\frac{2x^2-24}{x}\right)=11x(x-2).
\]

Απλοποιώντας κάθε όρο, παίρνουμε
\[
2x^2+(2x^2-24)(x-2)=11x(x-2).
\]

Αναπτύσσουμε τα γινόμενα:
\[
(2x^2-24)(x-2)=2x^3-4x^2-24x+48
\]
και
\[
11x(x-2)=11x^2-22x.
\]

Επομένως,
\[
2x^2+2x^3-4x^2-24x+48=11x^2-22x.
\]

Συγκεντρώνουμε όλους τους όρους στο αριστερό μέλος:
\[
2x^3-2x^2-24x+48-11x^2+22x=0,
\]
άρα
\[
2x^3-13x^2-2x+48=0.
\]

Αναζητούμε ρητές ρίζες. Για $x=6$ έχουμε
\[
2(6)^3-13(6)^2-2(6)+48
=432-468-12+48=0,
\]
οπότε το $x-6$ είναι παράγοντας του πολυωνύμου. Η παραγοντοποίηση είναι
\[
2x^3-13x^2-2x+48=(x-6)(2x^2-x-8).
\]

Άρα
\[
(x-6)(2x^2-x-8)=0,
\]
οπότε είτε
\[
x=6
\]
είτε
\[
2x^2-x-8=0.
\]

Για τη δεύτερη εξίσωση, η διακρίνουσα είναι
\[
\Delta=(-1)^2-4\cdot2\cdot(-8)=1+64=65.
\]

Επομένως,
\[
x=\frac{-(-1)\pm\sqrt{65}}{2\cdot2}
=\frac{1\pm\sqrt{65}}{4}.
\]

Καμία από τις τρεις λύσεις δεν παραβιάζει τους περιορισμούς $x\neq0,2$. Επειδή $\sqrt{65}>1$, ισχύει
\[
\frac{1-\sqrt{65}}{4}<0<\frac{1+\sqrt{65}}{4}<6.
\]

Συνεπώς, η μικρότερη λύση είναι
\[
\boxed{\frac{1-\sqrt{65}}{4}}.
\]
--- c2_math_1762 dev=False validity_severity=none polished=unchanged
PROBLEM: Έστω $\mathbf{a}$ και $\mathbf{b}$ δύο διανύσματα και έστω $\mathbf{m}$ το μέσο τους. Αν $\mathbf{m}=\begin{pmatrix}3\\7\end{pmatrix}$ και $\mathbf{a}\cdot\mathbf{b}=6$, να βρεις την τιμή του $\|\mathbf{a}\|^2+\|\mathbf{b}\|^2$.
TARGET: Αφού το διάνυσμα $\mathbf{m}$ είναι το μέσο των διανυσμάτων $\mathbf{a}$ και $\mathbf{b}$, ισχύει
\[
\mathbf{m}=\frac{\mathbf{a}+\mathbf{b}}{2}.
\]

Πολλαπλασιάζοντας και τα δύο μέλη με $2$, παίρνουμε
\[
\mathbf{a}+\mathbf{b}=2\mathbf{m}.
\]

Εφόσον
\[
\mathbf{m}=\begin{pmatrix}3\\7\end{pmatrix},
\]
έχουμε
\[
\mathbf{a}+\mathbf{b}=2\begin{pmatrix}3\\7\end{pmatrix}
=\begin{pmatrix}6\\14\end{pmatrix}.
\]

Επομένως, το τετράγωνο του μέτρου του αθροίσματος είναι
\[
\|\mathbf{a}+\mathbf{b}\|^2
=\left\|\begin{pmatrix}6\\14\end{pmatrix}\right\|^2
=6^2+14^2
=36+196
=232.
\]

Από την άλλη πλευρά,
\[
\begin{aligned}
\|\mathbf{a}+\mathbf{b}\|^2
&=(\mathbf{a}+\mathbf{b})\cdot(\mathbf{a}+\mathbf{b})\\
&=\mathbf{a}\cdot\mathbf{a}+\mathbf{a}\cdot\mathbf{b}
+\mathbf{b}\cdot\mathbf{a}+\mathbf{b}\cdot\mathbf{b}\\
&=\|\mathbf{a}\|^2+2\mathbf{a}\cdot\mathbf{b}+\|\mathbf{b}\|^2.
\end{aligned}
\]

Άρα
\[
\|\mathbf{a}\|^2+\|\mathbf{b}\|^2
=\|\mathbf{a}+\mathbf{b}\|^2-2\mathbf{a}\cdot\mathbf{b}.
\]

Χρησιμοποιώντας ότι $\|\mathbf{a}+\mathbf{b}\|^2=232$ και $\mathbf{a}\cdot\mathbf{b}=6$, βρίσκουμε
\[
\|\mathbf{a}\|^2+\|\mathbf{b}\|^2
=232-2\cdot6
=232-12
=\boxed{220}.
\]
--- c1b_math_672 dev=False validity_severity=None polished=None
PROBLEM: Επιλέγονται τυχαία δύο διαφορετικοί αριθμοί από το σύνολο $S = \{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11\}$. Η πιθανότητα το άθροισμά τους να είναι 12 θα ήταν μεγαλύτερη, αν είχε προηγουμένως αφαιρεθεί από το σύνολο $S$ ο αριθμός $n$. Ποια είναι η τιμή του $n$;
TARGET: Τα δυνατά ζεύγη είναι \(\binom{11}{2}=55\).
Τα ζεύγη με άθροισμα \(12\) είναι \((1,11),(2,10),(3,9),(4,8),(5,7)\).
Άρα τα ευνοϊκά ζεύγη είναι \(5\).
\(P=\frac{5}{55}\)
\(P=\frac{1}{11}\)
Ο μόνος αριθμός που δεν ανήκει σε ευνοϊκό ζεύγος είναι το \(6\).
Αν αφαιρεθεί το \(6\), τα δυνατά ζεύγη γίνονται \(\binom{10}{2}=45\).
Τα ευνοϊκά ζεύγη παραμένουν \(5\).
\(P'=\frac{5}{45}\)
\(P'=\frac{1}{9}\)
\(\frac{1}{9}>\frac{1}{11}\)
Απάντηση: \(6\)
\boxed{6}
--- c2_math5_442 dev=False validity_severity=none polished=unchanged
PROBLEM: Έστω $a,$ $b,$ $c$ διακεκριμένοι μιγαδικοί αριθμοί τέτοιοι ώστε
\[\frac{a}{1 - b} = \frac{b}{1 - c} = \frac{c}{1 - a} = k.\]
Να βρείτε το άθροισμα όλων των δυνατών τιμών του $k.$
TARGET: Από την ισότητα των τριών κλασμάτων παίρνουμε
\[
a=k(1-b),\qquad b=k(1-c),\qquad c=k(1-a).
\]
Αντικαθιστούμε διαδοχικά τις δύο τελευταίες σχέσεις στην πρώτη:
\begin{align*}
a&=k(1-b)\\
&=k\bigl(1-k(1-c)\bigr)\\
&=k\bigl(1-k(1-k(1-a))\bigr).
\end{align*}
Αναπτύσσοντας το δεξί μέλος, έχουμε
\begin{align*}
a&=k\bigl(1-k+k^2(1-a)\bigr)\\
&=k-k^2+k^3-ak^3.
\end{align*}
Επομένως,
\[
ak^3+a-k^3+k^2-k=0.
\]
Η παράσταση παραγοντοποιείται ως
\[
(k^2-k+1)(ak+a-k)=0.
\]
Άρα εξετάζουμε δύο περιπτώσεις.

Αν
\[
ak+a-k=0,
\]
τότε
\[
a(k+1)=k.
\]
Η τιμή $k=-1$ δεν ικανοποιεί την εξίσωση, οπότε
\[
a=\frac{k}{k+1}.
\]
Με τον ίδιο ακριβώς τρόπο, εφαρμόζοντας τις κυκλικές σχέσεις για τα $b$ και $c$, προκύπτει
\[
b=\frac{k}{k+1},\qquad c=\frac{k}{k+1}.
\]
Τότε όμως $a=b=c$, αντίθετα με την υπόθεση ότι οι τρεις μιγαδικοί είναι διακεκριμένοι. Επομένως αυτή η περίπτωση απορρίπτεται.

Άρα αναγκαστικά
\[
k^2-k+1=0.
\]
Οι δύο ρίζες είναι
\[
k_1=\frac{1+i\sqrt3}{2},\qquad k_2=\frac{1-i\sqrt3}{2}.
\]
Οι τιμές αυτές είναι πράγματι δυνατές: για καθεμία μπορούμε να επιλέξουμε
\[
a=2,
\qquad b=2k-1,
\qquad c=-k,
\]
οπότε οι $a,b,c$ είναι διακεκριμένοι, κανένας παρονομαστής δεν μηδενίζεται και οι τρεις λόγοι ισούνται με $k$.

Τέλος, από τους τύπους του Vieta, το άθροισμα των ριζών της $k^2-k+1=0$ είναι
\[
k_1+k_2=-\frac{-1}{1}=1.
\]
Συνεπώς, το ζητούμενο άθροισμα είναι
\[
\boxed{1}
\]
--- c2_math5_1123 dev=False validity_severity=none polished=edited
PROBLEM: Έστω ότι οι $x,$ $y,$ και $z$ είναι θετικοί πραγματικοί αριθμοί. Να βρείτε την ελάχιστη τιμή της παράστασης
\[\frac{4z}{2x + y} + \frac{4x}{y + 2z} + \frac{y}{x + z}.\]
TARGET: Θέτουμε
\[
a=2x,\qquad b=y,\qquad c=2z.
\]
Επειδή οι $x,y,z$ είναι θετικοί πραγματικοί αριθμοί, ισχύει και $a,b,c>0$. Επίσης,
\[
x=\frac a2,\qquad y=b,\qquad z=\frac c2.
\]
Άρα η δοσμένη παράσταση γίνεται
\begin{align*}
\frac{4z}{2x+y}+\frac{4x}{y+2z}+\frac{y}{x+z}
&=\frac{4\cdot\frac c2}{a+b}+\frac{4\cdot\frac a2}{b+c}+\frac{b}{\frac a2+\frac c2}\\
&=\frac{2c}{a+b}+\frac{2a}{b+c}+\frac{2b}{a+c}\\
&=2\left(\frac{a}{b+c}+\frac{b}{a+c}+\frac{c}{a+b}\right).
\end{align*}

Θέτουμε
\[
S=\frac{a}{b+c}+\frac{b}{a+c}+\frac{c}{a+b}.
\]
Τότε
\begin{align*}
S+3
&=\left(\frac{a}{b+c}+1\right)+\left(\frac{b}{a+c}+1\right)+\left(\frac{c}{a+b}+1\right)\\
&=\frac{a+b+c}{b+c}+\frac{a+b+c}{a+c}+\frac{a+b+c}{a+b}\\
&=(a+b+c)\left(\frac1{b+c}+\frac1{a+c}+\frac1{a+b}\right).
\end{align*}

Όμως
\[
a+b+c=\frac12\big[(b+c)+(a+c)+(a+b)\big],
\]
οπότε
\[
S+3=\frac12\big[(b+c)+(a+c)+(a+b)\big]
\left(\frac1{b+c}+\frac1{a+c}+\frac1{a+b}\right).
\]

Από την ανισότητα Cauchy–Schwarz,
\[
\big[(b+c)+(a+c)+(a+b)\big]
\left(\frac1{b+c}+\frac1{a+c}+\frac1{a+b}\right)
\ge (1+1+1)^2=9.
\]
Επομένως,
\[
S+3\ge\frac92
\quad\Longrightarrow\quad
S\ge\frac92-3=\frac32.
\]
Άρα η αρχική παράσταση ικανοποιεί
\[
2S\ge 2\cdot\frac32=3.
\]

Η ισότητα στην Cauchy–Schwarz ισχύει όταν
\[
b+c=a+c=a+b,
\]
δηλαδή όταν $a=b=c$. Με βάση τους αρχικούς ορισμούς, αυτό ισοδυναμεί με
\[
2x=y=2z.
\]
Επομένως η τιμή $3$ πράγματι επιτυγχάνεται και είναι η ελάχιστη δυνατή.

\[
\boxed{3}
\]
--- c2_math5_1152 dev=False validity_severity=none polished=unchanged
PROBLEM: Οι κύκλοι $A,B$ και $C$ εφάπτονται εξωτερικά μεταξύ τους και εσωτερικά στον κύκλο $D$. Οι κύκλοι $B$ και $C$ είναι ίσοι. Ο κύκλος $A$ έχει ακτίνα 1 και διέρχεται από το κέντρο του $D$. Ποια είναι η ακτίνα του κύκλου $B$;

[asy]unitsize(1cm);
pair A,B,C,D;
A=(-1,0);
B=(0.66,0.88);
C=(0.66,-0.88);
D=(0,0);
draw(Circle(A,1),linewidth(0.7));
draw(Circle(B,0.88),linewidth(0.7));
draw(Circle(C,0.88),linewidth(0.7));
draw(Circle(D,2),linewidth(0.7));
label("$A$",A,A);
label("$B$",B,B);
label("$C$",C,C);
label("$D$",(-1.2,1.6),NW);
[/asy]
TARGET: Έστω $E,H$ και $F$ τα κέντρα των κύκλων $A,B$ και $D$ αντίστοιχα, και $G$ το σημείο επαφής των ίσων κύκλων $B$ και $C$. Θέτουμε
\[
FG=x \quad\text{και}\quad GH=y.
\]
Επειδή το $H$ είναι το κέντρο του κύκλου $B$, το $GH=y$ είναι η ακτίνα του κύκλου $B$.

Ο κύκλος $A$ έχει ακτίνα 1 και διέρχεται από το κέντρο $F$ του κύκλου $D$, άρα
\[
EF=1.
\]
Επιπλέον, οι κύκλοι $A$ και $D$ εφάπτονται εσωτερικά. Επομένως, η ακτίνα του $D$ είναι
\[
1+EF=1+1=2.
\]

Οι ίσοι κύκλοι $B$ και $C$ είναι συμμετρικοί ως προς την ευθεία $EFG$, οπότε $HG\perp EF$. Άρα τα τρίγωνα $EGH$ και $FGH$ είναι ορθογώνια στο $G$.

Οι κύκλοι $A$ και $B$ εφάπτονται εξωτερικά, επομένως
\[
EH=1+y.
\]
Επίσης,
\[
EG=EF+FG=1+x.
\]
Εφαρμόζοντας το Πυθαγόρειο θεώρημα στο τρίγωνο $EGH$, παίρνουμε
\[
(1+y)^2=(1+x)^2+y^2.
\]
Αναπτύσσοντας:
\[
1+2y+y^2=1+2x+x^2+y^2,
\]
άρα
\[
2y=2x+x^2
\]
και συνεπώς
\[
y=x+\frac{x^2}{2}.
\]

Ο κύκλος $B$ εφάπτεται εσωτερικά στον κύκλο $D$, του οποίου η ακτίνα είναι 2, άρα
\[
FH=2-y.
\]
Στο ορθογώνιο τρίγωνο $FGH$ έχουμε
\[
(2-y)^2=x^2+y^2.
\]
Αναπτύσσοντας:
\[
4-4y+y^2=x^2+y^2,
\]
οπότε
\[
4-4y=x^2
\]
και
\[
y=1-\frac{x^2}{4}.
\]

Εξισώνουμε τις δύο εκφράσεις του $y$:
\[
x+\frac{x^2}{2}=1-\frac{x^2}{4}.
\]
Πολλαπλασιάζοντας με 4:
\[
4x+2x^2=4-x^2,
\]
άρα
\[
3x^2+4x-4=0.
\]
Παραγοντοποιούμε:
\[
(3x-2)(x+2)=0.
\]
Επομένως,
\[
x=\frac23 \quad\text{ή}\quad x=-2.
\]
Για $x=\frac23$,
\[
y=\frac23+\frac{(2/3)^2}{2}
=\frac23+\frac{4/9}{2}
=\frac23+\frac29
=\frac89.
\]
Για $x=-2$ προκύπτει $y=0$, που δεν μπορεί να είναι ακτίνα κύκλου. Άρα η ακτίνα του κύκλου $B$ είναι
\[
\boxed{\frac{8}{9}}
\]
--- c2_math5_946 dev=False validity_severity=none polished=unchanged
PROBLEM: Έστω $f(n)$ μια συνάρτηση η οποία, για έναν θετικό ακέραιο $n$, επιστρέφει έναν θετικό ακέραιο $k$, όπου $k$ είναι ο μικρότερος δυνατός θετικός ακέραιος τέτοιος ώστε το $k!$ να διαιρείται με το $n$. Δεδομένου ότι το $n$ είναι θετικό πολλαπλάσιο του 15, ποια είναι η μικρότερη τιμή του $n$ τέτοια ώστε $f(n) > 15$;
TARGET: Θέτουμε
\[
n=15r,
\]
όπου ο \(r\) είναι θετικός ακέραιος. Ζητάμε τη μικρότερη τιμή του \(n\) για την οποία \(n\nmid 15!\), αφού τότε ο μικρότερος \(k\) με \(n\mid k!\) θα είναι μεγαλύτερος από \(15\).

Για κάθε \(r\leq 14\), ο αριθμός \(r\) διαιρεί το \(14!\). Επομένως,
\[
15!=15\cdot14!
\]
διαιρείται με το
\[
15r=n.
\]
Άρα, για \(r\leq14\), ισχύει \(f(n)\leq15\). Συνεπώς πρέπει
\[
r>14.
\]

Εξετάζουμε διαδοχικά τις επόμενες τιμές του \(r\).

Για \(r=15\), έχουμε
\[
n=15\cdot15=225.
\]
Όμως μέσα στο \(15!\) υπάρχουν οι διαφορετικοί παράγοντες \(15\), \(5\) και \(3\), και
\[
15\cdot5\cdot3=225.
\]
Επομένως,
\[
225\mid15!,
\]
άρα \(f(225)\leq15\). Συνεπώς πρέπει \(r>15\).

Για \(r=16\), έχουμε
\[
n=15\cdot16=240.
\]
Μέσα στο \(15!\) υπάρχουν οι διαφορετικοί παράγοντες \(15\), \(8\) και \(2\), και
\[
15\cdot8\cdot2=240.
\]
Άρα
\[
240\mid15!,
\]
οπότε \(f(240)\leq15\). Συνεπώς πρέπει \(r>16\).

Για \(r=17\), παίρνουμε
\[
n=15\cdot17=255.
\]
Επειδή
\[
255=3\cdot5\cdot17
\]
και ο \(17\) είναι πρώτος, κανένα \(k!\) με \(k<17\) δεν περιέχει τον πρώτο παράγοντα \(17\). Άρα
\[
255\nmid k!\quad\text{για κάθε }k<17.
\]
Αντίθετα,
\[
17!=1\cdot2\cdots3\cdots5\cdots17
\]
περιέχει τους παράγοντες \(3\), \(5\) και \(17\), επομένως
\[
255\mid17!.
\]
Άρα
\[
f(255)=17>15.
\]

Επομένως, η μικρότερη ζητούμενη τιμή είναι
\[
\boxed{n = 255}
\]
--- c2_math5_1181 dev=False validity_severity=none polished=unchanged
PROBLEM: Έστω ότι $\theta$ είναι η γωνία μεταξύ της ευθείας
\[\frac{x + 1}{2} = \frac{y}{3} = \frac{z - 3}{6}\]
και του επιπέδου $-10x - 2y + 11z = 3.$ Να βρείτε το $\sin \theta.$

[asy]
import three;

size(150);
currentprojection = perspective(6,3,2);

triple I = (1,0,0), J = (0,1,0), K = (0,0,1), O = (0,0,0);

draw(surface((2*I + 2*J)--(2*I - 2*J)--(-2*I - 2*J)--(-2*I + 2*J)--cycle),paleyellow,nolight);
draw((2*I + 2*J)--(2*I - 2*J)--(-2*I - 2*J)--(-2*I + 2*J)--cycle);
draw((0,0,0)--(-0.5,1.5,1));
draw((0,0,0)--0.8*(-0.5,1.5,1),Arrow3(6));
draw((0,0,0)--1.2*(-0.5,-1.5,-1),dashed);
draw(1.2*(-0.5,-1.5,-1)--2*(-0.5,-1.5,-1));
draw((0,0,0)--(-0.5,1.5,0));

label("$\theta$", 0.5*(-0.5,1.5,0.0) + (0,0,0.3));

dot((0,0,0));
//
[/asy]
TARGET: Από τη συμμετρική μορφή της ευθείας
\[
\frac{x+1}{2}=\frac{y}{3}=\frac{z-3}{6},
\]
θέτουμε την κοινή τιμή ίση με \(t\). Τότε
\[
x+1=2t,\qquad y=3t,\qquad z-3=6t,
\]
άρα
\[
x=-1+2t,\qquad y=3t,\qquad z=3+6t.
\]
Επομένως, ένα διάνυσμα διεύθυνσης της ευθείας είναι
\[
\mathbf d=\begin{pmatrix}2\\3\\6\end{pmatrix}.
\]

Το επίπεδο έχει εξίσωση
\[
-10x-2y+11z=3,
\]
οπότε ένα κάθετο διάνυσμά του είναι
\[
\mathbf n=\begin{pmatrix}-10\\-2\\11\end{pmatrix}.
\]

Αν \(\theta\) είναι η γωνία μεταξύ της ευθείας και του επιπέδου, τότε η γωνία μεταξύ των διανυσμάτων \(\mathbf d\) και \(\mathbf n\) είναι \(90^\circ-\theta\). Άρα
\[
\sin\theta=\cos(90^\circ-\theta)
=\frac{|\mathbf d\cdot\mathbf n|}{\|\mathbf d\|\,\|\mathbf n\|}.
\]

Υπολογίζουμε πρώτα το εσωτερικό γινόμενο:
\[
\mathbf d\cdot\mathbf n
=2(-10)+3(-2)+6(11)
=-20-6+66
=40.
\]

Τα μέτρα των δύο διανυσμάτων είναι
\[
\|\mathbf d\|=\sqrt{2^2+3^2+6^2}
=\sqrt{4+9+36}
=\sqrt{49}
=7
\]
και
\[
\|\mathbf n\|=\sqrt{(-10)^2+(-2)^2+11^2}
=\sqrt{100+4+121}
=\sqrt{225}
=15.
\]

Επομένως,
\[
\sin\theta
=\frac{|40|}{7\cdot15}
=\frac{40}{105}
=\boxed{\frac{8}{21}}.
\]
--- c2_math5_746 dev=False validity_severity=none polished=edited
PROBLEM: Στο παρακάτω διάγραμμα, τα σημεία $A$, $B$, $C$ και $P$ είναι τοποθετημένα έτσι ώστε $PA=2$, $PB=3$, $PC=4$ και $BC=5$. Ποιο είναι το μέγιστο δυνατό εμβαδόν του $	riangle ABC$; [asy]
defaultpen(linewidth(0.8)); size(150);
pair B = (0,0), C = (5,0), A = (2,3), P = (2.2,2);
draw(A--B--C--cycle^^B--P^^C--P^^A--P);
label("$A$",A,N); label("$B$",B,S); label("$C$",C,S); label("$P$",P,S);
[/asy]
TARGET: Αφού $PB=3$, $PC=4$ και $BC=5$, παρατηρούμε ότι
\[
PB^2+PC^2=3^2+4^2=9+16=25=5^2=BC^2.
\]
Επομένως, από το αντίστροφο του Πυθαγόρειου θεωρήματος, το τρίγωνο $PBC$ είναι ορθογώνιο στο $P$.

Άρα το εμβαδόν του είναι
\[
[\triangle PBC]=\frac12\cdot PB\cdot PC
=\frac12\cdot3\cdot4=6.
\]

Έστω $H$ το ίχνος της καθέτου από το $P$ προς την ευθεία $BC$. Χρησιμοποιώντας τώρα ως βάση την $BC=5$, έχουμε
\[
[\triangle PBC]=\frac12\cdot BC\cdot PH.
\]
Άρα
\[
6=\frac12\cdot5\cdot PH
\]
και επομένως
\[
12=5PH \quad\Longrightarrow\quad PH=\frac{12}{5}.
\]

Έστω $h$ η απόσταση του $A$ από την ευθεία $BC$. Τότε
\[
[\triangle ABC]=\frac12\cdot BC\cdot h
=\frac12\cdot5\cdot h.
\]
Επομένως, για να μεγιστοποιηθεί το εμβαδόν, πρέπει να μεγιστοποιηθεί το ύψος $h$.

Το σημείο $A$ απέχει σταθερή απόσταση $AP=2$ από το $P$, άρα κινείται σε κύκλο με κέντρο $P$ και ακτίνα $2$. Η μεγαλύτερη δυνατή απόσταση του $A$ από την $BC$ προκύπτει όταν το $A$ βρίσκεται πάνω στην κάθετη προς την $BC$ που περνά από το $P$, στην πλευρά του $P$ που απομακρύνεται από την $BC$. Τότε
\[
h=PH+PA=\frac{12}{5}+2
=\frac{12}{5}+\frac{10}{5}
=\frac{22}{5}.
\]

Άρα το μέγιστο δυνατό εμβαδόν είναι
\[
[\triangle ABC]_{\max}
=\frac12\cdot5\cdot\frac{22}{5}
=\frac{22}{2}
=\boxed{11}.
\]

=== §K EXPOSURE POLICY ===
Parent 1-G2F1P0: 1 training row (a dolci code row) shares a 13-gram with one MATH-500 item; R3's 16 rows belong to a different lineage and are not in these pilots. The readout keeps the frozen primary analysis and additionally reports the paired status of that one item.
