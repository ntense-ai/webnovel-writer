# Init→Plan→Write Pipeline Integrity Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix seven user-facing breaks across init→plan→write→plan→write, ensuring genre flows from init to the reasoning layer, story-system runs at the right time, and cross-volume planning incorporates existing writing.

**Architecture:** Implement fixes from the data layer (complete CSV aliases) to workflows (standardize SKILL.md), centered on the decision that genre written by init into state.json is the sole source of truth.

**Tech Stack:** CSV (UTF-8 BOM), Python CLI, Markdown prompt files

**Confirmed decisions:**
1. Init writes genre to state.json; every later stage reads it there. Free-text queries must no longer determine routing
2. CSV retrieval results are creative references; master/chapter outlines take highest priority after user instructions
3. chapter_brief.json contains only reasoning/routing metadata and must not masquerade as a chapter-content contract
4. A rejected chapter does not block the next chapter; the user decides
5. Volume planning uses the outline + user input + existing plot state + CSV retrieval

---

## Task 1: Complete Init Genre Aliases in the Reasoning Table

**Problem:** Init genre labels (修仙, 系统流, 高武, 西幻, etc.) do not match reasoning-table labels (东方仙侠, 西方奇幻, etc.), so reasoning does not take effect for some genres.

**Files:**
- Modify: `webnovel-writer/references/csv/裁决规则.csv`
- Modify: `webnovel-writer/references/csv/题材与调性推理.csv`

- [ ] **Step 1: Map Init Genres to Reasoning Genres**

Genre set listed at lines 110–113 of init SKILL.md (exact runtime labels retained):

```
Fantasy/cultivation: 修仙 | 系统流 | 高武 | 西幻 | 无限流 | 末世 | 科幻
Urban/modern: 都市异能 | 都市日常 | 都市脑洞 | 现实题材 | 黑暗题材 | 电竞 | 直播文
Romance: 古言 | 宫斗宅斗 | 青春甜宠 | 豪门总裁 | ...
Special genres: 规则怪谈 | 悬疑脑洞 | 悬疑灵异 | 历史古代 | 历史脑洞 | ...
```

Map to the seven existing reasoning genres:

| Init genre label | → Reasoning genre |
|------------|-----------|
| 修仙、仙侠 | 东方仙侠 |
| 西幻、西方奇幻 | 西方奇幻 |
| 末世、科幻 | 科幻末世 |
| 都市异能、都市脑洞、现实题材 | 都市日常 |
| 都市修真、现代修真 | 都市修真 |
| 高武、都市异能 (high-martial-arts variant) | 都市高武 |
| 历史古代、历史脑洞 | 历史古代 |
| 系统流、无限流 | 东方仙侠 (fallback; mostly cultivation variants) |

Unmapped genres (romance, rule-based horror, mystery, etc.) currently have no reasoning rows and use an empty-reasoning fallback.

- [ ] **Step 2: Complete Aliases in the Keywords Column of 裁决规则.csv**

Append init genre labels to each row’s `关键词` (keywords) column:

| Reasoning genre | Current keywords | Append |
|---------|-----------|------|
| 西方奇幻 | `西方奇幻\|奇幻` | `\|西幻` |
| 东方仙侠 | `东方仙侠\|仙侠` | `\|修仙\|系统流\|无限流` |
| 科幻末世 | `科幻末世\|末世\|科幻` | (already covered) |
| 都市日常 | `都市日常\|都市` | `\|都市脑洞\|现实题材\|黑暗题材` |
| 都市修真 | `都市修真\|修真\|现代修真` | (already covered) |
| 都市高武 | `都市高武\|高武\|都市异能` | (already covered) |
| 历史古代 | `历史古代\|历史\|古代` | `\|历史脑洞` |

Edit the CSV and append to the `关键词` column in the corresponding rows.

- [ ] **Step 3: Check Routing-Table Alias Coverage**

The eight current rows in `题材与调性推理.csv` represent subgenres such as broken-engagement stories and rule-based horror, not broad genre categories. **Do not change existing rows.**

The routing table lacks broad-category rows such as 东方仙侠, 西方奇幻, and 科幻末世. When the user’s genre is 修仙, `_route()` may match no row because existing rows describe specific subgenres.

Determine whether broad-category rows are needed by checking `_route()` fallback behavior. With no match, it uses `--genre` as `explicit_genre_fallback` and consults the default recommendation table. This fallback is sufficient.

Conclusion: **leave the routing table unchanged**. Add aliases only to the reasoning table. Unmatched routes fall back to default recommendations while `_load_reasoning(genre)` can still match reasoning rows.

- [ ] **Step 4: Run Tests to Confirm**

```bash
cd "D:\wk\novel skill\webnovel-writer\webnovel-writer" && python -m pytest scripts/data_modules/tests/test_csv_config.py scripts/data_modules/tests/test_reasoning_engine.py -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
cd "D:\wk\novel skill\webnovel-writer" && git add webnovel-writer/references/csv/裁决规则.csv && git commit -m "fix: expand reasoning table genre aliases to cover init genre names"
```

---

## Task 2: Standardize story-system Genre Input on state.json as the Sole Source of Truth

**Problem:** When write SKILL.md calls `story-system "{chapter_goal}"`, the source of `{chapter_goal}` is unclear, making routing quality unpredictable.

**Decision:** Read genre solely from state.json. Use the chapter-outline objective as query for CSV retrieval, while always sourcing genre from state.json.

**Files:**
- Modify: `webnovel-writer/skills/webnovel-write/SKILL.md`
- Modify: `webnovel-writer/skills/webnovel-plan/SKILL.md`

- [ ] **Step 1: Update the Preparation-Stage story-system Call in write SKILL.md**

Current (lines 141–143):
```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" \
  story-system "{chapter_goal}" --chapter {chapter_num} --persist --emit-runtime-contracts --format both
```

Replace with:
```bash
# Read genre from state.json (sole source of truth)
GENRE="$(python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" state get-field --field project.genre)"

# Use the chapter-outline objective as retrieval query (fall back to genre if no outline)
CHAPTER_GOAL="{从章纲提取的本章目标，如'韩立进入坊市试探消息真伪'}"

python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" \
  story-system "${CHAPTER_GOAL}" --genre "${GENRE}" --chapter {chapter_num} --persist --emit-runtime-contracts --format both
```

Add the following explanation before this command:
```markdown
**Genre parameter rules:**
- Read `--genre` from `project.genre` in `state.json`; never enter it manually
- Set the first positional argument (query) to the chapter outline’s objective field for CSV knowledge retrieval
- If the outline has no explicit objective, fall back to `"{题材} 第{chapter_num}章"`
```

- [ ] **Step 2: Update the story-system Call in plan SKILL.md**

Current (lines 59–61):
```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" \
  story-system "{chapter_goal}" --chapter {chapter_num} --persist --emit-runtime-contracts --format both
```

Likewise use the standardized form with `--genre`.

- [ ] **Step 3: Confirm the `state get-field` CLI Command Exists**

```bash
grep -n "get-field" webnovel-writer/scripts/data_modules/webnovel.py
```

If absent, add a simple state subcommand to read an arbitrary JSON path, or use a jq/Python one-liner:

```bash
GENRE="$(python -X utf8 -c "import json; s=json.load(open('${PROJECT_ROOT}/.webnovel/state.json')); print(s.get('project',{}).get('genre',''))")"
```

- [ ] **Step 4: Commit**

```bash
git add webnovel-writer/skills/webnovel-write/SKILL.md webnovel-writer/skills/webnovel-plan/SKILL.md
git commit -m "fix: standardize story-system genre input from state.json as sole source"
```

---

## Task 3: Trigger story-system After Init to Generate MASTER_SETTING

**Problem:** After init, `.story-system/` does not exist, leaving volume planning without tone/prohibition references.

**Files:**
- Modify: `webnovel-writer/skills/webnovel-init/SKILL.md`

- [ ] **Step 1: Append a story-system Trigger to the End of the Generation Section in init SKILL.md**

After “3) Patch master outline” and before “Validation and delivery,” add:

```markdown
### 4) Generate the Pre-Writing Contract Tree (Story System Initialization)

Immediately after init, generate MASTER_SETTING to give subsequent planning tone/prohibition references:

```bash
GENRE="$(python -X utf8 -c "import json; s=json.load(open('{project_root}/.webnovel/state.json')); print(s.get('project',{}).get('genre',''))")"

python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "{project_root}" \
  story-system "${GENRE}" --genre "${GENRE}" --persist --format json
```

Notes:
- Do not pass `--chapter` yet; generate only `MASTER_SETTING.json` and `anti_patterns.json`
- Do not pass `--emit-runtime-contracts`; volume/chapter data does not exist yet
- Generate volume/chapter/review contracts when planning reaches individual chapters
```

- [ ] **Step 2: Update Init Validation and Delivery**

Add to validation checks:
```bash
test -f "{project_root}/.story-system/MASTER_SETTING.json"
```

Add to success criteria:
- `.story-system/MASTER_SETTING.json` exists and `route.primary_genre` is nonempty

- [ ] **Step 3: Commit**

```bash
git add webnovel-writer/skills/webnovel-init/SKILL.md
git commit -m "feat: init triggers story-system to generate MASTER_SETTING after project creation"
```

---

## Task 4: Clarify That chapter_brief Contains Only Reasoning Metadata

**Problem:** `chapter_focus` in `chapter_brief.json` is assembled from CSV results, unrelated to the actual chapter outline, and misleads context-agent.

**Decision:** chapter_brief contains only reasoning/routing metadata. The chapter outline has highest priority after user input and is read directly by context-agent.

**Files:**
- Modify: `webnovel-writer/agents/context-agent.md`
- Modify: `webnovel-writer/skills/webnovel-write/SKILL.md`

- [ ] **Step 1: Clarify Priorities in the Story System Mainline Section of context-agent.md**

After the pre-writing sources-of-truth list, add priority guidance:

```markdown
**Data priority (highest → lowest):**
1. Explicit user requirements
2. Original master/chapter outline (this chapter’s content in `大纲/第X卷-详细大纲.md`)
3. Story Contracts `MASTER_SETTING` (genre, tone, core prohibitions)
4. The `reasoning` field in `chapter_{NNN}.json` (reasoning-layer style/pacing/reader-turn-off advice)
5. Accepted `CHAPTER_COMMIT` (post-writing facts)
6. CSV retrieval results (creative references; do not override the outline)

The `chapter_focus` field in `chapter_{NNN}.json` is only a CSV-derived reference, not the actual chapter objective. The original chapter outline defines that objective.
```

- [ ] **Step 2: Add Guidance to the Required Contract-Tree Files Section of write SKILL.md**

After the contract-tree explanation at lines 146–148, add:

```markdown
**Note**: `chapter_focus` in `.story-system/chapters/chapter_{NNN}.json` is CSV-derived advice, not the actual chapter objective. For that objective, the original outline in `大纲/第X卷-详细大纲.md` takes highest priority. The core value of `chapter_{NNN}.json` is the reasoning metadata in `reasoning`: style priorities, pacing strategies, and anti-patterns.
```

- [ ] **Step 3: Commit**

```bash
git add webnovel-writer/agents/context-agent.md webnovel-writer/skills/webnovel-write/SKILL.md
git commit -m "docs: clarify chapter_brief carries reasoning metadata, outline is authority"
```

---

## Task 5: Read Existing Writing During Cross-Volume Planning

**Problem:** Planning volume 2 does not read commit history, summaries, or entity state, so chapter outlines may contradict existing writing.

**Decision:** Planning Step 1 loads the outline + user input + existing plot state + CSV retrieval.

**Files:**
- Modify: `webnovel-writer/skills/webnovel-plan/SKILL.md`

- [ ] **Step 1: Expand Data Loading in Planning Step 1**

Current Step 1 (lines 97–113) reads only state.json and the master outline. Replace with:

```markdown
### Step 1: Load Project Data and Confirm Prerequisites

**Required inputs:**

```bash
# Project state and genre
cat "$PROJECT_ROOT/.webnovel/state.json"

# Master outline (global blueprint)
cat "$PROJECT_ROOT/大纲/总纲.md"
```

**Plot state of existing volumes** (required for cross-volume planning):

If completed volumes exist (files under `.webnovel/summaries/`), load the following to understand existing writing:

```bash
# Latest five chapter summaries (understand plot direction)
for ch in $(seq $((START_CH - 5)) $((START_CH - 1))); do
  cat "$PROJECT_ROOT/.webnovel/summaries/ch$(printf '%04d' $ch).md" 2>/dev/null
done

# Current core-character state (understand protagonist progress)
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  knowledge query-entity-state --entity "{protagonist_id}" --at-chapter {上一卷最后章}

# Current core-relationship state
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  knowledge query-relationships --entity "{protagonist_id}" --at-chapter {上一卷最后章}

# Active foreshadowing (unresolved across volumes)
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  memory-contract get-open-loops
```

**CSV creative references** (retrieve as needed during volume planning):

```bash
# Genre-relevant pacing and plot-beat references for this volume
python -X utf8 "${SCRIPTS_DIR}/reference_search.py" --skill plan --table 爽点与节奏 --query "{卷级核心冲突}" --genre "${GENRE}"
python -X utf8 "${SCRIPTS_DIR}/reference_search.py" --skill plan --table 桥段套路 --query "{卷级核心冲突}" --genre "${GENRE}"
```
```

Read as needed (unchanged):
- `设定集/世界观.md`
- `设定集/力量体系.md`
- `设定集/主角卡.md`
- `设定集/反派设计.md`
- `.webnovel/idea_bank.json`

- [ ] **Step 2: Add Existing-State References to Planning Step 6 (Volume Outline Skeleton)**

After the Step 6 list of required volume-outline details, add:

```markdown
Cross-volume consistency checks:
- Unresolved foreshadowing from the previous volume must appear in the new volume’s plan, either advanced further or marked for payoff
- Carry forward relationship changes; do not act as if the previous volume never happened
- Continue protagonist ability/realm progression without regression or skipped levels unless explained by the plot
```

- [ ] **Step 3: Commit**

```bash
git add webnovel-writer/skills/webnovel-plan/SKILL.md
git commit -m "feat: plan reads write history for cross-volume awareness"
```

---

## Task 6: Run Tests + Final Validation

**Files:** (read-only verification)

- [ ] **Step 1: Run All Prompt-Integrity Tests**

```bash
cd "D:\wk\novel skill\webnovel-writer\webnovel-writer" && python -m pytest scripts/data_modules/tests/test_prompt_integrity.py -v --tb=short
```

- [ ] **Step 2: Run CSV Configuration Alignment Tests**

```bash
cd "D:\wk\novel skill\webnovel-writer\webnovel-writer" && python -m pytest scripts/data_modules/tests/test_csv_config.py -v --tb=short
```

- [ ] **Step 3: Verify Reasoning-Table Alias Coverage**

```bash
python3 -c "
import csv
from pathlib import Path
path = Path('webnovel-writer/references/csv/裁决规则.csv')
with open(path, 'r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        genre = row['题材']
        keywords = row['关键词']
        print(f'{genre}: {keywords}')
"
```

Confirm init labels such as 修仙, 西幻, 系统流, 都市脑洞, and 历史脑洞 appear in the corresponding rows’ keywords.

- [ ] **Step 4: Manually Walk the Critical Init→Write Path**

Simulated checks:
1. Init sets genre="修仙" → state.json.project.genre="修仙"
2. Init triggers story-system "修仙" --genre "修仙" → MASTER_SETTING.json is generated
3. Write reads genre from state.json → passes --genre "修仙" to story-system
4. story-system `_route()` attempts to match 修仙 → routing-table fallback (no exact match, but explicit_genre_fallback exists)
5. story-system `_load_reasoning("修仙")` → matches the 东方仙侠 reasoning row through alias 修仙
6. Reasoning takes effect → chapter_brief.reasoning has a value

Confirm this path is unbroken.

- [ ] **Step 5: Commit final**

```bash
git add -A && git commit -m "chore: final verification for chain integrity fixes"
```
