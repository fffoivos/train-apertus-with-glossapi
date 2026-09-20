#!/usr/bin/env python3
"""Record independent adjudication of root's two source-repair candidates."""
from pathlib import Path
import hashlib, json

PILOT=Path('/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot')
HERE=PILOT/'review/fresh8_agent'
SOURCE=PILOT/'review/fresh8_root/source_repairs.jsonl'
ACCEPTED=PILOT/'run_state/accepted'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
repairs={r['row_id']:r for r in [json.loads(x) for x in SOURCE.read_text().split('\n') if x.strip()]}

findings={
'fresh_math5_line_1950':{
 'decision':'accept_source_repair',
 'mathematical_basis':'Χωρίς ρητή κατανομή και ανεξαρτησία, η φράση «τυχαία χρονική στιγμή» δεν προσδιορίζει μοναδικό κοινό νόμο για τους δύο χρόνους άφιξης. Με ανεξάρτητες ομοιόμορφες αφίξεις στο [0,60], η περιοχή μη συνάντησης έχει εμβαδόν 2·(1/2)·45²=2025 μέσα σε συνολικό εμβαδόν 3600, άρα P=1-2025/3600=7/16.',
 'task_preservation':'Η προσθήκη κάνει ρητές ακριβώς τις υποθέσεις που χρησιμοποιούν η αναφορά και οι δύο λύσεις· δεν αλλάζει πρόσωπα, ώρες, διάρκεια, ζητούμενο ή υπολογισμό.',
 'solution_check':'Η υπάρχουσα high λύση εξακολουθεί να λύνει πλήρως τη διορθωμένη εκφώνηση. Η φράση «με τη συνήθη ερμηνεία» γίνεται περιττή αλλά δεν εισάγει λάθος και δεν απαιτεί αλλαγή λύσης.'},
'fresh_math5_line_6930':{
 'decision':'accept_source_repair',
 'mathematical_basis':'Η ταυτότητα δίνει ακριβώς sin²x+sin²2x+sin²3x+sin²4x-2=-2 cos x cos 2x cos 5x. Όμως Z(cos x)⊂Z(cos 5x): αν x=(2n+1)π/2, τότε 5x=(10n+5)π/2, επίσης μηδενικό του cos. Άρα τα γινόμενα με τριάδες (1,2,5) και (2,5,5) έχουν το ίδιο σύνολο μηδενικών, αλλά αθροίσματα 8 και 12. Το αρχικό μοναδικό «να βρεθεί» είναι επομένως ανεπαρκώς προσδιορισμένο.',
 'task_preservation':'Το «δώστε μία δυνατή τιμή» διατηρεί την τριγωνομετρική αναγωγή και ζητά τεκμηρίωση, ενώ παύει να υπονοεί ανύπαρκτη μοναδικότητα.',
 'solution_check':'Η υπάρχουσα high λύση αποδεικνύει ισοδυναμία με cos x cos 2x cos 5x=0 και ήδη λέει «μπορούμε να πάρουμε», άρα απαντά ακριβώς στη διορθωμένη εργασία με 8. Δεν χρειάζεται αλλαγή λύσης.'}}

rows=[]
for rid,f in findings.items():
    repair=repairs[rid]
    hp=ACCEPTED/f'solve_high__{rid}.json'
    rows.append({'row_id':rid,**f,'reviewed_repair':repair,
      'evidence':{'source_repairs_path':str(SOURCE),'source_repairs_sha256':sha(SOURCE),
                  'high_solution_path':str(hp),'high_solution_sha256':sha(hp),
                  'calculation_script':str(HERE/'source_repair_checks.py'),'calculation_script_sha256':sha(HERE/'source_repair_checks.py'),
                  'calculation_output':str(HERE/'source_repair_checks.txt'),'calculation_output_sha256':sha(HERE/'source_repair_checks.txt')},
      'review_provenance':{'reviewer':'if_audit_agent','date':'2026-09-13','additional_model_calls':0}})
(HERE/'source_repair_review.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
