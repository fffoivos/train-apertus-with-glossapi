# Review of astra's programme handoff (D083) — 14 September 2026

Reviewed: `~/Documents/Codex/2026-09-13/re/outputs/GREEK_SFT_HANDOFF_D083_20260914.md` plus
GOAL.md, PLAN.md, COMPETITION_MATHS_CHECKPOINTS_D038.md, DECISIONS.md (D038–D083), STATE.json,
budget.json, the capacity contract, and the diff astra left in this subproject.
Reviewer: Claude (Fable 5.1), the agent that ran R3/R3_pass and the evaluation battery.

## Verdict

The direction is right and two of astra's findings are real, verified, and change our picture.
But the process has become the product. In ~24 hours astra logged 45 decisions (D038–D083) and
about 25 Astra/xhigh reviews, promoted zero training rows (`data_promoted: false`), trained nothing,
and the critical path now waits on owner authorisation of a CHF 0.45 GPU job whose purpose is to
count tokens. That count can be done on the laptop for free; I did the upper bound below in one
minute, and it shows the planned dose is unreachable as specified. Separately, the experiment astra
froze answers a different question from the one our results review ranked first.

## Verified and valuable

1. **The English maths block is 100,000 solutions over 7,417 GSM8K problems.** I re-counted from
   `~/sft_annot/core_export/openmath_gsm_raw.jsonl`: 13.5 solutions per problem on average, 6,528
   problems with ten or more copies, max 29. It is 10.9% of R3's supervised tokens (15.33M). Our
   registry's "deduplicated" means exact-row dedup only; this is a genuine defect in the R3 mix and
   was not in our dataset reviews.
2. **Native GreekMMLU protocol mismatch.** Our harness scores average full-answer likelihood; the
   official Krikri code scores answer letters. On a fixed 200-item subset: Krikri 0.525 (ours) vs
   0.695 (official-style); R3 0.635 vs 0.715. The 52.0 vs published 66.5 "gap" is protocol, not
   capability. This bears directly on the owner's "train on a multiple-choice set" idea: run the
   full suite under the official protocol first; the MC set may be unnecessary.
3. **Scorer review bucket.** 2,211 of 11,000 MATH-500 responses (22 model×language cells) landed in
   the grader's unresolved bucket; a blinded 440-row diagnostic estimates 9.5% of those are correct.
   Counting them as wrong therefore understates scores by at most ~2 pp and does not change any
   ranking. Useful closure, but it cost 13 decisions.

Budget reconciles: astra's CHF 164.29 minus our ledger's 163.02 = CHF 1.27 = the 0.47 node-hours of
astra's diagnostic jobs (GreekMMLU 200-item ×2, Dolci CPU pilots; STATE.json `new_cscs_chf`
1.2658). I could not confirm via `sacct` because the CSCS certificate has expired.

## Problems

### P1. The planned dose is unreachable, and this was knowable without a GPU
Candidate arm target: 7,666,026 supervised tokens of English competition maths from ≤4,052
families, ≤4 visits per family. With the Apertus tokenizer, the published MATH train solutions
average 219 tokens (median 154, p90 461):

| Pool | Visits | Supervised tokens | Share of target |
|---|---:|---:|---:|
| all 7,500 MATH train families | 4 | 6.57M | 86% |
| 4,052 eligible families (pro rata) | 4 | ≈3.6M | ≈47% |

So the capacity measurement will trigger astra's own "stop and revise the dose" branch. Either
raise the visit cap (repetition, the thing the GSM8K finding warns against), add a second solution
source (OpenMathInstruct-2 synthetic, not "original published"), or halve the replacement to
≈3.5M tokens. This should be decided now, not after a cluster job.

### P2. Token counting does not need Clariden
The tokenizer (`swiss-ai/Apertus-8B-2509`, identical vocabulary to our CPT model) is in the local
HF cache and the trainer's rendering/masking code runs on CPU. The contract, sha256 bindings,
`--test-only` pseudo-job and the authorisation blocker are overhead around a one-minute laptop
task. The exact-rendering argument is worth one spot check on a single family, not a job.

### P3. Review cadence is the bottleneck
D038 requires a fresh Astra/xhigh review at every "scientific or spending boundary". In practice
that produced: a 96-case human-review website (D054–D067, six REPAIR rounds) that the owner then
waived; a protocol for judging 852 MultiChallenge responses that do not exist yet (D068–D073);
a proof-quality screen for the human-written MATH solutions (D074–D077); a packet builder and a
"mapping-free reviewer handoff builder" with REPAIR rounds over Unicode line splitting and
duplicate JSON keys (D078–D083). Recommend three review gates only: manifest freeze, launch
readiness/price, results readout.

### P4. The experiment answers a different question than our results review asked
Our results review (R4_PLAN §10) ranked H9 first: R3's Greek maths answers are terse and unboxed
(343/500, median 35 words) because the Greek maths targets are terse, and Level 5 is absent from
the Greek set. The two named experiments were a frozen recovery panel and a four-arm pilot
(worked vs terse Greek targets × correcting). Astra's PLAN §4 explicitly defers worked-vs-terse and
replaces it with English competition vs English elementary, both arms from stage 1. Consequences:

- It tests difficulty coverage in **English**. The owner's stated goal was a Greek maths set.
  Cross-lingual transfer is plausible but is exactly what R3 already failed to show: the English
  block's worked, boxed style did not carry into Greek outputs.
- The frozen rule advances on a **pooled** bilingual gain ≥3 pp with neither language worse by >1.
  An English-only gain can pass. Greek MATH-500-el should be the primary endpoint.
- The control keeps the 13.5× repeated GSM8K block while the candidate is diversity-bounded, so
  the contrast confounds "competition vs elementary" with "repetition vs diversity". Cheapest
  clean control: dedup GSM8K to ≤2 solutions per problem in both arms.
- A ≥3 pp screen is small against the 21 pp gap to Krikri (8.0 vs 32.2 on MATH-500-el). Even a
  pass leaves most of the gap. The lever that addresses the gap directly, Greek worked solutions
  including Level 5, is absent from the 13-step continuation. The partial cut-2 output
  (`data/math/cut2/out/`: 3,695 Greek solutions, ~2,100 Level-5 problems, 2,994 Level-5 solutions)
  is unreviewed and unmentioned; its 300-row audit needs Sol only, no CSCS.

### P5. Schedule already slipped
PLAN §5 dated the competition pair for 15–18 Sept and first DPO for 24–26 Sept. There is no
manifest yet, and the pair needs steps 2–9 of the continuation first, each with its own review.

### P6. Astra edited live code in this subproject, uncommitted
Working-tree changes attributable to astra: `data/export_core.py` (pins HF dataset revisions and
preserves tool payloads, good, but now **exits unless `SOURCE_REVISIONS_FILE` is set**, a breaking
change for the existing export driver), `data/benchmarks_el/bench_lib.py` (worker cap 100, input
dedup: good, matches the concurrency rule), `data/benchmarks_el/ifbench/score.py` (empty responses
can no longer pass a checker: correct, matches upstream), `data/math/mathlib.py` (control-character
rejection, raise on codex failure: good), four `docs/PRE_DPO_PROGRAMME_20260913*` snapshot trees,
`docs/PRE_DPO_CURRENT.md`, and a stray empty file named `--log` at the subproject root. The
interview `scores.json` and `execution_state.json` diffs are mine (Sol rescoring, ledger), also
uncommitted. Nothing here is wrong in intent; it needs a commit with the export change made
non-breaking (default revisions file or warning).

## Recommendations (owner decisions)

1. **Authorisation.** Do not gate on the CHF 0.45 job. Give astra a scoped authorisation for
   non-training CSCS jobs up to 3 node-hours cumulative without per-job asks; training stays
   gated on an explicit go with the recipe-parameter table disclosed.
2. **Dose.** Set the replacement to what the pool supports at ≤4 visits (≈3.5M tokens) or allow
   OpenMathInstruct-2 second solutions; decide before any measurement job.
3. **Endpoint.** Primary = Greek MATH-500-el paired gain ≥3 pp with 90% bootstrap LB > 0;
   English MATH-500 becomes a safeguard. Control arm uses deduplicated GSM8K (≤2 per problem).
4. **Third arm.** If budget allows (~1.5 nh each, ≈CHF 4), add candidate + Greek worked solutions
   incl. Level 5 from the audited cut-2 output. This is the arm that tests H9 and the owner's goal.
5. **Start the cut-2 audit now on Sol** (300 rows, blinded, Sol judge at 24 workers), in parallel
   with the manifest work. Zero CSCS cost.
6. **GreekMMLU.** One full-suite run each for Krikri and R3 under the official letter protocol
   before anyone builds an MC training set.
7. **Reviews.** Three gates (manifest, launch, readout). Stop reviewing reviewer-handoff tooling.
8. **Repo.** Commit astra's code changes separately, make `export_core.py` non-breaking, delete
   `--log`.
