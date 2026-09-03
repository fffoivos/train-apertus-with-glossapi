"""lm-evaluation-harness result processing for Greek IFEval."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, NamedTuple, Optional, Union


# External task modules are loaded by file path by lm-eval. Add only the task
# parent, then import the sibling package by its unique name to avoid a generic
# ``instructions`` module collision with other external tasks.
_TASKS_DIR = str(Path(__file__).resolve().parent.parent)
if _TASKS_DIR not in sys.path:
    sys.path.insert(0, _TASKS_DIR)
from ifeval_greek import instructions_registry  # noqa: E402


class InputExample(NamedTuple):
    key: int
    instruction_id_list: list[str]
    prompt: str
    kwargs: list[Dict[str, Optional[Union[str, int, float, list[str]]]]]


class OutputExample(NamedTuple):
    instruction_id_list: list[str]
    prompt: str
    response: str
    follow_all_instructions: bool
    follow_instruction_list: list[bool]


def _evaluate(inp: InputExample, response: str) -> OutputExample:
    following = []
    for index, instruction_id in enumerate(inp.instruction_id_list):
        checker = instructions_registry.INSTRUCTION_DICT[instruction_id](instruction_id)
        kwargs = {key: value for key, value in inp.kwargs[index].items() if value is not None}
        checker.build_description(**kwargs)
        args = checker.get_instruction_args()
        if args and "prompt" in args:
            checker.build_description(prompt=inp.prompt)
        following.append(bool(response.strip()) and checker.check_following(response))
    return OutputExample(
        instruction_id_list=inp.instruction_id_list,
        prompt=inp.prompt,
        response=response,
        follow_all_instructions=all(following),
        follow_instruction_list=following,
    )


def test_instruction_following_strict(inp, response):
    return _evaluate(inp, response)


def test_instruction_following_loose(inp, response):
    lines = response.split("\n")
    variants = [
        response,
        response.replace("*", ""),
        "\n".join(lines[1:]).strip(),
        "\n".join(lines[:-1]).strip(),
        "\n".join(lines[1:-1]).strip(),
    ]
    variants.extend(variant.replace("*", "") for variant in variants[2:])

    per_instruction = []
    for index, instruction_id in enumerate(inp.instruction_id_list):
        checker = instructions_registry.INSTRUCTION_DICT[instruction_id](instruction_id)
        kwargs = {key: value for key, value in inp.kwargs[index].items() if value is not None}
        checker.build_description(**kwargs)
        per_instruction.append(
            any(variant.strip() and checker.check_following(variant) for variant in variants)
        )
    return OutputExample(
        instruction_id_list=inp.instruction_id_list,
        prompt=inp.prompt,
        response=response,
        follow_all_instructions=all(per_instruction),
        follow_instruction_list=per_instruction,
    )


def process_results(doc, results):
    inp = InputExample(
        key=doc["key"],
        instruction_id_list=doc["instruction_id_list"],
        prompt=doc["prompt"],
        kwargs=doc["kwargs"],
    )
    strict = test_instruction_following_strict(inp, results[0])
    loose = test_instruction_following_loose(inp, results[0])
    return {
        "prompt_level_strict_acc": strict.follow_all_instructions,
        "inst_level_strict_acc": strict.follow_instruction_list,
        "prompt_level_loose_acc": loose.follow_all_instructions,
        "inst_level_loose_acc": loose.follow_instruction_list,
    }


def agg_inst_level_acc(items):
    flat = [item for sublist in items for item in sublist]
    return sum(flat) / len(flat)
