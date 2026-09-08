"""Shared helpers for the Greek math set: answer extraction, Greek number formats, answer equivalence, formatting checks, one codex JSON call."""
from __future__ import annotations
import json, os, re, subprocess, tempfile, unicodedata
from fractions import Fraction

TMP = os.environ.get('CLAUDE_JOB_DIR', tempfile.gettempdir()) + '/tmp'; os.makedirs(TMP, exist_ok=True)


def codex_json(prompt: str, schema_path: str, model: str = 'gpt-5.6-sol', effort: str = 'medium', timeout: int = 1500) -> dict:
    """One schema-enforced codex call; raises on failure (callers retry)."""
    out = tempfile.NamedTemporaryFile('w', suffix='.json', dir=TMP, delete=False).name
    subprocess.run(['codex', 'exec', '-m', model, '-c', f'model_reasoning_effort={effort}', '-c', 'project_doc_max_bytes=0', '-c', 'features.code_mode_host=false', '--skip-git-repo-check', '--sandbox', 'read-only', '--ephemeral', '--output-schema', schema_path, '-o', out, '-'],
                   input=prompt, capture_output=True, text=True, timeout=timeout, cwd=TMP)
    return json.load(open(out))


def write_schema(name: str, schema: dict) -> str:
    p = os.path.join(TMP, name); json.dump(schema, open(p, 'w')); return p


def gsm_answer(s: str) -> str:
    m = re.search(r'####\s*(.+)$', s.strip(), re.M); return (m.group(1) if m else s.strip().splitlines()[-1]).replace(',', '').strip()


def boxed(s: str) -> str | None:
    i = s.rfind('\\boxed');
    if i < 0: return None
    j = s.find('{', i); depth = 0
    for k in range(j, len(s)):
        if s[k] == '{': depth += 1
        elif s[k] == '}':
            depth -= 1
            if depth == 0: return s[j + 1:k]
    return None


def final_answer(sol: str) -> str:
    """Final answer of a Greek solution: the «Απάντηση:» line, else a boxed value, else the last number."""
    m = re.search(r'(?im)^\s*\**\s*απ[άa]ντηση\s*\**\s*[:：]\s*\**\s*(.+?)\s*\**\s*$', unicodedata.normalize('NFC', sol))
    if m: return m.group(1).strip()
    b = boxed(sol)
    if b: return b
    nums = re.findall(r'-?\d[\d.,]*', sol); return nums[-1] if nums else ''


def norm_num(s: str):
    """Parse a number written in Greek or English conventions; returns Fraction, or None."""
    t = s.strip().replace('€', '').replace('%', '').replace(' ', '').replace('\u202f', '')
    t = re.sub(r'\\(?:d)?frac\{([^}]*)\}\{([^}]*)\}', r'\1/\2', t); t = t.replace('$', '').strip('.').strip()
    m = re.fullmatch(r'(-?\d+)/(\d+)', t)
    if m: return Fraction(int(m.group(1)), int(m.group(2))) if int(m.group(2)) else None
    if re.fullmatch(r'-?\d{1,3}(\.\d{3})+(,\d+)?', t): t = t.replace('.', '').replace(',', '.')      # Greek: 1.000,5
    elif re.fullmatch(r'-?\d{1,3}(,\d{3})+(\.\d+)?', t): t = t.replace(',', '')                        # English: 1,000.5
    elif re.fullmatch(r'-?\d+,\d+', t): t = t.replace(',', '.')                                           # Greek decimal 3,5
    if re.fullmatch(r'-?\d+(\.\d+)?', t):
        try: return Fraction(t)
        except (ValueError, ZeroDivisionError): return None
    return None


def norm_expr(s: str) -> str:
    t = s.strip().replace(' ', '').replace('\\left', '').replace('\\right', '').replace('\\dfrac', '\\frac').replace('\\tfrac', '\\frac').replace('$', '').replace('^\\circ', '').replace('°', '')
    return t.rstrip('.').lower()


def equiv(a: str, b: str) -> bool:
    """Answer equivalence: numeric (Greek or English formats), else sympy on simple expressions, else normalised string."""
    if not a or not b: return False
    na, nb = norm_num(a), norm_num(b)
    if na is not None and nb is not None: return na == nb
    if norm_expr(a) == norm_expr(b): return True
    try:
        import sympy
        from sympy.parsing.sympy_parser import parse_expr
        ea, eb = parse_expr(norm_expr(a).replace('^', '**')), parse_expr(norm_expr(b).replace('^', '**'))
        return sympy.simplify(ea - eb) == 0
    except Exception: return False


GREEK = '\u0370-\u03ff\u1f00-\u1fff'


def fmt_checks(sol: str) -> dict:
    """Greek formatting conventions in a solution: decimal comma, euro after the number, an answer line, Greek script."""
    decimals_en = re.findall(r'(?<![\d.])\d+\.\d{1,2}(?![\d.])', sol)          # 3.5 (English decimal) vs 1.000 (Greek thousands)
    letters = re.findall(rf'[{GREEK}A-Za-z]', sol); greek = re.findall(rf'[{GREEK}]', sol)
    return dict(decimal_comma_ok=not decimals_en, euro_after_number=not re.search(r'€\s?\d', sol), answer_line=bool(re.search(r'(?im)^\s*\**\s*απ[άa]ντηση', unicodedata.normalize('NFC', sol))),
                greek_share=round(len(greek) / max(1, len(letters)), 3))
