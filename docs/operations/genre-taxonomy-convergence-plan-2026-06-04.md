# Genre Taxonomy Convergence Plan

Date: 2026-06-04
Status: Second revision

## Goal

Converge on the 15 `canonical_genre` values already used by the CSV data, while retaining 37 Chinese-named genre templates as composable initialization presets.

Guiding principle:

> CSV canonical values form the retrieval backbone; the taxonomy index is the source of truth for user input; template files are presets; platform subdivisions, tropes, and formats become tags.

## Verified Facts

- `webnovel-writer/templates/genres/*.md` currently contains 37 files.
- Only initialization directly reads these templates:
  - `skills/webnovel-init/SKILL.md` directs loading from `templates/genres/` based on the requested genre.
  - `scripts/init_project.py` builds `templates/genres/{key}.md` after `_normalize_genre_key()`.
- At least three input-normalization implementations exist, with different output namespaces:
  - `scripts/init_project.py::_normalize_genre_key()`: user input → template filename.
  - `scripts/reference_search.py::resolve_genre()`: user input/platform label/legacy value → 15 canonical values.
  - `scripts/data_modules/genre_aliases.py::GENRE_INPUT_ALIASES`: user input → preliminary label for the old template/profile key.
- Mapping size must no longer be estimated vaguely as a few dozen:
  - `PLATFORM_TO_CANONICAL`: 34 keys.
  - `_LEGACY_GENRE_MAP`: 27 keys.
  - Their union has 54 keys, with 7 overlaps.
  - Including 15 canonical values and `全部`, `resolve_genre()` handles 67 distinct inputs.
  - Adding the 15 input aliases from `_normalize_genre_key()` / `GENRE_INPUT_ALIASES` yields 78 distinct labels.
  - Including the 37 template stems brings complete coverage to 92 distinct labels/stems.
- `_normalize_genre_key()` and `GENRE_INPUT_ALIASES` contain the same 15 mappings: duplicated sources of truth.
- The current `state.json` schema uses `project_info.genre`, not top-level `project.genre`.
- Legacy `project.genre` consumers extend beyond plan/write:
  - `skills/webnovel-init/SKILL.md`
  - `skills/webnovel-plan/SKILL.md`
  - `skills/webnovel-write/SKILL.md`
  - `skills/webnovel-review/SKILL.md`
  - `scripts/data_modules/context_manager.py`
  - `scripts/data_modules/memory_contract_adapter.py`
- `context_manager.py` currently prioritizes `project.genre` and falls back to `project_info.genre`; reverse this to prefer `project_info`.
- `memory_contract_adapter.py` currently falls back from Story Contracts route → protagonist genre → legacy `state.project.genre`, without reading `project_info.genre`. Add `project_info` and put legacy `project.genre` last.
- `story_system_engine.py::_route()` includes keyword/alias matching, explicit-genre fallback, and inferred-genre fallback. If all fail, it raises `StorySystemRoutingError`; it does not silently fall back.
- `references/csv/题材与调性推理.csv` currently has 26 route rows. Tests must cover the actual complete CSV dynamically rather than hard-code 26 or 27.
- `references/genre-profiles.md` is already a fallback; frequently used genres have moved to Story Contracts as the mainline.

## Design Boundaries

### 1. Keep the Two Namespaces Distinct

A unified resolver does not imply a single output value. Explicitly distinguish:

- `canonical_genre`: CSV retrieval, Story System, adjudication rules, and new projects' `project_info.genre`.
- `template_files`: initialization loading of `templates/genres/*.md`.

Typical conflict:

- Old initialization: `玄幻 -> 修仙.md`.
- Old reference resolution: `resolve_genre("玄幻") -> 玄幻`.

The new resolver must express both simultaneously. Chinese labels in examples below are runtime identifiers, not untranslated prose.

```python
GenreResolution(
    raw_label="玄幻",
    canonical_genre="玄幻",
    template_files=["修仙.md"],
    matched_labels=["玄幻"],
    route_tags=[],
    trope_tags=[],
    format_tags=[],
    unresolved=[],
    warnings=[]
)
```

### 2. Fixed Genre Enum

Keep the same 15 canonical values as the only hard enum:

```text
都市 玄幻 仙侠 奇幻 科幻
历史 悬疑 游戏 古言 现言
幻言 年代 种田 快穿 衍生
```

Used by:

- CSV `适用题材`
- `题材` in `裁决规则.csv`
- Story System `canonical_genre`
- `reference_search.py --genre`
- New-project `state.json.project_info.genre`

### 3. Taxonomy Index

Add `webnovel-writer/references/taxonomy/genre-index.csv`. This is not merely a template inventory, but the single taxonomy data source for user input.

Suggested fields:

```csv
label,canonical_genre,label_type,template_file,route_tags,trope_tags,format_tags,aliases,notes
修仙,玄幻,preset,修仙.md,,,,"玄幻;玄幻修仙;修仙/玄幻;修真","preserve old init: 玄幻 loads 修仙.md"
都市脑洞,都市,platform,都市脑洞.md,都市脑洞,,,"都市奇闻",
高武,都市,platform,高武.md,高武,,,"都市高武",
电竞,游戏,platform,电竞.md,游戏电竞,,,"电竞文;游戏电竞",
直播文,现言,format,直播文.md,,,直播文,"直播;直播带货;主播",
克苏鲁,悬疑,preset,克苏鲁.md,克苏鲁,,,"克系;克系悬疑",
规则怪谈,悬疑,route,规则怪谈.md,规则怪谈,,,"规则动物园;规则类",
知乎短篇,现言,format,知乎短篇.md,,,知乎短篇,"知乎体;盐选;小程序短篇",
历史古代,历史,platform,历史古代.md,历史古代,,,"",
青春甜宠,现言,platform,青春甜宠.md,青春甜宠,,,"青春",
游戏体育,游戏,platform,游戏体育.md,游戏体育,,,"网游;竞技;体育",
民国言情,年代,platform,民国言情.md,民国言情,,,"",
武侠,历史,legacy,,,,,,legacy without template
```

Rules:

- Every `templates/genres/*.md` must have exactly one index row pointing to it through `template_file`.
- `label` and `aliases` share one lookup namespace; each must be unique and cannot map to multiple canonical values.
- Separate aliases with `;`; quote CSV fields containing commas.
- Platform/legacy aliases without templates must also move into the index rather than remain hard-coded in Python.
- `canonical_genre` must be one of the 15 canonical values or `全部`.
- Suggested `label_type`: `canonical`, `platform`, `route`, `trope`, `format`, `preset`, `legacy`.
- Do not add a separate `template_type` that duplicates `label_type`. Express template purpose through `label_type` and tag columns together.
- Do not migrate `GENRE_PROFILE_KEY_ALIASES` yet. It outputs English profile-section keys, a different namespace from canonical/template values. Phases 1–5 migrate only input aliases; retain and clearly name/document the profile-key mapping.

### 4. Resolver Contract

Add a shared loader/resolver, for example `scripts/genre_taxonomy.py`:

```python
GenreResolution(
    raw_label="知乎短篇风的规则怪谈",
    canonical_genre="悬疑",
    matched_labels=["规则怪谈", "知乎短篇"],
    template_files=["规则怪谈.md", "知乎短篇.md"],
    route_tags=["规则怪谈"],
    trope_tags=[],
    format_tags=["知乎短篇"],
    unresolved=[],
    warnings=[]
)
```

Compatibility:

- Keep `reference_search.resolve_genre()` as a wrapper returning only canonical or original values for existing callers.
- `_normalize_genre_key()` must no longer own an alias dictionary. If retained temporarily, delegate to the taxonomy resolver and return the first `template_file` stem.
- `data_modules/genre_aliases.py` must stop maintaining `GENRE_INPUT_ALIASES`. Keep only profile-key mappings, or obtain a template/profile lookup label through taxonomy first.
- Do not alter Story System `_route()` table-matching semantics; connect input canonicalization to the same wrapper.
- Cache the loader, for example with `functools.lru_cache`, to avoid repeatedly reading CSV on hot paths.

### 5. Matching Algorithm

Define and test this explicitly in Phase 1.5:

1. Normalize input: trim, unify full-width/half-width punctuation, ignore case, remove excess whitespace.
2. Split tokens on `+`, `＋`, `/`, `、`, `,`, `，`, `|`, and `与`.
3. Prefer exact matches: tokens matching a `label` or alias enter the results directly.
4. Fall back to longest substring matching: scan the complete original input by descending label/alias length, supporting composite language such as `知乎短篇风的规则怪谈`.
5. Deduplicate and resolve conflicts:
   - Keep each `template_file` once.
   - `route/platform/canonical/preset` take priority in selecting `canonical_genre`.
   - `format/trope` may add tags/templates but must not override route/platform canonical choices.
   - If high-priority labels imply different canonical values, return `warnings=["ambiguous_canonical"]`; initialization should show the inference and let the user confirm.
6. Put unmatched fragments into `unresolved`. Preserve wrapper behavior: `resolve_genre()` returns the original value rather than failing immediately.

## State Schema

New initialization writes:

```json
{
  "project_info": {
    "genre": "悬疑",
    "genre_label": "知乎短篇风的规则怪谈",
    "genre_tags": {
      "route": ["规则怪谈"],
      "trope": [],
      "format": ["知乎短篇"],
      "templates": ["规则怪谈", "知乎短篇"]
    }
  }
}
```

Read compatibility order:

1. `project_info.genre`
2. `project_info.genre_label`
3. Legacy `project.genre`
4. Configuration fallback

Do not add top-level `project.genre` to new projects.

## Scope of Changes

### Required

- `templates/genres/*.md`
  - The historical plan calls for Chinese H1 headings.
  - Do not move files.
- `references/taxonomy/genre-index.csv`
  - Cover all 37 templates.
  - Cover labels/aliases from `PLATFORM_TO_CANONICAL`, `_LEGACY_GENRE_MAP`, `_normalize_genre_key()`, and `GENRE_INPUT_ALIASES`.
- `scripts/genre_taxonomy.py`
  - Add shared CSV loader/resolver.
- `scripts/reference_search.py`
  - Remove hard-coded `PLATFORM_TO_CANONICAL` and `_LEGACY_GENRE_MAP`.
  - Delegate `resolve_genre()` to the taxonomy wrapper.
- `scripts/init_project.py`
  - Parse raw genre input through taxonomy.
  - Write canonical values into `project_info.genre`.
  - Load presets by `template_file`, not paths assembled directly from raw input.
- `scripts/data_modules/genre_aliases.py`
  - Remove `GENRE_INPUT_ALIASES`.
  - Retain and document `GENRE_PROFILE_KEY_ALIASES` as belonging to the fallback profile-key namespace.
- `scripts/data_modules/context_manager.py`
  - Replace current `project.genre` priority with `project_info.genre` / `genre_label`, then legacy fallback.
- `scripts/data_modules/memory_contract_adapter.py`
  - Add `project_info.genre` / `genre_label` to the fallback chain, with legacy `project.genre` last.
- `skills/webnovel-init/SKILL.md`
  - Display only 15 canonical values as primary genres.
  - Correct the legacy `project.genre` shell snippet.
  - Explain that presets, tropes, and formats are accepted but mapped to canonical values at runtime.
- `skills/webnovel-plan/SKILL.md`
  - Correct all legacy `project.genre` shell snippets.
- `skills/webnovel-write/SKILL.md`
  - Correct the legacy `project.genre` snippet.
- `skills/webnovel-review/SKILL.md`
  - Correct the legacy `project.genre` snippet.
- `templates/output/state-schema.md`
  - Add `project_info.genre_label` and `project_info.genre_tags` examples.
- `scripts/validate_csv.py`
  - Add bidirectional taxonomy validation.
  - Add symmetric-difference checks between the three old dictionaries and the index.
- Tests
  - Resolver compatibility for `reference_search`.
  - State/schema/template loading for `init_project`.
  - End-to-end Story System routes against real CSV data.
  - Grep/fixture checks for genre reads in every SKILL.md.

### Recommended

- `references/csv/genre-canonical.md`
  - Clarify that `题材/流派` in `题材与调性推理.csv` is a route tag, not a canonical enum.
- `references/csv/README.md`
  - Explain taxonomy index, template preset, and canonical relationships.
- `references/index/reference-loading-map.md`
  - Update initialization genre-template loading.
- `references/genre-profiles.md`
  - Replace documented `project.genre` with `project_info.genre` and identify fallback status.

### Deferred

- No large rewrite of the nine core CSVs.
- Do not delete the 37 templates.
- Do not immediately split `templates/genres/` into `canonical/` and `presets/`.
- No bulk migration of existing users' `state.json`; provide compatible reads only.
- Do not restore `genre-profiles.md` as primary truth.
- Do not migrate `GENRE_PROFILE_KEY_ALIASES` during Phases 1–5; evaluate its separate fallback namespace later.

## Phases

### Phase 1: Taxonomy Index and Template Validation

Scope:

- Add `references/taxonomy/genre-index.csv`.
- Cover all 37 template files.
- Include these complete sets in `label` or `aliases`:
  - 15 `GENRE_CANONICAL` values and `全部`.
  - 34 `PLATFORM_TO_CANONICAL` keys.
  - 27 `_LEGACY_GENRE_MAP` keys.
  - 15 `_normalize_genre_key()` keys.
  - 15 `GENRE_INPUT_ALIASES` keys.
  - 37 template stems.
- One row may contain several aliases; 92 rows are not required, but full coverage is.
- The historical plan specifies Chinese-only H1 headings without English parentheses.
- Validate:
  - Actual template files and index `template_file` values match bidirectionally.
  - Every template exists and is unique.
  - Canonical values belong to the 15 values or `全部`.
  - Labels/aliases are unique and do not map to several canonical values.
  - Symmetric differences against old dictionary keys are empty or explicitly allowlisted.

No runtime changes in this phase.

Verification:

```powershell
(Get-ChildItem -Path webnovel-writer\templates\genres -Filter *.md | Measure-Object).Count
python -X utf8 webnovel-writer\scripts\validate_csv.py
```

### Phase 1.5: Establish the Resolver Contract First

Scope:

- Add the shared loader/resolver.
- Define structured `GenreResolution`.
- Implement and test the exact + longest-substring algorithm in section 5.
- Document delegation for `reference_search.resolve_genre()`, initialization template resolution, and `genre_aliases` profile lookup.
- Keep `GENRE_PROFILE_KEY_ALIASES` in `genre_aliases.py`, but source input aliases from taxonomy.
- Prove old behavior is preserved:
  - Existing `PLATFORM_TO_CANONICAL` cases pass through the index resolver.
  - Existing `_LEGACY_GENRE_MAP` cases pass.
  - Old `_normalize_genre_key()` aliases resolve to the same files.
  - Old `GENRE_INPUT_ALIASES` yield the same profile lookup labels.

Eliminate competing-source design risk before migrating callers.

### Phase 2: Migrate Runtime Callers

Scope:

- Remove hard-coded mappings from `reference_search.py`.
- Remove the local alias dictionary from `init_project.py`; load `GenreResolution.template_files`.
- Preserve `_route()` keyword/alias/fallback/exception ordering in `story_system_engine.py`, changing only internal canonical resolution to the shared wrapper.
- Move input aliases from `genre_aliases.py` into taxonomy; keep profile keys solely for section/key compatibility.
- Add lint/grep checks preventing new hard-coded input dictionaries like `PLATFORM_TO_CANONICAL`, `_LEGACY_GENRE_MAP`, or `GENRE_INPUT_ALIASES`.

Verify:

- `都市日常 -> 都市`
- `宫斗宅斗 -> 古言`
- `玄幻言情 -> 幻言`
- `规则怪谈 -> 悬疑`
- `网游 -> 游戏`
- `玄幻`: canonical `玄幻`, initialization template `修仙.md`.
- `克系`: canonical `悬疑` or the index-configured value, template `克苏鲁.md`.
- `知乎短篇风的规则怪谈`: canonical `悬疑`, with both `规则怪谈.md` and `知乎短篇.md`.

### Phase 3: Initialization Writes and Schema Consumers

Scope:

- Write `project_info.genre`, `project_info.genre_label`, and `project_info.genre_tags` in `init_project.py`.
- Update genre reads in init/plan/write/review SKILL.md:
  - Prefer `project_info.genre`.
  - Use `project_info.genre_label` for display/diagnostics.
  - Fall back to legacy `project.genre`.
- Prefer `project_info` in `memory_contract_adapter.py` and `context_manager.py` too.
- Update `templates/output/state-schema.md`.

Compatibility:

- Old projects containing only `project.genre` remain readable.
- New projects no longer write it.
- Resolve old noncanonical values through taxonomy rather than crashing.

Verify:

- New initialization state-schema tests.
- Shell-snippet tests or grep checks in the four Skills.
- Memory/context fallback tests.

### Phase 4: End-to-End Routes Against Real CSV Data

Scope:

- Add route coverage using `webnovel-writer/references/csv/题材与调性推理.csv`.
- For each row:
  - If `关键词`, `意图与同义词`, or `题材别名` is populated, use the first available alias as query; `_route()` must not raise and should normally use `keyword_or_alias_match`.
  - If aliases are empty, use `题材/流派` or `canonical_genre` as explicit-genre fallback; no exception.
- Assert:
  - No `StorySystemRoutingError` for valid rows.
  - `route.canonical_genre` belongs to the 15 values.
  - `route.genre_filter == route.canonical_genre`, unless canonical is empty or `全部`.
  - Unknown query + unknown genre still raises `StorySystemRoutingError`, preserving failure semantics.
- The CSV currently has 26 rows, but tests must derive coverage dynamically rather than hard-code 26 or 27.

Verification:

```powershell
$env:PYTHONUTF8='1'; python -m pytest webnovel-writer\scripts\data_modules\tests\test_story_system_engine.py -q --no-cov
$env:PYTHONUTF8='1'; python -m pytest webnovel-writer\scripts\data_modules\tests\test_story_system_cli.py -q --no-cov
```

### Phase 5: Finalize Skills and Documentation

Scope:

- `webnovel-init/SKILL.md`
  - Display 15 canonical primary genres.
  - Explain presets/tropes/formats through examples, outside the hard enum.
- Plan/write/review SKILL.md
  - Confirm every genre snippet prefers `project_info`.
- `references/csv/genre-canonical.md`
  - Distinguish canonical, route, trope, and format tags.
- `references/csv/README.md`
  - State that CSVs accept canonical values; taxonomy handles user input.
- `references/index/reference-loading-map.md`
  - Update template loading rules.
- `references/genre-profiles.md`
  - Clarify fallback triggers.

### Phase 6: Optional Directory Refactor

Only after the first five phases stabilize.

Target structure:

```text
templates/genres/
  index.csv
  canonical/
    都市.md
    玄幻.md
  presets/
    都市异能.md
    规则怪谈.md
    知乎短篇.md
```

This significantly affects paths and requires a separate commit.

## genre-profiles.md Fallback Rules

Use it only when:

1. An old project lacks Story Contracts and cannot obtain route/profile from `.story-system`.
2. `story_contracts.master.route.primary_genre` is empty but protagonist/state fallback has a genre.
3. The user explicitly enables legacy profile fallback.

Target priority:

1. Story Contracts route/profile.
2. Taxonomy-resolved `project_info.genre_label` or `project_info.genre`.
3. Legacy `project.genre`.
4. Configured fallback genre.

`genre_profile_excerpt` is supplemental context only; it must not override the Story System contract's routing decision.

## Suggested Commits

1. `docs(genres): address taxonomy plan review`
2. `chore(genres): add taxonomy index and normalize headings`
3. `feat(genres): add taxonomy resolver`
4. `refactor(genres): migrate genre resolution call sites`
5. `feat(init): persist canonical genre and genre tags`
6. `docs(genres): update skill and csv taxonomy guidance`
7. Optional: `refactor(genres): split canonical and preset templates`

## Risks and Controls

- Risk: The CSV index becomes another competing source of truth.
  Control: Phase 2 removes Python input mappings and adds regression-preventing grep/lint checks.

- Risk: Template and canonical namespaces become confused.
  Control: `GenreResolution` returns both `canonical_genre` and `template_files`; callers use only the fields they need.

- Risk: Historical behavior such as `玄幻 -> 修仙.md` is lost.
  Control: Model it explicitly in the index and add regression tests.

- Risk: Default canonical mappings for `系统流` or `知乎短篇` are debatable.
  Control: Record `label_type`; show inferred mappings during initialization and allow explicit canonical selection.

- Risk: Resolver changes break Story System routes.
  Control: Phase 4 tests every real route row and preserves unknown-input errors.

- Risk: Missed consumers keep reading `project.genre`.
  Control: Phase 3 checks the four Skills plus memory/context through grep and compatibility tests.

- Risk: `GENRE_PROFILE_KEY_ALIASES` becomes orphaned.
  Control: Retain it explicitly through Phases 1–5 while removing input aliases; document its fallback-only purpose.

## Completion Criteria

- All 37 templates map through the index, with bidirectional agreement.
- Labels/aliases cover old mappings and template stems; symmetric differences are empty or allowlisted.
- The historical plan's template-heading criterion is Chinese-only titles.
- `PLATFORM_TO_CANONICAL`, `_LEGACY_GENRE_MAP`, and `GENRE_INPUT_ALIASES` no longer exist as hard-coded input dictionaries.
- `_normalize_genre_key()` no longer maintains local aliases.
- `GENRE_PROFILE_KEY_ALIASES` has clear ownership and is not mixed with canonical/template resolution.
- `reference_search.py`, `init_project.py`, and `genre_aliases.py` share taxonomy as input-normalization truth.
- New projects write canonical `project_info.genre` and retain `genre_label`/`genre_tags`.
- Legacy `project.genre` remains readable but is not newly written.
- All Skill genre reads prefer `project_info.genre`.
- All real route rows pass end-to-end tests; unknown inputs still raise `StorySystemRoutingError`.
- `validate_csv.py`, prompt integrity, and full pytest pass.
