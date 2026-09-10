#!/usr/bin/env python3
"""MATH-500 → Greek: Sol translates the problem prose; every LaTeX/math span and every number must survive byte-for-byte (programmatic check),
Greek school terminology, Arabic numerals kept (MGSM's design choice). Output math500/problems_el.jsonl. Usage: python3 translate.py [N]"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
SCHEMA = B.M.write_schema('s_m500.json', {"type": "object", "properties": {"problem_el": {"type": "string"}, "terms": {"type": "string"}, "issue": {"type": "string"}}, "required": ["problem_el", "terms", "issue"], "additionalProperties": False})
MATH = re.compile(r'(?<!\\)\$\$.*?(?<!\\)\$\$|(?<!\\)\$.*?(?<!\\)\$|\\\[.*?\\\]|\\\(.*?\\\)|\\begin\{.*?\}.*?\\end\{.*?\}', re.S)   # backslash-aware: \$ is an escaped dollar, not a delimiter (the 2026-09-10 cross-check found 11 rows corrupted by the naive scanner)
TEXT = re.compile(r'\\text(?:bf|it|rm)?\{[^{}]*\}')


def span_skeletons(s): return [TEXT.sub('\\text{…}', x) for x in MATH.findall(s)]   # \text{} prose is language and is translated; everything else must be identical


def spans(s): return MATH.findall(s)
def numbers(s): return re.findall(r'\d+(?:[.,]\d+)?', MATH.sub(' ', s))


def translate(r):
    prompt = (B.RULES_EL + "\n\nΕιδικά για ΜΑΘΗΜΑΤΙΚΑ προβλήματα: κάθε τμήμα LaTeX ($...$, $$...$$, \\[...\\], \\begin...\\end) και κάθε αριθμός μένουν ΑΚΡΙΒΩΣ όπως είναι, χαρακτήρα προς χαρακτήρα (μαζί με κάθε ανάστροφη κάθετο «\\», π.χ. \\$ για το δολάριο)· "
              "ΕΞΑΙΡΕΣΗ: το πεζό κείμενο μέσα σε \\text{...}, \\textbf{...} και οι επικεφαλίδες πινάκων (tabular) είναι γλώσσα και ΜΕΤΑΦΡΑΖΟΝΤΑΙ (π.χ. \\text{and} → \\text{και}, \\textbf{odd} → \\textbf{περιττός}). Μεταφράζεις την πεζή γλώσσα γύρω από τα μαθηματικά. Τακτικοί αριθμοί στα ελληνικά: 2003rd → 2003ος, $n^{\\text{th}}$ → $n$-οστός, $100^{\\mathrm{th}}$ → $100$ός. «Express your answer as a common fraction» → πάντα «Εκφράστε την απάντησή σας ως κοινό κλάσμα». «modulo n» → «ισοϋπόλοιπο … modulo n» ή «το υπόλοιπο της διαίρεσης με το n» (ποτέ «ισότιμο»). Το ελληνικό ερωτηματικό «;» μπαίνει ΕΞΩ από το τμήμα LaTeX. Επινοημένες μονάδες (daps, treeks) μεταγράφονται στα ελληνικά (νταπ, τρικ). Ορολογία σχολικού βιβλίου (π.χ. ρίζες πολυωνύμου, κοινή διαφορά αριθμητικής προόδου, ΕΚΠ/ΜΚΔ, εμβαδόν, περίμετρος, κλάσμα σε ανάγωγη μορφή, «Εκφράστε την απάντησή σας ως…»). "
              "Δεκαδικοί μέσα σε LaTeX μένουν με τελεία· στην πεζή γλώσσα αριθμοί επίσης όπως στο πρωτότυπο. Στο terms γράψε τις ορολογικές επιλογές σου (αγγλικός όρος → ελληνικός), στο issue ό,τι δεν μεταφέρεται καθαρά (λογοπαίγνιο, αγγλική λέξη ως αντικείμενο του προβλήματος) ή κενό.\n\n"
              f"Πρόβλημα (id {r['unique_id']}, θέμα {r['subject']}, επίπεδο {r['level']}):\n{r['problem']}\n\nΕπίστρεψε JSON {{\"problem_el\",\"terms\",\"issue\"}}.")
    j = B.sol_json(prompt, SCHEMA, effort='medium', timeout=600)
    if not j: return None
    el = j['problem_el']; ok_math = span_skeletons(el) == span_skeletons(r['problem']); ok_num = sorted(numbers(el)) == sorted(numbers(r['problem']))
    return dict(id=r['unique_id'], problem_en=r['problem'], problem_el=el, answer=r['answer'], solution_en=r['solution'], subject=r['subject'], level=r['level'], terms=j['terms'], issue=j['issue'],
                check_math_spans=ok_math, check_numbers=ok_num, greek_share=round(len(re.findall(r'[Ά-ώ]', MATH.sub('', el))) / max(1, len(re.findall(r'[A-Za-zΆ-ώ]', MATH.sub('', el)))), 3))


if __name__ == '__main__':
    rows = B.load(os.path.join(HERE, 'source', 'test.jsonl')); n = int(sys.argv[1]) if len(sys.argv) > 1 else len(rows)
    for r in rows: r['id'] = r['unique_id']
    out = B.run_jobs(rows[:n], translate, os.path.join(HERE, 'problems_el.jsonl'), stage='math500 translate')
    allr = B.load(os.path.join(HERE, 'problems_el.jsonl')); print('rows', len(allr), 'math spans ok', sum(r['check_math_spans'] for r in allr), 'numbers ok', sum(r['check_numbers'] for r in allr), 'issues', sum(bool(r['issue']) for r in allr))
