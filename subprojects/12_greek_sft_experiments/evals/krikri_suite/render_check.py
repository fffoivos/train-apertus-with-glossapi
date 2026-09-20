#!/usr/bin/env python3
"""Render every suite task through the harness without a model: doc counts, the first few-shot context, choices and target. Usage: render_check.py <include_path> <tasks,csv>"""
import sys, random
from lm_eval.tasks import TaskManager, get_task_dict
inc, names = sys.argv[1], sys.argv[2].split(',')
tm = TaskManager(include_path=inc); td = get_task_dict(names, tm)
def walk(d):
    for k, v in d.items():
        if isinstance(v, dict): yield from walk(v)
        else: yield k, v
for name, task in walk(td):
    if not hasattr(task, 'doc_to_text'): continue
    docs = list(task.test_docs()) if task.has_test_docs() else list(task.validation_docs())
    nf = task.config.num_fewshot or 0
    if hasattr(task, 'set_fewshot_seed'): task.set_fewshot_seed(1234)
    for j in (0, len(docs) // 2):
        doc = docs[j]
        try: ctx = task.fewshot_context(doc, nf)
        except TypeError: ctx = task.fewshot_context(doc, nf, rnd=random.Random(1234))
        print(f'===== {name} docs={len(docs)} num_fewshot={nf} doc#{j} context_chars={len(ctx)}')
        print(ctx if len(ctx) <= 2200 else ctx[:900] + '\n[...]\n' + ctx[-1300:])
        print('CHOICES', task.doc_to_choice(doc) if callable(getattr(task, 'doc_to_choice', None)) else None, '| TARGET', task.doc_to_target(doc))
