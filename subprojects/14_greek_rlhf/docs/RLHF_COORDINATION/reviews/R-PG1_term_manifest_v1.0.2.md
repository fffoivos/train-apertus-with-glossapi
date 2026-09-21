# R-PG1 term manifest — spec v1.0.2 and glossary v1.0.2

Answers R-PG1 review 2, finding 9. Replaces the one-line summary in `R-PG1_term_coverage.txt` (kept as history).
Spec: `docs/SEED_LABEL_SPEC_20260917.md` (v1.0.2). Glossary: `data/rlhf/prompts/seed_label_definitions_v1.md` (v1.0.2). Generated 17 Sept 2026.

What counts as a term: every bold-marked (`**…**`) term in the spec, with the section it sits in and its line number. Line numbers refer to spec v1.0.2 as frozen; the section anchor is the stable reference.
Glossary column: **yes** = the glossary carries a prompt-ready definition (a bullet label or a defining sentence); **spec-only** = deliberately kept in the spec only (the audit legend, length terms not sent to Sol, and the dataset, distribution, judging and identity terms of §5.4–§5.7 per the glossary's header); **no** = not carried by the glossary (each listed with its reason below).

Totals: 170 terms — yes 108, spec-only 56, no 6; 8 bold occurrences excluded as emphasis or references (listed at the end).

Terms marked **no**:
- §4.4 constraint revocation, real-error recovery, false-correction resistance, social response: listed in the spec but not defined there either; deferred to the dialogue track (decision 7).
- §4.8 serious error and minor defect: defined in the spec (annotator threshold, `turn_quality.txt`), but the glossary only uses "serious error" in its sampling-point bullets. Open gap, not fixed in v1.0.2: a dialogue prompt that sends the sampling-point paragraph does not carry the threshold.

Automatic presence check limits: the check matches a bullet label (`^ *- term( (…))?:`) or a case-insensitive substring; a substring hit is not proof of a definition, so every §5.4–§5.7 hit is classified spec-only and the prose hits in §4–§5.3 were read by hand (all carry a defining sentence in the glossary). `maths content` is marked in two places (§4.5 introduces the indicator, §5.6 is the canonical entry); both point to the same glossary text.

## Terms

| # | Term (as marked in the spec) | Spec anchor (line) | Glossary | Note |
|---|---|---|---|---|
| 1 | defined | §3 (42) | spec-only | audit legend |
| 2 | partial | §3 (42) | spec-only | audit legend |
| 3 | undefined | §3 (42) | spec-only | audit legend |
| 4 | A1 cooperative: | §4.1 (100) | yes | glossary bullet |
| 5 | A2 frustrated: | §4.1 (101) | yes | glossary bullet |
| 6 | A3 skeptical: | §4.1 (102) | yes | glossary bullet |
| 7 | A4 playful: | §4.1 (103) | yes | glossary bullet |
| 8 | A5 anxious (defined, not drawn; used in round 2): | §4.1 (104) | yes | glossary bullet |
| 9 | R1 standard: | §4.2 (107) | yes | glossary bullet |
| 10 | R2 informal: | §4.2 (108) | yes | glossary bullet |
| 11 | R3 formal: | §4.2 (109) | yes | glossary bullet |
| 12 | R4 greeklish: | §4.2 (110) | yes | glossary bullet |
| 13 | D1 routine: | §4.3 (113) | yes | glossary bullet |
| 14 | D2 compositional: | §4.3 (114) | yes | glossary bullet |
| 15 | D3 challenging: | §4.3 (115) | yes | glossary bullet |
| 16 | I1 followup: | §4.4 (119) | yes | glossary bullet |
| 17 | I2 revision: | §4.4 (120) | yes | glossary bullet |
| 18 | I3 constraint_retention: | §4.4 (121) | yes | glossary bullet |
| 19 | I4 recall: | §4.4 (122) | yes | glossary bullet |
| 20 | I5 uncertainty: | §4.4 (123) | yes | glossary bullet |
| 21 | constraint revocation | §4.4 (125) | no | listed only; deferred to the dialogue track (decision 7); not defined in the spec either |
| 22 | real-error recovery | §4.4 (125) | no | listed only; deferred to the dialogue track (decision 7); not defined in the spec either |
| 23 | false-correction resistance | §4.4 (125) | no | listed only; deferred to the dialogue track (decision 7); not defined in the spec either |
| 24 | social response | §4.4 (125) | no | listed only; deferred to the dialogue track (decision 7); not defined in the spec either |
| 25 | T1 everyday: | §4.5 (128) | yes | glossary bullet |
| 26 | T2 instruction: | §4.5 (129) | yes | glossary bullet |
| 27 | T3 factual: | §4.5 (130) | yes | glossary bullet |
| 28 | T4 safety: | §4.5 (131) | yes | glossary bullet |
| 29 | T5 math (maths): | §4.5 (132) | yes | glossary bullet |
| 30 | T5.1 calculation: | §4.5 (134) | yes | glossary bullet |
| 31 | T5.2 solving: | §4.5 (135) | yes | glossary bullet |
| 32 | T5.3 proof and justification: | §4.5 (136) | yes | glossary bullet |
| 33 | T5.4 construction and counterexamples: | §4.5 (137) | yes | glossary bullet |
| 34 | T5.5 explanation and learning: | §4.5 (138) | yes | glossary bullet |
| 35 | T5.6 checking and correction: | §4.5 (139) | yes | glossary bullet |
| 36 | T5.7 modelling: | §4.5 (140) | yes | glossary bullet |
| 37 | Reference. | §4.5 (142) | yes | glossary prose |
| 38 | Correctness and explanation length are separate. | §4.5 (143) | yes | glossary prose |
| 39 | Maths inside other primary purposes. | §4.5 (144) | yes | glossary prose |
| 40 | maths content | §4.5 (144) | yes | glossary maths block (Maths inside other primary purposes) |
| 41 | Ambiguity flag. | §4.5 (145) | yes | glossary prose |
| 42 | T6 dialogue: | §4.5 (146) | yes | glossary bullet |
| 43 | primary purposes | §4.5 (147) | yes | glossary prose |
| 44 | task type | §4.5 (147) | yes | glossary Task section: task_type reserved for the forum label |
| 45 | L1 bare: | §4.6 (150) | yes | glossary bullet |
| 46 | L2 terse: | §4.6 (151) | yes | glossary bullet |
| 47 | L3 short: | §4.6 (152) | yes | glossary bullet |
| 48 | L4 medium: | §4.6 (153) | yes | glossary bullet |
| 49 | L5 detailed: | §4.6 (154) | yes | glossary bullet |
| 50 | L6 rambling: | §4.6 (155) | yes | glossary bullet |
| 51 | detail | §4.6 (159) | yes | glossary prose |
| 52 | reply length | §4.6 (159) | spec-only | length term kept apart; not a label sent to Sol |
| 53 | depth | §4.6 (159) | spec-only | length term kept apart; not a label sent to Sol |
| 54 | M1 restate: | §4.7 (164) | yes | glossary bullet |
| 55 | M2 point_to_defect: | §4.7 (165) | yes | glossary bullet |
| 56 | M3 give_example: | §4.7 (166) | yes | glossary bullet |
| 57 | M4 decompose: | §4.7 (167) | yes | glossary bullet |
| 58 | M5 add_context: | §4.7 (168) | yes | glossary bullet |
| 59 | M6 simplify: | §4.7 (169) | yes | glossary bullet |
| 60 | M7 express_frustration: | §4.7 (170) | yes | glossary bullet |
| 61 | M8 accept_partial: | §4.7 (171) | yes | glossary bullet |
| 62 | M9 abandon: | §4.7 (172) | yes | glossary bullet |
| 63 | M10 clarify: | §4.7 (173) | yes | glossary bullet |
| 64 | M11 continue: | §4.7 (174) | yes | glossary bullet |
| 65 | M12 finish: | §4.7 (175) | yes | glossary bullet |
| 66 | Turn metadata: | §4.7 (177) | yes | glossary moves section: exactly four fields |
| 67 | restatement < pointed defect < partial scaffold or example < supplied solution | §4.7 (178) | yes | glossary prose |
| 68 | Serious error: | §4.8 (183) | no | glossary uses serious error in the sampling-point bullets without defining it |
| 69 | minor | §4.8 (183) | no | minor defect (the counterpart of serious error) not in the glossary |
| 70 | prevention point: | §4.8 (186) | yes | glossary bullet |
| 71 | supported recovery point: | §4.8 (187) | yes | glossary bullet |
| 72 | healthy continuation point: | §4.8 (188) | yes | glossary bullet |
| 73 | natural completion | §4.8 (191) | yes | glossary prose |
| 74 | abandonment | §4.8 (191) | yes | glossary prose |
| 75 | horizon | §4.8 (191) | yes | glossary prose |
| 76 | context cutoff | §4.8 (191) | yes | glossary prose |
| 77 | truncated output | §4.8 (191) | yes | glossary prose |
| 78 | infrastructure failure | §4.8 (191) | yes | glossary prose |
| 79 | ambiguous timeout | §4.8 (191) | yes | glossary prose |
| 80 | goal | §4.8 (193) | yes | glossary prose |
| 81 | known facts | §4.8 (193) | yes | glossary prose |
| 82 | expertise | §4.8 (193) | yes | glossary prose |
| 83 | misconception | §4.8 (193) | yes | glossary prose |
| 84 | disclosed preferences | §4.8 (193) | yes | glossary prose |
| 85 | private preferences | §4.8 (193) | yes | glossary prose |
| 86 | patience | §4.8 (193) | yes | glossary prose |
| 87 | helping ability | §4.8 (193) | yes | glossary prose |
| 88 | repeated defect count | §4.8 (193) | yes | glossary prose |
| 89 | task progress | §4.8 (193) | yes | glossary prose |
| 90 | Apertus view: | §4.8 (196) | yes | glossary bullet |
| 91 | user view: | §4.8 (197) | yes | glossary bullet |
| 92 | world resolver: | §4.8 (198) | yes | glossary bullet |
| 93 | learner view: | §4.8 (199) | yes | glossary bullet |
| 94 | evaluator view: | §4.8 (200) | yes | glossary bullet |
| 95 | writing | §4.8 (202) | yes | glossary prose |
| 96 | troubleshooting | §4.8 (202) | yes | glossary prose |
| 97 | learning | §4.8 (202) | yes | glossary prose |
| 98 | transfer check | §4.8 (202) | yes | glossary prose |
| 99 | F1 question: | §5.1 (207) | yes | glossary bullet |
| 100 | F2 explanation: | §5.1 (208) | yes | glossary bullet |
| 101 | F3 advice: | §5.1 (209) | yes | glossary bullet |
| 102 | F4 opinion: | §5.1 (210) | yes | glossary bullet |
| 103 | F5 translation: | §5.1 (211) | yes | glossary bullet |
| 104 | F6 calculation: | §5.1 (212) | yes | glossary bullet |
| 105 | F7 share: | §5.1 (213) | yes | glossary bullet |
| 106 | F8 other: | §5.1 (214) | yes | glossary bullet |
| 107 | F9 create: | §5.1 (215) | yes | glossary bullet |
| 108 | Precedence (exclusive assignment): | §5.1 (217) | yes | glossary prose |
| 109 | P1 supported: | §5.2 (221) | yes | glossary bullet |
| 110 | P2 contradicted: | §5.2 (222) | yes | glossary bullet |
| 111 | P3 unresolved: | §5.2 (223) | yes | glossary bullet |
| 112 | P4 not_applicable: | §5.2 (224) | yes | glossary bullet |
| 113 | S1 benign: | §5.3 (228) | yes | glossary bullet |
| 114 | S2 protective: | §5.3 (229) | yes | glossary bullet |
| 115 | S3 fiction: | §5.3 (230) | yes | glossary bullet |
| 116 | S4 harmful: | §5.3 (231) | yes | glossary bullet |
| 117 | S5 ambiguous: | §5.3 (232) | yes | glossary bullet |
| 118 | cell: | §5.4 (235) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 119 | accepted-pair yield: | §5.4 (236) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 120 | eligible preference pair: | §5.4 (237) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 121 | acceptable | §5.4 (237) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 122 | meaningful gap | §5.4 (237) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 123 | active view: | §5.4 (238) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 124 | superseded: | §5.4 (239) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 125 | held / quarantined: | §5.4 (240) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 126 | source lineage: | §5.4 (241) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 127 | task family: | §5.4 (242) | yes | glossary Task section (prose) |
| 128 | deduplication: | §5.4 (243) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 129 | trajectory: | §5.4 (244) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 130 | development_demo: | §5.4 (245) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 131 | provenance fields: | §5.4 (246) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 132 | `generator_version` | §5.4 (247) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 133 | `source_route` | §5.4 (248) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 134 | `dialogue_protocol_version` | §5.4 (249) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 135 | `opening_generator_version` | §5.4 (250) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 136 | target distribution: | §5.5 (254) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 137 | inventory: | §5.5 (255) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 138 | source kind: | §5.5 (256) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 139 | keepable: | §5.5 (257) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 140 | deficit: | §5.5 (258) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 141 | fill: | §5.5 (259) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 142 | prompt version: | §5.5 (260) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 143 | forum weights: | §5.5 (261) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 144 | near-duplicate: | §5.5 (262) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 145 | decontamination: | §5.5 (263) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 146 | candidate: | §5.6 (266) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 147 | original | §5.6 (266) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 148 | fresh | §5.6 (266) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 149 | resample | §5.6 (266) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 150 | prefix hash: | §5.6 (267) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 151 | verified reference: | §5.6 (268) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 152 | maths content: | §5.6 (269) | yes | glossary maths block (Maths inside other primary purposes) |
| 153 | maths judgement fields | §5.6 (270) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 154 | hint: | §5.6 (271) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 155 | development/production status: | §5.6 (272) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 156 | task instance: | §5.7 (275) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 157 | rendering: | §5.7 (276) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 158 | realised prompt: | §5.7 (277) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 159 | canonical key: | §5.7 (278) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 160 | instance key | §5.7 (278) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 161 | rendering key | §5.7 (278) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 162 | alias: | §5.7 (279) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 163 | seed status: | §5.7 (280) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 164 | reservation: | §5.7 (281) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 165 | compatibility rules: | §5.7 (282) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 166 | ledgers: | §5.7 (283) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 167 | A | §5.7 (283) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 168 | E | §5.7 (283) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 169 | y | §5.7 (283) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |
| 170 | frontier: | §5.7 (284) | spec-only | dataset, distribution, judging or identity term (glossary header: stays in the spec only) |

## Excluded bold occurrences (not definitions)

| Spec anchor (line) | Text | Reason |
|---|---|---|
| §3.2 (66) | anxious | audit-table emphasis; the value is defined in §4 or §5 |
| §3.3 (76) | task_type | audit-table emphasis; the value is defined in §4 or §5 |
| §3.3 (76) | undefined | audit-table emphasis; the value is defined in §4 or §5 |
| §5.3 (227) | harmful | value name inside the decision-order sentence; defined in the S1-S5 bullets |
| §5.3 (227) | fiction | value name inside the decision-order sentence; defined in the S1-S5 bullets |
| §5.3 (227) | protective | value name inside the decision-order sentence; defined in the S1-S5 bullets |
| §5.3 (227) | ambiguous | value name inside the decision-order sentence; defined in the S1-S5 bullets |
| §5.3 (227) | benign | value name inside the decision-order sentence; defined in the S1-S5 bullets |

## Reproducible check

The command used: the script below, saved as `term_manifest.sh` and run from `subprojects/12_greek_sft_experiments` as `sh term_manifest.sh` (POSIX sh, awk, grep, sed; it only reads the two files). The rows above are its tab-separated output, formatted as tables (TERM rows → Terms, EXCLUDED rows → Excluded).

```sh
#!/bin/sh
# Run from subprojects/12_greek_sft_experiments. Prints: anchor, spec line, term, glossary status, note.
S=docs/SEED_LABEL_SPEC_20260917.md; G=data/rlhf/prompts/seed_label_definitions_v1.md
DO=$(grep -n "^Exclusive decision order" "$S" | cut -d: -f1); LG=$(grep -n "^Legend:" "$S" | cut -d: -f1)
awk '/^## /{split(substr($0,4),a," "); anc=a[1]} /^### /{split(substr($0,5),a," "); anc=a[1]}
     { l=$0; while (match(l, /\*\*[^*]+\*\*/)) { t=substr(l, RSTART+2, RLENGTH-4); x=anc; sub(/\.$/,"",x);
       print "§" x "\t" NR "\t" t; l=substr(l, RSTART+RLENGTH) } }' "$S" |
while IFS="$(printf '\t')" read -r anc ln term; do
  k=$(printf '%s' "$term" | sed -E 's/^[A-Z][0-9]+(\.[0-9]+)? //; s/ \([^)]*\)//; s/[:.]$//; s/`//g')
  if grep -Eq "^ *- ${k}( \([^)]*\))?:" "$G"; then g=bullet; elif grep -Fqi -- "$k" "$G"; then g=text; else g=absent; fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$anc" "$ln" "$term" "$k" "$g"
done |
awk -F"\t" -v DO="$DO" -v LG="$LG" '
{ anc=$1; ln=$2; term=$3; k=$4; g=$5; st=""; note=""
  if (anc ~ /^§3/ && ln != LG) { print "EXCLUDED\t" anc "\t" ln "\t" term "\taudit-table emphasis; the value is defined in §4 or §5"; next }
  if (ln == DO)                { print "EXCLUDED\t" anc "\t" ln "\t" term "\tvalue name inside the decision-order sentence; defined in the S1-S5 bullets"; next }
  if (anc ~ /^§3/)                                  { st="spec-only"; note="audit legend" }
  else if (anc == "§4.4" && g == "absent")           { st="no"; note="listed only; deferred to the dialogue track (decision 7); not defined in the spec either" }
  else if (k == "task type")                        { st="yes"; note="glossary Task section: task_type reserved for the forum label" }
  else if (k == "reply length" || k == "depth")     { st="spec-only"; note="length term kept apart; not a label sent to Sol" }
  else if (k == "Turn metadata")                    { st="yes"; note="glossary moves section: exactly four fields" }
  else if (k == "Serious error")                   { st="no"; note="glossary uses serious error in the sampling-point bullets without defining it" }
  else if (k == "minor")                            { st="no"; note="minor defect (the counterpart of serious error) not in the glossary" }
  else if (k == "task family")                      { st="yes"; note="glossary Task section (prose)" }
  else if (k == "maths content")                    { st="yes"; note="glossary maths block (Maths inside other primary purposes)" }
  else if (anc ~ /^§5\.[4-7]/)                       { st="spec-only"; note="dataset, distribution, judging or identity term (glossary header: stays in the spec only)" }
  else if (g == "bullet")                           { st="yes"; note="glossary bullet" }
  else if (g == "text")                             { st="yes"; note="glossary prose" }
  else                                              { st="no"; note="not found in the glossary" }
  print "TERM\t" anc "\t" ln "\t" term "\t" st "\t" note }'
```
