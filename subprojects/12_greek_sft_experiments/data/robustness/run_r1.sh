#!/usr/bin/env bash
# R1: arm B only (owner, 9 September: "just run on our model so we can observe failure modes"). Serve arm B with vLLM on an open workbench,
# one IPv4 tunnel, the mixed-profile simulator at 16 workers, then the repetition-penalty arm, then close + ledger. Run on the Mac under nohup.
# Usage: bash run_r1.sh <jobid> [n_mixed=120] [n_penalty=60] [rep_penalty=1.1]
set -u; cd "$(dirname "$0")/../.."; J=$1; N=${2:-120}; NP=${3:-60}; RP=${4:-1.1}
R=/iopsstor/scratch/cscs/fffoivos/sft_round1; OUT=results/robustness_r1_$(date +%Y%m%d); mkdir -p "$OUT"; LOG=$OUT/run.log
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
sshc(){ ssh -4 -o BatchMode=yes -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
sshc "cd $R; nohup setsid bash -c \"srun --jobid=$J --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=288 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash $R/serve_models.sh armB=$R/eval_copies/R2_idB_ep2\" > $R/logs/serve_r1.out 2>&1 &"
NODE=$(sshc "squeue -h -j $J -o %N"); say "job $J on $NODE; serving arm B"
ssh -4 -N -o BatchMode=yes -o ServerAliveInterval=30 -L 8000:$NODE:8000 clariden & TUN=$!
for i in $(seq 1 40); do curl -s -m 10 http://127.0.0.1:8000/v1/models | grep -q '"id"' && break; sleep 15; done
curl -s -m 10 http://127.0.0.1:8000/v1/models | grep -q '"id"' || { say "arm B did not come up"; sshc "tail -3 $R/serve_armB.log"; kill $TUN; exit 1; }
say "endpoint ready after $((i*15)) s; mixed profile, $N dialogues, 16 workers"
WORKERS=16 python3 data/robustness/simulate.py "$OUT" --target armB=http://127.0.0.1:8000/v1/armB --n "$N" --profile mixed > "$OUT/sim_mixed.log" 2>&1; say "mixed done"
WORKERS=16 python3 data/robustness/simulate.py "$OUT/rp$RP" --target armB=http://127.0.0.1:8000/v1/armB --n "$NP" --profile mixed --rep-penalty "$RP" > "$OUT/sim_rp.log" 2>&1; say "penalty $RP done"
kill $TUN 2>/dev/null; sshc "bash $R/workbench.sh close $J" | tee -a "$LOG"; sleep 20; bash cluster/ledger.sh "$J" R1 "picky-user R1: arm B, mixed profiles ($N) + repetition penalty $RP ($NP)" | tee -a "$LOG"
for f in "$OUT"/armB_summary.json "$OUT"/rp$RP/armB_summary.json; do [ -s "$f" ] && { echo "== $f"; python3 -c "import json; d=json.load(open('$f')); print({k:v for k,v in d.items() if k not in ('tone','by_profile')}); print('tone', d.get('tone'), 'tail by profile', d.get('by_profile'))"; }; done | tee -a "$LOG"
say "R1 DONE"
