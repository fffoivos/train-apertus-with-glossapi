Review target: GATE 1 RE-REVIEW (checkpoint R3e) for the pilot continuations 1-G4F6P0--00/--01/--02 (legacy M0/M1/M2), after your fourth review (docs/reviews/ASTRA_gate1_pilots_v4_20260914.md: HOLD for the two HIGH IFEval input-validation defects; F1/F3/F5 MEDIUM; F4 LOW). Nothing in the recipe or the datasets changed. This pack closes every item and answers the three open questions. Judge whether the HOLD lifts. No filesystem access: everything is inlined.

Closures: HIGH F2a (unkeyed global IFEval result) -> readout v3.1 accepts a direct result only from the arm's own file; the multi-label file must contain the label explicitly; fixture Y (no arm files + one unkeyed global result -> incomplete, no advancement). HIGH F2b (self-declared denominator, empty item list) -> item keys must equal the FROZEN inventories (data/benchmarks_el/ifeval_el_keys.json: the 541 IFEval-el prompt keys; mgsm_el_doc_ids.json: the 250 MGSM-el doc ids), a present-but-empty list refuses, an absent field keeps the documented aggregate-only path; fixtures Z (n=1 with one item -> refused: keys differ from the inventory), Z2 (empty list -> refused). MEDIUM F1 -> cached equiv500_acc must be a finite fraction (fixtures Z3 NaN, Z4 finite-wrong). MEDIUM F5 -> adjudication ids must be MATH-500 items and `equivalent` a real boolean (fixtures Z5, Z6); V now asserts the full coverage dictionary and the advancing arm. MEDIUM F3 -> §C: the export auditor implementation with its self-tests (leading-LF case included: the repair function now handles i == 0), the backup inventory with hashes, a terminal disposition table for every id any pass marked unresolved/forced/manual (hash-labelled), and the four final row bodies. LOW F4 -> every refusal fixture asserts its reason; the runner also checks that refusals are exit-2 refusals and advancements are not.
Also fixed on the way: the pilot chain's IFEval rescoring call now writes the multi-label file (results/ifeval_el_rescored.json, with per-prompt items) and requires an entry for every arm before the readout.

=== §A READOUT v3.1 (data/pilot_summary.py, verbatim) ===
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
EXPOSED = 'test/number_theory/239.json'; TOL_PP = 2.0; BAND = 5; MIN_GAIN = 3.0; EPS = 1e-9
IFEVAL_KEYS = set(json.load(open(f'{ROOT}/data/benchmarks_el/ifeval_el_keys.json'))); MGSM_IDS = set(json.load(open(f'{ROOT}/data/benchmarks_el/mgsm_el_doc_ids.json')))   # frozen item inventories (541 / 250)
assert len(IFEVAL_KEYS) == 541 and len(MGSM_IDS) == 250
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
    if finite01(sc.get('equiv500_acc')) is None or abs(float(sc['equiv500_acc']) - acc) > 1e-4 + EPS: refuse(f'{path}: cached equiv500_acc={sc.get("equiv500_acc")!r} disagrees with the rows ({acc:.4f})')
    sc['equiv500_acc'] = acc
    adj = path.replace('_score.json', '_adjudicated.jsonl')   # optional Sol adjudication of unresolved rows (data/benchmarks_el/math500/adjudicate_unresolved.py), response-bound
    if os.path.exists(adj):
        upd = {}
        for l in open(adj):
            if not l.strip(): continue
            u = json.loads(l)
            if u.get('id') in upd: refuse(f'{adj}: duplicate adjudication id {u.get("id")}')
            if u.get('id') not in EXPECTED: refuse(f'{adj}: adjudication id {u.get("id")!r} is not a MATH-500 item')
            if type(u.get('equivalent')) is not bool: refuse(f'{adj}: adjudication {u["id"]} has a non-boolean equivalent={u.get("equivalent")!r}')
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
def check_items(name, it, inventory, aggregate, tol):
    """it: list of (key, value) as present in the file (an absent field never reaches here). Keys must be exactly the frozen inventory, values boolean, mean agreeing with the aggregate."""
    if not it: refuse(f'{name}: item list present but empty')
    d = {}
    for k, v in it:
        if k in d: refuse(f'{name}: duplicate item key {k!r}')
        if type(v) is not bool: refuse(f'{name}: item {k!r} is not boolean')
        d[k] = v
    if set(d) != inventory: refuse(f'{name}: item keys differ from the frozen inventory ({len(d)} items, {len(set(d) - inventory)} unknown, {len(inventory - set(d))} missing)')
    if abs(sum(d.values()) / len(d) - aggregate) > tol + EPS: refuse(f'{name}: items mean {sum(d.values()) / len(d):.5f} disagrees with the aggregate {aggregate:.5f}')
    return d
def ifeval(label):
    """prompt-strict fraction: the arm's own file results/<label>/ifeval_el_rescored.json (a direct result, or keyed by the label), else the multi-label file results/ifeval_el_rescored.json which must contain the label explicitly. Returns (pp, items|None)."""
    d = None; own = f'{RES}/{label}/ifeval_el_rescored.json'; glob_ = f'{RES}/ifeval_el_rescored.json'
    if os.path.exists(own):
        x = json.load(open(own)); d = x if 'prompt_strict' in x else x.get(label)
    if d is None and os.path.exists(glob_):
        x = json.load(open(glob_)); d = x.get(label) if isinstance(x, dict) else None   # never an unkeyed global result
    if not d: return None, None
    v = finite01(d.get('prompt_strict'))
    if v is None: refuse(f'IFEval-el prompt_strict for {label} is not a finite fraction in [0,1]: {d.get("prompt_strict")!r}')
    it = None
    if 'prompt_strict_items' in d: it = check_items(f'IFEval-el items {label}', [(e.get('key'), e.get('prompt_strict')) for e in (d['prompt_strict_items'] or [])], IFEVAL_KEYS, v, 0.5e-4)   # prompt_strict is stored rounded to 4 decimals
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
        it = check_items(f'MGSM-el items {label}', [(x.get('doc_id'), x.get('exact_match')) for x in raw], MGSM_IDS, v, 1e-6)
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

=== §B FIXTURES v3.1 (data/pilot_fixtures.py, verbatim) and their report (results/pilots/readout_fixture.md; synthetic readout fixtures: they exercise decisions and hash plumbing, not grading) ===
#!/usr/bin/env python3
"""Fixtures for the pilot readout v3 (astra R3c): fabricated readouts built from the stage-1 prediction files in temp dirs, scored/hashed the way scorer v2
does, each case stating the expected outcome (advancing arm, none, or REFUSED). Writes results/pilots/readout_fixture.md. Usage: python3 data/pilot_fixtures.py"""
import json, os, sys, shutil, subprocess, tempfile, random, hashlib, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); REF = f'{ROOT}/results/R3_single/bench_S1'
N_IF, N_MG = 541, 250
IF_KEYS = json.load(open(f'{ROOT}/data/benchmarks_el/ifeval_el_keys.json')); MG_IDS = json.load(open(f'{ROOT}/data/benchmarks_el/mgsm_el_doc_ids.json'))
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
                k = round(gi * N_IF); gi = round(k / N_IF, 4); its = [dict(key=key, prompt_strict=i < k) for i, key in enumerate(IF_KEYS)]
                json.dump(dict(n=N_IF, prompt_strict=gi, prompt_strict_items=its), open(f'{lab}/ifeval_el_rescored.json', 'w'))
            else: json.dump(dict(n=N_IF, prompt_strict=gi), open(f'{lab}/ifeval_el_rescored.json', 'w'))
        if gm is not None:
            if use_items:
                k = round(gm * N_MG); gm = k / N_MG; open(f'{lab}/ilsp/x/samples_mgsm_greek_1.jsonl', 'w').write(''.join(json.dumps(dict(doc_id=did, exact_match=i < k)) + '\n' for i, did in enumerate(MG_IDS)))
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
def items_all_false(p): d = json.load(open(p)); d['prompt_strict_items'] = [dict(key=key, prompt_strict=False) for key in IF_KEYS]; json.dump(d, open(p, 'w'))
def one_item_denominator(p): json.dump(dict(n=1, prompt_strict=1.0, prompt_strict_items=[dict(key=IF_KEYS[0], prompt_strict=True)]), open(p, 'w'))
def empty_items(p): json.dump(dict(n=N_IF, prompt_strict=1.0, prompt_strict_items=[]), open(p, 'w'))
def unkeyed_global(res):
    for a in ('M0', 'M1', 'M2'): os.remove(f'{res}/{a}_ep1/ifeval_el_rescored.json')
    json.dump(dict(prompt_strict=0.60), open(f'{res}/ifeval_el_rescored.json', 'w'))
def set_cached_acc(p, v): d = json.load(open(p)); d['equiv500_acc'] = v; json.dump(d, open(p, 'w'))
def adj_malformed(out):
    adjudication(out); p = f'{out}/bench_M1/math500_el_adjudicated.jsonl'; ls = [json.loads(l) for l in open(p)]; ls[1]['equivalent'] = None; open(p, 'w').write(''.join(json.dumps(e) + '\n' for e in ls))
def adj_unknown(out):
    adjudication(out); p = f'{out}/bench_M1/math500_el_adjudicated.jsonl'; ls = [json.loads(l) for l in open(p)]; ls[1]['id'] = 'test/algebra/999999.json'; open(p, 'w').write(''.join(json.dumps(e) + '\n' for e in ls))
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
 dict(name='C empty M1 response file', mutate=[lambda o, r: empty(f'{o}/bench_M1/math500_el.jsonl')], expect='expected exactly the 500 frozen ids, got 0 ('),
 dict(name='D partial M1 response file (499 rows, asserted)', mutate=[lambda o, r: truncate_lines(f'{o}/bench_M1/math500_el.jsonl', 499)], expect='expected exactly the 500 frozen ids, got 499'),
 dict(name='E duplicate id in M1 responses', mutate=[lambda o, r: dup_line(f'{o}/bench_M1/math500_el.jsonl')], expect='duplicate response id'),
 dict(name='F NaN IFEval value for M1', guard={'M0': (0.60, 0.48), 'M1': (float('nan'), 0.49), 'M2': (0.60, 0.48)}, expect='IFEval-el prompt_strict for M1_ep1 is not a finite fraction'),
 dict(name='G all guardrail files missing', guard={'M0': (None, None), 'M1': (None, None), 'M2': (None, None)}, expect='advancing arm: **none**'),
 dict(name='H negative primary (M1 -2 pp) with a strong secondary (M2 +8 over M1)', gains={'M0': (10, 0), 'M1': (0, 0), 'M2': (40, 0)}, expect='advancing arm: **none**'),
 dict(name='I M1 qualifies, M2 breaches IFEval (-3 pp)', guard={'M0': (0.60, 0.48), 'M1': (0.61, 0.49), 'M2': (0.57, 0.48)}, gains={'M0': (0, 0), 'M1': (21, 1), 'M2': (45, 0)}, expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='J M1 and M2 both qualify (M2 +4 over M1, guardrails pass)', gains={'M0': (0, 0), 'M1': (21, 1), 'M2': (42, 1)}, expect='advancing arm: **1-G4F6P0--02 (M2)**'),
 dict(name='K M1 gain +2 pp only (below the 3 pp floor)', gains={'M0': (0, 0), 'M1': (11, 1), 'M2': (14, 1)}, expect='advancing arm: **none**'),
 dict(name='L truncation breach: M1 66 length-finished vs M0 60 (band +5)', trunc={'M0': 60, 'M1': 66, 'M2': 60}, expect='advancing arm: **none**'),
 dict(name='M truncation boundary: M1 65 vs M0 60 (exactly +5) passes', trunc={'M0': 60, 'M1': 65, 'M2': 60}, expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='N cached truncated count disagrees with the responses', mutate=[lambda o, r: set_cached_truncated(f'{o}/bench_M1/math500_el_score.json', 0)], expect='cached truncated=0 disagrees'),
 dict(name='O response text altered after scoring (ids kept)', mutate=[lambda o, r: alter_one_response(f'{o}/bench_M1/math500_el.jsonl')], expect='responses_sha256 does not match'),
 dict(name='P IFEval exactly -2.0 pp (0.60 -> 0.58, aggregates only) passes', items=False, guard={'M0': (0.60, 0.48), 'M1': (0.58, 0.49), 'M2': (0.60, 0.48)}, expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='Q IFEval -2.01 pp (0.60 -> 0.5799, aggregates only) breaches', items=False, guard={'M0': (0.60, 0.48), 'M1': (0.5799, 0.49), 'M2': (0.60, 0.48)}, expect='advancing arm: **none**'),
 dict(name='R IFEval items contradict the aggregate (all false vs 0.61)', mutate=[lambda o, r: items_all_false(f'{r}/M1_ep1/ifeval_el_rescored.json')], expect='items mean 0.00000 disagrees'),
 dict(name='S primary gain +3.0 pp but one-sided 90% LB <= 0 (high discordance)', gains={'M0': (40, 0), 'M1': (95, 40), 'M2': (95, 40)}, expect='advancing arm: **none**'),
 dict(name='T loop breach: M1 +6 looping responses over M0', loops_add={'M1': 6}, expect='advancing arm: **none**'),
 dict(name='U loop boundary: M1 +5 looping responses (exactly the band) passes', loops_add={'M1': 5}, expect='advancing arm: **1-G4F6P0--01 (M1)**'),
 dict(name='V adjudication: valid positive, valid negative, stale hash, attempt on a resolved row (coverage reported; decision unchanged)', unresolved={'M1': 3}, mutate=[lambda o, r: adjudication(o)], expect=['advancing arm: **1-G4F6P0--01 (M1)**', "coverage: M1 {'unresolved': 3, 'attempts_on_unresolved': 3, 'attempts_on_resolved_rows': 1, 'stale_or_unbound': 1, 'valid_negative': 1, 'accepted_positive': 1}"]),
 dict(name='V2 duplicate adjudication id', unresolved={'M1': 3}, mutate=[lambda o, r: adjudication(o, dup=True)], expect='duplicate adjudication id'),
 dict(name='W score file not bound to its responses (scorer v1 style)', mutate=[lambda o, r: unbind(f'{o}/bench_M1/math500_el_score.json')], expect='score file not bound'),
 dict(name='X two MGSM results files for M1 (ambiguous run identity)', mutate=[lambda o, r: second_results(r)], expect='MGSM-el M1_ep1: 2 results files'),
 dict(name='Y no arm IFEval files, one unkeyed global result (must not supply every arm)', mutate=[lambda o, r: unkeyed_global(r)], expect='advancing arm: **none**'),
 dict(name='Z self-declared one-item IFEval denominator (n=1, 100%)', mutate=[lambda o, r: one_item_denominator(f'{r}/M1_ep1/ifeval_el_rescored.json')], expect='item keys differ from the frozen inventory'),
 dict(name='Z2 explicitly empty IFEval item list', mutate=[lambda o, r: empty_items(f'{r}/M1_ep1/ifeval_el_rescored.json')], expect='item list present but empty'),
 dict(name='Z3 cached equiv500_acc NaN', mutate=[lambda o, r: set_cached_acc(f'{o}/bench_M1/math500_el_score.json', float('nan'))], expect='cached equiv500_acc=nan disagrees'),
 dict(name='Z4 cached equiv500_acc finite but wrong (0.5)', mutate=[lambda o, r: set_cached_acc(f'{o}/bench_M1/math500_el_score.json', 0.5)], expect='cached equiv500_acc=0.5 disagrees'),
 dict(name='Z5 adjudication with a non-boolean equivalent (null)', unresolved={'M1': 3}, mutate=[lambda o, r: adj_malformed(o)], expect='has a non-boolean equivalent=None'),
 dict(name='Z6 adjudication on an id that is not a MATH-500 item', unresolved={'M1': 3}, mutate=[lambda o, r: adj_unknown(o)], expect='is not a MATH-500 item'),
]
report = ['# Readout fixtures v3 (fabricated from the stage-1 prediction files in temp dirs, scored and hashed like scorer v2; deleted after the run)', '', '| case | expected | observed | ok |', '|---|---|---|---|']; ok_all = True; caseA = ''; caseV = ''
for c in CASES:
    d, out, res = build(c); env = dict(os.environ, PILOT_OUT=out, PILOT_RESULTS=res, PILOT_REF=REF, PILOT_REF_LABEL='R2_stage1_ep1')
    p = subprocess.run([sys.executable, f'{HERE}/pilot_summary.py', 'M0', 'M1', 'M2'], env=env, capture_output=True, text=True)
    if p.returncode == 2: obs = 'REFUSED: ' + p.stdout.strip().splitlines()[-1][len('READOUT REFUSED: '):].replace(out + '/', '').replace(res + '/', '')[:150]
    elif p.returncode != 0: obs = f'exit {p.returncode}: {p.stderr.strip().splitlines()[-1][:160] if p.stderr.strip() else ""}'
    else: obs = next((l.strip('- ') for l in p.stdout.splitlines() if l.startswith('- advancing arm')), 'no decision line') + ('' if not c['name'].startswith('V ') else ' | ' + next((l for l in p.stdout.splitlines() if 'coverage' in l), '')[:400])
    exp = c['expect'] if isinstance(c['expect'], list) else [c['expect']]; wants_refusal = not any(e.startswith('advancing') for e in exp)
    ok = all(e in obs for e in exp) and (obs.startswith('REFUSED') == wants_refusal); ok_all &= ok; report.append(f"| {c['name']} | {' AND '.join(exp)} | {obs} | {'PASS' if ok else 'FAIL'} |")
    if c['name'].startswith('A '): caseA = p.stdout
    if c['name'].startswith('S '): report[-1] += ' ' + next((l for l in p.stdout.splitlines() if l.startswith('- primary')), '')[:160]
    shutil.rmtree(d)
report += ['', '## Case A output', '', caseA]; open(f'{ROOT}/results/pilots/readout_fixture.md', 'w').write('\n'.join(report) + '\n'); print('\n'.join(report[:len(CASES) + 4])); print('ALL PASS' if ok_all else 'SOME FAIL'); sys.exit(0 if ok_all else 1)

--- report ---
# Readout fixtures v3 (fabricated from the stage-1 prediction files in temp dirs, scored and hashed like scorer v2; deleted after the run)

| case | expected | observed | ok |
|---|---|---|---|
| A valid advancement: M1 +4 pp over M0 (guardrails present and passing), M2 +0.6 over M1 | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| B missing M0 English score file | advancing arm: **none** | advancing arm: **none** | PASS |
| C empty M1 response file | expected exactly the 500 frozen ids, got 0 ( | REFUSED: bench_M1/math500_el.jsonl: expected exactly the 500 frozen ids, got 0 (0 unexpected, 500 missing) | PASS |
| D partial M1 response file (499 rows, asserted) | expected exactly the 500 frozen ids, got 499 | REFUSED: bench_M1/math500_el.jsonl: expected exactly the 500 frozen ids, got 499 (0 unexpected, 1 missing) | PASS |
| E duplicate id in M1 responses | duplicate response id | REFUSED: bench_M1/math500_el.jsonl: duplicate response id test/number_theory/1032.json | PASS |
| F NaN IFEval value for M1 | IFEval-el prompt_strict for M1_ep1 is not a finite fraction | REFUSED: IFEval-el prompt_strict for M1_ep1 is not a finite fraction in [0,1]: nan | PASS |
| G all guardrail files missing | advancing arm: **none** | advancing arm: **none** | PASS |
| H negative primary (M1 -2 pp) with a strong secondary (M2 +8 over M1) | advancing arm: **none** | advancing arm: **none** | PASS |
| I M1 qualifies, M2 breaches IFEval (-3 pp) | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| J M1 and M2 both qualify (M2 +4 over M1, guardrails pass) | advancing arm: **1-G4F6P0--02 (M2)** | advancing arm: **1-G4F6P0--02 (M2)** | PASS |
| K M1 gain +2 pp only (below the 3 pp floor) | advancing arm: **none** | advancing arm: **none** | PASS |
| L truncation breach: M1 66 length-finished vs M0 60 (band +5) | advancing arm: **none** | advancing arm: **none** | PASS |
| M truncation boundary: M1 65 vs M0 60 (exactly +5) passes | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| N cached truncated count disagrees with the responses | cached truncated=0 disagrees | REFUSED: bench_M1/math500_el_score.json: cached truncated=0 disagrees with the responses (60 finish_reason=length) | PASS |
| O response text altered after scoring (ids kept) | responses_sha256 does not match | REFUSED: bench_M1/math500_el_score.json: responses_sha256 does not match bench_M1/math500_el.jsonl (rescore the responses) | PASS |
| P IFEval exactly -2.0 pp (0.60 -> 0.58, aggregates only) passes | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| Q IFEval -2.01 pp (0.60 -> 0.5799, aggregates only) breaches | advancing arm: **none** | advancing arm: **none** | PASS |
| R IFEval items contradict the aggregate (all false vs 0.61) | items mean 0.00000 disagrees | REFUSED: IFEval-el items M1_ep1: items mean 0.00000 disagrees with the aggregate 0.61000 | PASS |
| S primary gain +3.0 pp but one-sided 90% LB <= 0 (high discordance) | advancing arm: **none** | advancing arm: **none** | PASS | - primary 1-G4F6P0--01 (M1) vs 1-G4F6P0--00 (M0): **not qualified** (one-sided 90% LB -0.2 pp <= 0)
| T loop breach: M1 +6 looping responses over M0 | advancing arm: **none** | advancing arm: **none** | PASS |
| U loop boundary: M1 +5 looping responses (exactly the band) passes | advancing arm: **1-G4F6P0--01 (M1)** | advancing arm: **1-G4F6P0--01 (M1)** | PASS |
| V adjudication: valid positive, valid negative, stale hash, attempt on a resolved row (coverage reported; decision unchanged) | advancing arm: **1-G4F6P0--01 (M1)** AND coverage: M1 {'unresolved': 3, 'attempts_on_unresolved': 3, 'attempts_on_resolved_rows': 1, 'stale_or_unbound': 1, 'valid_negative': 1, 'accepted_positive': 1} | advancing arm: **1-G4F6P0--01 (M1)** | - adjudicated accuracies (Sol, unresolved rows, response-bound; secondary): M1 17.0; coverage: M1 {'unresolved': 3, 'attempts_on_unresolved': 3, 'attempts_on_resolved_rows': 1, 'stale_or_unbound': 1, 'valid_negative': 1, 'accepted_positive': 1} | PASS |
| V2 duplicate adjudication id | duplicate adjudication id | REFUSED: bench_M1/math500_el_adjudicated.jsonl: duplicate adjudication id test/number_theory/1032.json | PASS |
| W score file not bound to its responses (scorer v1 style) | score file not bound | REFUSED: bench_M1/math500_el_score.json: score file not bound to its responses (scorer v1); rescore with score_math500.py v2 | PASS |
| X two MGSM results files for M1 (ambiguous run identity) | MGSM-el M1_ep1: 2 results files | REFUSED: MGSM-el M1_ep1: 2 results files (ambiguous run identity): ['M1_ep1/ilsp/x/results_1.json', 'M1_ep1/ilsp/x/results_2.json'] | PASS |
| Y no arm IFEval files, one unkeyed global result (must not supply every arm) | advancing arm: **none** | advancing arm: **none** | PASS |
| Z self-declared one-item IFEval denominator (n=1, 100%) | item keys differ from the frozen inventory | REFUSED: IFEval-el items M1_ep1: item keys differ from the frozen inventory (1 items, 0 unknown, 540 missing) | PASS |
| Z2 explicitly empty IFEval item list | item list present but empty | REFUSED: IFEval-el items M1_ep1: item list present but empty | PASS |
| Z3 cached equiv500_acc NaN | cached equiv500_acc=nan disagrees | REFUSED: bench_M1/math500_el_score.json: cached equiv500_acc=nan disagrees with the rows (0.1680) | PASS |
| Z4 cached equiv500_acc finite but wrong (0.5) | cached equiv500_acc=0.5 disagrees | REFUSED: bench_M1/math500_el_score.json: cached equiv500_acc=0.5 disagrees with the rows (0.1680) | PASS |
| Z5 adjudication with a non-boolean equivalent (null) | has a non-boolean equivalent=None | REFUSED: bench_M1/math500_el_adjudicated.jsonl: adjudication test/precalculus/1303.json has a non-boolean equivalent=None | PASS |
| Z6 adjudication on an id that is not a MATH-500 item | is not a MATH-500 item | REFUSED: bench_M1/math500_el_adjudicated.jsonl: adjudication id 'test/algebra/999999.json' is not a MATH-500 item | PASS |

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
--- export auditor (data/math/cut2/escape_audit_exports.py, verbatim; the self-tests at the top run on every invocation) ---
#!/usr/bin/env python3
"""Escape audit of the EXPORTED rows, bound to the export hashes: every row's user and assistant text is run through the repair rules against its English
source; any repairable or unresolved event means residual corruption (TAB/LF classes included). Also counts C0 characters. Writes final/escape_audit.json."""
import json, re, hashlib, glob, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); from repair_escapes import repair
# SELF-TESTS of the repair rules (run every time; a failure aborts the audit)
T = [('\nabla f', '\\nabla f', '\\nabla f'), ('$x \neq 0$', '$x \\neq 0$', '$x \\neq 0$'), ('$\theta$', '', '$\\theta$'), ('$\x0crac{1}{2}$', '', '$\\frac{1}{2}$'),
     ('$\x08\x00eta$', '$\\beta$', '$\\beta$'), ('$\x00overline{AB}$', '$\\overline{AB}$', '$\\overline{AB}$'), ('$\x0010,\x10000$', '$\\$10,\\!000$', '$\\$10,\\!000$'), ('$\x07cd(a,b)$', '$\\gcd(a,b)$', '$\\gcd(a,b)$')]
for t, src_, want in T:
    got, _ = repair(t, src_); assert got == want, (t, got, want)
got, ev = repair('$\x08eta$', ''); assert got == '$\x08eta$' and any(e['kind'] == 'unresolved' and 'ambiguous' in e.get('note', '') for e in ev), ('ambiguity', ev)
got, ev = repair('\x1b[1mcos\x1b[0m', ''); assert any(e['kind'] == 'unresolved' for e in ev), ('garbage', ev)
got, _ = repair('code\n\treturn 2;', 'code\n\treturn 2;'); assert got == 'code\n\treturn 2;'
print('repair self-tests: OK')
src = {}
for l in open(f'{HERE}/prep/translations_with_reference.jsonl'): r = json.loads(l); src[r['id']] = r
for l in open(f'{HERE}/out/level5_problems_el.jsonl'): r = json.loads(l); src.setdefault(r['id'], r)
C0 = re.compile(r'[\x00-\x08\x0b-\x1f\x7f]'); out = {}
for f in sorted(glob.glob(f'{HERE}/final/rows_*.jsonl')):
    data = open(f, 'rb').read(); ev = collections.Counter(); bad_rows = []; rows = 0
    for l in data.decode('utf-8').splitlines():
        if not l.strip(): continue
        r = json.loads(l); rows += 1; pid = re.sub(r'^(c2_|c1b_|gm_)', '', r['id']); s = src.get(pid, {})
        hits = []
        for k, sk in (('user', 'problem_en'), ('assistant', 'solution_en')):
            t = r.get(k) or ''
            if C0.search(t): hits.append(f'{k}:C0')
            _, e = repair(t, s.get(sk, '') if s else '')
            for x in e:
                if x['kind'] == 'repaired_NB' and r['id'].startswith('c1b_'): ev['plain_text_line_start_c1b'] += 1; continue   # cut-1 terse targets are Unicode maths: lines start with 'sin', 'cos', 'log' (inspected 14 Sept), not decoded escapes
                if x['kind'].startswith('repaired') or x['kind'] == 'unresolved': hits.append(f"{k}:{x['kind']}:{x['old']}")
        for h in hits: ev[h.split(':')[1]] += 1
        if hits: bad_rows.append(dict(id=r['id'], hits=hits[:5]))
    out[os.path.basename(f)] = dict(rows=rows, sha256=hashlib.sha256(data).hexdigest(), events=dict(ev), residual_rows=len(bad_rows), examples=bad_rows[:10])
json.dump(out, open(f'{HERE}/final/escape_audit.json', 'w'), ensure_ascii=False, indent=1)
for k, v in out.items(): print(k, 'rows', v['rows'], 'sha256', v['sha256'][:12], 'residual rows', v['residual_rows'], v['events'], v['examples'][:3])

--- audit result (final/escape_audit.json) ---
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
--- terminal disposition of every id that any pass marked unresolved, forced or manually repaired (final/escape_disposition.json; row_sha256 = sha256 of the exported JSON line, first 16 hex) ---
[
 {
  "id": "gsm_310",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M0.jsonl",
    "row_id": "c1b_gsm_310",
    "row_sha256": "1f0283d0fb260cf6",
    "generation": null,
    "polished": null,
    "validity": null,
    "ctrl": false
   },
   {
    "file": "rows_M1.jsonl",
    "row_id": "c2_gsm_310",
    "row_sha256": "9ff21cec92bd8f7c",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "gsm_3230",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M0.jsonl",
    "row_id": "c1b_gsm_3230",
    "row_sha256": "40cdb1f582495e1e",
    "generation": null,
    "polished": null,
    "validity": null,
    "ctrl": false
   },
   {
    "file": "rows_M1.jsonl",
    "row_id": "c2_gsm_3230",
    "row_sha256": "4c60622c9e187614",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "gsm_3505",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M0.jsonl",
    "row_id": "c1b_gsm_3505",
    "row_sha256": "6d0f9450fd96c227",
    "generation": null,
    "polished": null,
    "validity": null,
    "ctrl": false
   },
   {
    "file": "rows_M1.jsonl",
    "row_id": "c2_gsm_3505",
    "row_sha256": "fb8a47580322e3e5",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math_2612",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M0.jsonl",
    "row_id": "c1b_math_2612",
    "row_sha256": "f5b9ca1efc6252e7",
    "generation": null,
    "polished": null,
    "validity": null,
    "ctrl": false
   },
   {
    "file": "rows_M1.jsonl",
    "row_id": "c2_math_2612",
    "row_sha256": "bfa4386848e87d99",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math_3175",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M0.jsonl",
    "row_id": "c1b_math_3175",
    "row_sha256": "12bcf71d0f49c733",
    "generation": null,
    "polished": null,
    "validity": null,
    "ctrl": false
   },
   {
    "file": "rows_M1.jsonl",
    "row_id": "c2_math_3175",
    "row_sha256": "cc42a9f2b928f944",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_55",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_55",
    "row_sha256": "a47c49d6caa898a4",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_74",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_74",
    "row_sha256": "c97ccbe62d15bafe",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_250",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_250",
    "row_sha256": "dc40938481b1554a",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_310",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_310",
    "row_sha256": "2328d0d6c6a07f14",
    "generation": "level5_solutions_el_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_444",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_469",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_538",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_541",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_541",
    "row_sha256": "8c8e9207b7a5ac5f",
    "generation": "level5_solutions_el_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_554",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_630",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_630",
    "row_sha256": "e89d4a2d750b9b6e",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_635",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_661",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_698",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_698",
    "row_sha256": "37dd2b8c4ce46c00",
    "generation": "level5_solutions_el_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_746",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_746",
    "row_sha256": "7a72b140cffdcfaf",
    "generation": "level5_solutions_el_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_758",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_758",
    "row_sha256": "29bdfcb1e531f3ad",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_765",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_802",
  "disposition": "EXCLUDED",
  "why": [
   "excluded by assembly (pairing/length/polish rule; see receipt drop reasons)"
  ],
  "validity": [
   [
    "none",
    "high"
   ]
  ],
  "fidelity": true
 },
 {
  "id": "math5_899",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_923",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_929",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_929",
    "row_sha256": "85991c641f55d1bd",
    "generation": "level5_solutions_el_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_970",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_972",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_972",
    "row_sha256": "29826c7ff334a626",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_1025",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_1067",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_1178",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_1178",
    "row_sha256": "aa2117799781ccab",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_1223",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_1228",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_1231",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_1231",
    "row_sha256": "31f179f0938114e9",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_1261",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_1261",
    "row_sha256": "5f6db31c59aaa811",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_1272",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_1272",
    "row_sha256": "f63e1df718704821",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_1277",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_1277",
    "row_sha256": "32958f992fc9a32b",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_1361",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_1361",
    "row_sha256": "035109e8d53bdc63",
    "generation": "level5_solutions_el_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_1372",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_1372",
    "row_sha256": "eb57fc85dc2a3af4",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_1392",
  "disposition": "EXCLUDED",
  "why": [
   "no translation record (retranslation rejected by the guard on every retry)"
  ],
  "validity": null,
  "fidelity": null
 },
 {
  "id": "math5_1412",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_1412",
    "row_sha256": "cfd8a604c0b04ad3",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_1468",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_1468",
    "row_sha256": "a1ecf9aec3d4da84",
    "generation": "solutions_el_repair_high.jsonl",
    "polished": "edited",
    "validity": "none",
    "ctrl": false
   }
  ]
 },
 {
  "id": "math5_1472",
  "disposition": "EXPORTED",
  "where": [
   {
    "file": "rows_M2_extra.jsonl",
    "row_id": "c2_math5_1472",
    "row_sha256": "3c95f8e1778b19ff",
    "generation": "level5_solutions_el_high.jsonl",
    "polished": "unchanged",
    "validity": "none",
    "ctrl": false
   }
  ]
 }
]
--- backup inventory (every .bak written by the repair passes; sha256 first 16 hex) ---
[
 {
  "file": "data/math/cut1/edited/rows_edited.jsonl.bak_20260914_190247",
  "bytes": 31698761,
  "sha256": "4063b575c26583f2"
 },
 {
  "file": "data/math/cut1/edited/rows_edited.jsonl.bak_20260914_193508",
  "bytes": 31698765,
  "sha256": "4c495bafe675206a"
 },
 {
  "file": "data/math/cut2/out/fidelity_adjudicated.jsonl.bak_20260914_190247",
  "bytes": 92018,
  "sha256": "b1ec79a9b701ebb6"
 },
 {
  "file": "data/math/cut2/out/fidelity_adjudicated.jsonl.bak_20260914_190500",
  "bytes": 75496,
  "sha256": "db309e496b8f21d7"
 },
 {
  "file": "data/math/cut2/out/fidelity_adjudicated.jsonl.bak_20260914_192045",
  "bytes": 78309,
  "sha256": "979c93a48304bbed"
 },
 {
  "file": "data/math/cut2/out/fidelity_adjudicated.jsonl.bak_20260914_192656",
  "bytes": 78133,
  "sha256": "5f58f03ad5087985"
 },
 {
  "file": "data/math/cut2/out/fidelity_adjudicated.jsonl.bak_20260914_193419",
  "bytes": 74455,
  "sha256": "694c8d243c375556"
 },
 {
  "file": "data/math/cut2/out/fidelity_all.jsonl.bak_20260914_190247",
  "bytes": 816469,
  "sha256": "48d2ef09ca3659d3"
 },
 {
  "file": "data/math/cut2/out/fidelity_all.jsonl.bak_20260914_190500",
  "bytes": 783319,
  "sha256": "02b5c46f7cf7805f"
 },
 {
  "file": "data/math/cut2/out/fidelity_all.jsonl.bak_20260914_192045",
  "bytes": 794221,
  "sha256": "9a95d1a71fc29229"
 },
 {
  "file": "data/math/cut2/out/fidelity_all.jsonl.bak_20260914_192656",
  "bytes": 793856,
  "sha256": "dd8a63300d854d55"
 },
 {
  "file": "data/math/cut2/out/fidelity_all.jsonl.bak_20260914_193419",
  "bytes": 787996,
  "sha256": "cb1f0183cbc26b12"
 },
 {
  "file": "data/math/cut2/out/fidelity_audit_passes.jsonl.bak_20260914_193419",
  "bytes": 18751,
  "sha256": "d563df1ede4082b1"
 },
 {
  "file": "data/math/cut2/out/fidelity_sample.jsonl.bak_20260914_193419",
  "bytes": 19674,
  "sha256": "ea4d7a7a62568c48"
 },
 {
  "file": "data/math/cut2/out/level5_problems_el.jsonl.bak_20260914_190247",
  "bytes": 4427729,
  "sha256": "7885a0008f70c609"
 },
 {
  "file": "data/math/cut2/out/level5_problems_el.jsonl.bak_20260914_190500",
  "bytes": 4427180,
  "sha256": "c101a3ac21a9057b"
 },
 {
  "file": "data/math/cut2/out/level5_problems_el.jsonl.bak_20260914_192045",
  "bytes": 4428468,
  "sha256": "03170fa906a3db96"
 },
 {
  "file": "data/math/cut2/out/level5_problems_el.jsonl.bak_20260914_192656",
  "bytes": 4431576,
  "sha256": "87de18bddd46aa2f"
 },
 {
  "file": "data/math/cut2/out/level5_problems_el.jsonl.bak_retranslate_192658",
  "bytes": 4431052,
  "sha256": "76d514a219b1924e"
 },
 {
  "file": "data/math/cut2/out/level5_problems_el.jsonl.bak_retranslate_193421",
  "bytes": 4406596,
  "sha256": "f3bd61d0bafef1df"
 },
 {
  "file": "data/math/cut2/out/level5_solutions_el_high.jsonl.bak_20260914_190247",
  "bytes": 3309807,
  "sha256": "3ac44ac8894613e5"
 },
 {
  "file": "data/math/cut2/out/solutions_el.jsonl.bak_20260914_190247",
  "bytes": 13472541,
  "sha256": "8ffcd0a8b45daaa9"
 },
 {
  "file": "data/math/cut2/out/solutions_el_l4_high.jsonl.bak_20260914_190247",
  "bytes": 2356098,
  "sha256": "fff42dc9449e9065"
 },
 {
  "file": "data/math/cut2/out/solutions_el_l4_high.jsonl.bak_20260914_190500",
  "bytes": 2356102,
  "sha256": "4b23e9c064db53c4"
 },
 {
  "file": "data/math/cut2/out/solutions_el_repair_high.jsonl.bak_20260914_190247",
  "bytes": 389077,
  "sha256": "8ea7bc33221c4f06"
 },
 {
  "file": "data/math/cut2/out/validity.jsonl.bak_20260914_190247",
  "bytes": 3595012,
  "sha256": "1c0b8afaa231f95f"
 },
 {
  "file": "data/math/cut2/out/validity.jsonl.bak_20260914_190500",
  "bytes": 3550777,
  "sha256": "b925c1f2981c31b2"
 },
 {
  "file": "data/math/cut2/out/validity.jsonl.bak_20260914_192045",
  "bytes": 3597137,
  "sha256": "43174f4287fd1610"
 },
 {
  "file": "data/math/cut2/out/validity.jsonl.bak_20260914_192656",
  "bytes": 3597137,
  "sha256": "6568aee9b0802c24"
 },
 {
  "file": "data/math/cut2/out/validity.jsonl.bak_20260914_193419",
  "bytes": 3593670,
  "sha256": "567feb7cb61db817"
 },
 {
  "file": "data/math/cut2/prep/translations_with_reference.jsonl.bak_20260914_190247",
  "bytes": 13761235,
  "sha256": "0abe79a2f6db733e"
 },
 {
  "file": "data/math/cut2/prep/translations_with_reference.jsonl.bak_20260914_193508",
  "bytes": 13761239,
  "sha256": "f550fde386b7e75e"
 }
]
--- the requested final row bodies, unabridged ---
--- rows_M0 c1b_gsm_310 meta={"generation_file": null, "polished": null, "validity_severity": null, "validity_key": null}
USER: Σε ένα δάσος υπάρχουν 4 είδη δέντρων: βελανιδιές, πεύκα, έλατα και σημύδες. Συνολικά υπάρχουν 4.000 δέντρα στο δάσος. Τα έλατα αποτελούν το 10% όλων των δέντρων και τα πεύκα το 13%. Οι βελανιδιές είναι τόσες όσα τα έλατα και τα πεύκα μαζί. Πόσες σημύδες υπάρχουν στο δάσος;
ASSISTANT: Έλατα:
4.000 · 10% = 400
Πεύκα:
4.000 · 13% = 520
Βελανιδιές:
400 + 520 = 920
Έλατα, πεύκα και βελανιδιές:
400 + 520 + 920 = 1.840
Σημύδες:
4.000 − 1.840 = 2.160
Απάντηση: 2.160 δέντρα
\boxed{2160}

--- rows_M0 c1b_gsm_3230 meta={"generation_file": null, "polished": null, "validity_severity": null, "validity_key": null}
USER: Η Χριστίνα μπορεί να τρέχει τρεις φορές πιο γρήγορα από τον Σάββα. Αν η Χριστίνα κάνει 12 γύρους στο γήπεδο ποδοσφαίρου ενηλίκων και, στο ίδιο χρονικό διάστημα, ο Σάββας τρέχει γύρω από το παιδικό γήπεδο ποδοσφαίρου, του οποίου η περίμετρος είναι η μισή από εκείνη του άλλου γηπέδου, πόσους γύρους έκανε ο Σάββας στο παιδικό γήπεδο;
ASSISTANT: Έστω Π η περίμετρος του γηπέδου ενηλίκων.
Η Χριστίνα διανύει 12 · Π.
Ο Σάββας τρέχει με το 1/3 της ταχύτητας της Χριστίνας.
Η απόσταση του Σάββα είναι (12 · Π) : 3 = 4 · Π.
Η περίμετρος του παιδικού γηπέδου είναι Π : 2.
Οι γύροι του Σάββα είναι (4 · Π) : (Π : 2) = 8.
Απάντηση: 8 γύρους
\boxed{8}

--- rows_M0 c1b_gsm_3505 meta={"generation_file": null, "polished": null, "validity_severity": null, "validity_key": null}
USER: Η Μαντὠ θέλει να φυτέψει λουλούδια στον κήπο της, ώστε να ανθίσουν 20. Υπολογίζει ότι περίπου οι μισοί από τους σπόρους που θα φυτέψει θα ξεραθούν πριν ανθίσουν. Ωστόσο, το ανθοπωλείο πουλά μόνο φακελάκια με 25 σπόρους το καθένα. Κάθε φακελάκι κοστίζει 5 €. Πόσα χρήματα θα ξοδέψει η Μαντώ για σπόρους, ώστε να φυτέψει 20 λουλούδια;
ASSISTANT: 20 · 2 = 40 σπόροι
40 : 25 = 1,6 φακελάκια
Χρειάζονται 2 ολόκληρα φακελάκια.
2 · 5 € = 10 €
Απάντηση: 10 €
\boxed{10}

--- rows_M1 c2_gsm_310 meta={"generation_file": "solutions_el_repair_high.jsonl", "polished": "edited", "validity_severity": "none", "validity_key": "gsm_310|b488b7ce"}
USER: Σε ένα δάσος υπάρχουν 4 είδη δέντρων: βελανιδιές, πεύκα, έλατα και σημύδες. Συνολικά υπάρχουν 4.000 δέντρα στο δάσος. Τα έλατα αποτελούν το 10% όλων των δέντρων και τα πεύκα το 13%. Οι βελανιδιές είναι τόσες όσα τα έλατα και τα πεύκα μαζί. Πόσες σημύδες υπάρχουν στο δάσος;
ASSISTANT: Αρχικά υπολογίζουμε πόσα είναι τα έλατα. Αποτελούν το 10% των 4.000 δέντρων, επομένως:

\[
\frac{10}{100}\cdot 4.000=400
\]

Άρα στο δάσος υπάρχουν 400 έλατα.

Στη συνέχεια υπολογίζουμε τα πεύκα, τα οποία αποτελούν το 13% του συνόλου:

\[
\frac{13}{100}\cdot 4.000=520
\]

Άρα υπάρχουν 520 πεύκα.

Οι βελανιδιές είναι τόσες όσες τα έλατα και τα πεύκα μαζί. Επομένως, ο αριθμός τους είναι:

\[
400+520=920
\]

Άρα υπάρχουν 920 βελανιδιές.

Για να βρούμε πόσες σημύδες υπάρχουν, αφαιρούμε από το σύνολο των 4.000 δέντρων τα έλατα, τα πεύκα και τις βελανιδιές:

\[
4.000-920-520-400=2.160
\]

Επομένως, στο δάσος υπάρχουν 2.160 σημύδες. Ο ζητούμενος αριθμός, γραμμένος ακριβώς ως ακέραιος χωρίς διαχωριστικό χιλιάδων, είναι:

\[
\boxed{2160}
\]

--- rows_M1 c2_gsm_3230 meta={"generation_file": "solutions_el_repair_high.jsonl", "polished": "edited", "validity_severity": "none", "validity_key": "gsm_3230|cee0e61d"}
USER: Η Χριστίνα μπορεί να τρέχει τρεις φορές πιο γρήγορα από τον Σάββα. Αν η Χριστίνα κάνει 12 γύρους στο γήπεδο ποδοσφαίρου ενηλίκων και, στο ίδιο χρονικό διάστημα, ο Σάββας τρέχει γύρω από το παιδικό γήπεδο ποδοσφαίρου, του οποίου η περίμετρος είναι η μισή από εκείνη του άλλου γηπέδου, πόσους γύρους έκανε ο Σάββας στο παιδικό γήπεδο;
ASSISTANT: Η Χριστίνα τρέχει τρεις φορές πιο γρήγορα από τον Σάββα. Επομένως, στο ίδιο χρονικό διάστημα, ο Σάββας διανύει το ένα τρίτο της απόστασης που διανύει η Χριστίνα.

Η Χριστίνα κάνει 12 γύρους στο γήπεδο ενηλίκων. Άρα η απόσταση που διανύει ο Σάββας αντιστοιχεί σε:

\[
12 \div 3 = 4
\]

Δηλαδή, ο Σάββας διανύει απόσταση ίση με 4 γύρους του γηπέδου ενηλίκων.

Όμως η περίμετρος του παιδικού γηπέδου είναι η μισή περίμετρος του γηπέδου ενηλίκων. Συνεπώς, μία περίμετρος του γηπέδου ενηλίκων αντιστοιχεί σε 2 γύρους του παιδικού γηπέδου.

Άρα οι 4 γύροι του γηπέδου ενηλίκων αντιστοιχούν σε:

\[
4 \cdot 2 = 8
\]

Επομένως, ο Σάββας έκανε 8 γύρους στο παιδικό γήπεδο.

\[
\boxed{8}
\]

--- rows_M1 c2_gsm_3505 meta={"generation_file": "solutions_el_repair_high.jsonl", "polished": "unchanged", "validity_severity": "none", "validity_key": "gsm_3505|6265b2bf"}
USER: Η Μαντὠ θέλει να φυτέψει λουλούδια στον κήπο της, ώστε να ανθίσουν 20. Υπολογίζει ότι περίπου οι μισοί από τους σπόρους που θα φυτέψει θα ξεραθούν πριν ανθίσουν. Ωστόσο, το ανθοπωλείο πουλά μόνο φακελάκια με 25 σπόρους το καθένα. Κάθε φακελάκι κοστίζει 5 €. Πόσα χρήματα θα ξοδέψει η Μαντώ για σπόρους, ώστε να φυτέψει 20 λουλούδια;
ASSISTANT: Αφού περίπου οι μισοί σπόροι θα ξεραθούν πριν ανθίσουν, αναμένεται να ανθίσει μόνο το 
\[
\frac{1}{2}
\]
των σπόρων που θα φυτέψει η Μαντώ.

Για να ανθίσουν 20 λουλούδια, πρέπει επομένως να αγοράσει διπλάσιους σπόρους:
\[
2\cdot 20=40 \text{ σπόροι}.
\]

Κάθε φακελάκι περιέχει 25 σπόρους. Ένα φακελάκι δεν αρκεί, επειδή:
\[
25<40.
\]

Άρα η Μαντώ πρέπει να αγοράσει 2 φακελάκια. Με αυτά θα έχει συνολικά:
\[
2\cdot 25=50 \text{ σπόρους},
\]
δηλαδή τουλάχιστον τους 40 σπόρους που χρειάζεται.

Κάθε φακελάκι κοστίζει 5 €, οπότε το συνολικό ποσό που θα ξοδέψει είναι:
\[
2\cdot 5=10\text{ €}.
\]

Επομένως, η Μαντώ θα ξοδέψει συνολικά 10 € για τους σπόρους.

\[
\boxed{10}
\]

--- rows_M2_extra c2_math5_746 meta={"generation_file": "level5_solutions_el_high.jsonl", "polished": "edited", "validity_severity": "none", "validity_key": "math5_746|0b2be05c"}
USER: Στο παρακάτω διάγραμμα, τα σημεία $A$, $B$, $C$ και $P$ είναι τοποθετημένα έτσι ώστε $PA=2$, $PB=3$, $PC=4$ και $BC=5$. Ποιο είναι το μέγιστο δυνατό εμβαδόν του $\triangle ABC$; [asy]
defaultpen(linewidth(0.8)); size(150);
pair B = (0,0), C = (5,0), A = (2,3), P = (2.2,2);
draw(A--B--C--cycle^^B--P^^C--P^^A--P);
label("$A$",A,N); label("$B$",B,S); label("$C$",C,S); label("$P$",P,S);
[/asy]
ASSISTANT: Αφού $PB=3$, $PC=4$ και $BC=5$, παρατηρούμε ότι
\[
PB^2+PC^2=3^2+4^2=9+16=25=5^2=BC^2.
\]
Επομένως, από το αντίστροφο του Πυθαγόρειου θεωρήματος, το τρίγωνο $PBC$ είναι ορθογώνιο στο $P$.

Άρα το εμβαδόν του είναι
\[
[\triangle PBC]=\frac12\cdot PB\cdot PC
=\frac12\cdot3\cdot4=6.
\]

Έστω $H$ το ίχνος της καθέτου από το $P$ προς την ευθεία $BC$. Χρησιμοποιώντας τώρα ως βάση την $BC=5$, έχουμε
\[
[\triangle PBC]=\frac12\cdot BC\cdot PH.
\]
Άρα
\[
6=\frac12\cdot5\cdot PH
\]
και επομένως
\[
12=5PH \quad\Longrightarrow\quad PH=\frac{12}{5}.
\]

Έστω $h$ η απόσταση του $A$ από την ευθεία $BC$. Τότε
\[
[\triangle ABC]=\frac12\cdot BC\cdot h
=\frac12\cdot5\cdot h.
\]
Επομένως, για να μεγιστοποιηθεί το εμβαδόν, πρέπει να μεγιστοποιηθεί το ύψος $h$.

Το σημείο $A$ απέχει σταθερή απόσταση $AP=2$ από το $P$, άρα κινείται σε κύκλο με κέντρο $P$ και ακτίνα $2$. Η μεγαλύτερη δυνατή απόσταση του $A$ από την $BC$ προκύπτει όταν το $A$ βρίσκεται πάνω στην κάθετη προς την $BC$ που περνά από το $P$, στην πλευρά του $P$ που απομακρύνεται από την $BC$. Τότε
\[
h=PH+PA=\frac{12}{5}+2
=\frac{12}{5}+\frac{10}{5}
=\frac{22}{5}.
\]

Άρα το μέγιστο δυνατό εμβαδόν είναι
\[
[\triangle ABC]_{\max}
=\frac12\cdot5\cdot\frac{22}{5}
=\frac{22}{2}
=\boxed{11}.
\]

=== §D ANSWERS ===
Q1: fixtures Y, Z, Z2 above; aggregate-only inputs stay valid (fixtures P, Q use aggregates only).
Q2: the auditor is inlined; a corrupted command at the very beginning of a field is now handled (self-test 1: '\\nabla f' from LF+'abla f') and the audit re-ran with it (0 residual rows); the backup inventory is inlined (32 files); the 'zero ambiguous repairs' figure was measured by re-running the rules on the earliest backups (suffix 190247) of every stored file.
Q3: the four row bodies are inlined; the disposition table gives every touched id its terminal state with the exported row hash or the exclusion reason (a Level-5 retranslation that the guard rejected on every retry has no record and is excluded; the count of such exclusions is in the table).
