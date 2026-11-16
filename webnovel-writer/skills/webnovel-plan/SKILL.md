---
name: webnovel-plan
description: Generate volume outlines, timelines, and chapter outlines from the master outline, and incrementally write new settings back into the existing setting collection.
allowed-tools: Read Write Edit Bash AskUserQuestion
argument-hint: "[volume number, e.g. 1]"
---

# Outline Planning

Main agent responsibility: incrementally refine volume outlines/timelines/chapter outlines from the master outline, write new settings back to the setting collection, and refresh Story System writing contracts. Do not redesign the global story or rewrite the entire master outline or setting collection.

## Operating principles

1. Fill gaps incrementally; do not rewrite the entire master outline or setting collection.
2. Lock down volume pacing before breaking chapters down in batches.
3. The timeline is a hard constraint; every chapter outline must contain time fields.
4. If the master outline conflicts with settings, block first and await the user's decision.
5. Priority chain: explicit user requirements > master outline's core conflict and volume-ending climax > hard timeline constraints > skill default workflow > reference suggestions.

## Blocking conditions

- Invalid project root or missing master outline.
- Master outline lacks volume title / chapter range / core conflict / volume-ending climax → block and ask the user to fill them in.
- Setting conflict found in Step 2 / Step 8 → mark `BLOCKER` and await a user decision.
- Time jumps backward during batch chapter planning without being marked as a flashback → block the current batch.
- Step 9 validation fails → redo only the failed batch; do not overwrite the whole volume.

## Environment preparation

```bash
export WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
export SKILL_ROOT="${CLAUDE_PLUGIN_ROOT}/skills/webnovel-plan"
export SCRIPTS_DIR="${CLAUDE_PLUGIN_ROOT}/scripts"
export PROJECT_ROOT="$(python "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" where)"

python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" placeholder-scan --format text
```

Run `placeholder-scan` at both the start and end of planning. During plan, warn about placeholders and complete the relevant files. Before chapter writing, no `[待...]` / `暂名` / `{占位}` placeholders may remain for entities relevant to the current chapter.

## Reading strategy (trigger by stage; do not preload every reference)

Read each reference only when its corresponding step triggers it, preferably by section: use `Grep` with `^#{2,4} ` to locate heading-anchor line numbers, then use `Read` offset/limit for the target section.

| Trigger | Reading mode | File |
|------|---------|------|
| Step 4 | Full text | `${SKILL_ROOT}/../../templates/output/大纲-卷节拍表.md` |
| Step 5 | Full text | `${SKILL_ROOT}/../../templates/output/大纲-卷时间线.md` |
| Step 6 always | Section | `${SKILL_ROOT}/../../references/genre-profiles.md` (only the current genre's `### 2.x` section) |
| Step 6 always | Full text | `${SKILL_ROOT}/../../references/shared/strand-weave-pattern.md` |
| Chapter breakdown always | Section | `${SKILL_ROOT}/../../references/outlining/plot-signal-vs-spoiler.md` |
| Step 6 needs gratification beats | Section | `${SKILL_ROOT}/../../references/shared/cool-points-guide.md` |
| Step 6/7 needs conflict | Section | `${SKILL_ROOT}/references/outlining/conflict-design.md` |
| Step 6/7 specific pacing | Section | `${SKILL_ROOT}/references/outlining/genre-volume-pacing.md` |
| Step 7 reader-retention analysis | Section | `${SKILL_ROOT}/../../references/reading-power-taxonomy.md` |
| Step 7 chapter refinement + node specification | Section | `${SKILL_ROOT}/references/outlining/chapter-planning.md` |

Search CSV creative references; do not `cat` entire tables:

```bash
python -X utf8 "${SCRIPTS_DIR}/reference_search.py" --skill plan --table 爽点与节奏 --query "{卷级核心冲突}" --genre "${GENRE}"
python -X utf8 "${SCRIPTS_DIR}/reference_search.py" --skill plan --table 桥段套路 --query "{卷级核心冲突}" --genre "${GENRE}"
python -X utf8 "${SCRIPTS_DIR}/reference_search.py" --skill plan --table 命名规则 --query "角色命名" --genre "${GENRE}"
```

## Procedure

### Step 1: Load project data and verify prerequisites

```bash
# Project configuration/projection state (compatibility read, not the post-writing source of truth)
cat "$PROJECT_ROOT/.webnovel/state.json"

# Master outline (global blueprint); verify volume title/chapter range/core conflict/volume-ending climax; block if insufficient
cat "$PROJECT_ROOT/大纲/总纲.md"

# Genre (from the init configuration snapshot; later CSV searches and decision matching depend on it); .story-system/ remains the post-writing main-pipeline source of truth
GENRE="$(python -X utf8 -c "import json; s=json.load(open('${PROJECT_ROOT}/.webnovel/state.json',encoding='utf-8')); pi=s.get('project_info',{}); print(pi.get('genre') or s.get('project',{}).get('genre',''))")"
```

Read settings on demand: `设定集/世界观.md`, `设定集/力量体系.md`, `设定集/主角卡.md`, `设定集/反派设计.md`, `.webnovel/idea_bank.json`.

**Cross-volume state reading** (mandatory when completed volumes already exist, i.e. `.webnovel/summaries/` contains files):

```bash
# Summaries of the last five chapters
for ch in $(seq $((START_CH - 5)) $((START_CH - 1))); do
  cat "$PROJECT_ROOT/.webnovel/summaries/ch$(printf '%04d' $ch).md" 2>/dev/null
done

# Current core-character state / core relationships / active foreshadowing (unresolved across volumes)
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" knowledge query-entity-state --entity "{protagonist_id}" --at-chapter {上一卷最后章}
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" knowledge query-relationships --entity "{protagonist_id}" --at-chapter {上一卷最后章}
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" memory-contract get-open-loops
```

### Step 2: Complete the setting baseline

Move the setting collection from a skeleton to a state ready for planning and writing. Fill gaps incrementally; do not clear or rewrite entire files. List conflicts and block if any are found.

- `设定集/世界观.md`: world boundaries, social structure, purposes of key locations.
- `设定集/力量体系.md`: realm chain, restrictions, costs, and cooldowns.
- `设定集/主角卡.md`: desire, flaw, starting resources, and limitations.
- `设定集/反派设计.md`: minor/intermediate/major antagonist tiers and mirror relationships.

### Step 3: Select the target volume and confirm scope

Confirm volume title, chapter range, core conflict, and any special requirements (viewpoint, emotional arcs, genre shifts).

### Step 4: Generate the volume beat sheet

Load `${SKILL_ROOT}/../../templates/output/大纲-卷节拍表.md`.

Hard requirements: fill in the midpoint reversal; if genuinely absent, write “None (reason: ...)”. Include at least three escalating crises. The new volume-ending hook must resolve into an unanswered question at the end of the final chapter.

Output file: `大纲/第{volume_id}卷-节拍表.md`

### Step 5: Generate the volume timeline

Load `${SKILL_ROOT}/../../templates/output/大纲-卷时间线.md`.

Hard requirements: specify the time system and this volume's duration; list countdown events, if any, and mark them D-N.

Output file: `大纲/第{volume_id}卷-时间线.md`

### Step 6: Generate the volume-outline skeleton

Required reading: `${SKILL_ROOT}/../../references/genre-profiles.md` and `${SKILL_ROOT}/../../references/shared/strand-weave-pattern.md`; read gratification / conflict / pacing references on demand (see reading-strategy table).

The volume outline must specify: volume summary, key characters and antagonist tiers, Strand distribution, gratification-beat density plan, foreshadowing plan, and constraint-trigger plan.

Cross-volume consistency checks (mandatory after the first volume):

- Unresolved foreshadowing from the previous volume must appear in the new volume's foreshadowing plan (continued development or marked for payoff).
- Character relationship changes must carry forward; do not act as if the previous volume never happened.
- Protagonist abilities / cultivation realm must carry forward without regression or skipped levels (unless explained by the plot).

### Step 7: Generate chapter outlines in batches

Batch rules: default `10 chapters/batch`; reduce to `8 chapters/batch` for complex genres or multiple simultaneous storylines; expand to `12 chapters/batch` for simple progression fiction. More than `12 chapters` per batch is not recommended.

Read `${SKILL_ROOT}/../../references/reading-power-taxonomy.md` and `${SKILL_ROOT}/references/outlining/chapter-planning.md` on demand.

Each chapter must include: goal, resistance, cost, time anchor, elapsed time within the chapter, time gap from the previous chapter, countdown status, gratification beat, Strand, antagonist tier, viewpoint/protagonist, key entities, chapter changes, unresolved chapter-ending question, hook, and structured nodes `CBN`, `CPNs`, `CEN`, `必须覆盖节点` (must-cover nodes), and `本章禁区` (chapter prohibitions).

#### Structured nodes

Use the unified node format `subject | action/change | object/result` (a writing-execution skeleton, not strict grammatical SVO). Full format explanations, field details, and examples are in the structured-node specification section of `${SKILL_ROOT}/references/outlining/chapter-planning.md`. Read that section on demand; do not inline it here.

Core constraints:

- Exactly one `CBN`, `2–4 CPNs`, and one `CEN` per chapter; arrange `CPNs` chronologically.
- Adjacent chapters' `CEN -> next chapter CBN` must connect logically (except the first and final chapters).
- At most four `必须覆盖节点`; recommended: `CBN + CEN + 1–2 core CPNs`. Optional nodes are suggestions only, not primary grounds for failure.
- At most five `本章禁区` entries; include only hard prohibitions on what absolutely must not happen in this chapter, not style suggestions.
- Backward compatibility: if old project outlines lack these fields, downstream workflows run normally and skip only structured checks.

Output file: `大纲/第{volume_id}卷-详细大纲.md`

### Step 8: Write new settings back into the existing collection

Inputs: volume beat sheet, volume timeline, detailed volume outline, and existing setting files.

Writeback rules: add incrementally to relevant sections only; put new characters into character sheets or groups; new factions / locations / rules into worldbuilding or power systems; new antagonist tiers into antagonist design.

Hard rule: if a conflict with the master outline or existing settings is found, mark `BLOCKER` and stop subsequent updates.

### Step 9: Validate, save, and update state

Required checks: beat sheet / timeline / detailed outline all exist and are nonempty; every chapter has complete time fields; timeline is monotonically increasing; countdowns advance correctly; new settings have been written back; `BLOCKER=0`; where nodes exist, adjacent `CEN -> CBN` have no obvious logical conflicts and each chapter has at most four `必须覆盖节点`.

After all checks pass, generate an explicit structured writeback file `大纲/第{volume_id}卷-总纲写回.json` (write only foreshadowing / open loops explicitly listed in the plan; never infer them from free-form volume-outline text):

```json
{
  "next_volume_anchor": {
    "volume": 2,
    "volume_name": "Next volume title",
    "core_conflict": "Next volume's core conflict",
    "volume_end_climax": "Next volume's ending climax"
  },
  "foreshadow_writeback": [
    {"content": "New foreshadowing explicitly added by this volume's plan", "buried_chapter": "第10章", "payoff_chapter": "", "level": "卷级"}
  ],
  "open_loop_writeback": [
    {"content": "A question that remains open after this volume ends", "buried_chapter": "", "payoff_chapter": "", "level": "持续开放环"}
  ]
}
```

Perform minimal master-outline writeback (update only volume V+1's title / core conflict / ending climax and the foreshadowing table in `大纲/总纲.md`; do not generate the next volume's detailed outline / beat sheet / timeline / chapter outlines):

```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "$PROJECT_ROOT" master-outline-sync \
  --volume {volume_id} \
  --writeback-file "大纲/第{volume_id}卷-总纲写回.json" \
  --format text
```

Update state:

```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "$PROJECT_ROOT" update-state -- \
  --volume-planned {volume_id} \
  --chapters-range "{start}-{end}"
```

### Step 10: Refresh Story System writing contracts (mandatory once planning reaches specific chapters)

Read genre from the `state.json` initialization configuration snapshot; the pre-writing main-pipeline source of truth is the `.story-system/` contract tree. First parse the actual `CHAPTER_GOAL` from the detailed outline; never pass placeholders such as `{章纲目标}` / `第N章章纲目标`.

```bash
GENRE="$(python -X utf8 -c "import json; s=json.load(open('${PROJECT_ROOT}/.webnovel/state.json',encoding='utf-8')); pi=s.get('project_info',{}); print(pi.get('genre') or s.get('project',{}).get('genre',''))")"

python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" story-system "${CHAPTER_GOAL}" \
  --genre "${GENRE}" --chapter {chapter_num} --persist --emit-runtime-contracts --format both
```

After generation, treat `.story-system/MASTER_SETTING.json`, `.story-system/volumes/`, `.story-system/chapters/`, and `.story-system/reviews/` as main-pipeline inputs for subsequent writing. Before writing, no `[待...]` / `暂名` / `{占位}` placeholders may remain for entities relevant to the current chapter.

## Hard-failure conditions

- Beat sheet / timeline / detailed outline is missing or empty.
- Midpoint reversal missing without a reason.
- Any chapter lacks time fields; time moves backward without a flashback marker; countdown arithmetic conflicts.
- Obvious conflict with the master outline's core conflict or volume-ending climax.
- Unresolved `BLOCKER` remains.

## Recovery rules

1. Redo only failed batches; do not overwrite whole-volume files.
2. If the final batch is invalid, delete and rewrite only that batch.
3. Update state only after all validations pass.

## Author-friendly progress and recovery contract

Before planning begins, explain the stages: check master outline and settings -> generate beat sheet -> generate timeline -> break down chapter outlines -> write back new settings -> refresh writing contracts. Use author-friendly language in progress updates, not raw JSON, tracebacks, or long command logs. Write technical details to `.webnovel/logs/run_last.log`:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" run-log \
  --event plan-progress \
  --payload-json "{\"stage\": \"plan\", \"volume\": {volume_id}}" \
  --format text
```

Limit each progress update to two lines describing only the current action and impact, e.g. “Breaking this volume into chapter outlines: each chapter's goal, time anchor, and prohibitions will be specified.” Minimize interruptions: continue by default; ask only for master-outline / setting conflicts, backward timeline jumps, volume-ending hook tradeoffs, or overwriting existing plans.

When a user decision is needed, offer finite choices and explain consequences, e.g. follow the master outline / modify settings / pause planning. When stuck, explain the blocker, completed work, and recovery advice, e.g. “The beat sheet and timeline are retained, but chapters 21–30 failed to break down; rerunning `/webnovel-plan {volume_id}` will redo only the failed batch.”

Mention `.webnovel/logs/run_last.log` in the final report only for unrecoverable failures; otherwise retain logs without bothering the author. Always call the author-report helper when finishing:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" user-report \
  --stage plan \
  --volume {volume_id} \
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
- `大纲/第{volume_id}卷-节拍表.md`.
- `大纲/第{volume_id}卷-时间线.md`.
- `大纲/第{volume_id}卷-详细大纲.md`.
- Which setting files received new settings.
- `大纲/第{volume_id}卷-总纲写回.json`.
- Whether `master-outline-sync`, `update-state`, and Story System contract refresh completed.
- Whether placeholder, timeline, and node-continuity checks passed.

Issue categories:
- Automatically handled: redoing only failed batches, filling non-blocking placeholders, rerunning contract refresh.
- Suggested for confirmation: new character names, faction names, or volume-ending hooks worth the author's review.
- Must address: master-outline / setting conflicts, backward timeline jumps, unresolved `BLOCKER`, remaining placeholders relevant to the current chapter.

Next-step suggestions must use task-oriented language plus copyable commands, for example:

```text
- Next, write the first chapter:
  /webnovel-write 1
```

Do not report token statistics; for troubleshooting, provide only the log path or suggest `/webnovel-doctor`.
