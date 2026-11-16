# Story System Final Convergence Specification

> **Date**: 2026-04-14
> **Status**: Draft v1
> **Purpose**: Based on the actual codebase, converge Story System from coexisting partial implementations into a six-layer mainline with synchronized consumers

---

## 1. Document Purpose

### 1.1 Problems This Specification Addresses

Earlier documents answered three questions:

- [`current-system-diagnosis.md`](../../architecture/current-system-diagnosis.md)
  - Where the current system is fragmented, duplicated, or only partially implemented
- [`2026-04-12-story-system-evolution-spec.md`](./2026-04-12-story-system-evolution-spec.md)
  - What the six-layer mainline should look like
- [`2026-04-14-context-agent-writing-brief-design.md`](./2026-04-14-context-agent-writing-brief-design.md)
  - How to consolidate the pre-writing brief entry point

This specification addresses a more direct question:

> Without preserving backward compatibility, how can the current code, CSVs, contracts, commit pipeline, projections, and consumers converge in one effort into a usable final state?

### 1.2 One-Sentence Conclusion

The goal is not to add another module, but to:

- Complete all six layers
- Delete scattered legacy write paths outright
- Reduce `context_manager` to a pure JSON assembler
- Make `CSV_CONFIG + reasoning table + contract tree + commit/projection` the sole mainline
- Have all consumers use only contracts and projection views

---

## 2. Confirmed Key Decisions

The following decisions were confirmed in brainstorming and should not be repeatedly reconsidered.

### 2.1 Scope

- Cover **all six layers**.
- Do not change only the code layer.
- Synchronize consumers including skills, agents, CLI, evals, and documentation.

### 2.2 Backward Compatibility

- **Do not preserve backward compatibility.**
- Delete legacy scattered-write, direct-read, and fallback paths wherever possible.
- Do not retain deprecated dual paths.

### 2.3 `context_manager`

- Reduce it to a **pure JSON payload assembler**.
- Remove text-rendering responsibilities.
- Remove snapshot logic serving the old instruction-manual text output.

### 2.4 `CSV_CONFIG`

- Place it in `reference_search.py`.
- Model its form on `ui-ux-pro-max/core.py`.
- Explicitly declare `file / search_cols / output_cols / poison_cols / role` for every table.

### 2.5 Reasoning Layer

- Create an independent `裁决规则.csv`.
- Key it by genre.
- It determines how to adjudicate matches, what takes priority, and where to inject results, not which tables to search.

### 2.6 `anti-ai-guide.md` and `core-constraints.md`

- Keep `anti-ai-guide.md` as the Markdown source of truth.
  - Do not split it into CSV.
  - Do not let consumers read it directly.
  - Upstream stages absorb and rewrite it only where needed.
- Stop reading `core-constraints.md` in full.
  - Decompose it into concrete constraints.
  - Place them at the appropriate stages in contracts, runtime, review, commit validation, and consumer wording.

### 2.7 Consumer Sources of Truth

- All consumers may directly consume only:
  - The contract tree
  - `CHAPTER_COMMIT`
  - Projection views
- Do not allow direct runtime reads of CSV / Markdown / references to fill gaps.

### 2.8 Initial Genre Scope

Complete these seven genres first (exact table labels retained):

1. Western fantasy (`西方奇幻`)
2. Eastern xianxia (`东方仙侠`)
3. Science-fiction apocalypse (`科幻末世`)
4. Urban slice of life (`都市日常`)
5. Urban cultivation (`都市修真`)
6. Urban high martial arts (`都市高武`)
7. Historical fiction (`历史古代`)

Other genres are outside this convergence effort.

### 2.9 Implementation Order

- Work upward from the foundations.
- Execute serially, not in parallel.
- Stabilize the foundations before synchronizing consumers.

---

## 3. Overall Pipeline

The final pipeline is fixed:

```text
Knowledge tables / reasoning table
        ↓
CSV_CONFIG + reference_search
        ↓
story_system_engine
        ↓
MASTER / VOLUME / CHAPTER / REVIEW
        ↓
context_manager (JSON only)
        ↓
context-agent (write the brief following examples)
        ↓
webnovel-write Step 2 (brief only)
        ↓
review / data-agent
        ↓
CHAPTER_COMMIT
        ↓
projection writers
        ↓
state / index / summaries / memory / vector
```

Two hard boundaries apply:

1. Consumers no longer read the knowledge layer directly at runtime.
2. Post-writing facts enter storage only through `CHAPTER_COMMIT -> projection`.

---

## 4. Section 1: `CSV_CONFIG` Registry Layer

### 4.1 Work Required

Introduce a registry-based `CSV_CONFIG` in `reference_search.py`, replacing the current global hard-coded:

- `_SEARCH_FIELD_WEIGHTS`
- `_CONTENT_COLUMNS`

Each table instead defines:

- `file`
- `search_cols`
- `output_cols`
- `poison_cols`
- `role`

### 4.2 Target Form

```python
CSV_CONFIG = {
    "命名规则": {
        "file": "命名规则.csv",
        "search_cols": ["关键词", "意图与同义词", "核心摘要"],
        "output_cols": ["编号", "命名对象", "核心摘要", "大模型指令", "详细展开"],
        "poison_cols": ["毒点"],
        "role": "base",
    },
    "场景写法": {
        "file": "场景写法.csv",
        "search_cols": ["关键词", "意图与同义词", "核心摘要"],
        "output_cols": ["编号", "模式名称", "核心摘要", "大模型指令", "详细展开"],
        "poison_cols": ["毒点"],
        "role": "base",
    },
    "题材与调性推理": {
        "file": "题材与调性推理.csv",
        "search_cols": ["题材关键词", "别名"],
        "output_cols": ["题材", "默认调性", "推荐基础表", "推荐动态表"],
        "poison_cols": ["毒点"],
        "role": "route",
    },
    "裁决规则": {
        "file": "裁决规则.csv",
        "search_cols": ["题材"],
        "output_cols": [
            "题材",
            "风格优先级",
            "爽点优先级",
            "节奏默认策略",
            "毒点权重",
            "冲突裁决",
            "contract注入层",
            "反模式",
        ],
        "poison_cols": [],
        "role": "reasoning",
    },
}
```
### 4.3 Required Changes

- `reference_search.py`
  - Read per-table configuration from `CSV_CONFIG`.
- `story_system_engine.py`
  - Stop hard-coding table roles internally.
  - Use `CSV_CONFIG` instead.
- Add a validation script.
  - Validate `CSV_CONFIG`.
  - Validate CSV headers.
  - Validate `README.md`.

### 4.4 Acceptance

- The same CLI actually uses different `search_cols` for different tables.
- Every field declared in `CSV_CONFIG` exists in the corresponding CSV header.
- The validation script passes.

---

## 5. Section 2: CSV Content Repairs

### 5.1 Work Required

Audit and repair existing tables consistently so the reasoning and contract layers can consume them reliably.

### 5.2 Main Problems

- Inconsistent names for reader-turn-off columns
- Insufficient routing-table fields
- Too few synonyms
- Uneven genre coverage

### 5.3 Specific Changes

#### 5.3.1 Standardize Reader-Turn-Off Columns

Rename these legacy columns uniformly to `毒点`:

- `反面写法`
- `忌讳写法`
- `常见误区`
- `常见崩盘误区`

#### 5.3.2 Add Routing-Table Fields

At minimum, add these to `题材与调性推理.csv`:

- `推荐基础表`
- `推荐动态表`
- `默认调性`
- `风格锚点`

#### 5.3.3 Content-Completion Rules

Make all additions manually; do not write an automated migration script.

Minimum requirements:

- Every table covers common scenarios for all seven genres.
- Every `意图与同义词` entry includes at least three synonymous expressions.
- Every `毒点` entry is nonempty.

#### 5.3.4 Synchronize README

Update `README.md` to reflect:

- The standardized reader-turn-off column name
- New routing-table fields
- Each table's schema

### 5.4 Acceptance

- All reader-turn-off columns are named `毒点`.
- The routing table returns recommended base and dynamic tables.
- `README` and `CSV_CONFIG` agree.

---

## 6. Section 3: Reasoning Table

### 6.1 Work Required

Create `裁决规则.csv` as an independent `Reasoning Layer`.

It does not choose which tables to search. It determines:

- How to select among multiple matches
- Which payoff types take priority
- Which reader turn-offs are more damaging
- Which contract-tree layer receives the results

### 6.2 Boundary With the Routing Table

- Routing table: which tables to search
- Reasoning table: how to use the results

This matches the relationship in `ui-ux-pro-max` between:

- `products.csv`
- `ui-reasoning.csv`

### 6.3 Fields

`裁决规则.csv` must include at least:

- `题材`
- `风格优先级`
- `爽点优先级`
- `节奏默认策略`
- `毒点权重`
- `冲突裁决`
- `contract注入层`
- `反模式`

### 6.4 Initial Coverage

Cover the seven genres first, one row each.

### 6.5 Acceptance

- `source_trace` can trace results to the reasoning table.
- Ordering across multiple table matches follows `冲突裁决`.
- Genre-specific output can explain why these entries entered the contract.

---

## 7. Section 4: Integrate the Reasoning Table Into the Engine

### 7.1 Current Problem

Currently `story_system_engine.build()` performs only:

1. Routing
2. Retrieval
3. Direct assembly

There is no explicit reasoning layer.

### 7.2 Target Workflow

Change it to:

1. `_route()`
2. `_collect_tables()`
3. `_load_reasoning()`
4. `_apply_reasoning()`
5. `_rank_anti_patterns()`
6. `_assemble_contract()`

### 7.3 New Methods

- `_load_reasoning(genre)`
- `_apply_reasoning(reasoning, base, dynamic)`
- `_rank_anti_patterns(reasoning, ...)`
- `_assemble_contract(ranked, anti_patterns, reasoning)`

### 7.4 `source_trace`

Everything entering a final contract must include:

- `source_table`
- `source_id`
- `reasoning_rule`
- `priority_rank`
- `inject_target`

### 7.5 Acceptance

- `writing_guidance` ordering follows the reasoning table.
- Every `source_trace` includes `reasoning_rule`.
- Lower-priority conflicting entries can be filtered or downgraded.

---

## 8. Section 5: Slim Down `context_manager`

### 8.1 Goal

Reduce `context_manager.py` from handling:

- Data assembly
- Text rendering
- Snapshot caching
- Checklist/scoring instruction manuals

To:

- **Pure JSON payload assembly**

### 8.2 Retained Responsibilities

- Read contracts
- Read runtime sources
- Assemble `genre_profile`
- Assemble `writing_guidance`
- Assemble `reader_signal`
- Assemble `plot_structure`
- Assemble `prewrite_validation`
- Return a unified dict

### 8.3 Removed Responsibilities

- All `_render_*` methods
- All legacy instruction-manual text output
- Snapshot management serving text rendering
- Inline logic duplicated by extracted builders

### 8.4 Output Form

`build_context()` returns only:

```json
{
  "meta": {"context_contract_version": "v3", "chapter": 12},
  "story_contract": {},
  "runtime_status": {},
  "latest_commit": {},
  "prewrite_validation": {},
  "plot_structure": {},
  "scene": {},
  "writing_guidance": {},
  "reader_signal": {},
  "genre_profile": {},
  "long_term_memory": {},
  "core": {}
}
```

### 8.5 Related Requirements

- `snapshot_manager.py`
  - Delete the whole file if it has no other consumers.
- `extract_chapter_context.py`
  - Stop producing the legacy audit-style text manual.
- Final writing brief
  - `context-agent` generates it directly from the JSON payload and examples.

### 8.6 Acceptance

- `context_manager.py` is fewer than 400 lines.
- No string-concatenated instruction-manual output remains.
- Snapshot logic is removed.

---

## 9. Section 6: Remove Scattered Legacy Write Paths

### 9.1 Problem

Two write paths still coexist:

- New: `data-agent -> chapter-commit -> projection`
- Old: skills / agents directly write `state / index / summaries / memory`

These must converge into one.

### 9.2 Paths to Remove

#### `webnovel-write`

- Direct `state set-chapter-status` in Step 2
- Direct `state set-chapter-status` in Step 4

#### Other Direct-Write Entry Points

- Any `index process-chapter` in skills / agents
- Any data-agent instructions to write `state/index/memory` directly

### 9.3 Permitted Direct Writes

Retain only:

- `webnovel-init`
- `webnovel-plan`
- Manual operational repair commands

None are part of the creative mainline.

### 9.4 `chapter_status`

Skills no longer advance it manually step by step.

Instead:

- accepted commit -> projection advances to `chapter_committed`
- rejected commit -> projection advances to `chapter_rejected`

### 9.5 Acceptance

- No `state set-chapter-status` remains in `skills/` or `agents/`.
- No `index process-chapter` remains in `skills/` or `agents/`.
- Each store is written only by its corresponding projection writer.

---

## 10. Section 7: Consolidate the Projection Layer

### 10.1 Goal

Confirm `CHAPTER_COMMIT -> projection` is the only write pipeline and complete event-routing coverage.

### 10.2 Work Required

#### 10.2.1 Complete `EventProjectionRouter`

Check against `story_event_schema.py` to ensure every event type is covered.

#### 10.2.2 Advance `chapter_status` Exclusively Through `state_projection_writer`

- accepted -> `chapter_committed`
- rejected -> `chapter_rejected`

#### 10.2.3 Write `projection_status` Back to the Commit

No `pending` status may remain in the final commit file.

#### 10.2.4 Failure Isolation

If one writer fails:

- Do not block other writers.
- Record `failed` for that item.
- Allow rerunning only failed writers.

### 10.3 Acceptance

- Final `projection_status` values are all `done / failed / skipped`.
- State advances automatically after an accepted commit.
- A single writer failure does not stall the entire pipeline.

---

## 11. Section 8: Synchronize Consumers

### 11.1 Files to Change

- `agents/context-agent.md`
- `agents/data-agent.md`
- `agents/reviewer.md` (if needed)
- `skills/webnovel-write/SKILL.md`
- `skills/webnovel-review/SKILL.md`
- `skills/webnovel-query/SKILL.md`
- `skills/webnovel-plan/SKILL.md` (inspect)
- `skills/webnovel-init/SKILL.md` (inspect)
- `skills/webnovel-dashboard/SKILL.md`
- `skills/webnovel-write/evals/evals.json`
- `docs/guides/commands.md`

### 11.2 Key Changes

#### `webnovel-write`

- Remove direct state writes in Steps 2/4.
- Remove direct Step 2 loading of `core-constraints` / `anti-ai-guide`.
- Step 1 generates the brief.
- Step 2 consumes only the brief.
- Simplify Step 5 to:
  - Call data-agent.
  - Call chapter-commit.
  - Confirm projection completion.

#### `context-agent`

- Use the working document for research.
- Write the final brief following examples.
- Stop outputting the old three-layer execution package.

#### `data-agent`

- Extract facts only.
- Produce commit artifacts only.
- Do not write directly to `state/index/memory`.

#### `webnovel-query`

- Route queries through commit / projection.
- Stop directly assembling legacy sources of truth at runtime.

### 11.3 Static Tests

At minimum, add these checks to `test_prompt_integrity.py`:

- Skills / agents must not reference removed scattered-write commands.
- `data-agent` must not write directly.
- Every referenced CLI subcommand exists in the registry.

### 11.4 Acceptance

- Skills / agents no longer reference legacy scattered-write paths.
- Static tests pass.
- Evals and command documentation are synchronized.

---

## 12. Section 9: Vector Index Enhancements and Temporal Query Interfaces

### 12.1 Lightweight Enhancements Only

Do not introduce a real graph engine or a new project-level knowledge-graph system.

Do only two lightweight things:

1. Write entities/events into the vector index after commits.
2. Add unified temporal query interfaces over existing SQLite tables.

### 12.2 Add Entity Semantics to the Vector Index

#### `EventProjectionRouter`

Add `vector` routes for key events:

- `character_state_changed`
- `power_breakthrough`
- `relationship_changed`
- `world_rule_revealed`
- `world_rule_broken`
- `artifact_obtained`

#### Add `vector_projection_writer.py`

Responsibilities:

- Convert `accepted_events`
- Convert `entity_deltas`

Into natural-language sentences and write them to the vector store.

For example:

- `Chapter 47: Han Li breaks through to early Foundation Establishment`
- `Chapter 47: Han Li and Chen Qiaoqian's relationship becomes cooperative`

### 12.3 Temporal Query Interfaces

Create `knowledge_query.py` providing:

- `entity_state_at_chapter(entity_id, chapter)`
- `entity_relationships_at_chapter(entity_id, chapter)`

For calls during `context-agent` research.

### 12.4 Non-Goals

- Do not introduce `neo4j`.
- Do not introduce `petgraph`.
- Do not implement graph traversal.
- Do not implement relationship visualization.

### 12.5 Acceptance

- Event chunks enter the vector store.
- State queries at a specified chapter work.
- Relationship queries at a specified chapter work.
- RAG can retrieve both prose chunks and event chunks.

---

## 13. Implementation Order

Proceed strictly serially:

1. `CSV_CONFIG`
2. CSV content repairs
3. Reasoning table
4. Engine integration with the reasoning table
5. `context_manager` slimming
6. Scattered legacy write-path cleanup
7. Projection-layer consolidation
8. Consumer synchronization
9. Vector index enhancements + temporal queries

The rationale is simple:

- This is not routine iteration.
- It is a one-time system convergence.
- The duration of intermediate states is not important.
- Clear acceptance criteria for each step and a correct final state are what matter.

---

## 14. Final Assessment

This specification's conclusion reduces to five statements:

1. Converge all six layers together, not just the first four.
2. Consumers must not read the knowledge layer directly; they consume only contracts and projection views.
3. Decompose `core-constraints` into concrete constraints instead of reading it in full.
4. Retain `anti-ai-guide`, but only for upstream absorption and rewriting.
5. `CHAPTER_COMMIT -> projection` is the sole post-writing source-of-truth path.

Only then does `webnovel-writer` truly move from coexisting partial implementations to a unified mainline.
