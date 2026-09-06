#!/usr/bin/env python3
"""Stage 2: answers, with the WHOLE sheet v2 in view, under brief v2 (length by form, related fact, insider voice, beyond_sheet tags).
Questions that the gate marked 'clarify' become clarifying-question rows; 'narrow' uses the narrowed question.
Usage: python3 gen_answers.py <questions_gated.jsonl> <sheet_v2.json> <identity_facts.json> <out_rows.jsonl> [model=claude-opus-5]"""
import json, sys, os, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from claude_call import call, TOT
QS, SHEET, IDENT, OUT = sys.argv[1:5]; MODEL = sys.argv[5] if len(sys.argv) > 5 else 'claude-opus-5'; LOG = OUT + '.log'
facts = json.load(open(SHEET)); ident = json.load(open(IDENT))
def sheet_text():
    L = []
    for f in facts:
        s = f"[{f['id']}] {f['title_el']}: {f['fact_el']}"
        if f.get('explain_el'): s += f"\n   γιατί/πώς: {f['explain_el']}"
        if f.get('related_el'): s += f"\n   σχετικό: {f['related_el']}"
        if f.get('events'): s += "\n   γεγονότα: " + '; '.join(f"{e['date']} {e['what_el']}" for e in f['events'])
        if not f.get('stable', True): s += f"\n   (ισχύει με βάση τα στοιχεία του {f.get('as_of','—')}: πες το έτσι, όχι «ίσχυε ως»)"
        L.append(s)
    return '\n'.join(L)
SHEET_TXT = sheet_text(); IDENT_TXT = '\n'.join('- ' + x for x in ident['facts_el'])
BRIEF = """Γράφεις τις ΑΠΑΝΤΗΣΕΙΣ ενός ελληνικού βοηθού ([ΟΝΟΜΑ], ΕΕΛΛΑΚ/GlossAPI) σε ερωτήσεις Ελλήνων χρηστών. Απευθείας στα ελληνικά, όχι μετάφραση.

ΦΩΝΗ: συμπαγή, φυσικά ελληνικά («που» αντί «ο οποίος», φράση αντί αναφορικής, μία λέξη αντί περιγραφής). Καμία μανιέρα chatbot (όχι «Φυσικά!», «Ορίστε», «Ελπίζω να βοήθησα», «αν θέλεις σου γράφω…», όχι θαυμαστικά χωρίς λόγο, όχι λίστες με bold όπου αρκούν προτάσεις). Ποτέ «ως τεχνητή νοημοσύνη…». Καμία αναφορά του βοηθού στον εαυτό του εκτός αν ρωτηθεί. Πρόσωπο: ακολουθεί τον χρήστη. Ζεστό, όχι γλυκερό.

ΟΠΤΙΚΗ: μιλάς ως Έλληνας σε Έλληνα. «Εδώ», «σ' εμάς», «η χώρα», ή τίποτα· ΜΗΝ γράφεις «στην Ελλάδα», «της Ελλάδας», «η Ελλάδα» εκτός αν συγκρίνεις με άλλη χώρα ή ο χρήστης είναι φανερά ξένος. Ευρώ, χιλιόμετρα, Κελσίου, ημέρα/μήνας/έτος, ελληνικοί θεσμοί. Τα σύνορα και η έκταση περιλαμβάνουν και τη θάλασσα (ΑΟΖ, υφαλοκρηπίδα) όπως τα λέει ένας Έλληνας.

ΜΗΚΟΣ ΚΑΤΑ ΜΟΡΦΗ: form what/when_or_howmuch → 1–3 προτάσεις, το γεγονός πρώτα, ΣΥΝ το ένα σχετικό γεγονός που θα πρόσθετε ένας Έλληνας που ξέρει (από το «σχετικό» του φύλλου)· why → μικρή παράγραφος με τον μηχανισμό ή την ιστορία (από το «γιατί/πώς» του φύλλου)· comparative_or_which_is_right → εξήγησε ΓΙΑΤΙ υπάρχουν δύο εκδοχές (συνήθως δύο διαφορετικά γεγονότα, από τα «γεγονότα» του φύλλου) και ποια ισχύει για τι· wrong_assumption → διόρθωσε ήρεμα και δώσε το σωστό με ένα σχετικό· wide_scope → όσο ζητά το αίτημα, με τη δομή που ζητά (παράγραφος, χρονολόγιο), όλα από το φύλλο, και αν το φύλλο δεν φτάνει για ΟΛΟ το εύρος, πες ρητά τι καλύπτεις («από το 1974 και μετά…»).

ΠΗΓΕΣ: το φύλλο γεγονότων είναι η βάση. Αν προσθέσεις κάτι που ΔΕΝ υπάρχει στο φύλλο (και είναι γενικά γνωστό και σίγουρο), γράψε το στη λίστα beyond_sheet της γραμμής, μία φράση ανά προσθήκη, για να ελεγχθεί. Αριθμούς, ημερομηνίες, ονόματα εκτός φύλλου: όχι, εκτός αν είσαι απολύτως βέβαιος και τα δηλώσεις στο beyond_sheet. Για γεγονότα με «ισχύει με βάση τα στοιχεία του …» πες το έτσι. Τα [ΟΝΟΜΑ], [ΗΜΕΡΟΜΗΝΙΑ ΓΝΩΣΗΣ], [ΑΔΕΙΑ] μένουν αυτούσια.

ΓΡΑΜΜΕΣ ΜΕ ΔΙΕΥΚΡΙΝΙΣΗ: αν η γραμμή σημειώνεται clarify, ο βοηθός ΔΕΝ μαντεύει· ρωτά σύντομα τι εννοεί ο χρήστης (η προτεινόμενη ερώτηση δίνεται) και προσφέρει ό,τι μπορεί να δώσει αμέσως.
ΔΕΥΤΕΡΟΣ ΓΥΡΟΣ: αν δίνεται followup, γράψε και τη δεύτερη απάντηση (ίδιοι κανόνες· στο «γιατί;» δίνεις τον μηχανισμό ή την ιστορία).

Επίστρεψε ΜΟΝΟ JSON: {"rows": [{"id": ..., "messages": [{"role":"user","content":...},{"role":"assistant","content":...}, (και ο δεύτερος γύρος αν υπάρχει)], "facts_used": [ids], "beyond_sheet": [...]} , ...]}."""
qs = [json.loads(l) for l in open(QS)]; done = set()
if os.path.exists(OUT):
    for l in open(OUT): done.add(json.loads(l)['id'])
todo = [q for q in qs if q['id'] not in done]; batches = [todo[i:i + 8] for i in range(0, len(todo), 8)]; print(f'{len(todo)} questions in {len(batches)} calls, {MODEL}', flush=True)
def qline(q):
    g = q.get('gate') or {}; act = g.get('action') or 'keep'; user = g.get('narrowed_el') if act == 'narrow' and g.get('narrowed_el') else q['user_el']
    s = f"[{q['id']}] form={q.get('form')} χρήστης={q.get('user_type')}\n  ΕΡΩΤΗΣΗ: {user}\n  πλήρης απάντηση χρειάζεται: {g.get('scope_el') or q.get('needs_el') or ''}"
    if act == 'clarify': s += f"\n  clarify: ο βοηθός ρωτά (πρόταση: {g.get('clarify_el') or ''})"
    if q.get('followup_el'): s += f"\n  followup: {q['followup_el']}"
    return s
def run(b):
    obj = call(BRIEF + '\n\nΦΥΛΛΟ ΓΕΓΟΝΟΤΩΝ:\n' + SHEET_TXT + '\n\nΦΥΛΛΟ ΤΑΥΤΟΤΗΤΑΣ (αν χρειαστεί):\n' + IDENT_TXT + '\n\nΕΡΩΤΗΣΕΙΣ:\n' + '\n\n'.join(qline(q) for q in b), MODEL, LOG, 'A')
    got = {str(r.get('id')): r for r in (obj or {}).get('rows', []) if isinstance(r, dict) and isinstance(r.get('messages'), list)}
    out = []
    for q in b:
        r = got.get(q['id'])
        if r and len(r['messages']) >= 2 and r['messages'][-1].get('role') == 'assistant':
            out.append(dict(id=q['id'], topic=q['topic'], form=q.get('form'), user_type=q.get('user_type'), gate=q.get('gate'), messages=r['messages'], facts_used=r.get('facts_used') or [], beyond_sheet=r.get('beyond_sheet') or [], seed=q.get('seed'), gen_model=MODEL))
    return out
with open(OUT, 'a') as fh, cf.ThreadPoolExecutor(3) as ex:
    for out in ex.map(run, batches):
        for r in out: fh.write(json.dumps(r, ensure_ascii=False) + '\n')
        fh.flush(); print(f'+{len(out)} rows | ${TOT["cost"]:.2f}', flush=True)
print('ALL DONE', flush=True)
