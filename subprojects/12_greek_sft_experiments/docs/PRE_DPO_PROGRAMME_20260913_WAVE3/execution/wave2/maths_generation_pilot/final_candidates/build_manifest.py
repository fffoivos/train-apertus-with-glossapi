#!/usr/bin/env python3
from pathlib import Path
import hashlib,json

PILOT=Path('/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot')
OUT=PILOT/'final_candidates'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
input_paths=[PILOT/'inputs.jsonl',PILOT/'manifest.json',PILOT/'adaptation_receipts_reused.jsonl',
 PILOT/'review/reused16/adjudications.jsonl',PILOT/'review/fresh8_root/adjudications.jsonl',
 PILOT/'review/fresh8_root/source_repairs.jsonl',PILOT/'review/fresh8_agent/adjudication.jsonl',
 PILOT/'review/fresh8_agent/source_repair_review.jsonl',PILOT.parent/'accepted_patchset/overlays.jsonl',
 PILOT/'run_state/summary.json']
output_names=['candidate_rows.jsonl','control_character_scan.json','usage_metrics.json','paired_high_xhigh.jsonl',
 'token_inventory.json','validation.json','REPORT.md','build_final_candidates.py','measure_tokens.py','validate_package.py','build_manifest.py']
manifest={'status':'review_complete_not_promoted','date':'2026-09-13',
 'counts':{'candidate_rows':32,'new_or_rebuilt':24,'retained_controls':8,'accepted_outputs_scanned':88,
           'selected_c0_del_findings':0,'paired_high_xhigh':8},
 'inputs':{str(p):sha(p) for p in input_paths},'outputs':{name:sha(OUT/name) for name in output_names}}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
