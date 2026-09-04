#!/usr/bin/env python3
"""Vantage scan v2 for the three big mixtures: read K parquet shards spread evenly across the split (the streams are
source-ordered, so a streaming prefix covers only a few sources), sample rows per bucket, score with the same lexicon.
Usage: python3 vantage_scan_shards.py <out_dir> [rows_per_bucket] [shards_per_dataset]"""
import json, sys, os, time, random, collections
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'vantage_scan.py')).read()
exec(src[:src.index('SOURCES = [')])  # lexicon, text_of, assistant_text, user_text, score

OUT = sys.argv[1]; PER = int(sys.argv[2]) if len(sys.argv) > 2 else 3000; K = int(sys.argv[3]) if len(sys.argv) > 3 else 8
os.makedirs(OUT, exist_ok=True); random.seed(11)
api = HfApi()
DATASETS = [('apertus_mixture', 'swiss-ai/apertus-sft-mixture', 'dataset_source'), ('dolci', 'allenai/Dolci-Instruct-SFT', 'domain'), ('tulu3', 'allenai/tulu-3-sft-mixture', 'source')]
results = {}; sample = []
for label, repo, bucket_col in DATASETS:
    t0 = time.time()
    files = sorted(f for f in api.list_repo_files(repo, repo_type='dataset') if f.endswith('.parquet') and 'train' in f)
    pick = [files[int(i * (len(files) - 1) / max(1, K - 1))] for i in range(min(K, len(files)))] if files else []
    print(f'{label}: {len(files)} parquet files, reading {len(pick)}', flush=True)
    per_bucket = collections.defaultdict(lambda: dict(n=0, l=[0,0,0,0], ident=0, greek=0, cats=collections.Counter(), words=0)); kept = collections.Counter()
    for f in pick:
        try:
            path = hf_hub_download(repo, f, repo_type='dataset')
            pf = pq.ParquetFile(path)
            for rg in range(pf.num_row_groups):
                tbl = pf.read_row_group(rg); rows = tbl.to_pylist()
                random.shuffle(rows)
                for row in rows[:4000]:
                    b = row.get(bucket_col) or 'none'
                    if label == 'tulu3': b = str(b).split('/')[-1][:40]
                    if kept[b] >= PER: continue
                    a = assistant_text(row)
                    if not a.strip(): continue
                    lvl, hits, ident, greek = score(a)
                    s = per_bucket[b]; s['n'] += 1; s['l'][lvl] += 1; s['ident'] += int(ident); s['greek'] += int(greek); s['words'] += len(a.split())
                    for c, n in hits.items(): s['cats'][c] += n
                    kept[b] += 1
                    if lvl >= 1 and random.random() < 0.03 and sum(1 for x in sample if x['source'] == label and x['bucket'] == b) < 12:
                        sample.append(dict(source=label, bucket=b, level=lvl, hits=hits, user=user_text(row)[:1500], assistant=a[:2500]))
                    elif lvl == 0 and random.random() < 0.005 and sum(1 for x in sample if x['source'] == label and x['level'] == 0) < 15:
                        sample.append(dict(source=label, bucket=b, level=0, hits={}, user=user_text(row)[:1500], assistant=a[:2500]))
            print(f'  {label}: {f} done; kept {sum(kept.values())} over {len(kept)} buckets', flush=True)
        except Exception as e:
            print(f'  {label}: {f} ERROR {str(e)[:160]}', flush=True)
    out = {}
    for b, s in per_bucket.items():
        n = s['n'] or 1
        out[b] = dict(n=s['n'], share_l1=round(s['l'][1]/n, 3), share_l2=round(s['l'][2]/n, 3), share_l3=round(s['l'][3]/n, 3), share_l2plus=round((s['l'][2]+s['l'][3])/n, 3),
                      share_identity=round(s['ident']/n, 3), share_greek=round(s['greek']/n, 3), markers_per_1k_words=round(1000*sum(s['cats'].values())/max(1, s['words']), 2), top_markers=s['cats'].most_common(5))
    results[label] = dict(hf=repo, shards=pick, seconds=round(time.time()-t0), buckets=out)
    print(f'{label}: {round(time.time()-t0)}s; ' + '; '.join(f"{b} n={v['n']} l2+={v['share_l2plus']}" for b, v in sorted(out.items(), key=lambda x: -x[1]['share_l2plus'])), flush=True)
    json.dump(results, open(f'{OUT}/scan_shards.json', 'w'), indent=1, ensure_ascii=False)
    with open(f'{OUT}/sample_shards.jsonl', 'w') as fh:
        for x in sample: fh.write(json.dumps(x, ensure_ascii=False) + '\n')
lines = ['| source | bucket | rows | level 2+ | identity | any marker | markers per 1k words | Greek presence | top markers |', '|---|---|---|---|---|---|---|---|---|']
for label, r in results.items():
    for b, v in sorted(r['buckets'].items(), key=lambda x: -x[1]['share_l2plus']):
        lines.append(f"| {label} | {b} | {v['n']} | {v['share_l2plus']:.1%} | {v['share_l3']:.1%} | {v['share_l1']+v['share_l2plus']:.1%} | {v['markers_per_1k_words']} | {v['share_greek']:.1%} | {', '.join(f'{c} {n}' for c, n in v['top_markers'][:3])} |")
open(f'{OUT}/scan_shards.md', 'w').write('\n'.join(lines) + '\n'); print('DONE', flush=True)
