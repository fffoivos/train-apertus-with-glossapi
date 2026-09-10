#!/usr/bin/env python3
"""Start a command in its OWN session/process group (start_new_session=True, the macOS-safe setsid), stdout+stderr appended to a log,
so a Claude Code session teardown cannot kill it. Usage: python3 launch_detached.py <log> <cwd> <cmd...>   Prints the pid."""
import os, subprocess, sys
log, cwd, cmd = sys.argv[1], sys.argv[2], sys.argv[3:]
with open(log, 'a') as f:
    p = subprocess.Popen(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True, env=dict(os.environ))
print(p.pid)
