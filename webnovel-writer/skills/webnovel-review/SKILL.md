---
name: webnovel-review
description: Assess chapter quality with a review Agent, generate a report, and persist review metrics.
allowed-tools: Read Grep Write Edit Bash Agent AskUserQuestion
argument-hint: "[chapter number or range, e.g. 5 or 1-5]"
---

# Quality Review Skill

## Project paths and output language

Use English for generated story content, headings, summaries, reports, and user-facing explanations unless the user explicitly requests another language. Preserve runtime schema keys, enum values, and machine-readable identifiers exactly.

New projects use English-only paths, filenames, schema keys, and enum identifiers. Use `chapters/`, `outlines/`, `settings/`, and `reviews/`. Resolve paths with `python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}"`; resolve individual files with `--path outlines/master-outline.md` or the corresponding English relative path. Pass resolved paths to subagents. This branch targets newly created projects and does not migrate or support old project layouts or schemas. Do not rename, overwrite, or merge existing book content automatically. Story prose and names may contain Unicode characters; that does not change the English project schema.

## Goals

- Resolve the actual book project root and dispatch the unified `reviewer` to perform a structured review and persist it.
- Main-pipeline facts come from `.story-system/reviews/chapter_{NNN}.review.json` and the latest accepted `CHAPTER_COMMIT`; `.webnovel/state.json` is only a compatibility projection.
- Submit issues with `blocking=true` to the user for a decision.

## Red lines

- Must call `reviewer` through the `Agent` tool. The main flow must not fabricate conclusions or replace subagent output with a verbal summary.
- reviewer returns strict JSON only; the main flow writes the returned value to `${PROJECT_ROOT}/.webnovel/tmp/review_results.json`, after which `review-pipeline` overwrites it with a standard review_result artifact.
- Reports and metrics are produced only by `review-pipeline --save-metrics`; the main flow must not fabricate `overall_score`.
- Invalid project root / missing `.webnovel/state.json` / missing chapter text to review → block.

## Procedure

### Step 1: Resolve the project root

```bash
export WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
export SCRIPTS_DIR="${CLAUDE_PLUGIN_ROOT}/scripts"
export PROJECT_ROOT="$(python "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" where)"
export REVIEWS_DIR="$(python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}" --directory reviews)"
```

`PROJECT_ROOT` must contain `.webnovel/state.json`; otherwise block.

### Step 2: Refresh runtime contracts if the target chapter lacks them

If the target chapter lacks runtime contracts, first refresh them using the actual chapter goal from the detailed outline (`CHAPTER_GOAL` must not contain placeholder text such as `{chapter-outlinegoal}` / `Chapter Nchapter-outlinegoal`):

```bash
GENRE="$(python -X utf8 -c "import json; s=json.load(open('${PROJECT_ROOT}/.webnovel/state.json',encoding='utf-8')); pi=s.get('project_info',{}); print(pi.get('genre') or s.get('project',{}).get('genre',''))")"

python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  story-system "${CHAPTER_GOAL}" --genre "${GENRE}" --chapter {chapter_num} --persist --emit-runtime-contracts --format both
```

### Step 3: Load references on demand

| Trigger | Reference |
|---------|-----------|
| always | `../../references/shared/core-constraints.md` |
| always | `../../references/review-schema.md` |
| Review involves gratification beats or hooks | `../../references/shared/cool-points-guide.md` |
| Review involves interwoven storylines | `../../references/shared/strand-weave-pattern.md` |
| A blocking issue requires a user decision (Step 8) | `../../references/review/blocking-override-guidelines.md` |

### Step 4: Load projection state and chapter text to review

```bash
cat "${PROJECT_ROOT}/.webnovel/state.json"
```

Confirm the current chapter number and corresponding chapter file; block immediately if the chapter text or compatibility state file is missing.

### Step 5: Call the unified review Agent

Must call `reviewer` through the `Agent` tool. The reviewer includes its own review methods and dimension criteria; this Skill does not repeat them.

```text
Use the Agent tool to run `webnovel-writer:reviewer`.

Prompt: chapter={chapter_num}; chapter_file={chapter_file}; project_root=${PROJECT_ROOT}; scripts_dir=${SCRIPTS_DIR}. Output strictly reviewer-schema JSON; do not score or provide a verbal summary.
```

After reviewer returns, the main flow writes the strict JSON to `${PROJECT_ROOT}/.webnovel/tmp/review_results.json` (reviewer does not have Write and does not write this artifact). `review-pipeline` must overwrite the same path with a standard review_result artifact (including `blocking_count`).

After the call, the main flow must record a `SubagentRun` summary (for the final report only):

```json
{
  "name": "reviewer",
  "user_label": "Writing check",
  "status": "completed | partial | failed | skipped",
  "problems": [],
  "auto_handled": [],
  "needs_user_action": false,
  "duration_ms": 0,
  "outputs": []
}
```

A skipped or failed reviewer, incomplete output, empty chapter text, skipped dimensions, blocking issues, or abnormal duration must be recorded in `problems` / `auto_handled` and must not be silently omitted from the final report.

### Step 6: Generate the report and persist to the database

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" review-pipeline \
  --chapter {chapter_num} \
  --review-results "${PROJECT_ROOT}/.webnovel/tmp/review_results.json" \
  --metrics-out "${PROJECT_ROOT}/.webnovel/tmp/review_metrics.json" \
  --report-file "$(python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}" --path "reviews/chapter-{chapter_num}-review.md")" \
  --save-metrics
```

`review-pipeline --save-metrics` generates the report, outputs `review_metrics.json`, and writes the `review_metrics` table. Blocking decisions are based on `blocking=true` in review_results.

### Step 7: Write the compatibility review record

```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" update-state -- --add-review "{chapter_num}-{chapter_num}" "$(python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}" --path "reviews/chapter-{chapter_num}-review.md")"
```

This is a compatibility projection / read model, not the post-writing source of truth.

### Step 8: Handle blockers

If any issue has `blocking=true`, use `AskUserQuestion` for the user's decision:

- Fix now: output a rework checklist and make minimal changes only with explicit user authorization.
- Save the report only and handle later: retain the report and metrics records, then end the workflow.

## Success criteria

1. The actual book project root has been resolved.
2. `reviewer` has returned structured issue JSON, saved to `.webnovel/tmp/review_results.json`.
3. The review report has been generated, `review_metrics` written to `index.db`, and `review_metrics.json` output.
4. The review record has been written to the `.webnovel/state.json` compatibility projection.
5. If blocking issues exist, the user has explicitly selected a handling strategy.

## Author-friendly progress and recovery contract

Before review begins, explain its stages: locate chapter text -> refresh missing contracts -> writing check -> generate report and metrics -> resolve blocking decisions. Use author-friendly language for progress updates; do not output raw JSON, tracebacks, or long command logs. Write technical details to `.webnovel/logs/run_last.log`:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" run-log \
  --event review-progress \
  --payload-json "{\"stage\": \"review\", \"chapter\": {chapter_num}}" \
  --format text
```

Limit each progress update to two lines and describe only the current action and its impact, e.g. “Generating the review report: blocking issues and the most valuable revision suggestions will appear at the top.” Minimize interruptions: do not ask when there are no blockers; ask only for a blocking issue, missing chapter text, or when the user asks whether to revise immediately.

When a user decision is needed, offer finite choices and explain their consequences, e.g. fix now / save report and handle later / abandon this review. When stuck, explain the blocker, completed work, and recovery advice, e.g. “reviewer results have been saved, but metrics could not be persisted; rerunning `/webnovel-review {chapter_num}` will resume from report persistence.”

Mention `.webnovel/logs/run_last.log` in the final report only for unrecoverable failures; otherwise retain logs without bothering the author. Always call the author-report helper when finishing:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" user-report \
  --stage review \
  --chapter {chapter_num} \
  --format text
```

## Author-friendly final report contract

The final reply must address the author, without raw JSON, tracebacks, or long command logs. Use the fixed three-part format, beginning with one overall-status sentence:

```text
Overall status: Completed / Partially completed / Needs your attention / Not completed.

1. Files produced and completion status
- ...

2. Issues and unusually long steps encountered
- Automatically handled: ...
- Suggested for confirmation: ...
- Must address: ...

3. Recommended next steps
- ...
```

Must report:
- The review report file.
- `.webnovel/tmp/review_results.json`.
- `.webnovel/tmp/review_metrics.json`.
- Whether `review_metrics` was persisted to the database.
- The number of blocking issues.
- The status of the user's decision.
- If there are no blockers, explicitly state that writing can continue.

Status rules:
- If blocking issues exist and the user has not selected a handling strategy, final status is “Needs your attention”.
- If only the report is saved for later handling, final status is “Needs your attention” or “Partially completed”.
- If reviewer was skipped, failed, or returned incomplete output, final status must not be “Completed”.

Issue categories:
- Automatically handled: regenerating a report, overwriting this run's old review intermediate files, successfully backfilling metrics.
- Suggested for confirmation: non-blocking, high-value revision suggestions; naming or setting details worth a look.
- Must address: blocking issues, missing chapter text, incomplete reviewer output, failed metrics persistence.

Next-step suggestions must use task-oriented language plus copyable commands, for example:

```text
- No review blockers; continue writing the next chapter:
  /webnovel-write {next_chapter}
```

Do not report token statistics; for troubleshooting, provide only the log path or suggest `/webnovel-doctor`.
