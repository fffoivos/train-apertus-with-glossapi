#!/usr/bin/env python3
"""Dev metrics from every DPO01 arm's training log, including the follow-up arms."""
import json, os, sys

R = "/iopsstor/scratch/cscs/fffoivos/sft_round1"
ARMS = sys.argv[1:] or ["01", "05", "07", "05s43", "01s43", "08", "BAL"]
DESC = {"01": "2e-6 a0 s42", "05": "2e-6 a0.25 s42", "07": "2e-6 a0.25 s42 5ep",
        "05s43": "2e-6 a0.25 s43", "01s43": "2e-6 a0 s43", "08": "4e-6 a0.25 s42",
        "BAL": "2e-6 a0 s42 balanced"}
print("%-8s %-22s %7s %10s %10s %8s" % ("arm", "config", "acc", "dChosen", "dRej", "devloss"))
print("-" * 70)
for a in ARMS:
    p = os.path.join(R, "logs", "dpo01_%s.out" % a)
    if not os.path.exists(p):
        print("%-8s %-22s  (no log)" % (a, DESC.get(a, ""))); continue
    raw = open(p, errors="ignore").read()
    i = raw.rfind("DPO_DONE")
    if i < 0:
        print("%-8s %-22s  (no receipt)" % (a, DESC.get(a, ""))); continue
    try:
        d = json.JSONDecoder().raw_decode(raw[raw.index("{", i):])[0]["dev_metrics"]
    except Exception as e:
        print("%-8s  parse failed: %s" % (a, e)); continue
    print("%-8s %-22s %7.3f %10.2f %10.2f %8.3f" % (
        a, DESC.get(a, ""), d["eval_rewards/accuracies"],
        d["eval_rewards/chosen"] / 0.1, d["eval_rewards/rejected"] / 0.1, d["eval_loss"]))
