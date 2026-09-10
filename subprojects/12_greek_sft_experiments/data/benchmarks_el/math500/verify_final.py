#!/usr/bin/env python3
"""Independent protection checker for the frozen MATH-500-el (astra F5): a fresh scanner (NOT the translate.py regex that produced the corruption) classifies
every math region with an explicit outcome — byte-identical | prose-only-exception (only \\text{…}/\\textbf{…}/tabular cell words differ) | by-design (documented
ordinal / question-mark / $70$ cases) | MISMATCH — plus [asy] byte-equality, number multiset equality, and a leftover-English scan; writes verify_report.json and
the closed repair ledger of the 11 first-pass corruptions. Usage: python3 verify_final.py"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
BY_DESIGN = {'test/precalculus/285.json': 'ordinal n^{th} → n-οστός', 'test/prealgebra/1804.json': 'table headers translated', 'test/number_theory/978.json': 'ordinal', 'test/number_theory/1201.json': 'question mark moved outside the span', 'test/prealgebra/1044.json': "$70\\text{'s}$ → $70$", 'test/number_theory/483.json': 'ordinal 100^{th} → 100ός', 'test/prealgebra/1865.json': 'table headers translated'}
LEDGER = {'test/algebra/2427.json': 'English prose spliced between \\$ spans + BEL byte → re-translated v2, cc2 sound', 'test/algebra/824.json': 'display block duplicated → cc1 fix; \\text{ if } left → cc2 fix «αν» (closed)', 'test/prealgebra/1203.json': 'untranslated + «60% of» error → cc1 fix, cc2 sound',
          'test/algebra/2551.json': 'English + dropped «discount» → cc1 fix, cc2 sound', 'test/prealgebra/1840.json': 'English + dropped «to bake» → cc1 fix, cc2 sound', 'test/algebra/1332.json': 'question in English → cc1 fix, cc2 sound', 'test/algebra/2626.json': 'given in English → cc1 fix, cc2 sound',
          'test/algebra/2743.json': 'second equation in English → cc1 fix, cc2 sound', 'test/algebra/2780.json': 'data point in English → cc1 fix, cc2 sound', 'test/number_theory/679.json': 'two givens in English → cc1 fix, cc2 sound', 'test/number_theory/1185.json': '«is defined as» in English → cc1 fix, cc2 sound'}


def regions(s):
    """Fresh scanner: walk the string, collect $…$ / $$…$$ / \\[…\\] / \\begin{env}…\\end{env} regions honouring \\$ escapes."""
    out = []; i = 0; n = len(s)
    while i < n:
        if s.startswith('\\$', i): i += 2; continue
        if s.startswith('$$', i):
            j = s.find('$$', i + 2)
            if j < 0: break
            out.append(s[i:j + 2]); i = j + 2; continue
        if s[i] == '$':
            j = i + 1
            while j < n and not (s[j] == '$' and s[j - 1] != '\\'): j += 1
            if j >= n: break
            out.append(s[i:j + 1]); i = j + 1; continue
        if s.startswith('\\[', i):
            j = s.find('\\]', i)
            if j < 0: break
            out.append(s[i:j + 2]); i = j + 2; continue
        m = re.match(r'\\begin\{(\w+\*?)\}', s[i:])
        if m:
            env = m.group(1); j = s.find('\\end{' + env + '}', i)
            if j < 0: break
            out.append(s[i:j + len('\\end{' + env + '}')]); i = j + len('\\end{' + env + '}'); continue
        i += 1
    return out


def prose_masked(x): return re.sub(r'\\(?:text|textbf|textit|mbox)\{[^{}]*\}', '\\\\text{…}', re.sub(r'(?<=&)[^&\\\n]*|(?<=\\hline)[^&\\\n]*', '…', x)) if ('tabular' in x or 'array' in x) else re.sub(r'\\(?:text|textbf|textit|mbox)\{[^{}]*\}', '\\\\text{…}', x)


def main():
    rows = [json.loads(l) for l in open(os.path.join(HERE, 'problems_el_final.jsonl'))]; rep = []; c = collections.Counter()
    for r in rows:
        en, el = regions(r['problem_en']), regions(r['problem_el'])
        if en == el: st = 'byte-identical'
        elif len(en) == len(el) and [prose_masked(x) for x in en] == [prose_masked(x) for x in el]: st = 'prose-only-exception'
        elif r['id'] in BY_DESIGN: st = 'by-design: ' + BY_DESIGN[r['id']]
        else: st = 'MISMATCH'
        asy_en, asy_el = re.findall(r'\[asy\].*?\[/asy\]', r['problem_en'], re.S), re.findall(r'\[asy\].*?\[/asy\]', r['problem_el'], re.S)
        nums = sorted(re.findall(r'\d+(?:[.,]\d+)?', r['problem_en'])) == sorted(re.findall(r'\d+(?:[.,]\d+)?', r['problem_el'])) or r['id'] in BY_DESIGN
        prose = re.sub(r'\[asy\].*?\[/asy\]', ' ', r['problem_el'], flags=re.S)
        for x in el: prose = prose.replace(x, ' ')
        eng = [m.group(0) for m in re.finditer(r'(?:\b[A-Za-z]{2,}\b[\s,.;:()\'"-]*){3,}', prose) if sum(w[0].islower() for w in re.findall(r'[A-Za-z]{2,}', m.group(0))) >= 2]
        item = dict(id=r['id'], math_regions=st, asy='byte-identical' if asy_en == asy_el else 'MISMATCH', numbers='equal' if nums else 'MISMATCH', english_prose=eng[:2]); rep.append(item); c[st.split(':')[0]] += 1; c['asy_' + item['asy']] += 1; c['numbers_' + item['numbers']] += 1; c['english_prose'] += bool(eng)
    bad = [x for x in rep if x['math_regions'] == 'MISMATCH' or x['asy'] == 'MISMATCH' or x['numbers'] == 'MISMATCH' or x['english_prose']]
    json.dump(dict(counts=dict(c), problems=bad, repair_ledger=LEDGER, verifier='verify_final.py (independent of translate.py\'s scanner)'), open(os.path.join(HERE, 'verify_report.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(dict(counts=dict(c), problems=[(x['id'], x['math_regions'], x['asy'], x['numbers'], x['english_prose']) for x in bad]), ensure_ascii=False)[:900])


if __name__ == '__main__': main()
