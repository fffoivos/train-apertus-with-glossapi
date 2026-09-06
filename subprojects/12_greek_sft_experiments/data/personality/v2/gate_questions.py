#!/usr/bin/env python3
"""Stage 1b: the self-containment gate. A model that did not write the questions reads each one ALONE and says whether it is answerable without extra context.
Usage: python3 gate_questions.py <questions.jsonl> <out.jsonl> [model=claude-sonnet-5]"""
import json, sys, os, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from claude_call import call, TOT
IN, OUT = sys.argv[1], sys.argv[2]; MODEL = sys.argv[3] if len(sys.argv) > 3 else 'claude-sonnet-5'; LOG = OUT + '.log'
BRIEF = """Είσαι ο πυλωρός ενός συνόλου εκπαίδευσης. Διαβάζεις ερωτήσεις χρηστών ΜΟΝΕΣ ΤΟΥΣ, χωρίς καμία άλλη πληροφορία, και κρίνεις για καθεμία:
- self_contained (true/false): καταλαβαίνει κανείς ακριβώς τι ρωτιέται χωρίς άλλο πλαίσιο; Είναι false αν αναφέρεται σε κάτι που δεν λέγεται («η φωτογραφία», «το βιβλίο», «αυτό το γεγονός», «ποια χρονιά;» χωρίς θέμα).
- scope_el: μία πρόταση, τι πρέπει να περιέχει μια πλήρης απάντηση όπως τη ζητά ο χρήστης (όχι όπως θα βόλευε).
- action: "keep" αν είναι αυτοτελής· "narrow" αν μπορεί να γίνει αυτοτελής με μικρή αλλαγή (δώσε narrowed_el, την ίδια ερώτηση με το πλαίσιο μέσα, στο ίδιο ύφος)· "clarify" αν ο σωστός βοηθός θα έπρεπε να ρωτήσει τι εννοεί ο χρήστης (δώσε clarify_el, την ερώτηση που θα έκανε ο βοηθός).
Μην διορθώνεις ορθογραφία ή greeklish: το ύφος του χρήστη είναι σκόπιμο. Επίστρεψε ΜΟΝΟ JSON: {"rows": [{"id": ..., "self_contained": ..., "scope_el": ..., "action": ..., "narrowed_el": ..., "clarify_el": ...}, ...]}"""
qs = [json.loads(l) for l in open(IN)]; done = set()
if os.path.exists(OUT):
    for l in open(OUT): done.add(json.loads(l)['id'])
todo = [q for q in qs if q['id'] not in done]; batches = [todo[i:i + 20] for i in range(0, len(todo), 20)]; print(f'{len(todo)} questions in {len(batches)} calls, {MODEL}', flush=True)
def run(b):
    obj = call(BRIEF + '\n\nΕΡΩΤΗΣΕΙΣ:\n' + '\n'.join(f"[{q['id']}] {q['user_el']}" for q in b), MODEL, LOG, 'G')
    got = {str(r.get('id')): r for r in (obj or {}).get('rows', []) if isinstance(r, dict)}
    return [dict(q, gate=got.get(q['id'], dict(self_contained=None, action='unjudged'))) for q in b]
with open(OUT, 'a') as fh, cf.ThreadPoolExecutor(4) as ex:
    for out in ex.map(run, batches):
        for q in out: fh.write(json.dumps(q, ensure_ascii=False) + '\n')
        fh.flush()
print('ALL DONE', flush=True)
