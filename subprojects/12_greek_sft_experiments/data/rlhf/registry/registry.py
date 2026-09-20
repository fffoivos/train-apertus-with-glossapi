#!/usr/bin/env python3
"""Prompt registry for generator 0.2/0.3 (PROMPT_INGESTION_AND_NEXT_500_PLAN_20260917.md §2–§4; spec v1.0 §5.5–§5.7).
Idempotent import of every existing prompt, seed, source, judgement and pair credit, with stable logical IDs and aliases, then the three
per-cell ledgers (A available prompts, E validated eligible pairs, y forecast yield) and the size/coverage frontier.
Usage:
  python3 data/rlhf/registry/registry.py import          # safe to repeat; prints counts
  python3 data/rlhf/registry/registry.py report [--sizes 500,750,1000]   # writes registry_report.json/.md
State: data/rlhf/registry/registry.sqlite (derived; delete and re-import to rebuild)."""
import argparse, collections, hashlib, json, math, pathlib, re, sqlite3, unicodedata
HERE = pathlib.Path(__file__).resolve().parent; RL = HERE.parent; POOL = RL / 'pool'; DB = HERE / 'registry.sqlite'
SPEC = RL.parents[1] / 'docs' / 'SEED_LABEL_SPEC_20260917.md'; GLOSSARY = RL / 'prompts' / 'seed_label_definitions_v1.md'
TARGET = json.load(open(RL / 'target_distribution_v1.json'))
PURPOSES = list(TARGET['primary_purpose_shares_percent']); LANGS = list(TARGET['language_shares_percent'])
FORUM_PURPOSE = {'question': 'factual', 'explanation': 'factual', 'calculation': 'math', 'advice': 'everyday', 'opinion': 'everyday', 'share': 'everyday', 'translation': 'everyday', 'other': 'everyday', 'create': 'everyday'}
RUBRIC_SHA16 = '8aa32f266afd08b4'
RELABEL = {json.loads(l)['id']: json.loads(l) for l in open(HERE / 'relabel_v1.jsonl')} if (HERE / 'relabel_v1.jsonl').exists() else {}
J = lambda p: [json.loads(l) for l in open(p) if l.strip()]
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
def norm(s): return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s or '')).strip()
def canon_messages(msgs): return sha(json.dumps([[m['role'], norm(m['content'])] for m in msgs], ensure_ascii=False))
MATHS_CUE = re.compile(r'(υπολόγ|πόσ[οαη]|κόστ|ευρώ|€|%|ποσοστ|μέσ[οη]ς? όρο|εξίσωσ|πιθανότητ|calculat|how much|how many|total|average|percent|equation|probabilit)', re.I)
def maths_flag(purpose, task_type, forum, text):
    if purpose == 'math' or task_type == 'calculation' or forum == 'mathematica': return 'maths'
    nums = re.findall(r'\d+(?:[.,]\d+)?', text or '')
    return 'maths_candidate' if len(nums) >= 2 and MATHS_CUE.search(text or '') else None
SCHEMA = """
CREATE TABLE IF NOT EXISTS sources(source_id TEXT PRIMARY KEY, kind TEXT, forum TEXT, url TEXT, gate_version TEXT, file TEXT, row_id TEXT, content_sha TEXT, status TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS seeds(seed_id TEXT PRIMARY KEY, generator_version TEXT, file TEXT, seed_json TEXT, seed_canonical TEXT, task TEXT, language TEXT, register TEXT, attitude TEXT, detail TEXT, status TEXT, compatibility_issue TEXT);
CREATE TABLE IF NOT EXISTS prompts(logical_id TEXT PRIMARY KEY, version INTEGER, messages TEXT, canonical_sha TEXT, source_kind TEXT, generator_version TEXT, round_first TEXT, primary_purpose TEXT, task_type TEXT, language TEXT, forum TEXT, detail TEXT, register TEXT, attitude TEXT, seed_id TEXT, seed_status TEXT, source_id TEXT, keepable INTEGER, status TEXT, status_reason TEXT, maths_content TEXT, words INTEGER, labels TEXT);
CREATE TABLE IF NOT EXISTS aliases(alias TEXT PRIMARY KEY, logical_id TEXT, round TEXT, file TEXT);
CREATE TABLE IF NOT EXISTS judgements(judgement_id TEXT PRIMARY KEY, logical_id TEXT, alias TEXT, batch INTEGER, rubric_sha TEXT, verdicts TEXT, ranking TEXT, margin TEXT, file TEXT, active INTEGER);
CREATE TABLE IF NOT EXISTS pair_credit(logical_id TEXT PRIMARY KEY, eligible INTEGER, reason TEXT, judgement_id TEXT, chosen_k INTEGER, rejected_k INTEGER, chosen_sha TEXT, rejected_sha TEXT);
"""
def connect():
    c = sqlite3.connect(DB); c.executescript(SCHEMA); return c
def logical_id_for(kind, key): return {'forum': 'fp', 'seeded': 'sp', 'template': 'tp', 'dialogue': 'dp'}[kind] + ':' + sha(key)[:16]
def do_import():
    c = connect(); cur = c.cursor()
    # sources: forum gated pool (gate v3), one per url
    gated = J(POOL / 'forum_gated_v3.jsonl'); by_url = collections.defaultdict(list)
    for r in gated: by_url[r['url']].append(r)
    for url, rs in by_url.items():
        r = rs[0]; g = r.get('gate') or {}
        accepted = g.get('post_kind') in ('request', 'social') and str(g.get('self_contained')) == 'True' and bool((g.get('prompt_el') or '').strip())
        cur.execute('INSERT OR IGNORE INTO sources VALUES (?,?,?,?,?,?,?,?,?,?)', ('fs:' + sha(url)[:16], 'forum_post', r['forum'], url, 'forum-gate-v3', 'pool/forum_gated_v3.jsonl', ','.join(x['id'] for x in rs), sha(norm(r.get('text', ''))), 'gate_accepted' if accepted else 'gate_rejected',
                    json.dumps({'gated_ids': [x['id'] for x in rs], 'task_type_v3': g.get('task_type'), 'prompt_el': g.get('prompt_el'), 'post_kind': g.get('post_kind'), 'false_premise': g.get('false_premise')}, ensure_ascii=False)))
    # seeds: round-2 seed batches (generator 0.2 prototype), curator seeds (0.1), dialogue manifest (0.1 fixtures)
    for f in sorted((RL / 'gen02_demo').glob('round2_batch*.json')):
        for it in json.load(open(f))['items']:
            s = it['seed']; substantive = {k: v for k, v in s.items() if k not in ('id', 'seed_hash')}
            issue = 'greeklish_with_non_greek_language' if s['register'] == 'greeklish' and s['language'] != 'el' else None
            cur.execute('INSERT OR IGNORE INTO seeds VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', ('seed:0.2:' + s['id'], '0.2-prototype', str(f.relative_to(RL)), json.dumps(it, ensure_ascii=False), sha(json.dumps(substantive, sort_keys=True, ensure_ascii=False)), s['task'], s['language'], s['register'], s['attitude'], s['detail'].split(':')[0], 'generated', issue))
    for r in J(RL / 'prompt_generator/runtime/runs/round1_121/curator.jsonl'):
        s = r['seed']; cur.execute('INSERT OR IGNORE INTO seeds VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', ('seed:0.1:' + r['id'], '0.1', 'prompt_generator/runtime/runs/round1_121/curator.jsonl', json.dumps(s, ensure_ascii=False, default=str), s.get('instance_hash'), s.get('purpose'), s.get('language'), s.get('register'), s.get('attitude'), None, 'generated', None))
    man = json.load(open(RL / 'dialogue_quality_depth/runtime/manifest.json'))
    for s in man['seeds']:
        cur.execute('INSERT OR IGNORE INTO seeds VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', ('seed:dialogue-v1:' + s['trajectory_id'], 'dialogue-quality-depth-v1 (0.1 fixtures)', 'dialogue_quality_depth/runtime/manifest.json', json.dumps(s, ensure_ascii=False, default=str), s.get('instance_hash'), s.get('task'), s.get('language'), s.get('register'), s.get('attitude'), None, 'generated', None))
    excl = set(json.load(open(POOL / 'round1_excluded_json_leak.json')))
    for rnd, pool in (('round1', 'round1_all.jsonl'), ('round2', 'round2_all.jsonl')):
        for r in J(POOL / pool):
            text = r['messages'][-1]['content']; forum = r['id'].split(':')[1] if r['slice'] == 'forum' else None
            if forum:
                url = r['source'].split(' ', 1)[1]; kind = 'forum'; lid = logical_id_for('forum', url); gen = 'forum-gate-v3'; seed_id = None; seed_status = 'not_applicable'; src = 'fs:' + sha(url)[:16]
            elif rnd == 'round1':
                kind = 'template'; lid = logical_id_for('template', canon_messages(r['messages'])); gen = '0.1'; seed_id = 'seed:0.1:' + r['id'].split(':', 1)[1]; seed_status = 'bound'; src = None
            else:
                kind = 'seeded'; lid = logical_id_for('seeded', canon_messages(r['messages'])); gen = '0.2-prototype'; seed_id = 'seed:0.2:' + r['id'].split(':', 1)[1]
                ok = cur.execute('SELECT seed_json FROM seeds WHERE seed_id=?', (seed_id,)).fetchone()
                seed_status = 'bound' if ok and norm(json.loads(ok[0])['message']) == norm(text) else 'unknown'; src = None
            status, reason = 'active', None
            if r['id'] in excl: status, reason = 'excluded', 'json_leak'
            elif gen == '0.1': status, reason = 'archived', 'defunct_generator_0.1'
            keepable = int(status == 'active')
            task_type = r.get('task_type') or r.get('family'); purpose = r['purpose']; mf = maths_flag(purpose, task_type, forum, text)
            rl = RELABEL.get(src) if forum else (RELABEL.get(lid) if kind == 'seeded' else None)
            if rl and forum:
                task_type = rl['task_type']; purpose = FORUM_PURPOSE[task_type]
            if rl:
                mf = 'maths' if (rl['maths_content'] or purpose == 'math') else None
            labels = {k: r.get(k) for k in ('false_premise', 'post_kind', 'kept_details', 'difficulty', 'story') if r.get(k) is not None}
            if rl: labels.update(task_type_v3=r.get('task_type'), purpose_before_relabel=r['purpose'], relabel_version=rl['relabel_version'], relabel_glossary_sha16=rl['glossary_sha16'], maths_ambiguity=rl['maths_ambiguity'])
            cur.execute('INSERT OR REPLACE INTO prompts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (lid, 1, json.dumps(r['messages'], ensure_ascii=False), canon_messages(r['messages']), kind, gen, rnd, purpose, task_type, r['language'], forum, r.get('detail'), r.get('register'), r.get('attitude'), seed_id, seed_status, src, keepable, status, reason, mf, len(re.findall(r'\w+', text)), json.dumps(labels, ensure_ascii=False, default=str)))
            cur.execute('INSERT OR IGNORE INTO aliases VALUES (?,?,?,?)', (r['id'], lid, rnd, 'pool/' + pool))
            if seed_id: cur.execute("UPDATE seeds SET status='selected' WHERE seed_id=?", (seed_id,))
    cur.execute("UPDATE seeds SET status='unselected' WHERE status='generated'")   # spec §5.4: a recovered seed with no bound prompt is unselected
    traj = {}
    for t in J(RL / 'dialogue_quality_depth/runtime/measurement/trajectories.jsonl'): traj[t['trajectory_id']] = t
    for tid, t in traj.items():
        s = next(x for x in man['seeds'] if x['trajectory_id'] == tid); lid = logical_id_for('dialogue', 'dialogue-v1:' + tid)
        cur.execute('INSERT OR IGNORE INTO prompts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (lid, 1, json.dumps(t['messages'][:1], ensure_ascii=False), canon_messages(t['messages'][:1]), 'dialogue', 'dialogue-quality-depth-v1', 'dialogue-pilot', 'dialogue', f"{s['task']}/{s['family']}", s['language'], None, None, s['register'], s['attitude'], 'seed:dialogue-v1:' + tid, 'bound', None, 0, 'archived', 'built_on_defunct_0.1_seeds', 'maths_candidate' if s['task'] == 'math' or s['family'] == 'e_plan' else None, None, json.dumps({'assistant_turns': t['assistant_turns'], 'terminal': t['terminal_code']})))
        cur.execute('INSERT OR IGNORE INTO aliases VALUES (?,?,?,?)', ('dialogue:' + tid, lid, 'dialogue-pilot', 'dialogue_quality_depth/runtime/measurement/trajectories.jsonl'))
    # judgements and pair credit (E): within one judged batch, chosen = top-ranked reinforce, rejected = lowest-ranked non-reinforce, margin clear, distinct texts
    samples = {}
    for f in ('round1_all_samples.jsonl', 'round2_all_samples.jsonl'):
        for s in J(POOL / f): samples[(s['id'], s['k'])] = s['text']
    for rnd, f in (('round1', 'round1_all_judged.jsonl'), ('round2', 'round2_all_judged.jsonl')):
        for r in J(POOL / f):
            if r.get('error') or r.get('pass', 1) != 1: continue
            lid = cur.execute('SELECT logical_id FROM aliases WHERE alias=?', (r['id'],)).fetchone()
            if not lid: continue
            jid = sha(f"{f}|{r['id']}|{r.get('batch', 0)}")[:20]
            cur.execute('INSERT OR IGNORE INTO judgements VALUES (?,?,?,?,?,?,?,?,?,?)', (jid, lid[0], r['id'], r.get('batch', 0), r.get('rubric_sha'), json.dumps({k: v.get('verdict') for k, v in r['by_k'].items()}), json.dumps(r['ranking_k']), (r.get('verdict') or {}).get('best_vs_worst'), 'pool/' + f, 1))
    cur.execute('DELETE FROM pair_credit')
    for lid, keepable, mf, status in cur.execute('SELECT logical_id, keepable, maths_content, status FROM prompts').fetchall():
        rows = cur.execute('SELECT judgement_id, alias, verdicts, ranking, margin, rubric_sha FROM judgements WHERE logical_id=? ORDER BY alias, batch', (lid,)).fetchall()
        if not rows: continue
        eligible, reason, best = 0, 'no_batch_meets_pair_rule', None
        for jid, alias, verdicts, ranking, margin, rsha in rows:
            v = json.loads(verdicts); rk = json.loads(ranking)
            ch = next((k for k in rk if v.get(str(k)) == 'reinforce'), None); rj = next((k for k in reversed(rk) if v.get(str(k)) != 'reinforce'), None)
            if ch is None or rj is None or margin != 'clear' or rsha != RUBRIC_SHA16: continue
            tc, tr = samples.get((alias, ch)), samples.get((alias, rj))
            if tc is None or tr is None or norm(tc) == norm(tr): continue
            best = (jid, ch, rj, sha(norm(tc))[:16], sha(norm(tr))[:16]); break
        if best:
            if not keepable: eligible, reason = 0, f'not_keepable:{status}'
            elif mf: eligible, reason = 0, f'held:{mf}_pending_specialist_judge'
            else: eligible, reason = 1, 'eligible'
        cur.execute('INSERT INTO pair_credit VALUES (?,?,?,?,?,?,?,?)', (lid, eligible, reason, *(best if best else (None, None, None, None, None))))
    c.commit(); return c
def counts(c):
    q = lambda s, *a: c.execute(s, a).fetchall()
    return dict(prompts_by_kind_status=q('SELECT source_kind, generator_version, status, COUNT(*) FROM prompts GROUP BY 1,2,3'),
                aliases=q('SELECT COUNT(*) FROM aliases')[0][0], logical_prompts=q('SELECT COUNT(*) FROM prompts')[0][0],
                duplicate_groups=q('SELECT logical_id, GROUP_CONCAT(alias) FROM aliases GROUP BY logical_id HAVING COUNT(*)>1'),
                seeds=q('SELECT generator_version, status, COUNT(*) FROM seeds GROUP BY 1,2'), seed_binding=q("SELECT seed_status, COUNT(*) FROM prompts WHERE generator_version='0.2-prototype' GROUP BY 1"),
                compatibility_issues=q('SELECT seed_id, compatibility_issue, status FROM seeds WHERE compatibility_issue IS NOT NULL'),
                judgements=q('SELECT COUNT(*) FROM judgements')[0][0], pair_credit=q('SELECT reason, COUNT(*) FROM pair_credit GROUP BY 1'),
                maths=q('SELECT maths_content, status, COUNT(*) FROM prompts WHERE maths_content IS NOT NULL GROUP BY 1,2'))
def joint_targets(N):
    """Integer targets per purpose x language cell whose row sums equal the purpose margins and column sums equal the language margins exactly (both by largest remainder over N)."""
    def lr(total, shares):
        raw = {k: total * s / sum(shares.values()) for k, s in shares.items()}; base = {k: math.floor(v) for k, v in raw.items()}
        for k in sorted(raw, key=lambda k: raw[k] - base[k], reverse=True)[: total - sum(base.values())]: base[k] += 1
        return base
    pm = lr(N, TARGET['primary_purpose_shares_percent']); lm = lr(N, TARGET['language_shares_percent'])
    ps, ls = TARGET['primary_purpose_shares_percent'], TARGET['language_shares_percent']
    raw = {(p, l): N * ps[p] / sum(ps.values()) * ls[l] / sum(ls.values()) for p in PURPOSES for l in LANGS}
    for _ in range(200):   # iterative proportional fitting to the integer margins
        for p in PURPOSES:
            s = sum(raw[(p, l)] for l in LANGS); raw.update({(p, l): raw[(p, l)] * pm[p] / s for l in LANGS} if s else {})
        for l in LANGS:
            s = sum(raw[(p, l)] for p in PURPOSES); raw.update({(p, l): raw[(p, l)] * lm[l] / s for p in PURPOSES} if s else {})
    T = {k: math.floor(v) for k, v in raw.items()}
    rrem = {p: pm[p] - sum(T[(p, l)] for l in LANGS) for p in PURPOSES}; crem = {l: lm[l] - sum(T[(p, l)] for p in PURPOSES) for l in LANGS}
    for (p, l) in sorted(raw, key=lambda k: (raw[k] - T[k], k), reverse=True):   # controlled rounding: largest fractions first, within both margins
        if rrem[p] > 0 and crem[l] > 0: T[(p, l)] += 1; rrem[p] -= 1; crem[l] -= 1
    for p in PURPOSES:                                                              # pair off any leftover row and column units exactly
        for l in LANGS:
            while rrem[p] > 0 and crem[l] > 0: T[(p, l)] += 1; rrem[p] -= 1; crem[l] -= 1
    assert all(sum(T[(p, l)] for l in LANGS) == pm[p] for p in PURPOSES) and all(sum(T[(p, l)] for p in PURPOSES) == lm[l] for l in LANGS)
    return T
def maths_calibration():
    """(prompts with an eligible positive and a non-positive reply, prompts judged) from the maths specialist calibration, verified references only."""
    f = RL / 'maths_judge' / 'calibration' / 'judged.jsonl'
    if not f.exists(): return None
    by = collections.defaultdict(lambda: [0, 0])
    for l in open(f):
        x = json.loads(l)
        if x.get('reference_status') != 'verified': by[x['id']][1] = -1; continue
        for v in x['by_k'].values(): by[x['id']][0] += bool(v['eligible_positive']); by[x['id']][1] += 0 if by[x['id']][1] < 0 else 1
    ok = [k for k, (pos, n) in by.items() if n > 0 and 0 < pos < n]
    return (len(ok), len(by))
MATHS_CAL = maths_calibration()
def wilson(k, n, z=1.2816):
    if n == 0: return (0.0, 1.0)
    ph = k / n; d = 1 + z * z / n; c0 = ph + z * z / (2 * n); r = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return ((c0 - r) / d, (c0 + r) / d)
def report(c, sizes):
    E = collections.Counter(); judged = collections.Counter(); judged_elig = collections.Counter()
    for lid, p, l, elig, reason, kind in c.execute('SELECT p.logical_id, p.primary_purpose, p.language, pc.eligible, pc.reason, p.source_kind FROM prompts p JOIN pair_credit pc USING(logical_id) WHERE p.keepable=1'):
        if reason.startswith('held'): continue          # held (maths pending the specialist judge): neither eligible yield nor a judged denominator
        E[(p, l)] += elig; judged[(p, l)] += 1; judged_elig[(p, l)] += elig
    # yield: eligible pairs per judged keepable prompt; maths yield comes from the specialist-judge calibration (below), not from held general-rubric pairs
    y = {}
    pooled = collections.Counter(); pooled_n = collections.Counter()
    for (p, l), n in judged.items(): pooled[p] += judged_elig[(p, l)]; pooled_n[p] += n
    for p in PURPOSES:
        for l in LANGS:
            n, k = judged[(p, l)], judged_elig[(p, l)]
            if p == 'math' and MATHS_CAL:
                kk, nn = MATHS_CAL; y[(p, l)] = dict(estimate=kk / nn, low=wilson(kk, nn)[0] * 0.75, high=wilson(kk, nn)[1], basis=f'provisional: maths specialist judge calibration, round-2 generated maths, {kk}/{nn} prompts with an eligible positive and a lower reply; low widened by 25%')
            elif n >= 10: y[(p, l)] = dict(estimate=k / n, low=wilson(k, n)[0], high=wilson(k, n)[1], basis=f'measured {k}/{n}')
            elif pooled_n[p]: kk, nn = pooled[p], pooled_n[p]; y[(p, l)] = dict(estimate=kk / nn, low=wilson(kk, nn)[0] * 0.75, high=wilson(kk, nn)[1], basis=f'provisional pooled {p} {kk}/{nn}, low widened by 25%')
            else: y[(p, l)] = dict(estimate=None, low=None, high=None, basis='no evidence (dialogue: separate model)')
    used_urls = {r[0] for r in c.execute("SELECT s.url FROM prompts p JOIN sources s ON s.source_id=p.source_id WHERE p.source_kind='forum'")}
    A = collections.Counter(); A_forum = collections.Counter()
    for url, forum, payload, status in c.execute("SELECT url, forum, payload, status FROM sources WHERE kind='forum_post'"):
        if status != 'gate_accepted' or url in used_urls: continue
        sid = 'fs:' + sha(url)[:16]; rl = RELABEL.get(sid); tt = rl['task_type'] if rl else json.loads(payload).get('task_type_v3'); p = FORUM_PURPOSE.get(tt)
        # maths content inside a non-maths post stays available; its replies route to the specialist maths judge (R-PG2 finding 4)
        if p: A[(p, 'el')] += 1; A_forum[forum] += 1
    out = dict(spec=str(SPEC.name), rubric_sha16=RUBRIC_SHA16, maths_calibration=MATHS_CAL, A_definition='provisional available inventory: unused gate-accepted forum posts by relabelled purpose (no owner review status exists); maths-content posts included', E=sum(E.values()), E_by_cell={f'{p}/{l}': E[(p, l)] for p in PURPOSES for l in LANGS if E[(p, l)]},
               A_forum_unused_gate_accepted={f'{p}/{l}': A[(p, l)] for (p, l) in A}, A_by_forum=dict(A_forum), yield_by_cell={f'{p}/{l}': y[(p, l)] for p in PURPOSES for l in LANGS}, frontier={})
    for N in sizes:
        T = joint_targets(N); rows = {}; need_expected = need_conservative = 0
        for p in PURPOSES:
            for l in LANGS:
                t_, e_ = T[(p, l)], E[(p, l)]; yy = y[(p, l)]
                if p == 'dialogue':
                    rows[f'{p}/{l}'] = dict(target=t_, E=e_, A=0, deficit=t_ - e_, new_prompts_expected=None, new_prompts_conservative=None, note='dialogue: reserved starting seeds; yield from the dialogue track'); continue
                a_ = A[(p, l)]
                d_exp = max(0, t_ - e_ - (yy['estimate'] or 0) * a_); d_con = max(0, t_ - e_ - (yy['low'] or 0) * a_)
                g_exp = math.ceil(d_exp / yy['estimate']) if yy['estimate'] else None; g_con = math.ceil(d_con / yy['low']) if yy['low'] else None
                need_expected += g_exp or 0; need_conservative += g_con or 0
                rows[f'{p}/{l}'] = dict(target=t_, E=e_, A=a_, deficit_expected=round(d_exp, 1), deficit_conservative=round(d_con, 1), new_prompts_expected=g_exp, new_prompts_conservative=g_con, yield_basis=yy['basis'])
        dialogue_target = sum(T[('dialogue', l)] for l in LANGS)
        out['frontier'][N] = dict(cells=rows, single_turn_new_prompts_expected=need_expected, single_turn_new_prompts_conservative=need_conservative, dialogue_pairs_target=dialogue_target)
    json.dump(out, open(HERE / 'registry_report.json', 'w'), indent=1, ensure_ascii=False, default=str)
    return out
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['import', 'report']); ap.add_argument('--sizes', default='500,750,1000'); a = ap.parse_args()
    c = do_import() if a.cmd == 'import' else connect()
    if a.cmd == 'import':
        print(json.dumps(counts(c), ensure_ascii=False, indent=1, default=str)[:4000])
    else:
        out = report(c, [int(s) for s in a.sizes.split(',')])
        print('E total', out['E']); print('E by cell', out['E_by_cell']); print('A (unused gate-accepted forum)', out['A_forum_unused_gate_accepted'])
        for N, f in out['frontier'].items(): print(f'N={N}: single-turn new prompts expected {f["single_turn_new_prompts_expected"]}, conservative {f["single_turn_new_prompts_conservative"]}; dialogue pair target {f["dialogue_pairs_target"]}')
