#!/usr/bin/env python3
"""Write every DPO01 training pair to one markdown file: prompt, reinforced reply, rejected reply.

Source of truth is data/rlhf/dpo01/provenance.jsonl, which carries the texts AND the provenance
(purpose, language, round, source alias, which sampled reply each side was, which judgement produced
the pair, and the train/dev split). Nothing is truncated: this is the record of what we trained on.

  python3 docs/build_pairs_doc.py [out.md]
"""
import collections, hashlib, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'docs' / 'DPO01_TRAINING_PAIRS_20260918.md')
SRC = ROOT / 'data' / 'rlhf' / 'dpo01' / 'provenance.jsonl'

def text(v):
    """prompt/chosen/rejected are either a string or a message list."""
    if isinstance(v, str):
        return v
    return '\n\n'.join(f"**{m.get('role','?')}:** {m.get('content','')}" for m in v)

def quote(s):
    """Blockquote, so the reply's own markdown cannot break the document's structure."""
    s = (s or '').replace('\r\n', '\n').strip()
    return '\n'.join('> ' + l if l.strip() else '>' for l in s.split('\n')) or '> *(empty)*'

def words(s):
    return len(text(s).split())

rows = [json.loads(l) for l in open(SRC, encoding='utf-8')]

# provenance carries chosen/rejected and every label, but the PROMPT lives in train/dev.jsonl.
# Join on the chosen text, which matches 397/397 exactly.
def flat(v):
    return v if isinstance(v, str) else ' '.join(m.get('content', '') for m in v)
prompts = {}
for fn in ('train.jsonl', 'dev.jsonl'):
    for l in open(ROOT / 'data/rlhf/dpo01' / fn, encoding='utf-8'):
        d = json.loads(l)
        prompts[flat(d['chosen'])] = d['prompt']
missing = 0
for r in rows:
    pr = prompts.get(flat(r['chosen']))
    if pr is None:
        missing += 1
    r['prompt'] = pr if pr is not None else '*(prompt not recovered)*'
if missing:
    print(f'WARNING: {missing} of {len(rows)} pairs could not be joined to a prompt', file=sys.stderr)
man = json.loads((ROOT / 'data/rlhf/dpo01/manifest.json').read_text())

by_purpose = collections.defaultdict(list)
for r in rows:
    by_purpose[r.get('purpose', 'unknown')].append(r)

# ------------------------------------------------------------------ header
n = len(rows)
splits = collections.Counter(r.get('split', '?') for r in rows)
langs = collections.Counter(r.get('language', '?') for r in rows)
rounds = collections.Counter(r.get('round', '?') for r in rows)
shorter = sum(1 for r in rows if words(r['chosen']) < words(r['rejected']))

doc = [f"""# DPO01 training pairs: every prompt, reinforced reply and rejected reply

The complete set of **{n} preference pairs** used to train the DPO01 arms on 18 September 2026 —
the data behind every arm in `G4F6P1--DPO01`. Nothing is truncated or sampled; this is the record.

| | |
|---|---|
| pairs | **{n}** ({splits.get('train', 0)} train, {splits.get('dev', 0)} dev) |
| by purpose | {', '.join(f'{k} {len(v)}' for k, v in sorted(by_purpose.items(), key=lambda kv: -len(kv[1])))} |
| by language | {', '.join(f'{k} {v}' for k, v in langs.most_common())} |
| by round | {', '.join(f'{k} {v}' for k, v in rounds.most_common())} |
| maths | excluded ({man['maths_excluded']} pairs dropped); round 1 excluded ({man['round1_excluded']}) |
| export | `data/rlhf/dpo01/provenance.jsonl`, frozen {man['created_utc'][:19]}Z |

**How a pair was made.** For each prompt the parent model sampled up to 32 replies. A judge ranked
them in batches of four under rubric v2.4. Within one judged batch the top-ranked *reinforce* reply
became the chosen side and the lowest *non-reinforce* reply became the rejected side, requiring a
clear margin and distinct texts. `chosen_k` and `rejected_k` below are which sampled replies those
were.

**A property worth knowing before reading.** The chosen reply is *shorter* than the rejected one in
**{shorter} of {n} pairs ({shorter/n:.0%})**. A rule that ignores content entirely and simply picks
the shorter reply scores 0.611 on the 54-pair dev set, against 0.643 for the best trained arm. The
skew is concentrated in everyday and safety prompts; instruction-following pairs are balanced. This
is the strongest single regularity in the data and it is not the one we intended to teach.

---
"""]

# ------------------------------------------------------------------ body
for purpose in sorted(by_purpose, key=lambda k: -len(by_purpose[k])):
    group = by_purpose[purpose]
    sh = sum(1 for r in group if words(r['chosen']) < words(r['rejected']))
    doc.append(f"\n## {purpose} — {len(group)} pairs\n")
    doc.append(f"*Chosen shorter than rejected in {sh}/{len(group)} ({sh/len(group):.0%}).*\n")
    for i, r in enumerate(sorted(group, key=lambda r: (r.get('split', ''), r.get('logical_id', ''))), 1):
        pid = r.get('logical_id') or r.get('group_key') or f'{purpose}-{i}'
        bits = [f"`{r.get('split','?')}`", r.get('language', '?'), r.get('round', '?')]
        if r.get('alias'):
            bits.append(f"`{r['alias']}`")
        if r.get('embedded_maths'):
            bits.append('embedded maths')
        doc.append(f"\n### {purpose} {i}/{len(group)} — {pid}\n")
        doc.append(f"{' · '.join(bits)} · chosen was sample k={r.get('chosen_k','?')}, "
                   f"rejected k={r.get('rejected_k','?')} · "
                   f"{words(r['chosen'])} vs {words(r['rejected'])} words\n")
        doc.append(f"\n**Prompt**\n\n{quote(text(r['prompt']))}\n")
        doc.append(f"\n**Reinforced (chosen)**\n\n{quote(text(r['chosen']))}\n")
        doc.append(f"\n**Rejected**\n\n{quote(text(r['rejected']))}\n")

body = ''.join(doc)
OUT.write_text(body, encoding='utf-8')
print(f"wrote {OUT}")
print(f"  {n} pairs, {len(body):,} chars, {len(body.encode()):,} bytes")
print(f"  sha256 {hashlib.sha256(body.encode()).hexdigest()[:16]}")
for k, v in sorted(by_purpose.items(), key=lambda kv: -len(kv[1])):
    print(f"  {k:<12} {len(v):>4}")
