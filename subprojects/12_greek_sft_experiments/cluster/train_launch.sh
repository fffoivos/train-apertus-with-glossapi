#!/bin/bash
# Launch one trainer run inside a workbench: train_launch.sh <jobid> <config.yaml> <run_label> [extra args...]
# Runs on the login node; the training happens on the allocated node via srun --overlap.
set -u
J=$1; CFG=$2; LABEL=$3; shift 3; EXTRA="$*"
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=$R/runs/$LABEL; CTL=$R/runs/$LABEL.ctl; mkdir -p $CTL $R/logs; rm -rf $OUT   # the trainer refuses a non-empty out-dir
cat > $CTL/run.sh <<EOS
#!/bin/bash
set -euo pipefail
export SCRATCH=$S HF_HOME=$R/hf_home HF_HUB_CACHE=$R/hf_home/hub HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
export HF_TOKEN=\$(cat $R/hf_home/token)
source $S/venvs/sft5/bin/activate
cd $R
echo "RUN \$(date -u +%FT%TZ) cfg=$CFG label=$LABEL extra=$EXTRA node=\$(hostname)"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader
accelerate launch --config_file cluster/configs/zero3.yaml cluster/sft_train.py --config $CFG --out-dir $OUT $EXTRA
echo "RUN_EXIT \$? \$(date -u +%FT%TZ)"
EOS
chmod +x $CTL/run.sh
nohup setsid bash -c "srun --jobid=$J --overlap --ntasks=1 --nodes=1 --gpus-per-node=4 --cpus-per-task=288 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash $CTL/run.sh" > $CTL/train.log 2>&1 &
echo "launched $LABEL pid $! log=$CTL/train.log"
