#!/bin/bash
# After the IFBench re-assembly (marker file ifbench/ASSEMBLED_V2): build the review sample (40 IFBench + 50 MATH-500 final rows) and run the astra review of the two programmatic benchmarks (xhigh).
cd "$(dirname "$0")"; until [ -f ifbench/ASSEMBLED_V2 ]; do sleep 30; done
~/venvs/sftdata/bin/python - <<'PY'
import json, random
rng = random.Random(12); ib = [json.loads(l) for l in open('ifbench/prompts_el_final.jsonl')]; m5 = [json.loads(l) for l in open('math500/problems_el_final.jsonl')]
rows = [dict(benchmark='ifbench', **{k: r[k] for k in ('id', 'prompt_en', 'prompt_el', 'instruction_id_list', 'kwargs', 'kwargs_en', 'overlap_class', 'transfer', 'adapted')}) for r in rng.sample(ib, 40)]
rows += [dict(benchmark='math500', **{k: r[k] for k in ('id', 'problem_en', 'problem_el', 'answer', 'subject', 'level', 'checks', 'provenance', 'template_sibling_in_sft')}) for r in rng.sample(m5, 50)]
with open('review_sample_programmatic.jsonl', 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
print('sample', len(rows))
PY
cd ..; python3 review_astra.py benchmarks_programmatic ../docs/reviews/briefs/astra_benchmarks_programmatic.md ../docs/reviews/ASTRA_benchmarks_programmatic_20260910.md --rows benchmarks_el/review_sample_programmatic.jsonl --n 90 --seed 1 > ../docs/reviews/astra_benchmarks_programmatic.log 2>&1
echo "REVIEW PROGRAMMATIC DONE $(wc -c < ../docs/reviews/ASTRA_benchmarks_programmatic_20260910.md) chars" >> ../docs/reviews/astra_benchmarks_programmatic.log
