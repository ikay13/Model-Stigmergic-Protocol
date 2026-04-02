"""Tests for CapabilityStandards (SKILLSMITH) — 7-file taxonomy, audit, scaffold."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from msp.layer5.skillsmith import CapabilityStandards, SkillSpec, AuditReport


@pytest.fixture
def skillsmith():
    return CapabilityStandards(markspace=MagicMock(), agent=MagicMock())


@pytest.fixture
def compliant_skill(tmp_path):
    """Create a fully compliant 7-file skill skeleton."""
    skill_dir = tmp_path / "my-skill"
    (skill_dir / "tasks").mkdir(parents=True)
    (skill_dir / "frameworks").mkdir()
    (skill_dir / "templates").mkdir()
    (skill_dir / "context").mkdir()
    (skill_dir / "checklists").mkdir()
    (skill_dir / "rules").mkdir()
    (skill_dir / "entry-point.md").write_text("# Entry Point\n## Routing\n- task1")
    (skill_dir / "tasks" / "task1.md").write_text("# Task 1")
    (skill_dir / "frameworks" / "domain.md").write_text("# Domain Knowledge")
    (skill_dir / "templates" / "output.md").write_text("# Output Template")
    (skill_dir / "context" / "background.md").write_text("# Background")
    (skill_dir / "checklists" / "quality.md").write_text("# Quality Gate")
    (skill_dir / "rules" / "constraints.md").write_text("# Constraints")
    return skill_dir


@pytest.fixture
def missing_entry_point_skill(tmp_path):
    skill_dir = tmp_path / "bad-skill"
    (skill_dir / "tasks").mkdir(parents=True)
    (skill_dir / "tasks" / "task1.md").write_text("# Task")
    return skill_dir


def test_audit_compliant_skill_has_no_critical_violations(skillsmith, compliant_skill):
    report = skillsmith.audit(compliant_skill)
    assert isinstance(report, AuditReport)
    critical = [v for v in report.violations if v["severity"] == "critical"]
    assert critical == []


def test_audit_missing_entry_point_is_critical(skillsmith, missing_entry_point_skill):
    report = skillsmith.audit(missing_entry_point_skill)
    critical = [v for v in report.violations if v["severity"] == "critical"]
    assert len(critical) == 1
    assert "entry-point" in critical[0]["file"]


def test_audit_missing_checklist_is_minor(skillsmith, tmp_path):
    skill_dir = tmp_path / "skill"
    (skill_dir / "tasks").mkdir(parents=True)
    (skill_dir / "entry-point.md").write_text("# Entry Point")
    (skill_dir / "tasks" / "t.md").write_text("# T")
    report = skillsmith.audit(skill_dir)
    minor = [v for v in report.violations if v["severity"] == "minor"]
    assert any("checklists" in v["file"] for v in minor)


def test_audit_emits_warning_marks_for_violations(tmp_path):
    ms = MagicMock()
    agent = MagicMock()
    sm = CapabilityStandards(markspace=ms, agent=agent)
    skill_dir = tmp_path / "skill"
    (skill_dir / "tasks").mkdir(parents=True)
    sm.audit(skill_dir)
    assert ms.write.called


def test_scaffold_creates_all_7_required_paths(skillsmith, tmp_path):
    spec = SkillSpec(name="my-tool", purpose="automate X", domains=["development"])
    dest = tmp_path / "generated"
    skill_dir = skillsmith.scaffold(spec, dest)
    assert (skill_dir / "entry-point.md").exists()
    assert (skill_dir / "tasks").is_dir()
    assert (skill_dir / "frameworks").is_dir()
    assert (skill_dir / "templates").is_dir()
    assert (skill_dir / "context").is_dir()
    assert (skill_dir / "checklists").is_dir()
    assert (skill_dir / "rules").is_dir()


def test_scaffold_then_audit_passes(skillsmith, tmp_path):
    """A freshly scaffolded skill has no critical violations."""
    spec = SkillSpec(name="new-skill", purpose="do things", domains=["planning"])
    dest = tmp_path / "gen"
    skill_dir = skillsmith.scaffold(spec, dest)
    report = skillsmith.audit(skill_dir)
    critical = [v for v in report.violations if v["severity"] == "critical"]
    assert critical == []


def test_validate_session_returns_true_for_compliant(skillsmith, compliant_skill):
    session = MagicMock()
    session.skill_path = compliant_skill
    assert skillsmith.validate_session(session) is True


def test_validate_session_returns_false_and_emits_need_for_critical(tmp_path):
    ms = MagicMock()
    agent = MagicMock()
    sm = CapabilityStandards(markspace=ms, agent=agent)
    skill_dir = tmp_path / "bad"
    skill_dir.mkdir()
    # No entry-point.md
    session = MagicMock()
    session.skill_path = skill_dir
    result = sm.validate_session(session)
    assert result is False
    from markspace import Need
    calls = ms.write.call_args_list
    need_calls = [c for c in calls if isinstance(c.args[1], Need)]
    assert len(need_calls) == 1
