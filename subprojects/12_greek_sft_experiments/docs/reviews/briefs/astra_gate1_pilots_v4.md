Review target: GATE 1 RE-REVIEW (checkpoint R3d) for the pilot continuations 1-G4F6P0--00/--01/--02 (legacy M0/M1/M2), after your third review (docs/reviews/ASTRA_gate1_pilots_v3_20260914.md, HOLD for F1-F3 with F4-F6 logged). Nothing in the recipe or the datasets changed since R3c; this pack closes F1-F6 and answers your five open questions. Judge whether the HOLD lifts. No filesystem access: everything is inlined.

Map: F1 truncation/accuracy trust -> §A (readout v3: recomputed from validated responses; cached disagreement refuses) + §B fixtures L, M, N. F2 binding -> §A (scorer v2 records per-row and file SHA-256; readout recomputes and refuses; guardrail items validated for uniqueness, boolean type, completeness, agreement with the aggregate; MGSM run identity = one results file + samples from the same directory) + fixtures O, R, W, X. F3 escape closure -> §C (export audit bound to export hashes; every row re-run through the repair rules against its source, TAB/LF classes included; ambiguity now unresolved and measured on the pre-repair backups: 0 events; cut-1 unresolved ids tracked). F4 -> §B (fixture D asserts 499 rows; boundary cases M, P, Q, U; gain-at-floor-but-LB<=0 case S; float tolerance 1e-9). F5 -> §A adjudication coverage in validated categories + fixtures V, V2. F6 -> §D (trainer-side SHA-256 = receipts; token-convention note).

=== §A READOUT v3 (data/pilot_summary.py, verbatim) ===
#!/usr/bin/env python3
"""Pilot readout under the frozen rule (R4 plan §4). v3 (14 Sept, astra R3c).
Completeness: every arm needs both MATH-500 score files, each BOUND to its response file (scorer v2 records per-row and file SHA-256; the readout recomputes
and refuses any mismatch), holding exactly the 500 frozen ids; truncations and accuracy are recomputed from the validated rows and must agree with the
cached values; IFEval-el and MGSM-el values must be finite fractions and, when per-item files exist, the items must be unique, boolean, complete and agree
with the aggregate (run identity: one results file, samples from the same directory). Anything missing -> no arm advances; anything structurally invalid or
self-contradictory -> the readout REFUSES (exit 2). Contrast tables are descriptive (gain, discordance, one-sided 90% bootstrap LB: 4,000 resamples,
seed 1); actions appear only in the decision section after guardrails and the hierarchy (primary M1-M0 first; M2-M1 only if the primary qualified; a failed
secondary leaves M1 advancing). Guardrails: IFEval-el prompt-strict (langdetect-rescored) and MGSM-el within 2 pp of M0 (exact boundary passes; tolerance
1e-9 on the pp scale), loops (a content line repeated 5+ times) and truncations <= M0 + 5 of 500 (boundary passes). English MATH-500 and the dev50 format
gate are REPORTED, not gated (frozen rule). The inherited MATH-500 exposure of the parent (test/number_theory/239.json) is annotated per arm with the
primary and secondary gains recomputed without it. Adjudication (Sol, unresolved rows, response-bound) is secondary and its coverage is reported in
validated categories. Usage: python3 pilot_summary.py M0 M1 [M2]
Env: PILOT_OUT (results/pilots), PILOT_RESULTS (results), PILOT_REF (results/R3_single/bench_S1, historical scorer v1: unbound, noted), PILOT_REF_LABEL."""
import json, os, sys, random, glob, math, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE); from gfp_names import label as gfp
OUT = os.environ.get('PILOT_OUT', f'{ROOT}/results/pilots'); RES = os.environ.get('PILOT_RESULTS', f'{ROOT}/results')
REF = os.environ.get('PILOT_REF', f'{ROOT}/results/R3_single/bench_S1'); REF_LABEL = os.environ.get('PILOT_REF_LABEL', 'R2_stage1_ep1')
arms = sys.argv[1:]
if arms[:2] != ['M0', 'M1'] or (len(arms) == 3 and arms[2] != 'M2') or len(arms) not in (2, 3): raise SystemExit('arms must be M0 M1 [M2] in this order (the experiment hierarchy)')
EXPECTED = set(json.load(open(f'{ROOT}/data/benchmarks_el/math500/ids_frozen.json'))); assert len(EXPECTED) == 500, 'frozen MATH-500 id list must hold exactly 500 ids'
EXPOSED = 'test/number_theory/239.json'; TOL_PP = 2.0; BAND = 5; MIN_GAIN = 3.0; EPS = 1e-9; N_IFEVAL = 541; N_MGSM = 250
def refuse(msg): print(f'READOUT REFUSED: {msg}'); sys.exit(2)
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def load_scores(path, allow_unbound=False):
    """None when missing; refuses when invalid or unbound; recomputes truncations/accuracy from the validated rows and binds them to the response file."""
    if not os.path.exists(path): return None
    sc = json.load(open(path)); rows = sc.get('rows') or []; ids = [r.get('id') for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != EXPECTED: refuse(f'{path}: expected exactly the 500 frozen MATH-500 ids, got {len(set(ids))} unique of {len(ids)} rows')
    for r in rows:
        if type(r.get('equiv500')) is not bool: refuse(f'{path}: row {r["id"]} equiv500 is not a boolean')
        if 'extracted' not in r or 'answer' not in r: refuse(f'{path}: row {r["id"]} lacks extracted/answer')
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
    bound = 'responses_sha256' in sc and all('response_sha256' in r for r in rows)
    if bound:
        if sc['responses_sha256'] != hashlib.sha256(open(rp, 'rb').read()).hexdigest(): refuse(f'{path}: responses_sha256 does not match {rp} (rescore the responses)')
        for r in rows:
            if r['response_sha256'] != sha(resp[r['id']]['response']): refuse(f'{path}: row {r["id"]} response hash mismatch (rescore)')
    elif not allow_unbound: refuse(f'{path}: score file not bound to its responses (scorer v1); rescore with score_math500.py v2')
    sc['bound'] = bound; sc['responses'] = resp
    trunc = sum(1 for r in resp.values() if r.get('finish_reason') == 'length')
    if 'truncated' in sc and (type(sc['truncated']) is not int or sc['truncated'] != trunc): refuse(f'{path}: cached truncated={sc.get("truncated")!r} disagrees with the responses ({trunc} finish_reason=length)')
    sc['truncated'] = trunc
    acc = sum(1 for r in rows if r['equiv500']) / len(rows)
    if sc.get('equiv500_acc') is None or abs(float(sc['equiv500_acc']) - acc) > 1e-4 + EPS: refuse(f'{path}: cached equiv500_acc={sc.get("equiv500_acc")!r} disagrees with the rows ({acc:.4f})')
    sc['equiv500_acc'] = acc
    adj = path.replace('_score.json', '_adjudicated.jsonl')   # optional Sol adjudication of unresolved rows (data/benchmarks_el/math500/adjudicate_unresolved.py), response-bound
    if os.path.exists(adj):
        upd = {}
        for l in open(adj):
            if not l.strip(): continue
            u = json.loads(l)
            if u.get('id') in upd: refuse(f'{adj}: duplicate adjudication id {u.get("id")}')
            upd[u['id']] = u
        unresolved = {r['id'] for r in rows if r['extracted'] in (None, '')}; byid = {r['id']: r for r in rows}
        cov = collections.Counter(unresolved=len(unresolved), attempts_on_unresolved=len(set(upd) & unresolved), attempts_on_resolved_rows=len(set(upd) - unresolved), stale_or_unbound=0, valid_negative=0, accepted_positive=0)
        for i, u in upd.items():
            if i not in unresolved: continue
            ok = u.get('response_sha256') == sha(resp[i]['response']) and u.get('reference') == byid[i]['answer']
            if not ok: cov['stale_or_unbound'] += 1; continue
            if u.get('equivalent') is True: byid[i]['adjudicated'] = True; cov['accepted_positive'] += 1
            else: cov['valid_negative'] += 1
        sc['adjudication_coverage'] = dict(cov); sc['adjudicated_acc'] = sum(1 for r in rows if r['equiv500'] or r.get('adjudicated')) / len(rows)
    return sc
def items(sc): return {r['id']: r['equiv500'] for r in sc['rows']}   # PRIMARY = deterministic equiv500 (the scorer every comparator was scored with)
def loops_of(sc):
    n = 0
    for r in sc['responses'].values():
        c = collections.Counter(x.strip() for x in r['response'].splitlines() if len(x.strip()) > 12); n += any(v >= 5 for v in c.values())
    return n
def finite01(x):
    try: v = float(x)
    except Exception: return None
    return v if math.isfinite(v) and 0.0 <= v <= 1.0 else None
def check_items(name, it, n_expected, aggregate, tol):
    """it: list of (key, value). Unique keys, complete, boolean, agreeing with the aggregate."""
    d = {}
    for k, v in it:
        if k in d: refuse(f'{name}: duplicate item key {k!r}')
        if type(v) is not bool: refuse(f'{name}: item {k!r} is not boolean')
        d[k] = v
    if len(d) != n_expected: refuse(f'{name}: {len(d)} items, expected {n_expected}')
    if abs(sum(d.values()) / len(d) - aggregate) > tol + EPS: refuse(f'{name}: items mean {sum(d.values()) / len(d):.5f} disagrees with the aggregate {aggregate:.5f}')
    return d
def ifeval(label):
    """prompt-strict fraction from results/<label>/ifeval_el_rescored.json (own file, or the multi-label file keyed by label); returns (pp, items|None)."""
    d = None
    for p in (f'{RES}/{label}/ifeval_el_rescored.json', f'{RES}/ifeval_el_rescored.json'):
        if os.path.exists(p):
            x = json.load(open(p)); d = x if 'prompt_strict' in x else x.get(label)
            if d: break
    if not d: return None, None
    v = finite01(d.get('prompt_strict'))
    if v is None: refuse(f'IFEval-el prompt_strict for {label} is not a finite fraction in [0,1]: {d.get("prompt_strict")!r}')
    it = d.get('prompt_strict_items')
    if it: it = check_items(f'IFEval-el items {label}', [(e.get('key'), e.get('prompt_strict')) for e in it], int(d.get('n') or N_IFEVAL), v, 0.5e-4)   # prompt_strict is stored rounded to 4 decimals
    return 100 * v, it
def mgsm(label):
    fs = sorted(glob.glob(f'{RES}/{label}/ilsp/**/results_*.json', recursive=True))
    if not fs: return None, None
    if len(fs) > 1: refuse(f'MGSM-el {label}: {len(fs)} results files (ambiguous run identity): {fs}')
    r = json.load(open(fs[0])).get('results', {}).get('mgsm_greek')
    if not r: return None, None
    v = finite01(r.get('exact_match,none', r.get('exact_match,flexible-extract')))
    if v is None: refuse(f'MGSM-el exact_match for {label} is not a finite fraction in [0,1]: {r!r}')
    ss = sorted(glob.glob(os.path.join(os.path.dirname(fs[0]), 'samples_mgsm_greek*.jsonl'))); it = None
    if len(ss) > 1: refuse(f'MGSM-el {label}: {len(ss)} sample files next to the results file')
    if ss:
        raw = [json.loads(l) for l in open(ss[0]) if l.strip()]
        it = check_items(f'MGSM-el items {label}', [(x.get('doc_id'), x.get('exact_match')) for x in raw], N_MGSM, v, 1e-6)
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
S1 = load_scores(f'{REF}/math500_el_score.json', allow_unbound=True); E1 = load_scores(f'{REF}/math500_en_score.json', allow_unbound=True)
G1 = dict(zip(('ifeval', 'ifeval_items'), ifeval(REF_LABEL))) | dict(zip(('mgsm', 'mgsm_items'), mgsm(REF_LABEL)))
missing = []
for a in arms:
    if S[a] is None: missing.append(f'{a}: MATH-500-el scores/responses')
    if E[a] is None: missing.append(f'{a}: MATH-500-en scores/responses')
    if G[a]['ifeval'] is None: missing.append(f'{a}: IFEval-el (rescored)')
    if G[a]['mgsm'] is None: missing.append(f'{a}: MGSM-el')
def f1(x): return '—' if x is None else f'{x:.1f}'
lines = ['# Pilot readout (frozen rule, plan §4; readout v3)', '', '| arm | MATH-500-el | loops (line x5) | truncated | MATH-500-en (reported) | IFEval-el prompt-strict (rescored) | MGSM-el |', '|---|---:|---:|---:|---:|---:|---:|']
if S1 and E1: lines.append(f"| G2F1P0@epoch1 (reference, recomputed{'' if S1['bound'] else '; scorer v1, unbound'}) | {S1['equiv500_acc']*100:.1f} | {loops_of(S1)} | {S1['truncated']} | {E1['equiv500_acc']*100:.1f} | {f1(G1['ifeval'])} | {f1(G1['mgsm'])} |")
for a in arms:
    s, e = S[a], E[a]
    lines.append(f"| {gfp(a)} | {f1(s and s['equiv500_acc']*100)} | {loops_of(s) if s else '—'} | {s['truncated'] if s else '—'} | {f1(e and e['equiv500_acc']*100)} | {f1(G[a]['ifeval'])} | {f1(G[a]['mgsm'])} |")
lines += ['', '| contrast (descriptive) | n | gain (pp) | discordant % | one-sided 90% LB | two-sided 90% CI |', '|---|---:|---:|---:|---:|---:|']
pairs = [(arms[i + 1], arms[i]) for i in range(len(arms) - 1)]; R = {}
for x, y in pairs:
    for tag, D in (('el', S), ('en, reported', E)):
        r = boot(items(D[x]), items(D[y])) if D[x] and D[y] else None; R[(x, y, tag)] = r
        lines.append(f"| {x}-{y} ({tag}) | {r['n']} | {r['delta']:+.1f} | {r['q']:.1f} | {r['lb90']:+.1f} | [{r['lo90']:+.1f}, {r['hi90']:+.1f}] |" if r else f'| {x}-{y} ({tag}) | missing | | | | |')
base = arms[0]; g0 = dict(ifeval=G[base]['ifeval'], mgsm=G[base]['mgsm'], loops=loops_of(S[base]) if S[base] else None, trunc=S[base]['truncated'] if S[base] else None)
def paired(a, ikey):
    ia, ib = G[a].get(ikey), G[base].get(ikey)
    if ia and ib and set(ia) == set(ib): r = boot(ia, ib); return f"paired {r['delta']:+.1f} pp, 90% CI [{r['lo90']:+.1f}, {r['hi90']:+.1f}] (n={r['n']})"
    return None
lines += ['', '| arm | IFEval-el vs M0 | MGSM-el vs M0 | loops vs M0 | truncated vs M0 | unresolved (no extracted answer) | format gate dev50 (reported) | guardrails |', '|---|---:|---:|---:|---:|---:|---|---|']
elig = {}; why = {}
for a in arms:
    unres = sum(1 for r in S[a]['rows'] if r['extracted'] in (None, '')) if S[a] else None
    if a == base: lines.append(f"| {a} | — | — | {g0['loops']} | {g0['trunc']} | {unres} | {fmt_gate(a + '_ep1')} | baseline |"); continue
    gi, gm = G[a]['ifeval'], G[a]['mgsm']; gl = loops_of(S[a]) if S[a] else None; gt = S[a]['truncated'] if S[a] else None; checks = []
    if S[a] is None or E[a] is None or S[base] is None or E[base] is None: checks.append('MATH-500 el/en readout incomplete')
    if gi is None or g0['ifeval'] is None: checks.append('IFEval missing')
    elif gi - g0['ifeval'] < -TOL_PP - EPS: checks.append(f'IFEval breach ({gi - g0["ifeval"]:+.2f} pp)')
    if gm is None or g0['mgsm'] is None: checks.append('MGSM missing')
    elif gm - g0['mgsm'] < -TOL_PP - EPS: checks.append(f'MGSM breach ({gm - g0["mgsm"]:+.2f} pp)')
    if gl is None or g0['loops'] is None: checks.append('loops missing')
    elif gl > g0['loops'] + BAND: checks.append(f'loops breach ({gl} vs {g0["loops"]})')
    if gt is None or g0['trunc'] is None: checks.append('truncations missing')
    elif gt > g0['trunc'] + BAND: checks.append(f'truncation breach ({gt} vs {g0["trunc"]})')
    elig[a] = not checks; why[a] = checks
    pi, pm = paired(a, 'ifeval_items'), paired(a, 'mgsm_items')
    lines.append(f"| {a} | {f1(gi)} vs {f1(g0['ifeval'])} · {pi or 'unpaired (no item files)'} | {f1(gm)} vs {f1(g0['mgsm'])} · {pm or 'unpaired (no item files)'} | {gl} vs {g0['loops']} | {gt} vs {g0['trunc']} | {unres} | {fmt_gate(a + '_ep1')} | {'PASS' if not checks else 'FAIL: ' + '; '.join(checks)} |")
lines += ['', '## Decision (frozen rule, plan §4; hierarchical: the secondary contrast is acted on only if the primary qualifies; no arm advances by default)', '']
adv = None
if missing:
    lines.append('- **INCOMPLETE readout: no arm advances.** Missing: ' + '; '.join(missing))
else:
    r = R[('M1', 'M0', 'el')]; reasons = []
    if r['delta'] < MIN_GAIN - EPS: reasons.append(f'gain {r["delta"]:+.1f} pp < {MIN_GAIN:.0f} pp')
    if r['lb90'] <= 0: reasons.append(f'one-sided 90% LB {r["lb90"]:+.1f} pp <= 0')
    reasons += why['M1']
    if not reasons: adv = 'M1'; lines.append(f'- primary {gfp("M1")} vs {gfp("M0")}: **qualified improvement** ({r["delta"]:+.1f} pp, LB {r["lb90"]:+.1f}, guardrails PASS)')
    else: lines.append(f'- primary {gfp("M1")} vs {gfp("M0")}: **not qualified** ({"; ".join(reasons)})')
    if 'M2' in arms:
        if adv is None: lines.append(f'- secondary {gfp("M2")} vs {gfp("M1")}: not evaluated for action (hierarchy: the primary contrast did not qualify); descriptive gain {R[("M2", "M1", "el")]["delta"]:+.1f} pp')
        else:
            r2 = R[('M2', 'M1', 'el')]; reasons2 = []
            if r2['delta'] < MIN_GAIN - EPS: reasons2.append(f'gain {r2["delta"]:+.1f} pp < {MIN_GAIN:.0f} pp')
            if r2['lb90'] <= 0: reasons2.append(f'one-sided 90% LB {r2["lb90"]:+.1f} pp <= 0')
            reasons2 += why['M2']
            if not reasons2: adv = 'M2'; lines.append(f'- secondary {gfp("M2")} vs {gfp("M1")}: **qualified** ({r2["delta"]:+.1f} pp, LB {r2["lb90"]:+.1f}, guardrails PASS): the Level-5 addition advances')
            else: lines.append(f'- secondary {gfp("M2")} vs {gfp("M1")}: **not qualified** ({"; ".join(reasons2)}); the Level-5 addition is not supported and {gfp("M1")} remains the advancing arm')
lines.append(f"- advancing arm: **{gfp(adv) if adv else 'none'}**")
if adv: lines.append('- next: dose/recipe check on the advancing checkpoint before Phase C (plan §5)')
elif not missing: lines.append('- next: no continuation from this readout; write up and re-plan the maths lane (plan §4 outcome table)')
lines.append('- English MATH-500 and the dev50 format gate are reported for the record; the frozen rule gates neither.')
ex = []
for name, sc in [('reference', S1)] + [(a, S[a]) for a in arms]:
    if sc: row = next((r for r in sc['rows'] if r['id'] == EXPOSED), None); ex.append(f"{name}: {'correct' if row and row['equiv500'] else 'incorrect'}")
if ex:
    lines.append(f'- inherited exposure (MATH-500 {EXPOSED}, one parent code row shares a 13-gram): ' + ', '.join(ex))
    for x, y in pairs:
        if S[x] and S[y]:
            a1, a0 = items(S[x]), items(S[y]); a1.pop(EXPOSED, None); a0.pop(EXPOSED, None); rr = boot(a1, a0); lines.append(f"  {x}-{y} gain without that item: {rr['delta']:+.1f} pp (LB {rr['lb90']:+.1f}, n={rr['n']})")
adjs = {a: S[a].get('adjudicated_acc') for a in arms if S[a] and S[a].get('adjudicated_acc') is not None}
if adjs: lines.append('- adjudicated accuracies (Sol, unresolved rows, response-bound; secondary): ' + ', '.join(f"{a} {v*100:.1f}" for a, v in adjs.items()) + '; coverage: ' + '; '.join(f"{a} {S[a]['adjudication_coverage']}" for a in adjs))
lines += ['', 'Uncertainty: MATH-500 contrasts are paired per item (bootstrap, 4,000 resamples, seed 1). Guardrail contrasts are paired per item when validated item files exist (shown in the table); otherwise the tolerance is applied to the point estimates and the difference is approximate (IFEval-el n=541: SE of a difference ≈ 2.9 pp at 65%; MGSM-el n=250: ≈ 4.4 pp at 50%). The 2 pp / +5-of-500 tolerances are frozen screening tolerances, not demonstrated non-inferiority. Primary scorer = equiv500 (scorer v2, response-bound) for every arm; the historical reference was scored with v1 and is shown unbound.']
os.makedirs(OUT, exist_ok=True); open(f'{OUT}/summary.md', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))

--- scorer v2 change (data/benchmarks_el/math500/score_math500.py): per-row response_sha256 and file responses_sha256 recorded; the pilot chain scores with this version; the historical stage-1 reference stays scorer v1 and is displayed as 'unbound' ---
#!/usr/bin/env python3
"""MATH-500-el scorer: equiv500 (our Greek-extended equivalence) and the upstream grader, by level and subject.
Usage: python3 score_math500.py <responses.jsonl: {id, response}> <out.json>"""
import json, os, sys, collections, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import equiv500 as E
bench = {json.loads(l)['id']: json.loads(l) for l in open(os.environ.get('MATH_BENCH_FILE', os.path.join(HERE, 'problems_el_final.jsonl')))}   # MATH_BENCH_FILE: e.g. ../math200_confirm/problems_el_final.jsonl
resp = [json.loads(l) for l in open(sys.argv[1])]
rows = []; by_level = collections.defaultdict(lambda: [0, 0]); by_subj = collections.defaultdict(lambda: [0, 0]); n_ok = n_up = n_trunc = 0
for r in resp:
    b = bench[r['id']]; pred = E.extract(r['response'] or ''); ok = bool(E.equiv500(b['answer'], pred)); up = E.upstream_equiv(b['answer'], pred)
    up = bool(up) if up is not None else None
    n_ok += ok; n_up += bool(up); n_trunc += (r.get('finish_reason') == 'length')
    by_level[b['level']][0] += ok; by_level[b['level']][1] += 1; by_subj[b['subject']][0] += ok; by_subj[b['subject']][1] += 1
    rows.append(dict(id=r['id'], level=b['level'], subject=b['subject'], answer=b['answer'], extracted=pred, equiv500=ok, upstream=up, truncated=r.get('finish_reason') == 'length', response_sha256=hashlib.sha256((r['response'] or '').encode('utf-8')).hexdigest()))
n = len(resp); n_up_avail = sum(1 for r in rows if r['upstream'] is not None)
out = dict(scorer_version=2, responses_sha256=hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest(), n=n, equiv500_acc=round(n_ok / n, 4) if n else None, upstream_acc=(round(n_up / n, 4) if n_up_avail == n else None), upstream_grader_available=n_up_avail == n, truncated=n_trunc,
                          by_level={str(k): round(v[0] / v[1], 4) for k, v in sorted(by_level.items())}, by_subject={k: round(v[0] / v[1], 4) for k, v in sorted(by_subj.items())}, rows=rows)
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1); print({k: v for k, v in out.items() if k != 'rows'})

=== §B FIXTURES v3 (data/pilot_fixtures.py, verbatim) and their report ===
#!/usr/bin/env python3
"""Fixtures for the pilot readout v3 (astra R3c): fabricated readouts built from the stage-1 prediction files in temp dirs, scored/hashed the way scorer v2
does, each case stating the expected outcome (advancing arm, none, or REFUSED). Writes results/pilots/readout_fixture.md. Usage: python3 data/pilot_fixtures.py"""
import json, os, sys, shutil, subprocess, tempfile, random, hashlib, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); REF = f'{ROOT}/results/R3_single/bench_S1'
N_IF, N_MG = 541, 250
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def build(case):
    d = tempfile.mkdtemp(prefix='pilot_fx_'); out = f'{d}/pilots'; res = f'{d}/results'
    ref_el = json.load(open(f'{REF}/math500_el_score.json')); ref_en = json.load(open(f'{REF}/math500_en_score.json'))
    resp_el = [json.loads(l) for l in open(f'{REF}/math500_el.jsonl')]; resp_en = [json.loads(l) for l in open(f'{REF}/math500_en.jsonl')]
    gains = case.get('gains', {'M0': (0, 0), 'M1': (21, 1), 'M2': (24, 1)}); guard = case.get('guard', {'M0': (0.60, 0.48), 'M1': (0.61, 0.49), 'M2': (0.60, 0.48)})
    trunc = case.get('trunc', {}); loops_add = case.get('loops_add', {}); unresolved = case.get('unresolved', {}); use_items = case.get('items', True)
    for a in ('M0', 'M1', 'M2'):
        b = f'{out}/bench_{a}'; os.makedirs(b)
        rs = [dict(r) for r in resp_el]
        if a in trunc:   # exactly trunc[a] responses finish with 'length'
            for i, r in enumerate(rs): r['finish_reason'] = 'length' if i < trunc[a] else 'stop'
        if a in loops_add:   # add a repeated 5x line to loops_add[a] responses that do not loop yet
            k = 0
            for r in rs:
                if k >= loops_add[a]: break
                lines_ = r['response'].splitlines()
                if not any(lines_.count(x) >= 5 for x in set(lines_) if len(x.strip()) > 12): r['response'] += '\n' + '\n'.join(['Επαναλαμβανόμενη γραμμή ελέγχου βρόχου.'] * 5); k += 1
        el = json.loads(json.dumps(ref_el)); rng = random.Random(7 if a != 'M0' else 3); rows = el['rows']
        up, down = gains[a]; ups = [r for r in rows if not r['equiv500']]; downs = [r for r in rows if r['equiv500']]
        for r in rng.sample(ups, up): r['equiv500'] = True
        for r in rng.sample(downs, down): r['equiv500'] = False
        for r in rows[:unresolved.get(a, 0)]: r['extracted'] = ''; r['equiv500'] = False   # the first k rows become unresolved (no extracted answer)
        by = {r['id']: r for r in rs}
        for r in rows: r['response_sha256'] = sha(by[r['id']]['response']); r['truncated'] = by[r['id']].get('finish_reason') == 'length'
        el['truncated'] = sum(1 for r in rs if r.get('finish_reason') == 'length'); el['equiv500_acc'] = round(sum(1 for r in rows if r['equiv500']) / 500, 4); el['scorer_version'] = 2
        text = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rs); open(f'{b}/math500_el.jsonl', 'w').write(text); el['responses_sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
        json.dump(el, open(f'{b}/math500_el_score.json', 'w'), ensure_ascii=False)
        en = json.loads(json.dumps(ref_en)); byen = {r['id']: r for r in resp_en}
        for r in en['rows']: r['response_sha256'] = sha(byen[r['id']]['response'])
        text = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in resp_en); open(f'{b}/math500_en.jsonl', 'w').write(text); en['responses_sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest(); en['scorer_version'] = 2
        json.dump(en, open(f'{b}/math500_en_score.json', 'w'), ensure_ascii=False)
        gi, gm = guard.get(a, (None, None)); lab = f'{res}/{a}_ep1'; os.makedirs(f'{lab}/ilsp/x')
        if gi is not None:
            if use_items and not (isinstance(gi, float) and math.isnan(gi)):
                k = round(gi * N_IF); gi = round(k / N_IF, 4); its = [dict(key=i, prompt_strict=i < k) for i in range(N_IF)]
                json.dump(dict(n=N_IF, prompt_strict=gi, prompt_strict_items=its), open(f'{lab}/ifeval_el_rescored.json', 'w'))
            else: json.dump(dict(n=N_IF, prompt_strict=gi), open(f'{lab}/ifeval_el_rescored.json', 'w'))
        if gm is not None:
            if use_items:
                k = round(gm * N_MG); gm = k / N_MG; open(f'{lab}/ilsp/x/samples_mgsm_greek_1.jsonl', 'w').write(''.join(json.dumps(dict(doc_id=i, exact_match=i < k)) + '\n' for i in range(N_MG)))
            json.dump(dict(results=dict(mgsm_greek={'exact_match,none': gm})), open(f'{lab}/ilsp/x/results_1.json', 'w'))
    for f in case.get('mutate', []): f(out, res)
    return d, out, res
def rm(p): os.remove(p)
def truncate_lines(p, n):
    ls = open(p).readlines(); assert len(ls) == 500, len(ls); open(p, 'w').write(''.join(ls[:n])); assert len(open(p).readlines()) == n
def dup_line(p): ls = open(p).readlines(); open(p, 'w').write(''.join(ls + [ls[0]]))
def empty(p): open(p, 'w').write('')
def set_cached_truncated(p, v): d = json.load(open(p)); d['truncated'] = v; json.dump(d, open(p, 'w'))
def alter_one_response(p):
    ls = [json.loads(l) for l in open(p)]; ls[0]['response'] = ls[0]['response'] + ' (altered)'; open(p, 'w').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in ls))
def items_all_false(p): d = json.load(open(p)); d['prompt_strict_items'] = [dict(key=i, prompt_strict=False) for i in range(N_IF)]; json.dump(d, open(p, 'w'))
def unbind(p): d = json.load(open(p)); d.pop('responses_sha256'); json.dump(d, open(p, 'w'))
def second_results(res): json.dump(dict(results=dict(mgsm_greek={'exact_match,none': 0.49})), open(f'{res}/M1_ep1/ilsp/x/results_2.json', 'w'))
def adjudication(out, dup=False):
    sc = json.load(open(f'{out}/bench_M1/math500_el_score.json')); rs = {json.loads(l)['id']: json.loads(l) for l in open(f'{out}/bench_M1/math500_el.jsonl')}
    unres = [r for r in sc['rows'] if r['extracted'] == '']; solved = [r for r in sc['rows'] if r['extracted'] != ''][0]
    a, b2, c = unres[0], unres[1], unres[2]
    ents = [dict(id=a['id'], equivalent=True, response_sha256=sha(rs[a['id']]['response']), reference=a['answer']),   # valid positive -> accepted
            dict(id=b2['id'], equivalent=False, response_sha256=sha(rs[b2['id']]['response']), reference=b2['answer']),   # valid negative
            dict(id=c['id'], equivalent=True, response_sha256='0' * 64, reference=c['answer']),   # stale hash -> rejected
            dict(id=solved['id'], equivalent=True, response_sha256=sha(rs[solved['id']]['response']), reference=solved['answer'])]   # attempt on a resolved row
    if dup: ents.append(dict(ents[0]))
    open(f'{out}/bench_M1/math500_el_adjudicated.jsonl', 'w').write(''.join(json.dumps(e) + '\n' for e in ents))
G0 = {'M0': (0.60, 0.48), 'M1': (0.61, 0.49), 'M2': (0.60, 0.48)}
CASES = [
 dict(name='A valid advancement: M1 +4 pp over M0 (guardrails present and passing), M2 +0.6 over M1', expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='B missing M0 English score file', mutate=[lambda o, r: rm(f'{o}/bench_M0/math500_en_score.json')], expect='advancing arm: **none**'),
 dict(name='C empty M1 response file', mutate=[lambda o, r: empty(f'{o}/bench_M1/math500_el.jsonl')], expect='REFUSED'),
 dict(name='D partial M1 response file (499 rows, asserted)', mutate=[lambda o, r: truncate_lines(f'{o}/bench_M1/math500_el.jsonl', 499)], expect='REFUSED'),
 dict(name='E duplicate id in M1 responses', mutate=[lambda o, r: dup_line(f'{o}/bench_M1/math500_el.jsonl')], expect='REFUSED'),
 dict(name='F NaN IFEval value for M1', guard={'M0': (0.60, 0.48), 'M1': (float('nan'), 0.49), 'M2': (0.60, 0.48)}, expect='REFUSED'),
 dict(name='G all guardrail files missing', guard={'M0': (None, None), 'M1': (None, None), 'M2': (None, None)}, expect='advancing arm: **none**'),
 dict(name='H negative primary (M1 -2 pp) with a strong secondary (M2 +8 over M1)', gains={'M0': (10, 0), 'M1': (0, 0), 'M2': (40, 0)}, expect='advancing arm: **none**'),
 dict(name='I M1 qualifies, M2 breaches IFEval (-3 pp)', guard={'M0': (0.60, 0.48), 'M1': (0.61, 0.49), 'M2': (0.57, 0.48)}, gains={'M0': (0, 0), 'M1': (21, 1), 'M2': (45, 0)}, expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='J M1 and M2 both qualify (M2 +4 over M1, guardrails pass)', gains={'M0': (0, 0), 'M1': (21, 1), 'M2': (42, 1)}, expect='advancing arm: **1-G4F6P0--02 (M2)**'),
 dict(name='K M1 gain +2 pp only (below the 3 pp floor)', gains={'M0': (0, 0), 'M1': (11, 1), 'M2': (14, 1)}, expect='advancing arm: **none**'),
 dict(name='L truncation breach: M1 66 length-finished vs M0 60 (band +5)', trunc={'M0': 60, 'M1': 66, 'M2': 60}, expect='advancing arm: **none**'),
 dict(name='M truncation boundary: M1 65 vs M0 60 (exactly +5) passes', trunc={'M0': 60, 'M1': 65, 'M2': 60}, expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='N cached truncated count disagrees with the responses', mutate=[lambda o, r: set_cached_truncated(f'{o}/bench_M1/math500_el_score.json', 0)], expect='REFUSED'),
 dict(name='O response text altered after scoring (ids kept)', mutate=[lambda o, r: alter_one_response(f'{o}/bench_M1/math500_el.jsonl')], expect='REFUSED'),
 dict(name='P IFEval exactly -2.0 pp (0.60 -> 0.58, aggregates only) passes', items=False, guard={'M0': (0.60, 0.48), 'M1': (0.58, 0.49), 'M2': (0.60, 0.48)}, expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='Q IFEval -2.01 pp (0.60 -> 0.5799, aggregates only) breaches', items=False, guard={'M0': (0.60, 0.48), 'M1': (0.5799, 0.49), 'M2': (0.60, 0.48)}, expect='advancing arm: **none**'),
 dict(name='R IFEval items contradict the aggregate (all false vs 0.61)', mutate=[lambda o, r: items_all_false(f'{r}/M1_ep1/ifeval_el_rescored.json')], expect='REFUSED'),
 dict(name='S primary gain +3.0 pp but one-sided 90% LB <= 0 (high discordance)', gains={'M0': (40, 0), 'M1': (95, 40), 'M2': (95, 40)}, expect='advancing arm: **none**'),
 dict(name='T loop breach: M1 +6 looping responses over M0', loops_add={'M1': 6}, expect='advancing arm: **none**'),
 dict(name='U loop boundary: M1 +5 looping responses (exactly the band) passes', loops_add={'M1': 5}, expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='V adjudication: valid positive, valid negative, stale hash, attempt on a resolved row (coverage reported; decision unchanged)', unresolved={'M1': 3}, mutate=[lambda o, r: adjudication(o)], expect="'accepted_positive': 1"),
 dict(name='V2 duplicate adjudication id', unresolved={'M1': 3}, mutate=[lambda o, r: adjudication(o, dup=True)], expect='REFUSED'),
 dict(name='W score file not bound to its responses (scorer v1 style)', mutate=[lambda o, r: unbind(f'{o}/bench_M1/math500_el_score.json')], expect='REFUSED'),
 dict(name='X two MGSM results files for M1 (ambiguous run identity)', mutate=[lambda o, r: second_results(r)], expect='REFUSED'),
]
report = ['# Readout fixtures v3 (fabricated from the stage-1 prediction files in temp dirs, scored and hashed like scorer v2; deleted after the run)', '', '| case | expected | observed | ok |', '|---|---|---|---|']; ok_all = True; caseA = ''; caseV = ''
for c in CASES:
    d, out, res = build(c); env = dict(os.environ, PILOT_OUT=out, PILOT_RESULTS=res, PILOT_REF=REF, PILOT_REF_LABEL='R2_stage1_ep1')
    p = subprocess.run([sys.executable, f'{HERE}/pilot_summary.py', 'M0', 'M1', 'M2'], env=env, capture_output=True, text=True)
    if p.returncode == 2: obs = 'REFUSED: ' + p.stdout.strip().splitlines()[-1][len('READOUT REFUSED: '):][:110]
    elif p.returncode != 0: obs = f'exit {p.returncode}: {p.stderr.strip().splitlines()[-1][:160] if p.stderr.strip() else ""}'
    else: obs = next((l.strip('- ') for l in p.stdout.splitlines() if l.startswith('- advancing arm')), 'no decision line') + ('' if not c['name'].startswith('V ') else ' | ' + next((l for l in p.stdout.splitlines() if 'coverage' in l), '')[:400])
    ok = c['expect'] in obs; ok_all &= ok; report.append(f"| {c['name']} | {c['expect']} | {obs} | {'PASS' if ok else 'FAIL'} |")
    if c['name'].startswith('A '): caseA = p.stdout
    if c['name'].startswith('S '): report[-1] += ' ' + next((l for l in p.stdout.splitlines() if l.startswith('- primary')), '')[:160]
    shutil.rmtree(d)
report += ['', '## Case A output', '', caseA]; open(f'{ROOT}/results/pilots/readout_fixture.md', 'w').write('\n'.join(report) + '\n'); print('\n'.join(report[:len(CASES) + 4])); print('ALL PASS' if ok_all else 'SOME FAIL'); sys.exit(0 if ok_all else 1)

--- report (results/pilots/readout_fixture.md; case A output included) ---
# Readout fixtures v3 (fabricated from the stage-1 prediction files in temp dirs, scored and hashed like scorer v2; deleted after the run)

| case | expected | observed | ok |
|---|---|---|---|
| A valid advancement: M1 +4 pp over M0 (guardrails present and passing), M2 +0.6 over M1 | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| B missing M0 English score file | advancing arm: **none** | advancing arm: **none** | PASS |
| C empty M1 response file | REFUSED | REFUSED: /var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/pilot_fx_h5qv8z2d/pilots/bench_M1/math500_el.jsonl: expected  | PASS |
| D partial M1 response file (499 rows, asserted) | REFUSED | REFUSED: /var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/pilot_fx_cslikftc/pilots/bench_M1/math500_el.jsonl: expected  | PASS |
| E duplicate id in M1 responses | REFUSED | REFUSED: /var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/pilot_fx_vivyqtqy/pilots/bench_M1/math500_el.jsonl: duplicate | PASS |
| F NaN IFEval value for M1 | REFUSED | REFUSED: IFEval-el prompt_strict for M1_ep1 is not a finite fraction in [0,1]: nan | PASS |
| G all guardrail files missing | advancing arm: **none** | advancing arm: **none** | PASS |
| H negative primary (M1 -2 pp) with a strong secondary (M2 +8 over M1) | advancing arm: **none** | advancing arm: **none** | PASS |
| I M1 qualifies, M2 breaches IFEval (-3 pp) | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| J M1 and M2 both qualify (M2 +4 over M1, guardrails pass) | advancing arm: **1-G4F6P0--02 (M2)** | advancing arm: **1-G4F6P0--02 (M2)** | PASS |
| K M1 gain +2 pp only (below the 3 pp floor) | advancing arm: **none** | advancing arm: **none** | PASS |
| L truncation breach: M1 66 length-finished vs M0 60 (band +5) | advancing arm: **none** | advancing arm: **none** | PASS |
| M truncation boundary: M1 65 vs M0 60 (exactly +5) passes | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| N cached truncated count disagrees with the responses | REFUSED | REFUSED: /var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/pilot_fx_25h_wncy/pilots/bench_M1/math500_el_score.json: cach | PASS |
| O response text altered after scoring (ids kept) | REFUSED | REFUSED: /var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/pilot_fx_55vlqaet/pilots/bench_M1/math500_el_score.json: resp | PASS |
| P IFEval exactly -2.0 pp (0.60 -> 0.58, aggregates only) passes | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| Q IFEval -2.01 pp (0.60 -> 0.5799, aggregates only) breaches | advancing arm: **none** | advancing arm: **none** | PASS |
| R IFEval items contradict the aggregate (all false vs 0.61) | REFUSED | REFUSED: IFEval-el items M1_ep1: items mean 0.00000 disagrees with the aggregate 0.61000 | PASS |
| S primary gain +3.0 pp but one-sided 90% LB <= 0 (high discordance) | advancing arm: **none** | advancing arm: **none** | PASS | - primary 1-G4F6P0--01 (M1) vs 1-G4F6P0--00 (M0): **not qualified** (one-sided 90% LB -0.2 pp <= 0)
| T loop breach: M1 +6 looping responses over M0 | advancing arm: **none** | advancing arm: **none** | PASS |
| U loop boundary: M1 +5 looping responses (exactly the band) passes | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| V adjudication: valid positive, valid negative, stale hash, attempt on a resolved row (coverage reported; decision unchanged) | 'accepted_positive': 1 | advancing arm: **1-G4F6P0--01 (M1)** | - adjudicated accuracies (Sol, unresolved rows, response-bound; secondary): M1 17.0; coverage: M1 {'unresolved': 3, 'attempts_on_unresolved': 3, 'attempts_on_resolved_rows': 1, 'stale_or_unbound': 1, 'valid_negative': 1, 'accepted_positive': 1} | PASS |
| V2 duplicate adjudication id | REFUSED | REFUSED: /var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/pilot_fx_spf8x1ng/pilots/bench_M1/math500_el_adjudicated.json | PASS |
| W score file not bound to its responses (scorer v1 style) | REFUSED | REFUSED: /var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/pilot_fx_cra26wf0/pilots/bench_M1/math500_el_score.json: scor | PASS |
| X two MGSM results files for M1 (ambiguous run identity) | REFUSED | REFUSED: MGSM-el M1_ep1: 2 results files (ambiguous run identity): ['/var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/p | PASS |

## Case A output

# Pilot readout (frozen rule, plan §4; readout v3)

| arm | MATH-500-el | loops (line x5) | truncated | MATH-500-en (reported) | IFEval-el prompt-strict (rescored) | MGSM-el |
|---|---:|---:|---:|---:|---:|---:|
| G2F1P0@epoch1 (reference, recomputed; scorer v1, unbound) | 12.8 | 27 | 60 | 16.4 | — | — |
| 1-G4F6P0--00 (M0) | 12.8 | 27 | 60 | 16.4 | 60.1 | 48.0 |
| 1-G4F6P0--01 (M1) | 16.8 | 27 | 60 | 16.4 | 61.0 | 48.8 |
| 1-G4F6P0--02 (M2) | 17.4 | 27 | 60 | 16.4 | 60.1 | 48.0 |

| contrast (descriptive) | n | gain (pp) | discordant % | one-sided 90% LB | two-sided 90% CI |
|---|---:|---:|---:|---:|---:|
| M1-M0 (el) | 500 | +4.0 | 4.4 | +2.8 | [+2.6, +5.6] |
| M1-M0 (en, reported) | 500 | +0.0 | 0.0 | +0.0 | [+0.0, +0.0] |
| M2-M1 (el) | 500 | +0.6 | 1.0 | +0.0 | [+0.0, +1.4] |
| M2-M1 (en, reported) | 500 | +0.0 | 0.0 | +0.0 | [+0.0, +0.0] |

| arm | IFEval-el vs M0 | MGSM-el vs M0 | loops vs M0 | truncated vs M0 | unresolved (no extracted answer) | format gate dev50 (reported) | guardrails |
|---|---:|---:|---:|---:|---:|---|---|
| M0 | — | — | 27 | 60 | 0 | None | baseline |
| M1 | 61.0 vs 60.1 · paired +0.9 pp, 90% CI [+0.4, +1.7] (n=541) | 48.8 vs 48.0 · paired +0.8 pp, 90% CI [+0.0, +2.0] (n=250) | 27 vs 27 | 60 vs 60 | 0 | None | PASS |
| M2 | 60.1 vs 60.1 · paired +0.0 pp, 90% CI [+0.0, +0.0] (n=541) | 48.0 vs 48.0 · paired +0.0 pp, 90% CI [+0.0, +0.0] (n=250) | 27 vs 27 | 60 vs 60 | 0 | None | PASS |

## Decision (frozen rule, plan §4; hierarchical: the secondary contrast is acted on only if the primary qualifies; no arm advances by default)

- primary 1-G4F6P0--01 (M1) vs 1-G4F6P0--00 (M0): **qualified improvement** (+4.0 pp, LB +2.8, guardrails PASS)
- secondary 1-G4F6P0--02 (M2) vs 1-G4F6P0--01 (M1): **not qualified** (gain +0.6 pp < 3 pp; one-sided 90% LB +0.0 pp <= 0); the Level-5 addition is not supported and 1-G4F6P0--01 (M1) remains the advancing arm
- advancing arm: **1-G4F6P0--01 (M1)**
- next: dose/recipe check on the advancing checkpoint before Phase C (plan §5)
- English MATH-500 and the dev50 format gate are reported for the record; the frozen rule gates neither.
- inherited exposure (MATH-500 test/number_theory/239.json, one parent code row shares a 13-gram): reference: incorrect, M0: incorrect, M1: incorrect, M2: incorrect
  M1-M0 gain without that item: +4.0 pp (LB +2.8, n=499)
  M2-M1 gain without that item: +0.6 pp (LB +0.0, n=499)

Uncertainty: MATH-500 contrasts are paired per item (bootstrap, 4,000 resamples, seed 1). Guardrail contrasts are paired per item when validated item files exist (shown in the table); otherwise the tolerance is applied to the point estimates and the difference is approximate (IFEval-el n=541: SE of a difference ≈ 2.9 pp at 65%; MGSM-el n=250: ≈ 4.4 pp at 50%). The 2 pp / +5-of-500 tolerances are frozen screening tolerances, not demonstrated non-inferiority. Primary scorer = equiv500 (scorer v2, response-bound) for every arm; the historical reference was scored with v1 and is shown unbound.


=== §C ESCAPE CLOSURE ===
Export audit bound to export hashes (data/math/cut2/escape_audit_exports.py: every exported user/assistant text re-run through the repair rules against its English source; any repairable or unresolved event = residual corruption; C0 characters counted; TAB/LF classes included):
{
 "rows_M0.jsonl": {
  "rows": 8934,
  "sha256": "97645de5f8a90632e5236f229f8201d1848eae85d072a28970042022db826fb0",
  "events": {
   "plain_text_line_start_c1b": 66
  },
  "residual_rows": 0,
  "examples": []
 },
 "rows_M1.jsonl": {
  "rows": 8934,
  "sha256": "88edac8e3add598ceefde3c4b33d3d29f4118036c290439e3d5c404269cbb3f6",
  "events": {},
  "residual_rows": 0,
  "examples": []
 },
 "rows_M2_extra.jsonl": {
  "rows": 1403,
  "sha256": "8d42368b17953a6b1331cadcd3f30d8b145356dc698e57f3b76f6651fbe3fbdb",
  "events": {},
  "residual_rows": 0,
  "examples": []
 },
 "rows_native.jsonl": {
  "rows": 5108,
  "sha256": "f0b9c65fe6a0b6763c02cda5fd4fa5c57701b8b2b066be92970e515f295c5a40",
  "events": {},
  "residual_rows": 0,
  "examples": []
 }
}
Notes: (1) rows_M0's 66 'plain_text_line_start_c1b' events are the newline-B detector firing on cut-1 terse targets written in Unicode maths (lines such as 'sin x·cos x = 10⁻¹', 'cos(Α/2) = √((1 + cos Α) / 2)'); inspected, not decoded escapes; those targets never passed through the JSON path that produced the defect and contain no LaTeX beyond \boxed. (2) Ambiguous repairs (pattern A and B both plausible, neither named by the source, e.g. BS+'eta') are now 'unresolved' -> regeneration; re-running the rules on the earliest pre-repair backups of every stored file finds 0 ambiguous events, so no applied repair was ambiguous. (3) '$x [LF]eq 0$' with a space before the LF: the newline rule now accepts a preceding space under the source-count condition; the export audit above applies that rule. (4) Cut-1: the two unresolved events in the first census were tabs in Asymptote code inherited from the English source (kept, 'inherited'); the one garbage cut-1 prompt (math_3175, ANSI bold codes around 'cos') was repaired by hand from its source 'Compute $\cos 72^\circ.$' in both stored files and re-checked (recorded in out/escape_repairs_report.json 'manual_repairs'). (5) Final texts you asked about: c2_math5_746 exported with '\triangle' intact (Level-5 high file, polished, validity none); gsm_310, gsm_3230, gsm_3505 were regenerated at high (forced), polished and validated (severity none), exported in M1; their M0 twins are the untouched cut-1 terse targets.
Repair report (out/escape_repairs_report.json, last apply):
{
 "files": {
  "prep/translations_with_reference.jsonl": {
   "rows": 9999,
   "changed": 0,
   "events": {
    "inherited": 6,
    "benign": 2,
    "unresolved": 2
   },
   "samples": [],
   "unresolved_ids": [
    "math_3175"
   ]
  },
  "out/level5_problems_el.jsonl": {
   "rows": 2180,
   "changed": 0,
   "events": {
    "unresolved": 107,
    "inherited": 2,
    "benign": 1
   },
   "samples": [],
   "unresolved_ids": [
    "math5_55",
    "math5_74",
    "math5_250",
    "math5_444",
    "math5_469",
    "math5_538",
    "math5_554",
    "math5_661",
    "math5_630",
    "math5_661",
    "math5_758",
    "math5_765",
    "math5_802",
    "math5_923",
    "math5_972",
    "math5_899",
    "math5_970",
    "math5_1025",
    "math5_1067",
    "math5_1178",
    "math5_1223",
    "math5_1261",
    "math5_1272",
    "math5_1412",
    "math5_1392",
    "math5_1372",
    "math5_1468"
   ]
  },
  "../cut1/edited/rows_edited.jsonl": {
   "rows": 14215,
   "changed": 0,
   "events": {
    "unresolved": 2
   },
   "samples": [],
   "unresolved_ids": [
    "gm_math_3175"
   ]
  },
  "out/solutions_el_repair_high.jsonl": {
   "rows": 220,
   "changed": 0,
   "events": {},
   "samples": [],
   "unresolved_ids": []
  },
  "out/solutions_el_l4_high.jsonl": {
   "rows": 1289,
   "changed": 0,
   "events": {},
   "samples": [],
   "unresolved_ids": []
  },
  "out/level5_solutions_el_high.jsonl": {
   "rows": 1493,
   "changed": 0,
   "events": {},
   "samples": [],
   "unresolved_ids": []
  },
  "out/solutions_el.jsonl": {
   "rows": 9989,
   "changed": 0,
   "events": {
    "unresolved": 17,
    "benign": 28
   },
   "samples": [],
   "unresolved_ids": [
    "gsm_310",
    "gsm_3230",
    "gsm_3505"
   ]
  }
 },
 "changed_problem_ids": [],
 "changed_solution_ids": [],
 "force_regen": [
  "gsm_310",
  "gsm_3230",
  "gsm_3505"
 ],
 "force_retranslate": [
  "math5_1025",
  "math5_1067",
  "math5_1178",
  "math5_1223",
  "math5_1261",
  "math5_1272",
  "math5_1372",
  "math5_1392",
  "math5_1412",
  "math5_1468",
  "math5_250",
  "math5_444",
  "math5_469",
  "math5_538",
  "math5_55",
  "math5_554",
  "math5_630",
  "math5_661",
  "math5_74",
  "math5_758",
  "math5_765",
  "math5_802",
  "math5_899",
  "math5_923",
  "math5_970",
  "math5_972",
  "math_3175"
 ],
 "applied": true,
 "time": "2026-09-14 19:34",
 "cut1_user_changed": [],
 "dropped_records": {
  "fidelity_all.jsonl": 26,
  "fidelity_sample.jsonl": 1,
  "fidelity_adjudicated.jsonl": 4,
  "fidelity_audit_passes.jsonl": 1,
  "validity.jsonl": 28
 },
 "manual_repairs": [
  {
   "id": "math_3175",
   "field": "problem_el",
   "old_repr": "'Να υπολογίσεις το $\\x1b[1mcos\\x1b[0m 72^\\\\circ$.'",
   "new": "Να υπολογίσεις το $\\cos 72^\\circ$.",
   "source": "Compute $\\cos 72^\\circ.$",
   "reason": "ANSI bold codes around cos; deterministic from the source",
   "files": [
    "data/math/cut2/prep/translations_with_reference.jsonl",
    "data/math/cut1/edited/rows_edited.jsonl"
   ]
  }
 ]
}
Repair rules (data/math/cut2/repair_escapes.py, verbatim):
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
            if word and i > 0 and (text[i - 1].isalnum() or text[i - 1] in ')}]|$ '):
                have = cmds(text)
                for k in range(len(word), 0, -1):
                    c = 'n' + word[:k]
                    if c in NEWLINE_CMDS and src.get(c, 0) > have.get(c, 0) and (k == len(word) or not word[k].isalpha()): cand = ('N', c, k); break
                if cand is None and sum(v for k, v in have.items() if k != 'boxed') > 0 and not text[i - 1].isspace():   # the backslash alone became the newline: LF + 'sqrt' where the source has \\sqrt more often than the Greek text; only in texts that use LaTeX at all (plain-text targets start lines with 'sin', 'log'...)
                    for k in range(len(word), 0, -1):
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
            if A and B and A[1] not in src and B[1] not in src: ev.append(dict(kind='unresolved', at=i, old=repr(ch + word[:12]), note=f'ambiguous {A[1]}|{B[1]}')); out.append(ch); i += 1; continue
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

=== §D TRAINER INPUT IDENTITY AND DOSE ===
SHA-256 of the uploaded manifests on the cluster (sha256sum) vs the receipts (byte attestation ran on the same local files):
M0 receipt 5bb1772e462b3831f3dee95d4b3ef75b4a451163cdf3d01bd7c6e43bd1885ba1 cluster 5bb1772e462b3831f3dee95d4b3ef75b4a451163cdf3d01bd7c6e43bd1885ba1
M1 receipt 0da4fc2334420d8828866beb8cfa633252b59e3044e8b44b8dc4f7cdeecb2daf cluster 0da4fc2334420d8828866beb8cfa633252b59e3044e8b44b8dc4f7cdeecb2daf
M2 receipt 3a75d29c19859b9cd687d38f19f2966ed20a8020940b792f864c4fcb8c28c155 cluster 3a75d29c19859b9cd687d38f19f2966ed20a8020940b792f864c4fcb8c28c155
The dry-run driver also verified md5 after each upload. The trainer reads exactly these files (config data paths). Token totals: the receipts count tokenizer content tokens per turn plus 8 per turn (a template approximation); the trainer counts the fully rendered chat template (BOS, role headers, system block), so its totals are 3-5% higher; the difference is a counting convention, not a different input. The dose figures of record are the trainer's: packed sequences and optimizer steps 459 / 479 / 493 (bfd packing, world size 4, effective batch 16); the checker's earlier estimates are retired.
Dry-runs (results/pilots/dryrun_M*.log):
M0: DRY_RUN_OK {"arm": "M0", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 16, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 1, "eval_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M0/dev.jsonl", "eval_rows": 373, "eval_tokens": 95760, "expected_full_train_tokens": null, "gradient_accumulation_steps": 4, "learning_rate": 1e-05, "lr_scheduler_type": "cosine_with_min_lr", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": 0.1, "model": "/iopsstor/scratch/cscs/fffoivos/sft_round1/runs/R2_stage1/epoch1", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 7331, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 459, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "M0_lr1e-5_1ep_cos", "steps_per_epoch": 459, "train_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M0/train.jsonl", "train_rows": 71715, "train_tokens": 29960812, "warmup_ratio": 0.03, "world_size": 4}
M1: DRY_RUN_OK {"arm": "M1", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 16, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 1, "eval_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M1/dev.jsonl", "eval_rows": 373, "eval_tokens": 109163, "expected_full_train_tokens": null, "gradient_accumulation_steps": 4, "learning_rate": 1e-05, "lr_scheduler_type": "cosine_with_min_lr", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": 0.1, "model": "/iopsstor/scratch/cscs/fffoivos/sft_round1/runs/R2_stage1/epoch1", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 7653, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 479, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "M1_lr1e-5_1ep_cos", "steps_per_epoch": 479, "train_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M1/train.jsonl", "train_rows": 71715, "train_tokens": 31278117, "warmup_ratio": 0.03, "world_size": 4}
M2: DRY_RUN_OK {"arm": "M2", "assistant_only_loss": true, "compute_autocast": "bfloat16", "effective_batch": 16, "eos_token": "<|assistant_end|>", "eos_token_id": 68, "epochs": 1, "eval_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M2/dev.jsonl", "eval_rows": 387, "eval_tokens": 118829, "expected_full_train_tokens": null, "gradient_accumulation_steps": 4, "learning_rate": 1e-05, "lr_scheduler_type": "cosine_with_min_lr", "max_length": 4096, "max_steps_override": -1, "min_lr_rate": 0.1, "model": "/iopsstor/scratch/cscs/fffoivos/sft_round1/runs/R2_stage1/epoch1", "model_parameter_dtype": "float32", "offline": true, "out_dir": null, "packed_sequences_bfd": 7878, "packing": true, "packing_strategy": "bfd", "padding_free": true, "per_device_train_batch_size": 1, "planned_optimizer_steps": 493, "revision": "18-avg-uniform5-tokens30B-50B", "run_name": "M2_lr1e-5_1ep_cos", "steps_per_epoch": 493, "train_file": "/iopsstor/scratch/cscs/fffoivos/sft_round1/data/arms/M2/train.jsonl", "train_rows": 73100, "train_tokens": 32199143, "warmup_ratio": 0.03, "world_size": 4}
Preflight: OK

=== §E ANSWERS TO YOUR OPEN QUESTIONS ===
Q1 (final texts, cut-1 unresolved): see §C notes (4)-(5).
Q2 (corrected fixture report, versions): §B; readout v3 = the inlined file; scorer v2 = the inlined file; fixtures fabricate score files exactly as scorer v2 writes them (per-row and file hashes, truncations and accuracy recomputed).
Q3 (token differences, trainer-side hashes): §D. I cannot decompose the per-arm difference further without instrumenting the trainer; identity is established by SHA-256, and the dose figures of record are the trainer's.
Q4 (English MATH safeguard, dev50 format gate): the frozen rule (plan §4) gates IFEval-el, MGSM-el, loops and truncations only; English MATH-500 and the dev50 format gate are reported for the record. The readout v3 says so explicitly in its decision section and labels both columns 'reported'.
Q5 (four loop ids, four contamination ids): the historical 23 came from the round-three diagnosis run on a different response file of the same checkpoint and is not reconstructible (the four ids are not recoverable); the readout retired the hard-coded figure and computes the reference with the same function as the arms. The four Level-5 rows removed by the arm assembler's rendered-row 13-gram check against the MATH-500/MATH-200 caches (data/list_contaminated.py): c2_math5_530, c2_math5_664, c2_math5_1156, c2_math5_1139. Snapshot labels: 10,306 / 8,930 / 1,376 were the pre-repair export; the current export is 10,337 = 8,934 + 1,403, arms M0/M1 71,715 rows and M2 73,100 rows (receipts in §D of the previous pack are superseded by these).
