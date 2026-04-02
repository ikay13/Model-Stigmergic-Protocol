"""Tests for msp.cli — SEED, PAUL plan, AEGIS subcommands."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# Python executable guaranteed to have a working pydantic install
PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python"


def _run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Invoke the CLI via `python -m msp` with the venv python."""
    return subprocess.run(
        [str(PYTHON), "-m", "msp", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# SEED
# ---------------------------------------------------------------------------

def test_seed_command_creates_planning_md(tmp_path):
    result = _run_cli(
        [
            "seed",
            "--type", "software",
            "--name", "myproject",
            "--goal", "Build auth",
            "--goal", "Add tests",
            "--root", str(tmp_path),
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, f"SEED failed:\n{result.stderr}"

    planning_md = tmp_path / "myproject" / "PLANNING.md"
    assert planning_md.exists(), f"PLANNING.md not found at {planning_md}"

    content = planning_md.read_text()
    assert "myproject" in content
    assert "Build auth" in content
    assert "Add tests" in content


def test_seed_command_prints_planning_path(tmp_path):
    result = _run_cli(
        [
            "seed",
            "--type", "research",
            "--name", "researchproj",
            "--goal", "Collect data",
            "--root", str(tmp_path),
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert "PLANNING" in result.stdout
    assert "researchproj" in result.stdout


# ---------------------------------------------------------------------------
# PAUL plan
# ---------------------------------------------------------------------------

def test_paul_plan_command_creates_state_md(tmp_path):
    result = _run_cli(
        [
            "paul", "plan",
            "--project", "myproject",
            "--milestone", "m1:Build auth:tests pass",
            "--root", str(tmp_path),
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, f"PAUL plan failed:\n{result.stderr}"

    state_md = tmp_path / "paul" / "STATE.md"
    assert state_md.exists(), f"STATE.md not found at {state_md}"

    content = state_md.read_text()
    assert "myproject" in content
    assert "m1" in content


def test_paul_plan_command_creates_milestones_md(tmp_path):
    result = _run_cli(
        [
            "paul", "plan",
            "--project", "planproj",
            "--milestone", "m1:First milestone:criterion one",
            "--milestone", "m2:Second milestone:criterion two",
            "--root", str(tmp_path),
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr

    milestones_md = tmp_path / "paul" / "MILESTONES.md"
    assert milestones_md.exists(), f"MILESTONES.md not found at {milestones_md}"

    content = milestones_md.read_text()
    assert "First milestone" in content
    assert "Second milestone" in content


def test_paul_plan_bad_milestone_format_exits_nonzero(tmp_path):
    result = _run_cli(
        [
            "paul", "plan",
            "--project", "p",
            "--milestone", "bad-format-no-colons",
            "--root", str(tmp_path),
        ],
        cwd=tmp_path,
    )
    assert result.returncode != 0


# ---------------------------------------------------------------------------
# AEGIS
# ---------------------------------------------------------------------------

def test_aegis_command_creates_findings_dir(tmp_path):
    result = _run_cli(
        [
            "aegis",
            "--project", "myproject",
            "--root", str(tmp_path),
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, f"AEGIS failed:\n{result.stderr}"

    findings_dir = tmp_path / "myproject" / "aegis" / "findings"
    assert findings_dir.exists(), f"Findings dir not found at {findings_dir}"
    assert findings_dir.is_dir()


def test_aegis_command_writes_domain_findings(tmp_path):
    result = _run_cli(
        [
            "aegis",
            "--project", "auditproj",
            "--root", str(tmp_path),
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr

    findings_dir = tmp_path / "auditproj" / "aegis" / "findings"
    json_files = list(findings_dir.glob("domain-*.json"))
    assert len(json_files) > 0, "No domain finding files written"


def test_aegis_command_prints_findings_count(tmp_path):
    result = _run_cli(
        [
            "aegis",
            "--project", "countproj",
            "--root", str(tmp_path),
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert "Findings" in result.stdout
