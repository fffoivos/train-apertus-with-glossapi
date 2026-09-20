#!/usr/bin/env python3
"""Measure the final 32 candidates with the pinned local CPT tokenizer/template."""
from pathlib import Path
from collections import Counter
import hashlib, json, sys

PILOT=Path('/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot')
OUT=PILOT/'final_candidates'
PROJECT=Path('/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments')
MODEL_CACHE=Path('/Users/foivoskarounos-zamparloukos/.cache/huggingface/hub/models--fffoivos--apertus-8b-greek-cpt')
TOKENIZER_REVISION='c7f806e268083c64ce831bc46483bf98e5ddcee1'
TOKENIZER=MODEL_CACHE/'snapshots'/TOKENIZER_REVISION
TEMPLATE=Path('/Users/foivoskarounos-zamparloukos/.cache/huggingface/hub/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/b946d40447b2b597999b9c86d44bee0b452c919f')

sys.path.insert(0,str(PROJECT/'cluster'))
from sft_train import prepare_tokenizer, tokenize_messages  # noqa: E402

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
rows=[json.loads(x) for x in (OUT/'candidate_rows.jsonl').read_text().split('\n') if x.strip()]
assert len(rows)==32
assert (MODEL_CACHE/'refs/18-avg-uniform5-tokens30B-50B').read_text().strip()==TOKENIZER_REVISION
tok,control_ids=prepare_tokenizer({'tokenizer_name_or_path':str(TOKENIZER),'template_source':str(TEMPLATE),
                                   'require_apertus_control_ids':True,'extend_control_tokens':False})

items=[]
for row in rows:
    encoded=tokenize_messages(tok,row['messages'])
    chars=[len(m['content']) for m in row['messages']]
    words=[len(m['content'].split()) for m in row['messages']]
    items.append({'row_id':row['row_id'],'candidate_class':row['candidate_class'],
                  'input_tokens':len(encoded['input_ids']),'assistant_supervised_tokens':sum(encoded['assistant_masks']),
                  'user_chars':chars[0],'assistant_chars':chars[1],
                  'user_whitespace_words':words[0],'assistant_whitespace_words':words[1],
                  'within_4096':len(encoded['input_ids'])<=4096})

inventory={'status':'exact_local_pinned_tokenizer','rows':len(rows),'all_within_4096':all(x['within_4096'] for x in items),
 'totals':{k:sum(x[k] for x in items) for k in ['input_tokens','assistant_supervised_tokens','user_chars','assistant_chars','user_whitespace_words','assistant_whitespace_words']},
 'ranges':{k:{'min':min(x[k] for x in items),'max':max(x[k] for x in items)} for k in ['input_tokens','assistant_supervised_tokens','user_chars','assistant_chars','user_whitespace_words','assistant_whitespace_words']},
 'by_candidate_class':{},
 'tokenizer':{'hub_id':'fffoivos/apertus-8b-greek-cpt','revision_name':'18-avg-uniform5-tokens30B-50B','resolved_revision':TOKENIZER_REVISION,
              'local_path':str(TOKENIZER),'tokenizer_json_sha256':sha(TOKENIZER/'tokenizer.json'),
              'tokenizer_config_sha256':sha(TOKENIZER/'tokenizer_config.json'),'vocab_size':len(tok),
              'template_source_hub_id':'swiss-ai/Apertus-8B-Instruct-2509','template_source_resolved_revision':TEMPLATE.name,
              'template_tokenizer_config_sha256':sha(TEMPLATE/'tokenizer_config.json'),'control_token_ids':control_ids,
              'canonical_code_path':str(PROJECT/'cluster/sft_train.py'),'canonical_code_sha256':sha(PROJECT/'cluster/sft_train.py')},
 'items':items}
for cls in sorted({x['candidate_class'] for x in items}):
    xs=[x for x in items if x['candidate_class']==cls]
    inventory['by_candidate_class'][cls]={'rows':len(xs),'input_tokens':sum(x['input_tokens'] for x in xs),
                                          'assistant_supervised_tokens':sum(x['assistant_supervised_tokens'] for x in xs)}
(OUT/'token_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
