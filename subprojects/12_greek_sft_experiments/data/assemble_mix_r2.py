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
ap.add_argument('--no-tokenizer', action='store_true'); ap.add_argument('--max-tokens', type=int, default=4032); ap.add_argument('--budget-tokens', type=int, default=0, help='option C: total train tokens; small blocks whole, the rest scaled by their plan share'); ap.add_argument('--seed', type=int, default=2026); ap.add_argument('--dev-fraction', type=float, default=0.01)
args = ap.parse_args(); random.seed(args.seed)
OUT = HERE / 'arms' / args.arm; OUT.mkdir(parents=True, exist_ok=True)

# ---------- plan: block -> (export file, label source, target rows, weight) ----------
# label source: 'labels' = keep rows from <block>.labels.jsonl (+ sol_routed overrides); 'verified:<dir>' = keep_ids.txt; 'all' = take all
PLAN = [
 ('dolci_precise_if', 'dolci_precise_if.jsonl', 'all', 137000, 1),
 ('ifeval_like', 'ifeval_like_raw.jsonl', 'verified:ifeval_like', 56000, 1),
 ('openmath_gsm', 'openmath_gsm_raw.jsonl', 'verified:openmath', 100000, 1),
 ('nemotron_chat', 'nemotron_chat.jsonl', 'labels', 100000, 1),
 ('dolci_chat', 'dolci_chat.jsonl', 'labels', 6000, 1),
 ('dolci_code_algo_20k', 'dolci_code_algo_20k.jsonl', 'labels', 20000, 1),
 ('dolci_reasoning', 'dolci_reasoning.jsonl', 'all', 30000, 1),
 ('puzzles', 'dolci_other.full.jsonl', 'verified:puzzles', 12000, 1),
 ('dolci_tooluse', 'dolci_tooluse.jsonl', 'labels', 30000, 1),
 ('dolci_science', 'dolci_science.jsonl', 'labels', 15000, 1),
 ('smoltalk2_multilingual', 'smoltalk2_multilingual.jsonl', 'labels_or_all', 25000, 1),
 ('dolci_safety', 'dolci_safety.jsonl', 'labels', 10000, 1),
 ('greek_rewrite', 'greek_rewrite_2k.jsonl', 'all', 2000, 1),
 ('greek_ours', None, 'ours', 20000, 2),
]

IDENT = re.compile(r"\b(as an? (ai|artificial intelligence|language model|large language model|llm|virtual assistant|ai assistant|ai language model|chatbot)|i am an? (ai|artificial intelligence|language model|large language model|llm|ai assistant|chatbot)|i'm an? (ai|artificial intelligence|language model|large language model|llm|ai assistant|chatbot)|i'm (chatgpt|claude|gemini|llama|olmo|gpt-4|gpt-3)|i am (chatgpt|claude|gemini|llama|olmo)|my (training|knowledge) (data|cutoff)|knowledge cutoff|i (do not|don't) have (access to )?real[- ]time|i cannot browse the internet|i (do not|don't) have the ability to (browse|access)|i am not able to access|developed by (openai|anthropic|google|meta|ai2|the allen institute|allen institute|mistral|nvidia|zhipu|z\.ai)|allen institute for ai|\bai2\b|"
                   r"en tant qu'?(ia|intelligence artificielle|modèle de langage|assistant ia)|je suis un(e)? (ia|intelligence artificielle|modèle de langage)|"
                   r"als (ki|künstliche intelligenz|sprachmodell|ki-assistent|ki-sprachmodell)|ich bin (eine? )?(ki|künstliche intelligenz|sprachmodell)|"
                   r"come (ia|intelligenza artificiale|modello linguistico)|sono un(a)? (ia|intelligenza artificiale|modello linguistico)|"
                   r"como (ia|inteligencia artificial|modelo de lenguaje|modelo de linguagem)|soy un(a)? (ia|inteligencia artificial|modelo de lenguaje)|sou um(a)? (ia|inteligência artificial|modelo de linguagem)|"
                   r"ως (τεχνητή νοημοσύνη|γλωσσικό μοντέλο|μοντέλο τεχνητής)|είμαι (ένα |μια )?(τεχνητή νοημοσύνη|γλωσσικό μοντέλο))", re.I)
def identity_hit(messages):
    for m in messages:
        if m['role'] == 'assistant' and IDENT.search(m['content']): return True
    return False

def load_ids(path):
    return set(l.strip() for l in open(path) if l.strip()) if os.path.exists(path) else None

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
    return {i for i, d in keep.items() if d == 'keep'}  # adapt rows are NOT taken: no line-cut exists yet, they would train the identity line in

def to_messages(row, block):
    """Trainer contract: system/user/assistant strings only. Tool rows: calls as <function_calls>, tool outputs as user turns."""
    if block == 'ifeval_like': return [dict(role='user', content=row['prompt']), dict(role='assistant', content=row['response'])]
    if block == 'openmath_gsm': return [dict(role='user', content=row['problem']), dict(role='assistant', content=row['generated_solution'])]
    if block == 'greek_rewrite':
        if not row.get('passage') or not row.get('answer'): return None
        return [dict(role='user', content=f"{row['passage'].strip()}\n\n{row['instruction'].strip()}"), dict(role='assistant', content=row['answer'].strip())]
    turns = row.get('turns') or [dict(role='user', content=row['user']), dict(role='assistant', content=row['assistant'])]
    out = []
    for t in turns:
        r, c = t.get('role'), (t.get('content') or '')
        if r == 'environment': r, c = 'user', '<function_results>\n' + c.strip() + '\n</function_results>'
        elif r == 'assistant' and c.startswith('TOOL_CALLS: '): c = '<function_calls>\n' + c[len('TOOL_CALLS: '):].strip() + '\n</function_calls>'
        elif r == 'tool': r, c = 'user', '<function_results>\n' + c.strip() + '\n</function_results>'
        if r not in ('system', 'user', 'assistant'): return None
        if not c.strip(): return None
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
PLAN_TOK = {'dolci_precise_if': 600, 'ifeval_like': 256, 'openmath_gsm': 342, 'nemotron_chat': 1584, 'dolci_chat': 350, 'dolci_code_algo_20k': 388, 'dolci_reasoning': 330, 'puzzles': 330, 'dolci_tooluse': 827, 'dolci_science': 941, 'smoltalk2_multilingual': 511, 'dolci_safety': 302, 'greek_rewrite': 700, 'greek_ours': 351}  # measured mean tokens per row (review F4)
receipt = dict(arm=args.arm, seed=args.seed, scale=args.scale, budget_tokens=args.budget_tokens, blocks=[], tokenizer='exact' if tok else 'approximate'); train, dev = [], []
if args.budget_tokens:
    whole_tok = sum(t * w * PLAN_TOK[b] for b, f, m, t, w in PLAN if b in WHOLE); big_tok = sum(t * w * PLAN_TOK[b] for b, f, m, t, w in PLAN if b not in WHOLE)
    share = max(0.0, (args.budget_tokens - whole_tok) / big_tok) if big_tok else 0
    print(f'token budget {args.budget_tokens/1e6:.0f}M: whole blocks {whole_tok/1e6:.0f}M, big blocks scaled to {share:.2f} of plan ({big_tok*share/1e6:.0f}M)', flush=True)
else: share = 1.0
for block, fname, mode, target, weight in PLAN:
    target = int(target * args.scale * (1.0 if (block in WHOLE or not args.budget_tokens) else share)); rows = []
    if mode == 'ours':
        for f in sorted((HERE / 'cache' / 'sources').glob('*.jsonl')):
            cfg = f.name.split('.')[0]
            for i, r in r1.read_jsonl(f):
                msgs = r.get('el_messages') or r.get('messages')
                if isinstance(msgs, list) and msgs: rows.append(dict(id=f"{cfg}:{r.get('row_id', i)}", messages=[dict(role=m['role'], content=m['content']) for m in msgs if m.get('role') in ('system', 'user', 'assistant')]))
    else:
        src = ANN / 'core_export' / fname if fname != 'greek_rewrite_2k.jsonl' else ANN / fname
        if not src.exists(): receipt['blocks'].append(dict(block=block, status='MISSING export', target=target)); print(f'{block}: export missing', flush=True); continue
        keep = None
        if mode == 'labels' or mode == 'labels_or_all':
            keep = labels_keep(block)
            if keep is None and mode == 'labels': receipt['blocks'].append(dict(block=block, status='MISSING labels', target=target)); print(f'{block}: labels missing', flush=True); continue
        elif mode.startswith('verified:'):
            keep = load_ids(ANN / 'verified' / mode.split(':')[1] / 'keep_ids.txt')
            if keep is None: receipt['blocks'].append(dict(block=block, status='MISSING verified list', target=target)); print(f'{block}: verified list missing', flush=True); continue
        for l in open(src):
            r = json.loads(l); rid = str(r['key'] if block == 'ifeval_like' else r.get('id', r.get('_row', r.get('key', ''))))  # verified lists key ifeval-like rows by `key`
            if block == 'puzzles' and 'puzzle_data' not in rid: continue
            if keep is not None and rid not in keep: continue
            m = to_messages(r, block)
            if m: rows.append(dict(id=rid, messages=m))
    random.shuffle(rows); taken = []; stats = collections.Counter(available=len(rows))
    for r in rows:
        if len(taken) >= target: break
        hit = contaminated(r['messages'])
        if hit: stats['contaminated'] += 1; continue
        if identity_hit(r['messages']): stats['identity_backstop'] += 1; continue  # review F1: full-text regex over every assistant turn, after the judges
        n = n_tokens(r['messages'])
        if n > args.max_tokens: stats['too_long'] += 1; continue  # margin under the trainer's 4,096 so its own render never overflows
        r['block'] = block; r['tokens'] = n; taken.append(r)
    stats['taken'] = len(taken); stats['tokens'] = sum(r['tokens'] for r in taken)
    ndev = max(1, int(len(taken) * args.dev_fraction)) if taken else 0
    dev += taken[:ndev]; train += taken[ndev:] * weight
    receipt['blocks'].append(dict(block=block, status='ok', target=target, weight=weight, **stats))
    print(f"{block:24s} available {stats['available']:7d} taken {stats['taken']:7d} x{weight} tokens {stats['tokens']:10d} contaminated {stats['contaminated']} too_long {stats['too_long']} identity_backstop {stats['identity_backstop']}", flush=True)
random.shuffle(train)
def dump(path, rows):
    h = hashlib.sha256()
    with open(path, 'w') as f:
        for r in rows:
            line = json.dumps(dict(messages=r['messages'], config=r['block'], id=r['id']), ensure_ascii=False) + '\n'; f.write(line); h.update(line.encode())
    return h.hexdigest()
receipt['train'] = dict(rows=len(train), tokens=sum(r['tokens'] for r in train), sha256=dump(OUT / 'train.jsonl', train))
receipt['dev'] = dict(rows=len(dev), tokens=sum(r['tokens'] for r in dev), sha256=dump(OUT / 'dev.jsonl', dev))
json.dump(receipt, open(OUT / 'receipt.json', 'w'), indent=1)
with open(OUT / 'summary.md', 'w') as f:
    f.write(f"# {args.arm}\n\ntrain {receipt['train']['rows']} rows, {receipt['train']['tokens']/1e6:.1f}M tokens ({receipt['tokenizer']}); dev {receipt['dev']['rows']} rows\n\n| block | status | target | available | taken | weight | contaminated | too long | identity backstop |\n|---|---|---|---|---|---|---|---|---|\n")
    for b in receipt['blocks']: f.write(f"| {b['block']} | {b['status']} | {b.get('target')} | {b.get('available','')} | {b.get('taken','')} | {b.get('weight','')} | {b.get('contaminated','')} | {b.get('too_long','')} | {b.get('identity_backstop','')} |\n")
post = sum(1 for r in train if identity_hit(r['messages'])); receipt['post_scan_identity_hits'] = post
print(f'post-assembly identity scan over the written train rows: {post} hits (must be 0)', flush=True)
print(f"TRAIN {receipt['train']['rows']} rows {receipt['train']['tokens']/1e6:.1f}M tokens; DEV {receipt['dev']['rows']} -> {OUT}", flush=True)
