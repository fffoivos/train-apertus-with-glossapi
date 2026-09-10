#!/usr/bin/env python3
"""MultiChallenge-el v3 after the third Claude pass: (1) quarantine five more target questions (263 usable) and the Greek τ-lipogram row; (2) re-translate WHOLE
conversations (one Sol call each, high effort, target question included) for every row the third pass found defective — with the checker's notes, a single
address register per conversation, identical Greek for identical English passages (version-editing rows), and Greek number/unit/time/month conventions;
(3) a mechanical post-pass on all rows (a.m./p.m., English month names, unit words, thousands separators outside code); (4) freeze v3. Usage: python3 retranslate_v3.py"""
import json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
from translate import SCHEMA, AXIS_EL
QUAR = {'6765f48a4421592a0e41c067': 'banned pronoun list collides with Greek articles/clitics (Greek-introduced)', '6781aa5341e87994fefeced6': 'target refers to an English section that does not exist once the email is Greek (Greek-introduced)',
        '6765f83933f9e1448cddbeea': 'target polarity garbled in the English (refuse a drink or drink)', '6781a94837c7655a14201b42': 'target asks about a dairy ban the history never states (inherited)', '6765f83aa5d32b513353ec07': 'asserted ranking does not follow from the stated costs (inherited)',
        '6765f1c86539ceefe4b7ab4f': 'Greek τ-lipogram: the demonstration turn cannot avoid τ in natural Greek (adaptation failed)'}
NOTES = {'674567322c2fb9897564643d': 'spaced repetition = «διαστηματική επανάληψη» everywhere (never «διαστημική»), also in the target question', '67455ecd538d78476d827be2': 'the SAME English poem appears in several turns: render it IDENTICALLY every time; dates/times in Greek (δέκα Δεκεμβρίου, εφτά το βράδυ)',
         '6765f48beb530881587044e9': '«Award-Winning Campaign Strategist» = «Βραβευμένος Στρατηγικός Σχεδιαστής Καμπανιών» in every version; identical English sentences → identical Greek', '6781ad8bec8b2f94d989103a': '«amicably» → «φιλικά» in the letter, and the later instruction must quote exactly the word used in the letter; the sign-off must NOT be «Φιλικά»',
         '674567323acc22154b07d657': 'units in Greek everywhere (μπύρα του ενός λίτρου)', '6781a948bacd5cfcbbb37656': 'inches → ίντσες everywhere with the same numbers', '6781aa53113b7dd6a81d27cb': 'feet/miles → πόδια/μίλια with the same numbers',
         '6781ad8b7d5d4b7679627100': 'the email drafts in the English are 4-space-indented code blocks in turns 1/3/5/7: keep that formatting in Greek so the later complaint about code blocks makes sense', '6781aa53a73754153f69ca1c': 'one address register (εσύ or εσείς) for the whole conversation; placeholders identical everywhere',
         '67456858ec557fa45f219f0b': '«My partner is a vegetarian» = only the partner is vegetarian, not the user', '6765fcbbd0cf10a192c5a702': 'vegan = «vegan / για vegan», never «χορτοφάγους»', '6765fc5e0af93a24e8fbe4ee': 'dates in Greek (Πέμπτη 16 Ιανουαρίου 2025; 28 Φεβρουαρίου 2025), times π.μ./μ.μ.; "liberty, freedom" → «ελευθερία, λευτεριά»',
         '6765f44133f9e1448cddbc84': 'the graded opening phrase must be rendered exactly and without an added ellipsis', '6781aad819cf84439e50c47b': 'all clock times as π.μ./μ.μ.', '67456856ceecce35027ef5a3': 'dates in Greek (9 Ιανουαρίου 2025)', '6765f4894421592a0e41c049': 'five feet → πέντε πόδια', '674567312e803a593c6b1d5a': '"newly bought" → «νεοαγορασμένο», "duvet" → «πάπλωμα»',
         '6781ad8b92c79eaae6b4cd68': 'one register throughout; «αριθμημένη» vs «ταξινομημένη»: use one term for the same English label everywhere', '6781adc5d2b793f40a8cd766': 'quoted résumé lines must match the bullet exactly (Διεξήγαγε…)'}
CONS = ['674567d0b9d767170e9698a4', '674567d234449d2a595f555c', '674568560907ad2ffaaf961a', '67456856ce39067956b7f7ab', '6745685836eac86fba54197f', '6765f4401329ce7263214866', '6765f48922031589ce9b4035', '6765f48a6c52e524f4a22e24', '6765f83aef494d11e9e10701', '6781a948d2b793f40a8cd6c7', '6781aad8fc48f01aa67baba1', '67455bc84f79e78f4a63c837', '6765f839a02fd129919ef243']
MONTHS = {'January': 'Ιανουαρίου', 'February': 'Φεβρουαρίου', 'March': 'Μαρτίου', 'April': 'Απριλίου', 'May': 'Μαΐου', 'June': 'Ιουνίου', 'July': 'Ιουλίου', 'August': 'Αυγούστου', 'September': 'Σεπτεμβρίου', 'October': 'Οκτωβρίου', 'November': 'Νοεμβρίου', 'December': 'Δεκεμβρίου'}
UNITS = {'feet': 'πόδια', 'foot': 'πόδι', 'inches': 'ίντσες', 'inch': 'ίντσα', 'miles': 'μίλια', 'mile': 'μίλι', 'pounds': 'λίβρες', 'gallons': 'γαλόνια', 'litre': 'λίτρο', 'litres': 'λίτρα', 'liter': 'λίτρο', 'liters': 'λίτρα'}


def post(text):
    """Mechanical conventions in Greek prose outside code blocks: a.m./p.m., English month names after a day number, unit words after a number, thousands separators."""
    parts = re.split(r'(```.*?```|(?:^ {4}.*\n?)+)', text, flags=re.S | re.M); out = []
    for i, p in enumerate(parts):
        if i % 2 == 1: out.append(p); continue
        p = re.sub(r'(\d)\s*(a\.m\.|am|AM|A\.M\.)\b', r'\1 π.μ.', p); p = re.sub(r'(\d)\s*(p\.m\.|pm|PM|P\.M\.)\b', r'\1 μ.μ.', p)
        for en, el in MONTHS.items(): p = re.sub(rf'\b{en}\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s*(\d{{4}})?', lambda m: f"{m.group(1)} {el}" + (f" {m.group(2)}" if m.group(2) else ''), p); p = re.sub(rf'\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{en}\b', rf'\1 {el}', p)
        for en, el in UNITS.items(): p = re.sub(rf'(\d)\s*(-\s*)?{en}\b', rf'\1 {el}', p)
        p = re.sub(r'(?<![\d.,])(\d{1,3})(,\d{3})+(?![\d,])', lambda m: m.group(0).replace(',', '.'), p)   # 50,000 → 50.000 (never touches decimals like 3.75)
        out.append(p)
    return ''.join(out)


def retranslate(r):
    conv = r['turns_en']; text = '\n\n'.join(f"[{i}] {m['role'].upper()}:\n{m['content']}" for i, m in enumerate(conv)); note = NOTES.get(r['id'], '')
    prompt = (B.RULES_EL + f"\n\nΞαναμετάφρασε ΟΛΟΚΛΗΡΗ αυτή τη συζήτηση MultiChallenge (άξονας {r['axis']}: {AXIS_EL[r['axis']]}) και την ερώτηση-κριτήριο, γιατί η προηγούμενη απόδοση είχε λάθη. "
              f"ΥΠΟΧΡΕΩΤΙΚΟΙ ΚΑΝΟΝΕΣ: (α) ένας ενικός/πληθυντικός ευγενείας για τον ίδιο συνομιλητή σε ΟΛΗ τη συζήτηση, όπως στον πρώτο γύρο· (β) αν το ίδιο αγγλικό κείμενο (ποίημα, email, λίστα, προφίλ) εμφανίζεται σε περισσότερους γύρους, η ελληνική απόδοση είναι ΤΑΥΤΟΣΗΜΗ σε όλους· "
              f"(γ) αριθμοί με ελληνική μορφή στην πεζή γλώσσα (50.000· 3,75), ώρες π.μ./μ.μ., μήνες στα ελληνικά, μονάδες στα ελληνικά με τις ίδιες τιμές (πόδια, ίντσες, μίλια), ημερομηνίες στα ελληνικά· (δ) ό,τι ζητά η ερώτηση-κριτήριο (φράσεις, όροι, ονόματα) με τις ΙΔΙΕΣ μορφές μέσα στη συζήτηση και στο κριτήριο· "
              f"(ε) η μορφοποίηση (μπλοκ κώδικα με 4 κενά, κουκκίδες, τίτλοι) ίδια με το αγγλικό. {('ΣΗΜΕΙΩΣΗ ΕΛΕΓΚΤΗ: ' + note) if note else ''}\n\nΣΥΖΗΤΗΣΗ ({len(conv)} γύροι):\n{text}\n\nΕΡΩΤΗΣΗ-ΚΡΙΤΗΡΙΟ: {r['target_question_en']}\n\nΕπίστρεψε JSON {{\"turns_el\":[{len(conv)} strings],\"target_question_el\",\"entities\",\"nontransferable\",\"reason\"}}.")
    j = B.sol_json(prompt, SCHEMA, effort='high', timeout=1800)
    if not j or len(j['turns_el']) != len(conv): print('retranslate failed', r['id'], flush=True); return None
    return dict(id=r['id'], turns_el=[dict(role=m['role'], content=t) for m, t in zip(conv, j['turns_el'])], target_question_el=j['target_question_el'])


def main():
    path = os.path.join(HERE, 'conversations_el_final.jsonl'); rows = B.load(path); shutil.copy(path, path + '.v2')
    cc3 = {c['id']: c for c in B.load(os.path.join(HERE, 'crosscheck3_conv_claude.jsonl'))}
    for r in rows:
        if r['id'] in QUAR: r['excluded'] = (r.get('excluded') or '') + ('; ' if r.get('excluded') else '') + 'quarantined (pass 3): ' + QUAR[r['id']]
    todo = [r for r in rows if not r.get('excluded') and (r['id'] in NOTES or r['id'] in CONS or (cc3.get(r['id'], {}).get('fidelity') == 'no') or (cc3.get(r['id'], {}).get('consistency') == 'no'))]
    print('quarantined total', sum(bool(r.get('excluded')) for r in rows), '| whole-conversation re-translations', len(todo), flush=True)
    done = {d['id']: d for d in B.run_jobs(todo, retranslate, os.path.join(HERE, 'retranslate_v3_out.jsonl'), stage='mc retranslate v3', workers=12)}
    for r in rows:
        if r['id'] in done: r['turns_el'] = done[r['id']]['turns_el']; r['target_question_el'] = done[r['id']]['target_question_el']; r['provenance']['retranslated_v3'] = True
        for m in r['turns_el']: m['content'] = post(m['content'])
        r['target_question_el'] = post(r['target_question_el']); r['provenance']['post_pass_v3'] = True
    with open(path, 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    usable = [r for r in rows if not r.get('excluded')]; s = json.load(open(os.path.join(HERE, 'summary.json')))
    s.update(version=3, usable=len(usable), excluded=[dict(id=r['id'], reason=r['excluded']) for r in rows if r.get('excluded')], retranslated_v3=len(done),
             crosscheck3='target questions: 263 valid / 4 invalid / 6 underdetermined (all 10 now quarantined; 7 inherited from the English); conversations (75 = 15 repaired + 1 chunked + 3 late + 56 random): fidelity no 19 (random 11/56 = 19.6%, 5 content-bearing = 8.9%, CI 3.9–19.3%), consistency no 20 (mostly εσύ/εσείς), naturalness ≤3: 6; 9 of the 15 one-turn repairs still defective (3 made worse by the repair) → whole conversations re-translated with the checker notes; 0 role labels; number multisets agree 261/273 with all differences explained',
             known_limits='the v3 re-translations and the mechanical post-pass (a.m./p.m., months, units, thousands) are NOT yet re-checked (fourth pass pending); register consistency is enforced by instruction only; the unchecked conversation 6765f839a02fd129919ef243 was included in the re-translation set')
    json.dump(s, open(os.path.join(HERE, 'summary.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps(dict(rows=len(rows), usable=len(usable), retranslated=len(done))))


if __name__ == '__main__': main()
