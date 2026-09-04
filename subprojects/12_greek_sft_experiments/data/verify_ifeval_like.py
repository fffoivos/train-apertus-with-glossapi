#!/usr/bin/env python3
"""Re-run the IFEval constraint checkers on argilla/ifeval-like-data rows (raw export with instruction_id_list + kwargs).
Writes keep_ids / wrong_ids and a summary. Runs inside the cluster lm_eval env (lm_eval.tasks.ifeval).
Usage: python3 verify_ifeval_like.py <raw.jsonl> <out_dir>"""
import json, sys, os, collections
import importlib, importlib.util, importlib.machinery
try:
    reg = importlib.import_module('lm_eval.tasks.ifeval.instructions_registry')
except Exception:
    import lm_eval
    d = os.path.join(os.path.dirname(lm_eval.__file__), 'tasks', 'ifeval')
    for name in ('instructions_util', 'instructions', 'instructions_registry'):
        pyc = os.path.join(d, name + '.pyc')
        spec = importlib.util.spec_from_file_location('lm_eval.tasks.ifeval.' + name, pyc, loader=importlib.machinery.SourcelessFileLoader('lm_eval.tasks.ifeval.' + name, pyc))
        mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    reg = sys.modules['lm_eval.tasks.ifeval.instructions_registry']
IN, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
stats = collections.Counter(); keep, wrong, unknown = [], [], []
per_type = collections.Counter(); per_type_fail = collections.Counter()
for line in open(IN):
    r = json.loads(line); stats['rows'] += 1
    ids = r.get('instruction_id_list') or []; kws = r.get('kwargs') or []
    if isinstance(ids, str):
        try: ids = json.loads(ids)
        except Exception: ids = []
    if isinstance(kws, str):
        try: kws = json.loads(kws)
        except Exception: kws = []
    prompt = r.get('prompt') or r.get('instruction') or ''; resp = r.get('response') or r.get('output') or ''
    rid = r.get('key') or r.get('id') or r.get('_row')
    if not ids or not resp.strip(): unknown.append(rid); stats['unknown'] += 1; continue
    ok = True
    for i, iid in enumerate(ids):
        cls = reg.INSTRUCTION_DICT.get(iid)
        if cls is None: unknown.append(rid); stats['unknown_type'] += 1; ok = None; break
        inst = cls(iid); kw = kws[i] if i < len(kws) and isinstance(kws[i], dict) else {}
        kw = {k: v for k, v in kw.items() if v is not None}
        try:
            inst.build_description(**kw)
            args = inst.get_instruction_args()
            if args and 'prompt' in args: inst.build_description(prompt=prompt)
            passed = inst.check_following(resp)
        except Exception as e:
            passed = None; stats['checker_error'] += 1
        per_type[iid] += 1
        if passed is False: ok = False; per_type_fail[iid] += 1
        elif passed is None: ok = None
    if ok is True: keep.append(rid); stats['pass'] += 1
    elif ok is False: wrong.append(rid); stats['fail'] += 1
    else: unknown.append(rid); stats['unknown'] += 1
for name, lst in (('keep', keep), ('wrong', wrong), ('unchecked', unknown)):
    open(f'{OUT}/{name}_ids.txt', 'w').write('\n'.join(str(x) for x in lst) + '\n')
summary = dict(stats=dict(stats), per_type={k: dict(n=per_type[k], fail=per_type_fail[k]) for k in per_type})
json.dump(summary, open(f'{OUT}/summary.json', 'w'), indent=1); print(json.dumps(summary['stats']))
for k, v in sorted(summary['per_type'].items(), key=lambda x: -x[1]['fail'])[:10]: print(f"{k:45s} n={v['n']:6d} fail={v['fail']}")
