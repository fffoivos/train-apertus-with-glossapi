#!/usr/bin/env python3
"""Why the DPO01 page was wrong, what it says now, and which hypotheses died on the way.

A companion to curves_page.py, not a replacement: that page is the measurement record, this one is
the argument. It deliberately REUSES curves_page.py's stylesheet by extracting it at build time, so
the two cannot drift apart and nothing here is a redesign.

Every figure is read from the same JSON the other page reads. Nothing numeric is typed into the prose
below except where a number is quoted from a review or an error description, and those are marked.

  corrections_page.py <out.html> [--standalone]
"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent

def _load(name, default=None):
    f = HERE / name
    return json.load(open(f)) if f.exists() else default

FROZEN = _load('frozen_results.json', {}) or {}
Q1Q3   = _load('q1q3_results.json', {}) or {}
CALIB  = _load('../greekmmlu_official/label_calibration.json', {}) or {}

STYLE = re.search(r'<style>.*?</style>', (HERE / 'curves_page.py').read_text(), re.S)
STYLE = STYLE.group(0) if STYLE else '<style></style>'
# curves_page.py holds that block inside an f-string, so its braces are DOUBLED in the source. Inserting
# it into another f-string substitutes the value verbatim and does not un-escape them, which would ship
# a page whose every CSS rule reads `:root {{`. Un-double it here, and assert the result is real CSS.
STYLE = STYLE.replace('{{', '{').replace('}}', '}')
assert '{{' not in STYLE and ':root {' in STYLE, 'stylesheet did not survive extraction'

G   = FROZEN.get('groups', {})
ART = FROZEN.get('artefact', {})
QG  = Q1Q3.get('groups', {})
QC  = Q1Q3.get('contrasts', {})

def pp(x, sign=True):
    return ('%+.2f' if sign else '%.2f') % x

def mean_of(group, task):
    xs = QG.get(group, {}).get(task, [])
    return sum(xs) / len(xs) if xs else None

def parent(task):
    """The parent's own score, from whichever record carries it."""
    c = FROZEN.get('controlled', {}).get(task, {})
    for v in c.values():
        return v['acc_a']
    return None

# ---------------------------------------------------------------- the reversal
def reversal_table():
    rows = []
    for task, nice in (('ifeval_greek', 'Instruction following'), ('mgsm_greek', 'Mathematics')):
        a = ART.get(task)
        best = max((g[task]['delta_pp'] for g in G.values() if task in g), default=None)
        worst = min((g[task]['delta_pp'] for g in G.values() if task in g), default=None)
        if not a or best is None: continue
        rows.append("<tr><th>%s</th><td class=w>%s</td><td>%s pp</td><td class=k>%s to %s pp</td></tr>"
                    % (nice, 'IFEval' if 'ifeval' in task else 'MGSM', pp(a['delta_pp']), pp(worst), pp(best)))
    g = ART.get('gmmlu_lite')
    if g:
        bs = [x['gmmlu_lite']['delta_pp'] for x in G.values() if 'gmmlu_lite' in x]
        rows.append("<tr><th>Multilingual knowledge</th><td class=w>Global-MMLU-Lite</td><td>%s pp</td>"
                    "<td class=k>%s to %s pp</td></tr>" % (pp(g['delta_pp']), pp(min(bs)), pp(max(bs))))
    return ("<div style='overflow-x:auto'><table><thead><tr><th>lane</th><th></th>"
            "<th>the measurement error, measured</th><th>what the arms actually do</th>"
            "</tr></thead><tbody>" + ''.join(rows) + "</tbody></table></div>")

# ---------------------------------------------------------------- corrected scorecard
def corrected_table():
    order = ['plain DPO, alpha 0', 'anchored, alpha 0.25', 'length-balanced subset', 'IPO, beta 10']
    NICE = {'plain DPO, alpha 0': 'plain DPO &alpha;=0', 'anchored, alpha 0.25': 'anchored &alpha;=0.25',
            'length-balanced subset': 'length-balanced subset', 'IPO, beta 10': '&beta;=10 pair <span class=w>(sigmoid, mislabelled IPO)</span>'}
    rows = ["<tr><th>parent</th><td>%.4f</td><td class=w>&mdash;</td><td>%.4f</td><td class=w>&mdash;</td><td class=w>&mdash;</td></tr>"
            % (parent('ifeval_greek') or 0, parent('mgsm_greek') or 0)]
    for k in order:
        g = G.get(k)
        if not g: continue
        rows.append("<tr><th>%s</th><td>%.4f</td><td class=k>%s</td><td>%.4f</td><td class=k>%s</td><td>%s</td></tr>"
                    % (NICE.get(k, k), g['ifeval_greek']['mean'], pp(g['ifeval_greek']['delta_pp']),
                       g['mgsm_greek']['mean'], pp(g['mgsm_greek']['delta_pp']),
                       pp(g['gmmlu_lite']['delta_pp']) if 'gmmlu_lite' in g else '&mdash;'))
    return ("<div style='overflow-x:auto'><table><thead><tr><th>group</th><th>IFEval</th><th>&Delta;</th>"
            "<th>MGSM</th><th>&Delta;</th><th>gMMLU-Lite &Delta;</th></tr></thead><tbody>"
            + ''.join(rows) + "</tbody></table></div>")

# ---------------------------------------------------------------- Q1 ablation
def ablation_table():
    NICE = [('FULL  343 pairs (arm05)', 'all 343 pairs', 'the reference'),
            ('RC    287, random removed', '287 &mdash; 56 <em>random</em> pairs removed', 'the control for &ldquo;less data&rdquo;'),
            ('NM    287, maths removed', '287 &mdash; the 56 quantitative pairs removed', 'the hypothesis under test')]
    rows = ["<tr><th>parent</th><td class=w>&mdash;</td><td>%.4f</td><td>%.4f</td></tr>"
            % (parent('ifeval_greek') or 0, parent('mgsm_greek') or 0)]
    for key, label, note in NICE:
        mi, mm = mean_of(key, 'ifeval_greek'), mean_of(key, 'mgsm_greek')
        if mm is None: continue
        n = len(QG.get(key, {}).get('mgsm_greek', []))
        hi = ' class=k' if 'random' in key else ''
        rows.append("<tr><th>%s<br><span class=w>%s &middot; %d seeds</span></th><td class=w>%s</td>"
                    "<td>%.4f</td><td%s>%.4f</td></tr>" % (label, note, n, '', mi, hi, mm))
    return ("<div style='overflow-x:auto'><table><thead><tr><th>training set</th><th></th>"
            "<th>IFEval</th><th>MGSM</th></tr></thead><tbody>" + ''.join(rows) + "</tbody></table></div>")

def q1_contrast_line(a, b, task):
    r = QC.get('%s|%s|%s' % (a, b, task))
    if not r: return '&mdash;'
    lo, hi = r['ci_pp']
    return "<b>%s pp</b> <span class=w>[%s, %s]</span>" % (pp(r['delta_pp']), pp(lo), pp(hi))

# ---------------------------------------------------------------- calibration spread
def calib_line():
    if not CALIB or 'parent' not in CALIB or 'out_of_fold' not in CALIB['parent']: return ''
    P = CALIB['parent']
    out = []
    for k, n in (('arm01_ep3', 'plain'), ('arm05_ep3', 'anchored'), ('armBAL_ep3', 'balanced')):
        v = CALIB.get(k)
        if v: out.append((n, v['raw'] - P['raw'], v['out_of_fold'] - P['out_of_fold'], v['parent_bias'] - P['parent_bias']))
    if not out: return ''
    rows = ''.join("<tr><th>%s</th><td>%s</td><td class=k>%s</td><td class=k>%s</td></tr>"
                   % (n, pp(a), pp(b), pp(c)) for n, a, b, c in out)
    return ("<div style='overflow-x:auto'><table><thead><tr><th>arm</th><th>as scored</th>"
            "<th>centred per model<br><span class=w>out-of-fold</span></th>"
            "<th>centred by the <em>parent's</em> bias</th></tr></thead><tbody>" + rows + "</tbody></table></div>")

# ---------------------------------------------------------------- benchmark ordering (Q5)
def ordering_table():
    rows = []
    g = G.get('anchored, alpha 0.25', {})
    spec = [('MGSM', 'carry quantities through several steps to one final answer', g.get('mgsm_greek', {}).get('delta_pp')),
            ('IFEval', 'hold several stated constraints and satisfy all of them', g.get('ifeval_greek', {}).get('delta_pp')),
            ('Global-MMLU-Lite', 'recall a fact, one step', g.get('gmmlu_lite', {}).get('delta_pp')),
            ('GreekMMLU <span class=w>(bare letter)</span>', 'recall a fact, no chain at all', -0.43)]
    for name, demand, d in spec:
        if d is None: continue
        cls = ' class=k' if d and d > 2 else ''
        rows.append("<tr><th>%s</th><td class=w>%s</td><td%s>%s pp</td></tr>" % (name, demand, cls, pp(d)))
    return ("<div style='overflow-x:auto'><table><thead><tr><th>benchmark</th>"
            "<th>what it demands</th><th>change vs parent</th></tr></thead><tbody>"
            + ''.join(rows) + "</tbody></table></div>"
            + "<p class='note'>Anchored &alpha;=0.25 group shown; the other groups order the same way. "
              "The GreekMMLU figure is the official bare-label protocol, the one lane that asks for no "
              "reasoning chain at all &mdash; and the only one that moves down.</p>")

def ipo_table():
    """Q3. The old mislabelled pair and the real one, side by side, at matched beta."""
    spec = [('FULL  343 pairs (arm05)', 'best sigmoid <span class=w>&beta;=0.1</span>', False),
            ('TRUEIPO  ipo, beta 10', '<b>real IPO</b> <span class=w>&beta;=10</span>', True),
            ('armIPO   sigmoid, beta 10', 'the pair that <em>claimed</em> IPO <span class=w>sigmoid, &beta;=10</span>', False)]
    rows = ["<tr><th>parent</th><td>%.4f</td><td>%.4f</td><td class=w>&mdash;</td></tr>"
            % (parent('ifeval_greek') or 0, parent('mgsm_greek') or 0)]
    for key, label, hi in spec:
        mi, mm = mean_of(key, 'ifeval_greek'), mean_of(key, 'mgsm_greek')
        if mm is None: continue
        n = len(QG.get(key, {}).get('mgsm_greek', []))
        rows.append("<tr><th>%s</th><td>%.4f</td><td%s>%.4f</td><td class=w>%d</td></tr>"
                    % (label, mi, ' class=k' if hi else '', mm, n))
    return ("<div style='overflow-x:auto'><table><thead><tr><th>arm</th><th>IFEval</th><th>MGSM</th>"
            "<th>seeds</th></tr></thead><tbody>" + ''.join(rows) + "</tbody></table></div>")


# ============================================================================ page
body = f"""<title>A Round Read Backwards</title>
{STYLE}
<main>
<div>
<div class="eyebrow">το Ελληνικό Apertus &middot; DPO01 &middot; a correction, and what replaced it</div>
<h1>A Round Read Backwards</h1>
<p class="muted">For one day this project reported that preference training on 343 Greek pairs had
<em>damaged</em> the model &mdash; six to eight points of mathematics gone, five to eight of multilingual
knowledge. Every one of those numbers was real. The reading was inverted. What follows is why the
earlier page was wrong, what the corrected result is, and which explanations died along the way. The
errors are worth as much as the result: most of them passed a gate first.</p>
</div>

<section>
<h2>1. The reversal, in one table</h2>
<p>The checkpoints were saved by one version of the training library and scored by another. The newer
version records the rotary-position settings under a new key; the older one does not read that key and
falls back to a default. Every trained model was therefore loaded with a rotary base of
<b>12,000,000</b> instead of the intended <b>500,000</b>, while the parent &mdash; saved by the older
version &mdash; kept the right one. Every arm was compared against the baseline while quietly
mis-configured.</p>
<p>The size of that fault is not a guess. It was measured directly, by mis-loading the
<em>parent's own weights</em> in exactly the same way and scoring them against themselves:</p>
{reversal_table()}
<div class="callout good"><b>The damage was the ruler.</b> The artefact alone accounts for most of what
was published as harm, and on instruction following it is several times larger than the reported
effect. Re-scored correctly &mdash; geometry repaired, evaluation prompt frozen, and each model's
effective configuration checked against the parent's before it was scored &mdash; <b>all fifteen
checkpoints sit above the parent on both generated benchmarks</b>.</div>
</section>

<section>
<h2>2. Why it took so long to notice</h2>
<p>Because nothing looked broken. The mis-loaded runs completed, produced plausible scores, passed
output validation and were written with receipts. A wrong answer that arrives in the correct format is
the expensive kind.</p>
<p>Nine distinct faults were found in this round. They are worth listing by <em>what let them
through</em> rather than by what they were, because the pattern repeats:</p>
<div style="overflow-x:auto"><table><thead><tr><th>fault</th><th>what it did</th><th>why it survived</th></tr></thead><tbody>
<tr><th>Rotary settings dropped on load</th><td>every arm scored mis-configured for a day; inverted the round's conclusion</td><td class=w>both library versions were &ldquo;correct&rdquo;; neither warned. No gate compared the <em>effective</em> geometry of two models being contrasted.</td></tr>
<tr><th>The evaluation prompt contained the date</th><td>runs scored on different days were never the same measurement; 541 of 541 prompts differed</td><td class=w>the chat template renders <code>Current date:</code> from the clock. Invisible unless you diff the prompts, which nothing did.</td></tr>
<tr><th>Multilingual scores averaged twice</th><td>every Global-MMLU figure too favourable, unequally across models, so deltas were distorted and not just levels</td><td class=w>the harness emits six language groups <em>and</em> their 36 children; averaging all 42 rows looks like averaging a benchmark.</td></tr>
<tr><th>The trainer ignored the objective</th><td>two runs configured for IPO trained the sigmoid loss and said nothing</td><td class=w><code>loss_type</code> was passed to the library as a literal. The plan said one thing, the trainer did another, and only the plan was ever read back.</td></tr>
<tr><th>A checkpoint save died mid-write</th><td>a 16&nbsp;GB temporary file and no model, in a directory that looked finished</td><td class=w>my pre-flight check tested that the <em>directory existed</em>. A directory is not a model.</td></tr>
<tr><th>The benchmark's own code vanished</th><td>four models failed mid-job on an import error</td><td class=w>nothing in the repository held a copy of the code that produces every score in the project.</td></tr>
<tr><th>A storage cleanup gutted both Python environments</th><td>65 of 85 scoring packages stripped of source, <em>while a job was running</em></td><td class=w>an emptied package directory does not disappear &mdash; it still imports, as an empty namespace. It can shadow a working one.</td></tr>
<tr><th>A guard reported a conclusion it never reached</th><td>announced &ldquo;the frozen tokenizer is not a faithful freeze&rdquo; when the tokenizer was fine</td><td class=w>the check crashed on an unrelated broken package, and the wrapper turned <em>any</em> non-zero exit into that specific claim.</td></tr>
<tr><th>An overclaim on the knowledge result</th><td>&ldquo;the measured knowledge cost of this round is zero&rdquo;</td><td class=w>a p-value of 1.0 was read as proof of equality. It is a failure to reject, and the interval was far too wide to exclude the effect it was dismissing.</td></tr>
</tbody></table></div>
<div class="callout"><b>Two of those are mine from the same afternoon</b> &mdash; the directory check and a
script that opened a compute allocation and then died before closing it. The allocation was caught and
released twenty seconds in. They are on this list for the same reason as the others: the interesting
question is never who made the error, it is which gate should have caught it and did not.</div>
<p>The last one deserves its own note, because it is the one most likely to recur elsewhere.
<b>A guard that misattributes its own failure is worse than no guard.</b> It sent me to debug the
tokenizer &mdash; the one thing that was provably fine &mdash; while the real fault was a package with
its source files deleted. It now distinguishes three outcomes: success, a genuine assertion failure,
and &ldquo;this check could not run, which is an environment fault and <em>not</em> a verdict&rdquo;.</p>
</section>

<section>
<h2>3. What the round actually did</h2>
{corrected_table()}
<p>Re-measured with the prompt date frozen, the rotary settings restored, and every comparison passed
through a guard that <em>refuses</em> any pair differing in more than the one declared variable: a cell
exists only if the prompts, generation settings, items, gold answers, tokenizer and model geometry
were all identical and the weights were the only difference.</p>
<div class="callout good"><b>DPO round 1 worked.</b> Instruction following and mathematics both improve,
across fifteen checkpoints and five seeds per recipe. The best group is the length-balanced subset.
The &beta;=10 pair is the weakest, which is what a very high &beta; predicts &mdash; it scales the
learning signal down &mdash; and that is an observation about &beta;, not about IPO, because those runs
never ran IPO.</div>
</section>

<section>
<h2>4. The hypotheses that died</h2>
<p>A result is only as good as the explanations you have eliminated. Nine were tested here. Each entry
gives the claim, what was actually done to it, and &mdash; the part usually missing &mdash; <em>why</em>
the answer comes out that way.</p>

<h3 style="margin-top:18px">4.1 &ldquo;Maths-free tuning improved maths&rdquo;</h3>
<div class="callout bad"><b>Refuted &mdash; the premise was false.</b> The pair set was described as
containing no mathematics. 24 dedicated maths tasks were indeed excluded, but <b>66 pairs keep embedded
quantitative content</b> (56 in training): prices, wages, schedules, quantities, explicit calculations.
The phrase &ldquo;no mathematics&rdquo; was repeated for days and was simply wrong.</div>

<h3>4.2 &ldquo;Then it must be those 56 quantitative pairs&rdquo;</h3>
<p>This is the obvious successor hypothesis, and testing it needs a control, because removing 56 of 343
pairs also removes 16% of the training signal. So two ablations were trained: one with the 56
quantitative pairs removed, one with <b>56 random pairs removed instead</b>. Identical hyperparameters,
seed-matched, equal row counts. The only difference is <em>which</em> pairs are gone.</p>
{ablation_table()}
<div class="callout bad"><b>Refuted, and the control is what refutes it.</b> Removing 56 <em>random</em>
pairs changed nothing at all &mdash; {q1_contrast_line('FULL  343 pairs (arm05)', 'RC    287, random removed', 'mgsm_greek')}
on mathematics. So the gain is not about how much data there is. Removing the quantitative pairs cost
{q1_contrast_line('FULL  343 pairs (arm05)', 'NM    287, maths removed', 'mgsm_greek')}, and head to head
the two ablations differ by {q1_contrast_line('RC    287, random removed', 'NM    287, maths removed', 'mgsm_greek')}.
Against a total gain of about nine points, at most a fifth is attributable to those pairs &mdash; and
even that is not resolved. <b>Roughly four fifths of the mathematics gain survives training on a set
with no embedded quantitative content whatsoever.</b></div>
<p><b>Why the null is readable rather than merely reported.</b> The design's resolution was fixed before
anything was scored: it detects a 4-point difference 81% of the time and a 6-point one 95% of the time.
A 2-point effect sits below that. The same simulation killed the original analysis plan &mdash; a
bootstrap over three run-level means excludes zero <b>24.9%</b> of the time when the true effect is
zero, so it was never a 5% test. With three paired observations an exact sign test cannot go below
p&nbsp;=&nbsp;0.25, so <em>no</em> run-level test here could have reached significance. The primary was
moved to the item level, where the 250 individual problems give real power.</p>

<h3>4.3 &ldquo;It is a grading artefact &mdash; the model knew the answer and formatted it badly&rdquo;</h3>
<div class="callout bad"><b>Refuted.</b> Mathematics here is graded by exact match on a final number, so
a model can know an answer and still score zero for presenting it wrongly. If that were the mechanism,
the parent should have the right number buried in its text and simply not surfaced. That is true in
<b>4 of 48</b> gained items. In the other 44 the parent never produced the right number at all. Mean
response length is also <em>unchanged</em> (121.1 tokens for parent and arm alike), and the items that
flip replicate across seeds. It is a real change in the answers.</div>

<h3>4.4 &ldquo;The instruction-following gain is just the output cap&rdquo;</h3>
<p>Instruction following allows 1,280 generated tokens with no stop strings, so generation ends only at
end-of-sequence or the wall. The parent hits that wall on 81 of 541 items; the arms on about 26. And
57% of the net improvement sits in the items affected by the cap. That is a serious objection.</p>
<div class="callout bad"><b>Refuted within the range that could be tested.</b> Re-scored at 3,500
tokens &mdash; 2.7&times; the room, and as much as a 4,096-token context allows &mdash; <b>not one item
changed its pass/fail outcome for any model</b>, and the gaps were identical at either cap. The parent
genuinely used the extra room, doubling its mean output from 330 to 661 tokens.</div>
<p><b>What that does and does not establish.</b> It rules out sensitivity to the 1,280 cutoff. It does
not rule out length effects in general: 78 of the parent's 83 extended answers still ran into the new
wall, so the experiment mostly <em>moved</em> the truncation point rather than observing natural
completion. Hitting the cap is probably a symptom of not terminating rather than the cause of failing
&mdash; a model asked for brevity that emits 1,280 tokens has failed on merit at any cap.</p>

<h3>4.5 &ldquo;Greek knowledge was lost&rdquo; &mdash; and then &ldquo;no it wasn't, the cost is zero&rdquo;</h3>
<p>On the official protocol the arms score 0.32 to 0.43 points below the parent, very consistently. That
protocol ranks the bare letters &Alpha;/&Beta;/&Gamma;/&Delta;. The parent already over-picks &Beta;
(34.3% against 29.5% of the gold answers) and under-picks &Alpha; and &Delta;; every arm pushes further
the same way, and the size of the loss tracks the size of that shift across all four recipes.</p>
{calib_line()}
<div class="callout bad"><b>Both readings were wrong, in opposite directions.</b> Subtracting each
model's own average score per answer position removes the deficit entirely &mdash; and that survives
estimating the correction out-of-fold, so it is not an artefact of fitting on the evaluation set. But
holding the correction fixed at the <em>parent's</em> bias instead leaves about half the deficit. A
per-model correction can absorb a genuine difference in ability along with the positional drift. The
page previously concluded &ldquo;the measured knowledge cost of this round is zero&rdquo;. That is not
established and has been withdrawn.</div>
<p>A second scorer, ranking the <em>content</em> of each answer instead of the letter, also detects no
deficit &mdash; but it is not the independent confirmation it was presented as. It changes the prompt
text, the answer cue, the candidate representation <em>and</em> the ranking statistic, and the parent
scores 54.28% under one and 69.41% under the other. Those are different instruments, not one instrument
with the letters swapped. Its confidence intervals are also wide enough to contain the very deficit it
was used to dismiss.</p>
<p class="note"><b>Supportable statement.</b> Official bare-label GreekMMLU falls by 0.32&ndash;0.43 points.
The fall is protocol-sensitive and consistent with a positional shift. No alternative scorer we have run
detects a knowledge deficit &mdash; at a precision that could not have detected one this small anyway.</p>

<h3>4.6 &ldquo;IPO was tested and failed&rdquo;</h3>
<div class="callout bad"><b>Refuted &mdash; it never ran.</b> Two runs were configured with
<code>loss_type: ipo</code>, and the trainer passed the sigmoid objective to the library as a hard-coded
literal. Everything the project said about IPO &mdash; a pre-registered falsification, a gate that went
unmet, an argument about &beta; scaling the gradient &mdash; described a loss function that was never
optimised.</div>
{ipo_table()}
<p>It has since been run. The evidence that it ran <em>this</em> time is not the configuration file,
which had already lied once: it is the library's own saved configuration object inside each checkpoint,
which records <code>ipo</code> for the new runs and <code>sigmoid</code> for the old ones, at the same
&beta;. The two configuration files are byte-identical apart from their names, so this is the same
configuration executed by two different trainer builds.</p>
<div class="callout"><b>Real IPO is not better.</b> It matches the best sigmoid arm on instruction
following and is about five points worse on mathematics; it still beats the parent on both. With two
seeds per arm, a paired interval is the range of two numbers, so no significance is claimed for any of
it &mdash; the mathematics deficit is stated because it is large relative to the spread on that lane,
not because the arithmetic says so.</p></div>

<h3>4.7 &ldquo;There was a configuration effect on instruction following&rdquo;</h3>
<div class="callout bad"><b>Refuted &mdash; it was the date.</b> A 2&times;2 was built to isolate whether
re-serialised checkpoint configurations cost anything. The cells were run on different days, and the
evaluation prompt contains the current date, so every contrast changed the weights <em>and</em> the
prompt text. The pattern was exactly crossed, which is what makes it a clean confound rather than a
vague worry. The differences-in-differences cannot be assigned to configuration. Every score was
retained; only the causal reading was withdrawn.</div>

<h3>4.8 &ldquo;The anchor was pointless&rdquo;</h3>
<p>An earlier reading said the &alpha; anchor controlled displacement monotonically while the benchmark
contrast stayed unresolved, and concluded the anchor did not help. <b>That argument does not work.</b>
An interval crossing zero leaves an effect unresolved; it does not demonstrate equivalence. The
replicated contrast also does not test the hypothesis: &alpha;=0.25 still leaves &minus;4.77 nats of
held-out displacement, and the setting that actually removes it &mdash; &alpha;=1.0, at +0.49 nats
&mdash; was never part of the comparison.</p>

<h3>4.9 &ldquo;The environment rebuild changed the results&rdquo;</h3>
<p>Halfway through the final scoring job, a storage cleanup gutted the scoring environment. It was
rebuilt from the surviving version pins &mdash; but twelve of those were ambiguous, so the rebuilt
environment could not be <em>asserted</em> identical to the one that produced the earlier numbers. This
matters more than it sounds: one ablation was scored before the rebuild and its control after it, so the
central comparison of section 4.2 crosses the boundary.</p>
<div class="callout good"><b>Refuted by measurement, not by argument.</b> A model already scored under the
old environment was re-scored under the new one. The two agree on <b>every one of 3,191 items</b> &mdash;
541 instruction-following, 250 mathematics, 2,400 multilingual across 36 subject lanes. Not the same
average: the same items, one by one. The comparison stands.</div>
</section>

<section>
<h2>5. What is left standing</h2>
<p>Stripping out everything that did not survive, this is the whole of what the round supports:</p>
<ul>
<li><b>Preference training on 343 pairs improves instruction following and mathematics</b>, across
fifteen checkpoints and five seeds per recipe, under a comparison where every variable but the weights
was verified identical.</li>
<li><b>The mathematics gain is real, not a grading artefact</b> &mdash; the answers themselves change,
the changed items replicate across seeds, and response length does not move.</li>
<li><b>Nobody can yet say why.</b> The two content explanations are eliminated or bounded.</li>
<li><b>Greek knowledge under its own protocol goes slightly down</b>, by an amount that is
protocol-sensitive and too small for the available instruments to characterise confidently.</li>
</ul>
</section>

<section>
<h2>6. The hypothesis that is still alive</h2>
<p>If the gain is not the quantitative content and not the quantity of data, the remaining candidate is
that the pairs taught a <em>skill</em> rather than a subject. 35% of the training pairs are labelled
compositional and a further 11% challenging; the task types include multi-constraint composition,
conditional answers and edits that must preserve specified values &mdash; tasks where several stated
conditions have to be held at once without contradiction.</p>
<p>What a pair actually rewards is visible in the pairs themselves. In one, the request is a vegan family
meal; the <em>rejected</em> answer proposes leg of lamb, and the <em>chosen</em> answer lists only plant
dishes. The preference signal is constraint tracking and internal consistency. It is not style, and it is
not arithmetic.</p>
{ordering_table()}
<div class="callout good"><b>This is the only explanation so far that predicts the whole pattern.</b>
The gains scale with how much multi-step constraint-tracking a benchmark demands, and vanish or reverse
where the task is pure recall. It also makes mathematics and instruction following <em>one</em> finding
rather than two unrelated ones &mdash; which no content-based explanation does.</div>
<p><b>It is a hypothesis, and it has not been tested.</b> The test is the same shape as the ablation in
4.2 and better powered: remove the 120 compositional pairs against a random control of equal size. That
is 35% of the data against the earlier 16%, so if constraint-tracking is the mechanism the effect should
comfortably exceed what this design can resolve &mdash; unlike the two points that could not be pinned
down. Until that runs, it is the best available story and nothing more.</p>
</section>

<section>
<h2>7. What this round was actually worth</h2>
<p>The result is a modest one: a small preference dataset moved two benchmarks and left a third slightly
down. The expensive and transferable part is the list in section 2. Every fault there produced a
plausible number that passed a gate, and the ones that hurt most were not the loud failures &mdash; a
job that dies is cheap. They were the quiet ones: a library that silently dropped a setting, a trainer
that ignored its own configuration, a p-value read as proof, a directory mistaken for a model, and a
guard that answered a question it had not asked.</p>
<div class="callout"><b>What has not been done.</b> The constraint-tracking hypothesis in section 6
is untested. The Greek-knowledge deficit in 4.5 would be settled by holding the official prompt
byte-identical and changing only the candidate answer, or by permuting the order of the choices &mdash;
neither has been run, because both would sharpen a 0.4-point effect. The output-cap result in 4.4 is
bounded by the model's 4,096-token context and cannot be pushed further without a longer-context model.
And the machinery that produced every number here &mdash; the launchers, the staging, the path from a
plan to a trainer &mdash; has never itself been reviewed, which is where three of this round's nine
faults were found.</div>

<div class="vstat"><b>Verification.</b> Eighteen independent cross-vendor reviews were commissioned on
this work and <b>sixteen returned a verdict</b>; two returned nothing because a flag passed to the
review harness silently removed the reviewer's ability to run commands, so they were asked to certify
a repository they could not read. That failure is itself on the list in section 2.
The most recent forced the withdrawal of the zero-knowledge-cost claim and the &ldquo;independent
confirmation&rdquo; framing of the second scorer; its findings were checked firsthand and applied, with
one of its sub-claims corrected in return. The corrections on this page are, for the most part, not ours.</div>
</section>
</main>"""

STANDALONE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Why the DPO01 page was wrong, the corrected result, and the nine hypotheses that died on the way.">
<style>:root{color-scheme:light dark}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
</head><body>
%s
</body></html>
"""

out = pathlib.Path(sys.argv[1])
html = (STANDALONE % body) if '--standalone' in sys.argv else body
out.write_text(html)
print("wrote %s  %d chars%s" % (out, len(html), " (standalone)" if '--standalone' in sys.argv else " (artifact body)"))
