"""Derived failure/recovery state and frozen JSON/HTML quality-depth reports."""
from __future__ import annotations

import collections
import html
import json
import pathlib
import random
from typing import Any

from annotate import effective_annotations, latest_trajectories, mandatory_boundary_rows
from budget import CallLedger, gpu_summary
from common import atomic_json, read_json, read_jsonl, sha256_text, utcnow


def derive_trajectory(annotation_rows: list[dict[str, Any]], terminal_code: str | None = None) -> dict[str, Any]:
    rows = sorted(annotation_rows, key=lambda r: r["turn_index"])
    first = next((r for r in rows if r["local_quality"] == "serious"), None)
    first_turn = first["turn_index"] if first else None
    opportunities = [r for r in rows if first_turn is not None and r["turn_index"] > first_turn and r["recovery_opportunity"]]
    successes = [r for r in opportunities if r["recovery_success"]]
    recovery_turn = successes[0]["turn_index"] if successes else None
    no_failure_kind = None
    if first_turn is None:
        no_failure_kind = "natural_completion" if terminal_code == "completed" else "observed_censored"
    return {
        "first_serious_turn": first_turn, "no_failure_observed": first_turn is None,
        "no_failure_kind": no_failure_kind, "unjudgeable_turns": [r["turn_index"] for r in rows if r["local_quality"] == "unjudgeable"],
        "recovery_opportunity_turns": [r["turn_index"] for r in opportunities],
        "recovery_success_turn": recovery_turn,
        "recovery_delay": recovery_turn - first_turn if recovery_turn is not None and first_turn is not None else None,
        "repeated_serious_turns": [r["turn_index"] for r in rows if first_turn is not None and r["turn_index"] > first_turn and r["local_quality"] == "serious"],
    }


def first_serious_and_recovery(rows: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    value = derive_trajectory(rows)
    return value["first_serious_turn"], value["recovery_success_turn"]


def build_report(state: str | pathlib.Path, stage: str) -> dict[str, Any]:
    state = pathlib.Path(state)
    manifest = read_json(state / "manifest.json")
    trajectories = latest_trajectories(state / stage / "trajectories.jsonl")
    if any(not row.get("terminal_code") for row in trajectories.values()):
        raise ValueError("report requires an honest terminal reason for every trajectory")
    annotations = effective_annotations(state, stage)
    by_tid: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in annotations:
        by_tid[row["trajectory_id"]].append(row)
    observed_turns = sum(t["assistant_turns"] for t in trajectories.values())
    if len(annotations) != observed_turns:
        raise ValueError(f"report requires annotation for every response: {len(annotations)}/{observed_turns}")
    seeds = {s["trajectory_id"]: s for s in manifest["seeds"] if s["stage"] == stage and s["trajectory_id"] in trajectories}
    depth: dict[str, Any] = {}
    for turn in range(1, 9):
        reached = [r for r in annotations if r["turn_index"] == turn]
        depth[str(turn)] = {"denominator_reached": len(reached),
                            "quality": dict(collections.Counter(r["local_quality"] for r in reached))}
    trajectory_state = {}
    for tid, trajectory in trajectories.items():
        trajectory_state[tid] = derive_trajectory(by_tid.get(tid, []), trajectory.get("terminal_code"))
    first_distribution = collections.Counter(
        str(v["first_serious_turn"]) if v["first_serious_turn"] is not None else "no_observed_error"
        for v in trajectory_state.values())
    onset = {}
    for turn in range(1, 9):
        at_risk = 0
        failures = 0
        for tid, rows in by_tid.items():
            earlier = [r for r in rows if r["turn_index"] < turn and r["local_quality"] == "serious"]
            current = next((r for r in rows if r["turn_index"] == turn), None)
            if current and not earlier:
                at_risk += 1
                failures += current["local_quality"] == "serious"
        onset[str(turn)] = {"at_risk": at_risk, "new_serious": failures,
                            "risk": failures / at_risk if at_risk else None}
    views: dict[str, Any] = {}
    for axis in ("task", "language"):
        views[axis] = {}
        for value in sorted({s[axis] for s in seeds.values()}):
            tids = [tid for tid, seed in seeds.items() if seed[axis] == value]
            quality = collections.Counter(r["local_quality"] for tid in tids for r in by_tid.get(tid, []))
            views[axis][value] = {"trajectories": len(tids), "quality": dict(quality),
                                       "descriptive_only": len(tids) < 5}
    endings = dict(collections.Counter(t.get("terminal_code") or "active" for t in trajectories.values()))
    ledger = CallLedger(state, manifest["config"])
    report = {
        "version": manifest["version"], "stage": stage, "created_utc": utcnow(),
        "statistical_unit": "trajectory", "trajectory_count": len(trajectories), "observed_turns": observed_turns,
        "quality_by_depth": depth, "first_serious_distribution": dict(first_distribution),
        "new_failure_risk": onset, "trajectory_state": trajectory_state, "ending_reasons": endings,
        "no_failure_endings": dict(collections.Counter(v["no_failure_kind"] for v in trajectory_state.values()
                                                       if v["no_failure_observed"])),
        "uncertain_trajectories": sum(bool(v["unjudgeable_turns"]) for v in trajectory_state.values()),
        "recovery_summary": _recovery_summary(trajectory_state),
        "trajectory_bootstrap": _bootstrap_depth(by_tid),
        "views": views, "context_length_bins": _context_bins(annotations),
        "planned_counts": (read_json(state / "forecast.json").get("admitted_planned_counts", {})
                           if stage == "measurement" and (state / "forecast.json").exists() else {}),
        "actual_counts": _actual_counts(seeds, trajectories),
        "user_policy_sha256": sha256_text(pathlib.Path(__file__).with_name("user_policy.txt").read_text(encoding="utf-8")),
        "annotation_prompt_sha256": sha256_text(pathlib.Path(__file__).with_name("turn_quality.txt").read_text(encoding="utf-8")),
        "call_ledger": ledger.counts(), "gpu_ledger": gpu_summary(state),
        "caveats": ["No-error means no serious error observed within this trajectory's ending.",
                    "Cells with fewer than five trajectories are descriptive only.",
                    "Correlated turns are not treated as independent statistical units."],
    }
    return report


def _context_bins(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bins = {"0-2k": [], "2k-4k": [], "4k+": []}
    for row in rows:
        key = "0-2k" if row["cumulative_tokens"] < 2000 else "2k-4k" if row["cumulative_tokens"] < 4000 else "4k+"
        bins[key].append(row)
    return {key: {"turns": len(values), "trajectories": len({r["trajectory_id"] for r in values}),
                  "quality": dict(collections.Counter(r["local_quality"] for r in values)),
                  "descriptive_only": len({r["trajectory_id"] for r in values}) < 5}
            for key, values in bins.items()}


def _recovery_summary(states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    opportunities = sum(bool(v["recovery_opportunity_turns"]) for v in states.values())
    successful = sum(v["recovery_success_turn"] is not None for v in states.values())
    delays = [v["recovery_delay"] for v in states.values() if v["recovery_delay"] is not None]
    return {"trajectories_with_opportunity": opportunities, "successful_repairs": successful,
            "recovery_delays": delays, "mean_delay": sum(delays) / len(delays) if delays else None,
            "repeated_serious_errors": sum(len(v["repeated_serious_turns"]) for v in states.values())}


def _bootstrap_depth(by_tid: dict[str, list[dict[str, Any]]], draws: int = 200, seed: int = 9162602) -> dict[str, Any]:
    """Trajectory-cluster bootstrap; turns are never resampled independently."""
    tids = sorted(by_tid)
    if not tids:
        return {"draws": 0, "serious_rate_95pct": {}}
    rng = random.Random(seed)
    values: dict[int, list[float]] = collections.defaultdict(list)
    for _ in range(draws):
        sampled = [rng.choice(tids) for _ in tids]
        for turn in range(1, 9):
            reached = [r for tid in sampled for r in by_tid[tid] if r["turn_index"] == turn]
            if reached:
                values[turn].append(sum(r["local_quality"] == "serious" for r in reached) / len(reached))
    intervals = {}
    for turn, rates in values.items():
        rates.sort()
        intervals[str(turn)] = [rates[int(.025 * (len(rates) - 1))], rates[int(.975 * (len(rates) - 1))]]
    return {"draws": draws, "resampling_unit": "trajectory", "serious_rate_95pct": intervals}


def _actual_counts(seeds: dict[str, dict[str, Any]], trajectories: dict[str, dict[str, Any]]) -> dict[str, Any]:
    accepted = [seeds[tid] for tid, row in trajectories.items() if row.get("terminal_code") not in {None, "infra_failure", "ambiguous_timeout"}]
    return {axis: dict(collections.Counter(r[axis] for r in accepted))
            for axis in ("task", "language", "interaction", "attitude", "register", "difficulty")}


def render_html(report: dict[str, Any]) -> str:
    def esc(value):
        return html.escape(str(value))

    def table(title, headers, rows):
        return (f"<h2>{esc(title)}</h2><div class='table-scroll'><table><thead><tr>"
                + "".join(f"<th scope='col'>{esc(h)}</th>" for h in headers)
                + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>" for row in rows)
                + "</tbody></table></div>")

    qualities = ("good", "minor", "serious", "unjudgeable")
    colors = {"good": "48,128,112", "minor": "179,139,49", "serious": "180,67,65", "unjudgeable": "108,92,143"}
    heat = []
    for quality in qualities:
        cells = []
        for turn in range(1, 9):
            value = report["quality_by_depth"][str(turn)]
            n, count = value["denominator_reached"], value["quality"].get(quality, 0)
            rate = count / n if n else 0
            cells.append(f"<td style='background:rgba({colors[quality]},{.07 + .32 * rate:.3f})'>"
                         f"<strong>{count}</strong><small>{rate:.0%}</small></td>" if n else "<td>—</td>")
        heat.append(f"<tr><th scope='row'>{quality}</th>{''.join(cells)}</tr>")
    reached = "".join(f"<td>{report['quality_by_depth'][str(t)]['denominator_reached']}</td>" for t in range(1, 9))
    heatmap = ("<figure aria-labelledby='heat-title'><h2 id='heat-title'>Quality across the full observed horizon</h2>"
               "<figcaption>Each cell shows turns and share of trajectories reaching that depth. "
               "Color intensity represents the within-depth share; zero reached depth is unmeasured.</figcaption>"
               "<div class='table-scroll'><table class='heat'><thead><tr><th>Quality / turn</th>"
               + "".join(f"<th>{t}</th>" for t in range(1, 9)) + "</tr></thead><tbody>"
               + "".join(heat) + f"<tr><th>Reached denominator</th>{reached}</tr></tbody></table></div></figure>")
    intervals = report["trajectory_bootstrap"]["serious_rate_95pct"]
    onset = []
    for turn in range(1, 9):
        r = report["new_failure_risk"][str(turn)]
        ci = intervals.get(str(turn))
        onset.append([turn, r["at_risk"], r["new_serious"],
                      f"{r['risk']:.1%}" if r["risk"] is not None else "unmeasured",
                      f"{ci[0]:.1%}–{ci[1]:.1%}" if ci else "unmeasured"])
    sections = table("First-error onset and uncertainty", ["Turn", "Reached without prior serious", "New serious", "Onset risk", "All-turn serious rate: 95% bootstrap interval"], onset)
    sections += "<p class='note'>Intervals use 200 trajectory-cluster bootstrap draws and describe all-turn serious rates, not onset risk. Sparse cells remain descriptive.</p>"
    sections += table("First serious failure", ["First serious turn / outcome", "Trajectories"], sorted(report["first_serious_distribution"].items()))
    sections += table("Observed endings", ["Terminal reason", "Trajectories"], sorted(report["ending_reasons"].items()))
    sections += table("No observed serious failure", ["Ending type", "Trajectories"], sorted(report["no_failure_endings"].items()))
    rec = report["recovery_summary"]
    sections += table("Recovery after a genuine earlier failure", ["Measure", "Value"], [
        ["Trajectories with an opportunity", rec["trajectories_with_opportunity"]],
        ["Trajectories with a successful repair", rec["successful_repairs"]],
        ["Observed recovery delays (assistant turns)", rec["recovery_delays"]],
        ["Repeated serious turns after onset", rec["repeated_serious_errors"]]])
    for axis in ("task", "language"):
        sections += table(f"Quality by {axis}", [axis.title(), "Trajectories", *qualities, "Scope"], [
            [key, v["trajectories"], *[v["quality"].get(q, 0) for q in qualities],
             "fewer than 5; descriptive only" if v["descriptive_only"] else "diagnostic pilot"]
            for key, v in sorted(report["views"][axis].items())])
    sections += table("Context token coverage", ["Input + current output tokens", "Trajectories", "Turns", *qualities], [
        [key, v["trajectories"], v["turns"], *[v["quality"].get(q, 0) for q in qualities]]
        for key, v in report["context_length_bins"].items()])
    sections += table("Every trajectory: failure, repair, and censoring", ["ID", "First serious", "Recovery opportunities", "First repair", "Repeated serious", "No-error ending", "Unjudgeable turns"], [
        [tid, v["first_serious_turn"] or "—", v["recovery_opportunity_turns"],
         v["recovery_success_turn"] or "—", v["repeated_serious_turns"], v["no_failure_kind"] or "—", v["unjudgeable_turns"]]
        for tid, v in sorted(report["trajectory_state"].items())])
    no_error = report["first_serious_distribution"].get("no_observed_error", 0)
    methods = table("Frozen measurement contract", ["Item", "Recorded value"], [
        ["Version", report["version"]], ["Statistical unit", "trajectory"],
        ["User policy SHA-256", report["user_policy_sha256"]],
        ["Annotation prompt SHA-256", report["annotation_prompt_sha256"]],
        ["Report freeze time (UTC)", report["created_utc"]],
        ["Sol calls at report freeze", report["call_ledger"]["sol_reserved_attempts"]],
        ["Recorded provider EUR at report freeze", f"{report['gpu_ledger']['spent_eur']:.6f}"]])
    coverage = []
    for axis, actual in report["actual_counts"].items():
        planned = report["planned_counts"].get(axis, {})
        for value in sorted(set(actual) | set(planned)):
            coverage.append([axis, value, planned.get(value, "not recorded"), actual.get(value, 0)])
    sections += table("Admission and observed coverage", ["Axis", "Cell", "Admitted plan", "Actual"], coverage)
    payload = json.dumps(report, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'><title>Dialogue quality and depth — {esc(report['stage'])}</title>
<style>:root{{color-scheme:light}}body{{background:#faf8f3;color:#192c40;font:16px/1.55 system-ui;margin:0 auto;max-width:1160px;padding:38px 24px}}h1,h2{{font-family:Georgia,serif;line-height:1.2}}h1{{font-size:clamp(30px,5vw,48px);max-width:900px}}h2{{font-size:25px;border-top:2px solid #b5c9ca;padding-top:20px;margin-top:42px}}p,figcaption{{max-width:920px}}.kicker,.note,figcaption{{color:#526776}}figure{{margin:0}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{text-align:left;vertical-align:top;border-bottom:1px solid #d9dcd9;padding:10px;overflow-wrap:anywhere}}th{{font-weight:650}}.heat td{{text-align:center;min-width:45px}}small{{display:block;color:#41525f}}.table-scroll{{overflow-x:auto;margin:18px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}}a{{color:#22658c}}@media(max-width:600px){{body{{padding:22px 14px}}th,td{{padding:7px}}h2{{font-size:22px}}}}@media print{{body{{max-width:none;padding:0;background:white}}table{{font-size:10px}}tr{{break-inside:avoid}}h2{{break-after:avoid}}*{{print-color-adjust:exact;-webkit-print-color-adjust:exact}}}}</style></head>
<body><p class='kicker'>APERTUS · RAW DIALOGUE MEASUREMENT · {esc(report['stage']).upper()}</p>
<h1>Where do errors begin, and when does recovery occur?</h1>
<p>{report['trajectory_count']} trajectories produced {report['observed_turns']} observed assistant turns; {no_error} trajectories had no observed serious error. These measurements precede preference-prefix selection.</p>
{heatmap}{sections}{methods}
<h2>Interpretation and limits</h2><p>One unselected target reply per raw turn. Natural completion and externally truncated histories have distinct endings. No unobserved suffix is counted as a success or failure. Language labels describe planned seed language; simulator language drift must be read with the final audit. These small, simulated conversations do not establish population rates or training benefit.</p>
<p>Candidate yield and the final cost reconciliation belong to the later <a href='final_recommendation.md'>recommendation</a>. The frozen report retains its pre-selection accounting snapshot.</p>
<p>Evidence: <a href='quality_depth_report.json'>report JSON</a> · <a href='trajectories.jsonl'>raw trajectory log</a> · <a href='annotations.jsonl'>annotations</a> · <a href='adjudications.jsonl'>adjudications</a> · <a href='../receipt.json'>receipts</a>.</p>
<script type='application/json' id='report-data'>{payload}</script></body></html>"""


def freeze_report(state: str | pathlib.Path, stage: str) -> dict[str, Any]:
    state = pathlib.Path(state)
    calibration_rows_path = state / stage / "calibration.jsonl"
    calibration_receipt_path = state / stage / "calibration_receipt.json"
    if not calibration_rows_path.exists() or not calibration_receipt_path.exists():
        raise ValueError("calibration sample and required-ID receipt must exist before report")
    calibration_receipt = read_json(calibration_receipt_path)
    if calibration_receipt.get("calibration_sha256") != sha256_text(calibration_rows_path.read_text(encoding="utf-8")):
        raise ValueError("calibration sample receipt hash mismatch")
    effective_boundaries = set(mandatory_boundary_rows(effective_annotations(state, stage)))
    previous_boundaries = set(calibration_receipt.get(
        "effective_boundary_ids", calibration_receipt.get("mandatory_boundary_ids", [])))
    boundaries_changed = effective_boundaries != previous_boundaries
    if boundaries_changed:
        calibration_receipt["effective_boundary_ids"] = sorted(effective_boundaries)
        calibration_receipt["required_review_ids"] = sorted(
            set(calibration_receipt.get("required_review_ids", [])) | effective_boundaries)
        calibration_receipt["boundary_recomputed_utc"] = utcnow()
        atomic_json(calibration_receipt_path, calibration_receipt)
    required_ids = set(calibration_receipt.get("required_review_ids", [])) | effective_boundaries
    decisions = {r["annotation_id"]: r for r in read_jsonl(state / stage / "adjudications.jsonl")}
    missing = sorted(required_ids - set(decisions))
    if missing:
        raise ValueError(f"calibration review incomplete after effective-boundary recompute: {len(missing)} required decisions missing")
    if boundaries_changed:
        raise ValueError("effective calibration boundary set changed; receipt updated, rerun to establish stability")
    annotations = {r["annotation_id"]: r for r in read_jsonl(state / stage / "annotations.jsonl")}
    changed = sum(decisions[aid]["decision"] != annotations[aid]["local_quality"] for aid in required_ids)
    change_share = changed / len(required_ids) if required_ids else 0
    if change_share > .2:
        raise ValueError("calibration severity changes exceed 20%; revise rubric and reannotate affected class")
    report = build_report(state, stage)
    report["calibration_review"] = {"required": len(required_ids), "reviewed": len(required_ids),
                                    "substantive_severity_changes": changed, "change_share": change_share,
                                    "mandatory_boundaries": len(effective_boundaries),
                                    "effective_boundary_ids": sorted(effective_boundaries),
                                    "boundary_set_stable": True}
    directory = state / stage
    json_path = directory / "quality_depth_report.json"
    html_path = directory / "quality_depth_report.html"
    if json_path.exists():
        raise ValueError("quality-depth report is already frozen")
    atomic_json(json_path, report)
    html_text = render_html(report)
    html_path.write_text(html_text, encoding="utf-8")
    receipt_path = state / "receipt.json"
    receipt = read_json(receipt_path) if receipt_path.exists() else {"artifacts": {}}
    receipt.setdefault("artifacts", {})[f"{stage}/quality_depth_report.json"] = {
        "sha256": sha256_text(json_path.read_text(encoding="utf-8")), "created_utc": utcnow(), "frozen": True}
    receipt["artifacts"][f"{stage}/quality_depth_report.html"] = {
        "sha256": sha256_text(html_text), "created_utc": utcnow(), "frozen": True}
    atomic_json(receipt_path, receipt)
    return report
