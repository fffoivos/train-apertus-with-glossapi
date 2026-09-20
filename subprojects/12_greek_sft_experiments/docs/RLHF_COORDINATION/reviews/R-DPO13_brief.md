# Review brief R-DPO13 (Sol) — are these positive results legitimate?

**One question: is the result below real, or is there an artefact we have not found?**

Yesterday this programme published DPO round 1 as damaging: "a serious mathematics regression",
−6 to −8 pp MGSM. A cross-vendor review then found that every trained checkpoint was loaded with the
wrong rotary base under the lm_eval environment (transformers 4.57 ignores the `rope_parameters` key
that transformers 5.16.1 writes, and falls back to theta 12,000,000; the parent, saved by 4.57, kept
the intended 500,000). We re-scored 19 models with the prompt date frozen and the rotary settings
repaired. **Every arm is now positive on every generated lane.** We do not believe it yet.

Read-only; `ssh clariden` works; launch nothing. Working dir: `subprojects/12_greek_sft_experiments/`.

## The result

`results/G4F6P1--DPO01/frozen_results.json`; runs under
`/iopsstor/scratch/cscs/fffoivos/sft_round1/results/G4F6P1--DPO01/frozen/<label>__<mode>cfg/`.

| group | runs | IFEval | Δ | MGSM | Δ | Global-MMLU-Lite | Δ |
|---|---|---|---|---|---|---|---|
| parent | 1 | 0.6026 | — | 0.4240 | — | 0.6154 | — |
| plain DPO α=0 | 5 | 0.6429 | +4.03 | 0.5088 | **+8.48** | 0.6264 | +1.10 |
| anchored α=0.25 | 5 | 0.6421 | +3.96 | 0.5144 | **+9.04** | 0.6303 | +1.49 |
| length-balanced | 3 | 0.6574 | +5.48 | 0.5360 | **+11.20** | 0.6135 | −0.19 |
| IPO β=10 | 2 | 0.6220 | +1.94 | 0.4740 | +5.00 | 0.6331 | +1.77 |

Between-seed SD: IFEval 0.46–0.65 pp, MGSM 0.85–1.95 pp.
Artefact measured directly (parent's OWN weights, mis-loaded vs correct — `parent_exportcfg` vs
`parent_ckptgen`): **−4.07 IFEval, −9.60 MGSM, −7.63 Global-MMLU.**
Equality check: `parent` and `parent_ckptgen` scored **identical** on both generated lanes.

## Why we are suspicious

The 397 preference pairs contain **no mathematics** — maths was deliberately removed from the RLHF
target. An 8–11 pp MGSM gain from them is not obviously a reasoning improvement. Our own item-level
check found 48 gained / 31 lost for `arm01_ep3` (32% of MGSM items changed), of which only 4 gains
were cases where the parent's text already held the gold number, so it is not mainly answer
extraction. We cannot explain the mechanism. Also: under the **official** GreekMMLU protocol
(correctly loaded, no chat template, `results/greekmmlu_official/`) the same arms score 0.26–0.43 pp
**BELOW** the parent — which does not fit "everything improved".

## Attack these specifically

1. **Is the repair legitimate, or did we hand the arms a better model than they were trained with?**
   The arms trained under transformers 5.16.1; we restored `rope_theta`/`rope_scaling` from their
   `rope_parameters` so 4.57 resolves them. Verify the repaired eval geometry equals the geometry the
   arms actually TRAINED with (check the training env's resolution, `cluster/dpo_train.py`, the sft5
   venv, and the checkpoints' own config). If training used something else, the gain may be an
   evaluation upgrade rather than a training effect. Check the same for the parent.
2. **Is the parent's own run fair?** It is n=1 and is the baseline for every arm. Generated lanes are
   deterministic here (0 of 250 items differ between two same-weights runs) — verify that claim, and
   check the parent was not disadvantaged: frozen tokenizer, staging, truncation, max_gen_toks,
   stop conditions, and that `parent` and `parent_ckptgen` really are identical.
3. **Are the arms the arms?** Weight content receipts are in
   `/iopsstor/scratch/cscs/fffoivos/sft_round1/receipts/weights/` and inside each `run_receipt.json`.
   Confirm each run's weights resolve to the intended checkpoint and that no two runs share weights.
4. **Contamination.** Could the DPO pairs (`data/rlhf/dpo01/`, and the doc of all 397 pairs at
   `docs/DPO01_TRAINING_PAIRS_20260918.md`) overlap MGSM, IFEval or Global-MMLU items?
5. **Stopping and truncation.** Parent generation config lists EOS `[2, 68]`, checkpoints `[68, 2, 68]`.
   We claim identical stopping. Verify. Check truncation/length effects on MGSM scoring.
6. **The MGSM churn.** 32% of items change. Is a net +8.5 pp from that churn credible, or does the
   pattern look like something other than a capability change? Item files are in each run dir.
7. **The GreekMMLU contradiction.** Explain or bound it. Is it protocol, language (Greek vs the six
   non-Greek Global-MMLU languages), or evidence against the whole picture?
8. **Anything we have not thought of.** This is the eighth consecutive round in which an artefact was
   found in these numbers. Assume there is a ninth.

## What we want back

For each: is the finding supported, and at what strength? If the result is real, say what may
legitimately be claimed and what may not. If it is an artefact, name it and show the number that
proves it. **Do not accept our framing; we have been wrong in both directions this week.**

## Disposition

BLOCKER/HIGH change what we publish. MEDIUM/LOW are logged.

## Deliverable

Markdown. Header (what you ran) → one-line verdict → point-by-point on the eight items above with the
deciding numbers → any new findings, most-severe-first, with `path:line` → permissible wording for the
headline claim → ordered asks.
**Last line exactly:** `VERDICT: <one line> | BLOCKERS: <n> | HIGH: <n> | RESULT: <real|artefact|unresolved>`
