"""Tests for WorkspaceState — workspace file CRUD and DriftItem."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from msp.layer5.base import WorkspaceState, DriftItem


@pytest.fixture
def workspace_dir(tmp_path):
    return tmp_path / "myproject"


def _make_state(workspace_dir, markspace=None, vault=None):
    from unittest.mock import MagicMock
    ms = markspace or MagicMock()
    v = vault or MagicMock()
    return WorkspaceState(project="myproject", root=workspace_dir, markspace=ms, vault=v)


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
