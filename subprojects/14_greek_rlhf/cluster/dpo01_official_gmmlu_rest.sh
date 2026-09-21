#!/usr/bin/env bash
# Poison ledger R3: OFFICIAL-protocol GreekMMLU for the DPO01 runs not yet scored under it.
# Stages each arm with the parent's tokenizer files (tokenizer.json verified byte-identical first;
# the checkpoints' tokenizer_config names a class the container cannot load), then hands four models
# at a time to cluster/greekmmlu_official.sh, which owns the workbench, the clean-GPU check and the
# copy-back. The official runner applies NO chat template, so these prompts carry no date.
set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/14_greek_rlhf
R=/iopsstor/scratch/cscs/fffoivos/sft_round1; P=$R/eval_copies/R4_full_ep1
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 clariden "$@" 2>/dev/null; }
SPECS=(arm01s43_ep3:01s43:129 arm01s44_ep3:01s44:129 arm01s45_ep3:01s45:129 arm01s46_ep3:01s46:129
       arm05s43_ep3:05s43:129 arm05s44_ep3:05s44:129 arm05s45_ep3:05s45:129 arm05s46_ep3:05s46:129
       armBAL_ep3:BAL:105 armBALs43_ep3:BALs43:105 armBALs44_ep3:BALs44:105 armIPO43_ep3:IPO43:129)
ARGS=()
for s in "${SPECS[@]}"; do IFS=: read -r L A STEP <<< "$s"
  # an existing file is a hint, never proof: it is re-validated against the staged config before it is skipped
  if [ -s ../12_greek_sft_experiments/results/greekmmlu_official/$L.json ] && [ -s ../12_greek_sft_experiments/results/greekmmlu_official/$L.json.receipt.json ]; then cs=$(sshc "sha256sum $R/eval_copies/official_stage_$L/config.json 2>/dev/null" | cut -d" " -f1)
    python3 ../12_greek_sft_experiments/cluster/eval_jobs/validate_official_result.py ../12_greek_sft_experiments/results/greekmmlu_official/$L.json $L $R/eval_copies/official_stage_$L "${cs:-none}" >/dev/null \
      && python3 -c "import sys;sys.path.insert(0,'.');from rlhf.evals import from_official_greekmmlu as f;f('../12_greek_sft_experiments/results/greekmmlu_official/$L.json')" >/dev/null 2>&1 \
      && { echo "have $L (re-validated incl. evaluator receipt)"; continue; } || echo "existing $L did not re-validate: re-scoring"; fi
  out=$(sshc "SRC=$R/runs/G4F6P1--DPO01--$A/checkpoint-$STEP; ST=$R/eval_copies/official_stage_$L
    [ -f \$SRC/config.json ] || { echo NOSRC; exit 0; }
    cmp -s \$SRC/tokenizer.json $P/tokenizer.json || { echo TOKDIFF; exit 0; }
    rm -rf \$ST; mkdir -p \$ST
    for f in \$SRC/*; do b=\$(basename \$f); case \$b in tokenizer*|special_tokens_map.json|chat_template.jinja) ;; *) ln -s \$f \$ST/\$b;; esac; done
    for t in tokenizer.json tokenizer_config.json special_tokens_map.json chat_template.jinja; do [ -f $P/\$t ] && cp $P/\$t \$ST/\$t; done
    n=0; for w in \$ST/*.safetensors; do [ -L \$w ] || { echo NOTLINK; exit 0; }; case \$(readlink -f \$w) in \$(readlink -f \$SRC)/*) n=\$((n+1));; *) echo WRONGTARGET; exit 0;; esac; done
    [ \$n -ge 1 ] && [ ! -L \$ST/tokenizer.json ] && cmp -s \$ST/tokenizer.json $P/tokenizer.json && echo OK || echo BADSTAGE")
  [ "$out" = OK ] || { echo "FATAL staging $L: $out"; exit 1; }
  ARGS+=("$L=$R/eval_copies/official_stage_$L")
done
echo "to score: ${#ARGS[@]}"; FAIL=0
for ((i=0; i<${#ARGS[@]}; i+=4)); do
  WALL=02:00:00 MAXWAIT=100 PROTOCOLS=official_label bash ../12_greek_sft_experiments/cluster/greekmmlu_official.sh "${ARGS[@]:i:4}" || { FAIL=1; echo "wave failed - stopping before another workbench is opened"; break; }
  for spec in "${ARGS[@]:i:4}"; do L=${spec%%=*}; [ -s ../12_greek_sft_experiments/results/greekmmlu_official/$L.json ] || { echo "MISSING $L"; FAIL=1; }; done
done
[ $FAIL -eq 0 ] && echo OFFICIAL_REST_DONE || { echo OFFICIAL_REST_INCOMPLETE; exit 1; }
