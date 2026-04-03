"""Integration tests: PAUL.apply() with real AgentSession routing.

These tests exercise the full PAUL → AgentSession → ProviderAdapter path
using stub adapters (no live API/CLI calls). The stub adapters are
structurally identical to CodexAdapter and GeminiAdapter — they just return
canned JSON instead of spawning subprocesses.

To run against live providers, replace StubAdapter with the real adapter
and ensure the CLI tools are authenticated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from markspace import Agent, DecayConfig, MarkSpace, Scope
from msp.layer3.adapter import AgentResponse, AgentRound, ProviderAdapter
from msp.layer3.identity import AgentURI
from msp.layer3.session import AgentSession
from msp.layer5.base import WorkspaceState
from msp.layer5.paul import Milestone, PlanApplyUnify, Task
from tests.layer2.test_workspace import _make_workspace


# ---------------------------------------------------------------------------
# Stub adapter — canned response, no subprocess/API calls
# ---------------------------------------------------------------------------

@dataclass
class StubAdapter(ProviderAdapter):
    """Returns a fixed AgentResponse for hermetic testing."""
    name: str = "stub"
    observations: list[dict] = field(default_factory=lambda: [
        {"topic": "task-complete", "content": {"status": "ok"}, "confidence": 0.9}
    ])
    needs: list[str] = field(default_factory=list)

    @property
    def provider_name(self) -> str:
        return self.name

    def run_round(self, round_: AgentRound) -> AgentResponse:
        return AgentResponse(
            observations=self.observations,
            needs=self.needs,
            raw_text='{"observations": [], "needs": [], "reasoning": "stub"}',
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def workspace_dir(tmp_path):
    return _make_workspace(tmp_path)


def _make_scope(name: str) -> Scope:
    return Scope(
        name=name,
        observation_topics=["*"],
        decay=DecayConfig(observation_half_life=3600.0, warning_half_life=3600.0, intent_ttl=1800.0),
    )


@pytest.fixture
def markspace_and_agent():
    """Real MarkSpace + Agent with scopes needed by AgentSession and PAUL."""
    ms = MarkSpace(scopes=[_make_scope("msp"), _make_scope("paul"), _make_scope("base")])
    agent = Agent(
        name="test-agent",
        scopes={
            "msp": ["observation", "need"],
            "paul": ["action", "intent", "observation", "need", "warning"],
            "base": ["observation"],
        },
    )
    return ms, agent


@pytest.fixture
def paul_and_ms(workspace_dir, markspace_and_agent):
    """Returns (PlanApplyUnify, ms, agent) all sharing the same markspace."""
    ms, agent = markspace_and_agent
    state = WorkspaceState(
        project="proj", root=workspace_dir, markspace=ms, vault=MagicMock(), agent=agent
    )
    return PlanApplyUnify(project="proj", state=state, markspace=ms, agent=agent), ms, agent


def _make_session(workspace_dir, ms, agent, adapter, scope="msp"):
    uri = AgentURI.parse(f"agent://test/msp/{adapter.provider_name}")
    return AgentSession(
        uri=uri,
        workspace_root=workspace_dir,
        mark_space=ms,
        agent=agent,
        adapter=adapter,
        scope=scope,
    )


# ---------------------------------------------------------------------------
# Tests: single session (backward-compat path)
# ---------------------------------------------------------------------------

def test_apply_single_session_completes_tasks(paul_and_ms, workspace_dir):
    """PAUL.apply() with a single session runs all tasks and marks them complete."""
    paul, ms, agent = paul_and_ms
    session = _make_session(workspace_dir, ms, agent, StubAdapter(name="claude"))

    milestones = [Milestone(id="m1", description="Do work", acceptance_criteria="done")]
    plan = paul.plan(milestones)
    plan.tasks = [
        Task(id="t1", milestone_id="m1", description="Task one"),
        Task(id="t2", milestone_id="m1", description="Task two"),
    ]

    result = paul.apply(plan, session)

    assert len(result.completed_tasks) == 2
    assert len(result.failed_tasks) == 0


# ---------------------------------------------------------------------------
# Tests: per-task routing via sessions dict
# ---------------------------------------------------------------------------

def test_apply_routes_tasks_by_provider(paul_and_ms, workspace_dir):
    """Each task is dispatched to the session matching task.provider."""
    paul, ms, agent = paul_and_ms
    sessions = {
        "claude": _make_session(workspace_dir, ms, agent, StubAdapter(name="claude")),
        "codex": _make_session(workspace_dir, ms, agent, StubAdapter(name="codex")),
        "gemini": _make_session(workspace_dir, ms, agent, StubAdapter(name="gemini")),
    }

    milestones = [Milestone(id="m1", description="Multi-provider", acceptance_criteria="all done")]
    plan = paul.plan(milestones)
    plan.tasks = [
        Task(id="t1", milestone_id="m1", description="Claude task", provider="claude"),
        Task(id="t2", milestone_id="m1", description="Codex task", provider="codex"),
        Task(id="t3", milestone_id="m1", description="Gemini task", provider="gemini"),
    ]

    result = paul.apply(plan, sessions)

    assert len(result.completed_tasks) == 3
    assert len(result.failed_tasks) == 0


def test_apply_falls_back_to_claude_for_unknown_provider(paul_and_ms, workspace_dir):
    """Tasks with an unknown provider fall back to the 'claude' session."""
    paul, ms, agent = paul_and_ms
    sessions = {"claude": _make_session(workspace_dir, ms, agent, StubAdapter(name="claude"))}

    milestones = [Milestone(id="m1", description="Fallback test", acceptance_criteria="done")]
    plan = paul.plan(milestones)
    plan.tasks = [
        Task(id="t1", milestone_id="m1", description="Unknown provider task", provider="unknown"),
    ]

    result = paul.apply(plan, sessions)

    assert len(result.completed_tasks) == 1
    assert len(result.failed_tasks) == 0


def test_apply_marks_written_to_markspace(paul_and_ms, workspace_dir):
    """PAUL.apply() writes Action marks to the markspace for completed tasks."""
    paul, ms, agent = paul_and_ms
    session = _make_session(workspace_dir, ms, agent, StubAdapter(name="claude"))

    milestones = [Milestone(id="m1", description="Mark test", acceptance_criteria="done")]
    plan = paul.plan(milestones)
    plan.tasks = [Task(id="t1", milestone_id="m1", description="Write marks")]

    paul.apply(plan, session)

    marks = ms.read(scope="paul")
    action_marks = [m for m in marks if type(m).__name__ == "Action"]
    assert any(getattr(m, "resource", None) == "t1" for m in action_marks)


def test_full_run_with_sessions_dict(paul_and_ms, workspace_dir):
    """Full PAUL.apply() + unify() loop works end-to-end with a sessions dict."""
    paul, ms, agent = paul_and_ms
    sessions = {
        "claude": _make_session(workspace_dir, ms, agent, StubAdapter(name="claude")),
        "codex": _make_session(workspace_dir, ms, agent, StubAdapter(name="codex")),
    }

    milestones = [Milestone(id="m1", description="Full loop", acceptance_criteria="summary written")]
    plan = paul.plan(milestones)
    plan.tasks = [
        Task(id="t1", milestone_id="m1", description="Claude step", provider="claude"),
        Task(id="t2", milestone_id="m1", description="Codex step", provider="codex"),
    ]

    result = paul.apply(plan, sessions)
    summary = paul.unify(plan, result)

    assert summary.completed == 2
    assert summary.failed == 0
    assert (workspace_dir / "paul" / "SUMMARY.md").exists()
