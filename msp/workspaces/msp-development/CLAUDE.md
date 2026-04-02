# MSP Development Workspace

Build the Model Stigmergic Protocol infrastructure layer by layer.

## Folder Map

```
msp-development/
├── CLAUDE.md                          (Layer 0: always loaded)
├── CONTEXT.md                         (Layer 1: task routing)
├── stages/
│   ├── 01-coordination-core/          (markspace + signal field + ECS)
│   ├── 02-context-layer/              (filesystem context engineering)
│   ├── 03-multi-provider/             (agent:// identity + adapters)
│   └── 04-knowledge-layer/            (Obsidian + memboot integration)
└── _config/
    └── architecture-ref.md            (pointer to planning/ARCHITECTURE.md)
```

## Routing

| You want to... | Go to |
|----------------|-------|
| Work on coordination core | `stages/01-coordination-core/CONTEXT.md` |
| Work on context layer (current) | `stages/02-context-layer/CONTEXT.md` |
| Work on multi-provider | `stages/03-multi-provider/CONTEXT.md` |
| Work on knowledge layer | `stages/04-knowledge-layer/CONTEXT.md` |

## Triggers

| Keyword | Action |
|---------|--------|
| `status` | Show pipeline completion across all 4 stages |
