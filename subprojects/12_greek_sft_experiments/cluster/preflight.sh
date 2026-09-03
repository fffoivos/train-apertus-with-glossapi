#!/usr/bin/env bash
# Budget guard per CLUSTER_PROTOCOL.md §3 (runs on the Mac): refuses if used + projected > cap.
# Usage: preflight.sh <projected_nh> <label>
set -euo pipefail
cd "$(dirname "$0")/.."
proj=$1; label=$2
cap=$(python3 -c "import json;print(json.load(open('execution_state.json'))['cap_chf'])")
rate=$(python3 -c "import json;print(json.load(open('execution_state.json'))['rate_chf_per_nh'])")
used=$(python3 -c "import json;print(json.load(open('execution_state.json'))['nh_used'])")
tot=$(python3 -c "print(round(($used+$proj)*$rate,2))")
month=$(ssh -o BatchMode=yes clariden 'sreport -n -t hours cluster AccountUtilizationByUser start=2026-09-01 end=now account=a0140 format=Used 2>/dev/null | awk "{u+=\$1} END {print u/288}"' 2>/dev/null | tail -1)
echo "preflight $label: used ${used} nh + projected ${proj} nh = CHF ${tot} of cap ${cap}; account usage this month ${month:-?} nh"
python3 -c "import sys; sys.exit(0 if $tot <= $cap else 1)" || { echo "REFUSED: over cap"; exit 1; }
echo OK
