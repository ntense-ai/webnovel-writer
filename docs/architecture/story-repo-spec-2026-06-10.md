# Story Repo Format Specification (v7 Draft 0.4 · Frozen)

> Status: 0.4. Change from 0.3: rename the umbrella directory to `定稿/` (finalized content), as chosen by the author: drafts stay in the workspace and move to finalized content after acceptance. Change from 0.2: abolish monolithic YAML data files; promises and information gaps use one Markdown file per entry with flat frontmatter (§4.3, §5). Add an error-resistant dialect (§2.2), repair cards (state 0 in §10), and the conversation-as-editor invariant (§1.9). See §14 for decisions.
> Source: the 2026-06-10 discussion of the most appropriate architecture + Phase 0 of the strangler-style convergence plan.
> Authority: this specification is the law for v7. Code derives from the format. If implementation conflicts with this specification, change one or the other; never silently store an extra copy in code.

---

## 0. In One Sentence

One book = one Git repository. `定稿/` stores accepted facts and prose, `大纲/` author intent and promises, `文风/` taste, and `工作区/` everything before the acceptance boundary. Accepting a chapter = one atomic commit. No persistent derived artifacts exist except one disposable cache.

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
<书名>/
├── .git/
├── .gitignore                 # Includes at least .cache/ and 工作区/
├── book.yaml                  # Book-wide configuration (§3)
├── 定稿/                       # ── After the acceptance boundary ──
│   ├── 正文/
│   │   └── 0152-北境的雪.md    # Chapter + frontmatter (§4.1)
│   ├── 设定/
│   │   ├── 角色/
│   │   │   └── 林晚.md         # Character profile (§4.2)
│   │   ├── 信息差/
│   │   │   └── S-021-灭门真凶.md  # Information gaps, one file per entry (§4.3)
│   │   ├── 世界观.md           # World rules and power system
│   │   ├── 时间线.md           # Append-only table (§4.4)
│   │   └── 名册.md             # Entity register: canonical name/aliases/first chapter (§4.5)
│   └── 记忆/
│       ├── 章摘要/0152.md      # Recorded at settle (§4.6)
│       └── 卷摘要/第05卷.md    # Generated during volume retrospective
├── 大纲/                       # ── Mutable author intent ──
│   ├── 总纲.md                 # Theme, special ability, ending promise
│   ├── 卷纲/
│   │   └── 第05卷.md
│   └── 承诺/
│       └── P-031-灭门真凶.md   # Promises, one file per entry (§5)
├── 文风/                       # ── Taste library ──
│   ├── 风格宪法.md             # （§6.1）
│   └── 金句库/                 # Automatically harvested (§6.2)
├── 工作区/                     # ── Before acceptance; Git-ignored by default ──
│   ├── 决策卡.md               # （§7）
│   ├── 上下文包.md             # Context pack for this rendering, retained for audit
│   ├── 草稿-A.md               # A/B/C for best-of-N
│   └── 评审报告/               # Machine-check and lens-review output
└── .cache/                     # Only permitted derived cache (§11)
    └── index.db
```

### 2.1 Engineering Constraints for Chinese Paths (Normative, CI-Enforced)

Handle the encoding cost of Chinese paths through hard constraints, not luck:

- Use explicit `encoding='utf-8'` for all file I/O; inject `PYTHONUTF8=1` at script/subprocess entry points; never rely on system locale.
- Set `git config core.quotepath false` during repository initialization so Chinese paths remain readable in Git logs.
- Sort files using zero-padded numeric prefixes (`0152-`, `第05卷`, `P-031`), not Chinese lexicographic order.
- Reference entities by their **canonical Chinese name**; resolve aliases through the register (§4.5). Do not introduce ASCII entity IDs.
- CI must include an end-to-end Windows test with Chinese paths (create repository → write chapter → settle → rebuild cache).

### 2.2 Error-Resistant Dialect (Normative Output-Format Constraints)

The three main YAML editing pitfalls for nonprogrammers are full-width punctuation, indentation, and surprising type coercion. All system-generated structured content must follow this dialect, so authors can safely imitate it:

- **Always flat**: No nested mappings in frontmatter or `book.yaml`; all fields are top-level.
- **Always block lists** (one item per line, such as `- 晚晚`); no inline `[a, b]`. Block lists avoid full-width comma problems.
- **Quote risky values**: Automatically quote strings that YAML might misinterpret (numeric-looking values, true/false/yes/no/是/否 forms).
- Use two-space indentation and UTF-8 without BOM.
- **Always one record per file**, never monolithic data files. A damaged entry affects only itself. Free text belongs in the Markdown body (full-width punctuation is fine); frontmatter contains only a few short, flat fields.

## 3. book.yaml

The repository's only pure YAML file: infrequently edited, flat, at most ten lines. Chinese format keys and example values below remain literal.

```yaml
spec_version: "7.0"
书名: 示例书名
类型: 玄幻
每章目标字数: 3000
卷规模: 40                 # Reference value, not a hard constraint
文体基线起: 1              # Style-fingerprint baseline chapter range; author-editable
文体基线止: 30
高承诺最大搁置章数: 10     # Exceeding this flags pacing debt
连续弱钩上限: 3
关键章稿数: 3              # best-of-N for volume openings/turning points/climaxes
```

## 4. Finalized Content: `定稿/`

Drafts live in the workspace and move into finalized content after acceptance; the directory name expresses the mental model.

### 4.1 Chapter Files: `定稿/正文/NNNN-标题.md`

Filename: four-digit zero-padded chapter number + hyphen + title. Frontmatter carries the chapter contract and settlement summary: **each chapter contains its own acceptance record**, so audits need no external table. Only settle writes this file; authors edit the prose, not frontmatter.

```markdown
---
章号: 152
标题: 北境的雪
卷: 5
视角: 林晚
书内时间: 大历1023年冬月初三    # Free text; consistent format throughout the book
字数: 3120
开启承诺:
  - P-058
推进承诺:
  - P-031
  - P-007
兑付承诺:
  - P-019
合同:                           # Contract assertions at acceptance time (validated)
  - 林晚 obtains the first concrete evidence of the massacre truth
  - P-058 opens: the mysterious elder's origins
  - Strong ending hook: the mystic-rank token appears
---
Chapter prose…
```

### 4.2 Character Profiles: `定稿/设定/角色/<正名>.md`

Frontmatter contains structured fields for machine checks (flat, block lists); the body contains free-form setting text.

```markdown
---
姓名: 林晚
别名:
  - 晚晚
  - 林师妹
状态: 在世                # Alive/dead/missing/sealed…
位置: 北境雪原            # Last known location
境界: 筑基七层            # Scale defined in 世界观.md
持有:
  - 青霜剑
  - 玄阶令牌
最后变更章: 152
---
## 设定
…Free text…
## 关系
…Free text; significant relationship changes also belong in the timeline…
```

### 4.3 Information Gaps: `定稿/设定/信息差/<编号>-<短题>.md`

Do not track every event known by every character. Register only **information gaps worth managing**, one per file. Leakage checks scan dialogue/interior monologue for keywords from information the character does not know. Redundancy checks flag repetition of information already known to the reader. Ensemble-scene attendance is covered by the timeline's present column (§4.4), not a separate mechanism.

```markdown
---
知情人:
  - 大长老
  - 神秘老者
读者已知: false
登记章: 87
关键词:                   # Used for leakage scanning
  - 大长老
  - 灭门
  - 血书
---
## 内容
The Grand Elder ordered the massacre; his sworn assassins carried it out.
```

### 4.4 Timeline: `定稿/设定/时间线.md`

An append-only Markdown table; settle appends a row. **The present column may be empty**: unnecessary for everyday chapters, recommended for ensemble/conspiracy scenes. It is the sole source for later queries about who witnessed what.

```markdown
| 章 | 书内时间 | 一句话事件 | 在场 |
|----|----------|------------|------|
| 152 | 1023冬月初三 | 林晚 obtains a blood-written letter in the north; the mystic-rank token appears | 林晚, 神秘老者 |
```

### 4.5 Entity Register: `定稿/设定/名册.md`

Prevent one person appearing under multiple names, or different people sharing a name. Table: `| 正名 | 别名 | 类型 | 首现章 |` (canonical name / aliases / type / first chapter). At settle, machine checks compare new proper names in prose with the register; unregistered names go onto the acceptance card for author confirmation as new entities or typos.

### 4.6 Memory Layer: `定稿/记忆/`

- `章摘要/NNNN.md`: ≤200 characters, generated by the model before settle and **shown on the acceptance card for the author to review/edit**, then recorded with the transaction.
- `卷摘要/第NN卷.md`: ≤500 characters, generated at volume retrospective; main-plot progress, relationship changes, and outstanding promises.
- The longer-range book skeleton is **derived** by assembling/compressing volume summaries on demand; do not persist it.

## 5. Promises: `大纲/承诺/` (One File per Entry)

The system's heart. Foreshadowing, mysteries, relationship arcs, anticipated payoffs, and declarations all become promises to the reader. Filename: `P-031-灭门真凶.md` (ID-short title). Frontmatter has only six short, flat fields; description, payoff plan, and history are free-form Markdown body text.

```markdown
---
类型: 悬念                # Foreshadowing|mystery|conflict|relationship|declaration|payoff setup
强度: 高                  # High|medium|low
状态: 进行                # Active|fulfilled|abandoned
开启章: 12
兑付期限: 第7卷           # Volume or chapter; required when intensity is high
最后推进章: 152
---
## 描述
The identity of the mastermind behind the massacre.

## 兑付计划
Expose the mastermind publicly at the sect assembly in volume seven. Required when opening the promise to prevent dangling threads.

## 履历
- Chapter 12: opened
- Chapter 87: advanced; the blood-letter clue appears
- Chapter 152: advanced; 林晚 obtains concrete evidence
```

**Settlement rules (script-executed, machine-check level)**:

- Every chapter settle must touch (open/advance/fulfill) at least one promise or be rejected. **Exemption belongs on the decision card**: when approving the brief, the author may exempt the chapter from promise settlement with a mandatory reason, such as a standalone extra. The model cannot exempt itself.
- settle writes to promise files by updating frontmatter (status/last-advanced chapter) and appending a history entry.
- A new promise requires a payoff plan; high-intensity promises require a payoff deadline.
- Pacing debt = high intensity and `current chapter − last-advanced chapter > maximum idle chapters for high promises`; show a yellow warning on the decision card.
- Abandonment must record a reason in history; even author-chosen abandonment needs an audit trail.
- Ledger-level views (due list, pacing debt, statistics) come from `.cache/` and the status board; **maintain no aggregate files**.
- Derived metrics, not separate mechanisms: cliffhanger intensity = intensity of outstanding promises at chapter end; retention risk = pacing-debt count + consecutive weak-hook count.

## 6. Style: `文风/`

### 6.1 Style Constitution: `文风/风格宪法.md`

Everything the system knows about the author's taste, available for author review/editing. Frontmatter is machine-consumed (block lists; verbal habits are flat character:phrase list items, not nested):

```markdown
---
禁词:
  - 眸子一缩
  - 嘴角勾起一抹
禁句式:
  - '不是.*而是'
口癖:
  - 林晚：自称"本姑娘"
---
## 铁律
…
## 节奏偏好
…
## 来自否决的规则
- Do not open with weather (source: three rejections in chapters 89/103/121)
```

Rules enter the constitution through three similar rejections → system proposal → author confirmation. Every rule cites its source.

### 6.2 Exemplar Library: `文风/金句库/`

At settle, if `diff(model draft, author final)` exceeds the threshold (default: >30% change in one paragraph), automatically save the author-edited paragraph plus a scene tag as an exemplar. Inject it as few-shot guidance for similar scenes. Separate files by scene: `战斗.md`, `对白.md`, `情感.md`, etc. Keep the latest 20 entries per file and rotate older entries into archives.

## 7. Workspace (`工作区/`) and Decision Cards

The entire workspace is Git-ignored by default; everything before acceptance may be discarded. Contracts ultimately live in chapter frontmatter (§4.1). **Users wanting draft history can remove that one `.gitignore` line**: settle still clears the workspace, behavior is unchanged, and Git retains history naturally. This is normative: implementation must not assume the workspace is untracked.

`决策卡.md` is the only interface the author needs to read, with four fixed sections (status board, proposal, contract, alternatives). The example retains literal format headings:

```markdown
# 决策卡：第 152 章
## 盘面（脚本生成）
- Position: volume 5, chapter 24/40
- Pacing debt: P-031 (high, no progress for 12 chapters)
- Consecutive weak hooks: 2 chapters
## 提案
Advance P-031 (林晚 obtains evidence), open P-058 along the way, and end on the mystic-rank token's appearance.
## 合同（拍板即生效）
- [ ] 林晚 obtains the first concrete evidence of the massacre truth
- [ ] P-058 opens: the mysterious elder's origins
- [ ] Strong ending hook
## 备选
Option B: a relationship-only transition chapter; defer P-031 to the next chapter (cost: pacing debt +1)
(If promise settlement is exempted, state the reason here)
```

The author has only three actions: adopt / edit the card / choose an alternative. Editing means changing this file directly or asking the system in one sentence (invariant 9).

## 8. Chapter Transaction (Inner Loop)

| # | Stage | Executor | File effect |
|---|------|--------|----------|
| 1 | brief | Script reads status board | Generate `工作区/决策卡.md` |
| 2 | Approve | **Author** | Freeze the decision card contract section |
| 3 | pack | Script | Assemble `工作区/上下文包.md`: status board + contract + fact slices + information-gap boundaries + recent chapter endings + anti-repetition list + style anchors |
| 4 | Render | Model (clean context) | `工作区/草稿-*.md`; best-of-N for key chapters |
| 5 | Machine check | Script | Contract assertions, information-leak scan, banned terms/repetition, new proper names vs. register, character count. **On failure, return to step 4 without interrupting the author** |
| 6 | Lens review | 3 models (each with fresh context) | Reader lens (satisfaction/where to skip), editor lens (structure/commercial appeal), fact lens (explain machine-check results only) → `工作区/评审报告/` |
| 7 | Accept | **Author** | Acceptance card = draft + three-sentence review + unconfirmed new names + **chapter summary (review/edit)**. Actions: accept / edit and accept / reject |
| 8 | settle | Script, **atomic** | See below |

**One settle commit includes**: draft → `定稿/正文/` (contract and promise settlement in frontmatter); changes to `设定/` (location/status/realm/possessions/information gaps/register/timeline); settlement of affected `大纲/承诺/` files (frontmatter updates + history append); `记忆/章摘要/` (accepted-card final version); harvesting into `文风/金句库/` if triggered; workspace clearing.

**Commit-message convention** (ASCII prefixes are machine protocol, convenient for `git log --grep`):

```text
ch(152): 北境的雪

承诺: +P-058 ~P-031 ~P-007 $P-019     # + open ~ advance $ fulfill
设定: 林晚.位置=北境雪原; 信息差+S-021
```

## 9. Middle/Outer Loops and Exceptional Transactions

- **Volume retrospective** `vol(05): 复盘与下卷规划`: audit promises (opened/fulfilled/overdue this volume) → `记忆/卷摘要/` → discuss with the author to create `大纲/卷纲/第06卷.md` → scan foreshadowing opportunities (model proposes 3–5 seeds for this volume paying off N volumes later, citing specific distant master-outline nodes; generate promise files after author selection).
- **Health check** (automatic every 50 chapters): style-fingerprint drift vs. baseline + bad promise debt + timeline orphans → report in workspace, not settled; author chooses correction or baseline update.
- **retcon**: `retcon(87): 修正大长老境界设定`. Explicit transaction permitting finalized-content changes, with a reason in the commit message, synchronized settings/promises, and an audit trail.
- **Manual-edit detection**: On startup, `git status` finds unsettled edits in finalized content/outlines → ask on the decision card whether to settle; after confirmation record as `fix(设定): …`. **The system adapts to the author instead of reporting an error.**
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
| `正文/` | `定稿/正文/` (add frontmatter; mark contract field as migrated) |
| `设定集/` | `定稿/设定/` (add character-profile frontmatter) |
| `大纲/` (master/volume outlines) | `大纲/总纲.md`、`大纲/卷纲/` |
| plot_threads / foreshadowing / chase_debt / reading_power | Generate one `大纲/承诺/` file per entry |
| `.webnovel/state.json` | Expand once into `定稿/设定/` |
| `summaries/` | `定稿/记忆/` |
| project_memory patterns / scratchpad | `文风/风格宪法.md` (human review before adoption) |
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
| 10 | The translation of canon sounded unnatural | Rename umbrella directory to `定稿/`, structure unchanged (alternatives: flatten top level or use official-history wording) | Author | Matches author thinking: drafts in workspace, accepted work in finalized content |
