#!/usr/bin/env bash
# Record a finished job's actual node-hours: ledger.sh <jobid> <WP> <note>   (runs on the Mac)
set -euo pipefail; cd "$(dirname "$0")/.."
jid=$1; wp=$2; note=$3
read -r el nodes <<<"$(ssh -4 -o BatchMode=yes clariden "sacct -j $jid -n -X -o Elapsed,AllocNodes" | head -1)"
nh=$(python3 -c "
h,m,s=[int(x) for x in '$el'.split('-')[-1].split(':')]; d=int('$el'.split('-')[0]) if '-' in '$el' else 0
print(round((d*24+h+m/60+s/3600)*int('$nodes'),3))")
python3 - <<PY
import json,datetime
s=json.load(open('execution_state.json')); s['nh_used']=round(s['nh_used']+$nh,3); s['chf_used']=round(s['nh_used']*s['rate_chf_per_nh'],2)
json.dump(s,open('execution_state.json','w'),indent=1,ensure_ascii=False)
open('EXECUTION_LOG.md','a').write(f"| {datetime.datetime.now():%Y-%m-%d %H:%M} | $wp | job $jid | claude | $note | —/{$nh} | {s['chf_used']:.2f} |\n")
print('ledger:', s['nh_used'], 'nh', s['chf_used'], 'CHF')
PY
