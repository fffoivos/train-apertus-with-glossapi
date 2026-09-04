#!/usr/bin/env python3
"""Brute-force checker for the Dolci/allenai zebra puzzles (5 houses). Usage: python3 zebra_check.py <rows.jsonl> [labels.json]
Parses attribute lists and templated clues, solves by backtracking, compares the dataset's final answer."""
import json, re, sys, itertools
ORD = {'first': 0, 'second': 1, 'third': 2, 'fourth': 3, 'fifth': 4}
ALIAS = {'brit': ['brit', 'british'], 'dane': ['dane', 'danish'], 'german': ['german'], 'mexican': ['mexican'], 'chinese': ['chinese'],
         'swede': ['swede', 'swedish'], 'norwegian': ['norwegian']}

def parse(text):
    attrs = {}
    for m in re.finditer(r'^ - (.+?): (.+)$', text, re.M):
        vals = [v.strip(' `') for v in re.split(r', ', m.group(2))]
        vals = [re.sub(r'^`|`$', '', v).strip().lower() for v in vals]
        attrs[m.group(1).strip()] = vals
    clues = re.findall(r'^\d+\. (.+)$', text, re.M)
    return attrs, clues

def entity(phrase, attrs):
    p = phrase.lower()
    child_ctx = ('child is named' in p) or ('mother of' in p)
    hits = []
    for a, vals in attrs.items():
        is_child = 'child' in a.lower()
        if child_ctx != is_child and any(v in p for v in vals) and 'name' in a.lower(): continue  # names vs child names by context
        for v in vals:
            forms = ALIAS.get(v, [v])
            if any(re.search(r'\b' + re.escape(f) + r'(s|es)?\b', p) for f in forms): hits.append((a, v))
    # prefer the longest value match (e.g. 'boba tea' over 'tea')
    hits.sort(key=lambda h: -len(h[1]))
    return hits[0] if hits else None

def parse_clue(c, attrs):
    c = c.strip().rstrip('.')
    pats = [
     (r'^(.+?) is in the (first|second|third|fourth|fifth) house$', 'pos'),
     (r'^(.+?) is directly left of (.+)$', 'dleft'),
     (r'^(.+?) is directly right of (.+)$', 'dright'),
     (r'^(.+?) is somewhere to the left of (.+)$', 'sleft'),
     (r'^(.+?) is somewhere to the right of (.+)$', 'sright'),
     (r'^(.+?) and (.+?) are next to each other$', 'adj'),
     (r'^There is one house between (.+?) and (.+)$', 'gap1'),
     (r'^There are two houses between (.+?) and (.+)$', 'gap2'),
     (r'^(.+?) is not in the (first|second|third|fourth|fifth) house$', 'notpos'),
    ]
    m_same = None
    if ' is ' in c and not re.search(r' is (directly|somewhere|not in|in the) ', c, re.I):
        parts = c.split(' is ')
        for k in range(1, len(parts)):
            e1, e2 = entity(' is '.join(parts[:k]), attrs), entity(' is '.join(parts[k:]), attrs)
            if e1 and e2 and e1 != e2: m_same = ('same', e1, e2); break
    for rx, kind in pats:
        m = re.match(rx, c, re.I)
        if not m: continue
        if kind in ('dleft', 'dright', 'sleft', 'sright', 'adj', 'gap1', 'gap2', 'pos', 'notpos') and m_same and kind in ('pos', 'notpos') and False: pass
        if kind in ('pos', 'notpos'):
            e = entity(m.group(1), attrs); return (kind, e, ORD[m.group(2).lower()]) if e else None
        e1, e2 = entity(m.group(1), attrs), entity(m.group(2), attrs)
        if not e1 or not e2 or e1 == e2: return m_same
        return (kind, e1, e2)
    return m_same

def solve(attrs, cons):
    names = list(attrs); n = 5
    def pos(assign, e): return assign[e[0]].index(e[1])
    def ok(assign):
        for k, *args in cons:
            es = [a for a in args if isinstance(a, tuple)]
            if any(e[0] not in assign for e in es): continue
            if k == 'pos':
                if pos(assign, args[0]) != args[1]: return False
            elif k == 'notpos':
                if pos(assign, args[0]) == args[1]: return False
            else:
                p1, p2 = pos(assign, args[0]), pos(assign, args[1])
                if k == 'same' and p1 != p2: return False
                if k == 'dleft' and p1 + 1 != p2: return False
                if k == 'dright' and p1 - 1 != p2: return False
                if k == 'sleft' and not p1 < p2: return False
                if k == 'sright' and not p1 > p2: return False
                if k == 'adj' and abs(p1 - p2) != 1: return False
                if k == 'gap1' and abs(p1 - p2) != 2: return False
                if k == 'gap2' and abs(p1 - p2) != 3: return False
        return True
    sols = []
    def rec(i, assign):
        if len(sols) > 1: return
        if i == len(names): sols.append(dict(assign)); return
        for perm in itertools.permutations(attrs[names[i]]):
            assign[names[i]] = list(perm)
            if ok(assign): rec(i + 1, assign)
            del assign[names[i]]
    rec(0, {}); return sols

rows = [json.loads(l) for l in open(sys.argv[1])]
labels = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
stats = dict(total=0, parsed=0, unique=0, agree=0, disagree=0, unparsed=0, multi=0); out = []
for i, r in enumerate(rows):
    text = r['user']; stats['total'] += 1
    ms = re.search(r'sort these words in (ascending|descending) order.*?list: (.+?)\s*$', text, re.S)
    if ms and 'houses' not in text:
        words = [w.strip() for w in ms.group(2).strip().rstrip('.').split(',')]
        truth = sorted(words, reverse=(ms.group(1) == 'descending'))
        given = [w.strip().strip('*`') for w in r['assistant'].strip().split('\n')[-1].split(',')]
        stats['sort_total'] = stats.get('sort_total', 0) + 1
        if given == truth: stats['sort_agree'] = stats.get('sort_agree', 0) + 1; out.append((i, 'agree sort'))
        else: stats['sort_wrong'] = stats.get('sort_wrong', 0) + 1; out.append((i, f'DISAGREE sort truth={truth} given={given}'))
        continue
    attrs, clues = parse(text)
    m = re.search(r'What is (.+?) of the person who lives in House (\d)', text)
    if not attrs or not clues or not m: stats['unparsed'] += 1; out.append((i, 'unparsed-question')); continue
    cons = [parse_clue(c, attrs) for c in clues]
    if any(c is None for c in cons):
        stats['unparsed'] += 1; out.append((i, 'unparsed-clue: ' + '; '.join(cl for cl, cc in zip(clues, cons) if cc is None)[:120])); continue
    stats['parsed'] += 1
    sols = solve(attrs, cons)
    if len(sols) != 1: stats['multi'] += 1; out.append((i, f'{len(sols)} solutions')); continue
    stats['unique'] += 1
    qattr = m.group(1).strip(); house = int(m.group(2)) - 1
    key = next((a for a in attrs if qattr.lower() in a.lower() or a.lower() in qattr.lower()), list(attrs)[0])
    truth = sols[0][key][house]
    ans = r['assistant'].strip().lower()
    given = ans.split()[-1].strip('*.`"\'') if ans else ''
    if truth in ans.split('\n')[-1].lower() or truth == given or truth in ans[-40:].lower(): stats['agree'] += 1; verdict = 'agree'
    else: stats['disagree'] += 1; verdict = f'DISAGREE truth={truth} given_tail={ans[-40:]!r}'
    luna = f" luna_q={labels[i].get('quality')}" if labels else ''
    out.append((i, verdict + luna))
print(stats)
for i, v in out:
    if 'agree' != v.split()[0] or (labels and labels[i].get('quality') == 1): print(i, v)
