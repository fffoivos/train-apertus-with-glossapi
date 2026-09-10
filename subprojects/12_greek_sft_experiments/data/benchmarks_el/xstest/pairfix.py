#!/usr/bin/env python3
"""XSTest-el second pass after the Claude cross-check: (1) apply the cross-checker's corrected prompts; (2) re-translate every safe/unsafe PAIR jointly
(homonyms, figurative, safe targets, safe contexts, definitions: ids i and i+25; historical events likewise) so both halves share the same Greek trigger word
and the same entity forms — the contrast design of XSTest depends on it (cross-check: ~30 of 90 lexical pairs had lost the shared trigger; the safe half was
neutralised or calqued). The cross-checker's notes for both halves are given to the translator. Writes prompts_el.jsonl (backup .v1). Usage: python3 pairfix.py"""
import json, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
SCHEMA = B.M.write_schema('s_xspair.json', {"type": "object", "properties": {"safe_el": {"type": "string"}, "unsafe_el": {"type": "string"}, "trigger_el": {"type": "string"}, "transfer": {"type": "string"}, "note": {"type": "string"}}, "required": ["safe_el", "unsafe_el", "trigger_el", "transfer", "note"], "additionalProperties": False})
BLOCKS = [1, 51, 101, 151, 201, 326]


def fix_pair(p):
    s, u = p['safe'], p['unsafe']
    prompt = (B.RULES_EL + "\n\nXSTest works in PAIRS: a SAFE prompt that only looks alarming because of a word or phrase, and its UNSAFE contrast that uses THE SAME word or phrase in its genuinely harmful sense. "
              "The test measures over-refusal, so the Greek pair must keep the SHARED SURFACE TRIGGER: the same Greek verb/noun (same stem) in both halves, alarming on the surface in the safe half and unambiguously benign to a Greek reader, genuinely harmful in the unsafe half and not more harmful than the English. "
              "Rules: (a) if a Greek word carries both meanings (σκοτώνω χρόνο / σκοτώνω άνθρωπο; εκτελώ πρόγραμμα / εκτελώ άνθρωπο; δέρνω κάποιον στο τάβλι / δέρνω κάποιον), use it in both; (b) if the English homonym has no Greek counterpart, choose a Greek homonym or idiom of the same type and rewrite BOTH halves around it, keeping the topic as close as possible (transfer=substitute); "
              "(c) never neutralise the safe half into a plain request (e.g. «πετύχω τους στόχους» for 'hit my targets' tests nothing) and never calque an English idiom that does not exist in Greek; (d) never sanitise the unsafe half (e.g. «υπερισχύω» for 'overpower' is wrong) and never add detail to it; "
              "(e) named people, places, events and fictional characters take the SAME form in both halves (standard Greek transliteration where one exists: Σίνζο Άμπε, Πινοσέτ, Τζέιμς Μποντ; otherwise keep the Latin form in both); (f) natural chat Greek a real user would type.\n\n"
              f"Type: {s['type']} / {u['type']}. Focus word: «{s['focus_en']}».\nSAFE EN: {s['prompt_en']}\nUNSAFE EN: {u['prompt_en']}\nCurrent Greek: SAFE «{s['prompt_el']}» | UNSAFE «{u['prompt_el']}»\n"
              f"Cross-checker's notes: SAFE: {s.get('cc_note', '')} {('FIX: ' + s['cc_fix']) if s.get('cc_fix') else ''} | UNSAFE: {u.get('cc_note', '')} {('FIX: ' + u['cc_fix']) if u.get('cc_fix') else ''}\n\n"
              "Return JSON {\"safe_el\",\"unsafe_el\",\"trigger_el\" (the shared Greek trigger stem),\"transfer\" (faithful|substitute),\"note\"}.")
    j = B.sol_json(prompt, SCHEMA, effort='high', timeout=900)
    return None if not j else dict(id=p['id'], **j)


def main():
    path = os.path.join(HERE, 'prompts_el.jsonl'); rows = {int(r['id']): r for r in B.load(path)}; shutil.copy(path, path + '.v1')
    cc = {int(c['id']): c for c in B.load(os.path.join(HERE, 'crosscheck_claude.jsonl'))}
    for i, r in rows.items():
        c = cc.get(i, {}); r['cc_note'] = c.get('note', ''); r['cc_fix'] = c.get('fix', ''); r['cc_mechanism'] = c.get('mechanism_kept'); r['cc_natural'] = c.get('natural')
        if c.get('fix'): r['prompt_el'] = c['fix']; r['crosscheck_fix'] = True
    pairs = [dict(id=f'{b + k}_{b + k + 25}', safe=rows[b + k], unsafe=rows[b + k + 25]) for b in BLOCKS for k in range(25)]
    out = {d['id']: d for d in B.run_jobs(pairs, fix_pair, os.path.join(HERE, 'pairfix_out.jsonl'), stage='xstest pairfix')}
    changed = 0
    for p in pairs:
        d = out.get(p['id'])
        if not d: continue
        for side, key in (('safe', 'safe_el'), ('unsafe', 'unsafe_el')):
            r = p[side]
            if r['prompt_el'] != d[key]: r['prompt_el_v1'] = r['prompt_el']; r['prompt_el'] = d[key]; changed += 1
            r['trigger_el'] = d['trigger_el']; r['transfer'] = d['transfer'] if d['transfer'] in ('faithful', 'substitute') else r['transfer']; r['pair_note'] = d['note']; r['pair_id'] = p['id']
    with open(path, 'w') as f: [f.write(json.dumps(rows[i], ensure_ascii=False) + '\n') for i in sorted(rows)]
    print(json.dumps(dict(rows=len(rows), pairs=len(pairs), pair_calls_ok=len(out), prompts_changed=changed, claude_fixes_applied=sum(1 for r in rows.values() if r.get('crosscheck_fix')))))


if __name__ == '__main__': main()
