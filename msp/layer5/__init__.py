"""Layer 5: Orchestration Ecosystem.

Six modules providing macro-level project orchestration:
  base       — WorkspaceState: JSON surfaces, drift detection, PSMM
  paul       — PlanApplyUnify: Plan→Apply→Unify loop, lifecycle marks
  carl       — ContextAugmentation: intent detection → JIT rule injection
  skillsmith — CapabilityStandards: 7-file taxonomy, audit, scaffold
  seed       — ProjectGenesis: type-first ideation, PLANNING.md, PAUL handoff
  aegis      — EpistemicAudit: 12 personas × 14 domains, adversarial review
"""
from msp.layer5.base import WorkspaceState, DriftItem
from msp.layer5.paul import PlanApplyUnify, Milestone, Plan, Task, Result, Summary
from msp.layer5.carl import ContextAugmentation
from msp.layer5.skillsmith import CapabilityStandards, SkillSpec
from msp.layer5.skillsmith import AuditReport as SkillAuditReport
from msp.layer5.seed import ProjectGenesis, Ideation
from msp.layer5.aegis import EpistemicAudit, AuditScope, Finding
from msp.layer5.aegis import AuditReport as AegisAuditReport

__all__ = [
    "WorkspaceState", "DriftItem",
    "PlanApplyUnify", "Milestone", "Plan", "Task", "Result", "Summary",
    "ContextAugmentation",
    "CapabilityStandards", "SkillSpec", "SkillAuditReport",
    "ProjectGenesis", "Ideation",
    "EpistemicAudit", "AuditScope", "Finding", "AegisAuditReport",
]
