"""Model Stigmergic Protocol — Python implementation."""

__version__ = "0.1.0"

# Layer 5: Orchestration Ecosystem
from msp.layer5 import (
    WorkspaceState, DriftItem,
    PlanApplyUnify, Milestone, Plan, Task, Result, Summary,
    ContextAugmentation,
    CapabilityStandards, SkillSpec, SkillAuditReport,
    ProjectGenesis, Ideation,
    EpistemicAudit, AuditScope, Finding, AegisAuditReport,
)

__all__ = [
    # Layer 5
    "WorkspaceState", "DriftItem",
    "PlanApplyUnify", "Milestone", "Plan", "Task", "Result", "Summary",
    "ContextAugmentation",
    "CapabilityStandards", "SkillSpec", "SkillAuditReport",
    "ProjectGenesis", "Ideation",
    "EpistemicAudit", "AuditScope", "Finding", "AegisAuditReport",
]
