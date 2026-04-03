# Model Stigmergic Protocol — Architecture Plan

## Overview

MSP is a bio-governed multi-agent coordination infrastructure built on stigmergic principles. Agents coordinate through shared environment marks — not direct messaging. The architecture draws from 29 evaluated candidate projects, formal protocol research, biological mathematics, and control theory.

## Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: Orchestration Ecosystem                           │
│  PAUL (plan-apply-unify) · AEGIS (audit) · BASE (state)    │
│  CARL (rules) · SEED (genesis) · Skillsmith (standards)    │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Knowledge Integration                             │
│  Obsidian (persistent knowledge) · NotebookLM (synthesis)   │
│  memboot (offline memory) · OpenViking (tiered retrieval)   │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Multi-Provider Orchestration                      │
│  Claude Code · Codex · Gemini CLI · Antigravity             │
│  agent:// identity · Provider adapters · animus (budgets)   │
│  obsidian-agent-client (unified interface)                  │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Context Engineering Infrastructure                │
│  ICM 5-layer hierarchy · Progressive disclosure             │
│  Hot/warm/cold tiers · FOL token encoding                   │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Coordination Core                                 │
│  markspace (formal spec, 66 properties)                     │
│  + claw-swarm (12-dim signal field, MMAS pheromone)         │
│  + sbp (wire protocol, JSON-RPC + SSE)                      │
│  + stigmergy (Rust ECS, PostgreSQL persistence)             │
│  + strix (control barriers, fractal hierarchy)              │
│  + autonomous-agents (Git-backed pure stigmergy)            │
│  + collective-intelligence (minimal trace model)            │
│  + pheromind (NL → structured signal translation)           │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Coordination Core

### Primary: markspace (formal spec — validated)

- Five typed marks: Intent, Action, Observation, Warning, Need
- Deterministic guard layer independent of agent compliance
- Exponential decay (pheromone evaporation model)
- Source-based trust weighting (fleet/verified/unverified)
- Sublinear reinforcement with flooding protection
- Statistical anomaly detection (Welford's algorithm)
- Absorbing barriers (monotonic scope restriction)
- Diagnostic probes (canary injection)
- 66 formal properties verified via Hypothesis
- **Status:** 312/312 tests passing on Jetson aarch64

### Complementary Sources

| Source | What to extract | Priority |
|---|---|---|
| **claw-swarm** | 12-dim signal field (trail, alarm, reputation, task, knowledge, coordination, emotion, trust, SNA, learning, calibration, species), forward-decay encoding, MMAS pheromone engine, role-based sensitivity filters, dual-process routing (System 1/2) | High |
| **sbp** | Pheromone wire protocol (JSON-RPC 2.0 + SSE), 4 decay models (exponential/linear/step/immortal), merge strategies (reinforce/replace/max/add), scent condition evaluation, rate limiting | High |
| **stigmergy** | Entity-Component-System architecture (Rust), auction-based bidding for conflict resolution, PostgreSQL persistence with ACID, schema validation, `stigctl` CLI | High |
| **strix** | Digital pheromone fields (explored/danger/interest/relay), multi-horizon temporal planning (H1/H2/H3), control barrier functions, fractal self-similar hierarchy, anti-fragile loss recovery | High |
| **autonomous-agents** | Git-backed task queue (queue.json → active.json), push-conflict as synchronization primitive, self-healing timeouts (4h task, 2h stale lock), knowledge persistence (patterns.jsonl) | Medium |
| **pheromind** | Natural language → structured signal translation (Scribe agent), signal dynamics (evaporation/amplification/pruning), hierarchical orchestrator pattern | Medium |
| **collective-intelligence** | Minimal trace model (~200 lines), async decay, convergence detection via idle rounds, cycle detection via state hashing | Medium |

---

## Layer 2: Context Engineering Infrastructure

### Primary: ICM (Interpreted Context Methodology)

Five-layer context hierarchy replacing framework abstractions with filesystem:

```
Layer 0 (Global Identity)    — CLAUDE.md / GEMINI.md / AGENTS.md (~800 tokens)
Layer 1 (Workspace Routing)  — Root CONTEXT.md maps requests to stages (~300 tokens)
Layer 2 (Stage Contract)     — Per-stage CONTEXT.md: inputs, process, outputs (200-500 tokens)
Layer 3 (Reference Material) — Stable config in references/ and _config/ (500-2k tokens)
Layer 4 (Working Artifacts)  — Per-run content in output/ folders
```

### Complementary Sources

| Source | What to extract | Priority |
|---|---|---|
| **OpenViking** | Tiered context (L0 ~100 tokens / L1 ~2k / L2 full), virtual `viking://` URIs, directory recursive retrieval, session auto-iteration memory extraction | High |
| **Free-Order-Logic** | Suffix-based token syntax for order-independent mark encoding (`.s`/`.o`/`.p`/`.t`), permanent vs. temporary state separation, vector summation for conflict resolution | Medium |
| **memboot** | AST-aware code chunking, TF-IDF embeddings, token-budgeted context builder, file watcher + auto-reindex | Medium |

### Hot/Warm/Cold Context Tiers

| Tier | Contains | Store | Access |
|------|----------|-------|--------|
| Hot | Active intents, fresh observations, recent actions | Redis / in-memory | Every agent round |
| Warm | Older actions, supersession chains, resolved needs | PostgreSQL | On-demand query |
| Cold | Expired intents, fully-decayed marks, archives | Cold storage | Audit only |

### Design Decisions Needed

- [ ] How does the ICM stage contract map to markspace scopes?
- [ ] Should CONTEXT.md files be marks themselves or external metadata?
- [ ] How does progressive disclosure interact with token budgets (P59-P63)?
- [ ] Does FOL suffix encoding replace or complement protobuf mark schemas?

---

## Layer 3: Multi-Provider Orchestration

### Agent Identity (from Rodriguez 2026)

```
agent://{trust-root}/{capability-path}/{unique-id}
```

Examples:
```
agent://ikay13/planning/architect/claude-opus-01
agent://ikay13/execution/builder/codex-pro-01
agent://ikay13/research/analyst/gemini-ultra-01
agent://ikay13/testing/validator/antigravity-01
```

### Provider Adapters

```
┌──────────────┐     ┌───────────────┐     ┌────────────┐
│ Claude Code   │────▶│ MSP Adapter   │────▶│            │
│ (Opus 4.6)    │     │ - read marks  │     │            │
└──────────────┘     │ - write marks │     │  Mark      │
                     │ - guard check │     │  Space     │
┌──────────────┐     ├───────────────┤     │            │
│ Codex Pro     │────▶│ MSP Adapter   │────▶│            │
└──────────────┘     └───────────────┘     │            │
                                           │            │
┌──────────────┐     ┌───────────────┐     │            │
│ Gemini Ultra  │────▶│ MSP Adapter   │────▶│            │
└──────────────┘     └───────────────┘     └────────────┘
```

### Complementary Sources

| Source | What to extract | Priority |
|---|---|---|
| **animus** | Quorum intent graphs, token budget enforcement, checkpoint/resume, constitutional principles (P1-P9), provider abstraction (Claude/OpenAI/Ollama) | High |
| **stigmer** | Multi-provider LLM abstraction, MCP server integration, Temporal workflow orchestration, YAML agent/workflow definitions | High |
| **obsidian-agent-client** | Ports-and-adapters pattern (IAgentClient interface), unified SessionUpdate event model, ACP adapter (JSON-RPC over stdin/stdout) | Medium |
| **Skill_Seekers** | Knowledge ingestion from 17 source types → 24 platform formats | Medium |

### Design Decisions Needed

- [ ] How do provider adapters authenticate with the mark space?
- [ ] Does each provider run its own guard instance or share one?
- [ ] How are provider-specific capabilities declared in manifests?
- [ ] Transport: MCP server, REST API, filesystem, or hybrid?
- [ ] Does animus Quorum replace or complement markspace's conflict resolution?

---

## Layer 4: Knowledge Integration

### Obsidian Vault as Persistent Memory

```
vault/
  {project}/           — Per-project tracking
    {project} Project.md  — Progress tracker
    sessions/            — Session logs
    decisions/           — Decision records
  agents/              — Agent profiles, role definitions
  research/            — Research findings
  architecture/        — System design documents
```

### Complementary Sources

| Source | What to extract | Priority |
|---|---|---|
| **memboot** | Dual-store pattern (chunks + memories), episodic memory CRUD, MCP server for tool exposure, SQLite offline-first persistence | High |
| **OpenViking** | Session auto-iteration (end-of-session memory extraction), dual-format output (markdown + YAML), VLM provider abstraction | Medium |
| **obsidian-agent-client** | Vault adapter pattern for filesystem context integration, permission handling with promise-based resolution | Medium |
| **NotebookLM** | Source ingestion, audio summary generation, Q&A over documents | Medium |

### Design Decisions Needed

- [ ] How does the Obsidian vault connect to the mark space?
- [ ] Should vault entries generate observation marks automatically?
- [ ] How does NotebookLM output feed into agent context?
- [ ] Does memboot replace or augment Obsidian for agent-facing memory?

---

## Layer 5: Orchestration Ecosystem

Six interconnected tools providing macro-level project orchestration:

```
SEED (genesis) → PAUL (orchestration) → AEGIS (audit)
                    ↕                       ↕
               BASE (state)            CARL (rules)
                    ↕
            SKILLSMITH (capability standards)
```

| Tool | Role | Key Pattern |
|---|---|---|
| **seed** | Project genesis | Type-first ideation, composable data layer, headless PAUL handoff |
| **paul** | Plan-Apply-Unify loop | Execute/Qualify loop, diagnostic failure routing, scope boundaries |
| **aegis** | Codebase audit | 12 personas × 14 domains, epistemic governance, adversarial review |
| **base** | Workspace state | JSON data surfaces, drift detection, PSMM session memory, Apex analytics |
| **carl** | Dynamic rules | JIT domain loading, context brackets, decision logging |
| **skillsmith** | Capability standards | 7-file taxonomy, discover→scaffold, compliance audit |

### Complementary Sources

| Source | What to extract | Priority |
|---|---|---|
| **ai-skills** | Skill registry (registry.yaml), WHY/WHAT/HOW workflow, validator/bundler infrastructure | Medium |
| **claude-skills_transferable** | 205-skill library, multi-tool conversion scripts, orchestration patterns (Solo Sprint, Domain Deep-Dive, Multi-Agent Handoff) | Medium |
| **claude-skills-marketplace** | Plugin auto-discovery, execution runtime for token-efficient bulk ops | Low |
| **system-prompts-and-models-of-ai-tools** | Reference archive of 37+ AI platform architectures | Low |

---

## Candidate Inventory (29 projects evaluated)

| # | Project | Tier | Layer | Status |
|---|---|---|---|---|
| 1 | markspace | Core | 1 | ✅ Validated (312/312 tests) |
| 2 | claw-swarm | Core | 1 | Evaluated |
| 3 | sbp | Core | 1 | Evaluated |
| 4 | stigmergy | Core | 1 | Evaluated |
| 5 | strix | Core | 1 | Evaluated |
| 6 | autonomous-agents | Core | 1 | Evaluated |
| 7 | collective-intelligence | Core | 1 | Evaluated |
| 8 | pheromind | Core | 1 | Evaluated |
| 9 | ICM | Infrastructure | 2 | Evaluated |
| 10 | OpenViking | Infrastructure | 2/4 | Evaluated |
| 11 | Free-Order-Logic | Infrastructure | 2 | Evaluated |
| 12 | memboot | Infrastructure | 2/4 | Evaluated |
| 13 | animus | Infrastructure | 3 | Evaluated |
| 14 | stigmer | Infrastructure | 3 | Evaluated |
| 15 | obsidian-agent-client | Infrastructure | 3/4 | Evaluated |
| 16 | Skill_Seekers | Tools | 3 | Evaluated |
| 17 | aegis | Ecosystem | 5 | Evaluated |
| 18 | base | Ecosystem | 5 | Evaluated |
| 19 | paul | Ecosystem | 5 | Evaluated |
| 20 | carl | Ecosystem | 5 | Evaluated |
| 21 | seed | Ecosystem | 5 | Evaluated |
| 22 | skillsmith | Ecosystem | 5 | Evaluated |
| 23 | xyph | Reference | 1 | Evaluated |
| 24 | ai-skills | Patterns | 5 | Evaluated |
| 25 | claude-skills_transferable | Patterns | 5 | Evaluated |
| 26 | claude-skills-marketplace | Patterns | 5 | Evaluated |
| 27 | system-prompts-and-models-of-ai-tools | Reference | — | Evaluated |
| 28 | MABE | Reference | — | Evaluated |
| 29 | DDIT | Reference | — | Evaluated |

Rejected: LinuxTools (personal utilities), RedOPS (security tooling)

---

## Gap Analysis: markspace → MSP

| markspace Gap | MSP Extension | Source Candidates | Priority |
|---|---|---|---|
| No multi-provider support | Layer 3: Provider adapters + agent:// identity | animus, stigmer, obsidian-agent-client | High |
| No agent identity standard | Layer 3: agent:// URI scheme | Rodriguez 2026 | High |
| No filesystem-based context | Layer 2: ICM context hierarchy | ICM, OpenViking, memboot | High |
| No signal field dimensions | Layer 1: 12-dim signal field | claw-swarm | High |
| No wire protocol | Layer 1: JSON-RPC + SSE | sbp | High |
| No persistent storage | Layer 1: PostgreSQL + ECS | stigmergy | High |
| No control theory safety | Layer 1: Control barrier functions | strix | Medium |
| No NL → signal translation | Layer 1: Scribe pattern | pheromind | Medium |
| No persistent knowledge | Layer 4: Obsidian + memboot | memboot, obsidian-agent-client | Medium |
| No research synthesis | Layer 4: NotebookLM | NotebookLM API | Medium |
| No macro orchestration | Layer 5: PAUL/AEGIS/BASE ecosystem | paul, aegis, base, carl, seed, skillsmith | Medium |
| Static trust (3 levels) | Future: Dynamic trust from control theory | strix, MMSP research | Future |
| No semantic error detection | Future: Cognitive neuroscience-inspired | MMSP research | Future |
| No stability guarantees | Future: Lyapunov stability analysis | MMSP research | Future |
| No perturbation resilience | Future: Chaos/perturbation theory | MMSP research | Future |

---

## Future: MSP/MMSP Protocol

The formal protocol will be extracted after infrastructure is built and validated. Research areas:

- **Control theory**: Lyapunov stability for governance guarantees (strix reference)
- **Dynamical systems**: Attractor analysis for agent convergence
- **Chaos & perturbation theory**: Resilience under adversarial conditions
- **Cognitive neuroscience**: Semantic error detection models
- **Biological agent-based systems**: Emergent coordination patterns (MABE sandbox)
- **Information theory**: Signal field efficiency measurement (DDIT)

See memory: `project_stigmeric_protocol.md`

---

## Implementation Order

1. ~~Get markspace running locally on Jetson~~ ✅ (312/312 tests)
2. Build Layer 2: filesystem context hierarchy (from ICM + OpenViking)
3. Build Layer 1 extensions: integrate claw-swarm signal field + sbp wire protocol
4. Build Layer 3: Claude Code adapter (first provider)
5. Build Layer 3: agent:// identity scheme
6. Build Layer 4: Obsidian vault + memboot integration
7. Integrate Layer 5: PAUL orchestration loop
8. Add second provider adapter (Codex or Gemini)
9. End-to-end: two agents coordinating through mark space
10. Extract MSP/MMSP protocol from working infrastructure
