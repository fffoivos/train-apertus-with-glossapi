"""A checkpoint's identity is its bytes, not the label someone gave it (R-DPO8 finding 3).

receipt(dir) digests every weight shard by RESOLVED path content: a staged directory of symlinks has
the same identity as the checkpoint it points into, and two different checkpoints can never share
one. Runs on the cluster's system python (3.6), so no f-strings-with-=, no dataclasses.

  python3 weights.py <out_dir> <model_dir> [<model_dir> ...]
"""
import hashlib, json, os, sys

def _is_weight(n):
    # model weights only: scheduler.pt / training_args.bin / rng_state*.pth are optimiser state, not the model
    return n.endswith(".safetensors") or (n.startswith("pytorch_model") and n.endswith(".bin"))

def _sha256(path, buf=16 * 1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def _id_of(files):
    canon = json.dumps([[f["name"], f["bytes"], f["sha256"]] for f in files], sort_keys=True)
    return "w:" + hashlib.sha256(canon.encode()).hexdigest()[:24]

def receipt(model_dir):
    names = sorted(n for n in os.listdir(model_dir) if _is_weight(n) or n.endswith(".index.json"))
    shards = [n for n in names if _is_weight(n)]
    if not shards:
        raise ValueError("no weight shards under %s" % model_dir)
    files = []
    for n in names:
        real = os.path.realpath(os.path.join(model_dir, n))
        files.append({"name": n, "bytes": os.path.getsize(real), "sha256": _sha256(real)})
    return {"weights_id": _id_of(files), "n_shards": len(shards),
            "total_bytes": sum(f["bytes"] for f in files), "files": files,
            "resolved_dir": os.path.realpath(model_dir)}

def load_receipt(obj):
    """Accept a receipt dict or a path to one; REFUSE a bare label."""
    if isinstance(obj, str):
        if not os.path.isfile(obj):
            raise ValueError("weights must be a content receipt (dict or path to receipt json), not the label %r" % obj)
        with open(obj) as fh:
            obj = json.load(fh)
    files = (obj or {}).get("files")
    if not (isinstance(files, list) and files and all(isinstance(f, dict) and isinstance(f.get("sha256"), str)
            and len(f["sha256"]) == 64 and isinstance(f.get("bytes"), int) and f.get("name") for f in files)):
        raise ValueError("not a weights receipt: %r" % (obj,))
    # R-DPO8b finding 2: the id is RECOMPUTED from the listed shard hashes. A receipt whose id was
    # edited -- one checkpoint relabelled as another -- no longer matches its own files.
    if obj.get("weights_id") != _id_of(files):
        raise ValueError("weights receipt is not self-consistent: id %r does not match its files" % obj.get("weights_id"))
    return obj

if __name__ == "__main__":
    out = sys.argv[1]
    if not os.path.isdir(out):
        os.makedirs(out)
    for d in sys.argv[2:]:
        r = receipt(d)
        key = hashlib.sha256(os.path.abspath(d).encode()).hexdigest()[:16]
        tmp = os.path.join(out, key + ".json.tmp")
        with open(tmp, "w") as fh:
            json.dump(dict(r, requested_dir=os.path.abspath(d)), fh, indent=1)
        os.rename(tmp, os.path.join(out, key + ".json"))
        print("%s  %s  %.1f GB  %s" % (r["weights_id"], r["n_shards"], r["total_bytes"] / 1e9, d))
