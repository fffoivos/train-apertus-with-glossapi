#!/usr/bin/env python3
"""Content-overlap check (astra HIGH 3 / R7, the inspectable part): every benchmark item (English source AND Greek translation) against every local SFT set
(IF final, math cut1, conversation suite, personality, and the natural-greek-sft exports if present) with normalised 8-gram overlap; an item is flagged
if > 50% of its 8-grams occur in one training row (Tülu 3 rule) or if any 13-gram matches. Reports flagged items and the remaining denominator per benchmark.
Exposure via the CPT corpus and via prior model selection are NOT covered here (recorded in the manifest as unchecked). Usage: python3 decontam.py"""
import glob, json, os, re, sys, unicodedata, collections
HERE = os.path.dirname(os.path.abspath(__file__))
SETS = {'greek_if_final': os.path.join(HERE, '..', 'greek_if', 'final', 'greek_if_sft.jsonl'), 'math_cut1': os.path.join(HERE, '..', 'math', 'cut1', 'edited', 'rows_edited.jsonl'),
        'convskills_pilot': os.path.join(HERE, '..', 'convskills', 'v1', 'rows_all.jsonl'), 'personality': os.path.join(HERE, '..', 'personality', 'personality_rows_20260906.jsonl')}
SETS.update({f'ngsft_{os.path.basename(p)}': p for p in glob.glob(os.path.expanduser('~/Projects/natural-greek-sft/data/exports/*.jsonl'))})


def norm(s): return re.sub(r'[^\w ]', ' ', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode() if False else re.sub(r'[̀-ͯ]', '', unicodedata.normalize('NFD', s)).lower())
def grams(s, n): w = norm(s).split(); return {' '.join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def texts_of(row):
    out = []
    for k in ('user', 'assistant', 'prompt', 'problem', 'problem_el', 'question', 'text'):
        if isinstance(row.get(k), str): out.append(row[k])
    for m in row.get('turns') or []: out.append(m.get('content', ''))
    return out


def main():
    index8 = collections.defaultdict(set); index13 = set(); sizes = {}
    for name, path in SETS.items():
        if not os.path.exists(path): print('skip (absent)', name); continue
        n = 0
        for l in open(path):
            try: row = json.loads(l)
            except Exception: continue
            n += 1
            for t in texts_of(row):
                for g in grams(t, 8): index8[g].add((name, n))
                index13 |= grams(t, 13)
        sizes[name] = n; print('indexed', name, n, flush=True)
    benches = {'math500': ('math500/problems_el.jsonl', ['problem_en', 'problem_el']), 'xstest': ('xstest/prompts_el.jsonl', ['prompt_en', 'prompt_el']),
               'ifbench': ('ifbench/prompts_el.jsonl', ['prompt_en', 'prompt_el']), 'multichallenge': ('multichallenge/conversations_el.jsonl', ['turns_en', 'turns_el'])}
    report = {}
    for b, (path, fields) in benches.items():
        p = os.path.join(HERE, path)
        if not os.path.exists(p): print('no file yet', b); continue
        rows = [json.loads(l) for l in open(p)]; flagged = []
        for r in rows:
            for f in fields:
                v = r.get(f); txt = ' '.join(m['content'] for m in v) if isinstance(v, list) else (v or '')
                g8 = grams(txt, 8)
                if not g8: continue
                hits = collections.Counter(src for g in g8 for src in index8.get(g, ()))
                worst = max(hits.values(), default=0) / len(g8); g13 = grams(txt, 13) & index13
                if worst > 0.5 or g13: flagged.append(dict(id=r['id'], field=f, share8=round(worst, 3), n13=len(g13), source=max(hits, key=hits.get)[0] if hits else None))
        report[b] = dict(items=len(rows), flagged=len({x['id'] for x in flagged}), remaining=len(rows) - len({x['id'] for x in flagged}), details=flagged[:50])
        print(b, 'items', len(rows), 'flagged', len({x['id'] for x in flagged}), flush=True)
    json.dump(dict(training_sets=sizes, rule='flag if >50% of an item\'s normalised 8-grams occur in one training row, or any 13-gram matches; CPT corpus and selection exposure NOT checked', benchmarks=report), open(os.path.join(HERE, 'decontam_report.json'), 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__': main()
