#!/usr/bin/env python3
"""Evaluator-side receipts for one scored model. Runs INSIDE the scoring environment, so what it records
is what that environment actually resolved -- not what a caller believes (R-DPO9 B1, B2).

  run_receipt.py geometry <model_dir>                      -> prints JSON: effective rotary settings + inv_freq digest
  run_receipt.py write <run_dir> <label> <weights_receipt.json> <scored_dir> <tokenizer_dir> <frozen_date> <config_mode>
"""
import glob, hashlib, json, os, sys

def geometry(model_dir):
    import transformers
    from transformers import AutoConfig
    from transformers.models.apertus.modeling_apertus import ApertusRotaryEmbedding
    c = AutoConfig.from_pretrained(model_dir)
    inv = ApertusRotaryEmbedding(config=c).inv_freq
    rp = getattr(c, "rope_parameters", None)
    return {"inv_freq_sha256": hashlib.sha256(inv.cpu().numpy().tobytes()).hexdigest(),
            "effective_rope_theta": float(getattr(c, "rope_theta", float("nan"))) if getattr(c, "rope_theta", None) is not None else None,
            "rope_scaling": getattr(c, "rope_scaling", None), "rope_parameters_key_present": rp is not None,
            "attention_scaling": float(getattr(ApertusRotaryEmbedding(config=c), "attention_scaling", 1.0)),
            "max_position_embeddings": getattr(c, "max_position_embeddings", None),
            "hidden_size": c.hidden_size, "num_hidden_layers": c.num_hidden_layers,
            "num_attention_heads": c.num_attention_heads, "transformers": transformers.__version__}

def effective_generation(model_dir, tok_dir):
    """What generation ACTUALLY uses, after every override (R-DPO10 finding 2). config.json's eos/use_cache
    fields are not it: generate() reads generation_config.json, and lm_eval's HFLM._model_generate passes
    use_cache=True unconditionally. EOS ids are a SET for stopping purposes ([2,68] == [68,2,68])."""
    from transformers import AutoTokenizer, GenerationConfig
    g = GenerationConfig.from_pretrained(model_dir)
    pad = AutoTokenizer.from_pretrained(tok_dir).pad_token_id      # lm_eval passes pad_token_id=self.tokenizer.pad_token_id, overriding the model's
    eos = g.eos_token_id; eos = sorted(set(eos if isinstance(eos, (list, tuple)) else [eos]))
    return {"eos_token_ids": eos, "bos_token_id": g.bos_token_id, "pad_token_id": pad, "pad_token_id_source": "tokenizer (lm_eval override)",
            "do_sample": bool(g.do_sample), "num_beams": g.num_beams, "repetition_penalty": g.repetition_penalty,
            "temperature": g.temperature if g.do_sample else None, "top_p": g.top_p if g.do_sample else None,
            "use_cache": True, "use_cache_source": "lm_eval HFLM._model_generate forces it"}

def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""): h.update(b)
    return h.hexdigest()

def write(run_dir, label, weights_receipt, scored_dir, tok_dir, date, cfg_spec, gen_kwargs="default"):
    with open(weights_receipt) as fh: w = json.load(fh)
    with open(os.path.join(scored_dir, "config.json")) as fh: cfg = json.load(fh)
    outs = sorted(glob.glob(os.path.join(run_dir, "**", "results_*.json"), recursive=True)
                  + glob.glob(os.path.join(run_dir, "**", "samples_*.jsonl"), recursive=True))
    if not outs: raise SystemExit("no outputs under %s" % run_dir)
    import lm_eval
    r = {"schema": "rlhf-run-receipt-v1", "label": label, "config_spec": cfg_spec, "gen_kwargs_override": gen_kwargs, "config_mode": cfg_spec.split(":")[0], "frozen_date": date,
         "weights_id": w["weights_id"], "weights_files": w["files"],
         "gen_config": effective_generation(scored_dir, tok_dir),
         "nominal_config_fields": {k: cfg.get(k) for k in ("eos_token_id", "pad_token_id", "bos_token_id", "use_cache")},
         "geometry": geometry(scored_dir),
         "tokenizer_sha256": _sha(os.path.join(tok_dir, "tokenizer.json")),
         "chat_template_sha256": _sha(os.path.join(tok_dir, "tokenizer_config.json")),
         "env": {"lm_eval": getattr(lm_eval, "__version__", None)},
         "outputs": {os.path.relpath(p, run_dir): _sha(p) for p in outs}}
    tmp = os.path.join(run_dir, "run_receipt.json.tmp")
    with open(tmp, "w") as fh: json.dump(r, fh, indent=1, sort_keys=True)
    os.replace(tmp, os.path.join(run_dir, "run_receipt.json"))
    print("receipt: %s  geometry %s  %d outputs" % (label, r["geometry"]["inv_freq_sha256"][:12], len(outs)))

if __name__ == "__main__":
    if sys.argv[1] == "geometry": print(json.dumps(geometry(sys.argv[2]), sort_keys=True))
    elif sys.argv[1] == "generation": print(json.dumps(effective_generation(sys.argv[2], sys.argv[3]), sort_keys=True))
    elif sys.argv[1] == "write": write(*sys.argv[2:10])
    else: raise SystemExit(__doc__)
