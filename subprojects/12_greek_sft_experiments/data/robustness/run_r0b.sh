#!/usr/bin/env bash
# R0/R1 with a tunnel-safe client load: one fresh IPv4 tunnel, 4 workers per model (16 streams), N dialogues per model, then R1 on arm B, then close + ledger.
set -u; cd "$(dirname "$0")/../.."; J=$1; N=${2:-60}; RP=${3:-1.1}; NODE=${4:-nid006927}; PROFILE=${PROFILE:-mixed}; TAG=${TAG:-r1}   # PROFILE hostile|benign|steering|mixed; outputs go to results/robustness_${TAG}_<date>
R=/iopsstor/scratch/cscs/fffoivos/sft_round1; OUT=results/robustness_${TAG}_$(date +%Y%m%d); mkdir -p "$OUT"; LOG=$OUT/run.log
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
sshc(){ ssh -4 -o BatchMode=yes -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
rm -f "$OUT"/stage1.jsonl "$OUT"/armB.jsonl "$OUT"/apertus.jsonl "$OUT"/krikri.jsonl
ssh -4 -N -o BatchMode=yes -o ServerAliveInterval=30 -L 8000:$NODE:8000 -L 8001:$NODE:8001 -L 8002:$NODE:8002 -L 8003:$NODE:8003 clariden & TUN=$!; sleep 4
ok=0; for p in 8000 8001 8002 8003; do curl -s -m 20 "http://127.0.0.1:$p/v1/models" | grep -q '"id"' && ok=$((ok+1)); done; say "relaunch: tunnel pid $TUN, endpoints $ok/4, $N dialogues per model, 4 workers each"
[ $ok -eq 4 ] || { say "endpoints missing"; kill $TUN; exit 1; }
PIDS=(); for m in armB:8000 stage1:8001 apertus:8002 krikri:8003; do n=${m%%:*}; p=${m##*:}; WORKERS=4 python3 data/robustness/simulate.py "$OUT" --target $n=http://127.0.0.1:$p/v1/$n --n "$N" --profile "$PROFILE" > "$OUT/sim_$n.log" 2>&1 & PIDS+=($!); done
wait "${PIDS[@]}"; say "R0 done"   # wait on the clients only, never on the tunnel
WORKERS=8 python3 data/robustness/simulate.py "$OUT/rp$RP" --target armB=http://127.0.0.1:8000/v1/armB --n "$N" --rep-penalty "$RP" --profile "$PROFILE" > "$OUT/sim_rp.log" 2>&1; say "penalty arm done"
kill $TUN 2>/dev/null; sshc "tail -1 $R/m3/out/armB_summary.json 2>/dev/null | cut -c1-80"; sshc "bash $R/workbench.sh close $J" | tee -a "$LOG"; sleep 20; bash cluster/ledger.sh "$J" R0 "picky-user benchmark R0/R1 + math M3 serving window" | tee -a "$LOG"
for f in "$OUT"/*_summary.json "$OUT"/r1_rp$RP/*_summary.json; do [ -s "$f" ] && { echo "== $f"; python3 -c "import json; d=json.load(open('$f')); print({k:v for k,v in d.items() if k!='tone'}); print('tone', d.get('tone'))"; }; done | tee -a "$LOG"
say "WINDOW DONE"
