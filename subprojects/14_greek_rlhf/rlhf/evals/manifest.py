"""What a result IS. A score without a manifest is not a result.

Every failure of 19 September was two numbers being compared that were not the same measurement:
a different prompt (the date line), a different protocol (custom_full_text vs official labels), a
different item population (16,632 raw vs 16,159 clean), a different generation config. A manifest
records all of them, so `compare()` can refuse instead of a reviewer finding out a day later.
"""
import glob, hashlib, json, os, re
from .weights import load_receipt
from .result import Result, _BUILDER

# Two results may be compared only if they agree on every one of these, except the keys the caller
# explicitly declares as the variable under test. `weights_id` is normally that variable.
IDENTITY_KEYS = ("benchmark", "protocol", "metric", "item_digest", "prompt_digest", "gen_config",
                 "gen_kwargs", "runtime", "geometry", "tokenizer_sha", "harness", "weights_id")

# Keys a runner genuinely cannot record, by protocol. The BUILDER declares them; a caller cannot
# (R-DPO8 finding 1: an open `allow_unknown` let any caller wave any unknown through).
UNRECORDABLE_BY_PROTOCOL = {
    "custom_full_text": ("prompt_digest", "gen_config", "gen_kwargs", "runtime", "tokenizer_sha", "geometry"),
    "official_label":   ("prompt_digest", "gen_config", "gen_kwargs", "tokenizer_sha", "geometry"),
}

_DATE = re.compile(r"(Current date: )\d{4}-\d{2}-\d{2}")

def _sha(parts):
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8") if isinstance(p, str) else p); h.update(b"\x00")
    return h.hexdigest()[:16]

class RunManifest(dict):
    """A plain dict with a fixed vocabulary, so it serialises and diffs trivially."""
    def identity(self):
        return {k: self.get(k) for k in IDENTITY_KEYS}
    def save(self, path):
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self, f, indent=1, sort_keys=True)
        os.replace(tmp, path)
    @classmethod
    def load(cls, path):
        return cls(json.load(open(path)))

def _canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

_ADDR = re.compile(r"(<[^<>]*?) at 0x[0-9a-fA-F]+(>)")

def _stable(obj):
    """Strip the volatile part of a callable's repr, keeping everything that identifies it.

    R-DPO11 finding 1: lm_eval serialises task callables as
        functools.partial(<function process_docs at 0xfff4ec604180>, category='Business')
    and the address differs between processes, so two runs of the SAME task got different digests and
    compare() refused all 36 Global-MMLU lanes -- the very comparison the re-score exists to make.
    The address goes; the function NAME and the partial's arguments (category='Business') stay, so a
    genuinely different task still differs. Limit (R-DPO12): a Python repr carries neither module nor code
    identity, so two same-named functions from different modules normalise alike. Adequate while the task
    implementation is fixed; comparing across task-code revisions needs a task-source digest as well.
    """
    if isinstance(obj, str):
        return _ADDR.sub(r"\1\2", obj)
    if isinstance(obj, dict):
        return {k: _stable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_stable(v) for v in obj]
    return obj

def _pathless(task_cfg):
    """lm_eval copies model_args into each task's metadata, so two runs of different checkpoints never
    share a task config byte-for-byte. `pretrained` and `tokenizer` there are PATHS, not identity: the
    weights are bound by their content receipt, the tokenizer by its hash and by the request digest.
    Exactly those two fields are dropped; dtype and everything else in the metadata stay bound."""
    c = dict(task_cfg); md = c.get("metadata")
    if isinstance(md, dict):
        c["metadata"] = {k: v for k, v in md.items() if k not in ("pretrained", "tokenizer")}
    return _stable(c)

def _request(row):
    """Everything the harness sent for this item: the rendered prompt, loglikelihood continuations,
    AND the nested per-request generation options (stop sequences, max_gen_toks, sampling). R-DPO8
    finding 2: hashing only the string arguments let a changed max_gen_toks through."""
    args = row.get("arguments")
    if not args:
        return None
    return _canon(args)

def _file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()

def _run_receipt(run_dir):
    """The evaluator's own account of what it scored (cluster/eval_jobs/run_receipt.py), written inside
    the scoring environment AFTER scoring: weights id, generation config, the EFFECTIVE rotary geometry
    that environment resolved, tokenizer hash, and a hash of every output file. R-DPO9 B2: identity used
    to arrive as builder arguments, so a caller could seal the parent's config onto an arm, or an arm's
    weights receipt onto the parent's outputs. Nothing about identity is an argument any more, and the
    receipt is refused unless the files on disk are the ones it hashed."""
    p = os.path.join(run_dir, "run_receipt.json")
    if not os.path.isfile(p):
        raise ValueError("%s has no run_receipt.json: a run scored before receipts existed has no verified "
                         "identity and cannot enter a comparison (re-score it)" % run_dir)
    with open(p) as fh:
        r = json.load(fh)
    if r.get("schema") != "rlhf-run-receipt-v1":
        raise ValueError("unknown run receipt schema %r" % r.get("schema"))
    load_receipt({"weights_id": r.get("weights_id"), "files": r.get("weights_files")})   # self-consistent weights id
    outs = r.get("outputs") or {}
    if not outs:
        raise ValueError("run receipt lists no outputs")
    for rel, want in outs.items():
        f = os.path.join(run_dir, rel)
        if not os.path.isfile(f) or _file_sha(f) != want:
            raise ValueError("run receipt does not match the files on disk: %s" % rel)
    g = r.get("geometry") or {}
    if not (isinstance(g.get("inv_freq_sha256"), str) and len(g["inv_freq_sha256"]) == 64):
        raise ValueError("run receipt carries no effective geometry")
    return r

def from_lm_eval(run_dir, task, metric):
    """Sealed Result for one lane of an lm_eval --log_samples run. Takes NO identity arguments."""
    rcpt = _run_receipt(run_dir)
    label, gen_config, tokenizer_sha = rcpt["label"], rcpt["gen_config"], rcpt["tokenizer_sha256"][:16]
    wr = {"weights_id": rcpt["weights_id"], "resolved_dir": None}
    fs = sorted(glob.glob(os.path.join(run_dir, "**", "samples_%s_*.jsonl" % task), recursive=True))
    if len(fs) != 1:
        raise ValueError("%s: expected exactly one samples file for %s, found %d" % (label, task, len(fs)))
    rs = sorted(glob.glob(os.path.join(run_dir, "**", "results_*.json"), recursive=True))
    if len(rs) != 1:
        raise ValueError("%s: expected exactly one results file, found %d" % (label, len(rs)))
    for f in (fs[0], rs[0]):
        if os.path.relpath(f, run_dir) not in rcpt["outputs"]:
            raise ValueError("%s: %s is not among the receipted outputs" % (label, os.path.relpath(f, run_dir)))
    with open(rs[0]) as fh:
        res = json.load(fh)
    items, records, requests, dateless, dates = {}, [], [], [], set()
    with open(fs[0]) as fh:
        lines = [l for l in fh if l.strip()]
    for line in lines:
        r = json.loads(line)
        iid = str(r["doc_id"])
        if iid in items:
            raise ValueError("%s: duplicate doc_id %s" % (label, iid))
        v = r.get(metric)
        if isinstance(v, float) and v in (0.0, 1.0):
            v = bool(v)
        if not isinstance(v, bool):
            raise ValueError("%s: item %s has %s=%r, expected a 0/1 outcome" % (label, iid, metric, v))
        items[iid] = v
        # item identity binds the id to the DOCUMENT and its GOLD, recomputed here rather than
        # trusted from the row's own hash fields (R-DPO8 finding 4)
        if "doc" not in r or "target" not in r:
            raise ValueError("%s: item %s lacks doc/target; cannot bind its identity" % (label, iid))
        records.append("%s|%s|%s" % (iid, _sha([_canon(r["doc"])]), _sha([_canon(r["target"])])))
        req = _request(r)
        if req is None:
            raise ValueError("%s: item %s carries no request" % (label, iid))
        requests.append(iid + "\x02" + req)
        dateless.append(iid + "\x02" + _DATE.sub(r"\g<1>YYYY-MM-DD", req))
        dates.update(m.group(0)[len("Current date: "):] for m in _DATE.finditer(req))
    cfg = (res.get("configs") or {}).get(task)
    if cfg is None:
        raise ValueError("%s: results file has no config for task %s" % (label, task))
    rc = res.get("config") or {}
    runtime = {"model_dtype": rc.get("model_dtype"), "batch_size": rc.get("batch_size"), "limit": rc.get("limit"),
               "seeds": [rc.get("random_seed"), rc.get("numpy_seed"), rc.get("torch_seed"), rc.get("fewshot_seed")],
               "cli_gen_kwargs": rc.get("gen_kwargs"), "n_shot": (res.get("n-shot") or {}).get(task),
               "task_hash": (res.get("task_hashes") or {}).get(task), "task_version": (res.get("versions") or {}).get(task),
               "task_config": _sha([_canon(_pathless(cfg))]), "fewshot_as_multiturn": res.get("fewshot_as_multiturn"),
               "system_instruction_sha": res.get("system_instruction_sha"), "max_length": res.get("max_length")}
    m = RunManifest(label=label, weights_id=wr["weights_id"], benchmark=task, metric=metric,
                    protocol="lm_eval:%s" % task, n_items=len(items),
                    item_digest=_sha(sorted(records)), prompt_digest=_sha(sorted(requests)),
                    prompt_digest_dateless=_sha(sorted(dateless)), prompt_dates=sorted(dates),
                    gen_config=gen_config, gen_kwargs=cfg.get("generation_kwargs") or {}, runtime=runtime,
                    geometry={k: rcpt["geometry"].get(k) for k in ("inv_freq_sha256", "max_position_embeddings",
                              "hidden_size", "num_hidden_layers", "num_attention_heads")},
                    tokenizer_sha=tokenizer_sha, unrecordable=[], frozen_date=rcpt.get("frozen_date"),
                    config_mode=rcpt.get("config_mode"),
                    harness={"lm_eval": res.get("lm_eval_version"), "transformers": res.get("transformers_version")},
                    provenance={"chat_template_sha": res.get("chat_template_sha"), "weights_dir": wr.get("resolved_dir"),
                                "model_args": rc.get("model_args")},
                    source=os.path.relpath(fs[0]))
    return Result(m, items, _token=_BUILDER)

def _legacy_native_mcq(run_dir, label, weights, keep_ids=None, population="raw"):
    """Manifest + outcomes from the native GreekMMLU runner. The protocol is named for what it is:
    full choice text ranked by mean token log-probability -- NOT the official label protocol, which
    scores the same parent about 15 points higher. Prompts are not retained by this runner, so
    `prompt_digest` is None and `compare()` will demand that be acknowledged explicitly."""
    wr = load_receipt(weights)
    fs = glob.glob(os.path.join(run_dir, "*_native_mcq_predictions.jsonl"))
    if len(fs) != 1:
        raise ValueError("%s: expected exactly one prediction file, found %d" % (label, len(fs)))
    with open(os.path.join(run_dir, "run_metadata.json")) as fh:
        md = json.load(fh)
    items = {}
    with open(fs[0]) as fh:
        lines = [l for l in fh if l.strip()]
    for line in lines:
        r = json.loads(line); iid = str(r["example_id"])
        if iid in items:
            raise ValueError("%s: duplicate example_id %s" % (label, iid))
        if not isinstance(r["correct"], bool):
            raise ValueError("%s: item %s has non-boolean correct=%r" % (label, iid, r["correct"]))
        if keep_ids is None or iid in keep_ids:
            items[iid] = r["correct"]
    b = (md.get("dataset_bindings") or [{}])[0]
    m = RunManifest(label=label, weights_id=wr["weights_id"], benchmark="greekmmlu", metric="correct",
                    protocol="custom_full_text", population=population, n_items=len(items),
                    item_digest=_sha(sorted(items)), prompt_digest=None, prompt_dates=[],
                    gen_config=None, gen_kwargs=None, runtime=None, geometry=None, tokenizer_sha=None,
                    unrecordable=list(UNRECORDABLE_BY_PROTOCOL["custom_full_text"]), provenance_class="caller-asserted",
                    harness={"runner": md.get("schema"), "dtype": md.get("dtype"),
                             "max_input_tokens": md.get("max_input_tokens"),
                             "dataset": "%s@%s" % (b.get("source"), (b.get("revision") or "")[:12]),
                             "sample_size": md.get("sample_size"), "random_state": md.get("random_state")},
                    source=os.path.relpath(fs[0]))
    return Result(m, items, _token=_BUILDER)

def from_official_greekmmlu(path, *, keep_ids=None, population="raw"):
    """Sealed Result from cluster/eval_jobs/greekmmlu_official.py (official A/B/G/D label protocol, no chat
    template, so no date). Takes NO identity arguments (R-DPO10 finding 1): label and weights come from
    `<path>.receipt.json`, written on the cluster by official_receipt.py, which hashes this result file and
    the weight shards the scored directory resolves to. The same result file can therefore never be
    presented as two different models."""
    rp = path + ".receipt.json"
    if not os.path.isfile(rp):
        raise ValueError("%s has no evaluator receipt (%s): its weights identity is unverified" % (path, os.path.basename(rp)))
    with open(rp) as fh:
        rc = json.load(fh)
    if rc.get("schema") != "rlhf-official-receipt-v1":
        raise ValueError("unknown official receipt schema %r" % rc.get("schema"))
    if _file_sha(path) != rc.get("result_sha256"):
        raise ValueError("receipt is for a different result file than %s" % path)
    wr = load_receipt({"weights_id": rc.get("weights_id"), "files": rc.get("weights_files")})
    with open(path) as fh:
        d = json.load(fh)
    label = rc["label"]
    if d.get("model_label") != label or d.get("model_path") != rc.get("model_path") or d.get("model_config_sha256") != rc.get("model_config_sha256"):
        raise ValueError("%s: result and receipt disagree about what was scored" % label)
    if d.get("chat_template_applied") is not False:
        raise ValueError("%s: official_label must be template-free" % label)
    items = {}
    for r in d["rows"]:
        iid = str(r["example_id"]); c = r["official_label"]["correct"]
        if iid in items or not isinstance(c, bool):
            raise ValueError("%s: bad row %s" % (label, iid))
        if keep_ids is None or iid in keep_ids:
            items[iid] = c
    m = RunManifest(label=label, weights_id=wr["weights_id"], benchmark="greekmmlu", metric="correct",
                    protocol="official_label", population=population, n_items=len(items),
                    item_digest=_sha(sorted("%s|%s" % (str(r["example_id"]), r["answer_index"]) for r in d["rows"]
                                            if keep_ids is None or str(r["example_id"]) in keep_ids)),
                    prompt_digest=None, prompt_dates=[], gen_config=None, gen_kwargs=None,
                    runtime={"dtype": d.get("dtype"), "max_input_tokens": d.get("max_input_tokens"),
                             "chat_template_applied": False}, geometry=None, tokenizer_sha=None,
                    unrecordable=list(UNRECORDABLE_BY_PROTOCOL["official_label"]),
                    harness={"runner": d.get("schema_version"), "dataset_sha256": d.get("parquet_sha256")},
                    provenance={"model_path": d.get("model_path"), "model_config_sha256": d.get("model_config_sha256")},
                    source=os.path.relpath(path))
    return Result(m, items, _token=_BUILDER)
