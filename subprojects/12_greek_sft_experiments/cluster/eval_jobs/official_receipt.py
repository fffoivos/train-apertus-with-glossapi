#!/usr/bin/env python3
"""Evaluator-side receipt for one official-protocol GreekMMLU result (R-DPO10 finding 1). Run ON THE CLUSTER,
next to the weights: it hashes the result file and the weight shards the scored directory RESOLVES to, so the
result is bound to the bytes that produced it rather than to a label a caller supplies.
  official_receipt.py <result.json> <out_receipt.json>        (python 3.6 compatible)"""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from weights_receipt import receipt, _sha256

def main(result, out):
    with open(result) as fh: d = json.load(fh)
    mp = d["model_path"]
    if not os.path.isdir(mp): raise SystemExit("scored directory no longer exists: %s" % mp)
    cfg = _sha256(os.path.join(mp, "config.json"))
    if cfg != d.get("model_config_sha256"): raise SystemExit("config.json under %s is not the one that was scored" % mp)
    w = receipt(mp)
    r = {"schema": "rlhf-official-receipt-v1", "label": d["model_label"], "result_sha256": _sha256(result),
         "model_path": mp, "model_config_sha256": cfg, "weights_id": w["weights_id"], "weights_files": w["files"],
         "weights_resolved_dir": os.path.dirname(os.path.realpath(os.path.join(mp, w["files"][0]["name"])))}
    tmp = out + ".tmp"
    with open(tmp, "w") as fh: json.dump(r, fh, indent=1, sort_keys=True)
    os.rename(tmp, out); print("%s %s -> %s" % (r["label"], r["weights_id"], r["weights_resolved_dir"]))

if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
