#!/usr/bin/env python3
"""Isolated validation for export_core_lossless.patch; does not fetch or rewrite corpus data."""
import ast
import json
import re
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = Path('/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments')
CANDIDATE = HERE / 'export_core_lossless_candidate.py'
PATCH = HERE / 'export_core_lossless.patch'

if (PROJECT / 'data/export_core.py').read_bytes() != CANDIDATE.read_bytes():
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=PROJECT, check=True)
tree = ast.parse(CANDIDATE.read_text(encoding='utf-8'))
wanted = {'_json_text', '_tag', '_export_turn', '_export_row', '_source_id', '_prepare_output', 'revision_for'}
defs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
assert {node.name for node in defs} == wanted

def text_of(content):
    if content is None: return ''
    if isinstance(content, str): return content
    if isinstance(content, dict) and content.get('text'): return content['text']
    return ''

ns = {'json': json, 're': re, 'text_of': text_of, 'os': __import__('os'),
      'TOOL_FIELDS': ('functions', 'function_calls', 'tool_calls', 'tool_call_id', 'name'),
      'SOURCE_REVISIONS': {'allenai/Dolci-Instruct-SFT': 'a' * 40}}
exec(compile(ast.Module(body=defs, type_ignores=[]), str(CANDIDATE), 'exec'), ns)

# A schema longer than the old 1,500-character cap must survive in native and text forms.
long_schema = [{'type': 'function', 'function': {'name': 'long.lookup', 'description': 'x' * 2400,
                'parameters': {'type': 'object', 'properties': {'q': {'type': 'string'}}, 'required': ['q']}}}]
system = ns['_export_turn']({'role': 'system', 'content': 'Use tools.', 'functions': long_schema})
assert system['functions'] == long_schema
assert len(system['content'].split('<functions>\n', 1)[1].rsplit('\n</functions>', 1)[0]) > 1500
assert system['content'].endswith('\n</functions>')

# Both function_calls and tool_calls retain long arguments, call IDs and all native objects.
long_args = json.dumps({'query': 'Ω' * 1800}, ensure_ascii=False)
tool_calls = [{'id': 'call_007', 'type': 'function',
               'function': {'name': 'long.lookup', 'arguments': long_args}}]
assistant = ns['_export_turn']({'role': 'assistant', 'content': '', 'tool_calls': tool_calls})
assert assistant['tool_calls'] == tool_calls
assert 'call_007' in assistant['content'] and len(assistant['content']) > 1500
legacy_calls = [{'name': 'legacy.lookup', 'arguments': {'query': 'z' * 1800}}]
legacy = ns['_export_turn']({'role': 'assistant', 'content': '', 'function_calls': legacy_calls})
assert legacy['function_calls'] == legacy_calls and len(legacy['content']) > 1500

# Mixed ordinary text plus all supported call representations must preserve both.
block_content = {'text': 'I will call the tools now.',
                 'blocks': [{'kind': 'calls', 'calls': [{'id': 'block_9', 'name': 'block.lookup'}]}]}
mixed = ns['_export_turn']({'role': 'assistant', 'content': block_content,
                            'function_calls': legacy_calls, 'tool_calls': tool_calls})
assert mixed['native_content'] == block_content
assert mixed['block_calls'] == block_content['blocks']
assert mixed['content'].startswith('I will call the tools now.\n<function_calls>\n')
mixed_payload = json.loads(mixed['content'].split('<function_calls>\n', 1)[1].split('\n</function_calls>', 1)[0])
assert set(mixed_payload) == {'function_calls', 'tool_calls', 'block_calls'}
assert mixed_payload['tool_calls'][0]['id'] == 'call_007'

# Missing optional fields stay missing rather than being fabricated.
plain = ns['_export_turn']({'role': 'user', 'content': 'hello'})
assert plain == {'role': 'user', 'content': 'hello'}
assert ns['_source_id']({'id': 0, 'conversation_id': 99}, 7) == 0
assert ns['_source_id']({'conversation_id': 0}, 7) == 0

# Refuse a nonempty output directory, while allowing a new/empty destination.
with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    empty = base / 'empty'; empty.mkdir(); ns['_prepare_output'](str(empty))
    occupied = base / 'occupied'; occupied.mkdir(); (occupied / 'sentinel').write_text('keep')
    try:
        ns['_prepare_output'](str(occupied))
    except SystemExit:
        pass
    else:
        raise AssertionError('nonempty output directory did not fail closed')

# Native result content and call identifiers survive a JSONL roundtrip exactly.
result_obj = {'ok': True, 'items': [{'id': 1}, {'id': 2}], 'note': None}
tool_result = ns['_export_turn']({'role': 'tool', 'content': result_obj,
                                  'tool_call_id': 'call_007', 'name': 'long.lookup'})
row = ns['_export_row']('dolci_tooluse', 'Tool Use', 73, 'u', 'a',
                        [system, assistant, tool_result], 'a' * 40,
                        {'file': 'train-000.parquet', 'row_group': 4, 'row_in_group': 9})
roundtrip = json.loads(json.dumps(row, ensure_ascii=False))
assert roundtrip['id'] == '73' and roundtrip['source_id'] == 73
assert roundtrip['turns'][0]['functions'] == long_schema
assert roundtrip['turns'][1]['tool_calls'] == tool_calls
assert roundtrip['turns'][2]['native_content'] == result_obj
assert roundtrip['turns'][2]['tool_call_id'] == 'call_007'
assert roundtrip['source_revision'] == 'a' * 40

# Exercise the actual current consumer. It strips native fields, so their JSON
# equivalents must still be present in rendered message content.
consumer_tree = ast.parse((PROJECT / 'data/assemble_mix_r2.py').read_text(encoding='utf-8'))
consumer_def = next(n for n in consumer_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'to_messages')
consumer_ns = {'GREEK_EDITS': {}}
exec(compile(ast.Module(body=[consumer_def], type_ignores=[]), 'assemble_mix_r2.py', 'exec'), consumer_ns)
rendered = consumer_ns['to_messages']({'turns': [system, {'role': 'user', 'content': 'go'}, mixed,
                                                     tool_result, {'role': 'assistant', 'content': 'done'}]}, 'dolci_tooluse')
assert rendered is not None
rendered_text = '\n'.join(m['content'] for m in rendered)
assert 'x' * 2400 in rendered_text and 'Ω' * 1800 in rendered_text
assert 'call_007' in rendered_text and 'block_9' in rendered_text
assert 'tool_call_id' in rendered_text and result_obj == tool_result['native_content']
assert all(set(m) <= {'role', 'content', 'train'} for m in rendered)  # native fields are stripped

# Intake fails closed unless the source is pinned to a full immutable commit.
assert ns['revision_for']('allenai/Dolci-Instruct-SFT') == 'a' * 40
try:
    ns['revision_for']('missing/repo')
except SystemExit:
    pass
else:
    raise AssertionError('missing source revision did not fail closed')

print('PASS patch-applies-or-exact-candidate-installed')
print('PASS long-schema-lossless')
print('PASS long-function-calls-lossless')
print('PASS mixed-text-and-all-call-forms')
print('PASS missing-optional-fields')
print('PASS source-id-zero')
print('PASS nonempty-output-refused')
print('PASS native-result-and-id-roundtrip')
print('PASS current-consumer-rendered-survival')
print('PASS immutable-revision-gate')
