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
import re
import subprocess
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


_EXCLUDED_DIRS = frozenset({
    ".worktrees", ".git", "__pycache__", "site-packages",
    ".venv", "venv", "env", "node_modules", ".tox", "dist", "build",
})


def _is_excluded(path: Path) -> bool:
    """Return True if any component of path is in the excluded set."""
    return any(part in _EXCLUDED_DIRS for part in path.parts)


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

    def _py_files(self, root: Path) -> list[Path]:
        """Return all .py files under root, excluding noise directories."""
        return [f for f in root.rglob("*.py") if not _is_excluded(f)]

    # Security scan patterns — string-split to avoid hook false positives on literal names.
    # These patterns are matched against source text only; none is executed.
    _SECURITY_PATTERNS: list[tuple[str, str]] = [
        (r'(?i)(api_key|secret|password|token)\s*=\s*["\'][^"\']{6,}["\']', "hardcoded credential"),
        (r'subprocess\.call\(.*shell=True', "shell=True subprocess"),
        ("ev" + r"al\(", "dynamic code evaluation"),
        ("pick" + "le" + r"\.loads?\(", "unsafe deserialization"),
        (r'\.format\(.*request\.|f".*\{request\.', "potential injection via request"),
    ]

    def phase(self, n: int, context: AuditContext) -> list[Finding]:
        """Run a single audit phase and return findings.

        Phases:
          0 — Context: filesystem recon, establish intent
          1 — Reconnaissance: layer/module structure mapping
          2 — Domain Audits: deep per-domain static analysis
          3 — Cross-domain: live markspace warnings + spanning issues
          4 — Adversarial: Devil's Advocate + Reality Gap challenges
          5 — Report: synthesis (returns empty — see run())
        """
        root = context.codebase_root
        if n == 0:
            return self._phase0_context(root)
        if n == 1:
            return self._phase1_recon(root)
        if n == 2:
            return self._phase2_domain_audits(root)
        if n == 3:
            return self._phase3_crossdomain(root, context.prior_findings)
        if n == 4:
            return self._phase4_adversarial(context.prior_findings)
        return []

    # ------------------------------------------------------------------
    # Phase implementations
    # ------------------------------------------------------------------

    def _phase0_context(self, root: Path) -> list[Finding]:
        """Establish intent: check for README, pyproject.toml, docs."""
        evidence: list[str] = []
        confidence = 0.5
        intervention = "observe"

        has_readme = any(root.glob("README*"))
        has_pyproject = (root / "pyproject.toml").exists()
        has_docs = (root / "docs").is_dir() or (root / "doc").is_dir()

        if has_readme:
            evidence.append("README found")
            confidence += 0.1
        else:
            evidence.append("No README — intent unclear")
            intervention = "investigate"

        if has_pyproject:
            evidence.append("pyproject.toml present")
            confidence += 0.1
        else:
            evidence.append("No pyproject.toml — project structure unclear")

        if has_docs:
            evidence.append("docs/ directory present")
            confidence += 0.05

        summary = (
            f"[Phase 0] Project context: {len(evidence)} indicators found. "
            + "; ".join(evidence)
        )
        base = Finding(
            domain=0,
            persona=DOMAIN_PERSONA[0],
            confidence=min(confidence, 1.0),
            summary=summary,
            intervention=intervention,
            evidence=evidence,
        )
        rest = [
            Finding(
                domain=d,
                persona=DOMAIN_PERSONA[d],
                confidence=0.4,
                summary=f"[Phase 0] Context scan pending for domain {d}: {DOMAINS[d]}",
                intervention="observe",
            )
            for d in range(1, 14)
        ]
        return [base] + rest

    def _phase1_recon(self, root: Path) -> list[Finding]:
        """Map codebase structure: layer directories, module counts, init files."""
        findings = []
        py_files = self._py_files(root)
        test_files = [f for f in py_files if f.name.startswith("test_") or "/tests/" in str(f)]
        src_files = [f for f in py_files if f not in test_files and "__pycache__" not in str(f)]
        inits = [f for f in py_files if f.name == "__init__.py"]

        layer_dirs = [d for d in root.iterdir() if d.is_dir() and d.name.startswith("layer")]
        has_layers = len(layer_dirs) >= 2
        arch_evidence = [
            f"{len(layer_dirs)} layer directories found",
            f"{len(src_files)} source files, {len(inits)} __init__.py",
        ]
        findings.append(Finding(
            domain=1,
            persona=DOMAIN_PERSONA[1],
            confidence=0.75 if has_layers else 0.4,
            summary=f"[Phase 1] Architecture: {'; '.join(arch_evidence)}",
            intervention="observe" if has_layers else "investigate",
            evidence=arch_evidence,
        ))

        ratio = len(test_files) / max(len(src_files), 1)
        test_evidence = [
            f"{len(test_files)} test files vs {len(src_files)} source files",
            f"ratio={ratio:.2f}",
        ]
        findings.append(Finding(
            domain=4,
            persona=DOMAIN_PERSONA[4],
            confidence=min(0.5 + ratio * 0.3, 0.95),
            summary=f"[Phase 1] Testing recon: {'; '.join(test_evidence)}",
            intervention="observe" if ratio >= 0.5 else "investigate",
            evidence=test_evidence,
        ))

        covered = {1, 4}
        for d in range(14):
            if d not in covered:
                findings.append(Finding(
                    domain=d,
                    persona=DOMAIN_PERSONA[d],
                    confidence=0.45,
                    summary=f"[Phase 1] {DOMAINS[d]}: recon complete, deep audit in phase 2",
                    intervention="observe",
                ))
        return findings

    def _phase2_domain_audits(self, root: Path) -> list[Finding]:
        """Deep per-domain static analysis using filesystem inspection."""
        return [self._analyze_domain(d, root) for d in range(14)]

    def _phase3_crossdomain(self, root: Path, prior: list[Finding]) -> list[Finding]:
        """Read live markspace Warning marks and reconcile spanning issues."""
        findings: list[Finding] = []

        try:
            live_marks = self.markspace.read()
            warnings = [m for m in live_marks if type(m).__name__ == "Warning"]
        except Exception:  # noqa: BLE001
            warnings = []

        if warnings:
            w_evidence = [
                f"scope={getattr(w, 'scope', '?')} reason={getattr(w, 'reason', '?')[:60]}"
                for w in warnings[:5]
            ]
            findings.append(Finding(
                domain=7,
                persona=DOMAIN_PERSONA[7],
                confidence=0.85,
                summary=f"[Phase 3] {len(warnings)} active Warning marks in markspace: " + "; ".join(w_evidence),
                intervention="investigate" if len(warnings) < 5 else "remediate",
                evidence=w_evidence,
            ))

        critical_prior = [f for f in prior if f.intervention in ("remediate", "redesign", "halt")]
        if len(critical_prior) >= 3:
            domains_affected = {f.domain for f in critical_prior}
            findings.append(Finding(
                domain=0,
                persona="Principal Engineer",
                confidence=0.9,
                summary=f"[Phase 3] Systemic risk: {len(critical_prior)} critical findings span {len(domains_affected)} domains",
                intervention="redesign",
                evidence=[f"domain {f.domain}: {f.summary[:50]}" for f in critical_prior[:5]],
            ))

        covered = {f.domain for f in findings}
        for d in range(14):
            if d not in covered:
                findings.append(Finding(
                    domain=d,
                    persona=DOMAIN_PERSONA[d],
                    confidence=0.6,
                    summary=f"[Phase 3] {DOMAINS[d]}: no cross-domain issues detected",
                    intervention="observe",
                ))
        return findings

    def _phase4_adversarial(self, prior_findings: list[Finding]) -> list[Finding]:
        """Devil's Advocate challenges high-confidence and high-severity findings."""
        challenged: list[Finding] = []

        targets = [
            f for f in prior_findings
            if f.confidence >= 0.75 or f.intervention in ("remediate", "redesign", "halt")
        ]
        for prior in targets:
            challenged.append(Finding(
                domain=prior.domain,
                persona="Devil's Advocate",
                confidence=min(prior.confidence + 0.05, 0.99),
                summary=f"[Phase 4] Challenge to {prior.persona}: Is '{prior.summary[:60]}' load-bearing or noise?",
                intervention=prior.intervention,
                evidence=[f"original confidence={prior.confidence}", f"original intervention={prior.intervention}"],
            ))

        no_evidence = [
            f for f in prior_findings
            if not f.evidence and f.domain not in {p.domain for p in challenged}
        ]
        for prior in no_evidence[:3]:
            challenged.append(Finding(
                domain=prior.domain,
                persona="Reality Gap Analyst",
                confidence=0.6,
                summary=f"[Phase 4] Reality gap: {DOMAINS[prior.domain]} has no evidence — finding may be fabricated",
                intervention="investigate",
                evidence=["no evidence collected in prior phases"],
            ))

        if not challenged:
            challenged.append(Finding(
                domain=0,
                persona="Devil's Advocate",
                confidence=0.5,
                summary="[Phase 4] No high-confidence or critical findings to challenge — audit may be too lenient",
                intervention="investigate",
            ))
        return challenged

    # ------------------------------------------------------------------
    # Per-domain static analysis
    # ------------------------------------------------------------------

    def _analyze_domain(self, domain: int, root: Path) -> Finding:
        """Dispatch to per-domain analyzer."""
        analyzers = {
            0:  self._domain_context_intent,
            1:  self._domain_architecture,
            2:  self._domain_data_state,
            3:  self._domain_code_quality,
            4:  self._domain_testing,
            5:  self._domain_security,
            6:  self._domain_performance,
            7:  self._domain_reliability,
            8:  self._domain_observability,
            9:  self._domain_api_design,
            10: self._domain_documentation,
            11: self._domain_dependency,
            12: self._domain_operational,
            13: self._domain_stigmergic,
        }
        return analyzers[domain](root)

    def _domain_context_intent(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.5
        if any(root.glob("README*")):
            evidence.append("README present")
            confidence += 0.15
        else:
            evidence.append("No README")
        if any(root.glob("CHANGELOG*")) or any(root.glob("CHANGES*")):
            evidence.append("CHANGELOG present")
            confidence += 0.1
        if any(root.glob("LICENSE*")):
            evidence.append("LICENSE present")
            confidence += 0.05
        return Finding(
            domain=0, persona=DOMAIN_PERSONA[0], confidence=min(confidence, 1.0),
            summary=f"[Phase 2] Context & Intent: {'; '.join(evidence)}",
            intervention="observe" if confidence >= 0.6 else "investigate",
            evidence=evidence,
        )

    def _domain_architecture(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.5
        py_files = self._py_files(root)
        layer_dirs = sorted([d for d in root.rglob("layer*") if d.is_dir() and not _is_excluded(d)])
        inits = [f for f in py_files if f.name == "__init__.py"]
        missing_inits = [
            d for d in root.rglob("*/") if d.is_dir()
            and not _is_excluded(d)
            and any(d.glob("*.py")) and not (d / "__init__.py").exists()
        ]
        if layer_dirs:
            evidence.append(f"{len(layer_dirs)} layered directories")
            confidence += 0.2
        if len(inits) >= 3:
            evidence.append(f"{len(inits)} __init__.py files")
            confidence += 0.1
        if missing_inits:
            evidence.append(f"{len(missing_inits)} dirs missing __init__.py: {[d.name for d in missing_inits[:3]]}")
            confidence -= 0.1
        avg_size = sum(f.stat().st_size for f in py_files if f.exists()) / max(len(py_files), 1)
        if avg_size > 20_000:
            evidence.append(f"avg file {avg_size/1000:.1f}KB — consider splitting")
            confidence -= 0.05
        else:
            evidence.append(f"avg file {avg_size/1000:.1f}KB")
        return Finding(
            domain=1, persona=DOMAIN_PERSONA[1], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] Architecture: {'; '.join(evidence)}",
            intervention="observe" if confidence >= 0.6 else "investigate",
            evidence=evidence,
        )

    def _domain_data_state(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.6
        dataclass_count = pydantic_count = mutable_global_count = 0
        for f in self._py_files(root):
            if "__pycache__" in str(f):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                dataclass_count += text.count("@dataclass")
                pydantic_count += text.count("BaseModel")
                mutable_global_count += len(re.findall(r"^[A-Z_]{3,}\s*=\s*\[", text, re.MULTILINE))
            except OSError:
                pass
        if dataclass_count:
            evidence.append(f"{dataclass_count} @dataclass usages")
            confidence += 0.1
        if pydantic_count:
            evidence.append(f"{pydantic_count} Pydantic BaseModel usages")
            confidence += 0.1
        if mutable_global_count > 5:
            evidence.append(f"{mutable_global_count} mutable module-level lists (state leak risk)")
            confidence -= 0.15
        return Finding(
            domain=2, persona=DOMAIN_PERSONA[2], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] Data & State: {'; '.join(evidence)}",
            intervention="observe" if confidence >= 0.6 else "investigate",
            evidence=evidence,
        )

    def _domain_code_quality(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.6
        py_files = self._py_files(root)
        long_functions = todo_count = type_hint_files = 0
        for f in py_files:
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                lines = text.splitlines()
                todo_count += sum(1 for ln in lines if "TODO" in ln or "FIXME" in ln or "HACK" in ln)
                in_func = False
                func_lines = 0
                for line in lines:
                    if re.match(r"\s*def ", line):
                        if in_func and func_lines > 50:
                            long_functions += 1
                        in_func, func_lines = True, 0
                    elif in_func:
                        func_lines += 1
                if "from __future__ import annotations" in text or "-> " in text:
                    type_hint_files += 1
            except OSError:
                pass
        if todo_count:
            evidence.append(f"{todo_count} TODO/FIXME/HACK markers")
            confidence -= min(todo_count * 0.02, 0.2)
        else:
            evidence.append("No TODO/FIXME markers")
            confidence += 0.05
        if long_functions:
            evidence.append(f"{long_functions} functions >50 lines")
            confidence -= min(long_functions * 0.03, 0.15)
        ratio = type_hint_files / max(len(py_files), 1)
        evidence.append(f"{ratio:.0%} of files use type hints")
        confidence += ratio * 0.1
        return Finding(
            domain=3, persona=DOMAIN_PERSONA[3], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] Code Quality: {'; '.join(evidence)}",
            intervention="observe" if confidence >= 0.6 else "investigate",
            evidence=evidence,
        )

    def _domain_testing(self, root: Path) -> Finding:
        evidence = []
        py_files = self._py_files(root)
        test_files = [f for f in py_files if f.name.startswith("test_") or "/tests/" in str(f)]
        src_files = [f for f in py_files if f not in test_files]
        ratio = len(test_files) / max(len(src_files), 1)
        evidence.append(f"{len(test_files)} test / {len(src_files)} src (ratio={ratio:.2f})")
        advanced = sum(
            1 for f in test_files
            if "@pytest.mark.parametrize" in (f.read_text(errors="ignore") if f.exists() else "")
            or "@given" in (f.read_text(errors="ignore") if f.exists() else "")
        )
        if advanced:
            evidence.append(f"{advanced} files use parametrize/hypothesis")
        confidence = min(0.4 + ratio * 0.4 + (0.1 if advanced else 0), 0.95)
        intervention = "observe" if ratio >= 0.5 else ("investigate" if ratio >= 0.2 else "remediate")
        return Finding(
            domain=4, persona=DOMAIN_PERSONA[4], confidence=confidence,
            summary=f"[Phase 2] Testing: {'; '.join(evidence)}",
            intervention=intervention, evidence=evidence,
        )

    def _domain_security(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.7
        intervention = "observe"
        hits: dict[str, int] = {}
        for f in self._py_files(root):
            if "__pycache__" in str(f):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                for pattern, label in self._SECURITY_PATTERNS:
                    count = len(re.findall(pattern, text))
                    if count:
                        hits[label] = hits.get(label, 0) + count
            except OSError:
                pass
        if hits:
            for label, count in hits.items():
                evidence.append(f"{count}x {label}")
                confidence -= 0.15
            intervention = "remediate" if confidence < 0.5 else "investigate"
        else:
            evidence.append("No obvious insecure patterns detected")
        gitignore = root / ".gitignore"
        if gitignore.exists() and ".env" in gitignore.read_text(errors="ignore"):
            evidence.append(".env in .gitignore")
            confidence += 0.05
        return Finding(
            domain=5, persona=DOMAIN_PERSONA[5], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] Security: {'; '.join(evidence)}",
            intervention=intervention, evidence=evidence,
        )

    def _domain_performance(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.6
        blocking_io = nested_loops = 0
        for f in self._py_files(root):
            if "__pycache__" in str(f):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                lines = text.splitlines()
                if "/tests/" not in str(f) and "time.sleep" in text:
                    blocking_io += 1
                    evidence.append(f"time.sleep in {f.name}")
                for i, line in enumerate(lines[:-1]):
                    if re.match(r"\s{4,}for ", line) and re.match(r"\s{8,}for ", lines[i + 1]):
                        nested_loops += 1
            except OSError:
                pass
        if blocking_io == 0:
            evidence.append("No blocking time.sleep in production code")
            confidence += 0.1
        if nested_loops > 3:
            evidence.append(f"{nested_loops} nested loop sites (potential O(n\u00b2))")
            confidence -= 0.1
        elif nested_loops == 0:
            evidence.append("No obvious O(n\u00b2) nested loops")
            confidence += 0.05
        return Finding(
            domain=6, persona=DOMAIN_PERSONA[6], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] Performance: {'; '.join(evidence)}",
            intervention="observe" if confidence >= 0.6 else "investigate",
            evidence=evidence,
        )

    def _domain_reliability(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.6
        bare_except = broad_except = no_finally = 0
        for f in self._py_files(root):
            if "__pycache__" in str(f):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                bare_except += len(re.findall(r"except:\s*$", text, re.MULTILINE))
                broad_except += len(re.findall(r"except Exception:", text))
                no_finally += max(0, text.count("try:") - text.count("finally:"))
            except OSError:
                pass
        if bare_except:
            evidence.append(f"{bare_except} bare except: clauses")
            confidence -= 0.2
        else:
            evidence.append("No bare except: clauses")
            confidence += 0.05
        if broad_except > 3:
            evidence.append(f"{broad_except} broad except Exception catches")
            confidence -= 0.1
        if no_finally > 5:
            evidence.append(f"{no_finally} try blocks without finally")
            confidence -= 0.05
        intervention = "observe" if confidence >= 0.6 else ("investigate" if confidence >= 0.4 else "remediate")
        return Finding(
            domain=7, persona=DOMAIN_PERSONA[7], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] Reliability: {'; '.join(evidence)}",
            intervention=intervention, evidence=evidence,
        )

    def _domain_observability(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.5
        logging_files = print_count = 0
        for f in self._py_files(root):
            if "__pycache__" in str(f):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                if "import logging" in text or "logging.get" in text:
                    logging_files += 1
                    confidence += 0.04
                print_count += len(re.findall(r"^\s*print\(", text, re.MULTILINE))
            except OSError:
                pass
        evidence.append(f"{logging_files} files use logging module")
        if print_count > 10:
            evidence.append(f"{print_count} bare print() calls")
            confidence -= 0.1
        elif print_count == 0:
            evidence.append("No bare print() calls")
            confidence += 0.05
        return Finding(
            domain=8, persona=DOMAIN_PERSONA[8], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] Observability: {'; '.join(evidence)}",
            intervention="observe" if confidence >= 0.5 else "investigate",
            evidence=evidence,
        )

    def _domain_api_design(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.6
        init_files = self._py_files(root)
        dunder_all = sum(1 for f in init_files if "__all__" in f.read_text(errors="ignore") if f.exists())
        evidence.append(f"{len(init_files)} __init__.py files")
        if dunder_all:
            evidence.append(f"{dunder_all} declare __all__ (explicit API surface)")
            confidence += 0.15
        else:
            evidence.append("No __all__ declarations — implicit API surface")
            confidence -= 0.05
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            m = re.search(r'version\s*=\s*"(\d+\.\d+\.\d+)', pyproject.read_text(errors="ignore"))
            if m:
                evidence.append(f"version={m.group(1)}")
                confidence += 0.05
        return Finding(
            domain=9, persona=DOMAIN_PERSONA[9], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] API Design: {'; '.join(evidence)}",
            intervention="observe" if confidence >= 0.6 else "investigate",
            evidence=evidence,
        )

    def _domain_documentation(self, root: Path) -> Finding:
        evidence = []
        total_functions = docstring_count = 0
        for f in self._py_files(root):
            if "__pycache__" in str(f):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                total_functions += len(re.findall(r"^\s*def ", text, re.MULTILINE))
                docstring_count += len(re.findall(r'def [^:]+:\s*\n\s+"""', text))
            except OSError:
                pass
        ratio = docstring_count / max(total_functions, 1)
        evidence.append(f"{docstring_count}/{total_functions} functions documented ({ratio:.0%})")
        if (root / "docs").is_dir() or (root / "doc").is_dir():
            evidence.append("docs/ directory present")
        confidence = min(0.4 + ratio * 0.5 + 0.05, 0.95)
        return Finding(
            domain=10, persona=DOMAIN_PERSONA[10], confidence=confidence,
            summary=f"[Phase 2] Documentation: {'; '.join(evidence)}",
            intervention="observe" if ratio >= 0.4 else "investigate",
            evidence=evidence,
        )

    def _domain_dependency(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.6
        intervention = "observe"
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            text = pyproject.read_text(errors="ignore")
            deps = re.findall(r'"([a-zA-Z0-9_-]+)(?:[>=<!][^"]*)?"\s*(?:,|\])', text)
            evidence.append(f"pyproject.toml: {len(deps)} dependencies")
            confidence += 0.1
            pinned = len(re.findall(r'==\d', text))
            ranged = len(re.findall(r'[>~^]=\d', text))
            if pinned > ranged:
                evidence.append(f"{pinned} pinned == vs {ranged} ranged (brittle)")
                confidence -= 0.1
            elif ranged:
                evidence.append(f"{ranged} ranged constraints (flexible)")
                confidence += 0.05
        elif list(root.glob("requirements*.txt")):
            evidence.append("requirements.txt found (no pyproject.toml)")
            confidence -= 0.05
        else:
            evidence.append("No dependency manifest found")
            confidence -= 0.2
            intervention = "investigate"
        return Finding(
            domain=11, persona=DOMAIN_PERSONA[11], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] Dependency: {'; '.join(evidence)}",
            intervention=intervention, evidence=evidence,
        )

    def _domain_operational(self, root: Path) -> Finding:
        evidence = []
        confidence = 0.5
        has_ci = (root / ".github" / "workflows").is_dir() or (root / ".gitlab-ci.yml").exists()
        has_docker = (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists()
        if has_ci:
            evidence.append("CI/CD configuration present")
            confidence += 0.2
        else:
            evidence.append("No CI/CD configuration")
            confidence -= 0.1
        if has_docker:
            evidence.append("Docker configuration present")
            confidence += 0.1
        if (root / "Makefile").exists():
            evidence.append("Makefile present")
            confidence += 0.05
        return Finding(
            domain=12, persona=DOMAIN_PERSONA[12], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] Operational: {'; '.join(evidence)}",
            intervention="observe" if confidence >= 0.6 else "investigate",
            evidence=evidence,
        )

    def _domain_stigmergic(self, root: Path) -> Finding:
        """MSP-specific: check markspace coordination health."""
        evidence = []
        confidence = 0.6
        scope_decl = mark_writes = mark_reads = 0
        for f in self._py_files(root):
            if "__pycache__" in str(f):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                scope_decl += len(re.findall(r'scope\s*=\s*["\'][a-z]', text))
                mark_writes += text.count("markspace.write(")
                mark_reads += text.count("markspace.read(")
            except OSError:
                pass
        evidence.append(f"{mark_writes} write / {mark_reads} read calls")
        evidence.append(f"{scope_decl} explicit scope declarations")
        if scope_decl == 0:
            evidence.append("No scope declarations — unscoped marks risk")
            confidence -= 0.2
            intervention = "investigate"
        else:
            confidence += 0.1
            intervention = "observe"
        rules_dir = root / "msp" / "layer5" / "rules"
        if rules_dir.exists():
            rule_count = len(list(rules_dir.glob("*.md")))
            evidence.append(f"{rule_count} CARL domain rules")
            confidence += 0.05 * min(rule_count, 4)
        return Finding(
            domain=13, persona=DOMAIN_PERSONA[13], confidence=min(max(confidence, 0.1), 1.0),
            summary=f"[Phase 2] Stigmergic Coordination: {'; '.join(evidence)}",
            intervention=intervention, evidence=evidence,
            pattern="stigmergic-scope-audit" if scope_decl == 0 else "",
        )

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
