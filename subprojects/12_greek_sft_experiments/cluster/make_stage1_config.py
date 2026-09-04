#!/usr/bin/env python3
"""Derive the stage-1 training config from the assembly receipt (review R7): 1 epoch, cosine, lr 1e-5, real token count.
Usage: python3 cluster/make_stage1_config.py <arm> [base_yaml=cluster/configs/E1_lr1e-5_3ep_const.yaml]
Writes cluster/configs/<arm>.yaml by textual substitution (no yaml module needed on the Mac)."""
import json, sys, re
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; arm = sys.argv[1]; base = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / 'cluster/configs/E1_lr1e-5_3ep_const.yaml'
rec = json.load(open(HERE / 'data/arms' / arm / 'receipt.json'))
if rec.get('tokenizer') != 'exact': raise SystemExit('receipt is not from an exact-tokenizer run; refuse to derive a training config from an estimate')
if rec.get('post_scan_identity_hits', 1) != 0: raise SystemExit('post-scan identity hits are not zero')
tokens = rec['train']['tokens']; rows = rec['train']['rows']
text = base.read_text()
def setkey(t, key, value):
    if re.search(rf'^{key}:', t, re.M): return re.sub(rf'^{key}:.*$', f'{key}: {value}', t, flags=re.M)
    return t + f'\n{key}: {value}\n'
text = setkey(text, 'run_name', f'{arm}_lr1e-5_1ep_cos'); text = setkey(text, 'arm', arm)
text = setkey(text, 'train_file', f'data/arms/{arm}/train.jsonl'); text = setkey(text, 'eval_file', f'data/arms/{arm}/dev.jsonl')
text = setkey(text, 'num_train_epochs', 1); text = setkey(text, 'lr_scheduler_type', 'cosine'); text = setkey(text, 'learning_rate', '1.0e-5')
text = setkey(text, 'expected_train_tokens', tokens); text = setkey(text, 'expected_train_rows', rows)
text = re.sub(r'^max_steps:.*$\n?', '', text, flags=re.M)  # epochs drive the length, not a fixed step count
out = HERE / 'cluster/configs' / f'{arm}.yaml'; out.write_text(text)
nh = tokens / 26e6; print(f'{out}: {rows} rows, {tokens/1e6:.1f}M tokens, 1 epoch ≈ {nh:.1f} node-hours ≈ CHF {nh*2.69:.1f}')
