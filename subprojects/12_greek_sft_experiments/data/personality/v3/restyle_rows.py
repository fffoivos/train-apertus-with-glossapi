#!/usr/bin/env python3
"""Restyle pass: ONE prompt that reads each existing row against the style guide, classifies the question (type, purpose,
expected level), judges the current answer (level, missing required contents, placeholders, naming Greece, mannerisms),
and decides keep | rewrite. On rewrite it writes the new assistant turn(s) in Greek from the row's facts.
Usage: python3 restyle_rows.py <rows.jsonl> <out.jsonl> [model=claude-opus-5] [batch=6]
Resumable (skips ids already in out). Facts: category A rows get their facts_used entries from sheet v2; B/C/D get the identity
facts + name decision + settled values; F gets sensitive_guidance.md. Settled placeholder values are PROPOSALS until the owner confirms."""
import json, sys, os, re, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(HERE, '..', 'v2')); from claude_call import call, TOT
IN, OUT = sys.argv[1], sys.argv[2]; MODEL = sys.argv[3] if len(sys.argv) > 3 else 'claude-opus-5'; BATCH = int(sys.argv[4]) if len(sys.argv) > 4 else 6; LOG = OUT + '.log'
GUIDE = open(os.path.join(ROOT, 'docs', 'STYLE_GUIDE_ANSWERS_20260906.md')).read()
GUIDE = GUIDE[GUIDE.index('## 0.'):GUIDE.index('## 6.')]  # rules only; examples excluded to save tokens
SHEET = {f['id']: f for f in json.load(open(os.path.join(HERE, '..', 'v2', 'facts_greece_v2.json')))}
IDENT = json.load(open(os.path.join(HERE, '..', 'identity_facts.json')))
SENS = open(os.path.join(HERE, '..', 'sensitive_guidance.md')).read() if os.path.exists(os.path.join(HERE, '..', 'sensitive_guidance.md')) else ''
SETTLED = {'[ΟΝΟΜΑ]': 'no name of its own: «Δεν έχω δικό μου όνομα· είμαι το Ελληνικό Apertus, ένα ανοιχτό έργο της ΕΕΛΛΑΚ στο πλαίσιο του GlossAPI» (open project in progress, not a finished entity; data, code and weights public). Rephrase, do not just substitute.',
           '[ΗΜΕΡΟΜΗΝΙΑ ΓΝΩΣΗΣ]': '«περίπου ως τα μέσα του 2025» (PROPOSED value)', '[ΑΔΕΙΑ]': '«Apache 2.0» (PROPOSED value)'}
def fact_text(f):
    s = f"[{f['id']}] {f['title_el']}: {f['fact_el']}"
    if f.get('explain_el'): s += f"\n   why/how: {f['explain_el']}"
    if f.get('related_el'): s += f"\n   related: {f['related_el']}"
    if f.get('events'): s += "\n   events: " + '; '.join(f"{e['date']} {e['what_el']}" for e in f['events'])
    if not f.get('stable', True): s += f"\n   (holds as of {f.get('as_of','—')}: say «με βάση τα στοιχεία του …», never «ίσχυε ως»)"
    return s
IDENT_TXT = '\n'.join('- ' + x for x in IDENT['facts_el']) + '\nNever claim: ' + '; '.join(IDENT['never_claim']) + '\nName decision: ' + IDENT['name_decision']['decision'] + ' Why: ' + IDENT['name_decision']['why'] + '\nPhrasings: ' + ' | '.join(IDENT['name_decision']['how_to_phrase_el'])
HEAD = """You are the editor-writer of the Greek Apertus personality SFT set. Apply the STYLE GUIDE below to every row.
For each row, in order:
1. Read the user's turn(s). Decide the question TYPE (1–10 of §2), the PURPOSE signal (§1.2) and the EXPECTED level (Ε1/Ε2/Ε3). Read the question, never a label.
2. Judge the CURRENT assistant turn(s): actual level (under/ok/over), the required contents of the type that are missing (list them briefly, in English), unresolved placeholders ([ΟΝΟΜΑ], [ΗΜΕΡΟΜΗΝΙΑ ΓΝΩΣΗΣ], [ΑΔΕΙΑ]), naming Greece to a Greek user («στην Ελλάδα» without contrast), mannerisms, facts not supported by the FACTS given.
3. Decide: "keep" only if nothing is missing, the level is ok, and there is no placeholder. Otherwise "rewrite".
4. If rewrite: write the new assistant turn(s) in natural, direct Greek (not translated), following the guide: the answer in the first sentence, anchors, the one related item, the caveat for things that change, the requested shape. Keep every user turn verbatim; rewrite every assistant turn that needs it and copy the others. Keep what was good in the old answer. Use ONLY the FACTS given for the row plus common, certain knowledge; list anything beyond the FACTS in beyond_sheet (one short phrase each). For rows where the assistant introduces itself, use the name decision (an absence of a name, an open project). Replace placeholders with the settled values.
Voice: compact natural Greek, «που» over «ο οποίος», no chatbot mannerisms («Φυσικά!», «Ορίστε», «Ελπίζω να βοήθησα»), no exclamation marks without reason, no bold lists where sentences suffice, never «ως τεχνητή νοημοσύνη», no self-reference unless asked. «Εμείς», «εδώ», «η χώρα μας» = Greece. Person follows the user. Warm, not sugary.
HARD RULE (owner): whenever the size, area, extent, borders or neighbours of Greece come up, the answer gives land AND sea together: land 131,957 km², territorial waters 6 nm Aegean / 12 nm Ionian, EEZ about 505,572 km² (almost four times the land), sea neighbours Italy, Albania, Libya, Egypt, Cyprus, Turkey, median line. Never the land figure alone, never «Italy for example» for the sea neighbours.
Settled placeholder values: """ + '; '.join(f'{k} → {v}' for k, v in SETTLED.items()) + """
Return ONLY JSON: {"rows": [{"id": ..., "type": 1-10, "purpose": "...", "expected_level": "Ε1|Ε2|Ε3", "actual_level": "under|ok|over", "missing": ["..."], "placeholders": true|false, "decision": "keep|rewrite", "reason": "one sentence, English", "messages": [ {"role":"user","content":...}, {"role":"assistant","content":...}, ... ] (ALL turns, only when decision is rewrite), "beyond_sheet": ["..."]}, ...]}

STYLE GUIDE:
""" + GUIDE
GEO_TRIGGER = re.compile(r'(έκταση|εκταση|τετραγωνικ|σύνορ|συνορ|γείτον|γειτον|ΑΟΖ|χωρικ[άα] ύδατα|μίλια|μιλια|υφαλοκρηπίδ|θαλάσσι|θαλασσι|πόσο μεγάλη|ποσο μεγαλη|μέγεθος|μεγεθος|ektasi|synora|geiton)', re.I)
GEO_LINKED = ['geo04', 'geo02', 'sea01', 'sea02']
def linked_facts(r):
    ids = list(r.get('facts_used') or [])
    for i in list(ids):  # follow «βλ. xxx» references inside the sheet
        for ref in re.findall(r'βλ\. ?([a-z]+\d+)', SHEET.get(i, {}).get('fact_el', '')): ids.append(ref)
    utext = ' '.join(m['content'] for m in r['messages'] if m['role'] == 'user')
    if any(i.startswith('geo') or i.startswith('sea') for i in ids) or GEO_TRIGGER.search(utext): ids += GEO_LINKED
    return list(dict.fromkeys(i for i in ids if i in SHEET))
def row_text(r):
    s = f"### ROW {r['id']} (category {r['category']}, user type: {r.get('user_type') or '—'})\n"
    for m in r['messages']: s += f"[{m['role']}] {m['content']}\n"
    facts = [fact_text(SHEET[i]) for i in linked_facts(r)]
    if facts: s += "FACTS for this row:\n" + '\n'.join(facts) + '\n'
    if r['category'] in 'BCD': s += "IDENTITY FACTS:\n" + IDENT_TXT + '\n'
    if r['category'] == 'F' and SENS: s += "SENSITIVE-TOPICS GUIDANCE:\n" + SENS[:6000] + '\n'
    return s
rows = [json.loads(l) for l in open(IN)]; done = set()
if os.path.exists(OUT):
    for l in open(OUT): done.add(json.loads(l)['id'])
todo = [r for r in rows if r['id'] not in done]; batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
print(f'{len(todo)} rows in {len(batches)} calls, {MODEL}', flush=True)
def run(b):
    obj = call(HEAD + '\n\nROWS:\n' + '\n'.join(row_text(r) for r in b), MODEL, LOG, 'R', max_turns=3, timeout=1800)
    got = {str(x.get('id')): x for x in (obj or {}).get('rows', []) if isinstance(x, dict)}
    out = []
    for r in b:
        x = got.get(r['id'])
        if not x: continue
        dec = x.get('decision'); msgs = x.get('messages') if dec == 'rewrite' else None
        if dec == 'rewrite' and not (isinstance(msgs, list) and len(msgs) >= 2 and msgs[-1].get('role') == 'assistant'): continue
        if msgs:  # user turns verbatim
            ut = [m['content'] for m in r['messages'] if m['role'] == 'user']; k = 0
            for m in msgs:
                if m['role'] == 'user' and k < len(ut): m['content'] = ut[k]; k += 1
        out.append(dict(id=r['id'], category=r['category'], task=r.get('task'), user_type=r.get('user_type'), facts_used=r.get('facts_used') or [],
                        old_messages=r['messages'], messages=msgs or r['messages'], type=x.get('type'), purpose=x.get('purpose'), expected_level=x.get('expected_level'),
                        actual_level=x.get('actual_level'), missing=x.get('missing') or [], placeholders=bool(x.get('placeholders')), decision=dec, reason=x.get('reason'),
                        beyond_sheet=x.get('beyond_sheet') or [], restyle_model=MODEL))
    return out
with open(OUT, 'a') as fh, cf.ThreadPoolExecutor(3) as ex:
    for out in ex.map(run, batches):
        for r in out: fh.write(json.dumps(r, ensure_ascii=False) + '\n')
        fh.flush(); print(f'+{len(out)} rows ({sum(1 for r in out if r["decision"]=="rewrite")} rewrite) | ${TOT["cost"]:.2f}', flush=True)
print('ALL DONE', flush=True)
