# tests/layer2/test_context_loader_extra_paths.py
"""Test extra_paths support added for CARL (Layer 5) integration."""
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from msp.layer2.context_loader import ContextLoader


def test_load_includes_extra_paths_content(tmp_path):
    """extra_paths content appears in the returned ContextBundle references."""
    (tmp_path / "CLAUDE.md").write_text("# Workspace Identity")
    (tmp_path / "CONTEXT.md").write_text("# Routing")

    rule_file = tmp_path / "extra_rule.md"
    rule_file.write_text("# Development Rules\nUse TDD.")

    loader = ContextLoader(tmp_path)
    bundle = loader.load(extra_paths=[rule_file])
    assert any("Development Rules" in ref for ref in bundle.references)


def test_load_with_no_extra_paths_unchanged(tmp_path):
    """Passing no extra_paths gives same result as before (backwards compat)."""
    (tmp_path / "CLAUDE.md").write_text("# Workspace Identity")
    (tmp_path / "CONTEXT.md").write_text("# Routing")
    loader = ContextLoader(tmp_path)
    bundle_before = loader.load()
    bundle_after = loader.load(extra_paths=[])
    assert bundle_before.as_text() == bundle_after.as_text()
