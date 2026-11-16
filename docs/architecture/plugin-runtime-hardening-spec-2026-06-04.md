# Plugin Runtime Hardening Spec

> Date: 2026-06-04
> Status: Draft v1
> Scope: Consolidate plugin structure, runtime reliability, workflow orchestration, doctor diagnostics, hook state awareness, evaluations, and release governance in `webnovel-writer`, based on research into high-quality Claude Code plugins
> Research samples: `anthropics/claude-plugins-official`、`anthropics/skills`、`obra/superpowers`、`SonarSource/sonarqube-agent-plugins`、`appwrite/claude-plugin`、`aws-samples/sample-claude-code-plugins-for-startups`, community multi-plugin marketplaces

---

## 1. Background

`webnovel-writer` is no longer a single ordinary Skill; it is a complete long-form writing runtime plugin:

- 7 Skill commands handle init / plan / write / review / query / learn / dashboard.
- 4 Agents handle prewrite context, review, fact extraction, and reference deconstruction.
- Python CLI and `data_modules` implement Story System, commits, projections, RAG, memory, and the Dashboard data layer.
- `.story-system/` is the contract/commit main pipeline; `.webnovel/*` contains projections/read models.

Lessons shared by strong Claude Code plugins:

1. `SKILL.md` handles routing and workflow, not all knowledge.
2. Move deterministic actions into scripts/runtime/MCP rather than prompt constraints.
3. Keep clear boundaries among commands / skills / agents / hooks / MCP.
4. Hooks provide lightweight status, diagnostics, or wiring, not heavy business logic.
5. Complex workflows have verifiable inputs, outputs, stopping conditions, and acceptance criteria.
6. Provide environment-check entry points such as `doctor / integrate / setup`.
7. Use real behavioral evaluations to demonstrate protocol compliance.
8. Validate manifests, marketplace, README, versions, and LICENSE to prevent drift.

This specification turns these lessons into the next architecture-refactoring roadmap for `webnovel-writer`.

---

## 2. One-Sentence Goal

Upgrade `webnovel-writer` from a strong Skill package plus Python tools into:

> A long-form writing runtime plugin that is self-diagnosing, verifiable, recoverable, replayable, and governed through releases.

---

## 3. Design Principles

### 3.1 Runtime First

The runtime must guarantee critical writing, commit, projection, and validation paths rather than relying mainly on natural-language Skill steps.

### 3.2 Skill as Router

Keep in `SKILL.md`:

- When to trigger
- Decision trees
- High-level workflow
- Required/on-demand reference routing
- Failure-handling boundaries

Do not put in `SKILL.md`:

- Long command-construction details
- Schema validation logic
- Projection repair logic
- Large bodies of genre knowledge
- Programmatically verifiable rules

### 3.3 Commit Is Fact

`CHAPTER_COMMIT` records postwrite facts and must not be mixed with projection execution logs. Gradually decouple facts from projection execution status.

### 3.4 Hooks Are Advisory Guards

Hooks may be automatically triggered lightweight guards, not hidden business workflows.

Allowed:

- SessionStart project-status summary
- Dependency/configuration reminders
- Doctor entry-point guidance
- Dashboard / RAG / Story System health notices
- Fixed skill-scoped preflight checks, silent on success
- PreToolUse hard blocks on dangerous writes/commit commands

Prohibited:

- Automatic state / commit / memory writes
- Automatic external-dependency installation
- Automatic prose or setting edits
- Injecting extensive writing methodology
- Writing step state as the main chapter state machine
- Automatic hook tracking at every step
- Advancing writing without user visibility

### 3.5 Behavior Must Be Tested

Retain Python unit tests, but they do not prove plugin behavior. Add Skill/Agent workflow-level evaluations.

### 3.6 UTF-8 First

The project frequently reads Chinese paths and filenames; new entry points must explicitly use UTF-8:

- Python CLI entry points call `enable_windows_utf8_stdio()` or equivalent.
- All text reads/writes explicitly use `encoding="utf-8"`.
- Prefer `python -X utf8` for hook/subprocess commands, or explicitly set `PYTHONUTF8=1`.
- doctor / project-status / write-gate / hook scripts must not rely on system encoding.

### 3.7 Follow Official `plugin-dev`

All future additions/changes must first follow official `plugin-dev` guidance:

```text
C:\Users\lcy\.claude\plugins\marketplaces\claude-plugins-official\plugins\plugin-dev
```

Implementation constraints:

- Follow `plugin-structure`: `.claude-plugin/plugin.json` belongs under the plugin root's `.claude-plugin/`; `commands/`, `agents/`, `skills/`, and `hooks/` are root-level.
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin paths; no hardcoded local absolute paths in manifests/hooks/commands.
- New Skills follow `skill-development`: `SKILL.md` requires `name`, a specific trigger `description`, optional `version`; keep the body concise, detailed rules in `references/`, deterministic scripts in `scripts/`.
- New Commands follow `command-development`: Markdown + YAML frontmatter with a clear `description`, and `argument-hint` / `allowed-tools` when needed.
- New Agents follow `agent-development`: include `name`, `description`, `model` / `tools`, etc.; illustrate complex triggers; check validate-agent rules after edits.
- New Hooks follow `hook-development`: plugin `hooks/hooks.json` uses a wrapper containing `description` and `hooks`; command hooks use `${CLAUDE_PLUGIN_ROOT}`. Use command hooks for lightweight deterministic checks and prompt hooks only for contextual judgments.
- After component changes, validate structure following `plugin-validator`: manifest, commands, agents, skills, hooks, MCP, README, LICENSE, sensitive information, and path portability.

This takes precedence over custom implementation suggestions in this specification; official `plugin-dev` constraints win conflicts.

---

## 4. Non-Goals

Out of scope this round:

- Do not rewrite Story System main-pipeline semantics.
- Do not introduce large new MCP services.
- Do not split 37 genre templates into 37 Skills.
- Do not copy Superpowers' frequent Git-commit mechanism.
- Do not put writing business logic in hooks.
- Do not refactor Dashboard frontend information architecture this round.
- Do not change existing user-project formats without compatible reads.

---

## 5. Target Architecture

### 5.1 Component Boundaries

```text
commands/ or Slash Skill entry point
        ↓
Skill router (workflow, reference routing, failure boundaries)
        ↓
Claude Code Todo (host-managed process constraints)
        ↓
Runtime Gates (batch prewrite / precommit / postcommit validation)
        ↓
Agents（context / draft / review / data extract）
        ↓
Artifact Validator
        ↓
CHAPTER_COMMIT (factual main pipeline)
        ↓
Projection Engine（state/index/summary/memory/vector）
        ↓
Dashboard / Query / Doctor (read-only consumers)
```

### 5.2 Writing-Process Management

Do not add independent resume / step marks / workflow state. Claude Code already provides Todo and session recovery; let host Todo manage writing-step constraints.

Recommended Todo:

```text
[ ] Prewrite checks and contract refresh
[ ] context-agent creates the writing brief
[ ] Draft prose
[ ] reviewer review
[ ] Decide blocking issues / targeted fixes
[ ] Polish and format
[ ] data-agent extracts factual artifacts
[ ] chapter-commit submits facts
[ ] Verify projections and backup
```

The runtime does not track every step; it offers batch gates at three natural boundaries:

- `prewrite`: Before writing, check project root, placeholders, Story Runtime, and chapter contracts.
- `precommit`: Before commit, check prose and review/fulfillment/disambiguation/extraction artifacts.
- `postcommit`: After commit, check commit, projections, summary, memory, and backup.

This adds at most 2–3 deterministic calls per chapter, not tracking at every step.

### 5.3 State-Awareness Model

Two project-state layers:

| Layer | Owner | Persistence | Purpose |
|---|---|---|---|
| In-session progress | Claude Code Task / Todo | Session | Constrain current writing steps and show current work |
| Actual project state | Story System / commit / projection / artifacts | Project | Determine next action in new conversations, resume, and doctor |

No independent workflow state. Derive actual state at runtime:

- Use `.story-system/commits/*.commit.json` to identify the latest accepted/rejected chapter.
- Use `.story-system/MASTER_SETTING.json` and chapter contracts for the next chapter goal.
- Use `.webnovel/tmp/*` artifacts to determine review / fulfillment / extraction completion.
- Use `.webnovel/projection_log.jsonl` or compatibility fields to detect projection failure.
- Use drafts and chapter artifacts to detect uncommitted prose.

Add a machine-readable project-state entry point without taking over `webnovel.py status`, which forwards to `status_reporter.py` for overall writing health. This specification needs a short summary, so use a new command:

```bash
webnovel.py project-status --format json
webnovel.py project-status --format summary
```

Example state:

```json
{
  "schema_version": "webnovel-project-status/v1",
  "project": "灵石庄",
  "latest_accepted_chapter": 12,
  "target_chapter": 13,
  "phase": "chapter_contract_ready",
  "blocking": [],
  "warnings": ["rag_vector_missing"],
  "next_action": "run /webnovel-write chapter 13"
}
```

`phase` is derived, not a hook-written state machine. Its vocabulary needs one authority: add `project_phase.py`, shared by doctor, project-status, and write-gate. Recommended minimum:

- `no_project`
- `unknown`
- `init_scaffolded`
- `init_ready`
- `plan_in_progress`
- `chapter_contract_ready`
- `draft_in_progress`
- `ready_to_commit`
- `chapter_committed`
- `projection_failed`

### 5.4 Hook/State Boundary

Hooks only read state, inject short context, or block dangerous actions:

- `SessionStart`: Call `project-status --format summary` after a new conversation, resume, clear, or compact to tell Claude current progress.
- `PreToolUse`: While `webnovel-write` is active, block commit/projection writes that bypass gates.
- `PostToolUse`: May provide gate-failure details to Claude, but cannot prevent effects that already occurred.

State transitions come only from explicit runtime commands:

- `write-gate --stage prewrite/precommit/postcommit`
- `chapter-commit`
- `projections retry/replay`
- Explicit user decisions on blocking issues

This keeps workflow progression in explicit Skill/runtime commands, not hidden hooks.

---

## 6. Phase 1: `webnovel-doctor` Project Diagnostics

### 6.1 Goal

Add read-only diagnostics above existing `preflight`. Since preflight already checks CLI environment, project_root, and `story_runtime`, doctor must reuse or absorb these checks, not create a parallel set.

Address three problem types:

1. **Files**: Directory layout, missing key files, expected JSON / SQLite / Markdown content.
2. **Configuration**: RAG API/key, Python dependencies, Dashboard build artifacts, and other runtime prerequisites.
3. **Error explanation and repair guidance**: Explain impact and provide executable repair commands or manual steps.

Doctor does not decide chapter content or replace write-gate. It answers:

> Are the book project and plugin environment complete, readable, and runnable? If not, what is broken and how can it be fixed?

### 6.2 Entry Points

CLI：

```bash
python -X utf8 webnovel-writer/scripts/webnovel.py --project-root "<PROJECT_ROOT>" doctor --format json
```

Skill：

```text
/webnovel-doctor
```

Relationship to existing entry points:

- `preflight`: Retain as a quick environment check and compatibility entry point.
- `doctor`: Includes preflight quick checks plus stage-aware inventories, SQLite, RAG, Python dependencies, Dashboard, and repair guidance.
- `project-status`: Only short status and next action, not deep diagnostics.
- `status`: Retain the overall writing-health semantics of `status_reporter.py`.

Optional future hook:

```text
SessionStart -> print project-status summary; on issues suggest /webnovel-doctor
```

### 6.3 Modes

Default mode performs local read-only checks only:

```bash
webnovel.py doctor --format json
webnovel.py doctor --format text
```

Only optional deep mode may perform slow or external-connectivity checks:

```bash
webnovel.py doctor --deep --format json
```

Optional chapter mode checks artifacts for a specified chapter:

```bash
webnovel.py doctor --chapter 13 --format json
```

Default doctor must not:

- Write any files.
- Repair automatically.
- Install Python / Node dependencies automatically.
- Launch Dashboard automatically.
- Test RAG APIs online by default.

### 6.4 Stage-Aware Expected-File Inventory

Doctor must determine the project stage before deciding expected files. Do not apply finished-project inventories to every project.

#### 6.4.1 Phase Resolution

Shared `project_phase.py` derives phases without writing state files. Doctor, project-status, and write-gate must use one resolver and one vocabulary:

| phase | Evidence | Meaning |
|---|---|---|
| `no_project` | Invalid project root or missing `.webnovel/state.json` | Not initialized or no bound book project |
| `unknown` | Insufficient file evidence for a reliable determination | Run only low-risk checks |
| `init_scaffolded` | State, base directories, settings/master outline exist, but no `.story-system/MASTER_SETTING.json` | `webnovel.py init` just finished; Story System not generated |
| `init_ready` | State, base settings, `大纲/总纲.md`, and `.story-system/MASTER_SETTING.json` exist | Init complete; ready for plan |
| `plan_in_progress` | MASTER_SETTING exists; volume/chapter contracts incomplete | Planning; not ready to write |
| `chapter_contract_ready` | Target has volume / chapter / review contracts | Ready for prewrite context and drafting |
| `draft_in_progress` | Target has draft prose or `.webnovel/tmp` artifacts | Writing or reviewing |
| `ready_to_commit` | All review / fulfillment / disambiguation / extraction artifacts exist | Ready for precommit gate |
| `chapter_committed` | Target chapter has a commit | Chapter committed; check projections |
| `projection_failed` | Latest commit has `projection_status.failed:*` | Read model untrusted; repair needed |

If uncertain, return `phase=unknown` and perform only low-risk readability checks.

#### 6.4.2 Stage Expectations

Doctor output must include current-stage expectations:

```json
{
  "phase": "init_ready",
  "expected_profile": "after_init",
  "expected_files": {
    "required": [
      ".webnovel/state.json",
      ".webnovel/summaries/",
      "设定集/世界观.md",
      "设定集/力量体系.md",
      "设定集/主角卡.md",
      "设定集/反派设计.md",
      "大纲/总纲.md",
      ".env.example",
      ".story-system/MASTER_SETTING.json"
    ],
    "conditional": [
      "设定集/主角组.md",
      "设定集/女主卡.md"
    ],
    "not_expected_yet": [
      ".story-system/volumes/volume_001.json",
      ".story-system/chapters/chapter_001.json",
      ".story-system/reviews/chapter_001.review.json",
      ".story-system/commits/chapter_001.commit.json",
      ".webnovel/summaries/chapter_001.md",
      ".webnovel/memory_scratchpad.json"
    ]
  }
}
```

Determine `conditional` files from `state.json`, for example:

- Require `设定集/主角组.md` only for multiple/group protagonists in `protagonist_structure`.
- Require `设定集/女主卡.md` only when `heroine_config` is not no-heroine.
- Projects without a special ability need no separate `金手指设计.md`.

#### 6.4.3 Immediately After Init

After `webnovel.py init`, require a complete skeleton, not postwrite artifacts.

Required:

```text
.webnovel/
.webnovel/backups/
.webnovel/archive/
.webnovel/summaries/
.webnovel/state.json
设定集/
设定集/世界观.md
设定集/力量体系.md
设定集/主角卡.md
设定集/反派设计.md
大纲/
大纲/总纲.md
正文/
审查报告/
.env.example
```

If `/webnovel-init` completed Story System initialization, also require:

```text
.story-system/
.story-system/MASTER_SETTING.json
.story-system/anti_patterns.json
```

Do not require during init:

```text
.story-system/volumes/volume_001.json
.story-system/chapters/chapter_001.json
.story-system/reviews/chapter_001.review.json
.story-system/commits/chapter_001.commit.json
.webnovel/summaries/chapter_001.md
.webnovel/memory_scratchpad.json
.webnovel/vectors.db
```

Missing items here yield only `skip` or `info`, never warnings/blockers.

#### 6.4.4 Plan / Write / Commit Inventories

Require only after planning:

```text
.story-system/volumes/volume_001.json
.story-system/chapters/chapter_001.json
.story-system/reviews/chapter_001.review.json
```

Check only during writing:

```text
.webnovel/tmp/review_results.json
.webnovel/tmp/fulfillment_result.json
.webnovel/tmp/disambiguation_result.json
.webnovel/tmp/extraction_result.json
```

Require only after commit:

```text
.story-system/commits/chapter_001.commit.json
.webnovel/summaries/chapter_001.md
.webnovel/index.db
```

The RAG vector database is always an enhancement:

```text
.webnovel/vectors.db
```

If missing/empty, return only a warning by default and explain BM25 fallback; escalate to blocker only when semantic retrieval is explicitly required or with `--deep --require-rag`.

#### 6.4.5 False-Positive Control

Doctor severity depends on current stage + user goal:

| Condition | Phase | Result |
|---|---|---|
| Missing commit | `init_ready` | `skip` / `info` |
| Missing commit | `ready_to_commit` | `blocker` |
| Missing summary | `init_ready` | `skip` / `info` |
| Missing summary | `chapter_committed` and projection summary=done | `blocker` |
| Missing vectors.db | Any default mode | `warning` |
| Missing MASTER_SETTING | `init_scaffolded` | `warning`; suggest story-system persist |
| Missing MASTER_SETTING | `plan_in_progress` or later | `blocker` |

### 6.5 File / Data-Structure Checks

Doctor must turn hard-to-inspect project files and database structures into readable reports.

#### 6.5.1 Directory Structure

Checks:

- Project root is valid and is not the plugin directory itself.
- `.webnovel/` exists.
- `.story-system/` exists.
- Book directories such as `正文/`, `大纲/`, and `设定集/` exist.
- Whether user-project files were mistakenly written into the plugin directory.

Assessment:

- Invalid project root: `blocker`.
- Missing `.webnovel/` or `.story-system/`: `blocker` or `warning`, depending on whether initialization just finished.
- Missing prose/outline/settings directories: `warning`, with initialization/creation guidance.

#### 6.5.2 Story System Main-Pipeline Files

Checks:

- `.story-system/MASTER_SETTING.json` exists, is readable JSON, and has the correct `meta.contract_type`.
- `volumes/volume_*.json` exists and is readable JSON.
- `chapters/chapter_*.json` exists and is readable JSON.
- `reviews/chapter_*.review.json` exists and is readable JSON.
- `commits/chapter_*.commit.json` exists and is readable JSON.
- Latest commit `meta.status` is `accepted` / `rejected`.
- Latest commit `provenance.write_fact_role` is `chapter_commit`.

Assessment:

- Unreadable main-pipeline JSON: `blocker`.
- Missing MASTER_SETTING after writing has begun: `blocker`.
- Clearly invalid latest-commit schema: `blocker`.
- New project without commits: `info` or `warning`, not a false error.

#### 6.5.3 Projection / Read-Model Files

Checks:

- `.webnovel/state.json` exists, is readable JSON, and has parseable base fields.
- `.webnovel/summaries/` exists and the latest accepted chapter has a summary.
- `.webnovel/memory_scratchpad.json` exists, is readable JSON, and has a parseable base structure.
- Latest commit `projection_status` contains `pending` / `failed:*`.

Assessment:

- Unreadable `state.json`: `blocker`.
- Projection writer failure: `blocker`, because later queries/dashboard may be unreliable.
- Missing summary/memory: usually `warning`, unless the projection is marked done but its output is absent.

#### 6.5.4 SQLite Databases

Check `.webnovel/index.db`:

- File exists.
- SQLite opens.
- Key tables exist.
- Key-table row counts are plausible.
- Basic queries execute.

Initial recommended key tables:

```text
entities
relationships
story_events
review_metrics
writing_checklist_scores
override_ledger
```

Check `.webnovel/vectors.db`:

- File exists.
- SQLite opens.
- `vectors` table exists.
- Vector row count.
- `bm25_index` / `doc_stats` exist.

Database reports must explicitly show tables and row counts, for example:

```json
{
  "id": "db.index.tables",
  "status": "ok",
  "severity": "info",
  "path": ".webnovel/index.db",
  "tables": {
    "entities": 128,
    "relationships": 42,
    "story_events": 36,
    "review_metrics": 12
  }
}
```

Assessment:

- Missing/unopenable `index.db`: `blocker`.
- Missing `story_events`: `warning` or `blocker`, depending on whether accepted commits exist.
- Missing `vectors.db`: `warning`; RAG can fall back to BM25.
- Zero `vectors` rows: `warning`.

#### 6.5.5 Reference / CSV Files

Checks:

- `references/csv/*.csv` exist.
- Required CSV headers match expectations.
- Core genre-alias, genre/tone reasoning, and anti-pattern tables are readable.
- Whether obvious placeholders remain.

Assessment:

- Unreadable core CSV or missing header: `warning`.
- Missing data preventing story-system from generating MASTER_SETTING: `blocker`.

### 6.6 System / Configuration Checks

#### 6.6.1 Python Dependencies

Checks:

- Current Python version.
- `scripts/requirements.txt` exists.
- Core packages import.

Initial core packages:

```text
pydantic
numpy
requests
fastapi
uvicorn
watchdog
```

Assessment:

- Missing package required by the CLI: `blocker`.
- Missing Dashboard-only package: `warning`, unless the user is running the dashboard Skill.

#### 6.6.2 RAG Configuration

Default-mode checks:

- Embedding configuration is readable from `.env` / environment variables.
- embed base_url / model are configured.
- embed api_key exists.
- rerank base_url / model / api_key exist.
- `vectors.db` exists and contains data.
- Inferred RAG mode: `full` / `embed_only` / `bm25_only`.

Only in `--deep` mode:

- embed API is callable.
- rerank API is callable.
- Returned dimensions are compatible with existing vectors.

Assessment:

- Missing RAG key: `warning`, explicitly explaining BM25 fallback.
- API connectivity failure: `warning` or `blocker`, depending on whether semantic retrieval is required.
- Clearly empty base_url / model: `warning`.

#### 6.6.3 Dashboard / Node

Checks:

- `dashboard/frontend/dist/index.html` exists.
- Dashboard backend imports.
- `dashboard/requirements.txt` exists.
- `dashboard/frontend/package.json` exists.

Excluded by default:

- No automatic `npm install`.
- No automatic service launch.
- No default localhost-port checks.

Assessment:

- Missing dist: `warning`, suggest rebuilding.
- Missing FastAPI dependency: `warning`.

### 6.7 Output Format

Each check must include:

- `id`: Stable error code for tests/UI.
- `status`：`ok` / `fail` / `warn` / `skip`。
- `severity`：`blocker` / `warning` / `info`。
- `path`: Relevant path, empty if none.
- `expected`: Expected state.
- `actual`: Actual state.
- `impact`: User impact.
- `repair`: Repair command or manual guidance.

```json
{
  "ok": false,
  "project_root": "...",
  "mode": "default",
  "phase": "chapter_committed",
  "expected_profile": "after_commit",
  "blocking_count": 1,
  "warning_count": 2,
  "expected_files": {
    "required": [".webnovel/state.json", ".story-system/commits/chapter_001.commit.json"],
    "not_expected_yet": []
  },
  "checks": [
    {
      "id": "db.index.missing_table",
      "status": "fail",
      "severity": "blocker",
      "path": ".webnovel/index.db",
      "expected": "table story_events exists",
      "actual": "table missing",
      "impact": "Cannot confirm whether the accepted commit event chain was projected",
      "repair": {
        "command": "webnovel.py projections replay --from 1 --to latest --writers index",
        "manual": "If replay is not implemented, rerun chapter-commit for the latest chapter or restore index.db from backup"
      }
    }
  ],
  "recommended_actions": [
    {
      "command": "webnovel.py rag stats",
      "reason": "vectors.db missing; semantic retrieval will fall back to BM25",
      "severity": "warning"
    }
  ]
}
```

### 6.8 Error-Code Naming

Error codes are grouped by domain:

```text
project.root.invalid
project.phase.unknown
project.expected_file.missing
project.structure.missing_dir
story.master.missing
story.commit.invalid_json
story.commit.invalid_status
projection.status.failed
projection.file.missing
db.index.unreadable
db.index.missing_table
db.vector.empty
rag.embed.key_missing
rag.embed.api_unreachable
python.import_missing
dashboard.dist_missing
reference.csv.invalid_header
artifact.schema_error
```

### 6.9 Files

- `webnovel-writer/scripts/data_modules/doctor.py`
- `webnovel-writer/scripts/data_modules/project_phase.py`
- `webnovel-writer/scripts/data_modules/project_status.py`
- `webnovel-writer/scripts/data_modules/webnovel.py`
- `webnovel-writer/skills/webnovel-doctor/SKILL.md`
- `webnovel-writer/scripts/data_modules/tests/test_doctor.py`
- `webnovel-writer/scripts/data_modules/tests/test_project_phase.py`
- `webnovel-writer/scripts/data_modules/tests/test_project_status.py`
- `docs/guides/commands.md`

### 6.10 Acceptance

- Empty project returns `ok=false` without writing files.
- Immediately after init, identify `phase=init_scaffolded` or `phase=init_ready` and return stage-specific `expected_files`.
- Missing commit / summary / memory / vectors.db immediately after init must not return blocker.
- Missing `state.json`, `设定集/世界观.md`, or `大纲/总纲.md` immediately after init must return blocker/warning with recovery commands.
- Missing `MASTER_SETTING.json` is warning at `init_scaffolded`, blocker at plan/write.
- Healthy project returns `ok=true` and key table/row counts for `index.db` / `vectors.db`.
- Missing `state.json` returns a `project.structure` or `projection.file` blocker.
- Missing key `index.db` tables return stable codes, impact, and repair guidance.
- Missing/empty `vectors.db` returns warning and explicit BM25 fallback notice.
- Missing RAG key warns without blocking ordinary writing.
- Missing required Python packages block and suggest installing `scripts/requirements.txt`.
- Missing Dashboard dist warns and suggests the build command.
- Failed latest-commit projection returns an actionable command.
- Default mode does not access networks, install dependencies, launch services, or write files.
- `--deep` may ping RAG APIs, explicitly labeled as a deep check.
- Preflight remains runnable and consistent with doctor quick checks.
- All Chinese paths/files use UTF-8 on Windows and do not fail under default GBK.

---

## 7. Phase 2: Chapter Runtime Gates

### 7.1 Goal

Do not build another workflow/resume system. Move error-prone `/webnovel-write` boundaries into batch-validation gates; Claude Code Todo controls sequence.

Runtime Gates depend on Artifact Validator error semantics. This section describes design, not implementation before the validator.

### 7.2 New Modules

Add gate wrappers, but prewrite must wrap or migrate existing `PrewriteValidator`, not duplicate placeholder/contract logic:

```text
webnovel-writer/scripts/data_modules/write_gates/
  __init__.py
  prewrite.py
  precommit.py
  postcommit.py
```

Existing reuse points:

- `webnovel-writer/scripts/data_modules/prewrite_validator.py`
- `webnovel-writer/scripts/data_modules/tests/test_prewrite_validator.py`

### 7.3 Gate Design

Do not write `.workflow.json` or maintain step state. Each gate computes from current files/artifacts.

Unified output:

```json
{
  "schema_version": "write-gate/v1",
  "chapter": 12,
  "stage": "precommit",
  "ok": false,
  "blocking": [
    {
      "type": "pending_disambiguation",
      "detail": "disambiguation_result.pending is not empty"
    }
  ],
  "warnings": [],
  "artifacts": {
    "review_result": ".webnovel/tmp/review_results.json",
    "fulfillment_result": ".webnovel/tmp/fulfillment_result.json",
    "disambiguation_result": ".webnovel/tmp/disambiguation_result.json",
    "extraction_result": ".webnovel/tmp/extraction_result.json"
  }
}
```

### 7.4 Gate Responsibilities

Runtime gates own:

- Checking required files.
- JSON-schema validation.
- Reusing `PrewriteValidator` at prewrite.
- Determining blocking issues.
- Deciding whether the next natural stage is allowed.
- Clear failure reasons and suggested commands.

Runtime gates do not own:

- Drafting prose in place of the LLM.
- Reviewing in place of Agents.
- Making user decisions automatically.
- Tracking every step.
- Replacing Claude Code Todo / session recovery.

### 7.5 CLI Subcommands

```bash
webnovel.py write-gate --chapter N --stage prewrite --format json
webnovel.py write-gate --chapter N --stage precommit --format json
webnovel.py write-gate --chapter N --stage postcommit --format json
```

### 7.6 Skill Changes

Change `webnovel-write/SKILL.md` to:

1. Create the chapter checklist using Claude Code Todo.
2. Run `write-gate --stage prewrite`; write only after it passes.
3. Invoke context-agent.
4. Draft prose。
5. Invoke reviewer.
6. Track blocking issues in Todo and resolve / fix them precisely.
7. Invoke data-agent after polishing.
8. Run `write-gate --stage precommit`; commit only after it passes.
9. Invoke chapter-commit.
10. Run `write-gate --stage postcommit`; announce completion only after it passes.

### 7.7 Acceptance

- Missing `review_results.json` prevents commit.
- Reviewer blocking issues yield `precommit.ok=false`.
- Nonempty disambiguation pending yields `precommit.ok=false`.
- Projection failure yields `postcommit.ok=false`.
- Limit gates to 2–3 calls per chapter, with no per-step marking.

---

## 8. Phase 3: Artifact Validator

### 8.1 Goal

Validate all Agent artifacts consistently to prevent field-name drift, wrong wrappers, and missing required fields.

### 8.2 Validation Targets

- `review_results.json`
- `fulfillment_result.json`
- `disambiguation_result.json`
- `extraction_result.json`
- `chapter_XXX.commit.json`
- `projection_status`

Authoritative schemas:

- For `review_results.json`, `fulfillment_result.json`, `disambiguation_result.json`, and `extraction_result.json`, default to commit-required Pydantic models in `chapter_commit_schema.py`.
- Similarly named models in `review_schema.py` / `entity_linker.py` remain local upstream-tool models, not final commit-artifact authorities.
- Normalize compatibility with upstream local models explicitly in `artifact_validator.py` and label the compatibility source.

### 8.3 Output Error Categories

```text
schema_error
missing_artifact
blocking_review
missed_outline_node
pending_disambiguation
commit_rejected
projection_failure
unsafe_project_root
placeholder_blocker
```

### 8.4 Files

- `webnovel-writer/scripts/data_modules/artifact_validator.py`
- `webnovel-writer/scripts/data_modules/tests/test_artifact_validator.py`
- `webnovel-writer/scripts/data_modules/write_gates/precommit.py`

### 8.5 Acceptance

- Wrapping `extraction_result.json` in `{"extraction": ...}` returns schema_error.
- Legacy field names in `state_deltas` are supported or clearly diagnosed.
- Nonempty `disambiguation_result.pending` blocks commit.
- Nonempty `fulfillment_result.missed_nodes` blocks an accepted commit.
- Same-named models such as `ReviewResult` / `DisambiguationResult` no longer drift independently; validator explicitly follows commit-artifact schemas.

---

## 9. Phase 4: Immutable Commits and External Projection Logs

### 9.1 Current Problem

Currently `ChapterCommitService`:

1. Builds a commit.
2. Persists it.
3. Applies projections.
4. Writes `projection_status` back into the commit.

This combines factual records and projection execution logs in one commit.

### 9.2 Goal

Separate facts from projection execution state:

```text
.story-system/commits/chapter_012.commit.json     # Immutable facts
.webnovel/projection_log.jsonl                    # Projection execution log
index.db.projection_runs                           # Queryable projection state
```

### 9.3 Migration Strategy

Phase 4 uses a dual-write transition rather than immediately removing commit `projection_status`:

1. Retain commit projection_status for Dashboard compatibility.
2. Add projection logs.
3. Dashboard / doctor prefer projection logs.
4. Deprecate commit projection_status in a later release.

### 9.4 Projection Run Schema

```json
{
  "run_id": "ch012-20260604T102233",
  "chapter": 12,
  "commit_path": ".story-system/commits/chapter_012.commit.json",
  "commit_hash": "sha256:...",
  "writer": "memory",
  "status": "done",
  "started_at": "...",
  "finished_at": "...",
  "error": "",
  "retry_of": ""
}
```

### 9.5 Files

- `webnovel-writer/scripts/data_modules/projection_log.py`
- `webnovel-writer/scripts/data_modules/chapter_commit_service.py`
- `webnovel-writer/scripts/data_modules/tests/test_projection_log.py`
- `webnovel-writer/dashboard/app.py`
- `webnovel-writer/scripts/data_modules/story_runtime_health.py`

### 9.6 Acceptance

- Every writer execution has a projection log.
- One failed writer does not affect other writers' records.
- Doctor identifies failed writers and retry commands.
- Projection logs trace the commit-file hash.

---

## 10. Phase 5: Projection Replay / Retry

### 10.1 Goal

Retry only failed projection writers, especially external dependencies such as vector / RAG.

### 10.2 CLI

```bash
webnovel.py projections status --chapter N
webnovel.py projections retry --chapter N --writer vector
webnovel.py projections retry-failed --chapter N
webnovel.py projections replay --from 1 --to 20 --writers state,index,summary
```

### 10.3 Constraints

- Replay reads only accepted commits.
- Rejected commits permit only the state writer to update status.
- Writers must be idempotent.
- Retry must not change factual commit content.

### 10.4 Files

- `webnovel-writer/scripts/data_modules/projection_runner.py`
- `webnovel-writer/scripts/data_modules/event_projection_router.py`
- Projection-writer idempotency tests

### 10.5 Acceptance

- After deleting `summaries/chapter_012.md`, retry summary restores it.
- Missing vector API key causes vector failure while other writers finish.
- After configuring the key, retry vector reruns only vector.
- After replaying 1–5, state/index/summary match the commit chain.

---

## 11. Phase 6: Strengthen Skill / Agent Contracts

### 11.1 Skill Frontmatter

Upgrade descriptions of the 7 existing Skills from one-line explanations to retrieval rules:

- When to use.
- Typical trigger phrases.
- When not to use.
- Whether side effects occur.

Example:

```yaml
description: Use when the user wants to draft, continue, rewrite, or commit a numbered webnovel chapter. Runs the full context -> draft -> review -> polish -> fact extraction -> chapter commit workflow. Do not use for pure status queries, project initialization, or dashboard-only requests.
```

### 11.2 Agent Frontmatter

Complete all Agents with:

- `name`
- `description`
- `tools`
- `model` (optional)
- `output_schema`
- `failure_statuses`

### 11.3 Agent Responsibility Changes

Existing:

- `context-agent`
- `reviewer`
- `data-agent`
- `deconstruction-agent`

Suggested additions/splits:

- `continuity-reviewer`: Settings / timeline / character state / foreshadowing compliance.
- `style-reviewer`: Style / AI-like prose / repeated sentence patterns / formatting.
- `reader-pull-reviewer`: Payoffs / hooks / micro-fulfillment / reader retention.

Initially split dimensions in the reviewer output schema without adding files; split Agents later.

### 11.4 Acceptance

- Prompt-integrity tests confirm sufficiently detailed Skill descriptions.
- Artifact validator can validate Agent output schemas.
- data-agent documentation still explicitly prohibits direct writes to state/index/summaries/memory.

---

## 12. Phase 7: Behavior Evals

### 12.1 Goal

Adopt Superpowers-style headless behavior testing to verify protocol compliance.

### 12.2 Eval Types

Add:

```text
evals/
  skill-triggering/
  workflow-behavior/
  agent-output-schema/
  continuity-conflict/
  memory-commit/
```

### 12.3 Initial Cases

| Eval | Goal |
|---|---|
| init_project_safety | No project creation in plugin directory or canon contamination |
| plan_outputs_executable_chapter_tasks | Chapter outline includes target emotion, character changes, foreshadowing, and prohibited content |
| write_blocks_on_review_blocking_issue | Blocking issues prevent commit |
| data_agent_never_writes_projection | data-agent produces artifacts only |
| commit_drives_projection | Accepted commits trigger projection writers |
| query_falls_back_explicitly | Query explicitly reports fallback when main pipeline is missing |
| dashboard_readonly | Dashboard API exposes no write endpoints |

### 12.4 Runner

Start with a lightweight runner:

```bash
python webnovel-writer/scripts/run_behavior_evals.py --case write_blocks_on_review_blocking_issue
```

Without local Claude Code CLI, skip transcript tests and run artifact fixtures only.

### 12.5 Acceptance

- At least one evaluation per Skill.
- `webnovel-write` covers at least success and blocking paths.
- Evaluations output JSON with pass/fail/reason/artifacts.

---

## 13. Phase 8: Manifest / Marketplace / Release Governance

### 13.1 Goal

Prevent drift among plugin metadata, README, marketplace, and versions.

### 13.2 Validation Script

Add:

```bash
python webnovel-writer/scripts/validate_plugin_package.py
```

Checks:

- Root `.claude-plugin/marketplace.json` exists.
- Plugin `.claude-plugin/plugin.json` exists.
- marketplace and plugin.json versions match.
- README / existing CI version locations match plugin.json; do not add README version rules conflicting with Plugin Version Check.
- Every `skills/*/SKILL.md` has frontmatter.
- Every `agents/*.md` has frontmatter.
- LICENSE exists.
- Dashboard dist exists.
- `scripts/requirements.txt` and root `requirements.txt` parse.
- Documentation command tables match actual Skill names.

### 13.3 Optional Manifest Enhancements

If supported by the Claude Code manifest, add:

- `commands`
- `agents`
- `hooks`
- `mcpServers`
- user config schema
- screenshots / assets

If the host requires no explicit declaration, retain default discovery and avoid overconfiguration.

### 13.4 Acceptance

- Validation passes after a clean clone.
- Changing any version location causes validation failure.
- Removing Skill frontmatter causes validation failure.
- Version checks reuse/align with CI, without conflicting with README version-table/badge checks.

---

## 14. Phase 9: Lightweight SessionStart Hook (Optional)

### 14.1 Goal

Add an optional project-status hook for session start, resume, clear, and compact. It observes state; it is not a state machine.

### 14.2 Output

```text
Webnovel Writer initialized.
  project: 灵石庄
  story runtime: mainline ready, latest chapter 12 accepted
  projections: 4 done, 1 failed(vector)
  rag: BM25 fallback; EMBED_API_KEY missing
  next: run /webnovel-doctor for details
```

### 14.3 Constraints

- Read-only.
- Do not install dependencies.
- Do not write files.
- At most 8 output lines.
- Healthy output is a summary, not full JSON.
- On failure provide one next-step command, not lengthy diagnostics.
- Disable through an environment variable:

```text
WEBNOVEL_DISABLE_SESSION_HOOK=1
```

### 14.4 Files

- `webnovel-writer/hooks/hooks.json`
- `webnovel-writer/hooks/session_start.py`
- `webnovel-writer/.claude-plugin/plugin.json` or default hook-discovery path
- `docs/operations/operations.md`

### 14.5 Acceptance

- No project root: report unbound project, not an error.
- With a project root, call `project-status --format summary` or doctor summary.
- No output when disabled.
- Resume refreshes latest-chapter/projection status.
- Output stays within 1000 characters.

### 14.6 Skill-Scoped Preflight Hook (Optional)

For higher-risk Skills such as `/webnovel-write`, attach lightweight frontmatter hooks:

- `PreToolUse(Bash)`: Best-effort reminders/fallback blocks for direct `chapter_commit.py`, `webnovel.py chapter-commit`, or projection writes. Bash string parsing cannot be the sole guarantee; enforce strong guarantees in runtime gates and commit entry points.
- `PreToolUse(Write|Edit)`: For `.story-system/` commits or projection artifacts such as `.webnovel/state.json`, `index.db`, and `memory_scratchpad.json`, require runtime commands.
- Hooks stay silent on success and return a brief reason only when blocking.

Do not put all fixed checks in hooks. Recommended layering:

| Check type | Location |
|---|---|
| New-session status summary | plugin-level `SessionStart` hook |
| May begin writing this chapter | `write-gate --stage prewrite` |
| May commit this chapter | `write-gate --stage precommit` |
| May announce completion | `write-gate --stage postcommit` |
| Prevent main-pipeline writes bypassing runtime | skill-scoped `PreToolUse` hook |
| Complex repair guidance | `/webnovel-doctor` skill |

## 15. Recommended Implementation Order

1. `project_phase` + `project-status` + `webnovel-doctor`: Establish shared phase resolution, short status, and read-only diagnostics first.
2. `Artifact Validator`: Unify error semantics.
3. `Runtime Gates`: Batch checks at prewrite/precommit/postcommit boundaries, reusing `PrewriteValidator`.
4. `Projection Log`: Decouple facts and projection logs.
5. `Projection Retry / Replay`: Add recovery.
6. `Skill / Agent contract hardening`: Reduce prompt drift.
7. `Behavior Evals`: Prove plugin protocols work.
8. `Plugin Package Validator`: Release governance.
9. Optional `SessionStart Hook`: Read-only status notices.
10. Optional `Skill-scoped PreToolUse Hook`: Block dangerous writes bypassing runtime.

---

## 16. Acceptance Summary

| Capability | Acceptance criterion |
|---|---|
| Doctor | Read-only reports on directories/files/databases, RAG/Python/Dashboard configuration, and repair guidance |
| Project Status | Derives chapter phase from main pipeline/artifacts without replacing `status_reporter.py` semantics or writing workflow state |
| Runtime Gates | Batch checks at three natural `/webnovel-write` boundaries: prewrite, precommit, postcommit |
| Validator | Uniform diagnosis of Agent-artifact schema drift |
| Commit | Facts and projection logs separately traceable |
| Replay | Failed vector/summary/etc. projections individually retryable |
| Skills | 7 Skills have routing-capable descriptions; long knowledge loaded on demand |
| Agents | Agents have tool scopes, output schemas, and failure statuses |
| Evals | At least 1 behavioral evaluation per Skill |
| Package | Manifest / marketplace / README / versions are verifiable |
| Hook | If enabled, SessionStart is read-only and brief; PreToolUse blocks dangerous actions only |

---

## 17. Risks

### 17.1 Overengineering

Risk: Excessive fragmentation while emulating strong plugins.
Control: Prioritize doctor / validator / runtime gates; do not rush to split 37 genre Skills.

### 17.2 Hook Side Effects

Risk: Automatic hook execution undermines trust.
Control: Read-only SessionStart, dangerous-action-only PreToolUse; all repair/progression explicitly triggered by Skills/runtime.

### 17.3 Hook State-Machine Drift

Risk: Hook-written state creates competing truths with commit/projection/Todo.
Control: Derive state through shared `project_phase` / `project-status`; hooks do not write state; only explicit Skill/runtime commands advance workflow.

### 17.4 Commit Migration Breaks Dashboard

Risk: Dashboard cannot read externalized projection_status.
Control: Dual-write first; Dashboard prefers new logs; retain legacy fields for one release cycle.

### 17.5 Evaluation Cost

Risk: Headless Claude evaluations are slow and expensive.
Control: Separate fast fixture and slow transcript evaluations; CI defaults to fast.

### 17.6 Changed Skill Triggers

Risk: Longer descriptions alter triggering.
Control: Add trigger evaluations and verify before release.

---

## 18. Invariants

All refactoring must preserve:

1. `.story-system/` is the main-pipeline source of truth.
2. Accepted `CHAPTER_COMMIT` is the postwrite fact entry point.
3. `.webnovel/state.json`, `index.db`, `summaries/`, and `memory_scratchpad.json` are projections/read models.
4. `data-agent` does not write projections directly.
5. Dashboard is read-only by default.
6. Missing RAG keys allow BM25 fallback.
7. User-project files must not be written to the plugin directory.
8. Hooks are not project-state truth.
9. `webnovel.py status` retains overall writing-health semantics; use `project-status` for short status.

---

## 19. Initial Actionable Tasks

1. Add `project_phase.py` for shared doctor / project-status / gate phase resolution.
2. Add `project_status.py`, register `project-status`, retain `status` forwarding to `status_reporter.py`.
3. Add `doctor.py`, reusing `preflight` / `build_story_runtime_health()`.
4. Register doctor in the unified CLI.
5. Add `/webnovel-doctor` Skill.
6. Add `artifact_validator.py`, initially wrapping commit-artifact Pydantic schemas from `chapter_commit_schema.py`.
7. Add validator fixtures for the four `webnovel-write` Agent artifact types.
8. Add `write_gates/prewrite.py`, `write_gates/precommit.py`, and `write_gates/postcommit.py`; prewrite wraps `PrewriteValidator`.
9. Update `webnovel-write/SKILL.md` to reference `write-gate --stage prewrite/precommit/postcommit`, retaining Claude Code Todo for process management.
10. Audit idempotency of all 5 projection writers before adding `projection_log.py`.
11. Expand descriptions for 7 Skills.
12. Add `validate_plugin_package.py`, aligning with version CI before checking frontmatter / LICENSE / dist.
13. Add optional SessionStart hook injecting only project-status summary.
14. Add optional skill-scoped PreToolUse hook for best-effort fallback reminders/blocks.

---

## 20. Final Assessment

The largest weakness is not insufficient knowledge or genre templates, but:

> Some critical processes still depend on Skill documentation and Agent protocol compliance.

Turn those protocols incrementally into runtime-verifiable mechanisms:

- Doctor checks completeness/usability of files, databases, and configuration;
- project-status uses a shared resolver to identify current progress;
- Runtime gates decide whether critical boundaries may be crossed;
- Validator establishes artifact trustworthiness;
- Projection logs track read-model synchronization;
- Evaluations demonstrate actual Agent protocol compliance;
- Package validator prevents release-artifact drift.

These changes give `webnovel-writer` the engineering stability of a strong Claude Code plugin.
