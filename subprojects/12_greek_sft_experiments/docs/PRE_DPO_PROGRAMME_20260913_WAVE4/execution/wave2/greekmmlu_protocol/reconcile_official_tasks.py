#!/usr/bin/env python3
"""Map the pinned All/test rows and frozen diagnostic IDs to official task configs."""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import re
from pathlib import Path

import pyarrow.parquet as pq


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"missing literal assignment {name}")


def config_counts_from_card(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    data = text.split("dataset_info:\n", 1)[1]
    counts = {}
    for block in re.split(r"(?m)^- config_name: ", data)[1:]:
        name, body = block.split("\n", 1)
        match = re.search(r"(?ms)^  splits:\n  - name: test\n.*?^    num_examples: (\d+)$", body)
        if not match:
            raise ValueError(f"no test count for {name}")
        counts[name.strip()] = int(match.group(1))
    return counts


def norm(value: str) -> str:
    return value.replace("&", "and").replace(" ", "_")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--contents", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    expected = {
        "parquet": "b77d269150c4c6e3441cfb20d52534f9aebd2c8c33883d0df7d61b3bc06129f5",
        "ids": "58ab651789059df8f69c19b1fc5346f3a6bc8ed7a0c08d8951b090c1feb56978",
        "generator": "a53092f2caabacd682fdb7160da33d308ef2c4a56383cb33f8e846c5835b8ba0",
        "card": "b166a19deb7d034c90e5c2b3092dadf12f630e6bdc0b8b4d24c86bcb95329a1c",
    }
    for key in expected:
        if sha(getattr(args, key)) != expected[key]:
            raise ValueError(f"{key} hash mismatch")

    with_levels = literal_assignment(args.generator, "SUBJECTS_WITH_LEVELS")
    without_levels = literal_assignment(args.generator, "SUBJECTS_WITHOUT_LEVELS")
    split_subjects = {norm(subject) for subject in with_levels}
    declared_subjects = split_subjects | {norm(subject) for subject in without_levels} | {"Maritime_Safety_and_Rescue_Operations"}

    card_counts = config_counts_from_card(args.card)
    if card_counts.get("All") != 16632 or len(card_counts) != 46:
        raise ValueError(f"card config drift: {len(card_counts)} configs, All={card_counts.get('All')}")
    official_configs = set(card_counts) - {"All"}

    contents = json.loads(args.contents.read_text(encoding="utf-8"))
    task_files = sorted(item["name"] for item in contents if item["name"].startswith("greekmmlu_") and item["name"].endswith(".yaml"))
    if len(task_files) != 45:
        raise ValueError(f"official task file count drift: {len(task_files)}")

    table = pq.read_table(args.parquet)
    if table.num_rows != 16632:
        raise ValueError(f"parquet row drift: {table.num_rows}")
    records = table.to_pylist()
    selections = [json.loads(line) for line in args.ids.read_text(encoding="utf-8").split("\n") if line.strip()]
    if len(selections) != 200 or len({row["example_id"] for row in selections}) != 200:
        raise ValueError("selection drift")
    selected_indices = {int(row["dataset_row_index"]) for row in selections}

    full_counts = collections.Counter()
    selected_counts = collections.Counter()
    strata_by_config: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)
    selected_strata_by_config: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)
    groups_by_config: dict[str, set[str]] = collections.defaultdict(set)
    for index, row in enumerate(records):
        subject = norm(str(row["subject"]))
        if subject not in declared_subjects:
            raise ValueError(f"undeclared subject form {row['subject']!r}")
        config = f"{subject}_{norm(str(row['level']))}" if subject in split_subjects else subject
        if config not in official_configs:
            raise ValueError(f"row maps outside official configs: {row['subject']!r}/{row['level']!r} -> {config}")
        full_counts[config] += 1
        strata_by_config[config].add((str(row["subject"]), str(row["level"])))
        groups_by_config[config].add(str(row["group"]))
        if index in selected_indices:
            selected_counts[config] += 1
            selected_strata_by_config[config].add((str(row["subject"]), str(row["level"])))

    count_mismatches = {name: {"all_config": full_counts[name], "official_config": card_counts[name]}
                        for name in official_configs if full_counts[name] != card_counts[name]}
    if count_mismatches:
        raise ValueError(f"All/config count mismatch: {count_mismatches}")
    if set(selected_counts) != official_configs:
        raise ValueError(f"fixed selection misses official configs: {sorted(official_configs - set(selected_counts))}")

    rows = []
    for config in sorted(official_configs):
        rows.append({
            "official_dataset_config": config,
            "official_task_file": ("greekmmlu_qa_maritime_safety_and_rescue_operations.yaml" if config == "Maritime_Safety_and_Rescue_Operations"
                                   else f"greekmmlu_{config.lower()}.yaml"),
            "population_rows": full_counts[config], "selected_rows": selected_counts[config],
            "all_config_subject_level_strata": [list(value) for value in sorted(strata_by_config[config])],
            "selected_subject_level_strata": [list(value) for value in sorted(selected_strata_by_config[config])],
            "groups": sorted(groups_by_config[config]),
        })

    payload = {
        "schema_version": "greekmmlu_all_to_official_tasks_v1",
        "status": "passed_not_launched",
        "dataset": {"repo_id": "dascim/GreekMMLU", "revision": "6a03aa06b68beb932fb75edff3a34e50b3674649",
                    "all_config_test_rows": 16632, "official_dataset_configs_excluding_all": 45},
        "official_code": {"repo": "mersinkonomi/GreekMMLU", "commit": "cd944748e860fda3e9dc21212c2f2710615ecdc5",
                          "task_yaml_files": len(task_files)},
        "reconciliation": {
            "observed_subject_level_strata": len({(str(row["subject"]), str(row["level"])) for row in records}),
            "official_task_configs": len(rows),
            "configs_with_multiple_observed_strata": sum(len(strata_by_config[name]) > 1 for name in official_configs),
            "population_count_mismatches": 0,
            "population_sum": sum(full_counts.values()),
            "selected_rows": sum(selected_counts.values()),
            "selected_configs": len(selected_counts),
            "explanation": "The official suite collapses every observed level for 17 unsplit subjects into one task, retains subject+level tasks for 12 declared split subjects, and adds the maritime task. The All config therefore has 61 raw subject-level strata but maps losslessly to 45 task configs.",
        },
        "bindings": {"parquet_sha256": sha(args.parquet), "selection_sha256": sha(args.ids),
                     "official_generator_sha256": sha(args.generator), "dataset_card_sha256": sha(args.card),
                     "official_contents_sha256": sha(args.contents)},
        "aggregation_gate": "For the fixed200 diagnostic, report paired item-level micro accuracy and protocol disagreement on identical IDs. The subset is not proportionally sampled within all 45 tasks, so do not label its aggregate an official full-suite reproduction.",
        "measurement_launched": False,
        "tasks": rows,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["reconciliation"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
