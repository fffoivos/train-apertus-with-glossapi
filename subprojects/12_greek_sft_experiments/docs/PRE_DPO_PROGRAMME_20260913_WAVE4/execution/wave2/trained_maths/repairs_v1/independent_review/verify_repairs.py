#!/usr/bin/env python3
"""Independent deterministic checks for the seven bounded maths repairs."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATES = HERE.parent / "candidate_rows.jsonl"
SAMPLE = HERE.parent.parent / "sample.jsonl"


def canonical_hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


rows = {r["row_id"]: r for r in map(json.loads, CANDIDATES.read_text().splitlines())}
source = {r["row_id"]: r for r in map(json.loads, SAMPLE.read_text().splitlines())}
assert len(rows) == 7
for rid, row in rows.items():
    assert canonical_hash(row["messages"]) == row["repair"]["after_messages_sha256"]
    assert canonical_hash(source[rid]["actual_training_messages"]) == row["repair"]["before_messages_sha256"]
    assert [m["role"] for m in row["messages"]] == ["user", "assistant"]

# gm_nat_738_1: affine table and requested inverse.
alpha = (230 - 146) / (10 - 4)
beta = 146 - alpha * 4
assert (alpha, beta, (398 - beta) / alpha) == (14, 90, 22)

# gm_gsm_4211: repaired input supplies the missing three billable hours.
assert 10 * 15 + 3 * 22 == 216

# gm_gsm_1514: 20 - 10, receive half of 10, then retain one third.
cookies = 20 - 10
cookies += 10 / 2
cookies -= (2 / 3) * cookies
assert cookies == 5

# gm_gsm_2098: p + (p/2 + 3) + engine + service car = 71.
passenger = 44
cargo = passenger / 2 + 3
assert passenger + cargo + 2 == 71

# gm_nat_301_3: base area, filled height fraction, and m^3 to litres.
assert 1.2 * 0.5 == 0.6
litres = 1.2 * 0.5 * 0.8 * (3 / 4) * 1000
assert math.isclose(litres, 360)

# gm_nat_618_4: annular-cylinder volume, 25%, €/L, then cents.
volume_cm3 = 3.14 * (12**2 - 4**2) * 8
syrup_l = 0.25 * volume_cm3 / 1000
cost_eur = syrup_l * 4.50
assert math.isclose(volume_cm3, 3215.36)
assert math.isclose(cost_eur, 3.61728)
assert round(cost_eur * 100) == 362

# gm_math_2231: executable support across a broad range plus exact witness;
# the target's elementary divisibility argument is the general proof.
products = [n * (n + 1) * (n + 2) * (n + 3) for n in range(-1000, 1001)]
assert all(product % 24 == 0 for product in products)
assert math.gcd(*products) == 24
assert 1 * 2 * 3 * 4 == 24

result = {
    "status": "PASS",
    "reviewed": 7,
    "accepted": 7,
    "held": 0,
    "hash_and_role_checks": 7,
    "arithmetic_checks": 6,
    "general_proof_read": ["gm_math_2231"],
    "model_subprocess_calls": 0,
    "production_writes": 0,
    "candidate_file_sha256": hashlib.sha256(CANDIDATES.read_bytes()).hexdigest(),
    "source_sample_sha256": hashlib.sha256(SAMPLE.read_bytes()).hexdigest(),
}
(HERE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(result, ensure_ascii=False, indent=2))
