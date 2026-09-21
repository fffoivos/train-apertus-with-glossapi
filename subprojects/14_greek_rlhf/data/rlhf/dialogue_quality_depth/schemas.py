"""Dataclasses and strict lightweight validation for all persisted artifacts."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar

from common import sha256_json, sha256_text


class ValidationError(ValueError):
    pass


def _required(data: dict[str, Any], fields: tuple[str, ...], kind: str) -> None:
    missing = [name for name in fields if name not in data]
    if missing:
        raise ValidationError(f"{kind}: missing {', '.join(missing)}")


def validate_messages(messages: Any, *, end_role: str | None = None) -> list[dict[str, str]]:
    if not isinstance(messages, list) or not messages:
        raise ValidationError("messages must be a non-empty list")
    for i, message in enumerate(messages):
        if not isinstance(message, dict) or set(message) != {"role", "content"}:
            raise ValidationError(f"message {i}: exactly role/content required")
        expected = "user" if i % 2 == 0 else "assistant"
        if message["role"] != expected or not isinstance(message["content"], str) or not message["content"].strip():
            raise ValidationError(f"message {i}: invalid alternating dialogue")
    if end_role and messages[-1]["role"] != end_role:
        raise ValidationError(f"messages must end in {end_role}")
    return messages


def prefix_sha256(messages: list[dict[str, str]]) -> str:
    validate_messages(messages, end_role="user")
    return sha256_json(messages)


@dataclass(frozen=True)
class Seed:
    trajectory_id: str
    stage: str
    split: str
    instance_hash: str
    content_family: str
    family: str
    task: str
    language: str
    difficulty: str
    interaction: str
    attitude: str
    register: str
    max_assistant_turns: int
    fixture: dict[str, Any]
    private_fields: tuple[str, ...] = ("reference", "checks", "instruction_spec")

    def __post_init__(self) -> None:
        if self.stage not in {"smoke", "measurement"} or self.split not in {"smoke", "train"}:
            raise ValidationError("invalid seed stage/split")
        if self.max_assistant_turns not in {3, 8}:
            raise ValidationError("pilot horizons are exactly 3 or 8")
        _required(self.fixture, ("content", "instruction_spec", "reference", "checks", "parameters"), "fixture")

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["private_fields"] = list(self.private_fields)
        return row

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Seed":
        values = dict(data)
        values["private_fields"] = tuple(values.get("private_fields", ("reference", "checks", "instruction_spec")))
        return cls(**values)


@dataclass(frozen=True)
class Event:
    event_id: str
    trajectory_id: str
    stage: str
    kind: str
    turn_index: int
    message: dict[str, str] | None
    created_utc: str
    receipt: dict[str, Any] = field(default_factory=dict)

    KINDS: ClassVar[set[str]] = {"user", "assistant", "terminal"}

    def __post_init__(self) -> None:
        if self.kind not in self.KINDS or self.turn_index < 0:
            raise ValidationError("invalid event")
        if self.kind != "terminal":
            if not self.message or self.message.get("role") != self.kind or not isinstance(self.message.get("content"), str):
                raise ValidationError("event message mismatch")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


TERMINAL_CODES = {"completed", "horizon", "context_limit", "truncated_output", "infra_failure", "ambiguous_timeout"}


@dataclass(frozen=True)
class Trajectory:
    trajectory_id: str
    stage: str
    messages: list[dict[str, str]]
    assistant_turns: int
    terminal_code: str | None = None
    terminal_detail: str | None = None
    instance_hash: str = ""
    content_family: str = ""
    split: str = ""

    def __post_init__(self) -> None:
        validate_messages(self.messages)
        if sum(m["role"] == "assistant" for m in self.messages) != self.assistant_turns:
            raise ValidationError("assistant turn count mismatch")
        if self.terminal_code is not None and self.terminal_code not in TERMINAL_CODES:
            raise ValidationError("invalid terminal code")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SEVERITIES = {"good", "minor", "serious", "unjudgeable"}
DIMENSIONS = ("correctness", "instruction_following", "memory", "uncertainty_premise", "helpfulness", "safety", "tone")


@dataclass(frozen=True)
class Annotation:
    annotation_id: str
    trajectory_id: str
    turn_index: int
    prefix_sha256: str
    response_sha256: str
    language: str
    task: str
    input_tokens: int
    output_tokens: int
    cumulative_tokens: int
    dimensions: dict[str, str]
    local_quality: str
    issue_tags: list[str]
    evidence: list[str]
    confidence: str
    new_error: bool
    propagated_error: bool
    recovery_opportunity: bool
    recovery_success: bool
    verifier_result: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.turn_index < 1 or self.local_quality not in SEVERITIES:
            raise ValidationError("invalid annotation severity/turn")
        if self.confidence not in {"low", "medium", "high"}:
            raise ValidationError("invalid confidence")
        if set(self.dimensions) != set(DIMENSIONS):
            raise ValidationError("all annotation dimensions are required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Adjudication:
    annotation_id: str
    trajectory_id: str
    turn_index: int
    decision: str
    evidence: str
    reviewer: str

    def __post_init__(self) -> None:
        if self.decision not in SEVERITIES or not self.evidence.strip() or not self.reviewer.strip():
            raise ValidationError("invalid adjudication")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Selection:
    selection_id: str
    trajectory_id: str
    kind: str
    depth: int
    prefix_messages: list[dict[str, str]]
    prefix_sha256: str
    original_response: str
    inclusion_receipt: dict[str, Any]
    language: str
    task: str

    def __post_init__(self) -> None:
        if self.kind not in {"P", "R", "C"}:
            raise ValidationError("selection kind must be P/R/C")
        validate_messages(self.prefix_messages, end_role="user")
        if prefix_sha256(self.prefix_messages) != self.prefix_sha256:
            raise ValidationError("selection prefix hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    selection_id: str
    source: str
    text: str
    text_sha256: str
    prefix_sha256: str
    finish_reason: str
    model: str
    usage: dict[str, Any]

    def __post_init__(self) -> None:
        if self.source not in {"original", "new"} or sha256_text(self.text) != self.text_sha256:
            raise ValidationError("invalid candidate source/hash")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Preference:
    id: str
    prefix_messages: list[dict[str, str]]
    prefix_sha256: str
    chosen: str
    rejected: str
    chosen_source: str
    rejected_source: str
    selection_kind: str
    depth: int
    language: str
    task: str
    trajectory_id: str
    receipt: dict[str, Any]

    def __post_init__(self) -> None:
        validate_messages(self.prefix_messages, end_role="user")
        if prefix_sha256(self.prefix_messages) != self.prefix_sha256 or self.chosen == self.rejected:
            raise ValidationError("preference prefix/pair invalid")
        if self.selection_kind not in {"P", "R", "C"} or self.depth < 1:
            raise ValidationError("invalid preference selection kind/depth")
        if self.chosen_source not in {"original", "new"} or self.rejected_source not in {"original", "new"}:
            raise ValidationError("invalid preference sources")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Receipt:
    artifact: str
    sha256: str
    created_utc: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_row(kind: str, data: dict[str, Any]) -> Any:
    classes = {
        "seed": Seed, "event": Event, "trajectory": Trajectory, "annotation": Annotation,
        "adjudication": Adjudication, "selection": Selection, "candidate": Candidate,
        "preference": Preference, "receipt": Receipt,
    }
    if kind not in classes:
        raise ValidationError(f"unknown schema kind {kind}")
    cls = classes[kind]
    if cls is Seed:
        return Seed.from_dict(data)
    return cls(**data)
