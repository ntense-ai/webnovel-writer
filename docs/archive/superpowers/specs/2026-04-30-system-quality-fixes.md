# System-Level Fixes Identified by Lingshizhuang Testing

> Historical design record. Examples have been translated to the English-only project layout: `chapters/`, `outlines/`, `settings/`, and `reviews/`. Consult the current runtime documentation before applying historical implementation snippets.

> Date: 2026-04-30
> Scope: webnovel-writer system issues (independent of LLM capability)
> Test basis: DeepSeek v4pro completed init / plan / write chapters 1-2 + review in `D:\wk\xiaoshuo\Spiritstone Manor`
> Fact check: Verified against current repository behavior and actual artifacts in `D:\wk\xiaoshuo\Spiritstone Manor`, correcting over-attribution and nonexistent implementation targets
> Already delivered: commit `f58d657 fix: align projection writers with real LLM commit schema` (schema-drift fixes)

---

## 1. Background and Scope

After the Lingshizhuang project completed two chapters through init→plan→write→review→commit with DeepSeek v4pro, the generated artifacts received an end-to-end review. This spec lists eight unresolved **system-side** issues (schema drift was fixed in f58d657), ordered by priority P0→P3. Each includes evidence, impact, root cause, proposed fix (specific files/line references), acceptance criteria, and effort estimate.

Outside this spec:
- Writing-quality problems in LLM output (AI flavor, parallel phrasing, excessive habitual gestures, etc.), which belong to the review agent.
- Schema drift already fixed in f58d657 (state_projection / memory_writer / vector_writer / index_manager schemas, protagonist_state mirroring, index protagonist identification, entity-alias fallback).
- Earlier fixes (init project root 9b8976e, entity-alias fallback fc63628, safe project-experience memory writes d2571d2, etc.).

Chinese paths, parser labels, fixture strings, placeholder patterns, and quoted artifact evidence below remain literal compatibility/test data.

---

## 2. Execution Plan

This section reorganizes the eight verified issues into an actionable workflow. The detailed issue specifications below remain the source of truth; this section defines order, dependencies, and implementation targets to avoid jumping between prompts, runtime briefs, init templates, and review feedback.

### Phase 1 — Chapter Directive / chapter_focus / Writing-Prompt Ordering (Issues #1 #2 #5)

**Objective**: Promote detailed-outline execution constraints to the top level of `chapter_brief`, ahead of `dynamic_context` in the writing brief, and stop misleading reference summaries from becoming `chapter_focus`.

**Files to change**:
- `webnovel-writer/scripts/chapter_outline_loader.py`
- `webnovel-writer/scripts/story_system.py`
- `webnovel-writer/scripts/data_modules/story_system_engine.py`
- `webnovel-writer/scripts/data_modules/runtime_contract_builder.py` (keep directives distinct from review/runtime contracts)
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- Related tests, preferably in existing story-system / outline-loader test directories.

**Concrete tasks**:
- Add/extend `load_chapter_execution_directive(project_root: Path, chapter: int)` in `chapter_outline_loader.py`. Extract `goal`, `obstacles`, `cost`, `time_anchor`, `chapter_span`, `countdown`, `cbn`, `cpns`, `cen`, `must_cover_nodes`, `forbidden_zones`, `chapter_end_open_question`, `hook_type`, `hook_strength`, `key_entities`, `strand`, and `antagonist_tier` from `outlines/Volume {vol}-detailedoutlines.md`.
- Add top-level `chapter_directive` during story-system brief assembly; retain the legacy path if no chapter block exists.
- Change `_suggest_chapter_focus()`: prefer `chapter_directive.goal`; without a directive, use a non-placeholder query; never derive it from `dynamic_context[0]["summary"]`.
- Order the `webnovel-write/SKILL.md` brief: hard chapter constraints → CBN/CPNs/CEN → forbidden content → style guidance → `dynamic_context` stylistic reference.
- Test persisted directive fields, `chapter_focus` provenance, no reference-summary copying without a directive, and a manually checked prompt-order fixture.

**Dependencies**:
- Existing `chapter_outline_loader.py` already recognizes `CBN / CPNs / CEN / mandatory_nodes / prohibitions`.
- Phase 2 ranking reuses `chapter_directive.goal/key_entities/strand/antagonist_tier`, so this phase must come first.

**Verification/tests**:
- New outline/story-system tests pass under `pytest --no-cov`.
- Generate a sample chapter 1 brief; confirm `chapter_directive.time_anchor`, `must_cover_nodes`, and `forbidden_zones`.
- Manually inspect the writing brief: `dynamic_context` is labeled supplementary and follows the directive.

**Estimated scope/risk**: Medium, 4-6 hours. Main risk: Markdown heading/field variants cause missed parsing; support `Chapter 1`, `Chapter 1`, and spacing variants.

### Phase 2 — Query Validity / Chapter-Aware Reference Ranking (Issue #3)

**Objective**: Give story-system a real chapter-goal query and amplify chapter semantics in ranking so genre-correct but scene-wrong cards do not outrank lending/investigation cards.

**Files to change**:
- `webnovel-writer/scripts/story_system.py`
- `webnovel-writer/scripts/data_modules/story_system_engine.py`
- `webnovel-writer/skills/webnovel-plan/SKILL.md`
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- `webnovel-writer/skills/webnovel-review/SKILL.md`
- Reference/story-system test fixtures.

**Concrete tasks**:
- Add placeholder-query protection at the `story_system.py` CLI entry. Detect `{chapter-outlinegoal}`, `Chapter Nchapter-outlinegoal`, and generic template text; diagnose or warn about degraded behavior.
- Require plan/write Skills to resolve the real chapter goal before calling story-system; never pass a placeholder as `query`.
- In review, compare `chapter_brief.meta.query` with the detailed-outline goal and flag placeholder queries as system issues.
- Add chapter-aware scoring around query expansion/table collection/ranking in `story_system_engine.py`, using `chapter_directive.goal/key_entities/strand/antagonist_tier`.
- Combine genre match and chapter-keyword scores; for equal priority, rank more chapter-keyword matches first.
- Preserve generic `reference_search.py` capabilities; do not invent a nonexistent routing layer.

**Dependencies**:
- Requires Phase 1 `chapter_directive`. Starting earlier permits only query-text signals and substantially reduces ranking benefits.
- Need a finance/promissory-note/interest reference fixture to demonstrate chapter 1 retrieval improvement.

**Verification/tests**:
- `test_story_system_rejects_or_warns_placeholder_query`: Placeholder query is diagnosed.
- `test_story_system_reference_matching_prefers_chapter_keywords`: Lending cards outrank generic philosophical-debate/pill/sect-management cards.
- Sample Lingshizhuang chapter 1 brief: `dynamic_context` contains at least one card related to promissory notes, interest, compound interest, or debt.

**Estimated scope/risk**: Medium, about 4 hours. Reference CSV fields vary; tolerate missing `keywords`, `intent_synonyms`, and `applicable_scenes`.

### Phase 3 — Init Template Pruning / Conditional Generation (Issue #4)

**Objective**: Reduce empty setting files/directories after init, avoid `protagonist-team.md` in single-protagonist projects, and concentrate facts in existing protagonist cards, worldbuilding, and volume outlines.

**Files to change**:
- `webnovel-writer/scripts/init_project.py`
- `webnovel-writer/templates/output/settings-special-advantage.md`
- `webnovel-writer/templates/output/hybrid-genre.md`
- `webnovel-writer/templates/output/settings-protagonist-team.md`
- `webnovel-writer/templates/output/settings-heroine.md`
- `webnovel-writer/skills/webnovel-init/SKILL.md`
- Init tests.

**Concrete tasks**:
- Remove redundant shell templates from default generation: special-advantage design, payoff planning, and hybrid-genre fusion logic, unless explicitly needed.
- Generate `protagonist-team.md` conditionally from `idea_bank.protagonist_structure`: only `protagonist-team`, `dual`, or `ensemble` projects.
- Generate `heroine.md` conditionally from `heroine_config`: not for `none`.
- Create `charactercollection/`, `items/`, and `other-settings/` only on the first entity-delta write.
- Update init instructions so prompts no longer demand pruned templates.

**Dependencies**:
- No code dependency on Phases 1/2; may run in parallel.
- First inspect generation lists in `init_project.py`, `webnovel-init/SKILL.md`, and template paths; do not remove templates without changing callers.

**Verification/tests**:
- Single-protagonist fixture creates `settings/protagonist.md`, not `settings/protagonist-team.md`.
- `none` fixture does not create `settings/heroine.md`.
- Default init does not create `special-power-design.md`, `payoff-plan.md`, or empty `charactercollection/items/othersetting` directories.

**Estimated scope/risk**: Small, about 2 hours. Template and output filenames differ; use actual `init_project.py` mappings.

### Phase 4 — Placeholder Guardrails / Cross-Volume Anchor Writeback (Issues #6 #7)

**Objective**: Detect `[TODO...]`, `temporary name`, `{placeholder}`, and similar drift at plan/write boundaries. Define Phase 7 as minimal cross-volume anchor writeback after current-volume planning: only after `webnovel-plan` completes and validates current-volume artifacts, write V+1's title, core conflict, ending climax, and explicitly structured foreshadowing/open loops to `master-outline.md`. Phase 7 must not automatically plan the next volume in detail.

**Files to change**:
- `webnovel-writer/scripts/data_modules/placeholder_scanner.py` (new)
- `webnovel-writer/scripts/webnovel.py`
- `webnovel-writer/skills/webnovel-plan/SKILL.md`
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- `webnovel-writer/templates/output/outlines-master-outline.md`
- Plan/write/CLI tests.

**Concrete tasks**:
- Add `scan_placeholders(project_root)` to scan `outlines/*.md` and `settings/*.md` for `\[TODO[^\]]*\]`, `（temporary name）`, `(temporary name)`, `（To be completed）`, and whole-field `{placeholder}` / `<placeholder>`.
- Add `placeholder-scan --project-root <dir>` to `webnovel.py`.
- Scan at plan start/end: warn, do not block planning.
- At write start, block if setting files for entities relevant to the current chapter retain pending markers.
- Change `outlines-master-outline.md`: no pre-generated empty V2-V20 rows at init.
- After successful, complete, validated current-volume planning, write only V+1's title, core conflict, and ending climax to `master-outline.md`.
- Append only new foreshadowing/continuing open loops explicitly structured in current planning output; never infer them from free text.
- Phase 7 must not generate the next volume's detailed outline, beat sheet, timeline, or chapter-level plan.

**Dependencies**:
- Template overlap with Phase 3: coordinate `templates/output/outlines-master-outline.md` and init generation when parallel.
- Write blocking should reuse Phase 1 `chapter_directive.key_entities` or existing chapter-entity parsing. Whole-project scanning otherwise risks false positives.

**Verification/tests**:
- `test_placeholder_scanner_finds_pending_marks` covers `[TODO...]`, `temporary name`, `{placeholder}`.
- `test_write_chapter_blocks_on_pending_related_entity`: Relevant entity placeholders block; unrelated ones do not.
- `test_plan_flow_writes_minimal_next_volume_anchor`: After V1 planning/validation, add only V2 title/conflict/climax, with no V3-V20 empty rows or V2 detailed outline/beat sheet/timeline.
- CLI smoke: `webnovel.py placeholder-scan --project-root <fixture>` returns structured output.

**Estimated scope/risk**: Medium, about 6 hours. Main risks: placeholder false positives and inaccurate chapter-entity relevance. Prioritize warning/blocking severity distinctions.

### Phase 5 — Anti-Pattern Feedback Loop (Issue #8)

**Objective**: Feed medium-or-higher `ai_flavor` review issues into `.story-system/anti_patterns.json` so future briefs proactively avoid identified sentence patterns.

**Files to change**:
- `webnovel-writer/scripts/data_modules/review_schema.py`
- `webnovel-writer/scripts/data_modules/story_system_engine.py`
- `webnovel-writer/skills/webnovel-review/SKILL.md`
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- Review/story-system tests.

**Concrete tasks**:
- Add a post-persistence hook: append anti-patterns when `category == "ai_flavor"` and `severity in {"medium", "high", "critical"}`.
- Store `text`, `source_table="review_extracted"`, `source_id="ch0002_issue_N"`, `category`, and `added_at`.
- Deduplicate identical evidence/text.
- Load review-extracted anti-patterns during brief construction as patterns to avoid.
- Document which review findings become future writing constraints.

**Dependencies**:
- No hard Phase 1 dependency, but Phase 1 prompt ordering makes correct anti-pattern placement easier.
- Verify existing `.story-system/anti_patterns.json` schema; preserve fields written by reference initialization.

**Verification/tests**:
- `test_ai_flavor_review_issue_added_to_anti_patterns`: Medium-or-higher ai_flavor is appended.
- `test_anti_pattern_review_feedback_dedupes_evidence`: Repeated evidence is not stored twice.
- Brief fixture confirms review-extracted text appears in later avoidance lists.

**Estimated scope/risk**: Small, about 2 hours. Review persistence may have multiple entry points; locate them all first.

---

## 3. Open Issues at a Glance

| # | Priority | Issue | Impact | Effort |
|---|--------|------|--------|--------|
| 1 | **P0** | chapter_brief lacks detailed-outline execution constraints | Every chapter's quality | Medium |
| 2 | **P0** | dynamic_context dominates writing prompts over outline constraints | Every chapter's quality | Small |
| 3 | P1 | Retrieval underweights actual chapter goals; genre routing dominates semantics | Every brief's relevance | Medium |
| 4 | P1 | Bulk empty setting templates; protagonist-group file in single-protagonist projects | Init confusion, placeholder noise | Small |
| 5 | P1 | Unrelated dynamic_context summary inserted into `chapter_focus` | Misleading briefs | Small |
| 6 | P2 | No placeholder/drift guardrails (outline `[TODO...]` vs named protagonist-card entry) | Planning inconsistency | Small |
| 7 | P2 | Missing V+1 minimal anchors / structured foreshadowing writeback | Broken cross-volume promises | Medium |
| 8 | P2 | Reviewed ai_flavor patterns do not feed `anti_patterns.json` | Repeated defects | Small |

---

## 4. Detailed Fix Specifications

### Issue #1 — chapter_brief Lacks Detailed-Outline Execution Constraints (P0)

**Evidence**:

Fields in `D:\wk\xiaoshuo\Spiritstone Manor\.story-system\chapters\chapter_001.json` (136 lines):

```json
{
  "meta": {...},
  "override_allowed": {"chapter_focus": "<copied from the SP-087 card>"},
  "dynamic_context": [SP-087, NR-077, SY-009, CH-072],
  "source_trace": [...],
  "reasoning": {...}
}
```

Chapter 1 in `D:\wk\xiaoshuo\Spiritstone Manor\outlines\volume-1-outline.md` fully specifies goal / resistance / cost / time anchor / countdown / Strand / antagonist tier / **CBN / CPNs / CEN / required nodes / forbidden content / chapter-end open question / hook type**.

Downstream structured parsing already recognizes `CBN / CPNs / CEN / Must-cover nodes / Chapter prohibitions`, but **the chapter brief itself lacks goal, resistance, cost, time anchor, countdown, and chapter-end open-question execution constraints**.

**Impact**:

- Chapter 2 review found Sun Wang saying "tomorrow" while the timeline specified D-Day evening: time anchor, chapter span, and countdown were absent from the primary writing brief.
- Forbidden content can become review-contract blocking rules, but is not presented proactively as pre-writing execution constraints; detection remains retrospective.
- fulfillment_result.json checks fulfillment after prose is complete, discovering missing nodes too late.

**Root cause**:

The chain is split:

- `webnovel-writer/scripts/chapter_outline_loader.py` extracts `cbn / cpns / cen / mandatory_nodes / prohibitions` from detailed outlines.
- `webnovel-writer/scripts/data_modules/runtime_contract_builder.py` consumes them for `selected_scenes / must_check / blocking_rules`.
- `CHAPTER_BRIEF` still mainly uses story-system `dynamic_context + chapter_focus`, without promoting execution constraints to primary writing inputs.

The problem is not "never reading the detailed outline," but **reading only its structural skeleton without injecting chapter execution instructions into the brief's main path**.

**Fix**:

1. Extend `webnovel-writer/scripts/chapter_outline_loader.py` or an adjacent helper with execution-constraint extraction:
   - `load_chapter_execution_directive(project_root: Path, chapter: int) -> dict`
   - Parse the chapter Markdown block in `outlines/Volume {vol}-detailedoutlines.md` for:
     - `goal` / `obstacles` / `cost` / `time_anchor` / `chapter_span` / `countdown`
     - `cbn` / `cpns: list[str]` / `cen`
     - `must_cover_nodes: list[str]` (the `Must-cover nodes` line)
     - `forbidden_zones: list[str]` (the `Chapter prohibitions` line, semicolon-separated)
     - `chapter_end_open_question` / `hook_type` / `hook_strength`
     - `key_entities: list[str]`, `strand`, `antagonist_tier`
   - Tolerant parsing: return None when the chapter block is absent so callers use the legacy path.

2. Modify persisted chapter-brief assembly in `webnovel-writer/scripts/story_system.py` + `webnovel-writer/scripts/data_modules/story_system_engine.py`; keep volume/review runtime contracts with `runtime_contract_builder.py`:
   ```python
   from chapter_outline_loader import load_chapter_execution_directive
   directive = load_chapter_execution_directive(project_root, chapter)
   brief["chapter_directive"] = directive  # New top-level field
   if directive and directive.get("goal"):
       # Replace chapter_focus copied from dynamic_context with the outline goal
       brief["override_allowed"]["chapter_focus"] = directive["goal"]
   ```

3. Put `chapter_directive` **before** dynamic_context in the `webnovel-writer/skills/webnovel-write/SKILL.md` prompt template and explicitly state constraints:
   ```markdown
   ## Hard Chapter Constraints (Highest Priority)
   - Time anchor: {directive.time_anchor}
   - Countdown: {directive.countdown}
   - Required nodes: {directive.must_cover_nodes}
   - Must remain unresolved at chapter end: {directive.chapter_end_open_question}
   - Forbidden content (violation fails review): {directive.forbidden_zones}
   ```

**Acceptance criteria**:

```python
def test_chapter_brief_contains_outline_directive(tmp_path):
    # Prepare an outline fixture containing one chapter block
    outline = tmp_path / "outlines" / "volume-1-outline.md"
    outline.parent.mkdir(parents=True)
    outline.write_text(SAMPLE_OUTLINE_CHAPTER_1, encoding="utf-8")
    # Build the brief
    brief = build_chapter_brief(tmp_path, chapter=1)
    # Required fields must exist
    assert brief["chapter_directive"]["time_anchor"] == "D-Day early morning"
    assert "servant disciples cannot leave the sect at will" in brief["chapter_directive"]["forbidden_zones"][0]
    assert len(brief["chapter_directive"]["cpns"]) >= 1
    # chapter_focus comes from the outline goal, not an SP-card summary
    assert "clarify" in brief["override_allowed"]["chapter_focus"]
```

**Effort**: Medium, about 4-6 hours including tests.

---

### Issue #2 — dynamic_context Dominates Writing Prompts (P0)

**Evidence**:

`webnovel-writer/skills/webnovel-write/SKILL.md` already says `chapter_focus` is CSV reference only, chapter goals come from the outline, and structured nodes should follow `CBN→CPNs→CEN`. However, brief generation lacks a stable `chapter_directive` presentation template, so supplementary references such as `dynamic_context` can overshadow execution constraints.

**Impact**: Coupled with #1: even with directives in the brief, an LLM may treat generic references as the main direction unless context-agent / writing-brief ordering is explicit.

**Fix**:

Order prompt sections in `webnovel-writer/skills/webnovel-write/SKILL.md`:

1. Title: `# Chapter N Writing Task`.
2. **Hard chapter constraints** (new, from chapter_directive): bullets.
3. **Required chapter nodes** (CBN/CPNs/CEN): numbered list.
4. **Forbidden content**: prominent warnings.
5. **Style guidance**: reasoning + protagonist-card out-of-character warnings extracted from master setting.
6. **Supplementary scene techniques**: dynamic_context, explicitly nonmandatory and **stylistic reference only**.

**Acceptance criteria**:

Manually review one writing prompt to confirm directive > dynamic_context in both order and weight.

**Effort**: Small, about 1 hour: Markdown-template edits + one fixture test.

---

### Issue #3 — Reference Retrieval Underweights Actual Chapter Goals (P1)

**Evidence**:

Chapter 1 brief injected:
- SP-087 philosophical debate: irrelevant to waking in a servants' dormitory.
- NR-077 pill/artifact naming: chapter 1 contains neither.
- SY-009 sect management: no organizational management in chapter 1.
- CH-072 sect prodigies: no prodigy appears in chapter 1.

Injected cards lean heavily toward generic xianxia techniques rather than the lending-investigation scenes in chapters 1-2.

**Impact**: Irrelevant knowledge displaces useful cards (no finance/economics references appear), and `chapter_focus` amplifies this retrieval bias.

**Root cause**:

Two issues combine:

1. **Upstream goals are not real**: plan/write instructions show `story-system "{chapter-outlinegoal}" ...`. The actual Lingshizhuang `MASTER_SETTING.json` even contains literal query `"Chapter 2chapter-outlinegoal"`, showing that real goals do not reliably enter the workflow. Later review exposes the resulting drift.
2. **Downstream retrieval still favors genre routing**: `webnovel-writer/scripts/data_modules/story_system_engine.py` passes `query` to `reference_search.py`, but genre routing first chooses recommended tables, then simplified BM25 ranks results. Placeholder/generic queries yield genre-correct, scene-wrong matches.

The root cause is not "searching only by genre_filter," but **unreliable real-goal injection and insufficient amplification of chapter semantics**.

**Fix**:

1. Correct upstream queries first:
   - In `webnovel-writer/skills/webnovel-plan/SKILL.md` and `webnovel-writer/skills/webnovel-write/SKILL.md`, upgrade `story-system "{chapter-outlinegoal}" ...` from a placeholder hint to a requirement to **resolve the real goal before calling**.
   - In `webnovel-writer/skills/webnovel-review/SKILL.md`, require comparison of actual `chapter_brief.meta.query` with the outline goal; do not treat placeholder-query output as a normal brief.
   - Add protection near the `webnovel-writer/scripts/story_system.py` entry: diagnose/warn if query remains `{chapter-outlinegoal}`, `Chapter Nchapter-outlinegoal`, or similar placeholder text.
2. Add chapter-aware reference signals:
   - Inputs: `chapter_directive.goal`, `chapter_directive.key_entities`, `chapter_directive.strand`, `chapter_directive.antagonist_tier`.
   - Extract keywords using jieba or simple splitting.
   - Score token overlap against card fields `keywords` / `intent_synonyms` / `applicable_scenes`.
3. Add ranking signals around `_collect_tables` / `_expand_query` in `webnovel-writer/scripts/data_modules/story_system_engine.py`:
   - Final score: `(genre_match_score * 0.4) + (chapter_keyword_score * 0.6)`.
   - Within equal `priority_rank`, prefer more chapter-keyword hits.
4. Preserve generic BM25 in `reference_search.py`; do not invent `genre_router.py`.

**Acceptance criteria**:

```python
def test_story_system_reference_matching_prefers_chapter_keywords():
    directive = {"goal": "see through the absurd terms of the promissory note", "key_entities": ["promissory note", "interest", "compound interest"]}
    result = StorySystemEngine(csv_dir=fixture_csv_dir).build(
        query="see through the absurd terms of the promissory note promissory note interest compound interest",
        genre="xianxia",
        chapter=1,
    )
    selected = result["chapter_brief"]["dynamic_context"]
    # Lending cards must outrank philosophical-debate cards
    assert selected[0]["id"] == "FIN-001"
```

**Effort**: Medium, about 4 hours including a finance-scene reference fixture.

---

### Issue #4 — Empty Setting Templates and Unwanted Protagonist Groups (P1)

**Evidence**:

Lingshizhuang's setting directory contains:
- `special-power-design.md`: Only `{placeholder}` and empty fields; information already exists in the protagonist card's special-advantage section and master outline's creative constraints.
- `hybrid-genre.md`: Empty; information already exists in worldbuilding/master-outline fusion sections.
- `protagonist-team.md`: Empty, despite **`state.protagonist_structure="singleprotagonist+supportingviewpoint"`**.
- `payoff-plan.md`: Only two sample rows for chapters 1-5/6-10; volume-outline payoff-density planning is more detailed.
- `characters/{minor,antagonist,primary}/`, `items/`, `other-settings/`: Empty directories.

**Impact**:

- Users cannot tell whether empty files need filling.
- A master-setting extractor reading every setting file may mistake empty fields for undecided facts.
- Redundant project structure.

**Root cause**:

`webnovel-writer/skills/webnovel-init/SKILL.md` hardcodes all templates without branching on `idea_bank` protagonist_structure / heroine_config / hybrid-genre flags.

**Fix**:

1. **Stop generating redundant templates**:
   - `special-power-design.md`: Information belongs in the protagonist card's special-advantage section.
   - `hybrid-genre.md`: Information belongs in worldbuilding's fusion section; relevant only to hybrid projects.
   - `payoff-plan.md`: The volume-outline payoff table is the single source of truth.
2. **Generate conditionally**:
   - `protagonist-team.md` only when `protagonist_structure ∈ {"protagonist-team", "dual", "ensemble"}`.
   - `heroine.md` only when `heroine_config != "none"`.
   - Always generate required `antagonist.md`.
   - If retained, `hybrid-genre.md` only when `genre_combination` is nonempty.
3. **Create directories on demand**:
   - `charactercollection/` on the first new-character `apply_entity_delta`, with entity_type/tier subdirectories.
   - Likewise `items/` and `other-settings/`.

Modify `webnovel-writer/scripts/init_project.py`, retained templates in `webnovel-writer/templates/output/`, and generation steps in `webnovel-writer/skills/webnovel-init/SKILL.md`.

**Acceptance criteria**:

```python
def test_init_skips_protagonist_group_for_single_protagonist(tmp_path):
    init_project(tmp_path, idea_bank={"protagonist_structure": "singleprotagonist+supportingviewpoint", ...})
    assert not (tmp_path / "settings" / "protagonist-team.md").exists()
    assert (tmp_path / "settings" / "protagonist.md").exists()

def test_init_skips_dead_template_files(tmp_path):
    init_project(tmp_path, idea_bank={...})
    for dead in ("special-power-design.md", "payoff-plan.md"):
        assert not (tmp_path / "settings" / dead).exists()
```

**Effort**: Small, about 2 hours.

---

### Issue #5 — Unrelated Summary Inserted into chapter_focus (P1)

**Evidence**:

`chapter_002.json:override_allowed.chapter_focus = "the debate's tension comes from arguments striking at the foundations of cultivation。"`

This says philosophical-debate tension comes from challenging cultivation foundations, copied directly from SP-087's `summary` in dynamic_context. Chapter 2 instead gathers lending information through a conversation by the well.

**Impact**: Treating chapter_focus as the main chapter direction misleads the LLM.

**Root cause**:

`_suggest_chapter_focus()` in `webnovel-writer/scripts/data_modules/story_system_engine.py` returns the first dynamic_context card's `summary` when there is no explicit outline goal. Reasoning rankings place generic cards such as SP-087 first, contaminating chapter_focus with unrelated summaries. This is not `runtime_contract_builder.py` behavior.

**Fix**:

Together with #1, source chapter_focus from `directive.goal`. **Without a directive, use a non-placeholder query or leave it empty; never copy dynamic_context**.

**Acceptance criteria**:

`test_chapter_brief_contains_outline_directive` already covers outline-goal provenance. Add:

```python
def test_chapter_focus_never_taken_from_dynamic_context_summary(tmp_path):
    brief = build_chapter_brief(tmp_path, chapter=99)  # No chapter 99 in the outline
    # Without an outline, chapter_focus is empty or None, not an SP-card summary
    assert brief["override_allowed"].get("chapter_focus", "") == ""
```

**Effort**: Small, about 30 minutes within #1.

---

### Issue #6 — No Placeholder / Drift Guardrails in Setting Files (P2)

**Evidence**:

- Volume outline `volume-001-outline.md:25`: `First heroine (temporary name) | heroine | [TODO: define specifics during chapter-outline breakdown] | Chapter 20 onward`.
- Protagonist card: `Su Yun: first heroine...`.
- Heroine card: Complete Su Yun (`Su Yun`) profile.

The character cards were filled during a planning pass, but **the volume table remained at an older version without a subsequent consistency check**.

The protagonist card also contains:
- `[To be completed]`: A capable fighter but slow-thinking brotherly character, to appear in a later volume.

The omission may remain unnoticed until writing that volume.

**Impact**: Planning files drift apart; without pre-writing warnings, users miss unfinished items.

**Root cause**:

This is not a failed automatic writeback pipeline. **The system promises incremental updates to existing settings, but has no placeholder scan, cross-file consistency check, or pre-writing pending blocker.** `webnovel-plan/SKILL.md` explicitly requires incremental setting updates after volume outlining, but no corresponding guardrail exists.

**Fix**:

1. Add `webnovel-writer/scripts/data_modules/placeholder_scanner.py`:
   - Scan `outlines/*.md` and `settings/*.md` for:
     - `\[TODO[^\]]*\]` (e.g. `[To be completed]`, `[TODO: define specifics during chapter-outline breakdown]`, `[undecided]`).
     - `（temporary name）`, `(temporary name)`, `（To be completed）`.
     - Whole-field `{placeholder}` / `<placeholder>` blocks.
   - Return `{file, line, context, suggested_fill_phase}` for each placeholder.

2. Add checks **before** these workflows:
   - At `webnovel-plan` start/end: scan all planning files; warn without blocking.
   - At `webnovel-write` start: scan setting files for **entities relevant to this chapter**; **block on `[TODO...]`**.
3. Add user-invoked `webnovel.py placeholder-scan --project-root <dir>`.

**Acceptance criteria**:

```python
def test_placeholder_scanner_finds_pending_marks(tmp_path):
    f = tmp_path / "outlines" / "Volume 1-volume outline.md"
    f.write_text("First heroine (temporary name)| [TODO: define specifics during chapter-outline breakdown]")
    results = scan_placeholders(tmp_path)
    assert len(results) == 2
    assert any("（temporary name）" in r["pattern"] for r in results)
    assert any("[TODOchapter-outline" in r["pattern"] for r in results)

def test_write_chapter_blocks_on_pending_protagonist_card(tmp_path):
    # Card has [To be completed], but this chapter does not involve the entity → do not block
    # Card has [To be completed] and this chapter involves the entity → block
    ...
```

**Effort**: Small, about 2 hours.

---

### Issue #7 — Missing Minimal Cross-Volume Anchors After Current-Volume Planning (P2)

**Evidence**:

`outlines/master-outline.md:46-62`:

```
| volume number | volume-title | chapter range | core conflict | volume-ending climax |
| 1 | Debt to the King of Hell | Chapters 1-50 | <filled> | <filled> |
| 2 | | Chapters 51-100 | | |
...
| 20 | | Chapters 951-1000 | | |
```

The foreshadowing table has only two core threads plus an empty row.

**Impact**: Planning lacks a cross-volume view; each new volume starts from scratch and may disconnect from earlier promises/foreshadowing.

**Fix**:

1. **Do not generate V2-V20 rows during init**, avoiding empty-table clutter.
2. Define Phase 7 as **minimal cross-volume anchor writeback** after successful current-volume planning, not automatic detailed next-volume planning:
   - Trigger: `webnovel-plan` successfully completes the current volume and its planning artifacts are complete/validated.
   - Write only V+1 `volume-title`, `core conflict`, `volume-ending climax` (title, core conflict, ending climax).
   - Update the next-volume row in `outlines/master-outline.md`, appending it if absent.
3. Restricted foreshadowing append after each planned volume: only explicitly structured current-output items:
   - New foreshadowing.
   - Continuing open loops.
4. Explicit prohibitions:
   - No inference of foreshadowing/open loops from free text.
   - No next-volume detailed outline.
   - No next-volume beat sheet.
   - No next-volume timeline.
   - No pre-generated V2-V20 empty rows.

This fits the writing workflow: completion preserves only necessary cross-volume promises in the master outline, leaving creative space for formal next-volume planning.

**Acceptance criteria**:

```python
def test_plan_flow_writes_minimal_next_volume_anchor(tmp_path):
    plan_volume(tmp_path, volume=1)  # Represents webnovel-plan completing V1 planning
    # Master outline gains minimal V2 anchors, with no V3-V20 prefilled rows
    summary = (tmp_path / "outlines" / "master-outline.md").read_text(encoding="utf-8")
    assert "| 2 |" in summary
    v2_line = [l for l in summary.split("\n") if l.startswith("| 2 |")][0]
    assert v2_line.count("|") == 6
    assert "Volume 2-detailedoutlines.md" not in list_outline_files(tmp_path)
    assert "Volume 2-beat-sheet.md" not in list_outline_files(tmp_path)
    assert "Volume 2-timeline.md" not in list_outline_files(tmp_path)

def test_plan_flow_appends_only_structured_foreshadow_items(tmp_path):
    plan_volume(tmp_path, volume=1, structured_foreshadow=[
        {"type": "new_foreshadowing", "text": "the red seal on the back of the debt contract remains unexplained"},
        {"type": "continued_open_loop", "text": "Su Yun's identity and the origin of the debt to the King of Hell remain unresolved"},
    ])
    summary = (tmp_path / "outlines" / "master-outline.md").read_text(encoding="utf-8")
    assert "the red seal on the back of the debt contract remains unexplained" in summary
    assert "Su Yun's identity and the origin of the debt to the King of Hell remain unresolved" in summary
```

**Effort**: Medium, about 4 hours including `webnovel-plan` prompt/workflow changes.

---

### Issue #8 — Reviewed ai_flavor Patterns Do Not Feed anti_patterns (P2)

**Evidence**:

All ten entries in `Spiritstone Manor/.story-system/anti_patterns.json` came from reference initialization (`pitfalls` fields in GR-011 / NR-077 / CH-072 / SP-087 / RS-002).

Chapter 2 review identified:
- Three parallel repetitions of "the only person who knows X."
- A three-part enumeration of "the first piece / second piece / third piece."

**These patterns never entered anti_patterns.json.** Future chapters lack an avoidance list for sentence patterns already flagged in the previous chapter.

**Fix**:

1. Add a post-review-persistence hook in `webnovel-writer/scripts/data_modules/review_schema.py` or the corresponding location:
   ```python
   if issue["category"] == "ai_flavor" and issue["severity"] in ("medium", "high", "critical"):
       anti_patterns_store.append({
           "text": issue["evidence"][:200],
           "source_table": "review_extracted",
           "source_id": f"ch{chapter:04d}_issue_{issue_idx}",
           "category": issue["category"],
           "added_at": now_iso(),
       })
   ```
2. Inject anti_patterns `text` into pre-writing briefs as patterns to avoid.
3. Deduplicate identical evidence.

**Acceptance criteria**:

```python
def test_ai_flavor_review_issue_added_to_anti_patterns(tmp_path):
    save_review_report(tmp_path, chapter=2, issues=[{
        "category": "ai_flavor",
        "severity": "medium",
        "evidence": "the only person who knows the compound-interest formula。the only person who knows..."
    }])
    patterns = json.loads((tmp_path / ".story-system" / "anti_patterns.json").read_text())
    assert any("the only person who knows" in p["text"] for p in patterns)
    assert any(p["source_id"].startswith("ch0002_") for p in patterns)
```

**Effort**: Small, about 2 hours.

---

## 5. Full Regression Plan

After implementation:

1. All `pytest --no-cov` tests pass (currently 508 cases).
2. Rerun init in a new `Spiritstone Manor2` project and verify:
   - No `protagonist-team.md`, `special-power-design.md`, `hybrid-genre.md`, or `payoff-plan.md`.
   - No empty directories.
3. Rewrite chapter 1 and compare briefs:
   - `chapter_directive` must exist.
   - At least one dynamic_context item concerns lending/promissory notes/interest.
   - chapter_focus comes from chapter 1's outline goal.
4. After writing chapter 1, deliberately introduce an ai_flavor pattern and review; confirm an anti_patterns.json addition.
5. After completing/validating volume 1 planning, master outline gains only V2 title/core conflict/ending climax. No V2 detailed outline, beat sheet, timeline, or V3-V20 empty rows.
6. If current planning explicitly structures new foreshadowing/continuing open loops, append those entries to the master table. Do not infer entries from free-text hints.
7. Leave `[To be completed]` in a protagonist-card entry, then write chapter 50 involving that character; writing must block.

---

## 6. Risks and Known Limitations

- #1 outline parsing depends on stable Markdown chapter blocks. Support English headings such as `Chapter 1` with optional spacing. Match English chapter labels and numeric chapter identifiers; old heading formats are outside this branch's new-project contract.
- #6 scanning may mistake real bracketed prose (e.g. `\[source text\]`) for placeholders. Use a whitelist and strict patterns requiring Chinese `TODO` for pending placeholders.
- #7 V+1 writeback must remain minimal. Accept only structured title/conflict/climax from current planning; do not expand free text or generate detailed next-volume plans. Defer its detailed outline, beat sheet, and timeline until the user enters next-volume planning.
- The protagonist_state mirror fixed in f58d657 may interact with #1 directives: directive time_anchor and state.protagonist_state location.last_chapter must not be conflated. Explicitly separate namespaces when implementing #1.

---

## 7. Outside This Spec

| Type | Example | Responsibility |
|------|------|------|
| LLM writing defects | AI flavor, excessive habitual gestures, repeated sentence patterns | Already caught by review agent |
| User-unfilled init metadata | Empty heroine_names | User responsibility; UI should prompt |
| Model choice / context-window size | Large chapter cannot fit in one generation → incremental updates | Model/platform layer |
| Slow data-agent calls (NOT_FOUND retries) | See `data_agent_timing.jsonl` | Main cause fixed in f58d657 |

---

## 8. Recommended Implementation Order

1. Implement `load_chapter_execution_directive()` in `chapter_outline_loader.py`; use a minimal fixture for detailed-outline chapter 1 field extraction.
2. Integrate `chapter_directive` into `story_system.py` / `story_system_engine.py` brief assembly; prefer `directive.goal` for `chapter_focus`.
3. Update `webnovel-write/SKILL.md` so hard constraints / CBN-CPNs-CEN / forbidden content precede `dynamic_context`.
4. Add placeholder-query diagnostics to `story_system.py`; update real-query requirements in `webnovel-plan`, `webnovel-write`, and `webnovel-review`.
5. Add chapter-aware ranking in `story_system_engine.py`, using `goal/key_entities/strand/antagonist_tier`.
6. Change template lists in `init_project.py` and `webnovel-init/SKILL.md`; first complete single-protagonist / no-heroine / dead-template pruning tests.
7. Add `placeholder_scanner.py` and `webnovel.py placeholder-scan`; implement whole-project scanning first, then plan warnings.
8. Add the placeholder guardrail before writing, limiting blocking to current-chapter entities.
9. Update master-outline template and `webnovel-plan/SKILL.md`: remove V2-V20 empty rows; after validated current-volume planning, write only V+1 title/conflict/climax and explicitly structured new foreshadowing/continuing open loops.
10. Add deduplicated `ai_flavor` → `anti_patterns.json` feedback in `review_schema.py`; verify the next brief reads review-extracted avoidance patterns.
