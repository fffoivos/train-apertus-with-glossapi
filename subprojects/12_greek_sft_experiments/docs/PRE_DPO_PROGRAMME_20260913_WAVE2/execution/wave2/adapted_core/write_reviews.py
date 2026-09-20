#!/usr/bin/env python3
"""Freeze bounded manual review findings and a reproducibility receipt."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (HERE / name).read_text().splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


CORE_NOTES = {
    "0695d312f819d7e80578425342b8aaa99fdcd36b81321cd73be53b7b12f991aa": ("keep", "The archery list, requested count, and brainstorming task survive; the blindfold idea is safely repaired rather than taught as practice, and the editor fixes a broken Greek collocation."),
    "42c6340cab8f31eedc9d1af3a5a23826968e3e02e14b75d56803f7bc91165a95": ("keep", "The British butler, Queen, and pounds frame is regenerated as a coherent Greek analogue; the Audio-Technica subject, persona, and multi-turn state survive."),
    "7bb8511d961f599a749ae6c434c3d80bb17d1aea8b1d1323cd429cfa36cb9ad1": ("keep", "The embedded US job-list source is correctly retained as source material; label order and exact extraction task survive."),
    "53008b27feb41c953816ef69d8b6efaa403ce1fc35c394e8ca81e1ba206ad28c": ("keep", "The source-bearing health question is preserved and the food-or-drink prompt defect is declared and repaired. The editor's fast-food wording is a style preference, not observed task damage."),
    "56405dfbe0feadd19e9da001aa4c33d0753017d0765f1f4c8b64b6418d3999cc": ("keep", "The Python task and code are preserved exactly enough to execute the requested operation. Shadowing the built-in name list is inherited from the source rather than introduced here."),
    "d0c3859b0b9d77efc8fa722b55164d3c48128e01b18baeac338824629ac95988": ("keep", "The embedded track list remains source material and the extraction output is exact; the editor repairs the apostrophe."),
    "coconot_413a2f93": ("keep", "The boundary is useful and specific, gives no drug or dose instruction, and redirects to appropriate help."),
    "coconot_d4ba69e8": ("keep", "The copyright refusal is narrowed to the disallowed request and continues with lawful access routes."),
    "coconot_c2511989": ("keep", "No procedural self-surgery detail is added; referral and emergency routing preserve the helpful task."),
    "personas_if_b6bfa838": ("keep", "The poster task survives and the response contains exactly two all-capital words as requested."),
    "personas_if_3ec2eb61": ("keep", "The exact required phrase and postscript survive, with natural enough Greek."),
    "personas_if_37ae2fa7": ("repair", "The prompt leaves the English word placeholders untranslated, and the answer invents a feminine sender/role ('Η υπεύθυνη χειρουργείου') absent from the source. Repair the Greek prompt and remove the unsupported identity choice."),
    "smolcon_447105b8": ("keep", "The explanation remains factual and safer while satisfying the exact three-bullet device."),
    "smolcon_eee569f3": ("keep", "Lowercase, title, three bullets, and the exact ending survive; the editor's repair is appropriate."),
    "smolcon_3013f07c": ("keep", "The Markdown-highlighting constraint and subject survive, and the editor fixes a Greek collocation."),
    "oasst_504508e8": ("keep", "The exact acknowledgement is present and uncertainty is grounded in date/version limitations rather than a claim of self-awareness."),
    "oasst_d72f82bb": ("keep", "The product is regenerated as a fictional Greek-language analogue; five scenarios, requested revisions, and multi-turn continuity survive."),
    "oasst_6d37ad2d": ("keep", "The Haskell task and code are repaired while multi-turn continuity survives. The term μονάδα could use a gloss but is not a task failure."),
    "everyday_76bf593b": ("keep", "The cooking progression, metric temperature, Greek food frame, and follow-up state survive."),
    "everyday_29dd09a3": ("keep", "The Greek is natural and the state carried into the follow-up is preserved."),
    "everyday_02708fe4": ("keep", "The game-category corrections are factual, non-Anglophone game names remain, and the response uses a Greek information-seeking perspective."),
    "systemchats_44e8971b": ("keep", "The fixed-string persona and all twelve repeated outputs are exact."),
    "systemchats_c9fd650b": ("keep", "The German target word is correctly retained, the language task is re-executed, and the pronoun ban is repaired without losing the device."),
    "systemchats_a93d0924": ("keep", "The noir voice, calculation task, euro frame, and corrected compound-interest result survive."),
}

FOREIGN_NOTES = {
    "bc8f27db0b74f77cf6abd3c3148b368facb09abea59068ead4e0557c05923478": ("keep", "The English twin coherently copies the Greek twin's renamed family members and preserves three distinct tones. Its standalone English adaptation receipt is absent."),
    "393a7e8ef70f7bc806f1d5c7c2b45475888e5dbc16cc46f57b48bff9c173c816": ("repair", "The embedded Texas source is correctly left as source material, but the summary has a comma error ('thief who was 32, ran'). Apply an English language repair; the standalone English adaptation receipt is also absent."),
    "6e53eb444a79f482e351fbcdde1331b380df3f7e4a2817e0d91d9e4c03a784e2": ("keep", "The joke device and fictional self-reference survive without an unnecessary cultural move. The standalone English adaptation receipt is absent."),
    "apertus_en_2b4cca87": ("keep", "The Python string-reversal task, examples, and code are exact."),
    "apertus_en_b5c111d2": ("keep", "The inches-to-millimetres perspective change is coherent. Python displays 0.3 rather than the requested-looking 0.30, an inherited wording ambiguity rather than adaptation damage."),
    "apertus_en_21a3d9ad": ("keep", "Greek names and flavours are introduced coherently, deliberately flawed prose remains available for the editing task, and the follow-up phrase is consistent."),
    "euroblocks_fr_4327dcdc": ("keep", "The answer detects the inconsistent sphere/cylinder premise and computes 25/54 under the stated conditional interpretation."),
    "euroblocks_fr_be823b4c": ("keep", "The real-square argument is correct and the mathematical task is preserved."),
    "euroblocks_fr_2c468ef2": ("keep", "The response corrects the bad uniqueness assumption and constructs the 2500-pair maximum."),
    "euroblocks_fr_aa700ecd": ("keep", "The database guidance is correct and age is calculated at query time rather than frozen."),
    "euroblocks_fr_ab62976c": ("keep", "The malformed prompt and obsidian premise are repaired without pretending there is a unique mineral."),
    "euroblocks_fr_3c014d32": ("keep", "The teaching task is preserved, but the precise 1580-year attribution has no evidence in the row and needs factual verification before promotion to gold."),
    "euroblocks_de_7d2be378": ("keep", "The answer detects the impossible tank capacity and gives the correct conditional result of 40 percent."),
    "euroblocks_de_0ab678f5": ("keep", "Charlie is changed to Christos coherently, while the arithmetic and constraints survive."),
    "euroblocks_de_a79858d1": ("keep", "Dollars become euros and the linear integer model remains complete and correct."),
    "euroblocks_de_68472159": ("keep", "The response correctly repairs percentage-points ambiguity."),
    "euroblocks_de_36c8b30a": ("keep", "The electroweak explanation and the named Nobel attribution remain accurate within this review."),
    "euroblocks_de_b33c3c1e": ("keep", "The German subject is appropriately retained under the reference's keep-foreign rule, and the geography is corrected."),
}

UNPAIRED_NOTES = {
    "39436": ("keep", "The retained Spanish record gives coherent generic advice about story conflict; no cultural-frame problem is visible."),
    "20461": ("repair", "The Spanish answer conflates variance in input data with estimator/model variance and says high input variance leads to overfitting. Repair the statistical explanation."),
    "15571": ("repair", "The Spanish phrase 'como la arena de una vieja arena' is nonsensical; it likely intended an hourglass image and needs language repair."),
    "19298": ("keep", "The retained Portuguese writing advice is verbose but coherent."),
    "35565": ("readapt", "If promoted into the adapted core, this Portuguese row needs cultural re-adaptation because English personal names and department labels retain an unexamined Anglophone frame."),
    "11743": ("readapt", "If promoted into the adapted core, this Portuguese row needs re-adaptation because its US astronaut persona and US-centred assistant perspective remain unchanged."),
    "12673": ("keep", "The Italian list-comprehension and rounding task is correct; Python's rounding behaviour matches the example."),
    "49139": ("repair", "Italian grammar requires 'Viene condotto uno studio'. The analysis also mixes a Welch-style standard error with pooled degrees of freedom and overstates association as causal effectiveness."),
    "36143": ("keep", "The Heron implementation meets the stated task. Invalid-triangle validation was not requested."),
}


core = [r for r in load_jsonl("core60_manifest.jsonl") if r["initial_read"]]
foreign = [r for r in load_jsonl("foreign60_manifest.jsonl") if r["initial_read"]]
unpaired = load_jsonl("unpaired_es_pt_it_coverage9.jsonl")
assert len(core) == 24 and len(foreign) == 18 and len(unpaired) == 9
assert {r["row_id"] for r in core} == set(CORE_NOTES)
assert {r["row_id"] for r in foreign} == set(FOREIGN_NOTES)
assert {r["id"] for r in unpaired} == set(UNPAIRED_NOTES)

findings = []
for scope, rows, notes in (
    ("core_pair", core, CORE_NOTES),
    ("foreign_pair", foreign, FOREIGN_NOTES),
    ("unpaired_retained", unpaired, UNPAIRED_NOTES),
):
    for row in rows:
        rid = row.get("row_id", row.get("id"))
        verdict, note = notes[rid]
        finding = {
            "scope": scope,
            "id": rid,
            "language": row.get("language", "el" if scope == "core_pair" else None),
            "source_family": row.get("stratum", "smoltalk2_multilingual"),
            "verdict": verdict,
            "teaching_task_device": "preserved" if verdict != "repair" else "see_finding",
            "cultural_adaptation": "needs_readaptation" if verdict == "readapt" else "acceptable_in_inspected_row",
            "greek_editor_damage": "none_observed" if scope == "core_pair" else "not_applicable",
            "finding": note,
            "paired_lineage": scope != "unpaired_retained",
        }
        if rid == "euroblocks_fr_3c014d32":
            finding["evidence_gate"] = "required_before_gold"
        if scope == "foreign_pair" and row["stratum"] == "en_no_robots_twin":
            finding["lineage_gap"] = "standalone_english_adaptation_receipt_not_in_export"
        findings.append(finding)

with (HERE / "findings.jsonl").open("w") as handle:
    for finding in findings:
        handle.write(json.dumps(finding, ensure_ascii=False) + "\n")

all_core = load_jsonl("core60_manifest.jsonl")
all_foreign = load_jsonl("foreign60_manifest.jsonl")
assembly_checks = []
for row in all_core + all_foreign:
    for assembly in row["lineage"]["assemblies"]:
        assembly_checks.append((row["row_id"], row.get("config", row["stratum"]), assembly))
mismatches = [
    {"row_id": rid, "config": cfg, "arm": a["arm"], "split": a["split"], "line": a["line"], "variant": a["variant"],
     "assembled_messages_sha256": a["messages_sha256"], "current_expected_messages_sha256": a["expected_messages_sha256"]}
    for rid, cfg, a in assembly_checks if not a["matches_expected_variant"]
]

counts = defaultdict(Counter)
for finding in findings:
    counts[finding["scope"]][finding["verdict"]] += 1

receipt = {
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "reviewer": "Sol agent",
    "review_method": "manual full semantic read of every selected complete record; deterministic scripts only for selection, hashes, joins, and counts",
    "additional_model_subprocess_calls": 0,
    "reviewed": {"core_pairs": len(core), "foreign_pairs": len(foreign), "unpaired_es_pt_it": len(unpaired), "total_records": len(findings)},
    "paired_foreign_languages": sorted({r["language"] for r in foreign}),
    "target_foreign_languages": ["en", "fr", "de", "es", "pt", "it"],
    "unpaired_only_languages": sorted({r["language"] for r in unpaired}),
    "verdict_counts": {scope: dict(counter) for scope, counter in counts.items()},
    "planned": {"core_pairs": len(all_core), "foreign_pairs": len(all_foreign)},
    "assembly_variant_checks": {"checks": len(assembly_checks), "matches": len(assembly_checks) - len(mismatches), "mismatches": len(mismatches), "mismatch_details": mismatches},
    "manifest_hashes": {name: sha256(HERE / name) for name in ("source_manifest.json", "core60_manifest.jsonl", "foreign60_manifest.jsonl", "unpaired_es_pt_it_coverage9.jsonl", "findings.jsonl")},
}
(HERE / "verification.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
