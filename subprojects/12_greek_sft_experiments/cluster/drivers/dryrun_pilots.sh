#!/usr/bin/env bash
# Trainer-native dry-runs for the pilot arms (the same command pilot_chain.sh runs before any submission), logs to results/pilots/dryrun_<arm>.log. Usage: bash cluster/drivers/dryrun_pilots.sh M0 M1 M2
set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=results/pilots; mkdir -p $OUT
sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }; say(){ echo "[$(date '+%m-%d %H:%M')] dryrun: $*"; }
for A in "$@"; do   # upload (the same step pilot_chain.sh runs) + md5 check, then the trainer dry-run
  say "$A: uploading $(wc -l < data/arms/$A/train.jsonl) train rows + config"; sshc "mkdir -p $R/data/arms/$A"; scp -4 -q data/arms/$A/train.jsonl data/arms/$A/dev.jsonl clariden:$R/data/arms/$A/ && scp -4 -q cluster/configs/$A.yaml clariden:$R/cluster/configs/$A.yaml || { say "FAILED: upload $A"; exit 1; }
  [ "$(sshc "cd $R && md5sum data/arms/$A/train.jsonl | cut -c1-12")" = "$(md5 -q data/arms/$A/train.jsonl | cut -c1-12)" ] || { say "FAILED: md5 mismatch after upload $A"; exit 1; }; say "$A: md5 verified"
  sshc "cd $R && uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc 'export SCRATCH=$S HF_HOME=$R/hf_home HF_HUB_CACHE=$R/hf_home/hub HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 HF_DATASETS_OFFLINE=1 HF_TOKEN=\$(cat $R/hf_home/token); source $S/venvs/sft5/bin/activate; python cluster/sft_train.py --config cluster/configs/$A.yaml --dry-run'" > $OUT/dryrun_$A.log 2>&1
  grep -q DRY_RUN_OK $OUT/dryrun_$A.log && say "$A: DRY_RUN_OK $(grep -oE 'PLAN \{.*\}' $OUT/dryrun_$A.log | cut -c1-260)" || { say "$A: FAILED: $(tail -3 $OUT/dryrun_$A.log | tr '\n' ' ' | cut -c1-300)"; exit 1; }
done
