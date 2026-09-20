#!/usr/bin/env bash
# Poll the cluster every 10 min; when the debug partition is available and not in maintenance, run the given command once. Usage: bash cluster/relaunch_when_up.sh <cmd...>
cd "$(dirname "$0")/.."; LOG=logs/relaunch_when_up.log
while true; do
  st=$(ssh -4 -o BatchMode=yes -o ConnectTimeout=30 clariden 'sinfo -p debug -h -o "%a %T %D" 2>/dev/null' 2>/dev/null | tr '\n' ';')
  echo "[$(date '+%m-%d %H:%M')] debug partition: ${st:-ssh failed}" >> $LOG
  if echo "$st" | grep -q "up idle\|up allocated\|up mixed" && ! echo "$st" | grep -qE "maint [0-9]{3,}"; then echo "[$(date '+%m-%d %H:%M')] cluster up: launching: $*" >> $LOG; exec "$@"; fi
  sleep 600
done
