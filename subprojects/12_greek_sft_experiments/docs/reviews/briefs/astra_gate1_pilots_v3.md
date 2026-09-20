Review target: GATE 1 RE-REVIEW (checkpoint R3c) for the three pilot continuations 1-G4F6P0--00/--01/--02 (legacy M0/M1/M2), after your second review (docs/reviews/ASTRA_gate1_pilots_v2_20260914.md, HOLD kept for the readout only). This pack closes the BLOCKER and the two MEDIUM findings, reports what your LOW finding turned out to be (a real dataset defect, now repaired), and answers your three open questions. Judge whether the HOLD can lift; the recipe is unchanged. You have no filesystem access: everything is inlined.

Your findings -> sections: BLOCKER readout completeness -> §A (script v2, verbatim) + §B (eleven fixtures with outcomes). MEDIUM verdict hierarchy -> §A decision section. MEDIUM reporting outputs (paired intervals, adjudication coverage, exposed-item annotation, 23 vs 27 loops) -> §A + §B + §C. LOW escape corruption -> §D (mechanism, census, repair rules, rerun, audit). Open questions -> §C. Re-assembly after the repair: receipts, attestation, dry-runs, preflight -> §E.

=== §A READOUT v2 (data/pilot_summary.py, verbatim) ===
#!/usr/bin/env python3
"""Pilot readout under the frozen rule (R4 plan §4). v2 (14 Sept, astra R3b): the readout is COMPLETE only when every arm has its MATH-500-el and -en score files,
each bound to a response file holding exactly the 500 frozen ids, plus finite in-range IFEval-el and MGSM-el values; anything missing -> no arm advances; any
structurally invalid file (wrong/duplicate ids, non-string responses, out-of-range metrics) -> the readout REFUSES (exit 2). Contrast tables are descriptive
(gain, discordance, one-sided 90% bootstrap LB: 4,000 resamples, seed 1); actions appear only in the decision section after guardrails and the hierarchy
(primary M1-M0 first; M2-M1 only if the primary qualified; a failed secondary leaves M1 advancing). Guardrails (IFEval-el prompt-strict langdetect-rescored,
MGSM-el) are paired per item when per-item files exist, else the unpaired approximation is labelled as such. Loops (a content line repeated 5+ times) and
truncations use the frozen band (<= M0 + 5 of 500) and are recomputed for the reference with the same function. The one inherited MATH-500 exposure of the
parent (test/number_theory/239.json, one code row sharing a 13-gram) is annotated per arm. Usage: python3 pilot_summary.py M0 M1 [M2]
Env: PILOT_OUT (results/pilots), PILOT_RESULTS (results), PILOT_REF (results/R3_single/bench_S1), PILOT_REF_LABEL (R2_stage1_ep1)."""
import json, os, sys, random, glob, math, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE); from gfp_names import label as gfp
OUT = os.environ.get('PILOT_OUT', f'{ROOT}/results/pilots'); RES = os.environ.get('PILOT_RESULTS', f'{ROOT}/results')
REF = os.environ.get('PILOT_REF', f'{ROOT}/results/R3_single/bench_S1'); REF_LABEL = os.environ.get('PILOT_REF_LABEL', 'R2_stage1_ep1')
arms = sys.argv[1:]
if arms[:2] != ['M0', 'M1'] or (len(arms) == 3 and arms[2] != 'M2') or len(arms) not in (2, 3): raise SystemExit('arms must be M0 M1 [M2] in this order (the experiment hierarchy)')
EXPECTED = set(json.load(open(f'{ROOT}/data/benchmarks_el/math500/ids_frozen.json'))); assert len(EXPECTED) == 500, 'frozen MATH-500 id list must hold exactly 500 ids'
EXPOSED = 'test/number_theory/239.json'   # data/math/en/inherited_exposure_R2_stage1.json: one dolci code row of the parent shares a 13-gram with this item
TOL_PP = 2.0; BAND = 5; MIN_GAIN = 3.0
def refuse(msg): print(f'READOUT REFUSED: {msg}'); sys.exit(2)
def load_scores(path):
    """None when missing; refuses when invalid; binds the response file (same stem) holding exactly the frozen ids."""
    if not os.path.exists(path): return None
    sc = json.load(open(path)); ids = [r['id'] for r in sc.get('rows', [])]
    if len(ids) != len(set(ids)) or set(ids) != EXPECTED: refuse(f'{path}: expected exactly the 500 frozen MATH-500 ids, got {len(set(ids))} unique of {len(ids)} rows')
    for r in sc['rows']:
        if r.get('equiv500') not in (True, False): refuse(f'{path}: row {r["id"]} has no boolean equiv500')
    rp = path.replace('_score.json', '.jsonl')
    if not os.path.exists(rp): refuse(f'{rp} missing: scored rows without their responses')
    resp = {}
    for l in open(rp):
        if not l.strip(): continue
        r = json.loads(l)
        if r.get('id') in resp: refuse(f'{rp}: duplicate response id {r.get("id")}')
        if not isinstance(r.get('response'), str): refuse(f'{rp}: response of {r.get("id")} is not a string')
        resp[r['id']] = r
    if set(resp) != EXPECTED: refuse(f'{rp}: expected exactly the 500 frozen ids, got {len(resp)} ({len(set(resp) - EXPECTED)} unexpected, {len(EXPECTED - set(resp))} missing)')
    sc['responses'] = resp
    if not isinstance(sc.get('truncated'), int): sc['truncated'] = sum(1 for r in resp.values() if r.get('finish_reason') == 'length')
    adj = path.replace('_score.json', '_adjudicated.jsonl')   # optional Sol adjudication of unresolved rows, response-bound (data/benchmarks_el/math500/adjudicate_unresolved.py)
    if os.path.exists(adj):
        upd = {json.loads(l)['id']: json.loads(l) for l in open(adj) if l.strip()}
        for r in sc['rows']:
            u = upd.get(r['id'])
            if u and r['extracted'] in (None, '') and u.get('equivalent') is True and u.get('response_sha256') == hashlib.sha256(resp[r['id']]['response'].encode('utf-8')).hexdigest() and u.get('reference') == r['answer']: r['adjudicated'] = True
        sc['adjudication_coverage'] = dict(unresolved=sum(1 for r in sc['rows'] if r['extracted'] in (None, '')), adjudicated=sum(1 for r in sc['rows'] if r['id'] in upd), accepted=sum(1 for r in sc['rows'] if r.get('adjudicated')))
        sc['adjudicated_acc'] = sum(1 for r in sc['rows'] if r['equiv500'] or r.get('adjudicated')) / len(sc['rows'])
    return sc
def items(sc): return {r['id']: bool(r['equiv500']) for r in sc['rows']}   # PRIMARY = deterministic equiv500 (the scorer every comparator was scored with)
def loops_of(sc):
    n = 0
    for r in sc['responses'].values():
        c = collections.Counter(x.strip() for x in r['response'].splitlines() if len(x.strip()) > 12); n += any(v >= 5 for v in c.values())
    return n
def finite01(x):
    try: v = float(x)
    except Exception: return None
    return v if math.isfinite(v) and 0.0 <= v <= 1.0 else None
def ifeval(label):
    """prompt-strict (fraction in [0,1]) from results/<label>/ifeval_el_rescored.json (own file, or the multi-label file keyed by label, or results/ifeval_el_rescored.json); returns (pp, items|None)."""
    d = None
    for p in (f'{RES}/{label}/ifeval_el_rescored.json', f'{RES}/ifeval_el_rescored.json'):
        if os.path.exists(p):
            x = json.load(open(p)); d = x if 'prompt_strict' in x else x.get(label)
            if d: break
    if not d: return None, None
    v = finite01(d.get('prompt_strict'))
    if v is None: refuse(f'IFEval-el prompt_strict for {label} is not a finite fraction in [0,1]: {d.get("prompt_strict")!r}')
    it = d.get('prompt_strict_items'); it = {e['key']: bool(e['prompt_strict']) for e in it} if it else None
    return 100 * v, it
def mgsm(label):
    fs = sorted(glob.glob(f'{RES}/{label}/ilsp/**/results_*.json', recursive=True))
    if not fs: return None, None
    r = json.load(open(fs[-1])).get('results', {}).get('mgsm_greek')
    if not r: return None, None
    v = finite01(r.get('exact_match,none', r.get('exact_match,flexible-extract')))
    if v is None: refuse(f'MGSM-el exact_match for {label} is not a finite fraction in [0,1]: {r!r}')
    ss = sorted(glob.glob(f'{RES}/{label}/ilsp/**/samples_mgsm_greek*.jsonl', recursive=True)); it = None
    if ss:
        it = {}
        for l in open(ss[-1]):
            if l.strip(): x = json.loads(l); it[x['doc_id']] = bool(x.get('exact_match'))
    return 100 * v, it
def boot(a, b, n_boot=4000, seed=1):
    ids = sorted(set(a) & set(b)); d = [int(a[i]) - int(b[i]) for i in ids]
    if not d: return None
    rng = random.Random(seed); bs = sorted(sum(d[rng.randrange(len(d))] for _ in d) / len(d) for _ in range(n_boot))
    return dict(n=len(d), delta=100 * sum(d) / len(d), q=100 * sum(1 for x in d if x) / len(d), lb90=100 * bs[int(0.10 * n_boot)], lo90=100 * bs[int(0.05 * n_boot)], hi90=100 * bs[int(0.95 * n_boot) - 1])
def fmt_gate(label):
    p = f'{RES}/{label}/light_results.json'
    return json.load(open(p)).get('format_gate_dev50') if os.path.exists(p) else None
S = {a: load_scores(f'{OUT}/bench_{a}/math500_el_score.json') for a in arms}; E = {a: load_scores(f'{OUT}/bench_{a}/math500_en_score.json') for a in arms}
G = {a: dict(zip(('ifeval', 'ifeval_items'), ifeval(a + '_ep1'))) | dict(zip(('mgsm', 'mgsm_items'), mgsm(a + '_ep1'))) for a in arms}
S1 = load_scores(f'{REF}/math500_el_score.json'); E1 = load_scores(f'{REF}/math500_en_score.json'); G1 = dict(zip(('ifeval', 'ifeval_items'), ifeval(REF_LABEL))) | dict(zip(('mgsm', 'mgsm_items'), mgsm(REF_LABEL)))
missing = []
for a in arms:
    if S[a] is None: missing.append(f'{a}: MATH-500-el scores/responses')
    if E[a] is None: missing.append(f'{a}: MATH-500-en scores/responses')
    if G[a]['ifeval'] is None: missing.append(f'{a}: IFEval-el (rescored)')
    if G[a]['mgsm'] is None: missing.append(f'{a}: MGSM-el')
def f1(x): return '—' if x is None else f'{x:.1f}'
lines = ['# Pilot readout (frozen rule, plan §4; readout v2)', '', '| arm | MATH-500-el | loops (line x5) | truncated | MATH-500-en | IFEval-el prompt-strict (rescored) | MGSM-el |', '|---|---:|---:|---:|---:|---:|---:|']
if S1 and E1: lines.append(f"| G2F1P0@epoch1 (reference, recomputed) | {S1['equiv500_acc']*100:.1f} | {loops_of(S1)} | {S1['truncated']} | {E1['equiv500_acc']*100:.1f} | {f1(G1['ifeval'])} | {f1(G1['mgsm'])} |")
for a in arms:
    s, e = S[a], E[a]
    lines.append(f"| {gfp(a)} | {f1(s and s['equiv500_acc']*100)} | {loops_of(s) if s else '—'} | {s['truncated'] if s else '—'} | {f1(e and e['equiv500_acc']*100)} | {f1(G[a]['ifeval'])} | {f1(G[a]['mgsm'])} |")
lines += ['', '| contrast (descriptive) | n | gain (pp) | discordant % | one-sided 90% LB | two-sided 90% CI |', '|---|---:|---:|---:|---:|---:|']
pairs = [(arms[i + 1], arms[i]) for i in range(len(arms) - 1)]; R = {}
for x, y in pairs:
    for tag, D in (('el', S), ('en, safeguard', E)):
        r = boot(items(D[x]), items(D[y])) if D[x] and D[y] else None; R[(x, y, tag)] = r
        lines.append(f"| {x}-{y} ({tag}) | {r['n']} | {r['delta']:+.1f} | {r['q']:.1f} | {r['lb90']:+.1f} | [{r['lo90']:+.1f}, {r['hi90']:+.1f}] |" if r else f'| {x}-{y} ({tag}) | missing | | | | |')
# guardrails: evaluated per candidate vs M0 (frozen tolerances: IFEval/MGSM within 2 pp of M0, loops and truncations <= M0 + 5 of 500); paired intervals when per-item files exist
base = arms[0]; g0 = dict(ifeval=G[base]['ifeval'], mgsm=G[base]['mgsm'], loops=loops_of(S[base]) if S[base] else None, trunc=S[base]['truncated'] if S[base] else None)
def paired(a, key, ikey):
    ia, ib = G[a].get(ikey), G[base].get(ikey)
    if ia and ib and set(ia) == set(ib): r = boot(ia, ib); return f"{r['delta']:+.1f} pp, paired 90% CI [{r['lo90']:+.1f}, {r['hi90']:+.1f}] (n={r['n']})"
    return None
lines += ['', '| arm | IFEval-el vs M0 | MGSM-el vs M0 | loops vs M0 | truncated vs M0 | unresolved (no extracted answer) | format gate (dev50) | guardrails |', '|---|---:|---:|---:|---:|---:|---|---|']
elig = {}; why = {}
for a in arms:
    unres = sum(1 for r in S[a]['rows'] if r['extracted'] in (None, '')) if S[a] else None
    if a == base: lines.append(f"| {a} | — | — | {g0['loops']} | {g0['trunc']} | {unres} | {fmt_gate(a + '_ep1')} | baseline |"); continue
    gi, gm = G[a]['ifeval'], G[a]['mgsm']; gl = loops_of(S[a]) if S[a] else None; gt = S[a]['truncated'] if S[a] else None; checks = []
    if S[a] is None or E[a] is None or S[base] is None or E[base] is None: checks.append('MATH-500 el/en readout incomplete')
    if gi is None or g0['ifeval'] is None: checks.append('IFEval missing')
    elif gi - g0['ifeval'] < -TOL_PP: checks.append(f'IFEval breach ({gi - g0["ifeval"]:+.1f} pp)')
    if gm is None or g0['mgsm'] is None: checks.append('MGSM missing')
    elif gm - g0['mgsm'] < -TOL_PP: checks.append(f'MGSM breach ({gm - g0["mgsm"]:+.1f} pp)')
    if gl is None or g0['loops'] is None: checks.append('loops missing')
    elif gl > g0['loops'] + BAND: checks.append(f'loops breach ({gl} vs {g0["loops"]})')
    if gt is None or g0['trunc'] is None: checks.append('truncations missing')
    elif gt > g0['trunc'] + BAND: checks.append(f'truncation breach ({gt} vs {g0["trunc"]})')
    elig[a] = not checks; why[a] = checks
    pi, pm = paired(a, 'ifeval', 'ifeval_items'), paired(a, 'mgsm', 'mgsm_items')
    lines.append(f"| {a} | {f1(gi)} vs {f1(g0['ifeval'])}{(' · ' + pi) if pi else ' · unpaired'} | {f1(gm)} vs {f1(g0['mgsm'])}{(' · ' + pm) if pm else ' · unpaired'} | {gl} vs {g0['loops']} | {gt} vs {g0['trunc']} | {unres} | {fmt_gate(a + '_ep1')} | {'PASS' if not checks else 'FAIL: ' + '; '.join(checks)} |")
lines += ['', '## Decision (frozen rule, plan §4; hierarchical: the secondary contrast is acted on only if the primary qualifies; no arm advances by default)', '']
adv = None
if missing:
    lines.append('- **INCOMPLETE readout: no arm advances.** Missing: ' + '; '.join(missing))
else:
    r = R[('M1', 'M0', 'el')]; reasons = []
    if r['delta'] < MIN_GAIN: reasons.append(f'gain {r["delta"]:+.1f} pp < {MIN_GAIN:.0f} pp')
    if r['lb90'] <= 0: reasons.append(f'one-sided 90% LB {r["lb90"]:+.1f} pp <= 0')
    reasons += why['M1']
    if not reasons: adv = 'M1'; lines.append(f'- primary {gfp("M1")} vs {gfp("M0")}: **qualified improvement** ({r["delta"]:+.1f} pp, LB {r["lb90"]:+.1f}, guardrails PASS)')
    else: lines.append(f'- primary {gfp("M1")} vs {gfp("M0")}: **not qualified** ({"; ".join(reasons)})')
    if 'M2' in arms:
        if adv is None: lines.append(f'- secondary {gfp("M2")} vs {gfp("M1")}: not evaluated for action (hierarchy: the primary contrast did not qualify); descriptive gain {R[("M2", "M1", "el")]["delta"]:+.1f} pp')
        else:
            r2 = R[('M2', 'M1', 'el')]; reasons2 = []
            if r2['delta'] < MIN_GAIN: reasons2.append(f'gain {r2["delta"]:+.1f} pp < {MIN_GAIN:.0f} pp')
            if r2['lb90'] <= 0: reasons2.append(f'one-sided 90% LB {r2["lb90"]:+.1f} pp <= 0')
            reasons2 += why['M2']
            if not reasons2: adv = 'M2'; lines.append(f'- secondary {gfp("M2")} vs {gfp("M1")}: **qualified** ({r2["delta"]:+.1f} pp, LB {r2["lb90"]:+.1f}, guardrails PASS): the Level-5 addition advances')
            else: lines.append(f'- secondary {gfp("M2")} vs {gfp("M1")}: **not qualified** ({"; ".join(reasons2)}); the Level-5 addition is not supported and {gfp("M1")} remains the advancing arm')
lines.append(f"- advancing arm: **{gfp(adv) if adv else 'none'}**")
if adv: lines.append('- next: dose/recipe check on the advancing checkpoint before Phase C (plan §5)')
elif not missing: lines.append('- next: no continuation from this readout; write up and re-plan the maths lane (plan §4 outcome table)')
# exposed item annotation (§K)
ex = []
for name, sc in [('reference', S1)] + [(a, S[a]) for a in arms]:
    if sc: row = next((r for r in sc['rows'] if r['id'] == EXPOSED), None); ex.append(f"{name}: {'correct' if row and row['equiv500'] else 'incorrect'}")
if ex:
    lines.append(f'- inherited exposure (MATH-500 {EXPOSED}, one parent code row shares a 13-gram): ' + ', '.join(ex))
    if S['M0'] and S['M1']:
        a1, a0 = items(S['M1']), items(S['M0']); a1.pop(EXPOSED, None); a0.pop(EXPOSED, None); rr = boot(a1, a0); lines.append(f"  primary gain without that item: {rr['delta']:+.1f} pp (LB {rr['lb90']:+.1f}, n={rr['n']})")
adjs = {a: S[a].get('adjudicated_acc') for a in arms if S[a]}
if any(v is not None for v in adjs.values()):
    lines.append('- adjudicated accuracies (Sol, unresolved rows, response-bound; secondary): ' + ', '.join(f"{a} {v*100:.1f}" for a, v in adjs.items() if v is not None) + '; coverage: ' + '; '.join(f"{a} {S[a].get('adjudication_coverage')}" for a in arms if S[a] and S[a].get('adjudication_coverage')))
lines += ['', 'Uncertainty: MATH-500 contrasts are paired per item (bootstrap, 4,000 resamples, seed 1). Guardrail contrasts are paired per item when per-item files exist (shown in the table); otherwise the tolerance is applied to the point estimates and the difference is approximate (IFEval-el n=541: SE of a difference ≈ 2.9 pp at 65%; MGSM-el n=250: ≈ 4.4 pp at 50%). The 2 pp / +5-of-500 tolerances are frozen screening tolerances, not demonstrated non-inferiority. Primary scorer = equiv500 for every arm and comparator.']
os.makedirs(OUT, exist_ok=True); open(f'{OUT}/summary.md', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))

=== §B FIXTURES (data/pilot_fixtures.py, verbatim) and their output (results/pilots/readout_fixture.md) ===
#!/usr/bin/env python3
"""Fixtures for the pilot readout (astra R3b): fabricated readouts built from the stage-1 prediction files in temp dirs; each case states the expected
outcome (advancing arm, none, or refusal). Writes results/pilots/readout_fixture.md. Usage: python3 data/pilot_fixtures.py"""
import json, os, sys, shutil, subprocess, tempfile, random, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); REF = f'{ROOT}/results/R3_single/bench_S1'
def flip(sc, n_up, n_down, seed):
    rng = random.Random(seed); rows = sc['rows']; ups = [r for r in rows if not r['equiv500']]; downs = [r for r in rows if r['equiv500']]
    for r in rng.sample(ups, n_up): r['equiv500'] = True
    for r in rng.sample(downs, n_down): r['equiv500'] = False
    sc['equiv500_acc'] = sum(1 for r in rows if r['equiv500']) / len(rows); return sc
def build(case):
    d = tempfile.mkdtemp(prefix='pilot_fx_'); out = f'{d}/pilots'; res = f'{d}/results'
    el = json.load(open(f'{REF}/math500_el_score.json')); en = json.load(open(f'{REF}/math500_en_score.json')); resp_el = open(f'{REF}/math500_el.jsonl').read(); resp_en = open(f'{REF}/math500_en.jsonl').read()
    gains = case.get('gains', {'M0': (0, 0), 'M1': (21, 1), 'M2': (24, 1)}); guard = case.get('guard', {'M0': (0.60, 0.48), 'M1': (0.61, 0.49), 'M2': (0.60, 0.48)})
    for a in ('M0', 'M1', 'M2'):
        b = f'{out}/bench_{a}'; os.makedirs(b); s = flip(json.loads(json.dumps(el)), *gains[a], seed=7); json.dump(s, open(f'{b}/math500_el_score.json', 'w')); json.dump(en, open(f'{b}/math500_en_score.json', 'w'))
        open(f'{b}/math500_el.jsonl', 'w').write(resp_el); open(f'{b}/math500_en.jsonl', 'w').write(resp_en)
        gi, gm = guard[a]; lab = f'{res}/{a}_ep1'; os.makedirs(f'{lab}/ilsp/x')
        if gi is not None:
            n = 541; k = 0 if (isinstance(gi, float) and math.isnan(gi)) else round(gi * n); its = [dict(key=i, prompt_strict=i < k) for i in range(n)]
            json.dump(dict(n=n, prompt_strict=gi, prompt_strict_items=its), open(f'{lab}/ifeval_el_rescored.json', 'w'))
        if gm is not None:
            json.dump(dict(results=dict(mgsm_greek={'exact_match,none': gm})), open(f'{lab}/ilsp/x/results_1.json', 'w'))
            k = round(gm * 250); open(f'{lab}/ilsp/x/samples_mgsm_greek_1.jsonl', 'w').write(''.join(json.dumps(dict(doc_id=i, exact_match=i < k)) + '\n' for i in range(250)))
    for f in case.get('mutate', []): f(out, res)
    return d, out, res
def rm(p): os.remove(p)
def truncate_lines(p, n): open(p, 'w').write(''.join(open(p).readlines()[:n]))
def dup_line(p): ls = open(p).readlines(); open(p, 'w').write(''.join(ls + [ls[0]]))
def empty(p): open(p, 'w').write('')
CASES = [
 dict(name='A valid advancement: M1 +4 pp over M0 (guardrails present and passing), M2 +0.6 over M1', expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='B missing M0 English score file', mutate=[lambda o, r: rm(f'{o}/bench_M0/math500_en_score.json')], expect='advancing arm: **none**'),
 dict(name='C empty M1 response file (loops would read 0)', mutate=[lambda o, r: empty(f'{o}/bench_M1/math500_el.jsonl')], expect='REFUSED'),
 dict(name='D partial M1 response file (499 rows)', mutate=[lambda o, r: truncate_lines(f'{o}/bench_M1/math500_el.jsonl', 499)], expect='REFUSED'),
 dict(name='E duplicate id in M1 responses', mutate=[lambda o, r: dup_line(f'{o}/bench_M1/math500_el.jsonl')], expect='REFUSED'),
 dict(name='F NaN IFEval value for M1', guard={'M0': (0.60, 0.48), 'M1': (float('nan'), 0.49), 'M2': (0.60, 0.48)}, expect='REFUSED'),
 dict(name='G all guardrail files missing', guard={'M0': (None, None), 'M1': (None, None), 'M2': (None, None)}, expect='advancing arm: **none**'),
 dict(name='H negative primary (M1 -2 pp) with a strong secondary (M2 +8 over M1)', gains={'M0': (10, 0), 'M1': (0, 0), 'M2': (40, 0)}, expect='advancing arm: **none**'),
 dict(name='I M1 qualifies, M2 breaches IFEval (-3 pp)', guard={'M0': (0.60, 0.48), 'M1': (0.61, 0.49), 'M2': (0.57, 0.48)}, gains={'M0': (0, 0), 'M1': (21, 1), 'M2': (45, 0)}, expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='J M1 and M2 both qualify (M2 +4 over M1, guardrails pass)', gains={'M0': (0, 0), 'M1': (21, 1), 'M2': (42, 1)}, expect='advancing arm: **1-G4F6P0--02 (M2)**'),
 dict(name='K M1 gain +2 pp only (below the 3 pp floor)', gains={'M0': (0, 0), 'M1': (11, 1), 'M2': (14, 1)}, expect='advancing arm: **none**'),
]
report = ['# Readout fixtures (fabricated from the stage-1 prediction files in temp dirs; deleted after the run)', '', '| case | expected | observed | ok |', '|---|---|---|---|']; ok_all = True; caseA = ''
for c in CASES:
    d, out, res = build(c); env = dict(os.environ, PILOT_OUT=out, PILOT_RESULTS=res, PILOT_REF=REF, PILOT_REF_LABEL='R2_stage1_ep1')
    p = subprocess.run([sys.executable, f'{HERE}/pilot_summary.py', 'M0', 'M1', 'M2'], env=env, capture_output=True, text=True)
    obs = 'REFUSED' if p.returncode == 2 else (next((l.strip('- ') for l in p.stdout.splitlines() if l.startswith('- advancing arm')), f'exit {p.returncode}: {p.stderr[-200:]}'))
    ok = c['expect'] in obs; ok_all &= ok; report.append(f"| {c['name']} | {c['expect']} | {obs if p.returncode != 2 else 'REFUSED: ' + p.stdout.strip().splitlines()[-1][:120]} | {'PASS' if ok else 'FAIL'} |")
    if c['name'].startswith('A'): caseA = p.stdout
    shutil.rmtree(d)
report += ['', '## Case A output', '', caseA]; open(f'{ROOT}/results/pilots/readout_fixture.md', 'w').write('\n'.join(report) + '\n'); print('\n'.join(report[:len(CASES) + 4])); print('ALL PASS' if ok_all else 'SOME FAIL'); sys.exit(0 if ok_all else 1)

--- output ---
# Readout fixtures (fabricated from the stage-1 prediction files in temp dirs; deleted after the run)

| case | expected | observed | ok |
|---|---|---|---|
| A valid advancement: M1 +4 pp over M0 (guardrails present and passing), M2 +0.6 over M1 | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| B missing M0 English score file | advancing arm: **none** | advancing arm: **none** | PASS |
| C empty M1 response file (loops would read 0) | REFUSED | REFUSED: READOUT REFUSED: /var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/pilot_fx_o78__3d2/pilots/bench_M1/math500_el.jsonl: ex | PASS |
| D partial M1 response file (499 rows) | REFUSED | REFUSED: READOUT REFUSED: /var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/pilot_fx_1aax6s7p/pilots/bench_M1/math500_el.jsonl: ex | PASS |
| E duplicate id in M1 responses | REFUSED | REFUSED: READOUT REFUSED: /var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/pilot_fx_5pdfuekv/pilots/bench_M1/math500_el.jsonl: du | PASS |
| F NaN IFEval value for M1 | REFUSED | REFUSED: READOUT REFUSED: IFEval-el prompt_strict for M1_ep1 is not a finite fraction in [0,1]: nan | PASS |
| G all guardrail files missing | advancing arm: **none** | advancing arm: **none** | PASS |
| H negative primary (M1 -2 pp) with a strong secondary (M2 +8 over M1) | advancing arm: **none** | advancing arm: **none** | PASS |
| I M1 qualifies, M2 breaches IFEval (-3 pp) | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| J M1 and M2 both qualify (M2 +4 over M1, guardrails pass) | advancing arm: **1-G4F6P0--02 (M2)** | advancing arm: **1-G4F6P0--02 (M2)** | PASS |
| K M1 gain +2 pp only (below the 3 pp floor) | advancing arm: **none** | advancing arm: **none** | PASS |

## Case A output

# Pilot readout (frozen rule, plan §4; readout v2)

| arm | MATH-500-el | loops (line x5) | truncated | MATH-500-en | IFEval-el prompt-strict (rescored) | MGSM-el |
|---|---:|---:|---:|---:|---:|---:|
| G2F1P0@epoch1 (reference, recomputed) | 12.8 | 27 | 60 | 16.4 | — | — |
| 1-G4F6P0--00 (M0) | 12.8 | 27 | 60 | 16.4 | 60.0 | 48.0 |
| 1-G4F6P0--01 (M1) | 16.8 | 27 | 60 | 16.4 | 61.0 | 49.0 |
| 1-G4F6P0--02 (M2) | 17.4 | 27 | 60 | 16.4 | 60.0 | 48.0 |

| contrast (descriptive) | n | gain (pp) | discordant % | one-sided 90% LB | two-sided 90% CI |
|---|---:|---:|---:|---:|---:|
| M1-M0 (el) | 500 | +4.0 | 4.4 | +2.8 | [+2.6, +5.6] |
| M1-M0 (en, safeguard) | 500 | +0.0 | 0.0 | +0.0 | [+0.0, +0.0] |
| M2-M1 (el) | 500 | +0.6 | 1.0 | +0.0 | [+0.0, +1.4] |
| M2-M1 (en, safeguard) | 500 | +0.0 | 0.0 | +0.0 | [+0.0, +0.0] |

| arm | IFEval-el vs M0 | MGSM-el vs M0 | loops vs M0 | truncated vs M0 | unresolved (no extracted answer) | format gate (dev50) | guardrails |
|---|---:|---:|---:|---:|---:|---|---|
| M0 | — | — | 27 | 60 | 0 | None | baseline |
| M1 | 61.0 vs 60.0 · +0.9 pp, paired 90% CI [+0.4, +1.7] (n=541) | 49.0 vs 48.0 · +0.8 pp, paired 90% CI [+0.0, +2.0] (n=250) | 27 vs 27 | 60 vs 60 | 0 | None | PASS |
| M2 | 60.0 vs 60.0 · +0.0 pp, paired 90% CI [+0.0, +0.0] (n=541) | 48.0 vs 48.0 · +0.0 pp, paired 90% CI [+0.0, +0.0] (n=250) | 27 vs 27 | 60 vs 60 | 0 | None | PASS |

## Decision (frozen rule, plan §4; hierarchical: the secondary contrast is acted on only if the primary qualifies; no arm advances by default)

- primary 1-G4F6P0--01 (M1) vs 1-G4F6P0--00 (M0): **qualified improvement** (+4.0 pp, LB +2.8, guardrails PASS)
- secondary 1-G4F6P0--02 (M2) vs 1-G4F6P0--01 (M1): **not qualified** (gain +0.6 pp < 3 pp; one-sided 90% LB +0.0 pp <= 0); the Level-5 addition is not supported and 1-G4F6P0--01 (M1) remains the advancing arm
- advancing arm: **1-G4F6P0--01 (M1)**
- next: dose/recipe check on the advancing checkpoint before Phase C (plan §5)
- inherited exposure (MATH-500 test/number_theory/239.json, one parent code row shares a 13-gram): reference: incorrect, M0: incorrect, M1: incorrect, M2: incorrect
  primary gain without that item: +4.0 pp (LB +2.8, n=499)

Uncertainty: MATH-500 contrasts are paired per item (bootstrap, 4,000 resamples, seed 1). Guardrail contrasts are paired per item when per-item files exist (shown in the table); otherwise the tolerance is applied to the point estimates and the difference is approximate (IFEval-el n=541: SE of a difference ≈ 2.9 pp at 65%; MGSM-el n=250: ≈ 4.4 pp at 50%). The 2 pp / +5-of-500 tolerances are frozen screening tolerances, not demonstrated non-inferiority. Primary scorer = equiv500 for every arm and comparator.


=== §C ANSWERS TO YOUR OPEN QUESTIONS ===
1) 27 vs 23 loops. The 23 was a hard-coded figure from the round-three diagnosis, whose rule differed slightly (it counted lines > 12 characters after a different strip). The readout v2 no longer hard-codes anything: the reference row is recomputed from the stage-1 response file with the same function as the arms, so the fixture and the reference agree by construction (see the reference row in §B case A: the reference and the copied arms show the same loop count).
2) The exposed item is MATH-500 test/number_theory/239.json (Greek prompt); one dolci code row of the parent shares a 13-gram with it (data/math/en/inherited_exposure_R2_stage1.json). The readout v2 prints, per arm and for the reference, whether that item is correct, and the primary gain recomputed without it (§A, 'inherited exposure' lines).
3) The five rows. 10,306 exported translated rows = 8,930 paired (M0/M1) + 1,376 Level-5 (M2 extra). The arm assembler runs its own 13-gram contamination check on the RENDERED rows (prompt + target, Greek and English caches); it dropped 4 Level-5 rows, so M2 took 15441 of 15445 Greek rows vs M1 14042 of 14042 (difference 1399 = train 1385 + dev 14). These figures are from the receipts of the re-assembly after the repair (§E); the same convention applied before it (5 contaminated Level-5 rows: 1,376 - 5 = 1,371 = 1,358 + 13).

=== §D THE ESCAPE CORRUPTION (your LOW finding), REPAIRED ===
Mechanism: Sol wrote LaTeX commands inside JSON strings without doubling the backslash; JSON decoding turned '\\theta' into TAB+'heta', '\\frac' into FF+'rac', '\\neq' into LF+'eq' (pattern A: backslash + escape letter -> one control character), and in a second pattern the backslash alone became a control character with the first letter lost or kept ('\\gcd' -> BEL+'cd', '\\mathbf' -> BEL+'mathbf'). The output guard rejected only non-whitespace controls, so TAB/CR/LF-class corruption passed every judge (the judges read through it) and every format check.
Census before repair (all stored Sol outputs, not only the exports): {"prep/translations_with_reference.jsonl": {"rows": 9999, "changed": 0, "events": {"inherited": 6, "benign": 2, "unresolved": 2}}, "out/level5_problems_el.jsonl": {"rows": 2180, "changed": 0, "events": {"unresolved": 107, "inherited": 2, "benign": 1}}, "../cut1/edited/rows_edited.jsonl": {"rows": 14215, "changed": 0, "events": {"unresolved": 2}}, "out/solutions_el_repair_high.jsonl": {"rows": 220, "changed": 0, "events": {}}, "out/solutions_el_l4_high.jsonl": {"rows": 1289, "changed": 0, "events": {}}, "out/level5_solutions_el_high.jsonl": {"rows": 1493, "changed": 0, "events": {}}, "out/solutions_el.jsonl": {"rows": 9989, "changed": 0, "events": {"unresolved": 17, "benign": 28}}}
Unrepairable by rule (regenerated at high, forced): ['gsm_310', 'gsm_3230', 'gsm_3505']; retranslated: ['math5_1025', 'math5_1067', 'math5_1178', 'math5_1223', 'math5_1261', 'math5_1272', 'math5_1372', 'math5_1392', 'math5_1412', 'math5_1468', 'math5_250', 'math5_444', 'math5_469', 'math5_538', 'math5_55', 'math5_554', 'math5_630', 'math5_661', 'math5_74', 'math5_758', 'math5_765', 'math5_802', 'math5_899', 'math5_923', 'math5_970', 'math5_972', 'math_3175'].
Repair rules (data/math/cut2/repair_escapes.py, applied in place with .bak copies and an event log): a control character followed by letters is rewritten to the longest LaTeX command implied by (A) escape-letter + tail, (B) the intact tail, or (A') any-letter + tail, where the English source problem/solution must name the command whenever the dictionary is ambiguous; newline-class repairs additionally require the source to contain the command more often than the Greek text and a non-space character before the newline (a line starting with 'u = ...' is not '\\nu'); control characters inherited from the English source (tabs in Asymptote code) and control characters followed by a non-letter are kept. Changed prompts lost their fidelity and validity records (both re-run: fidelity medium -> adjudication high); changed solutions re-keyed polish and validity by hash; the guard now rejects any decoded escape (data/math/mathlib.reject_disallowed_controls). The rerun chain ends with a control-character audit of the exports that fails closed.
Rerun log (tail):
dropped 40 level-5 translations for retranslation
[09-14 19:34] rerun: level5 retranslation
retry 2 ValueError disallowed control U+001B at $.problem_el[131]
2026-09-14 19:36 cut2 level5 problems: n=14 codex 66.0 -> 66.0 (delta 0.0)
[09-14 19:36] rerun: fidelity (medium) for changed problems
cut2 fidelity_all: 11183 unique items, 0 identical duplicates collapsed, 15 to do, 48 workers
2026-09-14 19:36 cut2 fidelity_all: n=15 codex 66.0 -> 66.0 (delta 0.0)
[09-14 19:36] rerun: fidelity adjudication (high)
cut2 fidelity adjudication HIGH: 618 unique items, 0 identical duplicates collapsed, 0 to do, 48 workers
2026-09-14 19:36 cut2 fidelity adjudication HIGH: n=0 codex 66.0 -> 66.0 (delta 0.0)
[09-14 19:36] rerun: forced regeneration (high)
retry 2 ValueError disallowed control U+0001 at $.solution_el[114]
2026-09-14 19:38 cut2 repair HIGH: n=16 codex 66.0 -> 66.0 (delta 0.0)
[09-14 19:38] rerun: polish
2026-09-14 19:39 cut2 polish targets: n=17 codex 66.0 -> 66.0 (delta 0.0)
Counter({'unchanged': 8, 'edited': 8, 'failed': 1})
[09-14 19:39] rerun: validate (high)
cut2 validate: 11467 unique items, 0 identical duplicates collapsed, 17 to do, 48 workers
2026-09-14 19:40 cut2 validate: n=17 codex 66.0 -> 66.0 (delta 0.0)
[09-14 19:40] rerun: repair pass for new validity failures
cut2 repair HIGH: 1 unique items, 0 identical duplicates collapsed, 1 to do, 48 workers
2026-09-14 19:40 cut2 repair HIGH: n=1 codex 66.0 -> 66.0 (delta 0.0)
[09-14 19:40] rerun: polish 2
2026-09-14 19:40 cut2 polish targets: n=1 codex 66.0 -> 66.0 (delta 0.0)
Counter({'edited': 1})
[09-14 19:40] rerun: validate 2
cut2 validate: 11468 unique items, 0 identical duplicates collapsed, 1 to do, 48 workers
2026-09-14 19:40 cut2 validate: n=1 codex 66.0 -> 66.0 (delta 0.0)
[09-14 19:40] rerun: assemble
  "native": 47.653876272513706
 }
}
{'rows_M0': 8934, 'rows_M1': 8934, 'rows_M2_extra': 1403, 'rows_native': 5108, 'arm_M0': 14042, 'arm_M1': 14042, 'arm_M2': 15445}
[09-14 19:40] rerun: coverage ledger
{"exported_translated_rows": 10337, "fully_covered": 10337, "problems": {}, "audit_flags_adjudicated": 5, "audit_flags_total": 5, "first_stage_flagged_adjudicated": 613, "first_stage_flagged": 613, "validity_effort_counts": {"high": 10337}, "repaired_rows": 69, "polish": {"unchanged": 7370, "edited": 2955, "reverted": 12}, "severity": {"none": 10314, "minor": 23}}
[09-14 19:40] rerun: control-character audit of the exports
rows with C0 controls other than TAB/LF in the exports: 0
[09-14 19:40] rerun: RERUN_DONE

Repair script (verbatim):
#!/usr/bin/env python3
"""Repair JSON-escape corruption in stored Sol outputs (14 Sept, found by astra's gate-1 re-review: c2_math5_746 showed a tab + 'riangle').
Mechanism: the model wrote LaTeX commands inside JSON strings without doubling the backslash, so '\\theta' decoded to TAB+'heta', '\\frac' to FF+'rac',
'\\neq' to LF+'eq' (pattern A: the backslash and the first letter became one control character); a second pattern replaced only the backslash
(BEL+'mathbf' for '\\mathbf'). Repairs are rule-based and source-guided: a control character followed by letters is rewritten to the longest LaTeX
command (dictionary or a command of the English source) that the pattern implies; newline-class repairs require the command in the English source and a
non-space character before the newline (a line starting with 'u = ...' is not '\\nu'). Control characters inherited from the English source (tabs in
Asymptote code) are kept; a control character followed by a non-letter is benign whitespace and kept. Everything else is 'unresolved' and the id goes to
out/force_regen.json (solutions) / out/force_retranslate.json (problems) so the chain regenerates it.
Side effects when applied: changed problem texts drop their fidelity and validity records (both re-run); changed solutions re-key polish and validity.
Usage: python3 repair_escapes.py [--apply]   (default: dry run; writes out/escape_repairs_report.json either way)"""
import json, re, os, sys, shutil, collections, argparse, time
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = f'{HERE}/out'; PREP = f'{HERE}/prep'; CUT1 = f'{HERE}/../cut1/edited/rows_edited.jsonl'
CTRL = {'\x07': 'a', '\x08': 'b', '\x0c': 'f', '\n': 'n', '\r': 'r', '\t': 't', '\x0b': 'v'}
C0 = {chr(c) for c in range(32)} | {chr(127)}   # every other control character (NUL, DLE, ESC...) stood for a lost backslash in some outputs
DICT = set("""alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi varpi rho varrho sigma varsigma tau upsilon phi varphi chi psi omega
Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega
frac dfrac tfrac cfrac sqrt binom dbinom tbinom overline underline widehat widetilde hat bar vec dot ddot tilde acute grave breve check mathbf mathrm mathit mathsf mathtt mathcal mathbb mathfrak mathscr boldsymbol bm text textbf textit textrm textsf texttt emph
left right big Big bigg Bigg bigl bigr Bigl Bigr biggl biggr langle rangle lfloor rfloor lceil rceil lvert rvert lVert rVert vert Vert
cdot cdots ldots dots vdots ddots times div pm mp ast star circ bullet oplus ominus otimes odot cup cap setminus vee wedge land lor lnot neg
le leq ge geq ne neq equiv approx sim simeq cong propto ll gg subset subseteq supset supseteq in notin ni mid nmid parallel perp nleq ngeq nsubseteq ncong nsim nexists
to rightarrow leftarrow Rightarrow Leftarrow leftrightarrow Leftrightarrow longrightarrow Longrightarrow mapsto implies iff uparrow downarrow nearrow searrow swarrow nwarrow hookrightarrow
sum prod int iint iiint oint lim limsup liminf max min sup inf arg det gcd lcm deg dim ker hom exp log ln lg sin cos tan cot sec csc arcsin arccos arctan sinh cosh tanh coth mod bmod pmod
infty partial nabla forall exists nexists emptyset varnothing angle triangle measuredangle sphericalangle square blacksquare Box diamond Diamond prime backslash
quad qquad hspace vspace phantom hphantom vphantom smash noindent indent newline linebreak nonumber notag nobreak tag label ref eqref
begin end array matrix pmatrix bmatrix vmatrix Vmatrix cases aligned align gather split equation displaystyle textstyle scriptstyle scriptscriptstyle limits nolimits
boxed fbox mbox hbox vbox underbrace overbrace underset overset stackrel substack atop over choose cancel bcancel xcancel sout
alpha ell hbar imath jmath wp Re Im aleph top bot therefore because dagger ddagger S P copyright pounds clubsuit diamondsuit heartsuit spadesuit gcd emph cot csc sec ldots cdots dots mathop operatorname lfloor rfloor
draw fill filldraw dot label pair path real int string unitsize size pen linewidth dashed arrow Arrow EndArrow BeginArrow MidArrow rgb gray black white red blue green
""".split())
NEWLINE_CMDS = {'neq', 'ne', 'nu', 'nabla', 'not', 'notin', 'newline', 'nonumber', 'nmid', 'nleq', 'ngeq', 'nsubseteq', 'ncong', 'nsim', 'nexists', 'nearrow', 'nwarrow', 'ni', 'notag'}
def cmds(text): return collections.Counter(re.findall(r'\\([A-Za-z]+)', text or ''))
def repair(text, source_text):
    """Returns (new_text, events); events = list of dict(kind, at, old, new) with kind in repaired_A|repaired_B|repaired_N|inherited|benign|unresolved."""
    if not text: return text, []
    src = cmds(source_text); src_ctrl = set(c for c in CTRL if c != '\n' and c in (source_text or ''))
    out = []; ev = []; i = 0; n = len(text)
    while i < n:
        ch = text[i]
        if ch not in CTRL and ch not in C0: out.append(ch); i += 1; continue
        letter = CTRL.get(ch); skip = 0
        while i + 1 + skip < n and text[i + 1 + skip] == '\x00': skip += 1   # a NUL glued to the control character (BS+NUL+'eta' was '\\beta') is part of the corruption
        m = re.match(r'[A-Za-z]+', text[i + 1 + skip:i + 40 + skip]); word = m.group(0) if m else ''
        cand = None
        if ch != '\n' and not word and i + 1 + skip < n and text[i + 1 + skip] in '$%&_{}#!,;: ' and ('\\' + text[i + 1 + skip]) in (source_text or ''):   # the backslash of an escaped symbol ('\\$2') became the control character
            ev.append(dict(kind='repaired_S', at=i, old=repr(text[i:i + 2 + skip]), new='\\' + text[i + 1 + skip])); out.append('\\'); i += 1 + skip; continue
        if ch != '\n' and not word:   # the whole '\\<sym>' became the control character: the source shows '\\<sym>' followed by the same text
            nxt = text[i + 1 + skip:i + 4 + skip]; hit = [sym for sym in '$!{},;: %&_#' if nxt and ('\\' + sym + nxt) in (source_text or '')]
            if len(hit) == 1: ev.append(dict(kind='repaired_S2', at=i, old=repr(text[i:i + 1 + skip]), new='\\' + hit[0])); out.append('\\' + hit[0]); i += 1 + skip; continue
        if ch == '\n':
            if word and i > 0 and (text[i - 1].isalnum() or text[i - 1] in ')}]|$'):
                have = cmds(text)
                for k in range(len(word), 0, -1):
                    c = 'n' + word[:k]
                    if c in NEWLINE_CMDS and src.get(c, 0) > have.get(c, 0) and (k == len(word) or not word[k].isalpha()): cand = ('N', c, k); break
                if cand is None:
                    for k in range(len(word), 0, -1):   # the backslash alone became the newline: LF + 'sqrt' where the source has \\sqrt more often than the Greek text
                        c = word[:k]
                        if len(c) >= 2 and src.get(c, 0) > have.get(c, 0) and (k == len(word) or not word[k].isalpha()): cand = ('NB', c, k); break
            if cand is None: out.append(ch); i += 1; continue   # ordinary newline
        else:
            if ch in src_ctrl and word and not any(((letter or '?') + word[:k]) in DICT for k in range(len(word), 0, -1)):
                ev.append(dict(kind='inherited', at=i, old=repr(ch + word[:12]))); out.append(ch); i += 1; continue
            if not word:
                if ch == '\t': ev.append(dict(kind='benign', at=i, old=repr(text[i:i + 8]))); out.append(ch); i += 1; continue   # a tab used as spacing
                ev.append(dict(kind='unresolved', at=i, old=repr(text[i:i + 10]))); out.append(ch); i += 1; continue   # ESC sequences, NUL, DEL...: garbage output, regenerate
            A = B = None
            for k in range(len(word) if letter else 0, 0, -1):   # pattern A: '\\X' + rest -> control char + rest, X = the JSON-escape letter of the control char
                c = letter + word[:k]
                if (c in DICT or c in src) and (k == len(word) or c in src): A = ('A', c, k); break
            for k in range(len(word), 0, -1):   # pattern B: the backslash alone became the control char, the command is intact
                c = word[:k]
                if (c in DICT or c in src) and (k == len(word) or c in src): B = ('B', c, k); break
            if A and B: cand = A if (A[1] in src or B[1] not in src) else B
            else: cand = A or B
            if cand is None or (cand[1] not in src):   # pattern A': the lost first letter is any letter (BEL+'cd' = '\\gcd', FF+'ot' = '\\cot'); the source must name the command
                alts = []
                for k in range(len(word), 0, -1):
                    for Lc in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
                        c = Lc + word[:k]
                        if src.get(c, 0) > 0 and (k == len(word) or not word[k].isalpha()): alts.append(('A2', c, k))
                    if alts: break
                if len({x[1] for x in alts}) == 1: cand = alts[0]
                elif cand is None and not alts:
                    alts = [(Lc + word) for Lc in 'abcdefghijklmnopqrstuvwxyz' if (Lc + word) in DICT]
                    if len(alts) == 1: cand = ('A2', alts[0], len(word))
            if cand is None:
                ev.append(dict(kind='unresolved', at=i, old=repr(ch + word[:14]))); out.append(ch); i += 1; continue
        kind, c, k = cand; new = '\\' + c
        ev.append(dict(kind='repaired_' + kind, at=i, old=repr(text[i:i + 1 + skip] + word[:k]), new=new)); out.append(new); i += 1 + skip + k
    return ''.join(out), ev
def L(p): return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
    src = {r['id']: r for r in L(f'{PREP}/translations_with_reference.jsonl')}
    for r in L(f'{OUT}/level5_problems_el.jsonl'): src.setdefault(r['id'], r)
    report = dict(files={}, changed_problem_ids=[], changed_solution_ids=[], force_regen=[], force_retranslate=[], applied=a.apply, time=time.strftime('%Y-%m-%d %H:%M'))
    stamp = time.strftime('%Y%m%d_%H%M%S')
    def process(path, field, source_of, id_of=lambda r: r['id'], seen_ids=None):
        rows = L(path); changed = 0; stats = collections.Counter(); samples = []; changed_ids = []; unresolved_ids = []
        for r in rows:
            pid = id_of(r); text = r.get(field)
            if not text: continue
            if seen_ids is not None and pid in seen_ids: continue   # only the best (first-preference) solution per id is repaired
            new, ev = repair(text, source_of(pid, r))
            for e in ev: stats[e['kind']] += 1
            if any(e['kind'] == 'unresolved' for e in ev): unresolved_ids.append(pid)
            if new != text:
                changed += 1; changed_ids.append(pid); r[field] = new
                if len(samples) < 6: samples.append(dict(id=pid, events=[e for e in ev if e['kind'].startswith('repaired')][:4]))
            if seen_ids is not None: seen_ids.add(pid)
        report['files'][os.path.relpath(path, HERE)] = dict(rows=len(rows), changed=changed, events=dict(stats), samples=samples, unresolved_ids=unresolved_ids)
        if a.apply and changed:
            shutil.copy(path, f'{path}.bak_{stamp}')
            with open(path, 'w') as f:
                for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
        return changed_ids, unresolved_ids
    # problems (prompts)
    ch, un = process(f'{PREP}/translations_with_reference.jsonl', 'problem_el', lambda pid, r: r.get('problem_en', '')); report['changed_problem_ids'] += ch; report['force_retranslate'] += un
    ch, un = process(f'{OUT}/level5_problems_el.jsonl', 'problem_el', lambda pid, r: r.get('problem_en', '')); report['changed_problem_ids'] += ch; report['force_retranslate'] += un
    def cut1_source(pid, r):
        s = src.get(pid.replace('gm_', '', 1)) or src.get(pid) or {}; return s.get('problem_en', '')
    ch, un = process(CUT1, 'user', cut1_source, id_of=lambda r: r.get('id', '')); report['cut1_user_changed'] = ch
    # solutions: the best file per id only (preference order of run_batches.SOLUTION_FILES)
    seen = set()
    for name in ('solutions_el_repair_high.jsonl', 'solutions_el_l4_high.jsonl', 'level5_solutions_el_high.jsonl', 'solutions_el.jsonl'):
        ch, un = process(f'{OUT}/{name}', 'solution_el', lambda pid, r: (src.get(pid) or {}).get('solution_en', ''), seen_ids=seen); report['changed_solution_ids'] += ch; report['force_regen'] += un
    # polished texts: a polish 'edited' text carries the corruption of its input; re-keying handles it (the input sha changes), nothing to rewrite
    report['force_regen'] = sorted(set(report['force_regen'])); report['force_retranslate'] = sorted(set(report['force_retranslate']))
    if a.apply:
        # invalidate fidelity + validity for changed prompts (both re-run through the chain); polish/validity for changed solutions re-key by sha
        changed_p = set(report['changed_problem_ids']) | set(report['force_retranslate'])
        for name in ('fidelity_all.jsonl', 'fidelity_sample.jsonl', 'fidelity_adjudicated.jsonl', 'fidelity_audit_passes.jsonl'):
            p = f'{OUT}/{name}'; rows = L(p); keep = [r for r in rows if r['id'] not in changed_p]
            if len(keep) != len(rows): shutil.copy(p, f'{p}.bak_{stamp}'); open(p, 'w').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in keep)); report.setdefault('dropped_records', {})[name] = len(rows) - len(keep)
        p = f'{OUT}/validity.jsonl'; rows = L(p); keep = [r for r in rows if r['pid'] not in changed_p]
        if len(keep) != len(rows): shutil.copy(p, f'{p}.bak_{stamp}'); open(p, 'w').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in keep)); report.setdefault('dropped_records', {})['validity.jsonl'] = len(rows) - len(keep)
        json.dump(report['force_regen'], open(f'{OUT}/force_regen.json', 'w')); json.dump(report['force_retranslate'], open(f'{OUT}/force_retranslate.json', 'w'))
    json.dump(report, open(f'{OUT}/escape_repairs_report.json', 'w'), ensure_ascii=False, indent=1)
    for f, d in report['files'].items(): print(f"{f}: rows {d['rows']} changed {d['changed']} events {d['events']} unresolved {d['unresolved_ids'][:8]}")
    print('changed problems', len(report['changed_problem_ids']), 'changed solutions', len(report['changed_solution_ids']), 'force_regen', report['force_regen'], 'force_retranslate', report['force_retranslate'], 'applied', a.apply)
if __name__ == '__main__': main()


=== §E RE-ASSEMBLY AFTER THE REPAIR ===
Coverage summary (data/math/cut2/final/coverage_summary.json):
{
 "exported_translated_rows": 10337,
 "fully_covered": 10337,
 "problems": {},
 "audit_flags_adjudicated": 5,
 "audit_flags_total": 5,
 "first_stage_flagged_adjudicated": 613,
 "first_stage_flagged": 613,
 "validity_effort_counts": {
  "high": 10337
 },
 "repaired_rows": 69,
 "polish": {
  "unchanged": 7370,
  "edited": 2955,
  "reverted": 12
 },
 "severity": {
  "none": 10314,
  "minor": 23
 }
}
Cut-2 receipt (data/math/cut2/final/receipt.json):
{
 "inputs": {
  "source_problems": 11482,
  "fidelity_results": 11482,
  "solutions": 11483,
  "validity_results": 11695,
  "polish_results": 11736,
  "cut1_rows": 14215,
  "native": 5108
 },
 "stage_counts": {
  "translated_gsm8k:source": 6000,
  "translated_gsm8k:kept": 5737,
  "translated_math:source": 3999,
  "translated_math:kept": 3197,
  "translated_math5:source": 1483,
  "translated_math5:kept": 1403,
  "translated_gsm8k:retained_final": 5737,
  "translated_math:retained_final": 3197,
  "translated_math5:retained_final": 1403
 },
 "dropped": {
  "translated_gsm8k:unfaithful_both_stages": 75,
  "translated_gsm8k:invalid_derivation": 81,
  "translated_gsm8k:no_cut1_pair": 96,
  "translated_gsm8k:length_short": 2,
  "translated_gsm8k:repeated_lines": 9,
  "translated_math:no_cut1_pair": 647,
  "translated_math:unfaithful_both_stages": 12,
  "translated_math:invalid_derivation": 23,
  "translated_math:math500_13gram": 87,
  "translated_math:no_solution": 9,
  "translated_math:length_short": 10,
  "translated_math:boxed_not_equivalent": 9,
  "translated_math:repeated_lines": 5,
  "translated_math5:invalid_derivation": 20,
  "translated_math5:math500_13gram": 47,
  "translated_math5:no_solution": 5,
  "translated_math5:unfaithful_both_stages": 5,
  "translated_math5:repeated_lines": 3
 },
 "flags": {
  "first_stage_flagged": 618,
  "audit_flagged": 5,
  "adjudicated": 618,
  "overturned_by_high": 526,
  "polished_edited": 3210,
  "polish_reverted": 15,
  "translated_overlays_user_changed_skipped": 1,
  "M0_overlays_applied": 1,
  "translated_math5:decimal_point_outside_latex": 2,
  "translated_math5:over_400_words": 2,
  "prompt_repairs_applied": 2,
  "native_overlays_applied": 3,
  "native_overlays_unmatched": 0
 },
 "files": {
  "rows_M0": {
   "rows": 8934,
   "sha256": "97645de5f8a90632e5236f229f8201d1848eae85d072a28970042022db826fb0"
  },
  "rows_M1": {
   "rows": 8934,
   "sha256": "88edac8e3add598ceefde3c4b33d3d29f4118036c290439e3d5c404269cbb3f6"
  },
  "rows_M2_extra": {
   "rows": 1403,
   "sha256": "8d42368b17953a6b1331cadcd3f30d8b145356dc698e57f3b76f6651fbe3fbdb"
  },
  "rows_native": {
   "rows": 5108,
   "sha256": "f0b9c65fe6a0b6763c02cda5fd4fa5c57701b8b2b066be92970e515f295c5a40"
  },
  "arm_M0": {
   "rows": 14042,
   "sha256": "4f67f1e72d161ac2efd63a0b9fb104d697c219a325b4b65feef3deb7f0ce0873"
  },
  "arm_M1": {
   "rows": 14042,
   "sha256": "20a1c3b5936e5d5aec1bcde7f2b712af9bd649bcc91f6a2d30ccce47de88f73b"
  },
  "arm_M2": {
   "rows": 15445,
   "sha256": "093525b1af54ab44e7a945488e4a0559e735c3aef9befe36aade5e757474afea"
  }
 },
 "paired_ids_M0_M1": 8934,
 "dev_rows": {
  "paired": 89,
  "level5": 14,
  "native": 51,
  "english_twins_excluded": 103
 },
 "tokenizer": "apertus-tokenizer",
 "words": {
  "M0": 40.43261696888292,
  "M1": 105.81217819565704,
  "M2_extra": 157.83962936564504,
  "native": 47.653876272513706
 }
}
Arm M0 receipt: train {'rows': 71715, 'tokens': 28546834, 'supervised_tokens': 18362535, 'sha256': '5bb1772e462b3831f3dee95d4b3ef75b4a451163cdf3d01bd7c6e43bd1885ba1'} dev {'rows': 373, 'sha256': '4da3ef752436f43a8dbead6631fcf2fbe1efe3b6b45ce7e940f6e44761d5ee68'} replay {"dolci_chat": {"available": 3009, "taken": 301, "contaminated": 0}, "dolci_code_algo_20k": {"available": 5034, "taken": 503, "contaminated": 0}, "dolci_precise_if_20k": {"available": 3895, "taken": 307, "contaminated": 83}, "dolci_reasoning": {"available": 27171, "taken": 2717, "contaminated": 0}, "dolci_safety": {"available": 6194, "taken": 619, "contaminated": 0}, "dolci_science": {"available":
 blocks: [{"block": "math_en_gsm", "renderer": "openmath", "copies": 1, "available": 22211, "contaminated": 12, "taken": 22199, "dev_rows": 195, "train_unique_rows": 22004, "train_rows_effective": 22004, "tokens_unique": 4515858, "tokens_effective": 4515858, "supervised_tokens_unique": 2809001, "supervised_tokens_effective": 2809001, "content_sha256": "0480fb2683a4892d8a514daee6529f120559a3ceb6072bbf25244ce3e642fa8e"}, {"block": "math_en_math", "renderer": "openmath", "copies": 2, "available": 7328, "contaminated": 119, "taken": 7209, "dev_rows": 38, "train_unique_rows": 7171, "train_rows_effective": 14342, "tokens_unique": 2208598, "tokens_effective": 4417196, "supervised_tokens_unique": 1562186, "supervised_tokens_effective": 3124372, "content_sha256": "92c3f02cd2157cf759054c7840824fb62c049e91ffd8c8726545e01be909f2ba"}, {"block": "greek_math", "renderer": "ua", "copies": 1, "available": 14042, "taken": 14042, "dev_rows": 140, "train_unique_rows": 13902, "train_rows_effective": 13902, "tokens_unique": 3281875, "tokens_effective": 3281875, "supervised_tokens_unique": 1607561, "supervised_tokens_effective": 1607561, "content_sha256": "01cb2dc7f41f2d719a0e169b39d27d08ce26f30b1967e47ac64a4ac755d15127"}]
Arm M1 receipt: train {'rows': 71715, 'tokens': 30320475, 'supervised_tokens': 20136176, 'sha256': '0da4fc2334420d8828866beb8cfa633252b59e3044e8b44b8dc4f7cdeecb2daf'} dev {'rows': 373, 'sha256': '41b38306bb4eabbad2a505a105703a40a17249eed65f34f16f653e7fff964a37'} replay {"dolci_chat": {"available": 3009, "taken": 301, "contaminated": 0}, "dolci_code_algo_20k": {"available": 5034, "taken": 503, "contaminated": 0}, "dolci_precise_if_20k": {"available": 3895, "taken": 307, "contaminated": 83}, "dolci_reasoning": {"available": 27171, "taken": 2717, "contaminated": 0}, "dolci_safety": {"available": 6194, "taken": 619, "contaminated": 0}, "dolci_science": {"available":
 blocks: [{"block": "math_en_gsm", "renderer": "openmath", "copies": 1, "available": 22211, "contaminated": 12, "taken": 22199, "dev_rows": 195, "train_unique_rows": 22004, "train_rows_effective": 22004, "tokens_unique": 4515858, "tokens_effective": 4515858, "supervised_tokens_unique": 2809001, "supervised_tokens_effective": 2809001, "content_sha256": "0480fb2683a4892d8a514daee6529f120559a3ceb6072bbf25244ce3e642fa8e"}, {"block": "math_en_math", "renderer": "openmath", "copies": 2, "available": 7328, "contaminated": 119, "taken": 7209, "dev_rows": 38, "train_unique_rows": 7171, "train_rows_effective": 14342, "tokens_unique": 2208598, "tokens_effective": 4417196, "supervised_tokens_unique": 1562186, "supervised_tokens_effective": 3124372, "content_sha256": "92c3f02cd2157cf759054c7840824fb62c049e91ffd8c8726545e01be909f2ba"}, {"block": "greek_math", "renderer": "ua", "copies": 1, "available": 14042, "taken": 14042, "dev_rows": 140, "train_unique_rows": 13902, "train_rows_effective": 13902, "tokens_unique": 5055516, "tokens_effective": 5055516, "supervised_tokens_unique": 3381202, "supervised_tokens_effective": 3381202, "content_sha256": "d05100ee0e39dff40a7ac396055f396bdc6ac82eec162a588c76abb33083dec7"}]
Arm M2 receipt: train {'rows': 73100, 'tokens': 31340918, 'supervised_tokens': 20948218, 'sha256': '3a75d29c19859b9cd687d38f19f2966ed20a8020940b792f864c4fcb8c28c155'} dev {'rows': 387, 'sha256': '63c19aa5c0bcbd23e2c499c147114f8ee8bd00c582aa3a917c8052864b355134'} replay {"dolci_chat": {"available": 3009, "taken": 301, "contaminated": 0}, "dolci_code_algo_20k": {"available": 5034, "taken": 503, "contaminated": 0}, "dolci_precise_if_20k": {"available": 3895, "taken": 307, "contaminated": 83}, "dolci_reasoning": {"available": 27171, "taken": 2717, "contaminated": 0}, "dolci_safety": {"available": 6194, "taken": 619, "contaminated": 0}, "dolci_science": {"available":
 blocks: [{"block": "math_en_gsm", "renderer": "openmath", "copies": 1, "available": 22211, "contaminated": 12, "taken": 22199, "dev_rows": 195, "train_unique_rows": 22004, "train_rows_effective": 22004, "tokens_unique": 4515858, "tokens_effective": 4515858, "supervised_tokens_unique": 2809001, "supervised_tokens_effective": 2809001, "content_sha256": "0480fb2683a4892d8a514daee6529f120559a3ceb6072bbf25244ce3e642fa8e"}, {"block": "math_en_math", "renderer": "openmath", "copies": 2, "available": 7328, "contaminated": 119, "taken": 7209, "dev_rows": 38, "train_unique_rows": 7171, "train_rows_effective": 14342, "tokens_unique": 2208598, "tokens_effective": 4417196, "supervised_tokens_unique": 1562186, "supervised_tokens_effective": 3124372, "content_sha256": "92c3f02cd2157cf759054c7840824fb62c049e91ffd8c8726545e01be909f2ba"}, {"block": "greek_math", "renderer": "ua", "copies": 1, "available": 15445, "contaminated": 4, "taken": 15441, "dev_rows": 154, "train_unique_rows": 15287, "train_rows_effective": 15287, "tokens_unique": 6075959, "tokens_effective": 6075959, "supervised_tokens_unique": 4193244, "supervised_tokens_effective": 4193244, "content_sha256": "6a6babf8221741f0296930fd9949e118d071a427dfa0cf7a1f0dcc03927da89d"}]
Checker output (results/pilots/check_arms.log, tail):
caches: english_originals.mmlu_arc_hellaswag_truthfulqa_20260905.jsonl:28449:1fb6d835, greek_mmlu.6a03aa06b68beb932fb75edff3a34e50b3674649.jsonl:16632:52395e62, gsm8k.740312add88f781978c0658806c59bc2815b9866.jsonl:1319:12d2145d, ifbench_el.jsonl:586:607ae20f, ifeval.966cd89545d6b6acfd7638bc708b98261ca58e84.jsonl:541:e0c1fda7, math200_confirm.jsonl:400:000148d2, math500_el.jsonl:1000:e29827dc, mgsm_el.jsonl:250:b96a9dd2, multichallenge_el.jsonl:3308:72468f1e, native_asep_mcqa.jsonl:2346:f8230d12, native_demosqa.jsonl:600:3d769837, native_gpcr.jsonl:208:ae256518, native_medical_mcqa.jsonl:432:ae4f9346, xstest_el.jsonl:900:b3a910ef
M0: 71715 train rows, 28.5M tokens (18.4M supervised), ≈436 updates, greek train 13902 / dev 140, blocks {'math_en_gsm': 22004, 'replay': 21467, 'greek_math': 13902, 'math_en_math': 14342}, benchmark hits 8-gram 0 / 13-gram 0
M1: 71715 train rows, 30.3M tokens (20.1M supervised), ≈463 updates, greek train 13902 / dev 140, blocks {'math_en_gsm': 22004, 'replay': 21467, 'greek_math': 13902, 'math_en_math': 14342}, benchmark hits 8-gram 0 / 13-gram 0
M2: 73100 train rows, 31.3M tokens (20.9M supervised), ≈478 updates, greek train 15287 / dev 154, blocks {'math_en_math': 14342, 'greek_math': 15287, 'replay': 21467, 'math_en_gsm': 22004}, benchmark hits 8-gram 0 / 13-gram 0
OK: M0 and M1 carry the same 13902 Greek maths prompts (multiset)
OK: M0/M1 Greek ids are exactly paired
OK: M2 = M1 + 1385 Level-5 rows
OK: replay identical multisets across arms (21467 rows)
OK: math_en_gsm identical multisets across arms (22004 rows)
OK: math_en_math identical multisets across arms (14342 rows)
OK: Greek dev sets paired (140 problems)
OK: no English training row shares a problem with the 103 dev problems
OK: byte-level attestation {'pairs_checked': 14042, 'user_mismatch': 0, 'native_mismatch': 0, 'm1_in_m2_mismatch': 0}
RESULT PASS

Attestation (results/pilots/attestation.json):
{
 "arms": [
  "M0",
  "M1",
  "M2"
 ],
 "attestation": {
  "pairs_checked": 14042,
  "user_mismatch": 0,
  "native_mismatch": 0,
  "m1_in_m2_mismatch": 0
 },
 "manifests": {
  "M0": "5bb1772e462b3831f3dee95d4b3ef75b4a451163cdf3d01bd7c6e43bd1885ba1",
  "M1": "0da4fc2334420d8828866beb8cfa633252b59e3044e8b44b8dc4f7cdeecb2daf",
  "M2": "3a75d29c19859b9cd687d38f19f2966ed20a8020940b792f864c4fcb8c28c155"
 }
}
Dry-run M0: {"arm": "M0", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 16, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 1, "eval_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M0/dev.jsonl", "eval_rows": 373, "eval_tokens": 95760, "expected_full_train_tokens": null, "gradient_accumulation_steps": 4, "learning_rate": 1e-05, "lr_scheduler_type": "cosine_with_min_lr", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": 0.1, "model": "/iopsstor/scratch/cscs/fffoivos/sft_round1/runs/R2_stage1/epoch1", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 7331, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 459, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "M0_lr1e-5_1ep_cos", "steps_per_epoch": 459, "train_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M0/train.jsonl", "train_rows": 71715, "train_tokens": 29960812, "warmup_ratio": 0.03, "world_size": 4} -> DRY_RUN_OK
Dry-run M1: {"arm": "M1", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 16, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 1, "eval_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M1/dev.jsonl", "eval_rows": 373, "eval_tokens": 109163, "expected_full_train_tokens": null, "gradient_accumulation_steps": 4, "learning_rate": 1e-05, "lr_scheduler_type": "cosine_with_min_lr", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": 0.1, "model": "/iopsstor/scratch/cscs/fffoivos/sft_round1/runs/R2_stage1/epoch1", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 7653, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 479, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "M1_lr1e-5_1ep_cos", "steps_per_epoch": 479, "train_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M1/train.jsonl", "train_rows": 71715, "train_tokens": 31278117, "warmup_ratio": 0.03, "world_size": 4} -> DRY_RUN_OK
Dry-run M2: {"arm": "M2", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 16, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 1, "eval_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M2/dev.jsonl", "eval_rows": 387, "eval_tokens": 118829, "expected_full_train_tokens": null, "gradient_accumulation_steps": 4, "learning_rate": 1e-05, "lr_scheduler_type": "cosine_with_min_lr", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": 0.1, "model": "/iopsstor/scratch/cscs/fffoivos/sft_round1/runs/R2_stage1/epoch1", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 7878, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 493, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "M2_lr1e-5_1ep_cos", "steps_per_epoch": 493, "train_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M2/train.jsonl", "train_rows": 73100, "train_tokens": 32199143, "warmup_ratio": 0.03, "world_size": 4} -> DRY_RUN_OK
Preflight: OK

Export control-character audit: rows with C0 controls other than TAB/LF in the exports: 0
