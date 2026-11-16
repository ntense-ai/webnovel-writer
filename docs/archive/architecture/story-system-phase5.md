# Story System Phase 5

## Core Conclusions

- Pre-writing source of truth: `.story-system/MASTER_SETTING.json`, `volumes/*.json`, `chapters/*.json`, and `reviews/*.review.json`
- Post-writing source of truth: accepted `CHAPTER_COMMIT`
- `.webnovel/state.json`, `index.db`, `summaries/`, and `memory_scratchpad.json`: projections / read-models
- `references/genre-profiles.md`: fallback-only

## Default Pipeline

```text
story-system --persist/--emit-runtime-contracts
    -> generate MASTER / VOLUME / CHAPTER / REVIEW contracts
context / query / write / review
    -> read the contract mainline by default
chapter-commit --chapter N
    -> accepted CHAPTER_COMMIT
    -> state / index / summary / memory projection writers
preflight + dashboard
    -> expose story runtime health / fallback status / latest commit status
```

## Runtime Priority

1. Story Contracts
2. Latest accepted `CHAPTER_COMMIT`
3. `.webnovel/*` read-models
4. Legacy fallbacks such as `genre-profiles.md`

## Phase 5 Implementation Results

- `ContextManager`, `memory_contract_adapter`, and `extract_chapter_context` now default to contract-first + commit-first.
- `webnovel-write` / `webnovel-query` / `webnovel-review` / `webnovel-plan` and `context-agent` / `data-agent` now describe the new mainline.
- `preflight` and the dashboard directly expose `story_runtime` / `story-runtime/health`.
- The legacy state-first mental model is downgraded to a compatibility layer and no longer presented as the mainline.

## Operational Implications

- If `.webnovel/state.json` disagrees with `.story-system/commits/`, inspect the commit chain and projection status first.
- Nonempty `fallback_sources` means the mainline is incomplete. The system can still run in compatibility mode, but is not fully-mainline-ready.
- When troubleshooting post-writing issues, inspect these in order:
  1. `.story-system/commits/chapter_XXX.commit.json`
  2. `projection_status`
  3. `story-events --health`
  4. `.webnovel/*` projection results
