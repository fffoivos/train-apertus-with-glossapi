#!/usr/bin/env python3
"""Per-turn loss mask test for cluster/sft_train.py (DATA_TODO 26).

Runs against the real Apertus tokenizer (a local checkpoint directory or the
hub cache) and checks that assistant messages flagged ``train: false`` are
context-only: their tokens, including the assistant-end token, get label -100,
while every other assistant turn stays fully supervised.

    ~/venvs/sfttrain/bin/python cluster/test_loss_mask.py [tokenizer_dir]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transformers import AutoTokenizer  # noqa: E402

import sft_train  # noqa: E402

TOKENIZER = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/models/greek-apertus-8b-sft-r2-idB-bf16")


def main() -> None:
    tok = AutoTokenizer.from_pretrained(TOKENIZER, local_files_only=True)
    tok.chat_template = sft_train.patch_apertus_template(tok.chat_template)
    end_id = tok.convert_tokens_to_ids(sft_train.ASSISTANT_END)
    msgs = [
        {"role": "user", "content": "Γεια"},
        {"role": "assistant", "content": "Καλημέρα, τι θέλεις;"},
        {"role": "user", "content": "Πες μου ένα αστείο."},
        {"role": "assistant", "content": "Πες μου ένα αστείο. Πες μου ένα αστείο.", "train": False, "kind": "planted:verbatim_repeat"},
        {"role": "user", "content": "Επαναλαμβάνεις ό,τι λέω."},
        {"role": "assistant", "content": "Έχεις δίκιο. Ένα αστείο: ο γάτος."},
    ]
    out = sft_train.tokenize_messages(tok, msgs)
    ids, labels, mask = out["input_ids"], out["labels"], out["assistant_masks"]
    runs = sft_train._mask_runs(mask)
    assert len(runs) == 2, runs
    supervised = [tok.decode(ids[a:b]) for a, b in runs]
    assert supervised[0] == "Καλημέρα, τι θέλεις;<|assistant_end|>", supervised[0]
    assert supervised[1] == "Έχεις δίκιο. Ένα αστείο: ο γάτος.<|assistant_end|>", supervised[1]
    planted = tok.encode("Πες μου ένα αστείο. Πες μου ένα αστείο.", add_special_tokens=False)
    text_ids = ids
    # the planted turn's tokens must all be -100, including its end token
    for i in range(len(text_ids) - len(planted) + 1):
        if text_ids[i : i + len(planted)] == planted and labels[i] == -100 and i > runs[0][1]:
            assert all(l == -100 for l in labels[i : i + len(planted) + 1]), "planted turn is supervised"
            assert text_ids[i + len(planted)] == end_id
            break
    else:
        raise AssertionError("planted turn not found in the rendered ids")
    assert sum(1 for l in labels if l != -100) == sum(b - a for a, b in runs)
    assert labels.count(end_id) == 2, labels.count(end_id)

    # default flag: every assistant turn supervised
    plain = [{k: v for k, v in m.items() if k in ("role", "content")} for m in msgs]
    out2 = sft_train.tokenize_messages(tok, plain)
    assert len(sft_train._mask_runs(out2["assistant_masks"])) == 3

    # all turns flagged off must fail loudly
    off = [dict(m, train=False) if m["role"] == "assistant" else m for m in plain]
    try:
        sft_train.tokenize_messages(tok, off)
    except sft_train.ConfigError:
        pass
    else:
        raise AssertionError("all-false row did not raise")
    print("LOSS_MASK_OK", len(ids), "tokens;", "supervised spans", runs)


if __name__ == "__main__":
    main()
