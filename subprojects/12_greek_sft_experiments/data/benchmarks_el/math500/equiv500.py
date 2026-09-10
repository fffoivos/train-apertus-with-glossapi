#!/usr/bin/env python3
"""MATH-500 answer equivalence: the upstream Hendrycks/Lightman string normalisation (strip_string) → exact match; else numeric equality for pure numbers
(Greek decimal comma accepted); else sympy on the normalised expression. Deliberately stricter than mathlib.equiv (no multi-number heuristics)."""
import re


def _fix_fracs(s):
    subs = s.split('\\frac'); new = subs[0]
    for sub in subs[1:]:
        new += '\\frac'
        if sub and sub[0] == '{': new += sub
        else:
            if len(sub) < 2: return s
            a, b = sub[0], sub[1]
            new += ('{' + a + '}{' + b + '}' + sub[2:]) if b != '{' else ('{' + a + '}' + b + sub[2:])
    return new


def _fix_a_slash_b(s):
    if len(s.split('/')) != 2: return s
    a, b = s.split('/')
    try:
        a, b = int(a), int(b); return '\\frac{' + str(a) + '}{' + str(b) + '}'
    except Exception: return s


def _fix_sqrt(s):
    if '\\sqrt' not in s: return s
    parts = s.split('\\sqrt'); new = parts[0]
    for p in parts[1:]:
        if p and p[0] != '{': new += '\\sqrt{' + p[0] + '}' + p[1:]
        else: new += '\\sqrt' + p
    return new


def strip_string(s: str) -> str:
    s = s.replace('\n', '').replace('\\!', '').replace('\\\\', '\\').replace('tfrac', 'frac').replace('dfrac', 'frac').replace('\\left', '').replace('\\right', '')
    s = s.replace('^{\\circ}', '').replace('^\\circ', '').replace('\\$', '').replace('$', '')
    s = re.sub(r'\\text\{\s*[^}]*\}$', '', s).strip()   # trailing units
    s = s.replace('\\%', '').replace('%', '')
    s = s.replace(' .', ' 0.').replace('{.', '{0.')
    if s and s[0] == '.': s = '0' + s
    if '=' in s and len(s.split('=')[0]) <= 2: s = s.split('=')[1]
    s = _fix_sqrt(s); s = s.replace(' ', ''); s = _fix_fracs(s)
    if s == '0.5': s = '\\frac{1}{2}'
    s = _fix_a_slash_b(s); return s


def _num(s):
    t = s.replace(' ', '')
    if re.fullmatch(r'-?\d{1,3}(\.\d{3})+,\d+', t): t = t.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'-?\d+,\d+', t): t = t.replace(',', '.')
    elif re.fullmatch(r'-?\d{1,3}(,\d{3})+(\.\d+)?', t): t = t.replace(',', '')
    try: return float(t)
    except Exception: return None


def equiv500(ref: str, pred: str) -> bool:
    if not ref or not pred: return False
    a, b = strip_string(ref), strip_string(pred)
    if a == b: return True
    na, nb = _num(a), _num(b)
    if na is not None and nb is not None: return abs(na - nb) <= 1e-9 * max(1.0, abs(na))
    if na is not None or nb is not None: return False
    try:
        import sympy
        from sympy.parsing.sympy_parser import parse_expr
        ea, eb = parse_expr(a.replace('^', '**').replace('\\frac', '').replace('{', '(').replace('}', ')')), parse_expr(b.replace('^', '**').replace('\\frac', '').replace('{', '(').replace('}', ')'))
        return sympy.simplify(ea - eb) == 0
    except Exception: return False
