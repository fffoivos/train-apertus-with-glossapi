#!/usr/bin/env python3
"""Greek IFEval / MGSM table: ours + peers, Krikri-card strict average. Reads results/<label>/ilsp/**/results*.json."""
import json,glob
ROWS=[('Llama-Krikri-8B-Instruct (ILSP card: 67.5%)','peer_krikri'),('Apertus-8B-Instruct-2509 (no Greek CPT)','peer_apertus_instruct'),
 ('Gemma-3-12B-it (50% larger)','peer_gemma3_12b'),('Meltemi-7B-Instruct-v1.5 (ILSP card: 32.7%)','peer_meltemi'),
 ('ours: lr 1e-5, epoch 3','E1_lr1e-5_ep3'),('ours: adapted imports, epoch 2','E3_cos_ep2'),('ours: lr 5e-6, epoch 3','E1_lr5e-6_ep3'),
 ('ours: the pick, lr 1e-5, epoch 2','E1_lr1e-5_ep2'),('ours: paired English, epoch 2','E2_cos_ep2'),('ours: raw imports, epoch 2','E3prime_cos_ep2'),
 ('ours: from the terminal CPT checkpoint','E1last_ep2')]
out=["| model | IFEval prompt-strict | IFEval inst-strict | IFEval strict avg | Greek MGSM |","|---|---|---|---|---|"]
for name,lab in ROWS:
    fs=sorted(glob.glob(f'results/{lab}/ilsp/**/results*.json',recursive=True))
    if not fs: out.append(f"| {name} | (not run) | | | |"); continue
    d=json.load(open(fs[-1]))['results']; i=d['ifeval_greek']; p=i['prompt_level_strict_acc,none']; s=i['inst_level_strict_acc,none']; m=d['mgsm_greek']['exact_match,none']
    out.append(f"| {name} | {p:.3f} | {s:.3f} | **{(p+s)/2*100:.1f}%** | {m:.3f} |")
print("\n".join(out)); open('results/peer_table.md','w').write("\n".join(out)+"\n")
