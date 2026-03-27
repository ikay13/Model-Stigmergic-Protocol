# Model Stigmergic Protocol — Architecture Plan

## Overview

MSP extends the markspace coordination protocol with four layers that address its documented gaps: multi-provider agent identity, filesystem-based context engineering, biological governance, and a knowledge integration layer.

## Layers

```
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Knowledge Integration                         │
│  Obsidian (persistent knowledge) + NotebookLM (synth)   │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Multi-Provider Orchestration                  │
│  Claude Code · Codex · Gemini CLI · Antigravity         │
│  Agent Identity URI (agent://) · Provider adapters      │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Context Engineering Infrastructure            │
│  ICM-inspired filesystem hierarchy · Progressive        │
│  disclosure · Hot/warm/cold context tiers               │
├─────────────────────────────────────────────────────────┤
│  Layer 1: Coordination Core (markspace)                 │
│  5 mark types · Guard · Decay · Trust · Reinforcement   │
│  66 formal properties · Adversarial validation          │
└─────────────────────────────────────────────────────────┘
```

## Layer 1: Coordination Core (markspace — exists)

The markspace protocol provides the stigmergic coordination foundation:
- Five typed marks: Intent, Action, Observation, Warning, Need
- Deterministic guard layer independent of agent compliance
- Exponential decay (pheromone evaporation model)
- Source-based trust weighting (fleet/verified/unverified)
- Sublinear reinforcement with flooding protection
- Statistical anomaly detection (Welford's algorithm)
- Absorbing barriers (monotonic scope restriction)
- Diagnostic probes (canary injection)
- 66 formal properties verified via Hypothesis

**Status:** Complete. Reference implementation in Python.

## Layer 2: Context Engineering Infrastructure (to build)

Based on the Interpreted Context Methodology (ICM) and "Everything is Context" (AFS) research.

### Five-Layer Context Hierarchy

```
Layer 0 (Global Identity)    — CLAUDE.md / GEMINI.md / AGENTS.md (~800 tokens)
Layer 1 (Workspace Routing)  — Root CONTEXT.md maps requests to stages (~300 tokens)
Layer 2 (Stage Contract)     — Per-stage CONTEXT.md: inputs, process, outputs (200-500 tokens)
Layer 3 (Reference Material) — Stable config in references/ and _config/ (500-2k tokens)
Layer 4 (Working Artifacts)  — Per-run content in output/ folders
```

### Hot/Warm/Cold Context Tiers

Maps directly to markspace's tiered mark management:

| Tier | Contains | Store | Access |
|------|----------|-------|--------|
| Hot | Active intents, fresh observations, recent actions | Redis / in-memory | Every agent round |
| Warm | Older actions, supersession chains, resolved needs | PostgreSQL | On-demand query |
| Cold | Expired intents, fully-decayed marks, archives | Cold storage | Audit only |

### Design Decisions Needed

- [ ] How does the ICM stage contract map to markspace scopes?
- [ ] Should CONTEXT.md files be marks themselves or external metadata?
- [ ] How does progressive disclosure interact with token budgets (P59-P63)?

## Layer 3: Multi-Provider Orchestration (to build)

### Agent Identity (from Rodriguez 2026)

Adopt the `agent://` URI scheme for topology-independent agent naming:

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

Key properties:
- **Trust root**: organizational identity (your GitHub user)
- **Capability path**: semantic discovery — agents find collaborators by capability
- **Cryptographic attestation**: PASETO tokens for cross-fleet identity verification
- Enables upgrading external marks to EXTERNAL_VERIFIED structurally

### Provider Adapters

Each provider needs an adapter that translates between the provider's native interface and the markspace protocol:

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
└──────────────┘     │               │     │            │
                     └───────────────┘     └────────────┘
```

### Design Decisions Needed

- [ ] How do provider adapters authenticate with the mark space?
- [ ] Does each provider run its own guard instance or share one?
- [ ] How are provider-specific capabilities declared in manifests?
- [ ] What's the transport: MCP server, REST API, filesystem, or hybrid?

## Layer 4: Knowledge Integration (to build)

### Obsidian Vault as Persistent Memory

```
vault/
  agents/           — Agent profiles, role definitions
  decisions/        — Decision logs (why X was chosen over Y)
  research/         — Research findings, referenced by marks
  architecture/     — System design documents
  sessions/         — Session logs and handoff notes
```

Obsidian provides:
- Persistent knowledge that survives context resets
- Bidirectional links between concepts
- Search and graph visualization
- Human-readable and editable

### NotebookLM as Research Synthesizer

- Ingest documentation, specs, papers
- Generate audio summaries for review
- Q&A over ingested sources
- Feed findings back as observation marks

### Design Decisions Needed

- [ ] How does the Obsidian vault connect to the mark space?
- [ ] Should vault entries generate observation marks automatically?
- [ ] How does NotebookLM output feed into agent context?

## Gap Analysis: markspace → MSP

| markspace Gap | MSP Extension | Priority |
|---|---|---|
| No multi-provider support | Layer 3: Provider adapters + agent identity | High |
| No agent identity standard | Layer 3: agent:// URI scheme | High |
| No filesystem-based context | Layer 2: ICM context hierarchy | High |
| No persistent knowledge layer | Layer 4: Obsidian integration | Medium |
| No research synthesis | Layer 4: NotebookLM integration | Medium |
| Static trust (3 levels only) | Future: Dynamic trust from control theory | Future (MSP/MMSP) |
| No semantic error detection | Future: Cognitive neuroscience-inspired | Future (MSP/MMSP) |
| No stability guarantees | Future: Lyapunov stability analysis | Future (MSP/MMSP) |
| No perturbation resilience | Future: Chaos/perturbation theory | Future (MSP/MMSP) |

## Future: MSP/MMSP Protocol

The formal protocol will be extracted after infrastructure is built and validated. Research areas:

- **Control theory**: Lyapunov stability for governance guarantees
- **Dynamical systems**: Attractor analysis for agent convergence
- **Chaos & perturbation theory**: Resilience under adversarial conditions
- **Cognitive neuroscience**: Semantic error detection models
- **Biological agent-based systems**: Emergent coordination patterns

See memory: `project_stigmeric_protocol.md`

## Implementation Order

1. Get markspace running locally on Jetson (validate reference impl)
2. Build Layer 2: filesystem context hierarchy
3. Build Layer 3: Claude Code adapter (first provider)
4. Build Layer 3: agent:// identity scheme
5. Build Layer 4: Obsidian vault integration
6. Add second provider adapter (Codex or Gemini)
7. End-to-end: two agents coordinating through mark space
8. Extract MSP protocol from working infrastructure
