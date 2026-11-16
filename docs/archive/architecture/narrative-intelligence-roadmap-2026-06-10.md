# Narrative Intelligence Upgrade Roadmap (2026-06-10)

> **Status (archived 2026-06-11):** This roadmap was absorbed into the v7 story repo specification and canceled as a standalone plan. Item destinations: M1-1 was rejected (v7 spec §13: information gaps and a timeline presence column replace the witnesses projection); M1-2 → promise-derived metrics (§5) + sentence-pattern diagnostics; M1-3 → style constitution, with vetoes promoted into constitutional rules (§6.1); M1-4 → memory-layer volume summaries (§4.6); M2-1 → diagnostic transactions (§9); M2-2 → three-lens review (§8); M3-1 → foreshadowing opportunity scans during volume retrospectives (§9); M2-3/M3-2/M3-3 were shelved under the freeze order. The ban on fully automated operation in this document's exclusions was revoked by spec 0.5 (§8.1); the specification takes precedence. See `docs/architecture/story-repo-spec-2026-06-10.md`.

> Source: 2026-06-10 full-project audit and architecture discussion of an “AI long-form webnovel writing system.”
> Prerequisite: Start after Phase 0/1 of `docs/superpowers/plans/2026-06-10-audit-fix-plan.md` (the remediation plan). Both modify the same modules; do not run them in parallel.

## Design Principles (Discussion Consensus)

1. **Three state layers**: factual state (already present: event log + projection + contract), narrative state (tension / information gaps / payoff pacing, the largest current gap), and stylistic state (verbal habits / voice / drift, the second gap). This roadmap targets the latter two.
2. **Do not use a model for deterministic checks**: Turn pacing rules into post-writing measurements rather than drafting instructions. Deterministic scripts calculate metrics; only threshold breaches trigger rework.
3. **More scripts, less model work**: Before each model call, deterministic code minimizes and sharpens context. Token costs are a hard constraint for real authors.
4. **Authorial taste is the only nonrenewable resource**: High-leverage decisions, including outline approval, arc turns, and foreshadowing setup/payoff, remain human decisions. The system learns from vetoes instead of requiring repeated corrections.

---

## M1 Near Term (Immediately After Remediation; Purely Incremental)

### M1-1 Character Knowledge Boundaries (Information-Gap Management)

**Motivation**: Suspense comes from differences between what the author, reader, and characters know. Existing review dimensions miss two subtle AI errors: leaks, where a character says something they cannot know, and redundant exposition that repeats information the reader already knows.

**Design**:
- The event log is already the event source of truth. Add optional `witnesses: [entity_id]` to `story_event_schema` for characters present or informed. Have data-agent annotate this during event extraction; without an annotation, default to “only characters present.”
- Add `knowledge_projection_writer` to accumulate each character's known-event set in a new `index.db` table: `entity_knowledge(entity_id, event_id, learned_chapter)`.
- At prewrite (`write_gates/prewrite.py`, or a new context-pack section `knowledge_boundaries`), inject the top-N key events each character present **does not know**, filtered by entity overlap with the chapter outline.
- Add deterministic review dimension `info_leak`: scan dialogue and internal monologue for entity and event keywords, compare against the speaking character's known set, and mark suspected leaks as warnings. Do not make them automatically blocking; observe false positives for one month first.

**Implementation locations**: `story_event_schema.py`, new `knowledge_projection_writer.py`, registration in `event_projection_router.py`, a new `context_manager.py` section, and a new `review_pipeline.py` checker.
**Acceptance**: In a test project with a conspiracy event that character A did not witness, A referencing the event in dialogue triggers an `info_leak` review warning.

### M1-2 Scripted Narrative Pacing Metrics (Post-writing Measurement, Not Pre-writing Lectures)

**Motivation**: Payoff density and hook strength currently exist as advisory SKILL prose that the model follows inconsistently. The `chapter_reading_power` table already stores hook_type/hook_strength, but no hard gate consumes it.

**Design**:
- Add `pacing_metrics.py`: given a chapter number, output deterministic metrics: chapters since main-plot advancement (`strand_tracker`), chapters since the last strong hook, payoff-event count in this chapter (payoff events in the event log), and consecutive transitional chapters.
- Add a soft gate to `write_gates/postcommit.py`: N consecutive chapters without a strong hook (default 3), or main-plot stagnation beyond a configured threshold, allows the commit but emits a prominent “pacing debt” warning and writes to the existing `chase_debt` table.
- In the `webnovel-review` SKILL, replace model-based pacing checks with reading `pacing_metrics` first. The model interprets the numbers rather than estimating them again.

**Implementation locations**: New `data_modules/pacing_metrics.py`, `write_gates/postcommit.py`, review SKILL step changes, and direct display in dashboard PacingPage (the frontend page skeleton already exists).
**Acceptance**: Four consecutive weak-hook chapters in test data produce a postcommit pacing-debt warning.

### M1-3 Generalize Overrides (Learn Rules From Vetoes)

**Motivation**: When an author repeatedly changes the same kind of expression, the system should learn a style rule rather than wait for a fourth correction. The override ledger and `project-memory add-pattern` already exist; the missing piece is their connection.

**Design**:
- Add `summarize_recurring(min_count=3)` to `override_ledger_service.py`: cluster overrides by category/target and output candidate rules for veto categories repeated at least three times.
- Add a closing instruction to the `webnovel-review` SKILL: call the command, and if candidates exist, ask the author, “You have repeatedly vetoed X. Should this become a persistent style rule?” After confirmation, write it to patterns in `project_memory.json` using the existing add-pattern command. Subsequent context packs automatically include it in preferences.

**Implementation locations**: `override_ledger_service.py`, review SKILL; no new storage.
**Acceptance**: Three similar overrides cause `summarize_recurring` to return a cluster.

### M1-4 Hierarchical Summaries (A Volume-Level Middle Layer)

**Motivation**: A volume-summary layer is missing between recent_summaries (full summaries of the latest three chapters) and story_skeleton (interval sampling). In an 800-chapter story, recalling medium-distance plot from 50–200 chapters earlier depends on RAG luck.

**Design**:
- At volume completion, through update_master_outline or the plan skill's volume retrospective, generate `.webnovel/summaries/volume_NN.md` within 500 Chinese characters: main-plot progress, relationship changes, and unresolved foreshadowing.
- Add `volume_summaries` to core in `context_manager._build_pack`, containing summaries of all volumes before the current one. At 500 characters per volume, even 30 volumes total only 15,000 characters, and older summaries can be further truncated.

**Implementation locations**: Plan SKILL volume-retrospective step and `context_manager.py`. Leave `summary_projection_writer.py` unchanged: the skill workflow, not a projection, generates volume summaries.
**Acceptance**: A project containing volume_01.md produces a context pack with a volume_summaries section.

---

## M2 Medium Term (After M1 Validation)

### M2-1 Stylistic Fingerprints and Drift Detection

**Motivation**: Context strategies cannot eliminate voice drift across thousands of chapters: drift accumulates even when each individual step is within tolerance. Periodic measurement and calibration are required. `style_sampler.py` already provides sampling foundations.

**Design**:
- Extend `style_sampler` with a `fingerprint` subcommand. For a chapter range, calculate sentence-length distribution (mean/variance/quantiles), dialogue proportion, top 20 verbal habits grouped by character, paragraph-length distribution, and punctuation density. Store results in a new `index.db` table: `style_fingerprints(range_start, range_end, metrics_json)`.
- Baseline: chapters 1–30, or the author's chosen best-feeling range. Every 50 chapters, automatically compare the latest window with the baseline. If KL divergence or simple percentage deviation exceeds the threshold, alert through doctor and dashboard with specific drift items, such as “protagonist's average dialogue sentence length +40%.”
- Add verbal-habit lists for the protagonist and core supporting characters to context-pack `voice_contract` before writing. On drift alerts, the author decides whether to pull back or accept the evolution and update the baseline.

**Acceptance**: Two deliberately different sets of chapters produce a fingerprint diff identifying sentence-length and verbal-habit shifts.

### M2-2 Split Review Personas

**Motivation**: A model that both writes and reviews shares its own blind spots. A single reviewer's evenly divided attention gives no dimension enough depth.

**Design**:
- Call the reviewer agent repeatedly through parameterized lenses, without adding agents: `--lens reader` (a sharp-tongued nonpaying reader who answers only whether it is satisfying, where they would swipe away, and whether they would abandon it); `--lens editor` (structure and commercial appeal); `--lens fact` (fact comparison only, with deterministic check results + contract as input).
- Lens adjudication: script results govern the fact lens, with the model only explaining them. Reader results never enter blocking, only reading_power / abandonment-risk annotations. The editor lens retains existing blocking semantics.
- Review SKILL workflow: deterministic checks → three lenses in parallel → aggregation. Explicitly exclude judging prose quality from every lens to prevent self-reinforcing model taste.

**Acceptance**: The three outputs for one test chapter are distinguishable. The reader lens contains no structural jargon; the editor lens contains no statements such as “this passage is not satisfying enough.”

### M2-3 Token Cost Budgets

**Motivation**: Multi-agent operation trades tokens for certainty, and million-character writing costs can discourage real authors. Context slimming on refactor/context-minimal-flow already reduces individual calls, but there is no aggregate view.

**Design**:
- `run_ledger` already records each SubagentRun. Extend it with prompt/output character counts as approximate tokens; add a per-chapter cost curve to `quality_trend_report`.
- Configure a per-chapter character budget with a generous default. Highlight over-budget chapters in yellow and list the largest calls, showing the author where the money goes without imposing hard limits.
- Add an experiment hook: run the same outline with `--profile minimal/full` context templates (`TEMPLATE_WEIGHTS` already supports multiple templates). Store review scores alongside costs and use evidence to choose how lean the default template should become.

**Acceptance**: `quality_trend_report` includes per-chapter cost and over-budget indicators.

---

## M3 Experiments (High Risk, High Reward; Validate as Separate Projects)

### M3-1 Long-Range Foreshadowing Opportunity Scans

**Motivation**: AI does not spontaneously decide to plant something that pays off 300 chapters later. Current foreshadowing depends entirely on explicit outline declarations. This is an open problem with substantial defensibility for whoever solves it.

**Design sketch**: Add an opportunity scan to the plan skill's volume-planning step. Inputs: unresolved foreshadowing, distant master-outline nodes, and this volume's chapter outlines. Ask the model for 3–5 candidates that can be naturally planted now and paid off N volumes later. Each must cite a specific distant master-outline node as its payoff target to avoid dangling setups. After the author selects candidates, write them to plot_threads.foreshadowing with target_chapter. **AI proposes; a human chooses.** No full automation.

**Validation**: Retain only if the author adopts at least one candidate per volume across two consecutive volumes; otherwise remove it.

### M3-2 Reader Simulator (Abandonment-Point Prediction)

**Design sketch**: Extend the reader lens (M2-2) with personas such as nonpaying readers, experienced genre readers, and female-market readers. Output a 0–100 abandonment risk and triggering passages for each chapter. Initially visualize trends only using the existing dashboard reading-power page. Decide whether to introduce gating only after 100+ chapters of human comparisons. Explicit role: advisory signal, never blocking.

### M3-3 Align Review Scores With Real Data (Long Term)

If the author publishes, correlate chapter follow-through/retention data, imported manually as CSV if necessary, with review scores and pacing_metrics through an extension to `quality_trend_report`. Give more weight to internal metrics that correlate most strongly with actual retention. Ultimately anchor the quality loop in reader behavior rather than model taste.

---

## Exclusions (Explicitly Rejected to Prevent Reintroduction)

- ❌ Full-text vectorization as the primary factual-recall route. Semantic similarity is not narrative relevance; vectors serve only style/scene references.
- ❌ Unrestricted model judgments of prose quality. Self-reinforcing taste makes the whole book increasingly AI-like.
- ❌ Fully automated unattended writing. Losing authorial taste removes the system's calibration source.
- ❌ New permanent agents. The existing four have clear responsibilities; prefer scripts or parameterized lenses on existing agents for new capabilities.

## Milestone Order and Dependencies

```text
Remediation Phase 0/1 -> M1-1 knowledge boundaries -> M2-2 review personas (fact lens consumes M1-1)
                     -> M1-2 pacing metrics -> M2-3 cost budgets (shared run_ledger/reporting)
                     -> M1-3 override generalization
                     -> M1-4 volume summaries -> M2-1 stylistic fingerprints (shared sampling infrastructure)
All M3 items are separate projects and may start after any M2 item is complete.
```
