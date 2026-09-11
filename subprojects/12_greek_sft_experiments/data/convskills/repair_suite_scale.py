#!/usr/bin/env python3
"""Targeted repairs/filters on the final suite rows after the astra scale review (docs/reviews/ASTRA_convskills_scale_20260911.md):
 H1 S3/S3c edits that lose a protected qualifier, condition, hedge or temporal marker → row dropped (no regeneration this round);
 H2 S5m location ambiguity: a later user turn placing the user elsewhere than the planted city → row dropped;
 H3 S5m budget demonstration: the target must show at least one amount other than the budget figure (an allocation) → else dropped;
 M1 editor changing the conversational act: if the editor removed a question from the target, or removed the planted name (S5m), the
    pre-edit target is restored (language slightly rougher, act preserved).
Usage: python3 repair_suite_scale.py <rows_final.jsonl> <out_rows.jsonl>   (then re-run reverify_suite.py on the output)"""
import json, re, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import gen_suite as G; C = G.C
QUAL = r'\b(φαίνεται|ενδέχεται|ίσως|μάλλον|συνήθως|περίπου|τουλάχιστον|το πολύ|εκτός|εφόσον|πριν|μετά|αφού|ήδη|ακόμη|ακόμα|χωρίς)\b'   # hedges, conditions, temporal markers (astra: conditions, temporal ordering, uncertainty, scope); negations and «αν/μόνο» excluded — every honest shortening drops some of those
def markers(t): return collections.Counter(m.lower() for m in re.findall(QUAL, t, re.I))
def loses_markers(old, new, banned=None):
    mo, mn = markers(old), markers(new); lost = [k for k in mo if mn[k] < mo[k] and (not banned or k != banned.lower())]
    return lost
src, dst = sys.argv[1], sys.argv[2]; rows = [json.loads(l) for l in open(src)]; stats = collections.Counter(); out = []
RAW = {}
for _f in ['v2/S5m.jsonl', 'v2/S3c.jsonl', 'v2/S3.jsonl']:
    if os.path.exists(_f):
        for _l in open(_f): _r = json.loads(_l); RAW[_r['id']] = _r
for r in rows:
    lane = r.get('lane') or r.get('bucket') or (r.get('meta') or {}).get('lane') or r['id'].split('_')[0]; t = r.get('turns') or r['messages']; drop = None
    if lane == 'S3c':   # S3 was 0/7 in the review; S3c 4/7 — the chained shortening is where qualifiers die
        ass = [m['content'] for m in t if m['role'] == 'assistant']; p = (r.get('meta') or {}).get('params') or r.get('params') or (RAW.get(r['id']) or {}).get('params') or {}; w = p.get('w')
        for a, b in zip(ass, ass[1:]):
            lost = loses_markers(a, b, w)
            if lost: drop = f'{lane}: lost markers {lost[:4]}'; break
    if lane == 'S5m' and not drop:
        facts = r.get('facts') or (r.get('meta') or {}).get('facts') or (RAW.get(r['id']) or {}).get('facts') or {}
        city = (facts.get('city') or '')[:4].lower(); later_users = [m['content'] for m in t[1:-1] if m['role'] == 'user']
        if city and any(re.search(r'\b(μένω|ζω|βρίσκομαι|είμαι|δουλεύω)\b[^.]{0,40}\b(σε|στη|στο|στην|στον)\b', u, re.I) and city not in u.lower() for u in later_users): drop = 'S5m: competing location in a later user turn'
        else:
            a = t[-1]['content']; budget = facts.get('budget'); nums = [int(x.replace('.', '')) for x in re.findall(r'\b\d{2,4}\b', a)]
            if budget and not any(n != budget for n in nums): drop = 'S5m: budget mentioned, no allocation shown'
    if drop: stats['dropped:' + drop.split(':')[0]] += 1; continue
    # M1: editor removed a question or the planted name from the target → restore the pre-edit target
    pre = r.get('pre_edit_assistant'); last = t[-1]['content'] if t[-1]['role'] == 'assistant' else None
    if pre and last and pre != last:
        name = ((r.get('facts') or (r.get('meta') or {}).get('facts') or (RAW.get(r['id']) or {}).get('facts') or {}).get('name') or '')
        q_pre, q_new = len(re.findall(r'[;?](\s|$)', pre)), len(re.findall(r'[;?](\s|$)', last))
        if (q_pre > q_new) or (name and name[:4].lower() in pre.lower() and name[:4].lower() not in last.lower()):
            t[-1]['content'] = pre; r['assistant'] = pre; r['edit_reverted'] = 'act changed by the editor (astra scale review M1)'; stats['edit_restored'] += 1
    out.append(r); stats['kept'] += 1
with open(dst, 'w') as f:
    for r in out: f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(json.dumps(dict(rows_in=len(rows), rows_out=len(out), **stats), ensure_ascii=False))
