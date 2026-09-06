#!/usr/bin/env python3
"""One seeded run of the v2 pipeline into a run directory (resumable stage by stage).
Usage: python3 run_pipeline.py <run_dir> <sheet_v2.json> <identity_facts.json> <fact_ids|all> <seed> [per_fact=6] [writer=claude-opus-5] [gate=claude-sonnet-5] [editor=claude-sonnet-5]"""
import subprocess, sys, os
D, SHEET, IDENT, IDS, SEED = sys.argv[1:6]; PER = sys.argv[6] if len(sys.argv) > 6 else '6'; W = sys.argv[7] if len(sys.argv) > 7 else 'claude-opus-5'; G = sys.argv[8] if len(sys.argv) > 8 else 'claude-sonnet-5'; E = sys.argv[9] if len(sys.argv) > 9 else 'claude-sonnet-5'
H = os.path.dirname(os.path.abspath(__file__)); os.makedirs(D, exist_ok=True)
def stage(name, cmd, marker):
    if os.path.exists(marker) and open(marker).read().strip() == 'done': print(f'{name}: done earlier', flush=True); return
    print(f'== {name}', flush=True); r = subprocess.run(cmd); 
    if r.returncode != 0: raise SystemExit(f'{name} failed')
    open(marker, 'w').write('done')
stage('questions', ['python3', f'{H}/gen_questions.py', SHEET, f'{D}/questions.jsonl', IDS, SEED, PER, W], f'{D}/.q')
stage('gate', ['python3', f'{H}/gate_questions.py', f'{D}/questions.jsonl', f'{D}/questions_gated.jsonl', G], f'{D}/.g')
stage('answers', ['python3', f'{H}/gen_answers.py', f'{D}/questions_gated.jsonl', SHEET, IDENT, f'{D}/rows.jsonl', W], f'{D}/.a')
stage('correct', ['python3', f'{H}/correct_rows.py', f'{D}/rows.jsonl', SHEET, f'{D}/checks.jsonl', f'{D}/rows_corrected.jsonl', E], f'{D}/.c')
subprocess.run(['python3', f'{H}/scans.py', D]); print('RUN DONE', flush=True)
