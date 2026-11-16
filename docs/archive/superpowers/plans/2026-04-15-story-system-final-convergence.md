# Story System Final Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Converge Story System from coexisting partial implementations into a usable six-layer mainline with synchronized consumers, covering nine sections: CSV_CONFIG registration, reasoning table, engine changes, context_manager slimming, legacy scattered-write cleanup, projection consolidation, consumer synchronization, and vector-index enhancements.

**Architecture:** Proceed serially from the bottom up: introduce per-table `CSV_CONFIG` in `reference_search.py`; standardize CSV reader-turn-off columns; create a reasoning table; integrate reasoning in `story_system_engine.py`; slim down `context_manager.py`; remove scattered legacy writes; consolidate projections; then synchronize consumer prompts and enhance the vector index.

**Tech Stack:** Python 3.11+, pytest, CSV (UTF-8 BOM), SQLite FTS5, RAG embedding

**Spec:** `docs/superpowers/specs/2026-04-14-story-system-final-convergence-spec.md`

---

## File Structure Overview

### New Files

| File | Responsibility |
|------|------|
| `webnovel-writer/references/csv/裁决规则.csv` | Reasoning layer keyed by genre, determining match priority and injection location |
| `webnovel-writer/scripts/data_modules/knowledge_query.py` | Temporal query interfaces: entity_state_at_chapter / relationships_at_chapter |
| `webnovel-writer/scripts/data_modules/vector_projection_writer.py` | Write events/entity_delta to the vector store after commits |
| `webnovel-writer/scripts/data_modules/tests/test_csv_config.py` | Validate CSV_CONFIG alignment with CSV headers |
| `webnovel-writer/scripts/data_modules/tests/test_reasoning_engine.py` | Reasoning-layer unit tests |
| `webnovel-writer/scripts/data_modules/tests/test_knowledge_query.py` | Temporal query unit tests |
| `webnovel-writer/scripts/data_modules/tests/test_vector_projection_writer.py` | Vector projection write tests |

### Main Modified Files

| File | Change Summary |
|------|---------|
| `webnovel-writer/scripts/reference_search.py` | Introduce `CSV_CONFIG`; `search()` uses per-table `search_cols` |
| `webnovel-writer/scripts/data_modules/story_system_engine.py` | Integrate the reasoning table; add `_load_reasoning` / `_apply_reasoning` / `_rank_anti_patterns` / `_assemble_contract` |
| `webnovel-writer/scripts/data_modules/context_manager.py` | Remove snapshot logic, `_compact_json_text`, and text rendering; reduce to fewer than 400 lines |
| `webnovel-writer/scripts/extract_chapter_context.py` | Make `_render_text()` pure JSON serialization; context-agent writes the brief from examples instead of code rendering text |
| `webnovel-writer/scripts/data_modules/event_projection_router.py` | Add `"vector"` routes for six event types |
| `webnovel-writer/scripts/data_modules/chapter_commit_service.py` | Integrate `VectorProjectionWriter` into `apply_projections` |
| `webnovel-writer/scripts/data_modules/state_projection_writer.py` | Advance `chapter_status` exclusively through projections |
| `webnovel-writer/skills/webnovel-write/SKILL.md` | Remove Step 2/4 `set-chapter-status` and direct `core-constraints` / `anti-ai-guide` reads |
| `webnovel-writer/agents/context-agent.md` | Align tool descriptions and research-source paths with code |
| `webnovel-writer/agents/data-agent.md` | Ensure no direct state/index/memory writes |
| `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py` | Add assertions detecting scattered writes |
| `webnovel-writer/scripts/data_modules/tests/test_event_projection_router.py` | Add vector-routing tests |
| `webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py` | Add reasoning-layer tests |
| `webnovel-writer/scripts/tests/test_reference_search.py` | Add per-table search_cols tests |
| `webnovel-writer/references/csv/*.csv` | Standardize reader-turn-off column names |

### Deleted Files

| File | Reason |
|------|------|
| `webnovel-writer/scripts/data_modules/snapshot_manager.py` | Remove snapshot logic as part of context_manager slimming |

---

## Task 1: CSV_CONFIG Registry Layer

**Files:**
- Modify: `webnovel-writer/scripts/reference_search.py:90-191`
- Create: `webnovel-writer/scripts/data_modules/tests/test_csv_config.py`
- Modify: `webnovel-writer/scripts/tests/test_reference_search.py`

- [ ] **Step 1: Add `CSV_CONFIG` to `reference_search.py`**

Insert `CSV_CONFIG` before `_TOKEN_SPLIT_RE`, around line 89:

```python
# ---------------------------------------------------------------------------
# Per-table configuration
# ---------------------------------------------------------------------------

CSV_CONFIG: Dict[str, Dict[str, Any]] = {
    "命名规则": {
        "file": "命名规则.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "命名对象", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "base",
    },
    "场景写法": {
        "file": "场景写法.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "模式名称", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "base",
    },
    "写作技法": {
        "file": "写作技法.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "技法名称", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "base",
    },
    "桥段套路": {
        "file": "桥段套路.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "桥段名称", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "dynamic",
    },
    "爽点与节奏": {
        "file": "爽点与节奏.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "节奏类型", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "dynamic",
    },
    "人设与关系": {
        "file": "人设与关系.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "人设类型", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "base",
    },
    "金手指与设定": {
        "file": "金手指与设定.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "设定类型", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "base",
    },
    "题材与调性推理": {
        "file": "题材与调性推理.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "题材别名": 3},
        "output_cols": ["编号", "题材/流派", "核心调性", "推荐基础检索表", "推荐动态检索表"],
        "poison_col": "毒点",
        "role": "route",
    },
    "裁决规则": {
        "file": "裁决规则.csv",
        "search_cols": {"题材": 4},
        "output_cols": [
            "题材", "风格优先级", "爽点优先级", "节奏默认策略",
            "毒点权重", "冲突裁决", "contract注入层", "反模式",
        ],
        "poison_col": "",
        "role": "reasoning",
    },
}
```

- [ ] **Step 2: Make `_build_doc_terms()` Use Per-Table `search_cols`**

Replace the global `_SEARCH_FIELD_WEIGHTS` dict with per-table parameters:

```python
# Delete the old global constant
# _SEARCH_FIELD_WEIGHTS = { ... }  # delete

# Retain as the default fallback
_DEFAULT_SEARCH_WEIGHTS: Dict[str, int] = {
    "意图与同义词": 4,
    "关键词": 3,
    "核心摘要": 2,
    "详细展开": 1,
}


def _build_doc_terms(row: Dict[str, str], search_weights: Dict[str, int] | None = None) -> List[str]:
    """Build weighted BM25 terms from the configured search fields."""
    weights = search_weights or _DEFAULT_SEARCH_WEIGHTS
    terms: List[str] = []
    for field, weight in weights.items():
        field_terms = _tokenize(row.get(field, ""))
        if not field_terms:
            continue
        terms.extend(field_terms * weight)
    return terms
```

- [ ] **Step 3: Make `search()` Read Configuration From `CSV_CONFIG`**

In `search()`, look up `CSV_CONFIG` using the `table` argument:

```python
def search(
    csv_dir: Path,
    skill: str,
    query: str,
    table: Optional[str] = None,
    genre: Optional[str] = None,
    max_results: int = 5,
) -> Dict[str, Any]:
    # ... (error check unchanged)

    tables = load_tables(csv_dir, table=table)
    if not tables:
        # ... (unchanged)

    # Look up search_cols by table
    table_config = CSV_CONFIG.get(table) if table else None
    search_weights = (
        dict(table_config["search_cols"]) if table_config else None
    )

    # 1) Collect filtered rows
    candidates: List[tuple] = []
    for tbl_name, rows in tables.items():
        for row in rows:
            if _skill_matches(row, skill) and _genre_matches(row, genre):
                candidates.append((tbl_name, row))

    if not candidates:
        # ... (unchanged)

    # 2) Tokenize using each row’s table-specific search_cols
    query_terms = _tokenize(query)
    doc_terms_list = []
    for tbl_name, row in candidates:
        tbl_cfg = CSV_CONFIG.get(tbl_name)
        weights = dict(tbl_cfg["search_cols"]) if tbl_cfg else search_weights
        doc_terms_list.append(_build_doc_terms(row, weights))

    # 3-4) unchanged ...
```

- [ ] **Step 4: Delete `_SEARCH_FIELD_WEIGHTS` and `_CONTENT_COLUMNS`**

Delete `_SEARCH_FIELD_WEIGHTS` at lines 90–95 and `_CONTENT_COLUMNS` at lines 180–190.

Update `_build_summary()` to select fields in `CSV_CONFIG.output_cols` order when available, otherwise retain the existing fallback.

```python
def _build_summary(row: Dict[str, str], table_name: str | None = None) -> str:
    core_summary = row.get("核心摘要", "").strip()
    if core_summary:
        return core_summary

    # Prefer output_cols from CSV_CONFIG
    if table_name and table_name in CSV_CONFIG:
        cols = CSV_CONFIG[table_name]["output_cols"]
    else:
        cols = [
            "技法名称", "桥段名称", "人设类型", "节奏类型", "设定类型",
            "规则", "说明", "模式名称", "命名对象", "场景类型",
        ]

    parts: List[str] = []
    for col in cols:
        val = row.get(col, "").strip()
        if val and col not in ("编号", "大模型指令", "详细展开", "核心摘要"):
            parts.append(val)
    if parts:
        return "；".join(parts)
    return row.get("详细展开", "").strip()
```

- [ ] **Step 5: Create CSV_CONFIG Alignment Tests**

```python
# webnovel-writer/scripts/data_modules/tests/test_csv_config.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate CSV_CONFIG alignment with actual CSV headers."""
import csv
from pathlib import Path

import pytest

# reference_search.py is under scripts/; add it to sys.path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from reference_search import CSV_CONFIG

CSV_DIR = Path(__file__).resolve().parent.parent.parent.parent / "references" / "csv"


@pytest.mark.parametrize("table_name,config", list(CSV_CONFIG.items()))
def test_csv_config_columns_exist_in_csv_header(table_name: str, config: dict):
    """Every column declared in CSV_CONFIG must exist in the CSV header."""
    csv_path = CSV_DIR / config["file"]
    if not csv_path.exists():
        pytest.skip(f"{config['file']} not yet created")

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])

    all_cols = set()
    for col in config.get("search_cols", {}):
        all_cols.add(col)
    for col in config.get("output_cols", []):
        all_cols.add(col)
    poison = config.get("poison_col", "")
    if poison:
        all_cols.add(poison)

    missing = all_cols - headers
    assert not missing, f"表 {table_name} 缺少列: {missing}"


def test_csv_config_file_field_matches_filename():
    """CSV_CONFIG file must equal key + '.csv'."""
    for name, config in CSV_CONFIG.items():
        assert config["file"] == f"{name}.csv", f"{name}: file 应为 '{name}.csv'，实际为 '{config['file']}'"
```

- [ ] **Step 6: Run Tests to Validate**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_csv_config.py -v`

Expected: `裁决规则` is skipped because its file does not exist yet; all other tables pass.

- [ ] **Step 7: Add Per-Table Retrieval Tests**

Append to `webnovel-writer/scripts/tests/test_reference_search.py`:

```python
class TestPerTableSearchCols:
    """Tests for CSV_CONFIG per-table search_cols."""

    def test_different_tables_use_different_search_weights(self):
        """Verify different tables retrieve using different search_cols."""
        # Naming and scene tables both return results using their own search_cols
        out1 = run_search("--skill", "write", "--table", "命名规则", "--query", "角色命名")
        out2 = run_search("--skill", "write", "--table", "场景写法", "--query", "战斗描写")
        assert out1["status"] == "success"
        assert out2["status"] == "success"
        assert out1["data"]["total"] >= 1
        assert out2["data"]["total"] >= 1
```

- [ ] **Step 8: Run All reference_search Tests**

Run: `cd webnovel-writer && python -m pytest scripts/tests/test_reference_search.py -v`

Expected: All PASS.

- [ ] **Step 9: Commit**

```bash
git add webnovel-writer/scripts/reference_search.py webnovel-writer/scripts/data_modules/tests/test_csv_config.py webnovel-writer/scripts/tests/test_reference_search.py
git commit -m "feat: introduce per-table CSV_CONFIG in reference_search"
```

---

## Task 2: Standardize CSV Reader-Turn-Off Columns

**Files:**
- Modify: `webnovel-writer/references/csv/场景写法.csv` (header rename)
- Modify: `webnovel-writer/references/csv/写作技法.csv` (header rename)
- Modify: `webnovel-writer/references/csv/爽点与节奏.csv` (header rename)
- Modify: `webnovel-writer/references/csv/人设与关系.csv` (header rename)
- Modify: `webnovel-writer/references/csv/桥段套路.csv` (header rename)
- Modify: `webnovel-writer/references/csv/题材与调性推理.csv` (header rename)
- Modify: `webnovel-writer/scripts/data_modules/story_system_engine.py:15-22`

- [ ] **Step 1: Inventory Current Reader-Turn-Off Column Names**

Current column mapping:
- `场景写法.csv` → `反面写法`
- `写作技法.csv` → `常见误区`
- `爽点与节奏.csv` → `常见崩盘误区`
- `人设与关系.csv` → `忌讳写法`
- `桥段套路.csv` → has an `忌讳写法` column
- `题材与调性推理.csv` → `强制禁忌/毒点`
- `命名规则.csv` → no reader-turn-off column; retain existing `反例` and add `毒点`
- `金手指与设定.csv` → no reader-turn-off column; add `毒点`

- [ ] **Step 2: Batch-Rename CSV Headers**

Run this one-off script without adding it to the repository:

```python
# Execute directly in Bash
python3 -c "
import csv, sys
from pathlib import Path

csv_dir = Path('webnovel-writer/references/csv')

renames = {
    '场景写法.csv': {'反面写法': '毒点'},
    '写作技法.csv': {'常见误区': '毒点'},
    '爽点与节奏.csv': {'常见崩盘误区': '毒点'},
    '人设与关系.csv': {'忌讳写法': '毒点'},
    '桥段套路.csv': {'忌讳写法': '毒点'},
    '题材与调性推理.csv': {'强制禁忌/毒点': '毒点'},
}

for filename, mapping in renames.items():
    path = csv_dir / filename
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        old_fields = list(reader.fieldnames)

    new_fields = [mapping.get(f, f) for f in old_fields]

    new_rows = []
    for row in rows:
        new_row = {}
        for old_f, new_f in zip(old_fields, new_fields):
            new_row[new_f] = row.get(old_f, '')
        new_rows.append(new_row)

    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fields)
        writer.writeheader()
        writer.writerows(new_rows)

print('Done')
"
```

- [ ] **Step 3: Add Empty `毒点` Columns to `命名规则.csv` and `金手指与设定.csv`**

```python
python3 -c "
import csv
from pathlib import Path

csv_dir = Path('webnovel-writer/references/csv')

for filename in ['命名规则.csv', '金手指与设定.csv']:
    path = csv_dir / filename
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames)

    if '毒点' not in fields:
        fields.append('毒点')
        for row in rows:
            row['毒点'] = ''

    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

print('Done')
"
```

- [ ] **Step 4: Update `ANTI_PATTERN_SOURCE_FIELDS` in `story_system_engine.py`**

Replace the old mapping at lines 15–22:

```python
ANTI_PATTERN_SOURCE_FIELDS = {
    "场景写法": ["反面写法"],
    "写作技法": ["常见误区"],
    "爽点与节奏": ["常见崩盘误区"],
    "人设与关系": ["忌讳写法"],
    "桥段套路": ["忌讳写法"],
    "题材与调性推理": ["强制禁忌/毒点"],
}
```

With this unified mapping:

```python
ANTI_PATTERN_SOURCE_FIELDS = {
    "场景写法": ["毒点"],
    "写作技法": ["毒点"],
    "爽点与节奏": ["毒点"],
    "人设与关系": ["毒点"],
    "桥段套路": ["毒点"],
    "题材与调性推理": ["毒点"],
    "命名规则": ["毒点"],
    "金手指与设定": ["毒点"],
}
```

- [ ] **Step 5: Run Tests**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_csv_config.py scripts/data_modules/tests/test_story_system_engine.py scripts/tests/test_reference_search.py -v`

Expected: test_story_system_engine fails because fixture CSVs still use old column names.

- [ ] **Step 6: Fix Fixture Column Names in `test_story_system_engine.py`**

Rename fixture CSV columns `忌讳写法`, `常见崩盘误区`, and `强制禁忌/毒点` to `毒点`.

Change `桥段套路.csv` fixture headers at line 53 to:
```python
["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要", "桥段名称", "毒点"],
```
Rename corresponding row keys from `忌讳写法` to `毒点`.

Change `爽点与节奏.csv` fixture headers at line 71 to:
```python
["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要", "毒点", "节奏类型"],
```
Rename corresponding row keys from `常见崩盘误区` to `毒点`.

At fixture line 26, rename `强制禁忌/毒点` to `毒点` in both `题材与调性推理.csv` headers and row keys.

- [ ] **Step 7: Run Tests and Confirm All Pass**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_story_system_engine.py scripts/data_modules/tests/test_csv_config.py -v`

Expected: All PASS.

- [ ] **Step 8: Commit**

```bash
git add webnovel-writer/references/csv/*.csv webnovel-writer/scripts/data_modules/story_system_engine.py webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py
git commit -m "refactor: unify poison column name to 毒点 across all CSV tables"
```

---

## Task 3: Create the Reasoning Rules Table

**Files:**
- Create: `webnovel-writer/references/csv/裁决规则.csv`

- [ ] **Step 1: Create the Reasoning Rules CSV File**

```csv
编号,适用技能,分类,层级,关键词,意图与同义词,适用题材,大模型指令,核心摘要,详细展开,题材,风格优先级,爽点优先级,节奏默认策略,毒点权重,冲突裁决,contract注入层,反模式
RS-001,write|plan,裁决,推理层,西方奇幻|奇幻,西方奇幻怎么写,西方奇幻,按冲突裁决排序命中条目,西方奇幻裁决规则,,西方奇幻,史诗感 > 冷硬算计 > 日常轻松,实力碾压 > 逆境翻盘 > 智谋博弈,快推慢收 对峙段拉长 过渡段压短,圣母病 > 情绪标签化 > 逻辑断裂,爽点与节奏 > 场景写法 > 写作技法,CHAPTER_BRIEF.writing_guidance,情绪标签化|角色行为无逻辑|战斗无代价
RS-002,write|plan,裁决,推理层,东方仙侠|仙侠,仙侠怎么写,东方仙侠,按冲突裁决排序命中条目,东方仙侠裁决规则,,东方仙侠,冷硬算计 > 超然物外 > 热血冲突,境界碾压 > 底牌揭晓 > 因果兑现,慢蓄快爆 修炼段精简 斗法段拉满,修炼水字数 > 圣母病 > 逻辑断裂,爽点与节奏 > 桥段套路 > 场景写法,CHAPTER_BRIEF.writing_guidance,修炼变流水账|境界突破无代价|感悟靠顿悟标签
RS-003,write|plan,裁决,推理层,科幻末世|末世|科幻,科幻末世怎么写,科幻末世,按冲突裁决排序命中条目,科幻末世裁决规则,,科幻末世,高压克制 > 冷硬算计 > 绝境反击,绝境生存 > 资源碾压 > 智谋博弈,紧凑推进 危机不断 喘息极短,主角无敌 > 科技无代价 > 末世无压迫感,场景写法 > 爽点与节奏 > 写作技法,CHAPTER_BRIEF.writing_guidance,末世没有生存压力|科技万能|角色行为无逻辑
RS-004,write|plan,裁决,推理层,都市日常|都市,都市日常怎么写,都市日常,按冲突裁决排序命中条目,都市日常裁决规则,,都市日常,日常轻松 > 温情治愈 > 微妙张力,情感共鸣 > 生活逆袭 > 社交碾压,慢节奏 情感铺垫长 冲突柔和,假大空说教 > 情绪标签化 > 逻辑断裂,写作技法 > 人设与关系 > 场景写法,CHAPTER_BRIEF.writing_guidance,情感靠标签|日常无冲突|角色千人一面
RS-005,write|plan,裁决,推理层,都市修真|修真|现代修真,都市修真怎么写,都市修真,按冲突裁决排序命中条目,都市修真裁决规则,,都市修真,隐秘低调 > 冷硬算计 > 热血爆发,身份反差 > 境界碾压 > 底牌揭晓,快慢交替 日常短 修真爆发长,修真体系与现代割裂 > 圣母病 > 装逼无代价,爽点与节奏 > 场景写法 > 桥段套路,CHAPTER_BRIEF.writing_guidance,修真体系照搬古代|现代元素没有影响|身份暴露无后果
RS-006,write|plan,裁决,推理层,都市高武|高武|都市异能,都市高武怎么写,都市高武,按冲突裁决排序命中条目,都市高武裁决规则,,都市高武,热血冲突 > 冷硬算计 > 力量美学,实力碾压 > 以弱胜强 > 排名跃升,快节奏 战斗密集 过渡极短,战力崩盘 > 圣母病 > 无脑开挂,爽点与节奏 > 场景写法 > 桥段套路,CHAPTER_BRIEF.writing_guidance,战力体系自相矛盾|升级无代价|打斗无策略
RS-007,write|plan,裁决,推理层,历史古代|历史|古代,历史古代怎么写,历史古代,按冲突裁决排序命中条目,历史古代裁决规则,,历史古代,沉稳厚重 > 权谋算计 > 家国情怀,权谋碾压 > 历史转折 > 身份反转,慢铺快收 权谋段拉长 战争段紧凑,现代价值观强加古人 > 逻辑断裂 > 历史常识错误,写作技法 > 人设与关系 > 场景写法,CHAPTER_BRIEF.writing_guidance,用现代口语写古代|权谋无逻辑|历史事件随意篡改
```

- [ ] **Step 2: Run CSV_CONFIG Validation to Confirm New Headers Align**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_csv_config.py -v`

Expected: `裁决规则` now exists and should PASS.

- [ ] **Step 3: Commit**

```bash
git add webnovel-writer/references/csv/裁决规则.csv
git commit -m "feat: add 裁决规则.csv reasoning table for 7 genres"
```

---

## Task 4: Integrate the Reasoning Table Into the Engine

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/story_system_engine.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_reasoning_engine.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py`

- [ ] **Step 1: Write Reasoning-Layer Tests**

```python
# webnovel-writer/scripts/data_modules/tests/test_reasoning_engine.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reasoning-layer integration tests."""
import csv

from data_modules.story_system_engine import StorySystemEngine


def _write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


ROUTE_HEADERS = [
    "编号", "适用技能", "分类", "层级", "关键词", "意图与同义词", "适用题材",
    "大模型指令", "核心摘要", "详细展开", "题材/流派", "题材别名", "核心调性",
    "节奏策略", "毒点", "推荐基础检索表", "推荐动态检索表", "默认查询词",
]

REASONING_HEADERS = [
    "编号", "适用技能", "分类", "层级", "关键词", "意图与同义词", "适用题材",
    "大模型指令", "核心摘要", "详细展开",
    "题材", "风格优先级", "爽点优先级", "节奏默认策略",
    "毒点权重", "冲突裁决", "contract注入层", "反模式",
]


def _setup_csvs(csv_dir):
    _write_csv(csv_dir / "题材与调性推理.csv", ROUTE_HEADERS, [{
        "编号": "GR-001", "适用技能": "write|plan", "分类": "题材路由",
        "层级": "知识补充", "关键词": "玄幻", "意图与同义词": "玄幻|仙侠",
        "适用题材": "玄幻", "大模型指令": "", "核心摘要": "", "详细展开": "",
        "题材/流派": "玄幻", "题材别名": "玄幻", "核心调性": "热血冲突",
        "节奏策略": "快推慢收", "毒点": "圣母病",
        "推荐基础检索表": "命名规则|人设与关系",
        "推荐动态检索表": "桥段套路|爽点与节奏",
        "默认查询词": "玄幻",
    }])

    _write_csv(csv_dir / "裁决规则.csv", REASONING_HEADERS, [{
        "编号": "RS-001", "适用技能": "write|plan", "分类": "裁决",
        "层级": "推理层", "关键词": "玄幻", "意图与同义词": "玄幻",
        "适用题材": "玄幻", "大模型指令": "", "核心摘要": "", "详细展开": "",
        "题材": "玄幻",
        "风格优先级": "热血冲突 > 冷硬算计",
        "爽点优先级": "实力碾压 > 逆境翻盘",
        "节奏默认策略": "快推慢收",
        "毒点权重": "圣母病 > 情绪标签化",
        "冲突裁决": "爽点与节奏 > 场景写法 > 写作技法",
        "contract注入层": "CHAPTER_BRIEF.writing_guidance",
        "反模式": "情绪标签化|战斗无代价",
    }])

    _write_csv(csv_dir / "桥段套路.csv",
        ["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要", "桥段名称", "毒点"],
        [{"编号": "TR-001", "适用技能": "write", "分类": "桥段", "层级": "知识补充",
          "关键词": "退婚", "适用题材": "玄幻", "核心摘要": "退婚反击",
          "桥段名称": "退婚反击", "毒点": "配角代打"}])

    _write_csv(csv_dir / "爽点与节奏.csv",
        ["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要", "毒点", "节奏类型"],
        [{"编号": "PA-001", "适用技能": "write", "分类": "节奏", "层级": "知识补充",
          "关键词": "打脸", "适用题材": "玄幻", "核心摘要": "兑现必须补刀",
          "毒点": "打脸软收尾", "节奏类型": "爆发期"}])


def test_build_with_reasoning_includes_reasoning_rule_in_source_trace(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()
    _setup_csvs(csv_dir)

    engine = StorySystemEngine(csv_dir=csv_dir)
    contract = engine.build(query="玄幻", genre=None, chapter=5)

    traces = contract["master_setting"]["source_trace"]
    reasoning_traces = [t for t in traces if t.get("reasoning_rule")]
    assert len(reasoning_traces) >= 1
    assert reasoning_traces[0]["reasoning_rule"] == "玄幻"


def test_reasoning_anti_patterns_sorted_by_weight(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()
    _setup_csvs(csv_dir)

    engine = StorySystemEngine(csv_dir=csv_dir)
    contract = engine.build(query="玄幻", genre=None, chapter=5)

    anti = contract["anti_patterns"]
    assert len(anti) >= 1


def test_reasoning_not_found_falls_back_gracefully(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()
    _setup_csvs(csv_dir)

    engine = StorySystemEngine(csv_dir=csv_dir)
    contract = engine.build(query="末日生存", genre="末日", chapter=1)

    # Missing reasoning rules must not cause an error
    assert "master_setting" in contract
    assert "anti_patterns" in contract
```

- [ ] **Step 2: Run Tests and Confirm Failure**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_reasoning_engine.py -v`

Expected: FAIL because `_load_reasoning` and related methods do not exist yet.

- [ ] **Step 3: Add Reasoning Methods to `story_system_engine.py`**

Append to `StorySystemEngine`:

```python
def _load_reasoning(self, genre: str) -> Dict[str, Any]:
    """Look up a genre row in the reasoning table and return a rule dict."""
    rows = self._load_csv_rows("裁决规则")
    genre_text = self._normalize_text(genre)
    for row in rows:
        row_genre = self._normalize_text(row.get("题材", ""))
        if row_genre == genre_text:
            return row
        aliases = self._split_multi_value(row.get("关键词")) + self._split_multi_value(row.get("意图与同义词"))
        if any(self._normalize_text(a) == genre_text for a in aliases):
            return row
    return {}

def _apply_reasoning(
    self,
    reasoning: Dict[str, Any],
    base_context: List[Dict[str, Any]],
    dynamic_context: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Rank matches using the conflict-adjudication field."""
    if not reasoning:
        return base_context + dynamic_context

    priority_order = [
        t.strip() for t in str(reasoning.get("冲突裁决", "")).split(">") if t.strip()
    ]
    priority_map = {name: idx for idx, name in enumerate(priority_order)}

    all_rows = base_context + dynamic_context
    for row in all_rows:
        table_name = str(row.get("_table", "")).strip()
        row["_priority_rank"] = priority_map.get(table_name, len(priority_order))
        row["_reasoning_rule"] = str(reasoning.get("题材", "")).strip()

    all_rows.sort(key=lambda r: r.get("_priority_rank", 999))
    return all_rows

def _rank_anti_patterns(
    self,
    reasoning: Dict[str, Any],
    anti_patterns: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Rank reader turn-offs using their weight field."""
    if not reasoning:
        return anti_patterns

    weight_order = [
        t.strip() for t in str(reasoning.get("毒点权重", "")).split(">") if t.strip()
    ]

    def sort_key(item):
        text = str(item.get("text", "")).strip()
        for idx, keyword in enumerate(weight_order):
            if keyword in text:
                return idx
        return len(weight_order)

    anti_patterns.sort(key=sort_key)

    # Append anti-patterns supplied by the reasoning table
    for text in self._split_multi_value(reasoning.get("反模式")):
        anti_patterns.append({
            "text": text,
            "source_table": "裁决规则",
            "source_id": reasoning.get("编号", ""),
        })

    return anti_patterns
```

- [ ] **Step 4: Integrate Reasoning Into `build()`**

Replace `build()` at lines 29–90 with:

```python
def build(self, query: str, genre: Optional[str], chapter: Optional[int]) -> Dict[str, Any]:
    route = self._route(query=query, genre=genre)
    search_query = self._expand_query(query, route.get("default_query", ""))
    base_context = self._collect_tables(
        search_query,
        route["recommended_base_tables"],
        genre=route["genre_filter"],
        top_k=1,
    )
    dynamic_context = self._collect_tables(
        search_query,
        route["recommended_dynamic_tables"],
        genre=route["genre_filter"],
        top_k=2,
    )

    # --- Reasoning layer ---
    primary_genre = str(
        route.get("meta", {}).get("primary_genre", "") or genre or ""
    ).strip()
    reasoning = self._load_reasoning(primary_genre)
    ranked = self._apply_reasoning(reasoning, base_context, dynamic_context)

    source_trace = route["source_trace"] + self._build_source_trace_with_reasoning(ranked, reasoning)

    raw_anti = merge_anti_patterns(
        route["route_anti_patterns"],
        self._extract_anti_patterns(base_context),
        self._extract_anti_patterns(dynamic_context),
    )
    anti_patterns = self._rank_anti_patterns(reasoning, raw_anti)

    return {
        "meta": {"query": query, "chapter": chapter, "explicit_genre": genre or ""},
        "master_setting": {
            "meta": {
                "schema_version": "story-system/v1",
                "contract_type": "MASTER_SETTING",
                "generator_version": "phase1",
                "query": query,
            },
            "route": route["meta"],
            "master_constraints": {
                "core_tone": route["core_tone"],
                "pacing_strategy": route["pacing_strategy"],
            },
            "base_context": [r for r in ranked if r.get("_priority_rank", 999) < 999],
            "source_trace": source_trace,
            "override_policy": {
                "locked": ["route.primary_genre", "master_constraints.core_tone"],
                "append_only": ["anti_patterns"],
                "override_allowed": [],
            },
        },
        "chapter_brief": (
            {
                "meta": {
                    "schema_version": "story-system/v1",
                    "contract_type": "CHAPTER_BRIEF",
                    "generator_version": "phase1",
                    "chapter": chapter,
                },
                "override_allowed": {
                    "chapter_focus": self._suggest_chapter_focus(query, dynamic_context),
                },
                "dynamic_context": ranked,
                "source_trace": source_trace,
                "reasoning": {
                    "genre": reasoning.get("题材", ""),
                    "inject_target": reasoning.get("contract注入层", ""),
                    "style_priority": reasoning.get("风格优先级", ""),
                    "pacing_strategy": reasoning.get("节奏默认策略", ""),
                } if reasoning else {},
            }
            if chapter is not None
            else None
        ),
        "anti_patterns": anti_patterns,
    }
```

- [ ] **Step 5: Add `_build_source_trace_with_reasoning`**

```python
def _build_source_trace_with_reasoning(
    self, ranked: List[Dict[str, Any]], reasoning: Dict[str, Any]
) -> List[Dict[str, Any]]:
    trace: List[Dict[str, Any]] = []
    reasoning_rule = str(reasoning.get("题材", "")).strip() if reasoning else ""
    for row in ranked:
        trace.append({
            "table": row.get("_table", ""),
            "id": row.get("编号", ""),
            "summary": row.get("核心摘要", ""),
            "reasoning_rule": row.get("_reasoning_rule", reasoning_rule),
            "priority_rank": row.get("_priority_rank", 999),
            "inject_target": str(reasoning.get("contract注入层", "")).strip() if reasoning else "",
        })
    return trace
```

- [ ] **Step 6: Run Reasoning-Layer Tests**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_reasoning_engine.py -v`

Expected: All PASS.

- [ ] **Step 7: Run Existing Engine Tests to Check for Regressions**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_story_system_engine.py -v`

Expected: All PASS, with graceful fallback when the reasoning table is absent.

- [ ] **Step 8: Commit**

```bash
git add webnovel-writer/scripts/data_modules/story_system_engine.py webnovel-writer/scripts/data_modules/tests/test_reasoning_engine.py
git commit -m "feat: integrate reasoning table into story_system_engine build pipeline"
```

---

## Task 5: Slim Down context_manager

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/context_manager.py`
- Delete: `webnovel-writer/scripts/data_modules/snapshot_manager.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_context_manager.py`

- [ ] **Step 1: Remove Snapshot Code From `context_manager.py`**

1. Delete import: `from .snapshot_manager import SnapshotManager, SnapshotVersionMismatch`(line 33)
2. Delete the `self.snapshot_manager` assignment in `__init__` (line 101)
3. Delete `_is_snapshot_compatible` (lines 105–146)
4. Remove snapshot load/save logic from `build_context` (lines 162–169 and 176–181)
5. Delete `_story_contract_signature` (lines 794–817)
6. Delete `_payload_signature` (lines 819–823)
7. Remove `use_snapshot` and `save_snapshot` from `build_context`

- [ ] **Step 2: Simplify `build_context` to Return Pure JSON**

Updated `build_context`:

```python
def build_context(
    self,
    chapter: int,
    template: str | None = None,
    max_chars: Optional[int] = None,
) -> Dict[str, Any]:
    template = template or self.DEFAULT_TEMPLATE
    self._active_template = template
    if template not in self.TEMPLATE_WEIGHTS:
        template = self.DEFAULT_TEMPLATE
        self._active_template = template

    pack = self._build_pack(chapter)
    if getattr(self.config, "context_ranker_enabled", True):
        pack = self.context_ranker.rank_pack(pack, chapter)

    return self._assemble_json_payload(pack, template=template, max_chars=max_chars)
```

- [ ] **Step 3: Rewrite `assemble_context` as `_assemble_json_payload`**

Return a dict directly without text rendering:

```python
def _assemble_json_payload(
    self,
    pack: Dict[str, Any],
    template: str = DEFAULT_TEMPLATE,
    max_chars: Optional[int] = None,
) -> Dict[str, Any]:
    chapter = int((pack.get("meta") or {}).get("chapter") or 0)
    weights = self._resolve_template_weights(template=template, chapter=chapter)

    payload: Dict[str, Any] = {
        "meta": {
            **(pack.get("meta") or {}),
            "context_contract_version": "v3",
        },
    }

    for section_name in self.SECTION_ORDER:
        if section_name in pack and section_name != "global":
            content = pack[section_name]
            weight = weights.get(section_name, 0.0)
            if weight > 0 or section_name in self.EXTRA_SECTIONS:
                payload[section_name] = content

    if chapter > 0:
        payload["meta"]["context_weight_stage"] = self._resolve_context_stage(chapter)

    return payload
```

- [ ] **Step 4: Delete `_compact_json_text`**

Delete lines 749–764.

- [ ] **Step 5: Delete the Old `assemble_context` Method**

Delete `assemble_context` at lines 185–217.

- [ ] **Step 6: Update the `__init__` Signature**

```python
def __init__(self, config=None):
    self.config = config or get_config()
    self.index_manager = IndexManager(self.config)
    self.context_ranker = ContextRanker(self.config)
```

- [ ] **Step 7: Delete `snapshot_manager.py`**

```bash
git rm webnovel-writer/scripts/data_modules/snapshot_manager.py
```

- [ ] **Step 8: Update `_load_contract_context` in `extract_chapter_context.py`**

Replace `_load_contract_context` at lines 294–325 with:

```python
def _load_contract_context(project_root: Path, chapter_num: int) -> Dict[str, Any]:
    """Build context via ContextManager and return payload directly."""
    _ensure_scripts_path()
    from data_modules.config import DataModulesConfig
    from data_modules.context_manager import ContextManager

    config = DataModulesConfig.from_project_root(project_root)
    manager = ContextManager(config)
    payload = manager.build_context(chapter=chapter_num, template="plot")

    return {
        "context_contract_version": (payload.get("meta") or {}).get("context_contract_version"),
        "context_weight_stage": (payload.get("meta") or {}).get("context_weight_stage"),
        "story_contract": payload.get("story_contract", {}),
        "runtime_status": payload.get("runtime_status", {}),
        "latest_commit": payload.get("latest_commit", {}),
        "prewrite_validation": payload.get("prewrite_validation", {}),
        "reader_signal": payload.get("reader_signal", {}),
        "genre_profile": payload.get("genre_profile", {}),
        "writing_guidance": payload.get("writing_guidance", {}),
        "plot_structure": payload.get("plot_structure", {}),
        "long_term_memory": payload.get("long_term_memory", {}),
        "scene": payload.get("scene", {}),
        "core": payload.get("core", {}),
    }
```

- [ ] **Step 9: Make `_render_text()` Pure JSON Serialization**

Current `_render_text()` (lines 364–601) is a 240-line audit-style renderer. In the target specification, code no longer renders text; context-agent writes the brief from the JSON payload and examples.

Replace all of `_render_text()` with:

```python
def _render_text(payload: Dict[str, Any]) -> str:
    """Serialize JSON; context-agent handles text rendering."""
    return json.dumps(payload, ensure_ascii=False, indent=2)
```

This makes `--format text` and `--format json` identical. Any later distinction can be handled by context-agent; code no longer concatenates Markdown.

- [ ] **Step 10: Fix Affected Tests**

In `test_context_manager.py`:
- Remove all `snapshot_manager` mocks and fixtures
- Remove snapshot tests
- Remove `use_snapshot` / `save_snapshot` from `build_context` calls
- Adapt assertions to the new structure: `payload["story_contract"]` instead of `payload["sections"]["story_contract"]["content"]`

In `test_extract_chapter_context.py`:
- Update assertions depending on legacy Markdown rendering, replacing heading checks such as `"## 本章大纲"` with JSON-key checks

- [ ] **Step 11: Run Tests**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_context_manager.py scripts/data_modules/tests/test_extract_chapter_context.py -v`

Expected: All PASS.

- [ ] **Step 12: Check Line Count**

Run: `wc -l webnovel-writer/scripts/data_modules/context_manager.py`

Expected: Fewer than 400 lines.

- [ ] **Step 13: Commit**

```bash
git add webnovel-writer/scripts/data_modules/context_manager.py webnovel-writer/scripts/extract_chapter_context.py webnovel-writer/scripts/data_modules/tests/test_context_manager.py
git rm webnovel-writer/scripts/data_modules/snapshot_manager.py
git commit -m "refactor: slim context_manager to pure JSON assembler, remove snapshot"
```

---

## Task 6: Remove Scattered Legacy Write Paths

**Files:**
- Modify: `webnovel-writer/skills/webnovel-write/SKILL.md:184,254,323`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`

- [ ] **Step 1: Remove Step 2 `set-chapter-status` From SKILL.md**

Delete lines 182–184:

```markdown
状态推进：

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" state set-chapter-status --chapter {chapter_num} --status chapter_drafted
```
```

- [ ] **Step 2: Remove Step 4 `set-chapter-status` From SKILL.md**

Delete the state-advancement section at lines 250–254, labeled `状态推进（--minimal 除外）：`, and its Bash block.

- [ ] **Step 3: Remove `set-chapter-status` at the End of Step 5 in SKILL.md**

Delete the state-advancement Bash block at lines 320–323. `state_projection_writer.py` now advances Step 5 state automatically when a commit is accepted.

Add this explanation to Step 5.3 projection-status validation:

```markdown
**chapter_status advancement:**
- accepted commit → `state_projection_writer` automatically advances to `chapter_committed`
- rejected commit → `state_projection_writer` automatically advances to `chapter_rejected`
- Skills no longer call `set-chapter-status` manually
```

- [ ] **Step 4: Update Sufficiency Gates**

For gate conditions at lines 338–346:
- Remove “2. `chapter_status` has advanced to `chapter_drafted` (Step 2 complete)”
- Replace the state check in “5. ... `chapter_status` has advanced to `chapter_reviewed`” with projection-only confirmation
- Replace “6. ... `chapter_status` has advanced to `chapter_committed`” with “6. ... all four projection_status entries are done/skipped”

Replace with:

```markdown
## Sufficiency Gates

Do not finish the workflow until all these conditions hold:

1. The chapter prose file exists and is nonempty.
2. Step 3 produced and persisted review results, except in `--minimal` mode.
3. If any issue has `blocking=true`, the workflow must remain at Step 3.
4. Step 4 has `anti_ai_force_check=pass`, except in `--minimal` mode.
5. Step 5 generated an accepted `CHAPTER_COMMIT`, with all four `projection_status` entries `done` or `skipped`.
6. `chapter_status` is `chapter_committed`, advanced automatically by the projection writer, not manually written.
7. If observability is enabled, the latest timing record has been read and interpreted.
```

- [ ] **Step 5: Add Prompt-Integrity Assertions**

Append to `test_prompt_integrity.py`:

```python
def test_no_direct_state_writes_in_write_skill():
    """webnovel-write SKILL.md must not call set-chapter-status; projection writers own transitions."""
    text = (SKILLS_DIR / "webnovel-write" / "SKILL.md").read_text(encoding="utf-8")
    assert "state set-chapter-status" not in text, (
        "webnovel-write 中不应直接调用 state set-chapter-status，"
        "chapter_status 由 state_projection_writer 在 commit 时自动推进"
    )


def test_no_direct_state_writes_in_agents():
    """The agents directory must not instruct direct state/index writes."""
    for agent_file in AGENT_FILES:
        text = _read_text(agent_file)
        assert "state set-chapter-status" not in text, (
            f"{agent_file.name}: 不应直接调用 state set-chapter-status"
        )
```

- [ ] **Step 6: Run Tests**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_prompt_integrity.py -v`

Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add webnovel-writer/skills/webnovel-write/SKILL.md webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py
git commit -m "refactor: remove direct set-chapter-status calls from write skill"
```

---

## Task 7: Consolidate the Projection Layer

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/event_projection_router.py`
- Modify: `webnovel-writer/scripts/data_modules/state_projection_writer.py`
- Modify: `webnovel-writer/scripts/data_modules/chapter_commit_service.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_event_projection_router.py`

- [ ] **Step 1: Write Vector-Routing Tests**

Append to `test_event_projection_router.py`:

```python
def test_router_maps_power_breakthrough_to_state_memory_vector():
    router = EventProjectionRouter()
    targets = router.route(
        {"event_type": "power_breakthrough", "subject": "xiaoyan", "payload": {}}
    )
    assert "vector" in targets
    assert "state" in targets
    assert "memory" in targets


def test_router_maps_relationship_changed_to_index_and_vector():
    router = EventProjectionRouter()
    targets = router.route(
        {"event_type": "relationship_changed", "subject": "xiaoyan", "payload": {}}
    )
    assert "index" in targets
    assert "vector" in targets


def test_required_writers_includes_vector_for_key_events():
    router = EventProjectionRouter()
    payload = {
        "meta": {"status": "accepted", "chapter": 5},
        "accepted_events": [
            {"event_type": "power_breakthrough", "subject": "xiaoyan", "payload": {}},
        ],
        "entity_deltas": [],
        "summary_text": "摘要",
    }
    writers = router.required_writers(payload)
    assert "vector" in writers
```

- [ ] **Step 2: Run Tests and Confirm Failure**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_event_projection_router.py -v`

Expected: The three new tests FAIL.

- [ ] **Step 3: Update `EventProjectionRouter.TABLE`**

```python
class EventProjectionRouter:
    TABLE = {
        "character_state_changed": ["state", "memory", "vector"],
        "power_breakthrough": ["state", "memory", "vector"],
        "relationship_changed": ["index", "vector"],
        "world_rule_revealed": ["memory", "vector"],
        "world_rule_broken": ["memory", "vector"],
        "open_loop_created": ["memory"],
        "open_loop_closed": ["memory"],
        "promise_created": ["memory"],
        "promise_paid_off": ["memory"],
        "artifact_obtained": ["index", "vector"],
    }
```

- [ ] **Step 4: Verify `state_projection_writer` Handles `chapter_status`**

`state_projection_writer.py:34-35` already contains:

```python
if chapter > 0:
    chapter_status[str(chapter)] = "chapter_committed"
```

This satisfies Sections 6/7: accepted commits automatically advance to `chapter_committed`.

Confirm rejected commits do not advance: line 15 returns immediately when `status != "accepted"`, without writing state. This is correct.

However, the specification requires rejected commits to advance to `chapter_rejected`. Add rejected handling at the start of `apply`:

```python
def apply(self, commit_payload: dict) -> dict:
    chapter = int(commit_payload.get("meta", {}).get("chapter") or 0)
    status = commit_payload["meta"]["status"]

    if status == "rejected":
        if chapter > 0:
            state_path = self.project_root / ".webnovel" / "state.json"
            state = read_json_if_exists(state_path) or {}
            progress = state.setdefault("progress", {})
            chapter_status = progress.setdefault("chapter_status", {})
            chapter_status[str(chapter)] = "chapter_rejected"
            write_json(state_path, state)
        return {"applied": True, "writer": "state", "reason": "commit_rejected_status_updated"}

    # ... rest of accepted logic
```

- [ ] **Step 5: Verify Failure Isolation in `chapter_commit_service.apply_projections`**

Lines 115–119 already provide try/except isolation:

```python
try:
    result = writer.apply(payload)
    payload["projection_status"][name] = "done" if result.get("applied") else "skipped"
except Exception as exc:
    payload["projection_status"][name] = f"failed:{exc}"
```

At line 120, `self.persist_commit(payload)` runs only after every writer, ensuring updated `projection_status`.

This satisfies the specification; no further change is needed.

- [ ] **Step 6: Run Tests**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_event_projection_router.py -v`

Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add webnovel-writer/scripts/data_modules/event_projection_router.py webnovel-writer/scripts/data_modules/state_projection_writer.py webnovel-writer/scripts/data_modules/tests/test_event_projection_router.py
git commit -m "feat: add vector route to projection router, handle rejected status"
```

---

## Task 8: Synchronize Consumers

**Files:**
- Modify: `webnovel-writer/agents/context-agent.md`
- Modify: `webnovel-writer/agents/data-agent.md`
- Modify: `webnovel-writer/skills/webnovel-write/SKILL.md`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`

- [ ] **Step 1: Update `context-agent.md` and Remove Legacy References**

1. In Section 2 tools, confirm `extract-context` is marked optional; it already is, so leave it
2. Remove snapshot references, checking with grep whether any exist
3. Confirm Section 8 output format includes a writing-brief example, completed in the previous refactor

- [ ] **Step 2: Confirm `data-agent.md` Does Not Write Directly**

`data-agent.md` already explicitly states:
- “You do not write these files directly” (line 111)
- “Do not write directly to `index.db` and `state.json`” (line 146)

Confirm no change is needed.

- [ ] **Step 3: Simplify the Step 5 Description in `SKILL.md`**

Add vector-related entries to the Step 5.4 failure-isolation table if absent.

Confirm the Step 1 writing-brief workflow matches current code, as completed in the previous refactor.

- [ ] **Step 4: Update `KNOWN_DELETED_FILES` in `test_prompt_integrity.py`**

Add `snapshot_manager.py` to the deleted-files list:

```python
KNOWN_DELETED_FILES = [
    "step-1.5-contract.md",
    "step-3-review-gate.md",
    "step-5-debt-switch.md",
    "workflow-details.md",
    "checker-output-schema.md",
    "workflow_manager.py",
    "webnovel-resume",
    "golden_three_checker.py",
    "snapshot_manager.py",
]
```

- [ ] **Step 5: Run All Prompt-Integrity Tests**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_prompt_integrity.py -v`

Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add webnovel-writer/agents/context-agent.md webnovel-writer/agents/data-agent.md webnovel-writer/skills/webnovel-write/SKILL.md webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py
git commit -m "refactor: sync consumer prompts with new mainline"
```

---

## Task 9: Vector Projection Writer

**Files:**
- Create: `webnovel-writer/scripts/data_modules/vector_projection_writer.py`
- Modify: `webnovel-writer/scripts/data_modules/chapter_commit_service.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_vector_projection_writer.py`

- [ ] **Step 1: Write Tests**

```python
# webnovel-writer/scripts/data_modules/tests/test_vector_projection_writer.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VectorProjectionWriter unit tests."""
from data_modules.vector_projection_writer import VectorProjectionWriter


def test_event_to_text_formats_power_breakthrough():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    event = {
        "event_type": "power_breakthrough",
        "chapter": 47,
        "subject": "韩立",
        "payload": {"field": "realm", "new": "筑基初期"},
    }
    text = writer._event_to_text(event)
    assert "第47章" in text
    assert "韩立" in text
    assert "筑基初期" in text


def test_delta_to_text_formats_relationship():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    delta = {
        "from_entity": "韩立",
        "to_entity": "陈巧倩",
        "relationship_type": "合作",
        "chapter": 47,
    }
    text = writer._delta_to_text(delta)
    assert "第47章" in text
    assert "韩立" in text
    assert "陈巧倩" in text
    assert "合作" in text


def test_collect_chunks_from_commit():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    payload = {
        "meta": {"chapter": 47, "status": "accepted"},
        "accepted_events": [
            {
                "event_type": "power_breakthrough",
                "chapter": 47,
                "subject": "韩立",
                "payload": {"field": "realm", "new": "筑基初期"},
            },
        ],
        "entity_deltas": [
            {
                "from_entity": "韩立",
                "to_entity": "陈巧倩",
                "relationship_type": "合作",
                "chapter": 47,
            },
        ],
    }
    chunks = writer._collect_chunks(payload)
    assert len(chunks) == 2
    assert chunks[0]["chunk_type"] == "event"
    assert chunks[1]["chunk_type"] == "entity_delta"


def test_rejected_commit_returns_not_applied():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    writer.project_root = None  # won't be used
    result = writer.apply({"meta": {"status": "rejected", "chapter": 1}})
    assert result["applied"] is False
```

- [ ] **Step 2: Run Tests and Confirm Failure**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_vector_projection_writer.py -v`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement `vector_projection_writer.py`**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class VectorProjectionWriter:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def apply(self, commit_payload: dict) -> dict:
        if commit_payload["meta"]["status"] != "accepted":
            return {"applied": False, "writer": "vector", "reason": "commit_rejected"}

        chunks = self._collect_chunks(commit_payload)
        if not chunks:
            return {"applied": False, "writer": "vector", "reason": "no_chunks"}

        try:
            stored = self._store_chunks(chunks)
            return {"applied": stored > 0, "writer": "vector", "stored": stored}
        except Exception as exc:
            logger.warning("vector_projection_failed: %s", exc)
            return {"applied": False, "writer": "vector", "reason": f"error:{exc}"}

    def _collect_chunks(self, commit_payload: dict) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        chapter = int(commit_payload.get("meta", {}).get("chapter") or 0)

        for event in commit_payload.get("accepted_events") or []:
            if not isinstance(event, dict):
                continue
            text = self._event_to_text(event)
            if text:
                evt_chapter = int(event.get("chapter") or chapter)
                chunks.append({
                    "chapter": evt_chapter,
                    "scene_index": 0,
                    "content": text,
                    "chunk_type": "event",
                    "parent_chunk_id": f"ch{evt_chapter:04d}_summary",
                    "source_file": f"commit:chapter_{evt_chapter:03d}",
                })

        for delta in commit_payload.get("entity_deltas") or []:
            if not isinstance(delta, dict):
                continue
            text = self._delta_to_text(delta)
            if text:
                d_chapter = int(delta.get("chapter") or chapter)
                chunks.append({
                    "chapter": d_chapter,
                    "scene_index": 0,
                    "content": text,
                    "chunk_type": "entity_delta",
                    "parent_chunk_id": f"ch{d_chapter:04d}_summary",
                    "source_file": f"commit:chapter_{d_chapter:03d}",
                })

        return chunks

    def _event_to_text(self, event: dict) -> str:
        chapter = int(event.get("chapter") or 0)
        subject = str(event.get("subject") or "").strip()
        event_type = str(event.get("event_type") or "").strip()
        payload = event.get("payload") or {}

        if event_type == "power_breakthrough":
            new_val = str(payload.get("new") or payload.get("to") or "").strip()
            return f"第{chapter}章：{subject}突破至{new_val}" if new_val else ""
        elif event_type == "character_state_changed":
            field = str(payload.get("field") or "").strip()
            new_val = str(payload.get("new") or payload.get("to") or "").strip()
            return f"第{chapter}章：{subject}的{field}变为{new_val}" if field and new_val else ""
        elif event_type == "relationship_changed":
            to_entity = str(payload.get("to_entity") or payload.get("to") or "").strip()
            rel_type = str(
                payload.get("relationship_type") or payload.get("type") or ""
            ).strip()
            return f"第{chapter}章：{subject}与{to_entity}关系变为{rel_type}" if to_entity else ""
        elif event_type in ("world_rule_revealed", "world_rule_broken"):
            desc = str(payload.get("description") or payload.get("rule") or "").strip()
            action = "揭示" if "revealed" in event_type else "打破"
            return f"第{chapter}章：{action}世界规则——{desc}" if desc else ""
        elif event_type == "artifact_obtained":
            name = str(payload.get("name") or subject or "").strip()
            owner = str(payload.get("owner") or payload.get("holder") or "").strip()
            return f"第{chapter}章：{owner}获得{name}" if owner else f"第{chapter}章：获得{name}"
        return ""

    def _delta_to_text(self, delta: dict) -> str:
        chapter = int(delta.get("chapter") or 0)
        from_e = str(delta.get("from_entity") or "").strip()
        to_e = str(delta.get("to_entity") or "").strip()
        rel = str(delta.get("relationship_type") or "").strip()

        if from_e and to_e and rel:
            return f"第{chapter}章：{from_e}与{to_e}关系变为{rel}"

        entity_id = str(delta.get("entity_id") or "").strip()
        canonical = str(delta.get("canonical_name") or entity_id).strip()
        if entity_id:
            return f"第{chapter}章：实体变更——{canonical}"
        return ""

    def _store_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        from .config import DataModulesConfig
        from .rag_adapter import RAGAdapter

        config = DataModulesConfig.from_project_root(self.project_root)
        adapter = RAGAdapter(config)
        try:
            stored = asyncio.run(adapter.store_chunks(chunks))
            return stored
        except Exception as exc:
            logger.warning("vector_store_failed: %s", exc)
            return 0
```

- [ ] **Step 4: Register the Vector Writer in `chapter_commit_service.py`**

Add the vector writer to `apply_projections` at lines 104–109:

```python
from .vector_projection_writer import VectorProjectionWriter

writers = {
    "state": StateProjectionWriter(self.project_root),
    "index": IndexProjectionWriter(self.project_root),
    "summary": SummaryProjectionWriter(self.project_root),
    "memory": MemoryProjectionWriter(self.project_root),
    "vector": VectorProjectionWriter(self.project_root),
}
```

Also add `"vector": "pending"` to `projection_status` in `build_commit`:

```python
"projection_status": {
    "state": "pending",
    "index": "pending",
    "summary": "pending",
    "memory": "pending",
    "vector": "pending",
},
```

- [ ] **Step 5: Run Tests**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_vector_projection_writer.py -v`

Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add webnovel-writer/scripts/data_modules/vector_projection_writer.py webnovel-writer/scripts/data_modules/chapter_commit_service.py webnovel-writer/scripts/data_modules/tests/test_vector_projection_writer.py
git commit -m "feat: add vector_projection_writer for event/entity embedding"
```

---

## Task 10: Temporal Query Interfaces

**Files:**
- Create: `webnovel-writer/scripts/data_modules/knowledge_query.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_knowledge_query.py`
- Modify: `webnovel-writer/scripts/data_modules/webnovel.py` (register CLI subcommand)

- [ ] **Step 1: Write Tests**

```python
# webnovel-writer/scripts/data_modules/tests/test_knowledge_query.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KnowledgeQuery temporal-query tests."""
import json
import sqlite3
from pathlib import Path

import pytest

from data_modules.knowledge_query import KnowledgeQuery


@pytest.fixture
def setup_db(tmp_path):
    """Create a test DB with state_changes and relationship_events tables."""
    db_path = tmp_path / ".webnovel" / "index.db"
    db_path.parent.mkdir(parents=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            canonical_name TEXT,
            type TEXT DEFAULT '角色',
            current_json TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS state_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT,
            field TEXT,
            old_value TEXT,
            new_value TEXT,
            chapter INTEGER,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS relationship_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_entity TEXT,
            to_entity TEXT,
            relationship_type TEXT,
            description TEXT,
            chapter INTEGER,
            created_at TEXT
        )
    """)

    # Insert test data
    conn.execute(
        "INSERT INTO entities (id, canonical_name, current_json) VALUES (?, ?, ?)",
        ("hanli", "韩立", json.dumps({"realm": "筑基中期", "location": "乱星海"})),
    )
    conn.execute(
        "INSERT INTO state_changes (entity_id, field, old_value, new_value, chapter) VALUES (?, ?, ?, ?, ?)",
        ("hanli", "realm", "练气圆满", "筑基初期", 30),
    )
    conn.execute(
        "INSERT INTO state_changes (entity_id, field, old_value, new_value, chapter) VALUES (?, ?, ?, ?, ?)",
        ("hanli", "realm", "筑基初期", "筑基中期", 50),
    )
    conn.execute(
        "INSERT INTO relationship_events (from_entity, to_entity, relationship_type, chapter) VALUES (?, ?, ?, ?)",
        ("hanli", "陈巧倩", "同门", 20),
    )
    conn.execute(
        "INSERT INTO relationship_events (from_entity, to_entity, relationship_type, chapter) VALUES (?, ?, ?, ?)",
        ("hanli", "陈巧倩", "合作", 45),
    )
    conn.commit()
    conn.close()

    return tmp_path


def test_entity_state_at_chapter_before_first_change(setup_db):
    kq = KnowledgeQuery(setup_db)
    result = kq.entity_state_at_chapter("hanli", 10)
    # Chapter 10 precedes the first state_change, so return no changes
    assert result["entity_id"] == "hanli"
    assert result["state_at_chapter"] == {}


def test_entity_state_at_chapter_after_first_breakthrough(setup_db):
    kq = KnowledgeQuery(setup_db)
    result = kq.entity_state_at_chapter("hanli", 35)
    assert result["state_at_chapter"]["realm"] == "筑基初期"


def test_entity_state_at_chapter_after_second_breakthrough(setup_db):
    kq = KnowledgeQuery(setup_db)
    result = kq.entity_state_at_chapter("hanli", 60)
    assert result["state_at_chapter"]["realm"] == "筑基中期"


def test_relationships_at_chapter_before_any(setup_db):
    kq = KnowledgeQuery(setup_db)
    result = kq.entity_relationships_at_chapter("hanli", 10)
    assert result["relationships"] == []


def test_relationships_at_chapter_after_first(setup_db):
    kq = KnowledgeQuery(setup_db)
    result = kq.entity_relationships_at_chapter("hanli", 25)
    assert len(result["relationships"]) == 1
    assert result["relationships"][0]["to_entity"] == "陈巧倩"
    assert result["relationships"][0]["relationship_type"] == "同门"


def test_relationships_at_chapter_after_update(setup_db):
    kq = KnowledgeQuery(setup_db)
    result = kq.entity_relationships_at_chapter("hanli", 50)
    rels = result["relationships"]
    assert len(rels) == 1
    assert rels[0]["relationship_type"] == "合作"
```

- [ ] **Step 2: Run Tests and Confirm Failure**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_knowledge_query.py -v`

Expected: FAIL.

- [ ] **Step 3: Implement `knowledge_query.py`**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class KnowledgeQuery:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self._db_path = self.project_root / ".webnovel" / "index.db"

    def entity_state_at_chapter(self, entity_id: str, chapter: int) -> Dict[str, Any]:
        """Query entity state at a specified chapter, reconstructed from state_changes."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT field, new_value
                FROM state_changes
                WHERE entity_id = ? AND chapter <= ?
                ORDER BY chapter ASC, id ASC
                """,
                (entity_id, chapter),
            ).fetchall()

            state: Dict[str, str] = {}
            for row in rows:
                field = str(row["field"] or "").strip()
                if field:
                    state[field] = str(row["new_value"] or "").strip()

            return {
                "entity_id": entity_id,
                "at_chapter": chapter,
                "state_at_chapter": state,
            }
        finally:
            conn.close()

    def entity_relationships_at_chapter(self, entity_id: str, chapter: int) -> Dict[str, Any]:
        """Query all entity relationships at a specified chapter using a relationship_events snapshot."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT from_entity, to_entity, relationship_type, description, chapter
                FROM relationship_events
                WHERE (from_entity = ? OR to_entity = ?) AND chapter <= ?
                ORDER BY chapter ASC, id ASC
                """,
                (entity_id, entity_id, chapter),
            ).fetchall()

            # Replace old relationships with the latest ones; deduplicate by pair
            latest: Dict[str, Dict[str, Any]] = {}
            for row in rows:
                from_e = str(row["from_entity"] or "").strip()
                to_e = str(row["to_entity"] or "").strip()
                pair_key = tuple(sorted([from_e, to_e]))
                latest[str(pair_key)] = {
                    "from_entity": from_e,
                    "to_entity": to_e,
                    "relationship_type": str(row["relationship_type"] or "").strip(),
                    "description": str(row["description"] or "").strip(),
                    "since_chapter": int(row["chapter"] or 0),
                }

            return {
                "entity_id": entity_id,
                "at_chapter": chapter,
                "relationships": list(latest.values()),
            }
        finally:
            conn.close()
```

- [ ] **Step 4: Run Tests**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_knowledge_query.py -v`

Expected: All PASS.

- [ ] **Step 5: Register the `knowledge` CLI Subcommand**

Register `knowledge` in `webnovel-writer/scripts/data_modules/webnovel.py`. Find subparser registration with grep `add_parser`, then add:

```python
# knowledge subcommand
knowledge_parser = subparsers.add_parser("knowledge", help="时序知识查询")
knowledge_sub = knowledge_parser.add_subparsers(dest="knowledge_action")

qs_parser = knowledge_sub.add_parser("query-entity-state", help="查询实体在指定章节的状态")
qs_parser.add_argument("--entity", required=True, help="实体 ID")
qs_parser.add_argument("--at-chapter", type=int, required=True, help="目标章节号")

qr_parser = knowledge_sub.add_parser("query-relationships", help="查询实体在指定章节的关系")
qr_parser.add_argument("--entity", required=True, help="实体 ID")
qr_parser.add_argument("--at-chapter", type=int, required=True, help="目标章节号")
```

Add a handler in command dispatch:

```python
if args.command == "knowledge":
    from .knowledge_query import KnowledgeQuery
    kq = KnowledgeQuery(project_root)
    if args.knowledge_action == "query-entity-state":
        result = kq.entity_state_at_chapter(args.entity, args.at_chapter)
        print_success(result, message="entity_state_at_chapter")
    elif args.knowledge_action == "query-relationships":
        result = kq.entity_relationships_at_chapter(args.entity, args.at_chapter)
        print_success(result, message="entity_relationships_at_chapter")
```

- [ ] **Step 6: Synchronize `REGISTERED_CLI_SUBCOMMANDS` and `context-agent.md`**

Add `"knowledge"` to `REGISTERED_CLI_SUBCOMMANDS` in `test_prompt_integrity.py` at lines 32–38:

```python
REGISTERED_CLI_SUBCOMMANDS = {
    "where", "preflight", "use",
    "index", "state", "rag", "style", "entity", "context", "memory",
    "migrate", "status", "update-state", "backup", "archive",
    "init", "extract-context", "memory-contract", "review-pipeline",
    "story-system", "chapter-commit", "story-events",
    "knowledge",
}
```

Add to the supplementary-commands section in `context-agent.md` Section 2:

```bash
# Temporal knowledge queries: entity state and relationships at a specified chapter
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "{project_root}" knowledge query-entity-state --entity "{entity_id}" --at-chapter {N}
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "{project_root}" knowledge query-relationships --entity "{entity_id}" --at-chapter {N}
```

- [ ] **Step 7: Run All Tests**

Run: `cd webnovel-writer && python -m pytest scripts/data_modules/tests/ scripts/tests/ -v --timeout=60`

Expected: All PASS.

- [ ] **Step 8: Commit**

```bash
git add webnovel-writer/scripts/data_modules/knowledge_query.py webnovel-writer/scripts/data_modules/tests/test_knowledge_query.py webnovel-writer/scripts/data_modules/webnovel.py webnovel-writer/agents/context-agent.md webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py
git commit -m "feat: add knowledge_query temporal API with CLI and prompt sync"
```

---

## Task 11: Final Integration Validation

**Files:** (read-only verification)

- [ ] **Step 1: Run the Full Test Suite**

```bash
cd webnovel-writer && python -m pytest scripts/data_modules/tests/ scripts/tests/ -v --timeout=120
```

Expected: All PASS, 0 FAIL.

- [ ] **Step 2: Use grep to Verify No Scattered Writes Remain**

```bash
grep -rn "state set-chapter-status" webnovel-writer/skills/ webnovel-writer/agents/ || echo "CLEAN"
grep -rn "index process-chapter" webnovel-writer/skills/ webnovel-writer/agents/ || echo "CLEAN"
```

Expected: Both output `CLEAN`.

- [ ] **Step 3: Check context_manager.py Line Count**

```bash
wc -l webnovel-writer/scripts/data_modules/context_manager.py
```

Expected: < 400 lines.

- [ ] **Step 4: Confirm snapshot_manager.py Is Deleted**

```bash
test -f webnovel-writer/scripts/data_modules/snapshot_manager.py && echo "STILL EXISTS" || echo "DELETED"
```

Expected: `DELETED`.

- [ ] **Step 5: Confirm the Reasoning Table Covers Seven Genres**

```bash
python3 -c "
import csv
from pathlib import Path
path = Path('webnovel-writer/references/csv/裁决规则.csv')
with open(path, 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
genres = [r['题材'] for r in rows]
print(f'题材数: {len(genres)}')
print(f'题材: {genres}')
assert len(genres) == 7
"
```

Expected: Seven genres.

- [ ] **Step 6: Confirm CSV_CONFIG Alignment**

```bash
cd webnovel-writer && python -m pytest scripts/data_modules/tests/test_csv_config.py -v
```

Expected: All PASS.

- [ ] **Step 7: Commit final**

If any fixes are needed, commit them:

```bash
git add -A
git commit -m "chore: final integration fixes for story system convergence"
```
