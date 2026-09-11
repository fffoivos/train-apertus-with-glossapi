#!/bin/bash
# Login-node dry run of the R3_single arm on a 5% sample (as for R2_stage1_s5): builds the sample arm (shuf seed 42), a config without the token
# expectation, and runs sft_train.py --dry-run under nice 19 (CPU only, no allocation). Run ON THE CLUSTER: bash dryrun_R3_single_s5.sh
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; cd $R || exit 1
mkdir -p data/arms/R3_single_s5
n=$(wc -l < data/arms/R3_single/train.jsonl); k=$(( n / 20 ))
shuf --random-source=<(yes 42) -n $k data/arms/R3_single/train.jsonl > data/arms/R3_single_s5/train.jsonl
cp data/arms/R3_single/dev.jsonl data/arms/R3_single_s5/dev.jsonl
sed -e 's/^arm: R3_single$/arm: R3_single_s5/' -e 's#data/arms/R3_single/#data/arms/R3_single_s5/#' -e '/^expected_train_tokens:/d' -e '/^expected_train_rows:/d' -e 's/^run_name: .*/run_name: R3_single_s5_dryrun/' cluster/configs/R3_single.yaml > cluster/configs/R3_single_s5.yaml
echo "sample arm: $k of $n rows; config cluster/configs/R3_single_s5.yaml"
exec uenv run pytorch/v2.9.1:v2 --view=default -- bash -lc "
  source $S/venvs/sft5/bin/activate
  export HF_HOME=$R/hf_home HF_HUB_CACHE=$R/hf_home/hub HF_DATASETS_CACHE=$R/hf_home/datasets HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
  echo \"start \$(date)\"; nice -n 19 python cluster/sft_train.py --dry-run --config cluster/configs/R3_single_s5.yaml; echo \"exit=\$? \$(date)\""
