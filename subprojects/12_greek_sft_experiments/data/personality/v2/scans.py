#!/usr/bin/env python3
"""Automatic metrics for one run: gate outcomes, naming-Greece rate, mannerisms, boilerplate, placeholders, duplicates, lengths by form, beyond_sheet, Γ verdicts, doubts.
Usage: python3 scans.py <run_dir>  (expects questions_gated.jsonl, rows.jsonl, checks.jsonl) → prints JSON and writes metrics.json"""
import json, sys, os, re, collections, statistics
D = sys.argv[1]
def load(p): return [json.loads(l) for l in open(p)] if os.path.exists(p) else []
qs, rows, checks = load(f'{D}/questions_gated.jsonl'), load(f'{D}/rows.jsonl'), [j for j in load(f'{D}/checks.jsonl') if j.get('verdict')]
GR = re.compile(r'(στην Ελλάδα|της Ελλάδας|η Ελλάδα|στη χώρα μας)'); MAN = re.compile(r'^\s*(Φυσικά|Βεβαίως|Βέβαια|Εξαιρετική|Καλή ερώτηση|Ορίστε)|(Ελπίζω να|Αν χρειαστείς|Μη διστάσεις|αν θέλεις,? σου|αν θέλετε,? σας)', re.I)
AI = re.compile(r'(ως (τεχνητή|γλωσσικό|βοηθός ΤΝ)|είμαι (ένα )?(γλωσσικό μοντέλο|τεχνητή))', re.I); SELF = re.compile(r'\b(δεν μπορώ να δω|δεν έχω πρόσβαση|είμαι (ο|το) \[ΟΝΟΜΑ\])', re.I)
m = {}
if qs:
    ga = collections.Counter((q.get('gate') or {}).get('action') or 'unjudged' for q in qs); m['questions'] = len(qs); m['gate'] = dict(ga); m['gate_keep_rate'] = round(ga.get('keep', 0) / len(qs), 3)
    m['forms'] = dict(collections.Counter(q.get('form') for q in qs)); m['duplicate_questions'] = len(qs) - len({q['user_el'] for q in qs}); m['followups'] = sum(1 for q in qs if q.get('followup_el'))
if rows:
    A = [' '.join(x['content'] for x in r['messages'] if x['role'] == 'assistant') for r in rows]; last = [r['messages'][-1]['content'] for r in rows]
    m['rows'] = len(rows); m['names_greece_rate'] = round(sum(bool(GR.search(a)) for a in A) / len(A), 3); m['mannerism_rate'] = round(sum(bool(MAN.search(a)) for a in A) / len(A), 3); m['ai_boilerplate'] = sum(bool(AI.search(a)) for a in A)
    m['multi_turn'] = sum(1 for r in rows if len(r['messages']) > 2); m['beyond_sheet_rows'] = sum(1 for r in rows if r.get('beyond_sheet')); m['beyond_sheet_items'] = sum(len(r.get('beyond_sheet') or []) for r in rows)
    m['exclamations_per_row'] = round(sum(a.count('!') for a in A) / len(A), 2); m['placeholder_rows'] = sum(1 for a in A if '[ΟΝΟΜΑ]' in a or '[ΗΜΕΡΟΜΗΝΙΑ ΓΝΩΣΗΣ]' in a or '[ΑΔΕΙΑ]' in a)
    byform = collections.defaultdict(list)
    for r in rows: byform[r.get('form')].append(len(r['messages'][1]['content']))
    m['answer_chars_median_by_form'] = {k: int(statistics.median(v)) for k, v in byform.items()}; m['answer_chars_median'] = int(statistics.median(len(x) for x in last))
    m['clarify_rows_asking'] = sum(1 for r in rows if ((r.get('gate') or {}).get('action') == 'clarify') and '?' in r['messages'][1]['content'] or (((r.get('gate') or {}).get('action') == 'clarify') and ';' in r['messages'][1]['content']))
if checks:
    v = collections.Counter(c['verdict'] for c in checks); g = [c['greekness'] for c in checks if isinstance(c.get('greekness'), int)]
    m['checked'] = len(checks); m['verdicts'] = dict(v); m['edit_rate'] = round((v.get('edited', 0) + v.get('rewrite', 0)) / len(checks), 3); m['greekness'] = round(sum(g) / len(g), 2) if g else None; m['fact_doubts'] = sum(1 for c in checks if (c.get('fact_doubt') or '').strip())
    ch = ' '.join(x for c in checks for x in (c.get('changes') or [])); m['changes_mentioning'] = {k: len(re.findall(p, ch)) for k, p in [('Ελλάδα', 'Ελλάδα'), ('self-reference', 'εαυτό'), ('mannerism', 'μανιέρ|προσφορά'), ('clitic/article', 'κλιτικ|άρθρο|αντικείμενο'), ('beyond sheet', 'φύλλο')]}
json.dump(m, open(f'{D}/metrics.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(m, ensure_ascii=False, indent=1))
