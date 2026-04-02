"""Stage contract parsing from ICM-style CONTEXT.md files.

Each stage defines a contract with three sections:
  Inputs  — what to load and from where
  Process — ordered steps to execute
  Outputs — artifacts to produce and where

CONTEXT.md files must stay under 500 tokens (ICM: ~80 lines max).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from msp.layer2._constants import TOKENS_PER_CHAR


@dataclass
class StageInput:
    source: str
    location: str
    scope: str
    why: str


@dataclass
class StageOutput:
    artifact: str
    location: str
    format: str


@dataclass
class StageContract:
    path: Path
    inputs: list[StageInput] = field(default_factory=list)
    process_steps: list[str] = field(default_factory=list)
    outputs: list[StageOutput] = field(default_factory=list)

    TOKENS_PER_CHAR = TOKENS_PER_CHAR

    @classmethod
    def from_file(cls, path: Path) -> "StageContract":
        text = path.read_text()
        contract = cls(path=path)
        contract.inputs = _parse_inputs(text)
        contract.process_steps = _parse_process(text)
        contract.outputs = _parse_outputs(text)
        return contract

    def token_estimate(self) -> int:
        return int(len(self.path.read_text()) * self.TOKENS_PER_CHAR)


def _extract_section(text: str, name: str) -> str:
    pattern = rf"##\s+{name}\s*\n(.*?)(?=\n##\s|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise ValueError(f"Missing required section: {name}")
    return match.group(1).strip()


def _parse_table_rows(section: str) -> list[list[str]]:
    rows = []
    for line in section.splitlines():
        if line.startswith("|") and not re.match(r"\|[-\s|]+\|", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0] not in ("Source", "Artifact"):  # skip header
                rows.append(cells)
    return rows


def _parse_inputs(text: str) -> list[StageInput]:
    section = _extract_section(text, "Inputs")
    return [
        StageInput(source=r[0], location=r[1], scope=r[2], why=r[3])
        for r in _parse_table_rows(section)
        if len(r) >= 4
    ]


def _parse_outputs(text: str) -> list[StageOutput]:
    section = _extract_section(text, "Outputs")
    return [
        StageOutput(artifact=r[0], location=r[1], format=r[2])
        for r in _parse_table_rows(section)
        if len(r) >= 3
    ]


def _parse_process(text: str) -> list[str]:
    section = _extract_section(text, "Process")
    steps = []
    for line in section.splitlines():
        match = re.match(r"^\d+\.\s+(.+)", line)
        if match:
            steps.append(match.group(1).strip())
    return steps
