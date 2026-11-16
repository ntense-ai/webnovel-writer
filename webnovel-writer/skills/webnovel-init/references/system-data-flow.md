---
name: system-data-flow-redirect
purpose: Redirect to the authoritative version
---

<context>
This file has moved to a unified location to avoid divergent versions.
</context>

<instructions>

## Authoritative version

`${CLAUDE_PLUGIN_ROOT}/skills/webnovel-query/references/system-data-flow.md`

## Loading

```bash
cat "${CLAUDE_PLUGIN_ROOT}/skills/webnovel-query/references/system-data-flow.md"
```

## Quick reference

### Directory structure
```
project-root/
├── 正文/           # Chapter files
├── 大纲/           # Volume/chapter outlines
├── 设定集/         # Worldbuilding/power systems/character sheets
└── .webnovel/
    ├── state.json          # Authoritative state
    ├── workflow_state.json # Workflow checkpoints
    ├── index.db            # SQLite index
    └── archive/            # Archived data
```

### Key changes in the current structure
- **Dual-Agent architecture**: Context Agent (reads) + Data Agent (writes).
- **No XML tags**: write plain chapter prose; Data Agent AI automatically extracts entities.
- **SQLite storage**: entities/aliases/state_changes moved to index.db.
- **Slim state.json**: keep below 5KB; primarily contains progress/protagonist_state/strand_tracker/disambiguation.

</instructions>
