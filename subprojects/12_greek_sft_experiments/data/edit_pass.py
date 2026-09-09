#!/usr/bin/env python3
"""Greek correction pass for a generated dataset (owner, 9 September: every produced row gets the editor, as the personality set did).
An editor model that did NOT write the rows reads every assistant turn with the Γ brief + the editor HEAD, returns corrected turns and a change log.
Guards: for instruction-following rows the edited answer is re-checked against the row's constraints and reverted if any breaks; for math rows the
final answer must stay equivalent. Resumable; batches of 5; Sol by default (Opus is not affordable at 30k rows).
Usage: python3 edit_pass.py <rows.jsonl> <out_dir> --kind if|math [--model gpt-5.6-sol] [--effort medium]   env WORKERS (24)"""
import argparse, collections, json, os, sys, threading
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'personality')); sys.path.insert(0, os.path.join(HERE, 'greek_if')); sys.path.insert(0, os.path.join(HERE, 'math'))
from personality_brief import BRIEF as GAMMA; import mathlib as M; import constraints as C
HEAD = ("Είσαι επιμελητής που ΔΕΝ έγραψε αυτές τις γραμμές: τις διαβάζεις με φρέσκο μάτι και αυστηρότητα, χωρίς να υπερασπίζεσαι το κείμενο. Διορθώνεις ΜΟΝΟ τη γλώσσα: ορθογραφία, γραμματική, σύνταξη, στίξη, μεταφρασμένες ή αφύσικες συνάψεις, λάθος ή ελλείποντα άρθρα και κλιτικά (π.χ. «θα βρεις κλειστά» → «θα τα βρεις κλειστά»), τόνους. "
        "ΔΕΝ αλλάζεις νόημα, περιεχόμενο, αριθμούς, ονόματα, δομή, μήκος ή ύφος πέρα από το γλωσσικά αναγκαίο· δεν προσθέτεις ούτε αφαιρείς προτάσεις· δεν κρίνεις την ορθότητα των πληροφοριών. Αφαιρούνται ΜΟΝΟ οι τυποποιημένες μανιέρες «Ελπίζω να βοήθησα», «Αν χρειαστείς κάτι άλλο…», «Μη διστάσεις…», «Φυσικά!» αν υπάρχουν. "
        "{kind_rules}\nΚρίνεις ΚΑΘΕ απάντηση του βοηθού και επιστρέφεις όλες τις απαντήσεις με τη σειρά, διορθωμένες όπου χρειάζεται και ΑΥΤΟΥΣΙΕΣ όπου όχι (verdict ok).\n\n")
KIND = {'if': "ΠΡΟΣΟΧΗ: κάθε γραμμή έχει ΟΔΗΓΙΕΣ ΜΟΡΦΗΣ που ο χρήστης έδωσε (λίστα «ΠΕΡΙΟΡΙΣΜΟΙ»). Ό,τι διέπουν οι περιορισμοί ΔΕΝ το αγγίζεις: πλήθος λέξεων/προτάσεων/παραγράφων/κουκκίδων, τίτλους, ετικέτες, λέξεις-κλειδιά και τη συχνότητά τους, γράμματα-στόχους, γραφή χωρίς τόνους ή σε greeklish ή με κεφαλαία, στίξη που απαγορεύεται ή απαιτείται, φράσεις αρχής/τέλους, εισαγωγικά, JSON. Αν η απάντηση είναι ατονική ή greeklish ή κεφαλαία επειδή το ζήτησε ο χρήστης, μένει έτσι.",
        'math': "ΠΡΟΣΟΧΗ: είναι λύσεις μαθηματικών προβλημάτων. ΔΕΝ αλλάζεις κανέναν αριθμό, πράξη, σύμβολο, μονάδα ή την τελική απάντηση «Απάντηση: …»· δεν αλλάζεις τη μορφή αριθμών (δεκαδικό κόμμα, τελεία χιλιάδων, «€» μετά τον αριθμό). Διορθώνεις μόνο το ελληνικό κείμενο γύρω τους."}
SCHEMA = M.write_schema('s_edit.json', {"type": "object", "properties": {"rows": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "verdict": {"type": "string"}, "edited_assistant_turns": {"type": "array", "items": {"type": "string"}}, "changes": {"type": "array", "items": {"type": "string"}}, "greekness": {"type": "integer"}}, "required": ["id", "verdict", "edited_assistant_turns", "changes", "greekness"], "additionalProperties": False}}}, "required": ["rows"], "additionalProperties": False})
lock = threading.Lock()


def turns_of(r): return r.get('turns') or [dict(role='user', content=r['user']), dict(role='assistant', content=r['assistant'])]


def render(batch, kind):
    parts = []
    for r in batch:
        conv = '\n\n'.join(f"[{m['role'].upper()}]{' (ΠΛΑΙΣΙΟ: μην το αλλάξεις, επίστρεψέ το αυτούσιο)' if m.get('train') is False else ''}\n{m['content']}" for m in turns_of(r))
        cons = ('ΠΕΡΙΟΡΙΣΜΟΙ: ' + ' | '.join(c['text'] for c in r['meta']['constraints']) + '\n') if kind == 'if' and r.get('meta', {}).get('constraints') else ''
        parts.append(f"===== ROW {r['id']} =====\n{cons}ΣΥΝΟΜΙΛΙΑ:\n{conv}")
    return HEAD.format(kind_rules=KIND[kind]) + GAMMA + f"\n\nΚρίνεις {len(batch)} γραμμές, χωριστά (===== ROW <id> =====). Επίστρεψε ΜΟΝΟ JSON {{\"rows\":[{{\"id\",\"verdict\": ok|edited,\"edited_assistant_turns\":[όλες οι απαντήσεις του βοηθού με τη σειρά],\"changes\":[\"πριν → μετά, γιατί\"],\"greekness\":1-5}}]}} με ακριβώς τα {len(batch)} ids.\n\n" + '\n\n'.join(parts)


def guard(r, new_turns, kind):
    """Keep the edit only if it breaks nothing the row is verified on. Returns (accept, reason)."""
    if kind == 'if':
        if not r.get('meta', {}).get('constraints'): return True, ''   # conversation-skills rows carry no constraint list: language edits accepted (their mechanical checks ran at generation)
        res = C.check_all(new_turns[-1], r['meta']['constraints'], r['user'])
        bad = [x['family'] for x in res if x['ok'] is False]
        return (not bad, 'constraints broken: ' + ','.join(bad) if bad else '')
    if kind == 'math':
        old, new = M.final_answer(r['assistant']), M.final_answer(new_turns[-1])
        return (M.equiv(old, new) or (not old and not new), '' if M.equiv(old, new) else f'final answer changed {old!r} → {new!r}')
    return True, ''


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rows'); ap.add_argument('out'); ap.add_argument('--kind', required=True, choices=['if', 'math']); ap.add_argument('--model', default='gpt-5.6-sol'); ap.add_argument('--effort', default='medium'); ap.add_argument('--workers', type=int, default=int(os.environ.get('WORKERS', '24'))); ap.add_argument('--batch', type=int, default=int(os.environ.get('BATCH', '15')), help='rows per editor call; 15 halves the per-call overhead that dominates the Codex window')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); checks_path = f'{a.out}/checks.jsonl'
    rows = [json.loads(l) for l in open(a.rows)]; have = {json.loads(l)['id'] for l in open(checks_path)} if os.path.exists(checks_path) else set(); todo = [r for r in rows if r['id'] not in have]
    print(len(rows), 'rows,', len(todo), 'to edit with', a.model, a.effort, a.workers, 'workers', flush=True)
    def batch(b):
        for t in range(3):
            try:
                j = M.codex_json(render(b, a.kind), SCHEMA, a.model, a.effort, timeout=1500); got = {x['id']: x for x in j['rows']}
                if set(got) != {r['id'] for r in b}: raise ValueError('id mismatch')
                with lock, open(checks_path, 'a') as f:
                    for r in b: f.write(json.dumps(dict(id=r['id'], **{k: got[r['id']][k] for k in ('verdict', 'edited_assistant_turns', 'changes', 'greekness')}, editor=a.model), ensure_ascii=False) + '\n')
                return
            except Exception as e: print('retry', t, type(e).__name__, str(e)[:100], flush=True)
    with ThreadPoolExecutor(a.workers) as pool: list(pool.map(batch, [todo[i:i + a.batch] for i in range(0, len(todo), a.batch)]))
    checks = {json.loads(l)['id']: json.loads(l) for l in open(checks_path)}; stats = collections.Counter(); out_rows = []
    for r in rows:
        c = checks.get(r['id']); rr = dict(r)
        if not c: stats['unedited_missing'] += 1
        elif c['verdict'] == 'edited' and len(c['edited_assistant_turns']) == sum(1 for m in turns_of(r) if m['role'] == 'assistant'):
            new = c['edited_assistant_turns']; ok, why = guard(r, new, a.kind)
            if ok:
                k = 0; turns = []
                for m in turns_of(r):
                    if m['role'] == 'assistant': turns.append(dict(m, content=(m['content'] if m.get('train') is False else new[k]))); k += 1   # keep extra keys (train flag); context-only turns (train=False, e.g. planted tics) are never edited
                    else: turns.append(m)
                rr['turns'] = turns; rr['assistant'] = turns[-1]['content']; rr['pre_edit_assistant'] = r['assistant']; rr['edited_by'] = a.model; rr['edit_changes'] = c['changes']; stats['edited'] += 1
            else: rr['edit_reverted'] = why; stats['reverted'] += 1
        else: stats['ok'] += 1
        rr['greekness'] = (c or {}).get('greekness'); out_rows.append(rr)
    with open(f'{a.out}/rows_edited.jsonl', 'w') as f:
        for r in out_rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    g = [r['greekness'] for r in out_rows if r.get('greekness')]
    summ = dict(rows=len(rows), **stats, mean_greekness=round(sum(g) / max(1, len(g)), 2), editor=a.model); json.dump(summ, open(f'{a.out}/summary.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))


if __name__ == '__main__': main()
