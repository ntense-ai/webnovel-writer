# Current System Architecture Diagnosis

> **Document status**: Diagnostic report (before introducing the Story Intelligence System Spec)
> **Assumption**: Large language models such as Opus 4.6 follow instructions perfectly and can correctly parse and execute every Bash command and formatting requirement.
> **Core conclusion**: The problem is not poor model writing or execution mistakes, but **fundamental flaws in the information structure, validation timing, and data-flow mechanisms supplied to the model**. The system tries to manage an extremely complex webnovel world state machine through a loose script pipeline, inevitably destabilizing long-running serials.
> A further qualification is important: the system is not entirely unstructured. It **already has several partially developed hubs, but lacks a unified Story Contract (SSOT) and a unified chapter commit mainline**.

---

## I. Architecture and Single Source of Truth Defects

### 1. Multiple Sources of Truth Create Conflicting Understanding

* **Observation**: Settings are scattered across `state.json` (dynamic state), `genre-profiles.md` (static tone), `index.db` (fragmented entities), and `memory` (long-term facts). Although `context_manager` and `genre_*` already attempt aggregation, they remain runtime assemblers and local hubs rather than a unified single source of truth (SSOT).
* **Impact**: A legitimate plot reversal or setting upgrade cannot be synchronized globally. The model receives conflicting instructions, such as Markdown requiring a weak protagonist who conceals their ability while state data says they are already invincible. Even a highly capable model, trying to honor both, produces incoherent characterization and plot.

### 2. The Setting-Evolution Ledger Is Only a Prototype and Does Not Cover Core World Settings

* **Observation**: Core webnovel rules evolve and may be broken as the plot advances, for example when the protagonist breaks a world limitation. Version 5.3 introduced the `override_contracts` table (see `index_debt_mixin.py`) with full CRUD operations, including `constraint_type`, `rationale_type`, `rationale_text`, `payback_plan`, `due_chapter`, and `status`. However, it currently **only records violations of soft recommendations in the reader-retention debt system**. It has not become an evolution ledger for core world settings such as power systems, character destinies, and world rules. Changes to these still rely mainly on silent overwrites or local projection updates.
* **Impact**: Nothing explicitly tells the AI that volume five has legitimately overturned volume one's restraint-focused characterization and that invincible-protagonist wish fulfillment is now the governing principle. Feeding old rules and new states together causes context contamination and logical deadlocks. Override Contract infrastructure exists, but its limited scope prevents it from resolving this core problem.

---

## II. Context and Knowledge Assembly Problems

### 3. Mechanical Truncation Creates Information Blind Spots

* **Observation**: `context_manager.py` already aggregates context, and `context_ranker.py` prioritizes and filters information such as alerts. The system is therefore not simply stuffing context indiscriminately. However, final assembly still forcibly truncates strings with `_compact_json_text` according to `TEMPLATE_WEIGHTS` and character budgets.
* **Impact**: No model can obey rules it never sees. Critical reader turn-offs, power limitations, and foreshadowing can be silently dropped merely because they fall beyond the string budget. The model then fills gaps through hallucination, destabilizing the setting. The issue is not missing aggregation, but that **budget logic can turn the aggregated input into an information blind spot**.

### 4. Late-Bound Knowledge and Disconnected Generalization

* **Observation**: The system does not merely look up CSV midway through writing. It already has a dual-track reference system combining mandatory Markdown reading, CSV retrieval, and `genre_profile`. Nevertheless, during writing it still requires the model to call `reference_search.py` at particular stages for generic entries, such as combat-writing guidance.
* **Impact**: Most retrieved results are generic webnovel techniques rather than book-specific settings. No upstream aggregation layer blends general patterns with this protagonist's traits, the genre's tone, and system boundaries. The resulting plot follows standard formulas but feels interchangeable and lacks the book's distinctive identity.

---

## III. Workflow and Verification Gaps

### 5. Defenses Diagnose Failures Afterward Instead of Preventing Them

* **Observation**: The system relies heavily on the Step 3 Reviewer Agent to inspect **already completed prose**, then sends blocking problems to Step 4 (polishing) for repair.
* **Impact**: Validation comes too late. Directional or structural drafting errors, such as killing a protected core character or triggering a serious reader turn-off, cannot be repaired by polishing that changes expression but not facts. This creates unresolvable loops or low-quality patched prose.

### 6. No Mandatory Outline Fulfillment Verification

* **Observation**: The system already reads planning information such as `chapter outline`, `plot_structure`, `mandatory_nodes`, and `prohibitions`. At post-writing submission, however, it only extracts what actually happened. It does not perform a rigorous structured diff between planned and achieved content, such as CBN/CEN nodes.
* **Impact**: If the model omits a key assassination setup because of length limits, the system accurately extracts what was written without reporting the unfulfilled outline requirement. Later chapter outlines can silently fail in a chain reaction.

---

## IV. Data Write-back and Disambiguation Risks

### 7. Fragmented Transactions and Ghost State

* **Observation**: Step 5 writes separately to `state.json`, `index.db`, `summaries`, and `memory`. To be precise, `state_manager` already provides local atomic writes and pending-snapshot protection, but not cross-storage chapter-level ACID consistency. `StateManager` also maintains **dual-write synchronization** between `state.json` and SQLite (`index.db`) through `_sync_to_sqlite` and `_sync_pending_patches_to_sqlite`, including pending-snapshot recovery. This introduces additional consistency complexity within a single module.
* **Impact**: There are two risk layers. **Internally**, a partial failure in JSON + SQLite dual writes may not be fully recovered in extreme cases, despite snapshot recovery. **Externally**, interruption during writes across four stores may leave the database saying a character is dead while `state.json` says they are alive, or leave summaries and long-term memory out of sync. Such ghost state severely confuses next-chapter generation.

### 8. Post-processing Disambiguation Can Amplify Hallucinations Into Index Pollution

* **Observation**: If Step 2 mistakenly calls protagonist Lin Chen “Zhang Chen,” post-processing disambiguation may not reject the draft immediately. The current system does use confidence tiers rather than blindly persisting every mistake. Nevertheless, a risk window remains: **once an error falls within an acceptable confidence range, disambiguation may merge the wrong entity into subsequent indexing**.
* **Impact**: A pure writing hallucination may be persisted as an alias, appearance, relationship, or state update because it was accepted despite low confidence. Over time this pollutes the database and makes subsequent disambiguation increasingly unreliable.

### 9. Disambiguation Warnings Leak Into Later Context

* **Observation**: If Step 5 encounters an ambiguous name that cannot be resolved automatically, it records it in `state.json` under `disambiguation_pending`. Unstable resolutions above the threshold enter `disambiguation_warnings`. Both are read again through context assembly when writing **the next chapter**.
* **Impact**: Unresolved disambiguation from the previous chapter becomes noise during the next draft. It distracts the model from new plot development and can even encourage forced explanations of the previous chapter's naming issue, disrupting narrative flow.

### 10. State Projections Dominate; Semantic Events Exist Without a Mainline

* **Observation**: The Data Agent and data pipeline do have delta events, including:
  - `state_changes`
  - `relationship_events`
  - `timeline_events`
  - `world_rules`
  - `open_loops`
  - `reader_promises`

  For relationships, the code already has a `relationship_events` table more complete than `relationships_new`, with strong structural capabilities. But events remain scattered across `state`, `index`, and `memory`, without a unified canonical event log. The mainline still favors state-projection updates over event-driven updates.
* **Impact**: The system can record “has reached Golden Core,” but struggles to express consistently how the breakthrough happened, what resources it consumed, what phenomena it caused, and how it should change higher-level world rules. It cannot automatically detect and trigger setting upgrades or expanded power-system thresholds. The model still has to infer the current power ceiling from incomplete evidence.

---

## Summary

Before introducing the advance contractual constraints of the `Story Intelligence System Spec`, the system is not relying on an entirely unsupported language model. Several partially developed hubs already provide **piecemeal support**:

- `context_manager` + `context_ranker` aggregate and prioritize context.
- `genre_*` normalizes genres and builds profiles.
- `state_manager` writes structured state, including JSON + SQLite dual-write synchronization.
- `memory writer / orchestrator` persists long-term facts.
- `override_contracts` records reader-retention debt violations, forming an early Override Ledger.

These capabilities have not yet converged into a unified story-fact system.

The fundamental problem is therefore not insufficient model capability:

**The system already has several local structural layers, including an Override Contract prototype and delta-event foundations, but lacks a unified Story Contract, a unified chapter Commit Chain, and a unified Override Ledger covering global world settings.**

This is precisely the value of the new architecture:

- Generate strongly constrained `Master / Volume / Chapter` JSON contracts.
- Establish an explicit Override ledger.
- Supply absolute red lines, system boundaries, and disambiguation scopes before writing.
- Downgrade `state / index / summary / memory / RAG` from scattered sources of truth to projections after contract submission.

Only complete, unambiguous, traceable, and internally consistent input lets a language model reliably sustain high-quality long-form serial fiction.
