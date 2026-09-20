#!/usr/bin/env python3
"""Staged edit for cluster/r4_full_chain.sh (apply ONLY after the thirteenth review verdict has landed; the chain script is pasted
into the gate-2 brief, so it must not change while a pass is in flight).

Problem: the training wait loop `st=$(sshc squeue ...); [ -z "$st" ] && break` treats an ssh failure (expired CSCS certificate,
network blip) exactly like "job finished", then the TRAIN_OK grep also fails over the dead ssh and the chain reports
"training ended without TRAIN_OK" while the Slurm job is still running. The certificate expires 2026-09-16 10:40, inside the
chain's expected span.

Fix: distinguish ssh failure from job completion; keep waiting (with a warning every 30 min) until ssh works again; after the
loop, wait for ssh to be back before reading train.log. Nothing else changes.
"""
import sys, pathlib, hashlib
p = pathlib.Path('cluster/r4_full_chain.sh'); s = p.read_text()
old = 'while true; do st=$(sshc "squeue -h -j $J -o %T"); [ -z "$st" ] && break; sleep 180; done\n'
new = ('fails=0; while true; do st=$(sshc "squeue -h -j $J -o %T"); rc=$?; if [ $rc -ne 0 ]; then if sshc true; then break; fi; fails=$((fails+1)); [ $((fails % 10)) = 1 ] && say "WARNING: ssh to clariden failing ($fails x 3 min; CSCS certificate expired? re-sign with: cscs-key sign); training job $J is unaffected, still waiting"; sleep 180; continue; fi; fails=0; [ -z "$st" ] && break; sleep 180; done\n'
       'fails=0; until sshc true; do fails=$((fails+1)); [ $((fails % 10)) = 1 ] && say "WARNING: job $J left the queue but ssh to clariden is failing ($fails x 3 min; re-sign the certificate); waiting before reading train.log"; sleep 180; done\n')
assert s.count(old) == 1, 'wait loop not found exactly once'
before = hashlib.sha256(s.encode()).hexdigest()[:16]
if '--apply' in sys.argv:
    p.write_text(s.replace(old, new)); print('applied; sha256', before, '->', hashlib.sha256(p.read_bytes()).hexdigest()[:16])
else:
    print('dry: would apply to cluster/r4_full_chain.sh (sha256', before + '); run with --apply after the verdict')
