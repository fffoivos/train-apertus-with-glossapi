"""Prompt-ready glossary access (spec §6): send only the definitions of the values a call uses, verbatim.

The glossary file is owned by the orchestrator and may change during the run; every call records the sha16 of the
bytes it actually read.
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field

from common import GLOSSARY_PATH, sha256_text

SECTION_KEYS = {
    "Attitude": "attitude", "Register": "register", "Difficulty": "difficulty", "Interaction": "interaction",
    "Task": "task", "Detail": "detail", "Forum task_type": "forum_task_type", "Premise status": "premise_status",
    "Safety context": "safety_context", "Response to failure": "moves", "Dialogue terms": "dialogue_terms",
    "Judgement calls": "judgement_calls",
}


@dataclass
class Section:
    heading: str
    lines: list[str]
    entries: dict[str, list[str]] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)


class GlossaryError(KeyError):
    pass


class Glossary:
    def __init__(self, text: str, path: pathlib.Path | None = None):
        self.text = text
        self.path = path
        self.sha16 = sha256_text(text)[:16]
        self.sections: dict[str, Section] = {}
        self._parse()

    @classmethod
    def load(cls, path: pathlib.Path | str = GLOSSARY_PATH) -> "Glossary":
        p = pathlib.Path(path)
        return cls(p.read_text(encoding="utf-8"), p)

    def _parse(self) -> None:
        current: Section | None = None
        for line in self.text.splitlines():
            if line.startswith("## "):
                heading = line[3:].strip()
                key = next((v for k, v in SECTION_KEYS.items() if heading.startswith(k)), None)
                current = Section(heading, []) if key else None
                if key:
                    self.sections[key] = current
                continue
            if current is not None:
                current.lines.append(line)
        for section in self.sections.values():
            last: str | None = None
            for line in section.lines:
                match = re.match(r"^- ([^:]+?)(?: \([^)]*\))?: ", line)
                if match:
                    last = match.group(1).strip()
                    section.entries[last] = [line]
                    section.order.append(last)
                elif line.startswith("  ") and last is not None:
                    section.entries[last].append(line)
                else:
                    last = None

    def entry(self, section: str, value: str) -> str:
        sec = self.sections.get(section)
        if sec is None or value not in sec.entries:
            raise GlossaryError(f"glossary has no definition for {section}={value!r} (sha16 {self.sha16})")
        return "\n".join(sec.entries[value])

    def section_paragraphs(self, section: str) -> list[str]:
        sec = self.sections[section]
        paragraphs, buf = [], []
        for line in sec.lines:
            if not line.strip():
                if buf:
                    paragraphs.append("\n".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            paragraphs.append("\n".join(buf))
        return paragraphs

    def paragraph(self, section: str, prefix: str, only_bullets: list[str] | None = None) -> str:
        for para in self.section_paragraphs(section):
            if para.startswith(prefix):
                if only_bullets is None:
                    return para
                lines = para.splitlines()
                head = [ln for ln in lines if not ln.startswith("- ")]
                bullets = [ln for ln in lines if ln.startswith("- ") and any(ln.startswith(f"- {b}:") for b in only_bullets)]
                if len(bullets) != len(only_bullets):
                    raise GlossaryError(f"glossary paragraph {prefix!r} lacks bullets {only_bullets}")
                return "\n".join(head + bullets)
        raise GlossaryError(f"glossary has no paragraph starting {prefix!r} in {section}")

    def moves_block(self) -> str:
        return "\n".join(ln for ln in self.sections["moves"].lines if ln.strip())

    def block(self, labels: dict[str, str] | None = None, *, moves: bool = False,
              dialogue: list[tuple[str, list[str] | None]] | None = None) -> str:
        """Verbatim glossary block for one call: label values used, optional move list, dialogue paragraphs."""
        parts = [f"GLOSSARY (verbatim excerpts from seed_label_definitions_v1.md, sha16 {self.sha16}):"]
        for section, value in (labels or {}).items():
            values = sorted(set(value)) if isinstance(value, (list, set, tuple)) else [value]
            parts.append(f"[{self.sections[section].heading}]\n" + "\n".join(self.entry(section, v) for v in values))
        if moves:
            parts.append(f"[{self.sections['moves'].heading}]\n{self.moves_block()}")
        for prefix, bullets in dialogue or []:
            parts.append(f"[{self.sections['dialogue_terms'].heading}]\n{self.paragraph('dialogue_terms', prefix, bullets)}")
        return "\n\n".join(parts)
