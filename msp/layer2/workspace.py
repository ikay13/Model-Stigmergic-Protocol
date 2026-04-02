"""Workspace discovery and navigation for ICM-structured directories.

A workspace is a folder containing:
  CLAUDE.md   — Layer 0: always-loaded identity (~800 tokens)
  CONTEXT.md  — Layer 1: task routing (~300 tokens)
  stages/     — numbered stage folders (01-name, 02-name, ...)
  _config/    — Layer 3: stable reference material
"""
from __future__ import annotations

import re
from pathlib import Path

from msp.layer2.stage import StageContract


class Workspace:
    """Navigate an ICM workspace filesystem."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def layer0(self) -> str:
        """Layer 0: CLAUDE.md content."""
        path = self.root / "CLAUDE.md"
        if not path.exists():
            raise ValueError(f"CLAUDE.md not found in {self.root}")
        return path.read_text()

    def layer1(self) -> str:
        """Layer 1: root CONTEXT.md content."""
        path = self.root / "CONTEXT.md"
        if not path.exists():
            raise ValueError(f"CONTEXT.md not found in {self.root}")
        return path.read_text()

    def stages(self) -> list[Path]:
        """Return numbered stage directories in order."""
        stages_dir = self.root / "stages"
        if not stages_dir.exists():
            return []
        return sorted(
            (p for p in stages_dir.iterdir()
             if p.is_dir() and re.match(r"^\d+", p.name)),
            key=lambda p: p.name,
        )

    def stage_contract(self, stage_name: str) -> StageContract:
        """Parse and return the StageContract for a named stage."""
        context = self.root / "stages" / stage_name / "CONTEXT.md"
        if not context.exists():
            raise ValueError(f"CONTEXT.md not found for stage: {stage_name}")
        return StageContract.from_file(context)

    def stage_complete(self, stage_name: str) -> bool:
        """True if the stage output/ folder contains non-gitkeep files."""
        output = self.root / "stages" / stage_name / "output"
        if not output.exists():
            return False
        files = [f for f in output.iterdir()
                 if f.is_file() and f.name != ".gitkeep"]
        return len(files) > 0

    def status(self) -> str:
        """ASCII pipeline status — mirrors ICM's `status` trigger."""
        lines = [f"Pipeline Status: {self.root.name}", ""]
        for stage in self.stages():
            marker = "COMPLETE" if self.stage_complete(stage.name) else "PENDING"
            lines.append(f"  [{stage.name}]  {marker}")
        return "\n".join(lines)
