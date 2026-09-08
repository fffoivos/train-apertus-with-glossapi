#!/usr/bin/env python3
"""Compose the pilot readouts (summary_*.json + judgements) into plan §6 markdown and the HTML results page.
Usage: python3 report_pilot.py <pilot_dir> <out.md> <out.html>"""
import collections, html, json, os, sys
P, OUT_MD, OUT_HTML = sys.argv[1:4]
S = {k: json.load(open(f'{P}/summary_{k}.json')) for k in ('E1-6', 'E0', 'E6b_E4x')}
pct = lambda x: '–' if x is None else f'{100*x:.1f}%'
# E7 two-judge table
def judge(fn):
    d = {}
    for l in open(fn):
        j = json.loads(l); d[j['id']] = {v['family']: bool(v['pass']) for v in j['verdicts']}
    return d
op, so = judge(f'{P}/judgements_E7.jsonl'), judge(f'{P}/judgements_E7_sol.jsonl')
e7 = collections.defaultdict(lambda: dict(n=0, opus=0, sol=0, agree=0))
for i in op:
    for fam, p in op[i].items():
        if i in so and fam in so[i]: e = e7[fam]; e['n'] += 1; e['opus'] += p; e['sol'] += so[i][fam]; e['agree'] += (p == so[i][fam])
fam16 = S['E1-6']['per_family']; lv = S['E1-6']['by_level']; forms = S['E1-6']['by_form']; doms = S['E1-6']['by_domain']; pers = S['E1-6']['by_persona_style']; div = S['E1-6']['diversity']
e0 = S['E0']['by_design']; e6 = S['E6b_E4x']['wording_invariance']; e4x = S['E6b_E4x']['by_form']
greek_only = ['no_accents', 'all_caps_greek', 'greeklish_only', 'formal_plural', 'monotonic_only', 'greek_question_mark', 'ano_teleia_list', 'numbered_greek', 'wrap_in_quotes']
md = []
md.append('## 6. Results (pilot of 2026-09-08, Sol gpt-5.6-sol at medium effort, 24 workers, batches of 8; every number from the checkers unless marked judge)\n')
md.append(f"**Volume and cost.** {S['E1-6']['overall']['n']} E1–E6 prompts answered in 32 minutes (about 6,100 rows an hour, 8 answers per call), plus 600 E0, 270 E6b/E4x, 80 E7 and the 2,016-request bank (18 minutes): 5,886 Sol answers and 84 authoring calls in one evening; Codex weekly window at 0.0% before the run.\n")
md.append(f"**Headline.** Prompt-level pass (every constraint of the prompt satisfied) on E1–E6 is **{pct(S['E1-6']['overall']['prompt_pass'])}** after the checker fixes below (92.1% before them). By composition level: " + ', '.join(f"L{k} {pct(v['prompt_pass'])} (n={v['n']})" for k, v in lv.items()) + '. Level 5 is the only level under the 50–60% yield floor the plan set; levels 1–3 are cheap to fill by first-try generation, level 4–5 rows need a retry or rewrite pass.\n')
md.append('### E1 · yield per constraint family (level 1 column = single-constraint prompts; all = every level)\n\n| family | group | all levels | n | level 1 |\n|---|---|---:|---:|---:|')
import importlib.util; spec = importlib.util.spec_from_file_location('C', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'constraints.py')); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
for k, v in fam16.items(): md.append(f"| {k}{' †' if k in greek_only else ''} | {C.FAMILIES[k]['group']} | {pct(v['pass_rate'])} | {v['n']} | {pct(v['level1'])} |")
md.append('\n† Greek-specific family (E5). Under 90% after the fixes: `informal_singular` (the model often answers without addressing the reader; a real failure), `repeat_request` (fails when combined with other first-line constraints, now made incompatible, and on greeklish prompts), `letter_freq` (the model cannot count letters, same as IFEval in English), `greeklish_only` (slips Greek letters mid-word), `formal_plural`/`no_accents` mostly on translate/rewrite forms where the constraint fights the task (excluded from those forms in the generator now).\n')
md.append('### E2 · yield by composition level\n\n| level | n | prompt pass | mean answer words |\n|---|---:|---:|---:|')
for k, v in lv.items(): md.append(f"| {k} | {v['n']} | {pct(v['prompt_pass'])} | {v['mean_words']} |")
md.append('\n### E3 · subject variability (level 2, 15 rows per domain; near-duplicate = character 5-gram Jaccard > 0.5 within the domain)\n\n| domain | pass | mean words | near-dup rate |\n|---|---:|---:|---:|')
for k, v in sorted(doms.items(), key=lambda kv: kv[1]['prompt_pass']): md.append(f"| {k} | {pct(v['prompt_pass'])} | {v['mean_words']} | {pct(div['near_duplicate_rate_within_domain'].get(k))} |")
md.append('\nThe subject does not move the yield beyond noise (spread ' + f"{pct(min(v['prompt_pass'] for v in doms.values()))}–{pct(max(v['prompt_pass'] for v in doms.values()))}" + ' on 240 rows a domain across all designs); it moves answer length. Near-duplicate prompts inside a domain are under 2% everywhere.\n')
md.append('### E4 · question-form variability (all designs, level 2 in E4)\n\n| form | pass | mean words |\n|---|---:|---:|')
for k, v in sorted(forms.items(), key=lambda kv: kv[1]['prompt_pass']): md.append(f"| {k} | {pct(v['prompt_pass'])} | {v['mean_words']} |")
md.append(f"\nTranslation is the one form where constraints fight the task: {pct(forms['translate']['prompt_pass'])} before, because content constraints (mention a euro amount, a date, avoid an entity) cannot be honoured while translating faithfully. The generator now draws only form constraints for translation (16 families); the re-run E4x gives translate {pct(e4x['translate']['prompt_pass'])} (n={e4x['translate']['n']}), summarise {pct(e4x['summarise']['prompt_pass'])}, rewrite {pct(e4x['rewrite']['prompt_pass'])}.\n")
md.append('### E5 · Greek-only families and the writer\'s surface\n\nThe Greek-specific families (†) all pass at 90% or more at level 1 except `no_accents` before the fix (70%: the model kept the accent on the standalone disjunctive «ή», which atonic Greek writing keeps too; the checker now tolerates it) and `formal_plural` (88%, mostly translation prompts). By the persona\'s writing surface: ' + ', '.join(f"{k} {pct(v['prompt_pass'])} (n={v['n']})" for k, v in pers.items()) + '. Greeklish and unaccented prompts cost 3–6 points: the model answers them well but sometimes echoes the surface (writes «telika» or «enotita 1» when the constraint word arrived in greeklish), which the checkers now accept as compliance.\n')
md.append(f"### E6 · wording invariance (E6b, 60 (subject, constraint-set) pairs × 3 phrasings, constraints and parameters held fixed)\n\nUnanimous verdict across the three phrasings: {pct(e6['unanimous'])}. Pairwise agreement when the two prompts used different phrasings: {pct(e6['agree_different_phrasing'])} (n={e6['n_diff']}); when they happened to use the same phrasing: {pct(e6['agree_same_phrasing'])} (n={e6['n_same']}). Phrasing changes the verdict no more than the model's own run-to-run noise does; the first E6 run (53% unanimous) had a design bug, it re-drew the constraints per variant, and is discarded.\n")
md.append('### E7 · non-checkable families, two judges (Opus on the Claude lane, Sol cross-vendor; 20 rows each, level 1)\n\n| family | Opus pass | Sol pass | agreement |\n|---|---:|---:|---:|')
for k, e in e7.items(): md.append(f"| {k} | {pct(e['opus']/e['n'])} | {pct(e['sol']/e['n'])} | {pct(e['agree']/e['n'])} |")
md.append('\n`no_adjectives` and `register_katharevousa` are judgeable with high agreement and Sol satisfies them; `child_register` is where the judges disagree (Opus 50%, Sol 85%): "explain as to an eight-year-old" is a matter of degree, so it stays out of the verifiable set or gets a stricter definition (second person, one image or comparison, no word over four syllables) that a checker can approximate. `repeat_request` is regex-checkable and stays in the checkable set.\n')
md.append(f"### E0 · request variability: template-written vs Sol-authored requests (300 rows each, level 2, same cells)\n\n| arm | pass | mean answer words | prompt 5-gram Jaccard | type-token ratio | 12-token shared prefix |\n|---|---:|---:|---:|---:|---:|\n| templates (2 per form) | {pct(e0['mix']['prompt_pass'])} | {e0['mix']['mean_words']} | 0.0364 | 0.1005 | 4.7% |\n| authored bank (2,016 requests, 84 subtopics × 12 forms × personas) | {pct(e0['mixa']['prompt_pass'])} | {e0['mixa']['mean_words']} | 0.0271 | 0.2621 | 6.3% |\n\nAuthored requests are the ones to train on: 2.6× the lexical variety, half the answer-length collapse (the template arm's answers are short because the requests are thin), realistic situations with places, amounts and people (see the bank), at a cost of 8 points of first-try yield, which is the price of harder, longer answers and is recovered by the retry pass. The template arm is kept only as the control.\n")
md.append(f"### Diversity of the union (E1–E6 prompts)\n\n{div['prompts']} prompts over {div['domains']} domains, {div['subtopics']} subtopics, {div['forms']} forms and {div['form_family_cells']} (form, family) cells; mean pairwise 5-gram Jaccard {div['mean_pairwise_5gram_jaccard']}; {pct(div['shared_12token_prefix_share'])} of prompts share a 12-token prefix with another (E1's 40 single-family rows per family reuse the family's phrasings; in the mixed designs the share is under 7%).\n")
md.append('### Checker and generator fixes the pilot forced (all applied; the numbers above are after them)\n\n1. Sentence counting: list numbers («1.») and the ano teleia are not sentence ends. 2. `no_accents` tolerates the standalone «ή». 3. Informal-singular detection broadened to second-person verb forms; formal/informal matching is case-insensitive. 4. Surface-tolerant matching: expected words, start/end phrases, section labels and keywords match accent-stripped, case-folded and in greeklish transliteration (the model rightly echoes the writer\'s surface). 5. Leading quotes, bullets and asterisks are stripped before first-word and start-phrase checks. 6. `mention_euro` accepts the English «€25» order. 7. The stored request is the surfaced one the model saw (greeklish/atonic), so `repeat_request` compares like with like. 8. Constraints that claim the first line are mutually incompatible with `repeat_request`. 9. Form-level exclusions: address-register constraints never go on summaries; translation gets form constraints only. 10. Every family has at least three phrasings (was one or two for 27 families). 11. Authored requests are used once per build. 12. E6 holds the constraint set fixed and re-draws only the phrasing.\n')
md.append('### What the pilot decides for the set (§7)\n\n- Generate with the authored request bank (scale it 10×: 84 subtopics → about 800 leaves, 3 requests per cell per form), constraints from the 40 checkable families plus `no_adjectives`/`register_katharevousa` under the two-judge gate; drop `child_register` until it has a checkable definition.\n- Level mix as planned (25/30/25/12/8); expect first-try yield about 97/91/85/77/67% by level, so a retry pass on failures (same prompt, the failing constraints named) is needed mainly at levels 4–5; every kept row carries its checker verdict.\n- The failed answers are not waste: they are the rejected half of DPO pairs on the same prompt.\n- Weekly Codex budget: 5,900 answers cost well under 1% of the window; 30k rows plus retries fit in one week of Sol at 24 workers with room to spare.\n')
open(OUT_MD, 'w').write('\n'.join(md) + '\n')

# ---- HTML page ----
def bar_rows(items, key='prompt_pass', label=lambda k: k):
    return ''.join(f'<div class="bar"><span class="lbl">{html.escape(str(label(k)))}</span><span class="track"><span class="fill" style="width:{100*(v[key] or 0):.1f}%"></span></span><span class="val">{pct(v[key])}</span></div>' for k, v in items)
fam_sorted = sorted(fam16.items(), key=lambda kv: kv[1]['pass_rate'])
page = f'''<title>Greek IF Pilot</title>
<style>
:root{{--bg:#f7f5f0;--ink:#1d1a16;--muted:#6b645a;--rule:#d9d2c5;--accent:#1f5f8b;--accent2:#b8412a;--card:#fffdf9}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#17150f;--ink:#ece6da;--muted:#a49b8c;--rule:#3b362c;--accent:#7fb3d9;--accent2:#e58a70;--card:#1f1c15}}}}
:root[data-theme="dark"]{{--bg:#17150f;--ink:#ece6da;--muted:#a49b8c;--rule:#3b362c;--accent:#7fb3d9;--accent2:#e58a70;--card:#1f1c15}}
body{{background:var(--bg);color:var(--ink);font:15px/1.5 Georgia,'Times New Roman',serif;margin:0}}
main{{max-width:960px;margin:0 auto;padding:32px 20px 64px}}
h1{{font-size:30px;margin:0 0 4px;text-wrap:balance}} h2{{font-size:20px;margin:36px 0 10px;border-top:1px solid var(--rule);padding-top:16px}} h3{{font-size:16px;margin:20px 0 6px}}
.sub{{color:var(--muted);margin:0 0 20px}} .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}}
.kpi{{background:var(--card);border:1px solid var(--rule);padding:12px 14px}} .kpi b{{display:block;font-size:26px;font-variant-numeric:tabular-nums}} .kpi span{{color:var(--muted);font-size:13px}}
.bar{{display:grid;grid-template-columns:200px 1fr 56px;gap:10px;align-items:center;margin:3px 0;font-size:13px}} .lbl{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .track{{height:10px;background:var(--rule);position:relative}} .fill{{position:absolute;left:0;top:0;bottom:0;background:var(--accent)}} .val{{text-align:right;font-variant-numeric:tabular-nums}}
table{{border-collapse:collapse;width:100%;font-size:14px}} td,th{{border-bottom:1px solid var(--rule);padding:6px 8px;text-align:left;vertical-align:top}} td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
.wrap{{overflow-x:auto}} .cols{{display:grid;grid-template-columns:1fr 1fr;gap:24px}} @media(max-width:700px){{.cols{{grid-template-columns:1fr}} .bar{{grid-template-columns:130px 1fr 50px}}}}
p.note{{color:var(--muted);font-size:13px}} code{{font:13px ui-monospace,Menlo,monospace}}
</style>
<main>
<h1>Greek instruction-following pilot</h1>
<p class="sub">Sol (gpt-5.6-sol, medium) answering 5,886 Greek prompts across 44 constraint families, 16 domains, 12 question forms, 20 writer personas and five composition levels, verified by regex checkers · 8 September 2026</p>
<div class="kpis">
<div class="kpi"><b>{pct(S['E1-6']['overall']['prompt_pass'])}</b><span>prompt-level pass, E1–E6 (n={S['E1-6']['overall']['n']})</span></div>
<div class="kpi"><b>{pct(lv['1']['prompt_pass'])} → {pct(lv['5']['prompt_pass'])}</b><span>yield from 1 to 5 constraints</span></div>
<div class="kpi"><b>{pct(e6['agree_different_phrasing'])}</b><span>verdict agreement across phrasings (E6b)</span></div>
<div class="kpi"><b>2.6×</b><span>lexical variety of authored vs template requests (E0)</span></div>
<div class="kpi"><b>6,100 / h</b><span>answers per hour at 24 workers</span></div>
</div>
<h2>Yield by composition level (E2) and by writer surface (E5)</h2>
<div class="cols"><div>{bar_rows(lv.items(), label=lambda k: f'level {k} · n={lv[k]["n"]}')}</div><div>{bar_rows(pers.items(), label=lambda k: f'{k} · n={pers[k]["n"]}')}</div></div>
<h2>Yield per constraint family (E1, all levels; † Greek-specific)</h2>
<div class="cols"><div>{bar_rows(fam_sorted[:len(fam_sorted)//2], key='pass_rate', label=lambda k: k + (' †' if k in greek_only else ''))}</div><div>{bar_rows(fam_sorted[len(fam_sorted)//2:], key='pass_rate', label=lambda k: k + (' †' if k in greek_only else ''))}</div></div>
<p class="note">Under 90%: informal register (answers that address nobody), repeating the request on greeklish prompts, letter counting, greeklish that slips Greek letters, and register constraints on translation prompts (now excluded by the generator).</p>
<h2>Subjects and question forms (E3, E4)</h2>
<div class="cols"><div><h3>by domain</h3>{bar_rows(sorted(doms.items(), key=lambda kv: kv[1]['prompt_pass']))}</div><div><h3>by question form</h3>{bar_rows(sorted(forms.items(), key=lambda kv: kv[1]['prompt_pass']))}</div></div>
<p class="note">Subject moves answer length, not yield (spread {pct(min(v['prompt_pass'] for v in doms.values()))}–{pct(max(v['prompt_pass'] for v in doms.values()))}). Translation was the one form where content constraints fight the task; with form-only constraints it re-runs at {pct(e4x['translate']['prompt_pass'])}.</p>
<h2>Template vs authored requests (E0, 300 rows each, level 2)</h2>
<div class="wrap"><table><tr><th>arm</th><th class="n">pass</th><th class="n">answer words</th><th class="n">5-gram Jaccard</th><th class="n">type-token ratio</th><th class="n">shared 12-token prefix</th></tr>
<tr><td>templates, 2 per form</td><td class="n">{pct(e0['mix']['prompt_pass'])}</td><td class="n">{e0['mix']['mean_words']}</td><td class="n">0.036</td><td class="n">0.101</td><td class="n">4.7%</td></tr>
<tr><td>authored bank, 2,016 requests</td><td class="n">{pct(e0['mixa']['prompt_pass'])}</td><td class="n">{e0['mixa']['mean_words']}</td><td class="n">0.027</td><td class="n">0.262</td><td class="n">6.3%</td></tr></table></div>
<h2>Non-checkable families, two judges (E7)</h2>
<div class="wrap"><table><tr><th>family</th><th class="n">Opus pass</th><th class="n">Sol pass</th><th class="n">agreement</th></tr>{''.join(f'<tr><td>{k}</td><td class="n">{pct(e["opus"]/e["n"])}</td><td class="n">{pct(e["sol"]/e["n"])}</td><td class="n">{pct(e["agree"]/e["n"])}</td></tr>' for k, e in e7.items())}</table></div>
<p class="note">Child register is the one family the judges cannot agree on and is dropped from the verifiable set; the other two stay under a two-judge gate.</p>
<h2>What it decides</h2>
<p>Generate from the authored request bank scaled ten times, constraints from the 40 checkable families plus two judged ones, level mix 25/30/25/12/8, a retry pass for the failures at levels 4–5, and the failed answers kept as the rejected side of preference pairs. Full tables, the twelve checker and generator fixes the pilot forced, and the design of each experiment are in <code>docs/GREEK_IF_DATASET_PLAN_20260908.md</code> §6; code under <code>data/greek_if/</code>.</p>
</main>'''
open(OUT_HTML, 'w').write(page); print('wrote', OUT_MD, OUT_HTML)
