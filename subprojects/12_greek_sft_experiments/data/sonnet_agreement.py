#!/usr/bin/env python3
"""Agreement between Luna's dispositions and the Sonnet 5 double check (data/sonnet_check.py output).
Usage: python3 data/sonnet_agreement.py <check_dir> [out.md]"""
import json, sys, os, glob, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from identity_patterns import identity_phrase_hit
D = sys.argv[1]; OUTMD = sys.argv[2] if len(sys.argv) > 2 else None; A = os.path.expanduser('~/sft_annot'); lines = []
def kappa(pairs):
    n = len(pairs); cats = sorted({a for a, b in pairs} | {b for a, b in pairs}); po = sum(a == b for a, b in pairs) / n
    pa = collections.Counter(a for a, b in pairs); pb = collections.Counter(b for a, b in pairs); pe = sum(pa[c] * pb[c] for c in cats) / (n * n)
    return po, (po - pe) / (1 - pe) if pe < 1 else 0.0
tot_pairs = []
for f in sorted(glob.glob(f'{D}/*.jsonl')):
    b = os.path.basename(f)[:-6]; rows = [json.loads(l) for l in open(f)]; rows = [r for r in rows if r.get('sonnet') in ('keep', 'adapt', 'drop')]
    if not rows: continue
    conf = collections.Counter((r['luna'], r['sonnet']) for r in rows); pairs = [(r['luna'], r['sonnet']) for r in rows]; tot_pairs += pairs
    po, k = kappa(pairs); lines.append(f"\n### {b} — {len(rows)} rows judged by Sonnet 5, agreement {po:.0%}, kappa {k:.2f}\n")
    lines.append("| Luna said | Sonnet keep | Sonnet adapt | Sonnet drop | n | Sonnet agrees |"); lines.append("|---|---|---|---|---|---|")
    for l in ('keep', 'adapt', 'drop'):
        n = sum(v for (a, s), v in conf.items() if a == l)
        if n: lines.append(f"| {l} | {conf[(l,'keep')]} | {conf[(l,'adapt')]} | {conf[(l,'drop')]} | {n} | {conf[(l,l)]/n:.0%} |")
    # mannerism flags: Luna vs Sonnet (needs Luna's labels)
    lab = {}
    for l in open(f'{A}/labels/{b}.labels.jsonl'):
        j = json.loads(l); lab[j['id']] = j
    mm = collections.Counter((bool(lab.get(r['id'], {}).get('mannerism')), bool(r.get('s_mannerism'))) for r in rows if r['id'] in lab)
    lf = mm[(True, True)] + mm[(True, False)]; ln = mm[(False, True)] + mm[(False, False)]
    if lf or ln: lines.append(f"\nMannerism flags: Luna flagged {lf} of these rows, Sonnet agrees on {mm[(True,True)]} ({mm[(True,True)]/lf:.0%} of Luna's flags); Luna unflagged {ln}, Sonnet flags {mm[(False,True)]} of those ({mm[(False,True)]/ln:.0%}).\n")
    refused = sum(1 for l in open(f) if json.loads(l).get('sonnet') == 'REFUSED')
    if refused: lines.append(f"Sonnet refused {refused} rows (safeguards); excluded above.\n")
    # Luna drops: identity phrase present or not, vs Sonnet
    ids = {r['id']: r for r in rows if r['luna'] == 'drop'}
    if ids and os.path.exists(f'{A}/core_export/{b}.jsonl'):
        lab = {}
        for l in open(f'{A}/labels/{b}.labels.jsonl'):
            j = json.loads(l)
            if j['id'] in ids: lab[j['id']] = j
        split = collections.Counter()
        for l in open(f'{A}/core_export/{b}.jsonl'):
            j = json.loads(l)
            if j['id'] in ids:
                ph = identity_phrase_hit([dict(role=t['role'], content=t.get('content')) for t in j['turns']]); fr = lab.get(j['id'], {}).get('frame_type')
                split[('identity' if fr == 'identity' else 'other', 'phrase' if ph else 'no phrase', ids[j['id']]['sonnet'])] += 1
        lines.append("\nLuna's drops by Luna frame and self-description phrase in the text, with Sonnet's verdict:\n")
        lines.append("| Luna frame | phrase | Sonnet keep | Sonnet adapt | Sonnet drop |"); lines.append("|---|---|---|---|---|")
        for fr in ('identity', 'other'):
            for ph in ('phrase', 'no phrase'):
                n = sum(v for k2, v in split.items() if k2[:2] == (fr, ph))
                if n: lines.append(f"| {fr} | {ph} | {split[(fr,ph,'keep')]} | {split[(fr,ph,'adapt')]} | {split[(fr,ph,'drop')]} |")
if tot_pairs:
    po, k = kappa(tot_pairs); lines.insert(0, f"# Luna × Sonnet 5 double check\n\nAll blocks: {len(tot_pairs)} rows, agreement {po:.0%}, kappa {k:.2f}. Sonnet judged under the full rubric v3 with a 12,000/24,000-character window; Luna's verdicts came from the light rubric (v3 for OpenAssistant) with 3,000/9,000.\n")
txt = '\n'.join(lines); print(txt)
if OUTMD: open(OUTMD, 'w').write(txt + '\n')
