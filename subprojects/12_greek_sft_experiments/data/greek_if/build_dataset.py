#!/usr/bin/env python3
"""Assemble the verified set: first-try answers that pass, else retry answers that pass; failures become preference pairs when a passing answer exists.
Usage: python3 build_dataset.py <prompts.jsonl> <answers.jsonl> <retry_answers.jsonl> <out_dir>
Writes greek_if_sft.jsonl (core-export schema + metadata), greek_if_dpo.jsonl (prompt, chosen, rejected), rejected_only.jsonl, summary.json"""
import collections, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import constraints as C
def main():
    prompts_path, ans_path, retry_path, out = sys.argv[1:5]; os.makedirs(out, exist_ok=True)
    rows = [json.loads(l) for l in open(prompts_path)]
    first = {json.loads(l)['id']: json.loads(l)['answer'] for l in open(ans_path)} if os.path.exists(ans_path) else {}
    retry = {json.loads(l)['id']: json.loads(l)['answer'] for l in open(retry_path)} if os.path.exists(retry_path) else {}
    sft, dpo, rej, stats = [], [], [], collections.Counter()
    for r in rows:
        cands = [(w, a) for w, a in (('first', first.get(r['id'])), ('retry', retry.get(r['id']))) if a]
        if not cands: stats['unanswered'] += 1; continue
        verdicts = {w: C.check_all(a, r['constraints'], r['request']) for w, a in cands}
        ok = {w: all(x['ok'] for x in v if x['checkable']) for w, v in verdicts.items()}
        chosen = next((w for w in ('first', 'retry') if ok.get(w)), None)
        meta = dict(constraints=[dict(family=c['family'], params=c['params'], text=c['text']) for c in r['constraints']], level=r['level'], domain=r['domain'], subtopic=r['subtopic'], form=r['form'], persona=r['persona'], persona_style=r['persona_style'], authored=r.get('authored', False))
        if chosen:
            a = dict(cands)[chosen]; stats[f'pass_{chosen}'] += 1
            sft.append(dict(source='greek_if', bucket=f"level{r['level']}", id=r['id'], user=r['prompt'], assistant=a, turns=[dict(role='user', content=r['prompt']), dict(role='assistant', content=a)], n_turns=2, verified=chosen, meta=meta))
            for w, a2 in cands:
                if not ok[w]: dpo.append(dict(id=r['id'], prompt=r['prompt'], chosen=a, rejected=a2, failed=[x['family'] for x in verdicts[w] if x['ok'] is False], meta=meta))
        else:
            stats['fail_both'] += 1; rej.append(dict(id=r['id'], prompt=r['prompt'], answers={w: a for w, a in cands}, failed={w: [x['family'] for x in verdicts[w] if x['ok'] is False] for w in verdicts}, meta=meta))
    for name, data in (('greek_if_sft.jsonl', sft), ('greek_if_dpo.jsonl', dpo), ('rejected_only.jsonl', rej)):
        with open(os.path.join(out, name), 'w') as f:
            for x in data: f.write(json.dumps(x, ensure_ascii=False) + '\n')
    by_level = collections.Counter(x['meta']['level'] for x in sft); by_form = collections.Counter(x['meta']['form'] for x in sft); fam = collections.Counter(c['family'] for x in sft for c in x['meta']['constraints'])
    summ = dict(prompts=len(rows), sft_rows=len(sft), dpo_pairs=len(dpo), rejected_only=len(rej), stats=dict(stats), by_level=dict(sorted(by_level.items())), by_form=dict(by_form), families=len(fam), min_family_rows=min(fam.values()) if fam else 0, mean_answer_words=round(sum(len(C.words(x['assistant'])) for x in sft) / max(1, len(sft))))
    json.dump(summ, open(os.path.join(out, 'summary.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))
if __name__ == '__main__': main()
