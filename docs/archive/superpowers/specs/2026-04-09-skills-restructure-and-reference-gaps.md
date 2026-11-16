# Webnovel Writer Skills Restructuring and Reference Gap Design

> Date: 2026-04-09
> Status: draft v4.3 (v4.2 + three corrections from Codex's second review)
> Goal: restructure `skills/`, assuming Claude already has general intelligence and writing ability, and identify gaps for later `references/` completion.

---

## 1. Why a new spec?

### 1.1 Relationship to the v6 spec

This spec **supplements**, not replaces, `2026-04-02-harness-v6-design.md` (v7).

- **v6 spec**: main-workflow architecture, deprecation/consolidation, state machine, memory contract, review workflow, and migration exit criteria. Phases 1/2A/3/4 are complete.
- **This spec**: consolidation of the documentation system after v6: slimmer skills and reference design/gap filling.
- **Reference design principles** (progressive disclosure, three content layers, on-demand loading, dual-track knowledge base, etc.) are governed by this spec.

Inherited unchanged from v6:
- Write Steps 0.5–6 and state machine
- Single reviewer agent + blocking-fix loop
- Memory contract v0/v1 interfaces
- Draft chapter-outline fields and layered `writer_exposure_policy`

### 1.2 Current problems

The earlier harness v6 spec mainly addressed migration, now largely complete. The real problem has shifted from missing main-workflow capabilities to insufficient documentation consolidation:

1. `skills/` mixes styles: mainline SOPs, command manuals, and miniature specs.
2. `references/` has unstable responsibilities: some repeat what Claude knows, while others omit crucial constraints addressing model weaknesses.
3. Boundaries among skills, references, and scripts are unclear, causing duplication, maintenance cost, and unclear expansion priorities.
4. Insufficient compensation for Chinese web-fiction model weaknesses: reused names, formulaic plot reuse, genre-vocabulary drift, converging dialogue voices, etc.

A new spec should move beyond migration and answer:

**Assuming Claude is already sufficiently intelligent, which minimum skills does this system need, and which reference gaps are worth filling?**

---

## 2. Core design philosophy

### 2.1 Claude is sufficiently intelligent

Assume Claude already has these abilities; skill documents need not reteach them:
- General writing
- General summarization, extraction, and polishing
- Common narrative techniques and characterization knowledge
- Ordinary software engineering and file I/O
- General skills in asking users questions, organizing steps, and checking work

Skills and references should not carry this general knowledge.

### 2.2 Document only what Claude handles inconsistently, does not know, or often gets wrong

Retained content must meet at least one criterion:
- **Project-private knowledge**: repository-specific state fields, CLI, paths, contracts, artifact locations.
- **Model-weakness compensation**: frequent mistakes not reliably solved through general knowledge.
- **Genre/platform-specific constraints**: Chinese web-fiction requirements, style preferences, prohibitions.
- **Workflow gates**: explicit step order, validation conditions, recovery.
- **High-value references**: real examples, counterexamples, naming rules, anti-template constraints.

Information meeting none should generally not appear in skills or references.

### 2.3 Four reference-design principles

These govern every decision to add, retain, or remove references.

#### Principle 1: Progressive disclosure

Organize references not by knowledge topic, but by the guidance needed during a particular skill's particular step.

- Map every reference to at least one specific skill + step **where possible**.
- For cross-skill weakness compensation, specify **primary** and **secondary use cases**.
- Skill loading strategies must say “At Step N, load reference Y when condition X occurs”.

#### Principle 2: Three content layers

Within each reference:

| Layer | Nature | Description | Example |
|------|------|------|------|
| **Reminder** | Claude knows it but forgets or applies it inconsistently during long-form writing | Lightweight “do not forget” items | Do not make everyone speak formally; do not end every paragraph with a summary |
| **Weakness compensation** | Systematic weaknesses that general knowledge does not solve | Explicit prohibitions, alternatives, and criteria | Naming homogenization guard; replacing formulaic slow/bland/slight adverbs; four-part closed-loop detection |
| **Knowledge supplement** | Claude knows the area but not deeply or completely enough | Chinese web-fiction techniques, patterns, positive/negative examples | Retention hooks, genre-specific pacing, real novel excerpts |

Arrange layers top to bottom; trim loading depth according to token budget.

#### Principle 3: Conditional on-demand loading

Load references only when the current chapter/task actually triggers their scenario.

- No combat → no combat reference.
- No first appearance of a new character → no naming reference.
- No time jump → no temporal-transition reference.

The loading strategy must state **triggers**, not “load everything every time”.

#### Principle 4: Align granularity with stable problem domains

**Markdown**: organize around stable problem domains and decision points, not mechanically tiny fragments. Split further only when scenarios genuinely conflict.

**CSV retrieval**: one result set should match one subtask's granularity. A CSV may contain multiple subtask types, filtered by retrieval.

- Naming needed → return naming entries only.
- Combat description needed → return combat entries only.
- Do not expand into related but currently unnecessary knowledge.

### 2.4 Better gap coverage, not fewer references

This round does not aim to reduce reference count. The criterion is:

**Does the reference genuinely address a Claude reliability gap or a project-private knowledge gap?**

Therefore:
- Remove or merge redundancy.
- Add missing references when the omission reliably causes mistakes.
- Explain the precise gap each new reference fills.

Reasonable additions include:
- Character naming rules
- Genre-specific naming prohibitions
- Distinct dialogue voices in Chinese web fiction
- Common genre-template voice and pitfall checklists

### 2.5 Skills are workflow entrypoints, not encyclopedias

`SKILL.md` handles:
- Applicable scenarios
- Execution order
- Required inputs/outputs
- When to read which references
- Validation and recovery rules

It does not handle:
- Extensive general methodology
- Complete example libraries
- Script internals in detail
- Miniature full-book tutorials

### 2.6 Chinese and web-fiction terminology first

This historical design serves Chinese web-fiction writing; documentation should prioritize its domain vocabulary:
- Chinese prose by default.
- Prefer domain terms: chapter/volume outline, hook, gratification beat, micro-payoff, reader retention, canon contradiction, reader-alienating pitfall, setting conflict, etc.
- Preserve necessary English in field names, CLI subcommands, frontmatter, JSON keys, and protocol names.
- Prefer one primary name per concept.

#### Chinese genre taxonomy

Existing `genres/` uses English names (`xuanhuan`, `realistic`, etc.); this round standardizes on Chinese genre names. **The first version uses Fanqie Novel's taxonomy as the default mapping baseline**, with extensible platform mappings later.

**Male-oriented categories:** Urban, xuanhuan, xianxia, fantasy, wuxia, history, military, science fiction, mystery, gaming, sports, and light novels.
**Female-oriented categories:** Contemporary romance, historical romance, fantasy romance, mystery, and light novels.

The CSV `applicable_genres` column uses these exact Chinese names. `all` means all genres.

Existing directory mappings:

| Current directory | Fanqie genre identifiers |
|-----------|------------|
| `xuanhuan/` | xuanhuan |
| `realistic/` | urban |
| `dog-blood-romance/` | contemporary-romance |
| `rules-mystery/` | mystery |
| `period-drama/` | historical-romance, historical |
| `zhihu-short/` | short-fiction / light novel (temporary mapping) |

---

## 3. Documentation-layer responsibilities

Restructure only three layers this round:
- `skills/`
- `references/`
- `scripts/`

### 3.1 Skills

Responsible for:
- Task entrypoints and applicable scenarios
- Main workflow steps
- Prerequisites
- Necessary-reference loading strategy
- Deliverables and success criteria
- Recovery and rerun rules

Not responsible for:
- Extensive methodology lessons
- Complete case libraries
- Reteaching general model knowledge
- Repeated explanations of underlying scripts

### 3.2 References

Responsible for, under §2.3:
- Subtask guidance bound to a specific skill + step
- Frequent unstable model weaknesses (compensation layer)
- Known but easily forgotten execution points (reminder layer)
- Insufficiently deep domain knowledge (supplement layer)
- Project-private standards (CLI, fields, paths)
- High-value examples/counterexamples (real novel excerpts)
- Genre-specific rules and prohibitions

Not responsible for:
- General writing knowledge Claude already applies reliably
- Broad, empty methodology surveys
- Structural templates without criteria
- Knowledge accumulation unbound to any step

### 3.3 Scripts

Responsible for:
- Error-prone but executable, verifiable stable operations
- Programmable data processing, validation, generation, migration, indexing

Not responsible for:
- Replacing skill workflow design
- Carrying main business explanations
- Replacing reference explanations of domain rules

### 3.4 When to script

Evaluate scripting before expanding a skill/reference if any applies:

1. Multiple skills repeat the same operation.
2. Success/failure can be determined programmatically.
3. Manual explanation is lengthy and easily misunderstood.
4. Stable filtering/retrieval/validation is needed.
5. Mistakes are costly and execution should not depend on memory.

---

## 4. Rewrite principles

### 4.1 Design each skill directly, not an abstract template first

Do not first produce a unified skill template because:
- Skills differ substantially.
- Premature abstraction constrains design.
- Problem-driven refactoring of existing skills is more appropriate now.

All rewritten skills must nevertheless provide clear:
- Applicability
- Prerequisites
- Main workflow
- Reference loading
- Validation/recovery
- Chinese, web-fiction-oriented language

### 4.2 Skills first, reference bodies later

Fixed sequence:
1. Define each skill's responsibility and structure.
2. List missing reference files.
3. Fill reference bodies individually in the next phase.

This spec lists only reference:
- Filename
- Purpose
- Weakness addressed
- Owning skill

It does not design complete contents.

### 4.3 Criteria for adding a reference

All four must pass:

1. **Binding**: identify which skill/step loads it under what condition. Cross-skill references need primary/secondary use cases.
2. **Gap**: does Claude consistently err (compensation), forget (reminder), or lack knowledge (supplement) in this subtask? At least one.
3. **Independence**: can one or two natural sentences in the main skill cover it? If so, inline it instead.
4. **Necessity**: will omission reliably repeat errors? If not, prefer workflow, script, or validation fixes.

Add only after all four pass.

### 4.4 Required skill structure

Beyond §4.1, requirements vary by priority:
- **P0**: all three required: red flags/common pitfalls, priority chain, decision-tree entrypoints.
- **P1**: explicitly include at least one or two.
- **P2**: use as needed, not mandatory.

#### Red flags/common pitfalls

Each mainline skill needs a dedicated list of **actual model reasoning mistakes**, not abstract prohibitions.

Example (`webnovel-write`):

```text
## Common pitfalls
- ❌ Skip Step 3 review because the chapter seems simple
- ❌ Start the next chapter after Step 5 fails (state still chapter_reviewed)
- ❌ Read every reference at once before writing
- ❌ Ignore a blocking issue because it seems “not serious”
- ❌ Substitute file existence for chapter_status checks
- ❌ Change event order or settings while polishing
```

#### Priority chain

Specify resolution order for conflicting instructions:

```text
1. Explicit user requirements (highest)
2. State-machine/workflow hard gates (chapter_status, blocking)
3. Project-private constraints (settings, existing plot)
4. Skill default workflow
5. Reference suggestions (lowest)
```

#### Decision-tree entrypoints

Beyond linear steps, include decisions at the start or key branches, covering at least:
- When to continue
- When to block
- When to return to the previous step
- When a user decision is needed

---

## 5. Skill overview matrix

| Skill | Current issue | Rewrite goal | Reference gaps | Priority |
|------|--------------|----------|-----------------|--------|
| `webnovel-write` | Heavy mainline and accumulated rules; unclear workflow/reference boundaries | Mainline orchestrator retaining workflow, gates, deliverables, recovery only | High | P0 |
| `webnovel-review` | Relatively simple, but reviewer/review-pipeline/state-machine integration needs clarity | Independent review entrypoint consolidating reports/blockers | Medium | P0 |
| `webnovel-plan` | Large, mixed hierarchy of rules and reference explanations | Planning entrypoint with clear structured nodes and volume planning | High | P0 |
| `webnovel-init` | Oversized mini-spec mixing collection, rules, and resources | Initialization workflow; move complex knowledge to references | High | P1 |
| `webnovel-query` | Clear query logic, manual-like documentation and excessive low-level commands | Query/analysis skill | Medium | P1 |
| `webnovel-dashboard` | Too lightweight, like a startup command; lacks validation/recovery | Tool-launch skill | Low | P2 |
| `webnovel-learn` | Too lightweight, command-like; lacks boundaries/recovery | Lightweight recording skill | Low | P2 |

---

## 6. Per-skill redesign

### 6.1 `webnovel-write`

#### Current issues
- Too much detail; prone to further growth.
- Some reference methodology remains in the skill.
- State-machine gates exist, but structure remains oversized.

#### Goal
- Explicitly the **mainline orchestration skill**.
- Retain workflow, state advancement, blockers, necessary references, deliverables, recovery.
- Exclude naming details, dialogue-style methodology, genre naming libraries, and plot-situation examples; move them to references.

#### Structure
Retain only:
1. Goal and applicability
2. Common pitfalls (§4.4)
3. Priority chain (§4.4)
4. Prerequisites/environment
5. Step-level loading strategy with CSV triggers
6. Main workflow (Steps 0.5–6, including decisions)
7. State advancement/blockers
8. Sufficiency gate
9. Validation/delivery
10. Recovery

#### Existing SKILL.md sections

| Section | Action | Reason |
|---------|------|------|
| Goal | Keep | Core definition |
| Operating principles | Keep | Hard gates |
| Modes | Keep | Standard/fast/minimal distinction |
| Loading levels (L0/L1/L2) | Keep | On-demand strategy |
| References list | Rewrite | Step triggers and conditional loading |
| Tool strategy | Keep, shorten | CLI entrypoints only, no argument detail |
| Preparation | Keep | Preflight + environment variables |
| Steps 0.5–6 | Keep | Core workflow |
| Issue-specific references | Move out | Reference index or in-step triggers |
| Sufficiency gate | Keep | Already state-machine-based |
| Validation/delivery | Keep | Already uses chapter_status |
| Failure handling | Keep | Rerun rules |

#### Reference bindings

Apply §2.3; organize by step + trigger. **Read Markdown directly; retrieve CSV on demand through the search script.**

##### Required Markdown (direct Read)

| Step | Trigger | Reference |
|------|---------|-----------------|
| Step 1 | Every run | `references/reading-power-taxonomy.md`, `references/genre-profiles.md`, `skills/webnovel-write/references/style-variants.md` |
| Step 2 | Every run | `references/shared/core-constraints.md`, `skills/webnovel-write/references/anti-ai-guide.md` |
| Step 4 | Every run | `skills/webnovel-write/references/polish-guide.md`, `skills/webnovel-write/references/writing/typesetting.md`, `skills/webnovel-write/references/style-adapter.md` |

##### CSV retrieval (`reference_search.py`)

Exact Chinese query/table literals are retained for compatibility with the knowledge base.

| Step | Trigger | Arguments |
|------|---------|---------|
| Step 2 | New character first appears | `--skill write --table naming --query "characternaming" --genre {genre}` |
| Step 2 | Combat/confrontation | `--skill write --query "combatdescription" --genre {genre}` |
| Step 2 | Multi-character dialogue | `--skill write --query "conversationvoice distinguishing voices"` |
| Step 2 | Emotional/psychological description | `--skill write --query "emotional-relationshipsdescription psychological"` |
| Step 2 | Frequently used plot situation | `--skill write --table scenes --query "{tropetype}"` |
| Step 4 | ai_flavor issue exists | `--skill write --query "AIstylistic traces negative_example replace"` |

#### Script needs
- No new script prerequisite now.
- Add a lightweight naming checker later if checks prove programmable.

#### Acceptance
- Clearly shorter main-workflow reading path
- References loaded only when triggered
- No weakening of state-machine/deliverable logic
- No extensive general writing advice in skill body

---

### 6.2 `webnovel-review`

#### Current issues
- Clear workflow, but reviewer/review-pipeline/report-persistence boundaries need refinement.
- Clarify blockers/rework as a review workflow.

#### Goal
- Independent review skill: chapter input → report output, database persistence, record writeback.
- Leave theory to reviewer and references.

#### Structure
Retain:
1. Applicability
2. Common pitfalls (§4.4)
3. Priority chain (§4.4)
4. Project-root resolution
5. Reference loading
6. Call reviewer (decision tree: blocking → rework/override)
7. Generate report and persist
8. Handle blockers/user decisions
9. Success/recovery

#### Reference bindings

##### Required Markdown

| Step | Trigger | Reference |
|------|---------|-----------------|
| Step 2 (load references) | Every run | `references/shared/core-constraints.md`, `references/review-schema.md` |
| Step 6 (handle blockers) | Blocking issue needs user decision | `references/review/blocking-override-guidelines.md` |

##### CSV retrieval

| Step | Trigger | Arguments |
|------|---------|---------|
| Step 4 (call reviewer) | ≥3 ai_flavor issues | `--skill review --query "AIstylistic traces negative_example replace"` |

#### Script needs
- No new mainline script.
- Consider `review-ai-flavor-check.py` later if independent rechecks need a stable interface.

#### Acceptance
- Clear blocker handling
- Stable review-artifact paths
- No duplication of reviewer's detailed dimensions

---

### 6.3 `webnovel-plan`

#### Current issues
- One document handles setting completion, volume beats, timeline, chapter outlines, node specifications, and setting writeback.
- Many rules belong in references rather than main skill prose.

#### Goal
- **Main planning entrypoint**, emphasizing:
  - Volume goals
  - Hard timeline constraints
  - Batch chapter breakdown
  - Structured-node artifacts
- Move genre pacing/conflict design into references.

#### Structure
1. Goal/scope
2. Common pitfalls (§4.4)
3. Priority chain (§4.4)
4. Prerequisites
5. Loading strategy
6. Main planning workflow (Steps 1–9 with decisions)
7. Structured-node artifact requirements
8. Hard-failure conditions
9. Recovery

#### Reference bindings

##### Required Markdown

| Step | Trigger | Reference |
|------|---------|-----------------|
| Chapter breakdown | Every run | `references/outlining/plot-signal-vs-spoiler.md` |

##### CSV retrieval

| Step | Trigger | Arguments |
|------|---------|---------|
| Volume planning | Every run | `--skill plan --table scenes --query "volumestructure narrationfunction"` |
| Chapter breakdown | New character | `--skill plan --table naming --query "characternaming" --genre {genre}` |

#### Script needs
- None now.
- Consider independent validation if timeline checks grow more complex.

#### Acceptance
- Planning entrypoint, not a complete tutorial
- Genre/conflict knowledge substantially moved to references
- Clear, centralized batch/node/timeline rules

---

### 6.4 `webnovel-init`

#### Current issues
- Oversized, approaching a mini-spec.
- Mixes collection, genre strategy, creative constraints, resource indexes.

#### Goal
- **Initialization interview and generation workflow**.
- Retain collection, sufficiency gate, generation, validation only.
- Move genre, naming, selling-point, and creativity knowledge into references.

#### Structure
1. Goal/applicability
2. Interaction principles
3. Staged collection
4. Sufficiency gate
5. Generation
6. Validation/delivery
7. Minimal rollback

#### Reference bindings

##### Required Markdown

| Step | Trigger | Reference |
|------|---------|-----------------|
| Selling-point/genre collection | Every run | `references/genre-profiles.md` |

##### CSV retrieval

| Step | Trigger | Arguments |
|------|---------|---------|
| Naming collection | User begins character/book/faction naming | `--skill init --table naming --query "{naming_target} {genre}" --genre {genre}` |

Note: `title-patterns-and-anti-patterns.md` and `protagonist-flaw-patterns.md` are not included in this round's gap list; restore them only if testing reveals persistent weaknesses.

#### Script needs
- None now; continue using `init_project.py`.

#### Acceptance
- Substantially slimmer skill body
- Clearer interaction
- Creative/genre/naming detail moved out

---

### 6.5 `webnovel-query`

#### Current issues
- Reasonable query workflow, manual-like documentation.
- Excessive low-level steps; emphasize query classification + source selection + output formatting.

#### Goal
- **Query/analysis skill** emphasizing:
  - Intent recognition
  - On-demand references
  - Minimal necessary data
  - Structured answers

#### Structure
1. Use when
2. Project-root guard
3. Query classification
4. Reference loading levels
5. Query procedure
6. Output format
7. Boundaries

#### Reference bindings

No mandatory additions. Current needs are project-private CLI/source knowledge already inline.

Candidates `entity-alias-resolution.md` and `foreshadowing-urgency-rules.md` may return if testing shows unstable output.

#### Script needs
- No mandatory additions.

#### Acceptance
- Query workflow rather than lengthy manual
- Consistent output style

---

### 6.6 `webnovel-dashboard` (P2, direction only)

Consolidate as a **tool-launch skill**: environment checks, startup, success criteria, common failures. The three structural elements are not mandatory for P2; no separate reference. Existing functionality is broadly coherent.

---

### 6.7 `webnovel-learn` (P2, direction only)

Consolidate as a **lightweight recording skill**: when to record, input structure, idempotency/deduplication, writeback format, failures. P2 does not require all three elements; add `pattern-taxonomy` only if testing warrants it.

---

## 7. Dual-track reference system

Use **two tracks**: workflow-required Markdown + writing knowledge base (CSV + search script).

### 7.1 Responsibilities

| Track | Format | Loading | Content | Examples |
|------|------|---------|---------|------|
| **Workflow-required** | `.md` | Direct `Read` at specified step | Gates, schemas, core constraints, review criteria | `core-constraints.md`, `review-schema.md`, `polish-guide.md` |
| **Writing knowledge base** | `.csv` + Python search | Script called for specific scenarios; matching entries only | Techniques, genre methods, scene inspiration, naming, examples/counterexamples | `techniques.csv`, `naming.csv`, `scenes.csv` |

Boundary:
- **Workflow/contracts/gates/schemas** → Markdown (read fully, not fragments).
- **Knowledge/techniques/inspiration/examples** → CSV (many entries, on-demand retrieval, relevant few only).

### 7.2 CSV design

#### Location

```
webnovel-writer/
  data/                          # CSV knowledge-base root
    techniques.csv
    naming.csv
    scenes.csv
  scripts/
    reference_search.py          # Unified BM25 search
```

#### Encoding

All CSV files use **UTF-8 with BOM** (`utf-8-sig`) so Windows Excel displays Chinese correctly.

#### Common columns

Exact schema names and machine values remain Chinese.

| Column | Type | Meaning | Examples |
|------|------|------|-------|
| `id` | string | Unique ID, table-specific prefix | `WT-001`, `NR-012`, `SP-003` |
| `applicable_skills` | string | Coarse filter, comma-separated | `write`, `init,plan`, `init,plan,write` |
| `category` | string | Broad scenario category | `combat`, `conversation`, `naming`, `emotional-relationships`, `scene` (combat/dialogue/naming/emotion/scene) |
| `level` | string | Three-layer marker | `reminder` / `defect-compensation` / `knowledge` (reminder/compensation/supplement) |
| `keywords` | string | Comma-separated BM25 keywords | `combat,physical combat,duel,realm suppression` |
| `applicable_genres` | string | Comma-separated Fanqie genre names | `all` or `xuanhuan,xianxia` |

#### Writing techniques (`techniques.csv`)

| Column | Meaning |
|------|------|
| (Common columns) | |
| `technique_name` | Short technique name |
| `description` | Technique description |
| `positive_example` | Positive example; long excerpts allowed (200–500 Chinese characters) |
| `negative_example` | Counterexample; long excerpts allowed |
| `fix recommendation` | Direction for revising counterexample into positive example |

Example row (original runtime CSV sample retained):

```
id,applicable_skills,category,level,keywords,applicable_genres,technique_name,description,positive_example,negative_example,fix recommendation
WT-001,write,conversation,defect-compensation,"converging voices,conversationdistinguish,charactervoice",all,conversationvoice differentiation,differentcharacterofconversationshould have distinctive spoken features andpacingdifferences,"Old Zhang held his pipe between his teeth，""Hey，You rascal, here for another free meal？""...","the two peopleconversationhave identical styles，both use standard written language",give eachcharactersetting 1-2 spoken markers and habitual sentence patterns
```

#### Naming rules (`naming.csv`)

| Column | Meaning |
|------|------|
| (Common columns) | |
| `naming_target` | `character` / `location` / `faction` / `cultivation technique` / `item` / `book-title` (character/location/faction/technique/item/book title) |
| `rule` | Rule description |
| `positive_example` | Positive example |
| `negative_example` | Counterexample |

#### Scene techniques (`scenes.csv`)

| Column | Meaning |
|------|------|
| (Common columns) | |
| `scene_type` | `confession`, `vindication`, `awakening`, `combat`, `negotiation`, `chase`, `everyday-life`, `farewell`, etc. (confession/comeuppance/awakening/combat/negotiation/chase/daily life/farewell) |
| `pattern_name` | Pattern name |
| `description` | Pattern description |
| `example_excerpt` | Long excerpts allowed (200–500 characters) |
| `negative examples` | Approaches to avoid |

### 7.3 Search script

#### CLI

```bash
# Basic: search by current skill and keywords
python -X utf8 "${SCRIPTS_DIR}/reference_search.py" \
  --skill write \
  --query "combatdescription realm suppression" \
  --max-results 3

# Genre filter
python -X utf8 "${SCRIPTS_DIR}/reference_search.py" \
  --skill write \
  --query "naming character" \
  --genre "xuanhuan" \
  --max-results 5

# Specific table
python -X utf8 "${SCRIPTS_DIR}/reference_search.py" \
  --skill plan \
  --table naming \
  --query "cross-volume characternaming" \
  --max-results 3
```

#### Retrieval flow

```
1. Coarse-filter by applicable_skills (applicable skill)
2. Optionally filter by applicable_genres (genre), when --genre is specified
3. BM25 keyword search within filtered results
4. Format and return top N entries
```

#### Output format

```
## Search results (writing techniques)
Query: combat description, realm suppression | Skill: write | Genre: xuanhuan | Matches: 3

### [WT-023] Physical experience of realm suppression
- Layer: knowledge supplement
- Description: show realm gaps through physical reactions rather than numerical comparisons
- Positive example: (excerpt...)
- Counterexample: (excerpt...)
- Repair suggestion: ...

### [WT-045] ...
```

### 7.4 Workflow-required Markdown (retain/add)

Read these directly at the specified step:

| File | Action | Skill | Timing |
|------|------|-----------|---------|
| `references/shared/core-constraints.md` | Retain | write/Step 2 | Every run |
| `references/review-schema.md` | Retain | write/Step 3, review/Step 4 | Every run |
| `references/shared/cool-points-guide.md` | Retain | review | On demand |
| `references/shared/strand-weave-pattern.md` | Retain | review | On demand |
| `references/reading-power-taxonomy.md` | Retain | write/Step 1 | Every run |
| `references/genre-profiles.md` | Retain | write/Step 1, init | Every run |
| `skills/webnovel-write/references/style-variants.md` | Retain | write/Step 1 | Every run (differentiation) |
| `skills/webnovel-write/references/polish-guide.md` | Retain | write/Step 4 | Every run |
| `skills/webnovel-write/references/anti-ai-guide.md` | Retain | write/Step 2 | Every run |
| `skills/webnovel-write/references/style-adapter.md` | Retain | write/Step 4 | Every run |
| `skills/webnovel-write/references/writing/typesetting.md` | Retain | write/Step 4 | Every run |
| `references/review/blocking-override-guidelines.md` | **Add** | review/Step 6 | Blocking issue needs user decision |
| `references/outlining/plot-signal-vs-spoiler.md` | **Add** | plan/chapter breakdown | Every run |

### 7.5 Writing-knowledge CSVs (new)

Migrate or create:

| Existing Markdown | CSV destination | Markdown afterward |
|-------------|-----------|--------------|
| `writing/combat-scenes.md` | `scenes.csv` (`scene_type=combat`) | Delete or retain redirect shell |
| `writing/dialogue-writing.md` | `techniques.csv` (`category=conversation`) | Same |
| `writing/emotion-psychology.md` | `techniques.csv` (`category=emotional-relationships`) | Same |
| `writing/scene-description.md` | `techniques.csv` (`category=scene`) | Same |
| `writing/desire-description.md` | `techniques.csv` (`category=emotional-relationships`) | Same |
| `writing/genre-hook-payoff-library.md` | `scenes.csv` (`scene_type=hook/payoff`) | Same |
| New: naming rules | `naming.csv` | No existing file |
| New: differentiated dialogue voices | `techniques.csv` (`category=conversation`, `level=defect-compensation`) | No existing file |
| New: anti-template plot situations | `scenes.csv` (`level=defect-compensation`) | No existing file |
| New: AI-flavor examples/counterexamples | `techniques.csv` (`category=AIstylistic traces`, `level=defect-compensation`) | No existing file |
| New: volume-level narrative-function patterns | `scenes.csv` (`scene_type=volumestructure`, `applicable_skills=plan`) | No existing file |

### 7.6 Filtered-out proposals

Not included now, but not permanently excluded. Restore if testing shows unreliable output in Chinese web-fiction scenarios.

| Proposal | Current reason for exclusion | Restoration condition |
|--------|------------|---------|
| `init/title-patterns-and-anti-patterns.md` | Book titles fit a few `naming.csv` entries (`naming_target=book-title`) | If too few rows cannot cover persistent template-like titles, expand into an independent entry group |
| `init/protagonist-flaw-patterns.md` | General model ability suffices | Add CSV entries if flaw design stays vague/label-like in practice |
| `query/entity-alias-resolution.md` | Alias resolution is code logic (entity_linker.py) | Add reference for frequent semantic ambiguity beyond code coverage |
| `query/foreshadowing-urgency-rules.md` | Urgency sorting already in context-agent | Add if explanations are unstable |
| `learn/pattern-taxonomy.md` | Low-frequency skill; inline classification suffices | Add CSV entries if classification remains unreliable |

---

## 8. Implementation batches

### Batch 0: Infrastructure
- Implement BM25 `reference_search.py`.
- Create `data/` and three CSV skeletons (headers + a few seeds).
- Add tests for coarse filtering → genre filtering → BM25.
- Map existing `genres/` directory names to Chinese.

Goal: CSV infrastructure ready for later content.

### Batch 1: Mainline skills (P0)
- `webnovel-write`
- `webnovel-review`
- `webnovel-plan`
- Add required Markdown: `blocking-override-guidelines.md` (review), `plot-signal-vs-spoiler.md` (plan).

Goal: consolidate mainline entrypoints and switch to dual-track loading.

**Freeze point:** review confirms stable mainline structure and complete Markdown/CSV trigger tables before Batch 2.

### Batch 2: Initialization and queries (P1)
- `webnovel-init`
- `webnovel-query`

Goal: consolidate preliminary collection and query-analysis documentation.

### Batch 3: Content and auxiliary skills (P2)
- `webnovel-dashboard`
- `webnovel-learn`
- Migrate writing knowledge from Markdown to CSV.
- Expand CSV entries continuously without blocking the mainline.

Goal: finish lightweight skills and begin ongoing knowledge-base population.

---

## 9. Acceptance criteria

1. Every skill has a clear primary role, no longer mixing manual/tutorial/spec.
2. Skill bodies converge on workflows, gates, deliverables, and recovery.
3. **Layered structural requirements implemented**: P0 includes all red flags/priority chain/decisions, P1 at least one or two, P2 as needed (§4.4).
4. **Dual-track references implemented**: workflow Markdown and knowledge CSV have separate roles.
5. `reference_search.py` supports the full applicable-skill coarse filter → genre filter → BM25 pipeline.
6. All CSVs use UTF-8 with BOM and open correctly in Windows Excel.
7. Chinese genre taxonomy implemented, using Fanqie as current default; existing directories mapped.
8. Aim for high-value gap coverage, not fewer references.
9. Skill prose uses Chinese web-fiction language; fields/protocols retain necessary English.
10. New/rewritten skills pass prompt-integrity checks and manual walkthrough.

---

## 10. Scope boundaries

Not covered:
- Rewriting `agents/` (agents contain prompts only, no attached reference files)
- Writing reference bodies (only filenames, trigger bindings, layers defined)
- Complete script implementation details
- Confirmed v6 architecture decisions (state machine, memory contract, reviewer workflow)

This spec answers only:
**How should skills be rewritten next, which reference files should be added, and under what conditions should they load?**
