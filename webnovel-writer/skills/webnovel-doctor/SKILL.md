---
name: webnovel-doctor
description: Run a read-only health check/diagnosis of a webnovel project (/webnovel-doctor), checking directories, files, JSON, SQLite, RAG configuration, dependencies, and Dashboard build artifacts for completeness.
version: 0.1.0
allowed-tools: Read Bash
argument-hint: "[--chapter N] [--deep]"
---

# Webnovel Doctor

## Project paths and output language

Use English for generated story content, headings, summaries, reports, and user-facing explanations unless the user explicitly requests another language. Preserve runtime schema keys, enum values, and machine-readable identifiers exactly.

New projects use English-only paths, filenames, schema keys, and enum identifiers. Use `chapters/`, `outlines/`, `settings/`, and `reviews/`. Resolve paths with `python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}"`; resolve individual files with `--path outlines/master-outline.md` or the corresponding English relative path. Pass resolved paths to subagents. This branch targets newly created projects and does not migrate or support old project layouts or schemas. Do not rename, overwrite, or merge existing book content automatically. Story prose and names may contain Unicode characters; that does not change the English project schema.

## Goal

Diagnose the current book project without modifying it: verify that the directories, files, JSON, SQLite, RAG configuration, Python dependencies, and Dashboard build artifacts expected at its current stage are complete.

## Principles

1. Read-only diagnosis: do not write project files, automatically repair anything, install dependencies, or start the Dashboard.
2. Run `project-status` first for a short status report, then `doctor` for phase-aware checks.
3. Consistently use `python -X utf8` to support Unicode story content consistently.
4. Explain the impact of missing items and suggested repairs according to the phase inferred by the runtime. Do not check a freshly initialized project as though it already had multiple written chapters.

## Execution

Prepare paths:

```bash
export WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
export SCRIPTS_DIR="${CLAUDE_PLUGIN_ROOT:?}/scripts"
```

Short status:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" project-status --format summary
```

Standard health check:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" doctor --format text
```

Add `--chapter {chapter_num}` to specify a chapter and `--deep` for a deep health check.

## Output format

Report: the current `phase` and `target_chapter`, whether blockers exist, paths of missing or abnormal files, missing RAG / Python / Dashboard configuration, and the impact and recommended repair action for each issue.

Do not perform actual repairs, display API keys, or ask the user to paste them.
