# System Architecture and Module Design

## Core Principles

### Sources of Truth

- Prewrite source of truth: `.story-system/MASTER_SETTING.json`, `volumes/`, `chapters/`, `reviews/`
- Postwrite source of truth: accepted `CHAPTER_COMMIT`
- `.webnovel/state.json`, `index.db`, `summaries/`, `memory_scratchpad.json`: projections / read models only
- `references/genre-profiles.md`: fallback-only

### Three Anti-Hallucination Laws

| Law | Description | Enforcement |
|------|------|----------|
| **The outline is law** | Follow the outline; do not improvise beyond it | Context Agent must load the chapter outline |
| **Settings are physics** | Respect established settings; avoid contradictions | Reviewer Agent includes consistency checks |
| **Inventions must be identified** | New entities must be registered and managed | Data Agent automatically extracts and disambiguates them |

### Strand Weave Pacing System

| Strand | Meaning | Ideal share | Description |
|--------|------|----------|------|
| **Quest** | Main plot | 60% | Advances the central conflict |
| **Fire** | Relationship arc | 20% | Develops character relationships |
| **Constellation** | World expansion | 20% | Background, factions, and setting |

Pacing limits:

- No more than 5 consecutive Quest chapters
- No Fire gap longer than 10 chapters
- No Constellation gap longer than 15 chapters

## Overall Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                      Claude Code                            │
├─────────────────────────────────────────────────────────────┤
│  Skills (7):                                                │
│    init / plan / write / review / query / learn / dashboard  │
├─────────────────────────────────────────────────────────────┤
│  Agents (3):                                                │
│    Context Agent / Data Agent / Reviewer (six dimensions)    │
├─────────────────────────────────────────────────────────────┤
│  Data Layer:                                                │
│    state.json / index.db (SQLite) / vectors.db                │
├─────────────────────────────────────────────────────────────┤
│  Story System:                                              │
│    .story-system/ (contracts, commits, events)                │
└─────────────────────────────────────────────────────────────┘
```

## Agent Responsibilities

### Context Agent (Read)

- File: `agents/context-agent.md`
- Responsibility: Build a writing brief before drafting, supplying chapter context, constraints, and reader-retention strategies.

### Data Agent (Write)

- File: `agents/data-agent.md`
- Responsibility: Extract commit artifacts such as `accepted_events / state_deltas / entity_deltas / summary_text` from the prose and pass them to `chapter-commit`, which drives projection writers to update `state.json`, `index.db`, summaries, and long-term memory.

### Reviewer (Review)

- File: `agents/reviewer.md`
- Responsibility: Review chapter quality across these six dimensions:

| Review dimension | Focus |
|----------|----------|
| High-point Checker | Density and quality of satisfying payoffs |
| Consistency Checker | Setting consistency (power levels, locations, timeline) |
| Pacing Checker | Strand proportions and gaps |
| OOC Checker | Whether character behavior deviates from established characterization |
| Continuity Checker | Scene and narrative continuity |
| Reader-pull Checker | Hook strength, expectation management, and reader retention |

## Story System (Contract-Driven Architecture)

Story System uses `.story-system/` as an independent runtime surface and consists of:

- **Contract seeds**: `MASTER_SETTING.json` + chapter contracts + anti-pattern configuration
- **Contract-first runtime**: Volume contracts (`volumes/`) + review contracts (`reviews/`) + prewrite validation
- **Chapter commit chain**: `commits/chapter_XXX.commit.json` + state/index/summary/memory projections
- **Event audit chain**: `events/chapter_XXX.events.json` + revision proposals + override ledger

The current default is contract-first + commit-first: `.story-system/` is the main pipeline source of truth, legacy `.webnovel/*` is downgraded to projections / read models, and `preflight` and the dashboard expose runtime health.

Core pipeline:

```text
story-system --persist
    -> Write contract seeds (MASTER_SETTING.json, etc.)
story-system --emit-runtime-contracts --chapter N
    -> Generate runtime contracts and validate before writing
chapter-commit --chapter N
    -> Submit an accepted commit and execute projection writes
story-events --chapter N / --health
    -> Event audit and health checks
preflight / dashboard
    -> Story runtime health / fallback status / latest commit status
```

The event audit chain does not introduce a second projection loop. Event routing only activates writers declaratively;
execution still enters through `ChapterCommitService.apply_projections()`.

For the detailed design, see `docs/archive/architecture/story-system-phase5.md`.
