#!/usr/bin/env python3
"""Checkpoint loop for Sol: an implementer session works up to a checkpoint, an independent reviewer session (fresh context,
read-only sandbox) reviews it against written criteria, and the two exchange messages through messages/ until the reviewer
returns VERDICT: PASS or the cycle cap is hit. The orchestrator (Fable) runs the tests between them and owns the loop.
Usage: python3 sol_loop.py --dir DIR --ckpt CK1 --criteria FILE [--impl-session ID] [--review-session ID] [--max-cycles 3]
       [--test-cmd CMD] [--impl-brief FILE] [--skip-first-impl] [--model gpt-5.6-sol] [--effort high]
Files: DIR/messages/{impl,review}_<ckpt>_<cycle>.md, tests_<ckpt>_<cycle>.txt, sessions.json. Exit 0 on PASS, 2 on HOLD after cap."""
import argparse, json, os, pathlib, re, subprocess, sys, time, datetime
ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); ap.add_argument('--ckpt', required=True); ap.add_argument('--criteria', required=True)
ap.add_argument('--impl-session'); ap.add_argument('--review-session'); ap.add_argument('--max-cycles', type=int, default=3); ap.add_argument('--test-cmd', default="python3 -m unittest discover -p 'test_*.py'")
ap.add_argument('--impl-brief'); ap.add_argument('--skip-first-impl', action='store_true'); ap.add_argument('--start-cycle', type=int, default=1); ap.add_argument('--impl-note', help='file with an execution failure report; the start cycle asks the implementer to fix it instead of answering a review'); ap.add_argument('--model', default='gpt-5.6-sol'); ap.add_argument('--effort', default='high')
a = ap.parse_args(); D = pathlib.Path(a.dir).resolve(); M = D / 'messages'; M.mkdir(exist_ok=True); SESS = M / 'sessions.json'
sessions = json.loads(SESS.read_text()) if SESS.exists() else {}
if a.impl_session: sessions['impl'] = a.impl_session
if a.review_session: sessions['review'] = a.review_session
FLAGS = ['--skip-git-repo-check', '-m', a.model, '-c', f'model_reasoning_effort={a.effort}', '-c', 'features.remote_plugin=false', '-c', 'features.apps=false']
def log(*x): print(f"[{datetime.datetime.now(datetime.UTC).strftime('%H:%M:%SZ')}]", *x, flush=True)
def codex(role, prompt, out, sandbox):
    """Run one Sol turn: resume the role's session if known, else start one (and record its id)."""
    sid = sessions.get(role); logf = M / f'{out.stem}.codexlog'
    if sid: cmd = ['codex', 'exec', 'resume', *FLAGS, '-o', str(out), sid, prompt]
    else: cmd = ['codex', 'exec', *FLAGS, '-s', sandbox, '-C', str(D), '-o', str(out), prompt]
    t0 = time.time()
    with open(logf, 'w') as h: rc = subprocess.run(cmd, cwd=D, stdout=h, stderr=subprocess.STDOUT).returncode
    txt = logf.read_text(errors='replace')
    if not sid:
        m = re.search(r'session id: ([0-9a-f-]{36})', txt)
        if m: sessions[role] = m.group(1); SESS.write_text(json.dumps(sessions, indent=1))
    log(f'{role} turn rc={rc} {round((time.time()-t0)/60,1)} min -> {out.name} ({out.stat().st_size if out.exists() else 0} bytes)')
    if rc != 0: log(f'{role} turn FAILED; see {logf.name}')
    return rc
def tests(cycle):
    out = M / f'tests_{a.ckpt}_{cycle}.txt'; r = subprocess.run(a.test_cmd, shell=True, cwd=D, capture_output=True, text=True)
    out.write_text(r.stdout + r.stderr); ok = r.returncode == 0; log(f'tests cycle {cycle}: {"OK" if ok else "FAIL"} rc={r.returncode}'); return ok, out
crit = pathlib.Path(a.criteria).resolve()
for cycle in range(a.start_cycle, a.start_cycle + a.max_cycles):
    impl_msg = M / f'impl_{a.ckpt}_{cycle}.md'; rev_msg = M / f'review_{a.ckpt}_{cycle}.md'; prev = M / f'review_{a.ckpt}_{cycle-1}.md'
    if not (cycle == a.start_cycle and a.skip_first_impl):
        if cycle == a.start_cycle and a.impl_note: p = f"Checkpoint {a.ckpt}, cycle {cycle}. The orchestrator executed your entry command and it failed. The failure report and log excerpt are in {pathlib.Path(a.impl_note).resolve()}. Diagnose from the log, fix the cause in your code (keep tests green: {a.test_cmd}), and write your reply at {impl_msg}: cause, fix (file and function), and what the orchestrator should run next. Do not modify files outside your directory."
        elif cycle == a.start_cycle and a.impl_brief: p = f"Checkpoint {a.ckpt}. Read {a.impl_brief} and do exactly that work, nothing beyond it. When done, write a message for the independent reviewer at {impl_msg} (what you built, how you tested it, what you could not do and why). Do not modify files outside your directory."
        else: p = f"Checkpoint {a.ckpt}, cycle {cycle}. The independent reviewer's findings are in {prev}. Address every finding: fix what is right, and where you disagree say so with evidence. Keep tests green ({a.test_cmd}). Then write your reply to the reviewer at {impl_msg}: for each finding, its number, what you changed (file and function) or why not. Do not modify files outside your directory."
        codex('impl', p, impl_msg.with_suffix('.last.md'), 'workspace-write')  # -o capture kept apart so it cannot overwrite the implementer's own message file
    ok, tout = tests(cycle)
    rp = (f"You are the independent reviewer for checkpoint {a.ckpt}, cycle {cycle}. You did not write this code; the implementer is a separate session. "
          f"Acceptance criteria: {crit}. The implementer's message to you: {impl_msg if impl_msg.exists() else '(none: first review of existing work)'}. "
          f"The orchestrator ran the tests; verbatim output: {tout} (result: {'PASS' if ok else 'FAIL'}). Read the criteria, then the code, prompts and docs in this directory, "
          f"and check every criterion against the actual source, not the implementer's claims. Your reply must start with exactly 'VERDICT: PASS' or 'VERDICT: HOLD' on the first line, "
          f"then numbered findings ordered by severity (blocking / major / minor), each with file and line, what is wrong, and the concrete required fix; then what you verified as correct. "
          f"HOLD only for findings that violate the criteria or the plan; do not hold for taste. You cannot write files; your final message is saved verbatim.")
    codex('review', rp, rev_msg, 'read-only')
    verdict = (rev_msg.read_text().strip().splitlines() or [''])[0] if rev_msg.exists() else ''
    log(f'cycle {cycle} verdict: {verdict[:40]}')
    if verdict.startswith('VERDICT: PASS') and ok: log(f'LOOP_PASS {a.ckpt} cycle {cycle}'); sys.exit(0)
log(f'LOOP_HOLD {a.ckpt} after {a.max_cycles} cycles'); sys.exit(2)
