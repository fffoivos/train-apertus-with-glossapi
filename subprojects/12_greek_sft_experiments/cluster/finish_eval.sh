#!/usr/bin/env bash
# Pull a checkpoint's light-eval outputs from the cluster and run the Mac-side voice score + interview scoring.
# Usage: cluster/finish_eval.sh <label>   (waits up to 30 min for ILSP results and turn3 to exist)
set -u
LABEL=$1; S=/iopsstor/scratch/cscs/fffoivos; EV=$S/sft_round1/evals/$LABEL
HERE="$(cd "$(dirname "$0")/.." && pwd)"; P=/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python
LOCAL=$HERE/results/$LABEL; mkdir -p $LOCAL/interviews $LOCAL/dev
sshc() { ssh -o BatchMode=yes clariden "$@" 2>/dev/null; }; say() { echo "[$(date '+%H:%M')] finish $LABEL: $*"; }
for i in $(seq 1 30); do ok=$(sshc "[ -s $EV/interviews/turn3.jsonl ] && ls $EV/ilsp/*/results*.json >/dev/null 2>&1 && [ -s $EV/dev/reading40_gen.jsonl ] && echo yes"); [ "$ok" = yes ] && break; sleep 60; done
say "inputs present: ${ok:-no}"
scp -rq clariden:$EV/dev clariden:$EV/ilsp $LOCAL/ 2>/dev/null; scp -q clariden:$EV/interviews/turn{1,2,3}.jsonl clariden:$EV/interviews/followups{2,3}.jsonl $LOCAL/interviews/ 2>/dev/null
$P - "$LOCAL" <<'PY'
import json, glob, sys
L=sys.argv[1]
for f in glob.glob(f'{L}/ilsp/*/results*.json'):
    d=json.load(open(f)); print('ILSP', {t:{k:round(v,4) for k,v in m.items() if isinstance(v,(int,float)) and 'stderr' not in k} for t,m in d['results'].items()})
g=json.load(open(f'{L}/dev/format_gate.json')); print('GATE', g['metrics'])
PY
(cd $HERE/evals && $P dev/voice_score.py $LOCAL/dev/dev_gen.jsonl) > $LOCAL/dev/voice.log 2>&1; say "voice: $(tail -n 2 $LOCAL/dev/voice.log | tr '\n' ' ' | cut -c1-200)"
(cd $HERE/evals && $P interviews/score.py --run $LABEL --out-dir $LOCAL/interviews) > $LOCAL/interviews/score.log 2>&1; say "interview score: $(tail -n 2 $LOCAL/interviews/score.log | tr '\n' ' ' | cut -c1-200)"
say DONE
