#!/usr/bin/env python3
"""PG3b: relabel existing records with the frozen glossary (spec v1.0) without changing any prompt text.
Forum posts (used and unused gate-accepted): task_type (F1–F9) + maths_content + maths ambiguity. Seeded round-2 prompts: maths_content +
ambiguity. Sol gpt-5.6-sol, batches of 6, 24 workers, resumable. Output: data/rlhf/registry/relabel_v1.jsonl (one row per item).
Usage: python3 data/rlhf/registry/relabel_v1.py"""
import concurrent.futures, hashlib, json, pathlib, re, sqlite3, sys
HERE = pathlib.Path(__file__).resolve().parent; RL = HERE.parent; sys.path.insert(0, str(RL.parent / 'math'))
from codex_server import CodexServer
OUT = HERE / 'relabel_v1.jsonl'; GL = (RL / 'prompts' / 'seed_label_definitions_v1.md').read_text()
GL_SHA16 = hashlib.sha256(GL.encode()).hexdigest()[:16]
def section(title):
    i = GL.find(title); j = GL.find('\n## ', i + 1); return GL[i:j].strip()
FORUM_TT = section('## Forum task_type'); TASK = section('## Task — primary purpose')
maths_block = TASK[TASK.find('- math (maths):'):TASK.find('- dialogue:')].strip()
PROMPT = f"""You label user requests for a Greek RLHF dataset with fixed definitions. Do not rewrite or answer the requests. Return JSON only.

For each item give:
- task_type (forum items only; for seeded items return "n/a"): exactly one value from these definitions:
{FORUM_TT}
- maths_content: true when the request's correctness depends on mathematics in the sense of the definition below, whatever its main purpose (for example a budget or a calculation inside a planning request); false otherwise.
- maths_ambiguity: "none", "ambiguous" (several readings) or "underspecified" (missing information needed for a determinate answer); "none" when maths_content is false.
- reason: one short English sentence naming the decisive feature.

Maths definition:
{maths_block}

ITEMS:
"""
SCHEMA = {'type': 'object', 'properties': {'items': {'type': 'array', 'items': {'type': 'object', 'properties': {
    'id': {'type': 'string'}, 'task_type': {'type': 'string', 'enum': ['question', 'explanation', 'advice', 'opinion', 'translation', 'calculation', 'share', 'other', 'create', 'n/a']},
    'maths_content': {'type': 'boolean'}, 'maths_ambiguity': {'type': 'string', 'enum': ['none', 'ambiguous', 'underspecified']}, 'reason': {'type': 'string'}},
    'required': ['id', 'task_type', 'maths_content', 'maths_ambiguity', 'reason'], 'additionalProperties': False}}}, 'required': ['items'], 'additionalProperties': False}
c = sqlite3.connect(HERE / 'registry.sqlite')
items = []
used = {}
for lid, msgs, src in c.execute("SELECT logical_id, messages, source_id FROM prompts WHERE source_kind='forum'"):
    used[src] = (lid, json.loads(msgs)[-1]['content'])
for sid, url, forum, payload, status in c.execute("SELECT source_id, url, forum, payload, status FROM sources WHERE kind='forum_post' AND status='gate_accepted'"):
    text = used[sid][1] if sid in used else json.loads(payload).get('prompt_el')
    items.append(dict(id=sid, kind='forum', forum=forum, text=text, text_sha16=hashlib.sha256(text.encode()).hexdigest()[:16], used=sid in used))
for lid, msgs in c.execute("SELECT logical_id, messages FROM prompts WHERE source_kind='seeded' AND status='active'"):
    text = json.loads(msgs)[-1]['content']; items.append(dict(id=lid, kind='seeded', forum=None, text=text, text_sha16=hashlib.sha256(text.encode()).hexdigest()[:16], used=True))
done = {json.loads(l)['id'] for l in open(OUT)} if OUT.exists() else set()
todo = [it for it in items if it['id'] not in done]
batches = [todo[i:i + 6] for i in range(0, len(todo), 6)]
print(f'{len(items)} items, {len(done)} done, {len(batches)} calls to make; glossary {GL_SHA16}', flush=True)
srv = CodexServer(); srv.start()
def run(batch):
    payload = [dict(id=b['id'], kind=b['kind'], forum=b['forum'], text=b['text']) for b in batch]
    for attempt in range(3):
        try:
            v = srv.call(PROMPT + json.dumps(payload, ensure_ascii=False), SCHEMA, model='gpt-5.6-sol', effort='medium', timeout=600)
            by = {x['id']: x for x in v['items']}
            if set(by) != {b['id'] for b in batch}: raise ValueError('id mismatch')
            return [dict(b, **{k: by[b['id']][k] for k in ('task_type', 'maths_content', 'maths_ambiguity', 'reason')}, glossary_sha16=GL_SHA16, relabel_version='relabel-v1') for b in batch]
        except Exception as e: err = str(e)[:200]
    return [dict(b, error=err) for b in batch]
n = 0
with open(OUT, 'a') as h, concurrent.futures.ThreadPoolExecutor(24) as ex:
    for rows in ex.map(run, batches):
        for r in rows:
            if 'error' not in r: h.write(json.dumps({k: v for k, v in r.items() if k != 'text'}, ensure_ascii=False) + '\n')
        h.flush(); n += 1
        if n % 20 == 0: print(f'{n}/{len(batches)} calls', flush=True)
srv.close(); print('RELABEL_DONE')
