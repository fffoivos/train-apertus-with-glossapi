#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, importlib.util, json, shutil, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
V1=HERE.parent
sys.dont_write_bytecode=True
shutil.rmtree(HERE/'__pycache__',ignore_errors=True)
RUNNER_SHA='c13862fd38c50facc721d385c9fcc3ea99a052719a52bf730d40490aa6b85005'
PROBE=['pilot48_01_true','pilot48_06_false','pilot48_10_partial','pilot48_03_unresolved']

def read_jsonl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def write_jsonl(p,rows): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))
def write_json(p,o): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon_sha(o): return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

for d in ['inputs','queues','prompts','schemas','receipts','sealed/final_confirmation','quarantine']:
 (HERE/d).mkdir(parents=True,exist_ok=True)
shutil.copyfile(V1/'run_queue.py',HERE/'run_queue.py')
assert sha(HERE/'run_queue.py')==RUNNER_SHA
for name in ['author_dialogue.schema.json','semantic_repair.schema.json','greek_correction.schema.json']:
 shutil.copyfile(V1/'schemas'/name,HERE/'schemas'/name)
shutil.copyfile(V1/'prompts/greek_correction.txt',HERE/'prompts/greek_correction.txt')

history_core={
'cf01_grocery_note':'Η αρχική λίστα είχε ένα γάλα, ψωμί και μήλα. Έπειτα τα γάλατα έγιναν δύο και τα μήλα αντικαταστάθηκαν από πορτοκάλια.',
'cf02_volunteer_roster':'Ο αρχικός κατάλογος είχε την Άννα και τον Νίκο. Έπειτα προστέθηκε η Μαρία και αφαιρέθηκε ο Νίκος, οπότε τώρα έχει την Άννα και τη Μαρία.',
'cf03_workshop_schedule':'Αρχικά το εργαστήριο ήταν Δευτέρα στις 17:00 στην αίθουσα Α, χωρίς καταγραμμένη διάρκεια. Έπειτα μεταφέρθηκε την Τρίτη στις 18:00 στην αίθουσα Β.',
'cf04_trip_packing':'Η αρχική λίστα είχε ταυτότητα και φορτιστή. Έπειτα προστέθηκε αδιάβροχο, οπότε τώρα περιέχει ταυτότητα, φορτιστή και αδιάβροχο.',
}
unresolved_core={
'pilot48_01_unresolved':'Στην τρέχουσα λίστα υπάρχουν δύο γάλατα, ψωμί και πορτοκάλια. Δεν είναι διαθέσιμες οι παλιότερες εκδόσεις της.',
'pilot48_02_unresolved':'Ο τρέχων κατάλογος έχει την Άννα και τη Μαρία.',
'pilot48_03_unresolved':'Το τρέχον πρόγραμμα γράφει Τρίτη στις 18:00 στην αίθουσα Β, αλλά δεν αναφέρει διάρκεια.',
'pilot48_04_unresolved':'Η τρέχουσα λίστα έχει ταυτότητα, φορτιστή και αδιάβροχο. Δεν είναι διαθέσιμο το ιστορικό προσθηκών.',
'pilot48_06_unresolved':'Στο ημερολόγιο γράφει ότι το φυτό ποτίστηκε την ημέρα 7, σήμερα είναι η ημέρα 10 και το διάστημα ποτίσματος είναι 4 ημέρες. Δεν υπάρχει μέτρηση υγρασίας.',
'pilot48_07_unresolved':'Το απόσπασμα διαδρομής δείχνει μόνο σύνδεση Αφετηρία–Πλατεία και Πλατεία–Μουσείο. Δεν περιλαμβάνει το Πανεπιστήμιο.',
'pilot48_08_unresolved':'Η καταγραφή αποθήκης λέει ότι παραλήφθηκαν 12 καρέκλες, δανείστηκαν 4 και 1 χάλασε. Δεν περιλαμβάνει πρόγραμμα προμηθευτή.',
'pilot48_10_unresolved':'Στον κειμενικό κατάλογο αυτού του νήματος υπάρχουν δύο ενεργές εγγραφές: «ραντεβού» και «αγορές».',
}
modified_decisions={
'pilot48_02_false':'Στον κατάλογο που μόλις μου έδειξες, φαίνεται ότι ο Νίκος είναι ακόμη στη λίστα. Πρόσθεσε τώρα και την Ελένη.',
'pilot48_02_partial':'Στον κατάλογο που μόλις μου έδειξες, φαίνεται ότι η Μαρία και ο Νίκος είναι καταχωρισμένοι. Αφαίρεσε τώρα την Άννα.',
'pilot48_03_unresolved':'Κράτα τη διάρκεια που είχαμε συμφωνήσει.',
'pilot48_04_partial':'Στη λίστα που μόλις μου έδειξες, φαίνεται ότι έχουμε φορτιστή αλλά όχι αδιάβροχο. Πρόσθεσε τώρα καπέλο.',
'pilot48_06_unresolved':'Με βάση μόνο τις ημέρες ποτίσματος, το χώμα πρέπει να είναι ακόμη υγρό.',
'pilot48_07_unresolved':'Από αυτό το απόσπασμα συμπεραίνω ότι η ίδια γραμμή συνεχίζει ως το Πανεπιστήμιο.',
'pilot48_08_unresolved':'Με βάση μόνο τους αριθμούς της αποθήκης, η επόμενη παράδοση από τον προμηθευτή πρέπει να είναι αύριο.',
'pilot48_10_false':'Στον κειμενικό κατάλογο που μόλις μου έδειξες, η εγγραφή «ραντεβού» φαίνεται ήδη ακυρωμένη. Ακύρωσε τώρα την εγγραφή «ραντεβού» στον κατάλογο.',
'pilot48_10_partial':'Στον κειμενικό κατάλογο που μόλις μου έδειξες, η εγγραφή «ραντεβού» φαίνεται ενεργή και η εγγραφή «αγορές» φαίνεται ακυρωμένη. Ακύρωσε τώρα την εγγραφή «ραντεβού» στον κατάλογο.',
}
reference_fields={
'pilot48_01_unresolved':'previous_fruit_reference',
'pilot48_02_unresolved':'female_reference',
'pilot48_03_unresolved':'prior_duration_reference',
'pilot48_04_unresolved':'later_item_reference',
'pilot48_10_unresolved':'referenced_task',
}

def revise(row,split):
 r=copy.deepcopy(row); s=r['scenario_spec']; rid=r['row_id']
 s['contract_version']=2
 if s['skill'] in {'version_editing','state_update'}: mode='text_record_edit'
 elif s['skill']=='cancellation': mode='text_record_edit'
 else: mode='reasoning_only'
 s['action_contract']={'mode':mode,'external_tool_result_supplied':False,'may_claim_external_action_success':False,'text_record_state_name':'ο κειμενικός κατάλογος αυτού του νήματος' if s['skill']=='cancellation' else None}
 if s['skill']=='cancellation':
  s['setting']='Κειμενικός κατάλογος υπενθυμίσεων μέσα στο ίδιο νήμα'
  s['context_blueprint']['evidence_summary_el']='Στον κειμενικό κατάλογο αυτού του νήματος υπάρχουν δύο ενεργές εγγραφές: ραντεβού και αγορές.'
 if split=='train':
  if rid in unresolved_core: core=unresolved_core[rid]
  elif s['family_id'] in history_core: core=history_core[s['family_id']]
  elif s['skill']=='cancellation': core='Στον κειμενικό κατάλογο αυτού του νήματος υπάρχουν δύο ενεργές εγγραφές: «ραντεβού» και «αγορές».'
  elif s['family_id']=='cf06_plant_log': core='Στο ημερολόγιο γράφει ότι το φυτό ποτίστηκε την ημέρα 7, σήμερα είναι η ημέρα 10 και το διάστημα ποτίσματος είναι 4 ημέρες.'
  elif s['family_id']=='cf07_bus_route': core='Το απόσπασμα διαδρομής δείχνει σύνδεση Αφετηρία–Πλατεία και Πλατεία–Μουσείο.'
  elif s['family_id']=='cf08_storeroom_inventory': core='Η καταγραφή αποθήκης λέει ότι παραλήφθηκαν 12 καρέκλες, δανείστηκαν 4 και 1 χάλασε.'
  else: raise AssertionError(rid)
 else:
  # General contract applies before dev/final authoring without opening their content for tuning.
  core=s['context_blueprint']['evidence_summary_el']
 s['visible_evidence_contract']={
  'required_user_context_core_el':core,
  'source_role':'user',
  'assistant_assertion_is_independent_evidence':False,
  'must_precede_decision':True,
  'visible_basis_sha256':canon_sha({'core':core,'evidence':s['evidence']}),
 }
 if split=='train' and rid in modified_decisions:
  s['user_decision_semantic_content_el']=modified_decisions[rid]
 if split=='train' and rid in reference_fields:
  s['claim_atoms']=[{'field':reference_fields[rid],'asserted':None,'source':'underspecified_reference'}]
 if split=='train' and rid in {'pilot48_01_unresolved','pilot48_04_unresolved'}:
  s['evidence']={'initial':copy.deepcopy(s['oracle']['state_before']),'events':[],'missing_history':True}
  s['visible_evidence_contract']['visible_basis_sha256']=canon_sha({'core':core,'evidence':s['evidence']})
 if split=='train' and rid=='pilot48_03_unresolved':
  # The evaluator has no hidden numeric duration; the dialogue must ask which duration.
  assert '60' not in s['user_decision_semantic_content_el']
 if split=='train' and rid=='pilot48_02_unresolved':
  s['evidence']={'initial':copy.deepcopy(s['oracle']['state_before']),'events':[],'ambiguous_referents':['Άννα','Μαρία']}
  s['visible_evidence_contract']['visible_basis_sha256']=canon_sha({'core':core,'evidence':s['evidence']})
 if split=='train' and rid=='pilot48_10_unresolved':
  s['evidence']={'initial':copy.deepcopy(s['oracle']['state_before']),'events':[],'ambiguous_cancel_targets':['ραντεβού','αγορές']}
  s['visible_evidence_contract']['visible_basis_sha256']=canon_sha({'core':core,'evidence':s['evidence']})
 s['decision_surface_contract']={
  'frozen_core_el':s['user_decision_semantic_content_el'],
  'must_appear_verbatim':True,
  'tone_wrapper_may_vary':True,
  'tone_wrapper_must_not_add_facts_values_references_or_operations':True,
  'tone_wrapper_must_not_change_declarative_core_into_question':True,
 }
 s['authoring_guards'] += [
  'the required user context core must appear in the user context turn before the decision',
  'assistant content never establishes oracle state independently',
  'copy the frozen decision core verbatim and do not surface hidden claim values',
  'a clear new user instruction applies now even if its historical preface is false',
  'do not claim an external action succeeded without a supplied tool result',
 ]
 r['protected']['visible_evidence_contract']=copy.deepcopy(s['visible_evidence_contract'])
 r['protected']['decision_surface_contract']=copy.deepcopy(s['decision_surface_contract'])
 r['protected']['action_contract']=copy.deepcopy(s['action_contract'])
 r['protected']['truth_category']=s['truth_category']
 r['protected']['oracle']=copy.deepcopy(s['oracle'])
 r['revision_lineage']={'from_bundle':'../','contract_version':2,'content_generation':'not_run'}
 return r

train=[revise(r,'train') for r in read_jsonl(V1/'inputs/train.jsonl')]
dev=[revise(r,'dev') for r in read_jsonl(V1/'inputs/dev.jsonl')]
final=[revise(r,'final_confirmation') for r in read_jsonl(V1/'sealed/final_confirmation/inputs.jsonl')]
old_candidates={}
old_hashes={}
old_receipt_hashes={}
for rid in PROBE:
 p=V1/'run_state/train/accepted'/f'author_{rid}.json'
 env=json.loads(p.read_text()); old_candidates[rid]=env['result']; old_hashes[str(p.relative_to(V1))]=sha(p)
for p in sorted((V1/'run_state/train/attempts').glob('*.receipt.json')):
 old_receipt_hashes[str(p.relative_to(V1))]=sha(p)
for r in train:
 if r['row_id'] in PROBE:
  rid=r['row_id']; r['prior_probe_candidate']=old_candidates[rid]
  r['prior_probe_binding']={'accepted_artifact':f'../run_state/train/accepted/author_{rid}.json','accepted_artifact_sha256':old_hashes[f'run_state/train/accepted/author_{rid}.json'],'prior_primary_call_consumed':True}
  defects={
   'pilot48_01_true':['The state evidence appeared only in an assistant assertion; put the authoritative history in the prior user turn.'],
   'pilot48_06_false':['Reissue under the revised visible-evidence and frozen-decision contract; preserve the correct calculation and avoid gratuitous argumentative tone.'],
   'pilot48_10_partial':['Bind both status claims to the text catalogue just shown, then apply the new command only to the appointment entry; do not present the false shopping status as an authoritative new update or imply an external reminder action.'],
   'pilot48_03_unresolved':['The old author inserted 60 into the user request, turning it into a clear new instruction; preserve the frozen number-free request and ask which duration.'],
  }
  r['probe_repair_scope']={'root_findings':defects[rid],'allowed_message_ids':[r['message_plan'][k] for k in ['optional_context_user_id','optional_context_assistant_id','decision_user_id','target_assistant_id']],'must_preserve_masks':True,'must_preserve_truth_and_oracle':True}
write_jsonl(HERE/'inputs/train.jsonl',train); write_jsonl(HERE/'inputs/dev.jsonl',dev); write_jsonl(HERE/'sealed/final_confirmation/inputs.jsonl',final)
shutil.copyfile(V1/'quarantine/silence_unspecified.jsonl',HERE/'quarantine/silence_unspecified.jsonl')

record_bound={'pilot48_02_false','pilot48_02_partial','pilot48_04_partial','pilot48_10_false','pilot48_10_partial'}
decision_audit=[]
for r in train:
 s=r['scenario_spec'];rid=r['row_id'];core=s['decision_surface_contract']['frozen_core_el']
 if rid in record_bound: adjudication='bound_to_displayed_text_record'
 elif s['truth_category']=='unresolved': adjudication='underspecified_reference_or_inference_preserved'
 elif s['skill']=='state_inference': adjudication='inference_from_visible_user_facts'
 elif s['truth_category'] in {'false','partial'}: adjudication='explicit_historical_or_version_claim'
 else: adjudication='truth_consistent_current_claim_or_instruction'
 decision_audit.append({'row_id':rid,'truth_category':s['truth_category'],'skill':s['skill'],'frozen_core_sha256':hashlib.sha256(core.encode()).hexdigest(),'history_vs_new_state_adjudication':adjudication,'tone_cannot_add_semantics':True,'tone_cannot_change_declarative_to_question':True})
write_jsonl(HERE/'receipts/train32_decision_core_audit.jsonl',decision_audit)

# General author prompt, used for every remaining primary call including sealed final content.
author='''# Dialogue authoring — revision 2 contract\n\nProduce one complete short natural Greek dialogue from the supplied fictional specification. Use only evidence that a dialogue participant can see at that turn. The required user-context core is authoritative evidence and must appear verbatim in the context user turn before the decision. An assistant restatement may aid flow, but an assistant assertion never creates independent oracle evidence.\n\nThe decision user turn must contain decision_surface_contract.frozen_core_el verbatim. A short tone wrapper may be added only when it adds no fact, number, referent, state change, or operation, and it must not turn a declarative core into a question. Preserve the core's sentence mood and punctuation. Never materialize values found only in hidden claim annotations. In an unresolved item, preserve the missing information and ask only for what is needed. If the user clearly supplies a new value or instruction, apply it now even when a historical attribution in the same turn is false; do not ask permission again. A status assertion is judged against the prior record only when the frozen core explicitly ties it to that displayed record; otherwise a clear user-owned status update is authoritative now.\n\nRespect action_contract. A text_record_edit changes only the explicitly named catalogue/list/log inside the conversation and may report that text-state result. Never imply that an external reminder, calendar item, notification, order, message, or device action occurred unless a supplied tool result proves it. Reasoning-only rows do not change state. Cancellation of an ambiguous referent leaves state unchanged and asks which listed item; silence remains quarantined when its representation is unspecified.\n\nFor corrections: acknowledge true atoms, correct false atoms while continuing the valid task, separate partial atoms, and state precisely what unresolved evidence cannot decide. Keep the response useful and concise. Do not add stock praise, automatic disagreement, a generic offer, invented state, or an argumentative tail. Earlier erroneous assistant history is context only and train=false.\n\nUse the stable message IDs. User turns and context assistant turns have train=false. Exactly one final assistant target has train=true. State transitions must equal the supplied oracle and describe text/in-dialogue state only unless a real tool result is supplied. An exact response must match byte-for-byte. If the label, visible evidence, frozen wording, or oracle conflict, return blocked rather than repairing them silently.\n\nReturn JSON only under the bound schema. INPUT_JSON_BEGIN\n{{INPUT_JSON}}\nINPUT_JSON_END\n'''
(HERE/'prompts/author_dialogue.txt').write_text(author)
semantic='''# Dialogue semantic repair — revision 2 contract\n\nRepair the supplied prior probe candidate against the revised scenario contract and named findings. This is semantic/state repair, not general Greek polishing. Return repair_proposed with a complete candidate_messages array when any named defect applies. Preserve row, family, split, stable IDs, roles, masks, truth category, oracle, valid content, and exactly one trained assistant target.\n\nThe context user message must contain visible_evidence_contract.required_user_context_core_el verbatim before the decision. Assistant statements are never independent evidence. The decision user message must contain decision_surface_contract.frozen_core_el verbatim; a tone wrapper may not add any fact, value, referent, or operation, change punctuation, or turn a declarative core into a question. Never surface a concrete value that exists only in claim annotations. When the frozen user wording clearly gives a new instruction, apply it now even if its historical account is false. When it does not supply the missing value or referent, ask for that information without asking permission to apply an instruction that was never given. Judge a status assertion against the prior record only when the frozen core explicitly identifies that displayed record.\n\nRespect action_contract. For text_record_edit, describe only the resulting in-conversation list/catalogue state. Do not claim that an external reminder or notification was actually cancelled, scheduled, sent, or changed without a supplied tool result. For an ambiguous cancellation, leave both entries unchanged and ask which entry.\n\nList each changed message with exact before and after text and its semantic reason. Report language-only preferences separately; do not use them to broaden the repair. Return JSON only. INPUT_JSON_BEGIN\n{{INPUT_JSON}}\nINPUT_JSON_END\n'''
(HERE/'prompts/semantic_repair.txt').write_text(semantic)

# Remaining primary queues: the four prior primary calls are not dispatched again.
def adjust_author_jobs(path,exclude=set()):
 jobs=[]
 for j in read_jsonl(path):
  if j['row_id'] in exclude: continue
  x=copy.deepcopy(j); x['template']='prompts/author_dialogue.txt'; x['schema']='schemas/author_dialogue.schema.json'; jobs.append(x)
 return jobs
train_jobs=adjust_author_jobs(V1/'queues/train.jsonl',set(PROBE)); dev_jobs=adjust_author_jobs(V1/'queues/dev.jsonl'); final_jobs=adjust_author_jobs(V1/'sealed/final_confirmation/queue.jsonl')
write_jsonl(HERE/'queues/train_remaining.jsonl',train_jobs); write_jsonl(HERE/'queues/dev.jsonl',dev_jobs); write_jsonl(HERE/'sealed/final_confirmation/queue.jsonl',final_jobs)

probe_jobs=[]
for rid in PROBE:
 probe_jobs.append({
  'job_id':f'semantic_repair_r2_{rid}','stage':'dialogue_semantic_repair','row_id':rid,'model':'gpt-5.6-sol','effort':'high','schema':'schemas/semantic_repair.schema.json','template':'prompts/semantic_repair.txt','depends_on':[],
  'payload':{
   'row_id':{'$record':'row_id'},'scenario_spec':{'$record':'scenario_spec'},'authored_candidate':{'$record':'prior_probe_candidate'},'prior_probe_binding':{'$record':'prior_probe_binding'},'named_findings':{'$record':'probe_repair_scope.root_findings'},'allowed_edit_locations':{'$record':'probe_repair_scope.allowed_message_ids'},'protected':{'$record':'protected'}
  }
 })
write_jsonl(HERE/'queues/probe_semantic_repair4.jsonl',probe_jobs)

# Bind every payload without dispatching. Final-confirmation bindings stay sealed.
runner_spec=importlib.util.spec_from_file_location('dialogue_revision2_runner',HERE/'run_queue.py')
runner=importlib.util.module_from_spec(runner_spec);runner_spec.loader.exec_module(runner)
record_maps={
 'train':{r['row_id']:r for r in train},
 'dev':{r['row_id']:r for r in dev},
 'final_confirmation':{r['row_id']:r for r in final},
}
def bind_jobs(jobs,records,outpath):
 receipts=[]
 for job in jobs:
  _,fields=runner.binding(job,records[job['row_id']],{})
  receipts.append({'job_id':job['job_id'],'row_id':job['row_id'],'stage':job['stage'],'job_spec_sha256':fields['job_spec_sha256'],'input_record_sha256':fields['input_record_sha256'],'payload_sha256':fields['payload_sha256'],'template_sha256':fields['template_sha256'],'schema_sha256':fields['schema_sha256'],'assembled_prompt_sha256':fields['prompt_sha256']})
 write_jsonl(outpath,receipts)
bind_jobs(probe_jobs,record_maps['train'],HERE/'receipts/probe_semantic_repair4_payload_bindings.jsonl')
bind_jobs(train_jobs,record_maps['train'],HERE/'receipts/train_remaining_payload_bindings.jsonl')
bind_jobs(dev_jobs,record_maps['dev'],HERE/'receipts/dev_payload_bindings.jsonl')
bind_jobs(final_jobs,record_maps['final_confirmation'],HERE/'sealed/final_confirmation/payload_bindings.jsonl')

ledger={
 'cumulative_absolute_call_cap':118,
 'consumed_before_revision2':{'primary_authoring':4,'retry':0,'semantic_repair':0,'greek_correction':0,'total':4},
 'revision2_runner_additional_call_cap':114,
 'reserved_next_probe':{'semantic_repair':4,'total':4},
 'remaining_work_caps_after_probe':{'primary_authoring':43,'retry':12,'semantic_repair':8,'greek_correction':47,'total':110},
 'cumulative_projection_at_all_caps':118,
 'no_cap_reset':True,
 'primary_accounting':{'original_total':47,'already_consumed_probe':4,'remaining':43},
 'semantic_repair_accounting':{'original_total_cap':12,'probe_reserved':4,'remaining_after_probe':8},
 'retry_cap':12,'greek_correction_cap':47,'max_workers':8,
 'note':'The isolated revision2 runner is capped at 114 additional calls because four primary calls are already present in the immutable revision1 receipts. Run only the four-job semantic repair probe first.'
}
write_json(HERE/'call_ledger.json',ledger)
write_json(HERE/'sealed/final_confirmation/gate_summary.json',{
 'split':'final_confirmation','row_count':len(final),'dispatchable':len(final_jobs),'quarantined':len(final)-len(final_jobs),'content_exposed_in_report':False,'content_available_for_tuning_or_selection':False,'prompt_contract_applied_before_generation':True,'authoring_launched':False,'family_ids_sha256':canon_sha(sorted(r['family_id'] for r in final)),'inputs_sha256':sha(HERE/'sealed/final_confirmation/inputs.jsonl')
})

artifacts={}
for p in sorted(HERE.rglob('*')):
 if p.is_file() and p.name not in {'manifest.json','prelaunch_verification.json'} and 'run_state' not in p.parts:
  artifacts[str(p.relative_to(HERE))]=sha(p)
manifest={
 'version':2,'status':'prepared_not_launched','revision_boundary':'immutable sibling of revision1; prior four calls and accepted artifacts are retained in revision1','runner':{'sha256':RUNNER_SHA,'additional_call_cap':114},
 'prelaunch_history':{'superseded_draft_path':'../prelaunch_subrevisions/revision2_draft1','snapshot_receipt_sha256':sha(V1/'prelaunch_subrevisions/revision2_draft1/SNAPSHOT_RECEIPT.json'),'reason':'preserve the original revision2 draft before decision-core history binding fixes'},
 'counts':{'specifications':48,'train':32,'dev':8,'final_confirmation':8,'quarantined':1,'prior_primary_calls_consumed':4,'remaining_primary_calls':43,'next_probe_semantic_repairs':4,'retry_cap':12,'semantic_repair_total_cap':12,'greek_correction_cap':47,'cumulative_absolute_call_cap':118,'absolute_call_cap':114},
 'probe':{'row_ids':PROBE,'queue':'queues/probe_semantic_repair4.jsonl','calls':4,'split':'train','launched':False},
 'old_probe_accepted_sha256':old_hashes,
 'old_probe_receipts_sha256':old_receipt_hashes,
 'final_confirmation_policy':'sealed; prompt contract applies before generation; content excluded from tuning, selection and report',
 'target_scale':{'train_decisions':600,'dev_decisions':60,'final_confirmation_decisions':60,'total_decisions':720,'family_disjoint':True},
 'artifact_sha256':artifacts,
}
write_json(HERE/'manifest.json',manifest)
print(json.dumps({'status':'BUILT','train':len(train),'dev':len(dev),'final':len(final),'remaining_primary':len(train_jobs)+len(dev_jobs)+len(final_jobs),'probe_repairs':len(probe_jobs),'cumulative_cap':118,'additional_cap':114},ensure_ascii=False,indent=2))
