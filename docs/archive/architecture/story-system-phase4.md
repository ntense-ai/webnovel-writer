# Story System Phase 4

## Goal

Phase 4 promotes Phase 3’s `accepted_events` to the official event mainline and expands
`override_contracts` into a unified override ledger.

This phase introduces two stable pipelines:

1. `CHAPTER_COMMIT.accepted_events -> .story-system/events/*.events.json`
2. `world_rule_broken -> amend_proposal -> override_contracts`

## Artifacts

Execution produces these core files or tables:

- `.story-system/events/chapter_XXX.events.json`
- `.webnovel/index.db.story_events`
- `.webnovel/index.db.override_contracts.record_type=*`

`story_events` is the canonical audit mirror. `override_contracts` retains the legacy
Override Contract / debt pipeline and adds:

- `soft_deviation`
- `contract_override`
- `amend_proposal`

## Execution Flow

```text
review / fulfillment / disambiguation / extraction
                │
                ▼
         CHAPTER_COMMIT.accepted
                │
                ├── apply_projections()
                │     ├── state/index/summary/memory
                │     └── EventProjectionRouter selects the writers to activate
                │
                ├── EventLogStore.write_events()
                │     ├── JSON files
                │     └── SQLite story_events mirror
                │
                └── AmendProposalTrigger.check()
                      └── persist_amend_proposals() -> override_contracts
```

## CLI

The unified entry point remains `webnovel.py`:

```bash
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" story-system "broken-engagement-fantasy" --persist
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" story-system "broken-engagement-fantasy" --emit-runtime-contracts --chapter 12
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" chapter-commit --chapter 12 --review-result .webnovel/tmp/review.json --fulfillment-result .webnovel/tmp/fulfillment.json --disambiguation-result .webnovel/tmp/disambiguation.json --extraction-result .webnovel/tmp/extraction.json
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" story-events --chapter 12
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" story-events --health
```

## Minimum Operational Checks

- After `story-system --persist`, `MASTER_SETTING.json` should exist.
- After `story-system --emit-runtime-contracts --chapter N`, `volume_XXX.json`
  and `chapter_XXX.review.json` should exist.
- After `chapter-commit` is accepted, `chapter_XXX.commit.json` should exist.
- `story-events --health` should return `sqlite_rows` and `event_files`.

## Current Boundaries

- Event routing remains centrally orchestrated by `ChapterCommitService.apply_projections()`.
- Phase 4 does not introduce a second independent projection loop.
- Downgrading the legacy pipeline and completing the switchover are deferred to Phase 5.
