#!/usr/bin/env bash
# Make an evaluation-compatible copy of a transformers-5 SFT checkpoint: weights symlinked, but config.json,
# generation_config.json and the tokenizer files taken from the BASE model (transformers-4 style: top-level rope_theta,
# tokenizer_class the frozen scorers and lm_eval 0.4.11 can load; tokenizer.json byte-identical to the base so the native
# suite's contract sha matches) plus the Apertus-Instruct chat template. Runs on the login node.
# Usage: make_eval_copy.sh <ckpt_dir> <dst_dir> [base_snapshot_dir]
set -euo pipefail
CK=$1; DST=$2; S=/iopsstor/scratch/cscs/fffoivos
B=${3:-$(ls -d $S/sft_round1/hf_home/hub/models--fffoivos--apertus-8b-greek-cpt/snapshots/c7f806e*)}
I=$(ls -d $S/sft_round1/hf_home/hub/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/*)
mkdir -p "$DST"
for f in "$CK"/*.safetensors "$CK"/model.safetensors.index.json; do [ -e "$f" ] && ln -sf "$f" "$DST/$(basename "$f")"; done
cp "$B/config.json" "$B/generation_config.json" "$B/tokenizer.json" "$B/special_tokens_map.json" "$DST/"
python3 - "$B" "$I" "$DST" <<'PY'
import json, sys
b, i, d = sys.argv[1:4]
cfg = json.load(open(f'{b}/tokenizer_config.json')); cfg['chat_template'] = open(f'{i}/chat_template.jinja').read()
json.dump(cfg, open(f'{d}/tokenizer_config.json', 'w'), indent=1, ensure_ascii=False)
g = json.load(open(f'{d}/generation_config.json')); g['eos_token_id'] = [2, 68]; json.dump(g, open(f'{d}/generation_config.json', 'w'), indent=1)
c = json.load(open(f'{d}/config.json'))
rp = c.get('rope_parameters') or c.get('rope_scaling') or {}
if 'rope_theta' not in c and isinstance(rp, dict) and 'rope_theta' in rp:
    c['rope_theta'] = rp['rope_theta']; json.dump(c, open(f'{d}/config.json', 'w'), indent=1)   # frozen scorers read the top-level key
print('eval copy:', d, '| rope_theta' in c and 'rope_theta' or 'NO rope_theta', '| vocab', c.get('vocab_size'), '| tie', c.get('tie_word_embeddings'))
PY
ls -la "$DST" | grep -E 'safetensors|config|tokenizer' | awk '{print $NF}' | tr '\n' ' '; echo
