#!/usr/bin/env python3
"""Turn full-run predictions into LABELLED metrics, fail-closed. R-DPO7b [BLOCKER], R-DPO7a2 [BLOCKER/HIGH].

Removing --sample-size does not give the 16,159-item clean subset; it gives ALL 16,632 raw rows.
The clean subset is applied only by the CPT-card finalizer, which refuses Apertus checkpoints. So
the job's own headline is the RAW number and must be labelled as such: mixing a clean figure for one
model with a raw one for another would manufacture a parent/arm difference out of nothing.

Both numbers are recomputed here for every model through one code path.
  raw   = all 16,632 rows         <- the population the 250-item slice was sampled from
  clean = the 16,159-id manifest  <- comparable to the CPT card

FAIL-CLOSED, because a finalizer that partially succeeds is how a seven-model table gets published
as eight. Any invalid model aborts the whole run; nothing is written until every check has passed.

Usage: finalize_greekmmlu_full.py <dir> --manifest PATH [--expect L1,L2,...] [--out PATH]
"""
import json, glob, os, sys, hashlib

SCHEMA = "apertus_mini_greekmmlu_clean_subset_v1"
# PINNED frames (R-DPO8 finding 8). Submitted outputs must MATCH these; they never define them. If every
# model carried the same wrong frame, "the first model defines the frame" would have passed them all.
#   raw frame  = greekmmlu:0 .. greekmmlu:<full_count-1>, one per line, numeric order, trailing newline
#   250 slice  = cluster/eval_jobs/greekmmlu250_slice_ids.txt, the ids of the adaptive 18-Sept diagnostic
RAW_FRAME_SHA256 = "110733ffb6c55f5174867fb87fa503e0f35a89a39e3314bfa0b0e829eb311a86"
SLICE_FILE = "greekmmlu250_slice_ids.txt"
SLICE_SHA256 = "62f8f4c73b85ae7f0f9550565f570bcf2d27a40b395a514e1e146f53e4156964"
SLICE_N = 250
PINNED = {"dataset_repo_id": "dascim/GreekMMLU", "dataset_revision": "6a03aa06b68beb932fb75edff3a34e50b3674649",
          "dataset_config": "All", "dataset_split": "test", "full_count": 16632, "clean_count": 16159}

def die(msg):
    print("FATAL: " + msg); sys.exit(1)

def load_manifest(path):
    """The frozen manifest contract. R-DPO7a2 [BLOCKER]: `clean_example_ids` is a DESCRIPTOR
    {path, bytes, sha256} pointing at a newline-delimited id file -- not the ids themselves. The
    previous heuristic treated the dict as the iterable and silently looked for ids named 'path'
    and 'sha256', skipping every model."""
    if not path: die("--manifest is required; refusing to emit a clean number without it")
    m = json.load(open(path))
    if m.get("schema_version") != SCHEMA: die("manifest schema %r, expected %r" % (m.get("schema_version"), SCHEMA))
    if m.get("status") != "frozen":       die("manifest status %r, expected 'frozen'" % m.get("status"))
    desc = m.get("clean_example_ids")
    if not isinstance(desc, dict) or "path" not in desc: die("clean_example_ids is not a {path,sha256} descriptor")
    idp = desc["path"]
    if not os.path.exists(idp):
        alt = os.path.join(os.path.dirname(path), os.path.basename(idp))
        if not os.path.exists(alt): die("clean id file missing: %s" % idp)
        idp = alt
    blob = open(idp, "rb").read()
    got = hashlib.sha256(blob).hexdigest()
    # R-DPO7b2 [MEDIUM]: these were checked only "if present", so a same-schema descriptor that
    # omitted them could authenticate nothing -- especially via the basename fallback. Require them.
    for f in ("sha256", "bytes"):
        if f not in desc: die("clean_example_ids descriptor has no %s; refusing to trust the id file" % f)
    if got != desc["sha256"]: die("clean id file sha256 %s != manifest %s" % (got[:16], desc["sha256"][:16]))
    if len(blob) != desc["bytes"]: die("clean id file is %d bytes, manifest says %d" % (len(blob), desc["bytes"]))
    for f, want in PINNED.items():
        if m.get(f) != want: die("manifest %s = %r, pinned expectation is %r" % (f, m.get(f), want))
    ids = [l.strip() for l in blob.decode().splitlines() if l.strip()]
    if len(set(ids)) != len(ids): die("clean id file contains duplicates")
    if len(ids) != m["clean_count"]: die("clean id file has %d ids, clean_count says %d" % (len(ids), m["clean_count"]))
    print("manifest OK: %s, frozen, full=%d clean=%d contaminated=%d" % (SCHEMA, m["full_count"], m["clean_count"], m.get("contaminated_item_count", -1)))
    print("  dataset %s @ %s split=%s" % (m.get("dataset_repo_id"), (m.get("dataset_revision") or "?")[:12], m.get("dataset_split")))
    print("  clean ids sha256 %s verified\n" % got[:16])
    return set(ids), m

def check_metadata(d, label, m):
    """R-DPO7b2 [BLOCKER]: counts are not identity. Bind each model to the pinned dataset."""
    f = os.path.join(d, "run_metadata.json")
    if not os.path.exists(f): die("%s: no run_metadata.json -- cannot certify what was scored" % label)
    md = json.load(open(f))
    if md.get("model_label") != label: die("%s: metadata model_label=%r" % (label, md.get("model_label")))
    if md.get("sample_size") not in (0, None): die("%s: sample_size=%r, this is not a full run" % (label, md.get("sample_size")))
    for k, want in (("dtype", "float32"), ("max_input_tokens", 3072),
                    ("candidate_batch_size", 16), ("example_batch_size", 16)):
        if md.get(k) != want: die("%s: scoring flag %s=%r, expected %r" % (label, k, md.get(k), want))
    bs = md.get("dataset_bindings") or []
    if len(bs) != 1: die("%s: expected exactly one dataset binding, found %d" % (label, len(bs)))
    b = bs[0]
    for k, want in (("source", m["dataset_repo_id"]), ("revision", m["dataset_revision"]), ("config", m["dataset_config"]),
                    ("resolved_split", m["dataset_split"]), ("rows_before_sampling", m["full_count"])):
        if b.get(k) != want: die("%s: dataset binding %s = %r, manifest says %r" % (label, k, b.get(k), want))
    return md

def read_predictions(d, label, full_n, expect_ids):
    fs = sorted(glob.glob(os.path.join(d, "*_native_mcq_predictions.jsonl")))
    if len(fs) != 1: die("%s: expected exactly 1 prediction file, found %d" % (label, len(fs)))
    rows, seen = {}, set()
    for line in open(fs[0]):
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        eid = str(r["example_id"])
        if eid in seen: die("%s: duplicate example_id %s" % (label, eid))
        seen.add(eid)
        if str(r.get("model", label)) != label: die("%s: prediction row carries model=%r" % (label, r.get("model")))
        if r.get("benchmark") not in (None, "greekmmlu"): die("%s: row benchmark=%r" % (label, r.get("benchmark")))
        c = r["correct"]
        # R-DPO7a2 [HIGH]: the runner emits a JSON boolean; anything else means a format change we
        # have not understood, and truthiness would score the string "false" as correct.
        if not isinstance(c, bool): die("%s: example %s has non-boolean correct=%r" % (label, eid, c))
        rows[eid] = c
    if len(rows) != full_n: die("%s: %d rows, expected the full population of %d" % (label, len(rows), full_n))
    # R-DPO7b2 [BLOCKER]: "16,159 clean ids plus any 473 others" previously passed. Require the
    # EXACT raw population, so a substituted or shuffled frame cannot satisfy the count alone.
    if expect_ids is not None and set(rows) != expect_ids:
        die("%s: raw id population differs from the reference frame (%d extra, %d missing)"
            % (label, len(set(rows) - expect_ids), len(expect_ids - set(rows))))
    return rows

def main():
    root = sys.argv[1]
    man = out = None; expect = None; slice_dir = None
    for i, a in enumerate(sys.argv):
        if a == "--manifest": man = sys.argv[i + 1]
        if a == "--out":      out = sys.argv[i + 1]
        if a == "--expect":   expect = [x for x in sys.argv[i + 1].split(",") if x]
        if a == "--slice-file": slice_dir = sys.argv[i + 1]
    keep, m = load_manifest(man)
    full_n, clean_n = m["full_count"], m["clean_count"]

    if not expect: die("--expect L1,L2,... is required: the model set is part of the claim")
    dirs = {os.path.basename(d): d for d in sorted(glob.glob(os.path.join(root, "*")))
            if os.path.isdir(d) and not os.path.basename(d).startswith(".")}
    if expect:
        missing = [l for l in expect if l not in dirs]
        if missing: die("expected models absent: %s" % ", ".join(missing))
        extra = [l for l in dirs if l not in expect]
        if extra: print("note: ignoring unexpected dirs: %s" % ", ".join(extra))
        dirs = {l: dirs[l] for l in expect}
    if not dirs: die("no model directories under %s" % root)

    # the ids of the 250-item slice already reported, so the full run can also be read as an
    # INDEPENDENT confirmation on the items we had not seen (R-DPO7b2: raw 16,382 / clean 15,916).
    sp = slice_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), SLICE_FILE)
    if not os.path.isfile(sp): die("pinned slice id file missing: %s" % sp)
    with open(sp, "rb") as fh: sblob = fh.read()
    if hashlib.sha256(sblob).hexdigest() != SLICE_SHA256: die("slice id file does not match its pinned sha256")
    slice_ids = set(sblob.decode().split())
    if len(slice_ids) != SLICE_N: die("slice has %d ids, pinned %d" % (len(slice_ids), SLICE_N))
    if not slice_ids <= set("greekmmlu:%d" % i for i in range(full_n)): die("slice ids fall outside the raw frame")
    if slice_ids: print("250-item slice loaded: %d ids -> held-out raw %d, held-out clean %d\n"
                        % (len(slice_ids), full_n - len(slice_ids), clean_n - len(slice_ids & keep)))

    frame_blob = "".join("greekmmlu:%d\n" % i for i in range(full_n))
    if hashlib.sha256(frame_blob.encode()).hexdigest() != RAW_FRAME_SHA256: die("raw frame digest does not match the pinned one")
    ref_ids = set(frame_blob.split())
    if not keep <= ref_ids: die("clean ids are not a subset of the raw frame")
    res = {}
    for label, d in dirs.items():
        check_metadata(d, label, m)
        rows = read_predictions(d, label, full_n, ref_ids)
        absent = keep - set(rows)
        if absent: die("%s: %d clean manifest ids absent from predictions" % (label, len(absent)))
        rc = sum(rows.values())
        cc = sum(rows[i] for i in keep)
        e = {"raw_n": full_n, "raw_correct": rc, "raw_acc": rc / full_n,
             "clean_n": clean_n, "clean_correct": cc, "clean_acc": cc / clean_n,
             "protocol": "custom_full_text",      # NOT official GreekMMLU -- see the note below
             "manifest_sha": hashlib.sha256(open(man, "rb").read()).hexdigest()[:16],
             "id_digest": hashlib.sha256("\n".join(sorted(rows)).encode()).hexdigest()[:16]}
        if slice_ids:
            ho = set(rows) - slice_ids
            hoc = ho & keep
            e.update({"heldout_n": len(ho), "heldout_acc": sum(rows[i] for i in ho) / len(ho),
                      "heldout_clean_n": len(hoc), "heldout_clean_acc": sum(rows[i] for i in hoc) / len(hoc),
                      "slice_n": len(slice_ids & set(rows)),
                      "slice_acc": sum(rows[i] for i in (slice_ids & set(rows))) / len(slice_ids & set(rows))})
        res[label] = e
    print("%-18s %8s %10s   %8s %10s" % ("model", "raw n", "raw acc", "clean n", "clean acc"))
    print("-" * 62)
    for k, v in res.items():
        print("%-18s %8d %10.4f   %8d %10.4f" % (k, v["raw_n"], v["raw_acc"], v["clean_n"], v["clean_acc"]))
    if "parent" in res:
        p = res["parent"]
        print("\ndeltas vs parent, percentage points:")
        print("%-20s %9s %9s %12s %12s" % ("model", "raw", "clean", "the 250", "HELD OUT"))
        print("-" * 68)
        for k, v in res.items():
            if k == "parent": continue
            ho = ("%12.2f" % ((v["heldout_acc"] - p["heldout_acc"]) * 100)) if "heldout_acc" in v else "%12s" % "-"
            sl = ("%12.2f" % ((v["slice_acc"] - p["slice_acc"]) * 100)) if "slice_acc" in v else "%12s" % "-"
            print("%-20s %9.2f %9.2f %s %s" % (k, (v["raw_acc"] - p["raw_acc"]) * 100,
                  (v["clean_acc"] - p["clean_acc"]) * 100, sl, ho))
        print("\nThe 'HELD OUT' column excludes the 250 items already reported, so it is the only")
        print("column that is independent of the slice the original claim was made on.")
    else:
        print("\nWARNING: no 'parent' model -- no deltas computed")
    print("\nPROTOCOL: custom_full_text -- full choice text ranked by mean token log-probability.")
    print("This is NOT the official GreekMMLU label protocol; the same parent scores ~69.4% there")
    print("against ~54.2% here. These numbers are comparable to each other and to the 250-item")
    print("slice, and are NOT comparable to a published GreekMMLU figure.")
    out = out or os.path.join(root, "finalized.json")
    tmp = out + ".tmp"
    json.dump({"models": res, "manifest": {k: m.get(k) for k in
               ("schema_version", "status", "full_count", "clean_count", "dataset_repo_id", "dataset_revision", "dataset_split")}},
              open(tmp, "w"), indent=1)
    os.replace(tmp, out)              # atomic, and only after every model passed
    print("\nwrote %s: %d models, all validated" % (out, len(res)))

main()
