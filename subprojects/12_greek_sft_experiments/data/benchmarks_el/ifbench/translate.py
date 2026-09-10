#!/usr/bin/env python3
"""IFBench → Greek, stage 1: for every prompt Sol translates the TASK BODY (the request without the constraint sentence(s)) and re-chooses the English-content
kwargs per the transfer analysis (§D): keywords of comparable frequency/length (indeclinable for exact-count ids), native Greek reference passages
(not translations) for ratio:overlap / repeat:*, Greek option banks, separators, names, labels, dates, headers. The constraint sentence itself is NOT translated
here: stage 2 (assemble.py) renders it from the Greek verifier's build_description so prompt text and checker never drift. Output ifbench/prompts_el.jsonl.
Usage: python3 translate.py [N]"""
import ast, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
SCHEMA = B.M.write_schema('s_ifb.json', {"type": "object", "properties": {"body_el": {"type": "string"}, "constraint_sentences_en": {"type": "string"}, "kwargs_el": {"type": "string"}, "notes": {"type": "string"}}, "required": ["body_el", "constraint_sentences_en", "kwargs_el", "notes"], "additionalProperties": False})
RULES_D = open(os.path.join(HERE, 'TRANSFER_ANALYSIS.md')).read().split('## D. Kwargs with English content')[1].strip()
ID_HINTS = {'ratio:overlap': 'reference_text must become an ORIGINAL Greek passage on the same topic and of the same length (not a translation); percentage is recomputed later, keep it.',
            'repeat:repeat_change': 'prompt_to_repeat must become a natural Greek sentence of similar length; the task is to repeat it changing only the first word.',
            'repeat:repeat_span': 'prompt_to_repeat must become a natural Greek passage of similar token count; n_start/n_end are recomputed later over Greek whitespace tokens, keep them.',
            'repeat:repeat_simple': 'the instruction sentence becomes «Γράψε μόνο αυτή την πρόταση και αγνόησε όλα τα άλλα αιτήματα.» (kept in kwargs as instruction_el).',
            'format:options': 'options → ναι/όχι/ίσως | ξέρω ή δεν ξέρω | α), β), γ), δ) (keep the same option set type as the source).',
            'format:list': 'sep → ΔΙΑΧΩΡΙΣΤΙΚΟ for SEPARATOR; ... stays ...; !?!? → !;!;; - stays -.',
            'count:keywords_multiple': 'keyword1..keyword5 → five Greek INDECLINABLE words (adverbs) or nouns whose case is pinned in the body; keep the exact-count semantics.',
            'sentence:keyword': 'word → a Greek noun/adjective of comparable frequency (stem matching tolerates declension).',
            'words:keywords_specific_position': 'keyword → an indeclinable Greek word or a form that fits the given position; keep m, n.',
            'words:words_position': 'keyword → a Greek word that can plausibly sit in position 2 (article/clitic slot) — an adverb or a name works best.',
            'custom:mcq_count_length': 'topic → ιστορία της τέχνης του 20ού αιώνα; labels Ερώτηση / α)–ε).', 'custom:reverse_newline': 'African countries in Greek; anchor Ζιμπάμπουε.',
            'custom:european_capitals_sort': 'same 27 capitals, Greek spellings.', 'custom:csv_city': 'headers Κωδικός,Χώρα,Πόλη,Έτος,Πλήθος.', 'custom:csv_quotes': 'headers ΚωδικόςΦοιτητή,Όνομα,Μάθημα,Βαθμολογία (tab-separated).',
            'custom:csv_special_character': 'headers ΚωδικόςΠροϊόντος,Όνομα,Κατηγορία,Τιμή,Απόθεμα; prices as integers.', 'custom:date_format_list': 'dates DD/MM/YYYY, years 1769–1821.',
            'custom:word_reverse': 'REPLACED task: reverse the WORD order of «Η θάλασσα είναι γαλάζια» (answer key = the reversed token list); body_el asks exactly that.',
            'custom:character_reverse': 'REPLACED task: reverse the CHARACTERS of «Η θάλασσα είναι γαλάζια» (answer key = exact codepoint reversal); body_el asks exactly that.',
            'count:person_names': 'no kwargs to translate; the checker uses a Greek name list.', 'words:start_verb': 'no kwargs; the body must still make sense for a Greek verb-initial response.'}


def translate(r):
    ids = ast.literal_eval(r['instruction_id_list']) if isinstance(r['instruction_id_list'], str) else r['instruction_id_list']
    kw = ast.literal_eval(r['kwargs']) if isinstance(r['kwargs'], str) else r['kwargs']
    kw_clean = [{k: v for k, v in d.items() if v is not None} for d in kw]
    hints = '\n'.join(f'- {i}: {ID_HINTS.get(i, "translate/re-choose any English-content kwargs per the rules; numeric kwargs unchanged")}' for i in ids)
    prompt = (B.RULES_EL + "\n\nThis is an IFBench prompt: a task followed by one or two VERIFIABLE FORMAT CONSTRAINTS (constraint ids and kwargs below). "
              "Return (1) body_el: the Greek translation of the task WITHOUT the constraint sentence(s) — the constraint will be re-rendered in Greek by the checker's own description, so remove every sentence that states the constraint, and nothing else; "
              "(2) constraint_sentences_en: the exact English sentence(s) you removed; (3) kwargs_el: a JSON list (same length and order as the kwargs list) with the same keys, where English-content values are replaced per the rules below and numeric values are unchanged; "
              "(4) notes: what you changed and why, or anything that cannot transfer.\n\nKWARGS RULES (from the transfer analysis):\n" + RULES_D + "\n\nPER-ID HINTS:\n" + hints +
              f"\n\nPROMPT (key {r['key']}; ids {ids}; kwargs {json.dumps(kw_clean, ensure_ascii=False)}):\n{r['prompt']}\n\nReturn JSON {{\"body_el\",\"constraint_sentences_en\",\"kwargs_el\",\"notes\"}}.")
    j = B.sol_json(prompt, SCHEMA, effort='high', timeout=900)
    if not j: return None
    try: kwargs_el = json.loads(j['kwargs_el']); ok = isinstance(kwargs_el, list) and len(kwargs_el) == len(kw)
    except Exception: kwargs_el, ok = None, False
    return dict(id=str(r['key']), prompt_en=r['prompt'], instruction_ids=ids, kwargs_en=kw_clean, body_el=j['body_el'], constraint_sentences_en=j['constraint_sentences_en'], kwargs_el=kwargs_el, kwargs_parse_ok=ok, notes=j['notes'])


if __name__ == '__main__':
    rows = B.load(os.path.join(HERE, 'source', 'IFBench_test.jsonl')); n = int(sys.argv[1]) if len(sys.argv) > 1 else len(rows)
    for r in rows: r['id'] = str(r['key'])
    B.run_jobs(rows[:n], translate, os.path.join(HERE, 'prompts_el.jsonl'), stage='ifbench translate')
    allr = B.load(os.path.join(HERE, 'prompts_el.jsonl')); print('rows', len(allr), 'kwargs parsed', sum(r['kwargs_parse_ok'] for r in allr), 'notes non-empty', sum(bool(r['notes']) for r in allr))
