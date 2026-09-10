#!/usr/bin/env python3
"""Language polishing pass for the four Greek benchmarks (owner rule 2026-09-10: everything adapted gets a Greek correction step before it is done).
Sol edits LANGUAGE ONLY (orthography, grammar, syntax, natural collocations, consistent register); guards revert any edit that touches what an item is scored on:
math → LaTeX/numbers/[asy] byte-identical (verify_final's scanner); xstest → the trigger stem must stay and the label meaning must not change; ifbench → body only,
constraint kwargs that appear in the body unchanged; multichallenge → turn count, digit multiset, quoted target spans and register unchanged. Writes *_polished.jsonl
next to each final file and a polish_report.json. Usage: python3 polish.py <math500|xstest|ifbench|multichallenge|all>"""
import json, os, re, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'math500')); import bench_lib as B
S_ONE = B.M.write_schema('s_polish1.json', {"type": "object", "properties": {"text": {"type": "string"}, "changes": {"type": "string"}}, "required": ["text", "changes"], "additionalProperties": False})
S_MANY = B.M.write_schema('s_polishN.json', {"type": "object", "properties": {"texts": {"type": "array", "items": {"type": "string"}}, "changes": {"type": "string"}}, "required": ["texts", "changes"], "additionalProperties": False})
HEAD = ("Είσαι επιμελητής ελληνικής γλώσσας για υλικό ΑΞΙΟΛΟΓΗΣΗΣ. Διορθώνεις ΜΟΝΟ τη γλώσσα: ορθογραφία, γραμματική, σύνταξη, αφύσικες ή μεταφρασμένες συνάψεις, τόνους, στίξη, συνέπεια ενικού/πληθυντικού ευγενείας μέσα στο ίδιο κείμενο. "
        "ΔΕΝ αλλάζεις νόημα, περιεχόμενο, αριθμούς, μονάδες, ονόματα, όρους-κλειδιά, LaTeX, κώδικα, μορφοποίηση, μήκος ή ύφος πέρα από το γλωσσικά αναγκαίο· δεν προσθέτεις, δεν αφαιρείς, δεν εξηγείς. Αν το κείμενο είναι ήδη σωστό, το επιστρέφεις αυτούσιο. ")


def polish_one(text, extra=''):
    j = B.sol_json(HEAD + extra + "\n\nΚΕΙΜΕΝΟ:\n" + text + "\n\nΕπίστρεψε JSON {\"text\": το διορθωμένο κείμενο, \"changes\": «πριν → μετά» ή κενό}.", S_ONE, effort='medium', timeout=600)
    return (j['text'], j['changes']) if j else (None, None)


def polish_many(texts, extra=''):
    body = '\n\n'.join(f'===== [{i}] =====\n{t}' for i, t in enumerate(texts))
    j = B.sol_json(HEAD + extra + f"\n\nΔιόρθωσε ΚΑΘΕ ένα από τα {len(texts)} κείμενα χωριστά και επίστρεψέ τα με την ίδια σειρά.\n\n" + body + f"\n\nΕπίστρεψε JSON {{\"texts\": [{len(texts)} strings], \"changes\": σύνοψη}}.", S_MANY, effort='medium', timeout=900)
    return (j['texts'], j['changes']) if j and len(j['texts']) == len(texts) else (None, None)


def nfc(s): return unicodedata.normalize('NFC', s)


def run_math():
    from verify_final import regions
    rows = B.load(os.path.join(HERE, 'math500', 'problems_el_final.jsonl')); rep = dict(rows=len(rows), edited=0, reverted=0)
    def one(r):
        new, ch = polish_one(r['problem_el'], "Το LaTeX ($...$, \\[...\\], \\begin...\\end), οι αριθμοί και τα μπλοκ [asy]...[/asy] μένουν ΧΑΡΑΚΤΗΡΑ ΠΡΟΣ ΧΑΡΑΚΤΗΡΑ όπως είναι. ")
        if new is None or nfc(new) == nfc(r['problem_el']): return dict(id=r['id'], status='unchanged')
        ok = regions(new) == regions(r['problem_el']) and sorted(re.findall(r'\d+(?:[.,]\d+)?', new)) == sorted(re.findall(r'\d+(?:[.,]\d+)?', r['problem_el'])) and re.findall(r'\[asy\].*?\[/asy\]', new, re.S) == re.findall(r'\[asy\].*?\[/asy\]', r['problem_el'], re.S)
        return dict(id=r['id'], status='edited' if ok else 'reverted', text=new if ok else None, changes=ch)
    res = {d['id']: d for d in B.run_jobs(rows, one, os.path.join(HERE, 'math500', 'polish_checks.jsonl'), stage='polish math500', workers=24)}
    for r in rows:
        d = res.get(r['id'], {})
        if d.get('status') == 'edited': r['problem_el_prepolish'] = r['problem_el']; r['problem_el'] = d['text']; r['polish_changes'] = d['changes']; rep['edited'] += 1
        elif d.get('status') == 'reverted': rep['reverted'] += 1
        r['polished'] = 'gpt-5.6-sol language-only, guarded'
    with open(os.path.join(HERE, 'math500', 'problems_el_final.jsonl'), 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    return rep


def run_xstest():
    rows = B.load(os.path.join(HERE, 'xstest', 'prompts_el_final.jsonl')); rep = dict(rows=len(rows), edited=0, reverted=0)
    def one(r):
        new, ch = polish_one(r['prompt_el'], f"Είναι ερώτηση χρήστη τύπου «{r['type']}» ({r['label']}). Η λέξη/ρίζα-εστία «{r.get('trigger_el') or ''}» πρέπει να παραμείνει αυτούσια· η ερώτηση πρέπει να μείνει εξίσου ανησυχητική στην επιφάνεια και με το ίδιο ακριβώς νόημα. ")
        if new is None or nfc(new) == nfc(r['prompt_el']): return dict(id=r['id'], status='unchanged')
        stem = (r.get('trigger_el') or '').strip('-* ').lower()[:4]; ok = (not stem) or (stem in new.lower()) or (stem in r['prompt_el'].lower() and stem in new.lower())
        return dict(id=r['id'], status='edited' if ok else 'reverted', text=new if ok else None, changes=ch)
    res = {str(d['id']): d for d in B.run_jobs(rows, one, os.path.join(HERE, 'xstest', 'polish_checks.jsonl'), stage='polish xstest', workers=24)}
    for r in rows:
        d = res.get(str(r['id']), {})
        if d.get('status') == 'edited': r['prompt_el_prepolish'] = r['prompt_el']; r['prompt_el'] = d['text']; r['polish_changes'] = d['changes']; rep['edited'] += 1
        elif d.get('status') == 'reverted': rep['reverted'] += 1
        r['polished'] = 'gpt-5.6-sol language-only, guarded'
    with open(os.path.join(HERE, 'xstest', 'prompts_el_final.jsonl'), 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    return rep


def run_ifbench():
    rows = B.load(os.path.join(HERE, 'ifbench', 'prompts_el_final.jsonl')); rep = dict(rows=len(rows), edited=0, reverted=0, skipped_empty=0)
    def one(r):
        if not r['body_el'].strip(): return dict(id=r['id'], status='skipped_empty')
        kws = [str(v) for kw in r['kwargs'] for v in kw.values() if isinstance(v, str) and 2 <= len(v) <= 40]
        new, ch = polish_one(r['body_el'], "Είναι το σώμα μιας εργασίας (χωρίς τον περιορισμό μορφής, που προστίθεται χωριστά). Λέξεις-κλειδιά που ίσως εμφανίζονται μένουν αυτούσιες: " + ', '.join(f'«{k}»' for k in kws[:8]) + '. ')
        if new is None or nfc(new) == nfc(r['body_el']): return dict(id=r['id'], status='unchanged')
        ok = all((k not in r['body_el']) or (k in new) for k in kws)
        return dict(id=r['id'], status='edited' if ok else 'reverted', text=new if ok else None, changes=ch)
    res = {d['id']: d for d in B.run_jobs(rows, one, os.path.join(HERE, 'ifbench', 'polish_checks.jsonl'), stage='polish ifbench', workers=24)}
    for r in rows:
        d = res.get(r['id'], {})
        if d.get('status') == 'edited':
            r['body_el_prepolish'] = r['body_el']; r['body_el'] = d['text']; r['polish_changes'] = d['changes']; rep['edited'] += 1
            body = r['body_el'].strip()
            if body and body[-1] not in '.;!?…»"\')': body += '.'
            r['prompt_el'] = (body + ('\n\n' if '\n' in body or len(body) > 200 else ' ') + ' '.join(r['descriptions_el'])).strip()
        elif d.get('status') == 'reverted': rep['reverted'] += 1
        elif d.get('status') == 'skipped_empty': rep['skipped_empty'] += 1
        r['polished'] = 'gpt-5.6-sol language-only on the body, guarded; constraint sentences are checker-rendered'
    with open(os.path.join(HERE, 'ifbench', 'prompts_el_final.jsonl'), 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    return rep


def run_mc():
    rows = B.load(os.path.join(HERE, 'multichallenge', 'conversations_el_final.jsonl')); rep = dict(rows=len(rows), edited=0, reverted=0, skipped_excluded=0)
    def one(r):
        if r.get('excluded'): return dict(id=r['id'], status='skipped_excluded')
        texts = [m['content'] for m in r['turns_el']] + [r['target_question_el']]
        new, ch = polish_many(texts, "Είναι οι γύροι μιας συζήτησης χρήστη–βοηθού (ο τελευταίος είναι η ερώτηση-κριτήριο). Κράτησε ΕΝΑΝ ενικό/πληθυντικό ευγενείας για τον ίδιο συνομιλητή σε όλη τη συζήτηση, όπως στον πρώτο γύρο· ό,τι επαναλαμβάνεται αυτούσιο (ποιήματα, email, λίστες) μένει ταυτόσημο· αριθμοί, ονόματα, μορφοποίηση (κενά εσοχής, κουκκίδες) αμετάβλητα. ")
        if new is None: return dict(id=r['id'], status='unchanged')
        old_digits = sorted(re.findall(r'\d+', ' '.join(texts))); new_digits = sorted(re.findall(r'\d+', ' '.join(new)))
        quoted = re.findall(r'«([^»]{12,})»', r['target_question_el']); hist = ' '.join(new[:-1])
        ok = old_digits == new_digits and all(q in hist for q in quoted if q in ' '.join(texts[:-1])) and all(m['content'].count('\n    ') == n.count('\n    ') for m, n in zip(r['turns_el'], new[:-1]))
        changed = any(nfc(a) != nfc(b) for a, b in zip(texts, new))
        return dict(id=r['id'], status=('edited' if ok else 'reverted') if changed else 'unchanged', texts=new if ok and changed else None, changes=ch)
    res = {d['id']: d for d in B.run_jobs(rows, one, os.path.join(HERE, 'multichallenge', 'polish_checks.jsonl'), stage='polish multichallenge', workers=12)}
    for r in rows:
        d = res.get(r['id'], {})
        if d.get('status') == 'edited':
            for m, t in zip(r['turns_el'], d['texts'][:-1]): m['content'] = t
            r['target_question_el'] = d['texts'][-1]; r['polish_changes'] = d['changes']; rep['edited'] += 1
        elif d.get('status') == 'reverted': rep['reverted'] += 1
        elif d.get('status') == 'skipped_excluded': rep['skipped_excluded'] += 1
        r['provenance']['polished'] = 'gpt-5.6-sol language-only, guarded (turn count, digits, quoted target spans, indentation)'
    with open(os.path.join(HERE, 'multichallenge', 'conversations_el_final.jsonl'), 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    return rep


if __name__ == '__main__':
    which = sys.argv[1]; report = {}
    for name, fn in (('math500', run_math), ('xstest', run_xstest), ('ifbench', run_ifbench), ('multichallenge', run_mc)):
        if which in (name, 'all'): report[name] = fn(); print(name, report[name], flush=True)
    p = os.path.join(HERE, 'polish_report.json'); old = json.load(open(p)) if os.path.exists(p) else {}; old.update(report); json.dump(old, open(p, 'w'), ensure_ascii=False, indent=1)
