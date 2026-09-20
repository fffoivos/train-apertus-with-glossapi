#!/usr/bin/env python3
"""Native Greek suite (8 multiple-choice benchmarks, the frozen clean_examples.jsonl) under the INSTRUCT-ADAPTED protocol (plan §9c): the item inside the
model's own chat template as a user turn (question, lettered choices, one instruction line), letters Α/Β/Γ/Δ ranked by summed log-probability at the start
of the assistant turn. Reuses the Scorer class of greekmmlu_official.py verbatim (fp32, one GPU). Existing letter prefixes in choices ("Α. …", "α. …") are
stripped so labels are not doubled. Usage: python native_chat.py --examples clean_examples.jsonl --model LABEL=/path --output out.json [--benchmarks a,b] [--limit N]"""
import argparse, json, re, collections, sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greekmmlu_official import Scorer, LABELS, INSTRUCTION_EL, sha
LEAD = re.compile(r'^\s*(?:[ΑΒΓΔαβγδA-Da-d])\s*[.)]\s+')
SUBJECT_EL = {'demosqa': 'συμβουλευτικής', 'medical_mcqa': 'Ιατρικής', 'asep_mcqa': 'δημόσιας διοίκησης και δικαίου', 'gpcr': 'ελληνικής πραγματικότητας', 'oyxoy_nli': 'λογικής συνεπαγωγής', 'oyxoy_wsd_definition': 'σημασίας λέξεων', 'oyxoy_wic': 'σημασίας λέξεων', 'oyxoy_metaphor': 'μεταφορικής χρήσης'}
def prompt_for(tokenizer, r):
    choices = [LEAD.sub('', str(c)) for c in r['choices']]
    body = f"Αυτό είναι μια ερώτηση {SUBJECT_EL.get(r['benchmark'], 'γενικών γνώσεων')}. Επίλεξε τη σωστή απάντηση!\n\nΕρώτηση: {r['question']}\n" + "\n".join(f"{LABELS[i]}. {c}" for i, c in enumerate(choices)) + f"\n\n{INSTRUCTION_EL}"
    return tokenizer.apply_chat_template([{"role": "user", "content": body}], tokenize=False, add_generation_prompt=True), len(choices)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--examples', type=Path, required=True); ap.add_argument('--model', required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--benchmarks', default=''); ap.add_argument('--limit', type=int, default=None); ap.add_argument('--max-input-tokens', type=int, default=3072); ap.add_argument('--candidate-batch-size', type=int, default=16); a = ap.parse_args()
    if a.output.exists(): raise FileExistsError(a.output)   # the .partial.json next to it is the resume point
    label, path = a.model.split('=', 1); model_path = Path(path); want = set(a.benchmarks.split(',')) if a.benchmarks else None
    rows = [json.loads(l) for l in open(a.examples, encoding='utf-8') if l.strip()]; rows = [r for r in rows if (not want or r['benchmark'] in want) and 2 <= len(r['choices']) <= 4]
    if a.limit: rows = rows[:a.limit]
    scorer = Scorer(model_path, a.max_input_tokens, a.candidate_batch_size); out = []; by = collections.defaultdict(lambda: [0, 0])
    # benchmark by benchmark, smallest first, with a partial save after each one and resume from saved partials (14 Sept: a 2-hour walltime cut lost a whole run)
    order = ['gpcr', 'medical_mcqa', 'demosqa', 'asep_mcqa', 'oyxoy_metaphor', 'oyxoy_nli', 'oyxoy_wsd_definition', 'oyxoy_wic']
    groups = {b: [r for r in rows if r['benchmark'] == b] for b in order if any(r['benchmark'] == b for r in rows)}
    part_path = a.output.with_suffix('.partial.json'); done = {}
    if part_path.exists():
        prev = json.loads(part_path.read_text(encoding='utf-8')); done = prev.get('by_benchmark_rows', {}); print('resuming with', list(done), flush=True)
    B = 512
    for bname, brows in groups.items():
        if bname in done:
            for r in done[bname]: out.append(r); by[bname][0] += r['correct']; by[bname][1] += 1
            continue
        brow_out = []
        for start in range(0, len(brows), B):
            chunk = brows[start:start + B]; cands = []; spans = []
            for r in chunk:
                p, n = prompt_for(scorer.tokenizer, r); s0 = len(cands); cands.extend(scorer.tokenize(p, lab) for lab in LABELS[:n]); spans.append((s0, len(cands)))
            scores = []
            for s in range(0, len(cands), a.candidate_batch_size): scores.extend(scorer.score_batch(cands[s:s + a.candidate_batch_size]))
            for r, (s0, s1) in zip(chunk, spans):
                sc = scores[s0:s1]; pred = max(range(len(sc)), key=lambda i: sc[i]['sum_logprob']); ok = pred == int(r['answer_index'])
                by[bname][0] += ok; by[bname][1] += 1; brow_out.append(dict(example_id=r['example_id'], benchmark=bname, answer_index=int(r['answer_index']), pred_index=pred, correct=ok))
        out.extend(brow_out); done[bname] = brow_out
        part_path.write_text(json.dumps(dict(model_label=label, by_benchmark_rows=done, accuracy_by_benchmark={b: round(v[0] / v[1], 4) for b, v in by.items()}), ensure_ascii=False) + '\n', encoding='utf-8')
        print(json.dumps(dict(done=bname, n=len(brow_out), acc=round(by[bname][0] / by[bname][1], 4))), flush=True)
    acc = {b: round(v[0] / v[1], 4) for b, v in sorted(by.items())}; payload = dict(schema_version='native_greek_chat_instructed_v1', model_label=label, model_path=str(model_path), examples=str(a.examples), examples_sha256=sha(a.examples), protocol='chat_instructed (letters, summed log-prob, own chat template, fp32)', items=len(out), accuracy_by_benchmark=acc, macro=round(sum(acc.values()) / len(acc), 4), rows=out)
    a.output.write_text(json.dumps(payload, ensure_ascii=False) + '\n', encoding='utf-8'); print(json.dumps(dict(model=label, items=len(out), accuracy_by_benchmark=acc, macro=payload['macro'])), flush=True)
if __name__ == '__main__': main()
