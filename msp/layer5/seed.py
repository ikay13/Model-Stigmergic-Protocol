"""SEED: ProjectGenesis — type-first ideation, PLANNING.md output, PAUL handoff.

Translates a raw idea into a structured PLANNING.md and seeds the markspace
with initial Intent marks before handing off to PAUL.

Marks emitted:
  Intent(scope="seed", resource=goal) — one per goal on seed_marks() / launch()
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from markspace import Agent, Intent, MarkSpace

from msp.layer5.paul import Milestone, PlanApplyUnify, Plan

PLANNING_TEMPLATE = """\
# {name} — Project Plan

**Type:** {project_type}

## Goals

{goals_list}

## Constraints

{constraints_list}

## Milestones

{milestones_section}
"""


@dataclass
class Ideation:
    """Structured output of a SEED ideation session."""
    project_type: str   # software | workflow | research | campaign | utility
    name: str
    goals: list[str]
    constraints: list[str]
    milestones: list[str] = field(default_factory=list)
    notes: str = ""


class ProjectGenesis:
    """Guides ideation and produces a structured PLANNING.md for PAUL.

    Attributes:
        markspace: Shared MarkSpace instance.
        paul:      PlanApplyUnify instance for headless PAUL handoff.
        root:      Parent directory for workspace files.
        agent:     Authorized Agent for writing marks.
    """

    def __init__(
        self,
        markspace: MarkSpace,
        paul: PlanApplyUnify,
        root: Path,
        agent: Agent | None = None,
    ) -> None:
        self.markspace = markspace
        self.paul = paul
        self.root = root
        self.agent = agent

    def ideate(self, project_type: str) -> Ideation:
        """Return a minimal Ideation for the given type (headless — no prompts).

        In a full interactive session, this would drive a guided interview.
        For programmatic/agent use, callers construct Ideation directly.
        """
        return Ideation(project_type=project_type, name="", goals=[], constraints=[])

    def graduate(self, ideation: Ideation) -> Path:
        """Write PLANNING.md to root/<name>/ and return its path."""
        project_dir = self.root / ideation.name
        project_dir.mkdir(parents=True, exist_ok=True)

        goals_list = "\n".join(f"- {g}" for g in ideation.goals) or "- (none specified)"
        constraints_list = "\n".join(f"- {c}" for c in ideation.constraints) or "- (none specified)"
        milestones_section = (
            "\n".join(f"- [ ] {m}" for m in ideation.milestones)
            if ideation.milestones
            else "- [ ] (to be defined with PAUL)"
        )

        content = PLANNING_TEMPLATE.format(
            name=ideation.name,
            project_type=ideation.project_type,
            goals_list=goals_list,
            constraints_list=constraints_list,
            milestones_section=milestones_section,
        )

        planning_path = project_dir / "PLANNING.md"
        planning_path.write_text(content, encoding="utf-8")
        return planning_path

    def seed_marks(self, ideation: Ideation) -> list[Intent]:
        """Emit one Intent mark per goal and return the list."""
        marks = []
        for goal in ideation.goals:
            intent = Intent(
                scope="seed",
                resource=ideation.name,
                action=goal,
                confidence=0.9,
            )
            if self.agent is not None:
                self.markspace.write(self.agent, intent)
            marks.append(intent)
        return marks

    def launch(self, ideation: Ideation) -> Plan:
        """Graduate + seed marks + initialize PAUL. No re-asking of questions."""
        self.graduate(ideation)
        self.seed_marks(ideation)

        milestones = [
            Milestone(
                id=f"m{i+1}",
                description=goal,
                acceptance_criteria=f"Goal achieved: {goal}",
            )
            for i, goal in enumerate(ideation.goals)
        ]
        return self.paul.plan(milestones)
