"""Tests for EpistemicAudit (AEGIS) — 6-phase audit, 12 personas, 14 domains."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from msp.layer5.aegis import (
    EpistemicAudit, AuditScope, AuditContext, Finding, AuditReport, RemediationPlan,
    PERSONAS, DOMAINS,
)


@pytest.fixture
def aegis(tmp_path):
    ms = MagicMock()
    ms.read.return_value = []
    paul = MagicMock()
    base = MagicMock()
    base.load.return_value = {"health": "ok"}
    return EpistemicAudit(
        project="test", root=tmp_path, markspace=ms, agent=MagicMock(), paul=paul, base=base
    )


def test_personas_count_is_12():
    assert len(PERSONAS) == 12


def test_domains_count_is_14():
    assert len(DOMAINS) == 14


def test_domain_13_is_stigmergic_coordination():
    assert DOMAINS[13] == "Stigmergic Coordination"


def test_finding_dataclass():
    f = Finding(domain=1, persona="Architect", confidence=0.8, summary="Architecture is layered correctly")
    assert f.domain == 1
    assert f.confidence == 0.8


def test_phase_returns_list_of_findings(aegis):
    ctx = AuditContext(phase=0, codebase_root=Path("."), prior_findings=[])
    findings = aegis.phase(0, ctx)
    assert isinstance(findings, list)
    assert len(findings) >= 1  # Domain 0 always produces a finding


def test_all_14_domains_produce_findings_in_run(aegis):
    """Every domain must produce at least one finding per run."""
    scope = AuditScope(codebase_root=Path("."), include_markspace=False)
    report = aegis.run(scope)
    covered_domains = {f.domain for f in report.findings}
    assert covered_domains == set(range(14))


def test_run_writes_findings_to_disk(aegis, tmp_path):
    scope = AuditScope(codebase_root=Path("."), include_markspace=False)
    aegis.run(scope)
    findings_dir = tmp_path / "test" / "aegis" / "findings"
    assert findings_dir.exists()
    assert len(list(findings_dir.glob("*.json"))) > 0


def test_transform_returns_remediation_plan(aegis):
    report = AuditReport(
        project="test",
        findings=[
            Finding(domain=0, persona="Principal Engineer", confidence=0.9,
                    summary="System purpose is clear", intervention="observe"),
            Finding(domain=5, persona="Security Engineer", confidence=0.7,
                    summary="Auth tokens stored in plaintext", intervention="remediate"),
        ]
    )
    plan = aegis.transform(report)
    assert isinstance(plan, RemediationPlan)
    assert len(plan.actions) >= 1


def test_update_carl_rules_writes_rule_files(aegis, tmp_path):
    report = AuditReport(
        project="test",
        findings=[
            Finding(domain=13, persona="Reality Gap Analyst", confidence=0.85,
                    summary="Agents emitting marks outside declared scope",
                    intervention="remediate", pattern="scope-violation"),
        ]
    )
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    paths = aegis.update_carl_rules(report, rules_dir=rules_dir)
    assert len(paths) >= 1
    assert all(p.suffix == ".md" for p in paths)


def test_run_emits_observation_marks_per_domain(aegis):
    scope = AuditScope(codebase_root=Path("."), include_markspace=False)
    aegis.run(scope)
    from markspace import Observation
    calls = aegis.markspace.write.call_args_list
    obs_calls = [c for c in calls if isinstance(c.args[1], Observation)]
    assert len(obs_calls) >= 14  # at least one per domain
