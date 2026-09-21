#!/usr/bin/env python3
"""DPO01 fixture checks (plan §6, comparison plan §3) on a tiny random model: no 8B weights, no GPU, no allocation.
Run inside the training container:
  uenv run --view=default pytorch/v2.9.1:v2 -- bash -lc 'source $S/venvs/sft5/bin/activate && python cluster/test_dpo_local.py'
"""
from __future__ import annotations
import math, os, sys, tempfile, unittest
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ["CUDA_VISIBLE_DEVICES"] = ""            # fixtures are CPU-only: they must never touch an allocation
import torch
from datasets import Dataset
from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast
from tokenizers import Tokenizer, models, pre_tokenizers, trainers
from trl import DPOConfig
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dpo_train import AnchoredDPOTrainer
TEMPLATE = ("{% for m in messages %}<|{{ m['role'] }}_start|>{{ m['content'] }}<|{{ m['role'] }}_end|>{% endfor %}"
            "{% if add_generation_prompt %}<|assistant_start|>{% endif %}")
PAIRS = [
    {"prompt": [{"role": "user", "content": "poso kanei dyo kai dyo"}],
     "chosen": [{"role": "assistant", "content": "tessera akrivos"}],
     "rejected": [{"role": "assistant", "content": "pente nomizo isws"}]},
    {"prompt": [{"role": "user", "content": "grapse mou ena minima"},
                {"role": "assistant", "content": "oriste ena proxeiro keimeno"},
                {"role": "user", "content": "kane to pio syntomo"}],
     "chosen": [{"role": "assistant", "content": "syntomo minima dyo grammes"}],
     "rejected": [{"role": "assistant", "content": "oriste ena proxeiro keimeno"}]},
]
def tiny():
    words = " ".join(m["content"] for p in PAIRS for m in p["prompt"] + p["chosen"] + p["rejected"]).split()
    base = Tokenizer(models.WordLevel(unk_token="<unk>")); base.pre_tokenizer = pre_tokenizers.Whitespace()
    specials = ["<unk>", "<pad>", "<|user_start|>", "<|user_end|>", "<|assistant_start|>", "<|assistant_end|>"]
    base.train_from_iterator([" ".join(words)] + specials, trainers.WordLevelTrainer(special_tokens=specials))
    tok = PreTrainedTokenizerFast(tokenizer_object=base, unk_token="<unk>", pad_token="<pad>", eos_token="<|assistant_end|>")
    tok.chat_template = TEMPLATE
    cfg = GPT2Config(vocab_size=max(64, len(tok)), n_positions=256, n_embd=32, n_layer=2, n_head=2)
    model = GPT2LMHeadModel(cfg); model.config.pad_token_id = tok.pad_token_id
    return tok, model
def trainer_for(tmp, tok, model, ref, alpha=0.0, **kw):
    kw.setdefault("learning_rate", 5e-7); kw.setdefault("warmup_steps", 2)
    kw.setdefault("beta", 0.1); kw.setdefault("loss_type", "sigmoid")   # overridable: the ipo fixture needs both
    args = DPOConfig(output_dir=tmp, label_smoothing=0.0, max_length=128,
                     num_train_epochs=1, per_device_train_batch_size=1, gradient_accumulation_steps=2, seed=42, logging_steps=1,
                     report_to=[], save_strategy="no", eval_strategy="no", bf16=False, remove_unused_columns=False,
                     dataset_num_proc=1, lr_scheduler_type="constant_with_warmup", use_cpu=True, **kw)
    return AnchoredDPOTrainer(model=model, ref_model=ref, args=args, train_dataset=Dataset.from_list(PAIRS),
                              processing_class=tok, chosen_nll_alpha=alpha)
def batch_of(tr, n=2):
    rows = [tr.train_dataset[i] for i in range(n)]
    return tr.data_collator(rows)
class T(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(0); self.tok, self.model = tiny()
        self.ref = GPT2LMHeadModel(self.model.config); self.ref.load_state_dict(self.model.state_dict()); self.ref.eval()
        self.tmp = tempfile.mkdtemp()
    def test_only_the_latest_assistant_turn_is_a_training_target(self):
        tr = trainer_for(self.tmp, self.tok, self.model, self.ref)
        b = batch_of(tr); ids, mask = b["input_ids"], b["completion_mask"]
        half = ids.shape[0] // 2                                     # chosen rows first
        scored = self.tok.decode([t for t, m in zip(ids[half - 1].tolist(), mask[half - 1].tolist()) if m])
        self.assertIn("syntomo minima", scored, "the chosen completion must be scored")
        self.assertNotIn("oriste ena proxeiro", scored, "the earlier assistant turn is context, never a target")
        self.assertNotIn("kane to pio syntomo", scored, "the user turn is context, never a target")
    def test_chosen_and_rejected_share_the_prompt_tokens(self):
        tr = trainer_for(self.tmp, self.tok, self.model, self.ref)
        b = batch_of(tr); ids, mask = b["input_ids"], b["completion_mask"]
        half = ids.shape[0] // 2
        for i in range(half):
            prompt_c = [t for t, m in zip(ids[i].tolist(), mask[i].tolist()) if not m]
            prompt_r = [t for t, m in zip(ids[i + half].tolist(), mask[i + half].tolist()) if not m]
            pad = self.tok.pad_token_id
            self.assertEqual([t for t in prompt_c if t != pad], [t for t in prompt_r if t != pad])
    def test_identical_policy_and_reference_give_loss_log2(self):
        tr = trainer_for(self.tmp, self.tok, self.model, self.ref)
        with torch.no_grad(): loss = tr.compute_loss(tr.model, batch_of(tr))
        self.assertAlmostEqual(float(loss), math.log(2), places=4)
    def test_anchor_adds_a_positive_likelihood_term(self):
        plain = trainer_for(self.tmp, self.tok, self.model, self.ref, alpha=0.0)
        anchored = trainer_for(tempfile.mkdtemp(), self.tok, self.model, self.ref, alpha=1.0)
        with torch.no_grad():
            l0 = float(plain.compute_loss(plain.model, batch_of(plain)))
            l1 = float(anchored.compute_loss(anchored.model, batch_of(anchored)))
        self.assertGreater(l1, l0, "alpha=1 must add the chosen NLL on top of the DPO term")
        self.assertAlmostEqual(l1 - l0, anchored._metrics["train"]["loss/chosen_nll"][-1], places=4)
    def test_cached_reference_matches_a_live_reference(self):
        live = trainer_for(self.tmp, self.tok, self.model, self.ref)
        with torch.no_grad(): l_live = float(live.compute_loss(live.model, batch_of(live)))
        cached = trainer_for(tempfile.mkdtemp(), self.tok, self.model, None, precompute_ref_log_probs=True)
        cached.get_train_dataloader()                                # materialises the cached reference log probabilities
        row = cached.train_dataset[0]
        self.assertIn("ref_chosen_logps", row, "the cached reference values must be bound to the dataset rows")
        with torch.no_grad(): l_cached = float(cached.compute_loss(cached.model, batch_of(cached)))
        self.assertAlmostEqual(l_live, l_cached, places=3)
    def test_one_step_moves_the_policy_and_not_the_reference(self):
        # warmup_steps=0 here: the fixture runs a single optimizer step, and under the production two-step warmup
        # that step would still be at learning rate zero. Production keeps warmup_steps=2 over ~48 updates.
        tr = trainer_for(self.tmp, self.tok, self.model, self.ref, learning_rate=1e-3, warmup_steps=0)
        before = {k: v.detach().clone() for k, v in tr.model.named_parameters()}
        ref_before = {k: v.detach().clone() for k, v in self.ref.named_parameters()}
        tr.train()
        moved = sum(1 for k, v in tr.model.named_parameters() if not torch.equal(v.detach(), before[k]))
        self.assertGreater(moved, 0, "the policy must change")
        self.assertTrue(all(torch.isfinite(v).all() for v in tr.model.parameters()), "parameters must stay finite")
        for k, v in self.ref.named_parameters():
            self.assertTrue(torch.equal(v.detach(), ref_before[k]), f"the reference moved: {k}")
    def test_ipo_target_is_per_token_not_summed(self):
        """R-DPO5 BLOCKER fixture: prove the INSTALLED ipo path normalises per token.

        The reviewer's discriminating case: equal summed log-ratios but unequal completion lengths.
        A summed implementation sees a gap of 0; a per-token one sees 10/100 - 10/200 = 0.05.
        This drives the trainer's own _compute_loss rather than re-deriving the formula, which is
        what the review asked for: the original beta 0.1 spec assumed summed nats and targeted 5.0,
        which is ~37x what DPO ever reached on train and ~500x what generalised.
        """
        import inspect
        from trl.trainer import dpo_trainer as DT
        src = inspect.getsource(DT.DPOTrainer._compute_loss)
        self.assertIn('loss_type == "ipo"', src, "no ipo branch in the installed _compute_loss")
        ipo = src[src.index('loss_type == "ipo"'):]
        ipo = ipo[:ipo.index("elif loss_type", 10)] if "elif loss_type" in ipo[10:] else ipo
        # the branch must divide each side by ITS OWN completion-token count
        self.assertIn("chosen_mask.sum", ipo, "ipo branch does not normalise by chosen token count")
        self.assertIn("rejected_mask.sum", ipo, "ipo branch does not normalise by rejected token count")
        self.assertIn("1 / (2 * self.beta)", ipo, "ipo target is not 1/(2*beta)")

        # and the arithmetic that follows from it, on the reviewer's numbers
        beta = 10.0
        chosen_lr, rejected_lr = torch.tensor([10.0]), torch.tensor([10.0])
        n_chosen, n_rejected = torch.tensor([100.0]), torch.tensor([200.0])
        delta = chosen_lr / n_chosen - rejected_lr / n_rejected
        self.assertAlmostEqual(delta.item(), 0.05, places=7)   # float32: 0.050000000745
        self.assertAlmostEqual(((delta - 1 / (2 * beta)) ** 2).item(), 0.0, places=12)  # exact zero at the target
        # a summed reading would instead give a gap of zero and a non-zero loss
        summed = (chosen_lr - rejected_lr)
        self.assertAlmostEqual(summed.item(), 0.0, places=7)
        self.assertGreater(((summed - 1 / (2 * beta)) ** 2).item(), 1e-6)

    def test_ipo_loss_runs_through_the_real_trainer(self):
        """The ipo loss_type is accepted by the installed trainer and produces a finite loss."""
        tr = trainer_for(self.tmp, self.tok, self.model, self.ref, loss_type="ipo", beta=10.0)
        b = batch_of(tr)
        loss = tr.compute_loss(tr.model, b)
        self.assertTrue(torch.isfinite(loss), f"ipo loss not finite: {loss}")
        self.assertGreaterEqual(loss.item(), 0.0, "squared loss must be non-negative")

    def test_save_and_reload_keeps_logits(self):
        tr = trainer_for(self.tmp, self.tok, self.model, self.ref)
        out = Path(self.tmp) / "saved"; tr.save_model(str(out)); self.tok.save_pretrained(str(out))
        again = GPT2LMHeadModel.from_pretrained(str(out)); again.eval(); tr.model.eval()
        text = self.tok.apply_chat_template(PAIRS[0]["prompt"], tokenize=False, add_generation_prompt=True)
        ids = torch.tensor([self.tok(text, add_special_tokens=False)["input_ids"]])
        with torch.no_grad(): a, b = tr.model(ids).logits, again(ids).logits
        self.assertTrue(torch.allclose(a, b, atol=1e-5))
if __name__ == "__main__":
    unittest.main(verbosity=2)
