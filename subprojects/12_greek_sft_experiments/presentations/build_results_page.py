#!/usr/bin/env python3
"""Build the Greek Apertus results page (HTML artifact): CPT trajectory, round-one SFT vs peers, the RLHF gap, ellinika-bench, and the
round-two training data with the Hugging Face link. Numbers are copied from the result files named in each section.
Usage: python3 build_results_page.py <out.html>"""
import sys, html
OUT = sys.argv[1]
e = html.escape
HF = 'https://huggingface.co/datasets/fffoivos/greek-apertus-sft'

# ---- data ----
CPT = [  # iter, tokens B, GreekMMLU clean %, retention macro (where measured)
    (0, 0.0, 35.78), (400, 1.678, 53.57), (1192, 5.0, 53.57), (2384, 9.999, 53.91), (3576, 14.999, 52.41), (4768, 19.998, 55.18),
    (5960, 24.998, 56.40), (7152, 29.998, 55.06), (8344, 34.997, 54.65), (9536, 39.997, 56.81), (10728, 44.996, 56.59), (11920, 49.996, 55.93),
    (13112, 54.996, 54.34), (14304, 59.995, 54.60), (14627, 61.35, 54.69), (15496, 64.995, 53.80), (16688, 69.995, 54.79), (17880, 74.994, 53.53), (18284, 76.689, 54.85)]
RET = [('base Apertus-8B-2509', 65.82), ('iter 400 (1.7B)', 66.10), ('avg_peak5 (SFT base)', 64.58), ('iter 9536 (40B)', 63.68), ('avg_cooldown5', 63.36), ('terminal (76.7B)', 62.95)]
RET_TASKS = [('arc_challenge', 58.70, 51.19, 56.40, 52.82, 51.37), ('arc_easy', 83.63, 76.47, 82.37, 78.62, 79.21), ('hellaswag', 78.84, 61.78, 78.03, 77.07, 76.37), ('winogrande', 69.30, 63.06, 69.85, 69.93, 68.51), ('piqa', 79.92, 74.97, 80.30, 79.71, 79.11), ('mmlu', 59.23, 57.53, 60.01, 56.64, 56.00), ('global_mmlu lite', 52.46, 51.75, 52.40, 50.80, 49.18), ('xcopa', 65.75, 63.27, 65.47, 63.75, 62.87), ('xnli', 44.00, 41.16, 45.04, 43.83, 43.95)]
PEERS = [  # label, prompt-strict, inst-strict, strict avg, MGSM, ours?
    ('Gemma-3-12B-it (50% larger)', 0.675, 0.763, 71.9, 0.908, False), ('Qwen3.5-9B, thinking off', 0.649, 0.740, 69.4, 0.876, False), ('Llama-Krikri-8B-Instruct', 0.614, 0.723, 66.8, 0.676, False),
    ('ours: lr 1e-5, epoch 3', 0.512, 0.612, 56.2, 0.392, True), ('Apertus-8B-Instruct-2509 (no Greek CPT)', 0.505, 0.615, 56.0, 0.532, False), ('ours: adapted imports E3, epoch 2', 0.497, 0.601, 54.9, 0.384, True),
    ('ours: lr 5e-6, epoch 3', 0.486, 0.584, 53.5, 0.416, True), ('ours: the pick, lr 1e-5, epoch 2', 0.479, 0.586, 53.3, 0.400, True), ('ours: raw imports E3′, epoch 2', 0.470, 0.579, 52.4, 0.408, True),
    ('ours: paired English E2, epoch 2', 0.473, 0.568, 52.1, 0.404, True), ('ours: from the terminal CPT checkpoint', 0.429, 0.540, 48.4, 0.328, True), ('Meltemi-7B-Instruct-v1.5', 0.277, 0.375, 32.6, 0.208, False)]
GMMLU_SFT = [('CPT base 18-avg (the SFT base)', 56.78, 1.0895), ('ours: the pick, E1 lr 1e-5 ep2', 56.02, 1.1646), ('ours: adapted imports, E3', 55.18, 1.1803), ('Apertus-8B-Instruct-2509', 54.86, 1.1029), ('Llama-Krikri-8B-Instruct', 51.97, 1.3080)]
NATIVE = [('ASEP MCQA', .562, .551, .614, .613, .616, .601), ('DemosQA', .469, .466, .472, .477, .467, .464), ('GPCR', .608, .629, .655, .644, .639, .624), ('Medical MCQA', .425, .384, .489, .494, .487, .463),
          ('OYXOY metaphor', .345, .339, .552, .581, .568, .339), ('OYXOY NLI', .651, .387, .643, .642, .642, .388), ('OYXOY WiC', .549, .336, .775, .775, .775, .737), ('OYXOY WSD', .385, .381, .390, .392, .391, .384), ('macro (8)', .499, .434, .574, .577, .573, .500)]
READING = [('base model (no SFT)', 1.13, 2.26, 0.00, 1.72), ('the pick: lr 1e-5, ep2', 3.13, 3.87, 0.87, 2.92), ('lr 1e-5, ep3', 3.38, 3.90, 0.90, 3.03), ('adapted imports E3', 3.15, 3.82, 0.90, 2.92), ('raw imports E3′', 2.95, 3.92, 0.92, 2.92), ('paired English E2', 3.00, 3.92, 0.90, 3.00)]
GAP_LIT = [('Tulu 3 8B (prompt-loose)', '72.8', '81.1 (+8.3)', '82.4 (+1.3, RLVR)', 'arXiv 2411.15124'), ('Tulu 3 70B (prompt-loose)', '82.1', '82.6 (+0.5)', '83.2 (+0.6)', 'same'), ('OLMo 2 7B', '66.9', '73.0 (+6.1)', '72.3 (−0.7)', 'model card'),
           ('OLMo 2 13B', '68.6', '80.2 (+11.6)', '82.6 (+2.4)', 'model card'), ('OLMo 3 7B Instruct', '81.7', '82.0 (+0.3)', '85.6 (+3.6)', 'arXiv 2512.13961'), ('OLMo 3 7B Think', '77.9', '75.9 (−2.0)', '88.2 (+12.3)', 'same'),
           ('AMALIA-9B (prompt-strict)', '56.7', '61.6 (+4.9)', '–', 'arXiv 2603.26511'), ('Conifer-7B (prompt-loose)', '50.8', '52.3 (+1.5)', '–', 'arXiv 2404.02823'), ('UltraIF Llama-3.1-8B (prompt-strict)', '69.9', '71.4 (+1.5)', '–', 'arXiv 2502.04153')]
LANG_GAP = [('Llama-3.1-8B-Instruct', 75.1, 45.8, 'Greek IFEval, ILSP'), ('Llama-Krikri-8B-Instruct', 82.4, 67.5, 'Greek IFEval'), ('Apertus-8B-Instruct', 71.7, 68.9, 'Multi-IFEval'), ('Qwen3-8B', 86.5, 82.8, 'Multi-IFEval'), ('gemma-3-12b-it', 80.0, 80.2, 'Multi-IFEval')]
ELL = [('Α Γλώσσα', 60, '40/67'), ('Β Νοημοσύνη', 54, '138/255'), ('Δ Συλλογιστική / κώδικας / σχεδιασμός', 59, '22/37'), ('Probes', 62, '5/8')]
ELL_BI = [('el', 0.0, 28.0, 63.4, 61.5), ('en', 2.5, 38.5, 75.2, 72.7), ('fr', 6.2, 31.7, 76.4, 74.5), ('de', 5.6, 34.8, 73.9, 72.7)]
BLOCKS = [('dolci_precise_if_20k', 'allenai/Dolci-Instruct-SFT, Precise IF (judge-screened)', 3934, 2.17, 1), ('ifeval_like', 'argilla/ifeval-like-data', 46619, 12.95, 1), ('openmath_gsm', 'nvidia/OpenMathInstruct-2, GSM8K-style', 91458, 25.31, 1),
          ('nemotron_chat_a + b', 'NVIDIA Nemotron post-training chat, halves A and B', 46747, 72.47, 1), ('dolci_chat', 'OpenAssistant via Dolci', 3039, 1.12, 1), ('dolci_code_algo_20k', 'Dolci Python algorithms (judge-screened)', 5084, 2.24, 1),
          ('dolci_reasoning', 'Dolci verifiable reasoning', 27445, 15.46, 1), ('puzzles', 'Dolci logic puzzles, brute-force verified', 11139, 4.16, 1), ('dolci_tooluse', 'Dolci tool use', 27445, 28.42, 1), ('dolci_science', 'Dolci OpenThoughts3+ science (judge-screened)', 6176, 5.66, 1),
          ('smoltalk2_multilingual', 'HuggingFaceTB/smoltalk2, de/fr/es/pt/it', 20412, 11.26, 1), ('dolci_safety', 'Dolci WildGuardMix + CoCoNot', 6256, 1.78, 1), ('greek_rewrite', 'our Greek rewriting and summarising set', 2000, 1.20, 1), ('greek_ours', 'our round-one Greek set, adapted to the Greek vantage', 20000, 7.80, 2)]
PERS = [('A', 660, 'Greece-centric facts from the Greek vantage'), ('B', 180, 'who am I: an open project, no name of its own'), ('C', 100, 'identity under pressure'), ('D', 120, 'limits'), ('E', 120, 'refusals in our voice'), ('F', 88, 'sensitive Greek topics'), ('G', 120, 'register')]

# ---- charts ----
def line_chart():
    W, H, L, R, T, B = 760, 300, 56, 16, 18, 44
    xs = [t for _, t, _ in CPT]; ys = [a for _, _, a in CPT]
    x0, x1, y0, y1 = 0, 80, 30, 60
    X = lambda t: L + (t - x0) / (x1 - x0) * (W - L - R); Y = lambda a: T + (y1 - a) / (y1 - y0) * (H - T - B)
    grid = ''.join(f'<line x1="{L}" x2="{W-R}" y1="{Y(a):.1f}" y2="{Y(a):.1f}" class="grid"/><text x="{L-8}" y="{Y(a)+4:.1f}" class="tick" text-anchor="end">{a}</text>' for a in range(30, 61, 5))
    xt = ''.join(f'<text x="{X(t):.1f}" y="{H-B+18}" class="tick" text-anchor="middle">{t}B</text>' for t in (0, 10, 20, 30, 40, 50, 60, 70, 80))
    path = 'M' + ' L'.join(f'{X(t):.1f},{Y(a):.1f}' for t, a in zip(xs, ys))
    dots = ''.join(f'<circle cx="{X(t):.1f}" cy="{Y(a):.1f}" r="3" class="dot"/>' for t, a in zip(xs, ys))
    peak = f'<circle cx="{X(39.997):.1f}" cy="{Y(56.81):.1f}" r="6" class="peak"/><text x="{X(39.997)+9:.1f}" y="{Y(56.81)-8:.1f}" class="lab">peak 56.81% at 40B (iter 9,536)</text>'
    win = f'<rect x="{X(30):.1f}" y="{T}" width="{X(50)-X(30):.1f}" height="{H-T-B}" class="win"/><text x="{X(40):.1f}" y="{T+14}" class="lab" text-anchor="middle">peak window 30–50B, averaged = the SFT base (56.78%)</text>'
    init = f'<text x="{X(0)+6:.1f}" y="{Y(35.78)+16:.1f}" class="lab">init 35.78%</text>'; term = f'<text x="{X(76.689)-4:.1f}" y="{Y(54.85)+18:.1f}" class="lab" text-anchor="end">terminal 54.85%</text>'
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="GreekMMLU accuracy across the 19 CPT checkpoints">{win}{grid}{xt}<path d="{path}" class="line"/>{dots}{peak}{init}{term}<text x="{L}" y="{H-6}" class="axis">token slots seen during continued pre-training (billions)</text><text transform="rotate(-90)" x="{-(H/2):.0f}" y="14" class="axis" text-anchor="middle">GreekMMLU, clean subset, accuracy %</text></svg>'
def bar_chart():
    rows = sorted(PEERS, key=lambda p: -p[3]); W, L, R, bh, gap = 760, 300, 60, 18, 6; H = len(rows) * (bh + gap) + 30
    X = lambda v: L + v / 80 * (W - L - R)
    out = []
    for i, (lab, ps, isv, avg, mg, ours) in enumerate(rows):
        y = 8 + i * (bh + gap)
        out.append(f'<text x="{L-8}" y="{y+bh-4}" class="blab{" ours" if ours else ""}" text-anchor="end">{e(lab)}</text><rect x="{L}" y="{y}" width="{X(avg)-L:.1f}" height="{bh}" class="bar{" ours" if ours else ""}"/><text x="{X(avg)+6:.1f}" y="{y+bh-4}" class="bval">{avg:.1f}</text>')
    ticks = ''.join(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="4" y2="{H-22}" class="grid"/><text x="{X(v):.1f}" y="{H-8}" class="tick" text-anchor="middle">{v}</text>' for v in (0, 20, 40, 60, 80))
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Greek IFEval strict average, ours versus peers">{ticks}{"".join(out)}</svg>'

def table(head, rows, cls='', fmt=None):
    th = ''.join(f'<th>{e(h)}</th>' for h in head)
    body = ''
    for r in rows:
        cells = ''
        for j, c in enumerate(r):
            v = c if isinstance(c, str) else (fmt[j](c) if fmt and fmt[j] else (f'{c:.2f}' if isinstance(c, float) else f'{c:,}'))
            cells += f'<td class="{"n" if not isinstance(c, str) or j > 0 and c.replace(".", "").replace("−", "").replace("-", "").replace("%", "").replace("+", "").replace("(", "").replace(")", "").replace(",", "").replace(" ", "").isdigit() else ""}">{e(v)}</td>'
        body += f'<tr>{cells}</tr>'
    return f'<div class="tbl"><table class="{cls}"><tr>{th}</tr>{body}</table></div>'
pct = lambda v: f'{v:.2f}'
one = lambda v: f'{v:.3f}'

page = f'''<title>Greek Apertus Results</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,500;7..72,700&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400&display=swap">
<style>
:root{{--bg:#F4F6F8;--ink:#14202B;--accent:#0E5C8F;--ours:#B8651B;--good:#3F7D3A;--muted:#5B6B7A;--rule:#D5DCE3;--panel:#FFFFFF;--tint:#E9EFF4;--win:#0E5C8F14;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace;--body:"Source Sans 3","Segoe UI",Roboto,Arial,sans-serif;--display:Literata,Georgia,"Times New Roman",serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0F151B;--ink:#E4E9EE;--accent:#6FB1E3;--ours:#E8A15C;--good:#8CC97F;--muted:#98A6B3;--rule:#28323C;--panel:#161E26;--tint:#1C2630;--win:#6FB1E31A}}}}
:root[data-theme="dark"]{{--bg:#0F151B;--ink:#E4E9EE;--accent:#6FB1E3;--ours:#E8A15C;--good:#8CC97F;--muted:#98A6B3;--rule:#28323C;--panel:#161E26;--tint:#1C2630;--win:#6FB1E31A}}
body{{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:17px;line-height:1.55;margin:0}}
main{{max-width:900px;margin:0 auto;padding:2.5rem 1.25rem 5rem}}
h1{{font-family:var(--display);font-weight:700;font-size:2.2rem;line-height:1.12;margin:0 0 .4rem;text-wrap:balance}}
h2{{font-family:var(--display);font-weight:500;font-size:1.5rem;margin:3rem 0 .8rem;padding-top:1.2rem;border-top:1px solid var(--rule);text-wrap:balance}}
h3{{font-weight:600;font-size:1.05rem;margin:1.6rem 0 .4rem}}
p{{margin:.6rem 0;max-width:72ch}} .eyebrow{{font-size:.8rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 .6rem}}
.lead{{font-size:1.08rem;max-width:72ch}}
nav{{display:flex;flex-wrap:wrap;gap:.35rem .9rem;font-size:.9rem;margin:1rem 0 0}} nav a{{color:var(--accent);text-decoration:none;border-bottom:1px solid transparent}} nav a:hover,nav a:focus-visible{{border-bottom-color:var(--accent);outline:none}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:.8rem;margin:1.4rem 0}} .kpi{{background:var(--panel);border:1px solid var(--rule);border-radius:4px;padding:.8rem 1rem}} .kpi b{{display:block;font-family:var(--mono);font-size:1.5rem;font-weight:400;font-variant-numeric:tabular-nums}} .kpi span{{font-size:.85rem;color:var(--muted)}}
.tbl{{overflow-x:auto;margin:.8rem 0 1.2rem}} table{{border-collapse:collapse;width:100%;font-size:.92rem;line-height:1.4}} th,td{{text-align:left;vertical-align:top;padding:.45rem .6rem;border-bottom:1px solid var(--rule)}} th{{font-weight:600;color:var(--muted);font-size:.78rem;letter-spacing:.05em;text-transform:uppercase;background:var(--tint)}} td.n{{font-family:var(--mono);font-size:.86rem;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
figure{{margin:1rem 0 1.4rem;background:var(--panel);border:1px solid var(--rule);border-radius:4px;padding:.8rem}} figcaption{{font-size:.86rem;color:var(--muted);margin-top:.4rem}} svg{{width:100%;height:auto;display:block}}
.grid{{stroke:var(--rule);stroke-width:1}} .tick,.lab,.axis,.blab,.bval{{fill:var(--ink);font-family:var(--body);font-size:12px}} .tick{{fill:var(--muted);font-family:var(--mono);font-size:11px}} .axis{{fill:var(--muted);font-size:11px}} .lab{{font-size:12px;fill:var(--muted)}}
.line{{fill:none;stroke:var(--accent);stroke-width:2.2}} .dot{{fill:var(--accent)}} .peak{{fill:none;stroke:var(--ours);stroke-width:2.5}} .win{{fill:var(--win)}}
.bar{{fill:var(--accent);opacity:.75}} .bar.ours{{fill:var(--ours);opacity:1}} .blab.ours{{font-weight:600}} .bval{{font-family:var(--mono);font-size:11px}}
.note{{background:var(--tint);border-left:3px solid var(--accent);padding:.6rem .9rem;margin:1rem 0;font-size:.95rem;max-width:none}} .warn{{border-left-color:var(--ours)}}
ul{{padding-left:1.2rem;max-width:72ch}} li{{margin:.25rem 0}} a{{color:var(--accent)}} .src{{font-size:.82rem;color:var(--muted)}}
.cta{{display:inline-block;background:var(--accent);color:#fff;padding:.5rem .9rem;border-radius:4px;text-decoration:none;font-weight:600;margin:.4rem 0}} .cta:focus-visible{{outline:2px solid var(--ours)}}
</style>
<main>
<p class="eyebrow">Greek Apertus · GlossAPI team, EELLAK · results as of 7 September 2026</p>
<h1>Greek Apertus: what the experiments measured so far</h1>
<p class="lead">Continued pre-training of Apertus 8B on Greek, a first round of supervised fine-tuning, and the data assembled for the second round. Every number below is copied from a result file in the project repository, named under each table.</p>
<div class="kpis">
<div class="kpi"><b>56.81%</b><span>GreekMMLU peak after 40B tokens of Greek CPT (from 35.78% at initialisation)</span></div>
<div class="kpi"><b>56.2%</b><span>Greek IFEval strict average, our best round-one SFT run; Apertus-8B-Instruct 56.0%</span></div>
<div class="kpi"><b>−11 pts</b><span>observed gap to Llama-Krikri-8B-Instruct (66.8%); literature puts +5 to +8 of it on DPO</span></div>
<div class="kpi"><b>334,383</b><span>rows in the round-two stage-1 mix, 197.9M tokens, plus 1,388 personality rows</span></div>
</div>
<nav><a href="#cpt">1 Continued pre-training</a><a href="#sft">2 Round-one SFT</a><a href="#gap">3 The RLHF gap</a><a href="#ell">4 ellinika-bench</a><a href="#data">5 Round-two data</a><a href="#caveats">Caveats</a></nav>

<h2 id="cpt">1. Continued pre-training on Greek: 19 checkpoints</h2>
<p>Apertus-8B-2509 continued on the Greek CPT corpus for 76.7B token slots. GreekMMLU on the frozen, decontaminated 16,159-question subset, zero-shot, length-normalised likelihood scoring.</p>
<figure>{line_chart()}<figcaption>GreekMMLU across the run. The uniform average of the five checkpoints between 30B and 50B (56.78%) is the base every SFT arm starts from; it keeps the peak's Greek knowledge with a better native-suite macro (49.93 vs 47.38) and a better retention macro (64.58 vs 63.68). Source: 09_full_8b_cpt_results_analysis/presentations/FULL8_ALL_CHECKPOINT_NATIVE_BENCHMARKS_20260819.data.json, CHECKPOINT_AVERAGE_RESULTS_20260819.md.</figcaption></figure>
<h3>English and multilingual retention (lm-eval, Apertus Table-14 suite, accuracy %)</h3>
{table(['task', 'base Apertus-8B-2509', 'init', '10B', '40B peak', '76.7B terminal'], RET_TASKS, fmt=[None, pct, pct, pct, pct, pct])}
{table(['model', 'retention macro %'], RET, fmt=[None, pct])}
<p class="src">Source: 09_full_8b_cpt_results_analysis/evaluation/RETENTION_LM_EVAL_RESULTS_20260819.md. The base-model anchor was scored on a since-rebuilt lm-eval install and has not been re-anchored.</p>

<h2 id="sft">2. Round-one SFT: our arms against the peers</h2>
<p>All arms start from the 30–50B average. E1 is Greek-only (17,602 rows, eleven adapted configs); E2 adds paired English; E3 adds skills and fr/de rows adapted to the Greek vantage; E3′ is the same rows unadapted. Grid over learning rate and epochs, packing 4,096, assistant-only loss. Peers were scored on the same harness (ILSP Greek IFEval, 541 prompts; Greek MGSM, 250 items); Krikri reproduces its card within a point (66.8 vs 67.5), Meltemi within 0.1.</p>
<figure>{bar_chart()}<figcaption>Greek IFEval strict average (mean of prompt-level and instruction-level strict accuracy). Our runs in amber. Stderr about ±2 points. Source: 12_greek_sft_experiments/results/peer_table.md.</figcaption></figure>
{table(['model', 'IFEval prompt-strict', 'inst-strict', 'strict avg %', 'Greek MGSM'], [(l, ps, isv, avg, mg) for l, ps, isv, avg, mg, _ in PEERS], fmt=[None, one, one, lambda v: f'{v:.1f}', one])}
<h3>Greek knowledge after SFT (GreekMMLU, clean subset)</h3>
{table(['model', 'GreekMMLU clean %', 'choice NLL'], GMMLU_SFT, fmt=[None, pct, lambda v: f'{v:.4f}'])}
<p>SFT costs the base under a point of Greek knowledge; the CPT is what puts us above Apertus-Instruct and Krikri. Seed noise about 0.4 points. Source: results/greekmmlu/greekmmlu_batch_summary.json.</p>
<h3>Native-Greek suite (accuracy, eight benchmarks)</h3>
{table(['benchmark', 'base 18-avg', 'base terminal', 'pick lr1e-5 ep2', 'lr5e-6 ep3', 'replicate seed 43', 'E1 from terminal'], NATIVE, fmt=[None] + [one] * 6)}
<p class="src">Source: results/native_summary.json, results/E0b/greek.json.</p>
<h3>Blind reading (Claude as rater, 39 prompts, scales 1–5 and shares)</h3>
{table(['run', 'answers', 'greek', 'stops', 'warmth'], READING, fmt=[None, pct, pct, pct, pct])}
<p>Rater noise floor: answers 0.1, greek 0.05, stops 0.0. The adaptation verdict from the interviews: adapted imports 2.91 against raw imports 2.63 on the interview mean, a gap fourteen times the seed floor. Source: results/reading2/summary.md, results/READOUT_provisional.md.</p>

<h2 id="gap">3. The RLHF gap</h2>
<p>We have not run preference optimisation, so the gap is estimated from two things: the distance our SFT leaves to instruct models that did, and what the literature reports DPO and RL add at this size.</p>
<div class="note"><strong>Observed.</strong> Our best run lands level with Apertus-8B-Instruct (56.2% vs 56.0%) and 11 points below Krikri, 13 below Qwen3.5-9B, 16 below Gemma-3-12B. On Greek MGSM every run of ours sits at 0.33–0.42 against 0.53 for Apertus-Instruct and 0.68 for Krikri.</div>
<div class="note"><strong>Estimated.</strong> At 7–9B, DPO adds about +5 to +8 IFEval points on top of SFT and verifiable-reward RL another +1 to +3; at 70B the DPO gain collapses to under a point. Constraint-following data explains most of the rest of Krikri's edge.</div>
{table(['model', 'SFT', 'DPO / APO', 'RL', 'source'], GAP_LIT)}
<p class="src">Source: docs/SFT_DATA_REVIEW_20260904.md §(c); design of the preference stage in SFT_ROUND2_PLAN.md §4 (DPO β 0.1 or SimPO, 100k–270k pairs, one epoch, 12–40 node-hours).</p>
<h3>The language gap on the same models (IFEval, English vs Greek or multilingual)</h3>
{table(['model', 'English', 'Greek / multilingual', 'benchmark'], [(m, a, b, s) for m, a, b, s in LANG_GAP], fmt=[None, lambda v: f'{v:.1f}', lambda v: f'{v:.1f}', None])}

<h2 id="ell">4. ellinika-bench</h2>
<p>Our own benchmark: four pillars (Γλώσσα, Νοημοσύνη &amp; Κατανόηση, Παραγωγή, Συλλογιστική / Κώδικας / Σχεδιασμός) plus language-specific probes, three difficulty tiers, in Greek, English, French and German, with the non-Greek editions re-authored natively rather than translated. 449 items per language (441 in English).</p>
<div class="note warn">It has been run on Apertus-8B-Instruct-2509 only. No CPT or SFT checkpoint of ours has been scored on it yet; the design review argues the generative track is a poor instrument for base checkpoints and proposes a likelihood and BPB track first.</div>
{table(['pillar', 'score %', 'correct / total'], ELL, fmt=[None, lambda v: f'{v:d}', None])}
<p>By difficulty: easy 66%, intermediate 53%, hard 46%. Reasoning penalty (English minus Greek on mirrored items): +12 points. LLM-judge mean on production and reasoning items: 69/100.</p>
<h3>Base vs instruct on the MCQ track (161 items per language)</h3>
{table(['language', 'base, generate %', 'base, likelihood %', 'instruct, generate %', 'instruct, likelihood %'], ELL_BI, fmt=[None, lambda v: f'{v:.1f}', lambda v: f'{v:.1f}', lambda v: f'{v:.1f}', lambda v: f'{v:.1f}'])}
<p class="src">Source: apertus-local-chat/benchmark/results/report.md, docs/base-vs-instruct-findings.md.</p>

<h2 id="data">5. The round-two training data</h2>
<p>All SFT datasets of the project now live in one gated Hugging Face repository. It is public with manual approval: request access and the maintainer approves colleagues.</p>
<a class="cta" href="{HF}">{HF.replace('https://', '')}</a>
<p>The rows below are the ones the trainer sees. Judged-out, adapt-flagged and dropped rows are not published.</p>
<h3>round2_stage1: 334,383 training rows, 197.9M tokens, 3,171 dev rows</h3>
{table(['block', 'source', 'rows taken', 'tokens (M)', 'weight'], BLOCKS, fmt=[None, None, lambda v: f'{v:,}', lambda v: f'{v:.2f}', lambda v: f'{v:d}'])}
<p>Each block was judged row by row for task type and for foreign-identity or foreign-vantage assertions before assembly; contamination against our evaluation sets and over-long rows were removed; the Greek sets carry weight 2. One epoch, lr 1e-5 with a cosine schedule to a 0.1 floor, about 7.6 node-hours. Receipt: docs/receipts/receipts_R2_stage1_final_20260906.json.</p>
<h3>personality_v3: 1,388 Greek rows</h3>
{table(['category', 'rows', 'content'], PERS, fmt=[None, lambda v: f'{v:,}', None])}
<p>Written natively from a verified fact sheet and an identity sheet, restyled under the answer style guide (level of detail by question type), corrected by a separate editor pass, and gated: no unresolved placeholders, the size and borders of Greece always with the sea and the EEZ, the agreed identity wording. Not yet assembled into the mix; training is gated on its review.</p>
<h3>Round-one arms</h3>
<p>E1 (17,602 rows), E2 (26,910), E3 (22,919) and E3′ (22,910) with their 658-row dev slices are in the same repository as separate configs.</p>

<h2 id="caveats">Caveats</h2>
<ul>
<li>ellinika-bench has no scores for our checkpoints; Belebele, XQuAD-el, ARC-el, HellaSwag-el and FLORES are configured but were never run.</li>
<li>The RLHF gap is an estimate from published 7–13B results, not a measurement on our model.</li>
<li>The retention base anchor predates a rebuild of the evaluation runtime.</li>
<li>Two "terminal" rows exist in one CPT document; the corrected 2026-08-20 values are used here.</li>
<li>The round-one pick (lr 1e-5, epoch 2) is provisional: the blind reading rates epoch 3 higher on answer quality.</li>
<li>The knowledge-cutoff wording and the licence inside the personality rows are proposals pending the owner's confirmation.</li>
</ul>
</main>'''
open(OUT, 'w').write(page); print(OUT, len(page), 'bytes')
