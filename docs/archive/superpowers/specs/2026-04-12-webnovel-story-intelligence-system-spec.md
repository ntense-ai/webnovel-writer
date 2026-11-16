# Webnovel Writer Story Intelligence System Target-State Refactoring Specification

> Date: 2026-04-12
> Status: Draft v2
> Purpose: Ideal target-state architecture blueprint

---

## 1. Document Purpose

### 1.1 Problems This Specification Addresses

`webnovel-writer` already provides:

- Entry-based knowledge retrieval through `references/csv/`
- Methodology and workflow constraints through `references/*.md`
- Runtime state / index / memory / context capabilities through `scripts/data_modules/`
- Initialization, planning, writing, and review entry points through `skills/webnovel-*`

More precisely, the current system already has:

- Step-based `L0 / L1 / L2` loading
- A dual-track reference system combining mandatory Markdown reading and CSV retrieval
- Partially developed aggregation through `context_manager + genre_*`

The real gaps are not on-demand reference reading, but:

1. No unified **aggregation middle layer** combining genre, pacing, plot beats, reader turn-offs, characters, and special advantages into a system
2. `reference_search.py` returns isolated entries rather than stable story-system contracts
3. `context_manager / genre_*` have not evolved into persistent `Story Contract` structures
4. No stable `Master + Overrides` structure for global settings and local chapter requirements

The goal is not more retrieval, but a `Story Intelligence System` that:

- Reasons first
- Aggregates next
- Persists next
- Finally supplies contracts to skills

### 1.2 Relationship to Existing Specifications

Existing documents:

- `2026-04-09-skills-restructure-and-reference-gaps.md`
- `2026-04-12-story-system-pro-max-retrofit-spec.md`

Their respective roles:

- `2026-04-09`: boundaries between `skills / references / scripts` and reference gaps
- `2026-04-12 retrofit`: a conservative `story_system` addition without major pipeline changes

This specification differs:

- It **does not require compatibility with legacy entry points**.
- It **does not follow a minimum-change principle**.
- It describes the project's **ideal refactoring target**.

In short:

- The retrofit specification explains how to add capabilities safely.
- This specification asks what the optimal architecture would be if redesigned.

### 1.2.1 Reuse and Replacement Boundaries With the Retrofit Specification

To prevent conflicting implementation guidance:

#### Directly Reusable

- Common CSV column contract
- `reference_search.py` as a low-level primitive
- `.story-system/` as the persistence directory
- Explicit negative fields take priority in anti-pattern extraction
- `StorySystemDict` as the seed structure for phase 1 JSON contracts

#### Superset Extensions

- Extend two persistence layers to `Master / Volume / Chapter`.
- Expand `StorySystemDict` into a contract family rather than one aggregated result.
- Upgrade skills from direct reference reading to contract-first consumption plus local on-demand loading.
- Explicitly move `state / memory / index` into the runtime factual layer.

#### Replacement Decisions

- `story_system.py` becomes a frontline hub, not an optional extra script.
- `genre-profiles.md` stops being the central configuration authority.
- `templates/genres/*.md` stops being the primary genre knowledge source.

Conflict-resolution priority:

1. For phase 1 engineering implementation, follow the retrofit specification.
2. For phase 2 and later refactoring targets, follow this specification.

### 1.3 Reference Architecture

Borrow the core pipeline of `ui-ux-pro-max-skill`, not its filenames:

1. Multi-domain data repository
2. Reasoning engine
3. Aggregator
4. Anti-pattern aggregation
5. Stable output contracts
6. Contract-centered skill consumption

The useful lesson is this system pipeline, not merely adding CSV files.

---

## 2. Design Conclusions

### 2.1 One-Sentence Conclusion

Replace:

- `Markdown references + CSV search + manual skill assembly`

With:

- `Reasoning Layer + Multi-domain Knowledge Layer + Story System Generator + Persistence Contracts + Skill Runtime`

### 2.2 Core Assessments

#### Assessment 1: CSV Should Be the Primary Knowledge Layer

The existing entry-based direction in `references/csv/` should become:

- Primary knowledge layer
- Primary retrieval layer
- Primary rule layer

Not supplementary material.

#### Assessment 2: Markdown Should Become the Methodology Layer

Keep methodology, review rules, AI-style avoidance, and workflow standards in Markdown.

Do not use Markdown directly as:

- The genre configuration center
- Primary story-system settings
- The primary skill-input source

#### Assessment 3: Skills Should Not Assemble Scattered References

The ideal `webnovel-init / plan / write / review`:

- Does not manually assemble multiple references
- Does not decide which tables and Markdown files to search first
- Consumes generated story contracts

“Contracts only” does not prohibit all step-based reference loading. It means:

- Global settings, genre tone, red lines, and system boundaries come primarily from contracts.
- Local writing techniques, scene patterns, naming, typesetting, and review standards may still load on demand per step.

#### Assessment 4: Existing data_modules Remain as Runtime Infrastructure

These remain valuable:

- `state.json`
- `memory_contract`
- `index.db / vectors / bm25`
- `context_manager`
- `query_router`

Their role shifts from main-workflow assembly to:

- Runtime facts
- Retrieval evidence
- Writing execution support

### 2.3 Contracts Versus Progressive Disclosure

This specification preserves the `2026-04-09` philosophy of progressive disclosure, dual tracks, and on-demand loading, while redefining consumption boundaries.

#### Contract-First Information

- Genre reasoning results
- Global tone and pacing promises
- `anti_patterns`
- `system_constraints`
- Volume/chapter objectives
- Override ledger

Shared characteristics:

- Global impact
- Must remain consistent across steps
- Unsuitable for repeated ad hoc skill assembly

Additional runtime boundary:

- Skills consume the **final resolved state** by default.
- The full override ledger is normally **audit/debug/dashboard data**.
- Writing prompts receive only chapter-relevant override summaries, not the full historical ledger.

#### On-Demand Reference Information

- Writing techniques
- Scene patterns
- Naming rules
- Dialogue voice
- Typesetting standards
- Polishing and anti-AI corrections
- Review schema and blocking-override rules

Shared characteristics:

- Strong dependence on a particular step
- Clear triggers
- Local execution manuals rather than global story contracts

The target is therefore not contracts replacing every reference:

- Contracts own global system information.
- Step-bound references retain local execution knowledge.

---

## 3. Goals and Non-Goals

### 3.1 Goals

Eight target-state goals:

1. Unified genre reasoning
2. Unified multi-domain knowledge repository
3. Unified story-system generator
4. Unified anti-pattern aggregation
5. Unified `Master / Volume / Chapter` contracts
6. Unified `.story-system/` persistence
7. Skills consuming contracts rather than assembling references directly
8. Existing state / index / memory pipelines retained as runtime facts

### 3.2 Non-Goals

This specification does not require:

1. Complete compatibility with old CLI invocations
2. `reference_search.py` remaining a frontline entry point
3. `genre-profiles.md` remaining the central configuration authority
4. Every old template retaining its original role
5. Tests for every knowledge entry

### 3.3 Knowledge-Migration Boundaries

Hard rules:

1. AI-like-writing detection, de-AI phrasing, and polishing replacement rules do not enter CSV.
2. Keep them in separate Markdown files.
3. Knowledge migration is manually curated and entered.
4. Do not write scripts that automatically extract Markdown into CSV entries.

This ban concerns knowledge-content migration, not ordinary engineering scripts.

---

## 4. Target Architecture

### 4.1 Layers

Five layers:

1. `Reasoning Layer`
2. `Knowledge Layer`
3. `Contract Layer`
4. `Persistence Layer`
5. `Skill Runtime Layer`

### 4.2 Relationships

```text
User intent / genre requirements
        ↓
Reasoning Layer
        ↓
Knowledge Layer
        ↓
Story System Generator
        ↓
Contract Layer
        ↓
Persistence Layer
        ↓
Skill Runtime Layer
        ↓
Prose / outlines / review / state persistence
```

### 4.3 Recommended Layout

```text
${CLAUDE_PLUGIN_ROOT}/
├── story_system/
│   ├── data/
│   │   ├── reasoning/
│   │   ├── rules/
│   │   ├── tropes/
│   │   ├── characters/
│   │   ├── pacing/
│   │   └── naming/
│   ├── engine/
│   │   ├── search_engine.py
│   │   ├── reasoning_engine.py
│   │   ├── aggregator.py
│   │   ├── anti_pattern_engine.py
│   │   ├── contract_builder.py
│   │   ├── renderer.py
│   │   └── persistence.py
│   ├── runtime/
│   │   ├── memory_bridge.py
│   │   ├── state_bridge.py
│   │   ├── index_bridge.py
│   │   └── review_bridge.py
│   ├── templates/
│   │   ├── master_setting.md.j2
│   │   ├── volume_brief.md.j2
│   │   ├── chapter_brief.md.j2
│   │   ├── anti_patterns.md.j2
│   │   └── review_contract.md.j2
│   └── cli.py
├── references/
│   ├── csv/
│   ├── shared/
│   ├── outlining/
│   └── review/
├── skills/
└── scripts/

${PROJECT_ROOT}/
├── .webnovel/
└── .story-system/
```

Notes:

- This is the **plugin runtime-directory model**, not the source-repository layout.
- The development repository produces the plugin; it does not determine runtime contract persistence paths.
- `CLAUDE_PLUGIN_ROOT` holds installed code, skills, scripts, and references.
- `PROJECT_ROOT` is the actual book-project directory containing `.webnovel/state.json`.
- `.story-system/` belongs under `PROJECT_ROOT`, never `CLAUDE_PLUGIN_ROOT`.
- `story_system/` is the new frontline hub.
- Existing `scripts/reference_search.py` and `scripts/data_modules/` may remain without being the design center.
- The engine files express target responsibilities; day 1 need not create seven separate files.

### 4.4 Initial Implementation Granularity

Clear responsibilities do not require one file per responsibility immediately.

Recommended:

1. Phase 1 may combine them into `search_reasoning.py + contract_runtime.py + persistence.py`.
2. Phase 2 can split them further by responsibility.

Define layers first; refine file granularity progressively.

---

## 5. Reasoning Layer

### 5.1 Responsibility

The system's reasoning layer converts vague creative intent into executable constraints.

It does not answer how to write one technique. It answers:

- What genre fundamentally defines the book?
- What is its core reader promise?
- Which payoffs take priority?
- Should pacing be fast or restrained?
- Which reader turn-offs are forbidden?
- Which knowledge domains should be retrieved first?

### 5.2 Core Table

Add the core routing table:

- Filename: `题材与调性推理.csv`
- Chinese name: `题材与调性推理` (genre and tone reasoning)

### 5.3 Suggested Fields

The table still follows the existing common CSV contract. These are **additional dedicated columns**:

| Field | Description |
|-------|-------------|
| `题材/流派` | Primary genre |
| `中文名` | Standard human-readable name |
| `题材别名` | Slang, common names, platform terminology |
| `核心调性` | Underdog rise, intense romantic tension, restrained buildup and release, uncanny pressure, etc. |
| `节奏策略` | Golden opening chapters, slow buildup, continuous payoffs, milestone eruptions, etc. |
| `主爽点` | Core payoff type |
| `辅助爽点` | Secondary payoffs |
| `冲突引擎` | How conflict is generated |
| `适配人设` | Recommended character frameworks |
| `适配金手指` | Recommended special-advantage or setting types |
| `适配桥段` | Common plot-beat directions |
| `强制禁忌/毒点` | Genre-level red lines |
| `推荐基础检索表` | Base domains prioritized during system generation |
| `推荐动态检索表` | Dynamic domains prioritized for volume/chapter briefs |
| `默认查询词` | Query expansions for vague input |

### 5.4 Genre Reasoning Principles

Order:

1. Identify the primary genre.
2. Identify secondary genres.
3. Identify the core promise.
4. Fix tone.
5. Fix pacing.
6. Fix reader turn-offs.
7. Generate the multi-domain retrieval plan.

Support primary/secondary genres, not only a single label.

### 5.5 Multi-Label Reasoning

Webnovels often combine genres:

- Cyberpunk + cosmic horror
- Cultivation + livestreaming
- Urban superpowers + romantic rivalry

The reasoning engine must support weighted multi-label fusion, not simple Top 1 matching.

Rules:

1. Identify the primary genre first.
2. Identify secondary genres next.
3. Primary genre governs core tone; secondary genres add flavor without taking over.
4. Union mandatory prohibitions/turn-offs.
5. Rank main payoffs by the primary genre; secondary payoffs may come from secondary genres.
6. Merge base/dynamic retrieval plans by weight rather than overwriting with one row.

In short:

- Tone has primary and secondary priorities.
- Turn-offs use a union.
- Retrieval plans must be fused.

Implement these rules, not merely describe them conceptually.

### 5.6 Reasoning Engine Boundaries

Avoid both extremes:

- Pure rules cannot understand all literary semantics.
- Genre recognition, tone fusion, and turn-off decisions must not all become an LLM black box.

Use three layers:

1. `L0 Deterministic Router`
2. `L1 Deterministic Fusion`
3. `L2 LLM Classifier / Synthesizer`

#### L0: Deterministic Routing

Handles:

- Alias normalization
- Explicit tag extraction
- BM25 / keyword candidate retrieval
- Initial confidence estimation

Reduce natural-language intent to a **candidate set**, not a final literary judgment.

#### L1: Deterministic Fusion

Handles:

- Weighted primary/secondary genre candidates
- Turn-off unions
- Base retrieval-plan fusion
- An offline-capable baseline contract

Even without an LLM, clear input produces a usable, conservative `MASTER`.

#### L2: LLM Classification / Fusion

Enable only for:

- Low-confidence input
- Clear genre hybrids
- Highly ambiguous tone descriptions
- Candidate scores too close for reliable adjudication

The LLM does not improvise freely. It:

- Classifies or reranks within the candidate set
- Explains why a particular fusion is preferable
- Produces strict structured JSON

Validate locally against the schema; fall back to L1 if validation fails.

Defaults:

- Operates offline
- Produces usable `MASTER` without an LLM
- Uses the LLM for semantic gaps and ambiguous fusion, never to bypass rules and directly dictate contracts

Fallback strategy:

1. High-confidence L0 + L1 output needs no LLM call.
2. Low-confidence output first exposes candidate genres and conflicts.
3. If LLM assistance is enabled, request structured fusion suggestions based only on those candidates.
4. Discard invalid LLM output and use the deterministic baseline.

Keep cost, latency, availability, explainability, and testability within acceptable engineering bounds.

---

## 6. Knowledge Layer

### 6.1 Knowledge Categories

Separate three categories rather than mixing everything:

1. `Reasoning Tables`
2. `Rule Tables`
3. `Methodology Docs`

### 6.2 Reasoning Tables

Global reasoning and routing:

| Filename | Name | Role |
|----------|------|------|
| `题材与调性推理.csv` | Genre and tone reasoning | Genre routing and global orchestration |

### 6.3 Rule Tables

Structured rules and entry-based knowledge:

| Filename | Name | Role |
|----------|------|------|
| `命名规则.csv` | Naming rules | People, places, factions, techniques, etc. |
| `场景写法.csv` | Scene writing | Combat, dialogue, conflict, and plot-scene patterns |
| `写作技法.csv` | Writing techniques | Techniques and pitfalls |
| `桥段套路.csv` | Plot tropes | Tropes, setup, reversals, variations |
| `人设与关系.csv` | Characters and relationships | Archetypes, interactions, prohibitions |
| `爽点与节奏.csv` | Payoffs and pacing | Pacing phases, emotional orchestration, failure modes |
| `金手指与设定.csv` | Special advantages and settings | Advantages, world rules, limits, costs |

Suggested future tables:

| Filename | Name | Role |
|----------|------|------|
| `冲突设计.csv` | Conflict design | Triggers, escalation chains, resolutions |
| `反派机制.csv` | Antagonist mechanisms | Logic, hierarchy, defeat patterns, prohibitions |

### 6.4 Methodology Docs

Retain these in Markdown, not CSV:

- `review-schema.md`
- `reading-power-taxonomy.md`
- `shared/core-constraints.md`
- `webnovel-write/references/anti-ai-guide.md`
- `webnovel-write/references/polish-guide.md`
- `webnovel-write/references/style-adapter.md`

They describe processes and methodology, not retrieval entries. Forcing them into CSV would degrade expression.

---

## 7. Contract Layer

### 7.1 Core Idea

Skills should not directly consume scattered CSV results, multiple Markdown references, or isolated templates. They consume standard contracts.

### 7.2 Contract Types

At least five:

1. `MASTER_SETTING`
2. `VOLUME_BRIEF`
3. `CHAPTER_BRIEF`
4. `ANTI_PATTERNS`
5. `REVIEW_CONTRACT`

### 7.3 Responsibilities

#### MASTER_SETTING

Stable book-wide settings:

- Genre and tone
- Protagonist/core-character baselines
- World rules and special-advantage boundaries
- Global pacing strategy
- Global turn-offs

#### VOLUME_BRIEF

Volume objectives:

- Core conflict
- Payoff targets
- Antagonist tier
- Key plot beats
- Pacing waveform

#### CHAPTER_BRIEF

Chapter execution requirements:

- Objective
- Plot beats
- Scene strategy
- Emotional expectations
- Prohibitions

#### ANTI_PATTERNS

Aggregate genre-, plot-, character-, and pacing-level turn-offs into explicit red lines.

#### REVIEW_CONTRACT

Tell review:

- What must be checked in this chapter/volume
- Which red lines take priority
- Which risks are genre-specific

### 7.4 Dual Artifacts and a Single Source of Truth

A contract may have both Markdown and JSON artifacts, but:

- `JSON` is the sole source of truth.
- `Markdown` is a read-only rendering of JSON.

Markdown serves people; JSON provides stable program/skill input. Editable Markdown would create dual sources of truth.

Hard rules:

1. Persist changes to JSON first, then render Markdown.
2. Mark Markdown headers `GENERATED FILE / DO NOT EDIT`.
3. Skills, runtime, dashboard, and tests consume JSON only as truth.
4. Manual amendments use CLI / Dashboard / explicit JSON editing, never automatic reverse synchronization from Markdown.

Manual Markdown edits are unsupported and may be overwritten during the next render.

### 7.4.1 Markdown Migration Decision Versus the Retrofit Specification

Resolve the difference from retrofit markers explicitly.

#### Phase 1

- Follow the retrofit specification.
- If Markdown has `<!-- STORY-SYSTEM:BEGIN -->` / `END` generated blocks, update only their contents.
- Temporarily retain manual notes outside markers.

#### Phase 2 and Later

- Follow this specification.
- Rebuild read-only Markdown entirely from JSON.
- Phase 1 marker compatibility may be removed.

In every phase:

- JSON remains the sole source of truth.
- Manual notes outside markers are not contract truth.
- Skills/runtime/tests never use Markdown as authoritative input.

### 7.5 JSON Contract Validation

Stable skill input requires structural validation, not merely best-effort correct JSON.

Recommended:

1. Explicit schemas for `MASTER_SETTING / VOLUME_BRIEF / CHAPTER_BRIEF / REVIEW_CONTRACT`
2. `Pydantic` or equivalent validation
3. Local validation after generation and before persistence
4. No superficially successful but structurally unstable contracts when validation fails

Minimum requirements:

- `anti_patterns` is always a list.
- `overrides` is always a structured object.
- `locked / append_only / override_allowed` is machine-readable.
- `lock_policy` is machine-readable.
- Defaults are stable, not alternating between empty strings and empty arrays.

This is foundational contract integrity, not optional extra testing.

### 7.5.1 Schema Version and Compatibility

Every contract JSON includes at least:

- `schema_version`
- `contract_type`
- `generator_version`

Rules:

1. Use an explicit version string, such as `story-system/v1`.
2. Readers validate the version before choosing direct reading, an explicit migrator, or an error requiring manual upgrade.
3. Never silently ignore fields under an incompatible schema.
4. Phase 1 contracts derived from `StorySystemDict` must also declare a version.

Otherwise older contracts can silently lose fields under phase 2 code or fail validation without a clear cause.

### 7.6 JSON Contract Baseline

Do not reinvent contracts from scratch:

1. Phase 1 reuses retrofit `StorySystemDict`.
2. Phase 2 expands it into `MASTER / VOLUME / CHAPTER / REVIEW / ANTI_PATTERNS` contracts.

Minimum fields follow.

#### `MASTER_SETTING.json`

- `meta`
- `genre_reasoning`
- `core_rules`
- `anti_patterns`
- `system_constraints`
- `contracts`
- `overrides`

#### `VOLUME_BRIEF.json`

- `meta`
- `volume_goal`
- `selected_tropes`
- `selected_pacing`
- `selected_scenes`
- `anti_patterns`
- `system_constraints`
- `overrides`

#### `CHAPTER_BRIEF.json`

- `meta`
- `chapter_goal`
- `scene_strategy`
- `hook_strategy`
- `must_cover`
- `anti_patterns`
- `system_constraints`
- `overrides`

Distinguish:

- `anti_patterns`: explicit prohibitions
- `system_constraints`: capability boundaries, world rules, numerical limits

Practical classification:

- Violations that directly feel alienating, story-breaking, or artificially foolish to readers belong in `anti_patterns`.
- Violations that first break setting consistency, logic, or numerical balance belong in `system_constraints`.

Examples:

- A special advantage usable only three times daily is a system constraint.
- A face-slapping payoff that requires an antagonist to become implausibly stupid is an anti-pattern.

#### `REVIEW_CONTRACT.json`

- `meta`
- `must_check`
- `blocking_rules`
- `genre_specific_risks`
- `anti_patterns`
- `system_constraints`
- `review_thresholds`
- `overrides`

Definitions:

- `must_check`: priority checks for this chapter/volume
- `blocking_rules`: rules whose violation directly blocks approval
- `genre_specific_risks`: high-risk genre-specific issues
- `review_thresholds`: minimum thresholds or blocking conditions by dimension

### 7.6.1 Mapping `StorySystemDict` Into the Contract Family

Minimum mapping to avoid ambiguity in phase 1→2 migration:

| `StorySystemDict` Field | Phase 2 Destination | Meaning |
|------------------------|---------------------|---------|
| `meta` | `MASTER_SETTING.meta` | Generation source, query, timestamp, and other metadata |
| `route` | `MASTER_SETTING.genre_reasoning` | Genre routing, candidates, match evidence |
| `master_constraints` | `MASTER_SETTING.core_rules` + `MASTER_SETTING.system_constraints` | Split genre tone, world boundaries, and hard constraints into core rules and system boundaries |
| `base_context` | `MASTER_SETTING.contracts.base_context_seed` | Base-table results as book-wide seed context |
| `dynamic_context` | `VOLUME_BRIEF.selected_*` + `CHAPTER_BRIEF.scene_strategy / hook_strategy / must_cover` | Split dynamic context into volume choices and chapter execution requirements |
| `anti_patterns` | Each contract's `anti_patterns` + derived `anti_patterns.json` | Put entry/genre turn-offs into contracts, then generate an aggregated runtime view |
| `override_policy` | `MASTER_SETTING.contracts.override_policy` | Field override rules and default policies |
| `source_trace` | Each contract's `meta.source_trace` or audit section | Debugging, audit, and traceability |

This does not freeze final field names. It establishes that:

- Phase 1 flat aggregation does not simply disappear.
- It is split and persisted into finer-grained contracts.
- Implementation must not guess field ownership semantically.

---

## 8. Persistence Layer

### 8.1 Directory Convention

Create under the actual book-project `PROJECT_ROOT`:

```text
PROJECT_ROOT/
├── .webnovel/
└── .story-system/
    ├── MASTER_SETTING.md
    ├── MASTER_SETTING.json
    ├── anti_patterns.md
    ├── anti_patterns.json
    ├── volumes/
    │   ├── volume_001.md
    │   ├── volume_001.json
    │   └── ...
    └── chapters/
        ├── chapter_001.md
        ├── chapter_001.json
        └── ...
```

Additional rules:

- `*.json` is contract truth.
- `*.md` is rendered output.
- Renderers support full Markdown reconstruction from JSON.
- Skills/agents start at `WORKSPACE_ROOT` but resolve the actual `PROJECT_ROOT` before reading/writing `.story-system/`.

### 8.1.1 Standalone `ANTI_PATTERNS` Versus Contract Fields

Avoid dual truth:

1. `anti_patterns` inside `MASTER_SETTING / VOLUME_BRIEF / CHAPTER_BRIEF` are the **layered sources of truth**.
2. Root `.story-system/anti_patterns.json` is a **derived aggregate view**.
3. `anti_patterns.md` renders only from that aggregate.

Responsibilities:

- `MASTER_SETTING.json.anti_patterns`: book-wide red lines
- `VOLUME_BRIEF.json.anti_patterns`: volume additions
- `CHAPTER_BRIEF.json.anti_patterns`: chapter additions
- `anti_patterns.json`: flatten currently visible levels for runtime and audit use

On conflict, layered contract fields win. Recompute the aggregate; never promote it into the source of truth.

### 8.1.2 Naming and Version Control

File names:

- Zero-padded volumes: `volume_001.json`
- Zero-padded chapters: `chapter_001.json`
- Human-readable titles belong in `meta.title`, not filenames.

Version control:

- Track `.story-system/*.json` and their primary Markdown renderings in Git by default.
- These are project contracts, not temporary caches.
- Debug diffs, health reports, and temporary audit snapshots may be ignored.

### 8.2 Override Rules

Fixed precedence:

1. `chapter_xxx`
2. `volume_xxx`
3. `MASTER_SETTING`

Overrides must be recorded explicitly, not silently substituted.

### 8.2.1 Three-Level Override Matrix

Distinguish field types rather than always letting lower layers overwrite higher ones:

| Field Type | Master → Volume | Volume → Chapter | Meaning |
|------------|-----------------|------------------|---------|
| `locked` | No direct override by default | No direct override by default | Whether `amend-*` may change it depends on `lock_policy` |
| `append_only` | Add, never delete | Add, never delete | Final value is the union |
| `override_allowed` | May override with a recorded reason | May override with a recorded reason | Nearest layer wins |

Additional rules:

1. `Master.locked` applies to both Volume and Chapter.
2. `Volume.locked` applies only to chapters in that volume.
3. Chapter cannot directly unlock upstream fields.
4. `append_only` always merges Master + Volume + Chapter.
5. `override_allowed` uses the nearest layer while retaining an override ledger.

### 8.2.1.1 `lock_policy`

To avoid locking out legitimate story reversals, every `locked` field also has:

1. `system_locked`
2. `user_locked`
3. `story_locked`

Meanings:

- `system_locked`: schema and baseline operating constraints; downstream contracts cannot change them.
- `user_locked`: explicit user hard constraints; no automatic runtime modification, only upstream amendment after explicit user confirmation.
- `story_locked`: stable core story settings; Volume/Chapter cannot directly override them, but an `amend-master / amend-volume` proposal plus human confirmation may revise upstream contracts.

Thus locks remain, but with different strengths. Story reversals proceed through amendment proposals and upstream changes, not Chapter breaking a lock directly.

### 8.2.2 Conflict-Override Records

When chapter or volume conflicts with an upstream contract, generate explicit override markers rather than keeping only the final value.

Suggested Markdown:

- `Chapter pacing: [Override from MASTER: slow buildup -> explosive climax]`
- `Chapter beat: [Override from VOLUME: probing confrontation -> immediate face-slapping payoff]`

Minimum JSON record:

- `field`
- `base_value`
- `override_value`
- `source_level`
- `reason`

The purpose is not presentation aesthetics, but to tell models and scripts that a state transition occurred through controlled override, not random drift.

### 8.2.3 Override Ledger Consumption Boundaries

Retain the ledger without injecting it wholesale into writing prompts.

Two modes:

1. `audit/debug mode`
2. `runtime prompt mode`

#### audit/debug mode

Full-ledger access for:

- Dashboard audits
- Contract diffs
- Health checks
- Troubleshooting

#### runtime prompt mode

Expose only:

- Current effective field values
- Overrides directly relevant to this chapter/volume
- Brief necessary reasons

By default, prohibit:

- Full historical ledgers in `webnovel-write` prompts
- Repeated injection of overrides from dozens of chapters earlier

Otherwise tokens are wasted, noise increases, and the model attends to historical explanations instead of current execution constraints.

### 8.2.4 Override Reasons

Whenever an `override_allowed` field changes, attach a `reason` where possible.

Suggested tags:

- `ARC_ESCALATION`
- `CHAPTER_PAYOFF`
- `TWIST_REQUIREMENT`
- `POV_SWITCH`
- `CONFLICT_INTENSIFICATION`

These are suggestions, not a closed enum. Allow `reason_tag + free_text`.

Plain `free_text` is also allowed. An override without a reason is low-confidence.

### 8.3 Field Types

Every field is marked:

1. `locked`
2. `append_only`
3. `override_allowed`

Examples:

- World rules: `locked`
- Global turn-offs: `append_only`
- Chapter plot-beat strategy: `override_allowed`

Without field-level rules, local overrides become uncontrolled.

Additional rules:

- `locked` requires `lock_policy`.
- Missing `lock_policy` defaults to `story_locked`; never silently relax it.
- `append_only` permits additions, never deletion of upstream constraints.

This is especially important for `anti_patterns`, world-rule limitations, and special-advantage boundaries. Letting lower layers delete them removes contractual rigor.

Phase 1 deduplication must also be explicit:

1. No automatic semantic merging for `append_only` by default.
2. Normalize string-list deduplication keys by trimming outer whitespace, collapsing repeated whitespace, and normalizing common full-width/half-width separator differences.
3. Explicitly define deduplication keys for structured objects; otherwise retain them and flag for audit.
4. For `anti_patterns`:
   - Deduplicate identical text.
   - Keep semantically similar but differently worded items in phase 1.
   - If only numerical thresholds differ, such as 300 versus 200 Chinese characters, never silently discard the stricter version.

Prefer overlapping items over weakening upstream red lines. More aggressive semantic deduplication requires later explicit rules or manual audit.

### 8.4 Persistence Entry Points

The **stable interface** visible to skills, agents, and tests must live under unified `webnovel.py`, not a parallel mainline CLI.

Target CLI:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" story-system generate-master --genre "修仙退婚流"
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" story-system generate-volume --title "拍卖会卷"
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" story-system generate-chapter --query "拍卖会打脸"
```

If retained, `story_system/cli.py` is only a local development/debugging or internal wrapper entry point, not an external command depended upon by skills/prompts.

Reasons:

- The project already has unified CLI, project_root resolution, workspace pointers, a registry, and prompt-integrity checks.
- A separate public CLI would immediately split skills, tests, dashboard, and documentation.
- Expose only `webnovel.py story-system ...` as the stable public interface.

Argument rules:

- Prefer named arguments over space-containing positional arguments.
- Reduce quoting differences across PowerShell / Bash / zsh.
- Skill-facing command examples follow the same rule.

Reserve explicit amendment entry points:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" story-system amend-master --event "主角获得第二核心金手指"
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" story-system amend-volume --volume 2 --event "阵营关系反转"
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" story-system refresh-chapter --chapter 15
```

These do not recalculate arbitrarily. They:

1. Read current contracts.
2. Read major runtime events.
3. Make controlled changes only to permitted fields.
4. Record amendment reasons and timestamps.

### 8.4.1 Idempotency and Overwrite Policy

Generation and amendment commands obey idempotency rules.

#### `generate-*`

1. Missing target: create it.
2. Existing target, identical input fingerprint: return it without overwriting.
3. Existing target, different fingerprint: reject silent overwrites by default and suggest `amend-*` or explicit `--force-rebuild`.

`generate-master` means initial generation plus idempotent reuse, not unlimited overwrite.

#### `amend-*`

- The **semantic amendment interface**
- Appends or modifies controlled fields in an existing contract
- Must not masquerade as regeneration

#### `--force-rebuild`

- Explicit destructive regeneration
- Must be requested by the caller
- Back up the previous JSON or record a historical snapshot first

### 8.4.2 Phase 1 Concurrency

Do not assume complex multi-writer merging for `.story-system/*.json`.

Minimum requirements:

1. Serialize `generate-* / amend-* / refresh-*` operations targeting the same file.
2. Use file locking or equivalent mutual exclusion.
3. If another process holds the write lock, return explicit `BUSY / RETRY`, never continue writing.
4. Design genuine multi-writer merging separately for day 2+.

---

## 9. Skill Runtime Layer

### 9.1 General Principle

Skills execute; they do not assemble the system.

### 9.2 `webnovel-init`

Responsibilities:

1. Understand the book concept.
2. Call `generate-master`.
3. Persist `.story-system/MASTER_SETTING.json` first.
4. Render `.story-system/MASTER_SETTING.md` next.
5. Populate the setting-document skeleton last.

### 9.3 `webnovel-plan`

Responsibilities:

1. Read `MASTER_SETTING`.
2. Call `generate-volume`.
3. Call `generate-chapter`.
4. Produce volume outlines, chapter outlines, and timelines.

Planning may propose `amend-master / amend-volume` when:

- A new core faction forms
- A new hard world-rule limit appears
- Special-advantage boundaries explicitly expand
- The genre promise shifts structurally

Default flow:

1. The planning skill identifies a possible amendment.
2. `contract-auditor / diff analyzer` produces a structured proposal.
3. Show a readable summary and affected fields.
4. Execute `amend-master / amend-volume` only after user confirmation.

Unless automatic amendments are explicitly configured, the planning skill must not rewrite `MASTER` itself.

It no longer decides which genre Markdown to read, which CSV to search, or which rules to combine. Story System handles those centrally.

### 9.4 `webnovel-write`

Responsibilities:

1. Read the chapter brief.
2. Fall back to volume brief if absent.
3. Fall back to master next.
4. Read the final resolved values at that level.
5. Inject only directly relevant chapter override summaries.
6. Draft using runtime memory/state/context.

Writing must not directly modify `MASTER_SETTING` by default.

Only major structural events may enter explicit `amend-master / amend-volume` hooks, for example:

- A new permanent core protagonist ability
- An irreversible new world rule
- A permanent reversal of core faction relationships
- An upgraded main-plot promise rather than temporary deviation

Runtime facts may drive amendments, but only through explicit interfaces. Chapter fluctuations must not cause constant `MASTER` drift.

Recommended independent hook: `contract-auditor`.

It does not edit contracts. It:

1. Compares runtime facts with upstream contracts.
2. Distinguishes temporary chapter deviation from a needed amendment.
3. Produces an `amend proposal`.
4. Awaits user confirmation.

### 9.5 `webnovel-review`

Responsibilities:

1. Read the review contract.
2. Read `anti_patterns`.
3. Perform structured review against the contract.
4. Persist results to review/index/state.

---

## 10. Integrating the Existing Data Pipeline

A central point: reposition the existing pipeline rather than discard it.

### 10.1 `references/csv/`

New role:

- Primary knowledge layer
- Primary rule layer
- Primary retrieval layer

### 10.2 `references/*.md`

New role:

- Methodology
- Workflow standards
- Review rules
- Active transitional knowledge sources while CSV coverage remains insufficient

### 10.3 `templates/genres/*.md`

New role:

- Example-template layer
- Human references and initialization drafts
- Supplementary genre sources until routing-table coverage is sufficient

### 10.4 `templates/output/*.md`

New role:

- Source of story-system rendering templates

### 10.5 `scripts/reference_search.py`

New role:

- Low-level primitive
- Reusable CSV search kernel
- No longer the main skill entry point

### 10.6 `scripts/data_modules/context_manager.py`

New role:

- Runtime context assembler
- Consumer of story-system contracts + memory/state/index
- No global story-system generation responsibility

Evolution:

1. Phase 1 retains `context_manager`, without a ground-up rewrite.
2. Phase 1 prioritizes contracts while still aggregating state / summaries / reader_signal / plot_structure.
3. Phase 2 gradually extracts global-generation logic into `story_system`.
4. Phase 3 reduces it to pure runtime context assembly.

Integrate first, extract next, consolidate last; do not discard it immediately.

### 10.6.1 Contract Injection Point

After day 2, “contract-first” must be a real entry point, not just documentation.

Minimum requirements:

1. `_build_pack()` reads currently visible chapter contracts from `.story-system/`.
2. Add an explicit pack section such as `story_contract`.
3. Give it higher priority than legacy `genre_profile` summaries and temporary global assembly.
4. If contracts are absent, fall back to the existing `genre_profile + global + reader_signal` pipeline.

Recommended order:

1. Chapter contract
2. Volume contract
3. Master contract
4. Existing `genre_profile / global / references`

Contract-first must shape actual pack assembly, not merely skill wording.

### 10.6.2 `genre_aliases.py` / `genre_profile_builder.py` / `genre-profiles.md`

These are important seed sources for the routing table, not mere legacy baggage.

New roles:

- `genre_aliases.py`: active genre-normalization dictionary
- `genre_profile_builder.py`: active composite-genre hints
- `genre-profiles.md`: structured genre reference during phases 1/2

Do not downgrade them abruptly:

1. Manually migrate stable fields into `题材与调性推理.csv`.
2. Have `story_system` prefer CSV with Markdown fallback.
3. Downgrade `genre-profiles.md` only after CSV coverage reaches the threshold.

### 10.6.3 Transitional Genre-Truth Priority

During phases 1/2, never allow peer sources of truth. Fix priority:

1. `.story-system` contracts
2. `题材与调性推理.csv`
3. `genre-profiles.md`
4. `templates/genres/*.md`

Constraints:

- Once a contract exists, `context_manager` must not independently contradict its genre conclusions.
- `genre-profiles.md` is only fallback or supplementary explanation during transition.
- Genre templates are only examples/supplementary genre sources.

Otherwise contracts say A, context packs inject B, and skills mix in C, defeating contract-first design.

### 10.7 `state.json`

New role:

- Writing-process state machine
- Current character state
- Chapter progress

Not the central story-setting authority.

### 10.8 `index.db / vectors / bm25`

New role:

- Runtime retrieval evidence
- Plot-fact history
- Not rule knowledge

### 10.9 `memory_contract / orchestrator / summaries`

New role:

- Long-term memory
- Facts that already occurred
- Foreshadowing/payoff tracking

Relationship:

- CSV supplies rules.
- Memory supplies facts.
- Story System combines them into contracts.

### 10.9.1 Minimum Viable Memory

Do not assume every memory subsystem is production-complete.

Minimum phase 1 factual inputs:

1. `state.json`
2. Recent chapter summaries
3. Directly readable entities, relationships, and state changes in `index.db`

`MemoryOrchestrator` is an enhancement, not a phase 1 hard dependency.

If memory components are unavailable:

- Continue generating rule contracts.
- Degrade factual contracts to state + summaries + index facts.
- Do not block `generate-master / generate-volume` because memory is incomplete.

### 10.10 Migration Stages

Even a target-state specification needs basic migration criteria.

#### Day 1

- Add `题材与调性推理.csv`.
- Add minimal `generate-master`.
- Retain `reference_search.py`.
- Retain `context_manager`.
- Retain `genre-profiles.md` as an active genre source.
- Skills continue the `2026-04-09` L0/L1/L2 strategy.
- Story System initially exists as an internal kernel, not necessarily exposed to skills.
- If a CLI is provided, integrate only as `webnovel.py story-system ...`.

#### Day 2

- Introduce Volume contracts.
- Move skills to contract-first + local on-demand references.
- Retain `genre-profiles.md` fallback; do not downgrade prematurely.
- Formally inject `story_contract` through `context_manager`.
- Teach dashboard / preflight / health / backup about `.story-system`.

#### Day 3 and Later

- Gradually remove genre templates from the mainline after knowledge-density thresholds are met.
- Keep `reference_search.py` only as a primitive.
- Make Story System the sole system-level skill entry point.

### 10.10.1 Knowledge-Density Threshold

Do not prematurely downgrade `genre-profiles.md` or genre templates until:

1. The routing CSV covers currently supported mainstream primary genres.
2. Frequent aliases in `genre_aliases.py` map reliably to routing-table targets.
3. Human sampling confirms that most representative init/plan/write genre inputs produce usable CSV + contract results.
4. Active genre families have at least one round of real-project validation, not just static data entry.

CSV does not replace Markdown merely by existing. Switch progressively once it can reliably support the mainline.

### 10.10.2 Contract Takeover Boundaries

After day 2, contracts primarily own:

- Genre tone
- Reader-turn-off red lines
- Global system boundaries
- Volume/chapter execution objectives

Step-bound references retain:

- Local writing techniques
- Local scene patterns
- Naming and vocabulary
- Polishing, typesetting, anti-AI, review schema

Runtime rules:

- `context_manager` and `webnovel-write` read **final resolved contracts** by default.
- Expand the full override ledger by default only in debug / dashboard / health reports.

### 10.11 `scripts/data_modules/config.py`

`DataModulesConfig` is already the de facto unified project configuration for:

- Paths
- Retrieval parameters
- Context budgets
- Memory / index / review tuning

Do not invent a completely independent parallel configuration tree.

Recommended:

1. Reuse `DataModulesConfig` in phase 1.
2. Namespace new settings `story_system_*`.
3. Any later `StorySystemConfig` is a thin wrapper/subview, not a separate system.

Avoid separate runtime and Story System configurations with identically named fields carrying different meanings. That would split contract, context, and memory pipelines again.

### 10.12 Operational Integration

A new persistent source of truth cannot remain invisible to existing operations.

Integrate at least:

#### preflight

After day 2, check:

- `.story-system/MASTER_SETTING.md` exists
- `.story-system/MASTER_SETTING.json` exists
- JSON contracts are readable

#### dashboard / watcher

Do not watch only `.webnovel/`. Also watch:

- `.story-system/MASTER_SETTING.*`
- `.story-system/volumes/*.json`
- `.story-system/chapters/*.json`

Otherwise contract changes will not refresh the frontend.

#### health / status reports

Beyond state.json and existing runtime data, include:

- Contract existence
- Contract freshness
- Override-ledger summary
- Warnings about obvious contract/state conflicts

#### backup / fallback backup

Git normally includes `.story-system/`, but local fallback backup must too.

Minimum:

- When Git is unavailable, do not back up only `.webnovel/state.json`.
- Also back up current `.story-system/` contracts.

Otherwise recovery loses the new system source of truth.

---

## 11. Legacy Module Decisions

### 11.1 Retain as Lower-Level Capabilities

- `reference_search.py`
- `query_router.py`
- `context_manager.py`
- `genre_aliases.py`
- `genre_profile_builder.py`

More precisely:

- Retain, evolve, and consolidate `context_manager.py`.
- Retain genre alias/profile modules while migrating their knowledge into routing tables.

### 11.2 Retain With New Responsibilities

- `references/csv/`
- `references/shared/`
- `references/outlining/`
- `templates/output/`

### 11.3 Retain Without Primary-Source Status

- `references/genre-profiles.md`
- `templates/genres/*.md`

### 11.4 New Frontline Modules

- `story_system/engine/search_engine.py`
- `story_system/engine/reasoning_engine.py`
- `story_system/engine/aggregator.py`
- `story_system/engine/anti_pattern_engine.py`
- `story_system/engine/contract_builder.py`
- `story_system/engine/renderer.py`
- `story_system/engine/persistence.py`

---

## 12. Unified Anti-Patterns

### 12.1 Principle

Do not require every legacy table to rename fields immediately, but require unified extraction.

### 12.2 Suggested Mapping

```python
ANTI_PATTERN_SOURCE_FIELDS = {
    "题材与调性推理": ["强制禁忌/毒点"],
    "人设与关系": ["忌讳写法"],
    "爽点与节奏": ["常见崩盘误区"],
    "场景写法": ["反面写法"],
    "写作技法": ["常见误区"],
    "桥段套路": ["忌讳写法"],
}
```

Notes:

- If retrofit phase 1 adds `忌讳写法` to `桥段套路.csv`, phase 2 must keep reading it to avoid divergence.
- `桥段套路.反套路变种` supplies variation ideas, not anti-patterns by default.
- `金手指与设定.数值控制边界` belongs in `system_constraints`, not automatically in anti-patterns.
- Only explicitly negative fields belong in `ANTI_PATTERN_SOURCE_FIELDS`.

### 12.3 Output Requirement

Every generated contract must prominently contain:

- `## Anti-Patterns`

This section defines hard red lines.

---

## 13. Runtime Workflows

### 13.1 Starting a Book

Input: “Write a cyberpunk hacker story.”

1. Reasoning identifies primary/secondary genres.
2. Aggregate base tables across domains.
3. Generate `MASTER_SETTING`.
4. Persist to `.story-system/`.
5. Initialize setting documents.

### 13.2 Planning

Input: “Plan volume one around an auction-house comeback.”

1. Read `MASTER`.
2. Aggregate plot beats, pacing, scenes, and character additions.
3. Generate `VOLUME_BRIEF`.
4. Break it into `CHAPTER_BRIEF` contracts.

### 13.3 Writing

Input: “Write chapter 15.”

1. Read `chapter_015`.
2. Fall back to volume if absent.
3. Fall back to master next.
4. Read final resolved values.
5. Inject only directly relevant chapter overrides, not full history.
6. Draft using state / memory / recent context.

### 13.4 Review

Input: “Review chapter 15.”

1. Read the review contract.
2. Read `anti_patterns`.
3. Produce structured issues using the review schema.

---

## 14. Testing and Validation

### 14.1 General Principle

This CSV knowledge base does not need one test per knowledge entry.

Cover:

1. Successful contract generation
2. Correct override rules
3. Persistence of key fields
4. Anti-pattern aggregation
5. Runtime contract reads

### 14.2 Discouraged Tests

Do not add:

1. A test for every CSV row
2. Assertions for every knowledge item
3. Mechanical unit tests of semantic content quality

### 14.3 Retained Validation

Recommended:

1. Reasoning-match smoke tests
2. Contract schema tests
3. Persistence override-rule tests
4. Minimal CLI generation pipeline tests

Additional low-cost, high-value validation:

5. Multi-label reasoning fusion
6. Override-ledger generation
7. JSON→Markdown rendering consistency
8. `locked + lock_policy` behavior

Focus on stable contracts, unioned multi-label turn-offs, explicit override records, and valid JSON schemas, not individually judging knowledge entries.

---

## 15. Implementation Constraints

### 15.1 Knowledge Migration

Perform knowledge migration manually.

Prohibited:

- Automatically extracting Markdown into CSV
- Automatically translating and bulk-importing knowledge
- Automatically splitting sentences into knowledge entries

Allowed:

- Reading old material manually
- Manually distilling summaries, keywords, and synonyms
- Manually translating English prompts before entry

### 15.2 Engineering Implementation

Engineering may create scripts, CLIs, renderers, aggregators, and persistence modules.

Banning scripted knowledge migration does not ban engineering scripts.

---

## 16. Final Architecture Decisions

1. Promote `references/csv` to the primary knowledge repository.
2. Retain `references/*.md` as methodology.
3. Downgrade `templates/genres` to examples.
4. Promote `templates/output` to contract templates.
5. Move `reference_search.py` from the frontline to a primitive.
6. Move central configuration from `genre-profiles.md` into structured reasoning data.
7. Make skills contract-first with local step-bound on-demand references.
8. Retain state / index / memory as runtime facts and evidence.
9. Expose Story System publicly only through unified `webnovel.py story-system ...`.
10. Integrate `.story-system` with preflight / dashboard / health / backup.
11. JSON is the sole truth; Markdown is read-only rendering.
12. Use L0/L1/L2 reasoning, deterministic routing as the baseline, and LLM fusion for low-confidence semantics.
13. Require `lock_policy` on locked fields; core story-setting changes require an amendment proposal and user confirmation.

---

## 17. Closing

This refactor is not merely more accurate reference search.

It stops the model from reconstructing the world from scattered material for every chapter. Establish a stable story system first, then make planning, writing, and review consistently follow it.

That is the key shift from a discrete retrieval tool to system-level intelligent writing infrastructure.
