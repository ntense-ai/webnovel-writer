# 2026-06-10 Full-Project Audit Remediation Plan

> **Status (closed out 2026-06-11):** This plan was curtailed by the v7 strangler-style consolidation (`docs/architecture/story-repo-spec-2026-06-10.md`).
> - **Completed and retained**: all of Phase 0 (Tasks 1–6, manuscript safety) + Task 7. These underpin v6 user data and the v7 migration reader.
> - **Canceled**: Tasks 8–24 (Phase 1 data pipeline), Tasks 26–27, and Tasks 29–34. Their target modules (SQLite projections, event log, v6 prompts, dashboard, CLI boilerplate) are removed wholesale in v7 rather than repaired.
> - **Exceptions retained as independent candidates**: Task 25 (embedding network egress by default, a privacy issue; mandatory if another v6 maintenance release ships), Task 28 (repository-level CI hardening, reused by v7 and independently actionable at any time).
> - Branch `fix/audit-2026-06-10` closes with Phase 0 + Task 7 merged into master as the final v6 data-safety maintenance batch.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all high/medium-risk issues found in the 2026-06-10 deep audit: data-loss paths, inconsistent data pipelines, skill workflow deadlocks, default privacy-related network egress, and guard bypasses.

**Architecture:** Four phases ordered by harm (P0 data safety → P1 data pipeline and workflow → P2 security/privacy → P3 quality/hygiene). Each phase is independently deliverable; proceed only after all checks pass. Follow “write a probe test reproducing the problem → fix → verify”. Rewrite obsolete wording assertions directly under the principle “tests are probes, not constraints”.

**Tech Stack:** Python 3.10+ / pytest (set `PYTHONUTF8=1` on Windows) / SQLite / FastAPI.

**Audit sources:** Findings from six dimensions in the 2026-06-10 session: data pipeline, prompts, code quality, dashboard+hooks, data safety+CI, and repository hygiene+residual modules.

**Run tests:** `python -m pytest` (root pytest.ini configures testpaths and cov-fail-under=90).

---

## Phase 0 — P0 Data Safety (manuscripts are irreplaceable data)

### Task 1: backup_manager must not report success after backup failure

**Files:**
- Modify: `webnovel-writer/scripts/backup_manager.py:150-166, 228-254`
- Test: `webnovel-writer/scripts/tests/test_backup_manager.py`

- [x] **Step 1: Write a failing test**: intentionally leave `user.name/user.email` unset in a temporary Git repository (`git config --local --unset` or `-c user.useConfigOnly=true`), call `backup()`, and assert failure, output containing the exact message `备份失败` (“backup failed”), and no `ch{N}` tag.
- [x] **Step 2: Run to confirm the false-success behavior** (currently prints ✅ and tags the old HEAD).
- [x] **Step 3: Fix `_run_git_command`**: change the `check=False` branch to return `(result.returncode == 0, stdout, stderr)`; callers use the real exit code. Detect “nothing to commit” from stdout/stderr text (the current `:233` `if not success and "nothing to commit"` is permanently false dead code; remove and rewrite it):

```python
def _run_git_command(self, args, check=True):
    result = subprocess.run(
        ["git", *args], cwd=self.project_root,
        capture_output=True, text=True, encoding="utf-8",
    )
    ok = result.returncode == 0
    if check and not ok:
        raise BackupError(f"git {' '.join(args)} 失败: {result.stderr.strip()}")
    return ok, result.stdout, result.stderr
```

- [x] **Step 4: Abort `backup()` if commit fails**: do not tag; return nonzero; output repair guidance (`git config user.name/user.email`). Treat “nothing to commit” as success but report “no changes in this chapter”.
- [x] **Step 5: After all backup tests pass, commit** `fix: backup reports real git failures and aborts tagging`.

### Task 2: Make rollback a forward-restoring operation; remove detached HEAD and hardcoded master

**Files:**
- Modify: `webnovel-writer/scripts/backup_manager.py:294-307`
- Test: `webnovel-writer/scripts/tests/test_backup_manager.py`

- [x] **Step 1: Write tests**: create a temporary repository with default branch `main`, create two chapter tags, and roll back to ch1. Assert (a) still on original branch (`git symbolic-ref HEAD` succeeds and points to main); (b) working tree matches ch1; (c) `git log` has an additional “rollback” commit, preserving history.
- [x] **Step 2: Implement forward-only rollback**:

```python
def rollback(self, chapter: int) -> bool:
    tag = f"ch{chapter}"
    ok, _, _ = self._run_git_command(["rev-parse", "--verify", tag], check=False)
    if not ok:
        print(f"❌ 备份点 {tag} 不存在"); return False
    ok, _, err = self._run_git_command(["checkout", tag, "--", "."], check=False)
    if not ok:
        print(f"❌ 回滚失败: {err}"); return False
    self._run_git_command(["add", "-A"], check=False)
    ok, _, err = self._run_git_command(
        ["commit", "-m", f"rollback: 恢复到 {tag} 备份点"], check=False)
    # If the working tree already matches the tag, "nothing to commit" counts as success
    return True
```

- [x] **Step 3: Remove all hardcoded `checkout master`**; detect branch names using `git symbolic-ref --short HEAD` wherever needed.
- [x] **Step 4: After tests pass, commit** `fix: rollback is forward-only, never detaches HEAD`.

### Task 3: Degraded backup without Git must include manuscripts, or clearly state otherwise

**Files:**
- Modify: `webnovel-writer/scripts/backup_manager.py:175-195`
- Test: `webnovel-writer/scripts/tests/test_backup_manager.py`

- [x] **Step 1: Write test**: simulate unavailable Git (monkeypatch `_git_available` to False), with `正文/第0001章-x.md` in the project. After `backup()`, assert a copy of that manuscript exists in the backup directory.
- [x] **Step 2: Implement**: in degraded mode, copy `正文/`, `大纲/`, `设定集/`, and `.webnovel/state.json` using `shutil.copytree/copy2` into `.webnovel/backups/snapshot_ch{N}_{ts}/`. Explicitly list what was backed up. Retain count-based rotation (maximum ten snapshots).
- [x] **Step 3: Commit** `fix: degraded backup covers manuscript files`.

### Task 4: Rerunning init must not silently overwrite corrupt state.json

**Files:**
- Modify: `webnovel-writer/scripts/init_project.py:294-300,366`
- Test: `webnovel-writer/scripts/data_modules/tests/test_init_project_pruning.py`

- [x] **Step 1: Write test**: place invalid JSON in state.json, rerun init, and assert (a) a `state.corrupt_*.json` copy contains the original damaged text; (b) output includes a warning.
- [x] **Step 2: Implement**: upon `json.JSONDecodeError`, first call `shutil.copy2(state_path, state_path.with_name(f"state.corrupt_{ts}.json"))`, then rebuild. Print a warning that the original state.json was damaged and saved separately for manual recovery.
- [x] **Step 3: Commit** `fix: preserve corrupt state.json before rebuilding`.

### Task 5: Migration must not prune on errors; make writeback atomic

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/migrate_state_to_sqlite.py:235-258`
- Test: `webnovel-writer/scripts/data_modules/tests/test_migrate_state_to_sqlite.py`

- [x] **Step 1: Write test**: construct an entity that fails migration (e.g. invalid type triggers `stats["errors"] += 1`), run migration, and assert state.json retains `entities_v3` and CLI exits nonzero.
- [x] **Step 2: Implement**: if `stats["errors"]` is nonzero, skip Step 5 pruning and report “migration errors exist; original fields retained”. Replace Step 5's bare `open('w')+json.dump` with `security_utils.atomic_write_json(state_path, state, use_lock=True)`.
- [x] **Step 3: Commit** `fix: migration never prunes state on partial failure`.

### Task 6: Atomic archive_manager writes + reverse restoration order

**Files:**
- Modify: `webnovel-writer/scripts/archive_manager.py:125-128, 494-508`
- Test: `webnovel-writer/scripts/data_modules/tests/test_archive_manager.py`

- [x] **Step 1: Switch `save_archive` to `atomic_write_json`** (archive is the only copy after data leaves state).
- [x] **Step 2: Reverse `restore_character` ordering**: restore SQLite first; remove character from archive JSON only after success. If SQLite fails, leave archive unchanged and return an error. Test: monkeypatch SQLite restoration to raise, then assert archive unchanged.
- [x] **Step 3: Commit** `fix: archive writes atomic, restore is delete-last`.

---

## Phase 1 — P1 Data-Pipeline Consistency and Workflow Deadlocks

### Task 7: SQLite synchronization failures must be visible

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/state_manager.py:393-416, 450-451, 606-609`
- Test: `webnovel-writer/scripts/data_modules/tests/test_state_manager_extra.py`

- [x] If `_sync_to_sqlite` fails, `save_state` returns `sqlite_sync_ok=False`; `process-chapter` CLI calls `emit_error` (nonzero exit), advising `webnovel.py projections retry --chapter N` for compensation. Test: monkeypatch `_sync_pending_patches_to_sqlite` to raise; assert nonzero exit and recovery guidance in stdout JSON.
- [x] Commit `fix: surface sqlite sync failures in process-chapter`.

### Task 8: get_state_changes / get_relationships use SQLite fallback

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/state_manager.py:972-977, 1005-1013`
- Test: `webnovel-writer/scripts/data_modules/tests/test_state_manager_extra.py`

- [ ] Follow `get_entity`'s SQLite-first pattern: query `self._sql_state_manager.get_entity_state_changes / get_recent_relationships` first; fall back to memory if empty. Test: a fresh StateManager instance (simulating another process) reads previously saved state_changes; assert nonempty.
- [ ] Also change `record_state_change` (:953–966) to write only to `_pending_state_changes`; remove appending to `self._state["state_changes"]`.
- [ ] Commit `fix: state change reads hit sqlite, not stale memory`.

### Task 9: Delete then insert chapter event mirrors

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/event_log_store.py:109-146`
- Test: `webnovel-writer/scripts/data_modules/tests/test_event_log_store.py`

- [ ] Test: write events A for a chapter, then fully overwrite with events B (different event_id); assert only B remains in `story_events`. Implement `_write_sqlite_mirror` with `DELETE FROM story_events WHERE chapter = ?` followed by INSERT in the same transaction (the JSON file is the chapter's fact source).
- [ ] Commit `fix: event mirror mirrors, not accumulates`.

### Task 10: Projection writer reuses the monotonic chapter_status state machine

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/state_projection_writer.py:59-65, 95`
- Test: `webnovel-writer/scripts/data_modules/tests/test_projection_writers.py`

- [ ] Extract `StateManager.set_chapter_status` rank comparison into module-level `should_transition(old, new) -> bool` (same file or schemas.py), shared by both sites. Test: project accepted commit, then replay historical rejected commit; status must remain `chapter_committed`.
- [ ] Commit `fix: projection respects chapter status monotonicity`.

### Task 11: Standardize total_words on projection recalculation

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/state_manager.py:280-285`
- Test: rewrite existing assertions expecting incremental `update_progress` counting (probe principle)

- [ ] `update_progress` no longer adds to `total_words`; update only `current_chapter/last_updated`. Always recalculate word count fully in `StateProjectionWriter`. Grep the repository for `total_words` writes and confirm projection is the sole writer.
- [ ] Commit `fix: single source of truth for total_words`.

### Task 12: Include add_entity aliases in the pending transaction

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/state_manager.py:839-854`
- Test: `webnovel-writer/scripts/data_modules/tests/test_state_manager_extra.py`

- [ ] Append alias writes to `_pending_alias_entries`, then persist together in `_sync_pending_patches_to_sqlite`. Test: after `add_entity` but before `save_state`, query SQLite and assert alias absent; after `save_state`, assert present.
- [ ] Commit `fix: alias writes go through pending patch transaction`.

### Task 13: Standardize SQLite connections on WAL + busy_timeout + batch transactions

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/index_manager.py:626-634` (`_get_conn`)
- Test: existing regression tests suffice

- [ ] Execute `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=8000` in `_get_conn`. Replace per-method commits along projection paths with one connection and transaction (`IndexProjectionWriter.apply` holds one connection and passes it to write methods).
- [ ] Commit `perf: WAL + single transaction per projection`.

### Task 14: Locked projection_log appends + compaction

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/projection_log.py:101-119`
- Test: `webnovel-writer/scripts/data_modules/tests/test_projection_log.py`

- [ ] Hold `FileLock(path + ".lock")` before appending; add `compact_projection_log(project_root, keep_per_chapter=3)` and expose it as `webnovel.py projections compact`. Test: write five runs for one chapter, compact, and assert only the latest three remain.
- [ ] Commit `fix: projection log locked appends + compact command`.

### Task 15: Guard the legacy commit path

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/memory_contract_adapter.py:71-120, 147-156`
- Test: `webnovel-writer/scripts/data_modules/tests/test_memory_contract_adapter.py`

- [ ] At `_commit_chapter_legacy` entry, reject execution if an accepted commit file already exists for the chapter, explaining that a Story System mainline chapter cannot be double-written through legacy. Mark docstring deprecated.
- [ ] `chapter_commit_service.py:182-188`: persist amend proposals only after successful projection (or include `projection_run_id` and exclude proposals for failed runs from pending until `projections retry` succeeds). Test: if all projections fail, override_ledger gains no new pending proposal.
- [ ] Commit `fix: legacy commit path refuses to double-write mainline chapters`.

### Task 16: Remove dangerous dead code

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/state_manager.py:708-711`

- [ ] Delete `_save_state` (no repository callers; bypasses pending-merge semantics). Grep to confirm no references, then commit `chore: remove dangerous dead _save_state`.

### Task 17: Resolve the write SKILL blocking deadlock

**Files:**
- Modify: `webnovel-writer/skills/webnovel-write/SKILL.md` (L162 Step 3, L245, L327–331)
- Test: `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py` (update related assertions if any)

- [ ] Change Step 3: after targeted blocking fixes, **rerun review-pipeline to regenerate review_results.json**, clearing fixed issues, before Step 4. Add an “author chooses to retain current version” exit: reference `references/review/blocking-override-guidelines.md`, explain recording via override ledger commands and passing `--override-ref` to commit. Both paths must agree with `chapter_commit_service.py:45`'s `rejected = bool(review.blocking_count)` decision. Verify override support in the service; if absent, add override_ref exemption logic. Read `chapter_commit_service.py` and `override_ledger_service.py` before drafting changes.
- [ ] Commit `fix(skill): unblock the blocking-fix path in write flow`.

### Task 18: Correct erroneous prompt commands

**Files:**
- Modify: `webnovel-writer/skills/webnovel-query/SKILL.md:78`, `webnovel-writer/agents/reviewer.md:30`

- [ ] Change `memory-contract query-rules --chapter {n}` to `--domain {domain}` (compare actual arguments in `memory_cli.py:90`); add required `--entity "{entity_id}"` to reviewer.md's `index get-state-changes --limit 20`. Execute each locally once to verify no argparse error.
- [ ] Commit `fix(skill): correct CLI invocations in query skill and reviewer agent`.

### Task 19: Align unified entrypoint and chapter_commit argument contracts

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/webnovel.py:554-559` or `webnovel-writer/scripts/chapter_commit.py:23-26`
- Test: `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`

- [ ] Make them required consistently (recommended, enforcing the contract): add `required=True` to the four arguments in `webnovel.py`. Missing-argument errors should occur at the unified entrypoint and be author-friendly. Test: call without `--review-result`; assert error includes argument name and example.
- [ ] Commit `fix: align chapter-commit arg contract between entrypoints`.

### Task 20: Repair dead genre-profiles paths (restore genre profiles)

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/config.py` (add `references_dir` resolution), `webnovel-writer/scripts/data_modules/context_manager.py:337-338`, `webnovel-writer/scripts/data_modules/memory_contract_adapter.py:245`
- Test: `webnovel-writer/scripts/data_modules/tests/test_context_manager.py`

- [ ] Add config resolution order: `{project_root}/.claude/references/` (user override) → `{plugin_root}/references/` (default, derived from `Path(__file__).resolve().parents[2] / "references"`). Both readers use `config.references_dir / "genre-profiles.md"`.
- [ ] Retain tests manually constructing `.claude/references` to verify override priority; add a test falling back to plugin directory when project-level files are absent.
- [ ] Commit `fix: genre profiles resolve to plugin references by default`.

### Task 21: Fix story_system_engine's always-empty base_context bug

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/story_system_engine.py:125, 412-423`
- Test: `webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py`

- [ ] `_apply_reasoning`'s early-return branch must also set `_priority_rank` per row: base_context rows get 0, dynamic rows 1 (base retains priority), so `build()`'s `< 999` filter does not wrongly discard them. Test: run `build()` for a genre without adjudication-rule rows; assert nonempty `master_setting.base_context`.
- [ ] Commit `fix: base_context survives the no-reasoning path`.

### Task 22: Deduplicate extract_chapter_context payload

**Files:**
- Modify: `webnovel-writer/scripts/extract_chapter_context.py:321-354`
- Test: `webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py`

- [ ] Choose between top-level `outline`/`previous_summaries`/`state_summary` and `core.*`: retain `core.*` (already ordered by ContextManager), remove top-level fields, and update consumers (first grep context-agent.md to identify referenced keys). Test: outline text appears only once in payload.
- [ ] Commit `fix: dedupe chapter context payload`.

### Task 23: Unify foreshadowing urgency units

**Files:**
- Modify: `webnovel-writer/skills/webnovel-query/references/advanced/foreshadowing.md`

- [ ] Use a 0–100 scale: `urgency = min(100, (elapsed chapters / target chapters) × tier weight × 33.3)`, or use a threshold table aligned with `urgency_utils` high/medium/low≈100/60/20. Remove “core unresolved >50 chapters is Critical”, which contradicts “core 50–300 chapters”; replace with “Critical when the thread's own target chapter count is exceeded”. Recalculate examples.
- [ ] Commit `fix(ref): foreshadowing urgency uses runtime 0-100 scale`.

### Task 24: Batch miscellaneous correctness fixes

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/rag_adapter.py:1477, 615-649`, `api_client.py` (nine print sites), `knowledge_query.py:17,46`, `webnovel.py:127, 583`, `update_state.py:344-351,609-611`, `config.py:30-48,60`, `context_manager.py:790-829`
- Test: corresponding test files

- [ ] In rag_adapter `index-chapter`, replace undefined `config` with `adapter.config.project_root`; rename row-unpacked `chapter` in `vector_search` to `row_chapter`.
- [ ] Send all api_client `[WARN]/[ERR]/[WARMUP]` output to `file=sys.stderr`.
- [ ] knowledge_query checks `is_file()` before connecting; if absent, give a friendly error with repair advice.
- [ ] For `webnovel.py`'s `int(e.code or 0)`, print non-integer codes and return 1; add `required=True` to `knowledge` subparsers.
- [ ] Accumulate update_state `update_strand_tracker` failures and exit nonzero.
- [ ] Strip config `.env` values with `strip().strip("\"'")`; move `_load_dotenv` from import time to an explicit call in `from_project_root`.
- [ ] Use `sys.exit(1)` on context_manager CLI failure paths.
- [ ] Add a probe in the matching test file before every fix. Commit `fix: batch correctness fixes from audit`.

---

## Phase 2 — P2 Security and Privacy

### Task 25: Embedding network egress requires explicit configuration

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/api_client.py` (embed/rerank call entrypoints), `vector_projection_writer.py:236-246`
- Test: `webnovel-writer/scripts/data_modules/tests/test_vector_projection_writer.py`
- Docs: `webnovel-writer/README.md`, `docs/guides/rag-and-config.md`

- [ ] If `EMBED_API_KEY` is empty, vector projection returns `{"status": "skipped", "reason": "no_api_key"}` immediately, without HTTP requests. Test: empty key + monkeypatched aiohttp; assert zero requests.
- [ ] Add a “Data egress” documentation section specifying default endpoints, transmitted content (summary/scene/event text), and how to disable it.
- [ ] Commit `fix: no network egress without explicit api key`.

### Task 26: Harden the write-guard hook

**Files:**
- Modify: `webnovel-writer/hooks/guard_runtime_write.py:61-67, 101-110`
- Test: `webnovel-writer/scripts/tests/test_hooks.py`

- [ ] Fix regex: handle `>` separately in `\b(>|out-file|...)` (`(?:^|\s)>{1,2}(?:\s|$)|\b(out-file|set-content|add-content|copy-item|move-item|cp|mv|rm|tee|sed|python|python3)\b`). Cover `echo x > .webnovel/state.json`, `mv a .webnovel/state.json`, and `tee .webnovel/index.db` in tests.
- [ ] Send `_deny` JSON decision output to stdout (retain exit code 2) so the host can parse `systemMessage`.
- [ ] Commit `fix(hooks): close redirect/unix-command bypass in write guard`.

### Task 27: Minimal dashboard protection

**Files:**
- Modify: `webnovel-writer/dashboard/app.py`, `server.py`
- Test: `webnovel-writer/scripts/tests/test_dashboard_security.py`

- [ ] Add `TrustedHostMiddleware(allowed_hosts=["localhost", "127.0.0.1"])` against DNS rebinding. Warn prominently that the entire project becomes network-visible when `--host` is non-loopback. Support `WEBNOVEL_DASHBOARD_TOKEN`; when set, all `/api/*` validate `Authorization: Bearer`. Test: forged Host returns 400; incorrect token returns 401.
- [ ] Also fix `_inspect_vector_db` connection leak at `app.py:175` using `closing()`.
- [ ] Commit `fix(dashboard): trusted host + optional token auth`.

### Task 28: CI hardening

**Files:**
- Modify: `.github/workflows/plugin-version.yml`, `.github/workflows/plugin-release.yml:43-51, 108`

- [ ] Add top-level `permissions: contents: read` to plugin-version.yml.
- [ ] Validate release `workflow_dispatch` version input first with `[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 1`. Pin `softprops/action-gh-release@v2` to a specific commit SHA. Distinguish failed `git ls-remote` queries (nonzero exit other than “not found”) from nonexistent tags.
- [ ] Do not change README version-table checks (hard CI constraint). Commit `ci: least privilege + input validation + pinned action`.

### Task 29: First-run experience

**Files:**
- Modify: `webnovel-writer/skills/webnovel-init/SKILL.md` (Step 0 preflight), `webnovel-writer/hooks/hooks.json`
- Test: manual verification

- [ ] Add an init SKILL Step 0 instruction: first run `python -X utf8 "{plugin_root}/scripts/webnovel.py" doctor --format json`. If blockers exist (missing pydantic/aiohttp, etc.), show the author the one-command installation `python -m pip install -r "{plugin_root}/scripts/requirements.txt"` and wait for completion. Doctor already has `python.import.*` checks; no new code needed.
- [ ] Keep `python` in hooks.json, but have `session_start.py` print a one-line Python-environment warning recommending `/webnovel-doctor` if the `webnovel.py` call fails (FileNotFoundError/nonzero exit). Surface guard-hook fail-open risk in the doctor report (new check using `shutil.which("python")`).
- [ ] Commit `feat: dependency preflight in init + doctor python check`.

---

## Phase 3 — P3 Quality and Hygiene (may run alongside Phase 2)

### Task 30: Extract duplicated prompts into shared references

**Files:**
- Create: `webnovel-writer/references/shared/author-report-contract.md`
- Modify: `webnovel-writer/skills/{webnovel-init,webnovel-plan,webnovel-write,webnovel-review}/SKILL.md`, `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`, `webnovel-writer/references/index/reference-loading-map.md`

- [ ] Extract “author-friendly progress and recovery contract” + “final report contract” (roughly 60–70 lines duplicated across four skills) into a shared file. Each SKILL retains a one-line reference + stage-specific parameters. Keep only one shared SubagentRun JSON template. Under the probe principle, replace wording assertions in `test_prompt_integrity.py` with assertions that the reference exists. Register the file in loading-map. SKILL edits follow the “instructions only” principle; no explanatory comments.
- [ ] Commit `refactor(skill): hoist author report contract to shared reference`.

### Task 31: Clean up outdated prompt content

**Files:**
- Modify: `webnovel-writer/templates/genres/*.md` (34 XML entity sections + 30 Pack numbers), `webnovel-writer/references/index/reference-loading-map.md`, `webnovel-writer/references/genre-profiles.md`, `webnovel-writer/references/shared/core-constraints.md:6-7`, `webnovel-writer/references/review-schema.md:3`, `webnovel-writer/references/review/blocking-override-guidelines.md:3,8,39`, `webnovel-writer/skills/webnovel-write/references/style-adapter.md:9`, `webnovel-writer/skills/webnovel-write/references/anti-ai-guide.md`

- [ ] Bulk-delete genre templates' `<entity .../>` extension sections and dangling Pack-number lines (script with sed/python, then spot-check three files).
- [ ] Reconcile loading-map step numbers against all eight SKILL files. Add missing genre-profiles sections or state a fallback rule at the start of §2 (no match → shuangwen baseline). Remove old Checkers/`project.genre` references from §3.
- [ ] Resolve the three-way anti-ai-guide contradiction: retain the file, change its loading timing to “on demand during polishing”, merge terms overlapping polish-guide, and register it in loading-map's indirect-reference table.
- [ ] Correct heading step numbers in core-constraints/review-schema/blocking-override/style-adapter.
- [ ] Commit `docs(ref): purge stale protocol fragments and fix loading map drift`.

### Task 32: Extract CLI boilerplate

**Files:**
- Create: `webnovel-writer/scripts/data_modules/cli_runtime.py`
- Modify: `main()` in `entity_linker.py`, `index_manager.py`, `rag_adapter.py`, `state_manager.py`, `sql_state_manager.py`, `style_sampler.py`; `webnovel.py:306-381`

- [ ] Provide `resolve_config(args) -> DataModulesConfig` wrapping normalize_global_project_root + resolve_project_root + from_project_root, and `run_cli(fn)` decorator unifying emit_success/emit_error + exit codes. Migrate six entrypoints; replace copied run-ledger/run-log code in `webnovel.py` with forwarding. Run all existing CLI regression tests.
- [ ] Commit `refactor: extract cli_runtime, dedupe six entrypoints`.

### Task 33: Performance fixes

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/rag_adapter.py:583-650, 721-758`, `webnovel-writer/scripts/status_reporter.py:370-460`

- [ ] Reuse hybrid's `vector_full_scan_max_vectors` prefilter in the direct-vector path; fetch BM25 hit chunks in one `WHERE chunk_id IN (...)` query. At status_reporter startup, build dictionaries with one `SELECT * FROM entities/chapters` pass and remove per-loop queries. Run existing regression tests and optionally compare timing with simulated thousand-chapter data.
- [ ] Commit `perf: kill N+1 queries in rag and status reporter`.

### Task 34: Repository and test hygiene

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py` (or fixture), `sitecustomize.py`, `.github/workflows/plugin-version.yml`, the three `requirements.txt` files including root, `webnovel-writer/scripts/update_state.py:159-178`, `webnovel-writer/scripts/data_modules/summary_projection_writer.py:20`

- [ ] Find tests writing `.tmp_story_system_engine/case_*` at repository root; use pytest `tmp_path` instead. Remove the existing 231 residual directories.
- [ ] Move `sitecustomize.py` out of the repository, or rename to `sitecustomize.py.example` with README guidance, to avoid affecting distribution users.
- [ ] Add CI dist synchronization check: after `npm ci && npm run build`, run `git diff --exit-code webnovel-writer/dashboard/frontend/dist` (or compare build hashes) to prevent source/dist drift.
- [ ] Add upper bounds to key requirements (`fastapi>=0.110,<1`, `pydantic>=2,<3`, etc.). Check whether dashboard httpx is test-only; if so, move it to test dependencies.
- [ ] Rotate update_state backups by count (keep latest twenty); write summary projections through temporary file + replace.
- [ ] Commit `chore: test/repo hygiene batch`.

---

## Overall acceptance checklist

- [ ] `python -m pytest` with PYTHONUTF8=1 fully passes; coverage ≥90% without regression
- [ ] Manual smoke test: create temporary project, init → write one chapter → review → chapter-commit → projections retry → start dashboard
- [ ] `git grep -n "checkout master"` returns no matches under scripts
- [ ] Run chapter-commit without a key; packet capture/logs confirm zero outbound requests
- [ ] README version table unchanged (hard CI constraint)
