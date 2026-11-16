# Reference CSV Data Specification

This directory contains structured knowledge entries searched by `reference_search.py`.

Core goals:

- Improve BM25 lexical recall for English webnovel queries.
- Return directly executable structured context to language models.
- Store itemizable knowledge in CSV while retaining methodological Markdown files.

Hard boundaries:

- **Do not put** AI-flavor reduction, AI-style removal, or polishing/replacement guidance in CSV.
- Keep that material in separate Markdown references.
- CSV content migration is **manual editing only**.
- Do not write or use automated migration, batch conversion, or automatic extraction scripts.

All CSV files use **UTF-8 with BOM**.

Column names, enum values, filenames, and queries use English runtime identifiers.

## Shared Columns (All Tables)

| Column | Required | Description | Example |
|------|------|------|------|
| `id` | Yes | Unique ID with table prefix | `NR-001`, `SP-002`, `WT-003` |
| `applicable_skills` | Yes | Multi-value field using `|` | `write|init|plan` |
| `category` | Yes | Topic category | `character`, `combat`, `emotional-relationships` |
| `level` | Yes | Reminder / defect compensation / supplementary knowledge | `reminder` / `defect-compensation` / `knowledge` |
| `keywords` | Yes | High-weight trigger terms; separate with `|` | `characternaming|personal names|xuanhuannaming` |
| `intent_synonyms` | No | Natural-language questions, jargon, idioms; separate with `|` | `how to choose names|naming|protagonistwhat to call` |
| `applicable_genres` | Yes | `all` or multiple genre names separated with `|` | `xuanhuan|xianxia` |
| `model_instruction` | No | Execution instruction passed directly to the model after retrieval | Prioritize genre-appropriate naming vocabulary; avoid modern associations. |
| `summary` | Yes | Concise summary for high-weight recall and display | Fantasy names should evoke cultivation and classical imagery rather than copied modern names. |
| `details` | No | Supplementary explanation used for low-weight recall | Prefer classical surnames and setting-related imagery; avoid duplicate core-character names. |

## General Rules

### 1. Separators

- Use `|` in every list-type field.
- This applies to:
  - `applicable_skills`
  - `keywords`
  - `intent_synonyms`
  - `applicable_genres`
- Legacy `,` / `，` separators remain parseable only for migration compatibility.
- Do not use comma separation in new or edited entries.

### 2. Long Text

- Keep fields concise, using short, focused English sentences.
- Split longer material into:
  - `summary`
  - `details`
- `summary` supports high-weight recall and display.
- `details` supplies additional explanation only; do not bury primary trigger terms there.

### 3. Instructions

- Write `model_instruction` as direct, actionable English imperatives while preserving the column name.
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

### naming.csv

| Column | Description |
|------|------|
| `naming_target` | Characters, book titles, places, factions, techniques, items, etc. |
| `rule` | Naming rule |
| `positive_example` | Positive example |
| `negative_example` | Negative example |

### scenes.csv

| Column | Description |
|------|------|
| `scene_type` | Combat, dialogue, narrative structure, plot scenes, etc. |
| `pattern_name` | Scene-writing pattern name |
| `description` | Additional scene-writing explanation |
| `example_excerpt` | Positive example |
| `negative examples` | Common failure pattern |

### techniques.csv

| Column | Description |
|------|------|
| `technique_type` | Dialogue, emotion, scene, pacing, etc. |
| `technique_name` | Technique name |
| `applicable_scenes` | Applicable writing scenario |
| `common pitfalls` | Frequent pitfalls |
| `positive_example` | Positive example |
| `negative_example` | Negative example |

### tropes.csv

| Column | Description |
|------|------|
| `trope_name` | Trope name |
| `setup` | Setup required before triggering |
| `core_payoff` | Primary payoff |
| `twist_design` | Key reversal |
| `subversive_variant` | Subversive variation |

### characters.csv

| Column | Description |
|------|------|
| `character_type` | Character-template name |
| `core_motivation` | Core goal driving behavior |
| `behavior_logic` | Behavioral logic |
| `interaction_pattern` | Typical interactions with others |
| `prohibited approaches` | Patterns that make characters foolish or formulaic |

### pacing.csv

| Column | Description |
|------|------|
| `pacing_type` | Suppression, eruption, payoff, etc. |
| `emotional_techniques` | Methods of steering reader emotion |
| `common failure modes` | Common pacing failures |

### powers.csv

| Column | Description |
|------|------|
| `setting_type` | System, inheritance, bloodline, world rules, etc. |
| `numeric_limits` | Caps, cooldowns, costs, limits |
| `plot_interaction` | Interaction with plot progression, conflict, and growth |

### genre-routing.csv

| Column | Description |
|------|------|
| `genre_route` | Routing entry; platform_tag or common user wording |
| `canonical_genre` | One of the 15 canonical genres, or `all` for general routing |
| `genre_aliases` | User aliases and jargon |
| `core_tone` | Tone reference for MASTER_SETTING |
| `pacing_strategy` | Pacing reference for MASTER_SETTING |
| `recommended_base_tables` | Tables searched when story-system builds base_context |
| `recommended_dynamic_tables` | Tables searched when story-system builds chapter dynamic_context |
| `default_query` | BM25 expansion queries after a route match |

### adjudication.csv

| Column | Description |
|------|------|
| `genre` | One of the 15 canonical genres |
| `style_priority` | Style decision order within a genre |
| `payoff_priority` | Payoff decision order within a genre |
| `default_pacing_strategy` | Default pacing written to CHAPTER_BRIEF reasoning |
| `pitfall_weight` | Basis for anti-pattern ranking |
| `conflict_resolution` | Ranking basis for matches from multiple tables |
| `contract_injection_layer` | Target location in Story Contracts for decisions |
| `anti_pattern` | Genre-level forbidden patterns merged into anti_patterns |

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

`applicable_genres` accepts only these 15 canonical values or `all`:

```
urban  xuanhuan  xianxia  fantasy  sci-fi
historical  mystery  game-lit  historical-romance  contemporary-romance
fantasy-romance  period-fiction  farming  quick-transmigration  fanfiction
```

See `genre-canonical.md` for the full two-level genre system (canonical + Fanqie `platform_tag` mapping).

**Do not put** the following in `applicable_genres`:

- Fanqie subcategory names (e.g. `urban-slice-of-life`, `warrior-son-in-law`): these are `platform_tag` values used only in routing tables.
- Trope names (e.g. `broken-engagement fiction`, `system-fiction`): these belong in `tropes.csv`.
- Tone / scene / format labels (e.g. `payoff-driven fiction`, `action`, `short-fiction`): these are outside the genre system.

## Retrieval

Search with `reference_search.py`:

```bash
python reference_search.py --skill write --query "characternaming" --genre xuanhuan
python reference_search.py --skill write --table naming --query "how to choose names" --genre xuanhuan
python reference_search.py --skill write --table techniques --query "emotional-relationshipsdescription psychological"
```
