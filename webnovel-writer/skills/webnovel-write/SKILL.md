---
name: webnovel-write
description: Produce publishable chapters through the complete context → drafting → review → polishing → commit → backup workflow.
allowed-tools: Read Write Edit Grep Bash Agent AskUserQuestion
argument-hint: "[chapter number] [--fast|--minimal]"
---

# Chapter writing workflow

## Goal

Produce a publishable chapter at `正文/第{NNNN}章-{title}.md`. Default length is 2,000–2,500 Chinese characters; follow the user/outline if it specifies otherwise.

## Modes

| Mode | Workflow |
|------|------|
| Default | Step 1→2→3→4→5→6 |
| `--fast` | Step 1→2→3(lightweight)→4→5→6 |
| `--minimal` | Step 1→2→3(write no-review artifact)→4(typesetting only)→5→6 |

## Hard rules

- Do not combine steps, skip steps, or fabricate reviews.
- Use the `Agent` tool to call the specified subagents; the main workflow must not verbally substitute for subagent output.
- Run only one review round; fix blocking issues locally or obtain a user decision before entering Step 4/5.
- On failure, rerun only the failed step; do not roll back.
- Load references on demand by step.

## Priority

User requirements > state-machine hard gates > project constraints (master outline/settings/memory) > skill workflow > reference suggestions

## CSV search (Step 2, on demand)

```bash
python -X utf8 "${SCRIPTS_DIR}/reference_search.py" --skill write --table {表名} --query "{关键词}" --genre {题材}
```

Triggers and exact table identifiers: new character → `命名规则` (naming rules), combat → `场景写法` (scene techniques), multi-character dialogue → `写作技法` (writing techniques), emotional description → `写作技法`, frequently used plot situations → `场景写法`.

## Procedure

### Preparation: Preflight

```bash
export WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
export SCRIPTS_DIR="${CLAUDE_PLUGIN_ROOT:?}/scripts"
export SKILL_ROOT="${CLAUDE_PLUGIN_ROOT:?}/skills/webnovel-write"

python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" preflight
export PROJECT_ROOT="$(python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" where)"

python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" placeholder-scan --format text
```

### Preparation: Refresh the contract tree

Read genre from the initialization configuration snapshot in `.webnovel/state.json` to refresh the contract tree; `.story-system/` contracts remain the pre-writing main-pipeline source of truth. Before calling story-system, parse the actual chapter goal from the detailed outline. Do not pass placeholder queries such as `{章纲目标}` or `第N章章纲目标`.

```bash
GENRE="$(python -X utf8 -c "import json,sys; s=json.load(open('${PROJECT_ROOT}/.webnovel/state.json',encoding='utf-8')); pi=s.get('project_info',{}); print(pi.get('genre') or s.get('project',{}).get('genre',''))")"

python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  story-system "${CHAPTER_GOAL}" --genre "${GENRE}" --chapter {chapter_num} --persist --emit-runtime-contracts --format both

python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  write-gate --chapter {chapter_num} --stage prewrite --format json
```

Required files: `MASTER_SETTING.json` (tone/prohibitions), `volume_{NNN}.json` (volume pacing), and `chapter_{NNN}.review.json` (required nodes/prohibited areas). Block if missing.

For `chapter_{NNN}.json`, check the top-level `chapter_directive` first. `chapter_focus` may come only from `chapter_directive.goal` or the actual query; do not inherit it from reference summaries in `dynamic_context`.

The writing brief must follow this fixed order:
1. Hard chapter constraints: `chapter_directive.goal/time_anchor/chapter_span/countdown/chapter_end_open_question`
2. CBN/CPNs/CEN and `must_cover_nodes`
3. Chapter prohibitions: `forbidden_zones`; violations fail
4. Style guidance: reasoning, protagonist-sheet OOC warnings, anti_patterns
5. Supplementary scene techniques: `dynamic_context`, for style reference only; cannot override chapter-outline constraints

### Step 1: context-agent generates the writing brief

Use the `Agent` tool to call `context-agent`; the main workflow must not compile the brief itself.

Use the Agent tool to run `webnovel-writer:context-agent`.

Task:
- chapter={chapter_num}
- project_root=${PROJECT_ROOT}
- scripts_dir=${SCRIPTS_DIR}
- storage_path=${PROJECT_ROOT}/.webnovel
- state_file=${PROJECT_ROOT}/.webnovel/state.json (projection/read-model, compatibility read only)
- Research first, then output a five-part writing brief in this order: hard chapter constraints → CBN/CPNs/CEN → chapter prohibitions → style guidance → supplementary dynamic_context references.
- Return a blocker if context is insufficient.

Output: a writing brief that independently supports drafting in Step 2.

After the call, the main workflow must record a `SubagentRun` summary (for the final report only):

```json
{
  "name": "context-agent",
  "user_label": "Organize writing context",
  "status": "completed | partial | failed | skipped",
  "problems": [],
  "auto_handled": [],
  "needs_user_action": false,
  "duration_ms": 0,
  "outputs": []
}
```

Insufficient context, legacy fallback, missing foreshadowing data, incomplete briefs, or abnormal duration must be recorded in `problems` / `auto_handled` and must not be silently omitted from the final report.

### Step 2: Draft the chapter

Draft only from the brief. Do not load core-constraints/anti-ai-guide (already incorporated into the brief). Output chapter prose only, without placeholders. Where structured nodes exist, develop CBN→CPNs→CEN. Compose with native Chinese-language thinking.

### Step 3: Review

Use the `Agent` tool to call `reviewer`; the main workflow must not fabricate review JSON.

Use the Agent tool to run `webnovel-writer:reviewer`.

Task:
- chapter={chapter_num}
- chapter_file=${CHAPTER_FILE}
- project_root=${PROJECT_ROOT}
- scripts_dir=${SCRIPTS_DIR}
- Return strict reviewer-schema JSON only; do not write any files.
- Do not score or provide a verbal summary.

reviewer returns JSON only; the main workflow uses `Write` to save the returned JSON to `${PROJECT_ROOT}/.webnovel/tmp/review_results.json` (reviewer does not have Write and does not write this artifact). Then run review-pipeline, which overwrites the same path with a standard review_result artifact (including `blocking_count`) for the precommit gate and subsequent commit commands.

After the call, the main workflow must record a `SubagentRun` summary (for the final report only):

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

A skipped or failed reviewer, incomplete output, `--minimal` no-review artifact, blocking issues, skipped dimensions, or abnormal duration must be recorded in `problems` / `auto_handled` and must not be silently omitted from the final report.

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" review-pipeline \
  --chapter {chapter_num} \
  --review-results "${PROJECT_ROOT}/.webnovel/tmp/review_results.json" \
  --metrics-out "${PROJECT_ROOT}/.webnovel/tmp/review_metrics.json" \
  --report-file "审查报告/第{chapter_num}章审查报告.md" \
  --save-metrics
```

Run only one review round; call reviewer only once. Apply targeted fixes to `blocking=true` issues without changing plot or breaking settings, then proceed directly to Step 4 without rerunning reviewer. For blocking issues that genuinely cannot be fixed, use `AskUserQuestion` for a user decision (accept current version / fix manually / abandon). Leave non-blocking issues to Step 4. `--fast` checks only setting/timeline/continuity.

`--minimal` calls neither reviewer nor `review-pipeline`, but must **overwrite** a new no-review `review_results.json` for this chapter (never reuse an old artifact), giving the Step 5 commit pipeline a valid `--review-result` (the exemption from the “review persisted” success criterion still applies to `--minimal`):

```bash
python -X utf8 -c "import json,os; from pathlib import Path; root=Path(os.environ['PROJECT_ROOT']); ch=int('{chapter_num}'); p=root/'.webnovel'/'tmp'/'review_results.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps({'chapter':ch,'issues':[],'issues_count':0,'blocking_count':0,'has_blocking':False,'summary':'minimal mode: reviewer skipped by user-selected --minimal flow','review_skipped':True,'review_mode':'minimal'},ensure_ascii=False,indent=2),encoding='utf-8')"
```

### Step 4: Polish

Read `references/polish-guide.md` by section: first use `Grep` with `^#{1,3} ` to locate anchor line numbers, then `Read` offset/limit for sections. For the main path read section 2, Execution Order (must follow in order). For the final Anti-AI check, separately read section 2A, Anti-AI Detection Details, and the Phase 1 supplement, Anti-AI Rules (seven layers, original), specifically the vocabulary section; do not read the entire file. `references/writing/typesetting.md` and `references/style-adapter.md` are short; read them in full.

Order: fix non-blocking issues → adapt style → typeset → final Anti-AI check.

Change expression only, not facts. Do not enter Step 5 when `anti_ai_force_check=fail`. `--minimal` performs typesetting only.

### Step 5: Commit

#### 5.1 Data Agent extracts facts

Use the `Agent` tool to call `data-agent`, producing three JSON files: fulfillment_result / disambiguation_result / extraction_result, and reuse Step 3's review_results.

Use the Agent tool to run `webnovel-writer:data-agent`.

Task:
- chapter={chapter_num}
- chapter_file=${CHAPTER_FILE}
- project_root=${PROJECT_ROOT}
- scripts_dir=${SCRIPTS_DIR}
- output_dir=${PROJECT_ROOT}/.webnovel/tmp
- Generate fulfillment_result.json, disambiguation_result.json, and extraction_result.json artifacts using your own schema (see the data-agent output-format section).
- You are the sole writer of these three artifacts; do not write directly to state/index/summaries/memory/vectors/projection.

Artifact field schemas are defined by data-agent and checked by the runtime validator. The main workflow checks only file existence and schema; it must not rewrite, supplement, or verbally substitute for them.

After the call, the main workflow must record a `SubagentRun` summary (for the final report only):

```json
{
  "name": "data-agent",
  "user_label": "Save this chapter's story facts",
  "status": "completed | partial | failed | skipped",
  "problems": [],
  "auto_handled": [],
  "needs_user_action": false,
  "duration_ms": 0,
  "outputs": []
}
```

Record the three artifacts' write status, invalid schemas, pending disambiguation, prolonged lack of progress, or incomplete output in `problems`; record automatic reruns or degraded handling in `auto_handled`.

#### 5.2 Precommit validation and CHAPTER_COMMIT

Run the precommit gate first:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  write-gate --chapter {chapter_num} --stage precommit --format json
```

After precommit passes, run a read-only `git diff` change-scope check before committing (write-ownership sanity check; read-only, no staging or committing):

```bash
if git -C "${PROJECT_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "${PROJECT_ROOT}" diff --name-status -- .
  git -C "${PROJECT_ROOT}" diff --check -- .
fi
```

Changes must not include the plugin directory, other book projects, other chapters' prose, or hand-edited state files outside this chapter's workflow. `git diff` covers only Git-visible files; validate SQLite / `.webnovel/` internal semantics through 5.3 postcommit and read-only runtime queries. If the project root is not a Git worktree, record “git diff check skipped”; do not skip the precommit gate. This step is read-only: no `git add`/`git commit` here.

After validation passes, run chapter-commit:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" chapter-commit \
  --chapter {chapter_num} \
  --review-result "${PROJECT_ROOT}/.webnovel/tmp/review_results.json" \
  --fulfillment-result "${PROJECT_ROOT}/.webnovel/tmp/fulfillment_result.json" \
  --disambiguation-result "${PROJECT_ROOT}/.webnovel/tmp/disambiguation_result.json" \
  --extraction-result "${PROJECT_ROOT}/.webnovel/tmp/extraction_result.json"
```

Automatic decision: blocking_count>0 or nonempty missed_nodes or nonempty pending → rejected; otherwise accepted.

#### 5.3 Validate projections

All five projection_status items (state/index/summary/memory/vector) must be done or skipped.

The projection writer advances chapter_status automatically: accepted→committed, rejected→rejected.

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  write-gate --chapter {chapter_num} --stage postcommit --format json
```

#### 5.4 Isolate failures

No commit generated → rerun 5.2. Projection failed → retry only projection, not Steps 1–4.

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  projections retry --chapter {chapter_num} --format json
```

### Step 6: Git backup

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" backup \
  --chapter {chapter_num} \
  --chapter-title "{title}"
```

Backup must use the resolved `PROJECT_ROOT`. Never run a bare, all-files Git add from the workspace parent directory, which could add the book repository as an embedded repository/submodule in the parent repository.

## Author-friendly progress and recovery contract

Before writing, explain the goal, main stages, and whether the author needs to stay nearby in author-friendly language; do not promise a fixed duration. Progress updates describe only the current action and expected output, not raw JSON, tracebacks, or long command logs. Write technical details to `.webnovel/logs/run_last.log`:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" run-log \
  --event write-start \
  --payload-json "{\"chapter\": {chapter_num}, \"mode\": \"{mode}\"}" \
  --format text
```

Writing progress milestones (at most six):

1. Check project environment: verify project, placeholders, and chapter requirements are ready.
2. Organize writing context: read chapter outline, recent plot, and unresolved foreshadowing.
3. Draft chapter prose: generate the chapter from the writing brief.
4. Writing check: review blocking issues and high-value revision suggestions.
5. Save this chapter's story facts: extract goal fulfillment, ambiguities, and new facts.
6. Commit and back up: record chapter facts, update story data, and back up.

When rerunning the same chapter, first read a trustworthy checkpoint:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" run-ledger write-resume \
  --chapter {chapter_num} \
  --mode "{mode}" \
  --format json
```

`run-ledger write-resume` only suggests where to resume; it does not automatically overwrite files. It determines the restart point from chapter prose, review results, data artifacts, commit, projection, and backup status. If prose was manually edited, the outline was updated after the prose, or an accepted chapter is rerun, stop and offer finite choices: keep current prose / redraft / view status only. Never overwrite the author's manual edits.

After each key step, record `run-ledger record-write-step`, including at least step, status, input/output file paths, problems, auto_handled, and duration_ms, for the next resume and final report.

Minimize interruptions: continue by default; ask only about creative direction, factual consistency, overwrite risk, or blocking issues that cannot be fixed locally. Offer 2–3 finite choices and explain their consequences.

When stuck, explain the blocker, completed work, and recovery advice, e.g. “The chapter and review report are retained, but saving story facts failed; rerunning `/webnovel-write {chapter_num}` will resume from data-agent.” Mention `.webnovel/logs/run_last.log` in the final report only for unrecoverable failures; otherwise retain logs without bothering the author.

Always call the author-report helper when finishing, preferably organizing the final reply around its output:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" user-report \
  --stage write \
  --chapter {chapter_num} \
  --format text
```

## Sufficiency gate

1. Chapter prose file exists and is nonempty.
2. Review is persisted (except `--minimal`).
3. blocking=true issues were fixed locally in Step 3 or decided by the user.
4. anti_ai_force_check=pass (except `--minimal`).
5. Accepted CHAPTER_COMMIT; all five projections done/skipped.
6. chapter_status=committed (advanced automatically by projection).
7. `write-gate` prewrite / precommit / postcommit all pass.

## Failure recovery

Missing review → rerun Step 3. Missing summary/state/memory → rerun Step 5. Polishing distorts facts → return to Step 4 to fix, then rerun Step 5.

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
- Chapter prose file path.
- Review report path.
- `.webnovel/tmp/review_results.json`.
- `.webnovel/tmp/fulfillment_result.json`.
- `.webnovel/tmp/disambiguation_result.json`.
- `.webnovel/tmp/extraction_result.json`.
- `.story-system/commits/chapter_{NNN}.commit.json`.
- state / index / summary / memory / vector update status.
- Backup status.
- Whether writing can continue with the next chapter.

Status rules:
- If `chapter-commit rejected`, any `write-gate` failed, or projection failed, final status must not be “Completed”.
- Explain skipped items in `--fast` and `--minimal`; when `--minimal` skips review, classify it as “Automatically handled” or “Suggested for confirmation”, never pretend a full review was completed.
- If projection retry occurs, report its automatic handling and final result.

Issue categories:
- Automatically handled: successful projection retry, temporary RAG degradation without impact on results, old no-review artifact overwritten by this chapter's new artifact.
- Suggested for confirmation: new character / setting names, low-confidence but non-blocking ambiguities, non-blocking review suggestions.
- Must address: unresolved blocking issues, missing data artifacts or incomplete schemas, commit rejected, projection failed.

Next-step suggestions must use task-oriented language plus copyable commands, for example:

```text
- Next, write the following chapter:
  /webnovel-write {next_chapter}
```

Do not report token statistics; for troubleshooting, provide only the log path or suggest `/webnovel-doctor`.
