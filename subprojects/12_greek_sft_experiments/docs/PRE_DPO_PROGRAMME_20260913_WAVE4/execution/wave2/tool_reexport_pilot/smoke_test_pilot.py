#!/usr/bin/env python3
"""End-to-end synthetic smoke for the frozen pilot; no source corpus access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
TOKENIZER = Path('/Users/foivoskarounos-zamparloukos/.cache/huggingface/hub/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/b946d40447b2b597999b9c86d44bee0b452c919f')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    snapshot = root / 'snapshot'
    (snapshot / 'data').mkdir(parents=True)
    rows = []
    for i in range(40):
        functions = json.dumps([{'type': 'function', 'function': {'name': 'weather.lookup',
            'parameters': {'type': 'object', 'properties': {'city': {'type': 'string'}, 'days': {'type': 'integer'}},
                           'required': ['city', 'days'], 'additionalProperties': False}}}])
        rows.append({'id': f'synthetic-{i}', 'source_dataset': 'Dolci Instruct Tool Use', 'domain': 'Tool Use', 'messages': [
            {'role': 'system', 'content': 'Use the declared function.', 'functions': functions, 'function_calls': None},
            {'role': 'user', 'content': f'Forecast synthetic city {i}.', 'functions': None, 'function_calls': None},
            {'role': 'assistant', 'content': None, 'functions': None,
             'function_calls': f'weather.lookup(city="City {i}", days=3)'},
            {'role': 'environment', 'content': '{"temperature":20}', 'functions': None, 'function_calls': None},
            {'role': 'assistant', 'content': 'The synthetic result is 20 degrees.', 'functions': None, 'function_calls': None},
        ]})
    shard = snapshot / 'data/train-00000-of-00001.parquet'
    pq.write_table(pa.Table.from_pylist(rows), shard)
    selected = [{'source_revision': 'a' * 40,
                 'source_locator': {'file': 'data/train-00000-of-00001.parquet', 'row_group': 0, 'row_in_group': i},
                 'source_id': f'synthetic-{i}', 'selection_sha256': hashlib.sha256(str(i).encode()).hexdigest(),
                 'stratum': 'data/train-00000-of-00001.parquet'} for i in range(40)]
    inventory = {'source_revision': 'a' * 40, 'selected': selected, 'schema_fields': ['id','messages','source_dataset','domain'],
                 'selected_locator_sha256': hashlib.sha256(json.dumps(selected,sort_keys=True).encode()).hexdigest()}
    inv = root / 'source_inventory.json'; inv.write_text(json.dumps(inventory))
    impl = {}
    for key, path in {
        'export_core': HERE/'remote_bundle/frozen_science/export_core.py',
        'consumer': HERE/'remote_bundle/frozen_science/assemble_mix_r2.py',
        'vantage_scan': HERE/'remote_bundle/frozen_science/vantage_scan.py',
        'sft_train': HERE/'remote_bundle/frozen_science/sft_train.py',
    }.items(): impl[key] = {'path': str(path), 'sha256': sha(path)}
    contract = {'schema_version':'dolci_tool200_pilot_v1','target_rows':40,'max_tokens':4032,
        'source': {'dataset':'synthetic/dolci-shape','revision':'a'*40,'snapshot':str(snapshot),
                   'inventory_path':str(inv),'inventory_sha256':sha(inv),
                   'selected_shards':[{'file':'data/train-00000-of-00001.parquet','bytes':shard.stat().st_size,'sha256':sha(shard)}],
                   'required_source_dataset':'Dolci Instruct Tool Use'},
        'implementation':impl,
        'tokenizer': {'path':str(TOKENIZER),'files':{x:sha(TOKENIZER/x) for x in ('tokenizer.json','tokenizer_config.json','chat_template.jinja')}}}
    contract_path = root/'contract.json'; contract_path.write_text(json.dumps(contract))
    env = dict(os.environ, APERTUS_DATA_STAGE_RUN_ROOT=str(root/'run'), APERTUS_DATA_STAGE_ATTEMPT='1')
    completed = subprocess.run([sys.executable, str(HERE/'pilot_run.py'), '--contract', str(contract_path),
                                '--expected-contract-sha256', sha(contract_path)], env=env,
                               text=True, capture_output=True, check=False)
    if completed.returncode:
        print(completed.stdout); print(completed.stderr, file=sys.stderr); raise SystemExit(completed.returncode)
    receipt = json.loads((root/'run/receipts/tool200.json').read_text())
    assert receipt['status']=='passed' and receipt['structural_accept']==40 and receipt['candidate_accept']==40
    print('PASS synthetic-end-to-end', receipt['candidate_accept'])
