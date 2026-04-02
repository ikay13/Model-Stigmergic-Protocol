"""BASE: WorkspaceState — JSON workspace surfaces, drift detection, PSMM.

Workspace files live at <root>/base/:
  workspace.json — project identity, health, active agents
  psmm.json      — Per-Session Meta Memory
  drift.json     — detected workspace/markspace divergence

Marks emitted:
  Observation(scope="base", topic="workspace-saved")  on save()
  Observation(scope="base", topic="workspace-drift")  on detect_drift()
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from markspace import Agent, Intent, MarkSpace, Observation, Source
from msp.layer4.vault_sync import VaultSync


@dataclass
class DriftItem:
    """Represents a single divergence between workspace and markspace state."""
    key: str
    workspace_value: Any
    markspace_value: Any


@dataclass
class WorkspaceState:
    """Manages JSON workspace surfaces for a project.

    Attributes:
        project:   Project name (used as subdirectory).
        root:      Parent directory; files go in root/base/.
        markspace: Shared MarkSpace instance.
        vault:     VaultSync instance for PSMM export.
        agent:     Authorized Agent for writing marks.
        scope:     Mark scope string (default "base").
    """
    project: str
    root: Path
    markspace: MarkSpace
    vault: VaultSync
    agent: Agent
    scope: str = "base"
    _base_dir: Path = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._base_dir = self.root / "base"

    def _read_json(self, filename: str) -> dict:
        path = self._base_dir / filename
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, filename: str, data: dict) -> None:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        path = self._base_dir / filename
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def load(self) -> dict:
        """Read workspace.json. Returns {} if not yet created."""
        return self._read_json("workspace.json")

    def save(self, data: dict) -> None:
        """Write workspace.json and emit an Observation mark."""
        self._write_json("workspace.json", data)
        self.markspace.write(
            self.agent,
            Observation(
                scope=self.scope,
                topic="workspace-saved",
                content={"project": self.project},
                confidence=1.0,
                source=Source.FLEET,
            ),
        )

    def detect_drift(self) -> list[DriftItem]:
        """Compare workspace.json against markspace Intent mark count."""
        workspace = self.load()
        recorded = workspace.get("active_intents", 0)
        live_marks = self.markspace.read(scope=self.scope)
        live_intents = sum(1 for m in live_marks if isinstance(m, Intent))

        items: list[DriftItem] = []
        if recorded != live_intents:
            item = DriftItem(
                key="active_intents",
                workspace_value=recorded,
                markspace_value=live_intents,
            )
            items.append(item)
            self.markspace.write(
                self.agent,
                Observation(
                    scope=self.scope,
                    topic="workspace-drift",
                    content={"key": item.key, "workspace": recorded, "live": live_intents},
                    confidence=0.9,
                    source=Source.FLEET,
                ),
            )
        return items

    def psmm_read(self) -> dict:
        """Read psmm.json. Returns {} if not yet created."""
        return self._read_json("psmm.json")

    def psmm_write(self, session_data: dict) -> None:
        """Write psmm.json and export to Obsidian vault."""
        self._write_json("psmm.json", session_data)
        self.vault.export_observations(self.scope)
