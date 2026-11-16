# Author-Friendly Experience Layer: Engineering Core + Author Shell

- Date: 2026-06-07
- Status: Draft v2 · merged after bidirectional cross-validation
- Target author: **A Chinese-language web-novel author already using Claude Code, but not a programmer**. They can enter `/webnovel-write`, yet jargon, errors, and long workflows put them off.
- Selected direction: Direction C, author-oriented refactoring, delivered incrementally on Direction B, the author presentation layer.
- Positioning and responsibilities: This specification defines **product layers** (layering, component responsibilities, boundaries, hard limits). Its companion, `docs/architecture/author-friendly-reporting-plan-2026-06-07.md` (the Codex plan), defines **engineering implementation** (phases, files, tests, execution order). They complement one another and should be used together, not treated as alternatives.

---

## 1. Background and Problems

`webnovel-writer` has a rigorous engineering fact chain: `Story System → write-gate → CHAPTER_COMMIT → projection`, plus RAG and long-term memory. This chain keeps a story consistent across hundreds of chapters and is the product's core value.

The problem: **the chain exposes engineering language, processes, and errors directly to authors.** Instead of a well-designed writing tool, they encounter developer-facing output such as `preflight`, `write-gate prewrite/precommit/postcommit`, `projection_status`, `CHAPTER_COMMIT accepted/rejected`, and `mainline_ready=false`.

The user explicitly requested improvements to all four pain points:

| Pain point | The author's experience |
|------|----------------|
| Progress is a black box | Claude fills the screen with commands and JSON while writing a chapter; the author cannot tell what it is doing, whether it is healthy, or how long remains |
| Errors are incomprehensible and recovery unclear | Errors explain technical causes but not which command to enter or file to change |
| Review reports are hard to use | Reports are technical and long; it is difficult to see whether a chapter works, whether changes are needed, and where |
| Jargon alienates authors | Contracts, commits, projections, gates, and accepted commits appear throughout; authors lack a corresponding mental model |

## 2. Core Insight

These are **not four independent problems, but four aspects of one missing layer**:

> The system needs an **author interface layer** that translates engineering facts into author language, compresses processes into meaningful progress, maps errors to actionable next steps, and renders review artifacts as decision-ready conclusions.

| Pain point | Root cause | What the layer supplies |
|------|------|------------|
| Black-box progress | Process language is not translated | Author milestones instead of a multistep pipeline |
| No clear error recovery | Errors are untranslated and offer no way forward | Error code → plain language + next action; rerun/resume support |
| Unusable review reports | Results are untranslated and not actionable | One conclusion + at most 3 actionable changes; technical detail on demand |
| Alienating jargon | Concepts are untranslated | A consistent terminology mapping |

Conclusion: **Add translation/presentation between the engineering chain and the author, without changing the engineering source of truth at all.** Preserve rigor while completely changing the author-facing experience.

## 3. Goals and Non-Goals

**Goals**
- Authors do not encounter engineering language, processes, or errors directly by default in everyday use.
- Errors always provide plain language and a next action; rerunning the same command can automatically resume work.
- Authors can understand a review conclusion and decide what to do within three seconds.
- Terminology is consistent and understandable throughout.

**Non-goals (YAGNI)**
- Do not rewrite logic or data structures in the engineering core (Story System / gates / commits / projections / RAG).
- Do not rename existing `/webnovel-*` commands or break established habits and documentation.
- Do not weaken consistency checks for nontechnical authors.
- **Do not introduce any new UI**: no collapsible panels, progress bars, or buttons. The author shell consists only of text prompts, Skill conventions, Python helpers, and log files.
- Do not build a broad automatic-repair loop (§8).

## 4. Constraints and Hard Limits

Two principles apply throughout:

1. **Hiding details from authors does not mean relaxing validation or staying silent.** Every gate still runs and blocks as before, with zero compromise on fact-chain correctness. Automatically handled work, such as projection retries, **must be disclosed in the final report**, never silently hidden. The only changes are not proactively showing engineering detail and not interrupting authors over minor process issues.
2. **Build C on B in three stages.** Each stage delivers independent value, with increasing risk and the option to stop at any point rather than attempting a big-bang rewrite.

> Claude Code capability boundary: this design assumes no collapsible UI, progress bars, background tasks, or graphical buttons. Engineering detail is hidden through **Skill constraints on output + concise reports rendered by Python helpers**, not UI-level collapsing.

## 5. Architecture: Engineering Core + Author Shell

Three layers. Authors interact only with the top layer while the engine moves behind the scenes. The author shell is **not a new application or interface**; it collectively means Skill prompt conventions, Python helpers, text output, and logs.

```text
┌───────────────────────────────────────────────────────────────────┐
│ Author Shell ← implemented through Skills + helpers + text + logs  │
│ · Next-step footer: "Next, you can…"                               │
│ · Task-oriented wording (prompts only; command names unchanged)     │
│ · Automatic handling: no interruption, but final disclosure         │
│ · Milestones/results by default; paths/commands when needed         │
├───────────────────────────────────────────────────────────────────┤
│ Author Layer ← non-invasive presentation/translation foundation     │
│ · Progress narration · Error → action catalog                       │
│ · Author-facing review view · Terminology glossary                  │
├───────────────────────────────────────────────────────────────────┤
│ Engine ← unchanged                                                 │
│ Story System · gates · commits · projections · RAG                  │
└───────────────────────────────────────────────────────────────────┘
```

## 6. Component Design

Seven single-responsibility, independently deliverable components, assigned to stages. Each has a defined implementation point in the Codex plan.

### 6.1 Glossary · Stage One
- **Responsibility**: The sole source mapping engineering terms to author terms and one-sentence explanations; all other components reference it.
- **Consumes**: Nothing; it is the vocabulary source.
- **Produces**: Controlled vocabulary, for example: contract → story-setting record; commit → save to the record; projection → synchronize across locations; gate → self-check checkpoint; `mainline_ready` → whether this book's records are ready.
- **Dependencies**: None. Foundation for the other three first-stage components.
- **Implementation**: One source-of-truth file (`references/author_glossary.md` or structured `author_glossary.json`), referenced consistently by SKILL prompts and script output. No independently invented translations. Merge the initial glossary in Codex plan §5 into this component.

### 6.2 Progress Narration · Stage One
- **Responsibility**: Compress the writing pipeline into author milestones and define wording templates.
- **Consumes**: The current step in the writing workflow.
- **Produces**: Authors see only “Check earlier events → Draft → Health check → Save to the record → Done.”
- **Dependencies**: Glossary.
- **Implementation**: Narration conventions for multistep commands defining when and what to report at each milestone. **Do not proactively display commands or JSON by default** (limited Skill output + concise helper rendering, not UI collapsing). **Failures must surface.** Corresponds to Codex plan §8.

### 6.3 Error Catalog · Stage One
- **Responsibility**: Map known errors to plain-language descriptions, next actions, and severity. The highest-value component in this proposal; Codex review agreed to include it.
- **Consumes**: Error codes or signatures from `preflight`, `write-gate`, `doctor`, etc.
- **Produces**: For example, `mainline_ready=false` → “This book's records are not set up yet. Run `/webnovel-init` first.”
- **Dependencies**: Glossary.
- **Implementation**: `error_catalog.py` + `author_error_catalog.json`. Unmatched errors fall back to an honest error report and `/webnovel-doctor`; never crash or invent a translation.

### 6.4 Review Author View · Stage One
- **Responsibility**: Render an author-facing view on top of the existing review report.
- **Consumes**: review_result from `review-pipeline`, including `blocking_count` and related fields.
- **Produces**: One top-line conclusion (✅ Pass / ⚠️ Changes recommended / ⛔ Changes required) plus at most 3 actionable changes. Technical details follow in a separate section for on-demand reading, not a collapsible UI.
- **Dependencies**: Glossary and existing review artifact structure.
- **Implementation**: Add an author-view section to report rendering in `review_pipeline.py`; do not change reviewer schema or decision logic.

### 6.5 Next-Step Advisor · Stage Two
- **Responsibility**: Answer “What should I do now?” **Decision: embed it in each command's ending**, rather than add a separate command. Codex review agreed.
- **Consumes**: Phase and next-step information from `project-status`.
- **Produces**: A standard footer after each command, such as “Next, **write the next chapter**: `/webnovel-write 5`.” Naturally fits the third section, next-step recommendations, of the Codex plan's three-part report.
- **Dependencies**: Glossary and `project-status`.
- **Implementation**: Part of `user_report.py`, called at command completion; standard formatting plus copyable commands.

### 6.6 Task Language · Stage Two
- **Responsibility**: Express actions as author tasks, reducing the burden of remembering 8 command names.
- **Consumes**: Next-Step Advisor recommendations.
- **Produces**: Prompts using task language (start a new book / write the next chapter / see how this chapter works / look up a setting), accompanied by the existing command.
- **Dependencies**: Next-Step Advisor and glossary.
- **Implementation**: Prompt-layer mapping only. **Keep existing `/webnovel-*` names unchanged**; do not create actual alias commands.

### 6.7 Auto-Handled & Quiet · Stage Three
- **Responsibility**: Preserve the system's existing limited automatic handling; avoid interruptions over minor process issues and do not proactively display engineering detail by default.
- **Consumes**: Error-catalog classifications and retryable process-error signals.
- **Produces**: **Retain** actions such as automatically retrying projections or re-emitting missing contracts, with **no author interruption + mandatory final-report disclosure + logged details**. Show milestones and conclusions by default; provide paths/commands when needed.
- **Dependencies**: Error catalog, progress narration, final report.
- **Implementation**: Attach actions to the catalog's automatically handleable category, constrained by §8. **No broad automatic-repair loop**. Actual failure recovery is author rerun → idempotent resume (§8; engineering details in Codex plan §9).

## 7. Data Flow

The translation layer **consumes read-only data and rerenders it; it never enters the engineering write path**.

```text
Engineering chain produces factual artifacts as before
(state.json / review_result.json / gate JSON / error codes / projection_log.jsonl)
        │  (read-only consumption)
        ▼
Translation layer consults glossary / error catalog / review-view rules
        │  → renders author language
        ▼
Author sees plain language; the chosen next step still invokes existing commands
```

**Engineering artifacts, never translated output, remain the source of truth.** A translation error requires fixing only the translation layer; underlying data was never changed. This technically guarantees hidden details without weaker validation and enables independent testing and replacement of the layer.

## 8. Error Handling and Recovery Boundaries

Three error categories correspond to the Codex plan's classifications (handled automatically / confirmation advised / must resolve):

1. **Automatically handleable (no interruption, mandatory disclosure)**: Only idempotent, retryable process errors that do not touch author content (projection failure → retry; missing contract → re-emit). Do not interrupt, but **honestly report what happened and whether it affected results**, and log details. **Never silent.**
2. **Author decision required (surface with bounded options)**: Content trade-offs or irreversible choices, such as an unresolvable blocking review finding or a commit rejected for `missed_nodes`. Explain plainly and offer 2–3 bounded choices (accept / edit manually / abandon).
3. **Honest error + help route**: Environment/dependency issues, such as an unconfigured RAG key or missing Python dependencies. Explain plainly and direct to `/webnovel-doctor`.

**Recovery = rerun to resume (incorporating Codex plan §9).** Authors need not memorize retry commands. Repeating the same command uses reliable completion criteria to recognize completed steps and resume from failure without rewriting existing results. Initially cover only `/webnovel-write`.

**Reruns must stop and ask at these boundaries (full agreement with Codex §9.5):**
- Manually edited prose → ask whether to reuse or rewrite; **never overwrite author edits**.
- Chapter outline newer than prose → ask whether to reuse the old prose or draft again.
- Chapter already accepted → ask whether to rewrite or only inspect status.

**Hard limits**: Never skip validation automatically, disguise rejected as accepted, swallow correctness-affecting errors, or repair silently. If repaired, disclose it. **No broad automatic-repair loop**: self-healing allowlists can easily expand into a new failure source, giving the worst risk/benefit ratio; both independent reviews rejected this.

## 9. Validation Strategy

Test behavior, not literal wording, consistent with the project's principle that tests are probes rather than constraints:

- **Fidelity probes**: For the same engineering artifact, translated output must retain key facts (pass/fail, missing nodes, blocking count), without alteration or loss.
- **Error-catalog coverage**: Unknown error codes fall back to honest reporting, without crashes or invented explanations.
- **Non-silence probes**: Automatically handled work, such as projection retries, must appear in the final report.
- **Resume-boundary probes**: Manually edited prose, newer chapter outlines, and already accepted chapters must cause a rerun to ask the author, never overwrite unilaterally.

## 10. Staged Delivery Roadmap

| Stage | Scope | Deliverables | Exit criteria |
|----|------|--------|----------|
| One (foundation) | Four translation-layer components | Glossary, progress narration, error catalog, review author view | All four delivered and passing fidelity/coverage probes; no engine intrusion |
| Two (upper shell) | Next-Step Advisor + task language | Standard next-step footer for each command, task-language mapping | Every command ends with the correct next step; command names unchanged |
| Three (lower shell) | Disclosure of automatic handling + quiet defaults + rerun/resume | Reports include automatic handling, concise default output, `/webnovel-write` resume | All non-silence/resume-boundary probes pass; default view contains only milestones and conclusions |

Each stage delivers independently and can be stopped at any time. The ordering matches Codex-plan priorities (§11).

## 11. Bidirectional Cross-Validation and Merge Plan

**Correction to an earlier inference**: Section 11 of v1 speculated that the Codex plan focused on reporting and was narrower. Reading it in full showed this was **wrong**: it also covers checkpoint resume, subagent return protocols, duration reporting, and sanitized logs, and is more complete and implementable in those areas.

**Consensus from two independently produced documents and mutual review:**

- Agreement: Leave the engine unchanged and work only on presentation; terminology, progress, understandable errors, and next steps are central; never hide problems or disguise rejected as accepted; prefer runtime/structured-data-driven behavior over prompts alone; hide engineering details by default but retain diagnostic logs.
- This spec is stronger on Error Catalog, Review Author View, embedded Next-Step Advisor, task language, and restrained staging. Codex review agreed to incorporate these.
- The Codex plan is stronger on the standardized three-section/four-status final report, checkpoint resume/run ledger, subagent return protocols, duration reporting, sanitized logs, and actionable Phases 0–7. This spec incorporates them.
- Risks identified by Codex and corrected in v2: (1) replace collapsing with not proactively displaying engineering detail (CC lacks collapsible UI); (2) replace silent self-healing with automatic handling that must be disclosed; (3) pin the author shell to Skills + helpers + text + logs to prevent scope expansion.

**Merged responsibilities**: This spec defines **product layering** (layers, component responsibilities, boundaries, hard limits); the Codex plan defines **engineering implementation** (phases, files, tests, execution order). Each of the seven components identifies where it enters the Codex plan under Implementation.

**Merged implementation priorities (aligned with Codex review):**
1. Single-source glossary
2. Error Catalog
3. Review Author View
4. Next-Step Advisor
5. Progress narration conventions
6. `user_report` helper
7. Checkpoint resume / run ledger
8. Automatic-handling allowlist (most restrained; last)

## 12. Risks and Open Questions

- **Risk: translation layer drifts from engine.** New error codes/artifact fields require corresponding catalog/view updates. Honest fallback covers misses, but synchronization must become part of release validation.
- **Risk: concise progress hides genuine stalls.** Quiet defaults must still surface failures and disclose automatic handling, enforced by §9 non-silence probes.
- **Open question: glossary format** (plain Markdown conventions vs. structured data + validation). This affects testability and is left to the implementation plan.
- **Open question: exact error codes in the automatic-handling allowlist.** Lowest priority; assess actual catalog entries individually before Stage Three. Prefer omissions to unsafe inclusions.
