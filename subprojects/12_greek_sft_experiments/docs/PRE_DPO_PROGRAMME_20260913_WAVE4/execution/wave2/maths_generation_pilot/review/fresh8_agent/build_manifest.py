#!/usr/bin/env python3
from pathlib import Path
import hashlib, json

PILOT=Path('/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot')
HERE=PILOT/'review/fresh8_agent'
ids=['1334','1379','3775','4646','2676','3093','3125','5977']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

reviewed=[PILOT/'inputs.jsonl',PILOT/'review/fresh8_root/source_repairs.jsonl']
for n in ids:
    rid=f'fresh_math5_line_{n}'
    for kind in ['adapt','solve_high','solve_xhigh','verify']:
        p=PILOT/'run_state/accepted'/f'{kind}__{rid}.json'
        if p.exists(): reviewed.append(p)

outputs=[HERE/name for name in [
 'adjudication.jsonl','source_repair_review.jsonl','REPORT.md',
 'independent_checks.py','independent_checks.txt','source_repair_checks.py','source_repair_checks.txt',
 'build_adjudication.py','build_source_repair_review.py','build_manifest.py']]
manifest={
 'date':'2026-09-13','status':'review_complete_not_applied',
 'scope':{'fresh_rows':ids,'root_source_repairs':['1950','6930']},
 'counts':{'fresh_rows_reviewed':8,'accepted_as_generated':5,
           'accepted_with_declared_source_typo_normalization':1,
           'adaptation_repairs_with_solution_accepted':2,'held':0,
           'root_source_repairs_accepted':2,'root_source_repairs_rejected':0},
 'reviewed_inputs':{str(p):sha(p) for p in reviewed},
 'outputs':{p.name:sha(p) for p in outputs}}
(HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
