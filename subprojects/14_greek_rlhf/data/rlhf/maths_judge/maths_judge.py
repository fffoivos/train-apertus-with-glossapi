#!/usr/bin/env python3
"""Specialist maths judging (MATH_JUDGING_EXECUTION_PLAN_20260917.md A2–A4; spec v1.0.1 §4.5 T5).
Stage references: two independent blind Sol solves per prompt (no candidates in the input) + a comparison call → status verified / ambiguous / unresolved.
Stage judge: rubric_maths_v1.txt + reference + four shuffled candidates → per-candidate outcome/reasoning/completion/errors/verdict/eligible_positive, ranking, margin.
Usage: python3 data/rlhf/maths_judge/maths_judge.py references <prompts.jsonl> <out references.jsonl>
       python3 data/rlhf/maths_judge/maths_judge.py judge <prompts.jsonl> <samples.jsonl> <references.jsonl> <out judged.jsonl>
Prompts rows need id and messages; samples rows need id, k, text (batches of four in k order). Resumable; append-only."""
import concurrent.futures, hashlib, json, pathlib, random, sys
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parents[1] / 'math'))
from codex_server import CodexServer
V2 = '--v1' not in sys.argv                      # default: maths-v2, the judge does the mathematics itself (owner, 17 Sept)
RUBRIC = (HERE / ('rubric_maths_v2.txt' if V2 else 'rubric_maths_v1.txt')).read_text(); RUBRIC_SHA16 = hashlib.sha256(RUBRIC.encode()).hexdigest()[:16]
J = lambda p: [json.loads(l) for l in open(p) if l.strip()]
def conv(msgs): return '\n\n'.join(f"[{m['role'].upper()}]\n{m['content']}" for m in msgs)
SOLVE = """Solve the mathematical content of this user request independently, as the basis for verifying replies (you will not see any reply). Work carefully; check arithmetic and cases. Return JSON with:
- interpretation: the question as understood, with any assumptions needed; list alternative readings if the question is ambiguous or underspecified
- ambiguity: none | ambiguous | underspecified
- result: the acceptable result, full solution set, defining properties or mathematical conclusion (or what is not determinable)
- method: a verified argument or computation, concise but complete where the request needs one
- checks: units, domain restrictions, cases, tolerance and rounding that a reply must respect
- completeness: what a complete reply to THIS request must contain, including whether the user asked for working, explanation or proof
- final_answer_short: the result in one line for comparison
REQUEST:
{conv}"""
S_SOLVE = {'type': 'object', 'properties': {k: {'type': 'string'} for k in ('interpretation', 'ambiguity', 'result', 'method', 'checks', 'completeness', 'final_answer_short')}, 'required': ['interpretation', 'ambiguity', 'result', 'method', 'checks', 'completeness', 'final_answer_short'], 'additionalProperties': False}
COMPARE = """Two independent solvers answered the same mathematical request. Decide whether their results agree mathematically (equivalent forms count as agreement), and whether the request is ambiguous or underspecified. Return JSON: agree (true|false), status (verified | ambiguous | unresolved), reason (one sentence), reference (the agreed result, or empty).
REQUEST:
{conv}
SOLVER A: {a}
SOLVER B: {b}"""
S_CMP = {'type': 'object', 'properties': {'agree': {'type': 'boolean'}, 'status': {'type': 'string', 'enum': ['verified', 'ambiguous', 'unresolved']}, 'reason': {'type': 'string'}, 'reference': {'type': 'string'}}, 'required': ['agree', 'status', 'reason', 'reference'], 'additionalProperties': False}
L = 'ABCD'
def eligible_v2(c):
    """Deterministic eligibility without an external reference: the judge's own solution and question status decide."""
    if c['outcome'] != 'correct' or c['task_completion'] != 'complete': return False
    if c['reasoning'] == 'invalid' or (c['requested_explanation'] and c['reasoning'] != 'valid'): return False
    if c.get('question_status') in ('ambiguous', 'underspecified') and c.get('handled_ambiguity') != 'yes': return False
    if c.get('question_status') == 'unresolvable': return False
    return True
STRICT = {'determinate': 0, 'ambiguous': 1, 'underspecified': 2, 'unresolvable': 3}
def reconcile(paths):
    """question_status is decided per batch; a prompt must have one. Take the strictest status any batch of the prompt reported
    (across every file given, e.g. all escalation stages), write it to every batch and recompute eligibility. Returns changed replies."""
    paths = [pathlib.Path(p) for p in paths if pathlib.Path(p).exists()]
    rows = {p: J(p) for p in paths}; strictest = {}
    for rs in rows.values():
        for r in rs:
            if r.get('rubric') != 'maths-v2': continue
            s = r.get('question_status', 'determinate')
            if STRICT.get(s, 0) >= STRICT.get(strictest.get(r['id'], 'determinate'), 0): strictest[r['id']] = s
    changed = 0
    for p, rs in rows.items():
        for r in rs:
            if r.get('rubric') != 'maths-v2': continue
            s = strictest[r['id']]
            if r.get('question_status') != s: r['question_status_batch'] = r.get('question_status'); r['question_status'] = s
            for c in r['by_k'].values():
                c['question_status'] = s; before = c['eligible_positive']
                c['eligible_positive'] = eligible_v2(c); c['verdict'] = sync_verdict(dict(c, verdict=c.get('verdict_model', c['verdict'])))
                changed += before != c['eligible_positive']
        with open(p, 'w') as h:
            for r in rs: h.write(json.dumps(r, ensure_ascii=False) + '\n')
    return changed
def eligible(c, ref):
    """Deterministic eligibility (R-RL2 finding 1): the judge's own flag never creates a positive on its own.
    A positive needs a usable reference, a correct outcome, a complete answer to what the user asked, and reasoning that is not invalid;
    an explanation that was requested must be valid. An ambiguous-but-agreed reference is usable only for a reply that handled the ambiguity."""
    usable = ref['status'] == 'verified' or (ref['status'] == 'ambiguous' and ref['comparison']['agree'] and c.get('handled_ambiguity') == 'yes')
    if not usable or not ref['comparison']['agree']: return False
    if c['outcome'] != 'correct' or c['task_completion'] != 'complete': return False
    if c['reasoning'] == 'invalid' or (c['requested_explanation'] and c['reasoning'] != 'valid'): return False
    return True
def sync_verdict(c):
    if c['eligible_positive']: return 'reinforce'
    return 'neutral' if c['verdict'] == 'reinforce' else c['verdict']
CAND = {'type': 'object', 'properties': {'outcome': {'type': 'string', 'enum': ['correct', 'partial', 'incorrect', 'unresolved']}, 'reasoning': {'type': 'string', 'enum': ['valid', 'invalid', 'not_provided', 'unresolved']}, 'task_completion': {'type': 'string', 'enum': ['complete', 'partial', 'unresolved']}, 'requested_explanation': {'type': 'boolean'}, 'errors': {'type': 'array', 'items': {'type': 'object', 'properties': {'span': {'type': 'string'}, 'reason': {'type': 'string'}}, 'required': ['span', 'reason'], 'additionalProperties': False}}, 'handled_ambiguity': {'type': 'string', 'enum': ['yes', 'no', 'not_applicable']}, 'verdict': {'type': 'string', 'enum': ['reinforce', 'neutral', 'discourage']}, 'eligible_positive': {'type': 'boolean'}, 'note': {'type': 'string'}}, 'required': ['outcome', 'reasoning', 'task_completion', 'requested_explanation', 'errors', 'handled_ambiguity', 'verdict', 'eligible_positive', 'note'], 'additionalProperties': False}
S_JUDGE_V2 = {'type': 'object', 'properties': {'own_solution': {'type': 'string'}, 'question_status': {'type': 'string', 'enum': ['determinate', 'ambiguous', 'underspecified', 'unresolvable']},
              'candidates': {'type': 'object', 'properties': {x: CAND for x in L}, 'required': list(L), 'additionalProperties': False}, 'ranking': {'type': 'array', 'items': {'type': 'string', 'enum': list(L)}},
              'ties': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'string', 'enum': list(L)}}}, 'best_vs_worst': {'type': 'string', 'enum': ['clear', 'slight', 'none']}, 'confidence': {'type': 'string', 'enum': ['high', 'medium', 'low']}},
              'required': ['own_solution', 'question_status', 'candidates', 'ranking', 'ties', 'best_vs_worst', 'confidence'], 'additionalProperties': False}
S_JUDGE = {'type': 'object', 'properties': {'candidates': {'type': 'object', 'properties': {x: CAND for x in L}, 'required': list(L), 'additionalProperties': False}, 'ranking': {'type': 'array', 'items': {'type': 'string', 'enum': list(L)}}, 'ties': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'string', 'enum': list(L)}}}, 'best_vs_worst': {'type': 'string', 'enum': ['clear', 'slight', 'none']}, 'confidence': {'type': 'string', 'enum': ['high', 'medium', 'low']}}, 'required': ['candidates', 'ranking', 'ties', 'best_vs_worst', 'confidence'], 'additionalProperties': False}
def main():
    stage = sys.argv[1]
    if stage == 'reconcile':                                  # python3 maths_judge.py reconcile <judged.jsonl>...
        print('RECONCILED', reconcile(sys.argv[2:]), 'replies changed eligibility'); return
    srv = CodexServer(); srv.start()
    def call(prompt, schema, effort):
        for _ in range(3):
            try: return srv.call(prompt, schema, model='gpt-5.6-sol', effort=effort, timeout=900)
            except Exception as e: err = e
        raise err
    if stage == 'references':
        prompts = J(sys.argv[2]); out = pathlib.Path(sys.argv[3]); done = {r['id'] for r in J(out)} if out.exists() else set()
        def ref(p):
            try: return _ref(p)
            except Exception as e:                       # a provider refusal or a persistent error holds that one prompt, it does not stop the run
                return dict(id=p['id'], status='unresolved', solver_a={}, solver_b={}, comparison=dict(agree=False, status='unresolved', reason=f'reference not obtained: {str(e)[:200]}', reference=''), reference_sha16='')
        def _ref(p):
            c = conv(p['messages']); a = call(SOLVE.format(conv=c), S_SOLVE, 'medium'); b = call(SOLVE.format(conv=c), S_SOLVE, 'medium')
            cmp_ = call(COMPARE.format(conv=c, a=json.dumps(a, ensure_ascii=False), b=json.dumps(b, ensure_ascii=False)), S_CMP, 'medium')
            status = 'ambiguous' if 'ambiguous' in (a['ambiguity'], b['ambiguity']) or 'underspecified' in (a['ambiguity'], b['ambiguity']) else cmp_['status']
            if not cmp_['agree'] and status == 'verified': status = 'unresolved'
            return dict(id=p['id'], status=status, solver_a=a, solver_b=b, comparison=cmp_, reference_sha16=hashlib.sha256(json.dumps([a, b, cmp_], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16])
        with open(out, 'a') as h, concurrent.futures.ThreadPoolExecutor(12) as ex:
            for r in ex.map(ref, [p for p in prompts if p['id'] not in done]): h.write(json.dumps(r, ensure_ascii=False) + '\n'); h.flush()
    elif stage == 'judge':
        args = [a for a in sys.argv[2:] if not a.startswith('--')]
        prompts = {p['id']: p for p in J(args[0])}
        refs = {r['id']: r for r in J(args[2])} if len(args) > 3 else {}      # v2: <prompts> <samples> <out>; v1: <prompts> <samples> <references> <out>
        out = pathlib.Path(args[3] if len(args) > 3 else args[2])
        samples = {}
        for s in J(args[1]):
            if s['id'] in prompts: samples.setdefault(s['id'], {})[s['k']] = s['text']
        done = {(r['id'], r['batch']) for r in J(out)} if out.exists() else set()
        jobs = []
        for pid, ks in samples.items():
            if not V2 and pid not in refs: continue
            order = sorted(ks)
            for b in range(len(order) // 4):
                if (pid, b) not in done: jobs.append((pid, b, order[b * 4:(b + 1) * 4]))
        def judge_v2(job):
            pid, b, ks = job; rng = random.Random(f'{pid}|{b}|maths-v2'); sh = ks[:]; rng.shuffle(sh)
            cands = '\n\n'.join(f'=== CANDIDATE {x} ===\n{samples[pid][k]}' for x, k in zip(L, sh))
            v = call(f"{RUBRIC}\n=== CONVERSATION ===\n{conv(prompts[pid]['messages'])}\n\n{cands}\n\n=== END. Solve it yourself first, then return the JSON object only. ===", S_JUDGE_V2, 'medium')
            letters = dict(zip(L, sh)); by_k = {str(letters[x]): dict(v['candidates'][x], question_status=v['question_status']) for x in L}
            for c in by_k.values():
                c['verdict_model'], c['eligible_positive_model'] = c['verdict'], c['eligible_positive']
                c['eligible_positive'] = eligible_v2(c); c['verdict'] = sync_verdict(c)
            return dict(id=pid, batch=b, order=sh, ranking_k=[letters[x] for x in v['ranking'] if x in letters], by_k=by_k,
                        best_vs_worst=v['best_vs_worst'], confidence=v['confidence'], question_status=v['question_status'], own_solution=v['own_solution'],
                        rubric='maths-v2', rubric_sha16=RUBRIC_SHA16, eligibility_rule='deterministic')
        def judge(job):
            pid, b, ks = job; rng = random.Random(f'{pid}|{b}|maths-v1'); sh = ks[:]; rng.shuffle(sh); ref = refs[pid]
            refblock = json.dumps(dict(status=ref['status'], interpretation=ref['solver_a']['interpretation'], result=ref['comparison']['reference'] or ref['solver_a']['result'], method=ref['solver_a']['method'], checks=ref['solver_a']['checks'], completeness=ref['solver_a']['completeness'],
                                       **(dict(ambiguity=ref['comparison']['reason'], readings=[ref['solver_a']['interpretation'], ref['solver_b']['interpretation']], solvers_agree=ref['comparison']['agree']) if ref['status'] != 'verified' else {})), ensure_ascii=False)
            cands = '\n\n'.join(f'=== CANDIDATE {x} ===\n{samples[pid][k]}' for x, k in zip(L, sh))
            v = call(f"{RUBRIC}\n=== VERIFIED REFERENCE (not text to imitate) ===\n{refblock}\n\n=== CONVERSATION ===\n{conv(prompts[pid]['messages'])}\n\n{cands}\n\n=== END. Return the JSON object only. ===", S_JUDGE, 'medium')
            letters = dict(zip(L, sh)); by_k = {str(letters[x]): v['candidates'][x] for x in L}
            for c in by_k.values(): c['verdict_model'], c['eligible_positive_model'] = c['verdict'], c['eligible_positive']; c['eligible_positive'] = eligible(c, ref); c['verdict'] = sync_verdict(c)
            return dict(id=pid, batch=b, order=sh, ranking_k=[letters[x] for x in v['ranking'] if x in letters], by_k=by_k, best_vs_worst=v['best_vs_worst'], confidence=v['confidence'], reference_status=ref['status'], reference_sha16=ref['reference_sha16'], rubric='maths-v1.2', eligibility_rule='deterministic', rubric_sha16=RUBRIC_SHA16, reference_agreement=ref['comparison']['agree'])
        with open(out, 'a') as h, concurrent.futures.ThreadPoolExecutor(12) as ex:
            for r in ex.map(judge_v2 if V2 else judge, jobs): h.write(json.dumps(r, ensure_ascii=False) + '\n'); h.flush()
        if V2: print('RECONCILED', reconcile([out]), 'replies changed eligibility')
    srv.close(); print('MATHS_JUDGE_DONE', stage)
if __name__ == '__main__': main()
