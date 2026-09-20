#!/usr/bin/env python
"""Stage the Greek Apertus SFT datasets (hardlinks, no copies) and upload them to the gated HF dataset repo fffoivos/greek-apertus-sft.
Run with the apertus-local-chat venv python (has huggingface_hub + the token). Usage: python upload_sft.py [stage|upload|all]"""
import json, os, sys, time
R = os.path.expanduser('~/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments')
S = os.path.expanduser('~/sft_annot/hf_stage/greek-apertus-sft')
REPO = 'fffoivos/greek-apertus-sft'
def link(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst): os.remove(dst)
    os.link(src, dst)
def stage():
    link(f'{R}/data/arms/R2_stage1/train.jsonl', f'{S}/round2_stage1/train.jsonl')
    link(f'{R}/data/arms/R2_stage1/dev.jsonl', f'{S}/round2_stage1/dev.jsonl')
    os.makedirs(f'{S}/receipts', exist_ok=True)
    for src, dst in [(f'{R}/data/arms/R2_stage1/receipt.json', f'{S}/receipts/round2_stage1_receipt.json'), (f'{R}/docs/receipts/receipts_R2_stage1_final_20260906.json', f'{S}/receipts/receipts_R2_stage1_final_20260906.json')]:
        open(dst, 'w').write(open(src).read())
    for a in ['E1', 'E2', 'E3', 'E3prime']:
        link(f'{R}/data/arms/{a}/train.jsonl', f'{S}/round1_arms/{a}_train.jsonl'); link(f'{R}/data/arms/{a}/dev.jsonl', f'{S}/round1_arms/{a}_dev.jsonl')
    os.makedirs(f'{S}/personality_v3', exist_ok=True); n = 0
    with open(f'{S}/personality_v3/train.jsonl', 'w') as f:
        for l in open(f'{R}/data/personality/v3/full_20260906/edited.jsonl'):
            r = json.loads(l); f.write(json.dumps(dict(id=r['id'], category=r['category'], messages=r['messages']), ensure_ascii=False) + '\n'); n += 1
    print('personality rows', n, flush=True)
    for root, _, files in os.walk(S):
        for fn in sorted(files):
            p = os.path.join(root, fn); print(f'{os.path.getsize(p)/1e6:8.1f} MB  {os.path.relpath(p, S)}', flush=True)
def upload():
    from huggingface_hub import HfApi
    a = HfApi(); a.create_repo(REPO, repo_type='dataset', private=False, exist_ok=True)
    try: a.update_repo_settings(repo_id=REPO, repo_type='dataset', gated='manual'); print('gated: manual', flush=True)
    except Exception as e: print('gating:', e, flush=True)
    t = time.time()
    a.upload_folder(folder_path=S, repo_id=REPO, repo_type='dataset', ignore_patterns=['upload.log', '*.py'], commit_message='Greek Apertus SFT datasets: round-2 stage-1 arm, round-1 arms, personality set v3, receipts')
    print(f'UPLOAD DONE in {int(time.time() - t)}s', flush=True)
mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
if mode in ('stage', 'all'): stage()
if mode in ('upload', 'all'): upload()
