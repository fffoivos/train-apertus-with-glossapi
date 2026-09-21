#!/usr/bin/env python3
"""Freeze the 750-instance DPO01 hyperparameter screen (DPO_EXPERIMENT_COMPARISON_20260918.md §4).

Deterministic: seed 20260918, hash ordering, largest-remainder quotas over recorded strata.
CPU only, no model, no GPU. Run on the login node; writes screen_manifest.json and nothing else.

  PYTHONPATH=$PYENV python3 build_screen_manifest.py --out <path>
"""
import argparse, collections, hashlib, json, os, pathlib, sys, datetime

SEED = "20260918"
S = pathlib.Path("/iopsstor/scratch/cscs/fffoivos")
ROUND = S / "sft_round1"
CLEAN_SUBSET = pathlib.Path("/capstor/scratch/cscs/fffoivos/cpt_runs/dataset-scheduling-0p5b/"
                            "20260803T064000Z-static-prelaunch-v2/greekmmlu_clean_subset_manifest.json")
LANGS = ["el", "en", "fr", "de", "es", "it", "pt"]

def h(*parts):
    """Stable ordering key: seed-salted sha256 of the item identity."""
    return hashlib.sha256(("|".join([SEED] + [str(p) for p in parts])).encode()).hexdigest()

def sha_file(p):
    p = pathlib.Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def largest_remainder(strata, total):
    """Allocate `total` across strata proportional to size, largest remainder, hash tie-break."""
    n = sum(len(v) for v in strata.values())
    if n <= total:
        return {k: len(v) for k, v in strata.items()}
    exact = {k: len(v) * total / n for k, v in strata.items()}
    base = {k: int(v) for k, v in exact.items()}
    left = total - sum(base.values())
    order = sorted(strata, key=lambda k: (-(exact[k] - base[k]), h("quota", k)))
    for k in order[:left]:
        base[k] += 1
    return base

def take(strata, quotas):
    """Pick quota items per stratum in hash order; returns a flat, hash-ordered id list."""
    out = []
    for k in sorted(strata):
        ids = sorted(strata[k], key=lambda i: h(k, i))
        out += ids[: quotas.get(k, 0)]
    return sorted(out, key=lambda i: h("final", i))

# ---------------------------------------------------------------- component builders
def ifeval(n=150):
    from datasets import load_dataset
    d = load_dataset("ilsp/ifeval_greek", split="train")
    strata = collections.defaultdict(list)
    for i, r in enumerate(d):
        key = str(r.get("key", i))
        fams = r.get("instruction_id_list") or ["unknown"]
        # multi-label items are assigned to their hash-lowest family, so every item lands in exactly one stratum
        fam = sorted(fams, key=lambda f: h("fam", key, f))[0].split(":")[0]
        strata[fam].append(key)
    q = largest_remainder(strata, n)
    return dict(task="ifeval_greek", source="ilsp/ifeval_greek", split="train", universe=len(d),
                selected=take(strata, q), strata={k: len(v) for k, v in strata.items()}, quotas=q,
                scorer="evals/ilsp/tasks/ifeval_greek/utils.py:process_results",
                primary_metric="prompt_level_strict_acc",
                decoding=dict(do_sample=False, temperature=0.0, max_gen_toks=1280, until=[]),
                num_fewshot=0)

def mgsm(n=50):
    from datasets import load_dataset
    d = load_dataset("ilsp/mgsm_greek", split="test")
    ids = [str(r.get("id", i)) for i, r in enumerate(d)]
    strata = {"all": ids}
    return dict(task="mgsm_greek", source="ilsp/mgsm_greek", split="test", universe=len(d),
                selected=take(strata, {"all": n}), strata={"all": len(ids)}, quotas={"all": n},
                scorer="evals/ilsp/tasks/mgsm_greek/utils.py", primary_metric="exact_match",
                decoding=dict(do_sample=False, temperature=0.0), num_fewshot=0)

def math500(n=50):
    src = ROUND / "data/benchmarks_el/math500/problems_el_final.jsonl"
    rows = [json.loads(l) for l in open(src, encoding="utf-8")]
    strata = collections.defaultdict(list)
    for r in rows:
        pid = r.get("id") or r.get("problem_id") or r.get("unique_id")
        strata[(r.get("subject") or r.get("type") or "unknown")].append(str(pid))
    q = largest_remainder(strata, n)
    ids = take(strata, q)
    return dict(task="math500", source=str(src), source_sha256=sha_file(src), universe=len(rows),
                selected=ids, instances=[f"{i}:{lang}" for i in ids for lang in ("el", "en")],
                strata={k: len(v) for k, v in strata.items()}, quotas=q,
                languages=["el", "en"], shared_ids_across_languages=True,
                scorer="data/benchmarks_el/math500/score_math500.py", primary_metric="accuracy",
                decoding=dict(temperature=0.0, top_p=1.0, max_tokens=2048))

def greekmmlu(n=100):
    """Clean subset = frozen ids (greekmmlu:<row index>) into dascim/GreekMMLU All/test; subject from the dataset."""
    from datasets import load_dataset
    man = json.loads(CLEAN_SUBSET.read_text())
    ids_path = pathlib.Path(man["clean_example_ids"]["path"])
    clean = [l.strip() for l in ids_path.read_text().splitlines() if l.strip()]
    # The legacy hub cache has a dangling blob for this parquet, so fetch the pinned revision instead.
    d = load_dataset(man["dataset_repo_id"], man["dataset_config"],
                     split=man["dataset_split"], revision=man["dataset_revision"])
    subj = [str(r) for r in d["subject"]]
    strata = collections.defaultdict(list)
    missing = 0
    for eid in clean:
        try:
            i = int(eid.split(":")[1])
            strata[subj[i]].append(eid)
        except (IndexError, ValueError):
            missing += 1
    q = largest_remainder(strata, n)
    return dict(task="greekmmlu_clean", source=str(CLEAN_SUBSET), source_sha256=sha_file(CLEAN_SUBSET),
                ids_file=str(ids_path), ids_sha256=sha_file(ids_path),
                dataset=f'{man["dataset_repo_id"]}@{man.get("dataset_revision")}',
                universe=len(clean), unresolved_ids=missing, selected=take(strata, q),
                strata={k: len(v) for k, v in strata.items()}, quotas=q,
                scorer="finalize_hf_greekmmlu.py (frozen CPT-card FP32 candidate likelihood)",
                primary_metric="accuracy", protocol="official_label", num_fewshot=0)

GLOBAL_MMLU_LITE = (S / "evals/full8_retention_20260819/retention_only/cache/3124429_iter_0002384"
                      / "hf_home/hub/datasets--CohereForAI--Global-MMLU-Lite/snapshots"
                      / "36c2fd756f19ccf13a9a96c8e53ccecc02192b8b")

def global_mmlu(n=50):
    """50 shared underlying question IDs, scored in every language that is actually cached offline.

    Only Global-MMLU-Lite is cached here and it carries no Greek, so `el` is recorded as UNMEASURED
    rather than substituted with another test (DPO_EXPERIMENT_COMPARISON_20260918.md and the plan's
    rule on unsupported languages). Greek retention is covered separately by greekmmlu_clean.
    """
    from datasets import load_dataset
    import glob
    per_lang, universe, unmeasured = {}, {}, []
    for lg in LANGS:
        files = sorted(glob.glob(str(GLOBAL_MMLU_LITE / lg / "*.parquet")))
        if not files:
            unmeasured.append(lg); continue
        d = load_dataset("parquet", data_files=files, split="train")
        cols = d.column_names
        idc = "sample_id" if "sample_id" in cols else ("id" if "id" in cols else None)
        per_lang[lg] = {(str(d[idc][i]) if idc else str(i)): str(d["subject"][i]) for i in range(len(d))}
        universe[lg] = len(d)
    if not per_lang:
        raise FileNotFoundError(f"no cached Global-MMLU parquet under {GLOBAL_MMLU_LITE}")
    shared = set.intersection(*[set(v) for v in per_lang.values()])
    ref = per_lang[sorted(per_lang)[0]]
    strata = collections.defaultdict(list)
    for sid in shared:
        strata[ref[sid]].append(sid)
    q = largest_remainder(strata, n)
    ids = take(strata, q)
    langs_ok = sorted(per_lang)
    return dict(task="global_mmlu_lite", source="CohereForAI/Global-MMLU-Lite",
                snapshot=str(GLOBAL_MMLU_LITE), split="test",
                languages_measured=langs_ok, languages_unmeasured=unmeasured,
                unmeasured_reason="not cached offline; not substituted with another test",
                universe_per_language=universe, shared_universe=len(shared),
                selected=ids, instances=[f"{i}:{lg}" for i in ids for lg in langs_ok],
                strata={k: len(v) for k, v in strata.items()}, quotas=q,
                scorer="lm_eval global_mmlu (installed task config)", primary_metric="acc", num_fewshot=0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROUND / "results/G4F6P1--DPO01/screen_manifest.json"))
    a = ap.parse_args()
    comps = {}
    for name, fn in (("ifeval_greek", ifeval), ("mgsm_greek", mgsm), ("math500", math500),
                     ("greekmmlu_clean", greekmmlu), ("global_mmlu", global_mmlu)):
        try:
            comps[name] = fn()
            k = comps[name]
            print(f"  {name}: {len(k.get('instances') or k['selected'])} instances "
                  f"from {k.get('universe') or k.get('shared_universe')} ({len(k['strata'])} strata)")
        except Exception as e:
            comps[name] = {"error": f"{type(e).__name__}: {e}"[:400]}
            print(f"  {name}: FAILED {type(e).__name__}: {e}", file=sys.stderr)
    total = sum(len(c.get("instances") or c.get("selected") or []) for c in comps.values())
    models = {"parent": "fffoivos/greek-apertus-8b-sft-r4-full@3a557e08"}
    for arm, lr, kind in (("00", "5e-7", "plain"), ("01", "2e-6", "plain"),
                          ("02", "5e-7", "anchored"), ("03", "2e-6", "anchored")):
        for ep, step in ((1, 43), (2, 86), (3, 129)):
            models[f"arm{arm}_ep{ep}"] = dict(
                path=f"runs/G4F6P1--DPO01--{arm}/checkpoint-{step}", lr=lr, objective=kind, epoch=ep)
    man = dict(
        experiment="G4F6P1--DPO01",
        purpose="hyperparameter screen: select at most two finalists (one plain, one anchored)",
        plan="docs/RLHF_COORDINATION/DPO_EXPERIMENT_COMPARISON_20260918.md §4-5",
        frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        seed=SEED, selection="seed-salted sha256 ordering, largest-remainder quotas over recorded strata",
        expected_instances_per_model=total, expected_total=total * len(models),
        models=models, components=comps,
        deviation=("The plan required this manifest to be frozen BEFORE training. It was not: the four arms "
                   "trained first. No benchmark output has been seen for any arm at freeze time, so the "
                   "selection remains blind to the screen, but the ordering deviation is recorded here."),
        selection_rules="§5: flag on retention thresholds, then highest Greek IFEval prompt-strict; "
                        "ties -> macro retention, earlier epoch, lower LR, plain DPO. Max two finalists.",
    )
    out = pathlib.Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    # Hash the BYTES ON DISK, not the pre-write string: the artifact is the file, and a manifest whose
    # recorded hash describes something else cannot bind anything. (Earlier version hashed body, wrote body+"\n".)
    out.write_text(json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    sidecar = out.with_suffix(".sha256")
    sidecar.write_text(f"{digest}  {out.name}\n")
    print(f"\nwrote {out}\n  {total} instances/model x {len(models)} models = {total*len(models)} scored instances"
          f"\n  sha256(file) {digest}\n  sidecar {sidecar.name}"
          f"\n  verify: sha256sum -c {sidecar}")

if __name__ == "__main__":
    main()
