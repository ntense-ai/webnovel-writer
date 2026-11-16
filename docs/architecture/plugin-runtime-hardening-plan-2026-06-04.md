# Plugin Runtime Hardening Implementation Plan

> Date: 2026-06-04
> Status: Draft v1
> Related spec: `docs/architecture/plugin-runtime-hardening-spec-2026-06-04.md`
> Scope: Break the spec into an implementable, testable, reversible engineering plan, emphasizing change scope and impact.

---

## 1. Goals

Move `webnovel-writer` from workflows constrained mainly by Skill documentation to a plugin with runtime-verifiable critical boundaries.

Core deliverables:

1. `project_phase` / `project-status`: Unified phase inference and short status, preserving the high-level creative-health semantics of `status_reporter.py`.
2. `/webnovel-doctor`: Phase-aware diagnostics for directories, files, databases, RAG, Python dependencies, and Dashboard configuration, with repair advice.
3. `artifact_validator`: Unified agent-artifact validation against field drift and schema errors.
4. `write-gate`: Batch validation at prewrite, precommit, and postcommit boundaries.
5. `projection_log`: Separate commit facts from projection execution logs.
6. `projections retry/replay`: Recover failed projections.
7. Stronger Skill / Agent contracts: Align frontmatter, descriptions, tools, and output constraints with official `plugin-dev`.
8. Behavior evals and package validator: Verify behavior and release consistency.
9. Optional lightweight hooks: SessionStart status and PreToolUse fallback warnings/blocks for dangerous actions.

---

## 2. Implementation Principles

### 2.1 Observe, Then Block, Then Migrate

Required order:

1. Provide read-only diagnostics first.
2. Add schema / gate blocking.
3. Finally implement projection logs and replay.

This reduces disruption from a large all-at-once change.

### 2.2 Preserve Existing User Projects

New capabilities default to backward compatibility:

- Preserve `.story-system/commits/*.commit.json` structure.
- Retain commit `projection_status` for at least one release cycle.
- Keep `.webnovel/state.json`, `index.db`, `summaries/`, and `memory_scratchpad.json` as projection/read models.
- Dashboard supports legacy fields first, then gradually reads projection logs.

### 2.3 Follow Official `plugin-dev`

All plugin-component changes must follow:

```text
C:\Users\lcy\.claude\plugins\marketplaces\claude-plugins-official\plugins\plugin-dev
```

Implementation requirements:

- Follow `plugin-structure` for plugin layout.
- Follow `skill-development`; keep `SKILL.md` concise and detailed rules in `references/`.
- Follow `command-development` for Commands.
- Follow `agent-development` for Agents.
- Follow `hook-development`; plugin-level `hooks/hooks.json` uses wrapper format.
- After each component-change round, apply `plugin-validator` principles to manifest, skills, agents, hooks, README, LICENSE, and path portability.

### 2.4 Independently Reversible Phases

Each phase should aim to:

- Prefer adding files over changing existing ones.
- Keep old entry points working.
- Isolate new CLI failures from old commands.
- Allow rollback by removing new entries or disabling hooks.

### 2.5 UTF-8 for All New Entry Points

All new CLI / hook / subprocess entry points must support Chinese Windows paths:

- CLI entries call `enable_windows_utf8_stdio()` or equivalent.
- Explicit `encoding="utf-8"` for file I/O.
- Hooks/subprocesses use `python -X utf8` or `PYTHONUTF8=1`.
- Never depend on system-default encoding.

---

## 3. Overall Dependency Order

```text
Phase 0 Baseline audit
  ↓
Phase 1 project_phase + project-status + doctor
  ↓
Phase 2 artifact_validator
  ↓
Phase 3 write-gate
  ↓
Phase 4 projection_log
  ↓
Phase 5 projection retry/replay
  ↓
Phase 6 Stronger skill / agent contracts
  ↓
Phase 7 behavior evals
  ↓
Phase 8 package validator
  ↓
Phase 9 hooks
```

Notes:

- Start with `project_phase` / `project-status` / `doctor`: read-only, lowest risk, and later gates/hooks need a shared phase.
- Build `artifact_validator` before `write-gate` to avoid duplicated schema checks.
- Build `projection_log` before retry/replay for stable failure records.
- Hooks come last because they change the Claude Code session experience.

---

## 4. Phase 0: Baseline Audit and Test Freeze

### 4.1 Goal

Establish the functional baseline before code changes so regressions can be identified.

### 4.2 Change Scope

Prefer no runtime changes; add/update documentation and test inventories only:

- `docs/architecture/plugin-runtime-hardening-plan-2026-06-04.md`
- Optionally update `docs/README.md`

### 4.3 Work Items

1. Record current CLI commands.
2. Record existing Skills, Agents, and Dashboard APIs.
3. Run a minimal test set:
   - `test_webnovel_unified_cli.py`
   - `test_story_runtime_health.py`
   - `test_chapter_commit_service.py`
   - `test_event_projection_router.py`
   - `test_rag_adapter.py`
   - `test_dashboard_app.py`
4. Check uncommitted repository changes to avoid overwriting user work.

### 4.4 Impact

No user-visible behavior changes.

### 4.5 Acceptance

- Record baseline test results.
- Identify which failures are pre-existing.

---

## 5. Phase 1: `project_phase` / `project-status` / `webnovel-doctor`

### 5.1 Goal

Add a unified phase resolver, short-status entry, and read-only diagnostics answering:

- What phase is the project in?
- Which files should exist in this phase?
- Are directories, JSON, SQLite, RAG, Python dependencies, and Dashboard configuration complete?
- How can missing/broken items be repaired?

Clarify the relationship to two existing entries first:

- `webnovel.py preflight`: Existing quick environment checks; preserve and reuse.
- `webnovel.py status`: Forwards to `scripts/status_reporter.py` for high-level creative health; preserve rather than repurpose.

### 5.2 Change Scope

Add:

- `webnovel-writer/scripts/data_modules/project_phase.py`
- `webnovel-writer/scripts/data_modules/project_status.py`
- `webnovel-writer/scripts/data_modules/doctor.py`
- `webnovel-writer/scripts/data_modules/tests/test_project_phase.py`
- `webnovel-writer/scripts/data_modules/tests/test_project_status.py`
- `webnovel-writer/skills/webnovel-doctor/SKILL.md`
- `webnovel-writer/scripts/data_modules/tests/test_doctor.py`

Modify:

- `webnovel-writer/scripts/data_modules/webnovel.py`
- `docs/guides/commands.md`
- `docs/README.md`

Reusable:

- Existing `_build_preflight_report()` in `webnovel.py`
- `story_runtime_health.py`
- `story_runtime_sources.py`
- `config.py`
- Dashboard patterns in `_inspect_vector_db()` / `_build_env_status()`

### 5.3 Detailed Work

1. Implement shared `project_phase.py`:
   - One phase vocabulary.
   - No state-file writes.
   - Shared by doctor / project-status / write-gate.
2. Implement `project-status`:
   - `webnovel.py project-status --format json|summary`
   - Preserve `webnovel.py status` forwarding and `status_reporter.py` semantics.
   - Output latest accepted chapter, target chapter, phase, warnings, next action.
3. Implement `doctor` data models:
   - `DoctorReport`
   - `DoctorCheck`
   - `RepairSuggestion`
   - `ExpectedFiles`
4. Infer phases in `project_phase.py`:
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
5. Implement phase-aware expected files:
   - After init, require only scaffold, `state.json`, setting bible, master outline, `.env.example`.
   - Init does not require commits, summaries, memory, or vectors.
   - Increase requirements gradually through plan / write / commit.
6. Implement file checks:
   - Directory existence.
   - JSON readability.
   - Required fields.
7. Implement SQLite checks:
   - Can `index.db` be opened?
   - Do key tables exist?
   - Row counts.
   - Can `vectors.db` be opened, and does it contain `vectors`?
8. Implement system-configuration checks:
   - Python version.
   - Core-package imports.
   - RAG environment / `.env` configuration.
   - Dashboard dist / requirements / package.json.
9. Register in the unified CLI:
   - `webnovel.py project-status --format json|summary`
   - `webnovel.py doctor --format json|text`
   - `webnovel.py doctor --chapter N --format json|text`
   - `webnovel.py doctor --deep --format json|text`
10. Add `/webnovel-doctor` Skill:
   - Read-only.
   - No repairs.
   - Output conclusion, impact, suggested commands.

### 5.4 Impact

User impact:

- New diagnostic command; existing workflow unchanged.
- New short `project-status`; existing `status` health report unchanged.
- Users see what is missing, its impact, and how to fix it.

Code impact:

- Add `project-status` and `doctor` subcommands to `webnovel.py`.
- Add read-only `doctor.py`.
- Add shared phase resolver.
- Do not modify commits, state, index, summaries, or memory.

Risks:

- Incorrect phase inference causes false alarms.
- Overstrict table inventories can misclassify old projects as broken.
- Confusion between `project-status` and `status_reporter.py`.

Controls:

- Run only low-risk checks when phase is uncertain.
- Missing later-stage artifacts during init yield only `skip/info`.
- Separate `required` and `observed` tables so missing legacy tables do not automatically block.
- Use `project-status`; preserve `status` semantics.
- Reuse `_build_preflight_report()` for quick doctor checks to prevent preflight/doctor drift.

### 5.5 Acceptance

- Empty directory returns `no_project` without traceback.
- `webnovel.py status` still runs existing `status_reporter.py`.
- `webnovel.py project-status --format json` returns the unified phase.
- `preflight` works and agrees with quick doctor checks.
- Just-completed init returns `init_scaffolded` or `init_ready`.
- Missing commit / summary / vectors immediately after init does not block.
- Missing key `index.db` tables produce names, impact, and repair advice.
- Missing RAG key produces a warning explaining BM25 fallback.
- Default mode performs no network access, file writes, installations, or service starts.
- Chinese Windows paths do not fail from default encoding.

### 5.6 Rollback

- Remove CLI registration for `doctor` / `project-status`.
- Unused `doctor.py` can remain without affecting existing flows.
- Unused `project_phase.py` can remain without affecting existing flows.
- Removing `/webnovel-doctor` leaves the original plugin workflow usable.

---

## 6. Phase 2: Artifact Validator

### 6.1 Goal

Unify agent-artifact validation to prevent field drift in `review_result`, `fulfillment_result`, `disambiguation_result`, and `extraction_result`.

### 6.2 Change Scope

Add:

- `webnovel-writer/scripts/data_modules/artifact_validator.py`
- `webnovel-writer/scripts/data_modules/tests/test_artifact_validator.py`

Possible modifications:

- `chapter_commit_service.py`
- `chapter_commit.py`
- `chapter_commit_schema.py`

### 6.3 Detailed Work

1. Define unified error types:
   - `schema_error`
   - `missing_artifact`
   - `blocking_review`
   - `missed_outline_node`
   - `pending_disambiguation`
   - `projection_failure`
2. Wrap existing Pydantic schemas, using the commit models in `chapter_commit_schema.py` as authority:
   - `ReviewResult`
   - `FulfillmentResult`
   - `DisambiguationResult`
   - `ExtractionResult`
3. Clarify boundaries of same/similar-name models:
   - `review_schema.py` contains reviewer / review-pipeline-local models.
   - Disambiguation models in `entity_linker.py` are local to entity linking.
   - artifact_validator uses only commit-artifact schemas as final submission authority.
4. Provide unified entry points:
   - `validate_review_result(path)`
   - `validate_fulfillment_result(path)`
   - `validate_disambiguation_result(path)`
   - `validate_extraction_result(path)`
   - `validate_chapter_commit(path)`
5. Support known legacy fields and provide clear diagnostics when incompatible.

### 6.4 Impact

User impact:

- Detect agent-output errors earlier, before commit.
- Replace Python tracebacks with structured explanations.

Code impact:

- Gradually make `chapter_commit_service` depend on validator.
- Later `write-gate` reuses validator to reduce duplication.

Risks:

- Overstrict schemas may block legacy artifacts.
- Choosing the wrong same-name model creates new drift.

Controls:

- Initial version supports legacy fields or warns.
- Block only errors clearly affecting commit correctness.
- Pin `chapter_commit_schema.py` as authority in comments/tests.

### 6.5 Acceptance

- Missing artifact returns `missing_artifact`.
- Incorrect outer JSON wrapper returns `schema_error`.
- Nonempty `disambiguation.pending` blocks.
- Reviewer blocking issue blocks.
- Do not mix same-name `ReviewResult` / `DisambiguationResult` models.

### 6.6 Rollback

- Keep the old validation path in `chapter_commit_service`.
- If validator is faulty, use it only for doctor/gate reporting without blocking commits.

---

## 7. Phase 3: Runtime Gates

### 7.1 Goal

Add critical-boundary chapter validation:

- `prewrite`
- `precommit`
- `postcommit`

### 7.2 Change Scope

Add:

- `webnovel-writer/scripts/data_modules/write_gates/__init__.py`
- `webnovel-writer/scripts/data_modules/write_gates/prewrite.py`
- `webnovel-writer/scripts/data_modules/write_gates/precommit.py`
- `webnovel-writer/scripts/data_modules/write_gates/postcommit.py`
- `webnovel-writer/scripts/data_modules/tests/test_write_gates.py`

Modify:

- `webnovel-writer/scripts/data_modules/webnovel.py`
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- `docs/guides/commands.md`

Reuse:

- `webnovel-writer/scripts/data_modules/prewrite_validator.py`
- `webnovel-writer/scripts/data_modules/tests/test_prewrite_validator.py`

### 7.3 Detailed Work

1. Register CLI:
   - `webnovel.py write-gate --chapter N --stage prewrite --format json`
   - `webnovel.py write-gate --chapter N --stage precommit --format json`
   - `webnovel.py write-gate --chapter N --stage postcommit --format json`
2. `prewrite` must wrap `PrewriteValidator`:
   - Project root.
   - Whether phase permits writing.
   - Story System contract completeness.
   - Placeholder blockers.
3. `precommit` checks:
   - Prose file.
   - review / fulfillment / disambiguation / extraction artifacts.
   - Artifact validator.
   - Blocking issues.
4. `postcommit` checks:
   - Commit file.
   - `projection_status`.
   - Basic existence of summary / index / memory / backup.
5. Update `/webnovel-write`:
   - Manage progress with Claude Code Todo.
   - Call gates only at natural boundaries.

### 7.4 Impact

User impact:

- Add 2-3 deterministic checks to chapter writing.
- Clearer precommit errors.

Code impact:

- `/webnovel-write` execution guidance changes.
- Add a `webnovel.py` subcommand.
- Existing `PrewriteValidator` underpins prewrite gate, preventing divergent implementations.

Risks:

- Overstrict gates disrupt writing.
- Overly permissive gates fail to improve reliability.
- Rewriting prewrite logic risks drift from `PrewriteValidator`.

Controls:

- Initially block only clearly untrustworthy states.
- Warnings do not block.
- Every gate supplies repair advice.
- Adapt existing validator output; do not rewrite prewrite.

### 7.5 Acceptance

- Missing review artifact yields `precommit.ok=false`.
- Blocking review yields `precommit.ok=false`.
- Pending disambiguation yields `precommit.ok=false`.
- Failed projection yields `postcommit.ok=false`.
- Calling `prewrite` during init gives a clear next step.
- Existing `test_prewrite_validator.py` keeps passing.

### 7.6 Rollback

- Temporarily restore the old `/webnovel-write` workflow.
- Retain CLI subcommands without Skill invocation.

---

## 8. Phase 4: Projection Log

### 8.1 Goal

Separate commit facts from projection execution state, reducing confusion from storing both in commit files.

Confirm real pain points before implementation:

- Have failed projections been impossible to trace to a writer?
- Has commit `projection_status` disagreed with actual read models?
- Do Dashboard / doctor genuinely need cross-writer execution history?

Without a real need, defer this phase and keep doctor diagnostics on existing `projection_status`.

### 8.2 Change Scope

Add:

- `webnovel-writer/scripts/data_modules/projection_log.py`
- `webnovel-writer/scripts/data_modules/tests/test_projection_log.py`

Modify:

- `chapter_commit_service.py`
- `event_projection_router.py`
- `story_runtime_health.py`
- `doctor.py`
- `dashboard/app.py`

### 8.3 Detailed Work

1. Add JSONL projection log:
   - `.webnovel/projection_log.jsonl`
2. Define run schema:
   - `run_id`
   - `chapter`
   - `commit_path`
   - `commit_hash`
   - `writer`
   - `status`
   - `started_at`
   - `finished_at`
   - `error`
3. Write one log per writer in `chapter_commit_service.apply_projections()`.
4. Continue dual-writing commit `projection_status`.
5. doctor prefers projection logs and falls back to commit fields.
6. Add compatible Dashboard reads without a redesign.

### 8.4 Impact

User impact:

- Identify the specific failed writer.
- Chapter-commit command unchanged.

Data impact:

- Add `.webnovel/projection_log.jsonl`.
- Do not remove commit fields yet.

Risks:

- Dual-write inconsistency.
- Slightly more complex Dashboard reads.
- Projection logs create a second execution-state source.

Controls:

- Log-write failure must warn, but not disrupt the main commit workflow.
- doctor reports dual-write inconsistencies.
- Explicit decision gate: implement only when benefits outweigh dual-write complexity.

### 8.5 Acceptance

- Every writer has a projection log.
- One failed writer does not affect other records.
- doctor identifies failed writers.
- Commit `projection_status` remains.

### 8.6 Rollback

- Dashboard and doctor fall back to commit `projection_status`.
- Removing projection logs does not affect commit reads.

---

## 9. Phase 5: Projection Retry / Replay

### 9.1 Goal

Retry failed projections by writer, especially vector / summary / memory.

This is the highest-risk phase; audit and test writer idempotency first.

### 9.2 Change Scope

Add:

- `webnovel-writer/scripts/data_modules/projection_runner.py`
- `webnovel-writer/scripts/data_modules/tests/test_projection_runner.py`

Modify:

- `event_projection_router.py`
- `webnovel.py`
- Projection-writer tests

### 9.3 Detailed Work

1. Add CLI:
   - `webnovel.py projections status --chapter N`
   - `webnovel.py projections retry --chapter N --writer vector`
   - `webnovel.py projections retry-failed --chapter N`
   - `webnovel.py projections replay --from 1 --to 20 --writers state,index,summary`
2. Audit idempotency of five writers first:
   - `state`
   - `index`
   - `summary`
   - `memory`
   - `vector`
3. Add idempotency tests, focusing on:
   - Duplicate character-count accumulation.
   - Duplicate relationship/event insertion.
   - Duplicate memory accumulation.
   - Duplicate vector chunks.
4. Runner reads accepted commits only.
5. Retry never changes commit facts.
6. Log retry results and compatibly update legacy `projection_status`.

### 9.4 Impact

User impact:

- External-dependency failures no longer require rewriting chapters.
- Retry vector / summary independently.

Data impact:

- Projection read models may be rebuilt.
- Ensure idempotency to avoid duplicate counts/relationships.

Risks:

- Insufficient idempotency creates duplicates.
- Incorrect replay commands affect more than a single chapter commit.

Controls:

- Add separate idempotency tests for state/index/summary/memory/vector first.
- Replay requires an explicit chapter range by default.
- No unbounded whole-book replay by default.

### 9.5 Acceptance

- Retry summary restores a deleted summary.
- Replaying the same chapter does not duplicate state / index / memory / vector data.
- Missing vector key leaves vector failed and other writers done.
- After configuring the key, retry vector updates only vector.
- After replay, state/index/summary match the commit chain.

### 9.6 Rollback

- Hide or disable projections CLI.
- Continue the old chapter-commit workflow.

---

## 10. Phase 6: Stronger Skill / Agent Contracts

### 10.1 Goal

Strengthen Skill / Agent triggering, tool scope, and output contracts under official `plugin-dev`.

### 10.2 Change Scope

Modify:

- `webnovel-writer/skills/*/SKILL.md`
- `webnovel-writer/agents/*.md`
- `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`

Optional additions:

- `webnovel-writer/agents/continuity-reviewer.md`
- `webnovel-writer/agents/style-reviewer.md`
- `webnovel-writer/agents/reader-pull-reviewer.md`

### 10.3 Detailed Work

1. Skill frontmatter:
   - Strengthen `description` with triggers and exclusions.
   - Keep `SKILL.md` concise.
   - Move long rules to `references/`.
2. Agent frontmatter:
   - Add `name`.
   - Add concrete `description`.
   - Specify `tools`.
   - Add `model` when needed.
3. Agent output contracts:
   - Fixed reviewer output dimensions.
   - data-agent explicitly produces artifacts only, never writes projections.
   - context-agent specifies context priority.
4. Validate manually or programmatically using plugin-dev validate-agent rules.

### 10.4 Impact

User impact:

- More reliable Claude Code Skill/Agent triggering.
- Fewer false/missed triggers.

Code impact:

- Primarily prompt / Markdown changes.
- May affect Claude Code selection behavior.

Risks:

- Description changes alter triggering patterns.

Controls:

- Change and test one group at a time.
- Add prompt-integrity tests.
- Keep command names unchanged.

### 10.5 Acceptance

- All seven Skills have clear trigger-oriented descriptions.
- All four existing Agents have plugin-dev-compliant frontmatter.
- Prompt-integrity tests pass.
- data-agent documentation still explicitly prohibits state/index/summary/memory writes.

### 10.6 Rollback

- Roll back frontmatter independently per Skill / Agent.
- Python runtime unaffected.

---

## 11. Phase 7: Behavior Evals

### 11.1 Goal

Verify actual plugin behavior against protocols, not just Python functions.

### 11.2 Change Scope

Add:

- `webnovel-writer/evals/`
- `webnovel-writer/scripts/run_behavior_evals.py`
- `webnovel-writer/evals/fixtures/`

Modify:

- CI / local testing documentation.
- `docs/operations/operations.md`

### 11.3 Detailed Work

1. Establish eval categories:
   - skill triggering
   - workflow behavior
   - agent output schema
   - continuity conflict
   - memory commit
2. Initial cases:
   - init does not contaminate the plugin directory.
   - write does not commit with a blocking issue.
   - data-agent does not write projections.
   - Commit drives projection.
   - Dashboard is read-only.
3. Runner emits JSON reports.
4. Separate fast fixture evals from slow transcript evals.

### 11.4 Impact

User impact:

- No direct usage changes.
- Greater pre-release reliability.

Code impact:

- More test assets.
- CI may take longer.

Risks:

- Transcript evals are expensive and slow.

Controls:

- Run only fast evals by default.
- Slow evals run manually or before releases.

### 11.5 Acceptance

- At least one eval per Skill.
- `/webnovel-write` covers success and blocking paths.
- Eval reports contain pass/fail/reason/artifacts.

### 11.6 Rollback

- Evals outside the default workflow can temporarily be skipped.
- Runtime unaffected.

---

## 12. Phase 8: Package Validator

### 12.1 Goal

Prevent manifest, marketplace, README, version, and frontmatter drift.

### 12.2 Change Scope

Add:

- `webnovel-writer/scripts/validate_plugin_package.py`
- `webnovel-writer/scripts/tests/test_validate_plugin_package.py`

Modify:

- `docs/operations/plugin-release.md`
- `docs/guides/commands.md`

### 12.3 Detailed Work

1. Check `.claude-plugin/plugin.json`:
   - Kebab-case name.
   - Semver version.
   - Nonempty description.
2. Check marketplace files.
3. Reuse/align with existing Plugin Version Check:
   - Marketplace version.
   - plugin.json version.
   - Existing README version locations/tables.
   - Do not add README-badge rules conflicting with current CI.
4. Check Skill frontmatter.
5. Check Agent frontmatter.
6. Check hook schema.
7. Check LICENSE.
8. Check Dashboard dist.
9. Reject hardcoded machine-local absolute paths.

### 12.4 Impact

User impact:

- More stable release packages.

Code impact:

- New pre-release validator.

Risks:

- Overstrict rules impede development.
- Version rules differing from CI can pass locally and fail in CI, or vice versa.

Controls:

- Separate `--strict` from default mode.
- Block only obvious errors by default.
- Read existing CI/release documentation before implementing version checks.

### 12.5 Acceptance

- Validation passes on a clean clone.
- Any version drift fails.
- Version-drift rules match current CI.
- Missing Skill frontmatter fails.
- Hook paths without `${CLAUDE_PLUGIN_ROOT}` warn or fail.

### 12.6 Rollback

- Temporarily remove validator from release flow.
- Plugin operation unaffected.

---

## 13. Phase 9: Hooks

### 13.1 Goal

Use Phase 1 `project-status` for lightweight summaries and fallback warnings/blocks against dangerous runtime-bypassing writes.

### 13.2 Change Scope

Add:

- `webnovel-writer/hooks/hooks.json`
- `webnovel-writer/hooks/session_start.py`
- `webnovel-writer/hooks/scripts/guard-runtime-write.py`

Modify:

- `webnovel-writer/scripts/data_modules/webnovel.py`
- `webnovel-writer/.claude-plugin/plugin.json`, only if an explicit hook path is needed.
- `docs/operations/operations.md`

### 13.3 Detailed Work

1. `SessionStart` hook:
   - Short summary only.
   - No file writes.
   - No full doctor run.
   - Call `webnovel.py project-status --format summary`.
   - Disable through environment variable.
2. `PreToolUse` hook:
   - Block direct `.story-system/commits` writes.
   - Block direct `.webnovel/state.json`, `index.db`, `memory_scratchpad.json` writes.
   - Best-effort detection of dangerous gate-bypassing commit/projection Bash commands.
   - Do not treat Bash string parsing as the sole hard guarantee.
3. Validate against plugin-dev hook-development:
   - Wrapper format in `hooks/hooks.json`.
   - Hook commands use `${CLAUDE_PLUGIN_ROOT}`.
   - Hook scripts validate stdin JSON.

### 13.4 Impact

User impact:

- New sessions show short status.
- Direct main-chain/projection edits are blocked or redirected through runtime.

Code impact:

- Add hooks directory.
- One additional lightweight command at Claude Code session start.

Risks:

- Long hook output consumes context.
- False blocks interfere with developer debugging.
- Too many Bash variants to reliably detect every bypass.

Controls:

- Limit output to 8 lines / 1,000 characters.
- Provide a disabling environment variable.
- Initially block only the most dangerous paths.
- Runtime gates and commit entry remain the real reliability guarantee.

### 13.5 Acceptance

- No error when no project root exists.
- With a project root, output latest chapter / phase / next action.
- No output when disabled by environment.
- Direct commit-file writes are blocked.
- Valid runtime commands are not blocked.
- `webnovel.py status` retains high-level creative-health semantics.

### 13.6 Rollback

- Remove or disable `hooks/hooks.json`.
- Keeping `project-status` CLI does not affect old flows.

---

## 14. Cross-Cutting Impact

### 14.1 Ownership of Health Entry Points

| Entry | Current/target responsibility | Output | Deep checks? | File writes? |
|---|---|---|---|---|
| `preflight` | Quick environment checks, backward compatible | text/json | No | No |
| `project-status` | Machine-readable short status, phase, next step | summary/json | No | No |
| `doctor` | File/database/configuration diagnostics and repairs advice | text/json | No by default; optional `--deep` | No |
| `status` / `status_reporter.py` | High-level creative health: characters, foreshadowing, payoffs, relationships | markdown/text | Yes, creative analysis | May currently write reports; preserve semantics |
| `build_story_runtime_health()` | Internal main-chain readiness helper | dict | No | No |

Principles:

- Do not cram every problem into one command.
- Preserve existing `status` semantics.
- doctor reuses preflight/story runtime health rather than duplicating logic.

### 14.2 User Commands

New commands:

- `/webnovel-doctor`
- `webnovel.py doctor`
- `webnovel.py write-gate`
- `webnovel.py projections`
- `webnovel.py project-status`

Retained commands:

- `/webnovel-init`
- `/webnovel-plan`
- `/webnovel-write`
- `/webnovel-review`
- `/webnovel-query`
- `/webnovel-dashboard`
- `/webnovel-learn`

Existing `webnovel.py status` keeps forwarding to `status_reporter.py`.

### 14.3 Project Data

New files:

- `.webnovel/projection_log.jsonl`
- Possible validation conventions for `.webnovel/tmp/*`.

Unchanged:

- `.story-system/` remains the main-chain source of truth.
- Accepted commits are the post-writing fact entry point.
- `.webnovel/*` remains projection / read-model data.

### 14.4 Dashboard

Short term:

- Dashboard remains read-only.
- Continue supporting commit `projection_status`.

Medium term:

- Dashboard can display projection logs.
- System page can show doctor / project-status summaries.

Risks:

- Dashboard frontend bundle may need rebuilding.

### 14.5 RAG

Default:

- Missing key falls back to BM25.
- Missing `vectors.db` only warns.

Deep checks:

- Only then test API connectivity.

### 14.6 Testing

The substantial new tests need layers:

- Unit: doctor / validator / gates / projection log.
- Integration: chapter commit + projection.
- Behavior: Skill / Agent protocols.
- Release: package validator.

---

## 15. Suggested PR Breakdown

### PR 1: Phase Resolver + Project Status + Doctor

Includes:

- Shared `project_phase`.
- `project-status` CLI.
- Doctor runtime.
- Doctor CLI.
- `/webnovel-doctor` Skill.
- Doctor tests.
- Reuse of preflight quick checks.

Excludes:

- write-gate.
- Projection log.
- Hooks.

### PR 2: Validator + Gates

Includes:

- Artifact validator.
- Write gates.
- Prewrite gate wrapping existing `PrewriteValidator`.
- `/webnovel-write` update.
- Gate tests.

### PR 3: Projection Writer Idempotency Audit

Includes:

- Idempotency tests for state / index / summary / memory / vector.
- Replay risk assessment.

### PR 4: Projection Log

Includes:

- Projection log.
- Chapter-commit dual writes.
- Compatible doctor / Dashboard reads.

### PR 5: Projection Retry / Replay

Includes:

- Projection runner.
- Projections CLI.
- Writer idempotency tests.

### PR 6: Skill / Agent Contracts

Includes:

- Skill frontmatter.
- Agent frontmatter.
- Prompt-integrity tests.

### PR 7: Evals + Package Validator

Includes:

- Behavior eval runner.
- Plugin-package validation.
- Release documentation.

### PR 8: Hooks

Includes:

- SessionStart hook.
- PreToolUse guard.
- plugin-dev hook validation.

---

## 16. Overall Acceptance

On completion:

1. Users can run `/webnovel-doctor` and understand file/database/configuration health.
2. `project-status` gives short status without repurposing `status_reporter.py`.
3. Missing commit / summary / vectors immediately after init causes no false alarm.
4. Chapter writing adds gates only at three natural boundaries.
5. Agent-artifact schema errors are reported consistently.
6. Projection failures identify the writer and can be retried.
7. Commit facts and projection execution logs are distinguishable.
8. Skill / Agent / Hook structure follows official `plugin-dev`.
9. Package consistency can be verified before release.

---

## 17. Minimal Initial Version

For a quick, high-value initial release, prioritize the following items:

1. `doctor`
2. `project-status` / `project_phase`
3. `artifact_validator`
4. `write-gate`

These address the core problems first:

- Users know where the project is broken.
- Runtime and short status share the same phase model.
- Runtime can determine whether agent artifacts are trustworthy.
- Critical writing boundaries no longer depend only on documentation.

Projection logs, retry/replay, hooks, and evals can follow once the foundation is stable.
