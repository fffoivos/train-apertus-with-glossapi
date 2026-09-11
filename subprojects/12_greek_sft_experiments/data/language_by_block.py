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
