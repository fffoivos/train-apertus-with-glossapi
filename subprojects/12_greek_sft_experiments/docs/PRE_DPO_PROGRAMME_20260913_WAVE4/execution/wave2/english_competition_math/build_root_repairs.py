#!/usr/bin/env python3
"""Build bounded root repairs for the six repairable OpenMath pilot families."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "proof_review_queue.v1.jsonl"

REPAIRS = {
    "openmath1m_45587": r"""The graph is a rhombus with vertices $(10,0)$, $(0,5)$, $(-10,0)$, and $(0,-5)$. Its diagonals therefore have lengths $20$ and $10$. The area of a rhombus is half the product of its diagonals, so
\[
\frac{20\cdot 10}{2}=\boxed{100}.
\]""",
    "openmath1m_13542": r"""Let $t$ and $p$ be the numbers of triangular and pentagonal faces. Counting face-vertex incidences gives
\[
t=\frac{VT}{3},\qquad p=\frac{VP}{5},\qquad
V\left(\frac{T}{3}+\frac{P}{5}\right)=32.
\]
Every vertex has degree $d=T+P$, so $E=Vd/2$. Euler's formula gives
\[
V-\frac{Vd}{2}+32=2,
\]
hence $V(d-2)=60$. A convex polyhedron has $3\le d<6$, so $d$ is $3$, $4$, or $5$. Using $P=d-T$ in the face equation and substituting $V=60/(d-2)$ yields
\[
2T=5d-16.
\]
Only $d=4$ gives an integer solution: $T=2$, $P=2$, and $V=30$. Therefore
\[
100P+10T+V=200+20+30=\boxed{250}.
\]""",
    "openmath1m_272973": r"""The largest possible product is obtained from the largest numbers of the two permitted lengths:
\[
9999\cdot999=9999(1000-1)=9{,}989{,}001.
\]
This product has seven digits, so the greatest possible number of digits is $\boxed{7}$.""",
    "openmath1m_61134": r"""The five existing times in order are $86,88,94,96,97$. With six observations, the median is the average of the third and fourth values. To obtain a median of $92$, the new time must lie below $94$, making $94$ the fourth value. If the new time is $x$, then
\[
\frac{x+94}{2}=92,
\]
so $x=\boxed{90}$, which indeed produces $86,88,90,94,96,97$.""",
    "openmath1m_98805": r"""Use the grid coordinates shown in the diagram. For unit squares, the five row counts are $3,5,5,5,3$, giving $21$. For $2\times2$ squares, the four row counts are $2,4,4,2$, giving $12$. For $3\times3$ squares, the three row counts are $1,3,1$, giving $5$. The shortened outer boundary prevents any $4\times4$ or $5\times5$ square. Hence the total is
\[
21+12+5=\boxed{38}.
\]""",
    "openmath1m_178865": r"""Both inverse-sine terms require $0\le x\le1$. Taking sine of the equation and using the principal-value square roots gives
\[
x\sqrt{2x-x^2}+(1-x)\sqrt{1-x^2}=\sqrt{1-x^2}.
\]
Thus
\[
x\sqrt{2x-x^2}=x\sqrt{1-x^2}.
\]
If $x=0$, the original equation holds. If $x>0$, divide by $x$, square, and simplify:
\[
2x-x^2=1-x^2,
\]
so $x=\tfrac12$. Direct substitution confirms this value as well. Therefore
\[
\boxed{x=0,\ \frac12}.
\]""",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = [json.loads(line) for line in SOURCE.read_text().splitlines() if line]
    by_id = {row["id"]: row for row in rows}
    assert set(REPAIRS) <= set(by_id)
    repaired = []
    for source_id, answer in REPAIRS.items():
        row = json.loads(json.dumps(by_id[source_id]))
        row["id"] = source_id + ".root_repair_v1"
        row["messages"][1]["content"] = answer
        row["solution_sha256"] = hashlib.sha256(answer.encode()).hexdigest()
        row["status"] = "root_repaired_independent_review_pending"
        row["repair_provenance"] = {
            "source_id": source_id,
            "source_solution_sha256": by_id[source_id]["solution_sha256"],
            "scope": "replace defective derivation only; problem and expected answer unchanged",
        }
        repaired.append(row)
    output = HERE / "root_repairs.v1.jsonl"
    output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in repaired))
    receipt = {
        "schema": "openmath_root_repairs_receipt_v1",
        "status": "six_repairs_built_independent_review_pending",
        "input": {SOURCE.name: sha256(SOURCE)},
        "repair_count": len(repaired),
        "family_count": len({row["family_sha256"] for row in repaired}),
        "output": {output.name: sha256(output)},
        "held_without_repair": [
            "intermediate-algebra infinite-series family: source candidates require a fresh verified derivation",
            "precalculus vector-incidence family: source candidate does not derive the asserted dot product"
        ],
        "training_eligible": False,
        "next_gate": "independent mathematical review of all 27 root selections and six root repairs"
    }
    (HERE / "root_repairs_receipt.v1.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
