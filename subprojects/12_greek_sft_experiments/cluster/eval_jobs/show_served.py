#!/usr/bin/env python3
"""Served-lane table: MATH-500 (el, en) and Greek IFBench for every DPO01 checkpoint, vs the parent."""
import json, glob, os

R = "/iopsstor/scratch/cscs/fffoivos/sft_round1/results/G4F6P1--DPO01/served"
ARMS = {"00": "5e-7 a0", "01": "2e-6 a0", "02": "5e-7 a1.0", "03": "2e-6 a1.0",
        "04": "2e-6 a0.1", "05": "2e-6 a0.25", "06": "2e-6 a0.5",
        "07": "2e-6 a0.25 5ep", "05s43": "2e-6 a0.25 s43", "01s43": "2e-6 a0 s43",
        "08": "4e-6 a0.25", "BAL": "2e-6 a0 balanced"}

def get(label):
    d = {}
    for lang in ("el", "en"):
        f = os.path.join(R, label, "math500_%s_score.json" % lang)
        if os.path.exists(f) and os.path.getsize(f):
            try:
                d["m_" + lang] = json.load(open(f)).get("equiv500_acc")
            except Exception:
                pass
    # score.py prints its summary to stdout and writes PER-ITEM rows to the file, so the
    # prompt-level strict rate is computed here: a prompt passes only if every constraint passes.
    f = os.path.join(R, label, "ifbench_el_score.jsonl")
    if os.path.exists(f) and os.path.getsize(f):
        try:
            rows = [json.loads(l) for l in open(f) if l.strip()]
            items = [r for r in rows if "strict" in r]
            if items:
                d["ifb"] = sum(1 for r in items if all(r["strict"])) / len(items)
                d["ifb_n"] = len(items)
        except Exception:
            pass
    return d

base = get("parent")

def cell(d, k, is_parent):
    v = d.get(k)
    if v is None:
        return "     --       "
    bv = base.get(k)
    delta = "" if is_parent or bv is None else "%+6.1f" % ((v - bv) * 100)
    return "%9.3f %6s" % (v, delta)

print("%-12s %-11s %14s %14s %14s" % ("model", "config", "MATH500-el", "MATH500-en", "IFBench-el"))
print("-" * 70)

def row(label, desc):
    d = get(label)
    if not d:
        return False
    p = label == "parent"
    print("%-12s %-11s %s %s %s" % (label, desc, cell(d, "m_el", p), cell(d, "m_en", p), cell(d, "ifb", p)))
    return True

row("parent", "parent")
n = 1
for ep in ("5", "4", "3", "2", "1"):
    for a in sorted(ARMS):
        if row("arm%s_ep%s" % (a, ep), ARMS[a]):
            n += 1
done = len(glob.glob(os.path.join(R, "*", "math500_el_score.json")))
print("\n%d models have MATH-500 scores" % done)
