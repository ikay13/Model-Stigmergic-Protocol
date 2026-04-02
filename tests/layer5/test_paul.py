"""Tests for PlanApplyUnify — Plan/Apply/Unify loop and lifecycle mark emission."""
from __future__ import annotations

from pathlib import Path
import tempfile
from unittest.mock import MagicMock
import pytest

from msp.layer5.paul import (
    Milestone, Plan, Task, Result, Summary, PlanApplyUnify
)
from msp.layer5.base import WorkspaceState


@pytest.fixture
def workspace_dir(tmp_path):
    return tmp_path / "proj"


@pytest.fixture
def mock_state(workspace_dir):
    ms = MagicMock()
    vault = MagicMock()
    agent = MagicMock()
    return WorkspaceState(
        project="proj", root=workspace_dir, markspace=ms, vault=vault, agent=agent
    )


@pytest.fixture
def paul(mock_state):
    ms = mock_state.markspace
    agent = mock_state.agent
    return PlanApplyUnify(project="proj", state=mock_state, markspace=ms, agent=agent)


def test_milestone_dataclass():
    m = Milestone(id="m1", description="Build BASE", acceptance_criteria="workspace.json created")
    assert m.id == "m1"
    assert m.acceptance_criteria == "workspace.json created"


def test_plan_creates_state_file(workspace_dir, paul):
    milestones = [Milestone(id="m1", description="Do X", acceptance_criteria="X done")]
    paul.plan(milestones)
    assert (workspace_dir / "paul" / "STATE.md").exists()


def test_plan_creates_milestones_file(workspace_dir, paul):
    milestones = [Milestone(id="m1", description="Do X", acceptance_criteria="X done")]
    paul.plan(milestones)
    assert (workspace_dir / "paul" / "MILESTONES.md").exists()


def test_plan_emits_one_intent_mark_per_milestone(paul):
    milestones = [
        Milestone(id="m1", description="Do X", acceptance_criteria="X done"),
        Milestone(id="m2", description="Do Y", acceptance_criteria="Y done"),
    ]
    paul.plan(milestones)
    assert paul.markspace.write.call_count == 2


def test_unify_writes_summary_file(workspace_dir, paul):
    milestones = [Milestone(id="m1", description="Do X", acceptance_criteria="X done")]
    plan = paul.plan(milestones)
    paul.markspace.write.reset_mock()
    result = Result(plan=plan, completed_tasks=[], failed_tasks=[])
    summary = paul.unify(plan, result)
    assert isinstance(summary, Summary)
    assert (workspace_dir / "paul" / "SUMMARY.md").exists()


def test_unify_emits_observation_mark(paul):
    milestones = [Milestone(id="m1", description="Do X", acceptance_criteria="X done")]
    plan = paul.plan(milestones)
    paul.markspace.write.reset_mock()
    result = Result(plan=plan, completed_tasks=[], failed_tasks=[])
    paul.unify(plan, result)
    from markspace import Observation
    calls = paul.markspace.write.call_args_list
    # Filter to scope="paul" only — unify also triggers state.save() which emits scope="base"
    paul_obs = [c for c in calls if isinstance(c.args[1], Observation) and c.args[1].scope == "paul"]
    assert len(paul_obs) == 1


def test_apply_emits_action_mark_per_completed_task(paul):
    milestones = [Milestone(id="m1", description="Do X", acceptance_criteria="X done")]
    plan = paul.plan(milestones)
    paul.markspace.write.reset_mock()

    mock_session = MagicMock()
    mock_session.run.return_value = MagicMock(observations=[], needs=[])

    task = Task(id="t1", milestone_id="m1", description="Step 1")
    plan.tasks = [task]
    result = paul.apply(plan, mock_session)

    from markspace import Action
    calls = paul.markspace.write.call_args_list
    action_calls = [c for c in calls if isinstance(c.args[1], Action)]
    assert len(action_calls) == 1


from hypothesis import given, settings, HealthCheck, strategies as st
import tempfile


@given(n_milestones=st.integers(min_value=1, max_value=5))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_run_always_produces_summary(tmp_path, n_milestones):
    """run() always produces a Summary regardless of milestone count."""
    ms = MagicMock()
    ms.read.return_value = []
    agent = MagicMock()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "p"
        state = WorkspaceState(
            project="p", root=root, markspace=ms, vault=MagicMock(), agent=agent
        )
        paul = PlanApplyUnify(project="p", state=state, markspace=ms, agent=agent)
        milestones = [
            Milestone(id=f"m{i}", description=f"Step {i}", acceptance_criteria=f"Done {i}")
            for i in range(n_milestones)
        ]
        mock_session = MagicMock()
        mock_session.run.return_value = MagicMock(observations=[], needs=[])
        summary = paul.run(milestones, mock_session)
        assert isinstance(summary, Summary)
        assert (root / "paul" / "SUMMARY.md").exists()
