# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.3-beta] - 2026-04-03

### Added

**Layer 1 — Coordination Core**
- `msp/layer1` namespace re-exporting the markspace public API as the MSP coordination foundation

**Layer 2 — Context Engineering Infrastructure**
- L0/L1/L2 tiered content loading with configurable token budgets
- ICM stage contract parsing and workspace navigator
- Budget-aware `ContextLoader` with `extra_paths` support for cross-layer injection
- `TOKENS_PER_CHAR` constant extracted to `_constants.py` for shared use
- MSP development workspace template

**Layer 3 — Multi-Provider Orchestration**
- `AgentURI` identity scheme for provider-agnostic agent addressing
- `ProviderAdapter` interface for pluggable LLM backends
- `ClaudeAdapter` backed by the markspace `LLMClient`
- `CodexAdapter` and `GeminiAdapter` via subprocess (`codex exec`, `gemini --prompt`)
- `AgentSession` — Layer 1 + 2 + 3 integration glue: loads context via `ContextLoader`, writes marks via markspace `Agent`
- `PAUL` multi-provider task routing with `AgentSession`
- `PSMM` session import — injects prior session memory at agent start

**Layer 4 — Knowledge Integration**
- `VaultSync` bidirectional Obsidian vault sync
- `import_tagged` — vault pages → marks pipeline
- `export_observations` — marks → vault pipeline
- YAML frontmatter parser and tag helper utilities
- `pyyaml>=6.0` dependency

**Layer 5 — Orchestration Ecosystem**
- `BASE` — `WorkspaceState` CRUD, drift detection, and PSMM integration
- `PAUL` full — Plan/Apply/Unify loop with lifecycle marks, qualify loop, diagnostic failure routing, scope enforcement
- `CARL` — intent detection, JIT rule injection, 9 domain rule sets, stale mark filtering with `max_age` param
- `SKILLSMITH` — 7-file skill taxonomy, compliance audit, scaffold generation
- `SEED` — type-first ideation, `PLANNING.md` generation, PAUL handoff
- `AEGIS` — 6-phase audit, 12 personas, 14-domain static codebase analysis pattern corpus
- CLI entrypoints: `seed`, `paul plan`, `aegis` subcommands
- Full public API exposed from top-level `msp` package
- Integration validation gate: BASE + PAUL + CARL + SKILLSMITH spine test
- Hypothesis property test: drift detection never false-negatives

**Documentation**
- Comprehensive README covering 5-layer architecture, attributions, biological inspiration, and CLI usage
- Hero image (Gemini-generated)
- Layer 5 design spec and implementation plan

### Fixed

- L1 truncation boundary bug in context loader
- `BASE` quality fixes: `scope` field, `agent` required, `detect_drift` test coverage
- `export_observations` now uses `isinstance` instead of `type().__name__` for type checking

### Changed

- Python requirement relaxed to `>=3.10` for Jetson Orin compatibility (was `>=3.11`)

[Unreleased]: https://github.com/ikay13/Model-Stigmergic-Protocol/compare/v0.1.3-beta...HEAD
[0.1.3-beta]: https://github.com/ikay13/Model-Stigmergic-Protocol/releases/tag/v0.1.3-beta
