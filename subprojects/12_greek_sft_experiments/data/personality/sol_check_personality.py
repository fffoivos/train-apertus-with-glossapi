#!/usr/bin/env python3
"""Non-Claude eyes on the personality set: Sol (gpt-5.6-sol) reads a sample of rows under the round-one Γ editing contract, adapted:
the fact sheet stands in for the English original; returns verdict ok/edited/rewrite, the edited answer, the list of changes, and
fact_doubt (a fact it believes wrong or unverifiable). Usage: python3 sol_check_personality.py <rows.jsonl> <out.jsonl> <n_sample> <workers>"""
import json, sys, os, random, subprocess, tempfile, time, threading, collections, concurrent.futures as cf
IN, OUT, N, W = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get('CHECK_MODEL', 'gpt-5.6-sol'); EFFORT = os.environ.get('CHECK_EFFORT', 'high'); TIER = 'default'
FACTS = {f['id']: f['fact_el'] for f in json.load(open(f'{HERE}/facts_greece.json'))}; IDENT = json.load(open(f'{HERE}/identity_facts.json'))['facts_el']
SCHEMA = f'{HERE}/sol_check_schema.json'
json.dump({"type": "object", "additionalProperties": False, "required": ["verdict", "edited_last_answer", "changes", "fact_doubt", "greekness"],
           "properties": {"verdict": {"type": "string", "enum": ["ok", "edited", "rewrite"]}, "edited_last_answer": {"type": "string"}, "changes": {"type": "array", "items": {"type": "string"}},
                          "fact_doubt": {"type": "string"}, "greekness": {"type": "integer", "minimum": 1, "maximum": 5}}}, open(SCHEMA, 'w'), ensure_ascii=False)
BRIEF = open(f'{HERE}/../gen_greek_rewrite_edit.py').read().split('BRIEF = """')[1].split('"""')[0]
BRIEF = BRIEF.split('ΚΕΙΜΕΝΟ:')[0]  # the Γ contract text (understanding + faults + non-faults + checklist), without the row template
BRIEF = BRIEF.replace('ένα ελληνικό κείμενο, η οδηγία ενός Έλληνα χρήστη πάνω σε αυτό, και η απάντηση του βοηθού', 'ένα φύλλο γεγονότων, η συνομιλία ενός Έλληνα χρήστη με τον βοηθό, και η τελευταία απάντηση του βοηθού που κρίνεις')
BRIEF = BRIEF.replace('Επίστρεψε ΜΟΝΟ JSON: verdict ("ok" αν δεν άλλαξες τίποτα, "edited" για διορθώσεις, "rewrite" αν έπρεπε να ξαναγράψεις την απάντηση), edited_answer (η τελική απάντηση, ολόκληρη, ακόμη και αν είναι ίδια), changes (λίστα, μία φράση ανά αλλαγή, κενή αν verdict=ok).',
                      'Επιπλέον: αν κάποιο γεγονός της απάντησης σου φαίνεται ΛΑΘΟΣ ή αμφίβολο (ημερομηνία, αριθμός, όνομα, θεσμός) γράψε το στο fact_doubt (αλλιώς κενό)· τα [ΟΝΟΜΑ], [ΗΜΕΡΟΜΗΝΙΑ ΓΝΩΣΗΣ], [ΑΔΕΙΑ] είναι σκόπιμα κενά, δεν είναι λάθος. Βαθμολόγησε greekness 1–5: πόσο φυσικά, ελληνικά ελληνικά είναι η απάντηση (5 = θα το έγραφε Έλληνας, 1 = φανερή μετάφραση).\nΕπίστρεψε ΜΟΝΟ JSON: verdict ("ok" αν δεν άλλαξες τίποτα, "edited" για διορθώσεις, "rewrite" αν έπρεπε να ξαναγράψεις), edited_last_answer (η τελική τελευταία απάντηση, ολόκληρη, ακόμη και αν είναι ίδια), changes (λίστα, μία φράση ανά αλλαγή, κενή αν ok), fact_doubt (κείμενο ή κενό), greekness (1–5).')
def render(r):
    facts = [FACTS[i] for i in r.get('facts_used') or [] if i in FACTS]; sheet = '\n'.join('- ' + f for f in facts) if facts else '(φύλλο ταυτότητας)\n' + '\n'.join('- ' + f for f in IDENT)
    conv = '\n\n'.join(f"[{m['role'].upper()}]\n{m['content']}" for m in r['messages'][:-1]); last = r['messages'][-1]['content']
    return BRIEF + f"\nΦΥΛΛΟ ΓΕΓΟΝΟΤΩΝ:\n{sheet}\n\nΣΥΝΟΜΙΛΙΑ ΩΣ ΤΩΡΑ:\n{conv}\n\nΤΕΛΕΥΤΑΙΑ ΑΠΑΝΤΗΣΗ ΒΟΗΘΟΥ (αυτή κρίνεις):\n{last}"
def check(r):
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, prefix='pchk_') as tmp: tmp.write(render(r)); p = tmp.name
    out = tempfile.mktemp(suffix='.json', prefix='pchk_out_'); t0 = time.time()
    try:
        res = subprocess.run(['codex', 'exec', '-m', MODEL, '-c', f'model_reasoning_effort={EFFORT}', '-c', f'service_tier={TIER}', '--skip-git-repo-check', '-c', 'features.code_mode_host=false', '--sandbox', 'read-only', '--ephemeral', '--output-schema', SCHEMA, '-o', out, '-'], stdin=open(p), capture_output=True, text=True, timeout=900)
        txt = open(out).read() if os.path.exists(out) else res.stdout; j = json.loads(txt[txt.index('{'):txt.rindex('}') + 1])
    except Exception as e: j = dict(verdict=None, error=type(e).__name__)
    for f in (p, out):
        try: os.remove(f)
        except Exception: pass
    j['id'] = r['id']; j['category'] = r.get('category'); j['seconds'] = round(time.time() - t0, 1); j['judge'] = MODEL; return j
rows = [json.loads(l) for l in open(IN)]; random.seed(23)
by = collections.defaultdict(list)
for r in rows: by[r.get('category') or '?'].append(r)
per = max(1, N // max(1, len(by))); sample = []
for c, rs in sorted(by.items()): random.shuffle(rs); sample += rs[:per]
done = set()
if os.path.exists(OUT):
    for l in open(OUT):
        j = json.loads(l)
        if j.get('verdict'): done.add(j['id'])
todo = [r for r in sample if r['id'] not in done]; print(f'{len(sample)} sampled over {len(by)} categories, {len(done)} done, {len(todo)} to check, {W} workers', flush=True)
lock = threading.Lock(); stats = collections.Counter(); t0 = time.time(); n = 0
with open(OUT, 'a') as fh, cf.ThreadPoolExecutor(W) as ex:
    for j in ex.map(check, todo):
        with lock:
            fh.write(json.dumps(j, ensure_ascii=False) + '\n'); fh.flush(); n += 1; stats[j.get('verdict') or 'fail'] += 1
            if n % 20 == 0 or n == len(todo): print(f'{n}/{len(todo)} {round(3600*n/(time.time()-t0))} rows/h {dict(stats)}', flush=True)
print('ALL DONE', flush=True)
