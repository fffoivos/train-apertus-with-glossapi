# Greek SFT, round one — execution plan (Sol executes, Claude assigns and verifies, owner gates)

Status: DRAFT for the owner's review, 2026-09-04. Companion to `SFT_PLAN_20260903.md`
(the *why*; §1–8). This document is the *how*: work packages, who does what, gates, budget,
and the caveats we carry into the runs.

## 0a. Vibes first (owner, 2026-09-04)

The thing that matters most after SFT is how the model *reads* — natural Greek, the house voice,
a Greek assistant rather than a translated American one. The evals are guards, not targets: a
run that scores better and reads worse loses. So the readout leads with the blind reading, the
numbers follow, and the preference round (§9 of the plan) is calibrated on the owner's own
ratings.

**The instrument — blind reading (WP1c):** 40 fixed prompts spanning the eleven categories
(some Greek reality, some math/code, some fr/de/en), every arm's answer shown unlabeled and in
shuffled order per prompt; the owner marks best and worst per prompt and flags each answer with
any of: *not Greek*, *American underneath*, *assistant mannerism*, *wrong fact*, *too long*,
*too short*. Per-arm vibe score = best − worst counts; the flags are the qualitative readout.
About one hour of the owner's time per round. The page is an artifact that saves the ratings
in place (artifact capability), so the ratings become data: the calibration set for the DPO
judges (§9) and the reference for the automatic voice score (stylometry vs no_robots-el), which
is only a proxy for this.

## 0. Roles and the rule of engagement

| role | does | does not |
| --- | --- | --- |
| **Owner** | decides at the gates G0–G4; approves every CHF; reads the Greek | write code, babysit jobs |
| **Claude** (this session) | writes each Sol brief, reviews the diff, runs the acceptance test, operates the cluster (submit, monitor, collect), keeps the ledger and the budget | trust Sol's word for a result; submit a job without a green acceptance |
| **Sol** (gpt-5.6-sol via `codex exec`) | executes one work package at a time from a written brief: code, configs, data builds, local tests | reach the cluster; spend node-hours; touch files outside the brief's paths; decide anything |

Assignment protocol, every step: (1) Claude writes `briefs/WPn.md` — context files to read, deliverable paths, the acceptance command, the size budget; (2) Sol runs in the repo with the brief as its prompt; (3) Claude runs the acceptance command *itself*, reads the diff, and either commits with the WP tag or returns the brief with the failing output; (4) one line in `EXECUTION_LOG.md` per attempt (WP, attempt, verdict, cost). A WP is never marked done on Sol's own report.

## 1. Scope — the lean round (owner, 2026-09-04)

Runs: **E0a** (Apertus-8B-Instruct: Greek evals, the five retention tasks once as the harness validation against the published table, and the blind reading + interviews as the *American assistant* contrast), **E0b** (Greek-CPT base `18-avg`: GreekMMLU/native/retention **pulled from the card**; run only what the card lacks — the known-ness scorer, gsm8k_el few-shot, ellinika-bench in base mode, dev-set perplexity and a format-gate baseline: ~1.5 nh),
**smoke** (200 steps of E1), **phase A: the E1 grid** (Greek 17.6k at lr 1e-5 and 5e-6, 3 epochs each,
warmup + constant lr, every epoch checkpoint evaluated → pick (lr, epoch); then one seed replicate
of the winner with the cosine schedule = the noise floor, and **E1-last** = the winning setting on the
terminal checkpoint `17`/`main`, read against the winner at G3 to fix phase B's base), **phase B** at the winning setting: **E2** (Greek + no_robots_en_pov),
**E3** (Greek + apertus_en + euroblocks fr/de, Greek point of view), **E3′** (E3 with the *raw*
slices: `messages_en` of the same rows). Retention tasks (evals-post-train ×5) on E0b, E1-s0, E3,
E3′ only; Greek evals on every model. Plus the **known-ness scorer** (labels only, no filtering).

Deferred, to be run only after the G4 readout: E4, E7/E7′/E8, E9 (raw replay, pre-built). E5/E6 are
absorbed by the grid.

Budget: ~30 node-hours ≈ **CHF 81**; **cap CHF 90** (≈30 node-hours) at CHF 2.69/node-hour.
The account holds CHF 2,095.08 ≈ 779 node-hours. Every submission is logged with its projected
and actual node-hours.

## 2. Work packages

| WP | deliverable | executor | acceptance (run by Claude) | budget |
| --- | --- | --- | --- | --- |
| **WP0 data** | `data/build_sft_mix.py` → per-arm `train.jsonl`/`dev.jsonl` from the 11 HF configs: Apertus-Instruct chat template applied on the CPT tokenizer, 2% held-out per config (fixed seed, row_ids listed), E3′ built from the rows' `messages_en`, token stats per arm, **contamination report** (SFT rows × eval prompts: ellinika-bench, GreekMMLU, native suite, gsm8k, ifeval) | Sol | script runs end to end on the Mac; every control token of the template exists in the CPT tokenizer (`added_tokens` check); dev/train disjoint; overlap report = 0 exact / listed near-duplicates; token totals within 2% of §5a′ | 0 nh |
| **WP1a retention harness** | evals-post-train on Clariden: container/uenv, the five tasks, vLLM backend, one launcher that takes a HF revision and writes `results/<run>/retention.json` | Sol writes; Claude runs | dry run on E0b completes; numbers for Apertus-Instruct reproduce the paper's table within 1 pt on two tasks | ~1.5 nh |
| **WP1b Greek harness** | one launcher for ellinika-bench (el+en), GreekMMLU + native suite (the subproject-09 FP32 loglik scorer, unchanged), `results/<run>/greek.json`; **the base's numbers are pulled from the CPT card's `checkpoint-index.json`, not re-run** (owner, 2026-09-04) | Sol | the launcher's first SFT checkpoint run completes; the scorer is byte-identical to subproject 09's (hash) | 0 nh on the base |
| **WP1c dev harness** | `dev_generate.py` (50 dev prompts per arm, greedy, 512 tokens) + **format gate** (EOT termination, Greek script share, turn structure) + **voice score** (natural-greek-sft `style_compare.py` against no_robots-el) + **blind reading page** (40 fixed prompts × arms, unlabeled, shuffled per prompt, best/worst + flags saved in place — §0a) | Sol | runs on E0b's generations; gate thresholds documented; page renders and saves a rating | ~0.2 nh/run |
| **WP1d ifeval_greek** | 541 IFEval prompts adapted to Greek through the natural-greek-sft pipeline (personas_if profile, house voice off — prompts only), **Greek-aware checkers** (the ~25 constraint types; capitalisation, comma, word-count and language rules rewritten for Greek), scorer = strict + loose accuracy | Sol (pipeline run by Claude) | 30-prompt owner-readable sample; every checker has a unit test with a Greek pass and fail case; Apertus-Instruct scores > 0 and < English IFEval | Sol tokens only |
| **WP1f unseen interviews** | 40 fresh seeds (10 per el/en/fr/de) written by owner + Claude, private file, overlap-checked; move scripts (challenge / clarify / localise / switch / stretch); batch-round driver (generate → interviewer writes follow-up → generate, ×2); Opus rubric scorer; transcripts feed the blind reading page (plan §12) | Sol builds the driver + scorer; seeds by owner + Claude | dry run on E0b: 40 three-turn transcripts, rubric scores, page renders; no seed overlaps a training row | ~0.1 nh/run + ~80 interviewer calls |
| **WP1e gsm8k_el-250** | 250 GSM8K test problems adapted (frame moves, numbers verbatim, boxed answer), exact-match scorer | Sol (pipeline by Claude) | numbers identical to source for all 250 (automatic); 20 read by owner | Sol tokens only |
| **WP2 trainer** | TRL SFT script per `apertus-finetuning-recipes` (packing, `assistant_only_loss`, lr 1e-5 cosine, 2 epochs, 4096, eff. batch 64, fp32 master weights, checkpoint per epoch), Slurm launcher for Clariden (1 node × 4 GH200; nodes=2 flag), `configs/E*.yaml`, smoke config (200 steps) | Sol | dry run on the Mac with a 20M-parameter stand-in: loss mask verified on 3 examples (user tokens −100), packing boundaries respected, checkpoint reloads; launcher lints | 0 nh |
| **WP3 known-ness scorer** | `score_claims.py`: for every claim in `reality_claims.jsonl` (a) corpus presence over the public modern-Greek snapshot + the dedup corpus on Clariden, (b) base-model few-shot answer on the question form (Gekhman split); row labels `none/known/mixed/unknown` written back as a side table | Sol | 200-claim hand-checkable sample; label distribution reported; runs inside the E0b job | ~1 nh |
| **WP4 runs** | E0a, E0b → G1; smoke → G2; E1-s0, E1-s1 → G3; E2, E3, E3′ → G4 | Claude submits, monitors every 15 min, collects | each run's `results/<run>/` complete; ledger line with nh | ~20 nh |
| **WP5 readout** | results table (all evals × runs, with the E1 seed spread as the readability bar), reading page, voice scores, known-ness distribution of what was trained on; decision memo on the deferred arms | Sol drafts, Claude verifies numbers against `results/` | every number traceable to a results file | 0 nh |

Order: WP0 ‖ WP2 ‖ WP1a–c (day 1) → WP1d, WP1e, WP3 (day 2) → G1 baselines, G2 smoke (day 2)
→ G3 E1 seeds (day 3) → E2/E3/E3′ (day 3) → G4 readout (day 4).

## 3. Gates (owner)

| gate | question | evidence | on red |
| --- | --- | --- | --- |
| **G0** | approve this plan and the CHF 80 cap | this document | revise scope |
| **G1** | do the harnesses reproduce known numbers? | WP1a/b acceptance on E0b and Instruct | fix harness, no training |
| **G2** | does the trainer work? | smoke: loss falls, checkpoint reloads, format gate ≥ 95% on 50 dev prompts, measured tokens/node-hour → re-budget | fix trainer; if throughput < 7 M tokens/nh, re-scope |
| **G3** | which (lr, epoch) wins the grid, and how big is seed noise? | the six checkpoints' Greek evals + blind reading; the replicate vs the winner → readability bar | if bar > expected effects, add a seed to E3/E3′ (+4 nh) before reading them |
| **G4** | which arm reads best, and do the numbers allow it? | **the blind reading first** (owner's best/worst + flags per arm), then WP5's table: no arm is picked whose retention or GreekMMLU fell below E0b by more than the seed spread | pick deferred arms; if vibes and numbers disagree, the disagreement is the finding |

## 4. Caveats we carry (read before G0)

1. **Template on a base model.** The CPT base has no chat template; we impose Apertus-Instruct's. Its control tokens must exist in the *extended* tokenizer — WP0 checks; if absent they are added and the embeddings initialised from the parent's, a deviation to record.
2. **Throughput is assumed.** 15 M tokens/node-hour is Meditron's number; ours is unmeasured until the smoke run. The budget can double; the cap still holds at 2×.
3. **Evals share a generator family with the data.** ellinika-bench and the two Greek evals we build (ifeval_greek, gsm8k_el) pass through the same LLM pipeline that wrote the SFT rows; scores may favour Sol-like Greek. Mitigation: the retention tasks are independent, the reading page is human, GreekMMLU/native suite predate the data. Say it in every readout.
4. **Contamination is unchecked until WP0.** GreekMMLU was decontaminated against the CPT corpus, not against these SFT rows. WP0's report gates training.
5. **One seed for E2/E3/E3′.** Differences under the E1 seed spread are not readable; G3 decides whether to buy a second seed.
6. **Knowledge alignment is labelled, not acted on** (§8). ~25% of rows assert Greek facts Sol vouched for; ~2% of claims are marked inferred/uncertain by Sol itself. Round one trains on all of them; the labels let E7/E7′ run later on the same base.
7. **Data residues.** 154 "underdetermined" English math rows dropped (restorable); 52 paired rows untouched English (content filter); the Greek Γ pass still leans nominal (Q20); fr/de voice has no stylometric reference; the last 20 English rows were regenerated after the Sol outage without the math check.
8. **Sol as executor.** No cluster access; its code is reviewed and its claims re-run; the OpenAI content filter can kill a brief mid-way (seen on the pair run) — briefs avoid security-flavoured wording; a WP that fails twice comes back to Claude.
9. **Cluster hygiene.** The CSCS certificate expires daily (`cscs-key sign`); login-node reaper kills long shells (drive from cron/sbatch, never from an interactive loop); `debug` vs `normal` walltime; monitor every 15 minutes, never fire-and-forget; one job at a time until G2.
10. **Money.** CHF 2.69/node-hour is inferred from the share count (779 = 2,095.08/2.69); confirm on the portal after the first job and correct the ledger.
11. **What round one cannot answer.** Whether averaging beat the terminal checkpoint under SFT (E1-last), whether Instruct is a better start (E4), whether unknown facts hurt (E7), whether corpus-grounded synthetic data is better (E8). Deferred by choice, listed so nobody reads the readout as settling them.

## 5. Ledger

`EXECUTION_LOG.md`, one line per attempt: `date | WP | attempt | executor | verdict | nh projected/actual | CHF cumulative`. Opened at G0.
