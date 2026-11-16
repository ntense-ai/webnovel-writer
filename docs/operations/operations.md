# Project Structure and Operations

## Directory Hierarchy

## Operational Conventions

- `.story-system/`: Main-pipeline source of truth
- accepted `CHAPTER_COMMIT`: The sole entry point for postwrite facts
- `.webnovel/state.json`、`index.db`、`summaries/`、`memory_scratchpad.json`: Projections/read models
- `references/genre-profiles.md`: fallback-only
- `preflight` and the dashboard's `story_runtime` / `story-runtime/health` are the first places to inspect

The system uses four directory levels. Understand their differences before use:

| Level | Description | Example |
|------|------|------|
| `WORKSPACE_ROOT` | Claude Code workspace root | `D:\wk\novels` |
| `.claude/` | Workspace-level configuration and project pointer | `D:\wk\novels\.claude\` |
| `PROJECT_ROOT` | Root directory for one book (created by `/webnovel-init`) | `D:\wk\novels\A Mortal's Capital` |
| `CLAUDE_PLUGIN_ROOT` | Plugin cache directory (outside the project, managed by Marketplace installation) | Automatically managed |

### Workspace Directory

```text
workspace-root/
├── .claude/
│   ├── .webnovel-current-project   # Points to the current book project root
│   └── settings.json
├── novelA/                          # PROJECT_ROOT
├── novelB/
└── ...
```

A workspace can contain multiple books. Use the `.webnovel-current-project` pointer to switch the active book.

### Book Project Directory (PROJECT_ROOT)

```text
project-root/
├── .webnovel/            # Runtime data
│   ├── state.json        # Project state
│   ├── index.db          # SQLite index (entities/relationships/chapter data)
│   ├── vectors.db        # Vector index
│   ├── projection_log.jsonl # Projection execution log
│   ├── summaries/        # Chapter summaries
│   ├── backups/          # Automatic backups
│   └── archive/          # Archive
├── .story-system/        # Story System data
│   ├── MASTER_SETTING.json
│   ├── chapters/
│   ├── volumes/
│   ├── reviews/
│   ├── commits/
│   └── events/
├── chapters/                  # Chapter prose
├── outlines/                  # Master and volume outlines
├── settings/                # Worldbuilding, characters, power system
└── reviews/              # Review outputs
```

### Plugin Directory

The plugin is installed in the Claude plugin cache, not in the book project. Reference it at runtime through `CLAUDE_PLUGIN_ROOT`:

```text
${CLAUDE_PLUGIN_ROOT}/
├── skills/       # 8 Skill command definitions
├── agents/       # 4 Agent definitions
├── scripts/      # Python scripts and data modules
├── hooks/        # Claude Code session hooks
├── references/   # References (genre profiles, reader-retention taxonomy, etc.)
├── templates/    # Initialization templates
├── genres/       # Fine-tuned genre configurations
└── dashboard/    # Visual dashboard frontend
```

### User-Level Global Mapping

When the workspace pointer is unavailable, the system looks up the workspace → project mapping in the user-level registry:

```text
${CLAUDE_HOME:-~/.claude}/webnovel-writer/workspaces.json
```

## Common Operational Commands

### Environment Preflight

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "${WORKSPACE_ROOT}" preflight
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "${WORKSPACE_ROOT}" project-status --format summary
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "${WORKSPACE_ROOT}" doctor --format text
```

`preflight` provides a quick check, `project-status` gives a short status and next step, and `doctor` performs stage-aware health checks.

Checks: plugin script paths / project-root resolution / Skill directory existence / stage-appropriate files / JSON / SQLite / RAG configuration / Python dependencies / Dashboard artifacts.

If `story_runtime.mainline_ready=false`, the project is still using legacy fallback or its commit main pipeline is incomplete.

### Chapter-Writing Gates

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "${PROJECT_ROOT}" write-gate --chapter 12 --stage prewrite --format text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "${PROJECT_ROOT}" write-gate --chapter 12 --stage precommit --format text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "${PROJECT_ROOT}" write-gate --chapter 12 --stage postcommit --format text
```

- `prewrite`: Check the project stage, runtime contract, placeholders, and required prewrite files.
- `precommit`: Check the prose and all four commit-artifact types: review / fulfillment / disambiguation / extraction.
- `postcommit`: Check commit and projection status.

### Rebuilding Indexes

```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" index process-chapter --chapter 1
python "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" index stats
```

### Health Reports

```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" status -- --focus all
python "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" status -- --focus urgency
```

`status` retains its overall writing-health-report semantics; use `project-status` for a brief machine-readable status.

### Rebuilding Vectors

```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" rag index-chapter --chapter 1
python "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" rag stats
```

### Retrying Projections

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "${PROJECT_ROOT}" projections retry --chapter 12 --format text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "${PROJECT_ROOT}" projections replay --from-chapter 1 --to-chapter 12 --format text
```

Projection retries read facts only from existing `.story-system/commits/*.commit.json` files and regenerate read models such as `.webnovel/state.json`, `index.db`, `summaries/`, `memory_scratchpad.json`, and `vectors.db`. Each run appends to `.webnovel/projection_log.jsonl`.

### Author-Friendly Reports and Recovery

Final reports from the main Skills use four standardized statuses: Completed, Partially completed, Action required, and Not completed. They show only the conclusions, outputs, issues, and next steps that authors need; internal JSON, tracebacks, and lengthy command logs are not displayed directly.

Exceptions are handled in three categories:

- **Handled automatically**: Idempotent, retryable issues that do not affect author content, such as a successful projection retry or regenerating a missing runtime contract. The workflow continues by default, but the final report must explain what was handled.
- **Confirmation required**: Issues affecting creative direction, factual choices, file overwrites, or resume boundaries, such as manually edited prose, a chapter outline updated after the prose, or rewriting an already accepted chapter. The system should present 2–3 bounded options.
- **Must be resolved**: Blocking review findings, missing key outputs, rejected commits, or projection retries that still fail. The system stops at a safe point and reports completed work, the blocker, and recovery recommendations.

`/webnovel-write` records writing checkpoints to identify reliably completed steps when rerunning:

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "${PROJECT_ROOT}" run-ledger write-resume --chapter 12 --format text
```

Resume guidance only evaluates and advises; it does not automatically overwrite files. Always ask first when author-edited prose, reuse of existing prose, or redoing an accepted commit is involved.

Unrecoverable failures direct you to:

```text
.webnovel/logs/run_last.log
```

This log preserves sanitized technical details from the latest run for troubleshooting. Common sensitive fields and values are masked, including `api_key`, `secret`, `token`, `authorization`, `password`, `passwd`, `credential`, and inline key fragments such as `KEY=value`. Logs may still contain file paths and error context; review them manually before filing an issue.

### Tests

```bash
pwsh "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.ps1" -Mode smoke
pwsh "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.ps1" -Mode full
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/run_behavior_evals.py" --format text
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_plugin_package.py" --format text
```

`run_behavior_evals.py` performs quick behavioral-contract checks; `validate_plugin_package.py` follows plugin-dev principles to check the manifest, Skill / Agent frontmatter, hook wrappers, README version, and path portability.

### Hook Switches

Plugin-level hooks are lightweight by default:

- `SessionStart`: Runs only `project-status --format summary`; does not write files or start services.
- `PreToolUse`: Provides a fallback guard against direct writes to main-pipeline / read-model files and dangerous commands that bypass the runtime.

To disable them temporarily, set these environment variables:

```bash
WEBNOVEL_DISABLE_SESSION_STATUS_HOOK=1
WEBNOVEL_DISABLE_RUNTIME_GUARD_HOOK=1
```

## Story System Operations

### Health Checks

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "${PROJECT_ROOT}" story-events --health
```

Returned fields:`sqlite_rows` / `event_files` / `ok`

Pay particular attention to:

- `.story-system/commits/chapter_XXX.commit.json` exists and is accepted
- `projection_status` entries are all `done` / `skipped`
- `.story-system/events/` is readable
- The `story_events` table in `index.db` is queryable
- `override_contracts` can count `amend_proposal` entries

### Backups

When backing up Story System, back up at least the following together:

```text
.story-system/
.webnovel/index.db
```

For chapter-level rollback, also back up `.webnovel/summaries/`.
