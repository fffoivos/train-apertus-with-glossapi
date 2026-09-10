#!/bin/bash
# After the MultiChallenge repair pass: build the review sample (30 MultiChallenge + 60 XSTest final rows), run the astra review of the two judge-based benchmarks (xhigh), log the Codex window.
cd "$(dirname "$0")"; [ -f multichallenge/conversations_el_final.jsonl ] || exit 1
~/venvs/sftdata/bin/python - <<'PY'
import json, random
rng = random.Random(11); mc = [json.loads(l) for l in open('multichallenge/conversations_el_final.jsonl')]; xs = [json.loads(l) for l in open('xstest/prompts_el_final.jsonl')]
rows = [dict(benchmark='multichallenge', id=r['id'], axis=r['axis'], excluded=r['excluded'], adapted=r['adapted'], provenance=r['provenance'], target_question_en=r['target_question_en'], target_question_el=r['target_question_el'], turns_el=r['turns_el'], turns_en_last=r['turns_en'][-1]['content']) for r in rng.sample(mc, 30)]
rows += [dict(benchmark='xstest', **{k: r[k] for k in ('id', 'type', 'label', 'prompt_en', 'prompt_el', 'trigger_el', 'transfer', 'pair_id', 'provenance')}) for r in rng.sample(xs, 60)]
with open('review_sample_judged.jsonl', 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
print('sample', len(rows))
PY
cd ..; python3 review_astra.py benchmarks_judged ../docs/reviews/briefs/astra_benchmarks_judged.md ../docs/reviews/ASTRA_benchmarks_judged_20260910.md --rows benchmarks_el/review_sample_judged.jsonl --n 90 --seed 1 > ../docs/reviews/astra_benchmarks_judged.log 2>&1
echo "REVIEW JUDGED DONE $(wc -c < ../docs/reviews/ASTRA_benchmarks_judged_20260910.md) chars" >> ../docs/reviews/astra_benchmarks_judged.log
