#!/usr/bin/env python3
"""MATH-500 answer equivalence for Greek responses (astra F1): (1) extraction from a full response (last \\boxed{}, else an «Απάντηση:» line, else the last line);
(2) the upstream Hendrycks/Lightman string normalisation (strip_string) → exact match; (3) categorical answers mapped Greek → English (έλλειψη ≡ \\text{ellipse},
άρτιος ≡ even, ανατολικά ≡ east …); (4) numeric equality for a lone number (Greek decimal comma accepted ONLY when the string is a single number, never inside
coordinates, lists or thousands groups); (5) sympy on the normalised expression. The vendored upstream grader (prm800k grading/grader.py) is run alongside to
report the upstream metric separately from this extended Greek metric."""
import re
CATEGORICAL = {'έλλειψη': 'ellipse', 'παραβολή': 'parabola', 'υπερβολή': 'hyperbola', 'κύκλος': 'circle', 'σημείο': 'point', 'ευθεία': 'line', 'δύο ευθείες': 'two lines', 'κενό': 'empty',
               'άρτιος': 'even', 'ζυγός': 'even', 'περιττός': 'odd', 'μονός': 'odd', 'ανατολικά': 'east', 'ανατολή': 'east', 'δυτικά': 'west', 'βόρεια': 'north', 'νότια': 'south', 'ναι': 'yes', 'όχι': 'no', 'αληθές': 'true', 'ψευδές': 'false',
               'δευτέρα': 'monday', 'τρίτη': 'tuesday', 'τετάρτη': 'wednesday', 'πέμπτη': 'thursday', 'παρασκευή': 'friday', 'σάββατο': 'saturday', 'κυριακή': 'sunday'}
UNITS = r'(?:cm|m|km|mm|inches|inch|feet|ft|cents|cent|degrees|degree|dollars|units|sq|square|εκατοστά|εκ\.?|μέτρα|μ\.?|ίντσες|σεντ|μοίρες|ευρώ|€|\$)'


def extract(resp: str) -> str:
    """Last \\boxed{...} (balanced braces); else the text after the last «Απάντηση:»/«Answer:»; else the last non-empty line."""
    last = None; i = 0
    while True:
        i = resp.find('\\boxed', i)
        if i < 0: break
        j = resp.find('{', i); depth = 0; k = j
        while k < len(resp):
            if resp[k] == '{': depth += 1
            elif resp[k] == '}':
                depth -= 1
                if depth == 0: break
            k += 1
        if j >= 0 and k < len(resp): last = resp[j + 1:k]
        i = k if k > i else i + 6
    if last is not None: return last.strip()
    m = list(re.finditer(r'(?im)^\s*\**\s*(?:Απάντηση|Answer)\s*:\s*(.+?)\s*\**\s*$', resp))
    if m: return m[-1].group(1).strip().strip('*').strip()   # «**Απάντηση:** έλλειψη»
    lines = [l.strip() for l in resp.strip().splitlines() if l.strip()]
    return lines[-1] if lines else ''


def _fix_fracs(s):
    subs = s.split('\\frac'); new = subs[0]
    for sub in subs[1:]:
        new += '\\frac'
        if sub and sub[0] == '{': new += sub
        else:
            if len(sub) < 2: return s
            a, b = sub[0], sub[1]; new += ('{' + a + '}{' + b + '}' + sub[2:]) if b != '{' else ('{' + a + '}' + b + sub[2:])
    return new


def _fix_a_slash_b(s):
    if len(s.split('/')) != 2: return s
    a, b = s.split('/')
    try: return '\\frac{' + str(int(a)) + '}{' + str(int(b)) + '}'
    except Exception: return s


def _fix_sqrt(s):
    if '\\sqrt' not in s: return s
    parts = s.split('\\sqrt'); new = parts[0]
    for p in parts[1:]: new += ('\\sqrt{' + p[0] + '}' + p[1:]) if p and p[0] != '{' else '\\sqrt' + p
    return new


def strip_string(s: str) -> str:
    s = s.replace('\n', '').replace('\\!', '').replace('\\\\', '\\').replace('tfrac', 'frac').replace('dfrac', 'frac').replace('\\left', '').replace('\\right', '')
    s = s.replace('^{\\circ}', '').replace('^\\circ', '').replace('\\$', '').replace('$', '')
    s = re.sub(r'\\(?:text|mbox)\{\s*[^}]*\}(\^\d)?$', '', s).strip()   # trailing units incl. \mbox{ cm}^2
    s = re.sub(r'\s+' + UNITS + r'(\^\d)?\s*$', '', s).strip()
    s = s.replace('\\%', '').replace('%', '').replace(' .', ' 0.').replace('{.', '{0.')
    if s and s[0] == '.': s = '0' + s
    if '=' in s and len(s.split('=')[0]) <= 2: s = s.split('=')[1]
    s = _fix_sqrt(s); s = s.replace(' ', ''); s = _fix_fracs(s); s = re.sub(r'\\frac\{([^{}]*)\}(\w)(?!\})', r'\\frac{\1}{\2}', s)   # \frac{270}7 → \frac{270}{7}
    if s == '0.5': s = '\\frac{1}{2}'
    return _fix_a_slash_b(s)


def categorical(s: str) -> str | None:
    t = re.sub(r'\\(?:text|mbox|textbf|mathrm)\{([^}]*)\}', r'\1', s).strip().strip('.').lower()
    if re.search(r'\d', t) or len(t) > 30: return None
    return CATEGORICAL.get(t, t) if re.fullmatch(r'[a-zA-Zα-ωά-ώϊϋΐΰ\s]+', t) else None


def _nums(s):
    """All defensible readings of a lone number string: «3,5» → 3.5 (Greek decimal); «1,000» → 1.0 (Greek decimal) AND 1000 (English thousands); «1.000» → 1000 (Greek thousands) AND 1.0;
    «1.234,56» → 1234.56. Not a lone number (coordinates, lists, letters) → []. Equality holds if any reading of one side equals any reading of the other (astra F1: decimal commas vs separators)."""
    t = s.replace(' ', ''); out = set()
    if re.fullmatch(r'-?\d{1,3}(\.\d{3})+,\d+', t): out.add(float(t.replace('.', '').replace(',', '.')))
    elif re.fullmatch(r'-?\d{1,3}(,\d{3})+\.\d+', t): out.add(float(t.replace(',', '')))
    elif re.fullmatch(r'-?\d+,\d+', t):
        out.add(float(t.replace(',', '.')))
        if re.fullmatch(r'-?\d{1,3}(,\d{3})+', t): out.add(float(t.replace(',', '')))
    elif re.fullmatch(r'-?\d+\.\d+', t):
        out.add(float(t))
        if re.fullmatch(r'-?\d{1,3}(\.\d{3})+', t): out.add(float(t.replace('.', '')))
    else:
        try: out.add(float(t))
        except Exception: pass
    return out


def _num(s):
    v = _nums(s); return min(v) if v else None


def equiv500(ref: str, pred: str) -> bool:
    if not ref or not pred: return False
    a, b = strip_string(ref), strip_string(pred)
    if a == b: return True
    ca, cb = categorical(ref), categorical(pred)
    if ca is not None or cb is not None: return ca is not None and ca == cb
    na, nb = _nums(a), _nums(b)
    if na and nb: return any(abs(x - y) <= 1e-9 * max(1.0, abs(x)) for x in na for y in nb)
    if na or nb: return False
    try:
        import sympy
        from sympy.parsing.sympy_parser import parse_expr
        conv = lambda x: x.replace('^', '**').replace('\\frac', '').replace('{', '(').replace('}', ')')
        return sympy.simplify(parse_expr(conv(a)) - parse_expr(conv(b))) == 0
    except Exception: return False


def upstream_equiv(ref: str, pred: str):
    """The vendored prm800k grader (upstream metric), None if it cannot run."""
    try:
        import upstream_grader; return bool(upstream_grader.grade_answer(pred, ref))
    except Exception: return None
