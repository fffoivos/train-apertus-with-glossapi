#!/usr/bin/env python3
"""Build the independent eight-row adjudication from frozen pilot artifacts."""
from pathlib import Path
import hashlib, json

PILOT = Path('/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot')
HERE = PILOT/'review/fresh8_agent'
ACCEPTED = PILOT/'run_state/accepted'
IDS = ['1334','1379','3775','4646','2676','3093','3125','5977']

def load_jsonl(path):
    return [json.loads(x) for x in path.read_text().split('\n') if x.strip()]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def csha(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

inputs = {r['row_id']: r for r in load_jsonl(PILOT/'inputs.jsonl')}

reviews = {
 '1334': {
  'decision':'repair_adaptation_accept_solution',
  'problem_text':'Ποιο είναι, σε τετραγωνικές μονάδες, το εμβαδόν του τριγώνου του οποίου κορυφές είναι τα σημεία τομής της καμπύλης $y=(x-3)^2(x+2)$ με τους άξονες $x$ και $y$;',
  'prompt_issue':'Η φράση «Πόσες τετραγωνικές μονάδες είναι το εμβαδόν» είναι κατανοητή αλλά μεταφραστική και συντακτικά άκομψη. Η προτεινόμενη μικροδιόρθωση διατηρεί ακριβώς καμπύλη, σημεία τομής και μονάδα.',
  'basis':'Οι τετμημένες των τομών με τον άξονα x είναι -2 και 3· η διπλή ρίζα 3 δίνει ένα σημείο. Η τομή με τον y είναι (0,18). Βάση 5 και ύψος 18 δίνουν εμβαδόν 45.',
  'domain':'Τρία διαφορετικά σημεία ορίζουν μη εκφυλισμένο τρίγωνο. Η πολλαπλότητα της ρίζας x=3 δεν δημιουργεί δεύτερο σημείο.',
  'reference':'correct', 'greek':'Η επιλεγμένη τυφλή λύση είναι σαφής και ορολογικά σωστή· απαιτείται μόνο η παραπάνω μικροδιόρθωση της εκφώνησης.'},
 '1379': {
  'decision':'repair_adaptation_accept_solution',
  'problem_text':'Έστω $f$ μια συνάρτηση ορισμένη για κάθε πραγματικό $x$ και αντιστρέψιμη (δηλαδή η $f^{-1}(x)$ υπάρχει για κάθε $x$ στο σύνολο τιμών της $f$).\n\nΑν σχεδιαστούν οι γραφικές παραστάσεις των $y=f(x^2)$ και $y=f(x^4)$, σε πόσα σημεία τέμνονται;',
  'prompt_issue':'Η φράση «η f(x) είναι μια συνάρτηση» συγχέει τη συνάρτηση f με την τιμή f(x). Η προτεινόμενη διατύπωση διορθώνει μόνο αυτό το ελληνικό/μαθηματικό σημείο.',
  'basis':'Η αντιστρεψιμότητα συνεπάγεται 1-1, άρα f(x²)=f(x⁴) iff x²=x⁴. Η παραγοντοποίηση x²(x-1)(x+1)=0 δίνει x=-1,0,1 και τρία διαφορετικά σημεία λόγω διαφορετικών τετμημένων.',
  'domain':'Η f ορίζεται σε όλο το R, άρα τα μη αρνητικά ορίσματα x² και x⁴ είναι επιτρεπτά. Οι ίδιες τεταγμένες στα x=±1 δεν ταυτίζουν τα σημεία.',
  'reference':'correct', 'greek':'Η επιλεγμένη τυφλή λύση είναι φυσική και πλήρης. Η εκφώνηση χρειάζεται τη μικροδιόρθωση f(x)→f.'},
 '3775': {
  'decision':'accept', 'problem_text':None, 'prompt_issue':None,
  'basis':'Με τον περιορισμό kx-1≠0 προκύπτει kx²-2x-2=0. Για k=0 υπάρχει ακριβώς η επιτρεπτή λύση x=-1. Για k≠0, Δ=4+8k: αρνητική δίνει καμία λύση, θετική δύο επιτρεπτές λύσεις, ενώ k=-1/2 δίνει μόνο x=-2, που μηδενίζει τον αρχικό παρονομαστή και απορρίπτεται.',
  'domain':'Η ανάλυση χωρίζει ρητά την εκφυλισμένη γραμμική περίπτωση k=0, όλες τις περιοχές της διακρίνουσας και την απαγορευμένη τιμή του παρονομαστή.',
  'reference':'correct', 'greek':'Η εκφώνηση και η επιλεγμένη τυφλή λύση είναι φυσικές και ακριβείς.'},
 '4646': {
  'decision':'accept', 'problem_text':None, 'prompt_issue':None,
  'basis':'Με y=1/x και x≠0, κάθε τομή ικανοποιεί το μονικό x⁴+Ax³+Cx²+Bx+1=0. Το γινόμενο των τεσσάρων ριζών είναι 1, άρα από 2·(-5)·(1/3)·r=1 παίρνουμε r=-3/10 και y=-10/3. Ανεξάρτητη ανακατασκευή του κύκλου δίνει μηδενικά υπόλοιπα και για τις τέσσερις ρίζες.',
  'domain':'Ο πολλαπλασιασμός με x² δεν εισάγει x=0, επειδή ο σταθερός όρος του πολυωνύμου είναι 1. Η τέταρτη τετμημένη είναι διαφορετική από τις τρεις δοσμένες.',
  'reference':'correct', 'greek':'Και οι τρεις λύσεις είναι σωστές. Η τυφλή λύση επιλέγεται ως πλήρης και λιτή.'},
 '2676': {
  'decision':'accept', 'problem_text':None, 'prompt_issue':None,
  'basis':'Το ίδιο τρίγωνο ACE έχει εμβαδόν (AE·CD)/2=20 και (CE·AB)/2=2CE, συνεπώς CE=10.',
  'domain':'Οι D και B δίνονται πάνω στις αντίστοιχες ευθείες, οπότε τα CD και AB είναι αποστάσεις/ύψη ακόμη και αν το ίχνος βρίσκεται σε προέκταση. Η τυφλή λύση το δηλώνει ρητά.',
  'reference':'correct', 'greek':'Η εκφώνηση είναι πιστή. Η τυφλή λύση έχει καλύτερη μαθηματική μορφοποίηση από την high και επιλέγεται.'},
 '3093': {
  'decision':'accept', 'problem_text':None, 'prompt_issue':None,
  'basis':'Με s=27 και βάση BC=24, K=rs=(1/2)·24h δίνει r/h=4/9. Η παράλληλη από το έγκεντρο αφήνει ύψος h-r, άρα λόγο ομοιότητας 5/9 και περίμετρο (5/9)·54=30.',
  'domain':'Οι πλευρές 12,18,24 ικανοποιούν αυστηρά τις ανισότητες τριγώνου. Εφόσον 0<r/h<1, η παράλληλη τέμνει πράγματι τα τμήματα AB και AC.',
  'reference':'correct', 'greek':'Η εκφώνηση και η επιλεγμένη τυφλή λύση είναι καθαρές και χρησιμοποιούν σωστά τον όρο «έγκεντρο».'},
 '3125': {
  'decision':'accept_with_declared_source_typo_normalization', 'problem_text':None,
  'prompt_issue':'Η αγγλική πηγή έχει το προφανές τυπογραφικό «of 50% longer». Η προσαρμογή το αποκαθιστά ως «is 50% longer», το δηλώνει και δεν αλλάζει κανένα μαθηματικό δεδομένο.',
  'basis':'Για κύλινδρο x²+y²=1 και επίπεδο z=kx+c, η τομή έχει ημιάξονες 1 και √(1+k²). Άρα ο μικρός άξονας είναι η διάμετρος 2. Με λόγο μεγάλου προς μικρό 1,5, ο μεγάλος άξονας είναι 3.',
  'domain':'Η τομή δηλώνεται έλλειψη, οπότε εξαιρείται επίπεδο παράλληλο στον άξονα. Η μετατόπιση c δεν επηρεάζει τα μήκη των ημιαξόνων.',
  'reference':'correct_despite_terse_justification', 'greek':'Η ελληνική αποκατάσταση είναι φυσική. Η τυφλή λύση παρέχει την αναλυτική αιτιολόγηση που λείπει από τη σύντομη αναφορά.'},
 '5977': {
  'decision':'accept', 'problem_text':None, 'prompt_issue':None,
  'basis':'Οι ορθές γωνίες δίνουν AB∥CD. Στο συνηθισμένο απλό τετράπλευρο με κορυφές στη δοσμένη σειρά, A και D είναι στην ίδια πλευρά της BC, άρα οι κάθετες συνιστώσες διαφέρουν κατά 20-5=15 και η παράλληλη απόσταση είναι 8. Επομένως AD=√(8²+15²)=17.',
  'domain':'Η απάντηση χρησιμοποιεί τη συνήθη σύμβαση ότι «τετράπλευρο ABCD» σημαίνει απλό τετράπλευρο. Η αντίθετη τοποθέτηση των A,D θα έκανε το περίγραμμα αυτοτεμνόμενο, όχι το δηλωμένο τετράπλευρο.',
  'reference':'correct', 'greek':'Η εκφώνηση είναι φυσική και η τυφλή λύση δηλώνει την κρίσιμη γεωμετρική σύμβαση.'}
}

rows=[]
for n in IDS:
    rid=f'fresh_math5_line_{n}'
    src=inputs[rid]
    paths={kind: ACCEPTED/f'{kind}__{rid}.json' for kind in ['adapt','solve_high','solve_xhigh','verify']}
    assert paths['adapt'].exists() and paths['solve_high'].exists() and paths['verify'].exists()
    available=[kind for kind,p in paths.items() if kind.startswith('solve_') or kind=='verify' if p.exists()]
    chosen_path=paths['verify']
    chosen=json.loads(chosen_path.read_text())
    a=json.loads(paths['adapt'].read_text())
    rv=reviews[n]
    prompt_text=rv['problem_text'] or a['result']['problem_text']
    finals={kind:json.loads(paths[kind].read_text())['result']['final_answers'] for kind in available}
    normalized_finals={kind:[(z['expression'],z.get('unit'),z.get('approximation')) for z in value] for kind,value in finals.items()}
    assert len({json.dumps(v,ensure_ascii=False,sort_keys=True) for v in normalized_finals.values()})==1
    rows.append({
      'row_id':rid,
      'decision':rv['decision'],
      'accepted_problem_text':prompt_text,
      'accepted_solution_version':'verify',
      'accepted_solution_job_id':chosen['job_id'],
      'accepted_solution_result':chosen['result'],
      'reviewed_solution_versions':available,
      'variant_comparison':{'final_answer_values_equivalent':True,'final_answers':finals,'note':'Every available solution was read in full; agreement of final-answer values was treated only as a cross-check, not as proof.'},
      'adjudication':{'mathematical_basis':rv['basis'],'domains_cases_units':rv['domain'],'reference_status':rv['reference'],'prompt_issue':rv['prompt_issue'],'greek_review':rv['greek']},
      'source_identity':{'inputs_jsonl_sha256':sha(PILOT/'inputs.jsonl'),'frozen_input_record_sha256':csha(src),'source_path':src['source_path'],'source_line':src['source_line'],'source_record_sha256':src['source_record_sha256'],'selection_hash':src['selection_hash']},
      'artifact_evidence':{kind:{'path':str(path),'sha256':sha(path)} for kind,path in paths.items() if path.exists()},
      'review_provenance':{'reviewer':'if_audit_agent','method':'independent source, derivation, domain/case/unit, Greek, reference, and full-variant review','date':'2026-09-13','additional_model_calls':0}
    })

(HERE/'adjudication.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
