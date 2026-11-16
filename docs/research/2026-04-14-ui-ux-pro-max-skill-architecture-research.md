# UI/UX Pro Max Skill Architecture Research Report

> Status: `draft` (2026-04-14)

## Purpose

This report investigates the actual engineering structure of the `ui-ux-pro-max` skill, addressing:

- If it is not a single-file prompt, what is it?
- Why does it work reliably rather than rely on accumulated instructions?
- Which ideas and architecture should `webnovel-writer` learn from?
- What can be adapted, and what should not be copied directly?

Notes:

- Based on local source at
  `C:\Users\lcy\.gemini\tmp\webnovel-writer\ui-ux-pro-max-skill\src\ui-ux-pro-max`
- The goal is transferable system design, not a file-by-file retelling.
- Findings inform subsequent convergence specifications for `references/csv` and `story-system`.

## In One Sentence

`ui-ux-pro-max` works not because its prompt is long, but because it is a small knowledge system combining **external knowledge base + generic retrieval core + higher-level reasoning aggregator + persistent master/override files + platform-distribution adapters**.

What we lack is not an aggregator (`StorySystemEngine` already fills that role), but an **explicit, structured, reviewable adjudication layer**. Many decisions remain scattered across engine code, CSVs, context_manager, and skill text rather than consolidated into configuration.

The five transferable architectural moves are:

1. Move knowledge out of prompts into structured tables.
2. Query knowledge domains through one retrieval primitive.
3. Use explicit reasoning to turn retrieved evidence into final decisions.
4. Persist runtime output as hierarchical `Master + Override` sources of truth.
5. Isolate platform differences in templates/metadata rather than contaminating core knowledge.

One distinction must come first: `ui-ux-pro-max` is a quasi-static, query-time aggregation system. Its styles, colors, fonts, and stack best practices do not evolve with runtime events. Our story system does: character states, relationships, settings, and world rules change with chapter commits. Even copying its first four layers would leave us needing runtime evolution through a `Chapter Commit Layer` and `Projection Layer`.

## Scope

Primary files examined:

- `scripts/core.py`
- `scripts/design_system.py`
- `scripts/search.py`
- `data/*.csv`
- `data/stacks/*.csv`
- `data/_sync_all.py`
- `templates/base/*.md`
- `templates/platforms/*.json`

## Actual System Layers

The directory structure has at least three physical layers and one execution path:

```text
ui-ux-pro-max/
├── data/        # Structured knowledge base
├── scripts/     # Retrieval, reasoning, aggregation, persistence
└── templates/   # Skill-content templates and platform installation metadata
```

Execution path:

```text
query
  -> search.py
  -> core.py / design_system.py
  -> structured output or persisted artifacts
```

### 1. Data Layer: Domain Tables + Reasoning Table + Stack Tables

The data falls into three categories.

#### 1.1 Domain Knowledge Tables

Examples:

- `styles.csv`
- `colors.csv`
- `charts.csv`
- `landing.csv`
- `products.csv`
- `ux-guidelines.csv`
- `typography.csv`
- `icons.csv`
- `react-performance.csv`
- `app-interface.csv`
- `google-fonts.csv`

Instead of one enormous table, these are split by knowledge domain. Evidence:

- `scripts/core.py:17`
- `scripts/core.py:18`
- `scripts/core.py:68`

Each domain has its own:

- `file`
- `search_cols`
- `output_cols`

The design defines **search fields** and **display fields** for each knowledge type rather than searching an entire table indiscriminately.

#### 1.2 Reasoning Table

`ui-reasoning.csv` does not store raw knowledge entries. It handles:

- Category-to-pattern mappings
- Style priorities
- Key effects
- Anti-patterns
- Decision rules

Evidence:

- `scripts/design_system.py:24`
- `scripts/design_system.py:43`
- `scripts/design_system.py:88`

The important separation is between retrieval results and final decisions.

#### 1.3 Stack Tables

It separately maintains 16 tables, including:

- `data/stacks/react.csv`
- `data/stacks/nextjs.csv`
- `data/stacks/vue.csv`
- `data/stacks/react-native.csv`
- `data/stacks/threejs.csv`

These contain **implementation best practices**, not product knowledge.

Evidence:

- `scripts/core.py:75`
- `scripts/core.py:95`
- `data/stacks/react.csv`

Data is layered by responsibility, not file type:

- Design knowledge: products, styles, colors, fonts
- Decision knowledge: reasoning
- Implementation knowledge: stacks

## Runtime Architecture

### 2. Generic Retrieval Core: One BM25 Primitive for Every Domain

The core of `core.py` is simple and clean:

1. Register domains in `CSV_CONFIG`
2. Load tables through `_load_csv()`
3. Use BM25 uniformly through `_search_csv()`
4. Query domains through `search()`
5. Query stacks through `search_stack()`

Evidence:

- `scripts/core.py:17`
- `scripts/core.py:166`
- `scripts/core.py:221`
- `scripts/core.py:243`

The lesson is not BM25 itself, but:

- One shared search primitive
- Variations represented in configuration
- Scripts concerned only with which table, which search columns, and which output columns

Tables can grow without a separate logic implementation for each one.

Excerpt:

```python
CSV_CONFIG = {
    "style": {
        "file": "styles.csv",
        "search_cols": [...],
        "output_cols": [...]
    },
    "color": {
        "file": "colors.csv",
        "search_cols": [...],
        "output_cols": [...]
    },
}
```

Our current implementation differs materially. `webnovel-writer/scripts/reference_search.py` still uses **globally hardcoded fields**, not per-domain registration. These Chinese field identifiers are retained literally:

```python
_SEARCH_FIELD_WEIGHTS = {
    "意图与同义词": 4,
    "关键词": 3,
    "核心摘要": 2,
    "详细展开": 1,
}

_CONTENT_COLUMNS = [
    "技法名称", "桥段名称", "人设类型", ...
]
```

The accurate mapping is therefore not simply `core.py -> reference_search.py`, but:

- `core.py -> reference_search.py + a not-yet-existing CSV_CONFIG registry layer`

### 3. Automatic Domain Detection: Decide What Kind of Knowledge to Search

`detect_domain()` uses a keyword table to infer the domain and choose the default search.

Evidence:

- `scripts/core.py:198`
- `scripts/core.py:202`
- `scripts/core.py:216`

Simple but useful:

- Callers need not always name a table explicitly
- Natural-language questions are first classified into knowledge domains
- Then they enter unified retrieval

For our system, this corresponds to:

- Genre-input routing
- Mapping task intent to knowledge tables
- Selecting tables for different prewrite steps

### 4. Higher-Level Aggregator: Retrieve, Reason, Then Assemble

`design_system.py` is the skill's real center.

Sequence:

1. Search `product`
2. Derive a category from the result
3. Find its reasoning rule in `ui-reasoning.csv`
4. Search multiple domains using `style_priority`
5. Select the best style / color / typography / landing entries
6. Assemble one `design_system` dictionary

Evidence:

- `scripts/design_system.py:51`
- `scripts/design_system.py:64`
- `scripts/design_system.py:88`
- `scripts/design_system.py:163`
- `scripts/design_system.py:197`

This sits above plain `reference_search`. It offers:

- Routing
- Adjudication
- Priorities
- One final output object

It is close to a lightweight contract generator.

## Persistence Architecture

### 5. Master + Overrides: Hierarchical Sources of Truth

Generated design systems can be persisted as:

- `design-system/<project>/MASTER.md`
- `design-system/<project>/pages/<page>.md`

Evidence:

- `scripts/search.py:13`
- `scripts/design_system.py:561`
- `scripts/design_system.py:589`
- `scripts/design_system.py:612`
- `scripts/design_system.py:886`

The pattern is significant:

- `MASTER.md` is the global source of truth
- `pages/*.md` records only local deviations
- Overrides are explicit, not implicit concatenations

This is structurally similar to Story System:

- `MASTER_SETTING` ≈ `MASTER.md`
- `VOLUME / CHAPTER / REVIEW contract` ≈ `page override`

The underlying idea is not UI-specific:

- Establish one master source
- Allow local overrides
- Make every override explicit

## Distribution and Platform Adaptation

### 6. Separate Platform Metadata from Skill Content

`templates/platforms/*.json` shows support for multiple agent platforms, for example:

- `templates/platforms/claude.json`
- `templates/platforms/codex.json`
- `templates/platforms/gemini.json`

These JSON files define:

- Installation root
- skillPath
- frontmatter
- title / description
- Whether to include quickReference

Evidence:

- `templates/platforms/claude.json`
- `templates/platforms/codex.json`
- `templates/platforms/gemini.json`

Three concerns are fully separated:

1. **Knowledge content**
2. **Runtime logic**
3. **Platform adapter shell**

This boundary is particularly worth adopting.

## Data Maintenance

### 7. Engineering Scripts Maintain Consistency Without Becoming Core Runtime Logic

`data/_sync_all.py`:

- Synchronizes `products.csv`, `colors.csv`, and `ui-reasoning.csv`
- Handles rename / remove / add
- Derives default color and reasoning rows

Evidence:

- `data/_sync_all.py:1`
- `data/_sync_all.py:63`
- `data/_sync_all.py:136`

This is an offline data-maintenance pipeline rather than runtime data patching.

However, adaptation requires care:

- **Adopt offline validation/synchronization**
- **Do not copy programmatic content generation**

Our constraints remain:

- `md -> csv` knowledge migration must be manual
- No automatic extraction, translation, or sentence splitting into the database

Keep:

- Schema validation
- Unique-ID validation
- Alias-coverage validation
- Route/rule-table consistency checks

Do not implement:

- Automatic bulk generation of story-knowledge entries from Markdown

## Most Transferable Ideas

### 8. Map the Architecture into Our Six-Layer Pipeline, Not the UI Data

To remain consistent with `story-system-evolution-spec.md`, use the six layers in `evolution-spec 6.1`:

```text
Knowledge Layer
    -> Reasoning Layer
        -> Contract Layer
            -> Runtime Assembly Layer
                -> Chapter Commit Layer
                    -> Projection Layer
```

`ui-ux-pro-max` mainly covers the first four, plus persistent truth in `MASTER.md + page override`.
Our story system additionally needs Chapter Commit and Projection because knowledge evolves with chapter execution.

More accurate mapping:

| `evolution-spec` layer | `ui-ux-pro-max` counterpart | `webnovel-writer` current / target | Completion |
|------|------|------|------|
| `Knowledge Layer` | `products.csv`, `styles/colors/...`, stack tables | Base, dynamic, and routing tables in `references/csv` | Basic structure exists: 7 rule tables, routing table, README schema |
| `Reasoning Layer` | `CSV_CONFIG + detect_domain()` in `core.py`; reasoning rules in `design_system.py` | `题材与调性推理.csv`, `StorySystemEngine._route()`, future explicit `CSV_CONFIG` and reasoning config | Partial: routing and engine decisions exist, not yet extracted into explicit configuration |
| `Contract Layer` | Unified `design_system` object and `MASTER.md/pages/*.md` | `MASTER_SETTING / VOLUME_BRIEF / CHAPTER_BRIEF / REVIEW_CONTRACT / anti_patterns` | Main structure connected: `engine.build()` produces `MASTER/CHAPTER/ANTI`; `RuntimeContractBuilder` produces `VOLUME/REVIEW` |
| `Runtime Assembly Layer` | Page assembly using page override before MASTER | `context_manager(contract-first)` and runtime context assembly | Partial: runtime contracts are read, but the overall assembler is not fully consolidated around contract-first SSOT |
| `Chapter Commit Layer` | No full counterpart; no event-commit main pipeline | `CHAPTER_COMMIT` + `override ledger` | Wired, governance pending: `ChapterCommitService` generates commits, writes event logs, triggers amend proposals and projection writers; rejected/backlog handling is not fully closed |
| `Projection Layer` | No full counterpart; no state-projection chain | `state / index / summaries / memory / dashboard` | Wired, demotion pending: four projection-writer types exist, but legacy scattered/dual writes to state/index/memory are not fully demoted to projections |

For retrieval and aggregation specifically:

- `core.py` ≈ `reference_search.py + a not-yet-existing CSV_CONFIG registry`
- `design_system.py` ≈ `StorySystemEngine + story_system.py + RuntimeContractBuilder`

### 8.1 The Missing Piece Is Explicit, Reviewable Adjudication, Not an Aggregator

We already have:

- `题材与调性推理.csv`
- 7 rule tables
- `reference_search.py`
- `story_system_engine.py`

The system already aggregates. `story_system.py` connects `build -> persist story seed -> build runtime contracts -> persist runtime contracts`:

```python
contract = engine.build(...)
persist_story_seed(...)
volume_brief, review_contract = RuntimeContractBuilder(project_root).build_for_chapter(...)
persist_runtime_contracts(project_root, args.chapter, volume_brief, review_contract)
```

`StorySystemEngine.build()` directly produces `MASTER_SETTING` / `CHAPTER_BRIEF` / `anti_patterns`:

```python
return {
    "master_setting": {
        "meta": {"contract_type": "MASTER_SETTING"},
        ...
    },
    "chapter_brief": {
        "meta": {"contract_type": "CHAPTER_BRIEF"},
        ...
    },
    "anti_patterns": anti_patterns,
}
```

Together, `StorySystemEngine + RuntimeContractBuilder` already perform most route / aggregate / persist responsibilities.

The actual situation is:

- An aggregator exists
- Its decisions are scattered across engine code, CSVs, `context_manager.py`, and skill text
- They are not yet consolidated into an explicit, structured, reviewable, testable rule layer like `ui-reasoning.csv`

Decision logic remains scattered in:

- `story_system_engine.py`
- `context_manager.py`
- Skill text
- Experience-based prompts

Consolidate it into Python configuration or a dedicated reasoning table.

CSV is optional; **structure, reviewability, and testability are mandatory**.

### 8.2 Strengthen the Master + Override Model

Partly implemented already, but specifications should state firmly:

- `MASTER_SETTING` is global truth
- `VOLUME_BRIEF` is a volume-level deviation
- `CHAPTER_BRIEF` / `REVIEW_CONTRACT` are chapter-level deviations
- Accepted `CHAPTER_COMMIT` is postwrite factual truth

This follows the same principle as `MASTER.md + page override`.

One important distinction: `ui-ux-pro-max` has **two override levels**:

- `MASTER.md`
- `pages/*.md`

We have **four contract levels plus postwrite facts**:

- `MASTER_SETTING`
- `VOLUME_BRIEF`
- `CHAPTER_BRIEF`
- `REVIEW_CONTRACT`
- Accepted `CHAPTER_COMMIT`

A field can therefore be overridden at multiple levels, much more complex than “page override trumps master.”
Do not directly copy its precedence logic; design it together with the `override ledger` in `evolution-spec 8.5`.

### 8.3 Learn Registry-Based Configuration, Not Dataset Size

Build one registry identifying:

- Each table's responsibility
- Search columns
- Output columns
- Pitfall columns
- Base / dynamic / routing role
- Whether it may enter the contract main pipeline

This is our `CSV_CONFIG`.

First recognize that `reference_search.py` is currently only a **generic BM25 primitive**, not a registry layer.
Search and output columns are globally hardcoded, without domains:

```python
_SEARCH_FIELD_WEIGHTS = {
    "意图与同义词": 4,
    "关键词": 3,
    "核心摘要": 2,
    "详细展开": 1,
}
_CONTENT_COLUMNS = [...]
```

The next step is per-table/per-domain metadata registration above the search algorithm, not rewriting that algorithm.

### 8.4 Isolate Consumer Adapters

Do not expose CSV structures directly to every consumer.

Instead:

- `story-system` produces unified contracts
- `context-agent` / `webnovel-write` / `webnovel-query` / `dashboard` consume only contracts
- Platform/skill differences remain at consumer entry points

### 8.5 Context-Window Cost Is an Underestimated Difference

`ui-ux-pro-max` places CSV results directly into a prompt that fits one interaction. Our writing brief combines prior summaries, long-term memory, RAG clues, current state, reader signals, and other sources; context-agent research alone consumes substantial context.

The reasoning layer therefore cannot simply retrieve everything and reason afterward. It must consider:

- Which sources to query on demand during research rather than inject wholesale
- What information density the final brief should retain, rather than including every result
- Keeping reasoning rules themselves lightweight

This affects the weight of the reasoning layer: prefer lightweight configuration + on-demand routing, not five or six domain retrievals chained into one call as in `design_system.py`.

## What Not to Copy Directly

### 9.1 Automatic Data Generation

`_sync_all.py` programmatically derives some data. That can be acceptable for UI color data but not a story-knowledge base.

Retain these hard boundaries:

- Humans curate knowledge-entry content
- Scripts may validate, fill blanks, align, deduplicate, and check IDs
- No automatic content migration from Markdown

### 9.2 Domain Detection as Sole Truth

`detect_domain()` mainly uses keyword heuristics. This can work for UI queries, but a story system needs stronger precedence:

1. Explicit user genre / `.story-system` contract
2. `题材与调性推理.csv`
3. Alias / fallback
4. Heuristic inference last

This is **genre-routing precedence**, not the **runtime context-assembly precedence** in `evolution-spec 7.2`.
The latter, when contracts exist, is `chapter -> volume -> master -> 题材与调性推理.csv -> genre-profiles.md -> templates/genres/*.md`.

### 9.3 Platform Templates Must Not Dictate Knowledge Structure

The platform adapter must remain a shell, not determine CSV structure.

## Direct Requirements for the Next Specification

The next actionable specification should emphasize structure, not merely hundreds of additional CSV rows.

### 10.1 Establish Our `CSV_CONFIG`

Do not replace `references/csv/README.md`; define complementary responsibilities:

- `CSV_CONFIG`: Python registry consumed directly by runtime retrieval, routing, and contract injection
- `README.md`: Human-readable schema, data-entry conventions, and table boundaries
- Validation scripts: Keep column definitions, table roles, and prefix conventions aligned

The README already documents schemas, for example (literal Chinese field names retained):

```md
| `关键词` | Yes | High-weight trigger terms; multivalue fields use `|` consistently |
| `核心摘要` | Yes | Concise summary for high-weight retrieval and display |

### 命名规则.csv
| `命名对象` | Characters, book titles, locations, factions, techniques, props, etc. |
```

The choice is not README versus `CSV_CONFIG`:

- README speaks to humans
- `CSV_CONFIG` speaks to machines
- **Hard requirement**: CI validation must keep both aligned. Two schema definitions without automated checking will drift; this is mandatory, not optional.

At minimum define:

- Table / filename
- Role
- Search fields
- Output fields
- Pitfall fields
- Base / dynamic / routing classification
- Contract injection point
- Main-pipeline eligibility
- Corresponding README schema section

### 10.2 Define the `route -> reasoning -> rule tables -> contract` Pipeline

This is the most important transferable conclusion of the research.

### 10.3 Close the Research–Entry–Validation–Acceptance Loop for CSV

The loop:

- Human topic selection
- Human synthesis
- CSV entry
- Schema / alias / route checks
- Sampled contract validation

### 10.4 Demote Skills / Agents / Dashboard to Consumers

Consume unified contracts rather than independently assembling knowledge.

## Final Assessment

The success of `ui-ux-pro-max` demonstrates:

> A strong skill is not a longer manual; it is clearly layered knowledge, retrieval, reasoning, persistence, and consumer boundaries.

For `webnovel-writer`, the lesson is not to:

- Write longer skill text
- Accumulate more disconnected Markdown
- Let every entry point decide independently which references to load

Instead:

- Use `references/csv` as the `Knowledge Layer` (`evolution-spec 6.1`, `12.3`)
- Use `story_system + explicit reasoning configuration` for the `Reasoning / Contract Layer` (`evolution-spec 6.1`, `7`)
- Use `.story-system` for primary truth and overrides (`evolution-spec 7`, `8.5`)
- Use `CHAPTER_COMMIT + override ledger + canonical event log` for runtime evolution (`evolution-spec 9`, `10`)
- Let skills / agents / dashboard consume unified outputs and projection views (`evolution-spec 9.4`, `12`)

These are the ideas and architecture worth transferring.
