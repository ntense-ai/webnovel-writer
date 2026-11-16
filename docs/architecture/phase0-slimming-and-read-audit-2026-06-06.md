# Phase 0 Audit: Slimming and Reading-Method Inventory (2026-06-06)

> Read-only audit and measurements. This document records traceable conclusions only; it changes no skill / agent / reference / test files.
> Purpose: Turn the four trimming criteria in Section 4, the responsibility table in §4.2, and the reading methods in §6.2 of `context-minimal-writing-flow-plan-2026-06-05.md` (the Plan) into an actionable checklist for each slimming phase.
> Rather than repeat the Plan, provide actionable rows: file → reading method / ownership / task.
>
> Working directory (Git repository root = worktree): `D:/wk/novel skill/webnovel-writer/.worktrees/context-minimal-flow`
> Plugin directory (nested): the `webnovel-writer/` subdirectory beneath the repository root. All paths below are relative to the plugin directory.
> Line counts were measured using `wc -l` (2026-06-06, local Bash), not copied from the Plan's prefilled figures.

---

## Usage

- **Section A** covers every directly Read Markdown entry in the reference-loading-map from Plan §6.2.1 and assigns a reading method. Phase 4 (Tasks #13/#14) uses this to change loading and remove dead files.
- **Section B** covers 8 Skills and 4 Agents, identifying essentials to retain and material to compress using the responsibility table in §4.2. Phases 1–5 (Tasks #5–#16) use this for slimming.
- Four reading categories (criterion four + §6.2.2): **full-file read** / **section read** / **retrieval read** (CSV, listed separately in A.3) / **do not read** (cleanup candidates).
- Section-read anchors are **literal headings from the files** (verified with Grep `^#{1,4} `). The Plan abbreviates anchors (removing `、` and shortening titles), so they **do not match actual headings verbatim**. Match this table's real anchors when reading sections; otherwise `Grep ^## one ` will not match `## one、`. See the anchor-validation and FLAG discussion below. This historical audit describes the anchors used at the time; recheck the current English headings before using an anchor.

---

## Section A — Reading-Method Audit (Each Directly Read Markdown File)

Line counts are measured. Assigned tasks: section reads for large target files = #13; dead-file cleanup = #14; other on-demand / full reads follow the consuming Skill's slimming task (Section B). Reading methods do not get separate tasks, but are recorded together in the Phase 4 loading-map (#13).

### A.1 Seven Large Target Files (Section Reads → Task #13)

Large Markdown files triggered `always` or frequently impose a recurring cost on every init / plan / write run. Each anchor has been verified with Grep.

| File | Measured lines | Reading method | Section: actual stable heading anchor (literal) | Assigned task |
|---|---|---|---|---|
| `references/genre-profiles.md` | 696 | Section read | The **single** `### 2.x` for the current genre (`### 2.1`…`### 2.13`, 13 genres at about 44 lines each); optionally add `## one、Profile fielddescription`. One genre per book → about 90% saved | #13 |
| `skills/webnovel-init/references/creativity/selling-points.md` | 687 | Section read | `## 9. coreselling-point positioning template` (skeleton); optionally add  `### 1.3 corecore selling-point formula`、`## 7. practical checklist` | #13 |
| `references/reading-power-taxonomy.md` | 361 | Section read | As needed, read  `## one、hook type` / `## two、payoffpattern` / `## three、immediate gratification/micro-payoff` | #13 |
| `skills/webnovel-plan/references/outlining/chapter-planning.md` | 322 | Section read | `## 10. structurenode specification（CBN/CPNs/CEN）` (L299 to EOF); when a template is needed, add  `## 7. chapterplanning template` | #13 |
| `skills/webnovel-init/references/creativity/creativity-constraints.md` | 327 | Section read | For score display, read  `### 8.1 five-dimensional scoring` (L262, about 10 lines); for idea collection, read  `## one、idea package Schema (Idea Package)` / `## six、creativity driven by hard constraints (Hard Constraints)` / `## eight、scoring system (Scoring System)` | #13 |
| `skills/webnovel-write/references/polish-guide.md` | 351 | Section read | Main path `## 2. execution order（must run in order）`; separate Anti-AI vocabulary section  `## 98:Phase 1 addendum：Anti-AI specification` (also `## 2A. Anti-AI detailed detection rules`). **Must not be itemized into CSV (hard boundary in csv/README)** | #13 |
| `references/shared/cool-points-guide.md` | 313 | Section read | Required payoff-dimension section; for genre adaptation use  `## nine、genreadaptation` (L194), selecting the relevant genre | #13 |

> Section-read technique: use `Grep` content output matching `^#{1,4} ` to get anchor line numbers, then `Read` with offset/limit. Both are built into Claude Code and platform-independent.

### A.2 Other Directly Read Markdown Files (Full / Section / Do Not Read)

Criteria: ≤ ~150 lines and requiring whole-document understanding → full read; clearly large, only one section needed, and triggered on demand / when X is needed in the Plan → section read; not currently called directly → do not read.

| File | Measured lines | Reading method | Section: actual anchor (if section read) | Assigned task |
|---|---|---|---|---|
| **webnovel-init** | | | | |
| `skills/webnovel-init/references/system-data-flow.md` | 43 | Full read | — | #10 |
| `skills/webnovel-init/references/genre-tropes.md` | 183 | Section read | Current-genre section (genre trope library; select by genre) | #10 |
| `skills/webnovel-init/references/worldbuilding/world-rules.md` | 86 | Full read | — | #10 |
| `skills/webnovel-init/references/worldbuilding/faction-systems.md` | 179 | Section read (on demand) | Triggered always but long; select sections needed for the current world | #10 |
| `skills/webnovel-init/references/worldbuilding/power-systems.md` | 160 | Section read (on demand) | Triggered only for power-system items; select the relevant subsection | #10 |
| `skills/webnovel-init/references/worldbuilding/character-design.md` | 111 | Full read | — | #10 |
| `skills/webnovel-init/references/worldbuilding/setting-consistency.md` | 215 | Section read | Triggered always but long; select consistency-check subsections | #10 |
| `skills/webnovel-init/references/creativity/creative-combination.md` | 510 | Section read | **Not among the 7 targets, but 510 lines**: trigger only when creative combinations are needed; select by current combination axis; full reads prohibited | #10 |
| `skills/webnovel-init/references/creativity/inspiration-collection.md` | 298 | Section read | Triggered only by Step1.5 inspiration-source questions; select the required collection subsection | #10 |
| `skills/webnovel-init/references/creativity/anti-trope-game.md` | 170 | Section read (on demand) | Triggered only for game genre + anti-trope needs; select the relevant anti-trope item | #10 |
| `skills/webnovel-init/references/creativity/anti-trope-rules-mystery.md` | 214 | Section read (on demand) | Triggered only for rules-mystery genre | #10 |
| `skills/webnovel-init/references/creativity/anti-trope-urban.md` | 169 | Section read (on demand) | Triggered only for urban genre | #10 |
| `skills/webnovel-init/references/creativity/anti-trope-xianxia.md` | 159 | Section read (on demand) | Triggered only for xianxia genre | #10 |
| **webnovel-plan** | | | | |
| `templates/output/outlines-volume-beats.md` | 38 | Full read | — Template; must be applied as a whole | #11 |
| `templates/output/outlines-volume-timeline.md` | 51 | Full read | — Template; must be applied as a whole | #11 |
| `references/shared/strand-weave-pattern.md` | 111 | Full read | — Plan §6.2.2 explicitly keeps full reads for short files | #11 |
| `references/outlining/plot-signal-vs-spoiler.md` | 53 | Full read | — | #11 |
| `skills/webnovel-plan/references/outlining/conflict-design.md` | 277 | Section read | Triggered only when conflict guidance is needed; select the relevant conflict-type subsection | #11 |
| `skills/webnovel-plan/references/outlining/genre-volume-pacing.md` | 84 | Full read | — Short; read all volume-level pacing guidance | #11 |
| **webnovel-write** | | | | |
| `skills/webnovel-write/references/writing/typesetting.md` | 60 | Full read | — Step4 always; short | #5 |
| `skills/webnovel-write/references/style-adapter.md` | 71 | Full read | — Step4 always; short | #5 |
| **webnovel-review** | | | | |
| `references/shared/core-constraints.md` | 111 | Full read | — Always-loaded hard rules; read in full | #8/#12 |
| `references/review-schema.md` | 59 | Full read | — Schema; read in full | #8/#12 |
| `references/review/blocking-override-guidelines.md` | 47 | Full read | — On demand; short | #12 |
| **webnovel-query** | | | | |
| `skills/webnovel-query/references/system-data-flow.md` | 343 | Section read | Long; select the data-source-priority subsection by query type | #15 |
| `skills/webnovel-query/references/advanced/foreshadowing.md` | 120 | Full read | — On demand; full read for foreshadowing queries | #15 |
| `skills/webnovel-query/references/tag-specification.md` | 154 | Full read (borderline) | — 154 lines; tag specification requires a full read; may become a section read if only one section is proven necessary | #15 |

> Both plan/review directly Read `cool-points-guide.md` (313) and `strand-weave-pattern.md` (111): the former is already a target section read in A.1; the latter is a full read. Apply the same decision across Skills.

### A.3 Retrieval Reads (CSV-Backed; Listed Separately from Direct Markdown Reads)

Plan §6.2.1 explicitly says the CSV pipeline is already correct and should not be redone. Record it here **without refactoring**; retain its current behavior in the Phase 4 loading-map.

| Data source | Reading method | Invocation | Notes |
|---|---|---|---|
| `references/csv/scenes.csv` | Retrieval read | `reference_search.py --table scenes --query ... --genre ...` | write Step2 combat/confrontation/plot beats; replaces retired Markdown such as combat-scenes |
| `references/csv/techniques.csv` | Retrieval read | `reference_search.py --table techniques --query ...` | write Step2 dialogue/emotion; replaces dialogue-writing / emotion-psychology |
| `references/csv/genre-routing.csv`、`adjudication.csv` and 8 tables in total | Retrieval read (indirect) | `story-system` internal `_route()` / `_collect_tables()` / `_load_reasoning()` | init/write consume indirectly through story-system; already on demand |

> Existing CSVs: `adjudication / scenes / powers / naming / tropes / characters / pacing / genre-routing / techniques` (9 tables)+ `genre-canonical.md` + `README.md`。

### A.4 Do Not Read (Phase 4 Cleanup Candidates → Task #14)

Items not currently called directly in the loading-map, plus writing/* migration candidates named in Plan §6.2.3. Approximately 1402 lines of dead content in total (measured). First verify CSV coverage; delete covered files or leave stubs pointing to CSV. For uncovered content, extend CSV before cleanup.

| File | Measured lines | Current state / CSV replacement | Assigned task |
|---|---|---|---|
| `skills/webnovel-write/references/writing/combat-scenes.md` | 229 | Combat triggers now use `scenes.csv`; not directly Read | #14 |
| `skills/webnovel-write/references/writing/dialogue-writing.md` | 231 | Dialogue triggers now use `techniques.csv` | #14 |
| `skills/webnovel-write/references/writing/emotion-psychology.md` | 265 | Emotion triggers now use `techniques.csv` | #14 |
| `skills/webnovel-write/references/writing/scene-description.md` | 263 | Named in Plan §6.2.3; not directly Read; verify `scenes.csv` coverage before cleanup | #14 |
| `skills/webnovel-write/references/writing/desire-description.md` | 311 | Same as above; verify CSV coverage before cleanup | #14 |
| `skills/webnovel-write/references/writing/genre-hook-payoff-library.md` | 85 | Named in Plan §6.2.3; not directly Read; verify CSV coverage before cleanup | #14 |
| `skills/webnovel-write/references/style-variants.md` | 38 | Not directly called | #14 |
| `skills/webnovel-review/references/common-mistakes.md` | 96 | Not directly called | #14 |
| `skills/webnovel-review/references/pacing-control.md` | 129 | Not directly called | #14 |

> `scene-description.md` (263), `desire-description.md` (311), and `genre-hook-payoff-library.md` (85) **all exist and are not currently directly Read**. Include them in cleanup verification as required by the Plan.
> Other existing references with no explicit action this round (not directly Read, not named by the Plan): `skills/webnovel-write/references/anti-ai-guide.md` (74; content merged into polish-guide §98/§2A; verify whether dead in #14)、`skills/webnovel-init/references/init-collection-schema.md` (74; Plan §6.2.4 designates this the source for init section reads; **retain**)、`skills/webnovel-init/references/creativity/market-positioning.md` (424; not registered as directly Read; verify in #14)、`references/shared/naming-and-voice-gaps.md`(63)、`skills/webnovel-plan/references/outlining/outline-structure.md`、`plot-frameworks.md` (not registered as directly Read; verify consumers in #13/#14)。

### A.5 Anchor Validation and FLAG

All 7 target anchors were verified with Grep `^#{1,4} ` to **exist**. None are missing. Note differences between Plan abbreviations and real headings (matching differences, not missing anchors; section reads must use the right-hand column):

| File | Wording in the Plan | Actual heading (match this for section reads) |
|---|---|---|
| genre-profiles | 「one、fielddescription」 | `## one、Profile fielddescription` |
| reading-power-taxonomy | 「## one hook type / ## two payoffpattern / ## three micro-payoff」 | `## one、hook type` / `## two、payoffpattern` / `## three、immediate gratification/micro-payoff` |
| selling-points | 「### 1.3」「## 7」「## 9」 | `### 1.3 corecore selling-point formula` / `## 7. practical checklist` / `## 9. coreselling-point positioning template` |
| chapter-planning | 「## 10 …」「## 7」 | `## 10. structurenode specification（CBN/CPNs/CEN）` / `## 7. chapterplanning template` |
| creativity-constraints | 「### 8.1」「one Schema / six hard constraints / eight score」 | `### 8.1 five-dimensional scoring` / `## one、idea package Schema (Idea Package)` / `## six、creativity driven by hard constraints (Hard Constraints)` / `## eight、scoring system (Scoring System)` |
| polish-guide | 「## 2 execution order」「Anti-AI vocabulary section」 | `## 2. execution order（must run in order）` / `## 98:Phase 1 addendum：Anti-AI specification` (also `## 2A. Anti-AI detailed detection rules`) |
| cool-points-guide | 「## nine genreadaptation」 | `## nine、genreadaptation` |

**FLAG: No missing anchors.** The only caveat: the Plan removes the Chinese enumeration delimiter `、` and shortens headings, so literal `Grep` can miss them. Phase 4 section reads and loading-map entries must use the actual headings in the right-hand column.

---

## Section B — Component Ownership (8 Skills + 4 Agents)

Based on the responsibility table in §4.2. Layer indicates the main-agent contract shape (Skill), subagent (Agent), or runtime boundary. Each cell is one sentence; cross-reference the Plan for details rather than repeating it.

| Component | Layer | Essentials to retain (one sentence) | Main compression / relocation opportunities (one sentence) | Assigned task |
|---|---|---|---|---|
| `skills/webnovel-write/SKILL.md`（202） | Skill: main-agent contract shape | Three modes + preparation chain + invocation contracts for three Agents + three gates/commit/postcommit/backup (§3.4, §8.2); add read-only precommit `git diff` (§5.2 B) | Move context/reviewer/data internal tutorials, data payload schema, and long polishing tutorials to Agent/reference (§8.3) | #5 |
| `agents/context-agent.md`（181） | subagent | Five-section writing brief + `memory-contract load-context` + on-demand queries + `.story-system` priority + blockers (§9.1) | Remove long examples, over-detailed inference guidance, and terminology explanations (§9.1) | #6 |
| `agents/data-agent.md`（120） | subagent (including the authoritative full artifact schema) | Minimum top-level/nested fields for three artifacts + no state/projection writes (§9.2, §4.3); `tools` includes `Write` | Compress long event_type payload descriptions, JSON examples, and legacy-field explanations (§9.2) | #7 |
| `agents/reviewer.md`（135） | subagent | Five-dimensional `dimension_results` (including passes) + evidence/fix_hint + strict JSON, no scores (§9.3); no `Write` permission, return JSON only | Remove chain-of-thought/ReAct metanarrative and lengthy review tutorials (§9.3; §12.2 loosens section-number tests) | #8 |
| `agents/deconstruction-agent.md`（296） | subagent | quick/deep/auto routing + no file writes + no invented canon + `init_reference_research`/quality/contamination prevention (§9.4, §3.2) | Compress long quality-gate tables, oversized schema, and detailed phased deep-analysis guidance (§9.4) | #9 |
| `skills/webnovel-init/SKILL.md`（402） | Skill: main-agent contract shape | Full §3.2 chain: Step1.5 inspiration questions, deconstruction invocation boundary, no canon writes before confirmation, root safety, idea_bank, patch master outline, MASTER after init, validation/rollback (§10.1) | Collection fields → section reads of `init-collection-schema.md`; consolidate genres, shrink CLI tables, load creativity/anti-tropes/worldbuilding on demand (§10.1, §6.2.4) | #10 |
| `skills/webnovel-plan/SKILL.md`（394） | Skill: main-agent contract shape | Full §3.3 chain: placeholder-scan, cross-volume state, settings baseline, beat sheet/timeline/volume outline/batch chapter outlines, settings writeback, master-outline writeback JSON, master-outline-sync, update-state, refresh contracts using actual CHAPTER_GOAL (§10.2) | CBN/CPN/CEN rules → section reads of `chapter-planning.md` §10; trigger long reference tables by phase; relocate node examples (§10.2, §6.2.4) | #11 |
| `skills/webnovel-review/SKILL.md`（170） | Skill: main-agent contract shape | Full §3.5 chain: story-system for missing contracts, reviewer invocation, `review-pipeline --save-metrics`, `update-state --add-review`, user decisions on blocking findings (§10.3) | Do not expand reviewer methodology / evidence queries in the Skill (§10.3) | #12 |
| `skills/webnovel-query/SKILL.md`（109） | Skill: main-agent contract shape (read-only) | Read-only + root protection + source priority (`.story-system`→accepted commit→memory-contract→projection) + degradation explanation (§11.1, §3.6) | Replace default full `load-context` with the narrowest query-specific tool (entity-state/relationships/query-rules/open-loop) (§11.1) | #15 |
| `skills/webnovel-learn/SKILL.md`（82） | Skill: main-agent contract shape | Root protection + read current chapter number + `project-memory add-pattern` + no handwritten JSON (§11.2) | Already minimal; little to compress; retain (§11.2) | #16 |
| `skills/webnovel-dashboard/SKILL.md`（101） | Skill: main-agent contract shape (read-only) | Read-only boundary + `story-runtime/health` + root resolution + dist validation (§11.3) | Do not install dependencies by default (show commands if missing); lightweight prelaunch checks (§11.3) | #16 |
| `skills/webnovel-doctor/SKILL.md`（70） | Skill: main-agent contract shape (read-only) | Run `project-status` first + stage-aware `doctor` + no repairs/installation/dashboard launch (§11.4, §3.6) | Change frontmatter description to a concise Chinese trigger description (§11.4) | #16 |

> The runtime layer (`webnovel.py` commands, artifact_validator, write-gate, chapter-commit, projection) owns schema/gate/commit/projection/backup/state advancement and is outside this prompt-slimming scope. Skills/Agents retain only invocation shapes; validation stays in the runtime (§4.2, §4.5 write-ownership matrix).
> Agent single-file constraint (§4.3): all 4 Agents remain single `agents/*.md` files; do not add `agents/references/*`. Their artifact schemas remain authoritative in those single files (especially important for data-agent).

---

## Size Summary (Measured)

- 8 Skills total **1530 lines** (write 202 / init 402 / plan 394 / review 170 / query 109 / learn 82 / dashboard 101 / doctor 70); init and plan are the largest and the main focus of §10.
- 4 Agents total **732 lines** (context 181 / data 120 / reviewer 135 / deconstruction 296); deconstruction is largest.
- 7 target references total **3057 lines** (section reads greatly reduce recurring per-book context; a single genre saves about 90% of genre-profiles).
- Do-not-read cleanup candidates total **about 1402 lines** (9 core candidates in A.4, pending CSV coverage verification).
- Reading distribution: 7 target section reads; 11 section reads in A.2; 15 full reads (templates/schemas/hard rules/short files); 3 CSV retrieval categories (unchanged); 9 do-not-read items (plus several suggested checks).
