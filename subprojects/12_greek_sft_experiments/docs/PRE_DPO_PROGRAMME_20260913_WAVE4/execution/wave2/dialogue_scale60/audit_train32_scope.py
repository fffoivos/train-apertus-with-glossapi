#!/usr/bin/env python3
"""Targeted read of accepted train32 user decision scope; never rewrites rows."""
from __future__ import annotations
import hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PILOT=ROOT.parent/'balanced_dialogue_pilot/revision2'
def rows(path): return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def canon(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

ASSESS={
 'pilot48_01_false':('keep','explicit_latest_version_historical_claim','The phrase «στην τελευταία έκδοση» fixes the claim to the displayed version history.'),
 'pilot48_01_partial':('keep','explicit_latest_version_historical_claim','The phrase «Η τελευταία λίστα» fixes both atoms to the displayed version.'),
 'pilot48_01_true':('keep','historical_claim_supported_by_visible_events','«είχαμε βάλει» is supported by the user-supplied event history; the following change is explicit.'),
 'pilot48_01_unresolved':('keep','intentional_ambiguous_historical_reference','The previous fruit is unavailable and «το προηγούμενο» remains unresolved.'),
 'pilot48_02_false':('keep','explicit_displayed_record_scope','«Στον κατάλογο που μόλις μου έδειξες» blocks a new-state reading.'),
 'pilot48_02_partial':('keep','explicit_displayed_record_scope','Both atoms are explicitly claims about the displayed catalogue.'),
 'pilot48_02_true':('keep','matching_current_state_statement','«Τώρα έχουν μείνει» could update personal state, but it matches the complete visible state and the add operation is clear.'),
 'pilot48_02_unresolved':('keep','intentional_ambiguous_pronoun','The two feminine candidates make «την» unresolved; it supplies no new identity.'),
 'pilot48_03_false':('keep','explicit_current_record_scope','The false time is explicitly attributed to the current entry; the projector update is separate.'),
 'pilot48_03_partial':('keep','explicit_latest_version_scope','The latest-version phrase scopes both schedule atoms.'),
 'pilot48_03_true':('keep','matching_current_state_statement','The naked schedule statement matches the complete visible entry; the new duration is explicit.'),
 'pilot48_03_unresolved':('keep','missing_historical_value','The request refers to a duration that the visible record explicitly lacks and gives no value.'),
 'pilot48_04_false':('keep','historical_claim_supported_for_adjudication','«Δεν είχαμε βάλει» is a historical claim contradicted by the visible initial list; the removal is explicit.'),
 'pilot48_04_partial':('keep','explicit_displayed_record_scope','Both list atoms are tied to the list just shown.'),
 'pilot48_04_true':('keep','matching_current_list_statement','The present-tense list restatement matches the complete visible snapshot and is followed by a clear addition.'),
 'pilot48_04_unresolved':('keep','intentional_missing_addition_history','The visible context says addition history is unavailable, so «εκείνο» remains unresolved.'),
 'pilot48_06_false':('keep','charitable_classroom_inference','In the schedule-calculation exchange, «η ημέρα ποτίσματος» is naturally a conclusion from day 7 plus a four-day interval, not a new observation or update.'),
 'pilot48_06_partial':('keep','charitable_classroom_inference','The elapsed-day and due-day clauses answer the immediately supplied calculation; there is no state-edit instruction.'),
 'pilot48_06_true':('keep','charitable_classroom_inference','Both numerical clauses directly compute from the visible log.'),
 'pilot48_06_unresolved':('keep','explicit_inference_scope','«με βάση μόνο τις ημέρες ποτίσματος» makes the moisture claim an unsupported inference.'),
 'pilot48_07_false':('keep','explicit_excerpt_scope','The direct-edge claim begins «Στο απόσπασμα φαίνεται».'),
 'pilot48_07_partial':('keep','explicit_excerpt_scope','Reachability and directness are both scoped to the excerpt.'),
 'pilot48_07_true':('keep','context_bound_route_inference','The exact via-Plaza path repeats the two edges from the immediately preceding excerpt; no wider network claim is needed.'),
 'pilot48_07_unresolved':('keep','explicit_inference_scope','«Από αυτό το απόσπασμα συμπεραίνω» prevents the university claim from becoming new route evidence.'),
 'pilot48_08_false':('scope_clarification_recommended_before_reuse','naked_present_inventory_conclusion','In context it is plausibly arithmetic, but «απομένουν 8» can also sound like a fresh inventory report. Future reuse should say «Με βάση την καταγραφή» or «Άρα».'),
 'pilot48_08_partial':('scope_clarification_recommended_before_reuse','naked_present_inventory_conclusion','The first atom repeats the record, while «απομένουν 8» can be heard as a new current count. Future reuse should bind both to the displayed inventory.'),
 'pilot48_08_true':('keep','matching_inventory_conclusion','The naked count matches the complete visible arithmetic. Future variants should still prefer an explicit inference marker.'),
 'pilot48_08_unresolved':('keep','explicit_inference_scope','«Με βάση μόνο τους αριθμούς» explicitly marks the supplier date as an unsupported inference.'),
 'pilot48_10_false':('keep','explicit_text_catalogue_scope','The false status and valid cancellation are both tied to the named text catalogue.'),
 'pilot48_10_partial':('keep','explicit_text_catalogue_scope','Both status atoms and the cancellation are tied to the named text catalogue.'),
 'pilot48_10_true':('keep','context_bound_text_record_action','The immediately preceding user context names the text catalogue, the state claim matches it, and the action contract limits cancellation to that record. Future variants should repeat the catalogue scope.'),
 'pilot48_10_unresolved':('keep','intentional_ambiguous_text_record_reference','Two active entries make «εκείνη την εγγραφή» unresolved; it is not a global stop or silence request.'),
}

def main():
 specs={r['row_id']:r for r in rows(PILOT/'inputs/train.jsonl')}
 candidates={r['row_id']:r for r in rows(PILOT/'accepted_train32/candidate_rows.jsonl')}
 assert set(specs)==set(candidates)==set(ASSESS) and len(specs)==32
 out=[]
 for rid in sorted(specs):
  candidate=candidates[rid]; spec=specs[rid]['scenario_spec']
  decision=next(m for m in candidate['messages'] if m['id'].endswith('.u_decision'))
  target=next(m for m in candidate['messages'] if m['id'].endswith('.a_target'))
  disposition,scope,reason=ASSESS[rid]
  out.append({'row_id':rid,'truth_category':spec['truth_category'],'decision_text':decision['content'],
              'target_text':target['content'],'scope_assessment':scope,'disposition':disposition,'reason':reason,
              'automatic_rewrite':False,'candidate_record_sha256':canon(candidate),'source_spec_sha256':canon(spec)})
 (ROOT/'accepted_train32_scope_recheck.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in out))
 counts=Counter(x['disposition'] for x in out)
 (ROOT/'accepted_train32_scope_recheck.md').write_text(f'''# Accepted train32 scope recheck

Reviewed `{datetime.now(timezone.utc).isoformat()}`. All 32 accepted decision turns and targets were read against their frozen user evidence and action contracts. No row was changed and no model call was made.

The review keeps 30 rows under their explicit or charitable contextual reading. Two inventory rows, `pilot48_08_false` and `pilot48_08_partial`, are mathematically adjudicated correctly by their targets, but their naked present-tense “απομένουν 8” can also sound like a fresh inventory report. They are marked for explicit inference scope before reuse in a larger batch, not automatically rewritten in the accepted pilot.

The plant-log arithmetic rows are acceptable classroom inferences from the immediately supplied day values. The true route row names the exact via-Plaza path shown in the excerpt. The true cancellation row remains an in-thread text-record action under its visible context and action contract, although future variants should repeat that scope in the decision turn.

Disposition counts: `{dict(counts)}`.
''')
 print(json.dumps({'status':'PASS_TARGETED_RECHECK','rows':32,'dispositions':dict(counts),'changed':0,'model_calls':0},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
