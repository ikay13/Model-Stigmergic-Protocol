"""Tests for WorkspaceState — workspace file CRUD and DriftItem."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from msp.layer5.base import WorkspaceState, DriftItem


@pytest.fixture
def workspace_dir(tmp_path):
    return tmp_path / "myproject"


def _make_state(workspace_dir, markspace=None, vault=None):
    from unittest.mock import MagicMock
    ms = markspace or MagicMock()
    v = vault or MagicMock()
    return WorkspaceState(project="myproject", root=workspace_dir, markspace=ms, vault=v, agent=MagicMock())


def test_workspace_load_returns_empty_dict_when_no_file(workspace_dir):
    state = _make_state(workspace_dir)
    data = state.load()
    assert data == {}


def test_workspace_save_and_load_round_trip(workspace_dir):
    state = _make_state(workspace_dir)
    state.save({"project": "myproject", "health": "ok"})
    loaded = state.load()
    assert loaded["project"] == "myproject"
    assert loaded["health"] == "ok"


def test_workspace_save_creates_directory(workspace_dir):
    state = _make_state(workspace_dir)
    state.save({"x": 1})
    assert (workspace_dir / "base" / "workspace.json").exists()


def test_workspace_save_emits_observation_mark(workspace_dir):
    from unittest.mock import MagicMock, call
    ms = MagicMock()
    agent = MagicMock()
    state = WorkspaceState(project="myproject", root=workspace_dir, markspace=ms, vault=MagicMock(), agent=agent)
    state.save({"x": 1})
    assert ms.write.called
    obs = ms.write.call_args[0][1]
    assert obs.scope == "base"
    assert obs.topic == "workspace-saved"
    assert obs.content["project"] == "myproject"


def test_psmm_read_returns_empty_when_no_file(workspace_dir):
    state = _make_state(workspace_dir)
    assert state.psmm_read() == {}


def test_psmm_write_and_read_round_trip(workspace_dir):
    state = _make_state(workspace_dir)
    state.psmm_write({"last_session": "2026-04-02", "next_step": "build PAUL"})
    data = state.psmm_read()
    assert data["next_step"] == "build PAUL"


def test_psmm_write_calls_vault_export(workspace_dir):
    from unittest.mock import MagicMock
    vault = MagicMock()
    state = WorkspaceState(project="myproject", root=workspace_dir, markspace=MagicMock(), vault=vault, agent=MagicMock())
    state.psmm_write({"x": 1})
    vault.export_observations.assert_called_once_with("base")


def test_drift_item_dataclass():
    item = DriftItem(key="task_count", workspace_value=3, markspace_value=5)
    assert item.key == "task_count"
    assert item.workspace_value == 3
    assert item.markspace_value == 5


def test_detect_drift_no_drift_when_counts_match(tmp_path):
    from unittest.mock import MagicMock
    from markspace import Intent
    ms = MagicMock()
    ms.read.return_value = [MagicMock(spec=Intent), MagicMock(spec=Intent)]
    state = WorkspaceState(project="p", root=tmp_path, markspace=ms, vault=MagicMock(), agent=MagicMock())
    state.save({"active_intents": 2})
    items = state.detect_drift()
    assert items == []


def test_detect_drift_returns_item_when_counts_differ(tmp_path):
    from unittest.mock import MagicMock
    from markspace import Intent
    ms = MagicMock()
    ms.read.return_value = [MagicMock(spec=Intent)]
    state = WorkspaceState(project="p", root=tmp_path, markspace=ms, vault=MagicMock(), agent=MagicMock())
    state.save({"active_intents": 0})
    items = state.detect_drift()
    assert len(items) == 1
    assert items[0].key == "active_intents"


def test_detect_drift_emits_observation_mark_on_drift(tmp_path):
    from unittest.mock import MagicMock
    from markspace import Intent, Observation
    ms = MagicMock()
    ms.read.return_value = [MagicMock(spec=Intent)]
    agent = MagicMock()
    state = WorkspaceState(project="p", root=tmp_path, markspace=ms, vault=MagicMock(), agent=agent)
    state.save({"active_intents": 0})
    ms.write.reset_mock()
    state.detect_drift()
    assert ms.write.called
    obs = ms.write.call_args[0][1]
    assert obs.topic == "workspace-drift"


def test_detect_drift_no_mark_when_no_drift(tmp_path):
    from unittest.mock import MagicMock
    from markspace import Intent
    ms = MagicMock()
    ms.read.return_value = []
    state = WorkspaceState(project="p", root=tmp_path, markspace=ms, vault=MagicMock(), agent=MagicMock())
    state.save({"active_intents": 0})
    ms.write.reset_mock()
    state.detect_drift()
    assert not ms.write.called


@given(recorded=st.integers(min_value=0, max_value=20),
       live=st.integers(min_value=0, max_value=20))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_drift_detected_whenever_counts_differ(tmp_path, recorded, live):
    """detect_drift() always returns a DriftItem when counts differ."""
    from unittest.mock import MagicMock
    from markspace import Intent
    ms = MagicMock()
    mock_intents = [MagicMock(spec=Intent) for _ in range(live)]
    ms.read.return_value = mock_intents
    state = WorkspaceState(
        project="p", root=tmp_path, markspace=ms, vault=MagicMock(), agent=MagicMock()
    )
    state.save({"active_intents": recorded})
    ms.write.reset_mock()
    items = state.detect_drift()
    if recorded != live:
        assert len(items) == 1
        assert items[0].key == "active_intents"
    else:
        assert items == []


def test_psmm_snapshot_writes_structured_dict(tmp_path):
    """psmm_snapshot() writes a fully structured PSMM dict and returns it."""
    from unittest.mock import MagicMock
    from markspace import MarkSpace, Scope, DecayConfig, Agent
    scope = Scope(name="base", observation_topics=["*"], decay=DecayConfig(observation_half_life=3600.0, warning_half_life=3600.0, intent_ttl=1800.0))
    ms = MarkSpace(scopes=[scope])
    agent = Agent(name="test-agent", scopes={"base": ["observation"]})
    state = WorkspaceState(project="p", root=tmp_path, markspace=ms, vault=MagicMock(), agent=agent, scope="base")

    result = state.psmm_snapshot(
        session_id="agent://ikay13/msp/claude-01",
        completed_tasks=["t1", "t2"],
        next_steps=["do AEGIS"],
        open_needs=["Which analyzer?"],
        agent_notes="test note",
    )

    assert result["session_id"] == "agent://ikay13/msp/claude-01"
    assert result["completed_tasks"] == ["t1", "t2"]
    assert result["next_steps"] == ["do AEGIS"]
    assert result["open_needs"] == ["Which analyzer?"]
    assert result["agent_notes"] == "test note"
    assert "timestamp" in result
    assert "mark_summary" in result
    # Verify it was persisted
    assert state.psmm_read()["session_id"] == "agent://ikay13/msp/claude-01"


def test_psmm_snapshot_counts_live_marks(tmp_path):
    """psmm_snapshot() mark_summary reflects live markspace state."""
    from unittest.mock import MagicMock
    from markspace import MarkSpace, Scope, DecayConfig, Agent, Observation, Source
    scope = Scope(name="base", observation_topics=["*"], decay=DecayConfig(observation_half_life=3600.0, warning_half_life=3600.0, intent_ttl=1800.0))
    ms = MarkSpace(scopes=[scope])
    agent = Agent(name="test-agent", scopes={"base": ["observation"]})
    state = WorkspaceState(project="p", root=tmp_path, markspace=ms, vault=MagicMock(), agent=agent, scope="base")

    ms.write(agent, Observation(scope="base", topic="t", content={}, confidence=1.0, source=Source.FLEET))
    ms.write(agent, Observation(scope="base", topic="t2", content={}, confidence=0.9, source=Source.FLEET))

    result = state.psmm_snapshot(session_id="agent://ikay13/msp/claude-01")
    assert result["mark_summary"]["observations"] == 2
