# Review Output Schema (v6)

> **Primary skills**: `webnovel-write` Step 3, `webnovel-review` Step 4
> **Content layer**: Workflow gate / schema definition
> **Key principle**: The reviewer's JSON output is the sole source of truth for review; `review-pipeline` persists reports and metrics; the main skill must not fabricate `overall_score`.

Unified review-agent output format. Replaces the scoring system in the former checker-output-schema.md.

## Core Changes

- **No overall score**: Output structured issues instead of overall_score.
- **blocking semantics**: Replaces timeline_gate; severity=critical blocks by default.
- **Single agent**: One reviewer agent replaces the six separate checkers.

## Issue Schema

| Field | Type | Required | Description |
|------|------|------|------|
| severity | critical/high/medium/low | ✅ | Severity |
| category | continuity/setting/character/timeline/ai_flavor/logic/pacing/other | ✅ | Issue category |
| location | string | ✅ | Location (e.g. "paragraph 3") |
| description | string | ✅ | Issue description |
| evidence | string | ❌ | Source quotation or comparison against memory |
| fix_hint | string | ❌ | Suggested fix |
| blocking | bool | ❌ | Whether the issue blocks progress (true by default for critical) |

## Blocking Rules

- Any issue with `blocking=true` → Step 4 must not begin.
- `severity=critical` automatically means `blocking=true`.
- For other severities, the review agent judges according to context.

## Persisting Metrics

Save the unified review agent's raw output as `review_results.json`, retaining the complete `issues` list.

Then `review-pipeline` generates `review_metrics.json` for insertion into `index.db.review_metrics`.
The file contains two kinds of information:

- **Database-compatible fields**:
  - `start_chapter`
  - `end_chapter`
  - `overall_score` (compatibility score derived from issue severities)
  - `dimension_scores`
  - `severity_counts`
  - `critical_issues`
  - `report_file`
  - `notes`
- **v6 observability fields**:
  - `chapter`
  - `issues_count`
  - `blocking_count`
  - `categories`
  - `timestamp`

Notes:
- The `review_metrics` table retains the compatible schema consumed by the existing dashboard / trend / context features.
- `overall_score` is only for trend observation and sorting; it does not replace the raw issue list.
- Gate decisions remain based on `blocking=true` and individual issue details.
