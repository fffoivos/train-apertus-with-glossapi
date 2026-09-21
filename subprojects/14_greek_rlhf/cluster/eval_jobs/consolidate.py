#!/usr/bin/env python3
"""One file with every DPO01 measurement, for the write-up and the artifact.

Emits both baselines for each model: `parent` (its own generation config) and `parent_ckptcfg`
(the parent's weights under a checkpoint's config). The second is the fair one — the difference
between them is a tooling artefact, not training.
"""
import glob, json, os, statistics as st

R = os.environ.get("DPO01_RESULTS", "/iopsstor/scratch/cscs/fffoivos/sft_round1/results/G4F6P1--DPO01")
# the six Global-MMLU-Lite language groups; their 36 subject children must NOT be averaged in
LANG_GROUPS = ["global_mmlu_%s" % l for l in ("de", "en", "es", "fr", "it", "pt")]

def lm(label):
    fs = glob.glob(os.path.join(R, "full", label, "**", "results_*.json"), recursive=True)
    if not fs: return {}
    d = json.load(open(fs[0]))["results"]
    cells = {t: v for t, mm in d.items() if t.startswith("global_mmlu_")
             for k, v in mm.items() if k.startswith("acc,") and isinstance(v, float)}
    out = {"ifeval": d.get("ifeval_greek", {}).get("prompt_level_strict_acc,none"),
           "ifeval_inst": d.get("ifeval_greek", {}).get("inst_level_strict_acc,none"),
           "mgsm": d.get("mgsm_greek", {}).get("exact_match,none")}
    if cells:
        # R-DPO7a [HIGH]: the harness emits SIX language group rows (global_mmlu_en, ...) AND their
        # 36 subject children, 42 rows in total. Averaging all 42 counts every observation twice --
        # once inside its language aggregate and once on its own -- and it does not bias every model
        # equally: the group rows are item-weighted within a language, so a model that is stronger on
        # the larger subjects shifts more. On the parent that was 1.96 pp against 0.53 pp for arm01,
        # i.e. it corrupted the DELTAS, not just the levels. Average the six official group rows.
        langs = [t for t in LANG_GROUPS if t in cells]
        if len(langs) != len(LANG_GROUPS):
            missing = sorted(set(LANG_GROUPS) - set(langs))
            out["gmmlu_lite_incomplete"] = missing          # never silently average a partial set
        else:
            out["gmmlu_lite"] = sum(cells[t] for t in langs) / len(langs)
        out["gmmlu_cells"] = cells
    return out

def served(label):
    out = {}
    for lang in ("el", "en"):
        f = os.path.join(R, "served", label, "math500_%s_score.json" % lang)
        if os.path.exists(f) and os.path.getsize(f):
            try: out["math500_" + lang] = json.load(open(f))["equiv500_acc"]
            except Exception: pass
    f = os.path.join(R, "served", label, "ifbench_el_score.jsonl")
    if os.path.exists(f) and os.path.getsize(f):
        try:
            rows = [json.loads(l) for l in open(f) if l.strip()]
            items = [r for r in rows if "strict" in r]
            if items: out["ifbench"] = sum(1 for r in items if all(r["strict"])) / len(items)
        except Exception: pass
    return out

def gmmlu_el(label):
    fs = glob.glob(os.path.join(R, "greekmmlu", label, "*_native_mcq_headline.json"))
    if not fs: return {}
    for r in json.load(open(fs[0])):
        if r.get("subject") == "__all__":
            return {"greekmmlu": r["accuracy"]}
    return {}

labels = sorted({os.path.basename(p.rstrip("/")) for d in ("full", "served", "greekmmlu")
                 for p in glob.glob(os.path.join(R, d, "*/"))} - {".stage_parent"})
all_ = {}
for l in labels:
    if l.startswith(".stage"): continue
    m = {}; m.update(lm(l)); m.update(served(l)); m.update(gmmlu_el(l))
    if any(v is not None for v in m.values()): all_[l] = m
out = os.path.join(R, "all_results.json")
json.dump(all_, open(out, "w"), indent=1)
print("wrote %s: %d models" % (out, len(all_)))
for k in ("parent", "parent_ckptcfg"):
    if k in all_:
        m = all_[k]
        print("  %-15s IFEval %s  MGSM %s  GreekMMLU %s" % (
            k, round(m.get("ifeval") or 0, 4), round(m.get("mgsm") or 0, 4), round(m.get("greekmmlu") or 0, 3)))
print("  coverage: %d with ifeval, %d with math500, %d with greekmmlu"
      % (sum(1 for m in all_.values() if m.get("ifeval") is not None),
         sum(1 for m in all_.values() if m.get("math500_el") is not None),
         sum(1 for m in all_.values() if m.get("greekmmlu") is not None)))
