# Model Stigmergic Protocol (MSP)

Bio-governed multi-agent coordination infrastructure based on stigmergic principles.

## What This Is

MSP extends the [markspace](https://github.com/opinionated-systems/markspace) coordination protocol (MIT licensed) with:

- **Multi-provider orchestration** — Claude Code, Codex, Gemini CLI, and Antigravity coordinating through a shared mark space
- **Agent identity** — `agent://` URI scheme for topology-independent naming and capability-based discovery (based on [Rodriguez, 2026](https://arxiv.org/abs/2601.14567))
- **Context engineering infrastructure** — filesystem-based context hierarchy inspired by the Interpreted Context Methodology ([ICM](https://arxiv.org/html/2603.16021)) and Agentic File System ([AFS](https://arxiv.org/html/2512.05470v1))
- **Knowledge integration** — Obsidian for persistent knowledge, NotebookLM for research synthesis
- **Biological governance** — immune-system trust models, quorum sensing, stigmergic decay

## Architecture

```
Layer 4: Knowledge Integration (Obsidian + NotebookLM)
Layer 3: Multi-Provider Orchestration (agent:// identity + provider adapters)
Layer 2: Context Engineering Infrastructure (ICM hierarchy + tiered context)
Layer 1: Coordination Core (markspace — 5 marks, guard, decay, trust, 66 properties)
```

See [planning/ARCHITECTURE.md](planning/ARCHITECTURE.md) for details.

## Foundation

The coordination core is the markspace protocol — a stigmergic coordination system for LLM agent fleets with:

- Five typed marks (Intent, Action, Observation, Warning, Need) with biological decay/reinforcement
- Deterministic guard layer independent of agent compliance
- Adversarial validation up to 1,050 agents
- 66 formal properties verified via property-based testing

## Status

**Early development.** Infrastructure first, protocol extraction later.

## License

- Code: MIT (see LICENSE-MIT)
- Documentation: CC BY 4.0 (see LICENSE-CC-BY-4.0)

## Attribution

Built on [markspace](https://github.com/opinionated-systems/markspace) by Opinionated Systems, Inc. (MIT License).
