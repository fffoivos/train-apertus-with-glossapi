#!/bin/zsh
# Correcting set at scale: three shards by seed (disjoint ids corr_<seed>_<k>), 24 workers each, Sol high. Usage: ./run_correcting_scale.sh [n_per_shard]
N=${1:-500}
cd "$(dirname "$0")"
for SEED in 2 3 4; do
  nohup ~/venvs/sftdata/bin/python build_correcting.py correcting/scale/s$SEED --n $N --seed $SEED --concurrency 24 --role-plant-share 0.2 > correcting/scale_s$SEED.log 2>&1 &
  echo "shard seed $SEED pid $! -> correcting/scale/s$SEED"
done
