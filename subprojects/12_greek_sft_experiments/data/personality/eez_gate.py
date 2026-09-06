#!/usr/bin/env python3
"""Gate: any row whose user turn asks about the size / area / borders / neighbours of Greece must answer with the sea too (ΑΟΖ).
Usage: python3 eez_gate.py <rows.jsonl> [...]  → lists offending ids, exit 1 if any."""
import json, sys, re
TRIG = re.compile(r'(πόσα τετραγωνικ|ποσα τετραγωνικ|έκταση της|εκταση της|έκταση έχει|πόσο μεγάλη είναι η (Ελλάδα|χώρα)|μέγεθος της (Ελλάδας|χώρας)|συνορεύ|σύνορα (της|μας|έχουμε)|συνορα|με ποι[εα]ς χώρες|γείτονές μας|γειτονικές χώρες|θαλάσσια σύνορα|synoreu|ektasi)', re.I)
SEA = re.compile(r'(ΑΟΖ|αποκλειστική οικονομική ζώνη|Αποκλειστικής Οικονομικής Ζώνης)', re.I)
code = 0
for path in sys.argv[1:]:
    rows = [json.loads(l) for l in open(path)]; bad = []
    for r in rows:
        u = ' '.join(m['content'] for m in r['messages'] if m['role'] == 'user'); a = ' '.join(m['content'] for m in r['messages'] if m['role'] == 'assistant')
        if TRIG.search(u) and not SEA.search(a): bad.append(r.get('id'))
    trig = sum(1 for r in rows if TRIG.search(' '.join(m['content'] for m in r['messages'] if m['role'] == 'user')))
    print(f'== {path}: {len(rows)} rows, {trig} ask size/borders/neighbours, {len(bad)} without ΑΟΖ' + (': ' + ', '.join(map(str, bad)) if bad else ''))
    if bad: code = 1
print('GATE OK' if code == 0 else 'GATE FAIL'); sys.exit(code)
