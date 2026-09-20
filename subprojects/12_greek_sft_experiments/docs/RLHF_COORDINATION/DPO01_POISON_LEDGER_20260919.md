# DPO01 — what the errors poisoned, and what must be re-run

> **RESULT, 19 September evening — the re-score is running and the first certified numbers reverse the round.**
> Measured on the parent's OWN weights, correctly loaded vs mis-loaded exactly as every arm was
> (`parent_ckptgen` vs `parent_exportcfg`, same weights, only the rotary settings differing):
> **IFEval −4.07 pp (p=0.045), MGSM −9.60 pp (p=0.007), Global-MMLU-Lite −7.63 pp.**
> The artefact is LARGER than the entire published "damage" on every lane.
> First repaired arm, guard-certified against the frozen parent (weights the only difference):
> `arm01_ep3` is **+3.88 pp IFEval (p=0.044), +6.80 pp MGSM (p=0.071), +1.33 pp Global-MMLU-Lite** — all positive.
> There was no mathematics regression and no multilingual regression; there was a loader bug.
> 15 of 19 models still scoring; seed spread, balanced and IPO arms to follow.
> The `parent_ckptgen` equality check also passed: identical to `parent` on IFEval and MGSM, confirming E2.
>
> **A by-product worth keeping: the likelihood lane's intrinsic noise floor, measured for the first time.**
> `parent` and `parent_ckptgen` are the same weights on the same frozen prompts. The generated lanes came
> back **bit-identical** (0 of 541 IFEval items, 0 of 250 MGSM). Global-MMLU-Lite differed on **51 of 2,400
> items across 24 of the 36 leaves**, netting 0.04 pp. That is pure numerical nondeterminism in likelihood
> scoring — bf16 batching and reduction order flipping near-ties — and it is the floor against which any
> Global-MMLU difference must be read. It bounds how much of a small Global-MMLU difference can be numerical; it does NOT establish a share of the
> churn in any parent-vs-arm comparison, which is a different pair of models. The two generated lanes were
> exactly reproducible in this one repeat; that is one observation, not a general guarantee of zero noise.


> **UPDATE, evening of 19 September — a sixth error (E6) supersedes much of what follows.** Under the lm_eval
> environment every DPO checkpoint loaded with the WRONG rotary settings; see "E6" below. Rows marked CLEAN or
> SURVIVES for any parent-versus-arm lm_eval contrast are downgraded there. The re-run list is replaced by R1′–R3.

19 September 2026. Companion to the six reviews in `reviews/` (R-DPO6, 7a, 7a2, 7b, 7b2, 7c).
"Poisoned" means: the number may be fine, but the **comparison it was used in** is not controlled,
so the conclusion drawn from it is not supported. Raw scores are never deleted.

## The six errors

| id | error | root cause | found by |
|---|---|---|---|
| **E1** | **Run-date in the prompt** | the chat template renders `Current date: strftime_now('%Y-%m-%d')`. Everything that uses the template is stamped with the day it ran. | R-DPO7c |
| **E2** | Generation config differs between parent and checkpoints | transformers 5.16.1 re-serialised checkpoints: eos 2→68, use_cache on→off | us, 18 Sept |
| **E3** | Global-MMLU-Lite averaged 6 group rows + their 36 children | `consolidate.py` globbed `global_mmlu_*` | R-DPO7a |
| **E4** | "GreekMMLU" was a custom protocol on an adaptive 250-item sample | native runner = full-text mean-log-prob; sample = `Random(42)` over the raw frame: 0/100 overlap with the frozen screen manifest, 7 contaminated items | R-DPO7b2, owner |
| **E6** | **Arms mis-loaded in the lm_eval environment** | checkpoints saved by transformers 5.16.1 keep RoPE under `rope_parameters`; the lm_eval env (4.57.0) ignores it → arms ran with rope_theta 12,000,000 (the 4.57 default; llama3 scaling factor 8 / original 8192 is still applied); parent (saved by 4.57) ran with the intended 500,000 + the same llama3 scaling. Verified by `ApertusRotaryEmbedding.inv_freq` digests (parent `4ae228093081`, arm `082aa1f8a9e9`). vllm + sft5 venvs (5.16.1) resolve both correctly. The CPT-card finalizer had refused these checkpoints for "geometry drift: rope_theta" and was bypassed. | R-DPO9 |
| **E5** | Claims in prose that no receipt supported | "the arm that did not train" (it ran 129/129 steps); "any perturbation does this" (no control run) | R-DPO7c |


### E6 — what it reaches

| lane | environment | arms loaded correctly? | consequence |
|---|---|---|---|
| DPO training | sft5, tf 5.16.1 | yes | training and §3–4 displacement unaffected |
| **lm_eval: IFEval, MGSM, Global-MMLU-Lite** (the arm runs among 54 generated-lane and 51 Global-MMLU entries; of the 2×2, the two *arm* cells — `parent_ckptcfg` kept correct geometry) | `python_envs/lm_eval`, tf 4.57.0 | **NO** | every parent-vs-arm contrast compares a correctly loaded parent with a mis-loaded arm. **MGSM −6…−7.6 pp, Global-MMLU −5…−8 pp, IFEval ±1–2 pp, the "config confound", the date-matched scorecard: none identifies a training effect.** |
| **custom GreekMMLU** (250-slice ×66, full ×8) | same env | **NO** | parent-vs-arm gains (+2.0 slice, +0.3…+0.5 full) carry the same defect |
| official GreekMMLU (parent + 3 arms) | vllm venv, tf 5.16.1 | yes | **−0.41 / −0.43 / −0.26 pp stands** |
| served lane: MATH-500, IFBench | vLLM, tf 5.16.1 | yes | geometry fine; still E1 (date, unverifiable) + E2 (no config control) |
| arm-vs-arm lm_eval contrasts (α0 vs α0.25; BAL vs standard) | tf 4.57.0 | both sides equally wrong | stand as observations **under the mis-loaded condition**; may not transfer to correctly loaded models |

Corrections to earlier rows of this ledger (R-DPO9): the movement-axis arms 01/05/07/08 were all *trained* on
18 Sept (only their evaluation dates differ) — the earlier "span two training dates" was wrong. BAL's multilingual
deficit **is** measured date-matched against the late standard seeds: −2.51 pp vs plain, −2.85 vs anchored
(−2.69/−3.02 restricting training date too) — "no date-matched measurement" understated it; only its absolute
loss against the parent is unmeasured. "Same-day Global-MMLU losses are CLEAN" is withdrawn (E6).

### E2 withdrawn — the nominal generation-config axis is inert in this lm_eval setup

Verified on the cluster with the evaluator's own code (`run_receipt.py generation`): after every override the
EFFECTIVE generation settings of the parent, the `parent_ckptcfg` stage and the arms are **byte-identical**
(digest `857c25f224c3`). lm_eval passes `use_cache=True` and the tokenizer's pad id unconditionally, and the two
EOS lists `[2, 68]` and `[68, 2, 68]` stop on the same tokens. The published "pure configuration penalty" of
−1.7 pp IFEval / −2.4 pp MGSM (`parent` vs `parent_ckptcfg`) compared two runs that differed in the prompt date
and nothing else that generation uses. Of the 2×2's nominal axes the generation config was not one: its cells differed by date (both parent runs) and by weights **and** effective geometry (the arm cells). This is a statement about *this* lm_eval path, not about serving generally — vLLM applies its own generation settings and is not covered by it.

`parent_exportcfg` measures E6 **on the parent's weights**; whether the same size applies to trained weights is
an assumption, not a measurement — the repaired arm runs are what measure the arms.

## Re-run list (replaces the one below)

One job, `cluster/eval_jobs/dpo01_frozen_rescore.sh`: prompt date frozen (E1), **RoPE settings restored to the
legacy keys in a staged config and the rotary frequency table asserted equal to the parent's before scoring (E6)**,
effective geometry recorded in an in-job run receipt that `rlhf.evals` binds to the outputs. **No earlier lm_eval
arm run is reused** — all carry E6.

| # | what | answers |
|---|---|---|
| **R1′** | parent (own config) · parent under checkpoint gen-config · **parent weights under a checkpoint's *export* config, un-repaired** (`parent_exportcfg`) — all lanes | the last one measures the artefact directly: the parent's own weights, mis-loaded exactly as the arms were |
| **R1′** | 16 arms, geometry repaired, checkpoint gen-config, all lanes: α0 ×5, α0.25 ×5, BAL ×3, IPO ×2, `arm07_ep3` (repeat) | the real training effect on IFEval / MGSM / Global-MMLU-Lite; real dispersion; a true same-prompt repeat |
| ~~R2′~~ | ~~the same 16 under the parent's gen-config~~ | **dropped (R-DPO10):** that axis is inert — see "E2 withdrawn" below. `parent_ckptgen` stays as the empirical check that it is |
| **R3** | official GreekMMLU for the 12 remaining epoch-3 runs | unchanged; unaffected by E6 |
| dropped | the movement axis (arm01/05 ep1–2, arm07 ep4–5, arm08) | claim already withdrawn as a mechanism, n=1 per point; not worth re-scoring |

### E1 is wider than the 2×2 it was found in

Scoring date of every lm_eval run (IFEval, MGSM **and Global-MMLU-Lite — likelihood scoring does not
remove the prompt**):

| scored 18 Sept (28 runs) | scored 19 Sept (26 runs) |
|---|---|
| **parent** (the only Global-MMLU baseline), arms 00–06 all epochs, seeds 42 and 43 | `parent_ckptcfg`, both `*_parentcfg` cells, seeds 44–46, **every balanced run, every IPO run**, arm07 (4–5 epochs), arm08 (4e-6) |

Size of the effect, from the one probe we hold with identical config **and** seed scored a day apart
(`arm05_ep3` → `arm07_ep3`): IFEval −0.92 pp, MGSM −2.80 pp, Global-MMLU-Lite −0.71 pp. That pair was
previously reported as the "same-seed repeat gap from ZeRO non-determinism". It is date **plus**
non-determinism and the two cannot be separated, so neither is measured.

The served lane (MATH-500, IFBench) is tainted the same way and **cannot be checked**: vLLM renders
the same template, and `generate.py` saved responses only, never the prompt. Parent served 18 Sept
20:18; later seeds 19 Sept 05:03. That lane also has **no configuration control at all** (E2).

DPO **training** prompts carry the date too — `cluster/dpo_train.py:67-70` renders the template for length
processing and TRL (`dpo_trainer.py:322`, `data_utils.py:228,247`) renders it again when preparing the
examples. By trainer-state mtime: arms 00–08, standard seeds 42–43 and **BAL seed 42** trained with
"2026-09-18"; standard seeds 44–46, **BALs43, BALs44** and both IPO runs with "2026-09-19". Effect unknown;
not worth a retrain. **No re-score can remove it**, so runs trained on different days are never exchangeable
replicates, and what R1 yields is *dispersion among checkpoints trained under differently dated prompts*,
not a pure seed SD.

## Status of every published claim

| claim | poisoned by | status | clean evidence we already hold |
|---|---|---|---|
| Held-out likelihood displacement; anchor controls it monotonically (§3–4) | — | **CLEAN as a contrast** | The prompts DO carry the date (an earlier version of this row said otherwise). It does not confound the result because policy and frozen reference see the same rendered prompt within a run, and all five dose arms were trained on the 18th. The absolute displacement could still depend on the date. |
| α=0.25 vs α=0: +0.70 pp, unresolved | E1 partly | **point estimate CLEAN; published interval was mislabelled** | Seeds are matched one-to-one by seed AND date across the two arms (42/43 on the 18th, 44/45/46 on the 19th), so the +0.70 pp is date-clean. But the published [−0.52, +1.77] is an **unpaired** bootstrap. The paired one over the five seed differences (+0.37, +1.11, −2.03, +2.03, +2.03) is **[−0.74, +1.85]** (`results/G4F6P1--DPO01/alpha_interval.json`). Still inconclusive. |
| Between-seed SD (IFEval .76/1.25 pp, MGSM 2.30/.95 pp) | **E1** | **POISONED** | each n=5 group mixes two dates; the SD contains the date effect |
| "Same-seed repeat gap 0.9 / 2.8 pp" | **E1** | **POISONED** | it is a cross-date pair |
| Config confound "−1.7 pp IFEval, −2.4 pp MGSM" | **E1** | **POISONED** | `parent` 18 Sept vs `parent_ckptcfg` 19 Sept |
| "Configuration interaction / IFEval reverses" | **E1** | **WITHDRAWN** | — |
| Scorecard IFEval/MGSM deltas vs `parent_ckptcfg` | **E1** for any 18-Sept run | **PARTLY POISONED** | date-matched subset: seeds 44–46, all BAL, all IPO. MGSM −7.60 (plain) / −6.13 (anchored); BAL +6.00 / +4.53 over them |
| MGSM regression exists | E1, E2 | **SURVIVES on the date-matched subset** | as above; mechanism not established |
| Balanced subset reduces the MGSM deficit | E1 (training date) | **SURVIVES qualitatively** | every BAL run (40.0–41.6%) > every standard run (32.4–38.4%). But BAL seed 42 was trained on the 18th and BALs43/s44 on the 19th, so the three-run mean is not a date-pure seed estimate; the two 19th-trained runs against 19th-trained standard seeds are the controlled part. |
| Global-MMLU-Lite deltas (−5.3 … −8.4) | **E1** for every 19-Sept run; E3 fixed | **POISONED for BAL, IPO, seeds 44–46** | clean only for 18-Sept runs vs the 18-Sept parent: plain −5.5/−5.7, anchored −4.9/−5.0 |
| "Balanced arm is the worst on multilingual (−8.4 vs −5.5)" | **E1** | **POISONED** | all BAL runs are 19 Sept, the parent is 18 Sept. The 19-Sept standard seeds are only ~0.3–0.6 pp lower than the 18-Sept ones, so most of the 2.9 pp gap probably survives — but that is an estimate, not a measurement |
| Movement trend / "no recovery at the far end" | **E1**, n=1 | **POISONED** | arm07 ep4–5 and arm08 ep1–3 were scored 19 Sept; the rest of the axis (arm01/05 ep1–3) and the parent 18 Sept. R1 re-scores the 18-Sept half at the frozen date. The checkpoints also span two training dates, which nothing repairs. |
| Served-lane tally 35/8/2 | **E1 + E2, unverifiable** | **POISONED** | prompts not saved; no config control |
| GreekMMLU-250, all 66 models | **E4** | **SUPERSEDED** | internally consistent custom diagnostic only |
| GreekMMLU custom full run, 8/8 models (+0.28…+0.52 held out) | E4 | **VALID but wrong ruler** | finalized with pinned frames. The job completed all 8; an earlier note said it was cancelled at 4 — it had already finished. |
| **GreekMMLU official: −0.41 / −0.43 / −0.26 pp, all significant** | — | **CLEAN** | one run, one day, no chat template so no date, one dataset hash, tokenizers byte-identical |
| "IPO did not train" | **E5** | **WITHDRAWN** | trainer_state: 129/129 steps |

## Re-run list — SUPERSEDED by R1′/R2′ above (kept for the record)

The freeze: a staged tokenizer whose template has the literal `'2026-09-19'` where `strftime_now` was,
passed to lm_eval as `tokenizer=` (no script may override it with `tokenizer=$PARENT`). The date is
the 19th on purpose: prompts are then byte-identical to the 26 runs already scored that day, which
`rlhf.evals.compare()` verifies by request digest, so those are reused rather than re-bought.
Job: `cluster/eval_jobs/dpo01_frozen_rescore.sh`, list `dpo01_frozen_models.txt`.

| # | what | cures | does NOT cure |
|---|---|---|---|
| **R1** | Frozen-date re-score of everything scored on the 18th that a claim still rests on: parent (own config, all lanes — also the Global-MMLU baseline), `parent_ckptcfg` (all lanes), α0 and α0.25 seeds 42–43, and the movement axis arm01/arm05 ep1–2 | evaluation-date mixing in the scorecard, seed dispersion, Global-MMLU deltas (incl. BAL/IPO vs parent), movement axis; `arm05_ep3`↔`arm07_ep3` becomes a true same-prompt repeat | the training-prompt date. Dispersion stays "checkpoints trained under differently dated prompts" |
| **R2** | The **replicated scorecard arms** (α0 ×5, α0.25 ×5, BAL ×3, IPO ×2) and the repeat run `arm07_ep3` under the **parent's** generation config, IFEval + MGSM only. Single-run arms 00, 02–04, 06, 08 are deliberately excluded: no surviving claim rests on them (Global-MMLU is likelihood-scored; generation settings do not reach it) | the deployment column and a date-clean estimate of the config effect, in both directions (parent@ckpt-config is in R1) | — |
| **R3** | Official-protocol GreekMMLU for the 12 epoch-3 runs not yet scored (`cluster/dpo01_official_gmmlu_rest.sh`). The four done need no re-run. | E4; seed dispersion on the right ruler; whether BAL differs | — |
| R4 | Served lane (MATH-500, IFBench) with an explicit frozen `--chat-template`, **requests saved** (messages, rendered prompt or token ids, template digest, generation config), parent under both configs | E1+E2 for those lanes | **not scheduled** — only if those lanes matter to a decision |

## Stale documents

Corrected numbers on the page do not fix older documents that still assert the old ones. Each of these
now opens with a correction banner pointing here:

- `docs/RLHF_COORDINATION/OVERNIGHT_20260918.md` — "IPO did not train", obsolete GreekMMLU gaps, pre-fix Global-MMLU
- `docs/RLHF_COORDINATION/reviews/R-DPO6_response.md` — the no-training premise, the "same-seed" repeat gap, the unpaired α interval described as seed-level
- `docs/RLHF_COORDINATION/reviews/R-DPO7a_response.md` — E1-poisoned Global-MMLU group deltas, "armIPO which reached 2% of its training target"
- `docs/DPO01_CURVES_20260918.html` is regenerated from the generator on every publish; the copy R-DPO8 read predated v15.

## Review findings: status of all 38

| review | finding | status |
|---|---|---|
| R-DPO6 | BLOCKER no independent verification | **closed** — it was our harness blinding the reviewer; five reviews since have recomputed |
| | HIGH noise floor as threshold | fixed in text; **the quantities themselves are now E1-poisoned → R1** |
| | HIGH fair baseline is conditional | fixed; superseded by E1 |
| | HIGH balanced ≠ length | fixed (confound stated) |
| | HIGH "barely trained because of β" | fixed |
| | HIGH seed stability ≠ precision | fixed |
| | HIGH correlations ≠ mechanisms | fixed (withdrawn) |
| R-DPO7a | HIGH Global-MMLU misaggregation | **fixed + verified by 7a2** |
| | MEDIUM baseline fallback | **fixed + verified** |
| | MEDIUM partial input | partly: root + completeness. **open:** deterministic file choice, zero-model fail → replaced by `rlhf/evals` |
| | LOW flip IDs in prose | **fixed** (renders from `common_flips`) |
| R-DPO7a2 | BLOCKER manifest descriptor | **fixed + verified by 7b2 on the real manifest** |
| | HIGH counts not identity | fixed after 7b2 (metadata binding, exact raw frame, strict booleans); **not re-reviewed** |
| | MEDIUM 2×2 weights-only | superseded by E1 |
| | LOW stale constants | **fixed** |
| R-DPO7b | BLOCKER raw 16,632 vs clean | **fixed + verified** |
| | HIGH shared stage | fixed in both scripts after 7b2; **not re-reviewed**. No checkpoint was damaged (68/68 verified) |
| | HIGH tokenizer unchecked | fixed fail-closed after 7b2; **not re-reviewed**. All 68 tokenizers verified identical |
| | HIGH failures exit 0 | partly — rc is logged, headline still decides. **open**; the finalizer is the receipt |
| | MEDIUM headline accepts malformed | **open** (mitigated by the finalizer) |
| | MEDIUM asymmetric overlay | **fixed + verified** |
| R-DPO7b2 | BLOCKER finalizer identity | fixed; **not re-reviewed** |
| | HIGH live job false success | moot — the job had in fact completed all 8 models (not 4, as an earlier note said); all 8 pass the pinned finalizer |
| | HIGH shared-stage incomplete | fixed; not re-reviewed |
| | HIGH tokenizer fail-open | fixed; not re-reviewed |
| | HIGH 250 slice not frozen, not official | **addressed by running the official protocol**; page labels the rest as a custom diagnostic |
| | HIGH no safe join full↔250 | page keeps them in separate tables; **structurally open** until the typed results store exists |
| | MEDIUM manifest contract optional | **fixed** |
| R-DPO7c | BLOCKER date crosses the 2×2 | claim withdrawn; **the wider taint is this ledger → R1** |
| | HIGH IPO is not untrained | **fixed** |
| | HIGH unequal standards MGSM | **fixed** |
| | HIGH α equivalence | **fixed** |
| | HIGH stale render + verification banner | **fixed** |
| | MEDIUM balanced population / exposure | **fixed** |
| | MEDIUM custom-protocol caveat | fixed, then overtaken by the official run |
| | asks: "nothing shippable", "only instrumentation", 235 as a ceiling | **open → fixing now** |
| R-DPO8 | BLOCKER comparison policy caller-bypassable | **fixed** — closed `POLICIES`; no `varying`/`allow_unknown` parameters exist; unknowns are declared by the builder per protocol from a closed table |
| | HIGH per-request generation options / runtime unbound | **fixed** — whole request digested; runtime (dtype, batch, seeds, n-shot, task hash/version/config) is an identity key |
| | HIGH weights identity caller-supplied | **fixed** — content receipt over resolved shards (`rlhf/evals/weights.py`); a label is refused; a symlinked stage resolves to its target's identity |
| | HIGH item/gold identity | **fixed** — id bound to recomputed document and target hashes |
| | HIGH re-run cure insufficient | **fixed** — what R1 does not cure is stated; movement axis added; R2 generated lanes only |
| | HIGH α interval mislabelled | **fixed** — paired bootstrap implemented, pinned in a test, published as [−0.74, +1.85] |
| | HIGH stale published documents | **fixed** — correction banners on three documents |
| | HIGH finalizer trusts the first model | **fixed** — raw frame and 250-slice pinned by sha256; manifest checked against pinned dataset identity; `--expect` mandatory |
| | HIGH tokenizer fail-open, cross-job cleanup | **closed by retirement** — the four legacy launchers exit 64; the replacement refuses a missing or different tokenizer and removes only its own stages |
| | HIGH launchers report success after failure | **closed by retirement**; the replacement requires rc==0 AND validated output per model, else exits non-zero |
| | HIGH official driver | **fixed** — per-run output dir, per-scorer exit receipts, WALL>MAXWAIT enforced, ≤4 models, full-frame validation before acceptance |
| | MEDIUM displacement rationale · MEDIUM paired bootstrap · LOW chat_template flag · LOW stats validation | **fixed** |
| R-DPO8b | BLOCKER guard still accepts uncontrolled public comparisons | **fixed** — one sealed, immutable `Result` (manifest + outcomes) that only the builders and the Store can mint; `compare(a, b, policy)` takes nothing else; manifest-level check is private; Store re-verifies the seal on load. All seven cycle-2 defeats are regression tests (31/31 pass) |
| | HIGH receipt id trusted | **fixed** — id recomputed from the listed shard hashes; a relabelled receipt is refused |
| | HIGH frozen list ≠ ledger | **fixed** — four movement checkpoints added, two already-19th cells removed, R2 wording narrowed to the replicated arms; 24 models. `parent_ckptcfg` kept deliberately (it has no Global-MMLU run; reason in the list header) |
| | HIGH R3 staging rejects every checkpoint | **fixed** — checks the resolved `*.safetensors` target (these are single-shard, no index); dry-run against a real checkpoint returns OK |
| | HIGH official validation count-only | **fixed** — `validate_official_result.py`: pinned dataset sha, exact frame, protocol, settings, strict booleans, correct==(pred==answer), recomputed accuracy, expected model path |
| | HIGH workbench shutdown unverified | **fixed** — explicit `scancel`, then waits for the scheduler to drop the job; still allocated after 5 min = FATAL with the command to run |
| | MEDIUM `.validated` weak | **fixed** — written only after `rlhf.evals` parses every sample and seals a manifest per lane; tested on a real run in both directions |
| | MEDIUM stale 4-model row · LOW WALL default | **fixed** (the missing default was my own search-and-replace) |
| R-DPO9 | **BLOCKER B1: arms mis-loaded (RoPE) in the lm_eval env** | **confirmed firsthand and against the reference contract** (`eellak/greek-apertus` `validate_full_8b_contract.py:111` requires base 500000, factor 8, 4096 ctx; every other architecture field matches in both envs). Recorded as **E6** above; page v17 leads with it. Job rebuilt: legacy RoPE keys restored in a per-job stage; a CPU geometry gate requires the rotary table to equal the parent's before any scoring; `parent_exportcfg` reproduces the artefact on purpose to measure it. **Dry-run on the cluster: 35/35 models pass the gate** (34 = parent's table, 1 = the intended mis-load) |
| | BLOCKER B2: sealed API still accepted uncontrolled comparisons | **fixed** — builders take NO identity arguments; identity comes from `run_receipt.json`, written inside the scoring env after scoring and bound to a hash of every output file; effective `geometry` is an identity key with its own policy; `POLICIES` is read-only. Four new regression tests; the comparison the first test suite accepted as "controlled" (parent_ckptcfg vs a 19-Sept arm) is now refused. 38/38 |
| | HIGH H1: contradictory active claims on the page | **fixed** — all five removed; verified absent from the rendered HTML |
| | HIGH H2: official validation weak | **fixed** — pinned gold answers (`greekmmlu_gold.tsv`, sha-pinned, agrees with the genuine result on 16,632 rows), expected `model_config_sha256`, finite bounded accuracy, non-boolean int indices, exact row schema. All four of the review's mutations are rejected |
| | HIGH H3: failed scheduler query read as "released" | **fixed** — sentinel-carrying query; ssh failure = unknown = FATAL; dirty-node path uses the same function. Simulated: gone → 0, still running → 1, ssh failure → 1 |
| | MEDIUM reuse trusts markers | **fixed** — both jobs re-validate an existing result from its files before skipping it |
| | MEDIUM/LOW record items (BAL multilingual understated; movement-axis training dates; §9 body; "+2.00 exactly"; Holm p; 274 of 343) | **fixed** on the page and in the E6 block above |
| | dry-run finding (ours) | the canary failed closed on its first real execution: its environment lacked `LD_LIBRARY_PATH`. Fixed; a launch without the dry-run would have died at step 1b |
| R-DPO10 | BLOCKER official/native builders still took identity as arguments | **fixed** — `from_official_greekmmlu(path)` takes no identity; `<result>.receipt.json` is written ON THE CLUSTER by `official_receipt.py`, hashing the result file and the weight shards the scored dir resolves to (done for the 4 existing results; ids equal the independent hashes). The same result file as two models is now refused three ways (stale positional call, missing receipt, another result's receipt) and tested. `from_native_mcq` left the public API; legacy custom-protocol results carry `caller-asserted` and are never comparable |
| | HIGH generation-config axis inert; receipts recorded inactive fields | **fixed** — receipt records EFFECTIVE generation settings (GenerationConfig + lm_eval overrides); verified identical across parent/stage/arm; the 16 `parent|gen` runs dropped (35 → 19 models); E2 withdrawn above and on the page |
| | HIGH page still reinstated withdrawn conclusions | **fixed** — all five passages; verified absent from the rendered HTML (v18) |
| | MEDIUM E6 mechanism / coverage / speculation | **fixed** — "12M with llama3 scaling"; coverage counts; every sentence guessing the artefact's share removed; `parent_exportcfg` scoped to parent weights |
| | MEDIUM resume + store identity | **fixed** — resume requires the saved receipt's weights id, mode and date to equal the requested list entry; store key includes weights, geometry, runtime, population (tested) |
| | MEDIUM dirty-node record, ambiguous sacct | **fixed** — no "closed" record unless release was confirmed; sacct must return terminal states only |
| | MEDIUM staged tree not a mirror | **fixed** — `cluster/eval_jobs/` synced wholesale, retired launchers included |
| | `mint_receipt` | kept as a unit-test fixture only, labelled as such; historic runs have NO production receipts and cannot enter a comparison (tested: "no run_receipt.json") |
| R-DPO11 | HIGH Global-MMLU runtime identity carried process memory addresses | **fixed** — lm_eval serialises task callables as `functools.partial(<function process_docs at 0x…>, category='Business')` and the address differs per process, so `compare()` refused all 36 Global-MMLU lanes: the frozen job would have produced numbers the guard could not use. `_stable()` strips ` at 0x…` and keeps the function NAME and the partial's arguments. (R-DPO12: it does not keep module or code identity — a Python repr carries neither. Fine for these fixed tasks; a task-source digest is needed before comparing across task-code revisions. Logged as follow-up.) Regression on the real 38-lane outputs of two models, separately serialised: **38/38 compare**, while a changed `category=` or function name still differs |
| | HIGH page still reinstated withdrawn conclusions | **fixed** — all four passages (v19); "the configuration confound" is now *withdrawn* rather than "not cleanly measured"; the ask is the corrected re-score, not another 2×2 |
| | MEDIUM resume binding | **fixed** — resume requires the receipt's weights id, FULL config spec (`verbatim:<src>` distinguishes sources) and geometry to match the requested entry; official resume additionally requires the evaluator receipt to load through `rlhf.evals` |
| | MEDIUM `CANCELLED by 123` + RUNNING accepted | **fixed** — `sacct -P` parsed per record, every record must be terminal. Simulated: terminal → 0; CANCELLED+RUNNING → 1; `CANCELLED by 123`+RUNNING → 1; ssh failure → 1; live → 1 |
| | ledger E2 scope | **fixed** — scoped to "the nominal generation-config axis is inert in this lm_eval setup"; says explicitly it does not establish serving-environment equivalence |
| | `parent_ckptgen` refused by compare() | **as designed** — its effective identity equals `parent`, so it is not a comparison; it is read as an equality check on matching manifests and per-item outcomes |

---

## Spend, 19–20 September

Owner raised the cap by CHF 500 on 20 Sept with standing authorisation to spend without asking,
against a record. Measured at the CSCS rate used by `cluster/ledger.sh`.

| run | what it bought | node-h | ~CHF |
|---|---|---|---|
| config 2×2 cell (3443153) | the missing off-diagonal cell; showed the "configuration effect" was the date | 1.3 | 4 |
| custom GreekMMLU full, 8 models (3443296) | the 250-item slice was too small to decide anything | 1.8 | 5 |
| official GreekMMLU, parent + 3 arms | the protocol that is comparable to a published number | 0.8 | 2 |
| **frozen re-score, 19 models (3444789)** | **the round's real result: geometry repaired, date frozen, weights the only difference** | 2.7 | 8 |
| official GreekMMLU, remaining 12 | seed spread on the Greek lane; all 15 arms | 2.5 | 7 |
| dual-protocol test, 4 models | Q4: the Greek deficit is protocol-sensitive (the stronger "artefact" reading was withdrawn by R-DPO15) | 0.8 | 2 |
| cap3500 truncation test (3453314) | Q2: whether the IFEval gain is compliance or termination | ~0.5 | ~2 |
| Q4 scores re-run (3453470) | per-choice log-probs, so the label prior can be calibrated | ~0.8 | ~2 |

Two launches cost nothing because they failed closed in seconds: the first cap4096 attempt (OUT_DIR
not honoured, so every model was correctly skipped as already-scored) and the second (4096 generated
tokens against a 4096 context — lm_eval refused). Both were my errors; neither reached a GPU.

| Q1/Q3 training, 6 runs (3455469) | the 56-pair ablation + its random-cut control, and IPO actually running | ~0.8 | ~2 |
| Q1/Q3 frozen re-score, 7 models (queued) | IFEval + MGSM + Global-MMLU-Lite on the six new arms | ~1.2 | ~4 |

Running total for the correction work: roughly **13 node-hours, ~CHF 38**, against a raised cap of
CHF 500. Reviews (Sol/Astra, cross-vendor) run on the owner's ChatGPT subscription and are not
metered here; R-DPO15 was one xhigh review.

## Review outcomes

| review | scope | verdict |
|---|---|---|
| R-DPO15 (Sol, xhigh) | Q4 calibration soundness, Q2 cap rerun | Q4 unsound as stated, Q2 qualified; 1 BLOCKER + 3 HIGH, all confirmed firsthand and applied (artifact v23) |
