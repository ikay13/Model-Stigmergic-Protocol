# Stage 02: Context Layer

Build the ICM-inspired filesystem context hierarchy — the `msp/layer2/` Python module.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Architecture | ../../../planning/ARCHITECTURE.md | Layer 2 section | Design spec |
| ICM conventions | ../../../../workshop/candidates/Interpreted-Context-Methdology/_core/CONVENTIONS.md | Full file | Patterns to follow |
| markspace spec | ../../../docs/spec.md | Section 9.10 Token Budgets | Budget integration |

## Process

1. Implement `msp/layer2/tier.py` (L0/L1/L2 tiered content)
2. Implement `msp/layer2/stage.py` (stage contract parsing)
3. Implement `msp/layer2/workspace.py` (workspace navigation)
4. Implement `msp/layer2/context_loader.py` (budget-aware loading)
5. Create workspace template in `msp/templates/workspace/`
6. Create MSP development workspace in `msp/workspaces/msp-development/`
7. Run full test suite — verify tests pass

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Layer 2 module | msp/layer2/ | Python package |
| Workspace template | msp/templates/workspace/ | Markdown files |
| MSP workspace | msp/workspaces/msp-development/ | ICM workspace |
| Tests | tests/layer2/ | pytest |

## Audit

| Check | Pass Condition |
|-------|---------------|
| All tests pass | pytest tests/ shows 0 failures |
| CONTEXT.md files under 80 lines | wc -l on each CONTEXT.md is 80 or less |
| Token budget respected | ContextLoader.load(budget=8000).total_tokens() <= 8000 |
| No circular references | Stage folders only reference parent _config/ or sibling output/ |
