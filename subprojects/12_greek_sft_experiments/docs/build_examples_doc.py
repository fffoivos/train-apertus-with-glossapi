#!/usr/bin/env python3
"""Build the companion document: how each Greek dataset was made, with real example rows from every block of the R4_full manifest.
Usage: python3 docs/build_examples_doc.py [out.html]"""
import collections, html, json, pathlib, random, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'docs' / 'SFT_DATASET_EXAMPLES_20260918.html')
E = lambda s: html.escape(str(s or ''))
def clip(s, n):
    s = re.sub(r'\n{3,}', '\n\n', (s or '').strip())
    return s if len(s) <= n else s[:n].rsplit(' ', 1)[0] + ' …'
# ---------------------------------------------------------------- sample rows
rng = random.Random(20260918)
pool = collections.defaultdict(list); counts = collections.Counter()
for line in open(ROOT / 'data' / 'arms' / 'R4_full' / 'train.jsonl', encoding='utf-8'):
    r = json.loads(line); c = r['config']; counts[c] += 1
    if len(pool[c]) < 8: pool[c].append(r)
    elif rng.random() < 0.003: pool[c][rng.randrange(8)] = r
NONLATIN = re.compile(r'[\u4e00-\u9fff\u0400-\u04ff\u0600-\u06ff\u3040-\u30ff]')
def pick(cfg, n=2, prefer_multi=False, want=None):
    rows = pool.get(cfg, [])
    if want: rows = [r for r in rows if want in r['id']] or rows
    if cfg.startswith('nemotron'):
        rows = [r for r in rows if not NONLATIN.search(r['messages'][0]['content'])] or rows
    if prefer_multi: rows = sorted(rows, key=lambda r: -len(r['messages']))
    else: rows = sorted(rows, key=lambda r: abs(sum(len(m['content']) for m in r['messages']) - 1400))
    return rows[:n]
def render(r, cap=900):
    out = [f"<div class='row'><div class='rid'>{E(r['id'])} · {len(r['messages'])} messages</div>"]
    for m in r['messages'][:6]:
        role = m['role']
        out.append(f"<div class='turn {role}'><span class='who'>{role}</span><div class='txt'>{E(clip(m['content'], cap))}</div></div>")
    if len(r['messages']) > 6: out.append(f"<div class='more'>… {len(r['messages']) - 6} further messages</div>")
    return ''.join(out) + "</div>"
# ---------------------------------------------------------------- the blocks, in the order the document tells the story
OURS = [
 ('greek_ours', 'Translated and adapted to a Greek frame', '19,792 unique rows, seen twice',
  """<p>Eleven open English sources become Greek rows in a pipeline of three stages.</p>
  <p><b>Selection and compilation.</b> Each source has a config that declares what it is for and which rows qualify: the instruction-following personas set for constraint work, no_robots for everyday assistance, OASST for open conversation, coconot for what should be declined, EuroBlocks French and German rows for non-English provenance, smoltalk's everyday and constraint subsets, Apertus's own English mixture, and systemchats for rows carrying a system turn.</p>
  <p><b>Generation.</b> A single model pass rewrites the row into Greek and moves its frame, under one governing test: would swapping this entity change whether the answer is true? If yes it is content and is frozen; if no it is frame and becomes Greek. A question about American tax brackets becomes a question about Greek ones; a question about the boiling point of water stays as it is. The prompt forbids adding facts, forbids mannerisms, and requires that institutions and procedures named in the answer actually exist here.</p>
  <p><b>Correction.</b> Independent editing passes then read each row against a written contract and propose the lightest change that fixes it; the lightest acceptable edit of several passes is kept. A row edited beyond a fifth of its length, or whose user turn is edited beyond 40%, is held for a person to look at rather than accepted silently. A separate screen samples rows for quality and can reject a whole build.</p>"""),
 ('greek_if', 'Greek constraint following', '29,773 rows, seen once',
  """<p>Built to teach the model to obey checkable instructions in Greek, including constraints that only exist in Greek.</p>
  <p><b>The grid.</b> 880 subtopics crossed with 12 question forms and 40 constraint families. Twenty-six families come from the standard English instruction-following battery (word counts, forbidden words, JSON output, sections, casing); fourteen are Greek-specific: the polite plural, the familiar singular, writing without accents, Greeklish only, capitals in Greek script, numbered lists with Greek numerals, the ano teleia, the Greek question mark.</p>
  <p><b>Authoring rather than templating.</b> A pilot compared templated requests against requests written as a person would ask them. Authored requests won, so every user turn is written, with the constraint stated the way a real user states it, usually as a final sentence.</p>
  <p><b>Composition levels.</b> One constraint in a quarter of rows, two in 30%, three in a quarter, four in 12%, five in 8%, so the model meets both single constraints and awkward combinations.</p>
  <p><b>Verification.</b> Every generated answer is run through the machine checker for its own constraints; failures are retried once and dropped if they fail again. Three builds produced 11,015, 9,894 and 9,411 rows from 12,000, 11,000 and 10,400 attempts. An editing pass then improves the Greek, re-runs the checkers, and reverts any edit that breaks a constraint: 12,361 rows edited, 163 reverted in the first two builds.</p>
  <p class='limit'>What this cannot do: the checkers verify the constraint, not whether the content is any good.</p>"""),
 ('greek_math_v2', 'Greek worked mathematics', '15,277 unique rows, seen twice',
  """<p>Two origins. Grade-school and competition problems from the standard English sets are translated into Greek; and problems are written natively for curriculum cells the translated sets leave thin, using a Greek setting with Greek names, prices in euro and realistic quantities.</p>
  <p><b>Solutions.</b> Each solution is worked at 100 to 250 words with the answer boxed, generated at higher effort for the two hardest levels. The style was chosen after the previous round's terse targets taught the model to answer in a median of 35 words without a boxed answer, which tripled looping.</p>
  <p><b>Checks.</b> Translation fidelity is judged, with a second higher-effort adjudication on disagreements. The derivation is checked against the published solution for translated problems. The Greek is polished with guards that forbid changing any number. A blind independent solve provides a second opinion on the final answer; disagreements are recorded rather than dropped, on the owner's instruction, because a disagreement between two solvers is not proof that the published answer is wrong.</p>
  <p class='limit'>Recorded limitation: 1,463 English and 794 Greek rows are kept whose blind solve disagreed with the reference answer.</p>"""),
 ('personality', 'Identity, limits and positions', '1,504 unique rows, seen four times',
  """<p>Written from three source documents: a sheet of 110 facts about Greece, a 14-statement identity sheet saying what the model is and who made it, and a guide to positions on contested topics.</p>
  <p><b>Seven categories.</b> Greece-centric facts; who am I; identity under pressure, where a user insists it is a different model; limits, where it must say what it cannot do; refusals in our own voice; sensitive Greek topics, where it gives the facts with dates and our position as ours with its evidence; and register, covering how formal to be with whom.</p>
  <p><b>Why four copies.</b> Round two ran the same mixture at three doses. At one copy the model still answered «Ναι, είμαι το ChatGPT». At two it learned the core but invented its own licence. At four it answered every probed fact as written, and held-out identity loss stopped improving. Four is where it saturates, not a guess.</p>
  <p>Corrections found later were applied as overlays to the existing rows rather than by regenerating: 29 corrections, 116 occurrences replaced.</p>"""),
 ('convskills_v2', 'Conversation skills', '1,682 unique rows, seen twice',
  """<p>Dialogues whose subject is the conversation itself, built as a live loop: a real checkpoint answers, and the next user turn reacts to what it actually said, so the exchange is not a script.</p>
  <p><b>Four lanes.</b> Treating the conversation as an object (quote my third message, count what I have asked); keeping a standing instruction across turns and releasing it when revoked; editing the previous answer; and chained edits where each instruction accumulates on the last.</p>
  <p><b>Two lanes were dropped.</b> An inference-memory lane failed its own audit: of 100 sampled rows, 74 were flawed, most inventing details the conversation never supplied. A habit-correction lane was dropped because it depends on masking parts of the context, which this run does not yet trust.</p>
  <p class='limit'>Recorded limitation: many rows reuse an assistant turn across several rows, so a defective answer propagates to 20 or 40 rows at once.</p>"""),
 ('personality_v3', 'The correction overlay', '5 rows, seen once',
  """<p>A late review of the identity set found seven factual targets to correct and some register rows that were too stiff. The owner's rule is that a completed set is not regenerated, so the corrections were applied as overlays over the existing rows — 29 corrections, 116 occurrences replaced — and six genuinely new rows were written for cells the review said were missing, mostly everyday register: writing to a landlord, a message of condolence, a question about stopping a course of antibiotics, a name day, a pupil asking in Greeklish. One of the six hit the decontamination cache and was dropped; five are in the manifest.</p>
  <p>It is a five-row block and it is listed here for completeness, not for weight.</p>"""),
 ('greek_rewrite', 'Rewriting and summarising', '1,980 rows, seen once',
  """<p>Each row is a realistic Greek passage plus an instruction over it: summarise, shorten, change the register, pull out the dates, turn it into bullets.</p>
  <p><b>How the passages are made.</b> Twenty genres crossed with forty topics and five lengths, each in a stated register, generated at high effort with a prompt that requires vouched material: institutions, services and procedures must exist or be plausible in Greece, and only personal names may be invented.</p>
  <p><b>Editing.</b> Of 2,006 rows judged, 1,062 passed untouched, 905 were edited and 33 rewritten. A separate screen kept 1,999 of 2,000, and the owner read 40 blind.</p>
  <p class='limit'>Recorded limitation: the passages are plausible fiction anchored on real places, with invented dates and figures.</p>"""),
]
IMPORTED = [
 ('nemotron_chat_a', 'General instruction chat', 'best-of-n samples from a large model, CC BY 4.0 / ODC-BY; 4.3% of rows are not in a Latin script'),
 ('nemotron_chat_b', 'General instruction chat, second shard', 'same source and licence; 4.6% not in a Latin script'),
 ('dolci_tooluse', 'Tool use', 'rendered as explicit function-call blocks, not the Apertus native tool format'),
 ('dolci_reasoning', 'Reasoning', 'Ai2 Dolci, ODC-BY'),
 ('dolci_science', 'Science', 'Ai2 Dolci, ODC-BY'),
 ('dolci_safety', 'Safety', 'Ai2 Dolci, ODC-BY'),
 ('dolci_code_algo_20k', 'Code and algorithms', 'Ai2 Dolci, ODC-BY'),
 ('dolci_precise_if_20k', 'Precise instruction following', 'Ai2 Dolci, ODC-BY'),
 ('dolci_chat', 'General chat', 'Ai2 Dolci, ODC-BY'),
 ('ifeval_like', 'Instruction-following synthetic', 'generated by a large open model, Qwen licence'),
 ('smoltalk2_multilingual', 'Multilingual chat', 'German, French, Spanish, Portuguese, Italian'),
 ('math_en_gsm', 'English grade-school mathematics', 'solutions from an open synthetic set, deduplicated to at most three per problem'),
 ('math_en_math', 'English competition mathematics', 'the published human solutions, MIT licence'),
 ('puzzles', 'Logic puzzles', 'every answer verified by brute force; 1,318 wrong ones removed'),
 ('format_mc', 'Multiple-choice formatting', 'existing question sets rendered as dialogue, no generation'),
]
def block(cfg, title, size, prose, n=2, multi=False, want=None):
    ex = ''.join(render(r) for r in pick(cfg, n, multi, want))
    return (f"<section><h3>{E(title)}</h3><p class='size'>{E(cfg)} · {E(size)} · {counts.get(cfg,0):,} rows in the manifest</p>"
            f"{prose}<h4>Example rows</h4>{ex}</section>")
ours_html = ''.join(block(c, t, s, p, 2, c in ('convskills_v2', 'personality')) for c, t, s, p in OURS)
imported_html = ''.join(
    f"<section class='imp'><h3>{E(t)}</h3><p class='size'>{E(c)} · {counts.get(c,0):,} rows · {E(note)}</p>{''.join(render(r, 520) for r in pick(c, 1))}</section>"
    for c, t, note in IMPORTED)
page = f"""<title>Greek Apertus SFT: Datasets and Examples</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
:root {{ --bg:#FBFAF8; --surface:#FFFFFF; --ink:#1B222E; --muted:#5B6674; --line:#DDD9D2; --accent:#1A6C8C; --user:#EEF3F6; --warn:#9A5A10; --warn-soft:#FAF1E2; --code-bg:#F2F0EC; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#12161B; --surface:#191E25; --ink:#E6E9EE; --muted:#9AA5B2; --line:#2B333D; --accent:#6FB6D2; --user:#1D242C; --warn:#DFA95F; --warn-soft:#332616; --code-bg:#0F1419; }} }}
:root[data-theme="dark"] {{ --bg:#12161B; --surface:#191E25; --ink:#E6E9EE; --muted:#9AA5B2; --line:#2B333D; --accent:#6FB6D2; --user:#1D242C; --warn:#DFA95F; --warn-soft:#332616; --code-bg:#0F1419; }}
* {{ box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--ink); font-family:"Source Serif 4",Georgia,serif; font-size:16.5px; line-height:1.6; margin:0; padding-inline:clamp(16px,4vw,40px); padding-block:32px 80px; }}
main {{ max-width:920px; margin:0 auto; }}
h1 {{ font-size:clamp(27px,4vw,38px); font-weight:600; margin:6px 0 10px; text-wrap:balance; }}
h2 {{ font-size:24px; margin:44px 0 10px; padding-bottom:6px; border-bottom:2px solid var(--ink); }}
h3 {{ font-size:19px; margin:30px 0 2px; }}
h4 {{ font-family:"IBM Plex Sans",sans-serif; font-size:12px; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); margin:16px 0 6px; }}
p {{ margin:0 0 11px; }} .lede {{ font-size:18px; color:var(--muted); }}
.eyebrow {{ font-family:"IBM Plex Sans",sans-serif; font-size:12px; letter-spacing:.09em; text-transform:uppercase; color:var(--muted); font-weight:600; }}
.size {{ font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--accent); margin-bottom:10px; }}
.limit {{ background:var(--warn-soft); border-left:3px solid var(--warn); padding:9px 13px; font-family:"IBM Plex Sans",sans-serif; font-size:14px; }}
.row {{ border:1px solid var(--line); background:var(--surface); margin:0 0 12px; }}
.rid {{ font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--muted); padding:6px 12px; border-bottom:1px solid var(--line); }}
.turn {{ padding:9px 12px; border-bottom:1px solid var(--line); }} .turn:last-child {{ border-bottom:none; }}
.turn.user {{ background:var(--user); }} .turn.system {{ background:var(--code-bg); }}
.who {{ font-family:"IBM Plex Sans",sans-serif; font-size:10.5px; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); font-weight:600; display:block; margin-bottom:3px; }}
.txt {{ white-space:pre-wrap; overflow-wrap:anywhere; font-size:15px; }}
.more {{ font-family:"IBM Plex Sans",sans-serif; font-size:12.5px; color:var(--muted); padding:7px 12px; }}
section.imp h3 {{ font-size:17px; }} section.imp .txt {{ font-size:14.5px; }}
code {{ font-family:"IBM Plex Mono",monospace; font-size:.85em; background:var(--code-bg); padding:1px 5px; }}
hr {{ border:none; border-top:1px solid var(--line); margin:34px 0; }}
</style>
<main>
<div class="eyebrow">GlossAPI · ΕΕΛΛΑΚ · companion to the SFT recipe · 18 September 2026</div>
<h1>What is in the training mixture, and how the Greek parts were made</h1>
<p class="lede">Every block of the 384,010-row mixture with real rows taken from the training file itself, not written for the document. The Greek sets we built are described with the process that produced them, including what each process cannot guarantee. Long turns are trimmed at a sentence boundary and marked.</p>

<h2>Part one: the Greek material we made</h2>
<p>Six sets, 25% of the supervised tokens. Each was generated by a model under a written contract, then corrected by independent passes, then screened; the differences are in what can be checked automatically. Constraint following can be machine-verified. Mathematics can be checked against a reference answer. Register, voice and identity can only be read.</p>
{ours_html}

<h2>Part two: the imported material</h2>
<p>Fifteen blocks, kept in their original language, selected for skills rather than for Greek. They supply 75% of the supervised tokens. Round one tested whether to adapt these to a Greek frame as well; adaptation helped on the small Greek-only arm, and at full scale we import the skill and let the Greek sets carry the frame.</p>
{imported_html}

<hr>
<p class="lede" style="font-size:15px">Rows are sampled deterministically at seed 20260918 from <code>data/arms/R4_full/train.jsonl</code>. Counts are the rows as they appear in the manifest, including block repeats. One source, no_robots, is CC BY-NC 4.0: derivatives of those rows are non-commercial and must be credited.</p>
</main>"""
OUT.write_text(page)
print('wrote', OUT, len(page), 'chars,', len(OURS) + len(IMPORTED), 'blocks documented')
