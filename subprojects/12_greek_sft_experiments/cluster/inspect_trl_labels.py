#!/usr/bin/env python3
"""TRAINING-path label AUDIT (astra gate-2 v6 M4, v7 H2): build the REAL SFTTrainer (the trainer's own SFTConfig kwargs, tokenizer and patched template;
random stand-in model) on selected manifest rows (+ a synthetic conversation with emoji-ending assistant turns), then iterate EVERY train batch and every
eval batch, split each collated sequence at packing boundaries (position_ids resets; attention mask for padded eval batches), match every segment to a
source row by its exact token ids, and compare the collator's labels token by token with the validator's tokenize_messages labels. Requirements for OK:
every row matched exactly once, no unmatched segment, zero deficit (validator-supervised but collator-masked), zero extra (collator-supervised but
validator-masked), supervised label values equal to the token ids. Exit 1 on any failure. --expect-deficit (negative control for a known-defective path):
exit 0 ONLY with complete coverage AND a positive training deficit AND zero extra supervision AND zero wrong label values; a clean run FAILS in this mode. Run on the cluster in the sft5 env:
python cluster/inspect_trl_labels.py --config cluster/configs/R4_full.yaml --train data/arms/R4_full/train.jsonl [--ids a,b,c] [--trainer sft_train] [--expect-deficit]"""
import argparse, json, sys, os, tempfile, importlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--train', required=True); ap.add_argument('--trainer', default='sft_train'); ap.add_argument('--ids', default=''); ap.add_argument('--expect-deficit', action='store_true'); a = ap.parse_args()
T = importlib.import_module(a.trainer)
from trl import SFTConfig
config = dict(T.load_config(a.config)); config.update(random_standin=True, out_dir=tempfile.mkdtemp(prefix='trl_audit_'), run_name='trl_audit', max_steps=-1, world_size=1, limit=None)
tok = T.prepare_tokenizer(config); tok = tok[0] if isinstance(tok, tuple) else tok
pretok = bool(config.get('pretokenized_masks', False))
if a.ids:
    want_ids = set(a.ids.split(',')); picked = {}
    for l in open(a.train):
        r = json.loads(l)
        if r['id'] in want_ids: picked[r['id']] = r
        if len(picked) == len(want_ids): break
    rows = list(picked.values()); missing_req = sorted(want_ids - set(picked)); print('IDS MODE:', len(rows), 'rows found of', len(want_ids), '| cohort sha256', __import__('hashlib').sha256(a.ids.encode()).hexdigest()[:16], '| train file sha256', __import__('hashlib').sha256(open(a.train, 'rb').read()).hexdigest()[:16])
    if missing_req: print('MISSING REQUESTED IDS:', missing_req); print('TRL_LABELS_CHECK FAIL: requested cohort incomplete'); sys.exit(1)
else:
    want = {'greek_math_v2': lambda r: True, 'format_mc': lambda r: sum(1 for m in r['messages'] if m['role'] == 'assistant') >= 3, 'convskills_v2': lambda r: sum(1 for m in r['messages'] if m['role'] == 'assistant') >= 2}
    picked = {}
    for l in open(a.train):
        r = json.loads(l); c = r['config']
        if c in want and c not in picked and want[c](r): picked[c] = r
        if len(picked) == len(want): break
    rows = list(picked.values()) + [dict(config='synthetic_emoji', id='synthetic_emoji', messages=[dict(role='user', content='Πες μου κάτι ευχάριστο.'), dict(role='assistant', content='Σήμερα έχει ήλιο 😊'), dict(role='user', content='Και κάτι ακόμη;'), dict(role='assistant', content='Αύριο θα έχει ακόμη περισσότερο ☀️🎉')])]
kw = T._sft_kwargs(config); kw['report_to'] = 'none'
try: args = SFTConfig(**kw)
except Exception as e:
    dropped = [k for k in ('bf16', 'fp16', 'tf32') if k in kw]; [kw.pop(k) for k in dropped]; print('SFTConfig retry without', dropped, 'because:', str(e)[:120]); args = SFTConfig(**kw)
print('TRAINER MODULE:', T.__name__, '| pretokenized_masks:', pretok, '| assistant_only_loss (effective SFTConfig):', kw.get('assistant_only_loss'), '| packing:', kw.get('packing'), kw.get('packing_strategy'), '| max_length:', kw.get('max_length'), '| per_device_train_batch_size:', kw.get('per_device_train_batch_size'))
model = T._load_model(config, tok)
trainer = T.EpochNamedSFTTrainer(model=model, args=args, train_dataset=(T._dataset(rows, tok) if pretok else T._dataset(rows)), eval_dataset=(T._eval_datasets_pretok(rows, tok) if pretok else T._eval_datasets(rows)), processing_class=tok)
print('TRAINING DATASET COLUMNS:', trainer.train_dataset.column_names, '| prepared examples:', len(trainer.train_dataset))
expected = {}
for r in rows:
    t = T.tokenize_messages(tok, r['messages']); expected[tuple(t['input_ids'])] = (r['id'], t['labels'])
def segments(batch):
    ids, labels = batch['input_ids'], batch['labels']
    for j in range(ids.shape[0]):
        row_ids, row_lab = ids[j].tolist(), labels[j].tolist()
        if 'position_ids' in batch:
            pos = batch['position_ids'][j].tolist(); starts = [k for k, p in enumerate(pos) if p == 0] + [len(pos)]
            for s, e in zip(starts, starts[1:]): yield row_ids[s:e], row_lab[s:e]
        elif 'attention_mask' in batch:
            keep = [k for k, x in enumerate(batch['attention_mask'][j].tolist()) if x]; yield [row_ids[k] for k in keep], [row_lab[k] for k in keep]
        else: yield row_ids, row_lab
def audit(loader, name, expect_rows=None):
    expect_rows = rows if expect_rows is None else expect_rows
    seen = collections.Counter(); deficit = extra = wrongval = unmatched = n_seg = n_batch = sup_col = sup_val = 0; ex_def = []
    for batch in loader:
        n_batch += 1
        for seg_ids, seg_lab in segments(batch):
            n_seg += 1; key = tuple(seg_ids)
            if key not in expected: unmatched += 1; continue
            rid, vlab = expected[key]; seen[rid] += 1
            for k, (c, v) in enumerate(zip(seg_lab, vlab)):
                cs, vs = c != -100, v != -100; sup_col += cs; sup_val += vs
                if vs and not cs:
                    deficit += 1
                    if len(ex_def) < 3: ex_def.append((rid, tok.decode(seg_ids[max(0, k - 6):k + 1])))
                if cs and not vs: extra += 1
                if cs and c != seg_ids[k]: wrongval += 1
    missing = [r['id'] for r in expect_rows if seen[r['id']] == 0]; dup = [i for i, n in seen.items() if n > 1]; unexpected = [i for i in seen if i not in {r['id'] for r in expect_rows}]
    coverage = not unmatched and not missing and not dup and not unexpected
    ok = coverage and deficit == 0 and extra == 0 and wrongval == 0
    print(f'{name}_AUDIT batches {n_batch} segments {n_seg} matched_rows {len(seen)}/{len(expect_rows)} unmatched_segments {unmatched} duplicate_rows {len(dup)} missing_rows {len(missing)} collator_supervised {sup_col} validator_supervised {sup_val} deficit {deficit} extra {extra} wrong_label_values {wrongval}' + (f' | first deficit sites: {ex_def}' if ex_def else ''))
    return ok, coverage, deficit, sup_col, sup_val, extra, wrongval
ok_tr, cov_tr, def_tr, sc, sv, ex_tr, wv_tr = audit(trainer.get_train_dataloader(), 'TRAIN')
ok_ev, cov_ev, def_ev, ex_ev, wv_ev = True, True, 0, 0, 0
for name, ds in trainer.eval_dataset.items():
    o, c, d, _, _, e, w = audit(trainer.get_eval_dataloader(ds), f'EVAL[{name}]', [r for r in rows if str(r.get('config', 'all')) == name]); ok_ev &= o; cov_ev &= c; def_ev += d; ex_ev += e; wv_ev += w   # eval datasets are per config
if a.expect_deficit:   # deficit mode is decided FIRST: a clean run is a FAILURE of the negative control (astra v9 H2)
    if cov_tr and cov_ev and def_tr > 0 and ex_tr == 0 and wv_tr == 0 and ex_ev == 0 and wv_ev == 0: print(f'TRL_LABELS_CHECK DEFICIT (expected for the audited path): train deficit {def_tr} of {sv} validator-supervised tokens ({100 * def_tr / max(1, sv):.1f}%), eval deficit {def_ev}; coverage complete; no extra supervision, no wrong label values'); sys.exit(0)
    print(f'TRL_LABELS_CHECK FAIL (deficit mode): coverage {cov_tr and cov_ev}, train deficit {def_tr}, extra {ex_tr + ex_ev}, wrong values {wv_tr + wv_ev}'); sys.exit(1)
if ok_tr and ok_ev: print(f'TRL_LABELS_CHECK OK: every batch audited; {len(rows)} rows matched once; collator labels equal the validator labels token by token (train {sc} supervised tokens; eval deficit 0)'); sys.exit(0)
print('TRL_LABELS_CHECK FAIL'); sys.exit(1)
