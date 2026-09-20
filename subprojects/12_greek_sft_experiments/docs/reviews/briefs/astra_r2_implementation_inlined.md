Review target: checkpoint R2 of /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/R4_EXEC_PLAN_20260914.md — a RE-REVIEW of the implementation after the owner-run review found six defects (dispositions in the plan's §8b). The complete source of every file under review is INLINED below with line numbers (you have no filesystem access in this session); this is a code review, not a plan review. Data generation is running; nothing has been trained.
What changed since the review you are re-checking:
1. Paired exclusions + shared dev split moved into /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/math/cut2/assemble_cut2.py (pair_too_long with the Apertus tokenizer; dev flags on rows; dev_problems_en.json for the English twins); /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/assemble_continuation.py honours dev flags, refuses over-window rows in Greek blocks, checks replay rows for contamination, sends English twins of dev problems to dev; /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/check_pilot_arms.py asserts M0=M1 prompt sets, M1⊂M2, identical replay/English ids, no benchmark hits, on the FINAL manifests; /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/pilot_chain.sh runs the trainer --dry-run per arm before sbatch.
2. /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/mixlib.py (decontamination rule + exact tokenizer, fails closed) used by /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/assemble_pass_r4.py on base replay, new blocks and maths rows.
3. /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/math/cut2/polish_targets.py keys polish by id|sha8 of the input solution; assemble_cut2 requires a polish disposition per (id, sha) and treats >400 words as a flag, >1,000 as a runaway drop.
4. /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/robustness/correcting/v2/build_v2.py reads scope_revision_train32; /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/benchmarks_el/xstest/judge.py reads prompts_el_final.jsonl.
5. /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/pilot_summary.py requires exactly the 500 MATH-500 ids per arm/language, evaluates guardrails into PASS/FAIL before choosing, reads an optional adjudication file; /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/benchmarks_el/math500/adjudicate_unresolved.py (Sol, bounded to rows with no extracted answer; secondary to equiv500).
6. /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/benchmarks_el/math200_confirm/build.py rebuilds from persisted records, requires the frozen ids, fails on missing/failed polish.
7. /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/math/cut2/run_batches.py: stages validate (keyed id|sha8), l4_high, repair_high, fidelity_adjudicate (high, mathematical-fidelity rule), fidelity_audit_passes (300 random medium passes at high); sequence in /Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/cluster/drivers/cut2_after_solutions.sh.
Judge: (1) is each of the six defects actually fixed, with evidence from the code? (2) new defects introduced by the fixes (e.g. the dev flag propagation, the pair_too_long zip assumption that rows_M0 and rows_M1 are aligned, the adjudication key format, the audit stage sampling)? (3) anything in the chain sequence that can silently skip a stage or export unreviewed rows? (4) is the readout script's decision logic consistent with plan §4's outcome table? Rank by severity with file:line evidence; BLOCKER/HIGH are fixed before gate 1 (R3); MEDIUM/LOW logged. Do not re-review the plan or the previously reviewed datasets.


=== PLAN §4 (the outcome table the readout must implement) ===
## 4. Phase B — three math pilots (15 Sept, ≈3.9 nh)

Continuations from the same stage-1 checkpoint (`runs/R2_stage1/epoch1`, arm B's parent), one epoch,
identical replay sample (seed 42: 10% of the rows of every non-maths stage-1 config, ≈12M tokens, which is
≈56% of each pilot's tokens; both fractions are reported), identical English maths block (A2, ≈6.7M
supervised tokens), identical optimizer settings. Only the Greek maths block varies:

| Arm | Greek maths block | Contrast |
|---|---|---|
| M0 | cut-1 terse targets on the retained translated problems, **with the reference answer appended in `\boxed{}`** so boxing is not part of the treatment, + native rows | control |
| M1 | cut-2 worked targets on the **same retained problem ids** (intersection after every exclusion) + native rows | M1−M0 = worked vs terse, one exposure each, different target lengths (not equal compute; stated as such) |
| M2 | M1 + Level-5 worked rows | M2−M1 = Level-5 addition as a package (content + dose) |

Estimand (astra F3): one exposure to terse versus worked targets on identical prompts; the worked arm
processes more supervised tokens by construction. Per-arm processed tokens, supervised tokens, optimizer
updates and exposures per source problem are published in each arm's receipt. Stage 1 itself is the
zero-exposure reference; its MATH-500-el predictions (12.8, same generator and grader receipts) are reused.

Recipe (every parameter vs arm B's pass, the last continuation we ran):

| Parameter | arm B pass | pilots | flag |
|---|---|---|---|
| parent | R2_stage1/epoch1 | same | — |
| data | 41,697 rows, 2 epochs | ≈45k rows, 1 epoch (≈21M tokens) | CHANGE: 1 epoch (screen, not a finish) |
| lr / schedule / warmup / floor | 1e-5 cosine, 3%, 0.1 | same | — |
| batch | 16 × 4096 (accum 4 × 4 GPUs) | same | — |
| precision, masking, template | fp32 master + bf16, per-turn masks, Apertus template | same | — |
| seed | 42 | 42 | — |

Readout (light evals, ≈0.5 nh each): MATH-500-el (equiv500 grader, Sol adjudication of unresolved rows),
English MATH-500, Greek MGSM, IFEval-el (langdetect rescoring), greedy loop/truncation counts on the fixed
panel, format gate. Extraction failures (unboxed/unresolved) are reported separately so an extraction-only
gain is visible.

Decision rule, frozen before launch (astra F1/F5), hierarchical: primary contrast M1−M0, secondary M2−M1,
each on MATH-500-el paired items with a one-sided 90% bootstrap lower bound (4,000 resamples, seed 1).
Measured discordance between our existing checkpoints on this benchmark is 9–15% of items
(`data/math/en/discordance_math500_el.txt`), so at q≈15% the SE of a paired difference is ≈1.7 pp: the screen
detects effects of ≥5 pp reliably (stage 1 vs R3, +4.8 pp, has LB +2.6) and passes a true 3-pp effect only
about half the time. It is a screen for the large effect H9 predicts, not a test of small gains.

| Outcome | Rule | Action |
|---|---|---|
| guardrail failure | IFEval-el or MGSM-el more than 2 pp below M0, or loops/truncations above M0 by more than the panel's noise band | that arm cannot advance, whatever its maths score |
| qualified improvement | observed gain ≥3 pp and one-sided 90% LB > 0, no guardrail failure | advance the eligible arm (M2 only if M2−M1 also qualifies, else M1) |
| positive but inconclusive | gain > 0, LB ≤ 0 or gain < 3 pp, no guardrail failure | keep the checkpoint; spend ≤1 nh of the reserve on the predefined dose check: continue that checkpoint for a second epoch over the maths blocks only, re-read |
| negative | gain ≤ 0 | H9 is not supported by this screen; stop Phase C, write up, re-plan the maths lane |

Guardrail tolerances are screening tolerances with paired intervals reported ("no observed breach", not
"retention established"); single seed, stated. No arm advances by default.


=== PLAN §8b (what was claimed fixed) ===
## 8b. Implementation-review dispositions (astra, owner-run, 14 Sept ≈11:30)

| Finding | Verified? | Disposition |
|---|---|---|
| 1. Continuation assembler filters each arm independently by length and splits dev per row, so pairs can break | yes | pair-level token-length exclusion moved into `assemble_cut2.py` (Apertus tokenizer, both arms, drop the pair); shared family-level dev split written on the rows (1% paired, Level 5, native) and the English twins of dev problems go to dev; the continuation assembler honours the flags and refuses a Greek block with any over-window row; `data/check_pilot_arms.py` asserts identical prompt sets M0=M1, M1⊂M2, identical replay/English ids on the FINAL manifests; the trainer's `--dry-run` runs on the cluster for each arm before sbatch (exact rendered counts) |
| 2. Pass assembler has no contamination/length checks; replay bypasses checks; approximate tokens | yes | `data/mixlib.py` (round-one decontamination rule, exact tokenizer required, fails closed) applied to base replay, new blocks and maths rows in `assemble_pass_r4.py`; replay rows in the continuation assembler now pass the same check (the parent predates the MATH-500 cache) |
| 3. Polish keyed by id can resurrect an obsolete text; missing polish does not block export; 600-word cap is a hidden difficulty filter | yes | polish keyed by id+solution hash; export requires a polish disposition (edited/unchanged/reverted); cap raised to 1,000 words as a runaway guard, rows over 400 words counted as a flag by level |
| 4. Correcting v2 loads `accepted_train32` not `scope_revision_train32` (4 rows differ); XSTest judge reads `prompts_el.jsonl` while generation serves `prompts_el_final.jsonl` | yes (4 rows; ids identical across the two prompt files) | both fixed |
| 5. Readout uses the id intersection; guardrails printed not evaluated; adjudication not wired | yes | exactly the 500 MATH-500 ids required per arm and language (fails otherwise); guardrails computed into a PASS/FAIL eligibility before any arm is chosen; Sol adjudication bounded to rows with no extracted answer (`adjudicate_unresolved.py`), reported as secondary; primary scorer stays equiv500, the scorer every comparator was scored with |
| 6. MATH-200 builder loses completed rows on resume; failed polish counted as unchanged | yes (`run_jobs` returns only new results) | rebuilt from persisted records, exact frozen ids required, failed polish blocks finalisation; the set's cache file is written before the pilot assembly so the assembler's decontamination covers it (MATH test vs MATH train: disjoint by construction anyway) |
| Claims: "9.5% → ≤2 pp, no ranking change" too strong | accepted | worded as a pooled estimate with uncertainty (§2, report) |
| Longer reasoning is a hypothesis; audit medium-stage passes too | accepted | `fidelity_audit_passes`: 300 random medium PASSES re-judged at high → missed-defect rate reported; validity judges steps and correctness, word ratios are diagnostics |
| Maths-led intermediate experiment | agreed | stated in §5: the interim floor and the arm-B comparison do not satisfy the programme objective (strongest Krikri release, multilingual retention, dialogue, release evidence) |
| ETA: polish ≈115 min at 48 workers | accepted | polish at 64 workers; timeline +1 h |


=== FILE data/math/cut2/assemble_cut2.py (134 lines) ===
   1| #!/usr/bin/env python3
   2| """Assemble the cut-2 Greek maths block for the R4 pilots (plan §3 A1, §4; astra F2/F3 dispositions).
   3| Per translated problem id: (1) problem fidelity (fidelity_sample + fidelity_all: faithful required; unchecked = excluded), (2) generated solution present
   4| (Level 5 from the HIGH file), (3) derivation validity vs the pinned source (validity.jsonl: valid and severity != major; unvalidated = excluded),
   5| (4) mechanical: \\boxed present, boxed answer equivalent to the reference under the equiv500 grader, 40-600 words, no line repeated 3+ times,
   6| (5) polish applied only when its guards passed (polish.jsonl status=edited). M0 = cut-1 terse target on the SAME retained ids with the reference answer
   7| appended in \\boxed{} (boxing is not a treatment); prompts byte-identical across arms (the fidelity-checked translation). Native cut-1 rows unchanged in
   8| every arm. Outputs data/math/cut2/final/{rows_M0,rows_M1,rows_M2_extra,rows_native,arm_M0,arm_M1,arm_M2}.jsonl + receipt.json. Usage: python3 assemble_cut2.py"""
   9| import json, os, re, sys, collections, hashlib, unicodedata
  10| HERE = os.path.dirname(os.path.abspath(__file__)); OUT = f'{HERE}/out'; PREP = f'{HERE}/prep'; FIN = f'{HERE}/final'; os.makedirs(FIN, exist_ok=True)
  11| sys.path.insert(0, f'{HERE}/..'); from mathlib import boxed, equiv   # the same functions the frozen MATH-500 scorer uses (data/math/mathlib.py)
  12| def L(p): return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []
  13| def normt(t): return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', t).casefold()))
  14| src = {r['id']: r for r in L(f'{PREP}/translations_with_reference.jsonl')}
  15| for r in L(f'{OUT}/level5_problems_el.jsonl'):
  16|     if r['id'] not in src: src[r['id']] = dict(r, ref=boxed(r['solution_en']) or '', src='math', level='Level 5')   # first occurrence wins (13 Sept duplicates)
  17| fid = {}
  18| for p in (f'{OUT}/fidelity_sample.jsonl', f'{OUT}/fidelity_all.jsonl'):
  19|     for r in L(p): fid.setdefault(r['id'], r)
  20| adj = {r['id']: r for r in L(f'{OUT}/fidelity_adjudicated.jsonl')}   # two-stage screen: a first-stage flag is overturned when the high adjudication says faithful
  21| flags = collections.Counter(first_stage_flagged=sum(1 for r in fid.values() if not r['faithful']), adjudicated=len(adj), overturned_by_high=sum(1 for r in adj.values() if r['faithful']))
  22| for pid, r in adj.items():
  23|     if pid in fid: fid[pid] = dict(fid[pid], faithful=r['faithful'], discrepancies=r['discrepancies'], stage='adjudication_high')
  24| sol = {}
  25| for name in ('solutions_el_repair_high.jsonl', 'solutions_el_l4_high.jsonl', 'level5_solutions_el_high.jsonl', 'solutions_el.jsonl'):   # preference order = run_batches.SOLUTION_FILES
  26|     for r in L(f'{OUT}/{name}'): sol.setdefault(r['id'], dict(r, _file=name))
  27| val = {}
  28| for r in L(f'{OUT}/validity.jsonl'): val[r['id']] = r   # keyed id|sha8
  29| pol = {r['id']: r for r in L(f'{OUT}/polish.jsonl')}   # keyed id|sha8 (bound to the exact input solution)
  30| cut1 = L(f'{HERE}/../cut1/edited/rows_edited.jsonl'); native = [r for r in cut1 if r['bucket'] == 'native']
  31| by_text = {normt(r['user']): r for r in cut1 if r['bucket'] != 'native'}
  32| # MATH-500 exclusion (astra F7 / inherited-exposure audit: R3's cut-1 block carried 16 rows on 12 MATH-500 items): any shared 13-gram or exact match between
  33| # the Greek or English problem and a MATH-500 en/el prompt drops the id from every arm
  34| EG = set(); EX = set()
  35| for r in L(f'{HERE}/../../cache/evals/math500_el.jsonl'):
  36|     ws = re.findall(r'\w+', unicodedata.normalize('NFKC', r['text']).casefold()); EX.add(' '.join(ws)); EG |= set(tuple(ws[i:i+13]) for i in range(len(ws)-12)) if len(ws) >= 13 else {tuple(ws)}
  37| def math500_hit(*texts):
  38|     for t in texts:
  39|         ws = re.findall(r'\w+', unicodedata.normalize('NFKC', t or '').casefold())
  40|         if ' '.join(ws) in EX or (len(ws) >= 13 and any(tuple(ws[i:i+13]) in EG for i in range(len(ws)-12))): return True
  41|     return False
  42| # astra's accepted greek_maths overlays (7 native rows, exact-match replace on the rendered messages' sha256): applied here so every arm carries the repairs
  43| OVL = os.path.expanduser('~/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/accepted_patchset/overlays.jsonl')
  44| ovl = {o['row_id']: o for o in L(OVL) if o.get('component') == 'greek_maths'}
  45| def msha(msgs): return hashlib.sha256(json.dumps([dict(role=m['role'], content=m['content']) for m in msgs], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
  46| stats = collections.Counter(); reasons = collections.Counter(); rows_M1, rows_M2, rows_M0 = [], [], []
  47| def words(t): return len(t.split())
  48| def looped(t):
  49|     c = collections.Counter(l.strip() for l in t.splitlines() if len(l.strip()) > 12); return any(v >= 3 for v in c.values())
  50| for pid, s in src.items():
  51|     bucket = 'translated_math5' if s.get('level') == 'Level 5' else ('translated_gsm8k' if s.get('src') == 'gsm8k' else 'translated_math'); stats[f'{bucket}:source'] += 1
  52|     if math500_hit(s.get('problem_el'), s.get('problem_en')): reasons[f'{bucket}:math500_13gram'] += 1; continue
  53|     f = fid.get(pid)
  54|     if f is None: reasons[f'{bucket}:fidelity_unchecked'] += 1; continue
  55|     if not f['faithful']:
  56|         if pid not in adj and f.get('stage') != 'adjudication_high': reasons[f'{bucket}:flagged_awaiting_adjudication'] += 1; continue
  57|         reasons[f'{bucket}:unfaithful_both_stages'] += 1; continue
  58|     g = sol.get(pid)
  59|     if g is None: reasons[f'{bucket}:no_solution'] += 1; continue
  60|     v = val.get(f"{pid}|{hashlib.sha256(g['solution_el'].encode('utf-8')).hexdigest()[:8]}")
  61|     if v is None: reasons[f'{bucket}:unvalidated'] += 1; continue
  62|     if not v['valid'] or v['severity'] == 'major': reasons[f'{bucket}:invalid_derivation'] += 1; continue
  63|     text = g['solution_el']; pz = pol.get(f"{pid}|{hashlib.sha256(text.encode('utf-8')).hexdigest()[:8]}")
  64|     if pz is None or pz.get('status') not in ('edited', 'unchanged', 'reverted'): reasons[f'{bucket}:unpolished'] += 1; continue   # owner rule: no export without a language-review disposition
  65|     if pz['status'] == 'edited' and pz.get('text'): text = pz['text']; flags['polished_edited'] += 1
  66|     elif pz['status'] == 'reverted': flags['polish_reverted'] += 1
  67|     b = boxed(text)
  68|     if b is None: reasons[f'{bucket}:no_boxed'] += 1; continue
  69|     if not equiv(b, str(s.get('ref', ''))): reasons[f'{bucket}:boxed_not_equivalent'] += 1; continue
  70|     w = words(text)
  71|     if w > 400: flags[f'{bucket}:over_400_words'] += 1   # review flag, not a filter (astra: an unnoticed difficulty filter)
  72|     if w < 40 or w > 1000: reasons[f'{bucket}:length_{"short" if w < 40 else "runaway_over_1000"}'] += 1; continue
  73|     if looped(text): reasons[f'{bucket}:repeated_lines'] += 1; continue
  74|     if re.search(r'\d\.\d{1,2}(?!\d)', re.sub(r'\$[^$]*\$|\\\[.*?\\\]|\\boxed\{[^}]*\}', '', text, flags=re.S)): flags[f'{bucket}:decimal_point_outside_latex'] += 1
  75|     meta = dict(ref=s.get('ref'), level=s.get('level'), subject=s.get('subject'), src=s.get('src'), verification='source_fidelity+derivation_validity', validity_severity=v['severity'], generation_file=g['_file'], polished=bool(pz and pz.get('status') == 'edited'))
  76|     row = dict(id=f'c2_{pid}', user=s['problem_el'], assistant=text, bucket=bucket, source='greek_math_v2', meta=meta)
  77|     if bucket == 'translated_math5': rows_M2.append(row); stats[f'{bucket}:kept'] += 1; continue
  78|     c1 = by_text.get(normt(s['problem_el']))
  79|     if c1 is None: reasons[f'{bucket}:no_cut1_pair'] += 1; continue   # intersection rule: an id without a terse counterpart is in neither arm
  80|     terse = c1['assistant'].rstrip() + '\n\\boxed{' + str(s.get('ref', '')) + '}'
  81|     o = ovl.get(c1['id'])
  82|     if o and c1['user'] != o['messages'][0]['content']: flags['translated_overlays_user_changed_skipped'] += 1   # problem-text repairs are superseded by the fidelity gate; prompts stay byte-identical across arms
  83|     if o and c1['user'] == o['messages'][0]['content']: terse = [m for m in o['messages'] if m['role'] == 'assistant'][-1]['content'].rstrip() + '\n\\boxed{' + str(s.get('ref', '')) + '}'; flags['M0_overlays_applied'] += 1
  84|     rows_M1.append(row); rows_M0.append(dict(id=f'c1b_{pid}', user=s['problem_el'], assistant=terse, bucket=bucket, source='greek_math_cut1_boxed', meta=dict(ref=s.get('ref'), level=s.get('level'), src=s.get('src'), cut1_id=c1['id']))); stats[f'{bucket}:kept'] += 1
  85| # paired exclusions (astra 14 Sept F1): a pair is dropped when EITHER arm's row would exceed the trainer's 4,096-token window; measured with the Apertus tokenizer
  86| try:
  87|     from tokenizers import Tokenizer; import glob as _g
  88|     _tok = Tokenizer.from_file(_g.glob(os.path.expanduser('~/.cache/huggingface/hub/models--swiss-ai--Apertus-8B-2509/snapshots/*/tokenizer.json'))[0]); TOKMODE = 'apertus-tokenizer'
  89|     def ntok(t): return len(_tok.encode(t).ids)
  90| except Exception as e:
  91|     raise SystemExit(f'tokenizer unavailable ({e.__class__.__name__}): run with the apertus-local-chat venv; approximate lengths are not accepted for the paired manifests')
  92| def row_tokens(r): return ntok(r['user']) + ntok(r['assistant']) + 16
  93| keep0, keep1 = [], []
  94| for r0, r1 in zip(rows_M0, rows_M1):
  95|     if row_tokens(r0) > 4096 or row_tokens(r1) > 4096: reasons['pair_too_long'] += 1; continue
  96|     keep0.append(r0); keep1.append(r1)
  97| rows_M0, rows_M1 = keep0, keep1
  98| rows_M2 = [r for r in rows_M2 if row_tokens(r) <= 4096 or reasons.update({'level5_too_long': reasons.get('level5_too_long', 0) + 1})]
  99| # shared development split (1% of paired ids, 1% of Level 5, 1% of native; seed 42), identical across arms; the English twins of dev problems are excluded from the English block
 100| import random as _rnd; _r = _rnd.Random(42)
 101| dev_pairs = set(_r.sample(range(len(rows_M1)), max(1, len(rows_M1) // 100))) if rows_M1 else set()
 102| for i, (r0, r1) in enumerate(zip(rows_M0, rows_M1)):
 103|     if i in dev_pairs: r0['dev'] = True; r1['dev'] = True
 104| dev_l5 = set(_r.sample(range(len(rows_M2)), max(1, len(rows_M2) // 100))) if rows_M2 else set()
 105| for i, r in enumerate(rows_M2):
 106|     if i in dev_l5: r['dev'] = True
 107| dev_problems_en = sorted({src[r['id'][3:]]['problem_en'] for r in rows_M1 if r.get('dev')} | {src[r['id'][3:]]['problem_en'] for r in rows_M2 if r.get('dev')})
 108| json.dump(dev_problems_en, open(f'{FIN}/dev_problems_en.json', 'w'), ensure_ascii=False)
 109| nat = []; ov_applied = ov_missed = 0
 110| for r in native:
 111|     o = ovl.get(r['id']); user, asst = r['user'], r['assistant']
 112|     if o:
 113|         cur = [dict(role='user', content=user), dict(role='assistant', content=asst)]
 114|         cands = [m for m in o['messages'] if m['role'] == 'assistant']
 115|         if cur[0]['content'] == o['messages'][0]['content'] or msha(cur) == o['before_messages_sha256']:
 116|             user = o['messages'][0]['content']; asst = cands[-1]['content'] if cands else asst; ov_applied += 1
 117|         else: ov_missed += 1
 118|     nat.append(dict(id=r['id'], user=user, assistant=asst, bucket='native', source='greek_math_cut1', meta=dict(r.get('meta') or {}, overlay=bool(o))))
 119| dev_nat = set(_r.sample(range(len(nat)), max(1, len(nat) // 100)))
 120| for i, r in enumerate(nat):
 121|     if i in dev_nat: r['dev'] = True
 122| flags['native_overlays_applied'] = ov_applied; flags['native_overlays_unmatched'] = ov_missed
 123| def dump(name, rows):
 124|     p = f'{FIN}/{name}.jsonl'; h = hashlib.sha256()
 125|     with open(p, 'w') as f:
 126|         for r in rows: s = json.dumps(r, ensure_ascii=False) + '\n'; f.write(s); h.update(s.encode())
 127|     return dict(rows=len(rows), sha256=h.hexdigest())
 128| rec = dict(inputs=dict(source_problems=len(src), fidelity_results=len(fid), solutions=len(sol), validity_results=len(val), polish_results=len(pol), cut1_rows=len(cut1), native=len(native)),
 129|            stage_counts=dict(stats), dropped=dict(reasons), flags=dict(flags), files={})
 130| for name, rows in (('rows_M0', rows_M0), ('rows_M1', rows_M1), ('rows_M2_extra', rows_M2), ('rows_native', nat), ('arm_M0', rows_M0 + nat), ('arm_M1', rows_M1 + nat), ('arm_M2', rows_M1 + rows_M2 + nat)): rec['files'][name] = dump(name, rows)
 131| assert [r['id'][4:] for r in rows_M0] == [r['id'][3:] for r in rows_M1], 'M0/M1 id order mismatch'
 132| rec['paired_ids_M0_M1'] = len(rows_M1); rec['dev_rows'] = dict(paired=len(dev_pairs), level5=len(dev_l5), native=len(dev_nat), english_twins_excluded=len(dev_problems_en)); rec['tokenizer'] = TOKMODE; rec['words'] = {k: (sum(words(r['assistant']) for r in v) / max(1, len(v))) for k, v in (('M0', rows_M0), ('M1', rows_M1), ('M2_extra', rows_M2), ('native', nat))}
 133| json.dump(rec, open(f'{FIN}/receipt.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps({k: v for k, v in rec.items() if k != 'files'}, ensure_ascii=False, indent=1)); print({k: v['rows'] for k, v in rec['files'].items()})
 134| 

=== FILE data/assemble_continuation.py (104 lines) ===
   1| #!/usr/bin/env python3
   2| """Assemble a CONTINUATION arm (R4 plan §4): a seeded replay sample of the parent's training mix plus new blocks, in the trainer's row format
   3| ({config, id, messages[{role, content, train?}]}). Decontamination = the round-one rule (NFKC+casefold word 8-grams of every USER turn; a row is
   4| dropped when >= 0.5 of a turn's distinct 8-grams occur in the eval cache), length filter 4,096 tokens (Apertus tokenizer when available).
   5| Usage: python3 assemble_continuation.py --arm M1 --parent data/arms/R2_stage1/train.jsonl --replay-frac 0.10 --exclude-replay openmath_gsm
   6|          --block math_en_gsm=data/math/en/gsm8k_dedup3.jsonl:openmath:1 --block math_en_math=data/math/en/math_train_published.jsonl:openmath:2
   7|          --block greek_math=data/math/cut2/final/rows_M1.jsonl:ua:1 [--dev-frac 0.01] [--seed 42]
   8| Block spec: name=file:renderer:copies; renderer 'openmath' = problem/generated_solution, 'ua' = user/assistant or turns/messages (train flags kept)."""
   9| import argparse, json, random, re, unicodedata, collections, hashlib, os, glob, pathlib
  10| HERE = pathlib.Path(__file__).resolve().parent
  11| ap = argparse.ArgumentParser(); ap.add_argument('--arm', required=True); ap.add_argument('--parent', required=True); ap.add_argument('--replay-frac', type=float, default=0.10)
  12| ap.add_argument('--exclude-replay', default=''); ap.add_argument('--block', action='append', default=[]); ap.add_argument('--dev-frac', type=float, default=0.01); ap.add_argument('--seed', type=int, default=42)
  13| ap.add_argument('--max-length', type=int, default=4096); ap.add_argument('--dev-problems', default='', help='JSON list of English problem texts whose rows go to dev (family-level split shared with the Greek block)'); a = ap.parse_args(); rng = random.Random(a.seed)
  14| DEV_PROBLEMS = set(json.load(open(a.dev_problems))) if a.dev_problems else set()
  15| OUT = HERE / 'arms' / a.arm; OUT.mkdir(parents=True, exist_ok=True)
  16| WORD_RE = re.compile(r"\w+", flags=re.UNICODE)
  17| def normalize_text(t): return " ".join(WORD_RE.findall(unicodedata.normalize("NFKC", t).casefold()))
  18| def ngrams(n_text, n=8):
  19|     w = n_text.split()
  20|     if not w: return frozenset()
  21|     return frozenset({tuple(w)}) if len(w) < n else frozenset(tuple(w[i:i+n]) for i in range(len(w)-n+1))
  22| eval_grams = {}
  23| for f in sorted(glob.glob(str(HERE / 'cache' / 'evals' / '*.jsonl'))):
  24|     suite = os.path.basename(f).split('.')[0]
  25|     for l in open(f):
  26|         if l.strip():
  27|             r = json.loads(l)
  28|             for g in ngrams(normalize_text(str(r['text']))): eval_grams.setdefault(g, (suite, str(r['eval_id'])))
  29| print(f'decontamination: {len(eval_grams)} distinct 8-grams from the eval cache', flush=True)
  30| def contaminated(messages):
  31|     for m in messages:
  32|         if m['role'] != 'user': continue
  33|         gs = ngrams(normalize_text(m['content']))
  34|         if gs and sum(1 for g in gs if g in eval_grams) / len(gs) >= 0.5: return eval_grams[next(g for g in gs if g in eval_grams)]
  35|     return None
  36| try:
  37|     from tokenizers import Tokenizer
  38|     tp = glob.glob(os.path.expanduser('~/.cache/huggingface/hub/models--swiss-ai--Apertus-8B-2509/snapshots/*/tokenizer.json'))[0]; tok = Tokenizer.from_file(tp); TOKMODE = 'apertus-tokenizer(content only, +8/turn)'
  39|     def ntok(s): return len(tok.encode(s).ids)
  40| except Exception as e:
  41|     tok = None; TOKMODE = f'approximate words*1.7 ({e.__class__.__name__})'
  42|     def ntok(s): return int(len(s.split()) * 1.7)
  43| def row_tokens(messages): return sum(ntok(m['content']) + 8 for m in messages)
  44| def sup_tokens(messages): return sum(ntok(m['content']) for m in messages if m['role'] == 'assistant' and m.get('train', True))
  45| def render(r, how):
  46|     if how == 'openmath': return [dict(role='user', content=r['problem']), dict(role='assistant', content=r['generated_solution'])]
  47|     turns = r.get('turns') or r.get('messages') or [dict(role='user', content=r['user']), dict(role='assistant', content=r['assistant'])]
  48|     out = []
  49|     for t in turns:
  50|         m = dict(role=t['role'], content=t['content'])
  51|         if t['role'] == 'assistant' and t.get('train') is False: m['train'] = False
  52|         out.append(m)
  53|     if not any(m['role'] == 'assistant' and m.get('train', True) for m in out): return None
  54|     return out
  55| receipt = dict(arm=a.arm, seed=a.seed, parent=a.parent, replay_frac=a.replay_frac, tokenizer=TOKMODE, blocks=[]); train, dev = [], []
  56| # replay
  57| excl = set(x for x in a.exclude_replay.split(',') if x); by = collections.defaultdict(list)
  58| for l in open(a.parent):
  59|     if l.strip():
  60|         r = json.loads(l); by[r['config']].append(r)
  61| rep_stats = {}
  62| for cfg, rows in sorted(by.items()):
  63|     if cfg in excl: rep_stats[cfg] = dict(available=len(rows), taken=0, excluded=True); continue
  64|     k = int(round(len(rows) * a.replay_frac)); pick = rng.sample(rows, k)
  65|     hit = 0
  66|     for r in pick:
  67|         if contaminated(r['messages']): hit += 1; continue   # replay rows get the same benchmark check as new blocks (the parent predates the MATH-500 cache)
  68|         train.append(dict(config=f'replay:{cfg}', id=r['id'], messages=r['messages']))
  69|     rep_stats[cfg] = dict(available=len(rows), taken=k - hit, contaminated=hit)
  70| receipt['replay'] = rep_stats; print(f'replay: {sum(v["taken"] for v in rep_stats.values())} rows from {len(by)} parent configs (excluded {sorted(excl)})', flush=True)
  71| # new blocks
  72| for spec in a.block:
  73|     name, rest = spec.split('=', 1); path, how, copies = rest.rsplit(':', 2); copies = int(copies)
  74|     rows = [json.loads(l) for l in open(path) if l.strip()]; st = collections.Counter(available=len(rows)); taken = []; seen_ids = set()
  75|     for i, r in enumerate(rows):
  76|         rid = str(r.get('id') or f'{name}_{i}')
  77|         if rid in seen_ids: st['duplicate_id'] += 1; continue
  78|         msgs = render(r, how)
  79|         if not msgs: st['unrenderable'] += 1; continue
  80|         if contaminated(msgs): st['contaminated'] += 1; continue
  81|         if row_tokens(msgs) > a.max_length: st['too_long'] += 1; continue
  82|         is_dev = bool(r.get('dev')) or (how == 'openmath' and r.get('problem') in DEV_PROBLEMS)
  83|         seen_ids.add(rid); taken.append(dict(config=name, id=rid, messages=msgs, _dev=is_dev))
  84|     if how == 'ua' and st['too_long']: raise SystemExit(f'{name}: {st["too_long"]} rows over the window; paired blocks must arrive pre-filtered (assemble_cut2 pair_too_long)')
  85|     flagged = [r for r in taken if r['_dev']]
  86|     if flagged: dv = flagged; tr = [r for r in taken if not r['_dev']]; ndev = len(dv)   # the split is decided upstream and identical across arms
  87|     else: rng.shuffle(taken); ndev = int(round(len(taken) * a.dev_frac)); dv, tr = taken[:ndev], taken[ndev:]
  88|     for r in taken: r.pop('_dev', None)
  89|     dev.extend(dv); sup = sum(sup_tokens(r['messages']) for r in tr); tot = sum(row_tokens(r['messages']) for r in tr)
  90|     for c in range(copies): train.extend(dict(r, id=f"{r['id']}#{c}" if c else r['id']) for r in tr)
  91|     b = dict(block=name, file=path, renderer=how, copies=copies, **st, taken=len(taken), dev_rows=ndev, train_unique_rows=len(tr), train_rows_effective=len(tr) * copies, tokens_unique=tot, tokens_effective=tot * copies, supervised_tokens_unique=sup, supervised_tokens_effective=sup * copies,
  92|              content_sha256=hashlib.sha256(''.join(json.dumps(r['messages'], ensure_ascii=False, sort_keys=True) for r in taken).encode()).hexdigest())
  93|     receipt['blocks'].append(b); print(f"{name:16s} available {st['available']:6d} taken {len(taken):6d} x{copies} contaminated {st['contaminated']} too_long {st['too_long']} dup_id {st['duplicate_id']} unrenderable {st['unrenderable']} supervised {sup} (x{copies})", flush=True)
  94| rng.shuffle(train); rng.shuffle(dev)
  95| def dump(p, rows):
  96|     h = hashlib.sha256()
  97|     with open(p, 'w') as f:
  98|         for r in rows: s = json.dumps(r, ensure_ascii=False) + '\n'; f.write(s); h.update(s.encode())
  99|     return h.hexdigest()
 100| ids_train = set(r['id'].split('#')[0] for r in train); assert not (ids_train & set(r['id'] for r in dev)), 'train/dev id overlap'
 101| receipt['train'] = dict(rows=len(train), tokens=sum(row_tokens(r['messages']) for r in train), supervised_tokens=sum(sup_tokens(r['messages']) for r in train), sha256=dump(OUT / 'train.jsonl', train))
 102| receipt['dev'] = dict(rows=len(dev), sha256=dump(OUT / 'dev.jsonl', dev)); json.dump(receipt, open(OUT / 'receipt.json', 'w'), indent=1, ensure_ascii=False)
 103| print(f"{a.arm}: train {len(train)} rows, {receipt['train']['tokens']/1e6:.1f}M tokens ({receipt['train']['supervised_tokens']/1e6:.1f}M supervised), dev {len(dev)} rows -> {OUT}", flush=True)
 104| 

=== FILE data/check_pilot_arms.py (38 lines) ===
   1| #!/usr/bin/env python3
   2| """Final-manifest assertions for the pilot arms (astra 14 Sept F1): the Greek maths prompts of M0 and M1 are the SAME set, M1's are a subset of M2's,
   3| replay and English blocks are identical across arms (ids), dev sets identical for shared blocks, no user turn hits MATH-500 or the confirmation set,
   4| and per-arm rows/tokens/updates are printed. Exit 1 on any failure. Usage: python3 check_pilot_arms.py M0 M1 M2"""
   5| import json, sys, os, re, unicodedata, collections
   6| H = os.path.dirname(os.path.abspath(__file__)); arms = sys.argv[1:]
   7| def L(p): return [json.loads(l) for l in open(p) if l.strip()]
   8| WORD = re.compile(r'\w+', flags=re.UNICODE)
   9| def normw(t): return WORD.findall(unicodedata.normalize('NFKC', t).casefold())
  10| ev = set(); eg = set()
  11| for f in ('math500_el.jsonl', 'math200_confirm.jsonl'):
  12|     p = f'{H}/cache/evals/{f}'
  13|     if os.path.exists(p):
  14|         for r in L(p): ws = normw(r['text']); ev.add(' '.join(ws)); eg |= set(tuple(ws[i:i+13]) for i in range(len(ws)-12)) if len(ws) >= 13 else {tuple(ws)}
  15| def hit(t): ws = normw(t); return ' '.join(ws) in ev or (len(ws) >= 13 and any(tuple(ws[i:i+13]) in eg for i in range(len(ws)-12)))
  16| data = {}; ok = True
  17| for a in arms:
  18|     tr = L(f'{H}/arms/{a}/train.jsonl'); dv = L(f'{H}/arms/{a}/dev.jsonl'); rc = json.load(open(f'{H}/arms/{a}/receipt.json'))
  19|     greek = {r['messages'][0]['content'] for r in tr if r['config'] == 'greek_math'}; ids = collections.defaultdict(set)
  20|     for r in tr: ids[r['config'].split(':')[0] if not r['config'].startswith('replay') else 'replay'].add(r['id'])
  21|     hits = sum(1 for r in tr for m in r['messages'] if m['role'] == 'user' and hit(m['content']))
  22|     data[a] = dict(greek=greek, ids=ids, dev=set(r['id'] for r in dv), rows=len(tr), tokens=rc['train']['tokens'], sup=rc['train']['supervised_tokens'], hits=hits)
  23|     updates = rc['train']['tokens'] / (16 * 4096); print(f"{a}: {len(tr)} rows, {rc['train']['tokens']/1e6:.1f}M tokens ({rc['train']['supervised_tokens']/1e6:.1f}M supervised), ≈{updates:.0f} updates of 16x4096, greek prompts {len(greek)}, benchmark hits {hits}")
  24|     if hits: ok = False; print(f'  FAIL: {hits} user turns hit MATH-500/confirm')
  25| if 'M0' in data and 'M1' in data:
  26|     if data['M0']['greek'] != data['M1']['greek']: ok = False; print(f"FAIL: M0/M1 Greek prompt sets differ ({len(data['M0']['greek'] ^ data['M1']['greek'])} symmetric difference)")
  27|     else: print(f"OK: M0 and M1 carry the same {len(data['M0']['greek'])} Greek maths prompts")
  28| if 'M1' in data and 'M2' in data:
  29|     if not data['M1']['greek'] <= data['M2']['greek']: ok = False; print('FAIL: M1 Greek prompts are not a subset of M2')
  30|     else: print(f"OK: M1 ⊂ M2 (+{len(data['M2']['greek'] - data['M1']['greek'])} Level-5 prompts)")
  31| for blk in ('replay', 'math_en_gsm', 'math_en_math'):
  32|     sets = [data[a]['ids'].get(blk, set()) for a in arms]
  33|     if all(s == sets[0] for s in sets): print(f'OK: {blk} identical across arms ({len(sets[0])} ids)')
  34|     else: ok = False; print(f'FAIL: {blk} differs across arms: ' + ', '.join(str(len(s)) for s in sets))
  35| devs = [data[a]['dev'] for a in arms]
  36| shared = set.intersection(*devs); print(f'dev sets: sizes {[len(d) for d in devs]}, shared {len(shared)}')
  37| print('RESULT', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
  38| 

=== FILE cluster/pilot_chain.sh (50 lines) ===
   1| #!/usr/bin/env bash
   2| # R4 plan §4: train the pilot continuations sequentially (sbatch, normal), light-eval each (ILSP IFEval/MGSM + dev50 format gate; interviews skipped),
   3| # then ONE vLLM window serving all arms for MATH-500 el/en (generate.py, frozen protocol), scored on the Mac, summarised with the frozen decision rule.
   4| # Mac-orchestrated; launch DETACHED (data/launch_detached.py). Usage: bash cluster/pilot_chain.sh M0 M1 M2   (arms assembled under data/arms/<arm>, configs cluster/configs/<arm>.yaml)
   5| set -u; cd "$(dirname "$0")/.."; HERE=$PWD; ARMS=("$@"); S=/iopsstor/scratch/cscs/fffoivos; R=$S/sft_round1; OUT=$HERE/results/pilots; mkdir -p $OUT; LOG=$OUT/chain.log
   6| say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }
   7| sshc(){ ssh -4 -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 clariden "$@" 2>/dev/null; }
   8| PY=$HOME/Projects/apertus-local-chat/.venv/bin/python
   9| sshc "echo ok" | grep -q ok || { say "FAILED: ssh clariden not available (certificate?)"; exit 1; }
  10| for A in "${ARMS[@]}"; do
  11|   [ -f data/arms/$A/train.jsonl ] && [ -f cluster/configs/$A.yaml ] || { say "FAILED: missing data/arms/$A or config"; exit 1; }
  12| done
  13| bash cluster/preflight.sh $(python3 -c "print(1.5*${#ARMS[@]})") "pilots_${ARMS[*]// /_}" | tail -1 | grep -q '^OK' || { say "FAILED: preflight refused the pilot set"; exit 1; }
  14| declare -A JOB
  15| for A in "${ARMS[@]}"; do   # upload + submit ALL arms first (normal partition, one node each; the queue is empty), then wait
  16|   say "$A: uploading $(wc -l < data/arms/$A/train.jsonl) train rows + config"; sshc "mkdir -p $R/data/arms/$A"; scp -4 -q data/arms/$A/train.jsonl data/arms/$A/dev.jsonl clariden:$R/data/arms/$A/ && scp -4 -q cluster/configs/$A.yaml clariden:$R/cluster/configs/$A.yaml || { say "FAILED: upload $A"; exit 1; }
  17|   [ "$(sshc "cd $R && md5sum data/arms/$A/train.jsonl | cut -c1-12")" = "$(md5 -q data/arms/$A/train.jsonl | cut -c1-12)" ] || { say "FAILED: md5 mismatch after upload $A"; exit 1; }
  18|   sshc "cd $R && uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc 'source $S/venvs/sft5/bin/activate; python cluster/sft_train.py --config cluster/configs/$A.yaml --dry-run'" > $OUT/dryrun_$A.log 2>&1 || { say "FAILED: trainer dry-run for $A: $(tail -3 $OUT/dryrun_$A.log | tr '\n' ' ' | cut -c1-300)"; exit 1; }
  19|   say "$A: trainer dry-run OK: $(grep -iE 'rows|tokens|steps' $OUT/dryrun_$A.log | tail -3 | tr '\n' ' ' | cut -c1-300)"
  20|   J=$(sshc "cd $R && bash cluster/train_sbatch.sh cluster/configs/$A.yaml $A 01:30:00" | tail -1); [[ "$J" =~ ^[0-9]+$ ]] || { say "FAILED: sbatch $A [$J]"; exit 1; }
  21|   JOB[$A]=$J; echo "$J" > $OUT/.${A}_job; say "$A: LAUNCHED training job $J (1 node, walltime 1:30, 1 epoch, lr 1e-5 cosine from R2_stage1/epoch1)"
  22| done
  23| for A in "${ARMS[@]}"; do
  24|   J=${JOB[$A]}; while true; do st=$(sshc "squeue -h -j $J -o %T"); [ -z "$st" ] && break; sleep 120; done
  25|   if ! sshc "grep -q TRAIN_OK $R/runs/$A.ctl/train.log"; then term=$(sshc "grep -E -m1 'RUN_EXIT|Traceback|TIME LIMIT|CANCELLED|OutOfMemory' $R/runs/$A.ctl/train.log | cut -c1-120"); say "FAILED: $A ended without TRAIN_OK: [$term]"; exit 1; fi
  26|   rt=$(sshc "grep -oE \"train_runtime.: .[0-9.]+\" $R/runs/$A.ctl/train.log | tail -1"); tl=$(sshc "grep -oE \"train_loss.: .[0-9.]+\" $R/runs/$A.ctl/train.log | tail -1")
  27|   say "$A: TRAIN_OK [$rt] [$tl]"; bash cluster/ledger.sh $J "pilot_$A" "training" | tail -1 | tee -a $LOG
  28|   sshc "bash $R/make_eval_copy.sh $R/runs/$A/epoch1 $R/eval_copies/${A}_ep1" | tail -1 | tee -a $LOG
  29| done
  30| say "light evals for all arms in parallel (normal partition workbenches, ILSP + dev50, interviews skipped)"; EP=""
  31| for A in "${ARMS[@]}"; do (SKIP_INTERVIEWS=1 EVAL_PARTITION=normal bash cluster/eval_checkpoint.sh $R/runs/$A/epoch1 ${A}_ep1 > $OUT/light_$A.log 2>&1; echo "light_$A exit $?" >> $LOG) & EP="$EP $!"; sleep 90; done
  32| wait $EP
  33| for A in "${ARMS[@]}"; do $PY evals/ilsp/rescore_ifeval_langdetect.py results/${A}_ep1 > $OUT/rescore_$A.log 2>&1; say "$A: ifeval rescored: $(tail -1 $OUT/rescore_$A.log | cut -c1-120)"; done
  34| say "all arms trained; MATH-500 window for ${ARMS[*]}"
  35| bash cluster/preflight.sh 1.5 "pilot_bench" | tail -1 | grep -q '^OK' || { say "FAILED: preflight refused the benchmark window"; exit 1; }
  36| W=$(sshc "bash $R/workbench.sh open pilot_bench normal 01:30:00" | tail -1); [[ "$W" =~ ^[0-9]+$ ]] || { say "FAILED: no workbench [$W]"; exit 1; }; say "workbench $W"
  37| SPEC=""; i=0; for A in "${ARMS[@]}"; do SPEC="$SPEC $A=$R/eval_copies/${A}_ep1"; i=$((i+1)); done
  38| sshc "cd $R; nohup setsid bash -c \"srun --jobid=$W --overlap --ntasks=1 --gpus-per-node=4 --cpus-per-task=288 --export=ALL uenv run --view=default pytorch/v2.9.1:v2 -- bash $R/serve_models.sh $SPEC\" > $R/serve_pilots.log 2>&1 &"
  39| NODE=""; for k in $(seq 1 20); do NODE=$(sshc "squeue -h -j $W -o %N"); [ -n "$NODE" ] && break; sleep 10; done
  40| TUNARGS=""; i=0; for A in "${ARMS[@]}"; do TUNARGS="$TUNARGS -L $((8000+i)):$NODE:$((8000+i))"; i=$((i+1)); done
  41| ssh -4 -N -o BatchMode=yes -o ServerAliveInterval=30 $TUNARGS clariden & TUN=$!
  42| ok=0; for k in $(seq 1 80); do ok=1; i=0; for A in "${ARMS[@]}"; do curl -s -m 10 http://127.0.0.1:$((8000+i))/v1/models | grep -q '"id"' || ok=0; i=$((i+1)); done; [ $ok = 1 ] && break; sleep 15; done
  43| [ $ok = 1 ] || { say "FAILED: models did not come up: $(sshc "tail -2 $R/serve_pilots.log" | tr '\n' ' ')"; kill $TUN; sshc "bash $R/workbench.sh close $W"; exit 1; }
  44| say "endpoints ready after $((k*15)) s; generating MATH-500 el+en for all arms (greedy, max_tokens 2048)"
  45| PIDS=""; i=0; for A in "${ARMS[@]}"; do $PY data/benchmarks_el/generate.py http://127.0.0.1:$((8000+i))/v1 $A $OUT/bench_$A --sets math500 --langs el,en --workers 24 > $OUT/bench_$A.log 2>&1 & PIDS="$PIDS $!"; i=$((i+1)); done
  46| wait $PIDS; kill $TUN 2>/dev/null; sshc "bash $R/workbench.sh close $W" | tail -1 | tee -a $LOG; bash cluster/ledger.sh $W "pilot_bench" "MATH-500 window for ${ARMS[*]}" | tail -1 | tee -a $LOG
  47| for A in "${ARMS[@]}"; do for L in el en; do python3 data/benchmarks_el/math500/score_math500.py $OUT/bench_$A/math500_$L.jsonl $OUT/bench_$A/math500_${L}_score.json | tail -1 | cut -c1-160 | tee -a $LOG; done; done
  48| for A in "${ARMS[@]}"; do WORKERS=24 $PY data/benchmarks_el/math500/adjudicate_unresolved.py $OUT/bench_$A/math500_el.jsonl $OUT/bench_$A/math500_el_score.json > $OUT/bench_$A/adjudicate_el.log 2>&1; say "$A: $(tail -1 $OUT/bench_$A/adjudicate_el.log | cut -c1-120)"; done
  49| python3 data/pilot_summary.py "${ARMS[@]}" | tee -a $LOG; say "PILOT_CHAIN_DONE"
  50| 

=== FILE data/pilot_summary.py (93 lines) ===
   1| #!/usr/bin/env python3
   2| """Pilot readout under the frozen rule (R4 plan §4): MATH-500-el paired contrasts M1-M0 (primary) and M2-M1 (secondary), one-sided 90% bootstrap LB
   3| (4,000 resamples, seed 1), guardrails IFEval-el (langdetect-rescored, prompt strict) and MGSM-el within 2 pp of M0, truncations (finish_reason=length)
   4| reported, English MATH-500 as safeguard, stage 1 as the zero-exposure reference. Usage: python3 pilot_summary.py M0 M1 M2 -> results/pilots/summary.md"""
   5| import json, os, sys, random, glob
   6| HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OUT = f'{ROOT}/results/pilots'; arms = sys.argv[1:]
   7| EXPECTED = {json.loads(l)['id'] for l in open(f'{ROOT}/data/benchmarks_el/math500/problems_el_final.jsonl')}
   8| def score(path):
   9|     if not os.path.exists(path): return None
  10|     sc = json.load(open(path)); ids = [r['id'] for r in sc['rows']]
  11|     if len(ids) != len(set(ids)) or set(ids) != EXPECTED: raise SystemExit(f'{path}: expected exactly the {len(EXPECTED)} MATH-500 ids, got {len(set(ids))} unique of {len(ids)} rows; no partial outputs in the readout')
  12|     adj = path.replace('_score.json', '_adjudicated.jsonl')   # optional Sol adjudication of unresolved rows (data/benchmarks_el/math500/adjudicate_unresolved.py)
  13|     if os.path.exists(adj):
  14|         upd = {json.loads(l)['id']: json.loads(l) for l in open(adj)}
  15|         for r in sc['rows']:
  16|             if r['id'] in upd and r['extracted'] in (None, '') and upd[r['id']].get('equivalent') is True: r['adjudicated'] = True
  17|         sc['adjudicated_acc'] = sum(1 for r in sc['rows'] if r['equiv500'] or r.get('adjudicated')) / len(sc['rows'])
  18|     return sc
  19| def items(sc): return {r['id']: bool(r['equiv500']) for r in sc['rows']} if sc else {}   # PRIMARY = deterministic equiv500 (the scorer every comparator was scored with); adjudicated accuracy is reported alongside
  20| def ifeval(label):
  21|     p = f'{ROOT}/results/{label}/ifeval_el_rescored.json'
  22|     if os.path.exists(p): d = json.load(open(p)); return d.get('prompt_strict') or d.get('prompt_level_strict_acc') or d
  23|     return None
  24| def mgsm(label):
  25|     for p in glob.glob(f'{ROOT}/results/{label}/ilsp/*mgsm*.json'):
  26|         d = json.load(open(p)); r = d.get('results', d); k = next((k for k in r if 'mgsm' in k), None)
  27|         if k: return r[k].get('exact_match,flexible-extract') or r[k].get('exact_match') or r[k]
  28|     return None
  29| def loops(a):
  30|     """R3 diagnosis rule: a Greek MATH-500 response 'loops' when one content line (>12 chars) repeats 5+ times (stage 1 23/500, arm B 7/500, R3 35/500)."""
  31|     import collections; p = f'{OUT}/bench_{a}/math500_el.jsonl'
  32|     if not os.path.exists(p): return None
  33|     n = 0
  34|     for l in open(p):
  35|         r = json.loads(l); c = collections.Counter(x.strip() for x in (r.get('response') or '').splitlines() if len(x.strip()) > 12)
  36|         n += any(v >= 5 for v in c.values())
  37|     return n
  38| def lb(a, b, n_boot=4000, seed=1):
  39|     ids = sorted(set(a) & set(b)); d = [int(a[i]) - int(b[i]) for i in ids]
  40|     if not d: return None
  41|     rng = random.Random(seed); bs = sorted(sum(d[rng.randrange(len(d))] for _ in d) / len(d) for _ in range(n_boot))
  42|     return dict(n=len(d), delta=100 * sum(d) / len(d), q=100 * sum(1 for x in d if x) / len(d), lb90=100 * bs[int(0.10 * n_boot)])
  43| S = {a: score(f'{OUT}/bench_{a}/math500_el_score.json') for a in arms}; E = {a: score(f'{OUT}/bench_{a}/math500_en_score.json') for a in arms}
  44| S1 = score(f'{ROOT}/results/R3_single/bench_S1/math500_el_score.json'); E1 = score(f'{ROOT}/results/R3_single/bench_S1/math500_en_score.json')
  45| lines = ['# Pilot readout (frozen rule, plan §4)', '', '| arm | MATH-500-el | loops (line x5) | truncated | MATH-500-en | IFEval-el (rescored) | MGSM-el |', '|---|---:|---:|---:|---:|---:|---:|']
  46| lines.append(f"| stage 1 (reference) | {S1['equiv500_acc']*100:.1f} | 23 | {S1['truncated']} | {E1['equiv500_acc']*100:.1f} | 62.85 | 48.8 |")
  47| for a in arms:
  48|     s, e = S[a], E[a]; lines.append(f"| {a} | {s['equiv500_acc']*100:.1f} | {loops(a)} | {s['truncated']} | {e['equiv500_acc']*100:.1f} | {ifeval(a + '_ep1')} | {mgsm(a + '_ep1')} |" if s and e else f'| {a} | missing ||||||')
  49| lines += ['', '| contrast | n | delta (pp) | discordant % | one-sided 90% LB | verdict |', '|---|---:|---:|---:|---:|---|']
  50| def verdict(r):
  51|     if r is None: return 'missing'
  52|     if r['delta'] >= 3 and r['lb90'] > 0: return 'qualified improvement (guardrails to check)'
  53|     if r['delta'] > 0: return 'positive but inconclusive -> dose check'
  54|     return 'negative'
  55| pairs = [(arms[i + 1], arms[i]) for i in range(len(arms) - 1)]
  56| for x, y in pairs:
  57|     r = lb(items(S[x]), items(S[y])); lines.append(f"| {x}-{y} (el) | {r['n']} | {r['delta']:+.1f} | {r['q']:.1f} | {r['lb90']:+.1f} | {verdict(r)} |" if r else f'| {x}-{y} | missing |||||')
  58|     r = lb(items(E[x]), items(E[y])); lines.append(f"| {x}-{y} (en, safeguard) | {r['n']} | {r['delta']:+.1f} | {r['q']:.1f} | {r['lb90']:+.1f} | — |" if r else '')
  59| # guardrails evaluated, not just printed: eligibility per candidate arm vs M0
  60| def num(x):
  61|     try: return float(x)
  62|     except Exception: return None
  63| base = arms[0]; g0 = dict(ifeval=num(ifeval(base + '_ep1')), mgsm=num(mgsm(base + '_ep1')), loops=loops(base))
  64| lines += ['', '| arm | IFEval-el vs M0 | MGSM-el vs M0 | loops vs M0 | guardrails |', '|---|---:|---:|---:|---|']
  65| elig = {}
  66| for a in arms[1:]:
  67|     gi, gm, gl = num(ifeval(a + '_ep1')), num(mgsm(a + '_ep1')), loops(a)
  68|     checks = []
  69|     if gi is None or g0['ifeval'] is None: checks.append('ifeval missing')
  70|     elif (gi - g0['ifeval']) * (100 if gi <= 1 else 1) < -2: checks.append('IFEval breach')
  71|     if gm is None or g0['mgsm'] is None: checks.append('mgsm missing')
  72|     elif (gm - g0['mgsm']) * (100 if gm <= 1 else 1) < -2: checks.append('MGSM breach')
  73|     if gl is None or g0['loops'] is None: checks.append('loops missing')
  74|     elif gl > g0['loops'] + 5: checks.append('loops breach')
  75|     elig[a] = not checks; lines.append(f"| {a} | {gi} vs {g0['ifeval']} | {gm} vs {g0['mgsm']} | {gl} vs {g0['loops']} | {'PASS' if not checks else 'FAIL: ' + ', '.join(checks)} |")
  76| def outcome(x, y):
  77|     r = lb(items(S[x]), items(S[y]))
  78|     if r is None: return 'missing'
  79|     if not elig.get(x, False): return 'cannot advance (guardrail failure or missing readout)'
  80|     if r['delta'] >= 3 and r['lb90'] > 0: return 'qualified improvement'
  81|     if r['delta'] > 0: return 'positive but inconclusive -> dose check'
  82|     return 'negative'
  83| lines += ['', '## Decision (frozen rule, plan §4)', '']
  84| for x, y in pairs: lines.append(f'- {x} vs {y}: **{outcome(x, y)}**')
  85| adv = None
  86| if len(arms) >= 2 and outcome(arms[1], arms[0]) == 'qualified improvement': adv = arms[1]
  87| if len(arms) >= 3 and adv == arms[1] and outcome(arms[2], arms[1]) == 'qualified improvement': adv = arms[2]
  88| lines.append(f"- advancing arm: **{adv or 'none'}** (no arm advances by default)")
  89| adjs = {a: S[a].get('adjudicated_acc') for a in arms if S[a]}
  90| if any(v is not None for v in adjs.values()): lines.append(f"- adjudicated accuracies (unresolved rows judged by Sol; secondary): {adjs}")
  91| lines += ['', 'Guardrails are screening tolerances (paired uncertainty applies); truncations reported; primary scorer = equiv500 for every arm and comparator.']
  92| open(f'{OUT}/summary.md', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
  93| 

=== FILE data/benchmarks_el/math500/adjudicate_unresolved.py (20 lines) ===
   1| #!/usr/bin/env python3
   2| """Sol adjudication of MATH-500 rows the deterministic scorer could not resolve (no extracted answer): does the response's final answer equal the
   3| reference? Bounded: only rows with extracted None/''; writes <score>_adjudicated.jsonl {id, equivalent, note}. The deterministic equiv500 score stays
   4| primary; the adjudicated accuracy is reported alongside. Usage: WORKERS=24 python3 adjudicate_unresolved.py <responses.jsonl> <score.json> [--bench problems_el_final.jsonl]"""
   5| import json, os, sys, argparse
   6| HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
   7| ap = argparse.ArgumentParser(); ap.add_argument('responses'); ap.add_argument('score'); ap.add_argument('--bench', default=os.path.join(HERE, 'problems_el_final.jsonl')); a = ap.parse_args()
   8| SCH = B.M.write_schema('m500_adjudicate', {'type': 'object', 'properties': {'equivalent': {'type': 'boolean'}, 'final_answer_found': {'type': 'string'}, 'note': {'type': 'string'}}, 'required': ['equivalent', 'final_answer_found', 'note'], 'additionalProperties': False})
   9| bench = {r['id']: r for r in B.load(a.bench)}; resp = {r['id']: r for r in B.load(a.responses)}; sc = json.load(open(a.score))
  10| items = [dict(id=r['id']) for r in sc['rows'] if r['extracted'] in (None, '')]
  11| print(f'{len(items)} unresolved of {len(sc["rows"])}', flush=True)
  12| def one(x):
  13|     b = bench[x['id']]; r = resp[x['id']]
  14|     p = ("A math response is graded against a reference answer. The automatic extractor found no boxed/final answer. Read the response and decide whether it states a final answer "
  15|          "that is mathematically equivalent to the reference (equivalent forms count; a response that never commits to one final answer is NOT equivalent). Quote the final answer you found.\n\n"
  16|          f"PROBLEM:\n{b['problem_el']}\n\nREFERENCE ANSWER: {b['answer']}\n\nRESPONSE:\n{(r.get('response') or '')[-3000:]}")
  17|     j = B.sol_json(p, SCH, effort='medium', timeout=600); return None if j is None else dict(id=x['id'], equivalent=j['equivalent'], final_answer_found=j['final_answer_found'], note=j['note'])
  18| out = a.score.replace('_score.json', '_adjudicated.jsonl'); B.run_jobs(items, one, out, stage='math500 adjudicate unresolved')
  19| rows = B.load(out); print(f'adjudicated {len(rows)}: {sum(1 for r in rows if r["equivalent"])} equivalent')
  20| 

=== FILE data/math/cut2/polish_targets.py (31 lines) ===
   1| #!/usr/bin/env python3
   2| """Guarded Greek language-polish pass over the generated cut-2 solutions (owner rule: every adapted artefact gets a language-correction pass before it is
   3| called done). Sol medium edits LANGUAGE ONLY; guards revert any edit that changes a LaTeX region, the number multiset, the \\boxed answer or the line
   4| count by more than 2. Writes out/polish.jsonl {id, status: edited|unchanged|reverted|failed, text, changes}. Usage: WORKERS=48 python3 polish_targets.py"""
   5| import json, os, re, sys, unicodedata
   6| HERE = os.path.dirname(os.path.abspath(__file__)); OUT = f'{HERE}/out'; sys.path.insert(0, f'{HERE}/../../benchmarks_el'); sys.path.insert(0, f'{HERE}/../../benchmarks_el/math500'); sys.path.insert(0, f'{HERE}/..')
   7| import bench_lib as B
   8| from verify_final import regions
   9| from polish import polish_one, nfc
  10| def L(p): return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []
  11| import hashlib
  12| val = {r['id'] for r in L(f'{OUT}/validity.jsonl') if r.get('valid') and r.get('severity') != 'major'}   # keyed id|sha8
  13| items = {}
  14| for name in ('solutions_el_repair_high.jsonl', 'solutions_el_l4_high.jsonl', 'level5_solutions_el_high.jsonl', 'solutions_el.jsonl'):
  15|     for r in L(f'{OUT}/{name}'):
  16|         if r['id'] in items: continue
  17|         key = f"{r['id']}|{hashlib.sha256(r['solution_el'].encode('utf-8')).hexdigest()[:8]}"
  18|         if key in val: items[r['id']] = dict(r, id=key, pid=r['id'])   # polish results are bound to the exact input solution (astra 14 Sept: an id-only key could resurrect an obsolete polished text)
  19| GUARD = ("Το κείμενο είναι ΛΥΣΗ μαθηματικού προβλήματος για εκπαίδευση μοντέλου. Το LaTeX ($...$, \\[...\\], \\begin...\\end), όλοι οι αριθμοί, τα σύμβολα, το \\boxed{...} "
  20|          "και η δομή των γραμμών μένουν ΧΑΡΑΚΤΗΡΑ ΠΡΟΣ ΧΑΡΑΚΤΗΡΑ όπως είναι· διορθώνεις μόνο την ελληνική πρόζα ανάμεσά τους. ")
  21| NUM = re.compile(r'\d+(?:[.,]\d+)?')
  22| def one(r):
  23|     old = r['solution_el']; new, ch = polish_one(old, GUARD)
  24|     if new is None: return dict(id=r['id'], pid=r['pid'], status='failed')
  25|     if nfc(new) == nfc(old): return dict(id=r['id'], pid=r['pid'], status='unchanged')
  26|     ok = (regions(new) == regions(old) and sorted(NUM.findall(new)) == sorted(NUM.findall(old)) and re.findall(r'\\boxed\{.*\}', new) == re.findall(r'\\boxed\{.*\}', old)
  27|           and abs(new.count('\n') - old.count('\n')) <= 2)
  28|     return dict(id=r['id'], pid=r['pid'], status='edited' if ok else 'reverted', text=new if ok else None, changes=ch)
  29| res = B.run_jobs(list(items.values()), one, f'{OUT}/polish.jsonl', stage='cut2 polish targets')
  30| import collections; print(collections.Counter(d['status'] for d in res))
  31| 

=== FILE data/math/cut2/run_batches.py (135 lines) ===
   1| #!/usr/bin/env python3
   2| """Run the cut-2 Sol batches (resumable, parallel; flags per data/benchmarks_el/bench_lib.py). Stages: fidelity | solutions | level5_problems | level5_solutions.
   3| Usage: WORKERS=48 python3 run_batches.py <stage> [--effort medium|high]   (level5_solutions needs level5_problems done: it translates the reference solution given the Greek problem)."""
   4| import os, sys, os, json, argparse, hashlib
   5| HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'benchmarks_el')); sys.path.insert(0, os.path.join(HERE, '..'))
   6| import bench_lib as B, mathlib as M
   7| PREP = os.path.join(HERE, 'prep'); OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
   8| SCH = {
   9|  'fidelity': M.write_schema('cut2_fidelity', {'type': 'object', 'properties': {'faithful': {'type': 'boolean'}, 'discrepancies': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['faithful', 'discrepancies'], 'additionalProperties': False}),
  10|  'solution': M.write_schema('cut2_solution', {'type': 'object', 'properties': {'solution_el': {'type': 'string'}}, 'required': ['solution_el'], 'additionalProperties': False}),
  11|  'validate': M.write_schema('cut2_validate', {'type': 'object', 'properties': {'valid': {'type': 'boolean'}, 'answer_equivalent': {'type': 'boolean'}, 'severity': {'type': 'string', 'enum': ['none', 'minor', 'major']}, 'issues': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['valid', 'answer_equivalent', 'severity', 'issues'], 'additionalProperties': False}),
  12|  'problem': M.write_schema('cut2_problem', {'type': 'object', 'properties': {'problem_el': {'type': 'string'}, 'changes': {'type': 'string'}}, 'required': ['problem_el', 'changes'], 'additionalProperties': False}),
  13| }
  14| RULES = ("Greek conventions: decimal comma (3,5), thousands with a dot (2.000), euro after the number (40 €), natural modern Greek, no transliterated English. "
  15|          "Mathematical notation stays LaTeX exactly as in the source. Do not add or drop any number, condition or step.")
  16| MODEL = 'gpt-5.6-sol'
  17| 
  18| 
  19| def provenance(x, prompt, model, effort):
  20|     input_bytes = json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
  21|     return dict(input_sha256=hashlib.sha256(input_bytes).hexdigest(),
  22|                 prompt_sha256=hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
  23|                 model=model, effort=effort)
  24| 
  25| 
  26| def fidelity(x, effort):
  27|     p = (f"You compare a Greek translation of a math problem with the English original. Report faithful=true ONLY if every number, quantity, condition, unit and the question itself are preserved "
  28|          f"(localised names, currency and decimal notation are allowed). List every discrepancy in English, precisely.\n\nENGLISH:\n{x['problem_en']}\n\nGREEK:\n{x['problem_el']}")
  29|     r = B.sol_json(p, SCH['fidelity'], effort=effort); return None if r is None else dict(id=x['id'], faithful=r['faithful'], discrepancies=r['discrepancies'])
  30| def validate(x, effort):
  31|     """F2 of the plan review (14 Sept): every generated Greek derivation is checked against the pinned English source solution and reference answer
  32|     (source-fidelity verification, not a solver-agreement filter): steps correct, no condition added/dropped vs the problem, method corresponds to the
  33|     reference (a different fully correct method is acceptable), boxed answer semantically equivalent to the reference."""
  34|     p = (f"You verify a Greek worked solution against its pinned English source. Report valid=true ONLY if: every step is mathematically correct; no condition, quantity or "
  35|          f"assumption is added or dropped relative to the problem; the derivation actually reaches the boxed answer (no gap that skips the hard part); the boxed answer is "
  36|          f"mathematically equivalent to the reference answer (different but equivalent forms are fine); and the method corresponds to the reference solution, or is a different "
  37|          f"method that is fully correct. answer_equivalent reports only the boxed-vs-reference comparison. severity: none = valid; minor = valid mathematics with a presentational "
  38|          f"slip; major = a wrong or unsupported step, a gap, or a non-equivalent answer. List every issue precisely in English (step, what is wrong).\n\n"
  39|          f"PROBLEM (Greek):\n{x['problem_el']}\n\nPROBLEM (English source):\n{x['problem_en']}\n\nGREEK SOLUTION UNDER REVIEW:\n{x['solution_el']}\n\n"
  40|          f"ENGLISH SOURCE SOLUTION:\n{x['solution_en']}\n\nREFERENCE ANSWER: {x['ref']}")
  41|     r = B.sol_json(p, SCH['validate'], effort=effort)
  42|     return None if r is None else dict(id=x['id'], valid=r['valid'], answer_equivalent=r['answer_equivalent'], severity=r['severity'], issues=r['issues'], solution_sha256=hashlib.sha256(x['solution_el'].encode('utf-8')).hexdigest(), effort=effort)
  43| def fidelity_adjudicate(x):
  44|     """Second stage of the problem-fidelity screen (14 Sept): the medium pass flags 9% while the 300-row high sample flagged 3%, and the flagged
  45|     discrepancies are mostly allowed localisations (materials, grade letters mapped to an equivalent threshold, phrasing of a ratio). A HIGH judge
  46|     re-decides every flagged row under the mathematical-fidelity rule; a row is dropped only when both stages flag it."""
  47|     p = (f"You adjudicate whether a Greek adaptation of a math word problem preserves the MATHEMATICS of the English original. Report faithful=true unless at least one of these "
  48|          f"changed: a number or quantity; a relation between quantities (e.g. 'x times', 'more than', 'half of'); a condition that affects the computation (a threshold, an ordering, "
  49|          f"who does what, when); the unit system in a way that changes the arithmetic; or the question being asked. ALLOWED and NOT a discrepancy: localised names, places, currency, "
  50|          f"decimal/thousands notation, materials or objects (stone -> cement), institutions, grading scales mapped to an equivalent threshold, idiomatic rephrasing of the same relation, "
  51|          f"and added or dropped decorative detail that no computation uses. A first reviewer flagged this row for: {x.get('first_flag', '')}. Decide independently; list only "
  52|          f"discrepancies that change the mathematics, in English.\n\nENGLISH:\n{x['problem_en']}\n\nGREEK:\n{x['problem_el']}")
  53|     r = B.sol_json(p, SCH['fidelity'], effort='high'); return None if r is None else dict(id=x['id'], faithful=r['faithful'], discrepancies=r['discrepancies'], stage='adjudication_high')
  54| def solution(x, effort, model=MODEL):
  55|     hard = str(x.get('level', '')) in ('Level 4', 'Level 5')   # 14 Sept: the 100-250-word band capped Level 5 at the English reference's length (ratio 1.01); hard problems get no upper band
  56|     band = ('as long as the derivation needs: write out every step, every case and every algebraic manipulation; hard problems typically need 150 to 400 words; never a bare answer' if hard
  57|             else 'typically 100 to 250 words; never a bare answer')
  58|     p = (f"Write a complete worked solution in Greek for this math problem, for a Greek student: chain-of-thought style, every step written out with its equation and its intermediate result, "
  59|          f"in the style of a full tutoring solution ({band}), and end with the final answer inside \\boxed{{}} exactly in the form of the reference answer. "
  60|          f"Use the English reference solution as the guide to the METHOD, but write out the reasoning fully even where the reference skips steps. {RULES}\n\n"
  61|          f"GREEK PROBLEM:\n{x['problem_el']}\n\nREFERENCE SOLUTION (English, method guide):\n{x['solution_en']}\n\nREFERENCE ANSWER: {x['ref']}")
  62|     r = B.sol_json(p, SCH['solution'], model=model, effort=effort); return None if r is None else dict(id=x['id'], solution_el=r['solution_el'], ref=x['ref'], level=x.get('level'), src=x.get('src'), generation=provenance(x, p, model, effort))
  63| def problem(x, effort, model=MODEL):
  64|     p = (f"Translate this competition math problem into natural Greek, preserving every number, condition and the question; localise names and currency only when that does not change the mathematics; keep LaTeX as is. {RULES}\n\nENGLISH:\n{x['problem_en']}")
  65|     r = B.sol_json(p, SCH['problem'], model=model, effort=effort); return None if r is None else dict(id=x['id'], problem_el=r['problem_el'], changes=r['changes'], problem_en=x['problem_en'], solution_en=x['solution_en'], subject=x['subject'], level='Level 5', generation=provenance(x, p, model, effort))
  66| SOLUTION_FILES = ('solutions_el_repair_high.jsonl', 'solutions_el_l4_high.jsonl', 'level5_solutions_el_high.jsonl', 'solutions_el.jsonl')   # preference order (first wins)
  67| def best_solutions():
  68|     """One solution per id: a high-effort repair beats the Level-4 high regeneration beats the Level-5 high file beats the medium file."""
  69|     out = {}
  70|     for name in SOLUTION_FILES:
  71|         path = f'{OUT}/{name}'
  72|         if not os.path.exists(path): continue
  73|         for x in B.load(path):
  74|             if x['id'] not in out: out[x['id']] = dict(x, _file=name)
  75|     return out
  76| def sources():
  77|     src = {x['id']: x for x in B.load(f'{PREP}/translations_with_reference.jsonl')}
  78|     for x in B.load(f'{OUT}/level5_problems_el.jsonl'):
  79|         if x['id'] not in src: src[x['id']] = dict(x, ref=M.boxed(x['solution_en']) or '')
  80|     return src
  81| def main():
  82|     ap = argparse.ArgumentParser(); ap.add_argument('stage', choices=['fidelity', 'fidelity_all', 'solutions', 'level5_problems', 'level5_solutions', 'level5_solutions_high', 'validate', 'l4_high', 'repair_high', 'fidelity_adjudicate', 'fidelity_audit_passes']); ap.add_argument('--effort', default='medium'); a = ap.parse_args()
  83|     if a.stage == 'fidelity': B.run_jobs(B.load(f'{PREP}/batch_fidelity_sample.jsonl'), lambda x: fidelity(x, 'high' if a.effort == 'medium' else a.effort), f'{OUT}/fidelity_sample.jsonl', stage='cut2 fidelity')
  84|     elif a.stage == 'fidelity_all':   # 14 Sept: the 300-row sample gave 3.0% unfaithful (> the 2% rule) -> check EVERY problem translation at high; output keyed by id
  85|         done = {x['id'] for x in B.load(f'{OUT}/fidelity_sample.jsonl')} if os.path.exists(f'{OUT}/fidelity_sample.jsonl') else set()
  86|         items = [x for x in B.load(f'{PREP}/translations_with_reference.jsonl') if x['id'] not in done]
  87|         seen = set(x['id'] for x in items) | done
  88|         for x in B.load(f'{OUT}/level5_problems_el.jsonl'):
  89|             if x['id'] not in seen: seen.add(x['id']); items.append(dict(id=x['id'], problem_en=x['problem_en'], problem_el=x['problem_el']))
  90|         B.run_jobs(items, lambda x: fidelity(x, os.environ.get('FIDELITY_EFFORT', 'medium')), f'{OUT}/fidelity_all.jsonl', stage='cut2 fidelity_all')   # 14 Sept: medium (number/condition preservation, not derivation); the 300-row sample ran at high
  91|     elif a.stage == 'validate':   # every current best solution, keyed by id|sha8 so regenerated solutions are re-validated, never skipped
  92|         src = sources(); items = []
  93|         for pid, x in best_solutions().items():
  94|             if pid not in src: continue
  95|             s0 = src[pid]; sha = hashlib.sha256(x['solution_el'].encode('utf-8')).hexdigest()
  96|             items.append(dict(id=f"{pid}|{sha[:8]}", pid=pid, problem_el=s0['problem_el'], problem_en=s0['problem_en'], solution_en=s0['solution_en'], ref=s0.get('ref', ''), solution_el=x['solution_el'], _file=x['_file']))
  97|         def v(x):
  98|             r = validate(x, 'high'); return None if r is None else dict(r, id=x['id'], pid=x['pid'], source_file=x['_file'])
  99|         B.run_jobs(items, v, f'{OUT}/validity.jsonl', stage='cut2 validate')
 100|     elif a.stage == 'l4_high':   # 14 Sept (owner): Level 4 was partly capped by the 100-250-word band (ratio 1.40, 29% shorter than the reference): regenerate ALL Level-4 rows at high, uncapped
 101|         items = [dict(x, level='Level 4') for x in B.load(f'{PREP}/translations_with_reference.jsonl') if str(x.get('level_src') or x.get('level')) == 'Level 4']
 102|         B.run_jobs(items, lambda x: solution(x, 'high'), f'{OUT}/solutions_el_l4_high.jsonl', stage='cut2 Level-4 HIGH')
 103|     elif a.stage == 'repair_high':   # regenerate at high every id whose current best solution failed the validity check (invalid or major); re-validate afterwards
 104|         src = sources(); best = best_solutions(); bad = set()
 105|         for r in B.load(f'{OUT}/validity.jsonl'):
 106|             pid = r.get('pid') or r['id'].split('|')[0]; x = best.get(pid)
 107|             if x and r['id'].endswith('|' + hashlib.sha256(x['solution_el'].encode('utf-8')).hexdigest()[:8]) and (not r['valid'] or r['severity'] == 'major'): bad.add(pid)
 108|         items = [dict(src[pid], level=src[pid].get('level_src') or src[pid].get('level')) for pid in sorted(bad) if pid in src]
 109|         print(f'repair_high: {len(items)} ids failed validity on their current best solution', flush=True)
 110|         B.run_jobs(items, lambda x: solution(x, 'high'), f'{OUT}/solutions_el_repair_high.jsonl', stage='cut2 repair HIGH')
 111|     elif a.stage == 'fidelity_adjudicate':   # every row flagged by the medium pass (and the sample's high flags) gets a HIGH adjudication under the mathematical-fidelity rule
 112|         src = sources(); items = []
 113|         for path in (f'{OUT}/fidelity_all.jsonl', f'{OUT}/fidelity_sample.jsonl'):
 114|             for r in B.load(path):
 115|                 if not r['faithful'] and r['id'] in src: s0 = src[r['id']]; items.append(dict(id=r['id'], problem_en=s0['problem_en'], problem_el=s0['problem_el'], first_flag='; '.join(r.get('discrepancies') or [])[:600]))
 116|         print(f'fidelity_adjudicate: {len(items)} flagged rows', flush=True)
 117|         B.run_jobs(items, fidelity_adjudicate, f'{OUT}/fidelity_adjudicated.jsonl', stage='cut2 fidelity adjudication HIGH')
 118|     elif a.stage == 'fidelity_audit_passes':   # astra 14 Sept: adjudicating only flagged rows measures false alarms; a random 300 of the medium PASSES re-judged at high measures missed defects
 119|         import random as _r; src = sources(); passed = [r['id'] for r in B.load(f'{OUT}/fidelity_all.jsonl') if r['faithful'] and r['id'] in src]
 120|         pick = _r.Random(42).sample(passed, min(300, len(passed))); items = [dict(id=pid, problem_en=src[pid]['problem_en'], problem_el=src[pid]['problem_el']) for pid in pick]
 121|         B.run_jobs(items, lambda x: fidelity(x, 'high'), f'{OUT}/fidelity_audit_passes.jsonl', stage='cut2 fidelity audit of medium passes (HIGH)')
 122|         rows = B.load(f'{OUT}/fidelity_audit_passes.jsonl'); print(f'audit of medium passes: {len(rows)} rows, {sum(1 for r in rows if not r["faithful"])} flagged at high (missed-defect rate {100*sum(1 for r in rows if not r["faithful"])/max(1,len(rows)):.1f}%)', flush=True)
 123|     elif a.stage == 'solutions': B.run_jobs(B.load(f'{PREP}/translations_with_reference.jsonl'), lambda x: solution(x, a.effort), f'{OUT}/solutions_el.jsonl', stage='cut2 solutions')
 124|     elif a.stage == 'level5_problems': B.run_jobs(B.load(f'{PREP}/level5_candidates_en.jsonl'), lambda x: problem(x, a.effort), f'{OUT}/level5_problems_el.jsonl', stage='cut2 level5 problems')
 125|     else:   # level5_solutions (medium, 13 Sept file) or level5_solutions_high (14 Sept: high effort into a separate file; Level 5 is where reasoning effort matters)
 126|         items = []; seen_l5 = set()
 127|         for x in B.load(f'{OUT}/level5_problems_el.jsonl'):
 128|             if x['id'] in seen_l5: continue   # 13 Sept double launch left duplicate ids with different translations: keep the first occurrence (deterministic)
 129|             seen_l5.add(x['id'])
 130|             import re; b = re.search(r'\\boxed\{(.*)\}', x['solution_en'] or '', re.S); ref = M.boxed(x['solution_en']) or ''
 131|             items.append(dict(x, ref=ref, src='math'))
 132|         if a.stage == 'level5_solutions_high': B.run_jobs(items, lambda x: solution(x, 'high'), f'{OUT}/level5_solutions_el_high.jsonl', stage='cut2 level5 solutions HIGH')
 133|         else: B.run_jobs(items, lambda x: solution(x, a.effort), f'{OUT}/level5_solutions_el.jsonl', stage='cut2 level5 solutions')
 134| if __name__ == '__main__': main()
 135| 

=== FILE cluster/drivers/cut2_after_solutions.sh (19 lines) ===
   1| set -u; cd ~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments; PY=$HOME/Projects/apertus-local-chat/.venv/bin/python; LOG=data/math/cut2/out/run.log; O=data/math/cut2/out
   2| say(){ echo "[$(date '+%m-%d %H:%M')] $*" | tee -a $LOG; }
   3| say "CHAIN v5 (audit of medium passes; polish at 64; assembly under the venv): waits for fidelity_all (pid 91791) and Level-4 HIGH (pid 91792); then stragglers at high (32) -> fidelity ADJUDICATION at high (64) -> validate (64) -> repair_high (32) -> validate -> polish (48) -> assemble; second pass after Level-5"
   4| while kill -0 91791 2>/dev/null || kill -0 91792 2>/dev/null; do sleep 30; done; say "fidelity_all + Level-4 HIGH ended: $(grep -c . $O/fidelity_all.jsonl) fidelity rows, $(grep -c . $O/solutions_el_l4_high.jsonl) L4 rows"
   5| WORKERS=32 $PY data/math/cut2/run_batches.py solutions --effort high > $O/solutions_resume.log 2>&1; say "solutions resume (stragglers at high) exit $?: $(grep -m1 'to do' $O/solutions_resume.log | cut -c1-100)"
   6| WORKERS=64 $PY data/math/cut2/run_batches.py fidelity_adjudicate > $O/fidelity_adjudicate.log 2>&1; say "fidelity adjudication exit $?: $(grep -m1 'flagged rows' $O/fidelity_adjudicate.log) -> $(python3 -c "import json; r=[json.loads(l) for l in open('$O/fidelity_adjudicated.jsonl')]; print(len(r),'adjudicated,',sum(1 for x in r if x['faithful']),'overturned (faithful)')" 2>/dev/null)"
   7| WORKERS=64 $PY data/math/cut2/run_batches.py fidelity_audit_passes > $O/fidelity_audit.log 2>&1; say "fidelity audit of medium passes exit $?: $(grep -m1 'audit of medium passes' $O/fidelity_audit.log | cut -c1-160)"
   8| WORKERS=64 $PY data/math/cut2/run_batches.py validate > $O/validate.log 2>&1; say "validate exit $?: $(tail -1 $O/validate.log | cut -c1-120)"
   9| WORKERS=32 $PY data/math/cut2/run_batches.py repair_high > $O/repair_high.log 2>&1; say "repair_high exit $?: $(grep -m1 'repair_high:' $O/repair_high.log)"
  10| WORKERS=64 $PY data/math/cut2/run_batches.py validate > $O/validate_r.log 2>&1; say "re-validate exit $?: $(tail -1 $O/validate_r.log | cut -c1-120)"
  11| WORKERS=64 $PY data/math/cut2/polish_targets.py > $O/polish.log 2>&1; say "polish exit $?: $(tail -1 $O/polish.log | cut -c1-120)"
  12| $PY data/math/cut2/assemble_cut2.py > $O/assemble_pass1.log 2>&1; say "assemble pass 1: $(tail -1 $O/assemble_pass1.log | cut -c1-160)"
  13| while pgrep -f "run_batches.py level5_solutions_high" >/dev/null; do sleep 60; done; say "Level-5 HIGH complete: $(grep -c . $O/level5_solutions_el_high.jsonl) rows"
  14| WORKERS=64 $PY data/math/cut2/run_batches.py validate > $O/validate2.log 2>&1; say "validate (L5) exit $?: $(tail -1 $O/validate2.log | cut -c1-120)"
  15| WORKERS=32 $PY data/math/cut2/run_batches.py repair_high > $O/repair_high2.log 2>&1; say "repair_high (L5) exit $?: $(grep -m1 'repair_high:' $O/repair_high2.log)"
  16| WORKERS=64 $PY data/math/cut2/run_batches.py validate > $O/validate3.log 2>&1; say "re-validate (L5) exit $?"
  17| WORKERS=64 $PY data/math/cut2/polish_targets.py > $O/polish2.log 2>&1; say "polish (L5) exit $?: $(tail -1 $O/polish2.log | cut -c1-120)"
  18| $PY data/math/cut2/assemble_cut2.py > $O/assemble_pass2.log 2>&1; say "assemble pass 2: $(tail -1 $O/assemble_pass2.log | cut -c1-160)"; say "CUT2_CHAIN_DONE"
  19| 

=== FILE data/mixlib.py (37 lines) ===
   1| #!/usr/bin/env python3
   2| """Shared manifest checks for the assemblers (astra 14 Sept F2): the round-one decontamination rule (NFKC+casefold word 8-grams of every USER turn
   3| against data/cache/evals; a row is dropped at >= 0.5 containment), the exact Apertus tokenizer (required, no approximate fallback for a manifest),
   4| and a length gate. Import: from mixlib import Decon, ntok, row_tokens, sup_tokens"""
   5| import json, os, re, glob, unicodedata, pathlib
   6| HERE = pathlib.Path(__file__).resolve().parent
   7| WORD_RE = re.compile(r"\w+", flags=re.UNICODE)
   8| def normalize_text(t): return " ".join(WORD_RE.findall(unicodedata.normalize("NFKC", t).casefold()))
   9| def ngrams(n_text, n=8):
  10|     w = n_text.split()
  11|     if not w: return frozenset()
  12|     return frozenset({tuple(w)}) if len(w) < n else frozenset(tuple(w[i:i+n]) for i in range(len(w)-n+1))
  13| class Decon:
  14|     def __init__(self, cache_dir=None):
  15|         self.eval_grams = {}
  16|         for f in sorted(glob.glob(str((cache_dir or HERE / 'cache' / 'evals') / '*.jsonl') if cache_dir is None else os.path.join(cache_dir, '*.jsonl'))):
  17|             suite = os.path.basename(f).split('.')[0]
  18|             for l in open(f):
  19|                 if l.strip():
  20|                     r = json.loads(l)
  21|                     for g in ngrams(normalize_text(str(r['text']))): self.eval_grams.setdefault(g, (suite, str(r['eval_id'])))
  22|     def contaminated(self, messages):
  23|         for m in messages:
  24|             if m['role'] != 'user': continue
  25|             gs = ngrams(normalize_text(m['content']))
  26|             if gs and sum(1 for g in gs if g in self.eval_grams) / len(gs) >= 0.5: return self.eval_grams[next(g for g in gs if g in self.eval_grams)]
  27|         return None
  28| try:
  29|     from tokenizers import Tokenizer
  30|     _tok = Tokenizer.from_file(glob.glob(os.path.expanduser('~/.cache/huggingface/hub/models--swiss-ai--Apertus-8B-2509/snapshots/*/tokenizer.json'))[0]); TOKMODE = 'apertus-tokenizer (content only, +8 per turn; the trainer dry-run gives the exact rendered count)'
  31|     def ntok(s): return len(_tok.encode(s).ids)
  32| except Exception as e:
  33|     TOKMODE = None
  34|     def ntok(s): raise SystemExit(f'exact tokenizer unavailable ({e.__class__.__name__}): run under the apertus-local-chat venv; a manifest is never built with approximate token counts')
  35| def row_tokens(messages): return sum(ntok(m['content']) + 8 for m in messages)
  36| def sup_tokens(messages): return sum(ntok(m['content']) for m in messages if m['role'] == 'assistant' and m.get('train', True))
  37| 

=== FILE data/assemble_pass_r4.py (65 lines) ===
   1| #!/usr/bin/env python3
   2| """Phase C (R4 plan §5): the Greek pass for R4 = arm B's pass rows (data/arms/R2_idB/train.jsonl: greek_ours, personality_v3 x4, greek_rewrite, 5% replay)
   3| MINUS the openmath_gsm replay (the 13.5x-repeated block) + conversation suite x2 (data/convskills/v2/final) + correcting v2 x2 (no v1 fallback) + a MATHS
   4| component sized to a fraction of the pass's supervised tokens (default 15%), drawn round-robin from the winning Greek block (all levels, incl. Level 5 and
   5| native) and the A2 English block (GSM8K dedup + MATH published) with level coverage recorded. Output data/arms/<arm>/{train,dev}.jsonl + receipt.json.
   6| Usage: python3 assemble_pass_r4.py --arm R4_pass --greek data/math/cut2/final/arm_M2.jsonl [--math-frac 0.15] [--seed 42]"""
   7| import argparse, json, random, collections, hashlib, glob, os, pathlib
   8| HERE = pathlib.Path(__file__).resolve().parent
   9| ap = argparse.ArgumentParser(); ap.add_argument('--arm', required=True); ap.add_argument('--greek', required=True); ap.add_argument('--math-frac', type=float, default=0.15); ap.add_argument('--seed', type=int, default=42)
  10| ap.add_argument('--base', default=str(HERE / 'arms' / 'R2_idB')); ap.add_argument('--suite', default=str(HERE / 'convskills' / 'v2' / 'final' / 'rows_final.jsonl')); ap.add_argument('--correcting', default=str(HERE / 'robustness' / 'correcting' / 'v2' / 'rows_v2.jsonl'))
  11| ap.add_argument('--math-en', default=f"{HERE}/math/en/gsm8k_dedup3.jsonl,{HERE}/math/en/math_train_published.jsonl"); a = ap.parse_args(); rng = random.Random(a.seed)
  12| OUT = HERE / 'arms' / a.arm; OUT.mkdir(parents=True, exist_ok=True)
  13| import sys; sys.path.insert(0, str(HERE)); from mixlib import Decon, ntok, row_tokens, sup_tokens, TOKMODE
  14| if TOKMODE is None: ntok('x')   # fails closed
  15| TOK = TOKMODE; DEC = Decon()
  16| def sup(msgs): return sup_tokens(msgs)
  17| def L(p): return [json.loads(l) for l in open(p) if l.strip()]
  18| def render(r):
  19|     turns = r.get('turns') or r.get('messages') or [dict(role='user', content=r['user']), dict(role='assistant', content=r['assistant'])]
  20|     out = [dict(role=t['role'], content=t['content'], **({'train': False} if t['role'] == 'assistant' and t.get('train') is False else {})) for t in turns]
  21|     return out if any(m['role'] == 'assistant' and m.get('train', True) for m in out) else None
  22| base_all = L(f'{a.base}/train.jsonl'); dropped_gsm = sum(1 for r in base_all if r['config'] == 'openmath_gsm')
  23| base = []; base_contaminated = 0; base_long = 0
  24| for r in base_all:   # historical rows get the SAME checks as new blocks (the parent predates the MATH-500/confirm caches)
  25|     if r['config'] == 'openmath_gsm': continue
  26|     if DEC.contaminated(r['messages']): base_contaminated += 1; continue
  27|     if row_tokens(r['messages']) > 4096: base_long += 1; continue
  28|     base.append(r)
  29| rec = dict(arm=a.arm, seed=a.seed, tokenizer=TOK, base=a.base, base_rows=len(base), base_openmath_replay_dropped=dropped_gsm, base_contaminated_dropped=base_contaminated, base_over_window_dropped=base_long, blocks=[])
  30| train = list(base); dev = L(f'{a.base}/dev.jsonl')
  31| def add_block(name, rows, copies, dev_frac=0.01):
  32|     rr = [dict(config=name, id=str(r.get('id')), messages=render(r)) for r in rows]; rr = [r for r in rr if r['messages']]
  33|     n0 = len(rr); rr = [r for r in rr if not DEC.contaminated(r['messages'])]; n1 = len(rr); rr = [r for r in rr if row_tokens(r['messages']) <= 4096]
  34|     rec.setdefault('block_drops', {})[name] = dict(contaminated=n0 - n1, over_window=n1 - len(rr)); rng.shuffle(rr)
  35|     nd = int(round(len(rr) * dev_frac)); dv, tr = rr[:nd], rr[nd:]; dev.extend(dv)
  36|     for c in range(copies): train.extend(dict(r, id=f"{r['id']}#{c}" if c else r['id']) for r in tr)
  37|     s = sum(sup(r['messages']) for r in tr); rec['blocks'].append(dict(block=name, rows=len(rr), dev=nd, copies=copies, supervised_tokens_effective=s * copies)); return s * copies
  38| add_block('convskills', L(a.suite), 2); add_block('correcting_v2', L(a.correcting), 2)
  39| base_sup = sum(sup(r['messages']) for r in train); target = a.math_frac / (1 - a.math_frac) * base_sup   # maths = frac of the final pass's supervised tokens
  40| greek = [r for r in L(a.greek) if not r.get('dev')]; devp = set(json.load(open(f'{HERE}/math/cut2/final/dev_problems_en.json'))) if os.path.exists(f'{HERE}/math/cut2/final/dev_problems_en.json') else set()
  41| en = [r for p in a.math_en.split(',') for r in L(p) if r.get('problem') not in devp]; rng.shuffle(greek); rng.shuffle(en)
  42| en_rows = [dict(id=r['id'], user=r['problem'], assistant=r['generated_solution'], meta=dict(level=r.get('level'), src=r.get('problem_source'))) for r in en]
  43| picked = []; tot = 0; gi = ei = 0; lv = collections.Counter()
  44| while tot < target and (gi < len(greek) or ei < len(en_rows)):   # round-robin Greek / English so both are covered at every dose
  45|     for src, rows, idx in (('greek', greek, gi), ('en', en_rows, ei)):
  46|         if idx < len(rows):
  47|             r = rows[idx]; msgs = render(r)
  48|             if DEC.contaminated(msgs) or row_tokens(msgs) > 4096:
  49|                 if src == 'greek': gi += 1
  50|                 else: ei += 1
  51|                 rec.setdefault('maths_drops', 0); rec['maths_drops'] += 1; continue
  52|             t = sup(msgs); picked.append(dict(config=f'math_{src}', id=f"pass_{r['id']}", messages=msgs)); tot += t; lv[(src, str((r.get('meta') or {}).get('level') or r.get('bucket')))] += 1
  53|             if src == 'greek': gi += 1
  54|             else: ei += 1
  55|         if tot >= target: break
  56| train.extend(picked); rec['maths'] = dict(target_supervised_tokens=int(target), achieved=tot, rows=len(picked), greek_rows=gi, english_rows=ei, by_source_level={f'{k[0]}:{k[1]}': v for k, v in sorted(lv.items())}, fraction_of_pass=round(tot / (base_sup + tot), 4))
  57| rng.shuffle(train); rng.shuffle(dev)
  58| def dump(p, rows):
  59|     h = hashlib.sha256()
  60|     with open(p, 'w') as f:
  61|         for r in rows: s = json.dumps(r, ensure_ascii=False) + '\n'; f.write(s); h.update(s.encode())
  62|     return h.hexdigest()
  63| rec['train'] = dict(rows=len(train), supervised_tokens=base_sup + tot, by_config=dict(collections.Counter(r['config'] for r in train)), sha256=dump(OUT / 'train.jsonl', train)); rec['dev'] = dict(rows=len(dev), sha256=dump(OUT / 'dev.jsonl', dev))
  64| json.dump(rec, open(OUT / 'receipt.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps({k: v for k, v in rec.items() if k != 'blocks'}, ensure_ascii=False)[:1500])
  65| 

=== FILE data/robustness/correcting/v2/build_v2.py (42 lines) ===
   1| #!/usr/bin/env python3
   2| """Correcting v2 (plan §3 A3; astra F8: no fallback to v1). Explicit, documented selection from the Sol labels (classify_v1.py) plus astra's accepted
   3| decision rows (32 pilot + 60 scale: true/false/partial/unresolved, context turns train:false).
   4| Rule: keep a v1 dialogue only if EVERY labelled claim turn has reaction_correct=true; then balance: cap dialogues whose claims are all 'true' (accept)
   5| at the number of dialogues containing a 'false' claim held against (the H10 imbalance), keep all partial/mixed; add every astra row.
   6| Output rows_v2.jsonl in the assembler's 'file' format (turns with train flags) + receipt.json with every count. Usage: python3 build_v2.py"""
   7| import json, os, random, collections, hashlib
   8| HERE = os.path.dirname(os.path.abspath(__file__)); rng = random.Random(2026)
   9| A = os.path.expanduser('~/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2')
  10| def L(p): return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []
  11| v1 = {r['id']: r for r in L(f'{HERE}/../scale/rows/rows_final.jsonl')}; lab = {r['id']: r for r in L(f'{HERE}/labels.jsonl')}
  12| rec = dict(v1_rows=len(v1), labelled=len(lab)); keep_true, keep_false, keep_mixed, drop_wrong, no_claim = [], [], [], [], []
  13| for rid, r in v1.items():
  14|     l = lab.get(rid)
  15|     if l is None: continue
  16|     claims = [t for t in l['turns'] if t['claim_truth'] != 'none']
  17|     if not claims: no_claim.append(rid); continue
  18|     if not all(t['reaction_correct'] for t in claims): drop_wrong.append(rid); continue
  19|     truths = {t['claim_truth'] for t in claims}
  20|     (keep_false if 'false' in truths else keep_true if truths == {'true'} else keep_mixed).append(rid)
  21| rec.update(no_claim=len(no_claim), dropped_wrong_reaction=len(drop_wrong), correct_all_true=len(keep_true), correct_with_false_hold=len(keep_false), correct_mixed=len(keep_mixed))
  22| cap = len(keep_false); rng.shuffle(keep_true); keep_true = sorted(keep_true[:cap]); rec['all_true_kept_after_cap'] = len(keep_true)
  23| rows = []
  24| for rid in keep_false + keep_mixed + keep_true:
  25|     r = v1[rid]; rows.append(dict(id=f'cv1_{rid}', turns=r['turns'], source='correcting_v1_selected', meta=dict(plants=r.get('plants'), labels=lab[rid]['turns'], selection='all claim reactions correct; all-true capped at false-hold count')))
  26| astra = []
  27| for p in (f'{A}/balanced_dialogue_pilot/revision2/scope_revision_train32/candidate_rows.jsonl'   # the later scope revision (4 conversations corrected: pilot48_08_*), per astra's 14 Sept review, f'{A}/dialogue_scale60/accepted_train60/candidate_rows.jsonl'):
  28|     for r in L(p):
  29|         turns = [dict(role=m['role'], content=m['content'], **({'train': False} if m['role'] == 'assistant' and m.get('train') is False else {})) for m in r['messages']]
  30|         if not any(t['role'] == 'assistant' and t.get('train', True) for t in turns): continue
  31|         astra.append(dict(id=f"astra_{r['row_id']}", turns=turns, source='astra_balanced_dialogue', meta=dict(truth_category=r.get('truth_category'), family=r.get('family_id'))))
  32| rec['astra_rows'] = len(astra); rec['astra_truth'] = dict(collections.Counter(r['meta']['truth_category'] for r in astra)); rows += astra
  33| seen = set(); out = []
  34| for r in rows:
  35|     key = hashlib.sha256(json.dumps([t['content'] for t in r['turns']], ensure_ascii=False).encode()).hexdigest()
  36|     if key in seen: rec['content_duplicates_dropped'] = rec.get('content_duplicates_dropped', 0) + 1; continue
  37|     seen.add(key); out.append(r)
  38| rec['rows_v2'] = len(out); rec['no_fallback_to_v1'] = True
  39| with open(f'{HERE}/rows_v2.jsonl', 'w') as f:
  40|     for r in out: f.write(json.dumps(r, ensure_ascii=False) + '\n')
  41| json.dump(rec, open(f'{HERE}/receipt.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps(rec, ensure_ascii=False))
  42| 

=== FILE data/benchmarks_el/math200_confirm/build.py (64 lines) ===
   1| #!/usr/bin/env python3
   2| """MATH-200-el-confirm (R4 plan §5, astra F7): a one-use Greek confirmation set of 200 MATH *test* problems outside MATH-500, level-proportional to
   3| MATH-500 (L1 17, L2 36, L3 42, L4 51, L5 54), no [asy] diagrams, no exact/13-gram overlap with MATH-500 en, translated with the frozen MATH-500 translator
   4| (translate.translate: LaTeX spans and numbers byte-identical), then the guarded language polish (polish.polish_one + the math guards), answers = the
   5| published \\boxed answer. Excluded from all training by the assembler's decontamination once its user texts are added to data/cache/evals (done here).
   6| Usage: WORKERS=24 python3 build.py [--seed 2026]   → problems_el_final.jsonl (MATH-500 row format), receipt.json, ../../cache/evals/math200_confirm.jsonl"""
   7| import json, os, re, sys, random, argparse, unicodedata, collections, glob
   8| HERE = os.path.dirname(os.path.abspath(__file__)); B0 = os.path.join(HERE, '..'); sys.path.insert(0, B0); sys.path.insert(0, os.path.join(B0, 'math500')); sys.path.insert(0, os.path.join(B0, '..', 'math'))
   9| import bench_lib as B; from translate import translate, span_skeletons, numbers; from polish import polish_one, nfc; from verify_final import regions; from mathlib import boxed
  10| ap = argparse.ArgumentParser(); ap.add_argument('--seed', type=int, default=2026); a = ap.parse_args(); rng = random.Random(a.seed)
  11| QUOTA = {'Level 1': 17, 'Level 2': 36, 'Level 3': 42, 'Level 4': 51, 'Level 5': 54}
  12| import pandas as pd
  13| snap = glob.glob(os.path.expanduser('~/.cache/huggingface/hub/datasets--EleutherAI--hendrycks_math/snapshots/*/'))[0]
  14| test = []
  15| for subj in ('algebra', 'counting_and_probability', 'geometry', 'intermediate_algebra', 'number_theory', 'prealgebra', 'precalculus'):
  16|     df = pd.read_parquet(os.path.join(snap, subj, 'test-00000-of-00001.parquet'))
  17|     for i, r in df.iterrows(): test.append(dict(problem=r['problem'], level=r['level'], subject=r.get('type', subj), solution=r['solution'], idx=f'{subj}/{i}'))
  18| WORD = re.compile(r'\w+', flags=re.UNICODE)
  19| def normw(t): return WORD.findall(unicodedata.normalize('NFKC', t).casefold())
  20| m500 = {json.loads(l)['id']: json.loads(l) for l in open(os.path.join(B0, 'math500', 'problems_el_final.jsonl'))}
  21| ex = set(); eg = set()
  22| for r in m500.values():
  23|     ws = normw(r['problem_en']); ex.add(' '.join(ws)); eg |= set(tuple(ws[i:i + 13]) for i in range(len(ws) - 12)) if len(ws) >= 13 else {tuple(ws)}
  24| def overlaps(p):
  25|     ws = normw(p); return ' '.join(ws) in ex or (len(ws) >= 13 and any(tuple(ws[i:i + 13]) in eg for i in range(len(ws) - 12)))
  26| pool = collections.defaultdict(list); drop = collections.Counter()
  27| for r in test:
  28|     if '[asy]' in r['problem'] or '[asy]' in r['solution']: drop['asy'] += 1; continue
  29|     if overlaps(r['problem']): drop['math500_overlap'] += 1; continue
  30|     ans = boxed(r['solution'])
  31|     if not ans: drop['no_boxed_answer'] += 1; continue
  32|     r['answer'] = ans; pool[r['level']].append(r)
  33| pick = []
  34| for lv, k in QUOTA.items(): rng.shuffle(pool[lv]); pick += pool[lv][:k]
  35| for r in pick: r['unique_id'] = f"m200/{r['idx']}"; r['id'] = r['unique_id']
  36| print(f'test {len(test)} rows; dropped {dict(drop)}; pool by level {({k: len(v) for k, v in pool.items()})}; picked {len(pick)}', flush=True)
  37| B.run_jobs(pick, translate, os.path.join(HERE, 'problems_el.jsonl'), stage='math200 translate')   # run_jobs returns only NEW results: always rebuild from the persisted file
  38| want = {r['id'] for r in pick}; tr = [r for r in B.load(os.path.join(HERE, 'problems_el.jsonl')) if r['id'] in want]
  39| if len({r['id'] for r in tr}) != len(want): raise SystemExit(f'translation incomplete: {len({r["id"] for r in tr})} of {len(want)} frozen ids present; rerun')
  40| rows = [r for r in tr if r['check_math_spans'] and r['check_numbers']]; bad = len(tr) - len(rows)
  41| GUARD = "Το LaTeX ($...$, \\[...\\], \\begin...\\end), οι αριθμοί και τα μπλοκ [asy]...[/asy] μένουν ΧΑΡΑΚΤΗΡΑ ΠΡΟΣ ΧΑΡΑΚΤΗΡΑ όπως είναι. "
  42| def pol(r):
  43|     new, ch = polish_one(r['problem_el'], GUARD)
  44|     if new is None: return dict(id=r['id'], status='failed')
  45|     if nfc(new) == nfc(r['problem_el']): return dict(id=r['id'], status='unchanged')
  46|     ok = regions(new) == regions(r['problem_el']) and sorted(re.findall(r'\d+(?:[.,]\d+)?', new)) == sorted(re.findall(r'\d+(?:[.,]\d+)?', r['problem_el'])) and span_skeletons(new) == span_skeletons(r['problem_en'])
  47|     return dict(id=r['id'], status='edited' if ok else 'reverted', text=new if ok else None, changes=ch)
  48| B.run_jobs(rows, pol, os.path.join(HERE, 'polish_checks.jsonl'), stage='math200 polish'); res = {d['id']: d for d in B.load(os.path.join(HERE, 'polish_checks.jsonl'))}
  49| failed = [r['id'] for r in rows if res.get(r['id'], {}).get('status') in (None, 'failed')]
  50| if failed: raise SystemExit(f'polish missing/failed for {len(failed)} rows (e.g. {failed[:3]}); rerun before finalising')
  51| edited = reverted = 0
  52| for r in rows:
  53|     d = res.get(r['id'], {})
  54|     if d.get('status') == 'edited': r['problem_el_prepolish'] = r['problem_el']; r['problem_el'] = d['text']; r['polish_changes'] = d['changes']; edited += 1
  55|     elif d.get('status') == 'reverted': reverted += 1
  56|     r['polished'] = 'gpt-5.6-sol language-only, guarded'; r['final_ok'] = True; r['checks'] = dict(math_spans=True, numbers=True, asy=True); r['provenance'] = dict(set='math200_confirm', seed=a.seed, source='EleutherAI/hendrycks_math test')
  57| with open(os.path.join(HERE, 'problems_el_final.jsonl'), 'w') as f:
  58|     for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
  59| os.makedirs(os.path.join(B0, '..', 'cache', 'evals'), exist_ok=True)
  60| with open(os.path.join(B0, '..', 'cache', 'evals', 'math200_confirm.jsonl'), 'w') as f:
  61|     for r in rows: f.write(json.dumps(dict(eval_id=r['id'] + ':el', text=r['problem_el']), ensure_ascii=False) + '\n'); f.write(json.dumps(dict(eval_id=r['id'] + ':en', text=r['problem_en']), ensure_ascii=False) + '\n')
  62| rec = dict(picked=len(pick), quotas=QUOTA, translated=len(tr), check_failures_dropped=bad, final=len(rows), final_by_level_meets_quota={lv: sum(1 for r in rows if r['level']==lv) for lv in QUOTA}, polished_edited=edited, polish_reverted=reverted, by_level=dict(collections.Counter(r['level'] for r in rows)), dropped_from_pool=dict(drop), seed=a.seed)
  63| json.dump(rec, open(os.path.join(HERE, 'receipt.json'), 'w'), indent=1); print(rec)
  64| 