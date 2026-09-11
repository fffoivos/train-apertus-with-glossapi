# Measures the language of every block in data/arms/R3_single/train.jsonl (unique rows): Greek-script share of the user and assistant text on every row, langdetect on a sample of up to 1,500 Latin-script assistant texts per block. Run with ~/Projects/apertus-local-chat/.venv/bin/python (langdetect). Output: docs/receipts_R3_single/language_by_block.json
import json, collections, re, random, sys
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0
random.seed(0)
GREEK = re.compile(r'[Ͱ-Ͽἀ-῿]')
LATIN = re.compile(r'[A-Za-z]')
CYR = re.compile(r'[Ѐ-ӿ]')
def script_of(text):
    g=len(GREEK.findall(text)); l=len(LATIN.findall(text)); c=len(CYR.findall(text))
    tot=g+l+c
    if tot < 20: return 'short'
    if g/tot >= 0.5: return 'el'
    if c/tot >= 0.5: return 'cyrillic'
    return 'latin'
seen=set()
per=collections.defaultdict(lambda: {'unique':0,'user':collections.Counter(),'asst':collections.Counter(),'latin_sample':[], 'idprefix':collections.Counter()})
with open('data/arms/R3_single/train.jsonl') as f:
    for line in f:
        r=json.loads(line); b=r['config']; rid=r['id']
        key=(b, rid.split('#')[0] if '#' in rid else rid)
        if key in seen: continue
        seen.add(key)
        d=per[b]; d['unique']+=1
        d['idprefix'][re.split(r'[_\-:/]', rid)[0][:16]]+=1
        u=' '.join(m['content'] for m in r['messages'] if m['role']=='user')
        a=' '.join(m['content'] for m in r['messages'] if m['role']=='assistant')
        su=script_of(u); sa=script_of(a)
        d['user'][su]+=1; d['asst'][sa]+=1
        if sa=='latin': d['latin_sample'].append(a[:1500])
out={}
for b,d in per.items():
    samp=d['latin_sample']
    if len(samp)>1500: samp=random.sample(samp,1500)
    ld=collections.Counter()
    for t in samp:
        try: ld[detect(t)]+=1
        except Exception: ld['?']+=1
    out[b]={'unique_rows':d['unique'],'user_script':dict(d['user']),'assistant_script':dict(d['asst']),
            'latin_langdetect_sample':{'n':len(samp),'dist':dict(ld.most_common(12))},
            'id_prefixes':dict(d['idprefix'].most_common(15))}
    print(b, out[b], flush=True)
json.dump(out, open('docs/receipts_R3_single/language_by_block.json','w'), ensure_ascii=False, indent=1)
print('DONE')


# ===== MODE 2 (run as: python data/language_by_block.py spans) =====
import sys as _s
if len(_s.argv) > 1 and _s.argv[1] == "spans":
    exec(open(__file__).read().split("# ===== MODE 2 SOURCE =====\n",1)[1])
    raise SystemExit
# ===== MODE 2 SOURCE =====
# ---- second mode: language over supervised spans (letters, effective rows) ----
# Language over SUPERVISED spans (assistant turns with train != false) of data/arms/R3_single/train.jsonl, EFFECTIVE rows (copies counted),
# character-weighted (letters only), per block and overall; categories: el (>=90% Greek letters), latin (>=90% Latin), mixed (neither), unknown (<20 letters).
import json, re, collections
GREEK = re.compile(r'[Ͱ-Ͽἀ-῿]'); LATIN = re.compile(r'[A-Za-z]'); CYR = re.compile(r'[Ѐ-ӿ]')
def cat(text):
    g=len(GREEK.findall(text)); l=len(LATIN.findall(text)); c=len(CYR.findall(text)); tot=g+l+c
    if tot < 20: return 'unknown', tot
    if g/tot >= 0.9: return 'el', tot
    if l/tot >= 0.9: return 'latin', tot
    if c/tot >= 0.9: return 'cyrillic', tot
    return 'mixed', tot
chars=collections.defaultdict(collections.Counter); spans=collections.defaultdict(collections.Counter)
with open('data/arms/R3_single/train.jsonl') as f:
    for line in f:
        r=json.loads(line); b=r['config']
        for m in r['messages']:
            if m['role']!='assistant' or m.get('train') is False: continue
            k,n=cat(m['content']); chars[b][k]+=n; spans[b][k]+=1
out={}
tot=collections.Counter(); tots=collections.Counter()
for b in sorted(chars):
    c=chars[b]; n=sum(c.values()); out[b]={'supervised_letters':n,'share_by_letters':{k:round(v/n,4) for k,v in c.items()},'spans':dict(spans[b])}
    tot.update(c); tots.update(spans[b])
    print(f"{b:24s} letters {n/1e6:7.2f}M  " + '  '.join(f"{k} {v/n*100:5.1f}%" for k,v in sorted(c.items(), key=lambda x:-x[1])), flush=True)
n=sum(tot.values()); out['_ALL_effective']={'supervised_letters':n,'share_by_letters':{k:round(v/n,4) for k,v in tot.items()},'spans':dict(tots)}
print('ALL (effective rows, supervised spans, letters):', {k:f"{v/n*100:.1f}%" for k,v in tot.items()}, 'spans', dict(tots))
json.dump(out, open('docs/receipts_R3_single/language_supervised_spans.json','w'), ensure_ascii=False, indent=1); print('DONE')
