# 12 — Greek SFT experiments on the Greek-CPT Apertus-8B

> **In one line:** the first supervised fine-tuning experiments of the Greek-continued-pretrained
> Apertus-8B (subproject 09) on the natural-Greek SFT data built in the sister repo
> `fffoivos/Greek-SFT-translated-and-adapted` — no_robots-el plus the six wave-1 sources.
> **Period:** opened 2026-09-03. **Status:** references gathered; recipes under examination; no run yet.

## Where the data comes from

The training data is produced and documented in `fffoivos/Greek-SFT-translated-and-adapted` (private GitHub) and
stored as one private HF dataset, `fffoivos/Greek-SFT-translated-and-adapted`, with one config per
source (`no_robots`, `coconot`, `personas_if`, `smolcon`, `oasst`, `everyday`, `systemchats`).
The dataset card describes the method (adaptation, not translation: frame moved into Greek
reality, content frozen; the no_robots voice measured and enforced; size anchors by task type;
two independent edit passes with the lighter one kept; owner-reviewed holds). The survey that
chose the sources is subproject `11_greek_posttraining` (formerly numbered 10).

## References (vendored, read-only)

| what | where | pinned |
|---|---|---|
| Fully Open Meditron (the Apertus SFT recipe paper) | `references/papers/2605.16215_fully_open_meditron.md` + PDF | arXiv v2, 2026-05-29 |
| `swiss-ai/apertus-finetuning-recipes` | `references/apertus-finetuning-recipes/` | see `references/apertus-finetuning-recipes.UPSTREAM_COMMIT.txt` |
| `swiss-ai/evals-post-train` | `references/evals-post-train/` | see `references/evals-post-train.UPSTREAM_COMMIT.txt` |

Vendored copies have their `.git` removed; the upstream commit and URL are recorded next to each.

## Plan

`SFT_PLAN_20260903.md` — the recipes and the literature examined against our data's shape, six
unknowns, an eight-run first round (E0–E6) with its evaluation, and the pre-flight list. Owner
decisions are marked ▶ in it.

## Data landed (2026-09-04)

All eleven configs are on the private HF dataset `fffoivos/Greek-SFT-translated-and-adapted`
(renamed from `natural-greek-sft-no-robots`): the seven Greek configs (17,968 rows) plus the
cross-language slices adapted to the Greek point of view in their own language (D37, "reading 2"):
`euroblocks_fr` 799, `euroblocks_de` 808, `apertus_en` 3,818 (persona math / GSM8K / persona
code / magpie-ultra), `no_robots_en_pov` 9,499 (human English with the Greek twin's entity moves,
5,217 rows transposed). Math rows whose final answer the adapter changed were independently
checked and the unconfirmed ones dropped (D38: fr 3, de 7, en 182 — 154 of them
"underdetermined" persona problems, restorable). The plan's mix table (§5c) should be re-read
with these counts: the English skills slice is 3.8k, not 4k, and fr/de are ~0.8k each.
