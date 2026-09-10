#!/usr/bin/env python3
"""Judge calibration for MultiChallenge-el (astra HIGH 2): for a stratified sample of conversations Sol writes (a) a fluent Greek response that satisfies the
target question and (b) a fluent one that violates it in exactly one way; the judge scores both; report false-fail (a judged NO) and false-pass (b judged YES)
rates per axis and per rubric language. Stage 1: python3 calibrate.py make [N per axis=10]  → constructed.jsonl; Stage 2: python3 judge.py constructed.jsonl judged.jsonl [--rubric en|el];
Stage 3: python3 calibrate.py report judged.jsonl"""
import json, os, random, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
SCHEMA = B.M.write_schema('s_mccal.json', {"type": "object", "properties": {"passing": {"type": "string"}, "failing": {"type": "string"}, "violation": {"type": "string"}}, "required": ["passing", "failing", "violation"], "additionalProperties": False})


def make(n_per_axis):
    rows = B.load(os.path.join(HERE, 'conversations_el.jsonl')); rng = random.Random(7); by = collections.defaultdict(list)
    for r in rows:
        if not r['nontransferable']: by[r['axis']].append(r)
    sample = [r for ax in sorted(by) for r in rng.sample(by[ax], min(n_per_axis, len(by[ax])))]
    def one(r):
        conv = '\n\n'.join(f"{'ΧΡΗΣΤΗΣ' if m['role'] == 'user' else 'ΒΟΗΘΟΣ'}: {m['content']}" for m in r['turns_el'])
        prompt = ("Είσαι συγγραφέας υλικού ΒΑΘΜΟΝΟΜΗΣΗΣ κριτή. Δίνεται μια συζήτηση χρήστη-βοηθού στα ελληνικά και το κριτήριο με το οποίο θα κριθεί η ΕΠΟΜΕΝΗ απάντηση του βοηθού. Γράψε ΔΥΟ υποψήφιες επόμενες απαντήσεις, και οι δύο άψογα φυσικά ελληνικά, ίδιο μήκος και ύφος, πλήρεις και βοηθητικές:\n"
                  "passing = ικανοποιεί το κριτήριο· failing = παραβιάζει το κριτήριο με ΕΝΑΝ ΜΟΝΟ, διακριτικό τρόπο (π.χ. ξεχνά την οδηγία, αγνοεί το γεγονός που ειπώθηκε νωρίτερα, αλλάζει τη θέση του, χάνει μία προηγούμενη αλλαγή) ενώ κατά τα άλλα είναι εξίσου καλή· στο violation γράψε σε μία πρόταση ΤΙ ακριβώς παραβιάζει.\n"
                  f"Άξονας: {r['axis']}.\nΚΡΙΤΗΡΙΟ: {r['target_question_el']}\n(αγγλικά: {r['target_question_en']})\n\nΣΥΖΗΤΗΣΗ:\n{conv}\n\nΕπίστρεψε JSON {{\"passing\",\"failing\",\"violation\"}}.")
        j = B.sol_json(prompt, SCHEMA, effort='high', timeout=1200)
        return None if not j else dict(id=r['id'], axis=r['axis'], passing=j['passing'], failing=j['failing'], violation=j['violation'])
    out = B.run_jobs(sample, one, os.path.join(HERE, 'constructed_pairs.jsonl'), stage='mc calibration pairs')
    with open(os.path.join(HERE, 'constructed.jsonl'), 'w') as f:
        for r in B.load(os.path.join(HERE, 'constructed_pairs.jsonl')):
            f.write(json.dumps(dict(id=r['id'], response=r['passing'], expected=True, pair=r['id']), ensure_ascii=False) + '\n'); f.write(json.dumps(dict(id=r['id'], response=r['failing'], expected=False, pair=r['id'], violation=r['violation']), ensure_ascii=False) + '\n')
    print('constructed.jsonl:', 2 * len(B.load(os.path.join(HERE, 'constructed_pairs.jsonl'))), 'responses')


def report(path):
    rows = B.load(path); by = collections.defaultdict(lambda: dict(ff=0, fp=0, n_pass=0, n_fail=0))
    for r in rows:
        k = by[r['axis']]
        if r['expected']: k['n_pass'] += 1; k['ff'] += (not r['passed'])
        else: k['n_fail'] += 1; k['fp'] += r['passed']
    tot = dict(n=len(rows), false_fail=round(sum(k['ff'] for k in by.values()) / max(1, sum(k['n_pass'] for k in by.values())), 3), false_pass=round(sum(k['fp'] for k in by.values()) / max(1, sum(k['n_fail'] for k in by.values())), 3), judge=rows[0].get('judge_model'), rubric=rows[0].get('rubric'))
    print(json.dumps(dict(total=tot, by_axis={a: dict(false_fail=f"{k['ff']}/{k['n_pass']}", false_pass=f"{k['fp']}/{k['n_fail']}") for a, k in by.items()}), ensure_ascii=False))
    json.dump(dict(total=tot, by_axis=dict(by)), open(os.path.join(HERE, 'calibration_summary.json'), 'w'), indent=1)


if __name__ == '__main__':
    if sys.argv[1] == 'make': make(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    else: report(sys.argv[2])
