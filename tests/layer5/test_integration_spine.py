"""Integration test: minimal stigmergic loop — BASE + PAUL core + CARL + SKILLSMITH.

This is the validation gate from the Layer 5 design spec.
Verifies the four modules work together before SEED and AEGIS are built.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from msp.layer5.base import WorkspaceState
from msp.layer5.paul import PlanApplyUnify, Milestone, Result
from msp.layer5.carl import ContextAugmentation
from msp.layer5.skillsmith import CapabilityStandards, SkillSpec


@pytest.fixture
def project_root(tmp_path):
    return tmp_path / "test_project"


def test_full_spine_plan_emit_inject_validate(project_root):
    """BASE + PAUL + CARL + SKILLSMITH complete a full lifecycle without errors."""
    # --- Shared markspace mock ---
    ms = MagicMock()
    ms.read.return_value = []
    agent = MagicMock()

    # --- BASE ---
    vault = MagicMock()
    state = WorkspaceState(
        project="test_project", root=project_root, markspace=ms, vault=vault, agent=agent
    )
    state.save({"health": "ok", "active_intents": 0})
    assert state.load()["health"] == "ok"

    # --- PAUL plan phase emits Intent marks ---
    paul = PlanApplyUnify(project="test_project", state=state, markspace=ms, agent=agent)
    milestones = [
        Milestone(id="m1", description="implement the feature", acceptance_criteria="tests pass"),
    ]
    plan = paul.plan(milestones)
    assert (project_root / "paul" / "STATE.md").exists()
    assert ms.write.call_count >= 1  # at least one Intent mark

    # --- CARL detects domain from PAUL's Intent marks ---
    from markspace import Intent
    mock_intent = MagicMock(spec=Intent)
    mock_intent.action = "implement the feature"
    mock_intent.resource = "m1"
    mock_intent.created_at = 0.0
    ms.read.return_value = [mock_intent]

    loader = MagicMock()
    loader.load.return_value = MagicMock(references=[], as_text=MagicMock(return_value=""))
    carl = ContextAugmentation(markspace=ms, loader=loader)
    config = carl.inject({"session_id": "s1"})
    assert "development" in config["carl_domains"]

    # --- SKILLSMITH validates a compliant skill session ---
    sm = CapabilityStandards(markspace=ms, agent=agent)
    skill_spec = SkillSpec(name="test-skill", purpose="run tests", domains=["development"])
    skill_dir = sm.scaffold(skill_spec, project_root / "skills")
    session = MagicMock()
    session.skill_path = skill_dir
    assert sm.validate_session(session) is True

    # --- PAUL unify closes the loop ---
    ms.write.reset_mock()
    result = Result(plan=plan, completed_tasks=[], failed_tasks=[])
    summary = paul.unify(plan, result)
    assert (project_root / "paul" / "SUMMARY.md").exists()

    from markspace import Observation
    obs_calls = [c for c in ms.write.call_args_list if isinstance(c.args[1], Observation)]
    assert any(c.args[1].topic == "plan-closed" for c in obs_calls)
