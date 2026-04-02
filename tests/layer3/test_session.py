# tests/layer3/test_session.py
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from markspace import Agent, MarkSpace, Scope, DecayConfig, Source
from msp.layer3.adapter import AgentResponse, AgentRound, ProviderAdapter
from msp.layer3.identity import AgentURI
from msp.layer3.session import AgentSession
from tests.layer2.test_workspace import _make_workspace


class _MockAdapter(ProviderAdapter):
    """Test adapter that returns a controlled response."""

    def __init__(self, response: AgentResponse) -> None:
        self._response = response

    @property
    def provider_name(self) -> str:
        return "mock"

    def run_round(self, round_: AgentRound) -> AgentResponse:
        self._last_round = round_
        return self._response


def _make_mark_space():
    """Create a minimal MarkSpace with one agent for testing."""
    scope = Scope(
        name="test",
        observation_topics=["*"],
        decay=DecayConfig(
            observation_half_life=3600.0,
            warning_half_life=3600.0,
            intent_ttl=1800.0,
        ),
    )
    space = MarkSpace(scopes=[scope])
    agent = Agent(
        name="test-agent",
        scopes={"test": ["observation", "need"]},
    )
    return space, agent


def test_session_loads_context(tmp_path):
    """AgentSession loads workspace context into the AgentRound."""
    root = _make_workspace(tmp_path)
    space, agent = _make_mark_space()
    uri = AgentURI.parse("agent://ikay13/test/claude-01")
    mock_response = AgentResponse(observations=[], needs=[], raw_text="{}")
    adapter = _MockAdapter(mock_response)

    session = AgentSession(
        uri=uri,
        workspace_root=root,
        mark_space=space,
        agent=agent,
        adapter=adapter,
        scope="test",
    )
    session.run(stage="01-research")

    assert "# Workspace" in adapter._last_round.context
    assert str(uri) in adapter._last_round.instructions


def test_session_writes_observations(tmp_path):
    """AgentSession writes observations returned by adapter to the mark space."""
    root = _make_workspace(tmp_path)
    space, agent = _make_mark_space()
    uri = AgentURI.parse("agent://ikay13/test/claude-01")
    mock_response = AgentResponse(
        observations=[
            {"topic": "progress", "content": {"status": "on track"}, "confidence": 0.9}
        ],
        needs=[],
        raw_text="{}",
    )
    adapter = _MockAdapter(mock_response)

    session = AgentSession(
        uri=uri,
        workspace_root=root,
        mark_space=space,
        agent=agent,
        adapter=adapter,
        scope="test",
    )
    session.run(stage="01-research")

    marks = space.read(scope="test", mark_type=None)
    observation_marks = [m for m in marks if type(m).__name__ == "Observation" and m.topic == "progress"]
    assert len(observation_marks) == 1
    assert observation_marks[0].confidence == 0.9


def test_session_writes_needs(tmp_path):
    """AgentSession writes needs returned by adapter to the mark space."""
    root = _make_workspace(tmp_path)
    space, agent = _make_mark_space()
    uri = AgentURI.parse("agent://ikay13/test/claude-01")
    mock_response = AgentResponse(
        observations=[],
        needs=["Should we proceed with Stage 03?"],
        raw_text="{}",
    )
    adapter = _MockAdapter(mock_response)

    session = AgentSession(
        uri=uri,
        workspace_root=root,
        mark_space=space,
        agent=agent,
        adapter=adapter,
        scope="test",
    )
    session.run(stage="01-research")

    marks = space.read(scope="test", mark_type=None)
    need_marks = [m for m in marks if type(m).__name__ == "Need"]
    assert len(need_marks) == 1
    assert "Stage 03" in need_marks[0].question


def test_session_returns_response(tmp_path):
    """AgentSession.run() returns the AgentResponse."""
    root = _make_workspace(tmp_path)
    space, agent = _make_mark_space()
    uri = AgentURI.parse("agent://ikay13/test/claude-01")
    mock_response = AgentResponse(observations=[], needs=[], raw_text="done")
    adapter = _MockAdapter(mock_response)

    session = AgentSession(
        uri=uri,
        workspace_root=root,
        mark_space=space,
        agent=agent,
        adapter=adapter,
        scope="test",
    )
    result = session.run()
    assert result.raw_text == "done"


def test_session_respects_token_budget(tmp_path):
    """AgentSession passes token_budget to ContextLoader."""
    root = _make_workspace(tmp_path)
    space, agent = _make_mark_space()
    uri = AgentURI.parse("agent://ikay13/test/claude-01")
    mock_response = AgentResponse(observations=[], needs=[], raw_text="{}")
    adapter = _MockAdapter(mock_response)

    session = AgentSession(
        uri=uri,
        workspace_root=root,
        mark_space=space,
        agent=agent,
        adapter=adapter,
        scope="test",
        token_budget=100,
    )
    session.run(stage="01-research")

    assert adapter._last_round.context != ""
