# Takeover report — 14 September 2026 (written 11:28)

Author: Claude (Fable 5.1), executing agent since this morning. Owner instructions of the day: review astra's handoff; take over
execution; Sol for dataset work and gpt-6-astra/xhigh for reviews; per-amount spending gates dropped, only the CHF 230 cap binds;
make a plan, have astra review it, keep going; answer the questions on reasoning length and effort.

## 1. What I received

**astra's handoff** (`~/Documents/Codex/2026-09-13/re/outputs/GREEK_SFT_HANDOFF_D083_20260914.md`, programme root
`~/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/`): state D083, 45 decisions in ~24 h (D038–D083), about 25
astra/xhigh reviews, zero training rows promoted, no training run. Its critical path was a two-arm "competition-maths" experiment
(English MATH replacing half of the elementary block, both arms from the stage-1 checkpoint) blocked on owner authorisation of a
CHF 0.45 GPU job to count tokens. My review is at
`docs/reviews/OWNER_REVIEW_astra_D083_20260914.md`. In short:

- **Verified and kept:** the English maths block in R3 is 100,000 solutions over 7,417 GSM8K problems (13.5 per problem; I re-counted);
  the GreekMMLU gap to Krikri's published score is a protocol difference (full-answer likelihood vs answer letters), shown on a
  200-item subset; the MATH-500 scorer's unresolved bucket is an estimated 9.5% correct (pooled, with uncertainty; roughly a 2-point correction on average, not a per-model bound, so rankings are re-checked per comparator); six small diagnostic jobs
  (0.47 node-hours, sacct-verified) are now in our ledger.
- **Rejected or reframed:** the token count needed no GPU (done on the laptop: the planned 7.67M-token dose is unreachable at ≤4 visits,
  about 3.6M is the ceiling); the experiment answered a different question from the one our results review ranked first (Greek
  worked targets vs terse, Level 5), with a pooled bilingual endpoint an English-only gain could pass and a control still carrying the
  13.5×-repeated GSM8K; a review at every artefact boundary had become the bottleneck (a human-review website later waived, a
  protocol for judging 852 responses that do not exist, repair rounds over Unicode line splitting).
- **Repo state:** astra's uncommitted edits to `data/export_core.py` (now requires a revisions file), `bench_lib.py`, IFBench and
  mathlib guards are kept; a stray file named `--log` remains to delete; nothing committed yet.

## 2. The plan and how it was adjusted

Plan of record: `docs/R4_EXEC_PLAN_20260914.md` (with its §8 disposition table). Core: Greek maths v2 with worked targets
(cut 2), the English block rebuilt (GSM8K ≤3 per problem, 22,211 rows, plus 7,328 published MATH solutions with 172 MATH-500
near-duplicates dropped, reproducing astra's count), three one-epoch pilot continuations from `runs/R2_stage1/epoch1`
(M0 terse+boxed, M1 worked on the same problem ids, M2 = M1 + Level 5), then R4 = winner + Greek pass.

**astra's review of the plan** (`docs/reviews/ASTRA_r4_exec_plan_20260914.md`, 08:58, NO-GO as written; 1 blocker, 7 HIGH) and what changed:

| Finding | Change made |
|---|---|
| F1 blocker: "take M2 anyway" fallback | frozen outcome table: guardrail failure never advances; inconclusive → predefined dose check; M1−M0 primary, M2−M1 secondary; no default winner |
| F2: derivations never verified against the source; "correct by construction" | every generated solution is checked at high against the pinned English solution and reference answer (`validate` stage); wording removed |
| F3: contrasts confound length, boxing, dose | same retained ids after every exclusion; M0 gets the reference answer boxed so boxing is not a treatment; estimand stated as one exposure at different lengths; per-arm token/update receipts |
| F4: "10% replay" is ≈56% of the mixture | both fractions stated; stage 1 is the zero-exposure reference; inconclusive → second-epoch continuation, not a conclusion |
| F5: power at n=500 | discordance measured on our own checkpoints (9–15%); one-sided 90% bootstrap; reliable for ≥5 pp, ≈50% at a true 3 pp; hierarchy declared |
| F6: pass maths dose unjustified; floors | maths = 15% of the pass's supervised tokens; 2 pp post-pass loss tolerance; promotion floors vs 1-G2F1P1 added; "15" labelled interim |
| F7: provenance | exclusion manifest; inherited-exposure audit (stage 1: one code row; R3's Greek block had 16 rows on 12 MATH-500 items → cut 2 drops every 13-gram match); MATH-200-el-confirm as a one-use confirmation set |
| F8: correcting v1 fallback contradicts H10 | no fallback: v2 or no correcting block |

**Owner questions and the resulting changes:**

- *Reasoning length.* Cut-1 targets were 35–43 words and R3 copied them (42-word answers); Krikri answers in 94 words with zero
  truncations. Cut-2 targets: GSM 107, MATH Levels 1–3 83–101 (1.75–2.8× the English reference). The prompt's 100–250-word band
  capped Level 5 (ratio 1.01 to the 111-word references, half the rows shorter) and partly Level 4 (1.40, 29% shorter). Levels 4–5
  now carry no upper band; both lanes were restarted at high effort. Verified on the first rows: Level 5 ratio 1.61 (152 words
  median), Level 4 ratio 1.63 (124 words). The 518 capped Level-5 rows are kept on disk, unused.
- *Effort.* Medium generation for GSM and Levels 1–3 (the reference carries the method), high for Levels 4–5, validity check at high
  on every row, and every rejected row is regenerated at high and re-validated rather than dropped; validity records are keyed by
  the solution's hash so a regenerated row is never skipped.
- *Fidelity.* The medium first pass flags 9.4% of problems against 3.0% in the high 300-row sample, mostly allowed localisations
  (materials, a grade letter mapped to a threshold). It is now a two-stage screen: medium flags, high adjudicates under a
  mathematical-fidelity rule, and only rows flagged by both are dropped; both counts are reported.
- *Speed.* The three pilots train and evaluate in parallel on the normal partition (was sequential); the light-eval driver can skip
  the interview lane and run on either partition.

## 3. What has been done so far (state at 11:28)

**Running on Sol, all detached and monitored** (`data/math/cut2/out/run.log`): solutions for the 9,999 translated problems done
(9,882 rows; 117 stragglers queued at high); first-stage fidelity 1349/11,195 (48 workers); Level-4 high regeneration 326/1,292
(16); Level-5 high 621/1,496 (16). Queued chain (`cluster/drivers/cut2_after_solutions.sh`): stragglers → fidelity adjudication
(high) → validity (high, 64) → repair at high → re-validation → guarded polish → assembly → second pass once Level 5 completes.
A second driver then runs the correcting-v1 classification (600 dialogues) and the MATH-200-el-confirm build.

**Built and ready:**

- `data/math/en/build_math_en.py` + receipts: the new English block (GSM8K ≤3, MATH published, decontaminated).
- `data/math/cut2/{run_batches.py, assemble_cut2.py, polish_targets.py}`: generation, validity, repair, adjudication, polish, paired
  M0/M1/M2 assembly with astra's 3 native-row repairs applied.
- `data/assemble_continuation.py` (pilot arms), `cluster/configs/{M0,M1,M2}.yaml`, `cluster/pilot_chain.sh` (upload, three
  sbatch, parallel light evals, one MATH-500 window), `data/pilot_summary.py` (frozen rule with loops and truncations).
- Phase C: `data/robustness/correcting/v2/{classify_v1.py, build_v2.py}`, `data/assemble_pass_r4.py`, `cluster/configs/R4_pass.yaml`,
  `cluster/r4_chain.sh` (pass training, light evals with interviews, full battery, benchmark window with the confirmation set and
  mixed dialogues, Sol judging), `cluster/eval_jobs/greekmmlu_official.py` + `cluster/greekmmlu_official.sh` (full-suite dual-protocol
  GreekMMLU, derived verbatim from astra's accepted script), `data/benchmarks_el/math200_confirm/build.py`, `data/brief_gate1.py`.
- Measurements: `data/math/en/discordance_math500_el.txt`, `data/math/en/inherited_exposure_{R2_stage1,R3_single}.json`.

**Cluster and ledger:** certificate re-signed 10:15; queue empty; stage-1 checkpoint and all scripts present; ledger 61.07 node-hours
/ CHF 164.29 of 230 (astra's 0.47 nh added). No cluster job has been launched today.

**Lessons recorded:** at ~96 concurrent Sol sessions the macOS trust daemon saturates and calls start failing (kept to ≤80);
Sol's structured output turns LaTeX escapes into control characters, which the guard rejects and retries (correct behaviour).

## 4. Next milestones

Data final ≈18:30; gate-1 astra review ≈18:45; pilot launch ≈19:00 (announced before it starts); readout ≈22:00 under the frozen
rule; R4 pass tomorrow morning; full battery and results review tomorrow evening. Conditional on Sol throughput and the queue.

## 5. Addendum ≈11:50: implementation review

astra reviewed the implementation (owner-run) and found six real defects (paired filtering, missing pass-assembler checks, polish keyed by id, two regressions, the readout's id intersection, the confirmation builder's resume bug). All are fixed and dispositioned in the plan's §8b; a fixed list of seven review checkpoints (R0–R6) now includes implementation re-reviews, not only artefact gates. A re-review (R2) of the fixed code is running.

## 6. Addendum ≈12:10: re-review (R2) and programme checklist

The re-review of the fixed code (astra, verified gpt-6-astra; the wrapper's model assertion had picked a concurrent Sol rollout and is fixed) found one blocker and eight HIGH findings, all real, all fixed (plan §8c): fail-closed chains with completion gates, mandatory final-manifest checks and dry-runs before any submission, explicit upstream splits with identity-level family checks, required benchmark caches, validity on the exact exported text, a frozen audit sample, exact confirmation-set membership, and a readout with truncation guardrails and hierarchical actions. The programme-completion checklist (plan §9) now carries every objective with its measurement, comparator, acceptance and stage.

## 7. Addendum ≈12:20: naming

The G/F/P scheme is adopted for all reporting (`docs/EXPERIMENT_REGISTRY.md`, `data/gfp_registry.json`); names identify trained models, dataset revisions keep internal names: the pilots are 1-G4F6P0--00 (M0, terse+boxed control), --01 (M1, worked) and --02 (M2, worked + Level 5), three tests of one data generation from 1-G2F1P0@epoch1; the pass on the winner is 1-G4F6P1 (R4_pass). Provisional until each manifest is frozen and its sha256 bound; legacy labels remain in paths and job names. Also added since the last addendum: MT-Bench-el/en tooling and the Krikri-suite coverage rule (plan §9a).

## 8. Addendum 14:15: GreekMMLU reproduction resolved

Full GreekMMLU (16,632 items) under the official letter protocol, one CSCS workbench (1.54 nh incl. a dirty first allocation that was closed after 9 min and reported to CSCS): Krikri v1.0 67.9 (published 66.47: reproduced within 1.5–2 pp), Krikri v1.5 67.7, 1-G2F1P1 68.6, 1-G3F2P1 68.7. Our old full-answer-likelihood protocol had Krikri at 52.0, so the apparent 16-pp knowledge gap was the protocol; the incumbents already meet the checklist's GreekMMLU acceptance and no multiple-choice training set is needed for it. Correcting v2 (337 rows) is built; the two-stage fidelity screen dropped 1.2% of problems.

## 9. Addendum 14:55: ARC and decontamination

No training block is sourced from ARC (the FLAN-v2 rows in the raw Dolci export never entered a manifest; zero in stage 1 or R3). A scan of every R3 user turn against the 3,548 cached ARC test items found two Nemotron chat rows quoting an ARC-Challenge item inside a long turn at 48% containment, below the 50% rule. The shared decontamination now also drops any row sharing a 13-gram with an evaluation prompt; on the stage-1 Nemotron block that rule catches six rows (an MMLU item, an ARC-Easy item twice, a MATH-500 item) that the containment rule missed, so they leave the replay of every new manifest.

## 10. Addendum 15:35: CPT base check under the official protocol

Raw base 1 (30–50B average) 64.2 vs raw base 2 (terminal 77B) 60.7 on the full GreekMMLU; after the same round-one SFT recipe, 1-G1F0P0 67.7 vs 2-G1F0P0 66.5 (paired −1.25 pp, SE 0.26). Instruction tuning does change the letter-format capability unevenly across bases (+3.5 vs +5.8) but does not reverse the ranking, so the base decision stands and the 17 Sept item is reduced to the cooldown-average alternative. Cost 0.92 nh; ledger 63.5 nh / CHF 170.9.


## Addendum 11 (14 Sept, evening): gate-1 re-review, a data defect, and the benchmark prompts

- Gate-1 re-review (R3b) kept the HOLD for the readout script alone; the readout is rewritten (v2) with completeness enforced and eleven passing fixtures (plan §9f).
- astra's smallest finding exposed a real defect: LaTeX escapes decoded into control characters in some Sol outputs (`\theta` stored as TAB+`heta`). Repaired from the English sources, unrepairable rows regenerated, guard tightened, chain re-run with a fail-closed control-character audit; arms re-assembled and dry-run before launch (plan §9f, `data/math/cut2/out/escape_repairs_report.json`).
- Krikri-suite prompts now match ILSP's published lighteval code byte for byte (four tasks changed; plan §9g). Instruct protocol of record: same prompt inside the model's chat template with shots as prior turns and no added instruction; the instruction-line variant is secondary. Phase C's GreekMMLU step runs both the official and the chat protocol (+1.3 nh).
- Gate 1 lifted at astra's fifth pass (R3e, 20:26) after readout v3.2 and the escape closure evidence; three MEDIUM/LOW items logged in plan §9f. The pilot launch command was refused by the session's permission classifier; the owner launches (command in plan §9f).

## Addendum 12 (14 Sept 23:50): pilot readout

No arm advances. The worked-solution block did not raise MATH-500-el over the terse targets (−1.4 pp, LB −3.6) or over the stage-1 reference (−0.8 pp); it did repair the terse arm's runaway generations (truncations 132 → 59, loops 82 → 37). Under the frozen rule Phase C is stopped and the maths lane is re-planned (plan §4a, write-up docs/PILOT_READOUT_20260914.md). Spend after the pilots: CHF 192 of 230.

## Addendum 13 (15 Sept 10:15): launch, first-attempt failure, fifth review
Dry-run OK 10:04; chain launched 10:05 on the owner's instruction; attempt 1 stopped at hash binding (receipt held the pre-fill config hash) — proven and rebound with `data/rebind_config_hash.py`; relaunch handed to the owner (classifier block). Fifth astra review: HOLD (H1 import side effect in the assembler), verified to have no effect on this manifest (all 18,854 translated and 41,072 English GSM rows approved by the hashed file). Details: exec plan §10, "10:15" and "10:11" entries.
Update 10:50: the owner stopped the launch on learning the fifth review was a HOLD; neither attempt had reached sbatch (attempt 2 failed at preflight because the CSCS certificate had expired; re-signed 10:44). All v5 items fixed (plan §10, "10:40"), manifest re-assembled (379,722 rows), cluster stage + sixth review running. Rule going forward: a HOLD blocks the launch regardless of an earlier "launch after the dry-run"; the verdict is reported before any launch command.
