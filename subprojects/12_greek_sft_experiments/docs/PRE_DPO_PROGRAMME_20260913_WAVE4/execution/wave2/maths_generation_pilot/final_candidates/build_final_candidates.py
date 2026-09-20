#!/usr/bin/env python3
"""Assemble the reviewed 32-row maths pilot candidate package without promotion."""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import hashlib, json, math, statistics

PILOT=Path('/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot')
OUT=PILOT/'final_candidates'
ACCEPTED=PILOT/'run_state/accepted'
ATTEMPTS=PILOT/'run_state/attempts'
INPUTS=PILOT/'inputs.jsonl'
REUSED_REVIEW=PILOT/'review/reused16/adjudications.jsonl'
ROOT_REVIEW=PILOT/'review/fresh8_root/adjudications.jsonl'
SOURCE_REPAIRS=PILOT/'review/fresh8_root/source_repairs.jsonl'
AGENT_REVIEW=PILOT/'review/fresh8_agent/adjudication.jsonl'
AGENT_SOURCE_REVIEW=PILOT/'review/fresh8_agent/source_repair_review.jsonl'
REUSE_RECEIPTS=PILOT/'adaptation_receipts_reused.jsonl'
OVERLAYS=PILOT.parent/'accepted_patchset/overlays.jsonl'

def load_jsonl(path): return [json.loads(x) for x in path.read_text().split('\n') if x.strip()]
def fsha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def csha(value): return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def tsha(text): return hashlib.sha256(text.encode()).hexdigest()

inputs=load_jsonl(INPUTS)
reused={r['row_id']:r for r in load_jsonl(REUSED_REVIEW)}
root_review={r['row_id']:r for r in load_jsonl(ROOT_REVIEW)}
source_repairs={r['row_id']:r for r in load_jsonl(SOURCE_REPAIRS)}
agent_review={r['row_id']:r for r in load_jsonl(AGENT_REVIEW)}
agent_source_review={r['row_id']:r for r in load_jsonl(AGENT_SOURCE_REVIEW)}
reuse_receipts={r['row_id']:r for r in load_jsonl(REUSE_RECEIPTS)}
overlays={r['row_id']:r for r in load_jsonl(OVERLAYS)}

agent_ids=set(agent_review)
root_ids=set(root_review)
assert len(inputs)==32 and len(agent_ids)==8 and len(root_ids)==8 and not agent_ids & root_ids

def envelope_binding(path, selected_field='solution_text'):
    env=json.loads(path.read_text())
    result=env['result']
    return {
      'binding_type':'generated_envelope', 'path':str(path), 'file_sha256':fsha(path),
      'job_id':env['job_id'],'stage':env['stage'],'model':env['model'],'effort':env['effort'],
      'job_spec_sha256':env['job_spec_sha256'],'input_record_sha256':env['input_record_sha256'],
      'payload_sha256':env['payload_sha256'],'template_sha256':env['template_sha256'],
      'schema_sha256':env['schema_sha256'],'prompt_sha256':env['prompt_sha256'],
      'result_sha256':csha(result),'selected_field':selected_field}

rows=[]
for src in inputs:
    rid=src['row_id']; group=src['pilot_group']; history=[]
    review_binding={}
    source_identity={
      'pilot_row_id':rid,'frozen_input_record_sha256':csha(src),'inputs_jsonl_path':str(INPUTS),
      'inputs_jsonl_sha256':fsha(INPUTS),'source_path':src['source_path'],'source_split':src['source_split'],
      'source_license':src['source_license'],'source_record_sha256':src['source_record_sha256'],
      'source_line':src.get('source_line'),'source_row_id_from_frozen_input':src.get('source_row_id'),
      'selection_hash':src.get('selection_hash')}
    if group=='fresh_level5':
        source_identity['identity_scope']='exact public-source line and record hash; candidate keeps the pilot row ID'
        adapt_path=ACCEPTED/f'adapt__{rid}.json'
        adapt=json.loads(adapt_path.read_text())
        problem=adapt['result']['problem_text']
        problem_binding=envelope_binding(adapt_path,'problem_text')
        problem_binding['adaptation_result']=adapt['result']
        if rid=='fresh_math5_line_1334':
            before=problem; problem=agent_review[rid]['accepted_problem_text']
            history.append({'type':'greek_naturalness_polish','status':'applied_in_candidate_only','author':'if_audit_agent',
                            'before':before,'after':problem,'before_sha256':tsha(before),'after_sha256':tsha(problem),
                            'reason':'Replace translation-like area wording while preserving every mathematical invariant.'})
        elif rid=='fresh_math5_line_1379':
            history.append({'type':'optional_notation_precision','status':'not_applied','author':'if_audit_agent',
                            'suggestion':agent_review[rid]['accepted_problem_text'],
                            'reason':'f(x)→f would be more precise notation, but the frozen adaptation follows the source wording and has no demonstrated semantic failure.'})
        elif rid in source_repairs:
            repair=source_repairs[rid]; before=problem; problem=repair['problem_text']
            history.append({'type':'source_clarification','status':'applied_in_candidate_only','author':repair['semantic_repair_author'],
                            'before':before,'after':problem,'before_sha256':repair['before_problem_sha256'],
                            'after_sha256':repair['after_problem_sha256'],'reason':repair['reason'],
                            'solution_changed':repair['solution_changed']})
            independent=agent_source_review[rid]
            history.append({'type':'independent_source_repair_review','status':independent['decision'],
                            'review_record_sha256':csha(independent),'mathematical_basis':independent['mathematical_basis'],
                            'task_preservation':independent['task_preservation']})
        if rid in agent_ids:
            selected_kind=agent_review[rid]['accepted_solution_version']
            review=agent_review[rid]
            review_binding={'path':str(AGENT_REVIEW),'file_sha256':fsha(AGENT_REVIEW),'record_sha256':csha(review),'reviewer':'if_audit_agent'}
            if rid=='fresh_math5_line_3775':
                selected_kind='solve_high'
                rejected=ACCEPTED/'verify__fresh_math5_line_3775.json'
                history.append({'type':'selection_correction_after_control_character_scan','status':'clean_high_selected',
                                'earlier_review_selection':'verify','rejected_path':str(rejected),'rejected_sha256':fsha(rejected),
                                'defect':'one decoded U+000C in an intended \\frac command','reason':'The high proof is mathematically equivalent, complete across all parameter cases, and clean.'})
        else:
            selected_kind='solve_high'
            review=root_review[rid]
            review_binding={'path':str(ROOT_REVIEW),'file_sha256':fsha(ROOT_REVIEW),'record_sha256':csha(review),'reviewer':'root'}
        solution_path=ACCEPTED/f'{selected_kind}__{rid}.json'
        env=json.loads(solution_path.read_text()); solution=env['result']['solution_text']
        solution_binding=envelope_binding(solution_path)
        final_answers=env['result']['final_answers']
        candidate_class='new_or_rebuilt'
        history.append({'type':'new_worked_solution','status':'selected','source':selected_kind,'solution_sha256':tsha(solution)})
    else:
        # These labels are preserved from the frozen pilot. Partial math5/gsm labels are not
        # promoted as proof of an exact historical training-row identity.
        if (src.get('source_row_id') or '').startswith(('math5_','gsm_')) and group=='confirmed_repair':
            source_identity['identity_scope']='repair-packet label only; no exact historical training-row mapping asserted'
        else:
            source_identity['identity_scope']='exact prior sampled record bound by source record hash'
        receipt=reuse_receipts[rid]
        problem=receipt['problem_text']
        problem_binding={'binding_type':'frozen_reuse_receipt','path':str(REUSE_RECEIPTS),'file_sha256':fsha(REUSE_RECEIPTS),
                         'record_sha256':csha(receipt),'receipt':receipt}
        for repair in src.get('source_problem_repairs',[]):
            history.append({'type':'declared_source_markup_repair','status':'already_frozen_in_input',**repair})
        review=reused[rid]
        review_binding={'path':str(REUSED_REVIEW),'file_sha256':fsha(REUSED_REVIEW),'record_sha256':csha(review),'reviewer':'dialogue_audit'}
        if group=='confirmed_control':
            solution=src['prior_candidate_solution']; final_answers=[{'part':'reference_final','expression':src['reference_final'],'unit':None,'approximation':False}]
            solution_binding={'binding_type':'retained_prior_candidate','inputs_jsonl_path':str(INPUTS),'inputs_jsonl_sha256':fsha(INPUTS),
                              'frozen_input_record_sha256':csha(src),'solution_sha256':tsha(solution)}
            candidate_class='retained_control'
            history.append({'type':'retained_control','status':'selected','reason':review['finding'],'solution_sha256':tsha(solution)})
        else:
            candidate_class='new_or_rebuilt'
            prior=src['prior_candidate_solution']
            if rid=='repair_gm_math_2231':
                overlay=overlays['gm_math_2231']; assert overlay['messages'][0]['content']==problem
                solution=overlay['messages'][1]['content']; final_answers=[{'part':'largest universal divisor','expression':'24','unit':None,'approximation':False}]
                solution_binding={'binding_type':'existing_accepted_overlay','path':str(OVERLAYS),'file_sha256':fsha(OVERLAYS),
                                  'overlay_record_sha256':csha(overlay),'operation':overlay['operation'],
                                  'before_messages_sha256':overlay['before_messages_sha256'],'after_messages_sha256':overlay['after_messages_sha256'],
                                  'solution_sha256':tsha(solution)}
                pilot_path=ACCEPTED/'solve_high__repair_gm_math_2231.json'
                history.append({'type':'candidate_conflict_resolution','status':'existing_overlay_selected',
                                'selected':'wave2/accepted_patchset overlay for gm_math_2231',
                                'not_selected':'pilot solve_high', 'not_selected_path':str(pilot_path),
                                'not_selected_sha256':fsha(pilot_path),
                                'reason':'Both are valid elementary proofs. The earlier accepted exact-match overlay is selected to avoid competing replacements and explicitly mentions negative and zero-containing blocks.'})
            else:
                selected_kind=review['acceptable_candidate_version']
                solution_path=ACCEPTED/f'{selected_kind}__{rid}.json'
                env=json.loads(solution_path.read_text()); solution=env['result']['solution_text']; final_answers=env['result']['final_answers']
                solution_binding=envelope_binding(solution_path)
            history.append({'type':'solution_repair','status':'selected','prior_solution_sha256':tsha(prior),
                            'selected_solution_sha256':tsha(solution),'reason':review['finding'],'mathematical_evidence':review['mathematical_evidence']})
    messages=[{'role':'user','content':problem},{'role':'assistant','content':solution}]
    rows.append({'row_id':rid,'candidate_class':candidate_class,'pilot_group':group,
                 'messages':messages,'final_answers':final_answers,
                 'source_identity':source_identity,'problem_binding':problem_binding,
                 'solution_binding':solution_binding,'review_binding':review_binding,
                 'repair_and_correction_history':history,
                 'candidate_messages_sha256':csha(messages),
                 'review_status':'candidate_reviewed_not_promoted'})

assert len(rows)==32 and Counter(r['candidate_class'] for r in rows)==Counter({'new_or_rebuilt':24,'retained_control':8})
(OUT/'candidate_rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))

# Decoded C0/DEL scan across every accepted output envelope.
def bad_chars(value,path='$'):
    found=[]
    if isinstance(value,str):
        for i,ch in enumerate(value):
            cp=ord(ch)
            if (cp<32 and ch not in '\t\n\r') or cp==127:
                found.append({'json_path':path,'character_index':i,'codepoint':f'U+{cp:04X}'})
    elif isinstance(value,list):
        for i,v in enumerate(value): found.extend(bad_chars(v,f'{path}[{i}]'))
    elif isinstance(value,dict):
        for k,v in value.items(): found.extend(bad_chars(v,f'{path}.{k}'))
    return found

accepted_files=sorted(ACCEPTED.glob('*.json'))
scan_rows=[]
for p in accepted_files:
    findings=bad_chars(json.loads(p.read_text()))
    scan_rows.append({'path':str(p),'sha256':fsha(p),'decoded_disallowed_c0_or_del':findings})
selected_findings=[]
for r in rows: selected_findings.extend([{'row_id':r['row_id'],**x} for x in bad_chars(r['messages'])])
scan={'definition':'decoded Unicode C0 U+0000..U+001F excluding TAB/LF/CR, plus DEL U+007F',
      'accepted_outputs_scanned':len(scan_rows),'files_with_findings':sum(bool(r['decoded_disallowed_c0_or_del']) for r in scan_rows),
      'total_findings':sum(len(r['decoded_disallowed_c0_or_del']) for r in scan_rows),
      'file_results':scan_rows,'selected_candidate_rows_scanned':len(rows),'selected_candidate_findings':selected_findings}
(OUT/'control_character_scan.json').write_text(json.dumps(scan,ensure_ascii=False,indent=2)+'\n')

# Measured call/token/latency receipt summary.
receipts=[json.loads(p.read_text())|{'_path':str(p)} for p in sorted(ATTEMPTS.glob('*.receipt.json'))]
def percentile(values,p):
    xs=sorted(values); return xs[max(0,math.ceil(p*len(xs))-1)]
def aggregate(rs):
    secs=[float(r['seconds']) for r in rs if r.get('seconds') is not None]
    usage=[r['usage'] for r in rs if r.get('usage')]
    return {'calls':len(rs),'calls_with_usage':len(usage),'sum_call_seconds':round(sum(secs),2),
            'latency_seconds':{'min':min(secs),'median':round(statistics.median(secs),3),'p95_nearest_rank':percentile(secs,.95),'max':max(secs),'mean':round(statistics.mean(secs),3)},
            'tokens':{k:sum(u.get(k,0) for u in usage) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']}}
groups=defaultdict(list)
for r in receipts: groups[(r['stage'],r['effort'],r['state'])].append(r)
starts=[datetime.fromisoformat(r['started']) for r in receipts]; finishes=[datetime.fromisoformat(r['finished']) for r in receipts]
usage_metrics={'model_values':sorted({r['model'] for r in receipts}),'calls_total':len(receipts),
 'states':dict(Counter(r['state'] for r in receipts)),'calls_without_reported_usage':sum(not r.get('usage') for r in receipts),
 'overall':aggregate(receipts),'wall_interval':{'earliest_start':min(starts).isoformat(),'latest_finish':max(finishes).isoformat(),
 'elapsed_seconds':round((max(finishes)-min(starts)).total_seconds(),3)},
 'by_stage_effort_state':{'|'.join(k):aggregate(v) for k,v in sorted(groups.items())},
 'runner_summary_path':str(PILOT/'run_state/summary.json'),'runner_summary_sha256':fsha(PILOT/'run_state/summary.json'),
 'receipt_files':[{'path':r['_path'],'job_id':r['job_id'],'attempt':r['attempt'],'state':r['state']} for r in receipts]}
(OUT/'usage_metrics.json').write_text(json.dumps(usage_metrics,ensure_ascii=False,indent=2)+'\n')

# Fixed eight-pair descriptive proof-quality comparison.
comparisons={
'fresh_math5_line_1379':('equivalent_complete','Both prove injectivity reduces the equation to x²=x⁴, enumerate -1,0,1, and distinguish the points by x-coordinate. Neither omits a domain case.'),
'fresh_math5_line_3775':('equivalent_complete','Both separate k=0, analyze all discriminant regimes for k≠0, and reject the k=-1/2 double root through the original denominator.'),
'fresh_math5_line_4646':('equivalent_complete','Both derive the same monic quartic after stating x≠0, apply Vieta correctly, and recover y=-10/3. Xhigh repeats the no-extraneous-root check; high already justifies multiplication by x².'),
'fresh_math5_line_6930':('same_valid_proof_same_source_sensitivity_miss','Both derive 4 cos x cos 2x cos 5x and the possible sum 8. Both fail to notice that the problem’s requested sum is nonunique because the cos x zero set is contained in the cos 5x zero set.'),
'repair_math5_1014':('xhigh_required_for_clean_candidate','Both mathematical approaches normalize the flag area and reach 2%, but high contains two decoded U+000C characters in intended fraction commands. Xhigh is clean and explicitly handles the nonnegative square-root branch.'),
'repair_math5_139':('equivalent_complete_high_slightly_more_direct','Both cover the admissible angle interval, sine-law formulas, quadratic branches, and final radical. High uses one auxiliary s=tan²θ; xhigh introduces t and then u, so high is marginally more direct.'),
'repair_math5_436':('xhigh_clearer_orientation_semantics','Both count 70 metal orders and nine valid orientation strings. Xhigh defines face-down/face-up symbols and bottom-to-top direction more explicitly, making the physically forbidden transition easier to audit.'),
'repair_math5_630':('both_complete_xhigh_shorter_optimization','Both coordinate proofs establish the tangent formula globally and show the angle is acute. High uses differentiation; xhigh uses AM-GM and explicitly states equality yields a nondegenerate triangle.'),
}
paired=[]
receipt_index={(r['job_id'],r['attempt']):r for r in receipts}
for rid,(rating,note) in comparisons.items():
    pair={}
    for kind in ['solve_high','solve_xhigh']:
        p=ACCEPTED/f'{kind}__{rid}.json'; env=json.loads(p.read_text())
        # Accepted envelopes record their accepted attempt number.
        rec=receipt_index[(env['job_id'],env['attempt'])]
        pair[kind]={'path':str(p),'sha256':fsha(p),'result_sha256':csha(env['result']),
                    'model':env['model'],'effort':env['effort'],'seconds':rec['seconds'],'usage':rec.get('usage'),
                    'final_answers':env['result']['final_answers']}
    paired.append({'row_id':rid,'proof_quality_relation':rating,'full_proof_comparison':note,
                   'high_vs_xhigh':pair,'scope_warning':'Descriptive selected-pair observation only; no significance or population claim.'})
(OUT/'paired_high_xhigh.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in paired))
