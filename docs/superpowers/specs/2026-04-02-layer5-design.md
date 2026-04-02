# Layer 5: Orchestration Ecosystem — Design Spec
**Date:** 2026-04-02  
**Status:** Approved  
**Builds on:** Layers 1-4 (markspace, ICM, AgentSession, VaultSync)

---

## Summary

Layer 5 implements six interconnected orchestration tools as Python modules in `msp/layer5/`. All six are reimplemented from their JavaScript Claude Code extension originals as stigmergic-first Python modules (Option A). Backup approaches retained for future experimentation: Option B (thin Python adapter over JS subprocesses), Option C (hybrid — PAUL + BASE in Python, AEGIS + CARL as JS).

No existing layers are modified. All Layer 5 modules depend downward on Layers 1-4 only.

---

## Architecture Overview

```
msp/layer5/
├── __init__.py
├── base.py          — WorkspaceState: JSON surfaces, drift detection, PSMM
├── paul.py          — PlanApplyUnify: Plan→Apply→Unify loop, lifecycle marks
├── carl.py          — ContextAugmentation: intent detection → JIT rule injection
├── skillsmith.py    — CapabilityStandards: 7-file taxonomy, audit, scaffold
├── seed.py          — ProjectGenesis: type-first ideation, PLANNING.md, PAUL handoff
└── aegis.py         — EpistemicAudit: 12 personas × 14 domains, adversarial review
```

**Dependency graph (all downward — no modifications to Layers 1-4):**
```
seed ──────────────────────────────▶ paul
aegis ─────────────────────────────▶ paul, base, carl, skillsmith
paul ──────────────────────────────▶ base, carl, skillsmith
carl ──────────────────────────────▶ ContextLoader (L2), markspace Agent (L1)
skillsmith ────────────────────────▶ AgentSession (L3)
base ──────────────────────────────▶ VaultSync (L4), markspace Agent (L1)
```

**Stigmergic integration — marks emitted per module (no agent-to-agent messaging):**
- `base` → `Observation` marks on workspace state changes and drift detection
- `paul` → `Intent` marks on plan creation (per milestone), `Action` marks on task completion, `Observation` marks on UNIFY
- `carl` → `Observation` marks recording which domains were injected
- `skillsmith` → `Warning` marks on compliance failures (severity: critical/minor)
- `seed` → `Intent` marks per top-level goal on graduation
- `aegis` → `Observation` marks per domain finding, `Warning` marks on critical issues

---

## Module Designs

### BASE (`base.py`)

**Class:** `WorkspaceState`

Workspace state engine. Three responsibilities: JSON surfaces, drift detection, VaultSync bridge.

**Workspace files** at `msp/workspaces/<project>/base/`:
- `workspace.json` — project identity, health, active agents, last-seen timestamps
- `psmm.json` — Per-Session Meta Memory: last session summary, open questions, next-agent context
- `drift.json` — detected divergence between planned and actual state

**Drift detection:** compares `workspace.json` against markspace state on demand. Emits `Observation` mark with `scope="base"` flagging any divergence found.

**VaultSync bridge:** on session end, calls `VaultSync.export_observations(scope="base")` to persist workspace state to Obsidian vault. PSMM becomes the agent-level session continuity mechanism.

```python
class WorkspaceState:
    def __init__(self, project: str, markspace: MarkSpace, vault: VaultSync): ...
    def load(self) -> dict
    def save(self, data: dict) -> None                  # write + emit Observation mark
    def detect_drift(self) -> list[DriftItem]           # compare workspace vs marks
    def psmm_read(self) -> dict
    def psmm_write(self, session_data: dict) -> None    # write + export to vault
```

---

### PAUL Core (`paul.py` — Step 2)

**Class:** `PlanApplyUnify`

Plan→Apply→Unify loop against a `WorkspaceState`. Plan state lives in structured files — **not** the markspace. Marks emitted at lifecycle events only.

**Biological analogy:** files = nest (the structured artifact), marks = pheromones (coordination signals).

**Plan files** at `msp/workspaces/<project>/paul/`:
- `STATE.md` — current plan state
- `MILESTONES.md` — milestone definitions with acceptance criteria
- `SUMMARY.md` — written on UNIFY

**Plan phase:** writes STATE.md + MILESTONES.md. Emits one `Intent` mark per milestone (not per task — keeps markspace lean).

**Apply phase:** executes tasks via `AgentSession`. Emits one `Action` mark per completed task with task ID in payload.

**Unify phase:** reconciles planned vs. completed, writes SUMMARY.md, emits single `Observation` mark closing the plan, updates BASE `workspace.json`.

**Key constraint:** `apply()` writes its own `Action` marks and reads its own `Intent` marks only. Other agents observe PAUL's progress through marks; PAUL does not observe theirs.

```python
class PlanApplyUnify:
    def __init__(self, project: str, state: WorkspaceState, markspace: MarkSpace): ...
    def plan(self, milestones: list[Milestone]) -> Plan
    def apply(self, plan: Plan, session: AgentSession) -> Result
    def unify(self, plan: Plan, result: Result) -> Summary
    def run(self, milestones: list[Milestone], session: AgentSession) -> Summary
```

---

### CARL (`carl.py`)

**Class:** `ContextAugmentation`

Intent detection → JIT rule injection. Hooks on every `AgentSession` launch. Reads active `Intent` marks, scores against domain trigger lists, calls `ContextLoader` to inject matched rule files as Layer 3 reference material.

**Rule domains** stored at `msp/layer5/rules/<domain>.md`:
- Inherited: `development`, `debugging`, `planning`, `research`, `review`, `content`
- MSP-specific: `stigmergy`, `orchestration`, `audit`

**Intent detection:** keyword scoring against domain trigger lists from active Intent marks. Top-scoring domains selected for injection.

**Injection:** calls `ContextLoader.load_context()` with matched rule files appended as Layer 3 reference material. No new context hierarchy — piggybacks on existing ICM infrastructure (L2). **Implementation note:** verify `ContextLoader` accepts supplemental paths at call time; if not, a minimal extension to `ContextLoader.load_context(extra_paths=[])` will be needed (small, additive change).

```python
class ContextAugmentation:
    def __init__(self, markspace: MarkSpace, loader: ContextLoader): ...
    def detect_domains(self, marks: list[Intent]) -> list[str]
    def load_rules(self, domains: list[str]) -> list[Path]
    def inject(self, session_config: dict) -> dict          # augmented config
    def observe(self, domains: list[str]) -> None           # emit Observation mark
```

PAUL calls `carl.inject(session_config)` before every `apply()` call.

---

### SKILLSMITH (`skillsmith.py`)

**Class:** `CapabilityStandards`

Pre-flight compliance checker for `AgentSession` skill directories. Enforces 7-file taxonomy before execution. Emits `Warning` marks for violations.

**7-file taxonomy:**
1. `entry-point.md` — routing and persona
2. `tasks/*.md` — task definitions
3. `frameworks/*.md` — domain knowledge
4. `templates/*.md` — output templates
5. `context/*.md` — background context
6. `checklists/*.md` — quality gates
7. `rules/*.md` — authoring constraints

**Compliance audit:** checks presence and structure of required files against spec rules. `Warning` mark severity: missing entry point = critical (blocks execution via `Need` mark), missing checklist = minor (logs only).

**Scaffold:** generates compliant skeleton directory from a `SkillSpec`. Used by SEED during genesis.

```python
class CapabilityStandards:
    def __init__(self, markspace: MarkSpace): ...
    def audit(self, skill_path: Path) -> AuditReport
    def scaffold(self, spec: SkillSpec, dest: Path) -> Path
    def validate_session(self, session: AgentSession) -> bool  # pre-flight before launch
```

PAUL calls `skillsmith.validate_session(session)` inside `apply()` before executing any `AgentSession`. Critical failure emits `Need` mark requesting remediation and blocks execution.

---

### PAUL Full (`paul.py` — Step 5 additions)

Three capabilities added on top of the core loop:

**1. Diagnostic failure routing:** classifies task failures and routes to appropriate handler.
- Scope creep → `Need` mark requesting plan revision
- Dependency missing → `Need` mark targeting blocking agent
- Compliance violation → calls `skillsmith.audit()`, attaches report to mark

**2. Scope boundaries:** enforces that `AgentSession` instances only write marks within their declared scope. Each session initialized with scope derived from milestone ID. Validated using markspace absorbing barrier properties (L1, P45-P52).

**3. Qualify loop:** after each `apply()` cycle, checks Action marks match expected outputs declared in Plan. Mismatch → re-queues task with gap description appended to context. Maximum 2 re-queue attempts before escalating to `Warning` mark.

```python
# Additions to PlanApplyUnify:
def qualify(self, task: Task, result: Result) -> QualifyVerdict
def route_failure(self, task: Task, error: TaskError) -> None
def enforce_scope(self, session: AgentSession, milestone: Milestone) -> None
```

---

### SEED (`seed.py`)

**Class:** `ProjectGenesis`

Type-first ideation → structured `PLANNING.md` → headless PAUL handoff. Emits initial `Intent` marks seeding the markspace for a new project.

**Project types:** `software`, `workflow`, `research`, `campaign`, `utility`. Type determines interview questions and PLANNING.md template.

**Guided ideation:** `Ideation` dataclass collects responses. SEED coaches (offers suggestions when stuck, pushes toward decisions when ready) — not interrogates.

**Graduation:** writes `PLANNING.md` to `msp/workspaces/<project>/`, emits one `Intent` mark per top-level goal, calls `PlanApplyUnify.plan()` to initialize PAUL workspace. No re-asking of answered questions.

```python
class ProjectGenesis:
    def __init__(self, markspace: MarkSpace, paul: PlanApplyUnify): ...
    def ideate(self, project_type: str) -> Ideation
    def graduate(self, ideation: Ideation) -> Path              # write PLANNING.md
    def launch(self, ideation: Ideation) -> Plan                # graduate + PAUL init
    def seed_marks(self, ideation: Ideation) -> list[Intent]    # emit initial Intent marks
```

---

### AEGIS (`aegis.py`)

**Class:** `EpistemicAudit`

Multi-phase audit system. Runs as `AgentSession` instances using MSP's own infrastructure — recursive governance. Audits both codebase and coordination behavior (live markspace).

**12 Personas:**

| # | Persona | Primary domains |
|---|---|---|
| 0 | Principal Engineer | Context & Intent, Architecture |
| 1 | Architect | Architecture, System Design |
| 2 | Staff Engineer | Code Quality, Patterns |
| 3 | Senior App Engineer | Implementation, Testing |
| 4 | Data Engineer | Data integrity, State |
| 5 | Test Engineer | Coverage, Edge cases |
| 6 | Security Engineer | Auth, Attack surface |
| 7 | Performance Engineer | Latency, Resource usage |
| 8 | SRE | Reliability, Observability |
| 9 | Compliance Officer | Governance, Standards |
| 10 | Devil's Advocate | Assumptions, Blind spots |
| 11 | Reality Gap Analyst | Planned vs. actual divergence |

**14 Audit Domains (0-13):**
0. Context & Intent — 1. Architecture — 2. Data & State — 3. Code Quality — 4. Testing — 5. Security — 6. Performance — 7. Reliability — 8. Observability — 9. API Design — 10. Documentation — 11. Dependency — 12. Operational — 13. Stigmergic Coordination *(MSP-specific: mark health, decay rates, scope violations, drift)*

**6 Execution Phases:**
- Phase 0: Context — establish constraints, success criteria
- Phase 1: Reconnaissance — map codebase + markspace structure
- Phase 2: Domain Audits — each persona audits primary domains
- Phase 3: Cross-domain — reconcile findings spanning multiple domains
- Phase 4: Adversarial — Devil's Advocate + Reality Gap Analyst challenge all findings
- Phase 5: Report — synthesized findings, intervention levels, remediation priorities

Phase handoffs use `Observation` marks with structured finding payloads.

**Three output layers:**
1. **Findings** — per-domain, with confidence scores and evidence. Stored in `msp/workspaces/<project>/aegis/findings/`.
2. **AEGIS Transform** — actionable remediation plan. Intervention levels: Observe → Investigate → Remediate → Redesign → Halt.
3. **Pattern Corpus** — recurring patterns written back to `msp/layer5/rules/` as new CARL domain rules. AEGIS improves CARL's rule base over time.

**Recursive property:** AEGIS uses AgentSession (L3) + CARL (L5) + SKILLSMITH (L5) internally. Domain 13 audits PAUL's mark emission patterns, CARL's rule injection history, and BASE's drift detection accuracy — closing the governance loop.

```python
class EpistemicAudit:
    def __init__(self, project: str, markspace: MarkSpace,
                 paul: PlanApplyUnify, base: WorkspaceState): ...
    def run(self, scope: AuditScope) -> AuditReport
    def phase(self, n: int, context: AuditContext) -> list[Finding]
    def transform(self, report: AuditReport) -> RemediationPlan
    def update_carl_rules(self, report: AuditReport) -> list[Path]
```

---

## Build Sequence

```
Step 1: base.py          — WorkspaceState, drift, PSMM, VaultSync bridge
Step 2: paul.py (core)   — Plan/Apply/Unify, lifecycle marks, scope enforcement
Step 3: carl.py          — intent detection, JIT injection, rules directory
Step 4: skillsmith.py    — 7-file taxonomy, audit, scaffold, pre-flight
── VALIDATION GATE: minimal stigmergic loop end-to-end ──
Step 5: paul.py (full)   — diagnostic routing, qualify loop
Step 6: seed.py          — type-first ideation, graduation, PAUL handoff
Step 7: aegis.py         — 6-phase audit, 12 personas, 14 domains, pattern corpus
```

---

## Test Strategy

All tests in `tests/layer5/`. Consistent with Layers 1-4: pytest + Hypothesis for property tests.

| Module | Unit | Integration | Property |
|---|---|---|---|
| base.py | WorkspaceState CRUD, drift logic | Round-trip with VaultSync (L4) | Drift never false-negative |
| paul.py | Each loop phase isolated | Full loop with mock AgentSession | Loop always closes |
| carl.py | Domain scoring, rule resolution | Inject into real ContextLoader (L2) | No domain scores negative |
| skillsmith.py | Each file type validator | Scaffold → audit round-trip | All scaffolded skills pass audit |
| seed.py | Each project type template | Graduate → PAUL handoff | PLANNING.md always parseable |
| aegis.py | Each phase isolated | Full 6-phase on MSP codebase | All 14 domains produce findings |

**Target:** 373 (current) → ~450+ tests after Layer 5.

---

## Integration Map

```
base    ←→ VaultSync (L4):     PSMM export, workspace persistence
base    ←→ markspace (L1):     Observation marks on state changes
paul    ←→ base:               reads/writes workspace.json, PSMM
paul    ←→ carl:               inject() before every apply()
paul    ←→ skillsmith:         validate_session() before every apply()
paul    ←→ AgentSession (L3):  executes tasks
carl    ←→ ContextLoader (L2): hot-loads rule files
carl    ←→ markspace (L1):     reads Intent marks, writes Observation marks
skillsmith ←→ AgentSession (L3): pre-flight validation
seed    ←→ paul:               launch() calls paul.plan()
seed    ←→ markspace (L1):     seed_marks() emits initial Intent marks
aegis   ←→ paul/base/carl/skillsmith: audits live system
aegis   ←→ carl:               update_carl_rules() feeds pattern corpus back
```

---

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Implementation language | Python (Option A) | Consistent with Layers 1-4; Options B/C retained as backup experiments |
| Plan state location | Structured files in `paul/` workspace | Marks = pheromones (signals); files = nest (artifacts). Biological stigmergy model. |
| CARL/SKILLSMITH integration | Separate L5 modules calling down into L2/3 | Preserves additive-only principle; no modifications to validated layers |
| Build order | Stigmergic spine first (BASE → PAUL core → CARL → SKILLSMITH → validation gate → rest) | Validate coordination architecture before committing to full build |
| AEGIS scope | Full — 12 personas × 14 domains | Consistent with depth of Layers 1-4 |
| CARL/SKILLSMITH future state | Option C (peer AgentSessions via marks) | Deferred until orchestration loop is stable |
