# Command Reference

## Skill Commands (in Claude Code)

### `/webnovel-init`

Initialize a novel project, generating its directory structure, setting templates, and state files.

Outputs:

- `.webnovel/state.json` (runtime state)
- `settings/` (worldbuilding, power system, protagonist profile, special-ability design, antagonist design, etc.)
- `outlines/master-outline.md`、`outlines/payoff-plan.md`
- `.env.example` (RAG configuration template)

### `/webnovel-plan [volume]`

Generate volume-level plans and chapter outlines.

```bash
/webnovel-plan 1
/webnovel-plan 2-3
```

### `/webnovel-write [chapter]`

Run the complete chapter-writing workflow (`context-agent` researches and creates the writing brief → draft from the brief → review → polish → persist data).

```bash
/webnovel-write 1
/webnovel-write 45
```

### `/webnovel-review [range]`

Review existing chapters across multiple quality dimensions.

```bash
/webnovel-review 1-5
/webnovel-review 45
```

### `/webnovel-query [keyword]`

Query runtime information such as characters, foreshadowing, pacing, and state.

```bash
/webnovel-query 萧炎
/webnovel-query 伏笔
```

### `/webnovel-learn [content]`

Extract reusable writing patterns from the current conversation or user input and save them to project memory.

```bash
/webnovel-learn "The crisis hook in this chapter was highly effective and maximized suspense"
```

Outputs:`.webnovel/project_memory.json`

### `/webnovel-dashboard`

Launch the read-only visual dashboard to inspect project status, entity relationships, chapters, and outlines.

```bash
/webnovel-dashboard
```

Notes:

- Read-only by default; does not modify project files
- Frontend build artifacts ship with the plugin; no local `npm build` is required

### `/webnovel-doctor [--chapter N] [--deep]`

Run a read-only health check on the current novel project, inspecting stage-appropriate files, JSON, SQLite, RAG configuration, Python dependencies, and Dashboard artifacts, and report impact and suggested fixes.

```bash
/webnovel-doctor
/webnovel-doctor --chapter 12
/webnovel-doctor --deep
```

Notes:

- Does not write to the project, install dependencies, or start services
- Determines the current project stage first, avoiding false alarms from applying finished-project requirements immediately after initialization

## Unified CLI (Command-Line Usage)

All CLI commands use `webnovel.py` as their entry point:

```bash
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" <subcommand> [arguments]
```

### Author-Friendly Runtime Experience

`/webnovel-init`, `/webnovel-plan`, `/webnovel-write`, and `/webnovel-review` all produce a standardized final report. Instead of raw JSON, tracebacks, or lengthy command logs, it starts with a one-sentence overall status, followed by three sections: generated files and completion status, problems and unusually slow steps, and recommended next steps.

There are four overall statuses:

- **Completed**: Target outputs and key validations all passed.
- **Partially completed**: Main outputs are preserved, but some items were skipped, handled automatically, or remain pending confirmation.
- **Action required**: The system stopped at a safe point and needs the author to decide creative direction, resolve factual trade-offs, approve file overwrites, or address blocking issues.
- **Not completed**: Key outputs were not reliably generated; rerun or investigate as recommended in the report.

Long workflows show only a few progress messages explaining the current stage and expected outputs. Idempotent operations such as retrying projections or re-emitting missing contracts do not interrupt the author, but appear in the final report. When a primary command is repeated, the system checks reliable checkpoints first. The initial resume implementation focuses on `/webnovel-write`, continuing from the failure point where possible rather than rewriting reliably completed prose, reviews, commits, or backups.

## Story System Main Pipeline

Recommended execution order:

1. Generate contracts

```bash
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" story-system "玄幻退婚流" --chapter 12 --persist --emit-runtime-contracts --format both
```

2. Commit the chapter

```bash
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" chapter-commit \
  --chapter 12 \
  --review-result ".webnovel/tmp/review_results.json" \
  --fulfillment-result ".webnovel/tmp/fulfillment_result.json" \
  --disambiguation-result ".webnovel/tmp/disambiguation_result.json" \
  --extraction-result ".webnovel/tmp/extraction_result.json"
```

3. Check main-pipeline health

```bash
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" preflight --format json
```

Here, `.story-system/` is the main pipeline source of truth, and `.webnovel/*` contains projections/read models.

### Common Utility Subcommands

| Subcommand | Description |
|--------|------|
| `where` | Print the resolved project root |
| `preflight` | Validate the CLI environment, script paths, and project-root availability |
| `project-status` | Output a brief machine-readable status (phase, target chapter, next step), without replacing the existing `status` command |
| `doctor` | Stage-aware project health check (directories, files, DB, RAG, dependencies, Dashboard) |
| `write-gate` | Validate natural chapter-writing boundaries (`prewrite` / `precommit` / `postcommit`) |
| `projections` | Retry or replay projections from existing commits |
| `user-report` | Render an author-friendly final report in text/json |
| `run-ledger` | Record writing-step states or generate checkpoint-resume guidance for `/webnovel-write` |
| `run-log` | Write sanitized runtime logs to `.webnovel/logs/run_last.log` |
| `use <path>` | Bind the book project used by the current workspace |

Examples:

```bash
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" user-report --stage write --chapter 12 --format text
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" run-ledger write-resume --chapter 12 --format text
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" run-log --event write_failed --payload-json "{\"chapter\":12,\"reason\":\"projection timeout\"}"
```

### Data Module Subcommands

| Subcommand | Description |
|--------|------|
| `index` | Index management (`process-chapter`, `stats`, etc.) |
| `state` | State management |
| `rag` | RAG vector indexing (`index-chapter`, `stats`, etc.) |
| `entity` | Entity linking |
| `context` | Context management |
| `style` | Style sampling |
| `migrate` | state.json → SQLite migration |

### Operations Subcommands

| Subcommand | Description |
|--------|------|
| `status` | Overall writing-health report (`--focus all` / `--focus urgency`), still forwarded to `status_reporter.py` |
| `update-state` | Manually update state |
| `backup` | Backup management |
| `archive` | Archive management |
| `extract-context` | Extract chapter context (`--chapter N --format json`) |

### Long-Term Memory Subcommands

| Subcommand | Description |
|--------|------|
| `memory stats` | View totals and statistics by category |
| `memory query` | Query with category/subject/status filters |
| `memory dump` | Export the full scratchpad |
| `memory conflicts` | View conflicting active entries with the same primary key |
| `memory bootstrap` | Backfill initial long-term memory from index.db and summaries |
| `memory update` | Manually map and write results for a specified chapter |

Examples:

```bash
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" memory stats
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" memory query --category character_state --subject xiaoyan
```

### Story System Subcommands

| Subcommand | Description |
|--------|------|
| `story-system "<genre>" --persist` | Write contract seeds (`MASTER_SETTING.json`, etc.) |
| `story-system "<genre>" --emit-runtime-contracts --chapter N` | Generate runtime contracts and run prewrite validation |
| `chapter-commit --chapter N` | Create a chapter commit (optionally including review/fulfillment/disambiguation/extraction results) |
| `write-gate --chapter N --stage prewrite` | Check project stage, Story System contracts, and placeholders before writing |
| `write-gate --chapter N --stage precommit` | Check chapter prose and four types of commit artifacts before committing |
| `write-gate --chapter N --stage postcommit` | Check commit and projection status after committing |
| `projections retry --chapter N` | Retry a single-chapter projection from an existing commit |
| `projections replay --from-chapter A --to-chapter B` | Replay projections for a chapter range |
| `user-report --stage write --chapter N` | Summarize writing outputs, issues, and recommended next steps for this run |
| `run-ledger record-write-step --chapter N` | Record the status, inputs/outputs, issues, and duration of key writing steps |
| `run-ledger write-resume --chapter N` | Suggest how to resume from reliable checkpoints without automatically overwriting files |
| `run-log --event <name>` | Write sanitized logs for troubleshooting unrecoverable failures |
| `story-events --chapter N` | Query events for a specified chapter |
| `story-events --health` | Event-chain health check |
| `memory-contract` | Memory contract management |
| `review-pipeline --chapter N --review-results <file>` | Review pipeline |

Examples:

```bash
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" story-system "玄幻退婚流" --persist
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" chapter-commit --chapter 12 --review-result .webnovel/tmp/review.json
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" story-events --health
```

Artifacts:

- `story-system --persist` → `.story-system/MASTER_SETTING.json`
- `--emit-runtime-contracts` → `volumes/*.json` and `reviews/*.review.json`
- `chapter-commit` → `commits/*.commit.json`
- `story-events` → Read `events/*.events.json` or `index.db.story_events`
