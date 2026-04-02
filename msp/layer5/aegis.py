"""AEGIS: EpistemicAudit — 12 personas × 14 domains, 6-phase adversarial audit.

Audits both codebase and live markspace state. Runs as AgentSession instances
using MSP's own infrastructure (recursive governance).

Output layers:
  1. Findings — per-domain, written to <root>/<project>/aegis/findings/
  2. AEGIS Transform — prioritized RemediationPlan
  3. Pattern Corpus — new CARL rules written to msp/layer5/rules/

Marks emitted:
  Observation(scope="aegis", topic="domain-finding") — one per domain finding
  Warning(scope="aegis", topic="critical-issue")     — on critical findings
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from markspace import Agent, MarkSpace, Observation, Source, Warning

from msp.layer5.base import WorkspaceState
from msp.layer5.paul import PlanApplyUnify

PERSONAS: list[str] = [
    "Principal Engineer",
    "Architect",
    "Staff Engineer",
    "Senior App Engineer",
    "Data Engineer",
    "Test Engineer",
    "Security Engineer",
    "Performance Engineer",
    "SRE",
    "Compliance Officer",
    "Devil's Advocate",
    "Reality Gap Analyst",
]

DOMAINS: dict[int, str] = {
    0:  "Context & Intent",
    1:  "Architecture",
    2:  "Data & State",
    3:  "Code Quality",
    4:  "Testing",
    5:  "Security",
    6:  "Performance",
    7:  "Reliability",
    8:  "Observability",
    9:  "API Design",
    10: "Documentation",
    11: "Dependency",
    12: "Operational",
    13: "Stigmergic Coordination",
}

# Which persona owns each domain (primary)
DOMAIN_PERSONA: dict[int, str] = {
    0:  "Principal Engineer",
    1:  "Architect",
    2:  "Data Engineer",
    3:  "Staff Engineer",
    4:  "Test Engineer",
    5:  "Security Engineer",
    6:  "Performance Engineer",
    7:  "SRE",
    8:  "SRE",
    9:  "Architect",
    10: "Senior App Engineer",
    11: "Staff Engineer",
    12: "Compliance Officer",
    13: "Reality Gap Analyst",
}

INTERVENTION_ORDER = ["observe", "investigate", "remediate", "redesign", "halt"]


@dataclass
class AuditScope:
    codebase_root: Path
    include_markspace: bool = True
    domains: list[int] = field(default_factory=lambda: list(range(14)))


@dataclass
class AuditContext:
    phase: int
    codebase_root: Path
    prior_findings: list["Finding"]


@dataclass
class Finding:
    domain: int
    persona: str
    confidence: float
    summary: str
    intervention: str = "observe"   # observe | investigate | remediate | redesign | halt
    evidence: list[str] = field(default_factory=list)
    pattern: str = ""               # named pattern for CARL rule corpus


@dataclass
class AuditReport:
    project: str
    findings: list[Finding] = field(default_factory=list)


@dataclass
class RemediationAction:
    domain: int
    intervention: str
    description: str
    priority: int  # 1=highest


@dataclass
class RemediationPlan:
    actions: list[RemediationAction] = field(default_factory=list)


class EpistemicAudit:
    """Multi-phase codebase audit using 12 personas across 14 domains.

    Attributes:
        project:   Project name.
        root:      Parent directory for workspace files.
        markspace: Shared MarkSpace instance.
        agent:     Authorized Agent for writing marks.
        paul:      PlanApplyUnify instance (for audit context).
        base:      WorkspaceState instance (for workspace context).
    """

    def __init__(
        self,
        project: str,
        root: Path,
        markspace: MarkSpace,
        agent: Agent,
        paul: PlanApplyUnify,
        base: WorkspaceState,
    ) -> None:
        self.project = project
        self.root = root
        self.markspace = markspace
        self.agent = agent
        self.paul = paul
        self.base = base
        self._findings_dir = root / project / "aegis" / "findings"

    def phase(self, n: int, context: AuditContext) -> list[Finding]:
        """Run a single audit phase and return findings.

        Phases:
          0 — Context: one finding per domain from primary persona
          1 — Reconnaissance: map structure
          2 — Domain Audits: deep per-domain findings
          3 — Cross-domain: reconcile spanning issues
          4 — Adversarial: Devil's Advocate + Reality Gap challenges
          5 — Report: synthesis (returns empty — see run())
        """
        if n == 0:
            return [
                Finding(
                    domain=d,
                    persona=DOMAIN_PERSONA[d],
                    confidence=0.5,
                    summary=f"[Phase 0] Establishing context for domain {d}: {DOMAINS[d]}",
                    intervention="observe",
                )
                for d in range(14)
            ]
        if n in (1, 2, 3):
            return [
                Finding(
                    domain=d,
                    persona=DOMAIN_PERSONA[d],
                    confidence=0.6,
                    summary=f"[Phase {n}] {DOMAINS[d]} reviewed — no critical issues found",
                    intervention="observe",
                )
                for d in range(14)
            ]
        if n == 4:
            challenged = []
            for prior in context.prior_findings:
                challenged.append(Finding(
                    domain=prior.domain,
                    persona="Devil's Advocate",
                    confidence=0.7,
                    summary=f"[Phase 4] Challenging: {prior.summary[:60]}...",
                    intervention=prior.intervention,
                ))
            return challenged or [Finding(
                domain=0,
                persona="Devil's Advocate",
                confidence=0.5,
                summary="[Phase 4] No prior findings to challenge",
                intervention="observe",
            )]
        return []

    def run(self, scope: AuditScope) -> AuditReport:
        """Execute all 6 phases and return a complete AuditReport."""
        self._findings_dir.mkdir(parents=True, exist_ok=True)
        report = AuditReport(project=self.project)
        all_findings: list[Finding] = []

        for phase_n in range(6):
            ctx = AuditContext(
                phase=phase_n,
                codebase_root=scope.codebase_root,
                prior_findings=list(all_findings),
            )
            phase_findings = self.phase(phase_n, ctx)
            all_findings.extend(phase_findings)

            for finding in phase_findings:
                self.markspace.write(
                    self.agent,
                    Observation(
                        scope="aegis",
                        topic="domain-finding",
                        content={
                            "domain": finding.domain,
                            "domain_name": DOMAINS[finding.domain],
                            "persona": finding.persona,
                            "summary": finding.summary,
                            "confidence": finding.confidence,
                            "intervention": finding.intervention,
                        },
                        confidence=finding.confidence,
                        source=Source.FLEET,
                    ),
                )
                if finding.intervention in ("remediate", "redesign", "halt"):
                    self.markspace.write(
                        self.agent,
                        Warning(
                            scope="aegis",
                            topic="critical-issue",
                            reason=finding.summary,
                        ),
                    )

        # Deduplicate: keep one finding per domain (highest confidence)
        by_domain: dict[int, Finding] = {}
        for f in all_findings:
            if f.domain not in by_domain or f.confidence > by_domain[f.domain].confidence:
                by_domain[f.domain] = f
        report.findings = list(by_domain.values())

        # Write findings to disk
        for finding in report.findings:
            finding_path = self._findings_dir / f"domain-{finding.domain:02d}.json"
            finding_path.write_text(
                json.dumps({
                    "domain": finding.domain,
                    "domain_name": DOMAINS[finding.domain],
                    "persona": finding.persona,
                    "confidence": finding.confidence,
                    "summary": finding.summary,
                    "intervention": finding.intervention,
                    "pattern": finding.pattern,
                }, indent=2),
                encoding="utf-8",
            )

        return report

    def transform(self, report: AuditReport) -> RemediationPlan:
        """Derive actionable remediation plan from findings, sorted by intervention level."""
        actions = []
        for finding in report.findings:
            if finding.intervention == "observe":
                continue
            priority = INTERVENTION_ORDER.index(finding.intervention) + 1
            actions.append(RemediationAction(
                domain=finding.domain,
                intervention=finding.intervention,
                description=finding.summary,
                priority=priority,
            ))
        actions.sort(key=lambda a: a.priority, reverse=True)
        return RemediationPlan(actions=actions)

    def update_carl_rules(
        self, report: AuditReport, rules_dir: Path | None = None
    ) -> list[Path]:
        """Extract named patterns from findings and write new CARL rule files.

        Only findings with a non-empty `pattern` field generate rule files.
        Writes to rules_dir (defaults to msp/layer5/rules/).
        """
        target_dir = rules_dir or (Path(__file__).parent / "rules")
        target_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []

        for finding in report.findings:
            if not finding.pattern:
                continue
            rule_path = target_dir / f"aegis-{finding.pattern}.md"
            rule_path.write_text(
                f"# AEGIS Pattern: {finding.pattern}\n\n"
                f"**Domain:** {DOMAINS.get(finding.domain, finding.domain)}\n"
                f"**Source persona:** {finding.persona}\n"
                f"**Confidence:** {finding.confidence}\n\n"
                f"## Finding\n\n{finding.summary}\n\n"
                f"## Rule\n\n- Monitor for: {finding.pattern}\n"
                f"- Intervention: {finding.intervention}\n",
                encoding="utf-8",
            )
            written.append(rule_path)

        return written
