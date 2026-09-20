#!/usr/bin/env bash
# Harvest the DPO01 screen and produce the §5 table + §8 paired comparison.
#
# The IFEval rescore MUST run where langdetect exists (the cluster harness lacks it, so every
# language:response_language instruction scores 0 there for every model). We therefore pull the
# saved samples to the Mac and rescore locally with the apertus-local-chat venv, reusing
# evals/ilsp/rescore_ifeval_langdetect.py UNMODIFIED - the samples are rearranged into the
# <root>/<label>/ilsp/<model>/ layout that script globs for, rather than editing the scorer.
#
#   bash cluster/eval_jobs/dpo01_harvest.sh [local_root]
set -euo pipefail
ROOT=${1:-results/G4F6P1--DPO01/screen_local}
REMOTE=/iopsstor/scratch/cscs/fffoivos/sft_round1/results/G4F6P1--DPO01/full
LANGPY=$HOME/Projects/apertus-local-chat/.venv/bin/python3
[ -x "$LANGPY" ] || { echo "FATAL: no langdetect interpreter at $LANGPY"; exit 1; }

mkdir -p "$ROOT"
echo "== pulling samples + results =="
rsync -a --prune-empty-dirs \
  --include='*/' --include='samples_*.jsonl' --include='results_*.json' --exclude='*' \
  clariden:"$REMOTE"/ "$ROOT/raw/"

echo "== rearranging into the layout rescore_ifeval_langdetect.py expects =="
rm -rf "$ROOT/for_rescore"
found=0
while IFS= read -r f; do
  rel=${f#$ROOT/raw/}
  label=${rel%%/*}
  model=$(basename "$(dirname "$f")")
  mkdir -p "$ROOT/for_rescore/$label/ilsp/$model"
  cp "$f" "$ROOT/for_rescore/$label/ilsp/$model/"
  found=$((found + 1))
done < <(find "$ROOT/raw" -name 'samples_ifeval_greek*.jsonl')
echo "   $found IFEval sample files staged"
[ "$found" -gt 0 ] || { echo "FATAL: no IFEval samples found - did the job write them?"; exit 1; }

echo "== rescoring with langdetect (unmodified scorer) =="
"$LANGPY" evals/ilsp/rescore_ifeval_langdetect.py "$ROOT/for_rescore"

echo "== paired item-level comparison vs parent (plan section 8) =="
python3 cluster/eval_jobs/dpo01_paired.py \
  --rescored "$ROOT/for_rescore/ifeval_el_rescored.json" \
  --json "$ROOT/paired_vs_parent.json"

echo "== aggregate screen table (MGSM + unrescored IFEval, for reference) =="
python3 cluster/eval_jobs/dpo01_screen_table.py --screen "$ROOT/raw" \
  --json "$ROOT/screen_table.json" || true
