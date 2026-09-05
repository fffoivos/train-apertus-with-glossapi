#!/usr/bin/env python3
"""Assemble the round-two stage-1 mix from exports + screen labels + checker lists.
Writes data/arms/<arm>/{train,dev}.jsonl (messages column, as the trainer expects), receipt.json, summary.md.
Usage: python3 assemble_mix_r2.py --arm R2_stage1 [--scale 1.0] [--no-tokenizer]
Reads ~/sft_annot (exports, labels, verified) and data/cache/sources (our Greek set). Deterministic (seed)."""
import json, sys, os, re, random, hashlib, argparse, collections, unicodedata
from pathlib import Path
HERE = Path(__file__).resolve().parent; ANN = Path.home() / 'sft_annot'
sys.path.insert(0, str(HERE))
class r1:  # the round-one helpers (data/build_sft_mix.py) inlined, so this script needs no `datasets` import
    MAX_LENGTH = 4096; NGRAM_SIZE = 8; CONTAINMENT_THRESHOLD = 0.5
    WORD_RE = re.compile(r"\w+", flags=re.UNICODE); ELLINIKA_ROOT = Path.home() / "Projects/apertus-local-chat/benchmark/data"
    class EvalPrompt:
        def __init__(self, suite, eval_id, text): self.suite, self.eval_id, self.text = suite, eval_id, text
    @staticmethod
    def normalize_text(text): return " ".join(r1.WORD_RE.findall(unicodedata.normalize("NFKC", text).casefold()))
    @staticmethod
    def ngrams(normalized):
        words = normalized.split()
        if not words: return frozenset()
        if len(words) < r1.NGRAM_SIZE: return frozenset({tuple(words)})
        return frozenset(tuple(words[i:i + r1.NGRAM_SIZE]) for i in range(len(words) - r1.NGRAM_SIZE + 1))
    @staticmethod
    def read_jsonl(path):
        with open(path, encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if line: yield i, json.loads(line)
    @staticmethod
    def read_eval_cache(path, suite): return [r1.EvalPrompt(suite, str(row["eval_id"]), str(row["text"])) for _, row in r1.read_jsonl(path)]
    @staticmethod
    def load_ellinika_prompts():
        prompts = []
        for path in sorted(r1.ELLINIKA_ROOT.rglob("*.jsonl")):
            rel = path.relative_to(r1.ELLINIKA_ROOT).as_posix()
            for i, row in r1.read_jsonl(path):
                if isinstance(row.get("prompt"), str) and row["prompt"].strip(): prompts.append(r1.EvalPrompt("ellinika_bench", f"{rel}:{row.get('id', i)}", row["prompt"]))
        return prompts, {"prompts": len(prompts)}

ap = argparse.ArgumentParser(); ap.add_argument('--arm', default='R2_stage1'); ap.add_argument('--scale', type=float, default=1.0)
ap.add_argument('--no-tokenizer', action='store_true'); ap.add_argument('--keep-adapt', action='store_true', help="keep Luna's adapt rows (default: excluded, as in the plan)"); ap.add_argument('--no-judge-tone', action='store_true', help="ignore Luna's mannerism flag (default: tone rule by judge label, as in the plan)"); ap.add_argument('--strict-identity-drops', action='store_true', help='honour every Luna identity drop (default: only when the text carries a self-description phrase)'); ap.add_argument('--max-tokens', type=int, default=4032); ap.add_argument('--budget-tokens', type=int, default=0, help='option C: total train tokens; small blocks whole, the rest scaled by their plan share');
ap.add_argument('--keep-lexicon-mannerism', action='store_true', help='keep rows whose last assistant turn opens/closes with a chatbot phrase (lexicon, all blocks; default dropped)'); ap.add_argument('--keep-mannerism', action='store_true', help='keep rows the judge flagged for chatbot mannerisms (default: dropped in chat and safety blocks)'); ap.add_argument('--drop-imperatives', action='store_true', help='also drop rows flagged for unasked second-person commands'); ap.add_argument('--seed', type=int, default=2026); ap.add_argument('--dev-fraction', type=float, default=0.01)
args = ap.parse_args(); random.seed(args.seed)
OUT = HERE / 'arms' / args.arm; OUT.mkdir(parents=True, exist_ok=True)

# ---------- plan: block -> (export file, label source, target rows, weight) ----------
# label source: 'labels' = keep rows from <block>.labels.jsonl (+ sol_routed overrides); 'verified:<dir>' = keep_ids.txt; 'all' = take all
PLAN = [
 ('dolci_precise_if_20k', 'dolci_precise_if_20k.jsonl', 'labels', 20000, 1),  # Sol spot-check found 27% unusable: only the Sol-screened subset trains
 ('ifeval_like', 'ifeval_like_raw.jsonl', 'verified:ifeval_like', 56000, 1),
 ('openmath_gsm', 'openmath_gsm_raw.jsonl', 'verified:openmath', 100000, 1),
 ('nemotron_chat_a', 'nemotron_chat_a.jsonl', 'labels+langfilter:nemotron_chat', 50000, 1),
 ('nemotron_chat_b', 'nemotron_chat_b.jsonl', 'labels+langfilter:nemotron_chat', 50000, 1),
 ('dolci_chat', 'dolci_chat.jsonl', 'labels+langfilter:dolci_chat', 6000, 1),
 ('dolci_code_algo_20k', 'dolci_code_algo_20k.jsonl', 'labels', 20000, 1),
 ('dolci_reasoning', 'dolci_reasoning.jsonl', 'all', 30000, 1),
 ('puzzles', 'dolci_other.full.jsonl', 'verified:puzzles', 12000, 1),
 ('dolci_tooluse', 'dolci_tooluse.jsonl', 'langfilter:dolci_tooluse', 30000, 1),  # regex + lexicon only (verified BFCL-style source). Luna's 3k-sample verdicts are NOT applied: its 337 drops are the API-irrelevance refusals ("I can't do X; based on the available API I can...") labelled identity/quality-1, wanted behaviour (handoff section 4, item 5)
 ('dolci_science', 'dolci_science.jsonl', 'labels', 15000, 1),
 ('smoltalk2_multilingual', 'smoltalk2_multilingual.jsonl', 'labels_or_all+langfilter:smoltalk2_multilingual', 25000, 1),
 ('dolci_safety', 'dolci_safety.jsonl', 'labels', 10000, 1),
 ('greek_rewrite', 'greek_rewrite_2k.jsonl', 'all', 2000, 1),
 ('greek_ours', None, 'ours', 20000, 2),
]

from identity_patterns import IDENT, identity_hit_messages as identity_hit, mannerism_hit_messages, identity_phrase_hit  # shared with lang_identity_filter.py (review R8); scans assistant and system turns

def load_ids(path):
    return set(l.strip() for l in open(path) if l.strip()) if os.path.exists(path) else None

TONE_BLOCKS = {'nemotron_chat_a', 'nemotron_chat_b', 'dolci_chat', 'dolci_safety', 'smoltalk2_multilingual', 'dolci_science'}
def labels_tone_drop(block):
    """ids the judge flagged for mannerism (and optionally unasked imperatives); Sol's verdict wins where it exists."""
    flags = {}
    for name in (f'{block}.labels.jsonl', f'{block}.sol.jsonl', f'{block}.sol_routed.jsonl'):
        p = ANN / 'labels' / name
        if not p.exists(): continue
        for l in open(p):
            j = json.loads(l); flags[j['id']] = (bool(j.get('mannerism')), bool(j.get('imperatives')))
    out = set()
    for i, (m, imp) in flags.items():
        if (m and not args.no_judge_tone and not args.keep_mannerism) or (imp and args.drop_imperatives): out.add(i)
    return out

IDENTITY_CONDITIONAL = {}  # block -> ids whose Luna identity-drop is conditional on a self-description phrase in the text
def labels_keep(block):
    keep = {}; p = ANN / 'labels' / f'{block}.labels.jsonl'
    if not p.exists(): return None
    for l in open(p):
        j = json.loads(l); keep[j['id']] = j.get('disposition')
    for extra in (f'{block}.sol.jsonl', f'{block}.sol_routed.jsonl'):  # Sol verdicts override Luna's (checker > Sol > Luna)
        p2 = ANN / 'labels' / extra
        if p2.exists():
            for l in open(p2):
                j = json.loads(l)
                if j.get('disposition'): keep[j['id']] = j.get('disposition')
    if not args.strict_identity_drops:  # Luna's identity DROPS are honoured only if the text carries a self-description (checked per row below)
        for l in open(p):
            j = json.loads(l)
            if j.get('disposition') == 'drop' and j.get('frame_type') == 'identity' and (j.get('quality') or 0) >= 2 and not j.get('mannerism') and keep.get(j['id']) == 'drop' and j.get('judge', '').endswith('luna'):
                keep[j['id']] = 'keep'; IDENTITY_CONDITIONAL.setdefault(block, set()).add(j['id'])
    if args.keep_adapt:  # opt-in: adapt rows kept; identity-framed ones still pass the phrase check
        for l in open(p):
            j = json.loads(l)
            if j.get('disposition') == 'adapt' and keep.get(j['id']) == 'adapt' and (j.get('quality') or 0) >= 2:
                keep[j['id']] = 'keep'
                if j.get('frame_type') == 'identity': IDENTITY_CONDITIONAL.setdefault(block, set()).add(j['id'])
    return {i for i, d in keep.items() if d == 'keep'}  # adapt rows are NOT taken: no line-cut exists yet, they would train the identity line in

GREEK_EDITS = {}
_ep = ANN / 'greek_rewrite_2k.edit.jsonl'
if _ep.exists():
    for _l in open(_ep):
        _j = json.loads(_l); GREEK_EDITS[_j['id']] = _j
    print(f'Greek correction pass loaded: {len(GREEK_EDITS)} rows', flush=True)

def to_messages(row, block):
    """Trainer contract: system/user/assistant strings only. Tool rows: calls as <function_calls>, tool outputs as user turns."""
    if block == 'ifeval_like': return [dict(role='user', content=row['prompt']), dict(role='assistant', content=row['response'])]
    if block == 'openmath_gsm': return [dict(role='user', content=row['problem']), dict(role='assistant', content=row['generated_solution'])]
    if block == 'greek_rewrite':
        if not row.get('passage') or not row.get('answer'): return None
        ans = row['answer']; e = GREEK_EDITS.get(row['id'])
        if e and e.get('verdict') in ('edited', 'rewrite') and (e.get('edited_answer') or '').strip(): ans = e['edited_answer']
        return [dict(role='user', content=f"{row['passage'].strip()}\n\n{row['instruction'].strip()}"), dict(role='assistant', content=ans.strip())]
    turns = row.get('turns') or [dict(role='user', content=row['user']), dict(role='assistant', content=row['assistant'])]
    out = []
    for t in turns:
        r, c = t.get('role'), (t.get('content') or '')
        if r == 'environment': r, c = 'user', '<function_results>\n' + c.strip() + '\n</function_results>'
        elif r == 'assistant' and c.startswith('TOOL_CALLS: '): c = '<function_calls>\n' + c[len('TOOL_CALLS: '):].strip() + '\n</function_calls>'
        elif r == 'tool': r, c = 'user', '<function_results>\n' + c.strip() + '\n</function_results>'
        if r not in ('system', 'user', 'assistant'): return None
        if not c.strip():
            if r == 'system': continue  # Nemotron rows carry an empty system turn: drop the turn, not the row
            return None
        if out and out[-1]['role'] == r: out[-1]['content'] += '\n\n' + c  # merge consecutive same-role turns
        else: out.append(dict(role=r, content=c))
    if not out or out[0]['role'] == 'assistant' or out[-1]['role'] != 'assistant': return None
    if not any(m['role'] == 'user' for m in out): return None
    return out

# ---------- evaluation prompts for decontamination ----------
evals = []
for f in sorted((HERE / 'cache' / 'evals').glob('*.jsonl')):
    suite = f.name.split('.')[0]; evals += r1.read_eval_cache(f, suite)
try:
    ell, _ = r1.load_ellinika_prompts(); evals += ell
except Exception as e: print('ellinika prompts unavailable:', str(e)[:80])
eval_grams = {}
for p in evals:
    for g in r1.ngrams(r1.normalize_text(p.text)): eval_grams.setdefault(g, (p.suite, p.eval_id))
print(f'decontamination: {len(evals)} eval prompts, {len(eval_grams)} distinct {r1.NGRAM_SIZE}-grams', flush=True)
def contaminated(messages):
    for m in messages:
        if m['role'] != 'user': continue
        gs = r1.ngrams(r1.normalize_text(m['content']))
        if not gs: continue
        hit = sum(1 for g in gs if g in eval_grams)
        if hit / len(gs) >= r1.CONTAINMENT_THRESHOLD: return eval_grams[next(g for g in gs if g in eval_grams)]
    return None

# ---------- tokenizer for the 4,096 filter ----------
tok = None
if not args.no_tokenizer:
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained('fffoivos/apertus-8b-greek-cpt', revision='18-avg-uniform5-tokens30B-50B')
        ref = AutoTokenizer.from_pretrained('swiss-ai/Apertus-8B-Instruct-2509'); tok.chat_template = ref.chat_template
        print('tokenizer loaded; exact length filter', flush=True)
    except Exception as e: print('tokenizer unavailable, approximate filter (chars/3.2):', str(e)[:100], flush=True)
def n_tokens(messages):
    if tok is not None:
        try:
            ids = tok.apply_chat_template(messages, tokenize=True)
            if hasattr(ids, 'keys'): ids = ids['input_ids']
            return len(ids)
        except Exception: pass
    return int(sum(len(m['content']) for m in messages) / 3.2)

# ---------- build ----------
WHOLE = {'puzzles', 'dolci_chat', 'dolci_safety', 'greek_rewrite', 'greek_ours'}  # small blocks kept whole under a token budget
PLAN_TOK = {'dolci_precise_if_20k': 600, 'ifeval_like': 256, 'openmath_gsm': 342, 'nemotron_chat_a': 1584, 'nemotron_chat_b': 1584, 'dolci_chat': 350, 'dolci_code_algo_20k': 388, 'dolci_reasoning': 330, 'puzzles': 330, 'dolci_tooluse': 827, 'dolci_science': 941, 'smoltalk2_multilingual': 511, 'dolci_safety': 302, 'greek_rewrite': 700, 'greek_ours': 351}  # measured mean tokens per row (review F4)
receipt = dict(arm=args.arm, seed=args.seed, scale=args.scale, budget_tokens=args.budget_tokens, blocks=[], tokenizer='exact' if tok else 'approximate'); train, dev = [], []
def present_rows(block, fname, mode):
    """cheap first pass: how many rows this block can actually contribute today (keep lists ∩ export), for the budget share (review S2)"""
    if mode == 'ours':
        k = labels_keep('greek_ours'); return len(k) if k is not None else 32892
    src = ANN / 'core_export' / fname if fname != 'greek_rewrite_2k.jsonl' else ANN / fname
    if not src.exists(): return 0
    keep = None
    for part in mode.split('+'):
        k = None
        if part in ('labels', 'labels_or_all'): k = labels_keep(block)
        elif part.startswith('verified:'): k = load_ids(ANN / 'verified' / part.split(':')[1] / 'keep_ids.txt')
        elif part.startswith('langfilter:'): k = load_ids(ANN / 'verified' / 'langfilter' / f"{part.split(':')[1]}.keep_ids.txt")
        if k is None and part in ('labels',) : return 0
        if k is None and part.startswith(('verified:', 'langfilter:')): return 0
        if k is not None: keep = k if keep is None else (keep & k)
    n = 0
    for l in open(src):
        if keep is None: n += 1; continue
        r = json.loads(l); rid = str(r['key'] if block == 'ifeval_like' else r.get('id', r.get('_row', r.get('key', ''))))
        if rid in keep: n += 1
    return n
if args.budget_tokens:
    avail = {b: min(present_rows(b, f, m), int(t * args.scale)) for b, f, m, t, w in PLAN}
    print('present rows per block:', {b: n for b, n in avail.items()}, flush=True)
    whole_tok = sum(avail[b] * w * PLAN_TOK[b] for b, f, m, t, w in PLAN if b in WHOLE); big_tok = sum(avail[b] * w * PLAN_TOK[b] for b, f, m, t, w in PLAN if b not in WHOLE)
    share = max(0.0, (args.budget_tokens - whole_tok) / big_tok) if big_tok else 0
    print(f'token budget {args.budget_tokens/1e6:.0f}M: whole blocks {whole_tok/1e6:.0f}M, big blocks scaled to {share:.2f} of plan ({big_tok*share/1e6:.0f}M)', flush=True)
else: share = 1.0
for block, fname, mode, target, weight in PLAN:
    target = int((min(avail[block], int(target * args.scale)) if args.budget_tokens else target * args.scale) * (1.0 if (block in WHOLE or not args.budget_tokens) else share)); rows = []
    if mode == 'ours':
        ours_keep = labels_keep('greek_ours'); ours_tone = labels_tone_drop('greek_ours') if ours_keep is not None else set()  # Luna labels on our own set, when present
        if ours_keep is not None: print(f'greek_ours: judge labels present, keep {len(ours_keep)}, tone drops {len(ours_tone)}', flush=True)
        for f in sorted((HERE / 'cache' / 'sources').glob('*.jsonl')):
            cfg = f.name.split('.')[0]
            for i, r in r1.read_jsonl(f):
                msgs = r.get('el_messages') or r.get('messages')
                rid = f"{cfg}:{r.get('row_id', i)}"
                if ours_keep is not None and (rid not in ours_keep or rid in ours_tone): continue
                if isinstance(msgs, list) and msgs: rows.append(dict(id=rid, messages=[dict(role=m['role'], content=m['content']) for m in msgs if m.get('role') in ('system', 'user', 'assistant')]))
    else:
        src = ANN / 'core_export' / fname if fname != 'greek_rewrite_2k.jsonl' else ANN / fname
        if not src.exists(): receipt['blocks'].append(dict(block=block, status='MISSING export', target=target)); print(f'{block}: export missing', flush=True); continue
        keep = None; missing = None
        for part in mode.split('+'):
            k = None
            if part in ('labels', 'labels_or_all'):
                k = labels_keep(block)
                if k is None and part == 'labels': missing = 'labels'
                if k is None: continue
            elif part.startswith('verified:'):
                k = load_ids(ANN / 'verified' / part.split(':')[1] / 'keep_ids.txt')
                if k is None: missing = 'verified list'
            elif part.startswith('langfilter:'):
                k = load_ids(ANN / 'verified' / 'langfilter' / f"{part.split(':')[1]}.keep_ids.txt")
                if k is None: missing = 'langfilter list'
            elif part.startswith('sample:'):  # rows judged in a sample block: drop those the judge dropped, keep the rest of the block as is
                sk = labels_keep(part.split(':')[1]); sp = ANN / 'labels' / f"{part.split(':')[1]}.labels.jsonl"
                if sk is not None and sp.exists():
                    judged = {json.loads(l)['id'] for l in open(sp)}; dropped = judged - sk
                    keep = (keep - dropped) if keep is not None else None
                    receipt.setdefault('sample_notes', []).append(dict(block=block, sample=part.split(':')[1], judged=len(judged), dropped=len(dropped)))
                continue
            elif part == 'all': continue
            if k is not None: keep = k if keep is None else (keep & k)
            if missing: break
        if missing: receipt['blocks'].append(dict(block=block, status=f'MISSING {missing}', target=target)); print(f'{block}: {missing} missing', flush=True); continue
        tone_drop = labels_tone_drop(block) if block in TONE_BLOCKS else set(); tone_dropped = 0
        for l in open(src):
            r = json.loads(l); rid = str(r['key'] if block == 'ifeval_like' else r.get('id', r.get('_row', r.get('key', ''))))  # verified lists key ifeval-like rows by `key`
            if rid in tone_drop: tone_dropped += 1; continue
            if block == 'puzzles' and 'puzzle_data' not in rid: continue
            if keep is not None and rid not in keep: continue
            m = to_messages(r, block)
            if m: rows.append(dict(id=rid, messages=m))
    random.shuffle(rows); taken = []; stats = collections.Counter(available=len(rows), contaminated=0, too_long=0, identity_backstop=0, lexicon_mannerism=0, tone_dropped=(tone_dropped if mode != 'ours' else 0))
    cond = IDENTITY_CONDITIONAL.get('greek_ours' if mode == 'ours' else block, set())
    for r in rows:
        if len(taken) >= target: break
        hit = contaminated(r['messages'])
        if hit: stats['contaminated'] += 1; continue
        if r['id'] in cond and identity_phrase_hit(r['messages']): stats['identity_judge_confirmed'] += 1; continue  # Luna said identity AND the text says so: drop
        if identity_hit(r['messages']): stats['identity_backstop'] += 1; continue  # review F1: full-text regex over every assistant turn, after the judges
        if not args.keep_lexicon_mannerism and mannerism_hit_messages(r['messages']): stats['lexicon_mannerism'] += 1; continue  # chatbot openers/closers, all blocks
        n = n_tokens(r['messages'])
        if n > args.max_tokens: stats['too_long'] += 1; continue  # margin under the trainer's 4,096 so its own render never overflows
        r['block'] = block; r['tokens'] = n; taken.append(r)
    stats['taken'] = len(taken); stats['tokens'] = sum(r['tokens'] for r in taken)
    ndev = max(1, int(len(taken) * args.dev_fraction)) if taken else 0
    dev += taken[:ndev]; train += taken[ndev:] * weight
    receipt['blocks'].append(dict(block=block, status='ok', target=target, weight=weight, **stats))
    print(f"{block:24s} available {stats['available']:7d} taken {stats['taken']:7d} x{weight} tokens {stats['tokens']:10d} contaminated {stats['contaminated']} too_long {stats['too_long']} identity_backstop {stats['identity_backstop']} lexicon_mannerism {stats['lexicon_mannerism']} tone_dropped {stats['tone_dropped']}", flush=True)
random.shuffle(train)
def dump(path, rows):
    h = hashlib.sha256()
    with open(path, 'w') as f:
        for r in rows:
            line = json.dumps(dict(messages=r['messages'], config=r['block'], id=r['id']), ensure_ascii=False) + '\n'; f.write(line); h.update(line.encode())
    return h.hexdigest()
receipt['train'] = dict(rows=len(train), tokens=sum(r['tokens'] for r in train), sha256=dump(OUT / 'train.jsonl', train))
receipt['dev'] = dict(rows=len(dev), tokens=sum(r['tokens'] for r in dev), sha256=dump(OUT / 'dev.jsonl', dev))
with open(OUT / 'summary.md', 'w') as f:
    f.write(f"# {args.arm}\n\ntrain {receipt['train']['rows']} rows, {receipt['train']['tokens']/1e6:.1f}M tokens ({receipt['tokenizer']}); dev {receipt['dev']['rows']} rows\n\n| block | status | target | available | taken | weight | contaminated | too long | identity backstop |\n|---|---|---|---|---|---|---|---|---|\n")
    for b in receipt['blocks']: f.write(f"| {b['block']} | {b['status']} | {b.get('target')} | {b.get('available','')} | {b.get('taken','')} | {b.get('weight','')} | {b.get('contaminated','')} | {b.get('too_long','')} | {b.get('identity_backstop','')} |\n")
post = sum(1 for r in train if identity_hit(r['messages'])); receipt['post_scan_identity_hits'] = post
print(f'post-assembly identity scan over the written train rows: {post} hits (must be 0)', flush=True)
json.dump(receipt, open(OUT / 'receipt.json', 'w'), indent=1)  # written after the post-scan so the receipt carries it
if args.budget_tokens and receipt['train']['tokens'] > args.budget_tokens:
    print(f"BUDGET EXCEEDED: {receipt['train']['tokens']} train tokens > {args.budget_tokens}", flush=True); sys.exit(3)
if post: print('IDENTITY POST-SCAN FAILED', flush=True); sys.exit(4)
print(f"TRAIN {receipt['train']['rows']} rows {receipt['train']['tokens']/1e6:.1f}M tokens; DEV {receipt['dev']['rows']} -> {OUT}", flush=True)
