#!/usr/bin/env python3
"""Does Luna's task-type (skill) label hold up? Sonnet 5 labels the skill of n rows per block from the same skill list; agreement is reported.
Usage: python3 data/sonnet_skill_check.py <out_dir> <n_per_block> <block1> [block2 ...]"""
import json, sys, os, re, random, subprocess, collections, datetime
OUT, N = sys.argv[1], int(sys.argv[2]); BLOCKS = sys.argv[3:]; A = os.path.expanduser('~/sft_annot'); os.makedirs(OUT, exist_ok=True); HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = json.load(open(f'{HERE}/annotation_schema.json'))['properties']['skill']['enum']
src = open(f'{HERE}/terra_probe.py').read(); RUB = re.search(r'^RUBRIC = """(.*?)"""', src, re.S | re.M).group(1)
skill_def = [l for l in RUB.split('\n') if l.startswith('skill:')]
HEAD = ("Label the TASK TYPE of each row below (what the row mainly teaches an assistant to do), using exactly one value from this list: " + ', '.join(SKILLS) +
        ". Definition from the rubric: " + ' '.join(skill_def) + " Do not use tools. Return ONLY one JSON object {\"rows\": [{\"id\": ..., \"skill\": ...}, ...]} with one entry per row, same ids.\n\n")
def render(r): return '\n\n'.join(f"[{t['role'].upper()}]\n{(t.get('content') or '')[:4000]}" for t in r['turns'] if (t.get('content') or '').strip())[:12000]
agree = collections.Counter(); conf = collections.Counter(); LOG = open(f'{OUT}/skill_usage.log', 'a'); cost = 0.0
for b in BLOCKS:
    lab = {}
    for l in open(f'{A}/labels/{b}.labels.jsonl'):
        j = json.loads(l)
        if j.get('skill'): lab[j['id']] = j['skill']
    ids = sorted(lab); random.Random(f'skill:{b}').shuffle(ids); want = set(ids[:N]); rows = []
    for l in open(f'{A}/core_export/{b}.jsonl'):
        if not want: break
        r = json.loads(l)
        if r['id'] in want: want.discard(r['id']); rows.append(r)
    out = open(f'{OUT}/{b}.skill.jsonl', 'w')
    for k in range(0, len(rows), 10):
        batch = rows[k:k + 10]; prompt = HEAD + '\n\n'.join(f"===== ROW {r['id']} =====\n{render(r)}" for r in batch)
        res = subprocess.run(['claude', '-p', '--model', 'claude-sonnet-5', '--output-format', 'json', '--max-turns', '2'], input=prompt, capture_output=True, text=True, timeout=900)
        try:
            j = json.loads(res.stdout); assert any(m.startswith('claude-sonnet-5') for m in (j.get('modelUsage') or {})), 'model'
            cost += j.get('total_cost_usd') or 0; txt = j.get('result') or ''; got = {str(x['id']): x['skill'] for x in json.loads(txt[txt.index('{'):txt.rindex('}') + 1])['rows']}
        except Exception as e:
            LOG.write(f"{datetime.datetime.now():%H:%M} {b} batch {k} failed {type(e).__name__}\n"); LOG.flush(); continue
        for r in batch:
            s = got.get(str(r['id'])); L = lab[r['id']]; out.write(json.dumps(dict(id=r['id'], luna=L, sonnet=s)) + '\n'); agree[(b, L == s)] += 1; conf[(b, L, s)] += 1
        LOG.write(f"{datetime.datetime.now():%H:%M} {b} {k + len(batch)}/{len(rows)} cumulative ${cost:.2f}\n"); LOG.flush()
    out.close()
    n = agree[(b, True)] + agree[(b, False)]; print(f"{b}: skill agreement {agree[(b, True)]}/{n} ({agree[(b, True)] / max(n, 1):.0%})", flush=True)
    dis = collections.Counter({(L, S): v for (bb, L, S), v in conf.items() if bb == b and L != S}).most_common(5); print('   top disagreements (luna -> sonnet):', dis, flush=True)
t = sum(agree.values()); print(f"ALL: {sum(v for (b, ok), v in agree.items() if ok)}/{t} ({sum(v for (b, ok), v in agree.items() if ok) / max(t, 1):.0%}); cost-equivalent ${cost:.2f}", flush=True)
