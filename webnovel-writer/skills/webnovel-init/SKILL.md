---
name: webnovel-init
description: Deep initialization of a webnovel project. Collect complete creative information through staged interaction, producing a project skeleton and constraint files ready for planning and writing.
allowed-tools: Read Write Edit Grep Bash Agent AskUserQuestion WebSearch WebFetch
argument-hint: "[book title or inspiration (optional)]"
---

# Project Initialization (Deep Mode)

## Project paths and output language

Use English for generated story content, headings, summaries, reports, and user-facing explanations unless the user explicitly requests another language. Preserve runtime schema keys, enum values, and machine-readable identifiers exactly.

New projects use English-only paths, filenames, schema keys, and enum identifiers. Use `chapters/`, `outlines/`, `settings/`, and `reviews/`. Resolve paths with `python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}"`; resolve individual files with `--path outlines/master-outline.md` or the corresponding English relative path. Pass resolved paths to subagents. This branch targets newly created projects and does not migrate or support old project layouts or schemas. Do not rename, overwrite, or merge existing book content automatically. Story prose and names may contain Unicode characters; that does not change the English project schema.

## Goals

- Collect sufficient information through structured interaction to avoid “generate first, redo later.”
- Produce a usable skeleton: `.webnovel/state.json`, `settings/*`, `outlines/master-outline.md`, `.webnovel/idea_bank.json`, and `.story-system/MASTER_SETTING.json`.
- Ensure subsequent `/webnovel-plan` and `/webnovel-write` can run directly.

## Operating principles

1. Collect first, then generate; do not run `webnovel.py init` before passing the sufficiency gate.
2. Ask in waves, requesting only information that is currently missing and blocks the next step. Do not repeat questions the user has answered; let the user resolve conflicts.
3. Reference-book deconstruction returns structured results only. Before user confirmation, do not write to `idea_bank.json`, `.story-system`, `settings`, `outlines`, `chapters`, `.webnovel/state.json`, or any canon/read-model file.

## Reference loading strategy

Paths: `references/` means `skills/webnovel-init/references/`; `../../references/` means shared references. Detailed collection fields are in `references/init-collection-schema.md` (read relevant sections on demand and collect item by item; required fields are governed by the “Sufficiency gate”).

| Step | Trigger | Reference |
|------|---------|-----------|
| Step 1 | always | `references/system-data-flow.md`, `references/genre-tropes.md` |
| Genre/selling-point collection | always | `../../references/genre-profiles.md` (read only the current genre section) |
| Character development stalled | Flat characters | `references/worldbuilding/character-design.md` |
| Worldbuilding/power | On demand | `references/worldbuilding/faction-systems.md`, `references/worldbuilding/power-systems.md`, `references/worldbuilding/world-rules.md`, `references/worldbuilding/setting-consistency.md` |
| Creative constraints | Step 6 | `references/creativity/creativity-constraints.md` (during collection read `## I. Idea Package Schema`, `## VI. Hard Constraints`, and `## VIII. Scoring System`; for score presentation read `### 8.1 Five Dimensions`), `references/creativity/selling-points.md` (`## 9. Design Templates` skeleton; supplement with `### 1.3 Core Formulas` and `## 7. Practical Checklists`, as needed); for hybrid genres read `creative-combination.md`; when stuck read `inspiration-collection.md`; load matching `anti-trope-*.md` for the genre |
| Naming | Start naming | `python -X utf8 "${SCRIPTS_DIR}/reference_search.py" --skill init --table naming --query "{naming_target} {genre}" --genre {genre}` |

Read these long-form guides (creative constraints, anti-trope libraries, worldbuilding guides, selling-point templates) on demand; do not inline their entries.

## Tool strategy

- `Read/Grep`: read project context and reference files.
- `Bash`: run `webnovel.py init`, file-existence checks, and minimal validation.
- `Agent`: divide parallel subtasks; call `webnovel-writer:deconstruction-agent` in Step 1.5 when the user chooses reference-book deconstruction as an inspiration source.
- `AskUserQuestion`: resolve consequential differences, select candidates, and obtain final confirmation.
- `WebSearch`/`WebFetch`: use only when the user requests market/platform trends, creative constraints need time-sensitive evidence, or genre information is clearly uncertain. Search first, then fetch to verify.

## Interaction procedure (Deep)

### Step 1: Preflight and context loading

Environment setup (before bash commands):
```bash
export WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"

if [ -z "${CLAUDE_PLUGIN_ROOT}" ] || [ ! -d "${CLAUDE_PLUGIN_ROOT}/scripts" ]; then
  echo "ERROR: CLAUDE_PLUGIN_ROOT is unset or directory is missing: ${CLAUDE_PLUGIN_ROOT}/scripts" >&2
  exit 1
fi
export SCRIPTS_DIR="${CLAUDE_PLUGIN_ROOT}/scripts"
```

Required:
- Verify the current directory is writable and the entry script `${SCRIPTS_DIR}/webnovel.py` exists (plugin directory only).
- Before initialization, do not use `where` to resolve `WORKSPACE_ROOT` to a book project root. When the new project does not yet exist, `where` may match an old pointer or project.
- Print only workspace and script directories; confirm the generation target will be a sanitized book-title subdirectory under the workspace.
- Load minimal references: `references/system-data-flow.md`, `references/genre-tropes.md`; read `templates/genres/` only on demand after choosing a genre.

Output: a “known information” list and “information to collect” list before entering Deep collection.

### Step 1.5: Ask about inspiration sources (optional)

Before collecting the story core, use `AskUserQuestion` or a direct question to establish whether the user has an inspiration source. Do not deconstruct books by default or require reference works.

Suggested question:

```text
Where would you like to start with this book's inspiration? You can describe an original idea or provide a reference work to deconstruct for inspiration. For deconstruction, give the book title and platform, and ideally chapter excerpts or a text-file path. You can skip this if you have no reference.
```

Acceptable sources: original ideas, reference-work deconstruction (title/platform/chapter excerpts/text path), market trends, genre templates/anti-trope libraries/existing idea fragments.

When the user chooses reference-work deconstruction and provides a text path or chapter excerpts, you must call `webnovel-writer:deconstruction-agent` through `Agent`. The init main workflow must not substitute a verbal analysis for its results.

```text
Use the Agent tool to run `webnovel-writer:deconstruction-agent`.

Prompt: reference_title={reference_title}; reference_source={reference_source}; reference_text_path={reference_text_path}; reference_text_excerpt={reference_text_excerpt}; analysis_mode={quick|deep|auto}; init_goal={current initialization direction or empty}; target_genre={genre or empty}. Return only an init_reference_research JSON object. Do not write files, create directories, or write .story-system, .webnovel, settings, outlines, chapters, idea_bank.json, state.json, or any canon/read-model files.
```

After the call, the main workflow must record a `SubagentRun` summary (for the final report only; do not write it into canon):

```json
{
  "name": "deconstruction-agent",
  "user_label": "Reference-work deconstruction",
  "status": "completed | partial | failed | skipped",
  "problems": [],
  "auto_handled": [],
  "needs_user_action": false,
  "duration_ms": 0,
  "outputs": []
}
```

If `quality.passed=false`, `confidence < 0.85`, input is insufficient, text is unreadable, processing degrades to quick mode, or output is incomplete, record it in `problems` and include it under “Suggested for confirmation / Must address” in the final report.

Handling rules:
- If only a title/platform is available, without text or excerpts, first ask whether the user can provide excerpts/a path. If not, treat the reference solely as a “directional clue”; do not invent its opening three chapters, characters, settings, or plot facts.
- After receiving `init_reference_research` JSON, use only `reader_promise`, `opening_hook_patterns`, `cool_point_loops`, `protagonist_patterns`, `antagonist_pressure_patterns`, `pacing_notes`, `borrowable_structures`, `differentiation_requirements`, `init_candidates`, and `quality`.
- Check `quality` first: if `quality.passed=false`, `confidence < 0.85`, or `warnings` is nonempty, do not fold candidates into the creative constraint package; present only risks and needed supplementary material for user confirmation.
- Include `do_not_copy` and `canon_contamination_warnings` in the known-information list as red lines for subsequent idea generation.
- Steps 2–6 may use only patterns the user has confirmed and that have been transformed into differentiated expressions for this book. Never copy reference-book characters, settings, organizations, locations, special abilities, or plot facts verbatim into generated project files.

### Step 2: Story core and commercial positioning

Required: title, genre (A+B hybrids supported), target scale (total word count or chapters), one-sentence story, core conflict, target readers/platform.

Canonical genre set (written to `project_info.genre`): urban, xuanhuan, xianxia, fantasy, sci-fi, historical, mystery, game-lit, historical-romance, contemporary-romance, fantasy-romance, period-fiction, farming, quick-transmigration, fanfiction. These are runtime identifiers for urban, xuanhuan, xianxia, fantasy, science fiction, historical, mystery, gaming, historical romance, contemporary romance, fantasy romance, period fiction, farming, quick transmigration, and derivative fiction.

Users may freely enter subgenre presets / tropes / formats; the initialization script maps them to canonical genres and loads templates according to the taxonomy (examples: cultivation, system-fiction, rules-horror, palace-household-intrigue, esports, apocalypse: cultivation, system fiction, rules horror, palace/household intrigue, esports, apocalypse). Prefer free-form user descriptions followed by structured confirmation; offer 2–4 candidate directions when they are stuck.

### Step 3: Character skeleton and relationship conflicts

Required: protagonist name, desire, flaw (one that imposes a cost), protagonist structure (single/multiple), romance configuration (none/single heroine/multiple heroines), antagonist tiers (minor/intermediate/major), and a one-sentence mirror conflict. Optional: protagonist archetype tags, division of roles among multiple protagonists.

### Step 4: Special ability and payoff mechanism

Required: special-ability type (may be “no special ability”), name/system name (empty if absent), style, visibility, irreversible cost (a cost is mandatory, or explicitly “none + reason”), and growth pacing.
Conditionally required: system fiction needs system personality + upgrade pacing; rebirth needs rebirth time point + memory completeness; inheritance/artifact spirits need assistance boundaries + intervention limits.

### Step 5: Worldbuilding and power rules

Required: world scale (single city/multiple regions/continent/multiple worlds), power-system type, faction landscape, social classes, and resource distribution.
Genre-dependent: currency and exchange rules, sect/organization hierarchy, realm chain and sub-realms.

### Step 6: Creative constraint package (differentiation core)

Procedure:
1. Summarize confirmed inspiration sources from Step 1.5: original ideas, reference deconstruction results, market trends, genre templates, or anti-trope libraries.
2. Load anti-trope libraries according to genre mapping (at most two primary relevant libraries).
3. Generate 2–3 idea packages, each with: a one-sentence selling point, one anti-trope rule, 2–3 hard constraints, one sentence explaining how the protagonist's flaw drives the story, one antagonist-mirror sentence, and an opening hook.
4. Filter with three questions: Why must this genre be written this way? Would it collapse with a conventional protagonist? Can the selling point be expressed in one sentence without duplicating a template?
5. Present five-dimension scores (see section 8.1 of `references/creativity/creativity-constraints.md`) to help the decision.
6. The user selects the final plan, or rejects it and gives reasons.

Notes:
- If the user requests alignment with the current market, external research may be triggered and timestamped.
- If reference deconstruction was used, candidate presentations must identify the reference source, transformation method, non-copyable elements, and differentiation requirements. Do not write to `idea_bank.json` or any generated project file before explicit user confirmation.

### Step 7: Consistency recap and final confirmation

Output a “draft initialization summary” and request confirmation: story core (genre/one-sentence story/core conflict), protagonist core (desire/flaw), special-ability core (ability and cost), world core (scale/power/factions), and creative-constraint core (anti-trope + hard constraints).

Confirmation rules: do not generate without explicit user confirmation; if the user changes only one part, return to the corresponding step for minimal recollection.

## Sufficiency gate (must pass)

Do not run `webnovel.py init` until all of the following are satisfied:

1. Title and genre (possibly hybrid) are settled.
2. Target scale is calculable (at least word count or chapter count).
3. Protagonist name + desire + flaw are complete.
4. World scale + power-system type are complete.
5. Special-ability type is settled (no special ability is allowed).
6. Creative constraints are settled: one anti-trope rule + at least two hard constraints, or the user explicitly refuses and the reason is recorded.

## Project directory safety rules (mandatory)

- `project_root` must be generated from a sanitized title: `PROJECT_ROOT="${WORKSPACE_ROOT}/${PROJECT_SLUG}"`; automatically prefix `proj-` if sanitization yields an empty string or one starting with `.`.
- Do not generate project files under the plugin directory (`${CLAUDE_PLUGIN_ROOT}`). Do not use `WORKSPACE_ROOT` directly as `PROJECT_ROOT` unless the user explicitly identifies the current directory as the book project root.
- Display and confirm `WORKSPACE_ROOT`, `PROJECT_SLUG`, and `PROJECT_ROOT` before initialization.

```bash
PROJECT_SLUG="$(python -X utf8 -c "import re,sys; title=sys.argv[1].strip(); slug=re.sub(r'[\\\\/:*?\"<>|]+','',title); slug=re.sub(r'\\s+','-',slug).strip('-'); print(('proj-' + slug) if (not slug or slug.startswith('.')) else slug)" "{title}")"
PROJECT_ROOT="${WORKSPACE_ROOT}/${PROJECT_SLUG}"
export SETTINGS_DIR="$(python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}" --directory settings)"
export OUTLINES_DIR="$(python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}" --directory outlines)"
echo "WORKSPACE_ROOT=${WORKSPACE_ROOT}"
echo "PROJECT_SLUG=${PROJECT_SLUG}"
echo "PROJECT_ROOT=${PROJECT_ROOT}"
```

## Generate the project

### 1) Run the initialization script

All arguments come from the collected data above (title/genre/protagonist/special ability/worldbuilding/antagonists/creative constraints, etc.). Map fields individually to `webnovel.py init` `--*` options. The complete field list is in `references/init-collection-schema.md`; use `python "${SCRIPTS_DIR}/webnovel.py" init --help` to check option names.

```bash
python "${SCRIPTS_DIR}/webnovel.py" init \
  "${PROJECT_ROOT}" "{title}" "{genre}" \
  --protagonist-name "{protagonist_name}" \
  --target-words {target_words} --target-chapters {target_chapters} \
  --protagonist-desire "{protagonist_desire}" --protagonist-flaw "{protagonist_flaw}" \
  --golden-finger-type "{gf_type}" --gf-irreversible-cost "{gf_irreversible_cost}" \
  --world-scale "{world_scale}" --power-system-type "{power_system_type}" \
  --core-selling-points "{core_points}"
  # Append the corresponding --* options for remaining collected fields (structure/romance/antagonists/factions/currency/realms/archetypes/readers/platform, etc.)
```

### 2) Write `idea_bank.json`

Write `.webnovel/idea_bank.json`; its content must match the final selected plan:

```json
{
  "selected_idea": {"title": "", "one_liner": "", "anti_trope": "", "hard_constraints": []},
  "constraints_inherited": {"anti_trope": "", "hard_constraints": [], "protagonist_flaw": "", "antagonist_mirror": "", "opening_hook": ""}
}
```

### 3) Patch the master outline

Complete `outlines/master-outline.md` with: one-sentence story, core main plot/hidden plot, creative constraints (anti-trope, hard constraints, protagonist flaw, antagonist mirror), antagonist tiers, and key gratification milestones (2–3).

### 4) Generate the pre-writing contract tree (Story System initialization)

Generate MASTER_SETTING immediately after init so later planning has tone/prohibition references. Do not pass `--chapter` here (generate only `MASTER_SETTING.json` and `anti_patterns.json`), or `--emit-runtime-contracts` (no volume/chapter data yet). Generate volume/chapter/review contracts when plan reaches specific chapters.

```bash
GENRE="$(python -X utf8 -c "import json,os; root=os.environ['PROJECT_ROOT']; s=json.load(open(root + '/.webnovel/state.json',encoding='utf-8')); pi=s.get('project_info',{}); print(pi.get('genre') or s.get('project',{}).get('genre',''))")"

python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  story-system "${GENRE}" --genre "${GENRE}" --persist --format json
```

## Validation and delivery

```bash
test -f "${PROJECT_ROOT}/.webnovel/state.json"
find "${SETTINGS_DIR}" -maxdepth 1 -type f -name "*.md"
test -f "$(python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}" --path outlines/master-outline.md)"
test -f "${PROJECT_ROOT}/.webnovel/idea_bank.json"
test -f "${PROJECT_ROOT}/.story-system/MASTER_SETTING.json"
test "$(basename "${PROJECT_ROOT}")" = "${PROJECT_SLUG}"
```

Success criteria:
- `state.json` exists and title/genre/target_words/target_chapters are nonempty.
- Core setting files exist: `worldbuilding.md`, `power-system.md`, `protagonist.md`; do not generate `protagonist-team.md` for a single protagonist or `heroine.md` when `heroine_config=none`.
- By default, do not generate `special-power-design.md`, `hybrid-genre.md`, `payoff-plan.md`, or empty directories; their sources of truth are the protagonist sheet, worldbuilding, and volume outline.
- `master-outline.md` has its core plot and constraint fields filled; `idea_bank.json` is written and matches the final selected plan.
- `.story-system/MASTER_SETTING.json` exists and `route.primary_genre` is nonempty.

## Failure handling (minimal rollback)

Triggers: missing key files; missing key master-outline fields; constraints enabled but `idea_bank.json` missing or inconsistent.

Recovery: collect only missing fields rather than asking everything again; rerun only the smallest required step (missing files → rerun `webnovel.py init`; missing outline fields → patch only the master outline; inconsistent idea_bank → rewrite only that file). Revalidate and finish after all checks pass.

## Author-friendly progress and recovery contract

Before initialization begins, explain the stages: collect the story core -> confirm creative constraints -> generate the project skeleton -> write initial story records -> verify readiness for planning. Use author-friendly language in progress updates; do not output raw JSON, tracebacks, or long command logs. Write technical details to `.webnovel/logs/run_last.log`:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" run-log \
  --event init-progress \
  --payload-json "{\"stage\": \"init\"}" \
  --format text
```

Limit progress updates to two lines each and describe only the current action and impact, e.g. “Generating the project skeleton: this creates the setting collection, master outline, and initial story records.” Minimize interruptions: continue collection and generation by default; only core settings, adoption of reference deconstruction, project-directory safety, and the final plan before canon writes need the user's decision.

When a user decision is needed, offer finite choices and explain each consequence, e.g. keep current settings / modify one part / pause initialization. When stuck, explain the blocker, completed work, and recovery advice, e.g. “The setting collection is generated, but initial Story System records are missing; rerunning `/webnovel-init` will fill only the missing files.”

Mention `.webnovel/logs/run_last.log` in the final report only for unrecoverable failures; otherwise retain logs without bothering the author. Always call the author-report helper when finishing:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" user-report \
  --stage init \
  --format text
```

## Author-friendly final report contract

The final reply must address the author, without raw JSON, tracebacks, or long command logs. Use the fixed three-part format, beginning with one overall-status sentence:

```text
Overall status: Completed / Partially completed / Needs your attention / Not completed.

1. Files produced and completion status
- ...

2. Issues and unusually long steps encountered
- Automatically handled: ...
- Suggested for confirmation: ...
- Must address: ...

3. Recommended next steps
- ...
```

Must report:
- Project directory, `.webnovel/state.json`, and `.webnovel/idea_bank.json`.
- `settings/worldbuilding.md`, `settings/power-system.md`, `settings/protagonist.md`, and `settings/antagonist.md`.
- `outlines/master-outline.md` and `.story-system/MASTER_SETTING.json`.
- Whether reference-work deconstruction was used, and that canon was not written before user confirmation.
- Whether missing information affects subsequent `/webnovel-plan`.

Issue categories:
- Automatically handled: script-created missing directories, rerunning minimal initialization steps, regenerating missing non-content files, etc.
- Suggested for confirmation: slightly low-quality reference analysis, candidate ideas worth another user look.
- Must address: unconfirmed core settings, unsafe project directory, still-missing key files.

Next-step suggestions must use task-oriented language plus copyable commands, for example:

```text
- Next, plan the first volume:
  /webnovel-plan 1
```

Do not report token statistics; for troubleshooting, provide only the log path or suggest `/webnovel-doctor`.
