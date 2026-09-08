#!/usr/bin/env python3
"""Prompt generator for the Greek instruction-following set: subjects × question forms × personas × constraint sets (levels 1–5).
Writes prompts.jsonl with the request, the constraint list (family, params, text, checkable) and the metadata needed for the pilot
readouts (domain, subtopic, form, persona, level, phrasing variant). No model calls.
Usage: python3 gen_prompts.py <out.jsonl> --n 300 [--seed 7] [--levels 1,2,3,4,5 --level-weights .3,.3,.2,.12,.08] [--families a,b,c] [--domains d1,d2]
   --design E1 (40 rows per checkable family, level 1) | E2 (60 per level) | E3 (15 per domain, level 2) | E4 (20 per form, level 2) | E5 (Greek-only families, 40 each) | E6 (60 pairs × 3 phrasings)"""
import argparse, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import constraints as C

DOMAINS = {
 'καθημερινότητα': ['σπίτι και επισκευές', 'ψώνια και σούπερ μάρκετ', 'γείτονες και πολυκατοικία', 'μετακίνηση στην πόλη', 'κατοικίδια'],
 'δημόσιες υπηρεσίες': ['ΚΕΠ και πιστοποιητικά', 'ΑΑΔΕ και φορολογική δήλωση', 'ΕΦΚΑ και ένσημα', 'ΕΟΠΥΥ και συνταγές', 'δήμος και δημοτικά τέλη', 'ΔΕΗ και λογαριασμοί', 'διαβατήριο και ταυτότητα'],
 'εργασία': ['βιογραφικό', 'συνέντευξη', 'σύμβαση και άδειες', 'επαγγελματικό email', 'μισθός και εκκαθαριστικό'],
 'εκπαίδευση': ['δημοτικό', 'Πανελλαδικές', 'πανεπιστήμιο και Erasmus', 'φροντιστήριο', 'ξένες γλώσσες'],
 'υγεία': ['κρυολόγημα και πυρετός', 'διατροφή', 'ύπνος και άγχος', 'φαρμακείο και εφημερίες', 'ραντεβού με γιατρό'],
 'φαγητό': ['συνταγές', 'νηστεία και νηστίσιμα', 'εστιατόριο και παραγγελία', 'παρασκευή για πολλούς', 'ελληνικά προϊόντα'],
 'ταξίδια στην Ελλάδα': ['νησιά και πλοία', 'ορεινά χωριά', 'ΚΤΕΛ και τρένο', 'αρχαιολογικοί χώροι', 'κάμπινγκ'],
 'ταξίδια στο εξωτερικό': ['βίζα και έγγραφα', 'πτήσεις', 'διαμονή', 'χρήματα και κάρτες', 'ασφάλεια ταξιδιού'],
 'ιστορία και πολιτισμός': ['1821', 'Πολυτεχνείο', 'Βυζάντιο', 'Μικρασιατική καταστροφή', 'παραδόσεις και γιορτές', 'μουσική'],
 'γλώσσα': ['ορθογραφία και τόνοι', 'σημασία λέξεων', 'ετυμολογία', 'greeklish', 'διάλεκτοι', 'πολυτονικό'],
 'επιστήμη': ['σεισμοί', 'καιρός και κλίμα', 'διάστημα', 'βιολογία', 'χημεία στην κουζίνα'],
 'τεχνολογία': ['κινητό και εφαρμογές', 'ασφάλεια κωδικών', 'ηλεκτρονικές αγορές', 'gov.gr wallet', 'υπολογιστής και αρχεία'],
 'χρήματα': ['λογαριασμοί', 'δάνεια', 'ενοίκιο', 'αποταμίευση', 'φόροι ακινήτων'],
 'αθλητισμός': ['ποδόσφαιρο', 'μπάσκετ', 'κολύμβηση', 'Ολυμπιακοί', 'τοπικοί αγώνες'],
 'τέχνες και ΜΜΕ': ['κινηματογράφος', 'θέατρο', 'βιβλία', 'τηλεόραση και ΕΡΤ', 'φωτογραφία'],
 'σχέσεις και εθιμοτυπία': ['ευχές και γιορτές', 'γάμος και βάφτιση', 'συλλυπητήρια', 'φιλίες', 'διαφωνίες στην οικογένεια'],
}
_SUBTOPICS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'subtopics.json')
if os.path.exists(_SUBTOPICS) and not os.environ.get('GREEK_IF_NO_SUBTOPICS'):   # the Sol-expanded tree from gen_subtopics.py replaces the hand-written leaves
    DOMAINS = {d: list(v) for d, v in json.load(open(_SUBTOPICS)).items()}
FORMS = {
 'quick_fact': ['Πες μου σύντομα {what} για {sub}.', 'Τι ισχύει με {sub}; Μία γρήγορη απάντηση.'],
 'explanation': ['Εξήγησέ μου πώς λειτουργεί το θέμα «{sub}».', 'Γιατί συμβαίνει αυτό με {sub}; Εξήγησέ το.'],
 'howto': ['Δώσε μου βήμα προς βήμα οδηγίες για {sub}.', 'Πώς το κάνω σωστά, {sub}; Θέλω τα βήματα.'],
 'comparison': ['Σύγκρινε δύο επιλογές που έχω σχετικά με {sub} και πες ποια προτιμάς.', 'Ποιο είναι καλύτερο για {sub}, το ένα ή το άλλο; Σύγκρινέ τα.'],
 'opinion': ['Ποια είναι η γνώμη σου για {sub}; Με επιχειρήματα.', 'Αξίζει τον κόπο {sub}; Πες μου τι πιστεύεις και γιατί.'],
 'creative': ['Γράψε ένα μικρό ποίημα για {sub}.', 'Γράψε μια σύντομη διαφήμιση για {sub}.', 'Γράψε μια μικρή ιστορία με θέμα {sub}.'],
 'rewrite': ['Ξαναγράψε το παρακάτω κείμενο για {sub}:\n\n{text}', 'Διόρθωσε και βελτίωσε το κείμενο που ακολουθεί (θέμα: {sub}):\n\n{text}'],
 'summarise': ['Συνόψισε το παρακάτω κείμενο για {sub}:\n\n{text}', 'Κάνε μου περίληψη αυτού (θέμα {sub}):\n\n{text}'],
 'translate': ['Μετάφρασε στα αγγλικά το παρακάτω κείμενο για {sub}:\n\n{text}', 'Απόδωσε στα αγγλικά αυτό το κείμενο (θέμα {sub}):\n\n{text}'],
 'list': ['Κάνε μου μια λίστα με τα βασικά για {sub}.', 'Ποια είναι τα κύρια σημεία για {sub}; Σε λίστα.'],
 'planning': ['Φτιάξε μου ένα πλάνο για {sub}.', 'Οργάνωσέ μου ένα πρόγραμμα σχετικά με {sub}.'],
 'correction': ['Νομίζω ότι {wrong}. Σωστά; Διόρθωσέ με αν κάνω λάθος, σχετικά με {sub}.', 'Άκουσα ότι {wrong}. Ισχύει; (θέμα: {sub})'],
}
WHATS = ['το πιο σημαντικό', 'τι πρέπει να ξέρω', 'τα βασικά', 'πού απευθύνομαι', 'πόσο κοστίζει']
WRONGS = ['δεν χρειάζεται καθόλου χαρτιά', 'γίνεται μόνο τον Αύγουστο', 'το κάνουν μόνο στην Αθήνα', 'είναι δωρεάν για όλους', 'καταργήθηκε πέρυσι']
TEXTS = [
 'Ο δήμος ανακοίνωσε ότι από την επόμενη εβδομάδα η αποκομιδή απορριμμάτων θα γίνεται τρεις φορές την εβδομάδα αντί για δύο, λόγω της αύξησης του όγκου. Οι κάτοικοι παρακαλούνται να βγάζουν τους κάδους μετά τις οκτώ το βράδυ.',
 'Το κατάστημα λειτουργεί καθημερινά από τις εννέα το πρωί έως τις εννέα το βράδυ, εκτός Κυριακής. Οι επιστροφές γίνονται μέσα σε δεκατέσσερις ημέρες με την απόδειξη, και το προϊόν πρέπει να είναι αχρησιμοποίητο.',
 'Η εγγραφή στο μάθημα γίνεται ηλεκτρονικά. Χρειάζεται ταυτότητα, μία φωτογραφία και το αποδεικτικό πληρωμής. Οι θέσεις είναι περιορισμένες και τηρείται σειρά προτεραιότητας.',
 'Το πλοίο για το νησί αναχωρεί δύο φορές την ημέρα, νωρίς το πρωί και το απόγευμα. Το ταξίδι διαρκεί περίπου τέσσερις ώρες, και τα εισιτήρια κόβονται από το γραφείο στο λιμάνι ή διαδικτυακά.',
 'Η ανακύκλωση χαρτιού και πλαστικού γίνεται στους μπλε κάδους. Τα γυάλινα μπουκάλια πηγαίνουν στους πράσινους κώδωνες, ενώ οι μπαταρίες σε ειδικά κουτιά στα σούπερ μάρκετ.',
 'Ο σεισμός των 5,2 βαθμών έγινε αισθητός σε όλη την περιοχή, χωρίς να αναφερθούν ζημιές ή τραυματισμοί. Οι αρχές συνιστούν ψυχραιμία και έλεγχο των παλαιών κτισμάτων.',
]
PERSONAS = [
 ('μαθητής γυμνασίου που γράφει χωρίς τόνους', 'atonic'), ('συνταξιούχος με πληθυντικό ευγενείας', 'formal'), ('ομογενής που γράφει greeklish', 'greeklish'),
 ('δημόσιος υπάλληλος', 'formal'), ('δημοσιογράφος', 'neutral'), ('νοσηλεύτρια', 'neutral'), ('αγρότης', 'casual'), ('φοιτήτρια στο εξωτερικό', 'casual'),
 ('ιδιοκτήτης μικρού μαγαζιού', 'casual'), ('βοηθός δικηγόρου', 'formal'), ('τουρίστας που μαθαίνει ελληνικά', 'simple'), ('μητέρα δύο παιδιών', 'casual'),
 ('υπάλληλος ΚΕΠ', 'formal'), ('καθηγήτρια φροντιστηρίου', 'neutral'), ('ναυτικός', 'casual'), ('μαθητής Γ΄ Λυκείου', 'casual'),
 ('προγραμματιστής', 'neutral'), ('γιαγιά που μόλις έμαθε κινητό', 'simple'), ('φοιτητής νομικής', 'formal'), ('οδηγός ταξί', 'casual'),
]
def greeklish(s):
    m = dict(zip('αβγδεζηθικλμνξοπρστυφχψωάέήίόύώϊϋ', ['a','b','g','d','e','z','i','th','i','k','l','m','n','x','o','p','r','s','t','y','f','x','ps','w','a','e','i','i','o','y','w','i','y']))
    return ''.join(m.get(ch, m.get(ch.lower(), ch).upper() if ch.isupper() else ch) for ch in s)
def surface(text, style, rng):
    if style == 'atonic': return C.strip_accents(text).replace('ϊ', 'ι').replace('ϋ', 'υ')
    if style == 'greeklish' and rng.random() < 0.7: return greeklish(text.lower())
    if style == 'formal': return text.replace('Πες μου', 'Θα μπορούσατε να μου πείτε').replace('Δώσε μου', 'Θα ήθελα').replace('Εξήγησέ μου', 'Εξηγήστε μου')
    if style == 'simple': return text.replace(';', ';').replace('Εξήγησέ μου', 'Πες μου απλά')
    return text

BANK = {}   # (domain, subtopic, form) -> authored requests, loaded with --requests
ADDRESS = {'formal_plural', 'informal_singular', 'formal_and_informal', 'child_register'}
TRANSLATE_OK = {'length_words_max', 'length_words_min', 'length_sentences_exact', 'length_paragraphs', 'title', 'no_comma', 'no_exclamation', 'all_lower', 'wrap_in_quotes', 'two_responses', 'bullets_n', 'highlight_n', 'end_with', 'start_with', 'postscript', 'keywords_exclude'}   # a translation must keep the content: only form constraints apply
FORM_EXCLUDE = {'translate': set(C.FAMILIES) - TRANSLATE_OK,
                'summarise': ADDRESS, 'rewrite': ADDRESS - {'formal_plural', 'informal_singular'}}   # constraints that cannot apply to the task are never drawn for it
def build(rng, domain, sub, form, persona, level, families=None, phrasing_seed=None, fixed_seed=None):
    tmpl = rng.choice(FORMS[form]); text = rng.choice(TEXTS); authored = BANK.get((domain, sub, form))
    if authored:
        fresh = [b for b in authored if not b.get('_used')] or authored   # each authored request is used once per build (no shared prefixes from reuse)
        b = rng.choice(fresh); b['_used'] = True; req = b['text']; persona = (b['persona'], b['persona_style']); text = None
    else: req = tmpl.format(sub=sub, what=rng.choice(WHATS), wrong=rng.choice(WRONGS), text=text)
    fams = [f for f in (families or list(C.FAMILIES)) if f not in FORM_EXCLUDE.get(form, set())]
    cons = C.sample_constraints(random.Random(fixed_seed) if fixed_seed is not None else rng, level, fams)
    if not cons: return None
    if fixed_seed is not None:   # E6: same families and params, the phrasing re-drawn per variant
        for c in cons: c['phrasing'] = rng.randrange(len(C.FAMILIES[c['family']]['phrasings'])); c['text'] = C.FAMILIES[c['family']]['phrasings'][c['phrasing']].format(**c['params'])
    lines = [c['text'] for c in cons]; rng.shuffle(lines)
    req = surface(req, persona[1], rng) if not authored else req; lines = [surface(l, persona[1], rng) for l in lines]   # request and constraints take the writer's surface separately, so the stored request is what the model saw
    layout = rng.random()
    if layout < 0.55: prompt = req + '\n\n' + ' '.join(lines)                       # request, then the constraints
    elif layout < 0.8: prompt = ' '.join(lines) + '\n\n' + req                      # constraints first
    else: prompt = req + ' ' + lines[0] + ('\n\n' + ' '.join(lines[1:]) if len(lines) > 1 else '')   # split
    if rng.random() < 0.1 and cons: prompt += '\n\n' + rng.choice(['Το ξαναλέω: ', 'Προσοχή: ']) + cons[0]['text']
    return dict(prompt=prompt, request=req, constraints=cons, level=len(cons), domain=domain, subtopic=sub, form=form, persona=persona[0], persona_style=persona[1], source_text=text if (text and '{text}' in tmpl) else None, authored=bool(authored))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--n', type=int, default=300); ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--levels', default='1,2,3,4,5'); ap.add_argument('--level-weights', default='.3,.3,.2,.12,.08'); ap.add_argument('--families', default=''); ap.add_argument('--domains', default=''); ap.add_argument('--design', default=''); ap.add_argument('--requests', default='', help='authored request bank from gen_requests.py')
    a = ap.parse_args(); rng = random.Random(a.seed); rows = []
    if a.requests:
        for l in open(a.requests): b = json.loads(l); BANK.setdefault((b['domain'], b['subtopic'], b['form']), []).append(b)
        print('request bank:', sum(len(v) for v in BANK.values()), 'requests in', len(BANK), 'cells')
    levels = [int(x) for x in a.levels.split(',')]; weights = [float(x) for x in a.level_weights.split(',')]
    fams = a.families.split(',') if a.families else None; doms = a.domains.split(',') if a.domains else list(DOMAINS)
    def cell(**kw):
        d = kw.get('domain') or rng.choice(doms); s = kw.get('sub') or rng.choice(DOMAINS[d]); f = kw.get('form') or rng.choice(list(FORMS)); p = kw.get('persona') or rng.choice(PERSONAS)
        return build(rng, d, s, f, p, kw.get('level') or rng.choices(levels, weights)[0], kw.get('families', fams), kw.get('phrasing_seed'))
    if a.design == 'E1':
        for fam in C.CHECKABLE:
            for _ in range(40): r = cell(level=1, families=[fam]); rows.append(r) if r else None
    elif a.design == 'E2':
        for lvl in (1, 2, 3, 4, 5):
            for _ in range(60): r = cell(level=lvl); rows.append(r) if r else None
    elif a.design == 'E3':
        for d in DOMAINS:
            for _ in range(15): r = cell(domain=d, level=2); rows.append(r) if r else None
    elif a.design == 'E4':
        for f in FORMS:
            for _ in range(20): r = cell(form=f, level=2); rows.append(r) if r else None
    elif a.design == 'E5':
        for fam in ['no_accents', 'all_caps_greek', 'greeklish_only', 'formal_plural', 'monotonic_only', 'greek_question_mark', 'ano_teleia_list', 'numbered_greek', 'wrap_in_quotes']:
            for _ in range(40): r = cell(level=1, families=[fam]); rows.append(r) if r else None
    elif a.design == 'E4x':
        for f in ('translate', 'summarise', 'rewrite'):
            for _ in range(30): r = cell(form=f, level=2); rows.append(r) if r else None
    elif a.design == 'E7':
        for fam in [n for n in C.FAMILIES if not C.FAMILIES[n]['checkable']]:
            for _ in range(20): r = cell(level=1, families=[fam]); rows.append(r) if r else None
    elif a.design == 'E6':
        for i in range(60):
            d = rng.choice(doms); s = rng.choice(DOMAINS[d]); f = rng.choice(list(FORMS)); p = rng.choice(PERSONAS); seed = 1000 + i
            for v in range(3):
                r = build(random.Random(seed * 10 + v), d, s, f, p, 2, fams, fixed_seed=seed)
                if r: r['pair_id'] = i; r['variant'] = v; rows.append(r)
    else:
        while len(rows) < a.n:
            r = cell(); rows.append(r) if r else None
    for i, r in enumerate(rows): r['id'] = f'{a.design or "mix"}{"a" if a.requests else ""}_{a.seed}_{i:05d}'
    with open(a.out, 'w') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    import collections
    print(len(rows), 'prompts →', a.out); print('levels', dict(collections.Counter(r['level'] for r in rows))); print('families', len({c['family'] for r in rows for c in r['constraints']}), 'domains', len({r['domain'] for r in rows}), 'forms', len({r['form'] for r in rows}))

if __name__ == '__main__': main()
