#!/usr/bin/env python3
"""Editor pass for restyled rows, by a model that did NOT write them (Sonnet by default). Unlike v2/correct_rows.py it judges EVERY
assistant turn of a row (restyle rewrites all of them), returns the edited turns, and records what changed. Prompt = the shared Γ brief +
the v2 HEAD, unchanged (no row-specific hints), so catches are a generalisation test. Identity rows (B/C/D) get the identity facts as their sheet.
Usage: python3 edit_rows.py <rows.jsonl> <out_checks.jsonl> <out_edited_rows.jsonl> [model=claude-sonnet-5]"""
import json, sys, os, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'v2')); sys.path.insert(0, os.path.join(HERE, '..'))
from claude_call import call, TOT; from personality_brief import BRIEF as GAMMA
ROWS, OUTC, OUTR = sys.argv[1:4]; MODEL = sys.argv[4] if len(sys.argv) > 4 else 'claude-sonnet-5'; LOG = OUTC + '.log'
facts = {f['id']: f for f in json.load(open(os.path.join(HERE, '..', 'v2', 'facts_greece_v2.json')))}
IDENT = json.load(open(os.path.join(HERE, '..', 'identity_facts.json')))
IDENT_TXT = '\n'.join('- ' + x for x in IDENT['facts_el']) + '\n- ' + ' | '.join(IDENT['name_decision']['how_to_phrase_el'])
HEAD = "Είσαι επιμελητής που ΔΕΝ έγραψε αυτές τις γραμμές: τις διαβάζεις με φρέσκο μάτι και αυστηρότητα, χωρίς να υπερασπίζεσαι το κείμενο. Επιπλέον έλεγξε: (α) «στην Ελλάδα/της Ελλάδας/η Ελλάδα» σε απάντηση προς Έλληνα χωρίς σύγκριση με άλλη χώρα → αφαιρέσέ το ή κάνε το «εδώ»/«σ' εμάς»· (β) αναφορές του βοηθού στον εαυτό του χωρίς να ρωτηθεί και καταληκτικές προσφορές → αφαιρούνται· (γ) λείπει αντικείμενο/κλιτικό ή άρθρο (π.χ. «θα βρεις κλειστά» → «θα τα βρεις κλειστά»).\nΚρίνεις ΚΑΘΕ απάντηση του βοηθού στη συνομιλία (όχι μόνο την τελευταία), και επιστρέφεις όλες τις απαντήσεις του βοηθού με τη σειρά, διορθωμένες όπου χρειάζεται και αυτούσιες όπου όχι.\n\n"
def sheet_for(r):
    fs = [facts[i] for i in r.get('facts_used') or [] if i in facts]
    s = '\n'.join(f"- {f['fact_el']}" + (f" (γιατί/πώς: {f['explain_el']})" if f.get('explain_el') else '') + (f" (σχετικό: {f['related_el']})" if f.get('related_el') else '') + ((' (γεγονότα: ' + '; '.join(e['date'] + ' ' + e['what_el'] for e in f['events']) + ')') if f.get('events') else '') for f in fs)
    if r.get('category') in ('B', 'C', 'D'): s = (s + '\n' if s else '') + 'ΦΥΛΛΟ ΤΑΥΤΟΤΗΤΑΣ ΤΟΥ ΒΟΗΘΟΥ:\n' + IDENT_TXT
    return s or '(κανένα από το φύλλο· κρίνε την απάντηση από τη συνομιλία)'
def render(b):
    parts = []
    for r in b:
        conv = '\n\n'.join(f"[{m['role'].upper()}]\n{m['content']}" for m in r['messages'])
        parts.append(f"===== ROW {r['id']} =====\nΦΥΛΛΟ ΓΕΓΟΝΟΤΩΝ:\n{sheet_for(r)}\nΠΡΟΣΘΗΚΕΣ ΠΟΥ ΔΗΛΩΣΕ Ο ΣΥΓΓΡΑΦΕΑΣ ΕΚΤΟΣ ΦΥΛΛΟΥ (έλεγξέ τες ιδιαίτερα): {r.get('beyond_sheet') or '—'}\n\nΣΥΝΟΜΙΛΙΑ ({sum(1 for m in r['messages'] if m['role']=='assistant')} απαντήσεις βοηθού προς κρίση):\n{conv}")
    return HEAD + GAMMA + f"\n\nΚρίνεις {len(b)} γραμμές, χωριστά (===== ROW <id> =====). Μην χρησιμοποιήσεις εργαλεία. Επίστρεψε ΜΟΝΟ JSON: {{\"rows\": [{{\"id\": ..., \"verdict\": ok|edited|rewrite, \"edited_assistant_turns\": [όλες οι απαντήσεις του βοηθού με τη σειρά, διορθωμένες ή αυτούσιες], \"changes\": [\"τι άλλαξε και γιατί, ένα στοιχείο ανά αλλαγή, με παράθεση πριν → μετά\"], \"fact_doubt\": ..., \"greekness\": 1-5}}, ...]}}\n\n" + '\n\n'.join(parts)
rows = [json.loads(l) for l in open(ROWS)]; done = set()
if os.path.exists(OUTC):
    for l in open(OUTC):
        j = json.loads(l)
        if j.get('verdict'): done.add(j['id'])
todo = [r for r in rows if r['id'] not in done]; batches = [todo[i:i + 5] for i in range(0, len(todo), 5)]; print(f'{len(todo)} rows in {len(batches)} calls, {MODEL}', flush=True)
def run(b):
    obj = call(render(b), MODEL, LOG, 'E'); got = {str(x.get('id')): x for x in (obj or {}).get('rows', []) if isinstance(x, dict)}
    out = []
    for r in b:
        x = got.get(r['id'])
        if not x: out.append(dict(id=r['id'], judge=MODEL, verdict=None)); continue
        out.append(dict(id=r['id'], category=r.get('category'), judge=MODEL, verdict=x.get('verdict'), edited_assistant_turns=x.get('edited_assistant_turns'), changes=x.get('changes'), fact_doubt=x.get('fact_doubt'), greekness=x.get('greekness')))
    return out
with open(OUTC, 'a') as fh, cf.ThreadPoolExecutor(4) as ex:
    for out in ex.map(run, batches):
        for j in out: fh.write(json.dumps(j, ensure_ascii=False) + '\n')
        fh.flush(); print(f'+{len(out)} | ${TOT["cost"]:.2f}', flush=True)
checks = {}
for l in open(OUTC):
    j = json.loads(l)
    if j.get('verdict'): checks[j['id']] = j
n_applied = 0
with open(OUTR, 'w') as fh:
    for r in rows:
        c = checks.get(r['id']); rr = dict(r)
        turns = c.get('edited_assistant_turns') if c else None
        if c and c['verdict'] in ('edited', 'rewrite') and isinstance(turns, list) and len(turns) == sum(1 for m in r['messages'] if m['role'] == 'assistant'):
            k = 0; msgs = []
            for m in r['messages']:
                if m['role'] == 'assistant': msgs.append(dict(role='assistant', content=turns[k] if isinstance(turns[k], str) else m['content'])); k += 1
                else: msgs.append(m)
            rr['messages'] = msgs; rr['edited_by'] = MODEL; rr['pre_edit_messages'] = r['messages']; n_applied += 1
        fh.write(json.dumps(rr, ensure_ascii=False) + '\n')
print(f'ALL DONE, edits applied to {n_applied} rows', flush=True)
