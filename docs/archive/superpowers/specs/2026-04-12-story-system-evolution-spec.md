# Webnovel Writer Story System Incremental Evolution Spec

> **Date**: 2026-04-12
> **Status**: Draft v1
> **Purpose**: A superpowers architecture-convergence spec grounded in the actual system

---

## 1. Purpose and Scope

### 1.1 The Problem This Spec Addresses

[`current-system-diagnosis.md`](../../architecture/current-system-diagnosis.md) identifies structural problems rather than insufficient model capability:

1. Fragmented sources of truth
2. No unified story contracts
3. No unified chapter-commit mainline
4. Structural gaps in context assembly and data writeback

The diagnosis explains what is wrong, not how to evolve safely from the current system.

This spec supplies that bridge:

- Do not rewrite existing project history.
- Do not pretend the current system has nothing useful.
- Do not treat an ideal blueprint as an implementation plan.
- Define **a gradual route from current foundations to a Story Contract mainline**.

### 1.2 Related Documents

- [`current-system-diagnosis.md`](../../architecture/current-system-diagnosis.md): diagnoses structural problems.
- [`2026-04-12-story-system-pro-max-retrofit-spec.md`](./2026-04-12-story-system-pro-max-retrofit-spec.md): conservative retrofit approach.
- [`2026-04-12-webnovel-story-intelligence-system-spec.md`](./2026-04-12-webnovel-story-intelligence-system-spec.md): ideal target architecture.

This spec bridges all three through current baseline → staged convergence → final contract system.

### 1.2.1 Boundaries Between Diagnosis, Retrofit, Ideal, and Evolution

#### Current-System Diagnosis

Answers:
- Where are the structural gaps?
- Which problems are real?
- Which partially built foundations already exist?

It does not define an implementation path.

#### Retrofit Spec

Explains how to add a minimally viable `story_system` while disturbing the existing mainline as little as possible.

Focus:
- Phase 1
- Conservative delivery
- Minimal intrusion

#### Ideal Spec

Explains the best final architecture without imposing a minimal-change constraint.

Focus:
- Phase 2 onward
- Final target
- Complete contract system

#### This Spec

Explains:
- How to converge partially built hubs into a contract mainline from the actual baseline.
- Which old paths integrate first, become secondary later, and are replaced last.

In short:
- Diagnosis defines the problems.
- Retrofit defines conservative additions.
- Ideal architecture defines the destination.
- **This spec defines the incremental journey.**

### 1.3 One-Sentence Conclusion

The system needs to converge several partially built hubs into one mainline, not be rebuilt from scratch.

The best response is not another script, prompt patch, or `context_manager` budget rule. Establish:

- **A unified story-contract layer**
- **A unified chapter-commit mainline**
- **A unified override ledger**
- **A unified event mainline**

Then make `state / index / summary / memory / RAG` projections of accepted contract-based commits.

---

## 2. Current Baseline

### 2.1 Reusable Partial Hubs

The diagnosis identifies existing foundations:

1. `context_manager + context_ranker`
   - Context aggregation, budgets, and priority ranking.
2. `genre_aliases.py + genre_profile_builder.py + genre-profiles.md`
   - Genre normalization, hints, and profiles.
3. `reference_search.py + references/csv`
   - Entry retrieval and lightweight scoring.
4. `state_manager`
   - Structured state writeback and dual synchronization of `state.json + SQLite`.
5. `index.db`
   - Structured entities, relationships, events, and indexes.
6. `memory writer / orchestrator / summaries`
   - Long-term fact retention and chapter summaries.
7. `override_contracts`
   - An initial mechanism for recording deviations.

### 2.2 Fundamental Missing Capabilities

Four mainline capabilities are missing, not merely an individual module:

1. **Unified story truth**
   - No `MASTER / VOLUME / CHAPTER` contract family as a single source of truth.
2. **Unified chapter commits**
   - Post-writing facts are scattered across writers rather than one commit distributed through projections.
3. **Unified setting-evolution ledger**
   - Only an initial reader-retention-debt override mechanism exists, not a global setting ledger.
4. **Unified events**
   - Many delta-event traces exist, but no canonical event log.

### 2.3 Evolution Implication

Do not add a large new module while ignoring old paths. Follow this order:

1. Establish unified contracts.
2. Make runtime consume them.
3. Make chapter commits the mainline.
4. Demote old paths to projections and fallback.

Reversing the order creates another competing hub instead of convergence.

---

## 3. Goals and Non-Goals

### 3.1 Eight Goals

1. Unified story contracts built on the existing system.
2. Contract-first context assembly.
3. Strong constraints before writing, not merely afterward.
4. Outline-fulfillment validation and review contracts.
5. Unified chapter commits.
6. Unified override ledger.
7. Canonical event log.
8. Reposition existing modules as foundations and projections.

### 3.2 Non-Goals

This spec does not require:

1. Replacing every old path at once.
2. Immediately retiring `context_manager`, `genre_*`, or `reference_search.py`.
3. Automatic Markdown-to-CSV knowledge migration.
4. A separate test for every CSV entry.
5. A fully event-driven architecture in Phase 1.

### 3.3 Hard Constraints

Throughout evolution:

1. AI-flavor, anti-AI, and polishing substitution rules stay in Markdown, not CSV.
2. CSV knowledge migration is manually organized and entered only.
3. Do not create new competing sources of truth.
4. Every implementation plan must explicitly include **documentation updates**.

---

## 4. Design Principles

### 4.1 Converge, Do Not Compete

The new system must consolidate old hubs, not stand alongside them.

Anti-patterns:
- Add `story_system` while `context_manager` independently generates another genre judgment.
- Add contracts while treating `genre-profiles.md` as an equal authority.
- Add chapter commits while allowing writeback to bypass them.

### 4.2 Contracts First, Runtime Facts Second

Runtime input has two layers:

1. **Contracts**: Genre/tone, reader-dealbreaker boundaries, system limits, volume/chapter goals.
2. **Facts**: State, recent summaries, entities, reader signals.

Contracts describe how the story should be written; facts describe what has happened.

### 4.3 Commit First, Project Afterward

After a chapter:

1. Form a structured commit.
2. Validate contract and outline fulfillment.
3. Only after acceptance, project into `state / index / summary / memory`.

Do not scatter writes first and reconcile them separately afterward.

### 4.4 Explicit Overrides, No Silent Drift

Every setting change must answer:

1. What changed?
2. Which layer was the basis?
3. Why?
4. Does it affect a higher-level contract?

Without these answers, it is not valid setting evolution.

### 4.5 Mainline Before Precision

The primary gap is orchestration, not accuracy. Build:

1. Contract mainline
2. Commit mainline
3. Event mainline
4. Better retrieval, reasoning, and multi-tag fusion precision

---

## 5. Mapping Diagnosis to Evolution Workstreams

The ten diagnosed problems form five workstreams.

### 5.1 Converge Sources of Truth

Problems:
- 1. Multiple authorities
- 2. Missing Override Ledger

Actions:
- Make contracts the only story authority.
- Expand `override_contracts` from reader-retention debt to setting evolution.

### 5.2 Contract-Based Context

Problems:
- 3. Context truncation black hole
- 4. Late knowledge binding and disconnected generalization

Actions:
- Make `context_manager` contract-first.
- Pre-aggregate general knowledge into book-specific contracts instead of ad hoc searches while writing.

### 5.3 Pre-Writing Validation

Problems:
- 5. Post-hoc inspection only
- 6. No outline-fulfillment checks

Actions:
- Create review contracts.
- Define pre-writing prohibitions, disambiguation domains, and post-writing fulfillment diffs.

### 5.4 Chapter Commits

Problems:
- 7. Fragmented cross-storage transactions
- 8. Contamination from late disambiguation
- 9. Disambiguation warnings propagating forward

Actions:
- Create one chapter-commit object.
- Move disambiguation and fact extraction into commit validation rather than final writeback fallback.

### 5.5 Event Mainline

Problem:
- 10. Event traces without a mainline

Actions:
- Define a canonical event log.
- Make events, rather than overwritten final state, trigger evolution.

---

## 6. Target Architecture

### 6.1 Six Layers

1. `Knowledge Layer`
2. `Reasoning Layer`
3. `Contract Layer`
4. `Runtime Assembly Layer`
5. `Chapter Commit Layer`
6. `Projection Layer`

### 6.2 Flow

```text
User intent / book genre requirements
        ↓
Reasoning Layer
        ↓
Story Contract Generator
        ↓
MASTER / VOLUME / CHAPTER / REVIEW / ANTI_PATTERNS
        ↓
context_manager(contract-first)
        ↓
Planning / writing / review
        ↓
CHAPTER_COMMIT
        ↓
Projection Writers
        ↓
state / index / summaries / memory / rag
```

### 6.3 Architectural Conclusion

Replace the conceptual mainline:
- `reference_search -> prompt -> reviewer -> data agent -> state`

With:
- `knowledge -> reasoning -> contract -> runtime pack -> chapter commit -> projections`

---

## 7. Authority and Priority

### 7.1 Story Authority

The contract family is the only story source of truth:

1. `MASTER_SETTING.json`
2. `VOLUME_BRIEF.json`
3. `CHAPTER_BRIEF.json`
4. `REVIEW_CONTRACT.json`
5. `anti_patterns.json`

Within it:
- `MASTER / VOLUME / CHAPTER` are the hierarchical authorities.
- `anti_patterns.json` is a derived view and cannot become upstream truth.
- `REVIEW_CONTRACT.json` is a derived review contract.

### 7.2 Runtime Priority

Fixed context order:

1. `chapter contract`
2. `volume contract`
3. `master contract`
4. `题材与调性推理.csv`
5. `genre-profiles.md`
6. `templates/genres/*.md`
7. Other local references

Once contracts exist, `context_manager`, `webnovel-plan`, `webnovel-write`, and `webnovel-review` must not produce conflicting global system judgments.

### 7.3 Post-Writing Authority

After completion:

1. `CHAPTER_COMMIT`
2. Projection to `state`
3. Projection to `index`
4. Projection to `summaries`
5. Projection to `memory`

These stores are no longer parallel fact authorities; they derive from `CHAPTER_COMMIT`.

---

## 8. Contract Design

### 8.1 Family

1. `MASTER_SETTING`
2. `VOLUME_BRIEF`
3. `CHAPTER_BRIEF`
4. `REVIEW_CONTRACT`
5. `ANTI_PATTERNS`
6. `CHAPTER_COMMIT`

The first five govern before writing; `CHAPTER_COMMIT` governs afterward. Without it, fragmented writeback, missing fulfillment, and broken event chains remain unresolved.

### 8.2 Responsibilities

#### MASTER_SETTING

Stable book-wide rules:
- Genre and tone
- World rules
- Core characters
- Special-advantage limits
- Global reader dealbreakers
- Global override policy

#### VOLUME_BRIEF

Volume-level rules:
- Conflict axis
- Payoff objectives
- Stage-specific relationships
- Pacing waveform
- Additional boundaries

#### CHAPTER_BRIEF

Chapter execution:
- Goal
- Scene strategy
- Hook
- Must-cover nodes
- Prohibited developments
- Local overrides

#### REVIEW_CONTRACT

Required checks:
- Blocking rules
- Genre-specific risks
- Outline fulfillment
- Disambiguation
- High-risk facts

#### ANTI_PATTERNS

Flatten all visible levels' boundaries into a runtime view.

#### CHAPTER_COMMIT

Final chapter result:
- Contracts used
- Facts established
- Events produced
- Outline/mandatory-node fulfillment
- Disambiguation result
- Review result
- Completed projections

### 8.3 Field Types

Keep:
1. `locked`
2. `append_only`
3. `override_allowed`

And `lock_policy`:
1. `system_locked`
2. `user_locked`
3. `story_locked`

### 8.4 Overrides

Priority:
1. `chapter`
2. `volume`
3. `master`

No silent overrides. Record:
- `field`
- `base_value`
- `override_value`
- `source_level`
- `reason`
- `reason_tag`
- `approved_by`

### 8.5 Override Ledger

Retain `override_contracts` as the foundation of a unified ledger.

Responsibilities:
1. Soft deviations in reader-retention debt.
2. Controlled chapter/volume overrides of higher contracts.
3. Proposals requiring `amend-master / amend-volume`.

Record categories:
1. `soft_deviation`
2. `contract_override`
3. `amend_proposal`

---

## 9. Chapter-Commit Mainline

### 9.1 Why It Is Necessary

The problem is not failure to save, but asynchronous scattered writes after generation. This creates inconsistent state, late-disambiguation contamination, lost fulfillment, and broken event chains.

Instead, form one commit and distribute it through projectors.

### 9.2 Minimal CHAPTER_COMMIT

Include:
- `meta`
- `contract_refs`
- `outline_snapshot`
- `review_result`
- `fulfillment_result`
- `disambiguation_result`
- `accepted_events`
- `state_deltas`
- `entity_deltas`
- `projection_status`

### 9.3 Commit Flow

1. Read `CHAPTER_BRIEF`.
2. Complete writing.
3. Generate `REVIEW_CONTRACT`.
4. Complete review.
5. Draft `CHAPTER_COMMIT`.
6. Validate fulfillment, disambiguation, and blocking rules.
7. Mark the commit accepted only after success.
8. Project to stores.

### 9.4 Projection Writers

At minimum:
1. `state_projection_writer`
2. `index_projection_writer`
3. `summary_projection_writer`
4. `memory_projection_writer`

Optional later:
5. `rag_projection_writer`

### 9.5 Failure Semantics

If `CHAPTER_COMMIT` fails validation, do not:
1. Partially write `state`.
2. Partially write `index`.
3. Save a summary first and repair state later.
4. Let the next chapter read unconfirmed facts.

Generated does not mean committed. Only `commit accepted` joins the factual mainline.

---

## 10. Canonical Event Log

### 10.1 Current Gap

Existing local event structures include:
- `state_changes`
- `relationship_events`
- `timeline_events`
- `world_rules`
- `open_loops`
- `reader_promises`

They do not yet form a unified mainline.

### 10.2 Target

- Every chapter commit produces `accepted_events`.
- Projections update from events, not only final-value overwrites.

### 10.3 Minimal Event Family

1. `character_state_changed`
2. `relationship_changed`
3. `world_rule_revealed`
4. `world_rule_broken`
5. `power_breakthrough`
6. `artifact_obtained`
7. `promise_created`
8. `promise_paid_off`
9. `open_loop_created`
10. `open_loop_closed`

### 10.4 Events and Contracts

Events do not directly modify `MASTER / VOLUME / CHAPTER`.

1. Enter events into `CHAPTER_COMMIT.accepted_events`.
2. If an event meets criteria for a higher-level setting change, create an `amend proposal`.
3. Update higher contracts after human confirmation.

This preserves both creative reversals and contract stability.

---

## 11. Pre- and Post-Writing Validation

### 11.1 Before Writing

Check explicitly:
1. Visible chapter contracts exist.
2. Prohibitions are complete.
3. No unresolved high-priority disambiguation remains.
4. Must-cover requirements are clear.
5. Whether a local override summary is needed.

### 11.2 After Writing

Check explicitly:
1. `blocking rules`
2. `mandatory_nodes` fulfillment
3. `anti_patterns` hits
4. Stable names for key entities
5. Setting amendments requiring escalation

### 11.3 Outline Fulfillment

The system currently records what was written without checking whether required content was written.

Add to `CHAPTER_COMMIT`:
- `planned_nodes`
- `covered_nodes`
- `missed_nodes`
- `extra_nodes`

At minimum, nonempty `missed_nodes` must prevent silent successful submission.

### 11.4 Earlier Disambiguation

Do not rely solely on final writeback fallback.

1. Before writing, supply a `disambiguation domain`: allowed frequent entities, aliases, and forms of address.
2. After writing, validate again at `CHAPTER_COMMIT`.

Only unresolved cases enter `disambiguation_pending`.

---

## 12. Existing Module Evolution

### 12.1 reference_search.py

New role:
- Low-level primitive
- CSV retrieval engine
- No system-aggregation responsibility

### 12.2 context_manager.py

New role: Contract-first runtime assembler.

Sequence:
1. Phase 1 retains current structure.
2. Phase 1 adds `story_contract` section.
3. Phase 2 fixes pack priority: `chapter -> volume -> master -> old profile`.
4. Phase 3 removes overlapping global-system generation.

### 12.3 genre_aliases.py / genre_profile_builder.py / genre-profiles.md

New role: Active seed sources while route tables are built.

1. Manually migrate stable fields into `题材与调性推理.csv`.
2. Make `story_system` prefer CSV.
3. Demote `genre-profiles.md` to fallback/reference.

### 12.4 state_manager

New role: Coordinates `CHAPTER_COMMIT` projection writers, not chapter-fact authority.

Responsibilities:
- Write accepted-commit state projections into `state.json`.
- Synchronize SQLite.
- Maintain local atomic writes and recovery.

### 12.5 index.db

New role:
- Fact retrieval
- Event indexing
- Audit history

Not the primary source of story rules.

### 12.6 Memory Writer / Orchestrator / Summaries

New role:
- Supplemental facts
- Historical recall
- Foreshadowing resolution

Stages:
1. Phase 1 may retain current behavior.
2. Phase 2 consumes accepted `CHAPTER_COMMIT` only.
3. Phase 3 aligns with the canonical event log.

### 12.7 override_contracts

Foundation of the unified override ledger, no longer limited to reader-retention debt.

### 12.8 scripts/data_modules/config.py

Continue as the unified project configuration entry point.

Constraints:
1. Reuse `DataModulesConfig` in Phase 1.
2. Put new `story_system` configuration under a clear namespace.
3. Do not create an independent parallel configuration tree.

Otherwise runtime budgets, contract budgets, and projection paths diverge, undermining contracts at the engineering level.

---

## 13. Staged Evolution

### 13.1 Phase 0: Prepare Convergence

Goal: Clarify authority and priority without changing the main flow.

Deliver:
1. Document current authority priority consistently.
2. Identify contract injection into `context_manager`.
3. Define transitional `genre-profiles.md` role.
4. Define `override_contracts` expansion.

### 13.2 Phase 1: Contract Seeds

Goal: Establish the first stable contracts.

Deliver:
1. `题材与调性推理.csv`
2. Minimal `MASTER_SETTING`
3. Minimal `CHAPTER_BRIEF`
4. `anti_patterns.json`
5. Contract reads in `context_manager`

Still permitted:
- Existing writing chain
- Genre-profile fallback
- No `VOLUME_BRIEF` yet

### 13.3 Phase 2: Contract-First Runtime

Goal: Planning, writing, and review use contracts as primary input.

Deliver:
1. `VOLUME_BRIEF`
2. `REVIEW_CONTRACT`
3. Pre-writing prohibitions and disambiguation domain
4. Outline-fulfillment diff
5. Contract-first context pack

Ad hoc reference assembly stops being the default. Contract-first plus on-demand local references becomes normal.

### 13.4 Phase 3: Chapter Commits

Goal: All fact writeback passes through one chapter-commit object.

Deliver:
1. `CHAPTER_COMMIT`
2. Four projection writers
3. Accepted/rejected semantics
4. Commit-driven writeback

Chapter authority moves from scattered writes to one commit.

### 13.5 Phase 4: Unified Events

Goal: Events become formal inputs to system evolution.

Deliver:
1. Canonical event log
2. Stable event-to-projection mappings
3. Event-to-amend-proposal triggers

### 13.6 Phase 5: Demote Old Paths

Goal: Old hubs become fallback or projection layers.

Exit criteria:
1. Contracts are the default primary input.
2. `CHAPTER_COMMIT` is the default submission mainline.
3. Frequent genres have migrated out of `genre-profiles.md`.
4. `context_manager` no longer independently generates conflicting global judgments.

---

## 14. Data and Directories

### 14.1 Contract Directory

Reuse existing authoritative runtime directory terminology. This repository is the **plugin source development directory**, not the installed runtime root. Persisted paths must follow Claude Code's real installed runtime model.

Three roots:

1. `CLAUDE_PLUGIN_ROOT`
   - Installed plugin directory containing `skills/ agents/ scripts/ references/`.
   - **Never write book project data here.**
2. `WORKSPACE_ROOT`
   - Workspace root; `.claude/.webnovel-current-project` may point to the active book.
3. `PROJECT_ROOT`
   - **Book project root**, defined as the directory containing **`.webnovel/state.json`**.

Story Contracts and `CHAPTER_COMMIT` belong to a particular book, so persist under `PROJECT_ROOT`, not the source repository, installed plugin, or workspace root.

Existing directory example:
- `WORKSPACE_ROOT = D:\wk\xiaoshuo`
- `PROJECT_ROOT = D:\wk\xiaoshuo\凡人资本论`
- Pointer: `D:\wk\xiaoshuo\.claude\.webnovel-current-project`

This demonstrates:
1. The project is one book inside a workspace.
2. It may be its own Git repository; this example contains `.git/`.

Suggested structure, with original runtime directory names preserved:

```text
WORKSPACE_ROOT/
├── .claude/
│   └── .webnovel-current-project
├── 小说A/
├── 小说B/
└── ...

PROJECT_ROOT/
├── .git/                  # Optional independent book version control
├── 正文/
├── 大纲/
├── 设定集/
├── 审查报告/
├── .webnovel/
└── .story-system/
    ├── MASTER_SETTING.json
    ├── MASTER_SETTING.md
    ├── anti_patterns.json
    ├── anti_patterns.md
    ├── volumes/
    │   ├── volume_001.json
    │   └── volume_001.md
    ├── chapters/
    │   ├── chapter_001.json
    │   └── chapter_001.md
    ├── reviews/
    │   ├── chapter_001.review.json
    │   └── chapter_001.review.md
    └── commits/
        ├── chapter_001.commit.json
        └── chapter_001.commit.md
```

`.story-system/` is explicitly **relative to `PROJECT_ROOT`**, never the source repository, `CLAUDE_PLUGIN_ROOT`, `WORKSPACE_ROOT`, or arbitrary working directory.

Any implementation-plan use of “root” must distinguish all three named roots.

### 14.1.1 Path Resolution

All runtime entry points follow existing rules:

1. Accept `WORKSPACE_ROOT` externally.
2. Resolve the actual `PROJECT_ROOT` through `resolve_project_root(...)`.
3. Base every `.story-system` read/write on that resolved root.

Thus:
- CLI `--project-root` may accept either a book root or workspace root.
- Entry points resolve it.
- Contracts and commits use only the final resolved project root.
- A user currently at workspace level must still resolve the book before accessing `.story-system/`.

### 14.2 Authority Rules

1. `*.json` is authoritative.
2. `*.md` is a read-only rendering.
3. The same applies in `reviews/` and `commits/`.

### 14.3 Names

Use zero padding:
- `volume_001`
- `chapter_001`

Do not put natural-language titles in filenames.

---

## 15. Knowledge Layers

### 15.1 CSV Responsibilities

- Itemized knowledge
- Routing knowledge
- Structured boundaries
- Search triggers and synonyms

### 15.2 Markdown Responsibilities

- Methodology
- Review rules
- Anti-AI guidance
- Polishing, voice, and formatting

### 15.3 Transitional Conclusion

Do not claim CSV has fully replaced Markdown before evolution is complete.

Instead:
- CSV supplies rules and routes.
- Markdown supplies methods and execution manuals.
- Contracts consolidate the structured knowledge this particular book needs before writing.

---

## 16. Testing and Verification

### 16.1 Principle

Avoid the heavyweight approach of one test per knowledge entry.

### 16.2 Required Coverage

1. Contract generation succeeds.
2. Override rules work.
3. `anti_patterns` aggregation is correct.
4. `context_manager` reads contracts correctly.
5. `REVIEW_CONTRACT` expresses blocking rules.
6. `CHAPTER_COMMIT` blocks invalid writeback.
7. Projection writers consume accepted commits only.
8. Events enter the canonical event log.

### 16.3 Not Required

1. Assertions for every CSV entry.
2. Mechanical semantic tests for every knowledge item.
3. Making data-content testing the main workload.

---

## 17. Documentation and Operations

### 17.1 Documentation

Every implementation plan explicitly includes updates to:
1. Contract schemas
2. Directory structure
3. Runtime flow
4. Migration guidance

### 17.2 Operations

`.story-system` must not become an operational blind spot. Integrate it into:
1. Preflight
2. Dashboard
3. Health checks
4. Backup/restore

### 17.3 Minimum Health Checks

1. `MASTER_SETTING.json` exists.
2. Contract schemas are readable.
3. No unhandled rejected chapter-commit backlog.
4. No persistently incomplete projection status.

---

## 18. Final Architecture Conclusions

1. The central problem is a missing mainline, not too few modules.
2. Retain but reposition `context_manager / genre_* / state_manager / memory / override_contracts`.
3. The essential addition is `Story Contract + Chapter Commit + Override Ledger + Canonical Event Log`, not another search entry point.
4. Contracts as pre-writing truth and commits as post-writing truth turn loosely connected hubs into a unified story operating system.

---

## 19. Implementation Advice

Do not begin with an event bus. Follow:

1. Working contract seeds
2. Contract-first runtime
3. `CHAPTER_COMMIT`
4. Unified event mainline

Otherwise a complete event model may create the illusion of progress while writing remains fragmented.

The immediate next artifact is an implementation plan explicitly containing:

1. Documentation tasks
2. Directory/path semantics tasks
3. Runtime integration-point tasks
