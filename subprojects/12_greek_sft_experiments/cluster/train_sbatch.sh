#!/usr/bin/env bash
# The one long run per CLUSTER_PROTOCOL.md §1: same container, same config and same command as the workbench probe, submitted once.
# Usage (on the login node): bash train_sbatch.sh <config.yaml> <run_label> <walltime hh:mm:ss>
# Writes runs/<label>.ctl/{run.sh,train.log,jobid}; the trainer saves every `save_steps` optimizer steps (config) so a killed job
# resumes with resume_from_checkpoint: runs/<label>/checkpoint-<n> in the config.
set -euo pipefail
CFG=$1; LABEL=$2; TL=$3
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=$R/runs/$LABEL; CTL=$R/runs/$LABEL.ctl; mkdir -p $CTL $R/logs
[ -e "$OUT" ] && [ -z "${ALLOW_EXISTING_OUT:-}" ] && { echo "out-dir $OUT exists; set ALLOW_EXISTING_OUT=1 only for a resume"; exit 1; }
cat > $CTL/run.sh <<EOS
#!/bin/bash
set -euo pipefail
export SCRATCH=$S HF_HOME=$R/hf_home HF_HUB_CACHE=$R/hf_home/hub HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 HF_DATASETS_OFFLINE=1
export HF_TOKEN=\$(cat $R/hf_home/token)
source $S/venvs/sft5/bin/activate
cd $R
echo "RUN \$(date -u +%FT%TZ) cfg=$CFG label=$LABEL node=\$(hostname) job=\${SLURM_JOB_ID:-?}"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader
accelerate launch --config_file cluster/configs/zero3.yaml cluster/sft_train.py --config $CFG --out-dir $OUT
echo "RUN_EXIT \$? \$(date -u +%FT%TZ)"
EOS
chmod +x $CTL/run.sh
JID=$(sbatch --parsable --account=a0140 --partition=normal --nodes=1 --ntasks-per-node=1 --gpus-per-node=4 --cpus-per-task=288 --mem=640G \
  --time="$TL" --job-name="tr_$LABEL" --output="$CTL/train.log" --error="$CTL/train.log" \
  --wrap="uenv run --view=default pytorch/v2.9.1:v2 -- bash $CTL/run.sh")
echo "$JID" > $CTL/jobid
echo "$(date -u +%FT%TZ) SBATCH $LABEL job=$JID cfg=$CFG time=$TL" >> $R/logs/workbench.log
echo "$JID"
