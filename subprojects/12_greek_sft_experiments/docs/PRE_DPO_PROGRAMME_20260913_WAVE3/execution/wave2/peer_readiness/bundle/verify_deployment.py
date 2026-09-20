#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

root=Path(__file__).resolve().parent
manifest=json.loads((root/"peer_eval_science_manifest.json").read_text())
payload=hashlib.sha256()
for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "peer_eval_science_manifest.json"):
    data=path.read_bytes(); digest=hashlib.sha256(data).hexdigest()
    payload.update(str(path.relative_to(root)).encode()+b"\0"+str(len(data)).encode()+b"\0"+digest.encode()+b"\n")
observed=payload.hexdigest()
if observed != manifest["payload_sha256"]:
    raise SystemExit(f"payload drift: {observed}")
print(json.dumps({"status":"passed","payload_sha256":observed,"root":str(root)}))
