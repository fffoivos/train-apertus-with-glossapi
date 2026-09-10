#!/usr/bin/env python3
"""MultiChallenge-el repair after the Claude cross-check: (1) strip role labels that Sol prepended to Greek turns in 31 rows (USER:/ASSISTANT:/ΧΡΗΣΤΗΣ:/ΒΟΗΘΟΣ:,
with or without [i]); (2) apply the target-question fix; (3) handle the non-transferable rows as recommended (adapt two, exclude one, keep three);
(4) re-translate the worst turn(s) of every conversation the cross-check marked fidelity=no, giving Sol the checker's note; (5) freeze conversations_el_final.jsonl
+ summary.json with the measured sample defect rates. Usage: python3 repair.py"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
LABEL = re.compile(r'^\s*(\[\d+\]\s*)?(USER|ASSISTANT|ΧΡΗΣΤΗΣ|ΒΟΗΘΟΣ)\s*:\s*\n?', re.I)
S_TURN = B.M.write_schema('s_mcturn.json', {"type": "object", "properties": {"turn_el": {"type": "string"}, "note": {"type": "string"}}, "required": ["turn_el", "note"], "additionalProperties": False})
EXCLUDE = {'67456856ff33175f5b310ec3'}; ADAPT_T = {'6765f1c86539ceefe4b7ab4f'}; ADAPT_WORDS = {'6765f4467e4dcd5e2143350a'}


def retranslate_turn(r, i, note):
    conv = r['turns_en']; ctx = '\n\n'.join(f"[{k}] {m['role'].upper()}: {m['content'][:600]}" for k, m in enumerate(r['turns_el'][:i]))
    prompt = (B.RULES_EL + f"\n\nΔιόρθωσε τη μετάφραση ΕΝΟΣ γύρου μιας συζήτησης MultiChallenge (άξονας {r['axis']}). Ο ανεξάρτητος ελεγκτής σημείωσε: «{note}». Κράτησε τις ίδιες αποδόσεις όρων με τους προηγούμενους γύρους: {r['entities'][:400]}. "
              "Αριθμοί, μονάδες και μορφές: ελληνική γραφή στην πεζή γλώσσα (50.000, 3,75, 2:00 μ.μ., μίλια/πόδια με την αγγλική τιμή διατηρημένη), ίδιο πρόσωπο/αριθμός ευγενείας με τους προηγούμενους γύρους, καμία ετικέτα ρόλου, κώδικας και μορφοποίηση όπως το αγγλικό.\n\n"
              f"ΠΡΟΗΓΟΥΜΕΝΟΙ ΓΥΡΟΙ (ελληνικά, συντομευμένοι):\n{ctx}\n\nΓΥΡΟΣ [{i}] ΑΓΓΛΙΚΑ ({conv[i]['role']}):\n{conv[i]['content']}\n\nΤΡΕΧΟΥΣΑ ΕΛΛΗΝΙΚΗ ΑΠΟΔΟΣΗ:\n{r['turns_el'][i]['content']}\n\nΕπίστρεψε JSON {{\"turn_el\",\"note\"}}.")
    j = B.sol_json(prompt, S_TURN, effort='high', timeout=900); return j['turn_el'] if j else None


def main():
    rows = B.load(os.path.join(HERE, 'conversations_el.jsonl')); tq = {c['id']: c for c in B.load(os.path.join(HERE, 'crosscheck_tq_claude.jsonl'))}; cv = {c['id']: c for c in B.load(os.path.join(HERE, 'crosscheck_conv_claude.jsonl'))}
    stripped = 0
    for r in rows:
        for m in r['turns_el']:
            new = LABEL.sub('', m['content'], count=1)
            if new != m['content']: m['content'] = new; stripped += 1
        c = tq.get(r['id'])
        if c and c['tq_ok'] == 'no' and c.get('fix_tq'): r['target_question_el'] = c['fix_tq']; r['tq_fixed'] = True
        if r['id'] in EXCLUDE: r['excluded'] = 'constraint undecidable in Greek (adjective/adverb repetition; Greek collapses distinctions the English keeps)'
        if r['id'] in ADAPT_T:
            for m in r['turns_el']: m['content'] = m['content'].replace('«T»', '«Τ»').replace('"T"', '«Τ»')
            r['target_question_el'] = r['target_question_el'].replace('«T»', '«Τ»').replace('"T"', '«Τ»'); r['adapted'] = 'Latin T → Greek Τ'
    repairs = []
    for r in rows:
        c = cv.get(r['id'])
        if not c or c['fidelity'] == 'yes' or r.get('excluded'): continue
        m = re.search(r'\d+', str(c.get('worst_turn', '')))
        i = int(m.group(0)) if m else None
        if i is None or i >= len(r['turns_el']): continue
        repairs.append((r, i, f"{c.get('worst_turn', '')} — {c.get('note', '')}"))
    print('role labels stripped', stripped, '| turn repairs', len(repairs), flush=True)
    from concurrent.futures import ThreadPoolExecutor
    def one(x):
        r, i, note = x; t = retranslate_turn(r, i, note)
        if t: r['turns_el'][i]['content'] = t; r.setdefault('repaired_turns', []).append(i)
        return bool(t)
    with ThreadPoolExecutor(12) as pool: done = sum(pool.map(one, repairs))
    for r in rows:   # the ADAPT_WORDS row: ban the Greek words in turn 0 and the target question
        if r['id'] in ADAPT_WORDS:
            j = B.sol_json(B.RULES_EL + "\n\nΞαναγράψε τον γύρο 0 και την ερώτηση-κριτήριο ώστε η απαγόρευση να αφορά τις ΕΛΛΗΝΙΚΕΣ λέξεις «πολιτική/πολιτικές» και «διαδικασία/διαδικασίες» (κάθε κλιτό τύπο) αντί για τις αγγλικές «policy»/«procedures». Επίστρεψε JSON {\"turn_el\": ο γύρος 0, \"note\": η ερώτηση-κριτήριο}.\n\nΓΥΡΟΣ 0:\n" + r['turns_el'][0]['content'] + "\n\nΕΡΩΤΗΣΗ-ΚΡΙΤΗΡΙΟ:\n" + r['target_question_el'], S_TURN, effort='high', timeout=900)
            if j: r['turns_el'][0]['content'] = j['turn_el']; r['target_question_el'] = j['note']; r['adapted'] = 'banned words → Greek forms (assistant turns to be re-audited)'
    with open(os.path.join(HERE, 'conversations_el.jsonl'), 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    with open(os.path.join(HERE, 'conversations_el_final.jsonl'), 'w') as f:
        for r in rows: f.write(json.dumps(dict(id=r['id'], axis=r['axis'], turns_el=r['turns_el'], target_question_el=r['target_question_el'], target_question_en=r['target_question_en'], pass_criteria=r['pass_criteria'], turns_en=r['turns_en'], nontransferable=r['nontransferable'], excluded=r.get('excluded'), adapted=r.get('adapted'), provenance=dict(chunked=bool(r.get('chunked')), tq_fixed=bool(r.get('tq_fixed')), repaired_turns=r.get('repaired_turns', []), role_labels_stripped=True)), ensure_ascii=False) + '\n')
    n_ok = sum(1 for r in rows if not r.get('excluded'))
    summ = dict(rows=len(rows), usable=n_ok, excluded=[r['id'] for r in rows if r.get('excluded')], adapted=[r['id'] for r in rows if r.get('adapted')], role_labels_stripped=stripped, turn_repairs=done,
                crosscheck=dict(target_questions='270 checked, 1 wrong (fixed)', conversations='62 checked (59 random + nontransferable): fidelity no 15 (4 of them only the role-label leak), consistency no 5, testable no 3, naturalness ≤3: 2; the worst turn of every fidelity-no row re-translated with the checker note; not re-checked after repair'),
                known_limits='English number/unit formats inside Greek prose in some rows (50,000; 3.75; 2:00 PM; miles/feet), occasional εσύ/εσείς flips; the repair pass touched only the worst turn per flagged row; sample defect rate before repair 11/59 random rows (19%) excluding the label leak',
                pipeline='Sol translate (chunked fallback for long conversations) → Claude cross-check (all target questions + 62 conversations) → programmatic role-label strip + TQ fix + nontransferable handling + worst-turn re-translation → frozen')
    json.dump(summ, open(os.path.join(HERE, 'summary.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False)[:600])


if __name__ == '__main__': main()
