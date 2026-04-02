"""Budget-aware context loader for MSP agents.

Loads the right context at the right time using the ICM 5-layer hierarchy.
Respects markspace token budget properties (P59-P63).

Layer 0 (~800t)  : always loaded — workspace identity
Layer 1 (~300t)  : always loaded — routing table
Layer 2 (~500t)  : loaded per stage — stage contract
Layer 3 (varies) : loaded selectively — reference material
Layer 4 (varies) : loaded selectively — working artifacts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from msp.layer2.stage import StageContract
from msp.layer2.workspace import Workspace


@dataclass
class ContextBundle:
    """Assembled context for one agent round."""
    layer0: str = ""
    layer1: str = ""
    layer2: StageContract | None = None
    references: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)

    TOKENS_PER_CHAR = 0.25

    def _estimate(self, text: str) -> int:
        return int(len(text) * self.TOKENS_PER_CHAR)

    def total_tokens(self) -> int:
        total = self._estimate(self.layer0) + self._estimate(self.layer1)
        if self.layer2:
            total += self.layer2.token_estimate()
        total += sum(self._estimate(r) for r in self.references)
        total += sum(self._estimate(a) for a in self.artifacts)
        return total

    def as_text(self) -> str:
        parts = []
        if self.layer0:
            parts.append(self.layer0)
        if self.layer1:
            parts.append(self.layer1)
        if self.layer2:
            parts.append(self.layer2.path.read_text())
        parts.extend(self.references)
        parts.extend(self.artifacts)
        return "\n\n---\n\n".join(parts)


class ContextLoader:
    """Loads MSP agent context from an ICM workspace."""

    def __init__(self, root: Path) -> None:
        self.workspace = Workspace(root)

    def load(
        self,
        stage: str | None = None,
        token_budget: int = 8000,
    ) -> ContextBundle:
        """Load context for an agent round.

        Args:
            stage: stage name (e.g. "01-research"). None = routing only.
            token_budget: max tokens to deliver (maps to markspace P61).
        """
        bundle = ContextBundle()

        # Layer 0 — always load
        bundle.layer0 = self.workspace.layer0()

        # Layer 1 — always load
        bundle.layer1 = self.workspace.layer1()

        if stage is not None:
            # Validate stage exists
            stage_names = [s.name for s in self.workspace.stages()]
            if stage not in stage_names:
                raise ValueError(f"Stage not found: {stage}")

            # Layer 2 — stage contract
            bundle.layer2 = self.workspace.stage_contract(stage)

            # Layer 3 + 4 — load from inputs table if budget allows
            remaining = token_budget - bundle.total_tokens()
            if remaining > 0 and bundle.layer2:
                self._load_inputs(bundle, stage, remaining)

        return bundle

    def _load_inputs(
        self, bundle: ContextBundle, stage: str, budget: int
    ) -> None:
        """Load Layer 3/4 inputs declared in the stage contract."""
        TOKENS_PER_CHAR = 0.25
        stage_path = self.workspace.root / "stages" / stage
        used = 0

        for inp in bundle.layer2.inputs:
            target = (stage_path / inp.location).resolve()
            if not target.exists():
                continue
            content = target.read_text()
            cost = int(len(content) * TOKENS_PER_CHAR)
            if used + cost > budget:
                break
            # Classify as Layer 3 (references/) or Layer 4 (output/)
            if "output" in inp.location:
                bundle.artifacts.append(content)
            else:
                bundle.references.append(content)
            used += cost
