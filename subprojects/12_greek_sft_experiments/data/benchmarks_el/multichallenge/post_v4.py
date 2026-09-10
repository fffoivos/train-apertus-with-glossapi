#!/usr/bin/env python3
"""Mechanical fifth pass (after the fourth Claude check): fix the artefacts of the v3 post-pass (doubled «μ.μ..», a converted English book title, thousands figures
followed by a comma), adopt the Greek decimal comma corpus-wide with guards (no versions/IPs/times, no code), «$25/hr» → «$25/ώρα», restore 4-space code
indentation where the English turn has it and the Greek lost it, and verify digit multisets are unchanged. Freezes v4 + summary. Usage: python3 post_v4.py"""
import json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B


def split_code(text):
    return re.split(r'(```.*?```|(?:^ {4}.*(?:\n|$))+)', text, flags=re.S | re.M)   # a run of 4-space-indented LINES (not re.S on the dot)


def fix(text):
    parts = split_code(text); out = []
    for i, p in enumerate(parts):
        if i % 2 == 1: out.append(p); continue
        p = p.replace('μ.μ..', 'μ.μ.').replace('π.μ..', 'π.μ.')
        p = re.sub(r'(?<![\d.,])(\d{1,3})(,\d{3})+(?![\d])', lambda m: m.group(0).replace(',', '.'), p)   # thousands, also when a comma follows the figure
        p = re.sub(r'(?<![\d.\w/])(\d{1,4})\.(\d{1,2})(?![\d.%])', r'\1,\2', p)   # decimal comma: 3.75 → 3,75; not 1.2.3, not 8.5.2024, not v2.0 (preceded by a word char), not 12.5% (kept: % is Greek-fine either way → keep English form out of scope)
        p = re.sub(r'(\$\s?\d+)/hr\b', r'\1/ώρα', p); p = re.sub(r'(\d+)\s?\$/hr\b', r'\1$/ώρα', p)
        out.append(p)
    return ''.join(out)


def main():
    path = os.path.join(HERE, 'conversations_el_final.jsonl'); rows = B.load(path); shutil.copy(path, path + '.v3'); n_dec = n_indent = 0
    for r in rows:
        for m_en, m_el in zip(r['turns_en'], r['turns_el']):
            new = fix(m_el['content'])
            if r['id'] == '6765f440b0ca0453b824ac33': new = new.replace('"D-Day: 6 Ιουνίου 1944"', '"D-Day: June 6, 1944"')
            en_lines = m_en['content'].split('\n'); el_lines = new.split('\n')
            if sum(l.startswith('    ') for l in en_lines) >= 5 and sum(l.startswith('    ') for l in el_lines) == 0 and len(el_lines) >= 5:   # code-block email lost its indentation (fourth check: 6781a949e813a5cdb592df67)
                head = next((k for k, l in enumerate(en_lines) if l.startswith('    ')), 0); tail = len(en_lines) - 1 - next((k for k, l in enumerate(reversed(en_lines)) if l.startswith('    ')), 0)
                if tail > head and len(el_lines) > tail: el_lines = el_lines[:head] + ['    ' + l if l.strip() else l for l in el_lines[head:tail + 1]] + el_lines[tail + 1:]; new = '\n'.join(el_lines); n_indent += 1
            if new != m_el['content']: n_dec += 1; m_el['content'] = new
        r['target_question_el'] = fix(r['target_question_el']); r['provenance']['post_pass_v4'] = True
    digits_ok = sum(sorted(re.findall(r'\d+', ' '.join(m['content'] for m in r['turns_en']))) == sorted(re.findall(r'\d+', ' '.join(m['content'] for m in r['turns_el']))) for r in rows)
    with open(path, 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    import hashlib; h = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    s = json.load(open(os.path.join(HERE, 'summary.json'))); s.update(version=4, sha256=h, turns_changed_v4=n_dec, indentation_restored=n_indent, digit_multisets_equal=f'{digits_ok}/273',
        crosscheck4='33 re-translated rows: fidelity 33/33, tq consistent 33/33, format 33/33, consistency 29/33 (4 cosmetic register/term); 40 random rows: fidelity 39/40, format 33/40, consistency 35/40; usable-set defect rate any 14/70 = 20% (CI 12–31%), content-bearing 1/70 = 1.4% (CI 0.3–7.7%); all 9 previously unsound repairs now sound on their named defect; post-pass artefacts (doubled μ.μ.., a converted book title, two mixed-separator rows) fixed mechanically in v4 together with a corpus-wide Greek decimal comma',
        known_limits='register (εσύ/εσείς) and term consistency inside a turn are not mechanically enforced (~10% of rows); v4 mechanical changes not re-checked by a model; licence unresolved')
    json.dump(s, open(os.path.join(HERE, 'summary.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps(dict(turns_changed=n_dec, indentation_restored=n_indent, digits_ok=f'{digits_ok}/273', sha256=h[:16])))


if __name__ == '__main__': main()
