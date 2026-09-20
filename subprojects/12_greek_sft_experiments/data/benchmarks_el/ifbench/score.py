#!/usr/bin/env python3
"""IFBench-el scorer with the reporting the astra review asked for (F3/F4): strict and loose accuracy at prompt level (all constraints) and instruction level,
per overlap class (prompt counts AND instruction-instance counts), per constraint family (macro), mixed-class prompts as a cross-cutting flag, unresolved
separately, and CORE vs EXTENSION (extension = prompts containing a replaced, dropped, re-tuned or predicate-changed constraint). Loose = upstream IFEval
loose (strip markdown asterisks, drop first/last line). Usage: python3 score.py <responses.jsonl: {id, response}> <out.jsonl>"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B; import instructions_registry_el as REG


def loose_variants(resp):
    r = resp.strip(); lines = r.split('\n'); out = [r, r.replace('*', '')]
    if len(lines) > 1: out += ['\n'.join(lines[1:]).strip(), '\n'.join(lines[:-1]).strip(), '\n'.join(lines[1:-1]).strip()]
    return [x for x in out if x] + [x.replace('*', '') for x in out if x]


def check(iid, kw, resp):
    inst = REG.INSTRUCTION_DICT[iid](iid); inst.build_description(**kw)
    # Match upstream evaluation_lib.py: a checker is never allowed to pass an
    # empty or whitespace-only response/loose variant.
    strict = bool(resp.strip()) and bool(inst.check_following(resp))
    loose = strict or any(bool(v.strip()) and bool(inst.check_following(v)) for v in loose_variants(resp))
    return strict, loose


def main():
    bench = {r['id']: r for r in B.load(os.path.join(HERE, 'prompts_el_final.jsonl'))}; resp = B.load(sys.argv[1]); out = []
    for x in resp:
        b = bench[x['id']]; res = [check(iid, kw, x['response']) for iid, kw in zip(b['instruction_id_list'], b['kwargs'])]
        out.append(dict(id=x['id'], ids=b['instruction_id_list'], strict=[s for s, _ in res], loose=[l for _, l in res], overlap_class=b['overlap_class'], overlap_classes=b['overlap_classes'], mixed=b['mixed_overlap'], core=b.get('core', True), fidelity=b.get('fidelity')))
    with open(sys.argv[2], 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in out]
    def prompt_acc(rs, k): return round(sum(all(r[k]) for r in rs) / max(1, len(rs)), 3)
    def inst_acc(rs, k): v = [x for r in rs for x in r[k]]; return round(sum(v) / max(1, len(v)), 3)
    rep = dict(n_prompts=len(out), prompt_strict=prompt_acc(out, 'strict'), prompt_loose=prompt_acc(out, 'loose'), inst_strict=inst_acc(out, 'strict'), inst_loose=inst_acc(out, 'loose'))
    for cls in ('seen', 'seen-novel-composition', 'unseen', 'unresolved'):
        rs = [r for r in out if r['overlap_class'] == cls]; inst = [(s, l) for r in out for c, s, l in zip(r['overlap_classes'], r['strict'], r['loose']) if c == cls]
        rep[f'class_{cls}'] = dict(prompts=len(rs), prompt_strict=prompt_acc(rs, 'strict'), prompt_loose=prompt_acc(rs, 'loose'), instances=len(inst), inst_strict=round(sum(s for s, _ in inst) / max(1, len(inst)), 3), inst_loose=round(sum(l for _, l in inst) / max(1, len(inst)), 3))
    mixed = [r for r in out if r['mixed']]; rep['mixed_prompts'] = dict(prompts=len(mixed), prompt_strict=prompt_acc(mixed, 'strict'))
    for part in ('core', 'extension'):
        rs = [r for r in out if (r['core'] if part == 'core' else not r['core'])]; rep[part] = dict(prompts=len(rs), prompt_strict=prompt_acc(rs, 'strict'), prompt_loose=prompt_acc(rs, 'loose'))
    fam = collections.defaultdict(list); [fam[i].append(s) for r in out for i, s in zip(r['ids'], r['strict'])]; rep['family_macro_strict'] = round(sum(sum(v) / len(v) for v in fam.values()) / max(1, len(fam)), 3); rep['families_present'] = len(fam)
    print(json.dumps(rep, ensure_ascii=False))


if __name__ == '__main__': main()
