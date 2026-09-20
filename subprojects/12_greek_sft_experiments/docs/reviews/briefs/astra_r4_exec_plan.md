Review target: the execution plan below (docs/R4_EXEC_PLAN_20260914.md) for the next Greek SFT training run of Apertus-8B Greek-CPT.
Context you need: the incumbent model is arm B (stage 1 + Greek pass). R3 (single-stage, 403,727 rows) traded instruction-following gains for
maths and loop regressions. Krikri leads us on MATH-500-el 32.2 vs 8.0–11.2. Results review conclusions: H9 (terse Greek maths targets copied by the
model) is the top hypothesis; the Greek pass without maths replay erased maths (12.8 → 7.6); correcting data taught acceptance (H10). astra's own
verified finding: the English maths block is 100,000 solutions over 7,417 GSM8K problems. Budget: 24.4 node-hours left under a CHF 230 cap.
Judge: (1) does the three-arm pilot isolate the variables it claims (worked vs terse on the same problems; Level 5 on top)? (2) is a one-epoch
continuation from the stage-1 checkpoint with 10% replay a valid screen, or will the replay/dose confound the readout? (3) is the frozen decision rule
(≥3 pp MATH-500-el, paired bootstrap 90% LB > 0, IFEval/MGSM within 2 pp) adequately powered at n=500 with baseline ≈12%? (4) is the fidelity-all
plus mechanical-check verification of translated derivations sufficient, given the owner's rule of no agreement filters and trust in verifiable
sources? (5) is the R4 stacking (stage 1 → maths continuation → pass with maths replay) sound, or should the maths data go into the pass itself?
(6) budget and timeline realism. (7) anything the plan drops that is on the critical path to beating Krikri on maths without regressing dialogue/IF.
Disposition: BLOCKER/HIGH findings change the plan before Phase B launches; MEDIUM/LOW are logged in the plan's §7. Do not re-review datasets already
reviewed on 13 Sept (Greek IF, correcting, personality, imports). Quote plan sections when you object.

=== PLAN ===
# R4 execution plan — 14 September 2026

Owner instructions (14 Sept): Claude takes over execution from astra. Sol codex jobs may be used to fix
datasets and gpt-6-astra/xhigh for reviews. Per-amount spending gates are dropped; only the overall
SFT cap (CHF 230) binds. Deliverable: a plan, an astra review of it, then execution. Question asked:
when will we be ready for a better training run?

**Answer up front:** data ready 15 Sept morning; three math pilot continuations on 15 Sept
(after the CSCS certificate is re-signed); the R4 candidate (pilot winner + Greek pass) trains on
16 Sept with its full battery through 17 Sept. Everything fits in ~13 of the remaining ~23 node-hours.

## 0. Authority and rules in force

- Spending: any CSCS job within the CHF 230 cap without per-job asks. Every launch is still announced
  in one line (what, node-hours, why) before it starts, and every training launch is preceded by the
  recipe table with each parameter that differs from the previous run flagged.
- Judging/scoring: Sol only (gpt-5.6-sol); astra (gpt-6-astra, xhigh) for reviews; never Opus in bulk.
- Concurrency: at most 100 concurrent Sol calls (kernel panic at 144 on 10 Sept). Only the owner's
  interactive codex session is live now, so the full 100 is available.
- IFBench-el stays untargeted (pure out-of-distribution measure).
- Review gates: three per experiment (data/manifest freeze, launch readiness, results readout), not
  one per artifact. astra's D038 "review at every boundary" rule is retired.
- Ledger: `execution_state.json` is canonical; astra's 0.47 node-hours of diagnostics (GreekMMLU
  200-item ×2, Dolci CPU pilots, CHF 1.27) are added on the next ledger write.

Blocker for any CSCS step: the certificate has expired (`ssh clariden` → publickey denied). The owner
runs `! cscs-key sign`.

## 1. Budget

| Item | Node-hours | CHF |
|---|---:|---:|
| Cap | 85.5 | 230.00 |
| Used (ours 60.60 + astra 0.47) | 61.07 | 164.29 |
| Remaining | 24.4 | 65.71 |
| Phase B: three math pilots (0.8 train + 0.5 light evals each) | 3.9 | 10.5 |
| Phase C: R4 pass (1.8) + light evals (0.5) + full battery (5.0) | 7.3 | 19.6 |
| GreekMMLU official-protocol runs (Krikri, arm B, R4) | 1.5 | 4.0 |
| Reserve for one more iteration | 11.7 | 31.6 |

Planning throughput 28M tokens per node-hour (R3: 228.6M tokens, 7 h 01 on one node).

## 2. What the run changes and why (from the results review + astra's verified findings)

| Lever | Evidence | Change |
|---|---|---|
| Greek maths targets are terse and unboxed (H9): R3 answers median 35 words, 343/500 unboxed; Krikri 32.2 vs our 8.0 on MATH-500-el | results review, accepted HIGH | replace the 9,999 translated problems' targets with the **translated published derivations** (cut 2, worked, `\boxed` kept, source length); add Level 5 (absent from cut 1) |
| English maths block is 100,000 solutions over 7,417 GSM8K problems (13.5× each, 6,528 problems ≥10 copies), 10.9% of R3 supervised tokens | astra finding, re-verified today | dedup to ≤3 solutions per problem (≈22k rows) and add the 7,500 published MATH train solutions (all levels), decontaminated against MATH-500 (drop the 172 families with 13-gram/exact hits) |
| The Greek pass erases maths (stage 1 12.8 → arm B 7.6 with no maths in the pass) | R2/R3 numbers | the pass carries 2,000 worked Greek maths rows as replay |
| Correcting set teaches acceptance (272 acceptances vs 20 false-claim holds; picky-user false_claim turns) (H10) | results review | correcting v2: balanced with astra's 32 + 60 accepted decision rows (true/false/partial/unresolved) and a capped acceptance subset |
| astra's accepted repairs: 14 Greek-IF rows, 7 Greek-maths rows (exact-match overlays) | accepted patchset | applied at export |

Deferred (not on the maths critical path, kept in DATA_TODO): suite lanes A–D, XSTest adequacy set,
decontaminated Greek MC set (first check GreekMMLU under the official protocol), IFBench words-checker
audit, personality 42 candidates (apply if assembly-ready by Phase C, else next iteration).

## 3. Phase A — data (Sol only, 14–15 Sept)

A1. **Greek maths v2 (cut 2).** Targets = published derivations translated (medium effort; no solving,
so no high reasoning needed; fidelity judgments run at high). Remaining generation: 6,281 solution
translations, 43 Level-5 problem translations, 289 Level-5 solution translations. Then:
  - fidelity of *every* problem translation (11,456 calls, high). The 300-row sample gave 9/300 = 3.0%
    unfaithful, above the 2% rule, so the pool does not enter unfiltered; unfaithful rows are dropped
    (translation QA, not an agreement filter).
  - mechanical checks: `\boxed` present, boxed answer equals the reference answer (normalized),
    decimal comma, length ratio to the English reference (median 0.8–1.25). Failing rows dropped and
    counted; the failing number is reported, never shaded.
  - guarded Greek language-polish pass with maths protected (owner rule before "done").
  - 4,071 native `gm_nat_*` rows: kept as they are (terse) for the pilots; optional lane: re-solve at
    source length with Sol high after the pilots read out.
  Expected: ≈11,000 worked rows incl. ≈1,100 Level 5, ≈2.6M supervised tokens (cut 1: 1.31M).
A2. **English maths rebuild.** GSM8K ≤3 solutions per problem (≈22k rows, ≈3.4M tokens) + MATH train
  7,500 published solutions ×2 copies (≈3.3M tokens); total ≈6.7M vs 15.3M. Decontamination as above.
A3. **Correcting v2.** Convert astra's 92 accepted rows (context turns carry `train:false`, same key as
  our masking) + all 176 planted-failure rows + an acceptance subset capped at the hold count;
  target ≈350 rows ×2 copies. Falls back to v1 if the conversion fails checks.
A4. **Apply overlays** (14 IF + 7 maths) at export; assemble arms; run the assembler's own gates
  (train∩dev = 0, decontamination, masking test on real rows).
A5. **Astra gate 1** (data/manifest freeze): one xhigh review of the three pilot manifests with 60-row
  samples of the new maths targets.

## 4. Phase B — three math pilots (15 Sept, ≈3.9 nh)

Continuations from the same stage-1 checkpoint (`runs/R2_stage1/epoch1`, arm B's parent), one epoch,
identical replay sample (seed 42, 10% of every non-maths block by tokens, ≈12M tokens), identical
English maths block (A2), identical optimizer settings. Only the Greek maths block varies:

| Arm | Greek maths block | Question |
|---|---|---|
| M0 | cut-1 terse targets on the 9,999 problems (fidelity-dropped rows removed in all arms) + native | control |
| M1 | cut-2 worked targets on the same problems + native | worked vs terse, same problems |
| M2 | M1 + Level-5 worked rows | does Level 5 add on top |

Recipe (every parameter vs arm B's pass, the last continuation we ran):

| Parameter | arm B pass | pilots | flag |
|---|---|---|---|
| parent | R2_stage1/epoch1 | same | — |
| data | 41,697 rows, 2 epochs | ≈45k rows, 1 epoch (≈21M tokens) | CHANGE: 1 epoch (screen, not a finish) |
| lr / schedule / warmup / floor | 1e-5 cosine, 3%, 0.1 | same | — |
| batch | 16 × 4096 (accum 4 × 4 GPUs) | same | — |
| precision, masking, template | fp32 master + bf16, per-turn masks, Apertus template | same | — |
| seed | 42 | 42 | — |

Readout (light evals, ≈0.5 nh each): MATH-500-el (equiv500 grader, Sol adjudication of unresolved
rows), English MATH-500, Greek MGSM, IFEval-el (langdetect rescoring), greedy loop/truncation counts,
format gate. Frozen rule: advance the arm with the best MATH-500-el if it beats M0 by ≥3 pp with a
paired-item 90% bootstrap lower bound above zero and neither IFEval-el nor MGSM-el drops by more
than 2 pp; report English MATH-500 as a safeguard. Otherwise report inconclusive and take M2 to the
pass anyway as the package we would ship, stating the pilot did not separate the arms.

## 5. Phase C — the R4 candidate (16–17 Sept, ≈7.3 nh)

R4 = pilot winner + R3_pass's pass composition (personality v3 ×4, greek_ours, greek_rewrite, 5%
replay, suite ×2) with correcting v2 ×2 in place of v1 and 2,000 worked maths rows as replay; 2 epochs,
lr 1e-5 cosine (arm B's pass settings). Battery: light evals, native suite, GreekMMLU (ours and the
official letter protocol), retention on the cached suite, the four Greek benchmarks, interviews (Sol),
mixed-profile dialogues (Sol user + judge). Comparators: arm B (incumbent), R3_pass, Krikri.
Astra gates 2 (launch readiness: recipe table + manifests) and 3 (results readout).

Promotion rule: R4 replaces arm B if MATH-500-el ≥ 15 (double R3_pass's 10.0 and above stage 1's 12.8),
IFEval-el ≥ R3_pass − 2 (69.6), greedy loops ≤ arm B's 7, mixed-profile coherence ≥ 90%, retention
within 1 pp of arm B. Otherwise it is a second data iteration, not a promotion.

## 6. Timeline

| When | What |
|---|---|
| 14 Sept evening | plan review (astra); cut-2 generation running; A2/A3 scripts |
| 15 Sept 02:00–08:00 | fidelity-all, mechanical checks, polish pass |
| 15 Sept morning | assemble M0/M1/M2, gate 1 review, owner re-signs cert, launch pilots (sequential on one node, ≈1.3 h each incl. light evals) |
| 15 Sept evening | pilot readout, arm choice |
| 16 Sept | R4 pass (≈2 h) + light evals; full battery starts |
| 17 Sept | battery complete, results review (gate 3), promotion decision |

## 7. Risks

- Fidelity-all drops more than expected: translations are still usable for training only when
  faithful; report the rate; if >10% we re-translate the failures rather than shrink the set.
- Cut-2 targets are translations of human solutions, so they are correct by construction, but style
  is English-textbook; the polish pass fixes Greek, not style.
- Stacking a third stage (stage 1 → maths continuation → pass) is new; R3_passB (R3 + arm B's pass) is
  the precedent that a pass on a different parent behaves.
- One node, debug QoS allows one job at a time; pilots run sequentially, so the cert must be valid for
  the whole 15 Sept window.
