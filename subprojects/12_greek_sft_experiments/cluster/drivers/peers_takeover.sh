set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; HUB=$R/hf_home/hub; OUT=$PWD/results/peers_20260913; LOG=$OUT/run.log; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; W=3388900
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }; sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
say "TAKEOVER: dialogues for krikri/meltemi/apertus start now; qwen's generation (pid 75045) continues; its dialogues start when it ends"
WORKERS=16 python3 data/robustness/simulate.py $OUT/r_krikri --target krikri=http://127.0.0.1:8000/v1/krikri --n 60 > $OUT/sim_krikri.log 2>&1 & S1=$!
WORKERS=16 python3 data/robustness/simulate.py $OUT/r_meltemi --target meltemi=http://127.0.0.1:8001/v1/meltemi --n 60 > $OUT/sim_meltemi.log 2>&1 & S2=$!
WORKERS=16 python3 data/robustness/simulate.py $OUT/r_apertus --target apertus=http://127.0.0.1:8002/v1/apertus --n 60 > $OUT/sim_apertus.log 2>&1 & S3=$!
while kill -0 75045 2>/dev/null; do sleep 20; done; say "qwen generation done: $(tail -2 $OUT/bench_qwen.log | tr '\n' ' ' | cut -c1-160)"
WORKERS=16 python3 data/robustness/simulate.py $OUT/r_qwen --target qwen=http://127.0.0.1:8003/v1/qwen --n 60 > $OUT/sim_qwen.log 2>&1 & S4=$!
wait $S1 $S2 $S3 $S4; say "window 1 dialogues done"
pkill -f "ssh -4 -N -o BatchMode=yes -o ServerAliveInterval=30 -L 8000:nid007466" 2>/dev/null; sshc "bash $R/workbench.sh close $W" | tail -1 | tee -a $LOG; bash cluster/ledger.sh $W peers1 "four peers: benchmarks + mixed picky-user" | tail -1 | tee -a $LOG
# window 2: gemma
GEMMA=$HUB/models--google--gemma-3-12b-it/snapshots/96b6f1eccf38110c56df3a15bffe176da04bfd80
bash cluster/preflight.sh 1.5 peers2 | tail -1 | grep -q '^OK' || { say "FAILED preflight peers2"; exit 1; }
W2=$(sshc "bash $R/workbench.sh open peers2 debug 01:29:00" | tail -1); [[ "$W2" =~ ^[0-9]+$ ]] || { say "FAILED no workbench [$W2]"; exit 1; }; say "peers2 workbench $W2 (gemma)"
sshc "cd $R; nohup setsid bash -c \"srun --jobid=$W2 --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=288 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash $R/serve_models.sh gemma=$GEMMA\" > $R/logs/serve_peers2.log 2>&1 &"
NODE2=$(sshc "squeue -h -j $W2 -o %N"); ssh -4 -N -o BatchMode=yes -o ServerAliveInterval=30 -L 8010:$NODE2:8000 clariden & TUN2=$!
ok=0; for i in $(seq 1 80); do curl -s -m 10 http://127.0.0.1:8010/v1/models | grep -q '"id"' && { ok=1; break; }; sleep 15; done
if [ $ok = 1 ]; then say "gemma ready after $((i*15)) s"; $PY data/benchmarks_el/generate.py http://127.0.0.1:8010/v1 gemma $OUT/bench_gemma --workers 24 > $OUT/bench_gemma.log 2>&1; say "gemma benchmarks: $(grep -c generated $OUT/bench_gemma.log)"; WORKERS=16 python3 data/robustness/simulate.py $OUT/r_gemma --target gemma=http://127.0.0.1:8010/v1/gemma --n 60 > $OUT/sim_gemma.log 2>&1; say "gemma dialogues done"
else say "WARN gemma did not come up: $(sshc "tail -3 $R/serve_gemma.log" | cut -c1-200)"; fi
kill $TUN2 2>/dev/null; sshc "bash $R/workbench.sh close $W2" | tail -1 | tee -a $LOG; bash cluster/ledger.sh $W2 peers2 "gemma: benchmarks + mixed picky-user" | tail -1 | tee -a $LOG
say "PEERS_DONE"
