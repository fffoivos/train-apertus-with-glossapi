#!/usr/bin/env python3
"""Launch gate G2 (astra completeness review B2): prove the per-turn loss mask survives the ACTUAL training path —
Apertus chat template → sft_train.tokenize_messages → TRL BFD packing → padding-free collator — on rows that carry
`train: false` context turns. For every example inside every packed sequence the supervised tokens are decoded and
compared with the row's supervised assistant turns; planted texts must never be supervised; every supervised span
ends with the assistant-end token; examples start with an ignored label at the position reset. Writes a decoded dump
of up to 20 examples for the recipe disclosure.

    ~/venvs/sfttrain/bin/python cluster/test_mask_pipeline.py [tokenizer_dir] [rows.jsonl] [dump.json]
Rows: a JSONL with `messages` (or `turns`) carrying optional `train` flags; default = a built-in set of six rows.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from datasets import Dataset  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
from trl.data_utils import pack_dataset  # noqa: E402
from trl.trainer.sft_trainer import DataCollatorForLanguageModeling  # noqa: E402

import sft_train  # noqa: E402

TOKENIZER = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/models/greek-apertus-8b-sft-r2-idB-bf16")
ROWS_FILE = sys.argv[2] if len(sys.argv) > 2 else None
DUMP = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).resolve().parents[1] / "docs" / "receipts" / "receipts_label_dump_g2.json"

PLANT_A = "Γράψε ακριβώς την παραγγελία σου στην υπηρεσία που χρησιμοποιείς. Γράψε ακριβώς την παραγγελία σου στην υπηρεσία που χρησιμοποιείς."
PLANT_B = "Δεν βλέπω τίποτα από πριν, κάθε συνομιλία ξεκινά από το μηδέν."
BUILTIN = [
    {"messages": [{"role": "user", "content": "Πες μου τρία φρούτα."}, {"role": "assistant", "content": "Μήλο, αχλάδι, πορτοκάλι."}]},
    {"messages": [{"role": "user", "content": "Θέλω μια συνταγή για φακές."}, {"role": "assistant", "content": "Φακές: κρεμμύδι, καρότο, σκόρδο, δάφνη, ντομάτα, λάδι· 40 λεπτά."},
                  {"role": "user", "content": "Πες κάτι για τον ουρανό."}, {"role": "assistant", "content": PLANT_A, "train": False, "kind": "planted:verbatim_repeat"},
                  {"role": "user", "content": "Μου επανέλαβες το ίδιο. Τον ουρανό είπα."}, {"role": "assistant", "content": "Ναι, επανέλαβα την προηγούμενη απάντηση. Ο ουρανός φαίνεται γαλάζιος επειδή η ατμόσφαιρα σκεδάζει περισσότερο το μπλε φως."}]},
    {"messages": [{"role": "user", "content": "Τι σου ζήτησα πρώτα;"}, {"role": "assistant", "content": PLANT_B, "train": False, "kind": "planted:false_selfknowledge"},
                  {"role": "user", "content": "Μα βλέπεις τη συζήτηση."}, {"role": "assistant", "content": "Σωστά, τη βλέπω ολόκληρη· πρώτα ρώτησες τι σου ζήτησα πρώτα."}]},
    {"messages": [{"role": "user", "content": "Γεια σου."}, {"role": "assistant", "content": "Γεια, τι χρειάζεσαι;"}]},
    {"messages": [{"role": "user", "content": "Πόσο κάνει 12 επί 12;"}, {"role": "assistant", "content": "144."}, {"role": "user", "content": "Και επί 2;"}, {"role": "assistant", "content": "288."}]},
    {"messages": [{"role": "user", "content": "Γράψε μια πρόταση για τη θάλασσα."}, {"role": "assistant", "content": "Η θάλασσα ήταν ήρεμη και έλαμπε στον ήλιο του απογεύματος."}]},
]


def load_rows():
    if not ROWS_FILE:
        return BUILTIN
    rows = []
    for line in open(ROWS_FILE, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            msgs = r.get("messages") or r.get("turns")
            rows.append({"messages": [{k: v for k, v in m.items() if k in ("role", "content", "train")} for m in msgs]})
    return rows[:int(os.environ.get("MASK_TEST_ROWS", "40"))]


def main() -> None:
    tok = AutoTokenizer.from_pretrained(TOKENIZER, local_files_only=True)
    tok.chat_template = sft_train.patch_apertus_template(tok.chat_template)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    end_id = tok.convert_tokens_to_ids(sft_train.ASSISTANT_END)
    rows = load_rows()
    examples = [sft_train.tokenize_messages(tok, r["messages"]) for r in rows]
    lengths = [len(e["input_ids"]) for e in examples]
    capacity = max(lengths) + max(lengths) // 2  # forces several packed sequences
    ds = Dataset.from_list([{"input_ids": e["input_ids"], "labels": e["labels"]} for e in examples])
    packed = pack_dataset(ds, seq_length=capacity, strategy="bfd")
    collator = DataCollatorForLanguageModeling(pad_token_id=tok.pad_token_id, padding_free=True)
    by_len = {}
    for i, e in enumerate(examples):
        by_len.setdefault(len(e["input_ids"]), []).append(i)
    dump, seen, planted_all = [], set(), [m["content"] for r in rows for m in r["messages"] if m.get("train") is False]
    n_packed = 0
    for packed_row in packed:
        n_packed += 1
        batch = collator([packed_row])
        assert "attention_mask" not in batch
        labels = batch["labels"][0].tolist(); ids = batch["input_ids"][0].tolist(); pos = batch["position_ids"][0].tolist()
        cursor = 0
        for length in packed_row["seq_lengths"]:
            seg_ids, seg_lab = ids[cursor:cursor + length], labels[cursor:cursor + length]
            assert pos[cursor:cursor + length] == list(range(length)), "position reset missing"
            assert seg_lab[0] == -100, "example start is supervised"
            # identify the source example by exact token match
            cands = [i for i in by_len.get(length, []) if examples[i]["input_ids"] == seg_ids and i not in seen]
            assert cands, "packed segment does not match any example"
            i = cands[0]; seen.add(i)
            sup_ids = [t for t, l in zip(seg_ids, seg_lab) if l != -100]
            decoded = tok.decode(sup_ids, clean_up_tokenization_spaces=False)
            expected = "".join(m["content"] + sft_train.ASSISTANT_END for m in rows[i]["messages"] if m["role"] == "assistant" and m.get("train", True))
            assert decoded == expected, f"example {i}: supervised text differs\n got: {decoded!r}\n exp: {expected!r}"
            # a planted turn's text may legitimately equal a supervised turn of the same row (a verbatim-repeat plant copies the
            # previous ideal answer), so count occurrences: no more than the supervised turns that carry the same text
            for p in (m["content"] for m in rows[i]["messages"] if m.get("train") is False):
                allowed = sum(1 for m in rows[i]["messages"] if m["role"] == "assistant" and m.get("train", True) and p in m["content"])
                assert decoded.count(p) <= allowed, f"example {i}: planted text supervised"
            # every supervised span ends with the end token and the end token of masked turns is not supervised
            n_end_sup = sum(1 for t, l in zip(seg_ids, seg_lab) if t == end_id and l != -100)
            n_targets = sum(1 for m in rows[i]["messages"] if m["role"] == "assistant" and m.get("train", True))
            n_masked = sum(1 for m in rows[i]["messages"] if m["role"] == "assistant" and m.get("train") is False)
            assert n_end_sup == n_targets, f"example {i}: {n_end_sup} supervised end tokens for {n_targets} targets"
            assert sum(1 for t in seg_ids if t == end_id) == n_targets + n_masked
            if len(dump) < 20:
                dump.append({"example": i, "tokens": length, "supervised_tokens": len(sup_ids), "masked_assistant_turns": n_masked, "supervised_decoded": decoded,
                             "labels_by_token": [(tok.decode([t]), l != -100) for t, l in zip(seg_ids, seg_lab)]})
            cursor += length
    assert len(seen) == len(examples), f"{len(seen)} of {len(examples)} examples found in packed sequences"
    DUMP.write_text(json.dumps({"tokenizer": TOKENIZER, "rows": len(rows), "packed_sequences": n_packed, "capacity": capacity, "examples": dump}, ensure_ascii=False, indent=1))
    print(f"MASK_PIPELINE_OK rows={len(rows)} packed_sequences={n_packed} masked_turns={len(planted_all)} dump={DUMP}")


if __name__ == "__main__":
    main()
