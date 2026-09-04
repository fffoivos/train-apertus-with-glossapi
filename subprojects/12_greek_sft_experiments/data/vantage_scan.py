#!/usr/bin/env python3
"""Vantage scan: how many rows of each candidate SFT source carry an anglosphere framing in the ASSISTANT text.
Streams a sample per source/bucket from Hugging Face, applies a marker lexicon, writes per-bucket shares and a
stratified sample for a Terra annotation probe. CPU only. Usage: python3 vantage_scan.py <out_dir> [rows_per_bucket]"""
import json, re, sys, os, time, random, collections
from datasets import load_dataset

OUT = sys.argv[1]; PER = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
os.makedirs(OUT, exist_ok=True)
random.seed(7)

# --- lexicon: framing markers (level 1-2) and identity markers (level 3). Word-boundary, case-sensitive where it matters.
FRAME = {
 'currency': [r'\$\s?\d', r'\bUSD\b', r'\bdollars?\b', r'\bcents?\b', r'£\s?\d', r'\bpounds? sterling\b', r'\bGBP\b'],
 'units': [r'\bmiles?\b', r'\bmph\b', r'\bfeet\b', r'\binches\b', r'\blbs?\b', r'\bpounds\b(?! sterling)', r'\bounces?\b', r'\b°F\b', r'\bFahrenheit\b', r'\bgallons?\b', r'\bacres?\b', r'\bsquare feet\b', r'\bcups? of\b'],
 'us_institutions': [r'\bIRS\b', r'\b401\(k\)', r'\bRoth IRA\b', r'\bSocial Security\b', r'\bMedicare\b', r'\bMedicaid\b', r'\bFDA\b', r'\bCDC\b', r'\bEPA\b', r'\bFBI\b', r'\bDMV\b', r'\bUSDA\b', r'\bSEC\b', r'\bFTC\b', r'\bOSHA\b', r'\bHOA\b', r'\bFAFSA\b', r'\bVA\b loan', r'\bFEMA\b'],
 'uk_institutions': [r'\bNHS\b', r'\bHMRC\b', r'\bOfsted\b', r'\bGCSEs?\b', r'\bA-levels?\b', r'\bcouncil tax\b', r'\bMOT\b test', r'\bDVLA\b'],
 'us_civic': [r'\bZIP code\b', r'\bzip code\b', r'\bCongress\b', r'\bthe Senate\b', r'\bSupreme Court\b', r'\bstate law\b', r'\byour state\b', r'\bcounty\b', r'\bFirst Amendment\b', r'\bSecond Amendment\b', r'\bfelony\b', r'\bmisdemeanor\b', r'\b911\b', r'\battorney\b', r'\bin the US\b', r'\bin the U\.S\.', r'\bin America\b', r'\bAmericans?\b', r'\bin the UK\b', r'\bBritish\b', r'\bfederal\b', r'\bthe President\b'],
 'holidays': [r'\bThanksgiving\b', r'\bFourth of July\b', r'\b4th of July\b', r'\bBlack Friday\b', r'\bSuper Bowl\b', r'\bMemorial Day\b', r'\bLabor Day\b', r'\bIndependence Day\b', r'\bBoxing Day\b', r'\bPresidents\' Day\b'],
 'education': [r'\bGPA\b', r'\bSAT\b', r'\bACT\b scores?', r'\bIvy League\b', r'\bcommunity college\b', r'\bK-12\b', r'\bfreshman\b', r'\bsophomore\b', r'\bhigh school diploma\b', r'\bcollege application\b', r'\bstudent loans?\b'],
 'brands_services': [r'\bWalmart\b', r'\bTarget\b store', r'\bCostco\b', r'\bHome Depot\b', r'\bAmazon Prime\b', r'\bVenmo\b', r'\bZelle\b', r'\bCVS\b', r'\bWalgreens\b', r'\bUber Eats\b', r'\bDoorDash\b', r'\bCraigslist\b', r'\bZillow\b', r'\bTurboTax\b'],
 'places': [r'\bNew York\b', r'\bCalifornia\b', r'\bTexas\b', r'\bFlorida\b', r'\bChicago\b', r'\bLos Angeles\b', r'\bLondon\b', r'\bManhattan\b', r'\bSeattle\b', r'\bBoston\b', r'\bWashington,? D\.?C\.?'],
 'formats': [r'\(\d{3}\)\s?\d{3}-\d{4}', r'\b\d{1,2}/\d{1,2}/\d{4}\b', r'\b\d{5}(?:-\d{4})?\b(?=.*\b(?:ZIP|zip)\b)'],
}
IDENTITY = [r'\bAs an AI language model\b', r'\bas an AI\b', r'\bI am an AI\b', r"\bI'm an AI\b", r'\bI am a language model\b', r'\bdeveloped by (?:OpenAI|Anthropic|Google|Meta|Microsoft|Ai2|Allen Institute|Hugging Face|Mistral|Alibaba|NVIDIA)\b', r'\btrained by (?:OpenAI|Anthropic|Google|Meta|Microsoft)\b', r'\bI am (?:ChatGPT|Claude|Gemini|Llama|Bard|Assistant|GPT-4|GPT-3)\b', r'\bOpenAI\b', r'\bAnthropic\b', r'\bknowledge cutoff\b', r'\bI don\'t have (?:personal )?(?:feelings|access to real-time)\b']
GREEK = [r'\bGreece\b', r'\bGreek\b', r'\bAthens\b', r'\beuros?\b', r'€', r'[Ͱ-Ͽ]{3,}']
FRAME_RE = {k: [re.compile(p) for p in v] for k, v in FRAME.items()}
ID_RE = [re.compile(p) for p in IDENTITY]; GR_RE = [re.compile(p) for p in GREEK]

def text_of(content):
    if content is None: return ''
    if isinstance(content, str): return content
    if isinstance(content, dict):
        if content.get('text'): return content['text']
        parts = content.get('parts') or []
        return ' '.join(p.get('text', '') for p in parts if isinstance(p, dict))
    if isinstance(content, list): return ' '.join(text_of(c) for c in content)
    return str(content)

def assistant_text(row):
    msgs = row.get('messages')
    if isinstance(msgs, str):
        try: msgs = json.loads(msgs)
        except Exception: msgs = None
    if isinstance(msgs, list):
        return '\n'.join(text_of(m.get('content')) for m in msgs if isinstance(m, dict) and m.get('role') == 'assistant')
    for k in ('response', 'generated_solution', 'targets', 'output', 'answer'):
        if row.get(k): return text_of(row[k])
    return ''

def user_text(row):
    msgs = row.get('messages')
    if isinstance(msgs, str):
        try: msgs = json.loads(msgs)
        except Exception: msgs = None
    if isinstance(msgs, list):
        return '\n'.join(text_of(m.get('content')) for m in msgs if isinstance(m, dict) and m.get('role') == 'user')
    for k in ('prompt', 'instruction', 'problem', 'inputs', 'question'):
        if row.get(k): return text_of(row[k])
    return ''

def score(a):
    hits = collections.Counter()
    for cat, pats in FRAME_RE.items():
        for p in pats:
            n = len(p.findall(a))
            if n: hits[cat] += n
    ident = any(p.search(a) for p in ID_RE)
    greek = any(p.search(a) for p in GR_RE)
    distinct_cats = len(hits)
    level = 3 if ident else (2 if distinct_cats >= 2 or sum(hits.values()) >= 3 else (1 if distinct_cats == 1 else 0))
    return level, dict(hits), ident, greek

SOURCES = [  # (label, hf id, config, split, bucket_fn, max_read)
 ('apertus_mixture', 'swiss-ai/apertus-sft-mixture', 'default', 'train', lambda r: r.get('dataset_source'), 120000),
 ('dolci', 'allenai/Dolci-Instruct-SFT', 'default', 'train', lambda r: r.get('domain'), 200000),
 ('tulu3', 'allenai/tulu-3-sft-mixture', 'default', 'train', lambda r: (r.get('source') or '').split('/')[-1][:40], 120000),
 ('smoltalk2_openhermes', 'HuggingFaceTB/smoltalk2', 'SFT', 'OpenHermes_2.5_no_think', lambda r: 'openhermes', PER),
 ('smoltalk2_magpie', 'HuggingFaceTB/smoltalk2', 'SFT', 'smoltalk_smollm3_smol_magpie_ultra_no_think', lambda r: 'magpie_ultra', PER),
 ('smoltalk2_systemchats', 'HuggingFaceTB/smoltalk2', 'SFT', 'smoltalk_smollm3_systemchats_30k_no_think', lambda r: 'systemchats', PER),
 ('smoltalk2_personas_if', 'HuggingFaceTB/smoltalk2', 'SFT', 'tulu_3_sft_personas_instruction_following_no_think', lambda r: 'personas_if', PER),
 ('smoltalk2_multilingual', 'HuggingFaceTB/smoltalk2', 'SFT', 'smoltalk_multilingual_8languages_lang_5_no_think', lambda r: 'multilingual8', PER),
 ('ifeval_like_filtered', 'argilla/ifeval-like-data', 'filtered', 'train', lambda r: 'ifeval_like', PER),
 ('nemotron_if_v3_if', 'nvidia/Nemotron-SFT-Instruction-Following-Chat-v3', 'default', 'instruction_following', lambda r: 'nemotron_if', PER),
 ('nemotron_if_v3_chat', 'nvidia/Nemotron-SFT-Instruction-Following-Chat-v3', 'default', 'chat', lambda r: 'nemotron_chat', PER),
 ('openmath2', 'nvidia/OpenMathInstruct-2', 'default', 'train', lambda r: 'openmath2', PER),
 ('orca_open_qa', 'microsoft/orca-agentinstruct-1M-v1', 'default', 'open_domain_qa', lambda r: 'orca_open_qa', PER),
 ('aya_greek', 'CohereLabs/aya_collection_language_split', 'greek', 'train', lambda r: 'aya_greek', PER),
]

results = {}; sample = []
for label, hf, cfg, split, bucket_fn, max_read in SOURCES:
    t0 = time.time(); per_bucket = collections.defaultdict(lambda: dict(n=0, l=[0,0,0,0], ident=0, greek=0, cats=collections.Counter(), words=0))
    kept = collections.Counter(); read = 0
    try:
        ds = load_dataset(hf, cfg, split=split, streaming=True)
        if label in ('apertus_mixture', 'dolci', 'tulu3'): ds = ds.shuffle(seed=7, buffer_size=20000)
        for row in ds:
            read += 1
            b = bucket_fn(row) or 'none'
            if kept[b] >= PER:
                if read >= max_read: break
                continue
            a = assistant_text(row)
            if not a.strip():
                continue
            lvl, hits, ident, greek = score(a)
            s = per_bucket[b]; s['n'] += 1; s['l'][lvl] += 1; s['ident'] += int(ident); s['greek'] += int(greek); s['words'] += len(a.split())
            for c, n in hits.items(): s['cats'][c] += n
            kept[b] += 1
            if lvl >= 1 and random.random() < 0.02 and len([x for x in sample if x['source'] == label]) < 40:
                sample.append(dict(source=label, bucket=b, level=lvl, hits=hits, user=user_text(row)[:1500], assistant=a[:2500]))
            elif lvl == 0 and random.random() < 0.004 and len([x for x in sample if x['source'] == label and x['level'] == 0]) < 10:
                sample.append(dict(source=label, bucket=b, level=0, hits={}, user=user_text(row)[:1500], assistant=a[:2500]))
            if read >= max_read: break
    except Exception as e:
        results[label] = {'error': str(e)[:300]}; print(label, 'ERROR', str(e)[:200], flush=True); continue
    out = {}
    for b, s in per_bucket.items():
        n = s['n'] or 1
        out[b] = dict(n=s['n'], share_l1=round(s['l'][1]/n, 3), share_l2=round(s['l'][2]/n, 3), share_l3=round(s['l'][3]/n, 3),
                      share_l2plus=round((s['l'][2]+s['l'][3])/n, 3), share_identity=round(s['ident']/n, 3), share_greek=round(s['greek']/n, 3),
                      markers_per_1k_words=round(1000*sum(s['cats'].values())/max(1, s['words']), 2), top_markers=s['cats'].most_common(5))
    results[label] = dict(hf=hf, config=cfg, split=split, rows_read=read, seconds=round(time.time()-t0), buckets=out)
    print(f"{label}: read {read} rows in {round(time.time()-t0)}s; buckets {[(b, v['n'], v['share_l2plus']) for b, v in out.items()]}", flush=True)
    json.dump(results, open(f'{OUT}/scan.json', 'w'), indent=1, ensure_ascii=False)
    with open(f'{OUT}/sample.jsonl', 'w') as f:
        for x in sample: f.write(json.dumps(x, ensure_ascii=False) + '\n')

# markdown table
lines = ['| source | bucket | rows | level 2+ | level 3 (identity) | any marker | markers per 1k words | Greek presence | top markers |', '|---|---|---|---|---|---|---|---|---|']
for label, r in results.items():
    if 'error' in r: lines.append(f'| {label} | error | | | | | | | {r["error"][:60]} |'); continue
    for b, v in sorted(r['buckets'].items(), key=lambda x: -x[1]['share_l2plus']):
        lines.append(f"| {label} | {b} | {v['n']} | {v['share_l2plus']:.1%} | {v['share_l3']:.1%} | {v['share_l1']+v['share_l2plus']:.1%} | {v['markers_per_1k_words']} | {v['share_greek']:.1%} | {', '.join(f'{c} {n}' for c, n in v['top_markers'][:3])} |")
open(f'{OUT}/scan.md', 'w').write('\n'.join(lines) + '\n')
print('DONE', flush=True)
