#!/usr/bin/env python3
"""Run one independent Sol review at a plan checkpoint (two-stream plan §10).
Usage: python3 data/rlhf/sol_review.py <CHECKPOINT_ID> [--cycle N] [--effort xhigh]
Reads docs/RLHF_COORDINATION/reviews/<ID>_brief.md (stage goal, scope, context files, acceptance criteria, evidence, out of scope) and,
for cycle > 1, <ID>_reply_<N-1>.md (the implementer's answers to the previous findings). Runs a fresh read-only Codex session with
gpt-5.6-sol at the given effort from the repository root, and saves the verdict to <ID>_review_<N>.md (first line VERDICT: PASS or
VERDICT: HOLD). Exit code 0 on PASS, 2 on HOLD, 1 on failure."""
import argparse, pathlib, subprocess, sys, datetime, re
ROOT = pathlib.Path(__file__).resolve().parents[2]; R = ROOT / 'docs' / 'RLHF_COORDINATION' / 'reviews'
ap = argparse.ArgumentParser(); ap.add_argument('ckpt'); ap.add_argument('--cycle', type=int, default=1); ap.add_argument('--effort', default='xhigh'); a = ap.parse_args()
brief = R / f'{a.ckpt}_brief.md'
if not brief.exists(): sys.exit(f'missing brief {brief}')
prev_reply = R / f'{a.ckpt}_reply_{a.cycle - 1}.md'
prev_review = R / f'{a.ckpt}_review_{a.cycle - 1}.md'
out = R / f'{a.ckpt}_review_{a.cycle}.md'; log = R / f'{a.ckpt}_review_{a.cycle}.codexlog'
prompt = (f"You are the independent reviewer for checkpoint {a.ckpt}, cycle {a.cycle}, of the Greek Apertus RLHF programme. "
          f"You did not do the work under review. Read the review brief {brief} first: it states the stage goal, the scope since the previous "
          f"checkpoint, the context files, the acceptance criteria, the evidence and what is out of scope. "
          + (f"The previous review is {prev_review} and the implementer's reply to it is {prev_reply}; check every earlier finding against the current files. " if a.cycle > 1 else "")
          + "Verify every criterion against the actual files, data and logs, not against claims in the brief or reply. Run read-only commands as needed. "
          "Your reply must start with exactly 'VERDICT: PASS' or 'VERDICT: HOLD' on the first line, then numbered findings ordered by severity "
          "(blocking / major / minor), each with the file and line or the record id, what is wrong, why it matters for this stage's goal, and the "
          "concrete fix; then a short list of what you verified as correct. HOLD only for blocking or major findings that violate the criteria or "
          "the stage goal; do not hold for taste. You cannot write files; your final message is saved verbatim.")
cmd = ['codex', 'exec', '--skip-git-repo-check', '-s', 'read-only', '-m', 'gpt-5.6-sol', '-c', f'model_reasoning_effort={a.effort}',
       '-c', 'features.remote_plugin=false', '-c', 'features.apps=false', '-C', str(ROOT), '-o', str(out), prompt]
t0 = datetime.datetime.now(datetime.UTC)
with open(log, 'w') as h: rc = subprocess.run(cmd, cwd=ROOT, stdout=h, stderr=subprocess.STDOUT).returncode
verdict = out.read_text().strip().splitlines()[0] if out.exists() and out.read_text().strip() else ''
mins = round((datetime.datetime.now(datetime.UTC) - t0).total_seconds() / 60, 1)
with open(R / 'INDEX.md', 'a') as h: h.write(f"| {t0:%Y-%m-%d %H:%M}Z | {a.ckpt} | cycle {a.cycle} | {a.effort} | {verdict or 'NO VERDICT (rc=' + str(rc) + ')'} | {mins} min | {out.name} |\n")
print(f'{a.ckpt} cycle {a.cycle}: {verdict or "no verdict"} ({mins} min, rc={rc})')
sys.exit(0 if verdict.startswith('VERDICT: PASS') else 2 if verdict.startswith('VERDICT: HOLD') else 1)
