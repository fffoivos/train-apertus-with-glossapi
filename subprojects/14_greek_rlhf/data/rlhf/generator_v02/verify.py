#!/usr/bin/env python3
"""Independent label and fidelity verification of accepted prompts (R-PG4 findings 1-3).
For every active prompt: a second, independent Sol pass reads the frozen definitions, the task instance and the realised message and reports
the labels it observes (difficulty, register, attitude, detail), whether the request needs calculation (maths_content) and whether the message
is faithful to the instance. Labels are then corrected to what the message actually realises; prompts whose task drifted are marked for regeneration.
Usage: python3 data/rlhf/generator_v02/verify.py [--runs-dir ...] [--out verification.jsonl] [--apply] [--fake]"""
import argparse, collections, concurrent.futures, hashlib, json, pathlib, sqlite3, sys
HERE = pathlib.Path(__file__).resolve().parent; RL = HERE.parent; sys.path.insert(0, str(RL.parent / 'math'))
import generate as G
PROMPT = """You verify prompts collected for a Greek assistant's RLHF set. You did not write them. For each item you get the task instance the writer was given, the labels the slot fixed, and the message that was written. Report what the message ACTUALLY realises, independently of what the labels claim.
For each item return:
- observed_difficulty, observed_register, observed_attitude, observed_detail: the value the message realises, from the definitions below.
- maths_content: "maths" if the central purpose of the request is mathematical; "embedded" if a correct answer needs calculation, quantitative reasoning or checking numbers (budgets, dates or durations, unit conversions, percentages, dosage, statistics) even though the main task is something else; "none" otherwise.
- fidelity: "ok", or the first problem that applies: "task_changed" (the message asks for something else than the instance), "missing_given", "changed_value", "added_fact" (a new fact that changes what a correct answer is), "framing_or_meta" (evaluation framing, label names, instructions about knowledge cutoffs, placeholders), "answers_itself", "unnatural" (no real person would write this).
- note: one sentence, only where something is not ok or a label differs.
Definitions:
{definitions}
Return JSON {{"items":[{{"slot_id":..., "observed_difficulty":..., "observed_register":..., "observed_attitude":..., "observed_detail":..., "maths_content":"none|embedded|maths", "fidelity":"...", "note":"..."}}]}}
ITEMS:
{items}"""
VALS = dict(observed_difficulty=['routine', 'compositional', 'challenging'], observed_register=['standard', 'formal', 'informal', 'greeklish'],
            observed_attitude=['cooperative', 'skeptical', 'frustrated', 'playful'], observed_detail=['bare', 'terse', 'short', 'medium', 'detailed', 'rambling'],
            maths_content=['none', 'embedded', 'maths'], fidelity=['ok', 'task_changed', 'missing_given', 'changed_value', 'added_fact', 'framing_or_meta', 'answers_itself', 'unnatural'])
SCHEMA = {'type': 'object', 'properties': {'items': {'type': 'array', 'items': {'type': 'object', 'properties': dict(slot_id={'type': 'string'}, note={'type': 'string'},
          **{k: {'type': 'string', 'enum': v} for k, v in VALS.items()}), 'required': ['slot_id'] + list(VALS) + ['note'], 'additionalProperties': False}}}, 'required': ['items'], 'additionalProperties': False}
def defs():
    lines = [G.gl_line('Detail is defined by'), G.purpose_def('math')]
    for group in VALS.values():
        for v in group:
            if v in ('none', 'embedded', 'maths', 'ok') or v in VALS['fidelity']: continue
            lines.append(G.definition(v))
    return '\n'.join(dict.fromkeys(lines))
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--runs-dir', default=str(HERE / 'runs')); ap.add_argument('--out', default=str(HERE / 'verification.jsonl'))
    ap.add_argument('--workers', type=int, default=24); ap.add_argument('--apply', action='store_true'); ap.add_argument('--fake', action='store_true'); a = ap.parse_args()
    rows = []
    for f in sorted(pathlib.Path(a.runs_dir).glob('*/prompts.jsonl')):
        for l in open(f):
            r = json.loads(l)
            if r['status'] == 'active': rows.append((f, r))
    out = pathlib.Path(a.out); done = {(json.loads(l)['slot_id'], json.loads(l).get('run')) for l in open(out)} if out.exists() else set()
    todo = [r for f, r in rows if (r['slot_id'], r['run']) not in done]   # a regenerated prompt is new content for the same slot
    print(f'{len(rows)} active prompts, {len(todo)} to verify', flush=True)
    if todo:
        if a.fake:
            from fake_sol import FakeSol; srv = FakeSol()
        else:
            from codex_server import CodexServer; srv = CodexServer(); srv.start()
        batches = [todo[i:i + 5] for i in range(0, len(todo), 5)]
        def one(b):
            items = [dict(slot_id=r['slot_id'], labels=dict(language=G.LANG_NAME[r['language']], difficulty=r['difficulty'], register=r['register'], attitude=r['attitude'], detail=r['detail']),
                          purpose=r['purpose'], subtype=r['subtype'], instance={k: r['instance'][k] for k in ('task_summary', 'givens', 'constraints', 'packet', 'deliverable', 'check_values')},
                          message=r['messages'][0]['content']) for r in b]
            for _ in range(3):
                try: return b, srv.call(PROMPT.format(definitions=defs(), items=json.dumps(items, ensure_ascii=False)), SCHEMA, model='gpt-5.6-sol', effort='medium', timeout=900)
                except Exception as e: err = e
            raise err
        with open(out, 'a') as h, concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
            for b, v in ex.map(one, batches):
                by = {x['slot_id']: x for x in v['items']}
                for r in b:
                    x = by.get(r['slot_id'])
                    if not x: continue
                    h.write(json.dumps(dict(x, assigned=dict(difficulty=r['difficulty'], register=r['register'], attitude=r['attitude'], detail=r['detail'], maths_content=r['maths_content'], purpose=r['purpose']), run=r['run']), ensure_ascii=False) + '\n')
                h.flush()
        if not a.fake: srv.close()
    V = {json.loads(l)['slot_id']: json.loads(l) for l in open(out)}
    diff = collections.Counter(); fid = collections.Counter(); mc = collections.Counter()
    for f, r in rows:
        v = V.get(r['slot_id'])
        if not v: continue
        for k in ('difficulty', 'register', 'attitude', 'detail'):
            if v['observed_' + k] != r[k]: diff[k] += 1
        fid[v['fidelity']] += 1
        assigned = r['maths_content'] or 'none'; observed = v['maths_content']
        if observed != assigned: mc[f'{assigned}->{observed}'] += 1
    print('label mismatches', dict(diff)); print('fidelity', dict(fid)); print('maths content changes', dict(mc))
    regen = sorted(s for s, v in V.items() if v['fidelity'] in ('task_changed', 'changed_value', 'added_fact', 'framing_or_meta', 'answers_itself', 'unnatural'))
    (HERE / 'regenerate_slots.txt').write_text(','.join(regen)); print('slots to regenerate:', len(regen))
    if a.apply:
        c = sqlite3.connect(RL / 'registry' / 'registry.sqlite', timeout=60); n = 0
        for f, r in rows:
            v = V.get(r['slot_id'])
            if not v: continue
            observed = v['maths_content']; new_mc = 'maths' if r['purpose'] == 'math' else (observed if observed in ('embedded', 'maths') else None)
            # glossary v1.0.3: pasted material never raises the detail level, so a packet prompt read as 'detailed' keeps its assigned label
            detail = r['detail'] if (r.get('pasted_span') and v['observed_detail'] == 'detailed' and r['detail'] != 'detailed') else v['observed_detail']
            upd = dict(difficulty=v['observed_difficulty'], register=v['observed_register'], attitude=v['observed_attitude'], detail=detail, maths_content=new_mc)
            if all(upd[k] == (r[k] if k != 'maths_content' else r['maths_content']) for k in upd): continue
            r['labels_assigned'] = dict(difficulty=r['difficulty'], register=r['register'], attitude=r['attitude'], detail=r['detail'], maths_content=r['maths_content'])
            r.update(upd); r['labels_verified'] = True; n += 1
            lid = 'sp:' + G.sha(r['instance_key'])[:16]
            c.execute('UPDATE prompts SET detail=?, register=?, attitude=?, maths_content=?, labels=? WHERE logical_id=?',
                      (r['detail'], r['register'], r['attitude'], new_mc, json.dumps({'difficulty': r['difficulty'], 'maths_ambiguity': r.get('maths_ambiguity'), 'labels_assigned': r['labels_assigned'], 'labels_verified': True}, ensure_ascii=False), lid))
        c.commit(); c.close()
        upd_by_slot = {r['slot_id']: r for f, r in rows}
        for f in sorted(pathlib.Path(a.runs_dir).glob('*/prompts.jsonl')):      # rewrite whole files: held rows are preserved untouched
            keep = [json.loads(l) for l in open(f)]
            with open(f, 'w') as h:
                for r in keep: h.write(json.dumps(upd_by_slot.get(r['slot_id'], r) if r['status'] == 'active' else r, ensure_ascii=False) + '\n')
        print('applied corrections to', n, 'prompts (verified labels written to prompts.jsonl and the registry)')
if __name__ == '__main__': main()
