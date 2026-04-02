"""PAUL: Plan-Apply-Unify loop — MSP Layer 5 orchestration core.

Plan state lives in structured files (the "nest"):
  <root>/paul/STATE.md      — current plan state
  <root>/paul/MILESTONES.md — milestone definitions
  <root>/paul/SUMMARY.md    — written on Unify

Marks emitted (the "pheromones"):
  Intent(scope="paul", resource=milestone_id)    on plan() — one per milestone
  Action(scope="paul", resource=task_id)         on apply() — one per completed task
  Observation(scope="paul", topic="plan-closed") on unify()
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from markspace import Agent, Action, Intent, MarkSpace, Observation, Source

from msp.layer5.base import WorkspaceState


@dataclass
class Milestone:
    id: str
    description: str
    acceptance_criteria: str


@dataclass
class Task:
    id: str
    milestone_id: str
    description: str
    expected_outputs: list[str] = field(default_factory=list)


@dataclass
class Plan:
    id: str
    project: str
    milestones: list[Milestone]
    tasks: list[Task] = field(default_factory=list)


@dataclass
class Result:
    plan: Plan
    completed_tasks: list[Task]
    failed_tasks: list[Task]


@dataclass
class Summary:
    plan_id: str
    completed: int
    failed: int
    notes: str = ""


@dataclass
class QualifyVerdict:
    passed: bool
    gap: str = ""


@dataclass
class TaskError:
    task: Task
    error_type: str   # "scope_creep" | "dependency_missing" | "compliance_violation" | "agent_error"
    detail: str


class PlanApplyUnify:
    """Implements the Plan → Apply → Unify orchestration loop.

    Attributes:
        project:   Project name.
        state:     WorkspaceState (BASE) for this project.
        markspace: Shared MarkSpace instance.
        agent:     Authorized Agent for writing marks.
    """

    def __init__(
        self,
        project: str,
        state: WorkspaceState,
        markspace: MarkSpace,
        agent: Agent,
    ) -> None:
        self.project = project
        self.state = state
        self.markspace = markspace
        self.agent = agent
        self._paul_dir = state.root / "paul"

    def plan(self, milestones: list[Milestone]) -> Plan:
        """Write STATE.md + MILESTONES.md and emit one Intent mark per milestone."""
        self._paul_dir.mkdir(parents=True, exist_ok=True)
        plan_id = str(uuid.uuid4())[:8]
        plan = Plan(id=plan_id, project=self.project, milestones=milestones)

        # Write STATE.md
        state_lines = [f"# Plan {plan_id}\n", f"**Project:** {self.project}\n", "**Status:** active\n\n"]
        state_lines += [f"- [ ] {m.id}: {m.description}\n" for m in milestones]
        (self._paul_dir / "STATE.md").write_text("".join(state_lines), encoding="utf-8")

        # Write MILESTONES.md
        ms_lines = [f"# Milestones — {self.project}\n\n"]
        for m in milestones:
            ms_lines += [f"## {m.id}\n", f"{m.description}\n\n", f"**AC:** {m.acceptance_criteria}\n\n"]
        (self._paul_dir / "MILESTONES.md").write_text("".join(ms_lines), encoding="utf-8")

        # Emit one Intent mark per milestone
        for milestone in milestones:
            self.markspace.write(
                self.agent,
                Intent(
                    scope="paul",
                    resource=milestone.id,
                    action=milestone.description,
                    confidence=1.0,
                ),
            )

        return plan

    def apply(self, plan: Plan, session: Any) -> Result:
        """Execute each task via the session and emit one Action mark per completion."""
        completed: list[Task] = []
        failed: list[Task] = []

        for task in plan.tasks:
            try:
                session.run(stage=task.id)
                completed.append(task)
                self.markspace.write(
                    self.agent,
                    Action(
                        scope="paul",
                        resource=task.id,
                        action=task.description,
                        result={"milestone_id": task.milestone_id},
                        failed=False,
                    ),
                )
            except Exception as exc:
                failed.append(task)
                self.markspace.write(
                    self.agent,
                    Action(
                        scope="paul",
                        resource=task.id,
                        action=task.description,
                        result={"error": str(exc)},
                        failed=True,
                    ),
                )

        return Result(plan=plan, completed_tasks=completed, failed_tasks=failed)

    def unify(self, plan: Plan, result: Result) -> Summary:
        """Reconcile planned vs completed, write SUMMARY.md, emit Observation mark."""
        summary = Summary(
            plan_id=plan.id,
            completed=len(result.completed_tasks),
            failed=len(result.failed_tasks),
            notes=f"{len(result.completed_tasks)}/{len(plan.tasks)} tasks completed",
        )

        summary_lines = [
            f"# Summary — Plan {plan.id}\n\n",
            f"**Completed:** {summary.completed}\n",
            f"**Failed:** {summary.failed}\n\n",
            f"{summary.notes}\n",
        ]
        (self._paul_dir / "SUMMARY.md").write_text("".join(summary_lines), encoding="utf-8")

        # Update BASE workspace
        workspace = self.state.load()
        workspace["last_plan_id"] = plan.id
        workspace["last_plan_completed"] = summary.completed
        self.state.save(workspace)

        # Emit closing Observation mark
        self.markspace.write(
            self.agent,
            Observation(
                scope="paul",
                topic="plan-closed",
                content={"plan_id": plan.id, "completed": summary.completed, "failed": summary.failed},
                confidence=1.0,
                source=Source.FLEET,
            ),
        )

        return summary

    def qualify(self, task: Task, result: Any) -> QualifyVerdict:
        """Check that result's observations cover all expected_outputs for the task."""
        if not task.expected_outputs:
            return QualifyVerdict(passed=True)
        observed_topics = {obs.get("topic", "") for obs in getattr(result, "observations", [])}
        missing = [o for o in task.expected_outputs if o not in observed_topics]
        if missing:
            return QualifyVerdict(passed=False, gap=f"Missing outputs: {', '.join(missing)}")
        return QualifyVerdict(passed=True)

    def route_failure(self, task: Task, error: TaskError) -> None:
        """Classify failure and emit appropriate mark."""
        from markspace import Need, Warning as MarkWarning
        if error.error_type in ("scope_creep", "dependency_missing", "compliance_violation"):
            self.markspace.write(
                self.agent,
                Need(
                    scope="paul",
                    question=f"Task '{task.id}' failed ({error.error_type}): {error.detail}",
                    context={"task_id": task.id, "error_type": error.error_type},
                    priority=0.8,
                    blocking=error.error_type == "dependency_missing",
                ),
            )
        else:
            self.markspace.write(
                self.agent,
                MarkWarning(
                    scope="paul",
                    topic="task-failure",
                    reason=f"Task '{task.id}' agent error: {error.detail}",
                ),
            )

    def enforce_scope(self, session: Any, milestone: Milestone) -> None:
        """Set the session's scope to the milestone ID to enforce absorbing barriers."""
        session.scope = f"paul.{milestone.id}"

    def run(self, milestones: list[Milestone], session: Any) -> Summary:
        """Full Plan → Apply → Unify loop."""
        plan = self.plan(milestones)
        result = self.apply(plan, session)
        return self.unify(plan, result)
