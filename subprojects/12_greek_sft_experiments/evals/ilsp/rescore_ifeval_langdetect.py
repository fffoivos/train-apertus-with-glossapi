#!/usr/bin/env python3
"""Offline rescoring of saved Greek IFEval samples with langdetect available (the cluster harness lacked it, so every language:response_language
instruction scored 0 for every model). Reuses the task's own checkers. Usage: python3 rescore_ifeval_langdetect.py <results_root> → writes <root>/ifeval_el_rescored.json
Run with a venv that has langdetect (apertus-local-chat)."""
import json, glob, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'tasks'))
from ifeval_greek import utils as U, instructions as I
assert I.langdetect is not None, 'langdetect missing in this interpreter'
root = sys.argv[1]; out = {}
for d in sorted(glob.glob(os.path.join(root, '*', 'ilsp'))):
    label = d.split(os.sep)[-2]; fs = sorted(glob.glob(os.path.join(d, '*', 'samples_ifeval_greek*.jsonl')))
    if not fs: continue
    rows = [json.loads(l) for l in open(fs[-1])]
    def _flat(v): return list(v) if isinstance(v, list) else [v]
    orig = dict(p=sum(float(r['prompt_level_strict_acc']) for r in rows) / len(rows), i=sum(sum(map(float, _flat(r['inst_level_strict_acc']))) for r in rows) / sum(len(_flat(r['inst_level_strict_acc'])) for r in rows))
    ps = pl = 0; is_ = il = 0; n_inst = 0; n_lang = 0; items = []
    for r in rows:
        doc = r['doc']; resp = r['filtered_resps'][0] if r.get('filtered_resps') else (r['resps'][0][0] if r.get('resps') else '')
        inp = U.InputExample(key=doc['key'], instruction_id_list=doc['instruction_id_list'], prompt=doc['prompt'], kwargs=doc['kwargs'])
        s = U.test_instruction_following_strict(inp, resp); l = U.test_instruction_following_loose(inp, resp)
        items.append(dict(key=doc['key'], prompt_strict=bool(s.follow_all_instructions))); ps += s.follow_all_instructions; pl += l.follow_all_instructions; is_ += sum(s.follow_instruction_list); il += sum(l.follow_instruction_list); n_inst += len(doc['instruction_id_list'])
        n_lang += sum(1 for x in doc['instruction_id_list'] if x.startswith('language:'))
    res = dict(n=len(rows), orig_prompt_strict=round(orig['p'], 4), orig_inst_strict=round(orig['i'], 4), prompt_strict=round(ps / len(rows), 4), inst_strict=round(is_ / n_inst, 4), prompt_loose=round(pl / len(rows), 4), inst_loose=round(il / n_inst, 4), language_instructions=n_lang)
    res['prompt_strict_items'] = items   # per-prompt booleans, keyed by the IFEval key, for paired contrasts (14 Sept readout v2)
    res['strict_avg'] = round((res['prompt_strict'] + res['inst_strict']) / 2 * 100, 1); res['orig_strict_avg'] = round((orig['p'] + orig['i']) / 2 * 100, 1)
    out[label] = res; print(f"{label:24s} strict avg {res['orig_strict_avg']:5.1f} → {res['strict_avg']:5.1f}  (prompt {res['prompt_strict']*100:.1f}, inst {res['inst_strict']*100:.1f}; loose prompt {res['prompt_loose']*100:.1f})")
json.dump(out, open(os.path.join(root, 'ifeval_el_rescored.json'), 'w'), indent=1); print('written', os.path.join(root, 'ifeval_el_rescored.json'))
