#!/usr/bin/env python3
"""Stage 3: the Γ correction pass by a model that did not write the rows (Sonnet by default), framed as an editor. Writes verdicts and a corrected copy.
Usage: python3 correct_rows.py <rows.jsonl> <sheet_v2.json> <out_checks.jsonl> <out_corrected_rows.jsonl> [model=claude-sonnet-5]"""
import json, sys, os, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from claude_call import call, TOT; from personality_brief import BRIEF as GAMMA
ROWS, SHEET, OUTC, OUTR = sys.argv[1:5]; MODEL = sys.argv[5] if len(sys.argv) > 5 else 'claude-sonnet-5'; LOG = OUTC + '.log'
facts = {f['id']: f for f in json.load(open(SHEET))}
HEAD = "Είσαι επιμελητής που ΔΕΝ έγραψε αυτές τις γραμμές: τις διαβάζεις με φρέσκο μάτι και αυστηρότητα, χωρίς να υπερασπίζεσαι το κείμενο. Επιπλέον έλεγξε: (α) «στην Ελλάδα/της Ελλάδας/η Ελλάδα» σε απάντηση προς Έλληνα χωρίς σύγκριση με άλλη χώρα → αφαίρεσέ το ή κάνε το «εδώ»/«σ' εμάς»· (β) αναφορές του βοηθού στον εαυτό του και καταληκτικές προσφορές → αφαιρούνται· (γ) λείπει αντικείμενο/κλιτικό ή άρθρο (π.χ. «θα βρεις κλειστά» → «θα τα βρεις κλειστά»).\n\n"
def sheet_for(r):
    fs = [facts[i] for i in r.get('facts_used') or [] if i in facts]
    return '\n'.join(f"- {f['fact_el']}" + (f" (γιατί/πώς: {f['explain_el']})" if f.get('explain_el') else '') + (f" (σχετικό: {f['related_el']})" if f.get('related_el') else '') + ((' (γεγονότα: ' + '; '.join(e['date'] + ' ' + e['what_el'] for e in f['events']) + ')') if f.get('events') else '') for f in fs) or '(κανένα από το φύλλο· κρίνε την απάντηση από τη συνομιλία)'
def render(b):
    parts = []
    for r in b:
        conv = '\n\n'.join(f"[{m['role'].upper()}]\n{m['content']}" for m in r['messages'][:-1]); last = r['messages'][-1]['content']
        parts.append(f"===== ROW {r['id']} =====\nΦΥΛΛΟ ΓΕΓΟΝΟΤΩΝ:\n{sheet_for(r)}\nΠΡΟΣΘΗΚΕΣ ΠΟΥ ΔΗΛΩΣΕ Ο ΣΥΓΓΡΑΦΕΑΣ ΕΚΤΟΣ ΦΥΛΛΟΥ (έλεγξέ τες ιδιαίτερα): {r.get('beyond_sheet') or '—'}\n\nΣΥΝΟΜΙΛΙΑ ΩΣ ΤΩΡΑ:\n{conv}\n\nΤΕΛΕΥΤΑΙΑ ΑΠΑΝΤΗΣΗ ΒΟΗΘΟΥ (αυτή κρίνεις):\n{last}")
    return HEAD + GAMMA + f"\n\nΚρίνεις {len(b)} γραμμές, χωριστά (===== ROW <id> =====). Μην χρησιμοποιήσεις εργαλεία. Επίστρεψε ΜΟΝΟ JSON: {{\"rows\": [{{\"id\": ..., \"verdict\": ok|edited|rewrite, \"edited_last_answer\": ..., \"changes\": [...], \"fact_doubt\": ..., \"greekness\": 1-5}}, ...]}}\n\n" + '\n\n'.join(parts)
rows = [json.loads(l) for l in open(ROWS)]; done = set()
if os.path.exists(OUTC):
    for l in open(OUTC):
        j = json.loads(l)
        if j.get('verdict'): done.add(j['id'])
todo = [r for r in rows if r['id'] not in done]; batches = [todo[i:i + 5] for i in range(0, len(todo), 5)]; print(f'{len(todo)} rows in {len(batches)} calls, {MODEL}', flush=True)
def run(b):
    obj = call(render(b), MODEL, LOG, 'C'); got = {str(x.get('id')): x for x in (obj or {}).get('rows', []) if isinstance(x, dict)}
    return [dict(id=r['id'], category=r.get('form'), judge=MODEL, **{k: got[r['id']].get(k) for k in ('verdict', 'edited_last_answer', 'changes', 'fact_doubt', 'greekness')}) if r['id'] in got else dict(id=r['id'], judge=MODEL, verdict=None) for r in b]
with open(OUTC, 'a') as fh, cf.ThreadPoolExecutor(4) as ex:
    for out in ex.map(run, batches):
        for j in out: fh.write(json.dumps(j, ensure_ascii=False) + '\n')
        fh.flush()
checks = {}
for l in open(OUTC):
    j = json.loads(l)
    if j.get('verdict'): checks[j['id']] = j
with open(OUTR, 'w') as fh:
    for r in rows:
        c = checks.get(r['id']); rr = dict(r)
        if c and c['verdict'] in ('edited', 'rewrite') and (c.get('edited_last_answer') or '').strip():
            rr['messages'] = r['messages'][:-1] + [dict(role='assistant', content=c['edited_last_answer'])]; rr['corrected_by'] = MODEL; rr['original_last_answer'] = r['messages'][-1]['content']
        fh.write(json.dumps(rr, ensure_ascii=False) + '\n')
print('ALL DONE', flush=True)
