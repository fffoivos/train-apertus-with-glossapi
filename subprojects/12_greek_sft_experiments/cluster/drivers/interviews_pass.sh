set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; HERE=$PWD
S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; LOG=$HERE/results/R3_single/interviews_pass.log; PY=$HERE/cluster/nsft_python.sh
say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }; sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
LABELS="R3_pass_ep2 R3_passB_ep2"
interviewer(){ local L=$1 k=$2; (cd evals && $PY interviews/interviewer.py --run $L --turn $k --out-dir $HERE/results/$L/interviews) > $HERE/results/$L/interviews/interviewer$k.log 2>&1; say "$L interviewer turn $k: $(tail -1 $HERE/results/$L/interviews/interviewer$k.log | cut -c1-120)"; }
say "PHASE 1: interviewer turn 2 for both (Mac, Opus)"
interviewer R3_pass_ep2 2 & interviewer R3_passB_ep2 2 & wait
for L in $LABELS; do [ -s results/$L/interviews/followups2.jsonl ] || { say "FAILED: no followups2 for $L"; exit 1; }; scp -4 -q results/$L/interviews/followups2.jsonl clariden:$R/evals/$L/interviews/; done
bash cluster/preflight.sh 0.8 "interviews_pass" | tail -1 | grep -q '^OK' || { say "FAILED preflight"; exit 1; }
W=$(sshc "bash $R/workbench.sh open int_pass debug 01:29:00" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "FAILED no workbench [$W]"; exit 1; }; say "workbench $W"
NODE_ENV="export HF_HOME=$R/hf_home HF_HUB_OFFLINE=1 HF_TOKEN=\$(cat $R/hf_home/token); source $S/venvs/sft/bin/activate; cd $R/evals_code"
lane(){ local L=$1 gpu=$2 k=$3; sshc "cd $R; nohup setsid bash -c \"srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=48 --export=ALL bash -c 'CUDA_VISIBLE_DEVICES=$gpu uenv run --view=default pytorch/v2.9.1:v2 -- bash -c \\\"$NODE_ENV; python interviews/driver.py --model $R/eval_copies/$L --seeds $R/evals_code/interviews/seeds.jsonl --run $L --round $k --out-dir $R/evals/$L/interviews\\\"'\" > $R/logs/${L}_int${k}_pass.launch.log 2>&1 & echo launched $L round $k"; }
wait_turn(){ local L=$1 k=$2; for i in $(seq 1 40); do sshc "[ -s $R/evals/$L/interviews/turn$k.jsonl ] && echo yes" | grep -q yes && return 0; sleep 60; done; return 1; }
say "PHASE 2: round 2 on the cluster"; lane R3_pass_ep2 0 2; lane R3_passB_ep2 1 2
for L in $LABELS; do wait_turn $L 2 && scp -4 -q clariden:$R/evals/$L/interviews/turn2.jsonl results/$L/interviews/ && say "$L turn2 fetched" || say "FAILED $L turn2 missing"; done
say "PHASE 3: interviewer turn 3 (Mac)"; interviewer R3_pass_ep2 3 & interviewer R3_passB_ep2 3 & wait
for L in $LABELS; do scp -4 -q results/$L/interviews/followups3.jsonl clariden:$R/evals/$L/interviews/; done
say "PHASE 4: round 3 on the cluster"; lane R3_pass_ep2 0 3; lane R3_passB_ep2 1 3
for L in $LABELS; do wait_turn $L 3 && scp -4 -q clariden:$R/evals/$L/interviews/turn3.jsonl results/$L/interviews/ && say "$L turn3 fetched" || say "FAILED $L turn3 missing"; done
sshc "bash $R/workbench.sh close $W" | tail -1 | tee -a $LOG; bash cluster/ledger.sh $W interviews_pass "interview rounds 2-3 for R3_pass and R3_passB" | tail -1 | tee -a $LOG
say "PHASE 5: scoring (Mac)"
for L in $LABELS; do (cd evals && $PY interviews/score.py --run $L --out-dir $HERE/results/$L/interviews) > results/$L/interviews/score.log 2>&1; say "$L interview score: $(tail -1 results/$L/interviews/score.log | cut -c1-100)"; (cd evals && PYTHONPATH=$HOME/Projects/natural-greek-sft/src:$HOME/Projects/natural-greek-sft $HOME/venvs/sfttrain/bin/python dev/voice_score.py ../results/$L/dev/dev_gen.jsonl) > results/$L/dev/voice.log 2>&1; say "$L voice: $(tail -2 results/$L/dev/voice.log | head -1 | cut -c1-100)"; done
say "INTERVIEWS_PASS_DONE"
