"""SKILLSMITH: CapabilityStandards — 7-file skill taxonomy, compliance audit, scaffold.

Enforces the 7-file skill structure before AgentSession launches.

7-file taxonomy:
  entry-point.md    — routing and persona (CRITICAL if missing)
  tasks/*.md        — task definitions
  frameworks/*.md   — domain knowledge
  templates/*.md    — output templates
  context/*.md      — background context
  checklists/*.md   — quality gates (MINOR if missing)
  rules/*.md        — authoring constraints (MINOR if missing)

Marks emitted:
  Warning(scope="skillsmith", topic="compliance-violation") per violation
  Need(scope="skillsmith", question=...)                    on critical failure
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from markspace import Agent, MarkSpace, Need, Warning
from markspace.core import Severity


@dataclass
class SkillSpec:
    name: str
    purpose: str
    domains: list[str]


@dataclass
class AuditReport:
    skill_path: Path
    violations: list[dict] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(v["severity"] == "critical" for v in self.violations)


# (file_or_dir, severity_label, Severity enum value, description)
TAXONOMY: list[tuple[str, str, Severity, str]] = [
    ("entry-point.md", "critical", Severity.CRITICAL, "skill entry point"),
    ("tasks",          "critical", Severity.CRITICAL, "task definitions directory"),
    ("frameworks",     "minor",    Severity.CAUTION,  "domain knowledge directory"),
    ("templates",      "minor",    Severity.CAUTION,  "output templates directory"),
    ("context",        "minor",    Severity.CAUTION,  "background context directory"),
    ("checklists",     "minor",    Severity.CAUTION,  "quality gates directory"),
    ("rules",          "minor",    Severity.CAUTION,  "authoring constraints directory"),
]


class CapabilityStandards:
    """Enforces the 7-file skill taxonomy for AgentSession pre-flight checks.

    Attributes:
        markspace: Shared MarkSpace instance.
        agent:     Authorized Agent for writing marks.
    """

    def __init__(self, markspace: MarkSpace, agent: Agent | None = None) -> None:
        self.markspace = markspace
        self.agent = agent

    def audit(self, skill_path: Path) -> AuditReport:
        """Check skill directory against 7-file taxonomy. Emits Warning marks for violations."""
        report = AuditReport(skill_path=skill_path)

        for name, severity_label, severity_enum, description in TAXONOMY:
            target = skill_path / name
            if not target.exists():
                violation = {"file": name, "severity": severity_label, "description": f"Missing {description}"}
                report.violations.append(violation)
                if self.agent is not None:
                    self.markspace.write(
                        self.agent,
                        Warning(
                            scope="skillsmith",
                            topic="compliance-violation",
                            reason=f"Missing {description}: {name}",
                            severity=severity_enum,
                        ),
                    )

        return report

    def scaffold(self, spec: SkillSpec, dest: Path) -> Path:
        """Generate a compliant skill skeleton from a SkillSpec."""
        skill_dir = dest / spec.name
        skill_dir.mkdir(parents=True, exist_ok=True)

        (skill_dir / "entry-point.md").write_text(
            f"# {spec.name}\n\n**Purpose:** {spec.purpose}\n\n## Routing\n\n- task1\n",
            encoding="utf-8",
        )
        for subdir in ("tasks", "frameworks", "templates", "context", "checklists", "rules"):
            sub = skill_dir / subdir
            sub.mkdir(exist_ok=True)
            placeholder = sub / f"{subdir[:-1] if subdir.endswith('s') else subdir}.md"
            placeholder.write_text(f"# {subdir.title()}\n\n<!-- Add content here -->\n", encoding="utf-8")

        return skill_dir

    def validate_session(self, session: object) -> bool:
        """Run pre-flight compliance check on session's skill_path.

        Returns True if no critical violations. On critical failure,
        emits a Need mark requesting remediation and returns False.
        """
        skill_path = getattr(session, "skill_path", None)
        if skill_path is None:
            return True  # session has no skill_path — not subject to SKILLSMITH

        report = self.audit(skill_path)
        if not report.passed and self.agent is not None:
            critical = [v for v in report.violations if v["severity"] == "critical"]
            self.markspace.write(
                self.agent,
                Need(
                    scope="skillsmith",
                    question=f"Skill at {skill_path} has {len(critical)} critical violation(s): "
                             + ", ".join(v["file"] for v in critical),
                    context={"skill_path": str(skill_path), "violations": critical},
                    priority=1.0,
                    blocking=True,
                ),
            )
        return report.passed
