from pathlib import Path
import pytest
from msp.layer2.workspace import Workspace


def _make_workspace(tmp_path: Path) -> Path:
    """Create a minimal ICM workspace for testing."""
    root = tmp_path / "my-workspace"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# Workspace\n\n## Folder Map\n")
    (root / "CONTEXT.md").write_text(
        "## Inputs\n| Source | File/Location | Section/Scope | Why |\n"
        "|--------|--------------|---------------|-----|\n\n"
        "## Process\n1. Route task\n\n"
        "## Outputs\n| Artifact | Location | Format |\n|----------|----------|--------|\n"
    )
    stage = root / "stages" / "01-research"
    stage.mkdir(parents=True)
    (stage / "CONTEXT.md").write_text(
        "## Inputs\n| Source | File/Location | Section/Scope | Why |\n"
        "|--------|--------------|---------------|-----|\n\n"
        "## Process\n1. Research\n\n"
        "## Outputs\n| Artifact | Location | Format |\n|----------|----------|--------|\n"
        "| Notes | output/notes.md | Markdown |\n"
    )
    (stage / "output").mkdir()
    return root


def test_discover_stages(tmp_path):
    """Discovers numbered stage directories."""
    root = _make_workspace(tmp_path)
    ws = Workspace(root)
    stages = ws.stages()
    assert len(stages) == 1
    assert stages[0].name == "01-research"


def test_layer0_is_claude_md(tmp_path):
    """Layer 0 returns CLAUDE.md content."""
    root = _make_workspace(tmp_path)
    ws = Workspace(root)
    assert "# Workspace" in ws.layer0()


def test_layer1_is_root_context(tmp_path):
    """Layer 1 returns root CONTEXT.md content."""
    root = _make_workspace(tmp_path)
    ws = Workspace(root)
    assert "Route task" in ws.layer1()


def test_stage_contract(tmp_path):
    """Returns parsed StageContract for a named stage."""
    root = _make_workspace(tmp_path)
    ws = Workspace(root)
    contract = ws.stage_contract("01-research")
    assert contract.process_steps == ["Research"]


def test_stage_complete_when_output_exists(tmp_path):
    """Stage is complete when output/ has non-gitkeep files."""
    root = _make_workspace(tmp_path)
    output = root / "stages" / "01-research" / "output"
    (output / "notes.md").write_text("Research notes.")
    ws = Workspace(root)
    assert ws.stage_complete("01-research") is True


def test_stage_pending_when_output_empty(tmp_path):
    """Stage is pending when output/ is empty."""
    root = _make_workspace(tmp_path)
    ws = Workspace(root)
    assert ws.stage_complete("01-research") is False


def test_invalid_workspace_raises(tmp_path):
    """Raises ValueError if root lacks CLAUDE.md."""
    ws = Workspace(tmp_path)
    with pytest.raises(ValueError, match="CLAUDE.md"):
        ws.layer0()
