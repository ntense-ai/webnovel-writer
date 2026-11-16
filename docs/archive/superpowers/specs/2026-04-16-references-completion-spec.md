# References Completion Spec

> Historical design record: project-directory examples retain their original names. New projects use `chapters/`, `outlines/`, `settings/`, and `reviews/`; existing legacy projects remain supported without renaming. Resolve actual paths with `scripts/project_paths.py` before using these examples.

> Status: `implemented` (2026-04-16)
> Dependencies: `2026-04-09-skills-restructure-and-reference-gaps.md`, `2026-04-12-story-system-evolution-spec.md`, `2026-04-14-ui-ux-pro-max-skill-architecture-research.md`
> Companion: `references/csv/genre-canonical.md`, the authoritative genre enum

## Completion Record

- Phase 1 structure is complete: `CSV_CONFIG` includes `prefix`, `required_cols`, and `contract_inject`; `validate_csv.py`, `references/README.md`, loading-map, and gap-register are in place.
- Phase 2 adjudication is complete: `题材与调性推理.csv` expanded to 26 rows and `裁决规则.csv` to 17, covering 15 canonical genres.
- Validation: `validate_csv.py --format json` reports 0 errors / 0 warnings; relevant reference/story-system tests pass.
- Phase 3 knowledge additions were not expanded within this spec; remaining gaps are recorded in `references/index/reference-gap-register.md`.

## Goal

Move `webnovel-writer/references/` from a ready skeleton with a thin adjudication layer and no validation loop to dependable support across init → plan → write → review.

This spec does not add knowledge entries; those gaps are in [Appendix A](#appendix-a-knowledge-entry-gap-register). It addresses structure, configuration, validation, and indexes only.

## Diagnosis

### Assets at the Time of Diagnosis

```
references/
├── csv/                         # 9 CSV tables
│   ├── README.md                # Human-readable schema
│   ├── 命名规则.csv      (45 rows) # NR- | base
│   ├── 场景写法.csv      (52 rows) # SP- | base
│   ├── 写作技法.csv      (64 rows) # WT- | base
│   ├── 桥段套路.csv      (62 rows) # TR- | dynamic
│   ├── 人设与关系.csv    (58 rows) # CH- | base
│   ├── 爽点与节奏.csv    (60 rows) # PA- | dynamic
│   ├── 金手指与设定.csv  (59 rows) # SY- | base
│   ├── 题材与调性推理.csv (8 rows) # GR- | route; very thin
│   └── 裁决规则.csv       (7 rows) # RS- | reasoning; very thin
├── genre-profiles.md            # Genre profiles, fallback only
├── reading-power-taxonomy.md    # Reader-retention taxonomy
├── review-schema.md             # Review output schema
├── index/
│   ├── reference-loading-map.md # skill→step→trigger→ref mapping
│   └── reference-gap-register.md# Baseline gap register
├── outlining/
│   └── plot-signal-vs-spoiler.md
├── review/
│   └── blocking-override-guidelines.md
└── shared/
    ├── core-constraints.md
    ├── cool-points-guide.md
    ├── naming-and-voice-gaps.md
    └── strand-weave-pattern.md
```

### Existing Code Infrastructure

| Component | Location | Status |
|------|------|------|
| `CSV_CONFIG` registry | `reference_search.py:89-154` | ✅ Per-table `search_cols`/`output_cols`/`poison_col`/`role` |
| BM25 search primitive | `reference_search.py:160-244` | ✅ |
| `StorySystemEngine._route()` | `story_system_engine.py:115-159` | ✅ Consumes `题材与调性推理.csv` |
| `StorySystemEngine._collect_tables()` | `story_system_engine.py:161-185` | ✅ Queries tables recommended by the route |
| `StorySystemEngine._apply_reasoning()` | `story_system_engine.py:278-338` | ✅ Consumes `裁决规则.csv` |
| `RuntimeContractBuilder` | `runtime_contract_builder.py` | ✅ MASTER + plot → volume_brief + review_contract |
| `ContextManager` | `context_manager.py` | ✅ Reads contracts, genre profiles, state, and summaries |

### Core Problems

| # | Problem | Impact | Severity |
|---|------|---------|--------|
| P1 | **Only 7 adjudication rules**: Western fantasy, Eastern cultivation, sci-fi apocalypse, urban daily life, suspense/thriller, historical martial arts, fantasy. Many subgenres lack rules, reducing `_apply_reasoning()` to unprioritized ordering | Entire write chain | High |
| P2 | **Only 8 genre/tone routes**: broken engagement, rule-based horror, release after oppression, live-in son-in-law, system, infinite-flow, rebirth, palace intrigue. Uncovered genres use `default_seed_fallback` | init → write | High |
| P3 | **No validator**: Global IDs, prefixes, required columns, delimiters, and README/header alignment rely on manual discipline | Data quality | Medium |
| P4 | **Two-source drift** between `CSV_CONFIG` and README schema without automated alignment | Maintenance | Medium |
| P5 | **Loading-map drift** from actual Skill triggers | Reviewability | Low |
| P6 | **No top-level references README** explaining csv/md/index/shared boundaries | Readability | Low |
| P7 | **Missing `contract_inject` in CSV_CONFIG**: `contract注入层` exists in rules, but injection mappings remain scattered in engine code | Reviewability | Low |

---

## End-to-End Reference Consumption

### Initialization

```
User genre/selling-point input
  → Read genre-tropes.md, genre-profiles.md
  → Read worldbuilding/*.md (faction, world-rules, power-systems, character-design)
  → Read creativity/*.md (constraints, selling-points, combination, inspiration)
  → CSV: 命名规则 (--skill init --query "{object} {genre}")
  → story-system CLI (--persist, MASTER_SETTING only)
      → StorySystemEngine._route()    consumes 题材与调性推理.csv
      → StorySystemEngine._collect()  consumes recommended base/dynamic tables
      → StorySystemEngine._reason()   consumes 裁决规则.csv
  → Output: .story-system/MASTER_SETTING.json + anti_patterns.json
```

**Needs**:
- Genre routing must match: initialization genre/subgenre/tag input starts the entire system.
- Without a matching route row, MASTER_SETTING `core_tone`, `pacing_strategy`, and recommended tables are empty or degraded.
- Without an adjudication row, anti_patterns lacks `反模式` and `毒点权重`.

### Planning

```
User volume/chapter planning input
  → Read genre-profiles.md, strand-weave-pattern.md
  → Read plot-signal-vs-spoiler.md
  → Read cool-points-guide.md as needed
  → Read reading-power-taxonomy.md as needed
  → Read outlining/*.md (conflict-design, chapter-planning, genre-volume-pacing)
  → CSV: 场景写法 (--skill plan --query "卷级结构 叙事功能")
  → CSV: 命名规则 for new character names
  → CSV: 爽点与节奏 for conflict design
  → CSV: 桥段套路 for conflict design
  → story-system CLI (--emit-runtime-contracts)
      → RuntimeContractBuilder.build_for_chapter()
  → Output: volume_brief + review_contract
```

**Needs**:
- Volume planning draws structural guidance from `场景写法` and `爽点与节奏`.
- `桥段套路` supplies optional conflict templates.
- Naming rules trigger for new characters.
- Shared outlining currently contains only `plot-signal-vs-spoiler.md`; `conflict-design.md`, `chapter-planning.md`, and `genre-volume-pacing.md` are Skill-local references.

### Writing

```
context-agent assembles a writing brief
  → ContextManager.build_context()
      → Read all contracts under .story-system/
      → Read genre-profiles.md as fallback
      → Read reading-power-taxonomy.md
      → Read 设定集/*.md
      → Read state.json, summaries, outlines, index.db
  → Output: JSON context pack

Step 2: Drafting
  → Read core-constraints.md
  → CSV: 命名规则 for new characters
  → CSV: 场景写法 for battles/confrontations
  → CSV: 写作技法 for dialogue/emotion
  → CSV: 场景写法 for frequent scene patterns

Step 3: Review
  → Read review-schema.md, core-constraints.md
  → Read cool-points-guide.md as needed
  → Read strand-weave-pattern.md as needed
  → Read blocking-override-guidelines.md as needed

Step 4: Polish
  → Read polish-guide.md, typesetting.md, style-adapter.md
  → Read anti-ai-guide.md when an ai_flavor issue exists
```

**Needs**:
- Persisted init/plan contracts are the primary source of truth.
- Conditional CSV searches in Step 2 supplement contracts.
- Markdown references provide Step 3–4 gates and polishing guidance.
- Weak initialization routes/adjudication produce weak MASTER_SETTING and therefore weak downstream contracts.

### Review

```
  → Read core-constraints.md, review-schema.md
  → Read blocking-override-guidelines.md for blocking issues
  → Read cool-points-guide.md for payoff analysis
  → Read strand-weave-pattern.md for multi-strand review
  → Read anti-ai-guide.md when ai_flavor >= 3
```

**Needs**:
- Direct consumption is Markdown only, not CSV.
- Depends on review_contract from planning's RuntimeContractBuilder.
- Empty `genre_specific_risks` omits genre-specific review checks.

---

## Design Decisions

### D1: Complete 裁决规则.csv

**Goal**: Cover all frequent genres in `genre-profiles.md` and all subgenres in `题材与调性推理.csv`.

**Original coverage, 7 rows**: Western fantasy, Eastern cultivation, sci-fi apocalypse, urban daily life, suspense/thriller, historical martial arts, fantasy.

**Required additions, at minimum**:

| Genre | Reason |
|------|------|
| System fiction | Route GR-005 exists without adjudication |
| Infinite-flow | Same for GR-006 |
| Rebirth | Same for GR-007 |
| Palace/political intrigue | Same for GR-008 |
| Modern romance | Frequent women's genre, entirely missing |
| Historical romance | Same |
| Light novels | Independent Fanqie category |
| Gaming/esports | Independent Fanqie category |

**Method**: Manually write each row, filling `风格优先级`, `爽点优先级`, `节奏默认策略`, `毒点权重`, `冲突裁决`, `contract注入层`, and `反模式`.

**Hard constraint**: Adjudication content must be manually distilled, never programmatically generated.

### D2: Complete 题材与调性推理.csv

**Goal**: Cover common genre/subgenre/tag combinations users may enter during initialization.

**Original coverage, 8 rows**: Broken engagement, rule-based horror, release after oppression, live-in son-in-law, system, infinite-flow, rebirth, palace intrigue.

**Additions**: See the route gaps in [Appendix A](#appendix-a-knowledge-entry-gap-register).

**Key principle**: Populate `题材别名` thoroughly. Common names, jargon, and colloquial names are crucial to route hit rate.

### D3: Enhance CSV_CONFIG

Add per-table fields in `reference_search.py`:

```python
"裁决规则": {
    "file": "裁决规则.csv",
    "search_cols": {"题材": 4},
    "output_cols": [...],
    "poison_col": "",
    "role": "reasoning",
    # New fields
    "contract_inject": "CHAPTER_BRIEF.writing_guidance",  # Injection target
    "prefix": "RS",                                    # ID prefix
    "required_cols": ["题材", "风格优先级", "爽点优先级", # Required columns
                      "节奏默认策略", "毒点权重", "冲突裁决"],
},
```

| Field | Purpose |
|------|------|
| `contract_inject` | Declares the final contract destination, centralizing injection metadata in the registry rather than scattered engine code |
| `prefix` | ID prefix for validation |
| `required_cols` | Columns that must be nonempty |

### D4: Validator

Add `scripts/validate_csv.py`:

| Check | Rule | Exit code |
|--------|------|--------|
| Unique IDs | `编号` globally unique across CSVs | 1 |
| Prefix consistency | Match `CSV_CONFIG[table].prefix` | 1 |
| Required values | Table `required_cols` plus common `编号/适用技能/分类/层级/关键词/适用题材/核心摘要` are nonempty | 1 |
| Delimiters | No Chinese comma `，` in `适用技能/关键词/意图与同义词/适用题材` | 1 |
| Headers | Actual columns are a superset of `search_cols` + `output_cols` + `required_cols` | 1 |
| Genre range | Split `适用题材` values belong to Fanqie categories or `全部` | Warning |
| Route coverage | Each adjudication `题材` has a matching route row | Warning |
| Adjudication coverage | Each route `题材/流派` has a matching adjudication row | Warning |

Read metadata from `CSV_CONFIG`; do not hard-code table or column names.

### D5: Top-Level README

Add this directory index to `references/README.md`:

```markdown
# References

## Directory Structure

| Directory/file | Responsibility | Consumption |
|-------------|------|----------|
| `csv/` | Structured knowledge | `reference_search.py` BM25 retrieval |
| `csv/README.md` | CSV schema | Human reference |
| `genre-profiles.md` | Fallback genre profiles | ContextManager direct Read |
| `reading-power-taxonomy.md` | Reader-retention taxonomy | Skills direct Read |
| `review-schema.md` | Review output format | webnovel-review Read |
| `index/` | Metadata indexes | Human reference |
| `outlining/` | Outline references | webnovel-plan Read |
| `review/` | Review references | webnovel-review Read |
| `shared/` | Cross-Skill references | Multiple Skills Read |

## Markdown vs CSV

- **Markdown**: Procedures, methods, review schema, hard constraints, polishing guidance
- **CSV**: Itemized writing knowledge, naming rules, scene techniques, plot templates

## Consumption Chain

See `index/reference-loading-map.md` for the complete init → plan → write → review path.
```

### D6: Synchronize Loading Map

Compare actual Skills with `index/reference-loading-map.md`; add:

- Plan's local `conflict-design.md`, `chapter-planning.md`, and `genre-volume-pacing.md`.
- All conditional worldbuilding/creativity loads in init.
- CSVs indirectly consumed by write through `StorySystemEngine`.

### D7: Refresh Gap Register

Mark already-completed items:

- `blocking-override-guidelines.md` created ✅
- `plot-signal-vs-spoiler.md` created ✅
- `naming-and-voice-gaps.md` created ✅
- Initial naming/scene/technique CSVs created ✅
- Add gaps newly discovered in this spec.

### D8: Review Shared Markdown for Migration

| File | Recommendation |
|------|---------|
| `core-constraints.md` | **Keep unchanged**: procedural hard constraints, not itemized knowledge |
| `strand-weave-pattern.md` | **Keep unchanged**: three-strand proportions/warnings are methodology, not an entry library |
| `cool-points-guide.md` | **Review**: six execution patterns and four-step vindication may become `爽点与节奏.csv` entries; retain information-asymmetry design and density guidance in Markdown |
| `naming-and-voice-gaps.md` | **Review**: genre naming and voice distinction tables may become `命名规则.csv`/`写作技法.csv` entries; retain compensation strategies in Markdown |

Record results in [Appendix A](#appendix-a-knowledge-entry-gap-register); migrate later.

---

## Implementation

### Phase 1: Structure, Without Content Additions

| Task | Output | Dependency |
|------|------|------|
| 1.1 Enhance CSV_CONFIG | Per-table `contract_inject`/`prefix`/`required_cols` | None |
| 1.2 Validator | `scripts/validate_csv.py` | 1.1 |
| 1.3 Top-level README | `references/README.md` | None |
| 1.4 Loading map | Updated `index/reference-loading-map.md` | None |
| 1.5 Gap register | Updated `index/reference-gap-register.md` | None |

### Phase 2: Adjudication, Manually Authored

| Task | Output | Dependency |
|------|------|------|
| 2.1 Complete adjudication | 7 → 15+ rows | Appendix A |
| 2.2 Complete genre/tone routes | 8 → 20+ rows | Appendix A |
| 2.3 Pass validation | All `validate_csv.py` checks | 1.2, 2.1, 2.2 |

### Phase 3: Knowledge, Manually Authored

| Task | Output | Dependency |
|------|------|------|
| 3.1 Review shared Markdown | Identify migratable entries | D8 |
| 3.2 Manually enter them into CSV | New entries | 3.1 |
| 3.3 Audit seven knowledge tables | Fill missing topics from the end-to-end analysis | Appendix A |

### Phase 4: Verification

| Task | Output | Dependency |
|------|------|------|
| 4.1 End-to-end smoke | Run `story_system.py` for three genres; route → collect → reason must not degrade | 2.3 |
| 4.2 Loading-map regression | Verify actual Skill loading against every updated mapping | 1.4 |

---

## Appendix A: Knowledge Entry Gap Register

> Register gaps only; do not fill content here. All entries must be authored individually by hand.

### A1: Genre/Tone Route Gaps

Original eight routes: broken engagement, rule-based horror, release after oppression, live-in son-in-law, system, infinite-flow, rebirth, palace intrigue.

| Missing genre/subgenre | Priority | Reason |
|---------------|--------|------|
| Transmigration, men's/women's fiction | P0 | Frequent; affects historical romance, history, and fantasy routing |
| Urban superpowers | P0 | Combat and power systems differ completely from urban daily life |
| Traditional cultivation within Eastern cultivation | P1 | Distinct cultivation–combat–sect–tribulation rhythm |
| Apocalypse survival | P1 | Need not contain science-fiction elements |
| Sweet/light romance | P1 | Major women's category without routes |
| Deductive mystery | P1 | Logic and information control differ from suspense/thriller |
| Farming/management | P2 | Popular in both men's and women's fiction |
| Entertainment industry | P2 | Popular women's genre |
| Competitive sports | P2 | Independent Fanqie category |
| Cosmic horror/mysteries | P2 | Distinct pacing and adjudication |
| Academy stories | P3 | Cross-genre narrative structure |
| Dungeon/stage stories | P3 | Similar to, but distinct from, infinite-flow |

### A2: Adjudication Gaps

Original seven: Western fantasy, Eastern cultivation, sci-fi apocalypse, urban daily life, suspense/thriller, historical martial arts, fantasy.

Principle: `裁决规则.csv` covers **major genre types**, not subgenres. Route parameters in `题材与调性推理.csv` handle subgenre differences.

| Missing genre | Priority | Reason |
|----------|--------|------|
| Modern romance | P0 | Major women's audience; emotion-first logic differs from existing male-oriented rules |
| Historical romance | P0 | Status, ritual, and court constraints need independent adjudication |
| System/gamified fiction | P0 | Existing routes lack rules for numbers, panels, and progression |
| Light novels | P1 | Distinct anime-influenced aesthetics, pacing, and payoffs |
| Gaming/esports | P1 | Tournament structure, teamwork, and technical description |
| Farming/everyday management | P2 | Low-conflict, accumulation-driven narrative |
| Cosmic horror/mysteries | P2 | Fear of the unknown, limited information, sanity checks |

### A3: Seven Knowledge-Table Audits

> Populate after analyzing existing coverage. This is an initial framework.

#### 命名规则.csv (45 Rows)

| Missing topic | Priority | Evidence |
|----------|--------|---------|
| Women's-fiction naming: historical/modern/sweet romance | P1 | Current entries favor men's fiction |
| Faction/organization naming: sects, gangs, companies, clans | P1 | Characters and places covered; organizations missing |
| Book/title naming | P2 | Previously deferred in gap register |

#### 场景写法.csv (52 Rows)

| Missing topic | Priority | Evidence |
|----------|--------|---------|
| Daily life/farming/management | P1 | Current emphasis on combat/confrontation |
| Romance: attraction, misunderstanding, reunion, separation | P1 | Core women's-fiction scenes missing |
| Mystery: clues, deductive confrontation, truth revelation | P2 | |

#### 写作技法.csv (64 Rows)

| Missing topic | Priority | Evidence |
|----------|--------|---------|
| Information control: suspense, asymmetry, limited viewpoint | P1 | Needed by mysteries and cosmic horror |
| Sweet romance: attraction and couple interaction | P1 | Women's-fiction needs |
| Humor/commentary for light novels and urban comedy | P2 | |

#### 桥段套路.csv (62 Rows)

| Missing topic | Priority | Evidence |
|----------|--------|---------|
| Women's-fiction classics: substitute marriage, auspicious marriage to cure illness, divorce, rebirth revenge | P1 | Entirely absent |
| System activation, hidden missions, upgrades | P1 | |
| Locked rooms, alibis, culprit reversals | P2 | |

#### 人设与关系.csv (58 Rows)

| Missing topic | Priority | Evidence |
|----------|--------|---------|
| Women's-fiction archetypes: idealized first love, deceptive innocent, domineering CEO, obsessive lover, childhood friend | P1 | |
| Team/couple relationships: partners, rivals, mentors and students | P2 | |

#### 爽点与节奏.csv (60 Rows)

| Missing topic | Priority | Evidence |
|----------|--------|---------|
| Women's-fiction payoffs: exposing false innocence, intense sweetness, identity reveals | P1 | |
| Farming/management accumulation payoffs | P2 | |
| Migratable execution patterns from cool-points-guide.md | P2 | D8 review |

#### 金手指与设定.csv (59 Rows)

| Missing topic | Priority | Evidence |
|----------|--------|---------|
| Women's-fiction advantages: portable space, medicinal garden, past-life memories, mind reading | P1 | |
| Noncombat advantages: appraisal, crafting, trading, information | P2 | |

### A4: Shared Markdown Migration Review

> Populate after Phase 3 review.

| Source | Candidate section | Target CSV | Estimated entries | Status |
|--------|-----------|---------|-----------|------|
| `cool-points-guide.md` | Pending review | `爽点与节奏.csv` | - | Not started |
| `naming-and-voice-gaps.md` | Pending review | `命名规则.csv` / `写作技法.csv` | - | Not started |

---

## Acceptance Criteria

| Phase | Criteria |
|------|---------|
| Phase 1 | Validator runs and passes current data, warnings allowed but no errors; top-level README exists; loading-map matches Skills |
| Phase 2 | At least 14 adjudication rows and 16 route rows; zero validator warnings; three-genre end-to-end flow does not degrade |
| Phase 3 | Shared Markdown reviewed and migratable entries added; P1 gaps in seven knowledge tables filled |
| Phase 4 | End-to-end smoke tests and loading-map regression pass |
