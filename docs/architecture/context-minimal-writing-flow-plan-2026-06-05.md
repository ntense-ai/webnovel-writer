# Writing-Workflow Context Reduction Refactoring Plan

> Date: 2026-06-05
> Status: Draft v3
> Scope: Refactor prompts and reading strategies in `skills/`, `agents/`, and `references/` to reduce unnecessary main-agent context and token use
> Core principle: Preserve the end-to-end workflow before compressing prompts; Skills define orchestration contracts, Agents own specialist procedures, Runtime enforces hard checks
> Pruning framework: Every retain / move / delete decision follows Section 4's four criteria: responsibility, tokens, noise, and reading mode, not arbitrary checklists
> v3 changes: (1) Section 4 pruning criteria; (2) Section 5 narrowed to cross-layer red lines; (3) Section 6 includes references/reading optimization using reference-loading-map; (4) Section 12 moves from wording assertions to behavior/contracts; (5) host fixed to Claude Code, with capabilities verified against official docs, local version, and registered plugin names
> Tool baseline: Claude Code is the fixed host. Default to its relevant built-ins (`Read` offset/limit, `Grep`, `Glob`, `Agent`, `Skill`, `AskUserQuestion`, `Write`, `Edit`, `WebSearch`, `WebFetch`) and cross-platform Bash. PowerShell is not recommended. Establish subagent/Skill behavior from official docs, then verify plugin registrations.

---

## 0. How to Read This Version

This plan does not force every file into a fixed format or aim merely to keep existing tests green.

The actual work is:

1. Confirm the complete init / plan / write / review / query / learn / dashboard / doctor workflows (Section 3).
2. Turn cross-layer business red lines into behavior assertions (Sections 5 and 12).
3. Slim Skills, Agents, and references under Section 4's criteria and assign each read a mode (Sections 4 and 6).
4. Validate with runtime, prompt integrity, behavior evals, and package validator. Test behavior/contracts, not wording (Section 12).

Keep these positions throughout:

- **Tests are probes, not constraints.** Slimming will break wording assertions such as `assert "字符串" in text`. Those assertions themselves are noise to remove. If they protect a real red line, replace them with behavior assertions at the producing layer rather than retaining redundant prose to pass tests.
- **Do not remove Section 3's end-to-end workflow.** Formatting, slimming, moving references, compressing schemas, or changing read modes must not remove business steps. Section 3 supplies red lines; Section 4 supplies pruning criteria. They do not conflict.
- **Use Claude Code's actual capabilities, neither invented nor excessively defensive.** This plan targets Claude Code, not a temporary chat shell, another agent environment, or remembered obsolete tool names. Design around official built-ins (`Read` offset/limit, `Grep`, `Glob`, `Agent`, `Skill`, `AskUserQuestion`, `Write`, `Edit`) and Bash, without hard dependencies on `sed` / `jq`. PowerShell is only an explicitly Windows-only fallback, with compatibility risks recorded. Preserve official behavior: subagents cannot spawn subagents; `tools` is a subagent allowlist; `skills` preloads entire Skills; Skill `allowed-tools` grants preapproval rather than restricting availability. Phase 0 verifies the current Claude Code version, actual registered names, local plugin-dev frontmatter compliance, and enabled tools in this repository.

---

## 1. Background

Webnovel Writer is no longer a single-prompt Skill. It has a runtime main workflow:

- `project-status`: Short project status.
- `doctor`: Phase-aware diagnostics.
- `placeholder-scan`: Pending placeholders/incomplete content.
- `story-system`: Pre-writing `.story-system/` contract tree.
- `write-gate`: Batch prewrite/precommit/postcommit checks.
- `context-agent`: Pre-writing context assembly.
- `reviewer`: Structured review.
- `review-pipeline`: Reports, metrics, and persistence.
- `data-agent`: Commit-artifact extraction.
- `chapter-commit`: Post-writing facts and projections.
- `projections retry`: Failed-projection recovery.
- `backup`: Backups scoped to the book-project root.

The problem is not too little context:

1. The main agent knows too much about subagent internals.
2. Skill text mixes orchestration, tutorials, schemas, examples, and failure rules.
3. Information obtainable on demand is injected into the main context early.
4. Skills, Agents, and runtime repeat the same information.
5. Long schemas/examples consume tokens when execution needs only inputs, outputs, and acceptance criteria.

Move from "the main agent memorizes the full tutorial" to "the main agent orchestrates, subagents specialize, runtime validates."

---

## 2. One-Sentence Goal

> The main agent sends tasks, not tutorials; subagents carry their own expertise; runtime validates; assertion tables protect workflow completeness.

---

## 3. End-to-End Workflow Baseline

This is the business baseline. Check it before every compression decision.

### 3.1 Global Invariants

Every Skill / Agent rewrite must preserve:

- Existing-project Skills resolve the actual book-project root before acting; never write project files into the plugin directory.
- Before new-project creation, `/webnovel-init` must not use `where` to resolve the workspace to an old project. Derive the target from a sanitized book title.
- `.story-system/` is the main-chain source of truth for pre-writing contracts and post-writing commits.
- `.webnovel/state.json` remains a compatibility projection/read model, not a post-writing fact source.
- Chapter-level `story-system` queries come from the actual detailed-outline goal, never `{章纲目标}`, `第N章章纲目标`, or other placeholders.
- Concrete chapter writing/review/contract refresh must generate or verify `.story-system/MASTER_SETTING.json`, `.story-system/volumes/`, `.story-system/chapters/`, `.story-system/reviews/`.
- Preserve all three `write-gate` stages: prewrite, precommit, postcommit.
- Explicitly invoke subagents with `Agent`; the main workflow cannot verbally substitute for `context-agent`, `reviewer`, `data-agent`, or `deconstruction-agent` outputs.
- Retry only failed steps, not the entire workflow.
- For deterministic runtime validation, prompts retain only minimal explanation and blocking boundaries.
- Read references on demand; do not add references merely for attractive structure without actual reuse.
- Every file artifact has one writer. Specify who writes, who only returns, and who only validates. Neither duplicate writes across layers nor leave outputs unsaved.
- Before each `chapter-commit`, inspect project-root `git diff` to confirm visible text/path changes belong only to the current chapter and its workflow. This write-ownership sanity check does not replace `write-gate precommit` or prove SQLite / `.webnovel/` internal correctness.

### 3.2 Complete `/webnovel-init` Workflow

Init is not merely collection. Preserve generation end to end:

1. Verify `CLAUDE_PLUGIN_ROOT` and `${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py`.
2. Do not resolve an old project with `where` before initialization.
3. Load minimal references: data flow, genre tropes, genre profile. Load others as needed.
4. Ask about inspiration before story-core collection. Reference-book analysis is optional, not automatic.
5. If the user provides reference text/path/excerpt, invoke `webnovel-writer:deconstruction-agent`; no main-flow substitute.
6. The deconstruction agent returns only `init_reference_research`, writes nothing, and creates no `.story-system`, `.webnovel`, `设定集`, `大纲`, `正文`, canon, or read model.
7. Consume only transferable patterns and differentiation requirements. With `quality.passed=false`, `confidence < 0.85`, or warnings, do not incorporate them into the creative-constraint package; show risks and obtain user confirmation.
8. Steps 2-6 use only user-approved patterns transformed into this book's differentiated expression.
9. Collect story core, characters, special advantage, worldbuilding, power rules, and creative constraints.
10. Present an initialization-summary draft and wait for explicit confirmation.
11. Sanitize the title into `PROJECT_SLUG` and `PROJECT_ROOT`; show `WORKSPACE_ROOT`, `PROJECT_SLUG`, `PROJECT_ROOT`; confirm before writing.
12. Run `webnovel.py init`.
13. Write only final approved creative constraints into `.webnovel/idea_bank.json`.
14. Patch `大纲/总纲.md` with one-line premise, main/hidden plots, creative constraints, antagonist tiers, payoff milestones.
15. Immediately generate the MASTER contract after init:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  story-system "${GENRE}" --genre "${GENRE}" --persist --format json
```

Do not pass `--chapter` here; generate only `MASTER_SETTING.json` and `anti_patterns.json`.

16. Validate `state.json`, core setting files, `大纲/总纲.md`, `idea_bank.json`, `.story-system/MASTER_SETTING.json`.
17. Recover by filling missing fields/rerunning minimal steps, not repeating the entire interview.

### 3.3 Complete `/webnovel-plan` Workflow

Plan is not only chapter outlining. Preserve the bridge from planning to writing contracts:

1. Resolve the actual root; run `placeholder-scan`.
2. Read genre from the initialization snapshot in `.webnovel/state.json`; `.story-system/` remains writing authority.
3. Read `大纲/总纲.md`; verify volume title, chapter range, core conflict, final climax. Block if insufficient.
4. For cross-volume planning, read recent summaries, core-character states, core relationships, active foreshadowing.
5. Complete the setting baseline: world, power system, protagonist card, antagonist design. Block on conflicts.
6. Select the target volume and confirm scope.
7. Generate a beat sheet with a midpoint reversal or explicit reason for none; escalate the crisis chain at least three times.
8. Generate a volume timeline with time system, span, countdown events.
9. Generate volume-outline skeleton: summary, cast/antagonist tiers, Strand, payoffs, foreshadowing, constraint triggers.
10. Batch chapter outlines: default 10/batch, 8 for complex genres, preferably no more than 12.
11. Each chapter includes goal, resistance, cost, time anchor, duration, gap since previous chapter, countdown, payoff, Strand, antagonist tier, POV/protagonist, key entities, change, unresolved ending question, hook.
12. Preserve structured nodes: `CBN`, `CPNs`, `CEN`, `必须覆盖节点`, `本章禁区`.
13. Write new settings incrementally into existing setting files only.
14. Validate beat sheet, timeline, detailed outline, time fields, countdown, BLOCKER, node continuity.
15. Generate explicit structured writeback file `大纲/第{volume_id}卷-总纲写回.json`.
16. Call `master-outline-sync`; update only V+1 anchors and explicit foreshadowing/open loops, never infer from free text.
17. Call `update-state -- --volume-planned ... --chapters-range ...`.
18. Once planning reaches concrete chapters, refresh runtime contracts with the actual chapter goal:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  story-system "${CHAPTER_GOAL}" --genre "${GENRE}" --chapter {chapter_num} \
  --persist --emit-runtime-contracts --format both
```

Before writing, no current-chapter entity may retain `[待...]`, `暂名`, or `{占位}`.

### 3.4 Complete `/webnovel-write` Workflow

Write is the most important acceptance target. Preserve:

#### Preparation

1. Set `WORKSPACE_ROOT`, `SCRIPTS_DIR`, `SKILL_ROOT`.
2. Run `preflight`.
3. Resolve actual `PROJECT_ROOT` with `where`.
4. Run `placeholder-scan`.
5. Parse real `CHAPTER_GOAL` from the detailed outline.
6. Read genre from `.webnovel/state.json`'s initialization snapshot.
7. Refresh chapter-level runtime contracts:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  story-system "${CHAPTER_GOAL}" --genre "${GENRE}" --chapter {chapter_num} \
  --persist --emit-runtime-contracts --format both
```

8. Run prewrite gate:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  write-gate --chapter {chapter_num} --stage prewrite --format json
```

Prewrite requires `MASTER_SETTING.json`, `volume_{NNN}.json`, `chapter_{NNN}.json`, `chapter_{NNN}.review.json`.

#### Step 1: Writing Brief

Invoke `webnovel-writer:context-agent`.

Pass only necessary parameters: chapter number, project root, script directory, storage/state compatibility paths, output requirements.

Return a complete five-part brief independently sufficient for drafting. Insufficient context yields a blocker, not main-flow invention.

#### Step 2: Draft Prose

Draft only from the brief. Do not reload long core-constraint or anti-AI guides.

Follow `CBN -> CPNs -> CEN` when structured nodes exist. No placeholders in prose.

#### Step 3: Review

Default and `--fast` invoke `webnovel-writer:reviewer`; `--minimal` may skip.

Default ownership: reviewer returns strict JSON only; main flow writes `${PROJECT_ROOT}/.webnovel/tmp/review_results.json`. If reviewer later writes directly, add `Write` to its frontmatter and remove main-flow writing. Never both.

After saving `review_results.json`, call:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" review-pipeline \
  --chapter {chapter_num} \
  --review-results "${PROJECT_ROOT}/.webnovel/tmp/review_results.json" \
  --metrics-out "${PROJECT_ROOT}/.webnovel/tmp/review_metrics.json" \
  --report-file "审查报告/第{chapter_num}章审查报告.md" \
  --save-metrics
```

Only one reviewer invocation in the writing workflow. Fix `blocking=true` issues specifically, or obtain user adjudication before polishing/commit. Nonblocking issues go to polishing.

#### Step 4: Polish

Change expression, not facts.

Keep existing reference loading if useful, but no long tutorials in the main Skill:

- `references/polish-guide.md`
- `references/writing/typesetting.md`
- `references/style-adapter.md`

Order: nonblocking fixes → style adaptation → formatting → final Anti-AI check.

Do not commit if `anti_ai_force_check=fail`. `--minimal` performs formatting only.

#### Step 5: Commit

Invoke `webnovel-writer:data-agent` to generate:

- `.webnovel/tmp/fulfillment_result.json`
- `.webnovel/tmp/disambiguation_result.json`
- `.webnovel/tmp/extraction_result.json`

Data-agent is the sole writer of these tmp artifacts. Main flow checks existence/schema only, never rewrites or fills them. Ask data-agent to retry the specific invalid artifact.

Data-agent never directly writes state / index / summaries / memory / vectors / projections.

Then run precommit gate:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  write-gate --chapter {chapter_num} --stage precommit --format json
```

After the gate passes, perform a final read-only diff-scope check:

```bash
if git -C "${PROJECT_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "${PROJECT_ROOT}" diff --name-status -- .
  git -C "${PROJECT_ROOT}" diff --check -- .
fi
```

Rules:

- `diff --name-status` must not include plugin directories, other books, other chapters' prose, or manual state files outside this chapter's workflow.
- `git diff` sees only Git-visible paths/text. Ignored `.webnovel/` files and binary `index.db` / `vectors.db` table/row changes are invisible.
- Projection-owned writes such as summaries/memory/vectors must not occur before `chapter-commit`; only it or `projections retry` may produce them. Combine runtime gates/read-model queries with diff checks.
- Outside a Git worktree, explicitly record "git diff validation skipped"; never skip `write-gate precommit` because of it.
- No `git add` / `git commit` here. This step is read-only.

Validate database/read-model semantics separately:

- After `review-pipeline --save-metrics`, confirm target-chapter `review_metrics` using runtime output/read-only queries, not Git diffs.
- After `chapter-commit`, use postcommit `projection_status` to confirm state/index/summary/memory/vector are all `done` or `skipped`.
- Prefer existing runtime queries for SQLite. If unavailable, Python `sqlite3` read-only queries are acceptable; never turn them into a write path.

Then run:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" chapter-commit \
  --chapter {chapter_num} \
  --review-result "${PROJECT_ROOT}/.webnovel/tmp/review_results.json" \
  --fulfillment-result "${PROJECT_ROOT}/.webnovel/tmp/fulfillment_result.json" \
  --disambiguation-result "${PROJECT_ROOT}/.webnovel/tmp/disambiguation_result.json" \
  --extraction-result "${PROJECT_ROOT}/.webnovel/tmp/extraction_result.json"
```

Automatic decision: `blocking_count > 0`, nonempty `missed_nodes`, or nonempty `pending` → rejected; otherwise accepted.

#### Step 6: Postcommit Validation and Backup

Run postcommit gate:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  write-gate --chapter {chapter_num} --stage postcommit --format json
```

All five projection_status entries `state/index/summary/memory/vector` must be `done` or `skipped`.

Retry only failed projections:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  projections retry --chapter {chapter_num} --format json
```

Backup must use the resolved `PROJECT_ROOT`:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" backup \
  --chapter {chapter_num} \
  --chapter-title "{title}"
```

Never run bare `git add .` from the workspace parent.

### 3.5 Complete `/webnovel-review` Workflow

Independent review may be more extensive than writing Step 3, but never fabricate reviewer output:

1. Resolve actual project root.
2. If runtime contracts are missing, refresh `story-system --emit-runtime-contracts` with real `CHAPTER_GOAL`.
3. Read core constraints/review schema; load other references according to issues.
4. Load `.webnovel/state.json` compatibility projection and target prose.
5. Invoke `webnovel-writer:reviewer` for strict JSON; main flow saves `.webnovel/tmp/review_results.json`.
6. Run `review-pipeline --save-metrics` to generate/persist reports and metrics into `review_metrics`.
7. Run `update-state -- --add-review ...` for compatibility review records.
8. With `blocking=true`, ask whether to fix now or later.

### 3.6 Query, Learning, Dashboard, and Diagnostics

`webnovel-query`:

- Read-only.
- Resolve root first.
- Classify the query, then use the narrowest tool.
- Source priority: `.story-system` pre-writing contracts → latest accepted `CHAPTER_COMMIT` → `memory-contract` → `.webnovel/state.json` / `index.db` fallback.
- Temporal queries prefer `knowledge query-entity-state` / `knowledge query-relationships`.
- Explicitly disclose legacy fallback.

`webnovel-learn`:

- Resolve root.
- Read current chapter from state; on failure use `source_chapter: null`.
- Call `project-memory add-pattern`; never handwrite JSON.

`webnovel-dashboard`:

- Read-only.
- Resolve Dashboard module and root.
- Report missing frontend dist; do not write project files.
- Expose Story Runtime main-chain status, such as `/api/story-runtime/health`.

`webnovel-doctor`:

- Read-only diagnosis; no repairs, dependency installation, or Dashboard launch.
- `project-status --format summary` first, then `doctor --format text`.
- Explain missing items according to runtime-inferred phase; do not treat newly initialized projects as multi-chapter ones.

---

## 4. Pruning Criteria and Responsibilities

Every retain / move / delete / reading-mode decision follows these four criteria, rather than per-phase inventories of mandatory prose.

### 4.1 Four Criteria

**Criterion 1: Responsibility (information belongs to its producer/consumer)**

- Main agent orchestrates and retains only **contract shape**: which subagent, which artifacts, which runtime consumer, what blocks.
- Field details belong to the producer: data-agent creates artifact fields and runtime validates them. Keep them in `data-agent.md` and runtime, not the main Skill.
- One source of truth per piece of information. Remove duplicates outside the producing layer.

**Criterion 2: Tokens (measure resident main-agent input, not file lines)**

- Optimize context tokens actually loaded to write one chapter, not file length.
- Material needed only for a subagent/step must not reside permanently in main context.
- Short full-file reads are fine. Target large files always read in full (Section 6), not slimming for its own sake.

**Criterion 3: Noise (retain instructions/red lines; remove meta-narration and nagging)**

| Noise | Example | Handling |
|---|---|---|
| Duplication | Schema fields repeated in Skill and Agent | Keep only at producer |
| Meta-narration (teaching how to think) | Reviewer "chain of thought (ReAct): read→compare→judge" | Remove without changing outputs |
| Stacked prohibitions | Long sequences of "do not..." | Retain red lines, remove reminders |
| Wrong audience | Main agent receives subagent-only details | Move by Criterion 1 |
| Structural filler | Empty sections maintaining a template | Delete and relax structural tests |

**Criterion 4: Reading Mode (full when needed, partial on demand)**

Label every file read; never default to full `cat`:

- **Full**: Short files needing holistic understanding (schema, core rules, methodology).
- **Section**: Use built-in `Grep` content output to locate heading lines, then `Read` offset/limit. Both are platform-independent Claude Code tools; no assumption about `sed` / `jq`. Give anchors when section names are already known.
- **Retrieval**: For CSV/JSON, prefer runtime tools (`reference_search.py`, `knowledge query-*`, dedicated schemas/validators). If no runtime command exists and temporary field extraction is needed, prefer Bash; never default to dumping a whole table. PowerShell is Windows-only fallback.
- **None**: Clean up migrated or unused files (Section 6).

### 4.2 Layer Boundaries

| Layer | Retains | Does not do |
|---|---|---|
| Skill | Root protection, order, runtime commands, Agent input shape, success/recovery | Subagent tutorials, long schemas, bypassing gates |
| Agent | Specialist procedure, minimum rules, output contract, boundaries | Depend on `agents/references/*`, write projections, replace runtime commit |
| Runtime | Schemas, gates, commits, projections, backups, state advancement | LLM writing judgments |
| Skill references | Long examples, collection fields, node details, polishing lists | Hidden subagent manuals, indiscriminate full loading |

### 4.3 Single-File Agents

Do not add `agents/references/*` by default: avoid fragmenting subagent instructions into invisible pieces. Compress specialist rules, including complete artifact schemas, into the Agent's single file. This implements producer ownership.

Official Claude Code capabilities allow Skills preloaded with `skills`; if `Skill` is in the subagent's tool set, it may invoke non-preloaded project/user/plugin Skills at runtime. Neither is the default here:

- Preloading injects the full Skill and may negate context savings.
- `skills` is preloaded context; `tools: Skill` permits runtime invocation. They differ.
- Subagents cannot spawn subagents; main flow must orchestrate chains.
- Do not design subagents around `Agent` or `AskUserQuestion`; return user decisions to main flow.
- Future subagent Skill use requires a Phase 0 record: preload or runtime invocation, why not inline, added context, and whether still within token budget.

### 4.4 Claude Code Tool Best Practices

Frontmatter uses official tool names/permission rules. Bodies assign tasks naturally; never invent unstable internal function APIs.

#### 4.4.1 Frontmatter

Skill `allowed-tools` is preapproval, not a restriction. Unlisted tools remain callable subject to permissions.

```yaml
allowed-tools: Read, Grep, Glob, Bash, Agent, AskUserQuestion
```

For narrower permissions, use official permission-rule syntax after verifying registrations:

```yaml
allowed-tools: Read, Grep, Glob, Bash(python -X utf8 *), Agent
```

Do not guess rules such as `Agent(webnovel-writer:context-agent)` before verification. Phase 0 verifies real plugin-scoped Agent names.

Agent `tools` is an allowlist; omission inherits session tools and is unsuitable as a production default. List the minimum needed for each role, not one universal template:

```yaml
# Read-only research, or JSON-only review saved by main flow
tools: Read, Grep, Glob, Bash

# When saving tmp JSON artifacts or raw reviewer JSON
tools: Read, Grep, Bash, Write
```

Preload through `skills:`, not by adding `Skill` to `tools` as a supposed reference loader. Include `Skill` only for genuine runtime invocation, with a recorded reason:

```yaml
skills:
  - api-conventions
```

#### 4.4.2 Agent Invocation in Prose

Avoid pseudo-functions:

```text
Agent(
  subagent_type: "...",
  prompt: "..."
)
```

Prefer task instructions:

```text
Use the Agent tool to run `webnovel-writer:context-agent`.

Task:
- chapter={chapter_num}
- project_root=${PROJECT_ROOT}
- scripts_dir=${SCRIPTS_DIR}
- Return a five-part writing brief.
- If context is insufficient, return a blocker.
```

This preserves explicit Agent invocation without hardcoding internal tool-call schemas into Skills.

#### 4.4.3 Tool Usage

| Tool | Default use | Best practice |
|---|---|---|
| `Read` | File content | Absolute paths; section reads for long files; locate anchors with Grep; avoid full large-reference reads in main flow |
| `Grep` | Text search/heading locations | Content output with path/line; narrow by glob/type; do not present `Grep -n` as tool API |
| `Glob` | File discovery | Narrow patterns; narrow again if excessive; do not replace simple discovery with shell enumeration |
| `Bash` | Cross-platform shell/runtime | Each call is a new process; variables do not persist. Group commands sharing variables or resolve them each call. Prefer runtime commands over temporary substitutes |
| `PowerShell` | Windows-only fallback | Not default; do not proactively set `shell: powershell` in Skills/hooks. Use only when built-ins/Bash cannot meet an explicitly Windows-only task; record risk |
| `Agent` | Subagent invocation | Main flow orchestrates. Use natural "Use the Agent tool... / Task..." instructions. Depend on final results, not intermediate tool output |
| `Skill` | Reusable Skills | Main session invokes as needed; subagent preload uses `skills`, runtime invocation needs `tools: Skill`. Avoid long-reference preloading. `Skill(...)` in allowed-tools is a permission rule, not an invocation template |
| `AskUserQuestion` | Adjudication/key choices | Only for blockers, plot decisions, initialization confirmation, etc.; not in subagent design |
| `Write` / `Edit` | Direct LLM file edits | Prefer runtime for structured state/projections. For Markdown, define target/minimal scope. Subagent tmp-JSON persistence requires `Write`; otherwise return JSON for main-flow saving |
| `WebSearch` / `WebFetch` | External research | Only for user-requested trends/platform conditions/time-sensitive material; search then fetch sources. Do not write unconfirmed external information into canon |

### 4.5 Write-Ownership Matrix

Do not merely say "produce a file." Name its sole writer and check this matrix whenever a Skill/Agent changes.

| Artifact/path | Sole writer | Other layers |
|---|---|---|
| New project directory, base `.webnovel/`, setting scaffold | `webnovel.py init` | Init Skill collects, confirms, invokes |
| `.webnovel/idea_bank.json`, initial `大纲/总纲.md` patch | Init main flow | Deconstruction agent never writes canon; runtime validates |
| `.story-system/MASTER_SETTING.json`, volume/chapter contracts | `story-system --persist` | Skills/Agents never handwrite contract JSON |
| `正文/第{chapter}章-*.md` | Write main flow Steps 2/4 | Context agent returns brief; reviewer/data-agent do not edit prose |
| `.webnovel/tmp/review_results.json` | Default write/review main flow saves returned reviewer JSON | Reviewer returns strict JSON; direct reviewer writing requires Write and removal of main-flow write |
| `.webnovel/tmp/review_metrics.json`, report, `review_metrics` table | `review-pipeline --save-metrics` | Main flow calls only; reviewer writes neither metrics nor report |
| `.webnovel/tmp/fulfillment_result.json`, `disambiguation_result.json`, `extraction_result.json` | Data-agent | Main flow checks existence/schema, never rewrites |
| Accepted commit, projections, `.webnovel/state.json`, index, summaries, memory, vectors | `chapter-commit` / `projections retry` | No direct data-agent writes or handwritten main-flow read models |
| Backups | `backup --project-root "${PROJECT_ROOT}"` | Main flow invokes and checks |

Acceptance:

- Every artifact answers who writes, who must not write, who retries.
- Remove duplicate writers until only the designated writer remains.
- Agents required to save files need `Write` in `tools`; otherwise they return content for main-flow saving.
- Before each chapter commit, read-only `git diff --name-status` checks Git-visible scope without staging/committing; runtime/SQLite read-only queries validate database internals.

---

## 5. Nonremovable Red Lines and Movable Content

Field-level details, examples, and collection rules follow Section 4. This section fixes only movable scope and **nonremovable cross-layer red lines**.

### 5.1 May Move / Compress / Read on Demand (Examples, Not Exhaustive)

- Subagent internal queries/reasoning explanations.
- Reviewer dimension explanations, ReAct meta-narration, long examples.
- Full artifact payload details, moved to data-agent's single file rather than repeated in main Skill.
- Init collection fields, genre lists, anti-trope libraries.
- Detailed CBN/CPN/CEN rules/examples.
- Long polishing checklists.
- Section 6's large always-full references: switch to section/retrieval/entry-based reading.

### 5.2 Nonremovable Cross-Layer Red Lines (Exhaustive; Tested in Section 12)

These span Skill / Agent / Runtime and require behavior/contract assertions. Two classes distinguish whether they can pass before slimming in Phase 0:

**A. Protect existing behavior (implemented; add/strengthen assertions to pass in Phase 0)**

- Root protection, sanitized init directory, no canon before user confirmation.
- `placeholder-scan` at key plan/write boundaries.
- Real `CHAPTER_GOAL`; no placeholder queries.
- Chapter refresh with `story-system --persist --emit-runtime-contracts`.
- Three ordered write gates: prewrite/precommit/postcommit.
- Explicit `Agent` invocation, not verbal main-flow substitution.
- Raw reviewer JSON persisted through `review-pipeline --save-metrics`.
- Three data-agent artifacts; runtime validates fields, not main-Skill wording.
- `chapter-commit` is sole fact submission and drives projections.
- Five postcommit projections checked; only `projections retry` after failure, no writing rollback.
- `backup --project-root "${PROJECT_ROOT}"`; no bare `git add .`.
- Plan beat sheets, timelines, chapter nodes, setting writeback, structured master-outline writeback, state updates.

**B. New contracts this round (unimplemented; Phase 0 writes pending assertions, later phases make them pass)**

- Ownership matrix: reviewer results, data artifacts, metrics, commits/projections/read models each have one writer, no duplication/omission. Agent tools match persistence: reviewer lacks Write and returns JSON; data-agent has Write and saves three artifacts. Introduced in 4.5; pass after Phase 1-3 prompt/frontmatter alignment.
- Read-only precommit Git diff scope check every chapter; no plugin/other-chapter/other-book/unauthorized state changes. Database internals checked separately. Not in current write Skill; pass after Phase 1.

> Specific fields such as `planned_nodes` are **not on this list**. Producer Agent/runtime schemas own them under Criterion 1; Section 12 contract tests protect them, not main-Skill wording requirements.

---

## 6. Change Scope

### 6.1 Main Files

| Type | File |
|---|---|
| Writing Skill | `webnovel-writer/skills/webnovel-write/SKILL.md` |
| Context Agent | `webnovel-writer/agents/context-agent.md` |
| Data Agent | `webnovel-writer/agents/data-agent.md` |
| Reviewer | `webnovel-writer/agents/reviewer.md` |
| Reference analysis Agent | `webnovel-writer/agents/deconstruction-agent.md` |
| Initialization Skill | `webnovel-writer/skills/webnovel-init/SKILL.md` |
| Planning Skill | `webnovel-writer/skills/webnovel-plan/SKILL.md` |
| Review Skill | `webnovel-writer/skills/webnovel-review/SKILL.md` |
| Query Skill | `webnovel-writer/skills/webnovel-query/SKILL.md` |
| Lightweight Skills | `webnovel-learn`, `webnovel-dashboard`, `webnovel-doctor` |

### 6.2 References and Reading Optimization

Top-level and per-Skill references total 60+ files, an underestimated token cost. Optimize through the existing loading map, explicit read modes, and cleanup of migrated dead files, not new references.

#### 6.2.1 Baseline: reference-loading-map

`references/index/reference-loading-map.md` records actual per-step consumption:

- **Direct Markdown Read** (whole files): the main problem.
- CSV retrieval through `reference_search.py` with `--table --query --genre`: already a model for targeted reads.
- Indirect CSV consumption through `story-system`: already on demand.

The CSV path is correct. **Do not rebuild retrieval**; fix direct full-Markdown reads and evolve the map from what is read to how.

#### 6.2.2 Token Targets: Large Always-Full Markdown Files

These direct always/frequent reads create recurring init/plan/write costs. Counts were measured line by line; section structure was checked:

| File | Lines | Full-read consumer | Target section instead |
|---|---|---|---|
| `references/genre-profiles.md` | 696 | init + plan always | One `### 2.x` genre (13 profiles, ~44 lines each); add Profile Fields if needed. One book uses one profile: ~90% saved |
| `skills/webnovel-init/references/creativity/selling-points.md` | 687 | init Step 5 always | Section 9 positioning template; optionally 1.3 golden formula / 7 practical checklist |
| `references/reading-power-taxonomy.md` | 361 | plan Step 7 | Needed type section: Hook Types / Payoff Patterns / Micro-Payoffs |
| `skills/webnovel-plan/references/outlining/chapter-planning.md` | 322 | plan Step 7 | Section 10 structured nodes (CBN/CPNs/CEN), plus Section 7 template as needed |
| `skills/webnovel-init/references/creativity/creativity-constraints.md` | 327 | init Step 5 always | Score display: 8.1 five-dimensional scoring (~10 lines); collection: schema / hard constraints / scoring |
| `skills/webnovel-write/references/polish-guide.md` | 351 | write Step 4 always | Section 2 execution order; separately read Phase 1 Anti-AI vocabulary supplement. **Never migrate into CSV (csv/README boundary)** |
| `references/shared/cool-points-guide.md` | 313 | plan/review triggers | Required payoff dimension; relevant genre under Genre Adaptation |

Keep short files, such as 111-line `references/shared/strand-weave-pattern.md`, as full reads.

> Standard section read: built-in Grep content output matching `^#{2,4} ` locates heading lines; Read offset/limit retrieves the section. Locate the actual current heading text for the listed sections.
> Earlier shell-pipeline counts were systematically low; this table uses line-by-line scripts. Measure other reference counts similarly.

#### 6.2.3 Dead Reference Cleanup (Verify CSV Coverage First)

Migration of `skills/webnovel-write/references/writing/*.md → CSV` in `reference-gap-register.md` is partly complete. The loading map lists combat-scenes, dialogue-writing, emotion-psychology, scene-description, desire-description, and genre-hook-payoff-library as no longer directly read, with CSV handling triggers. Files remain, approximately 1,400 lines of dead content. Procedure:

1. Check whether `场景写法.csv` / `写作技法.csv` genuinely covers each candidate; do not blindly delete.
2. If covered, delete or retain a CSV pointer stub.
3. If not, manually add missing entries under `csv/README.md` migration rules before retiring Markdown.

#### 6.2.4 Correct Outdated New-Reference Candidates

Reassess v2 Section 6.2 candidates against current state:

| v2 candidate | Current state | Action |
|---|---|---|
| `blocking-override-guidelines.md` | Already exists (gap-register 2026-04-16) | Reuse, not new |
| `chapter-node-rules.md` | Duplicates chapter-planning.md structured-node section | No new file; section read |
| `init-flow.md` | Duplicates existing init-collection-schema.md | Reuse with section reads |
| `subagent-contracts.md` | Conflicts with producer ownership: shape in Skill, schema in Agent | Do not create |
| `polish-checklist.md` | Could summarize polish-guide.md | Not by default; use short Skill checklist/section index if needed, never CSV |

Do not create references to force a three-part structure. Improve reads and remove dead files before adding files.

---

## 7. Phase 0: Baseline, Read Audit, and Red-Line Tests

### 7.1 Goal

Determine what to retain/move/delete/read differently; establish behavior tests for cross-layer red lines before slimming.

### 7.2 Work

1. Measure eight Skills, four Agents, and references. Reuse loading-map/Section 6 line counts.
2. Classify each file under Section 4: main-agent contract shape / subagent / runtime / references / changed reading / Section 3 red line.
3. **Optional token baseline, directional only**: Estimate main-agent context for one default chapter (main Skill + inline content + full references). Not a pass/fail threshold.
4. **Read audit**: Label direct reads Full / Section / Retrieval / None, targeting 6.2.2 first.
5. **Tests before slimming, distinguishing A/B**: Replace wording-only/missing A-class assertions with behavior/contracts and make them green first. B-class new ownership/tools/persistence/precommit-diff contracts are not implemented: write assertions as explicit pending (`xfail` / `skip` or eval pending), then activate in the relevant phase. Phase 0 need not pass B.
6. **Tool verification**: Record Claude Code version, official docs URL/date, current-session tool summary, registered Agent/Skill names. Design built-ins/Bash around official behavior. Record PowerShell availability/enabled state and Windows-only fallback limits, not a default path. Record official constraints: no subagent spawning; no Agent/AskUserQuestion in subagent design; tools/disallowedTools define boundaries; skills preloads full Skills; allowed-tools preapproves rather than restricts. Verify actual registrations/frontmatter/allowed-tools against local plugin-dev.
7. Run baseline checks:

```bash
python -m pytest webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py -q --no-cov
python -X utf8 webnovel-writer/scripts/run_behavior_evals.py --format json
python -X utf8 webnovel-writer/scripts/validate_plugin_package.py --format json
```

### 7.3 Acceptance

- Save a traceable per-file retain/move/delete/read-mode inventory, not merely a verbal conclusion.
- Optional token estimate recorded directionally; absence does not block acceptance.
- All Section 5.2 red lines have behavior/contracts: A passes; B is explicitly pending.
- Save the ownership matrix; its B-class assertions become mandatory as relevant phases land, checked by prompt integrity/behavior eval.
- Current validation commands pass.

---

## 8. Phase 1: Slim `webnovel-write`

### 8.1 Goal

Turn a tutorial into an orchestration contract while preserving the whole workflow.

### 8.2 Preserve

- Default / `--fast` / `--minimal` modes.
- Preparation: preflight, where, placeholder-scan, real CHAPTER_GOAL, story-system refresh, prewrite gate.
- context-agent, reviewer, data-agent invocations.
- Drafting from only the five-part brief.
- Raw reviewer JSON + `review-pipeline --save-metrics`.
- Targeted blocking fixes/user adjudication; no fabricated pass.
- Polishing order/final Anti-AI check.
- Three data artifacts.
- Precommit gate.
- chapter-commit.
- Postcommit gate.
- projections retry.
- `backup --project-root "${PROJECT_ROOT}"`.
- Success criteria and failure recovery.

### 8.3 Compress

- Context-agent query internals.
- Reviewer dimension-by-dimension methods.
- Complete data-agent payload schema.
- Long polishing tutorials/examples.

### 8.4 Target Agent Calls

Context-agent:

```text
Use the Agent tool to run `webnovel-writer:context-agent`.

Task:
- chapter={chapter_num}
- project_root=${PROJECT_ROOT}
- scripts_dir=${SCRIPTS_DIR}
- storage_path=${PROJECT_ROOT}/.webnovel
- state_file=${PROJECT_ROOT}/.webnovel/state.json (projection/read-model, compatibility reads only)
- Research first, then return a five-part brief ordered by hard constraints -> CBN/CPNs/CEN -> forbidden content -> style guidance -> supplementary dynamic_context.
- Return a blocker if context is insufficient.
```

Reviewer:

```text
Use the Agent tool to run `webnovel-writer:reviewer`.

Task:
- chapter={chapter_num}
- chapter_file=${CHAPTER_FILE}
- project_root=${PROJECT_ROOT}
- scripts_dir=${SCRIPTS_DIR}
- Return strict raw JSON only; do not write files.
- Main flow writes the returned JSON to ${PROJECT_ROOT}/.webnovel/tmp/review_results.json.
- No scoring or prose summary.
```

Data-agent:

```text
Use the Agent tool to run `webnovel-writer:data-agent`.

Task:
- chapter={chapter_num}
- chapter_file=${CHAPTER_FILE}
- project_root=${PROJECT_ROOT}
- scripts_dir=${SCRIPTS_DIR}
- output_dir=${PROJECT_ROOT}/.webnovel/tmp
- Generate fulfillment_result.json, disambiguation_result.json, extraction_result.json.
- Do not directly write state/index/summaries/memory/vectors/projection.
```

Persistence must match frontmatter. Default reviewer lacks Write and returns JSON for main-flow saving; data-agent has Write and saves three artifacts. Any future change must update templates, frontmatter, and prompt integrity together, preserving one writer per artifact.

### 8.5 Risk Controls

- Precommit gate/artifact_validator enforce schemas.
- Behavior eval checks gates, artifacts, precommit diff scope, commit, postcommit, backup.
- Prompt integrity checks no bare git add, no subagent substitution, and ownership/tools alignment.

---

## 9. Phase 2: Slim Four Agents

### 9.1 `context-agent`

Goal: Context compressor producing stable `chapter_task_brief`.

Preserve:

- `memory-contract load-context`.
- On-demand `query-entity`, `query-rules`, `get-timeline`.
- No duplicate queries for load-context content.
- `.story-system/` contracts first; state.json compatibility only.
- Actual outline goal / `chapter_directive.goal` first; dynamic_context technique reference only.
- Five parts: opening commission, chapter story, characters, writing flow, ending point.
- Red-line validation and insufficient-context blocker.

Remove/compress long examples, overly detailed inference explanations, unnecessary terminology.

### 9.2 `data-agent`

Goal: Fact extraction/artifact generation only.

Preserve:

- Read prose, entity index, aliases.
- Three artifact filenames.
- fulfillment top-level `planned_nodes`, `covered_nodes`, `missed_nodes`, `extra_nodes`.
- disambiguation top-level `pending`.
- extraction top-level `accepted_events`, `state_deltas`, `entity_deltas`, `entities_appeared`, `scenes`, `summary_text`.
- Event minimum: `event_id`, `chapter`, `event_type`, `subject`, `payload`.
- state_deltas `field`, `old`, `new`.
- entity_deltas `entity_type`.
- No direct state/index/summaries/memory/vectors/projection writes.

Remove/compress long event_type payload explanations, JSON examples, and legacy-field discussions.

### 9.3 `reviewer`

Goal: Verifiable factual review only.

Preserve:

- Five dimensions: setting, timeline, continuity, character, logic.
- dimension_results for each, including pass when clean.
- Evidence and fix_hint for each issue.
- No scoring, prose-quality judgment, new-plot recommendations, or unreached-outline spoilers.
- Strict JSON.

Remove/rewrite chain-of-thought/ReAct wording and overlong tutorials.

### 9.4 `deconstruction-agent`

Goal: Transferable reference patterns without canon contamination.

Preserve:

- quick / deep / auto routing.
- No invented opening-three-chapter/cast/setting/plot analysis from title/platform alone.
- No file writes.
- No new-book canon generation.
- `init_reference_research` JSON.
- `quality`, `resume_state`, `do_not_copy`, `canon_contamination_warnings`.
- Quick/deep modes, plot points, quality gates, abstraction/transformation rules.

Compress long quality tables, excessive schema detail, lengthy deep-analysis stage explanations.

---

## 10. Phase 3: Slim Init / Plan / Review Skills

### 10.1 `webnovel-init`

Retain Section 3.2's full chain.

Compression:

- Keep collection details in existing `skills/webnovel-init/references/init-collection-schema.md` with section reads; no init-flow.md (6.2.4).
- Genre list retains canonical set and a few examples.
- Replace long CLI-argument tables with parameters sourced from collection objects, but still explicitly execute init.
- Read creative constraints, anti-tropes, worldbuilding guides on demand.

Never remove inspiration question Step 1.5; deconstruction-agent boundaries; confirmation before canon; safe confirmed root; idea_bank.json; master-outline patch; post-init MASTER_SETTING; validation/minimal rollback.

### 10.2 `webnovel-plan`

Retain Section 3.3's full chain.

Compression:

- CBN/CPN/CEN details remain in chapter-planning.md's structured-node section, read selectively; no chapter-node-rules.md.
- Replace long reference tables with stage-triggered reading.
- Move structured-node examples out of main text.

Never remove placeholder-scan; cross-volume state; setting baseline; beat sheet; timeline; volume outline; batch chapter outlines; setting writeback; explicit `大纲/第{volume_id}卷-总纲写回.json`; master-outline-sync; update-state; actual CHAPTER_GOAL contract refresh.

### 10.3 `webnovel-review`

Retain Section 3.5's full chain.

Leave methods with reviewer and avoid detailed evidence-query procedure in Skill.

Never remove missing-contract story-system refresh; reviewer invocation; review-pipeline --save-metrics; update-state --add-review; blocking user adjudication.

---

## 11. Phase 4: Slim Lightweight Skills

### 11.1 `webnovel-query`

Goal: Classify, then narrow tools.

Retain read-only behavior, root protection, source priority (.story-system → latest accepted commit → memory-contract → projection fallback), and fallback disclosure.

Optimize:

- No default full memory-contract load-context; choose narrow tools by query.
- Character state: knowledge query-entity-state.
- Relationships: knowledge query-relationships.
- Rules: memory-contract query-rules.
- Foreshadowing: open-loop queries.

### 11.2 `webnovel-learn`

Keep minimal: root protection, current chapter, project-memory add-pattern, no handwritten JSON.

### 11.3 `webnovel-dashboard`

Keep read-only Dashboard, story-runtime/health, root resolution, frontend-dist validation.

Do not install dependencies by default; show commands when missing. Lightweight pre-launch checks are optional.

### 11.4 `webnovel-doctor`

Keep read-only diagnosis, project-status first, phase-aware doctor, no repairs/installations/Dashboard start.

The original plan proposes a concise Chinese trigger-oriented frontmatter description.

---

## 12. Phase 5: Tests and Behavior Validation

### 12.1 Files

- `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`
- `webnovel-writer/evals/fixtures/behavior/fast.json`
- Add behavior/contract assertions; delete/migrate obsolete wording assertions (12.2).

### 12.2 Acceptance: Behavior/Contracts, Not Wording

Assert correct actions, not the presence of particular strings. `fast.json`'s `commit_projection_runtime`, which actually runs commit→projection and checks state, is the model. Gradually retire `assert "字符串" in text`.

#### Required Behaviors

- Writing chain: ordered prewrite/precommit/postcommit gates; one reviewer round; targeted blocking fixes/adjudication; three data artifacts; read-only diff after precommit and before chapter-commit; runtime/SQLite read-only semantics for database/read models; commit drives projections; all five projections done/skipped; retry projections only; project-root backup.
- Artifact contracts: runtime schemas (`chapter_commit_schema` / `story_event_schema` / `schemas`) validate fields. **Add negative precommit cases**: missing missed_nodes / pending / key fields must block. This replaces main-Skill field-name wording tests.
- Eight Skills discoverable, valid frontmatter, triggerable descriptions, Chinese-first language in the original plan.
- Four single-file Agents with name/description/model/color, minimal tools aligned with persistence, no agents/references dependency.
- Agent boundaries: data-agent no direct projections; reviewer structured JSON/five dimensions; context-agent five-part brief/load-context; deconstruction-agent no files, init_reference_research, canon protection, Step 1.5/confirmation gate.
- Ownership: review_results, data artifacts, metrics/report, state/index/summaries/memory/vector each have one writer. Prompts neither assign duplicate writers nor leave persistence unspecified. SQLite/binary acceptance uses runtime queries, not diff contents.
- Plan preserves .story-system main chain, beats/timeline/nodes/master writeback/state updates. Query/dashboard/doctor remain read-only without project writes.

#### Existing Assertions to Delete / Migrate / Relax

| Assertion | Problem | Action |
|---|---|---|
| `test_webnovel_write_data_agent_prompt_requires_extraction_schema` | Requires schema fields verbatim in main Skill, violating ownership | **Delete**; protect in data-agent schema and negative precommit tests |
| Field list in `test_data_agent_is_described_as_extraction_only...` | Wording-level field presence | Strengthen into contract validation of data-agent's single-file schema |
| `test_agent_template_structure` requiring sections 1-8 | Forces filler; removing ReAct causes false failures | **Relax**: renumber/reduce required sections; no empty filler |
| Wording-bound `assert "字符串" in SKILL.md` | Obstructs slimming | Replace with behavior/contracts or move to producer |

### 12.3 Commands

Documentation/prompts:

```bash
python -m pytest webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py -q --no-cov
python -X utf8 webnovel-writer/scripts/run_behavior_evals.py --format json
python -X utf8 webnovel-writer/scripts/validate_plugin_package.py --format json
```

Conservative regression:

```bash
python -m pytest webnovel-writer/scripts/data_modules/tests webnovel-writer/scripts/tests -q --no-cov
```

### 12.4 Acceptance Criteria

- Eight Skills still discoverable; four Agents have valid frontmatter.
- Official plugin-structure and plugin-dev compliance.
- Behavior eval, package validator, prompt integrity pass after retiring wording assertions and adding behavior/contracts.
- All 5.2 red lines protected.
- Ownership/tools align; precommit diff exists and is read-only; database semantics covered by runtime/SQLite queries.
- Main-agent context per chapter should decrease directionally from Phase 0. Token numbers are not hard gates; missing estimates or insufficient reduction do not fail acceptance.
- No long subagent internals/data schemas in main Skill; authority belongs to producing Agent + runtime.
- Target references use on-demand reads; dead references verified/handled.
- Section 3 end-to-end steps remain intact.

---

## 13. Official plugin-dev Constraints

Follow local official plugin guidance:

```text
C:\Users\lcy\.claude\plugins\marketplaces\claude-plugins-official\plugins\plugin-dev
```

Rules:

- plugin-structure: `.claude-plugin/plugin.json` under plugin root; skills/agents/hooks/scripts remain root-level.
- skill-development: one directory per Skill with SKILL.md; at least name and concrete trigger description; details in its own references, loaded on demand.
- agent-development: one agents/*.md per Agent; name/description/model/color; minimum tools.
- Four Agents are explicitly invoked by Skills, not automatic triggering. Descriptions need caller, responsibility, deliverable.
- No external references as hidden Agent manuals.
- hook-development: wrapper hooks/hooks.json; `${CLAUDE_PLUGIN_ROOT}` command paths.
- After each component round, validate manifest, skills, agents, hooks, README, LICENSE, sensitive information, and portable paths using plugin-validator principles.

---

## 14. Risks and Controls

| Risk | Impact | Control |
|---|---|---|
| Formatting removes real workflow | Broken writing chain | Section 3 assertions; prompt integrity/behavior eval |
| Overslim main Skill | Insufficient Agent inputs | Keep minimal input contracts |
| Compressed schema loses fields | Precommit failure | artifact_validator/precommit gate |
| Agent file too short | Lower specialist quality | Retain minimum procedure/boundaries/output contract |
| Persistence mismatches tools | Missing reviewer/data tmp JSON | Give Write or main-flow persistence; integrity checks |
| Duplicate/no writers | Overwrites/missing files | Ownership matrix, one-writer behavior tests |
| Diff check becomes Git commit flow | Workspace pollution/unrelated staging | Only diff --name-status / --check; no add/commit |
| Assuming diff validates databases | Missed SQLite/vector/ignored-file errors | Runtime gate, projection_status, read-only SQLite queries |
| Too much moved to references | Forgotten reads | Keep triggers in main flow |
| Section-anchor drift | Wrong/empty reads | Stable headings; warn and fall back to full read |
| Wording assertions block slimming | Tests mistaken for constraints | Retire/migrate to behavior/contracts after checking red lines |
| Narrow queries miss answers | Lower query quality | Supplement on demand and disclose fallback |
| state.json treated as truth | Post-writing fact drift | Explicit .story-system/accepted-commit priority |
| Reference analysis contaminates canon | Infringement/imitative settings | No deconstruction file writes; confirmed transformed patterns only |

---

## 15. Recommended Work Order

1. Phase 0: baseline/read audit/token estimate; **green A-class behavior tests first, B-class pending assertions**.
2. webnovel-write: preserve chain, slim main Skill, retire wording-based schema assertions.
3. context-agent: stable five-part brief/context compression.
4. data-agent: single-file schema authority, remove long payload tutorials, add negative precommit cases.
5. reviewer + webnovel-review: remove ReAct meta-narration, renumber, unify structured review.
6. webnovel-init + deconstruction-agent: preserve confirmation/canon protection.
7. webnovel-plan: preserve planning-to-contract bridge.
8. References/read modes under 6.2; clean dead files/update loading map.
9. Query / learn / dashboard / doctor.
10. Final tests/evals.

Reasons:

- Writing consumes most tokens and is most vulnerable to context contamination; webnovel-write contains the most subagent detail, giving highest initial return.
- A green red-line baseline makes later slimming safe.
- Reference optimization is a separate cross-Skill step using one loading-map baseline.

---

## 16. Target Outcome

The writing chain becomes:

```text
preflight / where / placeholder-scan
  ↓
Resolve actual CHAPTER_GOAL
  ↓
story-system refreshes runtime contracts
  ↓
write-gate prewrite
  ↓
context-agent generates five-part brief
  ↓
Main agent drafts from brief
  ↓
reviewer reviews
  ↓
review-pipeline persists results
  ↓
Main agent applies targeted fixes and polishing
  ↓
data-agent generates artifacts
  ↓
write-gate precommit
  ↓
chapter-commit
  ↓
write-gate postcommit
  ↓
projection retry (failures only)
  ↓
backup
```

Each layer knows only what it needs:

- Main agent: orchestration and mandatory runtime commands.
- Context-agent: context compression.
- Reviewer: review.
- Data-agent: fact extraction.
- Runtime: validation, commits, projections, state advancement.

The goal is not shorter documents, but each piece of context appearing only when it is needed.
