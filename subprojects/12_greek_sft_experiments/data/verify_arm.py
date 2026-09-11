#!/usr/bin/env python3
"""Row-level ledger for an assembled arm (astra readiness review F2): per block — unique input rows, exclusion reasons (unrenderable: ends
with a user turn / empty turn / nothing to supervise / merged roles; too long; contaminated; exact duplicates; dev), train unique and effective;
content-hash disjointness of train vs dev (not just ids); cross-block content duplicates; the personality holdout ids + hashes verified absent
from train; exact totals and file hashes. Usage: python3 verify_arm.py <arm>  → data/arms/<arm>/ledger.json"""
import json, sys, os, hashlib, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent; arm = sys.argv[1]; A = HERE / 'arms' / arm
rec = json.load(open(A / 'receipt.json'))
def chash(msgs): return hashlib.sha1(json.dumps([(m['role'], m['content']) for m in msgs], ensure_ascii=False).encode()).hexdigest()
train = [json.loads(l) for l in open(A / 'train.jsonl')]; dev = [json.loads(l) for l in open(A / 'dev.jsonl')]
th = collections.defaultdict(set); tid = collections.defaultdict(set)
for r in train: th[r['config']].add(chash(r['messages'])); tid[r['config']].add(r['id'])
dh = {(r['config'], chash(r['messages'])) for r in dev}; dev_ids = {(r['config'], r['id']) for r in dev}
overlap_content = sum(1 for cfg, h in dh if h in th[cfg]); overlap_id = sum(1 for cfg, i in dev_ids if i in tid[cfg])
all_train_h = collections.Counter(chash(r['messages']) for r in train); cross = collections.Counter()
seen = {}
for r in train:
    h = chash(r['messages'])
    if h in seen and seen[h] != r['config']: cross[(seen[h], r['config'])] += 1
    seen.setdefault(h, r['config'])
hold = set(json.load(open(HERE / 'personality' / 'personality_holdout_ids.json'))); hold_in_train = sum(1 for r in train if r['config'] == 'personality' and r['id'] in hold)
hold_rows = [r for r in dev if r['config'] == 'personality']; hold_hashes = {r['id']: chash(r['messages']) for r in hold_rows}; hold_content_in_train = sum(1 for r in train if chash(r['messages']) in set(hold_hashes.values()))
ledger = dict(arm=arm, train_rows=len(train), dev_rows=len(dev), train_sha256=rec['train']['sha256'], dev_sha256=rec['dev']['sha256'], train_tokens=rec['train']['tokens'],
              train_dev_overlap_by_id=overlap_id, train_dev_overlap_by_content=overlap_content, cross_block_content_duplicates=dict((f'{a}->{b}', n) for (a, b), n in cross.items()),
              within_train_exact_content_duplicates=sum(n - 1 for n in all_train_h.values() if n > 1), personality_holdout_ids=len(hold), holdout_ids_in_train=hold_in_train, holdout_content_in_train=hold_content_in_train, holdout_rows_in_dev=len(hold_rows), holdout_id_hashes=hold_hashes, blocks={})
# per-block exclusion reasons: re-read the file-backed sources with the assembler's converter
src = open(HERE / 'assemble_mix_r2.py').read(); s0 = src.index('def to_messages'); s1 = src.index('# ---------- evaluation prompts')
ns = {'GREEK_EDITS': {}}; exec(src[s0:s1], ns); to_messages = ns['to_messages']
FILES = {'personality': 'personality/personality_v3v4_final.jsonl', 'greek_if': 'greek_if/final/greek_if_sft.jsonl', 'greek_math': 'math/cut1/edited/rows_edited.jsonl', 'convskills': 'convskills/v2/final/rows_final.jsonl', 'correcting': 'robustness/correcting/scale/rows/rows_final.jsonl'}
for b in rec['blocks']:
    if b.get('status') != 'ok': continue
    e = dict(unique_input_rows=b.get('unique_input_rows'), taken=b['taken'], dev_rows=b.get('dev_rows'), train_unique=b.get('train_unique_rows'), copies=b['weight'], train_effective=b.get('train_rows_effective'), contaminated=b['contaminated'], too_long=b.get('too_long'), exact_duplicates=b.get('exact_duplicates_dropped', 0), id_collisions=b.get('id_collisions_suffixed', 0), identity_backstop=b.get('identity_backstop'), lexicon_mannerism=b.get('lexicon_mannerism'), tone_dropped=b.get('tone_dropped'), masked_context_turns=b.get('masked_context_turns'))
    if b['block'] in FILES:
        reasons = collections.Counter(); n = 0
        for l in open(HERE / FILES[b['block']]):
            r = json.loads(l); n += 1; t = r.get('turns') or r.get('messages') or []
            m = to_messages(r, b['block'])
            if m is None:
                if t and t[-1]['role'] != 'assistant': reasons['unrenderable: ends with a user turn'] += 1
                elif any(x['role'] == 'assistant' and not (x.get('content') or '').strip() for x in t): reasons['unrenderable: empty assistant turn'] += 1
                elif not any(x['role'] == 'assistant' and x.get('train', True) for x in t): reasons['unrenderable: nothing to supervise'] += 1
                else: reasons['unrenderable: other (merged roles / no user turn)'] += 1
        e['source_rows'] = n; e['unrenderable'] = dict(reasons); e['accounted'] = n - sum(reasons.values()) - (b.get('exact_duplicates_dropped', 0)) == b.get('unique_input_rows') - b.get('exact_duplicates_dropped', 0) or None
    ledger['blocks'][b['block']] = e
json.dump(ledger, open(A / 'ledger.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in ledger.items() if k not in ('blocks', 'holdout_id_hashes')}, ensure_ascii=False))
for k in FILES: print(k, {kk: vv for kk, vv in ledger['blocks'][k].items() if kk in ('source_rows', 'unique_input_rows', 'unrenderable', 'contaminated', 'too_long', 'exact_duplicates', 'dev_rows', 'train_unique', 'train_effective')})
