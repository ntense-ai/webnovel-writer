---
name: webnovel-query
description: Query project settings, characters, power systems, factions, foreshadowing, and related information. Supports urgency analysis and special-ability status queries.
allowed-tools: Read Grep Bash
argument-hint: "[search term, e.g. character name/foreshadowing/cultivation realm]"
---

# Information Query Skill

## Project paths and output language

Use English for generated story content, headings, summaries, reports, and user-facing explanations unless the user explicitly requests another language. Preserve runtime schema keys, enum values, and machine-readable identifiers exactly.

New projects use English-only paths, filenames, schema keys, and enum identifiers. Use `chapters/`, `outlines/`, `settings/`, and `reviews/`. Resolve paths with `python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}"`; resolve individual files with `--path outlines/master-outline.md` or the corresponding English relative path. Pass resolved paths to subagents. This branch targets newly created projects and does not migrate or support old project layouts or schemas. Do not rename, overwrite, or merge existing book content automatically. Story prose and names may contain Unicode characters; that does not change the English project schema.

## Use when

Trigger when the user asks about project-specific story settings, characters, power systems, factions, foreshadowing, special abilities, pacing, or related information.

## Project root guard

```bash
export WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
export SCRIPTS_DIR="${CLAUDE_PLUGIN_ROOT}/scripts"
export SKILL_ROOT="${CLAUDE_PLUGIN_ROOT}/skills/webnovel-query"
export PROJECT_ROOT="$(python "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" where)"
```

- `PROJECT_ROOT` must contain `.webnovel/state.json`.
- **Never** read or write project files under `${CLAUDE_PLUGIN_ROOT}/`.

## Query category → narrowest tool

Identify the query type first, then use the narrowest tool in the table below. Do not load everything by default. Use `memory-contract load-context` only for comprehensive / cross-category queries.

| Query type | Keywords | Narrowest tool |
|---------|--------|---------|
| Historical character state | Character at chapter N / state at a point in time / cultivation realm changes | `knowledge query-entity-state` |
| Entity relationships | Relationships / friends and foes / master and disciple / faction affiliation | `knowledge query-relationships` |
| World rules | Power rules / inviolable setting rules / realm-system constraints | `memory-contract query-rules` |
| Foreshadowing / open loop | Foreshadowing / urgent foreshadowing / unresolved suspense | `memory-contract get-open-loops` |
| Comprehensive / complex | Cross-category, requiring both timeline and long-term memory | `memory-contract load-context` |
| Static settings | Character sheets / power system / worldbuilding / factions / tag formats | `Grep` + `Read` the setting collection |

## Reference loading strategy

Load on demand by query type; identify before loading. Paths: `references/` means the skill-private `skills/webnovel-query/references/`; `../../references/` means shared references.

| Query type | Reference | Actual path |
|---------|-----------|---------|
| Data flow / priority | Data flow specification | `${SKILL_ROOT}/references/system-data-flow.md` |
| Foreshadowing analysis | Foreshadowing analysis | `${SKILL_ROOT}/references/advanced/foreshadowing.md` |
| Pacing analysis | Strand pattern | `${SKILL_ROOT}/../../references/shared/strand-weave-pattern.md` |
| Format queries | Tag specification | `${SKILL_ROOT}/references/tag-specification.md` |

Do not load more than two references at once unless the user's request explicitly spans multiple categories.

## Query procedure

1. **Identify the query type**: match keywords against the “Query category → narrowest tool” table.
2. **Locate pre-writing sources of truth by priority** (pre-writing truth → post-writing truth → projection layer):
   1. `.story-system/MASTER_SETTING.json` - master settings for the book (genre, tone, core prohibitions).
   2. `.story-system/volumes/*.json` - volume-level contracts (volume goals, pacing strategy).
   3. `.story-system/chapters/*.json` - chapter-level contracts (chapter focus, dynamic context).
   4. Latest accepted `.story-system/commits/chapter_XXX.commit.json` - post-writing facts (finalized state of published chapters).
   5. `memory-contract` queries - memory orchestration results (long-term memory, foreshadowing, timeline).
   6. `.webnovel/state.json` / `index.db` - projection layer (fallback / read-model only, analogous to “character sheets” and “chapter lists” in a webnovel management backend).

   **Priority explanation**:
   - Pre-writing sources of truth (1–3): the “outline, settings, and forbidden areas” the author must follow before writing.
   - Post-writing source of truth (4): the “finalized state” of published chapters; must not be tampered with.
   - Projection layer (5–6): “query views” automatically generated from post-writing truth for fast retrieval.

3. **Retrieve with the narrowest tool**: call only the commands needed for the type; do not default to a full `load-context`.

```bash
# Historical character state: an entity's state at a specified chapter
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" knowledge query-entity-state --entity "{entity_id}" --at-chapter {N}

# Entity relationships: all relationships for an entity at a specified chapter
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" knowledge query-relationships --entity "{entity_id}" --at-chapter {N}

# World rules
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" memory-contract query-rules --chapter {chapter_num}

# Foreshadowing / open loop
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" memory-contract get-open-loops

# Comprehensive / complex queries only: use only when both timeline and long-term memory are needed
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" memory-contract load-context --chapter {chapter_num}
```

   For static settings (character sheets / power system / worldbuilding / tag formats), use `Grep` directly to locate line numbers, then `Read` the relevant excerpt; do not go through memory-contract.

4. **Format the output**: use the template below.

## Output format

```markdown
# Query results: {keywords}

## Summary
- **Match type**: {type}
- **Data source**: {actual source of truth used / projection layer}
- **Match count**: X entries

## Details
{structurestructured data，including file paths and line numbers}

## Data consistency check
{state.json differences from static files，omit if unchanged}
```

## Boundaries and failure recovery

- Read-only operation; do not modify any project files.
- If a data source is missing, explicitly tell the user which file is missing.
- If no matches are found, return empty results and suggest checking the scope.
- If `.story-system/` contracts and accepted commits are missing, explicitly state that this query has degraded to legacy fallback.
