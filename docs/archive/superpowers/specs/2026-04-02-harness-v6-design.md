# Webnovel-Writer Harness v6 Design

> Date: 2026-04-02 (updated 2026-04-09)
> Status: Draft v7 (v6 + implementation-alignment corrections; Phases 1/2A/3/4 complete)
> Based on: user feedback + issue #5 token analysis + a 23-item problem list

---

## 1. Ultimate Goal

Write a long-form webnovel of 500–2,000 chapters across multiple mainstream genres, with:

- Excellent prose and less AI-like writing
- Eventful, surprising plots, with AI leading ideation and the author reviewing afterward
- Consistent voice and continuity over long contexts
- Effective human–AI collaboration with room for author inspiration
- A stable system with reduced context consumption
- Appropriate error-correction mechanisms

## 2. Core Principles

- **Claude Code is the harness**: do not build another orchestration layer. Use native /resume, Task, subagent isolation, and automatic compaction.
- **The volume outline is the harness**: give the writing AI sufficient boundaries to prevent drift, loss of control, and forgetting.
- **Memory is the foundation**: continuity comes from the memory system, not outline nodes.
- **Subtract first**: remove steps that create no value rather than adding more process.

### 2.1 Out of Scope for the v6 Migration Baseline

These directions are confirmed but **outside the v6 migration baseline** to prevent scope creep:

- **Full Plan schema implementation**: the draft chapter-outline fields are reference material only; plan skill refactoring is Phase 6.
- **Examples throughout all references**: complete P0 methodology first; P1 may iterate later.
- **Underlying memory-storage refactor**: Phase 5; freeze the v0 contract first.
- **Iterative Init refinement**: await a detailed init design; it does not block the mainline.
- **Anti-AI mechanisms beyond blacklists**: Phase 7; use reviewer ai_flavor as the current fallback.

Priority: **converge the main workflow (remove → merge → freeze interfaces) and meet migration exit criteria**.

---

## 3. Problem List (23 Items)

### 3.1 Init

| # | Problem | Root Cause |
|---|---------|------------|
| 1 | References emphasize structure over examples | They teach format, not taste; the LLM knows the fields but not what good content looks like |
| 2 | No genre benchmarks | No examples from real novels showing a good world bible for few-shot guidance |
| 3 | Generation cannot iterate | Master outlines and setting documents are generated once without a refinement loop |

### 3.2 Plan

| # | Problem | Root Cause |
|---|---------|------------|
| 4 | Constrains exact events rather than direction and boundaries | An outline says “the protagonist rescues a girl named Duoduo,” is fully injected into the writer, and leaks spoilers |
| 5 | No volume-level narrative-function definition | Chapters lack explicit setup/development/turn/resolution roles within the volume |
| 6 | Time constraints are too explicit | Time anchors and countdowns in outlines are repeatedly mentioned in prose |
| 7 | Strand ratios hard-coded to 60/20/20 | Genres need different pacing; apocalyptic fiction cannot use the same ratios as sweet romance |
| 8 | Unclear downstream use of four output layers | Beat sheets, timelines, volume outlines, and chapter outlines exist, but writing actually consumes only chapter outlines |
| 9 | Quality declines across ten-chapter generation batches | Later chapters become formulaic |

### 3.3 Write

| # | Problem | Root Cause |
|---|---------|------------|
| 10 | Overweight pipeline | Eight steps plus workflow logging spend tokens on process instead of writing |
| 11 | context-agent is a token sink | All data is injected and a huge execution package is produced |
| 12 | Expensive review with little value | Six checkers each carry independent context and award 90 points while users dislike the result |
| 13 | Anti-AI controls need strengthening | Blacklists stop known verbal habits, not AI-like narrative structure, emotion, or rhythm |
| 14 | data-agent is too heavy | Nine substeps should be redesigned within the unified memory module |
| 15 | Writing and persistence are coupled | Persistence failure stalls the pipeline, although timing remains unchanged: persistence must finish before the next chapter |
| 16 | workflow_manager and resume skill are wasteful | Native Claude Code /resume already restores interrupted sessions |

### 3.4 Memory

| # | Problem | Root Cause |
|---|---------|------------|
| 17 | Six fragmented stores | state.json / index.db / scratchpad / summaries / vectors / snapshots are read and written separately |
| 18 | Layers do not match writing intuition | Organize by recency: recent details → medium-term summaries → distant active facts |
| 19 | Timeline is not the indexing axis | All memory should be time-indexed for queries such as a character's state at chapter N |
| 20 | Memory types need definition | Character state is mutable, world rules stable, foreshadowing has a lifecycle, and the timeline advances monotonically |

### 3.5 System-Wide

| # | Problem | Root Cause |
|---|---------|------------|
| 21 | Inconsistent Skill/Agent prompt formats | No common template; differing file structures obscure priorities for the LLM |
| 22 | References need cleanup and additions | Remove redundancy and add methodology, including real-novel positive/negative examples |
| 23 | Excessive token use | 3–5 million tokens per chapter; review costs the most while producing the least value |

---

## 4. Confirmed Design Directions

### 4.1 Removals

| Remove | Replacement |
|--------|-------------|
| workflow_manager.py | Native Claude Code /resume |
| resume skill | Native Claude Code /resume |
| Step 2B (separate style adaptation) | Merge into Step 4 polishing |
| Six independent checker agents | One unified review agent |
| Review scoring | Concrete code-review-style issue lists |
| memory_scratchpad.json (long-term memory system) | Redesign a unified memory module based on the remote version without long-term memory |

### 4.2 New Write Workflow

```text
Step 0.5 Preflight
  → Step 1 Context collection (context-agent, research mode)
  → Step 2 Drafting
  → Step 3 Review (one agent, code-review format)
  → Step 4 Polishing + style adaptation + anti-AI
  → Step 5 Data persistence (unified memory module, one call)
  → Step 6 Git backup
```

**Chapter-status model: monotonic progression, no regression**

| State | Entry Condition | May End Session | May Start Next Chapter | May Git Backup |
|-------|-----------------|:---:|:---:|:---:|
| `chapter_drafted` | Step 2 complete; prose draft exists | ✅ | ❌ | ❌ |
| `chapter_reviewed` | Steps 3–4 complete; no blockers and anti-AI recheck passed | ✅ | ❌ | ❌ |
| `chapter_committed` | Step 5 complete; memory persistence succeeded | ✅ | ✅ | ✅ |

Transition rules:

- Advance upon completion of Steps 2/4/5, writing `state.json.progress.chapter_status[NNNN]`.
- Step 5 failure does not roll back Steps 1–4. Remain at `chapter_reviewed`; do not start the next chapter.
- A session may end with persistence debt, but the next session must complete Step 5 first.
- Query: `python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" state get-chapter-status --chapter {N}`

### 4.3 New Context-Agent Mode

Replace all-at-once data injection and huge execution packages with research mode:

1. Call the combined memory interface for base context: chapter objective, character state, unresolved foreshadowing.
2. Determine what additional information the chapter needs.
3. Query independent memory interfaces as needed for character history, world rules, or the previous ending.
4. Confirm sufficiency, then output writing guidance in a fixed format.

### 4.4 New Review Mode

- Default to one agent receiving prose plus character state/world rules from memory.
- Output a structured issue list in code-review style.
- **Retain a split option**: if measurements show substantially lower ai_flavor detection or overloaded context, allow one lightweight specialized second check, such as ai_flavor only. Do not return to six agents.

**Minimal schema:**

```json
{
  "issues": [
    {
      "severity": "critical | high | medium | low",
      "category": "continuity | setting | character | timeline | ai_flavor | logic | pacing | other",
      "location": "Paragraph 3",
      "description": "The protagonist uses ability xxx, lost in chapter 15",
      "evidence": "Text: Xiao Yan activates technique xxx; memory: that ability was lost in chapter 15",
      "fix_hint": "Use currently available ability yyy instead",
      "blocking": true
    }
  ],
  "blocking_count": 1,
  "summary": "Found one blocking issue and two high-priority issues"
}
```

**Blocking rules:**

- `blocking=true` replaces the old `timeline_gate` semantics. Any blocking issue prevents entry into Step 4.
- `severity=critical` defaults to `blocking=true`; the reviewer decides for other severities.

**Blocking repair loop:**

- The main workflow, not reviewer, repairs blocking issues.
- Rerun the full Step 3 review after repairs to confirm no blockers remain.
- An explicit user override, such as judging a false positive, may skip re-review and enter Step 4. Record the override rationale in the review report.

**Lightweight metrics persistence:**

- Write every review to `index.db.review_metrics`: `chapter, issues_count, blocking_count, categories, severity_counts, timestamp`.
- Use it for trends: repeated issues of one category across N chapters indicate a systemic problem.
- Retain `overall_score` as a **derived compatibility field**, calculated by severity-weighted deductions, for sorting/trends only, **never gate decisions**.
- Gates always use `blocking=true` and issue details.
- The frozen `review-schema.md` governs storage. Observability emphasizes lightweight issues_count/blocking_count/categories; physical storage may retain overall_score/dimension_scores compatibility fields until dashboard/consumer migration is complete, then reconsider removal.

**Anti-AI responsibility split:**

- **Step 3 discovers** issues under category="ai_flavor" and lists them.
- **Step 4 repairs** each ai_flavor issue from Step 3.
- **After Step 4, an independent recheck is mandatory**. Default: rerun `reviewer` with only `ai_flavor` enabled. Step 4 may not judge its own pass/fail.
- An alternative check is equivalent only if all of these hold:
  1. Independent of Step 4; polishing cannot judge itself.
  2. Structured JSON output including `blocking_count`.
  3. Persisted, traceable results under `.webnovel/tmp/`.
- Rationale: avoid the bias of making changes and self-certifying success.

### 4.5 Memory Module (Two Delivery Stages)

**Stage A: Interface contract first, independent of storage**

Consumers, including context-agent, data-agent, and reviewer, depend only on this contract.

**v0: implemented and currently frozen**

> Implemented through `memory_contract.py` (Protocol + type definitions) and `memory_contract_adapter.py` (adapter), exposed through `webnovel.py memory-contract`, and already used by context-agent.

```python
# Combined interfaces
memory.commit_chapter(chapter: int, result: dict) -> CommitResult
memory.load_context(chapter: int, budget_tokens: int) -> ContextPack

# Independent interfaces, called as needed in context-agent research mode
memory.query_entity(entity_id: str) -> EntitySnapshot
memory.query_rules(domain: str) -> list[Rule]
memory.read_summary(chapter: int) -> str
memory.get_open_loops(status: str = "active") -> list[OpenLoop]
memory.get_timeline(from_ch: int, to_ch: int) -> list[TimelineEvent]
```

**v1: Phase 3 enhancement target, iterated after freezing v0**

- Replace `commit_chapter`'s `result: dict` with typed `CommitPayload`, explicitly defining chapter_file, review_result, entities, summary, etc.
- Add `intent: Literal["draft", "review", "repair"]` to `load_context` to tailor returned content.
- Refine `query_rules(domain: str)` to `domain: str, scope: str = "all"` for subdomain filtering.
- Include cross-cutting `source`, `chapter_range`, and `confidence` metadata in every return structure.

The v0→v1 upgrade changes CLI parameters and return richness, not upper-layer prompts.

**Stage B: Storage implementation later**

Confirmed direction:

- Recency layers: recent details → medium-term summaries → distant active facts
- Timeline as the indexing axis
- Memory types: mutable character state, stable world rules, lifecycle-based foreshadowing
- Specific implementation deferred for further consideration

### 4.6 Plan: Chapter-Outline Constraint Refactoring

The chapter outline serves as a harness, but the constraint form must change:

- **Constrain direction and boundaries**, not exact events.
- **Make time constraints implicit**: avoid fixed time anchors in the outline; transmit them indirectly through memory and validate after writing.
- **Use genre-specific Strand presets**, not hard-coded 60/20/20.
- **Define volume-level narrative function**: each chapter identifies its setup/development/turn/resolution role.
- Exact chapter-outline fields remain undecided.

**Minimal draft fields, pending validation:**

Content layer, the outline itself:

```json
{
  "chapter_goal": "The protagonist passes the trial and enters Jia Nan Academy",
  "must_payoff": ["The pill foreshadowing planted in chapter 3"],
  "forbidden_turns": ["The protagonist must not directly reveal the hidden identity"],
  "narrative_role_in_arc": "continuation",
  "strand_profile": "main_heavy",
  "time_pressure_source": "Enrollment deadline"
}
```

Consumption-policy layer, controlling how the outline reaches the writer rather than describing story content:

```json
{
  "writer_exposure_policy": {
    "verbatim_fields": ["chapter_goal", "must_payoff", "forbidden_turns"],
    "transform_fields": {
      "narrative_role_in_arc": "Convert to implicit pacing guidance; do not state the development role directly",
      "time_pressure_source": "Use only for validation; do not explicitly mention exact numbers or countdowns in prose"
    }
  }
}
```

Notes:

- `chapter_goal`: direction, not spoilers; do not specify “the protagonist rescues a girl named Duoduo.”
- `forbidden_turns`: explicit boundaries preventing drift.
- `strand_profile`: replaces hard-coded numeric ratios. genre-profiles defines weights, e.g. `main_heavy` = 70%+ main plot, `balanced` = balanced, `relationship_heavy` = relationship-led.
- `writer_exposure_policy`: separate from content and interpreted by context-agent during consumption; do not mix transport logic into the outline schema.

### 4.7 Unified Skill/Agent Prompt Template

Every skill/agent file uses this fixed structure:

```text
1. Identity and goal
2. Available tools/scripts, including invocation
3. Reasoning workflow (ReAct or another approach)
4. Inputs
5. Execution workflow: input → action → output for each step
6. Boundaries and prohibitions
7. Checklist
8. Output format
9. Error handling
```

### 4.8 References

**Remove** redundant references, obsolete documents, and duplicated shared references: 13 files total.

**Add** 16 P0 topics:

- Antagonist design, mirror antagonists, opponent progression, relationship dynamics
- Timeline design, long-form power progression, escalating antagonist pressure, foreshadowing setup/payoff
- Romantic progression, identity concealment/revelation
- Romantic tension, face-slapping payoffs, reversals, confrontation scenes
- Opening hooks and ending cliffhangers

**Requirements**: prioritize real-novel excerpts by reference tier:

- **P0 critical methodology** must include real-novel positive/negative examples for techniques directly affecting quality, such as retention hooks, reversals, and confrontations.
- **P1 secondary methodology** may initially use original or abstract examples, progressively replaced with real excerpts.

**Transform** existing genres/ and write/references/ files from structural templates into methodology + examples + counterexamples.

---

## 5. Unresolved Design Questions

| # | Question | Status |
|---|----------|--------|
| 1 | Memory implementation: layers, storage, interfaces | Deferred for further consideration |
| 2 | Exact chapter-outline fields defining direction/boundaries | Minimal draft in §4.6; finalize after actual planning validation |
| 3 | Anti-AI mechanisms beyond blacklists | Resolve during writing-prompt design |
| 4 | Exact context-agent writing-guidance output format | Await detailed write design |
| 5 | Collection of real-novel excerpts | Await user collection |
| 6 | Iterative Init refinement | Await detailed init design |
| 7 | Whether to retain beat sheets/timelines | Confirm downstream consumption |
| 8 | Optimal chapter-outline generation batch size | Requires experiments |
| 9 | Memory contract v0→v1 enhancements | Phase 3 details: typed CommitPayload, load_context intent, cross-cutting return metadata; see §4.5 |

---

## 6. Estimated Token Savings

> Directional estimates only; actual results depend on prose length, review rounds, and research hit rate. Validate with real execution logs.

| Stage | Current | Estimated After Optimization | Savings |
|-------|---------|------------------------------|---------|
| Review | ~2 million (6 agents × ~330,000) | 300,000–500,000, one agent including post-Step-4 ai_flavor recheck | ~75–85% |
| Context-agent | ~500,000, full injection | 100,000–200,000, on-demand retrieval | ~60–80% |
| Style adaptation | ~300,000, separate Step 2B | 0, merged into polishing | 100% |
| Workflow logging | ~50,000, 16 CLI calls | 0, removed | 100% |
| **Per-chapter total** | 3–5 million | **Estimated 800,000–1.5 million** | ~60–70% |

Assumptions:

- 2,000–2,500 Chinese characters per chapter
- No review blockers requiring rework
- context-agent research hit rate above 80%

---

## 7. Suggested Implementation Roadmap

| Phase | Work | Dependencies | Status |
|-------|------|--------------|--------|
| Phase 1 | Remove workflow/resume, consolidate review, merge Step 2B | None | **✅ Complete** |
| Phase 2A | Unified Skill/Agent prompt template and redundant-reference cleanup | None | **✅ Complete** |
| Phase 2B | Strengthen reference examples with real-novel excerpts | User-provided material | Undecided |
| Phase 3 | Memory-module interface contract | None | **✅ Complete** |
| Phase 4 | Context-agent research-mode refactor | Phase 3 contract | **✅ Complete** |
| Phase 5 | Memory storage implementation | Phase 3 contract + user design approval | Undecided |
| Phase 6 | Plan chapter-outline constraint refactor | Phases 4+5 | Undecided |
| Phase 7 | Anti-AI improvements + writing-prompt optimization | Phases 2A+4 | Undecided |

Phases 1/2A/3 may be explored in parallel, but require an **interface freeze** before merging. Freeze these first:

- `review-schema`: reviewer output and persisted metrics fields
- `memory-contract CLI`: memory interface signatures and return types

Only then do Phase 1/2A prompt changes have stable interfaces to depend on.

---

## 8. Migration Exit Criteria

The v6 migration is complete only when every condition holds:

1. **No runtime references to the six checkers remain**: no old names such as `continuity-checker` or `setting-checker` in skill/agent prompts.
2. **webnovel-write and webnovel-review use only reviewer**: one review path.
3. **All `workflow_manager` code is removed**: no imports, calls, or configuration remain.
4. **Eliminate legacy terminology by layer**:
   - Runtime references in skills/agents/scripts: **zero**.
   - Active prompt/skill-path references: **zero**.
   - Test fixtures / migration compatibility samples: permitted only within `evals/` or `tests/`.
   - Historical docs: permitted only with a `[deprecated]` label.
5. **At least one real project completes ten consecutive chapters**, validating:
   - No workflow-blocking exceptions across plan → write → review → data.
   - No state-write inconsistencies: monotonic chapter_status and consistent state.json / index.db.
   - No review/write/data contract mismatch: review-pipeline parses reviewer output correctly, and data-agent artifacts satisfy memory v0.
6. **Chapter status is implemented in state.json**: CLI queries expose `chapter_drafted` / `chapter_reviewed` / `chapter_committed`, with atomic transitions by Steps 2/4/5.
