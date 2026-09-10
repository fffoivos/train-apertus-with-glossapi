#!/usr/bin/env python3
"""IFBench-el stage 2: compose each Greek prompt = translated task body + the Greek constraint description rendered by OUR verifier class
(instructions_el.build_description(**kwargs_el)), so prompt wording and checker never drift; post-process kwargs whose English value was the prompt itself
(ratio:overlap reference_text, repeat:repeat_change / repeat_span prompt_to_repeat → the Greek body; repeat_span indices rescaled to Greek tokens;
repeat_simple instruction sentence). Verifies every constraint object builds and that check_following runs on a dummy answer. Writes prompts_el_final.jsonl
and overlap_classes.json (from TRANSFER_ANALYSIS). Usage: python3 assemble.py"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
import instructions_registry_el as REG
OVERLAP = {}   # id → overlap class from the transfer analysis table
for line in open(os.path.join(HERE, 'TRANSFER_ANALYSIS.md')):
    m = re.match(r'\| ([a-z_]+:[a-z_\-]+) \|.*\| (seen-novel-composition|unseen|unresolved|seen)[^|]*\| (faithful|adapt|replace|exclude)', line)
    if m: OVERLAP[m.group(1)] = dict(overlap=m.group(2), transfer=m.group(3))
PROMPT_KW = {'ratio:overlap': 'reference_text', 'repeat:repeat_change': 'prompt_to_repeat', 'repeat:repeat_span': 'prompt_to_repeat'}
FIDELITY = {  # prompt-semantic fidelity to the English instruction / checker fidelity to upstream / difficulty retuning (astra F3): anything not 'faithful' puts the prompt in the EXTENSION
 'format:thesis': ('weakened: "each section" → "at least one section" (matches the upstream checker, not the English text)', 'faithful', None),
 'words:palindrome': ('faithful wording', 'faithful', 'N 10 → 3'), 'words:vowel': ('faithful wording', 'faithful', 'distinct vowels ≤3 → ≤4'), 'words:repeats': ('faithful wording', 'faithful', 'small_n floor 5'),
 'custom:sentence_alphabet': ('localised: 26 → 24 letters', 'faithful', '26 → 24'), 'custom:reverse_newline': ('localised list', 'faithful', 'lines 52 → 14 (Greek collation)'),
 'custom:date_format_list': ('changed: ISO date → Greek numeric or month-name dates', 'adapted', None), 'format:quote_unquote': ('changed predicate: stated as what the checker tests', 'faithful', None),
 'ratio:sentence_type': ('strengthened: ≥1 interrogative required', 'tightened', None), 'ratio:sentence_balance': ('strengthened: ≥1 of each type', 'tightened', None),
 'custom:word_reverse': ('replaced task', 'replaced', None), 'custom:character_reverse': ('replaced task', 'replaced', None), 'count:pronouns': ('operational counter (clitic gate) disclosed', 'approximation', None), 'words:consonants': ('faithful wording; ξ/ψ count as clusters', 'approximation', None),
 'words:start_verb': ('faithful wording; heuristic verb rule', 'approximation', None), 'words:odd_even_syllables': ('faithful wording; rule-based syllables', 'approximation', None), 'format:emoji': ('faithful wording; emoji by codepoint ranges', 'approximation', None)}
try:
    sys.path.insert(0, os.path.join(HERE, '..', '..', 'greek_if')); import constraints as C
    FAMILY_EVIDENCE = {k: (v.get('phrasings') or [''])[0] for k, v in C.FAMILIES.items()}
except Exception: FAMILY_EVIDENCE = {}
CLOSEST = {}
for line in open(os.path.join(HERE, 'TRANSFER_ANALYSIS.md')):
    m = re.match(r'\| ([a-z_]+:[a-z_\-]+) \| [^|]* \| \d+ \| ([^|]*) \|', line)
    if m: CLOSEST[m.group(1)] = m.group(2).strip()


OVERRIDE_SPAN = {'287': (10, 12), '285': (5, 14), '284': (3, 7), '286': (0, 7)}   # exact Greek token spans verified by the cross-check
DROP_ID = {'212': 'words:consonants', '213': 'words:consonants', '214': 'words:consonants'}   # infeasible with ratio:overlap in Greek (function words have no consonant cluster); adaptation recorded
SEP_FIX = {'88': '!;!;'}


def fix_kwargs(r):
    out = []
    for iid, kw_en, kw_el in zip(r['instruction_ids'], r['kwargs_en'], r['kwargs_el'] or r['kwargs_en']):
        kw = dict(kw_el) if isinstance(kw_el, dict) else dict(kw_en)
        for k, v in kw_en.items():   # numeric kwargs always from the source
            if isinstance(v, (int, float)) and not isinstance(v, bool): kw[k] = int(v) if float(v).is_integer() else v
        if iid in PROMPT_KW and (kw_en.get(PROMPT_KW[iid]) or '').strip().lower()[:40] in r['prompt_en'].lower():
            kw[PROMPT_KW[iid]] = r['body_el'].strip()   # the English kwarg was the prompt itself: keep that semantics in Greek
            if iid == 'repeat:repeat_span' and 'n_start' in kw_en:
                n_en, n_el = len((kw_en.get('prompt_to_repeat') or r['prompt_en']).split()), len(r['body_el'].split()); scale = n_el / max(1, n_en)   # cross-check: scale by the repeated text, not the whole prompt
                kw['n_start'] = min(n_el - 1, int(round(kw_en['n_start'] * scale))); kw['n_end'] = max(kw['n_start'], min(n_el - 1, int(round(kw_en['n_end'] * scale))))
        if iid == 'repeat:repeat_span' and r['id'] in OVERRIDE_SPAN: kw['n_start'], kw['n_end'] = OVERRIDE_SPAN[r['id']]
        if iid == 'format:list' and r['id'] in SEP_FIX: kw['sep'] = SEP_FIX[r['id']]
        if iid == 'words:repeats' and 'small_n' in kw: kw['small_n_upstream'] = kw['small_n']; kw['small_n'] = max(5, int(kw['small_n']))   # effective value (RETUNED floor) stored explicitly
        out.append(kw)
    return out


def main():
    rows = B.load(os.path.join(HERE, 'prompts_el.jsonl')); final = []; errors = []
    for r in rows:
        if r['id'] in DROP_ID and DROP_ID[r['id']] in r['instruction_ids']:
            k = r['instruction_ids'].index(DROP_ID[r['id']]); r['instruction_ids'] = [x for j, x in enumerate(r['instruction_ids']) if j != k]; r['kwargs_en'] = [x for j, x in enumerate(r['kwargs_en']) if j != k]; r['kwargs_el'] = [x for j, x in enumerate(r['kwargs_el'] or r['kwargs_en']) if j != k]; r['adapted'] = f'dropped {DROP_ID[r["id"]]} (infeasible pair in Greek)'
        if r['id'] == '104': r['body_el'] = re.sub(r'(?m)^\s*([A-DΑ-Δ])[.)]\s*', lambda m: {'A': 'α) ', 'B': 'β) ', 'C': 'γ) ', 'D': 'δ) ', 'Α': 'α) ', 'Β': 'β) ', 'Γ': 'γ) ', 'Δ': 'δ) '}[m.group(1)], r['body_el'])   # options relabelled to the checker's α) β) γ) δ)
        kws = fix_kwargs(r); descs = []; ok = True
        for iid, kw in zip(r['instruction_ids'], kws):
            try:
                inst = REG.INSTRUCTION_DICT[iid](iid)
                dkw = dict(kw)
                d = inst.build_description(**dkw).replace('επικάλυψη τριγραμμάτων', 'επικάλυψη τριγραμμάτων (τριάδων διαδοχικών λέξεων· ποσοστό = κοινά τριγράμματα προς τα τριγράμματα της απάντησής σου)')   # astra F2: literal reference text and the formula; descs.append(d); inst.check_following('Δοκιμαστική απάντηση. Δεύτερη πρόταση!')
            except Exception as e: ok = False; errors.append(dict(id=r['id'], iid=iid, err=f'{type(e).__name__}: {str(e)[:120]}'))
        body = r['body_el'].strip()
        constraint_only = all(i.startswith('custom:') for i in r['instruction_ids']) or all(i == 'repeat:repeat_change' for i in r['instruction_ids'])   # cross-check: the 85%-of-prompt heuristic destroyed 4 task bodies; repeat_change's description already embeds the request
        if constraint_only: body = ''   # the English prompt IS the constraint (custom:* tasks, CSV/MCQ/lists): the Greek prompt is the checker's own description, nothing else (assemble review 2026-09-10: duplicated and mismatched headers otherwise)
        if body and body[-1] not in '.;!?…»"\')': body += '.'   # cross-check: 55 bodies ended without punctuation and read as run-ons
        prompt_el = (body + ('\n\n' if '\n' in body or len(body) > 200 else ' ') + ' '.join(descs)).strip() if body else ' '.join(descs).strip()
        classes = [OVERLAP.get(i, {}).get('overlap', 'unresolved') for i in r['instruction_ids']]; rank = {'seen': 0, 'seen-novel-composition': 1, 'unresolved': 2, 'unseen': 3}
        fid = [dict(id=i, prompt_semantic=FIDELITY.get(i, ('faithful', 'faithful', None))[0], checker=FIDELITY.get(i, ('faithful', 'faithful', None))[1], retuned=FIDELITY.get(i, ('faithful', 'faithful', None))[2], closest_family=CLOSEST.get(i, ''), family_evidence=FAMILY_EVIDENCE.get(CLOSEST.get(i, '').split(' ')[0].split('+')[0].strip(), '')) for i in r['instruction_ids']]
        core = not r.get('adapted') and all(f['prompt_semantic'].startswith(('faithful', 'localised')) and f['checker'] in ('faithful', 'approximation') and not f['retuned'] for f in fid)
        final.append(dict(id=r['id'], prompt_en=r['prompt_en'], prompt_el=prompt_el, body_el=body, instruction_id_list=r['instruction_ids'], kwargs=kws, kwargs_en=r['kwargs_en'], descriptions_el=descs, fidelity=fid, core=core,
                          overlap_class=min(classes, key=lambda c: rank[c]), overlap_classes=classes, mixed_overlap=len(set(classes)) > 1, adapted=r.get('adapted'), transfer=[OVERLAP.get(i, {}).get('transfer', 'adapt') for i in r['instruction_ids']], builds_ok=ok, notes=r['notes']))
    with open(os.path.join(HERE, 'prompts_el_final.jsonl'), 'w') as f: [f.write(json.dumps(x, ensure_ascii=False) + '\n') for x in final]
    import collections
    summ = dict(rows=len(final), builds_ok=sum(x['builds_ok'] for x in final), by_overlap=dict(collections.Counter(x['overlap_class'] for x in final)), by_overlap_instances=dict(collections.Counter(c for x in final for c in x['overlap_classes'])), mixed=sum(x['mixed_overlap'] for x in final), core=sum(x['core'] for x in final), extension=sum(not x['core'] for x in final), by_transfer=dict(collections.Counter(t for x in final for t in x['transfer'])), id_to_family=CLOSEST, errors=errors[:20])
    json.dump(summ, open(os.path.join(HERE, 'overlap_classes.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False)[:1200])


if __name__ == '__main__': main()
