#!/bin/zsh
# Correcting set at scale: five shards by seed (disjoint ids corr_<seed>_<k>), 24 workers each, Sol high; resumable (existing ids are skipped).
# Throughput is concurrency / dialogue duration (≈ 30 min per dialogue chain), so more shards = faster. Usage: ./run_correcting_scale.sh [n_per_shard] [seeds...]
N=${1:-300}; shift; SEEDS=(${@:-2 3 4 5 6})
cd "$(dirname "$0")"
for SEED in $SEEDS; do
  nohup ~/venvs/sftdata/bin/python build_correcting.py correcting/scale/s$SEED --n $N --seed $SEED --concurrency 24 --role-plant-share 0.35 >> correcting/scale_s$SEED.log 2>&1 &
  echo "shard seed $SEED pid $! -> correcting/scale/s$SEED (n=$N)"
done
