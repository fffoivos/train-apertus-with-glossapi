#!/usr/bin/env python3
"""Build and check a bounded, non-promoted 20-row Greek IF repair pilot."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

PROJECT = Path("/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments")
SOURCE = PROJECT / "data/greek_if/final/greek_if_sft.jsonl"
CHECKER = PROJECT / "data/greek_if/constraints.py"
COMPONENTS = {
    "v1v2_edited": PROJECT / "data/greek_if/v1v2/edited/rows_edited.jsonl",
    "v3_edited": PROJECT / "data/greek_if/v3/edited/rows_edited.jsonl",
}
OUT = Path(__file__).resolve().parent

IDS = [
    "mixa_2026_06155", "mixa_2028_05110", "mixa_2028_03200", "mixa_2028_08593",
    "mixa_2027_09179", "mixa_2026_08572", "mixa_2027_09553", "mixa_2027_09689",
    "mixa_2027_10080", "mixa_2026_04027", "mixa_2026_05543", "mixa_2026_07006",
    "mixa_2027_05368", "mixa_2026_06199", "mixa_2026_04931", "mixa_2026_11688",
    "mixa_2026_08647", "mixa_2027_09233", "mixa_2027_07834", "mixa_2027_01564",
]

CLASS = {
    "mixa_2026_06155": "impossible_language_mechanic",
    "mixa_2028_05110": "contradictory_constraints",
    "mixa_2028_03200": "exact_string_failure",
    "mixa_2028_08593": "contradictory_exact_end_and_wrapper",
    "mixa_2027_09179": "semantic_source_fidelity_failure",
    "mixa_2026_08572": "translation_padding_source_fidelity_failure",
    "mixa_2027_09553": "summary_padding_source_fidelity_failure",
    "mixa_2027_09689": "semantic_task_failure_from_format_constraint",
    "mixa_2027_10080": "checker_false_positive_orthography",
    "mixa_2026_04027": "irrelevant_constraint_padding",
    "mixa_2026_05543": "unresolved_exact_word_protocol",
    "mixa_2026_07006": "valid_control_complex",
    "mixa_2027_05368": "valid_control_monotonic",
    "mixa_2026_06199": "valid_control_highlight",
    "mixa_2026_04931": "valid_control_paragraph_start",
    "mixa_2026_11688": "valid_control_multi_constraint",
    "mixa_2026_08647": "valid_control_exact_start_wrapper",
    "mixa_2027_09233": "valid_control_lowercase",
    "mixa_2027_07834": "valid_control_placeholders_question_mark",
    "mixa_2027_01564": "valid_control_title_date_end",
}

spec = importlib.util.spec_from_file_location("wave2_greek_if_constraints", CHECKER)
C = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(C)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_constraint(row: dict, family: str, *, params: dict | None = None, text: str | None = None, new_family: str | None = None) -> None:
    for c in row["meta"]["constraints"]:
        if c["family"] == family:
            if new_family is not None:
                c["family"] = new_family
            if params is not None:
                c["params"] = params
            if text is not None:
                c["text"] = text
            return
    raise KeyError((row["id"], family))


def set_messages(row: dict, *, user: str | None = None, assistant: str | None = None) -> None:
    if user is not None:
        row["user"] = user
        row["turns"][0]["content"] = user
    if assistant is not None:
        row["assistant"] = assistant
        row["turns"][-1]["content"] = assistant


def repaired(original: dict) -> tuple[str, dict | None, list[str], list[str], str, list[str], list[str]]:
    """Return status, candidate, changes, mappings, explanation, issues, checks_needed."""
    rid = original["id"]
    r = copy.deepcopy(original)
    changes: list[str] = []
    mappings: list[str] = []
    issues: list[str] = []
    checks_needed: list[str] = []

    if CLASS[rid].startswith("valid_control"):
        return ("candidate", r, ["No change; held as a negative repair control."],
                ["All original constraints map identically."],
                "The original already satisfies both the deterministic constraints and the substantive request.", [], [])

    if rid == "mixa_2026_06155":
        user = ("Ftiakse mou mia asteia efchi gia ta genethlia tis theias mou tis Elenis sto Toronto, "
                "me ena paixnidi me tin idea oti o xronos petaei pou na menei katalipto xoris tonous.\n\n"
                "Όλη η απάντηση ανάμεσα σε « και ». grapse oli tin apantisi atonika, xwriς kanenan tono.")
        answer = ("«θεια ελενη, στο τοροντο ο χρονος πεταει, μα εσυ του εχεις κλεισει θεση επιστροφης. "
                  "χρονια πολλα με γελια, τουρτα και ταξιδια που κανουν καθε χρονο να θελει να ξαναγυρισει»")
        set_messages(r, user=user, assistant=answer)
        changes = ["Reauthored the requested joke so its mechanism remains intelligible without accents.", "Replaced the response with a concise atonic joke inside Greek quotation marks."]
        mappings = ["no_accents retained exactly", "wrap_in_quotes retained exactly", "accent-dependent πότε/ποτέ contrast replaced by accent-independent time-flight/return wordplay"]
        explanation = "The original specification destroys the very tonos contrast the joke is meant to exhibit. Source-level reauthoring preserves the creative and no-accent skills without pretending the contrast survives."
    elif rid == "mixa_2028_05110":
        user = original["user"].replace("Καλή συνέχεια.", "Μείνε ασφαλής.")
        answer = ("1. Μην αποκαλύπτεις κωδικούς, PIN, στοιχεία κάρτας ή κωδικούς μιας χρήσης σε τηλεφωνική κλήση.\n"
                  "2. Αν κάποιος λέει ότι τηλεφωνεί από τράπεζα ή υπηρεσία, κλείσε και χρησιμοποίησε εσύ τον επίσημο αριθμό.\n"
                  "3. Μην εγκαθιστάς εφαρμογές απομακρυσμένης πρόσβασης και μην ανοίγεις συνδέσμους που στέλνονται κατά την κλήση.\n"
                  "4. Πρόσεχε την πίεση για άμεση ενέργεια, τις απειλές και τις υποσχέσεις χρημάτων.\n"
                  "5. Αν έχεις ήδη δώσει στοιχεία, επικοινώνησε αμέσως με την τράπεζά σου και άλλαξε τους σχετικούς κωδικούς.\n\n"
                  "Μείνε ασφαλής.")
        set_messages(r, user=user, assistant=answer)
        replace_constraint(r, "end_with", params={"s": "Μείνε ασφαλής."}, text="Η τελευταία φράση να είναι «Μείνε ασφαλής.»." )
        changes = ["Changed the mandatory ending from a derivative of καλός to Μείνε ασφαλής.", "Removed the obsolete contradiction preface from the response."]
        mappings = ["end_with retained with a nonconflicting target", "keywords_exclude καλός retained"]
        explanation = "The original ending and ban cannot both be followed. The new ending preserves an exact-end constraint and the safety topic without weakening the forbidden-word task."
    elif rid == "mixa_2028_03200":
        answer = original["assistant"][:-len("Καλή συνέχεια.")] + "Καλη συνεχεια."
        set_messages(r, assistant=answer)
        replace_constraint(r, "end_with", params={"s": "Καλη συνεχεια."}, text="Κλείσε ακριβώς με τη φράση «Καλη συνεχεια.»." )
        changes = ["Restored the accentless ending literally requested by the surfaced user and aligned metadata to the same bytes."]
        mappings = ["informal_singular retained", "end_with changed from accent-folded lexical matching to the displayed exact surface target"]
        explanation = "The original checker passes an accented ending after accent folding, but the user explicitly asks for the accentless byte string."
    elif rid == "mixa_2028_08593":
        first, rest = original["user"].split("\n\n", 1)
        first = ("Η τελευταία φράση μέσα στα εξωτερικά εισαγωγικά να είναι ακριβώς «Καλή συνέχεια.». "
                 "Μετά από αυτή τη φράση να υπάρχει μόνο το κλείσιμο των εξωτερικών εισαγωγικών και κανένα άλλο κείμενο. "
                 "Βάλε ολόκληρη την απάντηση μέσα σε ελληνικά εισαγωγικά «…». Ακριβώς 3 παράγραφοι, "
                 "χωρισμένες μεταξύ τους με ***. Αρίθμησε τα σημεία με ελληνικά γράμματα: α΄, β΄, γ΄ κ.ο.κ.")
        set_messages(r, user=first + "\n\n" + rest)
        replace_constraint(r, "end_with", text="Η τελευταία φράση μέσα στα εξωτερικά εισαγωγικά να είναι «Καλή συνέχεια.»· μετά επιτρέπεται μόνο το κλείσιμο των εισαγωγικών.")
        changes = ["Reauthored the exact-end instruction to permit only the mandatory closing quotation mark after the phrase."]
        mappings = ["length_paragraphs, wrap_in_quotes, numbered_greek retained", "end_with interpreted as final phrase inside the wrapper"]
        explanation = "The original whole-output requirements were literally incompatible. The candidate keeps both skills and explicitly orders their boundary characters."
    elif rid == "mixa_2027_09179":
        user = original["user"].replace("τουλάχιστον 6 φορές", "τουλάχιστον 3 φορές")
        answer = ("Σύνοψη: Μετά από τροχαίο το 2022, το πρόσωπο αναφέρει *χρόνιο πόνο στον αυχένα και στο αριστερό χέρι*. "
                  "Ως τον Ιανουάριο συνέχιζε την *απασχόλησή του με συχνά διαλείμματα*. Μετά την αλλαγή προϊσταμένου, "
                  "του ζητήθηκαν καθημερινή ύψωση κιβωτίων και ορθοστασία, παρότι γνωμάτευση *φυσιάτρου προτείνει "
                  "αποφυγή άρσης βάρους και εναλλαγή στάσης*. Η εταιρεία επιβεβαίωσε τη λήψη της γνωμάτευσης αλλά "
                  "δεν απάντησε στο αίτημα προσαρμογής. Έκτοτε το πρόσωπο έλαβε δύο αναρρωτικές άδειες και εκφράζει φόβο απόλυσης.")
        set_messages(r, user=user, assistant=answer)
        replace_constraint(r, "letter_freq", params={"l": "ψ", "n": 3}, text="Χρησιμοποίησε το γράμμα «ψ» τουλάχιστον 3 φορές συνολικά.")
        changes = ["Removed the unsupported gender, the previously added mental-state claims, and speculation; retained only facts supplied by the note.", "Reduced ψ frequency from 6 to 3 so the lexical constraint can be met without semantic padding."]
        mappings = ["three highlights retained", "letter-frequency skill retained at a source-faithful level"]
        explanation = "The old guard restored unsupported claims to protect ψ frequency. A small source-level frequency change lets the semantic repair and surface constraints coexist."
    elif rid == "mixa_2026_08572":
        user = original["user"].replace("τουλάχιστον 300 λέξεις", "τουλάχιστον 50 λέξεις")
        answer = ("Αγαπητέ φίλε,\n\n“I am a taxi driver in Thessaloniki, and for the past two years I have been photographing "
                  "the city’s nighttime journeys. Together with two young photographers, we would like to organize an exhibition "
                  "at Warehouse C. We are seeking a grant of €7,500 for printing, lighting, and transporting the works. Your festival "
                  "could participate as an international partner and later host part of the exhibition.”")
        set_messages(r, user=user, assistant=answer)
        replace_constraint(r, "length_words_min", params={"n": 50}, text="Η απάντηση να έχει τουλάχιστον 50 λέξεις.")
        changes = ["Reduced the minimum from 300 to 50 words at source level.", "Kept one faithful translation instead of four expanded versions."]
        mappings = ["start_with retained exactly", "minimum-length skill retained at a bound compatible with a faithful translation"]
        explanation = "The 300-word minimum forces expansion beyond the short source. A lower bound retains measurable length following without licensing invented project details."
    elif rid == "mixa_2027_09553":
        user = original["user"].replace("τουλάχιστον 8 φορές", "τουλάχιστον 4 φορές").replace("Η απάντηση να έχει τουλάχιστον 300 λέξεις.", "Η απάντηση να μην ξεπερνά τις 120 λέξεις.")
        answer = ("Σύνοψη για τους γονείς: Κάθε μαθητής χρειάζεται τη δική του Ευρωπαϊκή Κάρτα Ασφάλισης Ασθενείας. "
                  "Κατά την προσωρινή διαμονή στη Μαδρίτη, η κάρτα δίνει πρόσβαση σε ιατρικά αναγκαία περίθαλψη με τους "
                  "όρους του δημόσιου συστήματος της Ισπανίας. Δεν αντικαθιστά την ταξιδιωτική ασφάλιση, δεν καλύπτει ιδιωτική "
                  "περίθαλψη και δεν ισχύει για ταξίδι που γίνεται ειδικά για θεραπεία. Αν η κάρτα δεν εκδοθεί εγκαίρως, μπορεί "
                  "να ζητηθεί Πιστοποιητικό Προσωρινής Αντικατάστασης. Συνοψίζοντας, ελέγξτε πριν από το ταξίδι ότι και οι δύο "
                  "μαθητές έχουν δικό τους έγκυρο έγγραφο.")
        set_messages(r, user=user, assistant=answer)
        replace_constraint(r, "letter_freq", params={"l": "ψ", "n": 4}, text="Χρησιμοποίησε το γράμμα «ψ» τουλάχιστον 4 φορές συνολικά.")
        replace_constraint(r, "length_words_min", new_family="length_words_max", params={"n": 120}, text="Η απάντηση να μην ξεπερνά τις 120 λέξεις.")
        changes = ["Changed the anti-summary 300-word minimum to a 120-word maximum.", "Reduced ψ frequency from 8 to 4 and wrote a source-faithful summary."]
        mappings = ["word-count instruction preserved but direction changed to match summarization", "letter-frequency skill retained at a naturally satisfiable level"]
        explanation = "The original constraints reward padding and unsupported advice. The candidate makes concision part of the measurable task and retains a bounded letter constraint."
    elif rid == "mixa_2027_09689":
        user = original["user"].replace("Μία λέξη μόνο: Ναι, Όχι ή Ίσως.", "Απάντησε σε 3 ακριβώς προτάσεις, ώστε να δώσεις και την επιλογή σου και τους λόγους.")
        answer = ("ΘΑ ΕΠΙΚΟΙΝΩΝΟΥΜΟΥΝ ΠΡΩΤΑ ΜΕ ΜΙΑ ΔΗΜΟΣΙΑ ΔΟΜΗ Ή ΜΕ ΤΟΝ ΦΟΡΕΑ ΤΗΣ ΕΥΡΩΠΑΪΚΗΣ ΚΑΡΤΑΣ ΓΙΑ ΝΑ ΜΑΘΩ ΠΟΥ ΜΠΟΡΩ ΝΑ ΕΞΕΤΑΣΤΩ ΣΤΑ ΧΑΝΙΑ. "
                  "ΑΝ Ο ΠΟΝΟΣ ΕΙΝΑΙ ΕΝΤΟΝΟΣ Ή ΥΠΑΡΧΕΙ ΠΡΗΞΙΜΟ ΠΥΡΕΤΟΣ Ή ΔΥΣΚΟΛΙΑ ΣΤΗΝ ΚΑΤΑΠΟΣΗ ΘΑ ΖΗΤΟΥΣΑ ΑΜΕΣΑ ΟΔΟΝΤΙΑΤΡΙΚΗ ΦΡΟΝΤΙΔΑ ΧΩΡΙΣ ΝΑ ΠΕΡΙΜΕΝΩ. "
                  "Η ΔΗΜΟΣΙΑ ΕΠΙΛΟΓΗ ΜΠΟΡΕΙ ΝΑ ΜΕΙΩΣΕΙ ΤΟ ΚΟΣΤΟΣ ΕΝΩ Η ΙΔΙΩΤΙΚΗ ΚΛΙΝΙΚΗ ΙΣΩΣ ΠΡΟΣΦΕΡΕΙ ΤΑΧΥΤΕΡΗ ΕΞΕΤΑΣΗ ΓΙ ΑΥΤΟ ΘΑ ΑΠΟΦΑΣΙΖΑ ΜΕ ΒΑΣΗ ΤΗΝ ΕΠΕΙΓΟΥΣΑ ΑΝΑΓΚΗ ΚΑΙ ΤΗ ΔΙΑΘΕΣΙΜΟΤΗΤΑ.")
        set_messages(r, user=user, assistant=answer)
        replace_constraint(r, "constrained_answer", new_family="length_sentences_exact", params={"n": 3}, text="Απάντησε σε 3 ακριβώς προτάσεις, ώστε να δώσεις και την επιλογή σου και τους λόγους.")
        changes = ["Replaced the one-word constraint with exactly three sentences.", "Added an uppercase conditional recommendation with reasons."]
        mappings = ["all_caps_greek retained", "format constraint changed from one word to three sentences so the requested reasoning remains possible"]
        explanation = "The original substantive task asks for a choice and reasons, which a one-word output cannot provide."
    elif rid == "mixa_2027_10080":
        answer = ("Ναι, κατά πάσα πιθανότητα αξίζει, γιατί η άνετη και ασφαλής εργασία του ταμία είναι σημαντικότερη από τη μικρή απώλεια χώρου πώλησης. "
                  "Ένα σταθερό σκαμπό με στήριξη, αρκετός χώρος για τα πόδια και φαρδύτερο πέρασμα μπορούν να μειώσουν την καταπόνηση του γόνατου και τον κίνδυνο πτώσης. "
                  "Αφαίρεσε κατά προτίμηση τη σειρά με τις χαμηλότερες πωλήσεις και μέτρησε για έναν μήνα αν επηρεάζεται ουσιαστικά ο τζίρος. "
                  "Ζήτησε και τη γνώμη του εργαζομένου για το ύψος και τη θέση του σκαμπό, χωρίς να θεωρήσεις ότι αυτό υποκαθιστά τις οδηγίες του γιατρού του.")
        set_messages(r, assistant=answer)
        changes = ["Restored ordinary monotonic accents throughout the response."]
        mappings = ["monotonic_only interpreted as standard modern monotonic Greek, not merely absence of polytonic marks"]
        explanation = "The original passes the current checker because the checker only rejects polytonic marks, but accentless prose is not ordinary monotonic orthography."
        issues = ["The current deterministic checker passes both original and repaired text; semantic orthography review is still required until the protocol is strengthened."]
    elif rid == "mixa_2026_04027":
        user = original["user"].replace("ΕΟΠΥΥ", "ΚΤΕΛ Λάρισας")
        answer = original["assistant"].replace("Κι ο ΕΟΠΥΥ ας περιμένει γιατί αγκαλιάζονται τώρα", "Κι από το ΚΤΕΛ Λάρισας γυρίζει στο χωριό του")
        set_messages(r, user=user, assistant=answer)
        replace_constraint(r, "mention_entity", params={"e": "ΚΤΕΛ Λάρισας"}, text="Πρέπει να αναφέρεις «ΚΤΕΛ Λάρισας».")
        changes = ["Reauthored the required entity from unrelated ΕΟΠΥΥ to task-relevant ΚΤΕΛ Λάρισας.", "Replaced the padding line with a travel-continuity line."]
        mappings = ["mention_entity retained with domain-relevant entity", "all four other constraints retained"]
        explanation = "The original checker pass is bought by inserting an irrelevant health-insurance entity into a travel song."
    elif rid == "mixa_2026_05543":
        options = [
            "Surface-exact protocol: require two byte-identical occurrences of επιλογη; the current accented response fails and mixed atonic/monotonic repair is unnatural.",
            "Lexical-identity protocol: normalize accents for the word requirement and change the displayed target to επιλογή; the current response is valid but the task no longer measures exact orthography.",
        ]
        return ("blocked", None, ["No candidate selected because the displayed atonic target and accent-folding checker encode different tasks."],
                options, "A versioned protocol decision is required before repair; neither option may be silently inferred from the current checker pass.",
                ["Exact-string versus accent-insensitive lexical identity is unresolved."],
                ["Choose a protocol option and re-run its explicit positive/negative controls."])
    else:
        raise AssertionError(rid)

    return "candidate", r, changes, mappings, explanation, issues, checks_needed


raw_lines = SOURCE.read_bytes().splitlines()
source_file_hash = sha256_bytes(SOURCE.read_bytes())
checker_hash = sha256_bytes(CHECKER.read_bytes())
located: dict[str, tuple[int, bytes, dict]] = {}
for line_no, raw in enumerate(raw_lines, 1):
    row = json.loads(raw)
    if row.get("id") in IDS:
        located[row["id"]] = (line_no, raw, row)
assert set(located) == set(IDS)

component_located: dict[str, dict] = {}
for component_name, component_path in COMPONENTS.items():
    component_bytes = component_path.read_bytes()
    component_hash = sha256_bytes(component_bytes)
    for line_no, raw in enumerate(component_bytes.splitlines(), 1):
        row = json.loads(raw)
        if row.get("id") in IDS:
            assert row["id"] not in component_located
            component_located[row["id"]] = {
                "name": component_name, "path": str(component_path), "line_number": line_no,
                "file_sha256": component_hash, "raw_row_sha256": sha256_bytes(raw),
            }
assert set(component_located) == set(IDS)

records = []
checks = []
for rid in IDS:
    line_no, raw, original = located[rid]
    status, candidate, changes, mappings, explanation, issues, checks_needed = repaired(original)
    original_checks = C.check_all(original["assistant"], original["meta"]["constraints"], original["user"])
    candidate_checks = None if candidate is None else C.check_all(candidate["assistant"], candidate["meta"]["constraints"], candidate["user"])
    candidate_json = None if candidate is None else json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    semantic_original = True if CLASS[rid].startswith("valid_control") else (None if rid == "mixa_2026_05543" else False)
    semantic_candidate = None if candidate is None else True
    rec = {
        "row_id": rid,
        "status": status,
        "selection_class": CLASS[rid],
        "source_identity": {
            "path": str(SOURCE), "line_number": line_no, "file_sha256": source_file_hash,
            "raw_row_sha256": sha256_bytes(raw),
            "version": original.get("version") or ("v3" if component_located[rid]["name"] == "v3_edited" else None),
            "edited_component": component_located[rid],
        },
        "original_row": original,
        "candidate_row": candidate,
        "candidate_row_sha256": None if candidate_json is None else sha256_bytes(candidate_json),
        "preserved_invariants": [
            "substantive domain and requested skill", "facts supplied by the user", "role order and turn count",
            "unmodified constraints except those explicitly mapped", "no benchmark-row content introduced",
        ],
        "constraint_mapping": mappings,
        "expected_result": "blocked_pending_protocol" if candidate is None else "canonical_checkers_pass_and_semantic_task_preserved",
        "explanation": explanation,
        "checks_needed": checks_needed,
        "changes": changes,
        "issues": issues,
        "checker_execution": {
            "module_path": str(CHECKER), "module_sha256": checker_hash,
            "original": original_checks, "candidate": candidate_checks,
            "original_all_checkable_pass": all(x["ok"] is not False for x in original_checks),
            "candidate_all_checkable_pass": None if candidate_checks is None else all(x["ok"] is not False for x in candidate_checks),
        },
        "semantic_read": {
            "original_task_adequate": semantic_original,
            "candidate_task_adequate": semantic_candidate,
            "basis": "full request-response read beyond substring/count checker",
        },
    }
    records.append(rec)
    checks.append({k: rec[k] for k in ("row_id", "status", "selection_class", "source_identity", "candidate_row_sha256", "checker_execution", "semantic_read", "issues")})

candidates_path = OUT / "candidates.jsonl"
checks_path = OUT / "checker_results.json"
candidates_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
checks_path.write_text(json.dumps({
    "source_file_sha256": source_file_hash,
    "checker_sha256": checker_hash,
    "records": checks,
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
manifest = {
    "selection": "10 established semantic/specification defects, 1 unresolved exact-word protocol, 9 valid controls",
    "not_a_prevalence_sample": True,
    "records": [{
        "row_id": r["row_id"], "selection_class": r["selection_class"], "status": r["status"],
        "source_identity": r["source_identity"], "candidate_row_sha256": r["candidate_row_sha256"],
    } for r in records],
    "artifacts": {
        "candidates.jsonl": sha256_bytes(candidates_path.read_bytes()),
        "checker_results.json": sha256_bytes(checks_path.read_bytes()),
    },
}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "records": len(records),
    "candidate": sum(r["status"] == "candidate" for r in records),
    "blocked": sum(r["status"] == "blocked" for r in records),
    "original_checker_pass": sum(r["checker_execution"]["original_all_checkable_pass"] for r in records),
    "candidate_checker_pass": sum(r["checker_execution"]["candidate_all_checkable_pass"] is True for r in records),
    "semantic_original_adequate": sum(r["semantic_read"]["original_task_adequate"] is True for r in records),
    "semantic_candidate_adequate": sum(r["semantic_read"]["candidate_task_adequate"] is True for r in records),
}, ensure_ascii=False, indent=2))
