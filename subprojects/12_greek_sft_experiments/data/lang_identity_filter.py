#!/usr/bin/env python3
"""Two cheap filters for blocks the judges will not reach in time, or as a language gate on chat blocks:
 (1) language: keep rows whose first user turn is in English, Greek or an EU language (langdetect);
 (2) identity lexicon: drop rows whose assistant text carries an AI self-description in English or the main EU languages.
Writes <out_dir>/<block>.keep_ids.txt, .drop_lang_ids.txt, .drop_identity_ids.txt and a summary.
Usage: python3 lang_identity_filter.py <export.jsonl> <out_dir> <block> [--no-lang]"""
import json, sys, os, re, collections
IN, OUT, BLOCK = sys.argv[1], sys.argv[2], sys.argv[3]; NOLANG = '--no-lang' in sys.argv; os.makedirs(OUT, exist_ok=True)
KEEP_LANGS = {'en', 'el', 'ca', 'fr', 'de', 'it', 'es', 'pt', 'nl', 'sv', 'da', 'no', 'fi', 'pl', 'cs', 'sk', 'sl', 'hr', 'ro', 'hu', 'bg', 'lt', 'lv', 'et', 'ga', 'mt'}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from identity_patterns import IDENT
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
    sys_and_asst = '\n'.join((t.get('content') or '') for t in turns if t.get('role') in ('assistant', 'system'))
    if IDENT.search(sys_and_asst[:30000]): di.append(rid); c['drop_identity'] += 1; continue
    keep.append(rid); c['keep'] += 1
for name, lst in (('keep', keep), ('drop_lang', dl), ('drop_identity', di)):
    open(f'{OUT}/{BLOCK}.{name}_ids.txt', 'w').write('\n'.join(lst) + '\n')
summary = dict(block=BLOCK, counts=dict(c), languages=dict(langs.most_common(25)))
json.dump(summary, open(f'{OUT}/{BLOCK}.summary.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps(summary, ensure_ascii=False))
