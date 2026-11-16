# Story Repo Format Specification (v7 Draft 0.4 · Frozen)

> Historical design record: project-directory examples retain their original names. New projects use `chapters/`, `outlines/`, `settings/`, and `reviews/`; existing legacy projects remain supported without renaming. Resolve actual paths with `scripts/project_paths.py` before using these examples.

> Status: 0.4. Change from 0.3: rename the umbrella directory to `finalized/` (finalized content), as chosen by the author: drafts stay in the workspace and move to finalized content after acceptance. Change from 0.2: abolish monolithic YAML data files; promises and information gaps use one Markdown file per entry with flat frontmatter (§4.3, §5). Add an error-resistant dialect (§2.2), repair cards (state 0 in §10), and the conversation-as-editor invariant (§1.9). See §14 for decisions.
> Source: the 2026-06-10 discussion of the most appropriate architecture + Phase 0 of the strangler-style convergence plan.
> Authority: this specification is the law for v7. Code derives from the format. If implementation conflicts with this specification, change one or the other; never silently store an extra copy in code.

---

## 0. In One Sentence

One book = one Git repository. `finalized/` stores accepted facts and prose, `outlines/` author intent and promises, `prose style/` taste, and `workspace/` everything before the acceptance boundary. Accepting a chapter = one atomic commit. No persistent derived artifacts exist except one disposable cache.

## 1. Design Invariants (Binding Rules)

1. **Files are truth**: All state is human-readable Markdown/YAML that authors can confidently edit. Detect manual changes and propose settlement; never reject them with an error.
2. **Derived artifacts are disposable**: After deleting all of `.cache/`, rebuild everything from source files and answer all queries normally. This is a CI acceptance criterion.
3. **Finalized content is append-only**: Do not retroactively change accepted chapter facts. Typo fixes are an exception; actual setting changes require an explicit retcon transaction (§9).
4. **Atomic settlement**: A chapter transaction's settle either completes one commit or leaves the workspace intact; no intermediate state.
5. **Separate writing and review**: Rendering and review must use different contexts; machine checks precede model review.
6. **Escalation principle**: Script < model < author. Do not ask a model to estimate what can be counted; do not interrupt authors over what a model can judge. The author interface uses decision cards, not commands.
7. **Do not build another VCS inside the VCS**: Use Git for versions, auditing, branches, and rollback; do not build a custom commit chain.
8. **Tolerant reads**: Preserve unknown fields encountered in any source file and write them back unchanged. Open-source users will extend the format; tools must not lose data.
9. **Conversation is the editor**: Any structured-data edit can be expressed in one natural-language sentence ("Abandon P-031 because we are switching to a hidden subplot"). Authors need not learn any file format; manual editing is only an escape hatch.

## 2. Directory Overview (Chinese Runtime Names)

The original design targets Chinese-language web-novel authors; **directory names, filenames, and author-visible field names are Chinese**. This English documentation preserves those format literals. ASCII is reserved for machine protocols: entry IDs (P-031, S-021), commit prefixes (ch/vol/retcon/fix), `spec_version`, and technical files (`book.yaml`, `.gitignore`, `.cache/`).

```text
<book-title>/
├── .git/
├── .gitignore                 # Includes at least .cache/ and workspace/
├── book.yaml                  # Book-wide configuration (§3)
├── finalized/                       # ── After the acceptance boundary ──
│   ├── chapters/
│   │   └── 0152-Snow in the North.md    # Chapter + frontmatter (§4.1)
│   ├── setting/
│   │   ├── character/
│   │   │   └── Lin Wan.md         # Character profile (§4.2)
│   │   ├── information advantage/
│   │   │   └── S-021-true culprit behind the family massacre.md  # Information gaps, one file per entry (§4.3)
│   │   ├── worldbuilding.md           # World rules and power system
│   │   ├── timeline.md           # Append-only table (§4.4)
│   │   └── roster.md             # Entity register: canonical name/aliases/first chapter (§4.5)
│   └── memory/
│       ├── chapter summary/0152.md      # Recorded at settle (§4.6)
│       └── volume summary/Volume 05.md    # Generated during volume retrospective
├── outlines/                       # ── Mutable author intent ──
│   ├── master-outline.md                 # Theme, special ability, ending promise
│   ├── volume outline/
│   │   └── Volume 05.md
│   └── promise/
│       └── P-031-true culprit behind the family massacre.md   # Promises, one file per entry (§5)
├── prose style/                       # ── Taste library ──
│   ├── style constitution.md             # （§6.1）
│   └── memorable-lines collection/                 # Automatically harvested (§6.2)
├── workspace/                     # ── Before acceptance; Git-ignored by default ──
│   ├── decision card.md               # （§7）
│   ├── context package.md             # Context pack for this rendering, retained for audit
│   ├── draft-A.md               # A/B/C for best-of-N
│   └── review report/               # Machine-check and lens-review output
└── .cache/                     # Only permitted derived cache (§11)
    └── index.db
```

### 2.1 Engineering Constraints for Chinese Paths (Normative, CI-Enforced)

Handle the encoding cost of Chinese paths through hard constraints, not luck:

- Use explicit `encoding='utf-8'` for all file I/O; inject `PYTHONUTF8=1` at script/subprocess entry points; never rely on system locale.
- Set `git config core.quotepath false` during repository initialization so Chinese paths remain readable in Git logs.
- Sort files using zero-padded numeric prefixes (`0152-`, `Volume 05`, `P-031`), not Chinese lexicographic order.
- Reference entities by their **canonical Chinese name**; resolve aliases through the register (§4.5). Do not introduce ASCII entity IDs.
- CI must include an end-to-end Windows test with Chinese paths (create repository → write chapter → settle → rebuild cache).

### 2.2 Error-Resistant Dialect (Normative Output-Format Constraints)

The three main YAML editing pitfalls for nonprogrammers are full-width punctuation, indentation, and surprising type coercion. All system-generated structured content must follow this dialect, so authors can safely imitate it:

- **Always flat**: No nested mappings in frontmatter or `book.yaml`; all fields are top-level.
- **Always block lists** (one item per line, such as `- Wanwan`); no inline `[a, b]`. Block lists avoid full-width comma problems.
- **Quote risky values**: Automatically quote strings that YAML might misinterpret (numeric-looking values, true/false/yes/no/yes/no forms).
- Use two-space indentation and UTF-8 without BOM.
- **Always one record per file**, never monolithic data files. A damaged entry affects only itself. Free text belongs in the Markdown body (full-width punctuation is fine); frontmatter contains only a few short, flat fields.

## 3. book.yaml

The repository's only pure YAML file: infrequently edited, flat, at most ten lines. Chinese format keys and example values below remain literal.

```yaml
spec_version: "7.0"
book-title: examplebook-title
type: xuanhuan
target words per chapter: 3000
volume size: 40                 # Reference value, not a hard constraint
prose-stylebaseline start: 1              # Style-fingerprint baseline chapter range; author-editable
prose-stylebaseline end: 30
highmaximum chapters a promise may remain stalled: 10     # Exceeding this flags pacing debt
maximum consecutive weak hooks: 3
number of key-chapter drafts: 3              # best-of-N for volume openings/turning points/climaxes
```

## 4. Finalized Content: `finalized/`

Drafts live in the workspace and move into finalized content after acceptance; the directory name expresses the mental model.

### 4.1 Chapter Files: `finalized/chapters/NNNN-title.md`

Filename: four-digit zero-padded chapter number + hyphen + title. Frontmatter carries the chapter contract and settlement summary: **each chapter contains its own acceptance record**, so audits need no external table. Only settle writes this file; authors edit the prose, not frontmatter.

```markdown
---
chapter number: 152
title: Snow in the North
volume: 5
viewpoint: Lin Wan
in-story time: Dali era1023year, third day of the winter month    # Free text; consistent format throughout the book
word count: 3120
open promise:
  - P-058
advance promise:
  - P-031
  - P-007
fulfill promise:
  - P-019
contract:                           # Contract assertions at acceptance time (validated)
  - Lin Wan obtains the first concrete evidence of the massacre truth
  - P-058 opens: the mysterious elder's origins
  - Strong ending hook: the mystic-rank token appears
---
Chapter prose…
```

### 4.2 Character Profiles: `finalized/setting/character/<canonical name>.md`

Frontmatter contains structured fields for machine checks (flat, block lists); the body contains free-form setting text.

```markdown
---
name: Lin Wan
alias:
  - Wanwan
  - Junior Sister Lin
status: alive                # Alive/dead/missing/sealed…
location: northern snowfields            # Last known location
realm: foundation-establishmentseventh layer            # Scale defined in worldbuilding.md
holds:
  - Azure Frost Sword
  - mystic-rank token
last changed chapter: 152
---
## setting
…Free text…
## relationship
…Free text; significant relationship changes also belong in the timeline…
```

### 4.3 Information Gaps: `finalized/setting/information advantage/<id>-<short title>.md`

Do not track every event known by every character. Register only **information gaps worth managing**, one per file. Leakage checks scan dialogue/interior monologue for keywords from information the character does not know. Redundancy checks flag repetition of information already known to the reader. Ensemble-scene attendance is covered by the timeline's present column (§4.4), not a separate mechanism.

```markdown
---
informed parties:
  - Grand Elder
  - mysterious elder
known to readers: false
registration chapter: 87
keywords:                   # Used for leakage scanning
  - Grand Elder
  - family massacre
  - blood-written letter
---
## content
The Grand Elder ordered the massacre; his sworn assassins carried it out.
```

### 4.4 Timeline: `finalized/setting/timeline.md`

An append-only Markdown table; settle appends a row. **The present column may be empty**: unnecessary for everyday chapters, recommended for ensemble/conspiracy scenes. It is the sole source for later queries about who witnessed what.

```markdown
| Chapter | in-story time | one sentenceevent | present |
|----|----------|------------|------|
| 152 | 1023third day of the winter month | Lin Wan obtains a blood-written letter in the north; the mystic-rank token appears | Lin Wan, mysterious elder |
```

### 4.5 Entity Register: `finalized/setting/roster.md`

Prevent one person appearing under multiple names, or different people sharing a name. Table: `| canonical name | alias | type | first appearance chapter |` (canonical name / aliases / type / first chapter). At settle, machine checks compare new proper names in prose with the register; unregistered names go onto the acceptance card for author confirmation as new entities or typos.

### 4.6 Memory Layer: `finalized/memory/`

- `chapter summary/NNNN.md`: ≤200 characters, generated by the model before settle and **shown on the acceptance card for the author to review/edit**, then recorded with the transaction.
- `volume summary/volume-NN.md`: ≤500 characters, generated at volume retrospective; main-plot progress, relationship changes, and outstanding promises.
- The longer-range book skeleton is **derived** by assembling/compressing volume summaries on demand; do not persist it.

## 5. Promises: `outlines/promise/` (One File per Entry)

The system's heart. Foreshadowing, mysteries, relationship arcs, anticipated payoffs, and declarations all become promises to the reader. Filename: `P-031-true culprit behind the family massacre.md` (ID-short title). Frontmatter has only six short, flat fields; description, payoff plan, and history are free-form Markdown body text.

```markdown
---
type: suspense                # Foreshadowing|mystery|conflict|relationship|declaration|payoff setup
strength: high                  # High|medium|low
status: in progress                # Active|fulfilled|abandoned
opening chapter: 12
payoff deadline: Volume 7           # Volume or chapter; required when intensity is high
last advanced chapter: 152
---
## description
The identity of the mastermind behind the massacre.

## payoff plan
Expose the mastermind publicly at the sect assembly in volume seven. Required when opening the promise to prevent dangling threads.

## history
- Chapter 12: opened
- Chapter 87: advanced; the blood-letter clue appears
- Chapter 152: advanced; Lin Wan obtains concrete evidence
```

**Settlement rules (script-executed, machine-check level)**:

- Every chapter settle must touch (open/advance/fulfill) at least one promise or be rejected. **Exemption belongs on the decision card**: when approving the brief, the author may exempt the chapter from promise settlement with a mandatory reason, such as a standalone extra. The model cannot exempt itself.
- settle writes to promise files by updating frontmatter (status/last-advanced chapter) and appending a history entry.
- A new promise requires a payoff plan; high-intensity promises require a payoff deadline.
- Pacing debt = high intensity and `current chapter − last-advanced chapter > maximum idle chapters for high promises`; show a yellow warning on the decision card.
- Abandonment must record a reason in history; even author-chosen abandonment needs an audit trail.
- Ledger-level views (due list, pacing debt, statistics) come from `.cache/` and the status board; **maintain no aggregate files**.
- Derived metrics, not separate mechanisms: cliffhanger intensity = intensity of outstanding promises at chapter end; retention risk = pacing-debt count + consecutive weak-hook count.

## 6. Style: `prose style/`

### 6.1 Style Constitution: `prose style/style constitution.md`

Everything the system knows about the author's taste, available for author review/editing. Frontmatter is machine-consumed (block lists; verbal habits are flat character:phrase list items, not nested):

```markdown
---
prohibited words:
  - pupils contracted
  - the corners of the lips curved into a
prohibited sentence patterns:
  - 'not.*but rather'
speech habit:
  - Lin Wan：self-reference"this young lady"
---
## iron rule
…
## pacingpreference
…
## derived from rejectionrule
- Do not open with weather (source: three rejections in chapters 89/103/121)
```

Rules enter the constitution through three similar rejections → system proposal → author confirmation. Every rule cites its source.

### 6.2 Exemplar Library: `prose style/memorable-lines collection/`

At settle, if `diff(model draft, author final)` exceeds the threshold (default: >30% change in one paragraph), automatically save the author-edited paragraph plus a scene tag as an exemplar. Inject it as few-shot guidance for similar scenes. Separate files by scene: `combat.md`, `dialogue-lines.md`, `emotional-relationships.md`, etc. Keep the latest 20 entries per file and rotate older entries into archives.

## 7. Workspace (`workspace/`) and Decision Cards

The entire workspace is Git-ignored by default; everything before acceptance may be discarded. Contracts ultimately live in chapter frontmatter (§4.1). **Users wanting draft history can remove that one `.gitignore` line**: settle still clears the workspace, behavior is unchanged, and Git retains history naturally. This is normative: implementation must not assume the workspace is untracked.

`decision card.md` is the only interface the author needs to read, with four fixed sections (status board, proposal, contract, alternatives). The example retains literal format headings:

```markdown
# decision card：Chapter 152
## story board（script-generated）
- Position: volume 5, chapter 24/40
- Pacing debt: P-031 (high, no progress for 12 chapters)
- Consecutive weak hooks: 2 chapters
## proposal
Advance P-031 (Lin Wan obtains evidence), open P-058 along the way, and end on the mystic-rank token's appearance.
## contract（effective upon approval）
- [ ] Lin Wan obtains the first concrete evidence of the massacre truth
- [ ] P-058 opens: the mysterious elder's origins
- [ ] Strong ending hook
## alternatives
Option B: a relationship-only transition chapter; defer P-031 to the next chapter (cost: pacing debt +1)
(If promise settlement is exempted, state the reason here)
```

The author has only three actions: adopt / edit the card / choose an alternative. Editing means changing this file directly or asking the system in one sentence (invariant 9).

## 8. Chapter Transaction (Inner Loop)

| # | Stage | Executor | File effect |
|---|------|--------|----------|
| 1 | brief | Script reads status board | Generate `workspace/decision card.md` |
| 2 | Approve | **Author** | Freeze the decision card contract section |
| 3 | pack | Script | Assemble `workspace/context package.md`: status board + contract + fact slices + information-gap boundaries + recent chapter endings + anti-repetition list + style anchors |
| 4 | Render | Model (clean context) | `workspace/draft-*.md`; best-of-N for key chapters |
| 5 | Machine check | Script | Contract assertions, information-leak scan, banned terms/repetition, new proper names vs. register, character count. **On failure, return to step 4 without interrupting the author** |
| 6 | Lens review | 3 models (each with fresh context) | Reader lens (satisfaction/where to skip), editor lens (structure/commercial appeal), fact lens (explain machine-check results only) → `workspace/review report/` |
| 7 | Accept | **Author** | Acceptance card = draft + three-sentence review + unconfirmed new names + **chapter summary (review/edit)**. Actions: accept / edit and accept / reject |
| 8 | settle | Script, **atomic** | See below |

**One settle commit includes**: draft → `finalized/chapters/` (contract and promise settlement in frontmatter); changes to `setting/` (location/status/realm/possessions/information gaps/register/timeline); settlement of affected `outlines/promise/` files (frontmatter updates + history append); `memory/chapter summary/` (accepted-card final version); harvesting into `prose style/memorable-lines collection/` if triggered; workspace clearing.

**Commit-message convention** (ASCII prefixes are machine protocol, convenient for `git log --grep`):

```text
ch(152): Snow in the North

promise: +P-058 ~P-031 ~P-007 $P-019     # + open ~ advance $ fulfill
setting: Lin Wan.location=northern snowfields; information advantage+S-021
```

## 9. Middle/Outer Loops and Exceptional Transactions

- **Volume retrospective** `vol(05): retrospective and next-volume planning`: audit promises (opened/fulfilled/overdue this volume) → `memory/volume summary/` → discuss with the author to create `outlines/volume outline/Volume 06.md` → scan foreshadowing opportunities (model proposes 3–5 seeds for this volume paying off N volumes later, citing specific distant master-outline nodes; generate promise files after author selection).
- **Health check** (automatic every 50 chapters): style-fingerprint drift vs. baseline + bad promise debt + timeline orphans → report in workspace, not settled; author chooses correction or baseline update.
- **retcon**: `retcon(87): correct the Grand Elder's realmsetting`. Explicit transaction permitting finalized-content changes, with a reason in the commit message, synchronized settings/promises, and an audit trail.
- **Manual-edit detection**: On startup, `git status` finds unsettled edits in finalized content/outlines → ask on the decision card whether to settle; after confirmation record as `fix(setting): …`. **The system adapts to the author instead of reporting an error.**
- **Branching futures**: To explore another plotline, use `git branch what-if/xxx`, project 3 chapter outlines for each option, then merge or delete after reading.

## 10. Status-Board State Machine (Single Entry Point)

Evaluate in order at startup; stop at the first match:

| Order | Condition | Next step |
|----|------|--------|
| 0 | Any source file fails to parse | **Repair card**: identify line, show context, propose an intent-preserving model fix, obtain author confirmation. Full-width colons/commas in structural positions (after keys/list separators) are deterministic errors: pre-fix and report without asking. **Never crash with a stack trace** |
| 1 | Unsettled edits in finalized content/outlines | Propose fix settlement |
| 2 | Incomplete workspace transaction | Resume from the interrupted stage |
| 3 | Just-settled chapter ends a volume | Volume retrospective |
| 4 | Chapter number reaches health-check interval | Health-check card |
| 5 | Otherwise | New-chapter brief (inner-loop step 1) |

All 8 legacy commands become internal stages of these states. Authors need only one entry point and “continue.”

## 11. Derived Cache: `.cache/index.db`

The only permitted persistent derived artifact, Git-ignored and disposable at any time. Rebuild on the first query, reading only source files in finalized content/outlines/style. Tables (machine domain, English names): `chapters` (expanded frontmatter), `promises`, `secrets`, `entities` (register), `fingerprints` (style-fingerprint history). **The rebuilder is the format's reference implementation**: complete reconstruction demonstrates format coherence.

## 12. Migration Mapping (v6 → v7, One-Time Script)

| v6 | v7 |
|----|----|
| `chapters/` | `finalized/chapters/` (add frontmatter; mark contract field as migrated) |
| `settings/` | `finalized/setting/` (add character-profile frontmatter) |
| `outlines/` (master/volume outlines) | `outlines/master-outline.md`、`outlines/volume outline/` |
| plot_threads / foreshadowing / chase_debt / reading_power | Generate one `outlines/promise/` file per entry |
| `.webnovel/state.json` | Expand once into `finalized/setting/` |
| `summaries/` | `finalized/memory/` |
| project_memory patterns / scratchpad | `prose style/style constitution.md` (human review before adoption) |
| `.story-system/` commit chain | Collapse into one initial migration commit; archive original directory read-only |
| index.db / vectors.db / projection_log | Delete (rebuild index in `.cache/`; vectors become an optional plugin) |

## 13. Explicit Non-Goals

- ❌ Monolithic YAML data files (always one Markdown file per record)
- ❌ Event-log tables and per-event witnesses projections (replaced by information-gap files + timeline attendance)
- ❌ Persistent vector databases (semantic retrieval is optional and never the primary factual-recall path)
- ❌ Persistent services (Dashboard becomes an on-demand static briefing reading the story repo only)
- ❌ Custom commit chains / projection_log / scratchpad
- ❌ Unconstrained model judgments of prose quality (explicitly excluded from lens responsibilities)
- ❌ Fully automatic unattended mode

## 14. Decision Log

### 0.1 → 0.2

| # | Question | Decision | Decider | Rationale |
|---|------|------|--------|------|
| 1 | Directory language | Chinese directories and author-visible fields; ASCII machine protocols | Author | Users write Chinese web novels; §2.1 constraints handle encoding costs |
| 2 | Track workspace in Git? | No by default; remove one `.gitignore` line to opt in; support both states | Claude | Keeps pre-acceptance work disposable by default; one-line switch meets advanced needs |
| 3 | Is simplified information-gap tracking enough? | Lightweight register + optional timeline attendance for ensemble scenes | Claude | One column vs. an event-projection mechanism differs in cost by two orders of magnitude |
| 4 | Who approves chapter summaries? | Author reviews/edits on acceptance card; settled with transaction | Author | Summaries seed long-term memory; one error can contaminate hundreds of chapters |
| 5 | Must every chapter settle a promise? | Keep hard machine check; author-only exemption on decision card with reason | Claude | Rules must be firm; exemptions are human taste decisions, not model decisions |

### 0.2 → 0.3 (Prompted by the Author Questioning Whether YAML Is Easy to Edit)

| # | Question | Decision | Decider | Rationale |
|---|------|------|--------|------|
| 6 | Monolithic YAML is unsafe for nonprogrammers | One Markdown + flat frontmatter per promise/information gap; book.yaml is the only pure YAML | Author raised it; Claude designed it | Full-width punctuation/indentation/type errors; blast radius shrinks from full ledger to one entry; free text returns to body |
| 7 | Prevent editing slips | Error-resistant dialect (§2.2): flat fields, block lists, quoted risky values | Claude | Authors can safely imitate generated output |
| 8 | Recover from editing slips | Repair card on parse failure (state 0 in §10), never crash; deterministic pre-fix of structural full-width punctuation | Claude | An LLM is always available, unlike ordinary software |
| 9 | Root solution | Adopt conversation-as-editor (invariant 9) | Claude | Authors never need to learn YAML |

### 0.3 → 0.4

| # | Question | Decision | Decider | Rationale |
|---|------|------|--------|------|
| 10 | The translation of canon sounded unnatural | Rename umbrella directory to `finalized/`, structure unchanged (alternatives: flatten top level or use official-history wording) | Author | Matches author thinking: drafts in workspace, accepted work in finalized content |
