#!/usr/bin/env python3
"""Generator 0.2 release: seed instance → reservation → rendering → code checks → independent review → at most two repairs.
Spec v1.0.2 (labels and terms); ingestion plan §3 (substantive seeds, keys, reservations, seed-to-message checks).
Usage: python3 data/rlhf/generator_v02/generate.py --run R3-validation --slots R3-0001,R3-0002,...   (or --first-n N / --all-remaining)
Outputs under data/rlhf/generator_v02/runs/<run>/; accepted and held prompts are registered in data/rlhf/registry/registry.sqlite."""
import argparse, collections, concurrent.futures, hashlib, json, pathlib, re, sqlite3, sys, threading, time, unicodedata
HERE = pathlib.Path(__file__).resolve().parent; RL = HERE.parent; sys.path.insert(0, str(RL.parent / 'math'))
GL = (RL / 'prompts' / 'seed_label_definitions_v1.md').read_text(); GL_SHA16 = hashlib.sha256(GL.encode()).hexdigest()[:16]
KINDS = json.load(open(HERE / 'task_kinds.json')); REG = RL / 'registry' / 'registry.sqlite'
LANG_NAME = {'el': 'Greek', 'en': 'English', 'fr': 'French', 'de': 'German', 'es': 'Spanish', 'it': 'Italian', 'pt': 'Portuguese'}
CEILING = {'bare': 12, 'terse': 30}
REASONS = ['missing_given', 'changed_value', 'dropped_constraint', 'task_changed', 'added_fact_changes_answerability', 'wrong_language', 'register_not_realised', 'attitude_not_realised', 'detail_not_realised', 'framing_or_meta_text', 'unnatural', 'answers_itself', 'packet_missing', 'unsafe_to_render_as_specified', 'other']
LEAK = re.compile(r'(\{\s*"|task_type|slot_id|\bR3-\d|givens|instance|check_values|\bseed\b|fictional|hypothetical|φανταστικ|υποθετικ)', re.I)
def norm(s): return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s or '')).strip()
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def definition(label):  # the glossary line for a label value, e.g. "- bare: ..."
    m = re.search(r'^- ' + re.escape(label) + r'(?: \([^)]*\))?:.*$', GL, re.M); return m.group(0) if m else f'- {label}: (no definition found)'
def purpose_def(p):
    sec = GL[GL.find('## Task — primary purpose'):GL.find('## Detail')]
    if p == 'math': return sec[sec.find('- math (maths):'):sec.find('- dialogue:')].strip()
    m = re.search(r'^- ' + p + r':.*$', sec, re.M); return m.group(0)
def safety_def(sub):
    sec = GL[GL.find('## Safety context'):]; m = re.search(r'^- ' + {'benign_sensitive': 'benign', 'protective': 'protective', 'fiction': 'fiction', 'harmful': 'harmful', 'ambiguous': 'ambiguous'}[sub] + r':.*$', sec, re.M); return m.group(0) if m else ''
def instance_key(slot, inst):
    core = dict(purpose=slot['purpose'], subtype=slot['subtype'], task=norm(inst['task_summary']).lower(), givens=sorted(norm(g).lower() for g in inst['givens']),
                constraints=sorted('|'.join(norm(c.get(k, '')).lower() for k in ('type', 'params', 'text')) for c in inst['constraints']), deliverable=norm(inst['deliverable']).lower(),
                packet_sha=sha(norm(inst.get('packet') or '')) if inst.get('packet') else None, check_values=sorted(norm(v).lower() for v in inst.get('check_values', [])),
                ambiguity=inst.get('ambiguity'), answer_conditions_sha=sha(norm(inst.get('answer_conditions') or '')))
    return sha(json.dumps(core, ensure_ascii=False, sort_keys=True))
def rendering_key(ikey, slot, message): return sha(ikey + '|' + slot['language'] + '|' + slot['register'] + '|' + slot['attitude'] + '|' + slot['detail'] + '|' + norm(message).lower())
def content_words(s): return {w for w in re.findall(r'\w{4,}', norm(s).lower())}
def instance_words(inst): return content_words(inst['task_summary'] + ' ' + ' '.join(inst['givens']))
TAG_STOP = set('with from that this their about into over under after before email message letter note text request reply question help advice plan planning check checking user users person asks wants needs'.split())
def scenario_stems(inst): return {w[:5] for w in re.findall(r'[a-z]{3,}', (inst.get('scenario') or '').lower()) if w not in TAG_STOP}
def similar(inst, known):
    w, st = instance_words(inst), scenario_stems(inst); out = []
    for other, ow, ost in known:
        if (w and ow and len(w & ow) / len(w | ow) > 0.45) or (st and ost and len(st & ost) / len(st | ost) >= 0.5): out.append(other)
    return out
def script_ok(slot, message, pasted):
    body = message.replace(pasted, ' ') if pasted else message
    letters = [c for c in body if c.isalpha()]; greek = sum('Ͱ' <= c <= 'Ͽ' or 'ἀ' <= c <= '῿' for c in letters)
    if not letters: return False
    ratio = greek / len(letters)
    if slot['language'] == 'el': return greek == 0 if slot['register'] == 'greeklish' else ratio >= 0.5
    return ratio <= 0.05
def word_count(message, pasted): return len(re.findall(r'\d+(?:[/.:,-]\d+)+|\w+', message.replace(pasted, ' ') if pasted else message))   # a date, time or decimal counts as one word
def code_checks(slot, inst, r, corpus):
    msg, pasted = r['message'], (r.get('pasted_span') or '') if slot['packet'] else ''
    issues = []
    if slot['packet'] and pasted and word_count(msg, pasted) == 0: issues.append('no_own_words')
    if pasted and pasted not in msg: issues.append('pasted_span_not_in_message')
    if not script_ok(slot, msg, pasted): issues.append('wrong_language')
    if slot['detail'] in CEILING and word_count(msg, pasted) > CEILING[slot['detail']]: issues.append('detail_ceiling_exceeded')
    if slot['packet'] and not (inst.get('packet') and norm(inst['packet'])[:60] in norm(msg)): issues.append('packet_missing')
    for v in inst.get('check_values', []):
        if norm(v).lower() not in norm(msg).lower(): issues.append(f'missing_value:{v}')
    if LEAK.search(msg.replace(pasted, '') if pasted else msg): issues.append('framing_or_meta_text')
    cw = content_words(msg)
    for other_id, ow in corpus:
        if other_id != slot['slot_id'] and cw and ow and len(cw & ow) / len(cw | ow) > 0.6: issues.append(f'near_duplicate:{other_id}'); break
    return issues
INSTANCE_PROMPT = """You create concrete task instances for a Greek-language assistant's RLHF prompt set. Each slot below fixes a primary purpose, a subtype, a language, a difficulty and ingredients (a person, a situation, a topic). For EACH slot, invent one concrete, self-consistent task instance that this person could really need in that situation, touching that topic where it fits naturally (drop the topic if it does not fit; never force it).
Rules:
- Satisfy the subtype's required preconditions exactly: {requires}
- Concrete values: real numbers, dates, names of things, units, constraints and texts, not placeholders.
- `packet`: ONLY for slots whose `needs_packet` is true, and then ONLY the material the person pastes (their draft, a notice, a record, a text, their attempted solution), written in full in the slot's language, 40–250 words. The packet never contains the request itself (no "please translate", no instructions to the assistant). For slots whose `needs_packet` is false, `packet` MUST be an empty string: the givens are stated by the person in their own message.
- `scenario`: 2–5 English words naming the real-life setting of the need (for example "dental appointment rescheduling", "lost dog sighting", "bike-share fare dispute").
- The scenario must be new: it must not repeat or closely resemble any of these scenarios already used in this collection, in any subtype or language: {avoid}. Also avoid these recent task summaries: {avoid_summaries}.
- The person, situation and topic are ingredients for realism, not a scenario template: most real requests do not involve juggling a work schedule; vary the kind of need widely.
- Size the instance to the slot's `detail` (how much the person will say; definitions below). The instance holds ONLY what this person will actually state. bare: the object of the ask and at most one value, no background, no names, no reasons (plus the pasted packet when needs_packet); for format or constraint tasks at most two very short constraints. terse: the ask plus at most one supporting fact or constraint beyond the task-defining values. short: the task-defining values plus one context detail, nothing pasted. medium: a paragraph's worth of situation. detailed and rambling: full context and several specifics. Values that define the task itself (the numbers of a calculation, the claim to prove, the format rules, the text to work on) always belong to the ask; subtype preconditions that describe the person's background (what they already tried, their priorities, the audience, the relationship) are included only when the detail level leaves room. When a bare or terse person leaves out something a good answer needs, keep it out, note in `answer_conditions` that the response should ask or state an assumption, and set `ambiguity` to underspecified if that leaves the answer open.
- `maths_content`: "maths" when the primary purpose is math; "embedded" when a non-maths task needs calculation, quantitative reasoning or number checking for a correct answer (budgets, date or time arithmetic, unit conversions, percentages, statistics); otherwise "none". Use the maths definition below.
- For maths follow the maths definition: choose a deliverable the person would plausibly ask for (result only, show the calculation, explain, prove); state assumptions; if you deliberately make the question ambiguous or underspecified, say so in `ambiguity`; never invent hidden assumptions to force a single answer.
- For factual instances use facts knowable by mid-2025; state the time scope. For false premises state the belief and the correct fact.
- For safety instances follow the safety sub-kind definition; harmful instances describe a request a real person might make, with no operational detail in the packet.
- `check_values`: short strings that MUST appear verbatim in the user's message (numbers, names, dates, exact constraint values), in the slot's language; empty when none. For a greeklish slot every check value the person types must be in Latin letters; Greek-script values may only appear inside a pasted packet.
- `answer_conditions`: private English notes on what a correct response must do (never shown to the model).
Definitions:
{definitions}
Return JSON {{"items":[{{"slot_id":..., "scenario": "2-5 English words", "task_summary": "English, one sentence", "givens": ["English facts and values"], "constraints": [{{"type": "...", "params": "...", "text": "English"}}], "packet": "text or empty string", "deliverable": "English", "ambiguity": "none|ambiguous|underspecified", "maths_content": "none|embedded|maths", "check_values": ["..."], "answer_conditions": "English"}}]}}
SLOTS:
{slots}"""
RENDER_PROMPT = """You write realistic user messages for a Greek-language assistant (RLHF prompt collection). For EACH slot: (1) privately imagine the person and why they ask right now (story, 2–4 sentences, English); (2) write EXACTLY what this person types.
The message must: carry the task instance faithfully (every given that the person would state, every constraint, the deliverable); include every string in check_values verbatim; paste the packet verbatim when there is one and report exactly that pasted substring in `pasted_span` (the person's own request stays outside it); when the slot has no packet, `pasted_span` is the empty string; be written in the slot's language, with the register, attitude and detail level as defined below; add no facts that change what a correct answer is; contain no framing, disclaimers, labels, placeholders or meta comments; not answer itself. Never state a knowledge cutoff, a time scope or a label as an instruction to the assistant (no "using information available by June 2025"): the person may mention a real date naturally, nothing more. A greeklish message is written entirely in Latin letters, including numbers' units and technical words; only material pasted as the object of the request keeps its own script. Detail ceilings count only the person's own words, not the pasted packet: bare at most 12 words, terse at most 30 words.
{repair}Definitions for the labels used below:
{definitions}
Return JSON {{"items":[{{"slot_id":..., "story": "...", "message": "...", "pasted_span": "..."}}]}}
SLOTS:
{slots}"""
REVIEW_PROMPT = """You independently review user messages written from task instances for an RLHF prompt set. You did not write them. For each item decide whether the message faithfully realises the instance and the labels, using the definitions. Fail it for any of these reason codes: {reasons}. Be strict about changed or missing values and constraints, task drift, added facts that change the correct answer, wrong language or register, and any framing or meta text; do not fail for style you merely dislike. For detail, count only the context the person volunteers (who they are, why, story, names, background); values that define the task (numbers of a calculation, format rules, the claim, the text to work on) are part of the ask. Word ceilings for bare and terse are checked by code; fail detail only when the volunteered context clearly does not match the label.
Definitions:
{definitions}
Return JSON {{"items":[{{"slot_id":..., "pass": true|false, "reasons": [...], "note": "one sentence"}}]}}
ITEMS:
{items}"""
S_INST = {'type': 'object', 'properties': {'items': {'type': 'array', 'items': {'type': 'object', 'properties': {'slot_id': {'type': 'string'}, 'scenario': {'type': 'string'}, 'task_summary': {'type': 'string'}, 'givens': {'type': 'array', 'items': {'type': 'string'}}, 'constraints': {'type': 'array', 'items': {'type': 'object', 'properties': {'type': {'type': 'string'}, 'params': {'type': 'string'}, 'text': {'type': 'string'}}, 'required': ['type', 'params', 'text'], 'additionalProperties': False}}, 'packet': {'type': 'string'}, 'deliverable': {'type': 'string'}, 'ambiguity': {'type': 'string', 'enum': ['none', 'ambiguous', 'underspecified']}, 'maths_content': {'type': 'string', 'enum': ['none', 'embedded', 'maths']}, 'check_values': {'type': 'array', 'items': {'type': 'string'}}, 'answer_conditions': {'type': 'string'}}, 'required': ['slot_id', 'scenario', 'task_summary', 'givens', 'constraints', 'packet', 'deliverable', 'ambiguity', 'maths_content', 'check_values', 'answer_conditions'], 'additionalProperties': False}}}, 'required': ['items'], 'additionalProperties': False}
S_REND = {'type': 'object', 'properties': {'items': {'type': 'array', 'items': {'type': 'object', 'properties': {'slot_id': {'type': 'string'}, 'story': {'type': 'string'}, 'message': {'type': 'string'}, 'pasted_span': {'type': 'string'}}, 'required': ['slot_id', 'story', 'message', 'pasted_span'], 'additionalProperties': False}}}, 'required': ['items'], 'additionalProperties': False}
S_REV = {'type': 'object', 'properties': {'items': {'type': 'array', 'items': {'type': 'object', 'properties': {'slot_id': {'type': 'string'}, 'pass': {'type': 'boolean'}, 'reasons': {'type': 'array', 'items': {'type': 'string', 'enum': REASONS}}, 'note': {'type': 'string'}}, 'required': ['slot_id', 'pass', 'reasons', 'note'], 'additionalProperties': False}}}, 'required': ['items'], 'additionalProperties': False}
LOCK = threading.Lock()
def db():
    c = sqlite3.connect(REG, timeout=60); c.execute('CREATE TABLE IF NOT EXISTS reservations(slot_id TEXT, attempt INTEGER, instance_key TEXT UNIQUE, rendering_key TEXT UNIQUE, run TEXT, status TEXT, retry_of TEXT, created REAL, PRIMARY KEY(slot_id, attempt))'); return c
def reserve(slot, ikey, run, attempt):
    with LOCK:
        c = db()
        try:
            c.execute('BEGIN IMMEDIATE'); c.execute('INSERT INTO reservations VALUES (?,?,?,?,?,?,?,?)', (slot['slot_id'], attempt, ikey, None, run, 'pending', f"{slot['slot_id']}#{attempt - 1}" if attempt > 1 else None, time.time())); c.commit(); return True
        except sqlite3.IntegrityError: c.rollback(); return False
        finally: c.close()
def set_reservation(slot_id, ikey, status, rkey=None):
    with LOCK:
        c = db()
        try: c.execute('UPDATE reservations SET status=?, rendering_key=COALESCE(?, rendering_key) WHERE slot_id=? AND instance_key=?', (status, rkey, slot_id, ikey)); c.commit()
        except sqlite3.IntegrityError: c.rollback(); c.execute('UPDATE reservations SET status=? WHERE slot_id=? AND instance_key=?', ('rejected_duplicate_rendering', slot_id, ikey)); c.commit()
        finally: c.close()
def gl_line(prefix):
    m = re.search(r'^' + re.escape(prefix) + r'.*$', GL, re.M); return m.group(0) if m else ''
def defs_for(slots, instance_stage=False):
    lines = {gl_line('Detail is defined by content')}
    if instance_stage: lines.add(purpose_def('math'))
    if any(s['purpose'] == 'safety' for s in slots): lines.add('Safety sub-kinds. ' + gl_line('Decision order'))
    for s in slots:
        lines.add(purpose_def(s['purpose'])); lines.update([definition(s['detail']), definition(s['register']), definition(s['attitude']), definition(s['difficulty'])])
        if s['purpose'] == 'safety': lines.add(safety_def(s['subtype']))
    return '\n'.join(sorted(lines))
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--retry-held', action='store_true'); ap.add_argument('--regenerate', default=''); ap.add_argument('--slots', default=''); ap.add_argument('--first-n', type=int, default=0); ap.add_argument('--all-remaining', action='store_true'); ap.add_argument('--workers', type=int, default=24); ap.add_argument('--fake', action='store_true'); ap.add_argument('--registry', default=''); ap.add_argument('--runs-dir', default=''); a = ap.parse_args()
    global REG
    if a.registry: REG = pathlib.Path(a.registry)
    man = json.load(open(HERE / 'manifest_round3.json')); runs = pathlib.Path(a.runs_dir) if a.runs_dir else HERE / 'runs'; out = runs / a.run; out.mkdir(parents=True, exist_ok=True)
    (out / 'generate.snapshot.py').write_bytes((HERE / 'generate.py').read_bytes())     # the exact source this run executed (R-PG4 finding 7)
    done_slots, active_slots = set(), set()
    for f in runs.glob('*/prompts.jsonl'):
        for l in open(f):
            r = json.loads(l); done_slots.add(r['slot_id'])
            if r['status'] == 'active': active_slots.add(r['slot_id'])
    if a.retry_held: done_slots = active_slots       # held slots get a fresh instance attempt
    regen = set()
    if a.regenerate:                                  # supersede accepted prompts that failed verification and generate them again
        src = pathlib.Path(a.regenerate); regen = set((src.read_text() if src.exists() else a.regenerate).replace('\n', ',').split(','));  regen = {s.strip() for s in regen if s.strip()}
        done_slots -= regen; c0 = sqlite3.connect(REG, timeout=60)
        for f in runs.glob('*/prompts.jsonl'):
            keep = [json.loads(l) for l in open(f)]; touched = False
            for r in keep:
                if r['slot_id'] in regen and r['status'] == 'active':
                    r['status'] = 'superseded'; r['superseded_by_run'] = a.run; touched = True
                    c0.execute("UPDATE prompts SET status='superseded', keepable=0, status_reason='verification: regenerated' WHERE logical_id=?", ('sp:' + sha(r['instance_key'])[:16],))
            if touched:
                with open(f, 'w') as h:
                    for r in keep: h.write(json.dumps(r, ensure_ascii=False) + '\n')
        c0.commit(); c0.close()
    if regen: slots = [s for s in man['slots'] if s['slot_id'] in regen]
    elif a.slots: slots = [s for s in man['slots'] if s['slot_id'] in set(a.slots.split(','))]
    elif a.all_remaining: slots = [s for s in man['slots'] if s['slot_id'] not in done_slots]
    else: slots = [s for s in man['slots'] if s['slot_id'] not in done_slots][: a.first_n]
    if a.fake:
        from fake_sol import FakeSol; srv = FakeSol()
    else:
        from codex_server import CodexServer; srv = CodexServer(); srv.start()
    calls = collections.Counter()
    def call(stage, prompt, schema, effort='high'):
        calls[stage] += 1
        for attempt in range(3):
            try: return srv.call(prompt, schema, model='gpt-5.6-sol', effort=effort, timeout=900)
            except Exception as e: err = e
        raise err
    c = sqlite3.connect(REG, timeout=60)
    corpus = [(lid, content_words(json.loads(m)[-1]['content'])) for lid, m in c.execute("SELECT logical_id, messages FROM prompts WHERE status IN ('active','held')")]
    avoid = collections.defaultdict(list)
    for (sj,) in c.execute("SELECT seed_json FROM seeds WHERE generator_version='0.2'"):
        s = json.loads(sj)
        if s.get('instance'): avoid[(s['slot']['purpose'], s['slot']['subtype'])].append(s['instance']['task_summary'])
    c.close()
    log = lambda name, row: open(out / f'{name}.jsonl', 'a').write(json.dumps(row, ensure_ascii=False) + '\n')
    # 1. instances + reservations
    instances = {}; inst_words = []; scen_all = []
    for f in runs.glob('*/instances.jsonl'):
        for l in open(f):
            x = json.loads(l)
            if x.get('reserved'): inst_words.append((x['slot_id'], instance_words(x['instance']), scenario_stems(x['instance']))); scen_all.append(x['instance'].get('scenario') or '')
    pending = list(slots)
    c0 = db(); offset = {sid: n for sid, n in c0.execute('SELECT slot_id, MAX(attempt) FROM reservations GROUP BY slot_id')}; c0.close()
    for attempt in (1, 2, 3):
        if not pending: break
        groups = collections.defaultdict(list)
        for s in pending: groups[(s['purpose'], s['subtype'])].append(s)
        batches = [g[i:i + 4] for g in groups.values() for i in range(0, len(g), 4)]
        def inst_batch(b):
            p, sub = b[0]['purpose'], b[0]['subtype']
            prompt = INSTANCE_PROMPT.format(requires=KINDS[p][sub]['requires'], avoid=json.dumps(sorted(set(scen_all)), ensure_ascii=False), avoid_summaries=json.dumps(avoid[(p, sub)][-25:], ensure_ascii=False), definitions=defs_for(b, instance_stage=True),
                                            slots=json.dumps([dict({k: s[k] for k in ('slot_id', 'purpose', 'subtype', 'language', 'difficulty', 'detail', 'person', 'situation', 'topic')}, needs_packet=s['packet']) for s in b], ensure_ascii=False))
            return b, call('instance', prompt, S_INST)
        nxt = []
        with concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
            for b, v in ex.map(inst_batch, batches):
                by = {x['slot_id']: x for x in v['items']}
                for s in b:
                    inst = by.get(s['slot_id'])
                    if not inst: nxt.append(s); continue
                    if not s['packet'] and inst.get('packet'): inst['packet'] = ''; inst.setdefault('dropped', []).append('packet_on_non_packet_subtype')
                    sim = similar(inst, inst_words)
                    if sim: log('instances', dict(slot_id=s['slot_id'], attempt=attempt + offset.get(s['slot_id'], 0), rejected='similar_instance', similar_to=sim[:3], instance=inst)); nxt.append(s); scen_all.append(inst.get('scenario') or ''); continue
                    att = attempt + offset.get(s['slot_id'], 0)
                    ikey = instance_key(s, inst); ok = reserve(s, ikey, a.run, att)
                    log('instances', dict(slot_id=s['slot_id'], attempt=att, instance_key=ikey, reserved=ok, instance=inst))
                    if ok: inst_words.append((s['slot_id'], instance_words(inst), scenario_stems(inst))); scen_all.append(inst.get('scenario') or ''); instances[s['slot_id']] = (inst, ikey); avoid[(s['purpose'], s['subtype'])].append(inst['task_summary'])
                    else: nxt.append(s)
        pending = nxt
    held = {s['slot_id']: ['instance_collision_or_missing'] for s in pending}
    # 2–4. render, check, review, repair
    todo = [s for s in slots if s['slot_id'] in instances]; final = {}; repair_notes = {}
    for round_ in (0, 1, 2):
        if not todo: break
        batches = [todo[i:i + 4] for i in range(0, len(todo), 4)]
        def rend_batch(b):
            payload = []
            for s in b:
                inst, _ = instances[s['slot_id']]
                payload.append(dict(slot_id=s['slot_id'], language=LANG_NAME[s['language']], register=s['register'], attitude=s['attitude'], detail=s['detail'], difficulty=s['difficulty'], person=s['person'], situation=s['situation'], topic=s['topic'],
                                    purpose=s['purpose'], subtype=s['subtype'], task_summary=inst['task_summary'], givens=inst['givens'], constraints=[x['text'] for x in inst['constraints']], deliverable=inst['deliverable'], packet=inst['packet'], check_values=inst['check_values'],
                                    previous_problems=repair_notes.get(s['slot_id'])))
            rep = 'REPAIR: some slots failed before; fix exactly the listed previous_problems without changing the instance.\n' if round_ else ''
            return b, call('render', RENDER_PROMPT.format(repair=rep, definitions=defs_for(b), slots=json.dumps(payload, ensure_ascii=False)), S_REND)
        renders = {}
        with concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
            for b, v in ex.map(rend_batch, batches):
                for x in v['items']: renders[x['slot_id']] = x
        checked = []; round_words = []
        for s in todo:
            r = renders.get(s['slot_id'])
            if not r: repair_notes[s['slot_id']] = ['no_rendering']; continue
            if not s['packet'] and r.get('pasted_span'): r['pasted_span'] = ''; r['pasted_span_cleared'] = True
            inst, ikey = instances[s['slot_id']]; issues = code_checks(s, inst, r, corpus + round_words)
            round_words.append((s['slot_id'], content_words(r['message'])))
            log('renderings', dict(slot_id=s['slot_id'], round=round_, rendering=r, code_issues=issues)); checked.append((s, r, issues))
        rb = [checked[i:i + 6] for i in range(0, len(checked), 6)]
        def rev_batch(b):
            items = [dict(slot_id=s['slot_id'], language=LANG_NAME[s['language']], register=s['register'], attitude=s['attitude'], detail=s['detail'], difficulty=s['difficulty'], purpose=s['purpose'], subtype=s['subtype'], instance={k: instances[s['slot_id']][0][k] for k in ('task_summary', 'givens', 'constraints', 'packet', 'deliverable', 'check_values')}, message=r['message']) for s, r, _ in b]
            return b, call('review', REVIEW_PROMPT.format(reasons=', '.join(REASONS), definitions=defs_for([x[0] for x in b]), items=json.dumps(items, ensure_ascii=False)), S_REV)
        nxt = []
        with concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
            for b, v in ex.map(rev_batch, rb):
                by = {x['slot_id']: x for x in v['items']}
                for s, r, issues in b:
                    rv = by.get(s['slot_id'], dict(slot_id=s['slot_id'], **{'pass': False}, reasons=['other'], note='no review'))
                    log('reviews', dict(slot_id=s['slot_id'], round=round_, review=rv))
                    problems = issues + ([f'review:{x}' for x in rv['reasons']] if not rv['pass'] else [])
                    if not problems:
                        corpus.append((s['slot_id'], content_words(r['message']))); final[s['slot_id']] = (r, rv, round_)
                    else: repair_notes[s['slot_id']] = problems + ([rv['note']] if rv.get('note') else []); nxt.append(s)
        todo = nxt
    for s in todo: held[s['slot_id']] = repair_notes.get(s['slot_id'], ['unknown'])
    # 5. write prompts and register
    c = sqlite3.connect(REG, timeout=60); res_updates = []
    with open(out / 'prompts.jsonl', 'a') as h:
        for s in slots:
            sid = s['slot_id']; inst, ikey = instances.get(sid, (None, None))
            if sid in final:
                r, rv, rnd = final[sid]; status = 'active'; reasons = []
            else:
                r, rv, rnd = None, None, None; status = 'held'; reasons = held.get(sid, ['unknown'])
            mc = (inst or {}).get('maths_content'); maths = 'maths' if s['purpose'] == 'math' else ('embedded' if mc == 'embedded' else None)
            row = dict(slot_id=sid, status=status, held_reasons=reasons, purpose=s['purpose'], subtype=s['subtype'], language=s['language'], difficulty=s['difficulty'], attitude=s['attitude'], register=s['register'], detail=s['detail'],
                       person=s['person'], situation=s['situation'], topic=s['topic'], instance=inst, instance_key=ikey, story=r['story'] if r else None, messages=[{'role': 'user', 'content': r['message']}] if r else None, pasted_span=r['pasted_span'] if r else None,
                       repair_rounds=rnd, maths_content=maths, maths_ambiguity=(inst or {}).get('ambiguity') if s['purpose'] == 'math' else None, instance_maths_content=mc, generator_version='0.2', glossary_sha16=GL_SHA16, run=a.run,
                       code_sha16=hashlib.sha256((HERE / 'generate.py').read_bytes()).hexdigest()[:16], manifest_version=man['version'])
            h.write(json.dumps(row, ensure_ascii=False) + '\n')
            if inst: res_updates.append((sid, ikey, 'completed' if status == 'active' else 'rejected', rendering_key(ikey, s, r['message']) if r else None))
            c.execute('INSERT OR REPLACE INTO seeds VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (f'seed:0.2:{sid}', '0.2', f'generator_v02/runs/{a.run}', json.dumps(dict(slot=s, instance=inst), ensure_ascii=False), ikey, f"{s['purpose']}/{s['subtype']}", s['language'], s['register'], s['attitude'], s['detail'], 'selected' if status == 'active' else 'held', None))
            if r:
                lid = 'sp:' + sha(ikey)[:16]; msgs = json.dumps(row['messages'], ensure_ascii=False)
                c.execute('INSERT OR REPLACE INTO prompts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (lid, 1, msgs, sha(json.dumps([['user', norm(r['message'])]], ensure_ascii=False)), 'seeded', '0.2', 'round3', s['purpose'], f"{s['purpose']}/{s['subtype']}", s['language'], None, s['detail'], s['register'], s['attitude'], f'seed:0.2:{sid}', 'bound', None, int(status == 'active'), status, ';'.join(reasons) or None, maths, len(re.findall(r'\w+', r['message'])), json.dumps({'difficulty': s['difficulty'], 'maths_ambiguity': row['maths_ambiguity']}, ensure_ascii=False)))
                c.execute('INSERT OR IGNORE INTO aliases VALUES (?,?,?,?)', (sid, lid, 'round3', f'generator_v02/runs/{a.run}/prompts.jsonl'))
    c.commit(); c.close()
    for u in res_updates: set_reservation(*u)
    receipt = dict(run=a.run, slots=len(slots), active=len(final), held=len(slots) - len(final), repairs_used=collections.Counter(v[2] for v in final.values()), sol_calls=dict(calls), glossary_sha16=GL_SHA16,
                   code_sha16=hashlib.sha256((HERE / 'generate.py').read_bytes()).hexdigest()[:16], manifest_sha16=hashlib.sha256((HERE / 'manifest_round3.json').read_bytes()).hexdigest()[:16], task_kinds_sha16=hashlib.sha256((HERE / 'task_kinds.json').read_bytes()).hexdigest()[:16], finished=time.time())
    json.dump(receipt, open(out / 'receipt.json', 'w'), indent=1, default=str); print('GEN_DONE', json.dumps(receipt, default=str))
    if not a.fake: srv.close()
if __name__ == '__main__': main()
