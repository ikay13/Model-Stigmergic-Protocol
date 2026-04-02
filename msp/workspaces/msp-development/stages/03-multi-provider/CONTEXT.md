# Stage 03: Multi-Provider Orchestration

Build agent:// identity scheme and provider adapters for Claude, Codex, Gemini, Antigravity.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Architecture | ../../../planning/ARCHITECTURE.md | Layer 3 section | Design spec |
| Agent Identity URI | ../../../planning/REFERENCES.md | Rodriguez 2026 | Identity scheme |

## Process

1. Implement agent:// URI scheme
2. Build Claude Code adapter
3. Build provider adapter interface
4. Add second provider (Codex or Gemini)

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Identity module | msp/layer3/identity.py | Python |
| Claude adapter | msp/layer3/adapters/claude.py | Python |
