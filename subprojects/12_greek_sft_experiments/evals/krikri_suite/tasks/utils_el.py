import re, datasets, json, os
_TQA = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ilsp_truthfulqa_prompt.json")))
def truthfulqa_doc_to_text(doc): return _TQA["pre_query"] + _TQA["prefix"] + doc["question"] + _TQA["suffix"]   # ILSP prompt verbatim
def preprocess(text):
    text = text.strip(); text = text.replace(" [title]", ". "); text = re.sub("\\[.*?\\]", "", text); return text.replace("  ", " ")
def process_docs(dataset: datasets.Dataset) -> datasets.Dataset:
    def _p(doc):
        ctx = doc["ctx_a"] + " " + doc["ctx_b"].capitalize()
        return {"query": preprocess(doc["activity_label"] + ": " + ctx), "choices": [preprocess(e) for e in doc["endings"]], "gold": int(doc["label"])}
    return dataset.map(_p)
def process_results_mc2(doc, results):
    import numpy as np
    lls, is_greedy = zip(*results); split_idx = list(doc["mc2_targets"]["labels"]).index(0)
    ll_true, ll_false = lls[:split_idx], lls[split_idx:]
    p_true, p_false = np.exp(np.array(ll_true)), np.exp(np.array(ll_false)); p_true = p_true / (sum(p_true) + sum(p_false))
    return {"acc": sum(p_true)}
