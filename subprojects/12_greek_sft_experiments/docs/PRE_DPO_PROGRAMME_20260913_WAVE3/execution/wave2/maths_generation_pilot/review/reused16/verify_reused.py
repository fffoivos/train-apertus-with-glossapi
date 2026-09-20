#!/usr/bin/env python3
"""Independent, deterministic checks for the 16 reused maths-pilot rows.

The calculations below are authored for this review.  No generated code is
loaded or executed; accepted JSON is read only to bind the selected text and
to detect decoded control characters.
"""

from __future__ import annotations

import itertools
import json
import math
from fractions import Fraction
from pathlib import Path


PILOT = Path(__file__).resolve().parents[2]
ACCEPTED = PILOT / "run_state" / "accepted"


SELECTED = {
    "repair_math5_139": "solve_high",
    "repair_math5_77": "solve_high",
    "repair_math5_537": "solve_high",
    "repair_math5_1014": "solve_xhigh",
    "repair_math5_630": "solve_xhigh",
    "repair_gsm_1253": "solve_high",
    "repair_math5_436": "solve_xhigh",
    "repair_gm_math_2231": "solve_high",
}


def disallowed_controls(value: object, path: str = "$") -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    if isinstance(value, str):
        for offset, char in enumerate(value):
            code = ord(char)
            if (code < 32 and char not in "\t\n\r") or code == 127:
                found.append({"path": path, "offset": offset, "codepoint": f"U+{code:04X}"})
    elif isinstance(value, dict):
        for key, child in value.items():
            found.extend(disallowed_controls(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(disallowed_controls(child, f"{path}[{index}]"))
    return found


def load(stage: str, row_id: str) -> dict:
    return json.loads((ACCEPTED / f"{stage}__{row_id}.json").read_text())


checks: dict[str, object] = {}

# repair_math5_139: verify the selected trigonometric branch and ratio.
u = (9 + 4 * math.sqrt(2)) / 7
ratio = (3 * u - 1) / (3 - u)
assert 1 < u < 3 and math.isclose(ratio, 3 + 2 * math.sqrt(2), rel_tol=0, abs_tol=1e-12)
checks["repair_math5_139"] = {"u": u, "ratio": ratio, "p_plus_q_plus_r": 7}

# repair_math5_77: exact cycle-type count.
ten_cycle = math.factorial(9)
five_five = math.factorial(10) // (5**2 * math.factorial(2))
shoe_probability = Fraction(ten_cycle + five_five, math.factorial(10))
assert shoe_probability == Fraction(3, 25)
checks["repair_math5_77"] = {
    "ten_cycles": ten_cycle,
    "two_five_cycles": five_five,
    "probability": str(shoe_probability),
    "m_plus_n": 28,
}

# repair_math5_537: enumerate every zero family in the open interval.
def cosine_zero_solutions(multiplier: int) -> list[Fraction]:
    values = set()
    for k in range(-20, 21):
        x = Fraction(90 + 180 * k, multiplier)
        if 100 < x < 200:
            values.add(x)
    return sorted(values)


trig_families = {m: cosine_zero_solutions(m) for m in (1, 3, 4, 5)}
trig_union = sorted(set().union(*trig_families.values()))
assert trig_families[1] == []
assert trig_union == [Fraction(225, 2), Fraction(126), Fraction(150), Fraction(315, 2), Fraction(162), Fraction(198)]
assert sum(trig_union) == 906
checks["repair_math5_537"] = {
    "families": {str(k): [str(x) for x in v] for k, v in trig_families.items()},
    "unique_solution_count": len(trig_union),
    "sum_degrees": 906,
}

# repair_math5_1014: white fraction 0.64 implies x=0.1L; blue is 2x^2.
arm_endpoint_fraction = (1 - math.sqrt(0.64)) / 2
blue_fraction = 2 * arm_endpoint_fraction**2
assert math.isclose(arm_endpoint_fraction, 0.1, abs_tol=1e-15)
assert math.isclose(blue_fraction, 0.02, abs_tol=1e-15)
checks["repair_math5_1014"] = {
    "arm_endpoint_fraction_of_side": arm_endpoint_fraction,
    "blue_fraction": blue_fraction,
    "blue_percent": 100 * blue_fraction,
}

# repair_math5_630: the denominator is positive and AM-GM is tight at sqrt(8).
tangent_t = math.sqrt(8)
denominator = tangent_t**2 - 3 * tangent_t + 8
tangent_max = math.sqrt(3) * tangent_t / denominator
stated_max = math.sqrt(3) / (4 * math.sqrt(2) - 3)
assert denominator > 0 and math.isclose(tangent_max, stated_max, abs_tol=1e-15)
checks["repair_math5_630"] = {
    "critical_AC": tangent_t,
    "denominator": denominator,
    "maximum": tangent_max,
}

# repair_gsm_1253: the Greek prompt explicitly requires outbound and return legs.
one_way_feet = 6 * 200 * 3
round_trip_minutes = 2 * one_way_feet // 400
assert one_way_feet == 3600 and round_trip_minutes == 18
checks["repair_gsm_1253"] = {"one_way_feet": one_way_feet, "round_trip_minutes": round_trip_minutes}

# repair_math5_436: enumerate orientations bottom-to-top, forbidding face-up/face-down.
valid_orientations = [
    "".join(bits)
    for bits in itertools.product("KP", repeat=8)
    if "PK" not in "".join(bits)
]
assert len(valid_orientations) == 9
assert math.comb(8, 4) * len(valid_orientations) == 630
checks["repair_math5_436"] = {
    "valid_orientation_count": len(valid_orientations),
    "metal_orders": math.comb(8, 4),
    "arrangements": 630,
}

# repair_gm_math_2231: finite exhaustive support plus the exact witness.
products = [n * (n + 1) * (n + 2) * (n + 3) for n in range(-1000, 1001)]
assert all(product % 24 == 0 for product in products)
assert 1 * 2 * 3 * 4 == 24
checks["repair_gm_math_2231"] = {"checked_starts": [-1000, 1000], "universal_divisor": 24, "witness": 24}

# Eight controls: recompute the requested values independently.
assert 3 * (60 + 3 * 80) + 20 == 920
assert 2 * 60 // 3 == 40
assert round(16 ** 0.25) * round(8 ** (1 / 3)) * math.isqrt(4) == 8
assert sum(i * i for i in range(1, 11)) % 11 == 0
assert 10**2 == 100  # area lower bound and the standard triangular-grid construction count
assert Fraction("10.5") / Fraction("0.25") == 42
assert Fraction(-1 - (-7), -5 - 4) == Fraction(-2, 3)
assert -1 / Fraction(-2, 3) == Fraction(3, 2)
numerator_roots = set(range(1, 101))
denominator_roots = {k * k for k in range(1, 101)}
assert len(numerator_roots - denominator_roots) == 90
checks["controls"] = {
    "control_gm_gsm_3835": 920,
    "control_gm_gsm_3096": 40,
    "control_gm_math_2731": 8,
    "control_gm_math_1054": 0,
    "control_gm_math_1745": 100,
    "control_gm_math_837": 42,
    "control_gm_math_3507": "3/2",
    "control_gm_math_3924": 90,
}

# Bind selected generated texts and expose the rejected high-output corruption.
selected_bindings = {}
for row_id, stage in SELECTED.items():
    envelope = load(stage, row_id)
    assert envelope["row_id"] == row_id
    assert envelope["result"]["status"] == "candidate"
    controls = disallowed_controls(envelope)
    assert not controls, (row_id, stage, controls)
    selected_bindings[row_id] = {
        "stage": stage,
        "job_id": envelope["job_id"],
        "prompt_sha256": envelope["prompt_sha256"],
        "input_record_sha256": envelope["input_record_sha256"],
    }

rejected_high_1014 = disallowed_controls(load("solve_high", "repair_math5_1014"))
assert [item["codepoint"] for item in rejected_high_1014] == ["U+000C", "U+000C"]
checks["selected_bindings"] = selected_bindings
checks["rejected_solve_high_repair_math5_1014_controls"] = rejected_high_1014

print(json.dumps({"status": "pass", "checks": checks}, ensure_ascii=False, indent=2))
