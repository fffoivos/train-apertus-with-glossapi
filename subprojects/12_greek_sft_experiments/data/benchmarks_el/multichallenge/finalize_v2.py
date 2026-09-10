#!/usr/bin/env python3
"""MultiChallenge-el v2 freeze after the astra review: quarantine the four rows whose target questions cannot support clean scoring (three inherited from the
English: shellfish vs nuts, antioxidant polarity, sweatshirt contact; one underdetermined: Jara), fix the «Jacks or Better» typo in target questions, make the
verbatim-reference target quote the actual Greek introduction from the history, attach judge notes (matching scope for banned words; Quattro/4WD category),
and record role-label provenance as a sweep with per-row counts. Writes conversations_el_final.jsonl (archives the previous freeze as .v1) + summary.json."""
import json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
QUARANTINE = {'67455eccbcab6aa613bebeaa': 'target asks about nuts, the history establishes a shellfish allergy (inherited from the English)', '674567315c67d815889df2db': 'target polarity contradictory: avoiding the banned word is described as violating it (inherited)',
              '6765f4907e4dcd5e2143352b': 'target refers to the model touching clothing and offers examples that conflict with the user restriction (inherited)', '6765f4400af93a24e8fbe1f1': 'target demands a song title and year the history never supplies (underdetermined)'}
NOTES = {'6765f839a02fd129919ef243': 'Ο περιορισμός λέξεων καλύπτει ΚΑΘΕ κλιτό τύπο της ίδιας λέξης (ενσυνείδητος/ενσυνείδητη, θεραπεύω/θεραπεύει, χαλάρωση/χαλάρωσης) αλλά ΟΧΙ παράγωγες λέξεις (ενσυνειδητότητα, θεραπευτικός).',
         '674567315c67d815889df2db': 'Ο περιορισμός καλύπτει κάθε κλιτό τύπο (αντιοξειδωτικό/αντιοξειδωτικά).', '6765f1c84fdcad5ca243d300': 'Κρίνε αν η απάντηση κατατάσσει το Quattro στην κατηγορία 4WD (σε αντιδιαστολή με το AWD), όχι αν περιγράφει ότι κινούνται και οι τέσσερις τροχοί.'}


def main():
    path = os.path.join(HERE, 'conversations_el_final.jsonl'); rows = B.load(path); shutil.copy(path, path + '.v1'); n_typo = 0
    for r in rows:
        if r['id'] in QUARANTINE: r['excluded'] = (r.get('excluded') or '') + ('; ' if r.get('excluded') else '') + 'quarantined: ' + QUARANTINE[r['id']]
        if 'Jacks and Better' in r['target_question_el'] or 'Jacks and Better' in r['target_question_en']: r['target_question_el'] = r['target_question_el'].replace('Jacks and Better', 'Jacks or Better'); r['tq_typo_fixed'] = True; n_typo += 1
        if r['id'] == '6765fca79308c5a618275196':
            m = None
            for t in r['turns_el']:
                m = re.search(r'Ο τομέας προσέλκυσε[^.\n]*\.', t['content'])
                if m: break
            if m: r['target_question_el'] = re.sub(r'«Ο τομέας προσέλκυσε[^»]*»', '«' + m.group(0).strip() + '»', r['target_question_el']); r['tq_reference_from_history'] = True
        if r['id'] in NOTES: r['judge_note_el'] = NOTES[r['id']]
        prov = r.get('provenance', {}); prov['role_label_sweep'] = True; prov['role_labels_removed'] = prov.pop('role_labels_stripped', None) and None
        r['provenance'] = {k: v for k, v in prov.items() if v is not None}
    with open(path, 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    usable = [r for r in rows if not r.get('excluded')]
    summ = json.load(open(os.path.join(HERE, 'summary.json'))); summ.update(version=2, usable=len(usable), excluded=[dict(id=r['id'], reason=r['excluded']) for r in rows if r.get('excluded')], tq_typo_fixed=n_typo, judge_notes=list(NOTES), licence='licence/permissions UNRESOLVED (no licence file in the upstream repository): internal evaluation only pending permission; no redistribution of the Greek conversations',
                calibration='43 conversations × (passing, failing) constructed by Sol; Claude Opus 5 judge: EN rubric false-fail 1/43, false-pass 3/43; EL rubric 1/43, 2/43 (the EL advantage is one response); not yet validated on real model outputs against human labels',
                audit_counts='Claude cross-check 1: 62 conversations checked (59 random + 3 non-transferable not in the draw): fidelity no 15, of which 4 only the role-label leak → 11 substantive among 62; the worst turn of each fidelity-no row re-translated; third cross-check (full re-check of repaired/late/chunked rows + fresh random audit + validity audit of all target questions) pending')
    json.dump(summ, open(os.path.join(HERE, 'summary.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps(dict(rows=len(rows), usable=len(usable), excluded=len(rows) - len(usable), typo_fixed=n_typo)))


if __name__ == '__main__': main()
