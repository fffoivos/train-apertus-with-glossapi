set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; HUB=$R/hf_home/hub; OUT=$PWD/results/peers_20260913; mkdir -p $OUT; LOG=$OUT/run.log; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }; sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
KRIKRI=$HUB/models--ilsp--Llama-Krikri-8B-Instruct/snapshots/06d813157ba5f19deb17d70c3862ce64035431ec; MELTEMI=$HUB/models--ilsp--Meltemi-7B-Instruct-v1.5/snapshots/77d7fa68ee9f9c0addf6ed93acdc32ebafde9394
APERTUS=$HUB/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/b946d40447b2b597999b9c86d44bee0b452c919f; QWEN=$HUB/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a; GEMMA=$HUB/models--google--gemma-3-12b-it/snapshots/96b6f1eccf38110c56df3a15bffe176da04bfd80
window(){ # window <label> <serve specs...>  → sets W, NODE, opens tunnels 8000-8003
  local label=$1; shift; bash cluster/preflight.sh 1.5 "$label" | tail -1 | grep -q '^OK' || { say "FAILED preflight $label"; exit 1; }
  W=$(sshc "bash $R/workbench.sh open $label debug 01:29:00" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "FAILED no workbench [$W]"; exit 1; }; say "$label workbench $W"
  sshc "cd $R; nohup setsid bash -c \"srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=288 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash $R/serve_models.sh $*\" > $R/logs/serve_$label.log 2>&1 &"
  NODE=$(sshc "squeue -h -j $W -o %N"); ssh -4 -N -o BatchMode=yes -o ServerAliveInterval=30 -L 8000:$NODE:8000 -L 8001:$NODE:8001 -L 8002:$NODE:8002 -L 8003:$NODE:8003 clariden & TUN=$!; sleep 5
}
ready(){ local port=$1; for i in $(seq 1 60); do curl -s -m 10 http://127.0.0.1:$port/v1/models | grep -q '"id"' && return 0; sleep 15; done; return 1; }
closewin(){ kill $TUN 2>/dev/null; sshc "bash $R/workbench.sh close $W" | tail -1 | tee -a $LOG; bash cluster/ledger.sh $W "$1" "$2" | tail -1 | tee -a $LOG; }
# ---- window 1: four peers
window peers1 krikri=$KRIKRI meltemi=$MELTEMI apertus=$APERTUS qwen=$QWEN
for p in 8000 8001 8002 8003; do ready $p || say "WARN port $p not ready"; done; say "window 1 endpoints checked"
$PY data/benchmarks_el/generate.py http://127.0.0.1:8000/v1 krikri $OUT/bench_krikri --workers 24 > $OUT/bench_krikri.log 2>&1 & G1=$!
$PY data/benchmarks_el/generate.py http://127.0.0.1:8001/v1 meltemi $OUT/bench_meltemi --workers 24 > $OUT/bench_meltemi.log 2>&1 & G2=$!
$PY data/benchmarks_el/generate.py http://127.0.0.1:8002/v1 apertus $OUT/bench_apertus --workers 24 > $OUT/bench_apertus.log 2>&1 & G3=$!
$PY data/benchmarks_el/generate.py http://127.0.0.1:8003/v1 qwen $OUT/bench_qwen --workers 24 --extra-body '{"chat_template_kwargs": {"enable_thinking": false}}' > $OUT/bench_qwen.log 2>&1 & G4=$!
wait $G1 $G2 $G3 $G4; say "window 1 benchmarks generated: $(for m in krikri meltemi apertus qwen; do echo -n "$m:$(grep -c generated $OUT/bench_$m.log) "; done)"
say "window 1: mixed-profile picky-user runs (60 each) for krikri, meltemi, apertus, qwen"
WORKERS=16 python3 data/robustness/simulate.py $OUT/r_krikri --target krikri=http://127.0.0.1:8000/v1/krikri --n 60 > $OUT/sim_krikri.log 2>&1 & S1=$!
WORKERS=16 python3 data/robustness/simulate.py $OUT/r_meltemi --target meltemi=http://127.0.0.1:8001/v1/meltemi --n 60 > $OUT/sim_meltemi.log 2>&1 & S2=$!
WORKERS=16 python3 data/robustness/simulate.py $OUT/r_apertus --target apertus=http://127.0.0.1:8002/v1/apertus --n 60 > $OUT/sim_apertus.log 2>&1 & S3=$!
WORKERS=16 python3 data/robustness/simulate.py $OUT/r_qwen --target qwen=http://127.0.0.1:8003/v1/qwen --n 60 > $OUT/sim_qwen.log 2>&1 & S4=$!
wait $S1 $S2 $S3 $S4; say "window 1 dialogues done"; closewin peers1 "four peers: four Greek benchmarks + mixed picky-user"
# ---- window 2: gemma
window peers2 gemma=$GEMMA
if ready 8000; then
  $PY data/benchmarks_el/generate.py http://127.0.0.1:8000/v1 gemma $OUT/bench_gemma --workers 24 > $OUT/bench_gemma.log 2>&1; say "gemma benchmarks: $(grep -c generated $OUT/bench_gemma.log)"
  WORKERS=16 python3 data/robustness/simulate.py $OUT/r_gemma --target gemma=http://127.0.0.1:8000/v1/gemma --n 60 > $OUT/sim_gemma.log 2>&1; say "gemma dialogues done"
else say "WARN gemma did not come up in vLLM: $(sshc "tail -3 $R/serve_gemma.log" | cut -c1-200)"; fi
closewin peers2 "gemma: four Greek benchmarks + mixed picky-user"
say "programmatic scoring"; for M in krikri meltemi apertus qwen gemma; do for L in el en; do
  [ -s $OUT/bench_$M/math500_$L.jsonl ] && $PY data/benchmarks_el/math500/score_math500.py $OUT/bench_$M/math500_$L.jsonl $OUT/bench_$M/math500_${L}_score.json 2>&1 | tail -1 | cut -c1-120 | sed "s/^/math500 $M $L: /" | tee -a $LOG
  [ -s $OUT/bench_$M/ifbench_$L.jsonl ] && $PY data/benchmarks_el/ifbench/score.py $OUT/bench_$M/ifbench_$L.jsonl $OUT/bench_$M/ifbench_${L}_score.jsonl 2>&1 | tail -1 | cut -c1-120 | sed "s/^/ifbench $M $L: /" | tee -a $LOG
done; done
say "PEERS_DONE"
