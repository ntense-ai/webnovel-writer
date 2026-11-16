---
name: webnovel-learn
description: Extract successful writing patterns from the current conversation and save them to project_memory.json
allowed-tools: Read Bash
argument-hint: "[writing lesson to remember]"
---

# /webnovel-learn

## Project paths and output language

Use English for generated story content, headings, summaries, reports, and user-facing explanations unless the user explicitly requests another language. Preserve runtime schema keys, enum values, and machine-readable identifiers exactly.

New projects use English-only paths, filenames, schema keys, and enum identifiers. Use `chapters/`, `outlines/`, `settings/`, and `reviews/`. Resolve paths with `python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}"`; resolve individual files with `--path outlines/master-outline.md` or the corresponding English relative path. Pass resolved paths to subagents. This branch targets newly created projects and does not migrate or support old project layouts or schemas. Do not rename, overwrite, or merge existing book content automatically. Story prose and names may contain Unicode characters; that does not change the English project schema.

## Project Root Guard (verify first)

- Must run in the project root (`.webnovel/state.json` must exist).
- Resolve the project root through the unified entry point to avoid writing to the wrong directory:

```bash
export WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
export SCRIPTS_DIR="${CLAUDE_PLUGIN_ROOT:?}/scripts"
export PROJECT_ROOT="$(python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" where)"
```

## Goal

Extract reusable writing patterns (hooks, pacing, dialogue, micro-payoffs, etc.) and append them to `.webnovel/project_memory.json`.

## Procedure

1. Read `progress.current_chapter` from `"$PROJECT_ROOT/.webnovel/state.json"` as the current chapter number; if missing, use `source_chapter: null` without blocking execution.
2. Parse the user input (the lesson text after `/webnovel-learn`; if empty, use writing approaches the user approved in this conversation), and classify `pattern_type` (hook/pacing/dialogue/payoff/emotion/format/other; use `other` if unclassifiable).
3. Call `project-memory add-pattern` to save it; do not handwrite or concatenate JSON:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" project-memory add-pattern \
  --pattern-type "{pattern_type}" \
  --description "{full user description or refined description}" \
  --category "{category，optional}" \
  --importance "{high|medium|low}"
```

## Constraints

- Append only; do not delete existing records.
- Scan existing `patterns` before appending; if `pattern_type` + `description` are exactly identical, skip and tell the user. Do not deduplicate partial similarities.
- Do not use `Write` or manually edit `.webnovel/project_memory.json`.

## Success criteria

- `project_memory.json` exists and is valid; the new pattern has been appended to the `patterns` array.
- Output includes `status: success` and the complete `learned` object.

## Failure recovery

| Failure | Recovery |
|------|---------|
| `project_memory.json` does not exist | The script automatically initializes `{"patterns": []}` and continues |
| JSON parsing fails | Do not write corrupt data; tell the user the file is damaged and recommend manual repair |
| `state.json` is missing, preventing chapter-number lookup | Use `source_chapter: null` without blocking execution |
