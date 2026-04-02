"""Tests for ProjectGenesis (SEED) — type-first ideation, PLANNING.md, PAUL handoff."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from msp.layer5.seed import ProjectGenesis, Ideation


PROJECT_TYPES = ["software", "workflow", "research", "campaign", "utility"]


def _make_seed(tmp_path):
    ms = MagicMock()
    ms.read.return_value = []
    agent = MagicMock()
    paul = MagicMock()
    paul.plan.return_value = MagicMock(id="plan1", milestones=[], tasks=[])
    return ProjectGenesis(
        markspace=ms, paul=paul, root=tmp_path, agent=agent
    ), ms, paul


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
def test_ideation_returns_ideation_for_all_types(tmp_path, project_type):
    seed, _, _ = _make_seed(tmp_path)
    ideation = Ideation(
        project_type=project_type,
        name="test-project",
        goals=["Ship it"],
        constraints=["No external APIs"],
    )
    assert ideation.project_type == project_type


def test_graduate_writes_planning_md(tmp_path):
    seed, ms, paul = _make_seed(tmp_path)
    ideation = Ideation(
        project_type="software",
        name="myapp",
        goals=["Build auth system"],
        constraints=["Python only"],
    )
    planning_path = seed.graduate(ideation)
    assert planning_path.exists()
    content = planning_path.read_text()
    assert "myapp" in content
    assert "Build auth system" in content


def test_graduate_planning_md_is_always_parseable(tmp_path):
    """PLANNING.md must always be valid UTF-8 text (Hypothesis-style check)."""
    seed, _, _ = _make_seed(tmp_path)
    for project_type in PROJECT_TYPES:
        ideation = Ideation(
            project_type=project_type,
            name=f"proj-{project_type}",
            goals=["Goal A"],
            constraints=["Constraint B"],
        )
        path = seed.graduate(ideation)
        content = path.read_text(encoding="utf-8")
        assert len(content) > 0


def test_seed_marks_emits_one_intent_per_goal(tmp_path):
    seed, ms, _ = _make_seed(tmp_path)
    ideation = Ideation(
        project_type="software",
        name="proj",
        goals=["Goal A", "Goal B", "Goal C"],
        constraints=[],
    )
    marks = seed.seed_marks(ideation)
    assert len(marks) == 3


def test_seed_marks_are_written_to_markspace(tmp_path):
    seed, ms, _ = _make_seed(tmp_path)
    ideation = Ideation(
        project_type="software",
        name="proj",
        goals=["Build X"],
        constraints=[],
    )
    seed.seed_marks(ideation)
    assert ms.write.called


def test_launch_calls_paul_plan(tmp_path):
    seed, ms, paul = _make_seed(tmp_path)
    ideation = Ideation(
        project_type="software",
        name="proj",
        goals=["Build X"],
        constraints=[],
    )
    plan = seed.launch(ideation)
    assert paul.plan.called


def test_launch_does_not_reask_answered_questions(tmp_path):
    """launch() must not prompt — it must use ideation data directly."""
    seed, ms, paul = _make_seed(tmp_path)
    ideation = Ideation(
        project_type="workflow",
        name="my-workflow",
        goals=["Automate deployment"],
        constraints=["No cloud"],
    )
    # launch() must complete without input() calls
    with patch("builtins.input", side_effect=AssertionError("Should not call input()")):
        seed.launch(ideation)
