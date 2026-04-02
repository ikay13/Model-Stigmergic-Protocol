# {{WORKSPACE_NAME}}

{{WORKSPACE_DESCRIPTION}}

## Folder Map

```
{{WORKSPACE_NAME}}/
├── CLAUDE.md              (Layer 0: workspace identity — always loaded)
├── CONTEXT.md             (Layer 1: task routing)
├── stages/
│   ├── 01-{{STAGE_NAME}}/
│   │   ├── CONTEXT.md     (Layer 2: stage contract)
│   │   ├── references/    (Layer 3: stable reference material)
│   │   └── output/        (Layer 4: working artifacts)
└── _config/               (Layer 3: cross-stage configuration)
```

## Routing

| You want to... | Go to |
|----------------|-------|
| Start stage 01 | `stages/01-{{STAGE_NAME}}/CONTEXT.md` |

## Triggers

| Keyword | Action |
|---------|--------|
| `setup` | Onboarding questionnaire |
| `status` | Show pipeline completion |
