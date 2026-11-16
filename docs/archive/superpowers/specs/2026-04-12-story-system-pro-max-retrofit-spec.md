# Webnovel Writer Story System Pro Max Architecture Retrofit Specification

> Date: 2026-04-12
> Status: Draft v1
> Goal: Add genre reasoning, multi-table aggregation, and persistent Master/Chapter overrides without breaking existing `reference_search.py` and CSV retrieval contracts.

---

## 1. Document Purpose

### 1.1 Relationship to Existing Specifications

This specification supplements, rather than replaces:

- `2026-04-02-harness-v6-design.md`
- `2026-04-09-skills-restructure-and-reference-gaps.md`

Their responsibilities are:

- `2026-04-02-harness-v6-design.md`: main workflow and harness architecture.
- `2026-04-09-skills-restructure-and-reference-gaps.md`: boundaries between `skills / references / scripts` and reference-design principles.
- **This specification**: a new `Story System` layer above the existing CSV knowledge base.

### 1.2 Problems to Solve

The system already supports discrete retrieval, but has three structural problems:

1. Results are isolated entries, not a coherent system setting.
2. After reading individual results, the model easily forgets global constraints and reader turn-offs.
3. Chapters lack a stable persistence mechanism for local overrides of global defaults.

Introduce a higher-level capability:

- Global genre/subgenre routing first
- Multi-table aggregation next
- Persistence as `MASTER + Chapter Overrides` last

---

## 2. Goals and Non-Goals

### 2.1 Goals

This retrofit has exactly five goals:

1. Add a genre-and-tone reasoning table to turn vague genre input into structured writing direction.
2. Add `story_system.py` as an aggregator above existing CSV retrieval.
3. Define a stable `StorySystemDict` data contract.
4. Establish `.story-system/` persistence conventions and explicit `Master + Overrides` rules.
5. Provide stable integration points for future skills and prompts.

### 2.2 Non-Goals

This effort does **not**:

1. Replace or redefine `reference_search.py` responsibilities.
2. Migrate all Markdown references into CSV.
3. Require identical reader-turn-off column names across every existing CSV.
4. Assume a particular `SKILL.md` exists in the current repository.
5. Require a heavyweight test matrix or individual tests for every knowledge entry.

---

## 3. Design Principles

### 3.1 Preserve the Retrieval Primitive

[`reference_search.py`](D:/wk/novel%20skill/webnovel-writer/webnovel-writer/scripts/reference_search.py) already reliably:

- Reads CSV
- Filters by `skill / table / query / genre`
- Scores using BM25-lite
- Returns a stable JSON envelope

It is protected by regression tests:

- [`test_reference_search.py`](D:/wk/novel%20skill/webnovel-writer/webnovel-writer/scripts/tests/test_reference_search.py)

Do not turn it into a system-level aggregator. The correct layers are:

- `reference_search.py`: low-level single-search primitive
- `story_system.py`: system-level orchestration and persistence entry point

### 3.2 Do Not Force Major Existing-Schema Changes

The existing CSV contract is documented in [`README.md`](D:/wk/novel%20skill/webnovel-writer/webnovel-writer/references/csv/README.md), and the content volume is already substantial.

Follow these principles:

- **Add rather than rewrite.**
- **Map rather than rename columns en masse.**
- **Add structures only for genuinely missing capabilities.**

### 3.3 Master and Chapter Must Be Machine-Readable

If `.story-system/` stores only human-readable Markdown, later agents must reparse semistructured text, making the system brittle.

Persistence therefore requires **dual artifacts**:

- Markdown for people
- JSON for scripts and agents

### 3.4 Explicit Override Rules

Saying only “chapter overrides master” is insufficient.

Divide fields into three classes:

1. `locked`: no local override
2. `append_only`: local additions only
3. `override_allowed`: local overrides permitted

Otherwise local settings can erase global settings and red lines.

### 3.5 Normalize Anti-Patterns Without Forcing Identical Names

Existing reader-turn-off/pitfall fields differ, for example:

- `场景写法.csv`: `反面写法`
- `写作技法.csv`: `常见误区`
- `爽点与节奏.csv`: `常见崩盘误区`
- `人设与关系.csv`: `忌讳写法`

This is not inherently a problem.

The correct approach here is:

- Define an anti-pattern source-field mapping inside `story_system.py`.
- Normalize results to `Anti-Patterns` when rendering.
- Add dedicated fields only to tables that genuinely lack a place for reader turn-offs.

---

## 4. Current Baseline

### 4.1 Available CSV Tables

`references/csv` currently contains:

- `命名规则.csv`
- `场景写法.csv`
- `写作技法.csv`
- `桥段套路.csv`
- `人设与关系.csv`
- `爽点与节奏.csv`
- `金手指与设定.csv`

### 4.2 Common CSV Contract

These shared columns are stable:

- `编号`
- `适用技能`
- `分类`
- `层级`
- `关键词`
- `意图与同义词`
- `适用题材`
- `大模型指令`
- `核心摘要`
- `详细展开`

New tables should follow this contract, not invent another column system.

### 4.3 Missing Capabilities

The gap is not knowledge volume, but:

1. Global routing for vague genre input
2. Layered aggregation across multiple tables
3. Reliable persistence of aggregated results as chapter-level override documents

---

## 5. New Data Structure: 题材与调性推理.csv

### 5.1 Location

Add:

- `webnovel-writer/references/csv/题材与调性推理.csv`

Suggested prefix:

- `GR-`

### 5.2 Responsibility

This is a **routing table**, not an ordinary knowledge-entry table.

Rather than supplying one plot beat or technique, it answers:

- What is the genre's overall tone?
- How should its pacing begin?
- Which base tables should be searched first?
- Which dynamic tables should be searched first?
- Which genre-level reader turn-offs must never be crossed?

### 5.3 Columns

Add these dedicated columns alongside the shared columns:

| Column | Required | Description |
|--------|----------|-------------|
| `题材/流派` | Yes | Primary label, e.g. live-in-son-in-law stories, cyberpunk hackers, or a rules-based zoo |
| `题材别名` | Yes | Synonyms, platform slang, and common names, separated by `|` |
| `核心调性` | Yes | Global mood and atmosphere |
| `节奏策略` | Yes | Opening pace, payoff cadence, and chapter beats |
| `主冲突模板` | No | Default conflict skeleton |
| `必选爽点` | No | Frequently required genre payoffs |
| `强制禁忌/毒点` | Yes | Genre-level global red lines |
| `推荐基础检索表` | Yes | E.g. `命名规则|人设与关系|金手指与设定` |
| `推荐动态检索表` | Yes | E.g. `桥段套路|爽点与节奏|场景写法` |
| `基础检索权重` | No | Base-table ranking hints |
| `动态检索权重` | No | Dynamic-table ranking hints |
| `默认查询词` | No | Default query expansions when user input is too vague |

### 5.4 Design Notes

The table must serve three input types:

1. Explicit genre input, e.g. `赘婿流` (live-in-son-in-law stories)
2. Combined genre input, e.g. `赛博朋克黑客流` (cyberpunk hacker stories)
3. Vague style input, e.g. `压抑一点，后面爆` (more restrained initially, explosive later)

Thus `题材别名` and `默认查询词` are necessary, not dispensable.

---

## 6. Anti-Pattern Normalization

### 6.1 Existing-Table Mapping

Use a mapping layer rather than forcing every table to rename fields:

```python
ANTI_PATTERN_SOURCE_FIELDS = {
    "场景写法": ["反面写法"],
    "写作技法": ["常见误区"],
    "爽点与节奏": ["常见崩盘误区"],
    "人设与关系": ["忌讳写法"],
    "桥段套路": ["忌讳写法"],
    "题材与调性推理": ["强制禁忌/毒点"],
}
```

### 6.2 Handling 桥段套路.csv

Currently `桥段套路.csv` has only:

- `桥段名称`
- `前置铺垫`
- `核心爽点`
- `转折设计`
- `反套路变种`

`反套路变种` describes trope subversions, not anti-patterns, and must not be treated as reader-turn-off data.

Recommended change:

- **Add** `忌讳写法` to `桥段套路.csv`.
- Fill it progressively for new entries.
- Allow existing entries to remain empty temporarily.

### 6.3 Final Aggregation

Rendered `Anti-Patterns` is the union of:

1. Global turn-offs in `题材与调性推理.csv`
2. Entry-level turn-offs from dynamic retrieval matches
3. Chapter-local additions

Remember:

- Chapter may **add** local turn-offs.
- Chapter cannot remove Master global turn-offs.

---

## 7. New Script: story_system.py

### 7.1 Location

Add:

- `webnovel-writer/scripts/story_system.py`

### 7.2 Role

`story_system.py` is the system aggregation layer, not the low-level retrieval layer.

It handles:

1. Genre routing
2. Multi-table query orchestration
3. Result aggregation
4. Markdown / JSON output
5. `.story-system/` persistence

It does not:

1. Replace `reference_search.py`
2. Generate prose directly
3. Parse or execute a particular skill's main workflow

### 7.3 CLI Design

Suggested CLI:

```bash
python story_system.py "玄幻退婚流"
python story_system.py "玄幻退婚流" --persist
python story_system.py "拍卖会打脸" --persist --chapter chapter_015
python story_system.py "压抑一点，后面爆" --genre 现言 --persist
python story_system.py "规则动物园" --format json
```

Suggested arguments:

| Argument | Required | Description |
|----------|----------|-------------|
| Positional `query` | Yes | Current user intent or genre description |
| `--genre` | No | Explicit genre |
| `--chapter` | No | Chapter override name, e.g. `chapter_015` |
| `--persist` | No | Write to `PROJECT_ROOT/.story-system/` |
| `--format` | No | `markdown` / `json` / `both` |
| `--csv-dir` | No | Testing and custom-directory support |
| `--story-root` | No | Explicit `.story-system/` directory for development/testing only; mainline runtime resolves it from `PROJECT_ROOT` by default |

### 7.4 Main Workflow

Fix the `story_system.py` execution order as follows.

#### Step 1: Genre Reasoning

Search `题材与调性推理.csv` first using `query`:

- Clear genre match → use the genre-routing result
- Multiple matches → weighted ranking with a primary route and candidates
- No match → fallback

#### Step 2: Fallback Routing

With no match, fall back in this order:

1. Use explicitly supplied `--genre` as the primary genre.
2. Extract from `query` the genre closest to frequent keywords in existing tables.
3. If still unsuccessful, use general-writing routing:
   - Default base tables: `命名规则|人设与关系|金手指与设定`
   - Default dynamic tables: `桥段套路|爽点与节奏|场景写法`

#### Step 3: Base-Table Retrieval

Use `推荐基础检索表` from the genre-routing table:

- Take Top 1 from each base table.
- Defaults:
  - `命名规则`
  - `人设与关系`
  - `金手指与设定`
  - Future extension: `题材与调性推理`

#### Step 4: Dynamic-Table Retrieval

Use `推荐动态检索表` from the genre-routing table:

- Take Top 2 from each dynamic table.
- Defaults:
  - `桥段套路`
  - `爽点与节奏`
  - `场景写法`
  - Optional addition: `写作技法`

#### Step 5: Aggregate Anti-Patterns

Merge genre-level turn-offs and entry-level pitfall fields into one normalized collection.

#### Step 6: Render and Persist

Output:

- `StorySystemDict`
- Markdown view
- Optional writes to `.story-system/`

---

## 8. StorySystemDict Data Contract

### 8.1 Top-Level Structure

Suggested structure:

```json
{
  "meta": {},
  "route": {},
  "master_constraints": {},
  "base_context": {},
  "dynamic_context": {},
  "anti_patterns": [],
  "override_policy": {},
  "source_trace": []
}
```

### 8.2 Detailed Fields

#### `meta`

Record:

- Query
- Explicit genre
- Inferred matched genre
- Whether chapter mode is active
- Generation time

#### `route`

Record:

- Primary genre route
- Candidate genres
- Routing-match rationale
- Recommended base tables
- Recommended dynamic tables

#### `master_constraints`

Record global information that should not change casually:

- Core tone
- Pacing strategy
- Main-conflict template
- Hard limits on the protagonist's special advantage
- Hard protagonist constraints
- Global reader turn-offs

#### `base_context`

Store base-table results:

- `命名规则`
- `人设与关系`
- `金手指与设定`
- Optional `写作技法`

#### `dynamic_context`

Store dynamic-table results:

- `桥段套路`
- `爽点与节奏`
- `场景写法`

#### `anti_patterns`

Unified format:

```json
[
  {
    "source_table": "爽点与节奏",
    "source_id": "PA-054",
    "text": "质疑太弱没有压迫"
  }
]
```

#### `override_policy`

Explicitly declare:

- `locked`
- `append_only`
- `override_allowed`

#### `source_trace`

Record matched sources:

- Table name
- Entry ID
- Summary
- Instruction

This is primarily for debugging and traceability.

---

## 9. Markdown Formatter Specification

### 9.1 Output Goal

Markdown is a readable view for humans and agents, not raw data.

It must provide:

1. Clear hierarchy
2. Immediately visible global tone
3. Immediately visible chapter overrides
4. Immediately visible absolute turn-offs

### 9.2 Suggested Structure

```markdown
# Story System

## Meta

## Route

## Master Constraints

## Base Context

## Dynamic Context

## Anti-Patterns

## Source Trace
```

### 9.3 Anti-Patterns Section Requirements

Retain a prominent section:

```markdown
## Anti-Patterns (Absolute Red Lines: Never Cross)
```

Display rules:

- Give each red line its own item.
- Wrap short statements in backticks.
- Identify the source table and ID.

For example:

```markdown
- `Supporting characters must not monopolize the spotlight for more than 300 Chinese characters consecutively` (source: GR-003)
- `A face-slapping payoff must include the final finishing beat` (source: PA-054)
```

### 9.4 JSON–Markdown Relationship

Make these rules explicit:

- JSON is the source data.
- Markdown is a projection of JSON.
- All override/merge logic uses JSON, not reverse-parsed Markdown.

---

## 10. Persistence Architecture: .story-system

### 10.1 Directory Structure

Follow existing runtime-directory terminology rather than inferring locations from the source checkout:

1. `CLAUDE_PLUGIN_ROOT`
   - Plugin installation directory
   - Contains `skills / scripts / references`
   - Never receives book-project data
2. `WORKSPACE_ROOT`
   - Claude workspace root
   - Resolves the current book project through `.claude/.webnovel-current-project`
3. `PROJECT_ROOT`
   - Actual book-project root
   - Defined as the directory containing `.webnovel/state.json`

Therefore the default persistence location must be:

- `PROJECT_ROOT/.story-system/`

Not:

- The current source checkout
- `CLAUDE_PLUGIN_ROOT`
- `WORKSPACE_ROOT`

Suggested layout:

```text
PROJECT_ROOT/
  .webnovel/
  正文/
  大纲/
  设定集/
  .story-system/
    MASTER_SETTING.md
    MASTER_SETTING.json
    chapters/
      chapter_001.md
      chapter_001.json
      chapter_015.md
      chapter_015.json
```

Additional runtime constraints:

1. Skills start from `WORKSPACE_ROOT` by default.
2. Resolve the actual `PROJECT_ROOT` through `webnovel.py --project-root "${WORKSPACE_ROOT}" where`.
3. When part of the mainline, `story_system` recognizes only the resolved `PROJECT_ROOT`.
4. `--story-root` is a development override, not a default skill input.

### 10.2 MASTER Responsibilities

`MASTER_SETTING.*` stores:

- Primary genre route
- Global tone
- Hard protagonist constraints
- Hard limits on the protagonist's special advantage
- World-level constraints
- Long-range pacing strategy
- Global anti-patterns

### 10.3 Chapter Responsibilities

`chapters/chapter_xxx.*` stores:

- Chapter plot beats
- Chapter scenes
- Local pacing
- Additional local turn-offs
- Special chapter emphases

### 10.4 Override Classes

#### 10.4.1 `locked`

Read these only from Master; Chapter cannot override them:

- Primary genre route
- Core tone
- Foundational protagonist characterization
- Hard limits on the protagonist's special advantage
- World-rule consistency
- Global anti-patterns

#### 10.4.2 `append_only`

Chapter may add to these but cannot delete Master content:

- Naming language families
- Long-range foreshadowing
- Long-range relationship reminders
- Additional global prohibitions
- Important source traces

Merge through:

- Union
- Deduplication

#### 10.4.3 `override_allowed`

Chapter may override Master defaults for:

- Chapter plot beats
- Chapter scenes
- Chapter pacing goals
- Local emotional emphasis
- Chapter output priorities

### 10.5 Anti-Pattern Merge Rules

The effective writing red lines are:

```text
Effective red lines = Master global red lines ∪ Chapter local red lines
```

Remember:

- Chapter may add new red lines.
- Chapter cannot remove Master red lines.

### 10.6 File-Update Strategy

To avoid overwriting manual edits:

1. Scripts fully manage JSON files.
2. Markdown files may contain manual-notes sections.
3. Scripts update only marked autogenerated blocks.

Suggested markers:

```markdown
<!-- STORY-SYSTEM:BEGIN -->
... autogenerated content ...
<!-- STORY-SYSTEM:END -->
```

Scripts must not modify handwritten content outside the markers.

---

## 11. Prompt / Skill Integration Contract

### 11.1 Define the Contract Without Assuming Specific Hooks

Editable `SKILL.md` locations for `webnovel-plan` / `webnovel-write` are not directly exposed in the current repository.

This specification therefore does not assume:

- Prompts reside in this repository.
- Skills reside in this repository.
- Runtime automatically reads a particular path.

Define only the **integration contract** here.

### 11.2 Standard Read Logic

Future integration must:

1. Prefer `chapters/[当前章节].json` if it exists.
2. Prefer Chapter for `override_allowed` fields.
3. Merge Chapter and Master for `append_only` fields.
4. Read only Master for `locked` fields.
5. Always include the union of global and local `Anti-Patterns`.

### 11.3 Standard Prompt Fragment

Suggested integration constraints:

```markdown
[Core State Read Logic]
1. If `.story-system/chapters/[当前章节].json` exists, read Chapter first.
2. Chapter governs `override_allowed` fields.
3. Merge `append_only` fields by union.
4. `locked` fields obey only `.story-system/MASTER_SETTING.json`.
5. `Anti-Patterns` is the union of global and local rules; none may be violated.
```

---

## 12. Implementation Phases

### Phase 1: Data Layer

Deliver:

1. New `题材与调性推理.csv`
2. New `忌讳写法` column in `桥段套路.csv`
3. Updated `references/csv/README.md`

This phase does not require bulk rewriting of existing table content.

### Phase 2: Aggregation Script

Deliver:

1. New `story_system.py`
2. Unchanged responsibilities for `reference_search.py`
3. `StorySystemDict` implementation
4. Markdown / JSON output

### Phase 3: Persistence

Deliver:

1. Automatic creation of `.story-system/`
2. `MASTER_SETTING.*` persistence
3. `chapter_xxx.*` persistence
4. Marked-block update logic

### Phase 4: Integration Layer

Deliver:

1. Locate the actual skill / prompt integration points.
2. Integrate using this specification's read priorities.
3. Verify Chapter overrides correctly replace local fields.

---

## 13. Testing Strategy

### 13.1 Principles

This project does not need a test for every knowledge item.

Protect system contracts, not content details.

### 13.2 Required Tests

Add at least these lightweight tests:

1. **Genre routing**
   - Explicit genres match `题材与调性推理.csv`.
   - Vague queries use fallback.
2. **Aggregation structure**
   - All top-level `StorySystemDict` fields exist.
   - Base/dynamic results enter the correct sections.
3. **Anti-pattern aggregation**
   - Pitfall fields from different tables are extracted uniformly.
   - Master and Chapter red lines form a union.
4. **Override rules**
   - Chapter cannot override `locked` fields.
   - `append_only` uses the correct union.
   - Chapter takes priority for `override_allowed`.
5. **Persistence**
   - `--persist` writes Markdown and JSON.
   - Manual content outside markers is not overwritten.
6. **Retrieval regression**
   - Existing `reference_search.py` tests continue to pass.

### 13.3 Tests Not Required

This effort does not require:

1. Assertions for every CSV knowledge entry
2. Visual-detail snapshots of Markdown rendering
3. Complex end-to-end agent tests

---

## 14. Risks and Constraints

### 14.1 Greatest Risk

The greatest risk is confused responsibilities, not code complexity.

Avoid:

1. Breaking `reference_search.py`
2. Treating Markdown as source data
3. Letting Chapter erase Master hard limits
4. Mistaking `反套路变种` for a reader-turn-off field

### 14.2 Data-Entry Constraints

Continue following existing CSV principles:

- Primarily curate new content manually.
- Do not automatically migrate all Markdown.
- Do not require every genre to be completed at once.

### 14.3 Rollout Order

The correct order is:

1. Add the routing table.
2. Write the aggregator.
3. Implement persistence.
4. Integrate prompts / skills last.

Do not skip intermediate layers and have prompts directly assemble CSV results.

---

## 15. Final Conclusion

The core upgrade is not a bigger search system, but:

1. **Preserving the stable retrieval primitive**
2. **Adding a Story System aggregator**
3. **Persisting global constraints and local overrides**
4. **Having the model follow a structured system instead of repeatedly reinterpreting scattered results**

The goal is not more elaborate search:

**Start a book with a Master, write chapters with Overrides, and always have traceable, persistent, authoritative system-level context.**
