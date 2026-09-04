#!/usr/bin/env python3
"""Two cheap filters for blocks the judges will not reach in time, or as a language gate on chat blocks:
 (1) language: keep rows whose first user turn is in English, Greek or an EU language (langdetect);
 (2) identity lexicon: drop rows whose assistant text carries an AI self-description in English or the main EU languages.
Writes <out_dir>/<block>.keep_ids.txt, .drop_lang_ids.txt, .drop_identity_ids.txt and a summary.
Usage: python3 lang_identity_filter.py <export.jsonl> <out_dir> <block> [--no-lang]"""
import json, sys, os, re, collections
IN, OUT, BLOCK = sys.argv[1], sys.argv[2], sys.argv[3]; NOLANG = '--no-lang' in sys.argv; os.makedirs(OUT, exist_ok=True)
KEEP_LANGS = {'en', 'el', 'fr', 'de', 'it', 'es', 'pt', 'nl', 'sv', 'da', 'no', 'fi', 'pl', 'cs', 'sk', 'sl', 'hr', 'ro', 'hu', 'bg', 'lt', 'lv', 'et', 'ga', 'mt'}
IDENT = re.compile(r"\b(as an? (ai|artificial intelligence|language model|large language model|llm|virtual assistant|ai assistant|ai language model)|i am an? (ai|artificial intelligence|language model|llm|ai assistant)|i'm an? (ai|artificial intelligence|language model|llm)|my (training|knowledge) (data|cutoff)|knowledge cutoff|i (do not|don't) have (access to )?real[- ]time|developed by (openai|anthropic|google|meta|ai2|allen institute|mistral|nvidia|zhipu|z\.ai)|(chatgpt|gpt-4|gpt-3|claude|gemini|llama|olmo|glm-5|qwen)\b.{0,40}\b(i am|i'm|my name)|"
                   r"en tant qu'?(ia|intelligence artificielle|modèle de langage|assistant ia)|je suis un(e)? (ia|intelligence artificielle|modèle de langage)|"
                   r"als (ki|künstliche intelligenz|sprachmodell|ki-assistent)|ich bin (eine? )?(ki|künstliche intelligenz|sprachmodell)|"
                   r"come (ia|intelligenza artificiale|modello linguistico)|sono un(a)? (ia|intelligenza artificiale|modello linguistico)|"
                   r"como (ia|inteligencia artificial|modelo de lenguaje|modelo de linguagem)|soy un(a)? (ia|inteligencia artificial|modelo de lenguaje)|sou um(a)? (ia|inteligência artificial|modelo de linguagem)|"
                   r"ως (τεχνητή νοημοσύνη|γλωσσικό μοντέλο|μοντέλο τεχνητής)|είμαι (ένα |μια )?(τεχνητή νοημοσύνη|γλωσσικό μοντέλο))", re.I)
det = None
if not NOLANG:
    try:
        from langdetect import detect, DetectorFactory; DetectorFactory.seed = 0; det = detect
    except Exception as e: print('langdetect unavailable, language gate skipped:', e)
def first_user(turns):
    for t in turns:
        if t.get('role') == 'user' and (t.get('content') or '').strip(): return t['content']
    return ''
def assistant_text(turns): return '\n'.join((t.get('content') or '') for t in turns if t.get('role') == 'assistant')
c = collections.Counter(); langs = collections.Counter(); keep, dl, di = [], [], []
for line in open(IN):
    r = json.loads(line); rid = str(r.get('id', r.get('_row', ''))); turns = r.get('turns') or [dict(role='user', content=r.get('user', '')), dict(role='assistant', content=r.get('assistant', ''))]
    c['rows'] += 1
    if det is not None:
        u = first_user(turns)[:1500]
        try: lang = det(u) if len(u.strip()) >= 20 else 'unk'
        except Exception: lang = 'unk'
        langs[lang] += 1
        if lang != 'unk' and lang not in KEEP_LANGS: dl.append(rid); c['drop_lang'] += 1; continue
    if IDENT.search(assistant_text(turns)[:20000]): di.append(rid); c['drop_identity'] += 1; continue
    keep.append(rid); c['keep'] += 1
for name, lst in (('keep', keep), ('drop_lang', dl), ('drop_identity', di)):
    open(f'{OUT}/{BLOCK}.{name}_ids.txt', 'w').write('\n'.join(lst) + '\n')
summary = dict(block=BLOCK, counts=dict(c), languages=dict(langs.most_common(25)))
json.dump(summary, open(f'{OUT}/{BLOCK}.summary.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps(summary, ensure_ascii=False))
