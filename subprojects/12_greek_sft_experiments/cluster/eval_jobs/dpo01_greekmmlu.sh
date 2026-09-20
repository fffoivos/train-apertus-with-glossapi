#!/bin/bash
#SBATCH --account=a0140
#SBATCH --job-name=dpo01_gmmlu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=288
#SBATCH --mem=640G
#SBATCH --time=03:30:00
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/dpo01_gmmlu_%j.out
# GreekMMLU, 250-item diagnostic, for the parent and every arm checkpoint.
#
# The owner approved the 250-item form on 18 September; it is the fallback the full-battery plan
# names when the allocation will not carry the full clean subset. Full GreekMMLU is 16,159 items x
# ~4 candidate continuations in float32 on ONE gpu (the scorer is not shardable) = ~2.8 h per model,
# which is ~9 node-hours for 22 models and does not fit the remaining budget. 250 items is ~1.5% of
# that work.
#
# The scorer, prompt form, precision and batch sizes are the CPT card's frozen ones, taken verbatim
# from cluster/eval_jobs/greekmmlu.sh. The ONLY change is --sample-size 250, with --random-state 42
# so every model sees the identical fixed 250 items. Do not "improve" any other flag: the parent's
# comparability depends on the protocol being byte-identical across models.
# ---------------------------------------------------------------------------------------------
# RETIRED 2026-09-19. R-DPO7b, R-DPO7b2 and R-DPO8 each traced fail-open paths through this script
# (success on a failed model, tokenizer checks that could be skipped, stage cleanup that could
# cross jobs). It is kept as the record of how the published numbers were produced and must not
# be run again: custom full-text GreekMMLU on an adaptive 250-item sample is superseded. Use cluster/greekmmlu_official.sh (official label protocol).
echo "RETIRED: $(basename "$0") - see the header"; exit 64
# ---------------------------------------------------------------------------------------------
set -uo pipefail
S=/iopsstor/scratch/cscs/fffoivos
ROUND=$S/sft_round1
# Paths taken from cluster/eval_jobs/common.sh, except FINALIZER: the snapshot common.sh names has an
# evaluation/ directory but no finalize_hf_greekmmlu.py. Every copy of that file on scratch is
# byte-identical (sha256 ca0b18b342e3...), so this points at a verified one rather than the empty path.
PYENV=$S/python_envs/lm_eval
WHEEL=$S/evals/full8_native_greek_peak_window_20260817/vendor_probe/accelerate-1.14.0-py3-none-any.whl
B=$S/orchestration/full8b-cpt/20260807T221007Z-sanitized-v43
NATIVE_ROOT=$B/subprojects/03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval
FINALIZER=$S/orchestration/targeted-8b-cpt/20260816T120000Z-hard-h2g-r2-5caa614d-safepath-v103/subprojects/07_full_8b_cpt/evaluation/finalize_hf_greekmmlu.py
CLEAN_SUBSET=/capstor/scratch/cscs/fffoivos/cpt_runs/dataset-scheduling-0p5b/20260803T064000Z-static-prelaunch-v2/greekmmlu_clean_subset_manifest.json
[ -f "$FINALIZER" ] || { echo "FATAL: finalizer missing at $FINALIZER"; exit 1; }
[ -f "$NATIVE_ROOT/run_native_greek_mcq_eval.py" ] || { echo "FATAL: native runner missing"; exit 1; }
OUT=$ROUND/results/G4F6P1--DPO01/greekmmlu
mkdir -p "$OUT"
PARENT=$ROUND/eval_copies/R4_full_ep1
[ -d "$PARENT" ] || { echo "FATAL: parent missing"; exit 1; }

MODELS=("parent|$PARENT")
for ep in 3:129 2:86 1:43; do
  for arm in 00 01 02 03 04 05 06 01s43 05s43 08 01s44 01s45 01s46 05s44 05s45 05s46 IPO42 IPO43; do
    d=$ROUND/runs/G4F6P1--DPO01--${arm}/checkpoint-${ep##*:}
    [ -d "$d" ] && MODELS+=("arm${arm}_ep${ep%%:*}|$d")
  done
done
# the length-balanced arms land on 35/70/105 steps (274 pairs), and arm 07 runs to 5 epochs
for arm in BAL BALs43 BALs44; do
  for ep in 3:105 2:70 1:35; do
    d=$ROUND/runs/G4F6P1--DPO01--${arm}/checkpoint-${ep##*:}
    [ -d "$d" ] && MODELS+=("arm${arm}_ep${ep%%:*}|$d")
  done
done
for ep in 5:215 4:172; do
  d=$ROUND/runs/G4F6P1--DPO01--07/checkpoint-${ep##*:}
  [ -d "$d" ] && MODELS+=("arm07_ep${ep%%:*}|$d")
done
echo "HB $(date -u +%FT%TZ) greekmmlu-250 start: ${#MODELS[@]} models"

run_one() {
  local label=${1%%|*} path=${1##*|} gpu=$2
  local dir="$OUT/$label"
  if ls "$dir"/*_native_mcq_headline.json >/dev/null 2>&1; then echo "HB skip $label (scored)"; return 0; fi
  mkdir -p "$dir"
  local t0=$(date +%s)
  # The native MCQ runner calls AutoTokenizer.from_pretrained(model_path) with no override, and the
  # checkpoints carry tokenizer_class TokenizersBackend (written by transformers 5.16.1) which the
  # container's 4.57 cannot load. So stage a directory that symlinks the checkpoint's weights and
  # takes the PARENT's tokenizer files. tokenizer.json is byte-identical between them, so this
  # changes no tokenisation - it only restores a class name the loader recognises.
  local stage="$OUT/.stage_${SLURM_JOB_ID:-$$}_$label"   # R-DPO7b [HIGH]: unique per job
  if [ "$path" != "$PARENT" ]; then
    rm -rf "$stage"; mkdir -p "$stage"
    for f in "$path"/*; do ln -sf "$f" "$stage/$(basename "$f")" 2>/dev/null; done
    # R-DPO7b [HIGH]: "this changes no tokenisation" was a comment, not a check. If the checkpoint's
    # tokenizer.json is NOT byte-identical to the parent's, copying the parent's over it silently
    # changes token ids and every score in the run. Prove it instead of asserting it.
    # R-DPO7b2 [HIGH]: "check only if both exist" is fail-OPEN -- no checkpoint carries
    # special_tokens_map.json, so that comparison never ran. Require the file, then compare.
    [ -f "$PARENT/tokenizer.json" ] || { echo "HB FATAL parent tokenizer.json missing"; return 1; }
    [ -f "$path/tokenizer.json" ] || { echo "HB FATAL $label: checkpoint has no tokenizer.json"; return 1; }
    if true; then
      if ! cmp -s "$path/tokenizer.json" "$PARENT/tokenizer.json"; then
        echo "HB FATAL $label: tokenizer.json differs from the parent - refusing to stage"
        echo "   ckpt   $(sha256sum "$path/tokenizer.json" | cut -c1-16)"
        echo "   parent $(sha256sum "$PARENT/tokenizer.json" | cut -c1-16)"
        return 1
      fi
    fi
    # special_tokens_map must match too; only tokenizer_config carries the unloadable class name
    # special_tokens_map.json is absent from every checkpoint in this round; absence is fine, a
    # DIFFERENCE is not. tokenizer_config.json legitimately differs (that is the unloadable class
    # name we are repairing), so compare it with tokenizer_class normalised away and fail on any
    # other difference rather than copying it wholesale.
    if [ -f "$path/special_tokens_map.json" ] && [ -f "$PARENT/special_tokens_map.json" ]; then
      cmp -s "$path/special_tokens_map.json" "$PARENT/special_tokens_map.json" || {
        echo "HB FATAL $label: special_tokens_map.json differs from the parent"; return 1; }
    fi
    if [ -f "$path/tokenizer_config.json" ] && [ -f "$PARENT/tokenizer_config.json" ]; then
      python3 - "$path/tokenizer_config.json" "$PARENT/tokenizer_config.json" <<'TC' || return 1
import json, sys
DROP = {"tokenizer_class", "auto_map", "transformers_version"}
a = {k: v for k, v in json.load(open(sys.argv[1])).items() if k not in DROP}
b = {k: v for k, v in json.load(open(sys.argv[2])).items() if k not in DROP}
diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
if diff:
    print("  tokenizer_config differs beyond the class name: %s" % ", ".join(diff))
    sys.exit(1)
TC
    fi
    for t in tokenizer.json tokenizer_config.json special_tokens_map.json; do
      rm -f "$stage/$t"; [ -f "$PARENT/$t" ] && cp "$PARENT/$t" "$stage/$t"
    done
    for t in tokenizer.json tokenizer_config.json; do
      [ -L "$stage/$t" ] && { echo "HB FATAL $label: $t still a symlink after staging"; return 1; }
    done
    path="$stage"
  fi
  echo "HB $(date -u +%FT%TZ) start $label gpu=$gpu"
  CUDA_VISIBLE_DEVICES=$gpu uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
    set -euo pipefail
    export PYTHONPATH=$WHEEL:$PYENV
    export LD_LIBRARY_PATH=$PYENV/scipy.libs:$PYENV/numpy.libs:$PYENV/scikit_learn.libs:\${LD_LIBRARY_PATH:-}
    export HF_TOKEN=\$(cat /users/fffoivos/.cache/huggingface/token 2>/dev/null) HF_HUB_OFFLINE=1
    export HF_HOME=$ROUND/hf_home
    python3 '$NATIVE_ROOT/run_native_greek_mcq_eval.py' --registry '$NATIVE_ROOT/native_greek_benchmark_registry.json' \
      --benchmarks greekmmlu --model '$label=$path' --output-dir '$dir' --sample-size 250 \
      --random-state 42 --dtype float32 --max-input-tokens 3072 \
      --candidate-batch-size 16 --example-batch-size 16 --trust-remote-code
    python3 '$FINALIZER' --model '$path' --evaluation-root '$dir' --model-label '$label' \
      --clean-subset-manifest '$CLEAN_SUBSET' --output '$dir/receipt.json'
  " > "$dir/run.log" 2>&1
  local rc=$? el=$(( $(date +%s) - t0 ))
  # R-DPO7b2 [HIGH]: a headline on disk is not success. The legacy finalizer fails on Apertus, so
  # rc!=0 is EXPECTED here -- but the runner's own failure must still be caught, and the job's exit
  # status is not a completion receipt either way: finalize_greekmmlu_full.py is.
  if ls "$dir"/*_native_mcq_headline.json >/dev/null 2>&1; then
    if [ $rc -ne 0 ]; then
      echo "HB $(date -u +%FT%TZ) done-with-nonzero $label rc=$rc in ${el}s (legacy finalizer; headline present)"
    else
      echo "HB $(date -u +%FT%TZ) done $label in ${el}s"
    fi
    return 0
  else
    echo "HB $(date -u +%FT%TZ) FAILED $label rc=$rc in ${el}s"; tail -12 "$dir/run.log"; return 1
  fi
}

i=0
while [ $i -lt ${#MODELS[@]} ]; do
  pids=()
  for g in 0 1 2 3; do
    idx=$(( i + g )); [ $idx -ge ${#MODELS[@]} ] && break
    run_one "${MODELS[$idx]}" "$g" & pids+=($!)
  done
  # R-DPO7b [HIGH]: collect EVERY status so all four workers finish, then remember the failures.
  for p in "${pids[@]}"; do wait "$p" || FAILED=$(( FAILED + 1 )); done
  i=$(( i + 4 ))
  echo "HB $(date -u +%FT%TZ) wave complete, $i/${#MODELS[@]} dispatched"
done
rm -rf "$OUT"/.stage_* 2>/dev/null
if [ "${FAILED:-0}" -gt 0 ]; then
  echo "HB $(date -u +%FT%TZ) GREEKMMLU_INCOMPLETE: $FAILED model(s) failed"; exit 1
fi
echo "HB $(date -u +%FT%TZ) GREEKMMLU_DONE"
