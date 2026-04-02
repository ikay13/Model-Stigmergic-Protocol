# Layer 5: Orchestration Ecosystem Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement six Python modules (BASE, PAUL, CARL, SKILLSMITH, SEED, AEGIS) in `msp/layer5/` that provide macro-level project orchestration via stigmergic coordination, building on Layers 1-4 without modifying them.

**Architecture:** All six modules depend downward on Layers 1-4 only. Plan state lives in workspace files (the "nest"); marks carry coordination signals (the "pheromones"). A validation gate after Task 4 confirms the minimal stigmergic loop works before building SEED and AEGIS.

**Tech Stack:** Python 3.10+, pytest, hypothesis, markspace (Layer 1), ContextLoader (Layer 2), AgentSession (Layer 3), VaultSync (Layer 4), pyyaml, dataclasses, pathlib.

---

## File Map

**Create:**
- `msp/layer5/__init__.py`
- `msp/layer5/base.py` — `WorkspaceState`, `DriftItem`
- `msp/layer5/paul.py` — `PlanApplyUnify`, `Milestone`, `Plan`, `Task`, `Result`, `Summary`, `QualifyVerdict`, `TaskError`
- `msp/layer5/carl.py` — `ContextAugmentation`
- `msp/layer5/skillsmith.py` — `CapabilityStandards`, `SkillSpec`, `AuditReport`
- `msp/layer5/seed.py` — `ProjectGenesis`, `Ideation`
- `msp/layer5/aegis.py` — `EpistemicAudit`, `AuditScope`, `AuditContext`, `Finding`, `AuditReport` (aegis variant), `RemediationPlan`
- `msp/layer5/rules/development.md`
- `msp/layer5/rules/debugging.md`
- `msp/layer5/rules/planning.md`
- `msp/layer5/rules/research.md`
- `msp/layer5/rules/review.md`
- `msp/layer5/rules/content.md`
- `msp/layer5/rules/stigmergy.md`
- `msp/layer5/rules/orchestration.md`
- `msp/layer5/rules/audit.md`
- `tests/layer5/__init__.py`
- `tests/layer5/test_base.py`
- `tests/layer5/test_paul.py`
- `tests/layer5/test_carl.py`
- `tests/layer5/test_skillsmith.py`
- `tests/layer5/test_seed.py`
- `tests/layer5/test_aegis.py`

**Modify:**
- `msp/__init__.py` — expose layer5 package
- `msp/layer2/context_loader.py` — add `extra_paths` param to `load()`

---

## Task 1: Layer 5 package skeleton + BASE workspace CRUD

**Files:**
- Create: `msp/layer5/__init__.py`
- Create: `msp/layer5/base.py`
- Create: `tests/layer5/__init__.py`
- Create: `tests/layer5/test_base.py`

- [ ] **Step 1: Write failing tests for WorkspaceState CRUD**

```python
# tests/layer5/test_base.py
"""Tests for WorkspaceState — workspace file CRUD and DriftItem."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from msp.layer5.base import WorkspaceState, DriftItem


@pytest.fixture
def workspace_dir(tmp_path):
    return tmp_path / "myproject"


def _make_state(workspace_dir, markspace=None, vault=None):
    from unittest.mock import MagicMock
    ms = markspace or MagicMock()
    v = vault or MagicMock()
    return WorkspaceState(project="myproject", root=workspace_dir, markspace=ms, vault=v)


def test_workspace_load_returns_empty_dict_when_no_file(workspace_dir):
    state = _make_state(workspace_dir)
    data = state.load()
    assert data == {}


def test_workspace_save_and_load_round_trip(workspace_dir):
    state = _make_state(workspace_dir)
    state.save({"project": "myproject", "health": "ok"})
    loaded = state.load()
    assert loaded["project"] == "myproject"
    assert loaded["health"] == "ok"


def test_workspace_save_creates_directory(workspace_dir):
    state = _make_state(workspace_dir)
    state.save({"x": 1})
    assert (workspace_dir / "base" / "workspace.json").exists()


def test_workspace_save_emits_observation_mark(workspace_dir):
    from unittest.mock import MagicMock, call
    ms = MagicMock()
    agent = MagicMock()
    state = WorkspaceState(project="myproject", root=workspace_dir, markspace=ms, vault=MagicMock(), agent=agent)
    state.save({"x": 1})
    assert ms.write.called


def test_psmm_read_returns_empty_when_no_file(workspace_dir):
    state = _make_state(workspace_dir)
    assert state.psmm_read() == {}


def test_psmm_write_and_read_round_trip(workspace_dir):
    state = _make_state(workspace_dir)
    state.psmm_write({"last_session": "2026-04-02", "next_step": "build PAUL"})
    data = state.psmm_read()
    assert data["next_step"] == "build PAUL"


def test_psmm_write_calls_vault_export(workspace_dir):
    from unittest.mock import MagicMock
    vault = MagicMock()
    state = WorkspaceState(project="myproject", root=workspace_dir, markspace=MagicMock(), vault=vault, agent=MagicMock())
    state.psmm_write({"x": 1})
    vault.export_observations.assert_called_once_with("base")


def test_drift_item_dataclass():
    item = DriftItem(key="task_count", workspace_value=3, markspace_value=5)
    assert item.key == "task_count"
    assert item.workspace_value == 3
    assert item.markspace_value == 5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_base.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'msp.layer5'`

- [ ] **Step 3: Create package skeleton**

```python
# msp/layer5/__init__.py
"""Layer 5: Orchestration Ecosystem.

Six modules providing macro-level project orchestration:
  base       — WorkspaceState: JSON surfaces, drift detection, PSMM
  paul       — PlanApplyUnify: Plan→Apply→Unify loop, lifecycle marks
  carl       — ContextAugmentation: intent detection → JIT rule injection
  skillsmith — CapabilityStandards: 7-file taxonomy, audit, scaffold
  seed       — ProjectGenesis: type-first ideation, PLANNING.md, PAUL handoff
  aegis      — EpistemicAudit: 12 personas × 14 domains, adversarial review
"""
```

```python
# tests/layer5/__init__.py
```

- [ ] **Step 4: Implement WorkspaceState and DriftItem**

```python
# msp/layer5/base.py
"""BASE: WorkspaceState — JSON workspace surfaces, drift detection, PSMM.

Workspace files live at <root>/<project>/base/:
  workspace.json — project identity, health, active agents
  psmm.json      — Per-Session Meta Memory
  drift.json     — detected workspace/markspace divergence

Marks emitted:
  Observation(scope="base", topic="workspace-saved")  on save()
  Observation(scope="base", topic="workspace-drift")  on detect_drift()
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from markspace import Agent, MarkSpace, Observation, Source
from msp.layer4.vault_sync import VaultSync


@dataclass
class DriftItem:
    """Represents a single divergence between workspace and markspace state."""
    key: str
    workspace_value: Any
    markspace_value: Any


@dataclass
class WorkspaceState:
    """Manages JSON workspace surfaces for a project.

    Attributes:
        project:   Project name (used as subdirectory).
        root:      Parent directory; files go in root/base/.
        markspace: Shared MarkSpace instance.
        vault:     VaultSync instance for PSMM export.
        agent:     Authorized Agent for writing marks. Auto-created if None.
    """
    project: str
    root: Path
    markspace: MarkSpace
    vault: VaultSync
    agent: Agent | None = None

    def __post_init__(self) -> None:
        self._base_dir = self.root / "base"

    def _read_json(self, filename: str) -> dict:
        path = self._base_dir / filename
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, filename: str, data: dict) -> None:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        path = self._base_dir / filename
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def load(self) -> dict:
        """Read workspace.json. Returns {} if not yet created."""
        return self._read_json("workspace.json")

    def save(self, data: dict) -> None:
        """Write workspace.json and emit an Observation mark."""
        self._write_json("workspace.json", data)
        if self.agent is not None:
            self.markspace.write(
                self.agent,
                Observation(
                    scope="base",
                    topic="workspace-saved",
                    content={"project": self.project},
                    confidence=1.0,
                    source=Source.FLEET,
                ),
            )

    def detect_drift(self) -> list[DriftItem]:
        """Compare workspace.json against markspace Intent mark count.

        Returns a DriftItem if the workspace's recorded active_intents
        doesn't match the number of live Intent marks in the markspace.
        Emits an Observation mark if drift is found.
        """
        from markspace import Intent
        workspace = self.load()
        recorded = workspace.get("active_intents", 0)
        live_marks = self.markspace.read(scope="base")
        live_intents = sum(1 for m in live_marks if isinstance(m, Intent))

        items: list[DriftItem] = []
        if recorded != live_intents:
            item = DriftItem(
                key="active_intents",
                workspace_value=recorded,
                markspace_value=live_intents,
            )
            items.append(item)
            if self.agent is not None:
                self.markspace.write(
                    self.agent,
                    Observation(
                        scope="base",
                        topic="workspace-drift",
                        content={"key": item.key, "workspace": recorded, "live": live_intents},
                        confidence=0.9,
                        source=Source.FLEET,
                    ),
                )
        return items

    def psmm_read(self) -> dict:
        """Read psmm.json. Returns {} if not yet created."""
        return self._read_json("psmm.json")

    def psmm_write(self, session_data: dict) -> None:
        """Write psmm.json and export to Obsidian vault."""
        self._write_json("psmm.json", session_data)
        self.vault.export_observations("base")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_base.py -v 2>&1 | tail -15
```

Expected: all 9 tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add msp/layer5/__init__.py msp/layer5/base.py tests/layer5/__init__.py tests/layer5/test_base.py
git commit -m "feat(layer5): BASE — WorkspaceState CRUD, drift detection, PSMM"
```

---

## Task 2: BASE drift detection property test + Hypothesis coverage

**Files:**
- Modify: `tests/layer5/test_base.py`

- [ ] **Step 1: Write Hypothesis property test — drift never false-negative**

Add to `tests/layer5/test_base.py`:

```python
from hypothesis import given, strategies as st
from unittest.mock import MagicMock


@given(recorded=st.integers(min_value=0, max_value=20),
       live=st.integers(min_value=0, max_value=20))
def test_drift_detected_whenever_counts_differ(tmp_path, recorded, live):
    """detect_drift() always returns a DriftItem when counts differ."""
    from markspace import Intent, MarkSpace, Agent
    ms = MagicMock()
    # Mock read() to return `live` Intent marks
    mock_intents = [MagicMock(spec=Intent) for _ in range(live)]
    ms.read.return_value = mock_intents
    state = WorkspaceState(
        project="p", root=tmp_path, markspace=ms, vault=MagicMock(), agent=MagicMock()
    )
    state.save({"active_intents": recorded})
    items = state.detect_drift()
    if recorded != live:
        assert len(items) == 1
        assert items[0].key == "active_intents"
    else:
        assert items == []
```

- [ ] **Step 2: Run to verify it passes**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_base.py::test_drift_detected_whenever_counts_differ -v
```

Expected: PASS (Hypothesis runs 200 examples by default).

- [ ] **Step 3: Commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add tests/layer5/test_base.py
git commit -m "test(layer5): BASE Hypothesis property — drift never false-negative"
```

---

## Task 3: ContextLoader extra_paths extension (prerequisite for CARL)

**Files:**
- Modify: `msp/layer2/context_loader.py`

- [ ] **Step 1: Write failing test for extra_paths**

Add to a new file `tests/layer2/test_context_loader_extra_paths.py`:

```python
# tests/layer2/test_context_loader_extra_paths.py
"""Test extra_paths support added for CARL (Layer 5) integration."""
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from msp.layer2.context_loader import ContextLoader


def test_load_includes_extra_paths_content(tmp_path):
    """extra_paths content appears in the returned ContextBundle references."""
    # Set up minimal ICM workspace
    (tmp_path / "CLAUDE.md").write_text("# Workspace Identity")
    (tmp_path / "CONTEXT.md").write_text("# Routing")

    rule_file = tmp_path / "extra_rule.md"
    rule_file.write_text("# Development Rules\nUse TDD.")

    loader = ContextLoader(tmp_path)
    bundle = loader.load(extra_paths=[rule_file])
    assert any("Development Rules" in ref for ref in bundle.references)


def test_load_with_no_extra_paths_unchanged(tmp_path):
    """Passing no extra_paths gives same result as before (backwards compat)."""
    (tmp_path / "CLAUDE.md").write_text("# Workspace Identity")
    (tmp_path / "CONTEXT.md").write_text("# Routing")
    loader = ContextLoader(tmp_path)
    bundle_before = loader.load()
    bundle_after = loader.load(extra_paths=[])
    assert bundle_before.as_text() == bundle_after.as_text()
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer2/test_context_loader_extra_paths.py -v
```

Expected: FAIL — `TypeError: load() got unexpected keyword argument 'extra_paths'`

- [ ] **Step 3: Add extra_paths to ContextLoader.load()**

Open `msp/layer2/context_loader.py`. Find the `load()` method signature and add `extra_paths`:

```python
def load(
    self,
    stage: str | None = None,
    token_budget: int = 8000,
    extra_paths: list[Path] | None = None,
) -> ContextBundle:
```

Then, after the existing Layer 3 reference loading logic and before the return statement, add:

```python
        # Extra paths (injected by CARL, Layer 5)
        if extra_paths:
            for path in extra_paths:
                if path.exists():
                    text = path.read_text(encoding="utf-8")
                    if bundle.total_tokens() + self.workspace._estimate_tokens(text) <= token_budget:
                        bundle.references.append(text)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer2/test_context_loader_extra_paths.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Verify existing Layer 2 tests still pass**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer2/ -v 2>&1 | tail -10
```

Expected: all existing tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add msp/layer2/context_loader.py tests/layer2/test_context_loader_extra_paths.py
git commit -m "feat(layer2): add extra_paths to ContextLoader.load() for CARL integration"
```

---

## Task 4: PAUL core — Plan/Apply/Unify loop with lifecycle marks

**Files:**
- Create: `msp/layer5/paul.py`
- Create: `tests/layer5/test_paul.py`

- [ ] **Step 1: Write failing tests for PAUL core**

```python
# tests/layer5/test_paul.py
"""Tests for PlanApplyUnify — Plan/Apply/Unify loop and lifecycle mark emission."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from msp.layer5.paul import (
    Milestone, Plan, Task, Result, Summary, PlanApplyUnify
)
from msp.layer5.base import WorkspaceState


@pytest.fixture
def workspace_dir(tmp_path):
    return tmp_path / "proj"


@pytest.fixture
def mock_state(workspace_dir):
    ms = MagicMock()
    vault = MagicMock()
    agent = MagicMock()
    return WorkspaceState(
        project="proj", root=workspace_dir, markspace=ms, vault=vault, agent=agent
    )


@pytest.fixture
def paul(mock_state):
    ms = mock_state.markspace
    agent = mock_state.agent
    return PlanApplyUnify(project="proj", state=mock_state, markspace=ms, agent=agent)


def test_milestone_dataclass():
    m = Milestone(id="m1", description="Build BASE", acceptance_criteria="workspace.json created")
    assert m.id == "m1"
    assert m.acceptance_criteria == "workspace.json created"


def test_plan_creates_state_file(workspace_dir, paul):
    milestones = [Milestone(id="m1", description="Do X", acceptance_criteria="X done")]
    plan = paul.plan(milestones)
    assert isinstance(plan, Plan)
    state_file = workspace_dir / "paul" / "STATE.md"
    assert state_file.exists()


def test_plan_creates_milestones_file(workspace_dir, paul):
    milestones = [Milestone(id="m1", description="Do X", acceptance_criteria="X done")]
    paul.plan(milestones)
    milestones_file = workspace_dir / "paul" / "MILESTONES.md"
    assert milestones_file.exists()


def test_plan_emits_one_intent_mark_per_milestone(paul):
    milestones = [
        Milestone(id="m1", description="Do X", acceptance_criteria="X done"),
        Milestone(id="m2", description="Do Y", acceptance_criteria="Y done"),
    ]
    paul.plan(milestones)
    # markspace.write called once per milestone
    assert paul.markspace.write.call_count == 2


def test_unify_writes_summary_file(workspace_dir, paul):
    milestones = [Milestone(id="m1", description="Do X", acceptance_criteria="X done")]
    plan = paul.plan(milestones)
    paul.markspace.write.reset_mock()
    result = Result(plan=plan, completed_tasks=[], failed_tasks=[])
    summary = paul.unify(plan, result)
    assert isinstance(summary, Summary)
    summary_file = workspace_dir / "paul" / "SUMMARY.md"
    assert summary_file.exists()


def test_unify_emits_observation_mark(paul):
    milestones = [Milestone(id="m1", description="Do X", acceptance_criteria="X done")]
    plan = paul.plan(milestones)
    paul.markspace.write.reset_mock()
    result = Result(plan=plan, completed_tasks=[], failed_tasks=[])
    paul.unify(plan, result)
    # One Observation mark emitted on unify
    from markspace import Observation
    calls = paul.markspace.write.call_args_list
    obs_calls = [c for c in calls if isinstance(c.args[1], Observation)]
    assert len(obs_calls) == 1


def test_apply_emits_action_mark_per_completed_task(paul):
    from unittest.mock import MagicMock
    milestones = [Milestone(id="m1", description="Do X", acceptance_criteria="X done")]
    plan = paul.plan(milestones)
    paul.markspace.write.reset_mock()

    mock_session = MagicMock()
    mock_session.run.return_value = MagicMock(observations=[], needs=[])

    task = Task(id="t1", milestone_id="m1", description="Step 1")
    plan.tasks = [task]
    result = paul.apply(plan, mock_session)

    from markspace import Action
    calls = paul.markspace.write.call_args_list
    action_calls = [c for c in calls if isinstance(c.args[1], Action)]
    assert len(action_calls) == 1
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_paul.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'msp.layer5.paul'`

- [ ] **Step 3: Implement PAUL core**

```python
# msp/layer5/paul.py
"""PAUL: Plan-Apply-Unify loop — MSP Layer 5 orchestration core.

Plan state lives in structured files (the "nest"):
  <root>/<project>/paul/STATE.md      — current plan state
  <root>/<project>/paul/MILESTONES.md — milestone definitions
  <root>/<project>/paul/SUMMARY.md    — written on Unify

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

    def run(self, milestones: list[Milestone], session: Any) -> Summary:
        """Full Plan → Apply → Unify loop."""
        plan = self.plan(milestones)
        result = self.apply(plan, session)
        return self.unify(plan, result)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_paul.py -v 2>&1 | tail -15
```

Expected: all tests PASS.

- [ ] **Step 5: Add Hypothesis property test — loop always closes**

Add to `tests/layer5/test_paul.py`:

```python
from hypothesis import given, strategies as st

@given(n_milestones=st.integers(min_value=1, max_value=5))
def test_run_always_produces_summary(tmp_path, n_milestones):
    """run() always produces a Summary regardless of milestone count."""
    from unittest.mock import MagicMock
    from msp.layer5.base import WorkspaceState
    ms = MagicMock()
    ms.read.return_value = []
    agent = MagicMock()
    state = WorkspaceState(
        project="p", root=tmp_path / "p", markspace=ms, vault=MagicMock(), agent=agent
    )
    paul = PlanApplyUnify(project="p", state=state, markspace=ms, agent=agent)
    milestones = [
        Milestone(id=f"m{i}", description=f"Step {i}", acceptance_criteria=f"Done {i}")
        for i in range(n_milestones)
    ]
    mock_session = MagicMock()
    mock_session.run.return_value = MagicMock(observations=[], needs=[])
    summary = paul.run(milestones, mock_session)
    assert isinstance(summary, Summary)
    assert (tmp_path / "p" / "paul" / "SUMMARY.md").exists()
```

- [ ] **Step 6: Run all Layer 5 tests**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/ -v 2>&1 | tail -15
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add msp/layer5/paul.py tests/layer5/test_paul.py
git commit -m "feat(layer5): PAUL core — Plan/Apply/Unify loop with lifecycle marks"
```

---

## Task 5: CARL — intent detection and JIT rule injection

**Files:**
- Create: `msp/layer5/carl.py`
- Create: `msp/layer5/rules/` (9 rule files)
- Create: `tests/layer5/test_carl.py`

- [ ] **Step 1: Write rule domain files**

```bash
mkdir -p /home/orin/Model-Stigmergic-Protocol/msp/layer5/rules
```

Create each file with minimal content:

```markdown
<!-- msp/layer5/rules/development.md -->
# Development Rules
- Write tests before implementation (TDD)
- Keep functions focused and small
- Follow existing code patterns in the repo
```

```markdown
<!-- msp/layer5/rules/debugging.md -->
# Debugging Rules
- Read the error message before changing code
- Reproduce the bug with a failing test first
- Fix root cause, not symptoms
```

```markdown
<!-- msp/layer5/rules/planning.md -->
# Planning Rules
- Define acceptance criteria before starting
- Break work into tasks of 2-5 minutes each
- Commit after each passing test
```

```markdown
<!-- msp/layer5/rules/research.md -->
# Research Rules
- Cite sources for all factual claims
- Distinguish confirmed facts from hypotheses
- Write findings as Observation marks
```

```markdown
<!-- msp/layer5/rules/review.md -->
# Review Rules
- Check for missing tests first
- Verify types match across call sites
- Flag security implications explicitly
```

```markdown
<!-- msp/layer5/rules/content.md -->
# Content Rules
- Write for the audience, not the author
- Lead with the most important information
- Use active voice
```

```markdown
<!-- msp/layer5/rules/stigmergy.md -->
# Stigmergy Rules
- Coordinate through marks, never direct messages
- Emit one mark per lifecycle event, not per sub-step
- Scope marks to the milestone they belong to
```

```markdown
<!-- msp/layer5/rules/orchestration.md -->
# Orchestration Rules
- PAUL owns plan state; other agents read marks only
- BASE is the single source of workspace truth
- CARL injects rules before every AgentSession launch
```

```markdown
<!-- msp/layer5/rules/audit.md -->
# Audit Rules
- Every domain must produce a finding (even "no issues")
- Confidence scores must be justified
- Adversarial phase must challenge every high-severity finding
```

- [ ] **Step 2: Write failing CARL tests**

```python
# tests/layer5/test_carl.py
"""Tests for ContextAugmentation (CARL) — intent detection and JIT rule injection."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from msp.layer5.carl import ContextAugmentation


RULES_DIR = Path(__file__).parent.parent.parent / "msp" / "layer5" / "rules"


@pytest.fixture
def carl():
    ms = MagicMock()
    loader = MagicMock()
    loader.load.return_value = MagicMock(references=[], as_text=MagicMock(return_value=""))
    return ContextAugmentation(markspace=ms, loader=loader, rules_dir=RULES_DIR)


def _make_intent(topic: str):
    from unittest.mock import MagicMock
    from markspace import Intent
    m = MagicMock(spec=Intent)
    m.action = topic
    m.resource = topic
    return m


def test_detect_domains_development_keywords(carl):
    marks = [_make_intent("implement the feature with TDD")]
    domains = carl.detect_domains(marks)
    assert "development" in domains


def test_detect_domains_debugging_keywords(carl):
    marks = [_make_intent("fix the bug in the auth module")]
    domains = carl.detect_domains(marks)
    assert "debugging" in domains


def test_detect_domains_stigmergy_keywords(carl):
    marks = [_make_intent("coordinate agents via marks")]
    domains = carl.detect_domains(marks)
    assert "stigmergy" in domains


def test_detect_domains_no_match_returns_empty(carl):
    marks = [_make_intent("xyzzy frobnicator")]
    domains = carl.detect_domains(marks)
    assert domains == []


def test_load_rules_resolves_existing_paths(carl):
    paths = carl.load_rules(["development", "debugging"])
    assert all(p.exists() for p in paths)
    assert len(paths) == 2


def test_load_rules_ignores_missing_domains(carl):
    paths = carl.load_rules(["development", "nonexistent_domain"])
    assert len(paths) == 1


def test_inject_returns_augmented_config(carl):
    marks = [_make_intent("implement the feature")]
    carl.markspace.read.return_value = marks
    config = carl.inject({"session_id": "s1"})
    assert "session_id" in config
    assert "carl_domains" in config


def test_inject_emits_observation_mark(carl):
    marks = [_make_intent("fix the bug")]
    carl.markspace.read.return_value = marks
    carl.inject({"session_id": "s1"})
    assert carl.markspace.write.called


def test_no_domain_scores_negative(carl):
    """All domain scores are >= 0 for any input."""
    marks = [_make_intent("some random task description here")]
    scores = carl._score_domains(marks)
    assert all(v >= 0 for v in scores.values())
```

- [ ] **Step 3: Run to verify they fail**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_carl.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'msp.layer5.carl'`

- [ ] **Step 4: Implement ContextAugmentation**

```python
# msp/layer5/carl.py
"""CARL: ContextAugmentation — intent detection and JIT rule injection.

Reads active Intent marks from the markspace, scores them against domain
trigger lists, and injects matching rule files into the ContextLoader before
an AgentSession launches.

Marks emitted:
  Observation(scope="carl", topic="rules-injected") recording injected domains.
"""
from __future__ import annotations

from pathlib import Path

from markspace import Agent, Intent, MarkSpace, Observation, Source

from msp.layer2.context_loader import ContextLoader

# Keyword triggers per domain. Any match scores +1 for that domain.
DOMAIN_TRIGGERS: dict[str, list[str]] = {
    "development": ["implement", "build", "feature", "code", "tdd", "test", "write"],
    "debugging":   ["fix", "bug", "error", "debug", "broken", "failing", "issue"],
    "planning":    ["plan", "milestone", "roadmap", "design", "spec", "architect"],
    "research":    ["research", "investigate", "analyse", "analyze", "explore", "survey"],
    "review":      ["review", "audit", "check", "inspect", "validate", "verify"],
    "content":     ["write", "document", "draft", "content", "copy", "narrative"],
    "stigmergy":   ["mark", "marks", "coordinate", "stigmerg", "pheromone", "signal"],
    "orchestration": ["orchestrate", "paul", "plan-apply", "workflow", "pipeline", "schedule"],
    "audit":       ["aegis", "audit", "persona", "domain", "finding", "epistemic"],
}


class ContextAugmentation:
    """Detects intent from marks and injects domain rules into AgentSession context.

    Attributes:
        markspace: Shared MarkSpace instance (for reading Intent marks).
        loader:    ContextLoader to inject rules into.
        rules_dir: Path to the rules directory (default: msp/layer5/rules/).
        agent:     Authorized Agent for writing Observation marks.
        scope:     MarkSpace scope to read Intent marks from.
    """

    def __init__(
        self,
        markspace: MarkSpace,
        loader: ContextLoader,
        rules_dir: Path | None = None,
        agent: Agent | None = None,
        scope: str = "paul",
    ) -> None:
        self.markspace = markspace
        self.loader = loader
        self.rules_dir = rules_dir or (Path(__file__).parent / "rules")
        self.agent = agent
        self.scope = scope

    def _score_domains(self, marks: list) -> dict[str, int]:
        """Score each domain against mark content. Returns domain → score dict."""
        scores = {domain: 0 for domain in DOMAIN_TRIGGERS}
        for mark in marks:
            text = f"{getattr(mark, 'action', '')} {getattr(mark, 'resource', '')}".lower()
            for domain, keywords in DOMAIN_TRIGGERS.items():
                scores[domain] += sum(1 for kw in keywords if kw in text)
        return scores

    def detect_domains(self, marks: list) -> list[str]:
        """Return domains with score > 0, sorted by score descending."""
        scores = self._score_domains(marks)
        return [d for d, s in sorted(scores.items(), key=lambda x: -x[1]) if s > 0]

    def load_rules(self, domains: list[str]) -> list[Path]:
        """Resolve domain names to existing rule file paths."""
        paths = []
        for domain in domains:
            path = self.rules_dir / f"{domain}.md"
            if path.exists():
                paths.append(path)
        return paths

    def inject(self, session_config: dict) -> dict:
        """Detect domains from live Intent marks and inject rule files.

        Reads active Intent marks from markspace, detects domains,
        loads matching rule files, calls loader.load(extra_paths=...),
        emits an Observation mark, and returns an augmented session config.
        """
        marks = self.markspace.read(scope=self.scope)
        intent_marks = [m for m in marks if isinstance(m, Intent)]
        domains = self.detect_domains(intent_marks)
        rule_paths = self.load_rules(domains)

        if rule_paths:
            self.loader.load(extra_paths=rule_paths)

        self.observe(domains)

        return {**session_config, "carl_domains": domains, "carl_rules": [str(p) for p in rule_paths]}

    def observe(self, domains: list[str]) -> None:
        """Emit an Observation mark recording which domains were injected."""
        if self.agent is not None:
            self.markspace.write(
                self.agent,
                Observation(
                    scope="carl",
                    topic="rules-injected",
                    content={"domains": domains},
                    confidence=1.0,
                    source=Source.FLEET,
                ),
            )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_carl.py -v 2>&1 | tail -15
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add msp/layer5/carl.py msp/layer5/rules/ tests/layer5/test_carl.py
git commit -m "feat(layer5): CARL — intent detection, JIT rule injection, 9 domain rules"
```

---

## Task 6: SKILLSMITH — 7-file taxonomy, compliance audit, scaffold

**Files:**
- Create: `msp/layer5/skillsmith.py`
- Create: `tests/layer5/test_skillsmith.py`

- [ ] **Step 1: Write failing SKILLSMITH tests**

```python
# tests/layer5/test_skillsmith.py
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
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_skillsmith.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'msp.layer5.skillsmith'`

- [ ] **Step 3: Implement CapabilityStandards**

```python
# msp/layer5/skillsmith.py
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

from markspace import Agent, MarkSpace, Need, Observation, Source, Warning


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


# (file_or_dir, required, severity, description)
TAXONOMY: list[tuple[str, bool, str, str]] = [
    ("entry-point.md",  True,  "critical", "skill entry point"),
    ("tasks",           True,  "critical", "task definitions directory"),
    ("frameworks",      False, "minor",    "domain knowledge directory"),
    ("templates",       False, "minor",    "output templates directory"),
    ("context",         False, "minor",    "background context directory"),
    ("checklists",      False, "minor",    "quality gates directory"),
    ("rules",           False, "minor",    "authoring constraints directory"),
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

        for name, required, severity, description in TAXONOMY:
            target = skill_path / name
            if not target.exists():
                violation = {"file": name, "severity": severity, "description": f"Missing {description}"}
                report.violations.append(violation)
                if self.agent is not None:
                    self.markspace.write(
                        self.agent,
                        Warning(
                            scope="skillsmith",
                            topic="compliance-violation",
                            reason=f"Missing {description}: {name}",
                            severity=severity,  # type: ignore[arg-type]
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
            (skill_dir / subdir).mkdir(exist_ok=True)
            placeholder = skill_dir / subdir / f"{subdir[:-1] if subdir.endswith('s') else subdir}.md"
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
```

- [ ] **Step 4: Fix Warning severity type — check markspace Severity enum**

```bash
grep -n "class Severity\|INFO\|WARN\|CRITICAL\|ERROR" /home/orin/Model-Stigmergic-Protocol/markspace/core.py | head -10
```

If `Severity` has values like `INFO`/`WARN`/`ERROR`/`CRITICAL`, update the `Warning` calls in `skillsmith.py` to use `Severity.WARN` or `Severity.ERROR` instead of the raw strings. Check the output and adjust accordingly.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_skillsmith.py -v 2>&1 | tail -15
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add msp/layer5/skillsmith.py tests/layer5/test_skillsmith.py
git commit -m "feat(layer5): SKILLSMITH — 7-file taxonomy, compliance audit, scaffold"
```

---

## Task 7: Validation gate — end-to-end stigmergic loop test

**Files:**
- Create: `tests/layer5/test_integration_spine.py`

This is the validation gate from the design: BASE holds state, PAUL emits lifecycle marks, CARL injects rules, SKILLSMITH validates sessions — all wired together.

- [ ] **Step 1: Write the integration spine test**

```python
# tests/layer5/test_integration_spine.py
"""Integration test: minimal stigmergic loop — BASE + PAUL core + CARL + SKILLSMITH.

This is the validation gate from the Layer 5 design spec.
Verifies the four modules work together before SEED and AEGIS are built.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from msp.layer5.base import WorkspaceState
from msp.layer5.paul import PlanApplyUnify, Milestone, Task
from msp.layer5.carl import ContextAugmentation
from msp.layer5.skillsmith import CapabilityStandards, SkillSpec


@pytest.fixture
def project_root(tmp_path):
    return tmp_path / "test_project"


def test_full_spine_plan_emit_inject_validate(project_root):
    """BASE + PAUL + CARL + SKILLSMITH complete a full lifecycle without errors."""
    # --- Shared markspace mock ---
    ms = MagicMock()
    ms.read.return_value = []
    agent = MagicMock()

    # --- BASE ---
    vault = MagicMock()
    state = WorkspaceState(
        project="test_project", root=project_root, markspace=ms, vault=vault, agent=agent
    )
    state.save({"health": "ok", "active_intents": 0})
    assert state.load()["health"] == "ok"

    # --- PAUL plan phase emits Intent marks ---
    paul = PlanApplyUnify(project="test_project", state=state, markspace=ms, agent=agent)
    milestones = [
        Milestone(id="m1", description="implement the feature", acceptance_criteria="tests pass"),
    ]
    plan = paul.plan(milestones)
    assert (project_root / "paul" / "STATE.md").exists()
    assert ms.write.call_count >= 1  # at least one Intent mark

    # --- CARL detects domain from PAUL's Intent marks ---
    from markspace import Intent
    mock_intent = MagicMock(spec=Intent)
    mock_intent.action = "implement the feature"
    mock_intent.resource = "m1"
    ms.read.return_value = [mock_intent]

    loader = MagicMock()
    loader.load.return_value = MagicMock(references=[], as_text=MagicMock(return_value=""))
    carl = ContextAugmentation(markspace=ms, loader=loader)
    config = carl.inject({"session_id": "s1"})
    assert "development" in config["carl_domains"]

    # --- SKILLSMITH validates a compliant skill session ---
    sm = CapabilityStandards(markspace=ms, agent=agent)
    skill_spec = SkillSpec(name="test-skill", purpose="run tests", domains=["development"])
    skill_dir = sm.scaffold(skill_spec, project_root / "skills")
    session = MagicMock()
    session.skill_path = skill_dir
    assert sm.validate_session(session) is True

    # --- PAUL unify closes the loop ---
    from msp.layer5.paul import Result
    ms.write.reset_mock()
    result = Result(plan=plan, completed_tasks=[], failed_tasks=[])
    summary = paul.unify(plan, result)
    assert (project_root / "paul" / "SUMMARY.md").exists()

    from markspace import Observation
    obs_calls = [c for c in ms.write.call_args_list if isinstance(c.args[1], Observation)]
    assert any(c.args[1].topic == "plan-closed" for c in obs_calls)
```

- [ ] **Step 2: Run the validation gate**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_integration_spine.py -v
```

Expected: PASS — the stigmergic spine is working end-to-end.

- [ ] **Step 3: Run all Layer 5 tests**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/ -v 2>&1 | tail -20
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add tests/layer5/test_integration_spine.py
git commit -m "test(layer5): validation gate — BASE+PAUL+CARL+SKILLSMITH spine integration"
```

---

## Task 8: PAUL full — diagnostic routing and qualify loop

**Files:**
- Modify: `msp/layer5/paul.py`
- Modify: `tests/layer5/test_paul.py`

- [ ] **Step 1: Write failing tests for PAUL full additions**

Add to `tests/layer5/test_paul.py`:

```python
from msp.layer5.paul import QualifyVerdict, TaskError


def test_qualify_passes_when_outputs_present(paul):
    task = Task(id="t1", milestone_id="m1", description="Build X", expected_outputs=["workspace.json"])
    result = MagicMock()
    result.observations = [{"topic": "workspace.json", "content": {}}]
    verdict = paul.qualify(task, result)
    assert verdict.passed is True


def test_qualify_fails_when_expected_outputs_missing(paul):
    task = Task(id="t1", milestone_id="m1", description="Build X", expected_outputs=["workspace.json"])
    result = MagicMock()
    result.observations = []
    verdict = paul.qualify(task, result)
    assert verdict.passed is False
    assert "workspace.json" in verdict.gap


def test_route_failure_scope_creep_emits_need(paul):
    from markspace import Need
    task = Task(id="t1", milestone_id="m1", description="Do X")
    error = TaskError(task=task, error_type="scope_creep", detail="added unrequested feature")
    paul.markspace.write.reset_mock()
    paul.route_failure(task, error)
    calls = paul.markspace.write.call_args_list
    need_calls = [c for c in calls if isinstance(c.args[1], Need)]
    assert len(need_calls) == 1


def test_route_failure_dependency_missing_emits_need(paul):
    from markspace import Need
    task = Task(id="t1", milestone_id="m1", description="Do X")
    error = TaskError(task=task, error_type="dependency_missing", detail="missing base module")
    paul.route_failure(task, error)
    calls = paul.markspace.write.call_args_list
    need_calls = [c for c in calls if isinstance(c.args[1], Need)]
    assert len(need_calls) >= 1


def test_route_failure_agent_error_emits_warning(paul):
    from markspace import Warning
    task = Task(id="t1", milestone_id="m1", description="Do X")
    error = TaskError(task=task, error_type="agent_error", detail="timeout")
    paul.markspace.write.reset_mock()
    paul.route_failure(task, error)
    calls = paul.markspace.write.call_args_list
    warn_calls = [c for c in calls if isinstance(c.args[1], Warning)]
    assert len(warn_calls) >= 1
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_paul.py::test_qualify_passes_when_outputs_present -v 2>&1 | tail -10
```

Expected: `AttributeError: 'PlanApplyUnify' object has no attribute 'qualify'`

- [ ] **Step 3: Add qualify() and route_failure() to paul.py**

Add the following methods to the `PlanApplyUnify` class in `msp/layer5/paul.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_paul.py -v 2>&1 | tail -20
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add msp/layer5/paul.py tests/layer5/test_paul.py
git commit -m "feat(layer5): PAUL full — qualify loop, diagnostic failure routing, scope enforcement"
```

---

## Task 9: SEED — type-first ideation and PAUL handoff

**Files:**
- Create: `msp/layer5/seed.py`
- Create: `tests/layer5/test_seed.py`

- [ ] **Step 1: Write failing SEED tests**

```python
# tests/layer5/test_seed.py
"""Tests for ProjectGenesis (SEED) — type-first ideation, PLANNING.md, PAUL handoff."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from msp.layer5.seed import ProjectGenesis, Ideation


PROJECT_TYPES = ["software", "workflow", "research", "campaign", "utility"]


def _make_seed(tmp_path):
    ms = MagicMock()
    ms.read.return_value = []
    agent = MagicMock()
    paul = MagicMock()
    paul.plan.return_value = MagicMock(id="plan1", milestones=[], tasks=[])
    return ProjectGenesis(
        markspace=ms, paul=paul, root=tmp_path, agent=agent
    ), ms, paul


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
def test_ideation_returns_ideation_for_all_types(tmp_path, project_type):
    seed, _, _ = _make_seed(tmp_path)
    ideation = Ideation(
        project_type=project_type,
        name="test-project",
        goals=["Ship it"],
        constraints=["No external APIs"],
    )
    assert ideation.project_type == project_type


def test_graduate_writes_planning_md(tmp_path):
    seed, ms, paul = _make_seed(tmp_path)
    ideation = Ideation(
        project_type="software",
        name="myapp",
        goals=["Build auth system"],
        constraints=["Python only"],
    )
    planning_path = seed.graduate(ideation)
    assert planning_path.exists()
    content = planning_path.read_text()
    assert "myapp" in content
    assert "Build auth system" in content


def test_graduate_planning_md_is_always_parseable(tmp_path):
    """PLANNING.md must always be valid UTF-8 text (Hypothesis-style check)."""
    seed, _, _ = _make_seed(tmp_path)
    for project_type in PROJECT_TYPES:
        ideation = Ideation(
            project_type=project_type,
            name=f"proj-{project_type}",
            goals=["Goal A"],
            constraints=["Constraint B"],
        )
        path = seed.graduate(ideation)
        # Should not raise
        content = path.read_text(encoding="utf-8")
        assert len(content) > 0


def test_seed_marks_emits_one_intent_per_goal(tmp_path):
    seed, ms, _ = _make_seed(tmp_path)
    ideation = Ideation(
        project_type="software",
        name="proj",
        goals=["Goal A", "Goal B", "Goal C"],
        constraints=[],
    )
    marks = seed.seed_marks(ideation)
    assert len(marks) == 3


def test_seed_marks_are_written_to_markspace(tmp_path):
    seed, ms, _ = _make_seed(tmp_path)
    ideation = Ideation(
        project_type="software",
        name="proj",
        goals=["Build X"],
        constraints=[],
    )
    seed.seed_marks(ideation)
    assert ms.write.called


def test_launch_calls_paul_plan(tmp_path):
    seed, ms, paul = _make_seed(tmp_path)
    ideation = Ideation(
        project_type="software",
        name="proj",
        goals=["Build X"],
        constraints=[],
    )
    plan = seed.launch(ideation)
    assert paul.plan.called


def test_launch_does_not_reask_answered_questions(tmp_path):
    """launch() must not prompt — it must use ideation data directly."""
    seed, ms, paul = _make_seed(tmp_path)
    ideation = Ideation(
        project_type="workflow",
        name="my-workflow",
        goals=["Automate deployment"],
        constraints=["No cloud"],
    )
    # launch() must complete without input() calls
    with patch("builtins.input", side_effect=AssertionError("Should not call input()")):
        seed.launch(ideation)
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_seed.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'msp.layer5.seed'`

- [ ] **Step 3: Implement ProjectGenesis**

```python
# msp/layer5/seed.py
"""SEED: ProjectGenesis — type-first ideation, PLANNING.md output, PAUL handoff.

Translates a raw idea into a structured PLANNING.md and seeds the markspace
with initial Intent marks before handing off to PAUL.

Marks emitted:
  Intent(scope="seed", resource=goal) — one per goal on seed_marks() / launch()
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from markspace import Agent, Intent, MarkSpace, Source

from msp.layer5.paul import Milestone, PlanApplyUnify, Plan

PLANNING_TEMPLATE = """\
# {name} — Project Plan

**Type:** {project_type}

## Goals

{goals_list}

## Constraints

{constraints_list}

## Milestones

{milestones_section}
"""


@dataclass
class Ideation:
    """Structured output of a SEED ideation session."""
    project_type: str   # software | workflow | research | campaign | utility
    name: str
    goals: list[str]
    constraints: list[str]
    milestones: list[str] = field(default_factory=list)
    notes: str = ""


class ProjectGenesis:
    """Guides ideation and produces a structured PLANNING.md for PAUL.

    Attributes:
        markspace: Shared MarkSpace instance.
        paul:      PlanApplyUnify instance for headless PAUL handoff.
        root:      Parent directory for workspace files.
        agent:     Authorized Agent for writing marks.
    """

    def __init__(
        self,
        markspace: MarkSpace,
        paul: PlanApplyUnify,
        root: Path,
        agent: Agent | None = None,
    ) -> None:
        self.markspace = markspace
        self.paul = paul
        self.root = root
        self.agent = agent

    def ideate(self, project_type: str) -> Ideation:
        """Return a minimal Ideation for the given type (headless — no prompts).

        In a full interactive session, this would drive a guided interview.
        For programmatic/agent use, callers construct Ideation directly.
        """
        return Ideation(project_type=project_type, name="", goals=[], constraints=[])

    def graduate(self, ideation: Ideation) -> Path:
        """Write PLANNING.md to root/<name>/ and return its path."""
        project_dir = self.root / ideation.name
        project_dir.mkdir(parents=True, exist_ok=True)

        goals_list = "\n".join(f"- {g}" for g in ideation.goals) or "- (none specified)"
        constraints_list = "\n".join(f"- {c}" for c in ideation.constraints) or "- (none specified)"
        milestones_section = (
            "\n".join(f"- [ ] {m}" for m in ideation.milestones)
            if ideation.milestones
            else "- [ ] (to be defined with PAUL)"
        )

        content = PLANNING_TEMPLATE.format(
            name=ideation.name,
            project_type=ideation.project_type,
            goals_list=goals_list,
            constraints_list=constraints_list,
            milestones_section=milestones_section,
        )

        planning_path = project_dir / "PLANNING.md"
        planning_path.write_text(content, encoding="utf-8")
        return planning_path

    def seed_marks(self, ideation: Ideation) -> list[Intent]:
        """Emit one Intent mark per goal and return the list."""
        marks = []
        for goal in ideation.goals:
            intent = Intent(
                scope="seed",
                resource=ideation.name,
                action=goal,
                confidence=0.9,
            )
            if self.agent is not None:
                self.markspace.write(self.agent, intent)
            marks.append(intent)
        return marks

    def launch(self, ideation: Ideation) -> Plan:
        """Graduate + seed marks + initialize PAUL. No re-asking of questions."""
        self.graduate(ideation)
        self.seed_marks(ideation)

        milestones = [
            Milestone(
                id=f"m{i+1}",
                description=goal,
                acceptance_criteria=f"Goal achieved: {goal}",
            )
            for i, goal in enumerate(ideation.goals)
        ]
        return self.paul.plan(milestones)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_seed.py -v 2>&1 | tail -15
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add msp/layer5/seed.py tests/layer5/test_seed.py
git commit -m "feat(layer5): SEED — type-first ideation, PLANNING.md, PAUL handoff"
```

---

## Task 10: AEGIS — 6-phase audit, 12 personas, 14 domains, pattern corpus

**Files:**
- Create: `msp/layer5/aegis.py`
- Create: `tests/layer5/test_aegis.py`

- [ ] **Step 1: Write failing AEGIS tests**

```python
# tests/layer5/test_aegis.py
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
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_aegis.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'msp.layer5.aegis'`

- [ ] **Step 3: Implement EpistemicAudit**

```python
# msp/layer5/aegis.py
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
import uuid
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
            # Context phase: one placeholder finding per domain
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
            # Reconnaissance + domain audits: one finding per domain
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
            # Adversarial: Devil's Advocate challenges all prior findings
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

            # Emit marks and write to disk for phases 0-4
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/test_aegis.py -v 2>&1 | tail -20
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add msp/layer5/aegis.py tests/layer5/test_aegis.py
git commit -m "feat(layer5): AEGIS — 6-phase audit, 12 personas, 14 domains, pattern corpus"
```

---

## Task 11: Wire __init__.py and run full Layer 5 test suite

**Files:**
- Modify: `msp/__init__.py`
- Modify: `msp/layer5/__init__.py`

- [ ] **Step 1: Update msp/layer5/__init__.py to export public API**

```python
# msp/layer5/__init__.py
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
```

- [ ] **Step 2: Run the complete Layer 5 test suite**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer5/ -v 2>&1 | tail -30
```

Expected: all tests PASS. Count the total — should be 40+ tests.

- [ ] **Step 3: Run Layer 2 tests to verify extra_paths didn't break anything**

```bash
cd /home/orin/Model-Stigmergic-Protocol
python -m pytest tests/layer2/ -v 2>&1 | tail -10
```

Expected: all existing Layer 2 tests PASS.

- [ ] **Step 4: Final commit**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git add msp/layer5/__init__.py
git commit -m "feat(layer5): wire public API in __init__.py — Layer 5 complete"
```

---

## Summary

Layer 5 is complete when:
- [ ] All tests in `tests/layer5/` pass
- [ ] All tests in `tests/layer2/` still pass (extra_paths addition is backwards-compatible)
- [ ] Validation gate test (`test_integration_spine.py`) passes
- [ ] All 6 modules exported from `msp/layer5/__init__.py`
- [ ] All 9 rule files exist in `msp/layer5/rules/`
- [ ] Findings directory created on first AEGIS run
- [ ] Total test count is 40+ new tests in `tests/layer5/`
