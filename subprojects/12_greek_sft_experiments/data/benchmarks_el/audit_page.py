#!/usr/bin/env python3
"""Owner's native audit pages: a random sample of 59 items per benchmark (the size that bounds the defect rate at 5% if zero defects are found), English and
Greek side by side, with the checks and provenance shown. One HTML per benchmark. Usage: python3 audit_page.py <out_dir>"""
import html, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CSS = """<style>
:root{--bg:#f7f6f2;--ink:#1e1d1a;--muted:#6b675e;--rule:#dcd8cf;--card:#fffdf8;--en:#f1f0ea;--el:#eef3f8;--acc:#3b5f8a;--warn:#a06a10}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#171613;--ink:#ece8df;--muted:#a49f93;--rule:#3a3730;--card:#211f1b;--en:#26241f;--el:#1e2a36;--acc:#8fb3dd;--warn:#e0a94a}}
:root[data-theme="dark"]{--bg:#171613;--ink:#ece8df;--muted:#a49f93;--rule:#3a3730;--card:#211f1b;--en:#26241f;--el:#1e2a36;--acc:#8fb3dd;--warn:#e0a94a}
body{background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,"Helvetica Neue",Arial,sans-serif;margin:0;padding:24px} h1{font-size:22px;margin:0 0 4px} .sub{color:var(--muted);margin-bottom:18px;max-width:900px}
.it{background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:12px 14px;margin:0 0 14px;max-width:1000px} .meta{font-size:12px;color:var(--muted);margin-bottom:6px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:10px} .en,.el{padding:8px 10px;border-radius:6px;white-space:pre-wrap;font-size:14px} .en{background:var(--en)} .el{background:var(--el)} .lab{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.warn{color:var(--warn)} @media (max-width:700px){.pair{grid-template-columns:1fr}}</style>"""


def page(title, sub, items, out):
    h = [f'<title>{html.escape(title)}</title>', CSS, f'<h1>{html.escape(title)}</h1><div class="sub">{html.escape(sub)}</div>']
    for meta, en, el in items:
        h.append(f'<div class="it"><div class="meta">{html.escape(meta)}</div><div class="pair"><div class="en"><div class="lab">English</div>{html.escape(en)}</div><div class="el"><div class="lab">Ελληνικά</div>{html.escape(el)}</div></div></div>')
    open(out, 'w').write('\n'.join(h))


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True); rng = random.Random(59); L = lambda p: [json.loads(l) for l in open(os.path.join(HERE, p))] if os.path.exists(os.path.join(HERE, p)) else []
    m = L('math500/problems_el_final.jsonl')
    if m:
        s = rng.sample(sorted(m, key=lambda r: r['id']), 59); page('MATH-500 Greek Audit', '59 random problems of 500. Check: same question and givens, school terminology, natural Greek, LaTeX untouched (prose in \\text{} translated), answer format instruction kept.', [(f"{r['id']} · {r['subject']} L{r['level']} · answer {r['answer']} · checks {json.dumps(r['checks'])}" + (' · template sibling in SFT' if r.get('template_sibling_in_sft') else ''), r['problem_en'], r['problem_el']) for r in s], os.path.join(out, 'audit_math500.html'))
    x = L('xstest/prompts_el_final.jsonl') or L('xstest/prompts_el.jsonl')
    if x:
        s = rng.sample(sorted(x, key=lambda r: int(r['id'])), 59); page('XSTest Greek Audit', '59 random prompts of 450 (safe = looks alarming but is benign; unsafe = genuinely harmful). Check: does the Greek keep the alarming surface AND the benign reading (safe), the same harm (unsafe), and read like something a user would type?', [(f"id {r['id']} · {r['type']} · {r['label']} · trigger «{r.get('trigger_el', '')}» · transfer {r.get('transfer')}", r['prompt_en'], r['prompt_el']) for r in s], os.path.join(out, 'audit_xstest.html'))
    i = L('ifbench/prompts_el_final.jsonl')
    if i:
        s = rng.sample(sorted(i, key=lambda r: int(r['id'])), 59); page('IFBench Greek Audit', '59 random prompts of 300. The Greek prompt = translated task + the constraint sentence rendered by our Greek checker. Check: the task means the same, the Greek constraint sentence is clear and natural, and the chosen Greek keywords/passages fit.', [(f"key {r['id']} · {', '.join(r['instruction_id_list'])} · overlap {r['overlap_class']} · kwargs {json.dumps(r['kwargs'], ensure_ascii=False)[:160]}", r['prompt_en'], r['prompt_el']) for r in s], os.path.join(out, 'audit_ifbench.html'))
    c = L('multichallenge/conversations_el_final.jsonl') or L('multichallenge/conversations_el.jsonl')
    if c:
        s = rng.sample(sorted(c, key=lambda r: r['id']), min(59, len(c))); fmt = lambda t: '\n\n'.join(f"[{m['role'].upper()}] {m['content']}" for m in t)
        page('MultiChallenge Greek Audit', '59 random conversations of 273. The model under test writes the next assistant turn; the judge checks it against the target question. Check: every turn faithful, entity forms consistent, the target question asks the same thing, and the test still makes sense in Greek.', [(f"{r['id']} · {r['axis']} · {len(r['turns_el'])} turns · nontransferable {r['nontransferable']} · TARGET EN: {r['target_question_en']} · TARGET EL: {r['target_question_el']}", fmt(r['turns_en']), fmt(r['turns_el'])) for r in s], os.path.join(out, 'audit_multichallenge.html'))
    print('pages in', out, os.listdir(out))


if __name__ == '__main__': main()
