# Reference CSV Data Specification

This directory contains structured knowledge entries searched by `reference_search.py`.

Core goals:

- Improve BM25 lexical recall for Chinese webnovel scenarios.
- Return directly executable structured context to language models.
- Store itemizable knowledge in CSV while retaining methodological Markdown files.

Hard boundaries:

- **Do not put** AI-flavor reduction, AI-style removal, or polishing/replacement guidance in CSV.
- Keep that material in separate Markdown references.
- CSV content migration is **manual editing only**.
- Do not write or use automated migration, batch conversion, or automatic extraction scripts.

All CSV files use **UTF-8 with BOM**.

Chinese column names, enum values, filenames, and retrieval queries below are literal runtime identifiers retained for compatibility with unchanged CSV data and scripts.

## Shared Columns (All Tables)

| Column | Required | Description | Example |
|------|------|------|------|
| `编号` | Yes | Unique ID with table prefix | `NR-001`, `SP-002`, `WT-003` |
| `适用技能` | Yes | Multi-value field using `|` | `write|init|plan` |
| `分类` | Yes | Topic category | `角色`, `战斗`, `情感` |
| `层级` | Yes | Reminder / defect compensation / supplementary knowledge | `提醒` / `缺陷补偿` / `知识补充` |
| `关键词` | Yes | High-weight trigger terms; separate with `|` | `角色命名|人名|玄幻命名` |
| `意图与同义词` | No | Natural-language questions, jargon, idioms; separate with `|` | `名字怎么取|起名|主角叫什么` |
| `适用题材` | Yes | `全部` or multiple genre names separated with `|` | `玄幻|仙侠` |
| `大模型指令` | No | Execution instruction passed directly to the model after retrieval | Prioritize genre-appropriate naming vocabulary; avoid modern associations. |
| `核心摘要` | Yes | Concise summary for high-weight recall and display | Fantasy names should evoke cultivation and classical imagery rather than copied modern names. |
| `详细展开` | No | Supplementary explanation used for low-weight recall | Prefer classical surnames and setting-related imagery; avoid duplicate core-character names. |

## General Rules

### 1. Separators

- Use `|` in every list-type field.
- This applies to:
  - `适用技能`
  - `关键词`
  - `意图与同义词`
  - `适用题材`
- Legacy `,` / `，` separators remain parseable only for migration compatibility.
- Do not use comma separation in new or edited entries.

### 2. Long Text

- Keep each field concise (legacy Chinese entries target at most 200 characters). English additions should use short, focused sentences.
- Split longer material into:
  - `核心摘要`
  - `详细展开`
- `核心摘要` supports high-weight recall and display.
- `详细展开` supplies additional explanation only; do not bury primary trigger terms there.

### 3. Instructions

- For English additions, write `大模型指令` as direct, actionable English imperatives while preserving the column name. Existing rows remain Chinese source material; translate retrieved guidance into natural English when presenting it to English-language users.
- Prioritize what to check, what to avoid, and how to adjudicate.
- Avoid vague wording such as "write better" or "pay attention to prose quality."

### 4. Manual Migration

- Allowed: Manual entry-by-entry edits, manual copying followed by cleanup, manually adding summaries and synonyms.
- Prohibited: Scripted batch conversion, regex-generated bulk content, programmatic Markdown-to-CSV extraction.
- Historical bulk-migration scripts were removed. Edit entries manually, then run `scripts/validate_csv.py`.
- Rationale: Entry quality matters more than migration speed.

## ID Prefixes

| Prefix | Table |
|------|------|
| `NR-` | Naming rules |
| `SP-` | Scene writing |
| `WT-` | Writing techniques |
| `TR-` | Plot tropes |
| `CH-` | Characterization and relationships |
| `PA-` | Payoffs and pacing |
| `SY-` | Special advantages and settings |
| `GR-` | Genre and tone reasoning |
| `RS-` | Decision rules |

## Table-Specific Columns

### 命名规则.csv

| Column | Description |
|------|------|
| `命名对象` | Characters, book titles, places, factions, techniques, items, etc. |
| `规则` | Naming rule |
| `正例` | Positive example |
| `反例` | Negative example |

### 场景写法.csv

| Column | Description |
|------|------|
| `场景类型` | Combat, dialogue, narrative structure, plot scenes, etc. |
| `模式名称` | Scene-writing pattern name |
| `说明` | Additional scene-writing explanation |
| `示例片段` | Positive example |
| `反面写法` | Common failure pattern |

### 写作技法.csv

| Column | Description |
|------|------|
| `技法类型` | Dialogue, emotion, scene, pacing, etc. |
| `技法名称` | Technique name |
| `适用场景` | Applicable writing scenario |
| `常见误区` | Frequent pitfalls |
| `正例` | Positive example |
| `反例` | Negative example |

### 桥段套路.csv

| Column | Description |
|------|------|
| `桥段名称` | Trope name |
| `前置铺垫` | Setup required before triggering |
| `核心爽点` | Primary payoff |
| `转折设计` | Key reversal |
| `反套路变种` | Subversive variation |

### 人设与关系.csv

| Column | Description |
|------|------|
| `人设类型` | Character-template name |
| `核心动机` | Core goal driving behavior |
| `行为逻辑` | Behavioral logic |
| `互动模式` | Typical interactions with others |
| `忌讳写法` | Patterns that make characters foolish or formulaic |

### 爽点与节奏.csv

| Column | Description |
|------|------|
| `节奏类型` | Suppression, eruption, payoff, etc. |
| `情绪调动手法` | Methods of steering reader emotion |
| `常见崩盘误区` | Common pacing failures |

### 金手指与设定.csv

| Column | Description |
|------|------|
| `设定类型` | System, inheritance, bloodline, world rules, etc. |
| `数值控制边界` | Caps, cooldowns, costs, limits |
| `与剧情交互方式` | Interaction with plot progression, conflict, and growth |

### 题材与调性推理.csv

| Column | Description |
|------|------|
| `题材/流派` | Routing entry; platform_tag or common user wording |
| `canonical_genre` | One of the 15 canonical genres, or `全部` for general routing |
| `题材别名` | User aliases and jargon |
| `核心调性` | Tone reference for MASTER_SETTING |
| `节奏策略` | Pacing reference for MASTER_SETTING |
| `推荐基础检索表` | Tables searched when story-system builds base_context |
| `推荐动态检索表` | Tables searched when story-system builds chapter dynamic_context |
| `默认查询词` | BM25 expansion queries after a route match |

### 裁决规则.csv

| Column | Description |
|------|------|
| `题材` | One of the 15 canonical genres |
| `风格优先级` | Style decision order within a genre |
| `爽点优先级` | Payoff decision order within a genre |
| `节奏默认策略` | Default pacing written to CHAPTER_BRIEF reasoning |
| `毒点权重` | Basis for anti-pattern ranking |
| `冲突裁决` | Ranking basis for matches from multiple tables |
| `contract注入层` | Target location in Story Contracts for decisions |
| `反模式` | Genre-level forbidden patterns merged into anti_patterns |

## Markdown Suitable for CSV Migration

Suitable for manual extraction into CSV entries:

- Entry libraries
- Template libraries
- Rule lists
- Collections of common pitfalls and positive/negative examples

Not suitable for replacement by CSV:

- Workflow specifications
- Methodological overviews
- Review schemas
- Project hard constraints
- AI-flavor polishing guidance

## Applicable Genre Enumeration

`适用题材` accepts only these 15 canonical values or `全部`:

```
都市  玄幻  仙侠  奇幻  科幻
历史  悬疑  游戏  古言  现言
幻言  年代  种田  快穿  衍生
```

See `genre-canonical.md` for the full two-level genre system (canonical + Fanqie `platform_tag` mapping).

**Do not put** the following in `适用题材`:

- Fanqie subcategory names (e.g. `都市日常`, `战神赘婿`): these are `platform_tag` values used only in routing tables.
- Trope names (e.g. `退婚流`, `系统流`): these belong in `桥段套路.csv`.
- Tone / scene / format labels (e.g. `爽文`, `动作`, `短篇`): these are outside the genre system.

## Retrieval

Search with `reference_search.py`:

```bash
python reference_search.py --skill write --query "角色命名" --genre 玄幻
python reference_search.py --skill write --table 命名规则 --query "名字怎么取" --genre 玄幻
python reference_search.py --skill write --table 写作技法 --query "情感描写 心理"
```
