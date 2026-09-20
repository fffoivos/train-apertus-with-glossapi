#!/bin/bash
#SBATCH --account=a0140
#SBATCH --job-name=dpo01_frozen
#SBATCH --nodes=1 --ntasks-per-node=1 --gpus-per-node=4 --cpus-per-task=288 --mem=640G
#SBATCH --time=10:00:00
#SBATCH --output=/iopsstor/scratch/cscs/fffoivos/sft_round1/logs/dpo01_frozen_%j.out
# Frozen-date re-score (poison ledger R1 + R2, docs/RLHF_COORDINATION/DPO01_POISON_LEDGER_20260919.md).
#
# The Apertus chat template renders  Current date: strftime_now('%Y-%m-%d')  into every prompt, so
# runs scored on different days were never the same measurement. This job scores through a staged
# tokenizer whose template carries the LITERAL date below. It is 2026-09-19 on purpose: prompts are
# then byte-identical to the runs already scored on the 19th, which rlhf.evals.compare() verifies by
# prompt digest, so those runs are reused instead of re-bought.
#
# E6 (R-DPO9): checkpoints written by transformers 5.16 keep RoPE under `rope_parameters`; this
# environment (4.57) ignores that key and would load them with rope_theta 12e6 and no llama3 scaling.
# EVERY model is therefore scored from a job-unique stage whose config.json carries the legacy
# `rope_theta`/`rope_scaling` keys, and a CPU geometry gate proves - before any GPU time - that the
# rotary frequency table this environment builds equals the parent's. No earlier arm run is reused.
#
# Model list ($LIST): one per line,  label|weights_dir|config|tasks
#   config: own     the model's own generation config, geometry repaired
#           parent  the model's WEIGHTS under the PARENT's generation config, geometry repaired
#           verbatim:<dir>  the model's weights under <dir>/config.json + generation_config.json, copied as they
#                   are; the gate requires the PARENT's geometry (used for parent weights under a staged config)
#           export:<dir>  the same, but the gate requires the geometry to DIFFER from the parent's:
#                   with the parent's weights this reproduces the arms' mis-loading on purpose and
#                   measures the artefact directly; the gate then requires the table to DIFFER.
#   tasks:  full | gen     (gen = ifeval_greek,mgsm_greek; the MMLU lane is likelihood-scored and
#                           does not depend on the generation config, so it is not repeated per config)
# RECOVER=1 ... bash <this script>  re-stages each model, re-checks its geometry, and writes the receipt +
#   manifests for runs whose SCORING finished but whose lm_eval exited non-zero in its cosmetic results-table
#   printer (make_table -> pytablewriter -> chardet), long after every output was written. It scores nothing.
#   Accepted only when that exact traceback is the failure AND every lane validates; anything else is refused.
#
# DRYRUN=1 bash <this script>  runs everything that needs no GPU - freeze, canary, list preflight, staging and the
# geometry gate for every model - and scores nothing. Use it before every launch.
# Fail-closed: exact model count, rc==0, validated sample counts and date, non-zero exit on any failure.
set -uo pipefail
FROZEN_DATE=2026-09-19
S=/iopsstor/scratch/cscs/fffoivos; ROUND=$S/sft_round1
PYENV=$S/python_envs/lm_eval
WHEEL=$S/evals/full8_native_greek_peak_window_20260817/vendor_probe/accelerate-1.14.0-py3-none-any.whl
PARENT=$ROUND/eval_copies/R4_full_ep1
OUT=$ROUND/results/G4F6P1--DPO01/frozen
COSMETIC="module .chardet. has no attribute .detect."   # lm_eval prints its summary table AFTER writing everything
[ "${DRYRUN:-0}" = 1 ] && OUT=$ROUND/results/G4F6P1--DPO01/.frozen_dryrun_$$
LIST=${LIST:?need LIST=<model list file>}
JOB=${SLURM_JOB_ID:-$$}
TOK=$ROUND/eval_copies/tok_frozen_${FROZEN_DATE}
FULL=ifeval_greek,mgsm_greek,global_mmlu_en,global_mmlu_de,global_mmlu_es,global_mmlu_fr,global_mmlu_it,global_mmlu_pt
# GEN_KWARGS raises the generation cap for the truncation experiment. IFEval allows 1280 tokens with NO
# stop strings, so a model that will not terminate is cut off; the parent hits that wall on 81 of 541
# items and the arms on ~26. Scoring at a larger cap says how much of the arms' advantage is the wall
# and how much is the model. Runs at a different cap are a DIFFERENT measurement: rlhf.evals records
# gen_kwargs in the manifest and will refuse to compare them with the 1280 runs, which is correct.
GK=${GEN_KWARGS:-}
GEN=ifeval_greek,mgsm_greek
mkdir -p "$OUT"
[ -f "$LIST" ] || { echo "HB FATAL no list at $LIST"; exit 1; }
[ -f "$ROUND/rlhf/evals/manifest.py" ] || { echo "HB FATAL rlhf package not deployed at $ROUND/rlhf"; exit 1; }
RR=$ROUND/cluster/eval_jobs/run_receipt.py; [ -f "$RR" ] || { echo "HB FATAL run_receipt.py not deployed"; exit 1; }
ENVSET="export PYTHONPATH=$WHEEL:$PYENV; export LD_LIBRARY_PATH=$PYENV/scipy.libs:$PYENV/numpy.libs:$PYENV/scikit_learn.libs:\${LD_LIBRARY_PATH:-}; export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false"

# ---- 1. the frozen tokenizer, built once and verified every time
python3 - "$PARENT" "$TOK" "$FROZEN_DATE" <<'PY' || { echo "HB FATAL frozen tokenizer could not be built/verified"; exit 1; }
import json, os, shutil, sys, filecmp
parent, tok, date = sys.argv[1:4]
NEEDLE = "strftime_now('%Y-%m-%d')"
os.makedirs(tok, exist_ok=True)
for f in ("tokenizer.json", "special_tokens_map.json"):
    if os.path.exists(os.path.join(parent, f)) and not os.path.exists(os.path.join(tok, f)):
        shutil.copy(os.path.join(parent, f), os.path.join(tok, f))
assert filecmp.cmp(os.path.join(parent, "tokenizer.json"), os.path.join(tok, "tokenizer.json"), shallow=False), "tokenizer.json differs"
n = 0
for f in ("tokenizer_config.json", "chat_template.jinja"):
    src = os.path.join(parent, f)
    if not os.path.exists(src): continue
    text = open(src, encoding="utf-8").read()
    # inside tokenizer_config.json the template is a JSON string, so the quotes are plain there too
    k = text.count(NEEDLE); n += k
    text = text.replace(NEEDLE, "'%s'" % date)
    assert "strftime_now" not in text, "%s still calls strftime_now" % f
    with open(os.path.join(tok, f), "w", encoding="utf-8") as fh: fh.write(text)
assert n >= 1, "the date call was not found in the parent's template - nothing was frozen"
cfg = json.load(open(os.path.join(tok, "tokenizer_config.json")))
assert ("Current date: ' + '%s'" % date) in cfg.get("chat_template", "") or os.path.exists(os.path.join(tok, "chat_template.jinja")), "literal date not in the template"
print("HB frozen tokenizer ok: %d replacement(s), date %s, %s" % (n, date, tok))
PY

# ---- 1b. canary: the frozen template must render EXACTLY what the real one renders, date aside.
# If the literal substitution changed anything else (quoting, whitespace), every model below would be
# scored on a subtly different prompt and the reuse of the existing 19-Sept runs would be invalid.
uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
  $ENVSET
  python3 - '$PARENT' '$TOK' '$FROZEN_DATE' <<'PY'
import re, sys
from transformers import AutoTokenizer
parent, tok, date = sys.argv[1:4]
msgs = [[{'role': 'user', 'content': 'Γράψε μια περίληψη σε 3 προτάσεις.'}],
        [{'role': 'user', 'content': 'a'}, {'role': 'assistant', 'content': 'b'}, {'role': 'user', 'content': 'c'}]]
A, B = AutoTokenizer.from_pretrained(parent), AutoTokenizer.from_pretrained(tok)
norm = lambda s: re.sub(r'(Current date: )\\d{4}-\\d{2}-\\d{2}', r'\\1D', s)
for m in msgs:
    for gen in (True, False):
        a = A.apply_chat_template(m, tokenize=False, add_generation_prompt=gen)
        b = B.apply_chat_template(m, tokenize=False, add_generation_prompt=gen)
        assert ('Current date: ' + date) in b, 'frozen template does not render the frozen date'
        assert norm(a) == norm(b), 'frozen template renders differently from the real one beyond the date'
        assert A(a)['input_ids'] == B(a)['input_ids'], 'tokenisation differs'
print('HB canary ok: frozen template == real template, date aside; tokenisation identical')
PY
" || { echo "HB FATAL canary failed - the frozen tokenizer is not a faithful freeze"; exit 1; }

# ---- 2. the model list, exact
MODELS=(); while IFS= read -r line; do [ -n "$line" ] && [ "${line:0:1}" != "#" ] && MODELS+=("$line"); done < "$LIST"
EXPECT=${EXPECT:?need EXPECT=<number of models in the list>}
[ ${#MODELS[@]} -eq "$EXPECT" ] || { echo "HB FATAL list has ${#MODELS[@]} models, EXPECT=$EXPECT"; exit 1; }
for m in "${MODELS[@]}"; do IFS='|' read -r l w c t <<< "$m"
  [ -f "$w/config.json" ] || { echo "HB FATAL $l: no config.json under $w"; exit 1; }
  # every model is scored through ONE tokenizer ($TOK). That is only legitimate if the model's own
  # tokenizer.json is byte-identical to the parent's. Absent or different = refuse, never skip.
  [ -f "$w/tokenizer.json" ] || { echo "HB FATAL $l: no tokenizer.json under $w"; exit 1; }
  cmp -s "$w/tokenizer.json" "$PARENT/tokenizer.json" || { echo "HB FATAL $l: tokenizer.json differs from the parent's"; exit 1; }
  case "$c" in own|parent) ;; export:*|verbatim:*) [ -f "${c#*:}/config.json" ] || { echo "HB FATAL $l: no config at ${c#*:}"; exit 1; };; *) echo "HB FATAL $l: config '$c'"; exit 1;; esac
  case "$t" in full|gen) ;; *) echo "HB FATAL $l: tasks '$t'"; exit 1;; esac
done
# content receipts for every distinct weights dir (rlhf.evals identity; ~20 s per 16 GB, 8 at a time)
mkdir -p "$ROUND/receipts/weights"
if [ "${DRYRUN:-0}" = 1 ]; then echo "HB DRYRUN: skipping weights receipts (hashing) and all scoring"; else
printf '%s\n' "${MODELS[@]}" | cut -d'|' -f2 | sort -u | xargs -P 8 -n 1 python3 "$ROUND/cluster/eval_jobs/weights_receipt.py" "$ROUND/receipts/weights" \
  || { echo "HB FATAL weights receipts failed"; exit 1; }
fi
PARENT_GEO=$(uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "$ENVSET; python3 $RR geometry $PARENT" 2>/dev/null | tail -1 | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['inv_freq_sha256'])")
[ ${#PARENT_GEO} -eq 64 ] || { echo "HB FATAL could not resolve the parent's geometry"; exit 1; }
echo "HB parent geometry (inv_freq sha256) ${PARENT_GEO:0:12}"
echo "HB $(date -u +%FT%TZ) frozen re-score start: ${#MODELS[@]} models, date $FROZEN_DATE"

stage_model() {   # $1 label  $2 weights dir  $3 mode -> echoes the staged dir. Weights are symlinks; every file we write is regular.
  local st="$ROUND/eval_copies/.frozen_${JOB}_$1_${3%%:*}"
  rm -rf "$st"; mkdir -p "$st" || return 1
  local f b; for f in "$2"/*; do b=$(basename "$f")
    case "$b" in config.json|generation_config.json|tokenizer*|special_tokens_map.json|chat_template.jinja) ;;   # never linked
      *) ln -s "$f" "$st/$b" || return 1;; esac
  done
  python3 - "$2" "$PARENT" "$st" "$3" <<'PY' || return 1
import json, os, shutil, sys
src, par, st, mode = sys.argv[1:5]
def put(name, obj):
    tgt = os.path.join(st, name); assert not os.path.lexists(tgt), name + " already present in a fresh stage"
    with open(tgt, "w") as fh: json.dump(obj, fh, indent=1)
if mode.startswith(("export:", "verbatim:")):       # config copied as it is, never repaired; the gate decides what it must resolve to
    exp = mode.split(":", 1)[1]
    put("config.json", json.load(open(os.path.join(exp, "config.json"))))
    g = os.path.join(exp, "generation_config.json")
    if os.path.exists(g): put("generation_config.json", json.load(open(g)))
    sys.exit(0)
c = json.load(open(os.path.join(src, "config.json")))
rp = c.get("rope_parameters")
if isinstance(rp, dict) and "rope_theta" not in c:  # E6 repair: give 4.57 the keys it actually reads
    c["rope_theta"] = rp["rope_theta"]
    sc = {k: v for k, v in rp.items() if k != "rope_theta"}
    if sc.get("rope_type", "default") != "default": c["rope_scaling"] = sc
gsrc = src
if mode == "parent":
    p = json.load(open(os.path.join(par, "config.json")))
    for f in ("eos_token_id", "pad_token_id", "bos_token_id", "use_cache"):   # symmetric: assign or delete
        if f in p: c[f] = p[f]
        elif f in c: del c[f]
    gsrc = par
put("config.json", c)
g = os.path.join(gsrc, "generation_config.json")
if os.path.exists(g): put("generation_config.json", json.load(open(g)))
PY
  echo "$st"
}

validate_run() {   # $1 dir $2 tasks $3 label : parse every sample, bind to the receipt, seal a manifest per lane
  uenv run --view=default pytorch/v2.9.1:v2 -- python3 - "$1" "$2" "$FROZEN_DATE" "$3" "$ROUND" <<'PY'
import glob, json, os, sys
d, tasks, date, label, root = sys.argv[1:6]
sys.path.insert(0, root)
from rlhf.evals import from_lm_eval
lanes = [("ifeval_greek", "prompt_level_strict_acc", 541), ("mgsm_greek", "exact_match", 250)]
if tasks == "full":
    leaves = sorted(os.path.basename(f).split("samples_")[1].rsplit("_", 1)[0]
                    for f in glob.glob(os.path.join(d, "**", "samples_global_mmlu_*.jsonl"), recursive=True))
    assert len(leaves) == 36, "expected 36 Global-MMLU leaf lanes, found %d" % len(leaves)
    lanes += [(t, "acc", None) for t in leaves]
os.makedirs(os.path.join(d, "manifests"), exist_ok=True); total = 0
for task, metric, n in lanes:
    r = from_lm_eval(d, task, metric); m = r.manifest       # identity comes from run_receipt.json, verified against the output hashes
    assert m["label"] == label, "receipt label %r != %r" % (m["label"], label)
    assert n is None or m["n_items"] == n, "%s: %d items, expected %d" % (task, m["n_items"], n)
    assert m["prompt_dates"] == [date], "%s: prompt dates %r, expected only %s" % (task, m["prompt_dates"], date)
    if n is None: total += m["n_items"]
    with open(os.path.join(d, "manifests", task + ".json"), "w") as fh:
        json.dump({"manifest": m, "seal": r.seal, "accuracy": sum(r.items.values()) / float(len(r.items))}, fh, indent=1, sort_keys=True)
assert tasks != "full" or total == 2400, "Global-MMLU-Lite is %d items, expected 2,400" % total
print("HB manifested %s: %d lanes" % (label, len(lanes)))
PY
}

run_one() {
  local label w cfg tasks gpu=$2; IFS='|' read -r label w cfg tasks <<< "$1"
  local dir="$OUT/${label}__${cfg%%:*}cfg" tl=$GEN; [ "$tasks" = full ] && tl=$FULL
  # a marker is a hint, never proof (R-DPO9): an existing run is re-validated from its files before it is skipped
  if [ -f "$dir/run_receipt.json" ] && validate_run "$dir" "$tasks" "$label" > "$dir/revalidate.log" 2>&1 \
     && python3 - "$dir/run_receipt.json" "$ROUND/receipts/weights" "$w" "$cfg" "$FROZEN_DATE" "$PARENT_GEO" <<'PY' >> "$dir/revalidate.log" 2>&1
import hashlib, json, os, sys
rp, wdir, w, cfg, date, pgeo = sys.argv[1:7]; r = json.load(open(rp))
want = json.load(open(os.path.join(wdir, hashlib.sha256(os.path.abspath(w).encode()).hexdigest()[:16] + ".json")))["weights_id"]
assert r["weights_id"] == want, "receipt is for other weights"
assert r.get("config_spec", r.get("config_mode")) == cfg, "receipt is for another config spec (%r != %r)" % (r.get("config_spec"), cfg)
assert r["frozen_date"] == date, "receipt is for another date"
geo = r["geometry"]["inv_freq_sha256"]
assert (geo != pgeo) if cfg.startswith("export:") else (geo == pgeo), "receipt geometry does not match what this entry requires"
PY
  then echo "HB skip $label/$cfg (re-validated against this list entry)"; return 0; fi
  if [ "${RECOVER:-0}" != 1 ]; then rm -rf "$dir"; fi
  mkdir -p "$dir"
  local path; path=$(stage_model "$label" "$w" "$cfg") || { echo "HB FAILED $label/$cfg: staging"; return 1; }
  # ---- geometry gate (CPU): what THIS environment resolves, not what the JSON says
  local geo; geo=$(uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "$ENVSET; python3 $RR geometry $path" 2>/dev/null | tail -1)
  local dig; dig=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['inv_freq_sha256'])" "$geo" 2>/dev/null)
  [ -n "$dig" ] || { echo "HB FAILED $label/$cfg: geometry could not be resolved"; rm -rf "$path"; return 1; }
  case "$cfg" in
    export:*) [ "$dig" != "$PARENT_GEO" ] || { echo "HB FAILED $label/$cfg: export control did NOT reproduce the mis-load (geometry equals the parent's)"; rm -rf "$path"; return 1; };;
    *)        [ "$dig" = "$PARENT_GEO" ]  || { echo "HB FAILED $label/$cfg: geometry ${dig:0:12} != parent ${PARENT_GEO:0:12} - refusing to score a mis-loaded model"; rm -rf "$path"; return 1; };;
  esac
  if [ "${RECOVER:-0}" = 1 ]; then
    if [ ! -f "$dir/run.log" ]; then echo "HB RECOVER skip $label/$cfg (never ran)"; rm -rf "$path"; return 0; fi
    if ! { grep -qE "$COSMETIC" "$dir/run.log" && grep -q "make_table" "$dir/run.log"; }; then
      echo "HB RECOVER refuse $label/$cfg: its failure is not the known cosmetic one"; rm -rf "$path"; return 1; fi
    local key2; key2=$(python3 -c "import hashlib,os,sys; print(hashlib.sha256(os.path.abspath(sys.argv[1]).encode()).hexdigest()[:16])" "$w")
    uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "$ENVSET; python3 $RR write $dir $label $ROUND/receipts/weights/$key2.json $path $TOK $FROZEN_DATE \"$cfg\"" >> "$dir/run.log" 2>&1
    local rrc=$?; rm -rf "$path"
    [ $rrc -eq 0 ] || { echo "HB RECOVER FAILED $label/$cfg: run receipt"; return 1; }
    validate_run "$dir" "$tasks" "$label" >> "$dir/run.log" 2>&1 || { echo "HB RECOVER FAILED $label/$cfg: outputs did not manifest"; tail -3 "$dir/run.log"; return 1; }
    echo "HB RECOVER ok $label/$cfg"; return 0
  fi
  if [ "${DRYRUN:-0}" = 1 ]; then echo "HB DRY ok $label cfg=${cfg%%:*} tasks=$tasks geometry=${dig:0:12} $([ "$dig" = "$PARENT_GEO" ] && echo '= parent' || echo 'DIFFERS from parent (intended: export control)')"; rm -rf "$path"; return 0; fi
  local t0=$(date +%s); echo "HB $(date -u +%FT%TZ) start $label cfg=$cfg tasks=$tasks gpu=$gpu geometry=${dig:0:12}"
  CUDA_VISIBLE_DEVICES=$gpu uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "
    set -euo pipefail
    $ENVSET; export HF_HOME=$ROUND/hf_home HF_DATASETS_OFFLINE=1
    cd $ROUND
    python3 -m lm_eval --model hf --model_args pretrained=$path,tokenizer=$TOK,dtype=bfloat16 \
      --tasks $tl --apply_chat_template --include_path evals_code/ilsp/tasks \
      ${GK:+--gen_kwargs $GK} \
      --batch_size 16 --log_samples --output_path $dir
  " > "$dir/run.log" 2>&1
  local rc=$? el=$(( $(date +%s) - t0 ))
  if [ $rc -ne 0 ]; then
    # lm_eval writes results and samples, THEN prints a summary table. That printer crashes in this
    # container (chardet), so a non-zero status here does not by itself mean the scoring failed. Accept
    # it only for that exact traceback; the outputs still have to validate below, which is the real gate.
    if grep -qE "$COSMETIC" "$dir/run.log" && grep -q "make_table" "$dir/run.log"; then
      echo "HB $(date -u +%FT%TZ) note $label/$cfg: lm_eval rc=$rc from its cosmetic summary-table printer, after all outputs were written; validating them"
    else
      rm -rf "$path"; echo "HB $(date -u +%FT%TZ) FAILED $label/$cfg rc=$rc in ${el}s"; tail -8 "$dir/run.log"; return 1
    fi
  fi
  local key; key=$(python3 -c "import hashlib,os,sys; print(hashlib.sha256(os.path.abspath(sys.argv[1]).encode()).hexdigest()[:16])" "$w")
  uenv run --view=default pytorch/v2.9.1:v2 -- bash -c "$ENVSET; python3 $RR write $dir $label $ROUND/receipts/weights/$key.json $path $TOK $FROZEN_DATE "$cfg"" >> "$dir/run.log" 2>&1
  local wrc=$?; rm -rf "$path"
  [ $wrc -eq 0 ] || { echo "HB $(date -u +%FT%TZ) FAILED $label/$cfg: run receipt"; return 1; }
  validate_run "$dir" "$tasks" "$label" >> "$dir/run.log" 2>&1 || { echo "HB $(date -u +%FT%TZ) FAILED $label/$cfg: output could not be manifested"; tail -4 "$dir/run.log"; return 1; }
  echo "HB $(date -u +%FT%TZ) done $label/$cfg in ${el}s"
}

FAILED=0; i=0
while [ $i -lt ${#MODELS[@]} ]; do
  pids=()
  for g in 0 1 2 3; do idx=$(( i + g )); [ $idx -ge ${#MODELS[@]} ] && break
    run_one "${MODELS[$idx]}" "$g" & pids+=($!); done
  for p in "${pids[@]}"; do wait "$p" || FAILED=$(( FAILED + 1 )); done
  i=$(( i + 4 )); echo "HB $(date -u +%FT%TZ) wave complete, $i/${#MODELS[@]} dispatched, failures so far: $FAILED"
done
rm -rf "$ROUND/eval_copies/.frozen_${JOB}_"* 2>/dev/null
if [ $FAILED -gt 0 ]; then echo "HB $(date -u +%FT%TZ) FROZEN_INCOMPLETE: $FAILED failed"; exit 1; fi
[ "${RECOVER:-0}" = 1 ] && { [ $FAILED -eq 0 ] && echo "HB $(date -u +%FT%TZ) RECOVER_DONE: all ${#MODELS[@]} entries receipted and manifested" || echo "HB $(date -u +%FT%TZ) RECOVER_INCOMPLETE: $FAILED"; exit $(( FAILED > 0 )); }
[ "${DRYRUN:-0}" = 1 ] && { rm -rf "$OUT"; echo "HB $(date -u +%FT%TZ) DRYRUN_OK: all ${#MODELS[@]} models staged and passed the geometry gate"; exit 0; }
echo "HB $(date -u +%FT%TZ) FROZEN_DONE"
