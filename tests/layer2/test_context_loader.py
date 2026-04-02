from pathlib import Path
import pytest
from msp.layer2.context_loader import ContextLoader, ContextBundle
from tests.layer2.test_workspace import _make_workspace


def test_load_returns_bundle(tmp_path):
    """load() returns a ContextBundle with all layers."""
    root = _make_workspace(tmp_path)
    loader = ContextLoader(root)
    bundle = loader.load(stage="01-research")
    assert isinstance(bundle, ContextBundle)
    assert bundle.layer0 != ""
    assert bundle.layer1 != ""
    assert bundle.layer2 is not None


def test_bundle_respects_token_budget(tmp_path):
    """ContextBundle total token estimate respects budget."""
    root = _make_workspace(tmp_path)
    loader = ContextLoader(root)
    bundle = loader.load(stage="01-research", token_budget=2000)
    assert bundle.total_tokens() <= 2000


def test_no_stage_loads_layers_0_and_1_only(tmp_path):
    """Without stage, loads only Layer 0 and 1."""
    root = _make_workspace(tmp_path)
    loader = ContextLoader(root)
    bundle = loader.load()
    assert bundle.layer0 != ""
    assert bundle.layer1 != ""
    assert bundle.layer2 is None


def test_bundle_as_text(tmp_path):
    """as_text() concatenates layers with separators."""
    root = _make_workspace(tmp_path)
    loader = ContextLoader(root)
    bundle = loader.load(stage="01-research")
    text = bundle.as_text()
    assert "---" in text
    assert "# Workspace" in text


def test_missing_stage_raises(tmp_path):
    """Raises ValueError for unknown stage name."""
    root = _make_workspace(tmp_path)
    loader = ContextLoader(root)
    with pytest.raises(ValueError, match="Stage not found"):
        loader.load(stage="99-nonexistent")
