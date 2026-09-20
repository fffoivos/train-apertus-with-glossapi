#!/usr/bin/env python3
"""Accept an official-protocol GreekMMLU result only if it is exactly what it claims (R-DPO8b finding 5).
A row count is not validation: this checks the pinned dataset, the exact frame, the protocol, the
scoring settings, strict booleans, the model it was scored from, and recomputes the accuracy.
Usage: validate_official_result.py <result.json> <label> <expected_model_path> <expected_model_config_sha256>"""
import hashlib, json, math, os, sys
PARQUET_SHA256 = "18e9ac12b1ecc6a02ef94ecbc5117bcf7ab60d498fc752a775892253b5fd5f59"   # pinned GreekMMLU All/test projection
RAW_FRAME_SHA256 = "110733ffb6c55f51"          # prefix of sha256("greekmmlu:0\n...greekmmlu:16631\n"), as in finalize_greekmmlu_full.py
N = 16632
GOLD_SHA256 = "9cd8b41b97fbe4f6b2143397c8743be4e0983cb47e8cdaf540ba93c85ea4ea24"   # cluster/eval_jobs/greekmmlu_gold.tsv: id, gold index, n choices -- from the pinned projection
def die(m): print("INVALID: " + m); sys.exit(1)
path, label, model_path, config_sha = sys.argv[1:5]
gp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "greekmmlu_gold.tsv")
gblob = open(gp, "rb").read()
if hashlib.sha256(gblob).hexdigest() != GOLD_SHA256: die("gold file does not match its pinned sha256")
GOLD = {l.split("\t")[0]: (int(l.split("\t")[1]), int(l.split("\t")[2])) for l in gblob.decode().splitlines()}
d = json.load(open(path))
if d.get("schema_version") != "greekmmlu_full_dual_protocol_v1": die("schema %r" % d.get("schema_version"))
if d.get("model_label") != label: die("label %r, expected %r" % (d.get("model_label"), label))
if d.get("model_path") != model_path: die("scored from %r, expected %r" % (d.get("model_path"), model_path))
if len(config_sha) != 64 or d.get("model_config_sha256") != config_sha: die("model_config_sha256 %r is not the staged config's %r" % (d.get("model_config_sha256"), config_sha))
if d.get("parquet_sha256") != PARQUET_SHA256: die("dataset sha %r is not the pinned one" % d.get("parquet_sha256"))
if d.get("dtype") != "float32" or d.get("chat_template_applied") is not False or d.get("max_input_tokens") != 3072:
    die("scoring settings: dtype=%r chat_template_applied=%r max_input_tokens=%r" % (d.get("dtype"), d.get("chat_template_applied"), d.get("max_input_tokens")))
if sorted(d.get("accuracy", {})) != ["official_label"]: die("protocols present: %r" % sorted(d.get("accuracy", {})))
rows = d.get("rows") or []
ids = [str(r.get("example_id")) for r in rows]
if len(ids) != N or len(set(ids)) != N: die("%d rows, %d unique; expected %d" % (len(ids), len(set(ids)), N))
frame = "".join("greekmmlu:%d\n" % i for i in range(N))
if not hashlib.sha256(frame.encode()).hexdigest().startswith(RAW_FRAME_SHA256): die("internal: frame pin mismatch")
if set(ids) != set(frame.split()): die("ids are not exactly the pinned raw frame")
ROW_KEYS = {"example_id", "subject", "level", "answer_index", "official_label"}
isint = lambda v: isinstance(v, int) and not isinstance(v, bool)
correct = 0
for r in rows:
    if set(r) != ROW_KEYS: die("row %s has keys %s; only the official protocol may be present" % (r.get("example_id"), sorted(r)))
    o = r["official_label"]
    if not (isinstance(o, dict) and set(o) == {"pred_index", "correct"} and isinstance(o["correct"], bool) and isint(o["pred_index"]) and isint(r["answer_index"])):
        die("row %s malformed" % r.get("example_id"))
    gold, nch = GOLD[str(r["example_id"])]
    if r["answer_index"] != gold: die("row %s: gold answer %r is not the pinned %r" % (r["example_id"], r["answer_index"], gold))
    if not 0 <= o["pred_index"] < nch: die("row %s: prediction %r outside its %d choices" % (r["example_id"], o["pred_index"], nch))
    if o["correct"] != (o["pred_index"] == r["answer_index"]): die("row %s: correct flag contradicts pred/answer" % r["example_id"])
    correct += o["correct"]
acc = d["accuracy"]["official_label"]
if not (isinstance(acc, float) and math.isfinite(acc) and 0.0 <= acc <= 1.0): die("reported accuracy %r is not a finite number in [0, 1]" % (acc,))
if abs(correct / float(N) - acc) > 1e-12: die("accuracy %r does not equal recomputed %r" % (d["accuracy"]["official_label"], correct / float(N)))
print("%s %d %.6f valid" % (label, N, correct / float(N)))
