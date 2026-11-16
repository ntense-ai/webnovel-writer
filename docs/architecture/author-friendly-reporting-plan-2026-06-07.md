# Author-Friendly Reporting and Exception Visibility Plan

> Historical design record: project-directory examples retain their original names. New projects use `chapters/`, `outlines/`, `settings/`, and `reviews/`; existing legacy projects remain supported without renaming. Resolve actual paths with `scripts/project_paths.py` before using these examples.

> Date: 2026-06-07
> Status: Draft v2 · aligned with `docs/superpowers/specs/2026-06-07-author-friendly-experience-design.md`
> Scope: Implement the specification's seven Author Shell / Author Layer components, standardizing final reports, subagent return protocols, error catalog, author-facing review view, next steps, exception categories, timing, and terminology for init / plan / write / review; remove token statistics for now
> Principles: Never hide problems; disclose automatic handling; hide technical details by default; reports address authors, not engineering logs; leave the engine unchanged
> Implementation: Establish behavior through Skill / Agent contracts, then consolidate formatting in runtime helpers rather than rely on prompts alone

---

## 0. Alignment with the Product Specification

This is the engineering implementation plan for `docs/superpowers/specs/2026-06-07-author-friendly-experience-design.md`, not a separate product definition.

Responsibilities:

| Document | Owns | Does not own |
|---|---|---|
| Product specification | Engineering Core + Author Shell layers, seven components, recovery boundaries, staged value | Specific files, tests, execution order |
| This plan | Maps components to Skills / Agents / runtime helpers / tests / docs | Redefining product goals or weakening hard limits |

Shared boundaries:

- Do not change engine semantics or weaken checks in Story System, `write-gate`, `chapter-commit`, projections, or RAG.
- Authors see milestones, conclusions, impact, and next steps by default. Commands, JSON, schemas, and tracebacks belong in logs/technical details.
- Automatic handling is limited to idempotent, retryable process problems that do not touch author content; final reports must disclose it.
- No new UI, buttons, progress bars, command aliases, or broad automatic-repair loop.

Component mapping:

| Specification component | Plan location |
|---|---|
| Glossary | §5 single source; structured vocabulary in Phase 1 |
| Progress narration | §8 process usability; Phase 5A |
| Error → action mapping | §15 classifications + Phase 4 helpers; new `error_catalog.py` and `author_error_catalog.json` |
| Review Author View | §16 helpers / `review_pipeline.py` rendering; prioritize review in Phase 4 |
| Next-Step Advisor | Third report section in §4; early delivery in §20 |
| Task language | Next steps in §4 / §19 / §23; wording only, no aliases |
| Automatic handling + quiet engineering details | §3.2–3.4, §11, §15, §21; disclosure/logging only before stage three, no allowlist expansion |

## 1. Goals

Replace ad hoc main-agent summaries after execution with stable, readable, trustworthy author receipts on every run.

Core deliverables:

1. Standard final report: one overall status followed by three fixed sections for every main Skill.
2. Global author-friendly rules: Chinese-language author communication, little jargon, no hidden problems, disclosure of automatic handling, technical details on demand.
3. Stage-specific templates for `/webnovel-init`, `/webnovel-plan`, `/webnovel-write`, and `/webnovel-review`.
4. Subagent return protocol: aggregate status, issues, automatic handling, and duration from context-agent, reviewer, data-agent, and deconstruction-agent.
5. Exception categories: handled automatically / confirmation recommended / must resolve; expose subagent failures, skips, retries, and incomplete output.
6. Timing visibility: elapsed time and key-step durations; explain possible causes/impact of stalls without promising fixed completion times.
7. Translate engineering terminology into meaningful writing concepts.
8. Unified runtime report helper consuming existing structured project-status, doctor, write-gate, review-pipeline, chapter-commit, projection_log, etc.
9. Usable long workflows: clear progress, fewer interruptions, recoverable state, understandable blockers.
10. Checkpoint resume: repeating the same command recognizes completed steps and resumes from the latest reliable checkpoint rather than requiring special retry commands.
11. Interactive decisions: bounded choices for user-required decisions rather than asking authors to figure out file edits themselves.
12. Technical traceability: concise reports plus local engineering logs for feedback and diagnosis.
13. Error catalog mapping runtime codes to understandable causes, impact, and actions.
14. Author-facing review headline and at most 3 actionable changes.
15. Task-oriented next steps and copyable commands, without new aliases.

---

## 2. Background

The underlying workflow is already fairly complete:

- `project-status` determines stage and next action.
- `doctor` provides stage-aware diagnostics.
- `write-gate` covers prewrite, precommit, and postcommit.
- `review-pipeline` normalizes reviews, generates reports, and persists metrics.
- `chapter-commit` records postwrite facts and drives state / index / summary / memory / vector projections.
- `projection_log` identifies projection status.

The gap is not missing checks, but inconsistent translation of results for authors:

1. Final replies vary, forcing authors to reassess whether work is really complete.
2. Technical details, JSON, and command output impose reading burden.
3. Degradation, skips, retries, or automatic handling may remain internal and absent from the final report.
4. Subagent success, completeness, and duration lack unified aggregation.
5. The four main workflows have clear success criteria but unclear author-delivery requirements.
6. Authors may not know the current step, why they are waiting, whether intervention is needed, or whether interrupted work can resume.
7. Recovery often requires understanding internal steps and retry commands.
8. User-required decisions become errors with long explanations rather than clear choices.

Do not rewrite the main writing pipeline or add a broad repair loop. Add an understandable delivery layer.

---

## 3. Design Principles

### 3.0 Claude Code Capability Boundaries

Use existing Claude Code capabilities and implementable plugin runtime features. Do not invent UI, background tasks, or interaction mechanisms.

Available capabilities:

- `SKILL.md` constrains workflow and final output.
- The main workflow invokes registered subagents through `Agent`.
- It may use `AskUserQuestion` for key decisions when allowed by Skill frontmatter and supported by the host.
- `Read` / `Write` / `Edit` / `Bash` access files and run plugin scripts.
- Python CLI reads/writes `.webnovel/`, `.story-system/`, logs, and intermediate artifacts.

Do not assume:

- Live progress bars, graphical buttons, background queues, or native terminal menus.
- Automatic structured subagent metadata; implement it through prompt protocols and main-workflow records.
- Built-in Skill checkpoint resume; implement it using artifacts, run ledger, and gates.
- Complex forms in AskUserQuestion; keep 2–3 short options.
- Automatically available logs, durations, or recovery points; explicitly record them.

Progress messages are short main-workflow updates at key points. Interactive decisions are bounded choices through AskUserQuestion or ordinary conversation. Resume is plugin file/state inspection, not a built-in Claude Code workflow engine.

### 3.1 Author-Friendly, Not an Engineering Showcase

The original product calls for understandable Chinese-language author output, avoiding raw terms such as subagent, artifact, projection, schema, and runtime contract. Examples here are translated for English documentation.

Retain paths/commands in details when needed, but lead with impact:

```text
Saving this chapter's story facts failed. Later queries may not know what happened in it.
```

Not:

```text
data-agent artifact schema_error: extraction_result missing accepted_events
```

### 3.2 Never Hide Problems

Always include in final reports:

- Subagent invocation failure
- Subagent skipped by the user's selected mode
- Incomplete subagent output
- Skipped reviewer or `--minimal` no-review artifact
- Missing/invalid data-agent result among its three artifacts
- Any failed write-gate stage
- Rejected chapter-commit
- Failed / pending / missing projection
- RAG fallback
- Backup failure
- Unusual duration

### 3.3 Disclose Automatic Handling

Briefly disclose actions such as:

- Projection retries
- Fallback to keyword retrieval
- Allowlisted nonblocking targeted fixes, such as formatting or unambiguous typo correction
- Replacing an old no-review artifact
- Git initialization or fallback to local backup

Explain what was handled and its effect on results, not every internal step.

### 3.4 Hide Technical Detail by Default

Lead with conclusions and impact. Add paths, commands, or error types only when the user needs to act.

### 3.5 Runtime First, Prompts as Fallback

Do not rely on main-agent judgment for states the runtime can confirm.

The report helper prioritizes structured inputs:

- `project-status --format json`
- `doctor --format json`
- `write-gate --format json`
- `review-pipeline` payload
- `chapter-commit` payload
- `projection_log`
- Subagent run summary

Skill documents define required reporting, not independent formats.

### 3.6 Process Usability Is Part of Delivery

A final report reduces uncertainty after completion, not anxiety during execution.

Long workflows must keep authors informed of:

1. The current step
2. Its expected output
3. Whether a decision is needed
4. Any blocker and its effect on completed work

Keep updates short, low-jargon, and unobtrusive. Continue by default; interrupt only for creative direction, factual consistency, or file safety.

### 3.7 Prefer Automatic Recovery

Explaining recovery is the minimum; repeating the same command to resume is the goal.

Move toward idempotent main workflows:

- Do not regenerate reliable completed artifacts.
- Preserve prose, reviews, and intermediate results after failure.
- Check checkpoints first on a repeated command and resume from the latest failure.
- Rerun prior steps only for stale artifacts, changed parameters, or explicit rewrite requests.

### 3.8 Traceability Without Burdening Authors

Hide JSON, schemas, tracebacks, and complete logs by default, but preserve local evidence for:

- Developer diagnosis
- User reports of unrecoverable failures
- Helper checkpoint/step-state decisions

Ordinary reports need only a low-friction note:

```text
To report this failure, attach .webnovel/logs/run_last.log.
```

---

## 4. Standard Final Report

All main Skills use:

```text
Overall status: Completed / Partially completed / Action required / Not completed.

1. Files produced and completion status
- ...

2. Issues and unusually slow steps
- Handled automatically: ...
- Confirmation recommended: ...
- Must resolve: ...
- Unusual duration: ...

3. Recommended next steps
- ...
```

Status meanings:

| Status | Meaning |
|---|---|
| Completed | All stage artifacts exist and key checks pass; ready for next step |
| Partially completed | Main artifacts exist, with skips, fallback, unfinished items, or nonblocking issues |
| Action required | Results can be preserved, but user confirmation, judgment, or information is required |
| Not completed | Missing key artifacts or blocking failure prevents the next stage |

---

## 5. Terminology Mapping (Single Source of Truth)

Maintain one Author Layer glossary rather than a separate vocabulary in each Skill.

Use structured data initially for helpers and prompt-integrity tests:

```text
webnovel-writer/references/author_glossary.json
```

A Markdown summary is optional; implementation/tests treat JSON as authoritative.

Maintenance rules:

- Skills/Agents may reference terms but not invent inconsistent translations.
- `user_report.py`, `error_catalog.py`, and Review Author View share the glossary.
- Unknown terms remain unchanged, with impact explained first; add glossary entries later rather than inventing translations on the fly.
- Tests check key terms and explanations, not exact wording.

| Engineering term | Author-friendly expression |
|---|---|
| subagent | Writing / review / research / book-analysis assistant |
| context-agent | Writing preparation |
| reviewer | Writing check |
| data-agent | Save this chapter's story facts |
| deconstruction-agent | Analyze reference works |
| artifact | Intermediate result file |
| review_results | Writing-check results |
| fulfillment_result | Chapter-goal completion |
| disambiguation_result | Names/settings awaiting clarification |
| extraction_result | New story facts in this chapter |
| chapter-commit | Submit chapter facts |
| projection | Update story records |
| state / index / summary / memory / vector | State / index / summary / long-term memory / search library |
| blocking issue | Problem preventing continued writing |
| fallback | Temporary fallback reading |
| runtime contract | Chapter writing requirements |
| schema error | Incomplete intermediate-result format |
| pending | Awaiting confirmation |
| rejected | Chapter facts not accepted |
| accepted | Chapter facts accepted |

---

## 6. Scope of Changes

### 6.1 Skill / Agent Documents

- `webnovel-writer/skills/webnovel-init/SKILL.md`
- `webnovel-writer/skills/webnovel-plan/SKILL.md`
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- `webnovel-writer/skills/webnovel-review/SKILL.md`
- `webnovel-writer/agents/context-agent.md`
- `webnovel-writer/agents/reviewer.md`
- `webnovel-writer/agents/data-agent.md`
- `webnovel-writer/agents/deconstruction-agent.md`

### 6.2 Runtime Helpers

Add:

- `webnovel-writer/references/author_glossary.json`
- `webnovel-writer/references/author_error_catalog.json`
- `webnovel-writer/scripts/data_modules/author_glossary.py`
- `webnovel-writer/scripts/data_modules/error_catalog.py`
- `webnovel-writer/scripts/data_modules/review_author_view.py`
- `webnovel-writer/scripts/data_modules/user_report.py`
- `webnovel-writer/scripts/data_modules/run_ledger.py`
- `webnovel-writer/scripts/data_modules/run_logger.py`
- `webnovel-writer/scripts/data_modules/tests/test_author_glossary.py`
- `webnovel-writer/scripts/data_modules/tests/test_error_catalog.py`
- `webnovel-writer/scripts/data_modules/tests/test_review_author_view.py`
- `webnovel-writer/scripts/data_modules/tests/test_user_report.py`
- `webnovel-writer/scripts/data_modules/tests/test_run_ledger.py`
- `webnovel-writer/scripts/data_modules/tests/test_run_logger.py`

Modify:

- `webnovel-writer/scripts/data_modules/webnovel.py`
- `webnovel-writer/scripts/review_pipeline.py`
- `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`
- `webnovel-writer/skills/webnovel-write/SKILL.md`

### 6.3 Prompt / Behavior Tests

Modify or add:

- `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`
- `webnovel-writer/evals/fixtures/behavior/fast.json`

---

## 7. Capability Mapping and Implementation Boundaries

| Usability goal | Available Claude Code capability | Plugin additions / changes | Does not depend on |
|---|---|---|---|
| Progress messages | Main-workflow natural-language output | Skill requirements at key nodes | Live progress bars |
| Initial expectations | Short introductory output | Workflow overview template | Background duration-estimation system |
| Final report | Main-workflow final reply | `user_report.py` text/json rendering | Automatic host formatting |
| Subagent status aggregation | Agent calls + main-workflow records | `SubagentRun` protocol and aggregation | Automatic subagent telemetry |
| Exception classification | Read runtime JSON | `user_report.py` classification | Host error classification |
| Timing | Bash/Python timers or workflow records | Ledger/helper step times | Built-in performance panel |
| Checkpoint resume | Python CLI and local files via Bash | `run_ledger.py`, artifact trust checks, gate reuse | Built-in resume engine |
| Interactive decisions | AskUserQuestion or conversation | Bounded options and branches | Graphical buttons / complex forms |
| Traceability | Python local logs | `run_logger.py`, sensitive-data filtering | Automatic host log export |
| Next-step commands | Final-report text | Suggested commands in user_report | One-click buttons |

Principles:

1. Implement with existing Skill / Agent / Bash / Python CLI capabilities first.
2. Every runtime judgment needs evidence in local files, JSON, or command output.
3. UI-like experiences remain text, bounded questions, or reports unless a future Dashboard project explicitly changes that.
4. Do not make unpromised Claude Code behavior an acceptance criterion.

---

## 8. Process Usability

### 8.1 Goal

Without understanding internal engineering, authors should know:

- What the system is doing
- Why it matters
- Whether progress continues
- When their decision is needed
- What has completed after a failure and where to resume

Do not print every command; express long workflows as understandable current actions.

### 8.2 Set Expectations Before Starting

Give a short overview:

```text
Starting chapter 13: gather evidence → draft → check the writing → polish → save story facts → update records and back up.
API, model, and network speeds vary, so there is no fixed completion time. I will ask only when a creative decision or factual conflict needs your judgment.
```

Include:

- This run's goal
- Main steps
- No fixed-duration promise
- Whether the user needs to remain present

### 8.3 Standard Progress Format

Use short messages, no more than two lines:

```text
Gathering this chapter's writing evidence: chapter outline, recent plot, and unresolved foreshadowing.
```

```text
Saving this chapter's story facts: updating the summary, character state, and future retrieval records.
```

Avoid:

```text
Running write-gate --stage precommit and validating artifacts...
```

### 8.4 Stage Names

| Internal step | Progress label |
|---|---|
| preflight | Check project environment |
| placeholder-scan | Check incomplete placeholders |
| story-system | Refresh chapter writing requirements |
| write-gate prewrite | Prewrite check |
| context-agent | Gather writing evidence |
| draft | Draft prose |
| reviewer | Check the writing |
| review-pipeline | Generate the check report |
| polish | Polish and format |
| data-agent | Save chapter story facts |
| write-gate precommit | Pre-submission check |
| chapter-commit | Submit chapter facts |
| write-gate postcommit | Confirm submission |
| projections retry | Retry story-record updates |
| backup | Back up chapter results |

### 8.5 Minimize Interruptions

Do not interrupt unless:

| Must ask | Reason |
|---|---|
| Final init proposal confirmation | Writes core new-book settings |
| Reference analysis is low quality but user wants to adopt it | May contaminate original ideas |
| Planning finds master-outline/setting conflict | Requires creative judgment |
| Writing finds a blocking issue that targeted fixes cannot resolve | Prevents chapter submission |
| Low-confidence data-agent ambiguity affects factual persistence | May write incorrect future state |
| User wants to proceed after commit rejection | Requires explicit risk acceptance |
| Abnormal write scope | May affect other chapters/projects |

Do not ask for:

- Ordinary nonblocking review issues that polishing can address
- RAG fallback that does not affect current writing
- Automatically retryable projections
- Successful fallback from Git to local backup
- Slow execution with otherwise normal results

### 8.6 Long-Workflow Milestones

Show at most 3–6 milestones per main Skill, not every internal command.

`/webnovel-init`:

1. Collect the story's core.
2. Organize creative constraints.
3. Await final confirmation.
4. Create project files.
5. Generate main-pipeline foundation records.
6. Verify readiness for planning.

`/webnovel-plan`:

1. Read master outline and existing plot state.
2. Complete the settings baseline.
3. Plan volume pacing and timeline.
4. Break down chapter outlines.
5. Write back new settings.
6. Refresh writing requirements.

`/webnovel-write`:

1. Check prewrite conditions.
2. Gather writing evidence.
3. Draft prose.
4. Check and polish.
5. Save chapter story facts.
6. Submit, update records, and back up.

`/webnovel-review`:

1. Confirm target chapters.
2. Gather review evidence.
3. Check the writing.
4. Generate/persist the review report.
5. Await user decisions on blockers, if any.

### 8.7 Feedback When Blocked

Do not merely report an error. Explain:

1. The blocked step
2. Completed work
3. Recovery action

Example:

```text
Blocked at “Save chapter story facts”: prose and the review report are complete, but extracted facts lack a summary field.
I will rerun the records assistant. If it still fails, I will preserve the prose and review without submitting incomplete facts.
```

### 8.8 Recovery-Point Notices

Both progress feedback and final reports should identify recovery points after interruption/failure:

| Blocker | Recovery |
|---|---|
| context-agent failure | Complete outline/contracts and rerun writing |
| Review fails after drafting | Preserve prose and rerun the writing check |
| Review blockers | Targeted fixes or user decision, then polish |
| Missing data-agent artifact | Rerun saving story facts |
| precommit failure | Fix intermediate results and rerun pre-submission check |
| Rejected commit | Resolve missed_nodes / pending / blocking and resubmit |
| Projection failure | Run `projections retry` |
| Backup failure | Manual/retried backup; accepted facts remain unaffected |

### 8.9 Author-Controlled Detail

Possible future options:

```text
--quiet      Only key confirmations and final report
--verbose    Milestones, exception causes, and key commands
```

Options are not mandatory initially, but Skill documents should follow concise progress + detailed final-report defaults.

---

## 9. Checkpoint Resume

### 9.1 Goal

After incidental failures, authors should not need internal retry commands. Repeating the main command should recognize completed steps and resume from the latest reliable checkpoint.

Example:

```text
The previous chapter 13 run completed drafting and review but stopped while saving story facts.
This run resumes there without rewriting the prose.
```

### 9.2 Checkpoint Sources

Reuse existing artifacts and gates first:

| Step | Reliable completion criterion |
|---|---|
| Prewrite check | `write-gate prewrite ok=true` or a current successful rerun |
| Writing evidence | context-agent brief returned and not stale |
| Drafting | Target prose file exists and is nonempty |
| Writing check | review_results identifies target chapter; review-pipeline report exists |
| Polishing | Prose modified after review report; no anti-ai blocking record |
| Saving facts | Three data artifacts exist and precommit passes |
| Submitting facts | Commit file exists with accepted status |
| Updating records | Postcommit passes; five projections done/skipped |
| Backup | Successful backup result or chapter backup record |

### 9.3 Run Ledger

No complex state machine is needed initially, but add a lightweight ledger:

```text
.webnovel/runs/write_ch0013.json
.webnovel/logs/run_last.log
```

`write_ch0013.json` stores machine-readable progress:

```json
{
  "schema_version": "webnovel-run-ledger/v1",
  "command": "webnovel-write",
  "chapter": 13,
  "started_at": "",
  "updated_at": "",
  "steps": [
    {"id": "draft", "label": "Draft prose", "status": "done", "outputs": ["正文/第0013章.md"]},
    {"id": "data", "label": "Save chapter story facts", "status": "failed", "problem": "API timeout"}
  ]
}
```

`run_last.log` stores engineering detail:

- Commands
- JSON-output summaries
- Tracebacks
- Raw subagent exceptions
- Durations

Do not expand it in author reports; show its path only for unrecoverable failures.

### 9.4 Idempotency Strategy

On a repeated command:

1. Resolve PROJECT_ROOT, chapter, and mode.
2. Read ledger and artifacts.
3. Verify that completed steps remain trustworthy.
4. Resume from the first failed or untrustworthy step.
5. If parameters changed, prose was manually edited, or the outline is newer than prose, ask whether to rerun earlier steps.

### 9.5 Resume Branches Requiring Decisions

| Scenario | Handling |
|---|---|
| Prose exists but user requests rewrite | Ask overwrite / save separately / cancel |
| Outline newer than prose | Ask reuse prose / redraft |
| Review refers to old prose | Automatically rerun review |
| Chapter already accepted and write is repeated | Ask rewrite / inspect status only |
| Backup failed after successful commit | Retry backup automatically, without rewriting prose |

### 9.6 Delivery Stages

Start with `/webnovel-write`, the longest workflow with the most failure points.

Later extend to:

- `/webnovel-plan`: Resume by batch; redo failed batches without overwriting a volume.
- `/webnovel-init`: Do not force resume of pre-confirmation conversation; generation can fill missing files.
- `/webnovel-review`: Skip reviewed chapters whose prose has not changed.

---

## 10. Interactive Decisions

### 10.1 Goal

Give bounded options when user action is necessary rather than asking authors to interpret errors and edit files themselves.

### 10.2 Decision Format

```text
Your decision is needed: Shen Zhao's magical item conflicts with the outline.

Outline: Qingfeng Sword
Prose: Purple-Gold Gourd

Choose:
1. Follow the outline: revise affected prose back to Qingfeng Sword
2. Adopt the new setting: keep Purple-Gold Gourd and record the setting change
3. Handle manually: pause, then continue after your edits
```

### 10.3 Standard Decision Types

| Type | Options |
|---|---|
| Setting conflict | Keep established setting / adopt new setting / manual |
| Timeline conflict | Revise prose to timeline / adjust timeline / manual |
| Character OOC | Revise to profile / update rationale for character change / manual |
| Low-confidence disambiguation | A / B / defer persistence |
| Rejected commit | Fix and resubmit / accept risk without committing / manual |
| Abnormal write scope | Cancel write / retain safe files only / inspect details |

### 10.4 AskUserQuestion

Prefer AskUserQuestion for key decisions in Claude Code.

Keep choices short and explain impact:

- Recommended option first
- State what each option changes
- No fixed “Other” option; users can freely add details

### 10.5 No-Automatic-Decision Boundaries

The system must not independently:

- Change the protagonist's long-term ability path
- Change the central antagonist's identity
- Change the volume-climax outcome
- Incorporate reference-work content into new-book canon
- Overwrite manually edited prose
- Treat a rejected commit as accepted and proceed

---

## 11. Technical Traceability and Logs

### 11.1 Goal

Keep author reports clean while preserving complete diagnostic evidence.

### 11.2 Locations

Recommended:

```text
.webnovel/logs/run_last.log
.webnovel/logs/runs/YYYYMMDD-HHMMSS-{command}.log
```

### 11.3 Contents

Include:

- Commands and arguments
- Resolved project root
- Start/end times for each milestone
- Subagent run summaries
- Runtime JSON-output summaries
- Exception tracebacks
- Final `user-report --format json`

Exclude:

- API keys
- Raw `.env`
- Unconfirmed core-setting drafts for a new book, unless already supplied as input to this run

### 11.4 Final-Report Presentation

Show log paths only when:

- Work is not completed
- User action is needed and the issue is hard to describe
- The user chooses `--verbose`

Example:

```text
Technical details saved to .webnovel/logs/run_last.log. Attach it when reporting the failure.
```

---

## 12. Phase 0: Baseline Audit

### 12.1 Goal

First establish the boundaries of current reports, gates, and agent outputs so that format drift can be traced after the changes.

### 12.2 Tasks

- [ ] Record the current final-output requirements of the four main Skills.
- [ ] Record the four agents' current output formats and write responsibilities.
- [ ] Record the JSON fields of `project-status`, `doctor`, `write-gate`, `review-pipeline`, and `chapter-commit`.
- [ ] Record existing error codes, repair messages, gate-failure signatures, and projection states as initial source material for `author_error_catalog.json`.
- [ ] Record the `review-pipeline` fields available to the author view: overall score, blocking count, dimension-level issues, recommendations, and report paths.
- [ ] Record engineering terms already present in documentation and Skills, and deduplicate them against the glossary in §5.
- [ ] Identify which existing tests assert wording and which can become behavior-level assertions.

### 12.3 Acceptance

- Reusable structured data sources are listed.
- It is clear which issues can only be recorded by prompts and which runtime helpers can read.
- Initial entries in `author_glossary.json` and `author_error_catalog.json` have clear sources rather than being guessed during implementation.

---

## 13. Phase 1: Skill Final-Report Contract

### 13.1 Goal

Use minimal changes to make the four main workflows follow a unified final-response format.

### 13.2 `/webnovel-init`

Must report:

- Project directory.
- `.webnovel/state.json`.
- `设定集/世界观.md`, `设定集/力量体系.md`, `设定集/主角卡.md`, `设定集/反派设计.md`.
- `大纲/总纲.md`.
- `.webnovel/idea_bank.json`.
- `.story-system/MASTER_SETTING.json`.
- Whether reference-work deconstruction was used.
- Any material not written to canon pending user confirmation.
- Whether missing information affects subsequent planning.

Tasks:

- [ ] Add a "Final Report Requirements" section to `webnovel-init/SKILL.md`.
- [ ] Map success criteria to the three-part report.
- [ ] Require failed reference deconstruction, insufficient input, or below-threshold quality to appear under "Confirmation Recommended / Action Required."

### 13.3 `/webnovel-plan`

Must report:

- `大纲/第{volume_id}卷-节拍表.md`.
- `大纲/第{volume_id}卷-时间线.md`.
- `大纲/第{volume_id}卷-详细大纲.md`.
- Which setting files received new settings.
- `大纲/第{volume_id}卷-总纲写回.json`.
- Whether `master-outline-sync` completed.
- Whether `update-state` completed.
- Whether Story System contracts were refreshed.
- Whether placeholder, timeline, and beat-continuity checks passed.

Tasks:

- [ ] Add a "Final Report Requirements" section to `webnovel-plan/SKILL.md`.
- [ ] Require backward timeline jumps, BLOCKERs, and remaining placeholders to be reported.
- [ ] When only failed batches are rerun, explain what was handled automatically.

### 13.4 `/webnovel-write`

Must report:

- Chapter-text path.
- Writing-check report path.
- `.webnovel/tmp/review_results.json`.
- `.webnovel/tmp/fulfillment_result.json`.
- `.webnovel/tmp/disambiguation_result.json`.
- `.webnovel/tmp/extraction_result.json`.
- `.story-system/commits/chapter_{NNN}.commit.json`.
- Update status for state / index / summary / memory / vector.
- Backup status.
- Whether writing can proceed to the next chapter.

Tasks:

- [ ] Add a "Final Report Requirements" section to `webnovel-write/SKILL.md`.
- [ ] Require disclosure of steps skipped by `--fast` and `--minimal`.
- [ ] Prohibit a "Completed" final status when `chapter-commit rejected` occurs.
- [ ] When a projection retry occurs, report the automatic handling and its outcome.

### 13.5 `/webnovel-review`

Must report:

- Review-report file.
- `review_metrics.json`.
- Whether `review_metrics` was persisted to the database.
- Number of blocking issues.
- User-adjudication status.
- If there are no blockers, explicitly state that writing may continue.

Tasks:

- [ ] Add a "Final Report Requirements" section to `webnovel-review/SKILL.md`.
- [ ] Require blocking issues to appear under "Action Required" or "Confirmation Recommended."
- [ ] When only the report is saved and handling is deferred, use "Your Action Needed" or "Partially Completed" as the final status.

---

## 14. Phase 2: Subagent Return Protocol

### 14.1 Goal

Allow the main workflow to reliably aggregate each subagent's completion status, problems, automatic handling, and elapsed time.

### 14.2 Unified Protocol

The main workflow records a `SubagentRun` for every subagent invocation:

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

Field definitions:

| Field | Meaning |
|---|---|
| `name` | Agent name |
| `user_label` | Author-friendly name |
| `status` | Completion status |
| `problems` | Problems encountered |
| `auto_handled` | Actions handled automatically |
| `needs_user_action` | Whether user action is required |
| `duration_ms` | Elapsed time |
| `outputs` | Key artifacts produced or returned |

### 14.3 Tasks

- [ ] `context-agent`: insufficient context, legacy fallback, and missing foreshadowing data must be recordable by the main workflow.
- [ ] `reviewer`: empty chapter text, state-read failures, and skipped dimensions must appear in the summary or problem fields.
- [ ] `data-agent`: write status for all three artifacts, prolonged lack of progress, and pending disambiguation must be aggregatable.
- [ ] `deconstruction-agent`: insufficient input, below-threshold quality, and fallback to quick mode must be aggregatable.
- [ ] After invoking an agent, the main Skill must record a `SubagentRun` for the final report.

### 14.4 Acceptance

- The chapter-writing final report lists the status of the three assistants: pre-writing preparation, writing checks, and saving chapter story facts.
- If any agent is skipped, fails, or produces incomplete output, the final report does not claim complete success.

---

## 15. Phase 3: Exception Classification and Elapsed-Time Presentation

### 15.1 Exception Classification

All issues fall into three categories:

| Category | Definition | Example |
|---|---|---|
| Automatically Handled | The system reran a step, used a fallback, or completed an allowlisted targeted action; no user action needed | Successful projection retry; RAG fallback without affecting the result |
| Confirmation Recommended | The result is usable, but the user should review it | Slightly low reference-deconstruction quality; an ambiguous character name was adopted |
| Action Required | Leaving it unresolved affects further writing, submission, or consistency | Blocking issue, missing chapter text, commit rejected, projection failed |

### 15.2 Error Catalog

`author_error_catalog.json` maps errors to author actions and is shared by `error_catalog.py` and `user_report.py`. It does not change error detection; it translates known errors into:

- A plain-language cause.
- Impact on the current chapter / subsequent writing.
- A next action or copyable command.
- Severity and exception category.
- Whether automatic handling is permitted.

Unknown errors must fall back honestly:

```text
This step encountered a problem the system has not cataloged yet. It will not be treated as completed. Please run /webnovel-doctor first, or include the log when reporting the issue.
```

The error catalog only translates and classifies. The automatic-handling allowlist must be registered explicitly and separately, and existing automatic-handling scope must not expand before Phase 3.

### 15.3 Elapsed-Time Presentation

By default, show only:

- Elapsed time.
- Whether the current step is still progressing.
- Possible reasons for prolonged lack of progress.
- Whether completed results are affected.

Do not set fixed duration thresholds. APIs, models, networks, chapter lengths, and review complexity vary too much; fixed thresholds would mislead authors.

Progress messages may use relative wording:

```text
"Save this chapter's story facts" has been running for a while. The interface may be responding slowly, or this chapter may introduce many new facts. The generated chapter text is currently unaffected.
```

### 15.4 Tasks

- [ ] Add exception classification to Skill final-report requirements.
- [ ] Add `author_error_catalog.json` and `error_catalog.py`.
- [ ] Create initial entries for `mainline_ready=false`, `write-gate failed`, `chapter-commit rejected`, projection failed / pending, RAG fallback, incomplete artifact schemas, and similar cases.
- [ ] Unmatched error codes fall back to an honest error message + `/webnovel-doctor` + log path; never crash or invent a translation.
- [ ] Preserve and standardize the requirement in `data-agent.md` to explain causes and impact when progress stalls for a long time.
- [ ] Implement elapsed-time formatting in the runtime helper.
- [ ] Do not collect token statistics or show tokens in final reports.

### 15.5 Acceptance

- Final reports do not mix warnings, blockers, and automatically handled issues.
- Known errors map to actionable author steps; unknown errors fall back honestly.
- A prolonged stalled step includes a possible cause and an assessment of impact.
- Tokens are not a user-visible report item.

---

## 16. Phase 4: Runtime Report Helper

### 16.1 Goal

Add a unified helper that renders structured run results as author-friendly reports.

This phase also implements the specification's Review Author View: add an author view at the top of the existing review report without changing reviewer schemas, scoring, or blocking decisions.

Author-view format:

```text
Chapter verdict: ✅ Ready to continue / ⚠️ Revision recommended / ⛔ Revise before continuing

The 1-3 most worthwhile actions:
- ...
```

Generation rules:

- `blocking_count > 0`: verdict is "Revise before continuing"; list at most three blocking or high-risk issues.
- No blockers but substantial recommendations: verdict is "Revision recommended"; list at most three recommendations with the greatest benefit to plot, characters, or pacing.
- No blockers and only minor recommendations: verdict is "Ready to continue"; retain only one explanatory sentence.
- Technical metrics, schemas, and raw reviewer dimensions remain in the detailed report below, not the top-level verdict.

### 16.2 CLI Shape

Add:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" user-report \
  --stage write \
  --chapter {chapter_num} \
  --format text
```

Support:

```bash
--stage init|plan|write|review
--chapter N
--volume N
--format text|json
```

### 16.3 Data Model

`user_report.py` uses internally:

```json
{
  "schema_version": "webnovel-user-report/v1",
  "stage": "write",
  "overall_status": "completed | partial | needs_user | failed",
  "project_root": "",
  "chapter": 0,
  "volume": 0,
  "files": [],
  "issues": {
    "auto_handled": [],
    "needs_confirmation": [],
    "must_handle": []
  },
  "timing": {
    "total_ms": 0,
    "steps": []
  },
  "next_actions": []
}
```

### 16.4 Data Sources

| Stage | Data sources |
|---|---|
| init | File existence, `project-status`, `.story-system/MASTER_SETTING.json` |
| plan | Planning artifacts, `placeholder-scan`, `master-outline-sync` output, Story System contract files |
| write | Three `write-gate` stages, review artifacts, commit payload, projection log, backup output, subagent runs |
| review | `review_results.json`, `review_metrics.json`, report files, `review_metrics` table |

### 16.5 Tasks

- [ ] Add `review_author_view.py` to render one verdict + at most three actionable recommendations from the existing review payload.
- [ ] Insert the author view during report rendering in `review_pipeline.py`, without changing reviewer schemas.
- [ ] Add `user_report.py`.
- [ ] Add the `webnovel.py user-report` subcommand.
- [ ] Implement the `write` report first: it is the most complex and provides the most value.
- [ ] Implement the `review` report alongside it, reusing the review author view.
- [ ] Implement `init` and `plan` last.
- [ ] Add helper unit tests that do not depend on a real LLM.

### 16.6 Acceptance

- The review report begins with an author-readable verdict and at most three actionable recommendations.
- The author view preserves key facts such as blocking counts and never labels required fixes "Ready to continue."
- `user-report --stage write --format json` emits a stable schema.
- `user-report --stage write --format text` emits a three-part Chinese report.
- Projection failures, rejected commits, missing artifacts, and similar cases are classified correctly.
- Helper output contains no token statistics.

---

## 17. Phase 5: Checkpoint Resumption and Interaction Validation

### 17.1 Prompt Integrity

Add or adjust assertions:

- [ ] All four main Skills include progress-message requirements.
- [ ] All four include a low-interruption confirmation policy.
- [ ] `/webnovel-write` has no more than six author-understandable progress stages.
- [ ] Progress messages use author-friendly stage names, not raw engineering commands as the main message.
- [ ] When stalled, explain the blockage, completed work, and recovery advice.
- [ ] `/webnovel-write` explains that repeating the same command can resume from a trusted checkpoint.
- [ ] Questions requiring user adjudication preferentially offer a limited set of choices.
- [ ] Technical details go to `.webnovel/logs/run_last.log` by default rather than cluttering the author report.

### 17.2 Runtime Tests

Add:

- [ ] `test_run_ledger_records_write_step_status`
- [ ] `test_write_resume_skips_completed_draft_and_review`
- [ ] `test_write_resume_rechecks_review_when_chapter_file_changed`
- [ ] `test_write_resume_retries_backup_after_commit_done`
- [ ] `test_run_log_redacts_env_values`
- [ ] `test_user_report_includes_log_path_only_on_failure`

If the first release does not implement a run ledger, retain these as Phase 5 contracts awaiting implementation rather than adding them to the default required test suite.

### 17.3 Behavior Evaluation

Add:

- [ ] During `/webnovel-write`, explain whether the current stage is pre-writing checks, drafting, review, saving facts, or commit/backup.
- [ ] RAG fallback does not interrupt the user but appears in the final report.
- [ ] Automatic projection retries do not ask the user, but progress messages explain the rerun.
- [ ] Ask the user about a blocking issue only when targeted handling cannot resolve it.
- [ ] If data-agent output is incomplete, explain that chapter text and review reports are preserved; do not commit incomplete facts.
- [ ] Repeating `/webnovel-write` for the same chapter does not rewrite trusted text; automatically resume from the failed step.
- [ ] Setting-conflict blockers use limited-choice adjudication.
- [ ] Unrecoverable-failure reports provide `.webnovel/logs/run_last.log`.

### 17.4 Acceptance

- Authors can tell what is happening during a long workflow.
- Noncritical issues do not frequently interrupt them.
- The system does not bypass crucial creative decisions.
- Failures show a clear recovery point.
- After a transient failure, repeating the same main command resumes from the latest trusted step.
- Engineering logs support diagnosis without bothering authors by default.

---

## 18. Phase 6: Testing and Behavioral Validation

### 18.1 Prompt Integrity

Add or adjust assertions:

- [ ] All four main Skills include final-report requirements.
- [ ] All four require an overall status + three-part report.
- [ ] `webnovel-write` must report chapter text, review, data artifacts, commit, projection, and backup.
- [ ] `webnovel-review` must report the review report, metrics, and blocking adjudication.
- [ ] Agent protocols allow aggregation of status / problems / auto_handled / needs_user_action / duration.
- [ ] Do not require exact wording; check that the contract exists.

### 18.2 Runtime Tests

Add:

- [ ] `test_user_report.py::test_render_write_report_success`
- [ ] `test_user_report.py::test_render_write_report_commit_rejected`
- [ ] `test_user_report.py::test_render_write_report_projection_failed`
- [ ] `test_user_report.py::test_render_review_report_blocking`
- [ ] Cover `user-report` registration in `test_webnovel_unified_cli.py`.

### 18.3 Behavior Evaluation

Add to fast eval:

- [ ] `/webnovel-write --minimal` final reports must disclose skipped writing checks.
- [ ] Missing data-agent output prevents a "Completed" final status.
- [ ] Successful projection retries appear under "Automatically Handled."
- [ ] Reviewer blockers appear under "Action Required."

### 18.4 Validation Commands

```bash
python -m pytest webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py -q --no-cov
python -m pytest webnovel-writer/scripts/data_modules/tests/test_user_report.py -q --no-cov
python -m pytest webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py -q --no-cov
python -X utf8 webnovel-writer/scripts/run_behavior_evals.py --format json
```

---

## 19. Phase 7: Documentation and README

### 19.1 Goal

Help users understand the final report after each command.

### 19.2 Scope

- `README.md`
- `docs/guides/commands.md`
- `docs/operations/operations.md`

### 19.3 Tasks

- [ ] Add "How to Read the Final Report" to the README chapter-writing workflow.
- [ ] Explain the progress messages users will see in the README or commands guide.
- [ ] Explain in the commands guide that repeating a main command first attempts checkpoint resumption.
- [ ] Explain the four overall statuses in the commands guide.
- [ ] Explain in operations documentation which situations prompt users and which are handled automatically.
- [ ] Explain the purpose of `.webnovel/logs/run_last.log` and sensitive-information rules in operations documentation.
- [ ] Explain exception categories and common handling in operations documentation.
- [ ] Do not document token statistics.

### 19.4 Acceptance

- Users can distinguish Completed / Partially Completed / Your Action Needed / Not Completed from the documentation.
- Users know which problems can be ignored and which require action.
- Users know they can repeat the original command after transient failures.
- Users know they may attach logs when reporting failures but do not normally need to read them.

---

## 20. Recommended Implementation Order

1. Phase 0: Baseline audit.
2. Phase 1A: Establish `author_glossary.json` so the four main Skills share terminology.
3. Phase 1B: Update final-report requirements for the four main Skills and add task-oriented next-action guidance.
4. Phase 3A: Establish `author_error_catalog.json` / `error_catalog.py`; standardize exception categories and unknown-error fallbacks.
5. Phase 4A: Implement `review_author_view.py` with one verdict + at most three recommendations at the top of review reports.
6. Phase 2: Add subagent return protocols so the main workflow has material to aggregate.
7. Phase 4B: Implement `user_report.py`, integrating `/webnovel-write` and `/webnovel-review` first.
8. Phase 5A: Add progress messages, pre-run expectations, confirmation policies, and recovery points.
9. Phase 5B: Implement the `/webnovel-write` run ledger, logs, and checkpoint resumption.
10. Phase 5C: Consolidate blocking issues into interactive adjudication.
11. Phase 6: Add prompt integrity, unit tests, and behavior evaluation.
12. Phase 7: Update README / docs.

Rationale:

- The glossary and error catalog are the Author Layer's single source of truth. Implementing them first prevents divergent translations across wording and helpers.
- Skill contracts and next-action guidance immediately improve visible output with the lowest risk.
- The review author view offers high value through a short implementation path, independent of the main writing chain, making it suitable for early delivery.
- Runtime helpers solve long-term consistency, but the first version remains read-only rendering and does not alter the writing chain.
- The run ledger, automatic-handling allowlist, and checkpoint resumption are riskier; implement them later, initially covering only `/webnovel-write`.

---

## 21. Risks and Controls

| Risk | Impact | Control |
|---|---|---|
| Prompt-only changes cause format drift | Final reports still differ across Skills | Add a runtime helper in Phase 4 |
| Reports too long | Authors will not read them | Default to three parts; expand technical details only for required action |
| Reports too short | Problems are hidden | Explicitly define situations that cannot be silent |
| Too much engineering terminology | Authors cannot understand | Use the terminology translation table |
| Helper enters the main workflow too early | New failure points | Begin with read-only rendering; do not change the writing chain |
| Inaccurate timing | Misleads users | Start with coarse step-level durations, not precise performance diagnosis |
| Subagents cannot directly return protocol fields | Difficult aggregation | Wrap calls in `SubagentRun`; do not force changes to agents' original artifact formats |
| Removing token statistics reduces cost visibility | One fewer engineering metric | Retain tokens for internal observation, not author final reports |
| Excessive progress messages | Interrupts immersion | Show at most 3-6 progress milestones per main workflow |
| Failing to ask when necessary | System decides creative direction or factual state without authorization | List mandatory questions in the low-interruption policy |
| Asking unnecessarily | Minor technical issues interrupt authors | Handle automatic categories without asking; disclose them in final reports |
| Reporting only an error when stalled | Authors do not know whether work was lost | Stalled-step feedback includes completed work and recovery point |
| Incorrectly trusting checkpoint artifacts | Continue committing outdated text/reviews | Check file modification time, chapter number, mode parameters, and gate status before resuming |
| Automatic resumption overwrites manual edits | User writing is overwritten | Ask when new edits to text or chapter outlines are detected |
| Too many adjudication options | Users remain confused | Offer only 2-3 clear choices each time |
| Logs leak sensitive information | API keys or private configuration exposed | Filter `.env`, API keys, and secret fields before writing logs |

---

## 22. Out of Scope

This plan does not include:

- Automatically fixing / rereviewing every blocking review issue.
- New multi-round reviewer loops.
- Rewriting the chapter-commit or projection main chain.
- A major Dashboard frontend redesign.
- Token-cost statistics.
- Automatically creating PRs / git commits.
- Refactoring and shortening every Skill's wording.
- A real-time progress-bar UI.
- Dashboard workflow-progress visualization.
- A complete transactional workflow engine.
- Full checkpoint resumption across every Skill; the first version prioritizes `/webnovel-write`.

Plan these separately.

---

## 23. Minimum Viable Version

For quick benefits, implement this minimum version first:

1. Establish `author_glossary.json` as the single source of truth for terminology translations.
2. Establish `author_error_catalog.json`, covering at least `mainline_ready=false`, `write-gate failed`, `chapter-commit rejected`, projection failed / pending, RAG fallback, and incomplete artifact schemas. Unknown errors fall back honestly to `/webnovel-doctor`.
3. Add final-report requirements to all four main Skills: overall status + three-part report + next-action guidance.
4. Add aggregatable status / problems / automatic handling / timing protocols to the four agents.
5. Add the review author view at the top of reports in `review_pipeline.py`: one verdict + at most three actionable recommendations.
6. Require the `webnovel-write` final report to cover:
   - Chapter text.
   - Review report.
   - Data artifacts.
   - Commit status.
   - Projection status.
   - Backup status.
   - Whether the next chapter may proceed.
7. Defer the complete `user_report.py`, but explicitly make the helper a next-phase objective.
8. Add six author-friendly progress milestones and stalled-step recovery guidance to `/webnovel-write`.
9. Explain in `/webnovel-write` that repeating the same command attempts to continue from the failed step; implement the actual run ledger in the next phase.
10. Include task-oriented explanations and copyable commands in the final report's next-action guidance.

After the minimum version, authors should reliably know:

- Whether files were generated.
- Whether writing can continue after this chapter.
- Which problems the system already handled.
- Which problems require their confirmation.
- Which workflow step is currently running.
- Where to resume after failure.
- Which command they can run next.

---

## 24. Final Result

After implementation, authors see a consistent delivery report rather than a string of commands and JSON:

```text
Overall status: Completed. You may continue with Chapter 13.

1. Generated Files and Completion Status
- 正文/第0012章-风雪夜归人.md: Generated and passed writing checks.
- 审查报告/第12章审查报告.md: Generated, with no blocking issues.
- This chapter's story facts: Saved; state, summary, long-term memory, and retrieval library updated.
- Backup: Completed.

2. Issues and Unusually Long Steps
- Automatically handled: Retrieval-library updates were slow; the system waited for completion. Results are unaffected.
- Confirmation recommended: The new character "Shen Zhao" has been added to the story records. Please check whether you are happy with the name.
- Action required: None.

3. Suggested Next Action
- Continue with:
  /webnovel-write 13
```

The value is not merely a nicer-looking report. It lets authors confidently judge, every time, whether this run is reliable and whether they can proceed.
