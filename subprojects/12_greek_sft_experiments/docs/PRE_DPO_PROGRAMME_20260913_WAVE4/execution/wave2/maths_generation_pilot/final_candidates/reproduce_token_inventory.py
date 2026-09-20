#!/usr/bin/env python3
"""Reproduce token_inventory.json without overwriting it; emit an environment receipt."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import platform
import sys

OUT = Path(__file__).resolve().parent
PROJECT = Path('/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments')
TOKENIZER_REVISION = 'c7f806e268083c64ce831bc46483bf98e5ddcee1'
TOKENIZER = Path('/Users/foivoskarounos-zamparloukos/.cache/huggingface/hub/models--fffoivos--apertus-8b-greek-cpt/snapshots') / TOKENIZER_REVISION
TEMPLATE = Path('/Users/foivoskarounos-zamparloukos/.cache/huggingface/hub/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/b946d40447b2b597999b9c86d44bee0b452c919f')

import torch
import tokenizers
import transformers
import trl

sys.path.insert(0, str(PROJECT / 'cluster'))
from sft_train import prepare_tokenizer, tokenize_messages  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


rows = [json.loads(x) for x in (OUT / 'candidate_rows.jsonl').read_text().split('\n') if x.strip()]
prior = json.loads((OUT / 'token_inventory.json').read_text())
tok, control_ids = prepare_tokenizer({
    'tokenizer_name_or_path': str(TOKENIZER),
    'template_source': str(TEMPLATE),
    'require_apertus_control_ids': True,
    'extend_control_tokens': False,
})
items = []
for row in rows:
    encoded = tokenize_messages(tok, row['messages'])
    chars = [len(m['content']) for m in row['messages']]
    words = [len(m['content'].split()) for m in row['messages']]
    items.append({
        'row_id': row['row_id'], 'candidate_class': row['candidate_class'],
        'input_tokens': len(encoded['input_ids']),
        'assistant_supervised_tokens': sum(encoded['assistant_masks']),
        'user_chars': chars[0], 'assistant_chars': chars[1],
        'user_whitespace_words': words[0], 'assistant_whitespace_words': words[1],
        'within_4096': len(encoded['input_ids']) <= 4096,
    })
totals = {k: sum(x[k] for x in items) for k in [
    'input_tokens', 'assistant_supervised_tokens', 'user_chars', 'assistant_chars',
    'user_whitespace_words', 'assistant_whitespace_words']}
ranges = {k: {'min': min(x[k] for x in items), 'max': max(x[k] for x in items)} for k in [
    'input_tokens', 'assistant_supervised_tokens', 'user_chars', 'assistant_chars',
    'user_whitespace_words', 'assistant_whitespace_words']}
comparisons = {
    'rows_match': len(rows) == prior['rows'],
    'items_match': items == prior['items'],
    'totals_match': totals == prior['totals'],
    'ranges_match': ranges == prior['ranges'],
    'all_within_4096_match': all(x['within_4096'] for x in items) == prior['all_within_4096'],
    'control_token_ids_match': control_ids == prior['tokenizer']['control_token_ids'],
    'vocab_size_match': len(tok) == prior['tokenizer']['vocab_size'],
}
receipt = {
    'schema_version': 'maths32_token_inventory_reproduction_v1',
    'created_at': datetime.now(timezone.utc).isoformat(),
    'status': 'pass' if all(comparisons.values()) else 'mismatch',
    'correction': 'The earlier bundled-runtime command pointer was incorrect; this receipt records the actual supported project environment used for reproduction.',
    'command': ['/Users/foivoskarounos-zamparloukos/venvs/sfttrain/bin/python', str(Path(__file__).resolve())],
    'environment': {
        'sys_executable': sys.executable,
        'python': platform.python_version(),
        'torch': torch.__version__,
        'transformers': transformers.__version__,
        'tokenizers': tokenizers.__version__,
        'trl': trl.__version__,
    },
    'bindings': {
        'candidate_rows_sha256': sha(OUT / 'candidate_rows.jsonl'),
        'prior_token_inventory_sha256': sha(OUT / 'token_inventory.json'),
        'canonical_sft_train_path': str(PROJECT / 'cluster/sft_train.py'),
        'canonical_sft_train_sha256': sha(PROJECT / 'cluster/sft_train.py'),
        'tokenizer_json_sha256': sha(TOKENIZER / 'tokenizer.json'),
        'tokenizer_config_sha256': sha(TOKENIZER / 'tokenizer_config.json'),
        'template_tokenizer_config_sha256': sha(TEMPLATE / 'tokenizer_config.json'),
    },
    'comparisons': comparisons,
    'measured': {'rows': len(items), 'totals': totals, 'ranges': ranges, 'vocab_size': len(tok), 'control_token_ids': control_ids},
}
(OUT / 'token_reproduction_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
if receipt['status'] != 'pass':
    raise SystemExit('reproduction mismatch')
print(json.dumps(receipt, ensure_ascii=False, indent=2))
