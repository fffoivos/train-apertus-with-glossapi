#!/usr/bin/env python3
"""Build six immutable adapted-core repair candidates and deterministic checks."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
CORE = PARENT / "initial42_review_material.jsonl"
UNPAIRED = PARENT / "unpaired_es_pt_it_coverage9.jsonl"


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def record_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_line(path: Path, target: int) -> dict:
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if line_no == target:
                return json.loads(raw)
    raise IndexError(f"missing line {target} in {path}")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


core_rows = read_rows(CORE)
unpaired_rows = read_rows(UNPAIRED)
core_by_id = {row["row_id"]: (line, row) for line, row in enumerate(core_rows, 1)}
unpaired_by_id = {row["id"]: (line, row) for line, row in enumerate(unpaired_rows, 1)}


personas_before = core_by_id["personas_if_37ae2fa7"][1]["review_material"]["corrected"]
personas_after = [
    {
        "role": "user",
        "content": "Συντάξτε ένα email που θα μπορούσα να στείλω στην ομάδα τεχνολόγων χειρουργείου για να ζητήσω σχόλια σχετικά με τα χειρουργικά εργαλεία που χρησιμοποιούμε. Συμπεριλάβετε ακριβώς τρία πεδία προς συμπλήρωση για συγκεκριμένα εργαλεία και ζητήστε προτάσεις για εργονομικές βελτιώσεις. Χρησιμοποιήστε ολοκεφαλικές λέξεις για έμφαση το πολύ μία φορά ανά παράγραφο. Στο τέλος προσθέστε υστερόγραφο που να αρχίζει με P.S.",
    },
    {
        "role": "assistant",
        "content": "Θέμα: Σχόλια για τα χειρουργικά εργαλεία που χρησιμοποιούμε\n\nΑγαπητή ομάδα,\n\nΘα ήθελα τη γνώμη σας για τη λειτουργικότητα και την άνεση των εργαλείων που χρησιμοποιούμε καθημερινά στο χειρουργείο. Η εμπειρία σας μπορεί να αναδείξει πρακτικά προβλήματα που δεν φαίνονται εκτός αίθουσας.\n\nΠαρακαλώ σχολιάστε τα εξής:\n\n1. [όνομα εργαλείου 1]\n2. [όνομα εργαλείου 2]\n3. [όνομα εργαλείου 3]\n\nΑναφέρετε δυσκολίες στη λαβή, στο βάρος ή στον χειρισμό και προτείνετε αλλαγές που θα έκαναν τα εργαλεία πιο ΕΡΓΟΝΟΜΙΚΑ και ασφαλή. Συγκεκριμένα παραδείγματα από τη χρήση τους θα είναι ιδιαίτερα χρήσιμα.\n\nΣας ευχαριστώ για τον χρόνο και τη συμβολή σας.\n\nΜε εκτίμηση,\n\nP.S. Τα σχόλιά σας θα καθοδηγήσουν τις επόμενες αποφάσεις μας για τον εξοπλισμό και το εργασιακό περιβάλλον.",
    },
]

english_id = "393a7e8ef70f7bc806f1d5c7c2b45475888e5dbc16cc46f57b48bff9c173c816"
english_before = core_by_id[english_id][1]["review_material"]["corrected"]
english_after = [
    english_before[0],
    {
        "role": "assistant",
        "content": "On Monday, May 1, a 48-year-old man was arriving at work when he saw someone leaving the property with a stolen catalytic converter. The accused thief, who was 32, ran to his truck, and the 48-year-old got back into his vehicle. The two vehicles collided. While the younger man was trying to escape, the 48-year-old man shot him several times. The accused thief was rushed to the hospital with life-threatening injuries and the 48-year-old man was arrested on a charge of aggravated assault with a deadly weapon.",
    },
]

es20461_before = unpaired_by_id["20461"][1]["review_material"]["retained_messages"]
es20461_after = [
    es20461_before[0],
    {
        "role": "assistant",
        "content": "La palabra «varianza» puede referirse a cantidades distintas en una regresión lineal, y conviene separarlas.\n\nPrimero está la dispersión del predictor. En una regresión lineal simple, condicionada a los valores observados de X, la varianza del estimador de la pendiente es\n\n\\[\n\\operatorname{Var}(\\hat\\beta_1\\mid X)=\\frac{\\sigma^2}{\\sum_i (x_i-\\bar x)^2}.\n\\]\n\nSi el tamaño muestral y el ruido se mantienen fijos, una mayor dispersión de X aporta más información sobre la pendiente y reduce esa varianza; poca variación en X hace más difícil estimarla. Por tanto, una alta varianza de los datos de entrada no causa por sí sola sobreajuste.\n\nOtra cantidad es la varianza del error, \\(\\sigma^2=\\operatorname{Var}(\\varepsilon\\mid X)\\). Un ruido mayor aumenta la incertidumbre de los coeficientes y de las predicciones. La varianza residual de la muestra estima ese ruido bajo los supuestos del modelo, pero un residuo pequeño en entrenamiento no garantiza buen rendimiento fuera de la muestra.\n\nTambién se habla de la varianza del modelo o del estimador: cuánto cambiarían los coeficientes y las predicciones si repitiéramos el muestreo. Esta sensibilidad depende, entre otras cosas, del ruido, del tamaño muestral, del diseño de X, de la colinealidad y de la flexibilidad del procedimiento. Los modelos muy flexibles pueden tener alta varianza y ajustar fluctuaciones del entrenamiento; la regularización puede reducirla a cambio de introducir sesgo.\n\nLa generalización debe evaluarse con datos de validación o prueba, o mediante validación cruzada. No puede inferirse únicamente de que los predictores estén muy o poco dispersos ni de que los residuos de entrenamiento sean pequeños.",
    },
]

es15571_before = unpaired_by_id["15571"][1]["review_material"]["retained_messages"]
old_story = es15571_before[1]["content"]
story_tail = old_story.split("\n\n", 1)[1]
new_first_paragraph = (
    "El viejo capitán Miguel moría en su cama, en el camarote de su barco, que flotaba a la deriva en medio del océano. "
    "Las olas acariciaban suavemente la quilla, mientras el viento susurraba historias antiguas a través de los mástiles. "
    "Rodeado de mapas desgastados y viejas fotografías que contaban una vida llena de aventuras y desafíos, Miguel, con los ojos cerrados y el rostro sereno, "
    "sentía que la vida se escapaba de su cuerpo como la arena de un reloj de arena a punto de vaciarse."
)
es15571_after = [es15571_before[0], {"role": "assistant", "content": new_first_paragraph + "\n\n" + story_tail}]

it49139_before = unpaired_by_id["49139"][1]["review_material"]["retained_messages"]
it_user = it49139_before[0]["content"].replace("Viene condotta uno studio", "Viene condotto uno studio", 1)
it49139_after = [
    {"role": "user", "content": it_user},
    {
        "role": "assistant",
        "content": "Per due campioni indipendenti, senza assumere che le varianze siano uguali, userei un test t di Welch a una coda. Le ipotesi sono\n\n\\[H_0:\\mu_B\\leq\\mu_A, \\qquad H_1:\\mu_B>\\mu_A.\\]\n\nLa statistica è\n\n\\[\nt=\\frac{\\bar X_B-\\bar X_A}{\\sqrt{s_A^2/n_A+s_B^2/n_B}}\n=\\frac{80-75}{\\sqrt{8^2/80+7^2/70}}\n=4.082482905.\n\\]\n\nI gradi di libertà di Welch-Satterthwaite sono\n\n\\[\n\\nu=\\frac{(s_A^2/n_A+s_B^2/n_B)^2}{(s_A^2/n_A)^2/(n_A-1)+(s_B^2/n_B)^2/(n_B-1)}\n=147.999879329.\n\\]\n\nAl livello \\(\\alpha=0{,}05\\), il valore critico per una coda è circa \\(1{,}66\\). Poiché \\(4{,}082>1{,}66\\), si rifiuta \\(H_0\\): sotto le ipotesi del test, i dati forniscono una forte evidenza che la media della popolazione B sia maggiore della media della popolazione A.\n\nQuesta conclusione riguarda una differenza statistica tra le medie. Il testo non specifica assegnazione casuale o controllo dei fattori confondenti, quindi il risultato da solo non dimostra che il metodo B causi punteggi più alti o sia causalmente superiore al metodo A.",
    },
]

fr_id = "euroblocks_fr_3c014d32"
fr_before = core_by_id[fr_id][1]["review_material"]["corrected"]
fr_after = [
    fr_before[0],
    {
        "role": "assistant",
        "content": "L'article de Cornell du 15 juin 2016 rapporte plutôt un ordre de grandeur d'environ 1 500 ans dans le modèle probabiliste proposé par Evan Solomonides avec Yervant Terzian. Ce modèle combine le paradoxe de Fermi et le principe de médiocrité et estime qu'à cet horizon environ la moitié de la Voie lactée aurait été atteinte par des signaux, rendant une détection probable. Ce n'est ni une conséquence de la seule équation de Drake, ni une échéance garantie, ni le temps de parcours d'une unique émission à travers une demi-galaxie : le résultat dépend des hypothèses du modèle.",
    },
]


specs = [
    {
        "candidate_id": "repair6_personas_if_37ae2fa7",
        "row_id": "personas_if_37ae2fa7",
        "language": "el",
        "source_kind": "initial42_review_material",
        "before_variant": "corrected",
        "before": personas_before,
        "after": personas_after,
        "repair_class": "instruction_language_and_response_identity_repair",
        "reasons": [
            "Replace the English loanword placeholders with natural Greek in the instruction and the three fields.",
            "Remove the invented feminine operating-room-manager signature.",
            "Retain exactly three instrument fields, the required P.S., ergonomic-feedback request, and the uppercase-emphasis constraint.",
        ],
        "sources": [],
    },
    {
        "candidate_id": "repair6_en_393a7e8e",
        "row_id": english_id,
        "language": "en",
        "source_kind": "initial42_review_material",
        "before_variant": "corrected",
        "before": english_before,
        "after": english_after,
        "repair_class": "minimal_summary_fidelity_and_grammar_repair",
        "reasons": [
            "Add the missing comma before the nonrestrictive who-clause.",
            "Restore truck from the embedded article instead of car.",
            "Keep the embedded news article byte-for-byte unchanged.",
        ],
        "sources": [],
    },
    {
        "candidate_id": "repair6_es_20461",
        "row_id": "20461",
        "language": "es",
        "source_kind": "unpaired_es_pt_it_coverage9",
        "before_variant": "retained_messages",
        "before": es20461_before,
        "after": es20461_after,
        "repair_class": "substantive_statistical_explanation_repair",
        "reasons": [
            "Remove the false claim that high predictor variance itself causes overfitting.",
            "Distinguish predictor spread, error variance, estimator variance, residual variance, and out-of-sample generalization.",
            "State the conditional simple-regression slope-variance relationship and the limits of training residuals.",
        ],
        "sources": ["duke_slr", "islr_bias_variance"],
    },
    {
        "candidate_id": "repair6_es_15571",
        "row_id": "15571",
        "language": "es",
        "source_kind": "unpaired_es_pt_it_coverage9",
        "before_variant": "retained_messages",
        "before": es15571_before,
        "after": es15571_after,
        "repair_class": "prompt_order_and_language_repair",
        "reasons": [
            "Begin with the sailor dying in bed aboard the ship in mid-ocean, as explicitly requested.",
            "Replace the malformed phrase arena de una vieja arena with a natural hourglass image.",
            "Retain the remaining plot, paragraphs, names, and narrative voice exactly.",
        ],
        "sources": [],
    },
    {
        "candidate_id": "repair6_it_49139",
        "row_id": "49139",
        "language": "it",
        "source_kind": "unpaired_es_pt_it_coverage9",
        "before_variant": "retained_messages",
        "before": it49139_before,
        "after": it49139_after,
        "repair_class": "language_and_inferential_statistics_repair",
        "reasons": [
            "Correct Viene condotta uno studio to Viene condotto uno studio.",
            "Use one internally consistent independent-sample Welch test with the correct one-sided composite null.",
            "Bind t, Welch-Satterthwaite degrees of freedom, and the approximate 5% critical value to the supplied summaries.",
            "Remove the unsupported causal-superiority conclusion from an unspecified study design.",
        ],
        "sources": ["nist_two_sample_t", "duke_causality"],
    },
    {
        "candidate_id": "repair6_fr_euroblocks_3c014d32",
        "row_id": fr_id,
        "language": "fr",
        "source_kind": "initial42_review_material",
        "before_variant": "corrected",
        "before": fr_before,
        "after": fr_after,
        "repair_class": "primary_source_factual_repair",
        "reasons": [
            "Replace unsupported 1580 with the approximately 1500-year estimate reported by Cornell in 2016.",
            "Attribute the speculative model to Evan Solomonides and Yervant Terzian and distinguish it from the Drake equation alone.",
            "State that the estimate is probabilistic and assumption-dependent, not a guarantee or one radio wave's crossing time.",
            "Preserve the named-scientist subject rather than culturally replacing it.",
        ],
        "sources": ["cornell_2016"],
    },
]


records = []
deltas = []
targets = []
for spec in specs:
    if spec["source_kind"] == "initial42_review_material":
        source_line, source_record = core_by_id[spec["row_id"]]
        expected = source_record["lineage"]["corrected_sha256"]
        lineage_snapshot = source_record["lineage"]
        source_path = CORE
    else:
        source_line, source_record = unpaired_by_id[spec["row_id"]]
        expected = source_record["source_messages_sha256"]
        underlying_path = Path(source_record["source_path"])
        underlying_record = read_line(underlying_path, source_record["source_line"])
        underlying_messages = [
            {"role": "user", "content": underlying_record["user"]},
            {"role": "assistant", "content": underlying_record["assistant"]},
        ]
        assert underlying_record["id"] == spec["row_id"]
        assert underlying_messages == spec["before"]
        assert canonical_sha(underlying_messages) == expected
        lineage_snapshot = {
            "source_path": source_record["source_path"],
            "source_line": source_record["source_line"],
            "source_messages_sha256": source_record["source_messages_sha256"],
            "assembly_path": source_record["assembly_path"],
            "assembly_line": source_record["assembly_line"],
            "assembly_messages_sha256": source_record["assembly_messages_sha256"],
            "source_equals_assembly": source_record["source_equals_assembly"],
            "paired_adaptation": source_record["paired_adaptation"],
            "missing": source_record["missing"],
        }
        source_path = UNPAIRED
    assert canonical_sha(spec["before"]) == expected
    record = {
        "schema_version": "adapted_core_repair_candidate_v1",
        "candidate_id": spec["candidate_id"],
        "row_id": spec["row_id"],
        "language": spec["language"],
        "status": "proposed_pending_root_technical_and_language_review",
        "repair_class": spec["repair_class"],
        "source_binding": {
            "review_material_path": str(source_path),
            "review_material_file_sha256": sha_file(source_path),
            "review_material_line": source_line,
            "review_material_record_sha256": record_sha(source_record),
            "before_variant": spec["before_variant"],
            "before_messages_sha256": expected,
            "lineage_snapshot": lineage_snapshot,
        },
        "before_messages": spec["before"],
        "proposed_messages": spec["after"],
        "proposed_messages_sha256": canonical_sha(spec["after"]),
        "changed_roles": [
            role for role in ("user", "assistant")
            if next(m["content"] for m in spec["before"] if m["role"] == role) != next(m["content"] for m in spec["after"] if m["role"] == role)
        ],
        "evidence_source_ids": spec["sources"],
        "corpus_mutated": False,
        "model_calls": 0,
    }
    if spec["source_kind"] == "unpaired_es_pt_it_coverage9":
        record["source_binding"]["underlying_source_record_sha256"] = record_sha(underlying_record)
        record["source_binding"]["underlying_source_line_verified"] = True
    records.append(record)
    deltas.append({
        "candidate_id": spec["candidate_id"],
        "row_id": spec["row_id"],
        "before_messages_sha256": expected,
        "proposed_messages_sha256": record["proposed_messages_sha256"],
        "repair_class": spec["repair_class"],
        "delta_reasons": spec["reasons"],
        "scope_guard": "Only the listed defects may change; source lineage and unrelated content remain fixed.",
    })
    targets.append({
        "candidate_id": spec["candidate_id"],
        "row_id": spec["row_id"],
        "language": spec["language"],
        "status": record["status"],
        "before_messages_sha256": expected,
        "proposed_messages_sha256": record["proposed_messages_sha256"],
        "messages": spec["after"],
    })

write_jsonl(HERE / "candidate_records.jsonl", records)
write_jsonl(HERE / "delta_reasons.jsonl", deltas)
write_jsonl(HERE / "proposed_targets.jsonl", targets)

sources = {
    "nist_two_sample_t": {
        "url": "https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm",
        "used_for": "Unpaired two-sample statistic, Welch-Satterthwaite degrees of freedom, and one-sided critical region.",
    },
    "duke_slr": {
        "url": "https://www2.stat.duke.edu/courses/Fall18/sta210.001/slides/lectures/06_slr.html",
        "used_for": "Simple-regression error variance, slope standard error, residual variance estimate, and distinction between mean and individual prediction uncertainty.",
    },
    "duke_causality": {
        "url": "https://www2.stat.duke.edu/courses/Fall18/sta210.001/slides/lectures/06_slr.html",
        "used_for": "A statistical association does not establish causality without an appropriate design or adequate confounding control.",
    },
    "islr_bias_variance": {
        "url": "https://www.statlearning.com/s/ISLRSeventhPrinting.pdf",
        "used_for": "Bias-variance tradeoff and out-of-sample test error; training fit alone does not establish generalization.",
    },
    "cornell_2016": {
        "url": "https://news.cornell.edu/stories/2016/06/relax-itll-be-1500-years-aliens-contact-us",
        "published": "2016-06-15",
        "used_for": "Approximately 1500 years under the Solomonides-Terzian probabilistic Fermi-paradox/mediocrity model, with an explicit non-guarantee.",
    },
}
write_json(HERE / "evidence_sources.json", sources)

# Deterministic checks of changed-text constraints and supplied Welch arithmetic.
by_id = {row["candidate_id"]: row for row in records}
p = by_id["repair6_personas_if_37ae2fa7"]
p_user, p_assistant = [m["content"] for m in p["proposed_messages"]]
uppercase_greek = re.findall(r"\b[Α-ΩΆΈΉΊΌΎΏΪΫ]{2,}\b", p_assistant)
e = by_id["repair6_en_393a7e8e"]
e_before_user = e["before_messages"][0]["content"]
e_after_user, e_after_assistant = [m["content"] for m in e["proposed_messages"]]
s = by_id["repair6_es_15571"]
s_before_tail = s["before_messages"][1]["content"].split("\n\n", 1)[1]
s_after_parts = s["proposed_messages"][1]["content"].split("\n\n", 1)
it = by_id["repair6_it_49139"]
it_user_after, it_answer = [m["content"] for m in it["proposed_messages"]]
fr_answer = by_id["repair6_fr_euroblocks_3c014d32"]["proposed_messages"][1]["content"]

v_a, v_b = 8**2 / 80, 7**2 / 70
t_value = (80 - 75) / math.sqrt(v_a + v_b)
df_value = (v_a + v_b) ** 2 / (v_a**2 / 79 + v_b**2 / 69)
checks = {
    "six_unique_candidates": len(records) == len({row["candidate_id"] for row in records}) == 6,
    "all_before_hashes_match_source": all(canonical_sha(row["before_messages"]) == row["source_binding"]["before_messages_sha256"] for row in records),
    "all_proposed_hashes_match": all(canonical_sha(row["proposed_messages"]) == row["proposed_messages_sha256"] for row in records),
    "personas_natural_greek_instruction": "placeholders" not in p_user and "πεδία προς συμπλήρωση" in p_user,
    "personas_exactly_three_instrument_fields": re.findall(r"\[[^\[\]]+\]", p_assistant) == ["[όνομα εργαλείου 1]", "[όνομα εργαλείου 2]", "[όνομα εργαλείου 3]"],
    "personas_no_invented_signature": "Η υπεύθυνη χειρουργείου" not in p_assistant and "[Your Name]" not in p_assistant,
    "personas_uppercase_emphasis_and_postscript": uppercase_greek == ["ΕΡΓΟΝΟΜΙΚΑ"] and p_assistant.split("\n\n")[-1].startswith("P.S."),
    "english_embedded_news_unchanged": e_before_user == e_after_user,
    "english_relative_clause_and_truck": "thief, who was 32," in e_after_assistant and "ran to his truck" in e_after_assistant and "ran to his car" not in e_after_assistant,
    "es_regression_distinctions": all(term in by_id["repair6_es_20461"]["proposed_messages"][1]["content"] for term in ["dispersión del predictor", "varianza del error", "varianza del modelo o del estimador", "varianza residual", "generalización"]),
    "es_regression_formula": "\\operatorname{Var}(\\hat\\beta_1\\mid X)=\\frac{\\sigma^2}{\\sum_i (x_i-\\bar x)^2}" in by_id["repair6_es_20461"]["proposed_messages"][1]["content"],
    "story_required_opening_and_phrase_fix": all(term in s_after_parts[0] for term in ["moría", "cama", "barco", "medio del océano"]) and "arena de una vieja arena" not in s_after_parts[0] and "reloj de arena" in s_after_parts[0],
    "story_rest_preserved_exactly": s_after_parts[1] == s_before_tail,
    "italian_prompt_agreement": it_user_after.startswith("Viene condotto uno studio"),
    "welch_arithmetic": abs(t_value - 4.082482904639) < 1e-12 and abs(df_value - 147.999879329070) < 1e-12,
    "italian_welch_values_and_hypothesis": all(term in it_answer for term in ["H_0:\\mu_B\\leq\\mu_A", "4.082482905", "147.999879329", "1{,}66"]),
    "italian_no_causal_superiority": "non dimostra che il metodo B causi" in it_answer and "è più efficace rispetto" not in it_answer,
    "french_primary_source_number": "1 500" in fr_answer and "1580" not in fr_answer,
    "french_attribution_and_uncertainty": all(term in fr_answer for term in ["Evan Solomonides", "Yervant Terzian", "paradoxe de Fermi", "principe de médiocrité", "ni une échéance garantie", "unique émission"]),
    "no_corpus_mutation_declared": all(not row["corpus_mutated"] and row["model_calls"] == 0 for row in records),
}

check_rows = [{"check": key, "pass": value} for key, value in checks.items()]
write_jsonl(HERE / "constraint_checks.jsonl", check_rows)
verification = {
    "verified_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
    "ok": all(checks.values()),
    "checks": checks,
    "welch": {"t": t_value, "df": df_value, "critical_one_sided_alpha_0_05_approx": 1.66},
}
write_json(HERE / "verification.json", verification)

report = """# Six targeted adapted-core repair candidates

Status: proposed for full root technical and language review. No corpus row was modified, no model subprocess was called, and no candidate is approved for assembly.

## Candidate summary

| Candidate | Language | Narrow repair |
|---|---|---|
| `personas_if_37ae2fa7` | Greek | Natural Greek field wording, exactly three instrument fields, no invented feminine manager signature; P.S. and uppercase-emphasis constraint retained. |
| `393a7e8e…` | English | Adds the missing nonrestrictive-clause comma and restores `truck`; embedded news is byte-identical. |
| `20461` | Spanish | Replaces the statistically false input-variance account with separate treatment of predictor spread, noise, estimator variance, residual variance, and generalization. |
| `15571` | Spanish | Opens with the dying sailor in bed as requested and repairs the malformed hourglass phrase; every later paragraph is unchanged. |
| `49139` | Italian | Fixes agreement and supplies one consistent one-sided Welch test with correct hypotheses, statistic, degrees of freedom, threshold, and noncausal interpretation. |
| `euroblocks_fr_3c014d32` | French | Replaces 1580 with the source-supported approximately 1500-year speculative estimate and corrects its attribution and uncertainty. |

## Evidence boundary

The Spanish regression repair follows the conditional simple-regression slope variance and residual-noise relationships in [Duke's simple linear regression notes](https://www2.stat.duke.edu/courses/Fall18/sta210.001/slides/lectures/06_slr.html), together with the bias-variance and test-error treatment in [*An Introduction to Statistical Learning*](https://www.statlearning.com/s/ISLRSeventhPrinting.pdf). Predictor spread is not itself overfitting; noise, design, estimator sensitivity, and out-of-sample evaluation are distinct.

The Italian test uses the unequal-variance two-sample statistic and Welch-Satterthwaite degrees of freedom documented by the [NIST Engineering Statistics Handbook](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm). Direct arithmetic from the supplied summaries gives `t = 4.082482904639` and `df = 147.999879329070`; the proposed target rounds these transparently and uses an approximately 1.66 one-sided 5% threshold. The study description does not establish a causal design.

The French correction follows the [Cornell Chronicle report dated June 15, 2016](https://news.cornell.edu/stories/2016/06/relax-itll-be-1500-years-aliens-contact-us). It reports about 1,500 years under the probabilistic Solomonides-Terzian Fermi-paradox/mediocrity model and explicitly frames the horizon as likely rather than guaranteed. The target preserves the named scientists and topic while avoiding a claim that the number follows from the Drake equation alone or describes one signal's travel time.

## Review artifacts

`candidate_records.jsonl` contains every complete before and proposed message pair with source lineage and hashes. `delta_reasons.jsonl` states the permitted change for each row. `proposed_targets.jsonl` is the compact review envelope. `constraint_checks.jsonl` and `verification.json` cover hashes, exact field count, unchanged embedded content, preserved story tail, statistical arithmetic, and the factual guardrails.
"""
(HERE / "report.md").write_text(report, encoding="utf-8")

assets = [
    "candidate_records.jsonl", "delta_reasons.jsonl", "proposed_targets.jsonl",
    "constraint_checks.jsonl", "verification.json", "evidence_sources.json", "report.md", "build_repair6.py",
]
manifest = {
    "schema_version": "adapted_core_repair6_manifest_v1",
    "created_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
    "status": "proposed_pending_root_technical_and_language_review",
    "candidate_count": len(records),
    "model_calls": 0,
    "corpus_mutations": 0,
    "source_files": {str(CORE): sha_file(CORE), str(UNPAIRED): sha_file(UNPAIRED)},
    "artifact_sha256": {name: sha_file(HERE / name) for name in assets},
}
write_json(HERE / "manifest.json", manifest)
print(json.dumps({"candidates": len(records), "checks_ok": verification["ok"]}, indent=2))
raise SystemExit(0 if verification["ok"] else 1)
