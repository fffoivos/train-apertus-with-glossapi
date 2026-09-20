#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import hashlib,json

PILOT=Path('/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot')
OUT=PILOT/'final_candidates'; ACCEPTED=PILOT/'run_state/accepted'
def load(p): return [json.loads(x) for x in p.read_text().split('\n') if x.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def csha(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def bad(s): return [(i,f'U+{ord(c):04X}') for i,c in enumerate(s) if (ord(c)<32 and c not in '\t\n\r') or ord(c)==127]

rows=load(OUT/'candidate_rows.jsonl'); inputs=load(PILOT/'inputs.jsonl'); by={r['row_id']:r for r in rows}
assert len(rows)==32==len(by) and set(by)=={r['row_id'] for r in inputs}
assert Counter(r['candidate_class'] for r in rows)==Counter({'new_or_rebuilt':24,'retained_control':8})
assert Counter(r['pilot_group'] for r in rows)==Counter({'fresh_level5':16,'confirmed_repair':8,'confirmed_control':8})
for r in rows:
    assert [m['role'] for m in r['messages']]==['user','assistant']
    assert all(isinstance(m['content'],str) and m['content'].strip() for m in r['messages'])
    assert not any(bad(m['content']) for m in r['messages'])
    assert r['candidate_messages_sha256']==csha(r['messages'])
    sb=r['solution_binding']
    if sb['binding_type']=='generated_envelope':
        p=Path(sb['path']); assert sha(p)==sb['file_sha256']; env=json.loads(p.read_text())
        assert env['result']['solution_text']==r['messages'][1]['content'] and csha(env['result'])==sb['result_sha256']
    elif sb['binding_type']=='existing_accepted_overlay':
        overlay=next(x for x in load(Path(sb['path'])) if x['row_id']=='gm_math_2231')
        assert overlay['messages']==r['messages'] and csha(overlay)==sb['overlay_record_sha256']
    else:
        assert sb['binding_type']=='retained_prior_candidate' and sha(Path(sb['inputs_jsonl_path']))==sb['inputs_jsonl_sha256']
    assert r['review_status']=='candidate_reviewed_not_promoted'

adapt_1379=json.loads((ACCEPTED/'adapt__fresh_math5_line_1379.json').read_text())['result']['problem_text']
assert by['fresh_math5_line_1379']['messages'][0]['content']==adapt_1379
assert any(x['type']=='optional_notation_precision' and x['status']=='not_applied' for x in by['fresh_math5_line_1379']['repair_and_correction_history'])
assert by['fresh_math5_line_1334']['messages'][0]['content'].startswith('Ποιο είναι, σε τετραγωνικές μονάδες')
for rid in ['fresh_math5_line_1950','fresh_math5_line_6930']:
    assert any(x['type']=='source_clarification' and x['status']=='applied_in_candidate_only' for x in by[rid]['repair_and_correction_history'])
assert by['fresh_math5_line_3775']['solution_binding']['job_id']=='solve_high__fresh_math5_line_3775'
assert any(x['type']=='selection_correction_after_control_character_scan' for x in by['fresh_math5_line_3775']['repair_and_correction_history'])
assert by['repair_gm_math_2231']['solution_binding']['binding_type']=='existing_accepted_overlay'
assert any(x['type']=='candidate_conflict_resolution' for x in by['repair_gm_math_2231']['repair_and_correction_history'])
for r in rows:
    if r['pilot_group']=='confirmed_repair' and (r['source_identity'].get('source_row_id_from_frozen_input') or '').startswith(('math5_','gsm_')):
        assert r['source_identity']['identity_scope'].startswith('repair-packet label only')

scan=json.loads((OUT/'control_character_scan.json').read_text())
assert scan['accepted_outputs_scanned']==88 and scan['files_with_findings']==2 and scan['total_findings']==3
assert scan['selected_candidate_findings']==[]
tokens=json.loads((OUT/'token_inventory.json').read_text())
assert tokens['status']=='exact_local_pinned_tokenizer' and tokens['rows']==32 and tokens['all_within_4096']
assert max(x['input_tokens'] for x in tokens['items'])==1003
usage=json.loads((OUT/'usage_metrics.json').read_text())
assert usage['calls_total']==92 and usage['states']=={'failed':4,'accepted':88} and usage['calls_without_reported_usage']==4
pairs=load(OUT/'paired_high_xhigh.jsonl'); assert len(pairs)==8==len({r['row_id'] for r in pairs})
pilot_manifest=json.loads((PILOT/'manifest.json').read_text())
immutable_checks={name:{'expected':want,'actual':sha(PILOT/name),'match':sha(PILOT/name)==want}
                  for name,want in pilot_manifest['artifact_sha256'].items()}
assert all(x['match'] for x in immutable_checks.values())
validation={'status':'valid_review_candidate_package_not_promoted','rows':32,'unique_ids':32,
 'candidate_class_counts':dict(Counter(r['candidate_class'] for r in rows)),
 'pilot_group_counts':dict(Counter(r['pilot_group'] for r in rows)),
 'message_shape':'all exactly user,assistant and nonempty','selected_disallowed_c0_del':0,
 'all_88_scan':{'files_with_findings':2,'findings':3},'tokenizer_gate':'pass_exact_local_pinned','all_rows_within_4096':True,
 'usage_receipts':{'calls':92,'accepted':88,'failed_initial_adaptation_attempts':4,'calls_with_usage':88},
 'paired_rows':8,'immutable_pilot_artifacts':immutable_checks,'production_mutations':0,'additional_model_calls':0}
(OUT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
