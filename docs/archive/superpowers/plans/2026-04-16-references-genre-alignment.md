# References Genre Alignment and Structural Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish authoritative genre enums, aligning the CSV `适用题材` column, routing table, reasoning table, and search script to one set of values; fill validation-script and structural gaps.

**Architecture:** A two-layer genre system (15 canonical_genre + 37 platform_tag values) drives the entire pipeline. `genre-canonical.md` is the human-readable source of truth; Python constant `GENRE_CANONICAL` is the machine-readable source. `validate_csv.py` checks consistency between both and actual CSV data. Changes are limited to `references/csv/`, `scripts/reference_search.py`, `scripts/validate_csv.py`, and `scripts/data_modules/story_system_engine.py`; do not change skill prose or contract output structures.

**Tech Stack:** Python 3.10+, pytest, csv (stdlib)

**Spec:** `docs/superpowers/specs/2026-04-16-references-completion-spec.md`
**Genre Canonical:** `webnovel-writer/references/csv/genre-canonical.md`

**Status:** Completed. The reference canonical pipeline is implemented, route/reasoning CSVs meet Phase 2 thresholds, and `validate_csv.py --format json` reports 0 errors / 0 warnings.

---

### Task 1: Add GENRE_CANONICAL constants and mappings to reference_search.py

**Files:**
- Modify: `webnovel-writer/scripts/reference_search.py:84-154`
- Test: `webnovel-writer/scripts/tests/test_reference_search.py`

- [ ] **Step 1: Write failing tests: canonical constants exist and are complete**

Append to `webnovel-writer/scripts/tests/test_reference_search.py`:

```python
class TestGenreCanonical:
    def test_canonical_genres_has_15_entries(self):
        from reference_search import GENRE_CANONICAL
        assert len(GENRE_CANONICAL) == 15
        expected = {
            "都市", "玄幻", "仙侠", "奇幻", "科幻",
            "历史", "悬疑", "游戏", "古言", "现言",
            "幻言", "年代", "种田", "快穿", "衍生",
        }
        assert GENRE_CANONICAL == expected

    def test_platform_to_canonical_maps_all_37_tags(self):
        from reference_search import PLATFORM_TO_CANONICAL
        assert len(PLATFORM_TO_CANONICAL) == 37
        # Every value must be a canonical genre
        from reference_search import GENRE_CANONICAL
        for tag, canonical in PLATFORM_TO_CANONICAL.items():
            assert canonical in GENRE_CANONICAL, f"{tag} -> {canonical} not in GENRE_CANONICAL"

    def test_platform_to_canonical_spot_checks(self):
        from reference_search import PLATFORM_TO_CANONICAL
        assert PLATFORM_TO_CANONICAL["都市日常"] == "都市"
        assert PLATFORM_TO_CANONICAL["战神赘婿"] == "都市"
        assert PLATFORM_TO_CANONICAL["东方仙侠"] == "仙侠"
        assert PLATFORM_TO_CANONICAL["西方奇幻"] == "奇幻"
        assert PLATFORM_TO_CANONICAL["古风世情"] == "古言"
        assert PLATFORM_TO_CANONICAL["豪门总裁"] == "现言"
        assert PLATFORM_TO_CANONICAL["快穿"] == "快穿"
        assert PLATFORM_TO_CANONICAL["科幻末世"] == "科幻"
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/test_reference_search.py::TestGenreCanonical -v`
Expected: FAIL — `ImportError: cannot import name 'GENRE_CANONICAL'`

- [ ] **Step 3: Add constants to reference_search.py**

Insert before `CSV_CONFIG` in `reference_search.py` (around line 84):

```python
# ---------------------------------------------------------------------------
# Genre canonical list & platform tag mapping
# ---------------------------------------------------------------------------

GENRE_CANONICAL: set[str] = {
    "都市", "玄幻", "仙侠", "奇幻", "科幻",
    "历史", "悬疑", "游戏", "古言", "现言",
    "幻言", "年代", "种田", "快穿", "衍生",
}

PLATFORM_TO_CANONICAL: Dict[str, str] = {
    # Male-oriented categories
    "都市日常": "都市", "都市修真": "都市", "都市高武": "都市",
    "战神赘婿": "都市", "都市种田": "都市", "都市脑洞": "都市",
    "传统玄幻": "玄幻", "玄幻脑洞": "玄幻",
    "东方仙侠": "仙侠",
    "西方奇幻": "奇幻",
    "科幻末世": "科幻",
    "历史古代": "历史", "历史脑洞": "历史", "抗战谍战": "历史",
    "悬疑脑洞": "悬疑", "悬疑灵异": "悬疑",
    "游戏体育": "游戏",
    "动漫衍生": "衍生", "男频衍生": "衍生",
    # Female-oriented categories
    "古风世情": "古言", "宫斗宅斗": "古言", "古言脑洞": "古言",
    "现言脑洞": "现言", "青春甜宠": "现言", "星光璀璨": "现言",
    "职场婚恋": "现言", "豪门总裁": "现言",
    "玄幻言情": "幻言",
    "年代": "年代", "民国言情": "年代",
    "种田": "种田",
    "快穿": "快穿",
    "女频悬疑": "悬疑",
    "女频衍生": "衍生",
}

# Legacy values that appeared in old CSV data → canonical mapping.
# Used by _resolve_genre() during the migration period.
_LEGACY_GENRE_MAP: Dict[str, str] = {
    "东方仙侠": "仙侠", "西方奇幻": "奇幻", "科幻末世": "科幻",
    "都市日常": "都市", "都市修真": "都市", "都市高武": "都市",
    "历史古代": "历史",
    "谍战": "历史", "军事": "历史", "武侠": "历史",
    "刑侦": "悬疑", "惊悚": "悬疑", "推理": "悬疑", "规则怪谈": "悬疑",
    "末世": "科幻", "赛博朋克": "科幻",
    "网游": "游戏", "电竞": "游戏", "竞技": "游戏", "体育": "游戏",
    "轻小说": "衍生", "同人": "衍生",
    "校园": "现言", "青春": "现言", "娱乐圈": "现言", "职场": "现言",
    "高武": "都市",
}


def resolve_genre(genre: Optional[str]) -> Optional[str]:
    """Resolve a user-facing genre string to its canonical form.

    Accepts canonical genres, platform tags, and legacy values.
    Returns the canonical genre string, or the original input if unresolvable.
    """
    if genre is None:
        return None
    g = genre.strip()
    if g in GENRE_CANONICAL or g == "全部":
        return g
    if g in PLATFORM_TO_CANONICAL:
        return PLATFORM_TO_CANONICAL[g]
    if g in _LEGACY_GENRE_MAP:
        return _LEGACY_GENRE_MAP[g]
    return g  # unresolvable — pass through
```

- [ ] **Step 4: Run tests to confirm success**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/test_reference_search.py::TestGenreCanonical -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/scripts/reference_search.py webnovel-writer/scripts/tests/test_reference_search.py
git commit -m "feat: add GENRE_CANONICAL constants and resolve_genre() to reference_search"
```

---

### Task 2: Use resolve_genre in _genre_matches and search()

**Files:**
- Modify: `webnovel-writer/scripts/reference_search.py:74-82, 294-335`
- Test: `webnovel-writer/scripts/tests/test_reference_search.py`

- [ ] **Step 1: Write failing tests: platform_tag supplied as --genre matches canonical values**

Append to `TestGenreCanonical` in `test_reference_search.py`:

```python
    def test_resolve_genre_canonical_passthrough(self):
        from reference_search import resolve_genre
        assert resolve_genre("都市") == "都市"
        assert resolve_genre("全部") == "全部"
        assert resolve_genre(None) is None

    def test_resolve_genre_platform_tag(self):
        from reference_search import resolve_genre
        assert resolve_genre("都市日常") == "都市"
        assert resolve_genre("战神赘婿") == "都市"
        assert resolve_genre("古风世情") == "古言"

    def test_resolve_genre_legacy(self):
        from reference_search import resolve_genre
        assert resolve_genre("武侠") == "历史"
        assert resolve_genre("刑侦") == "悬疑"
        assert resolve_genre("网游") == "游戏"

    def test_search_with_platform_tag_genre(self):
        """--genre 都市日常 should match rows with 适用题材=都市."""
        out = run_search(
            "--skill", "write",
            "--table", "命名规则",
            "--query", "角色命名",
            "--genre", "都市日常",
        )
        assert out["status"] == "success"
        # Should find results (都市日常 resolves to 都市, matching rows tagged 都市)
        assert out["data"]["total"] >= 0  # may be 0 if no 都市 rows, but no error
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/test_reference_search.py::TestGenreCanonical::test_search_with_platform_tag_genre -v`
Expected: May PASS because `都市日常` contains the substring `都市`, or may match imprecisely. The three `resolve_genre` tests are the key checks.

- [ ] **Step 3: Modify _genre_matches and search**

Modify `_genre_matches` in `reference_search.py` (around line 74):

```python
def _genre_matches(row: Dict[str, str], genre: Optional[str]) -> bool:
    """Return True if *genre* is None, or matches ``适用题材`` (``全部`` always matches).

    Both the input *genre* and the cell values are resolved to canonical form
    before comparison, so platform tags and legacy values work transparently.
    """
    if genre is None:
        return True
    cell = row.get("适用题材", "")
    if cell.strip() == "全部":
        return True
    resolved_genre = resolve_genre(genre)
    cell_genres = [resolve_genre(v) for v in _split_multi_value(cell)]
    return resolved_genre in cell_genres
```

Modify `search` (around line 294), resolving genre at the start:

```python
def search(
    csv_dir: Path,
    skill: str,
    query: str,
    table: Optional[str] = None,
    genre: Optional[str] = None,
    max_results: int = 5,
) -> Dict[str, Any]:
    resolved = resolve_genre(genre)
    # ... rest of function uses resolved instead of genre for filtering,
    # but keeps original genre in the response envelope for traceability
```

Specifically, add `resolved = resolve_genre(genre)` as the first statement in `search()`, then replace `_genre_matches(row, genre)` with `_genre_matches(row, resolved)`. Retain `"genre": genre` in output for traceability to the original input.

- [ ] **Step 4: Run all tests to confirm success**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/test_reference_search.py -v`
Expected: ALL PASS (including existing tests to prevent regressions)

- [ ] **Step 5: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/scripts/reference_search.py webnovel-writer/scripts/tests/test_reference_search.py
git commit -m "feat: _genre_matches resolves platform tags and legacy values to canonical"
```

---

### Task 3: Add prefix and required_cols fields to CSV_CONFIG

**Files:**
- Modify: `webnovel-writer/scripts/reference_search.py:88-154`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_csv_config.py`

- [ ] **Step 1: Write failing tests: every CSV_CONFIG entry has prefix and required_cols**

Append to `test_csv_config.py`:

```python
def test_csv_config_has_prefix_field():
    for name, config in CSV_CONFIG.items():
        assert "prefix" in config, f"表 {name} 缺少 prefix 字段"
        assert isinstance(config["prefix"], str)
        assert len(config["prefix"]) >= 2


def test_csv_config_has_required_cols_field():
    for name, config in CSV_CONFIG.items():
        assert "required_cols" in config, f"表 {name} 缺少 required_cols 字段"
        assert isinstance(config["required_cols"], list)
        assert len(config["required_cols"]) >= 1


def test_csv_config_prefix_matches_actual_data():
    """Every row's 编号 must start with the declared prefix."""
    for name, config in CSV_CONFIG.items():
        csv_path = CSV_DIR / config["file"]
        if not csv_path.exists():
            continue
        prefix = config["prefix"]
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                row_id = row.get("编号", "")
                assert row_id.startswith(prefix + "-"), (
                    f"表 {name} 行 {row_id} 编号不以 {prefix}- 开头"
                )
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest data_modules/tests/test_csv_config.py -v`
Expected: FAIL — `KeyError: 'prefix'`

- [ ] **Step 3: Add prefix and required_cols to every CSV_CONFIG entry**

Modify `CSV_CONFIG` in `reference_search.py`, adding two fields per table:

```python
CSV_CONFIG: Dict[str, Dict[str, Any]] = {
    "命名规则": {
        "file": "命名规则.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "命名对象", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "base",
        "prefix": "NR",
        "required_cols": ["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要"],
    },
    "场景写法": {
        "file": "场景写法.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "模式名称", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "base",
        "prefix": "SP",
        "required_cols": ["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要"],
    },
    "写作技法": {
        "file": "写作技法.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "技法名称", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "base",
        "prefix": "WT",
        "required_cols": ["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要"],
    },
    "桥段套路": {
        "file": "桥段套路.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "桥段名称", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "dynamic",
        "prefix": "TR",
        "required_cols": ["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要"],
    },
    "爽点与节奏": {
        "file": "爽点与节奏.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "节奏类型", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "dynamic",
        "prefix": "PA",
        "required_cols": ["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要"],
    },
    "人设与关系": {
        "file": "人设与关系.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "人设类型", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "base",
        "prefix": "CH",
        "required_cols": ["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要"],
    },
    "金手指与设定": {
        "file": "金手指与设定.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "核心摘要": 2},
        "output_cols": ["编号", "设定类型", "核心摘要", "大模型指令", "详细展开"],
        "poison_col": "毒点",
        "role": "base",
        "prefix": "SY",
        "required_cols": ["编号", "适用技能", "分类", "层级", "关键词", "适用题材", "核心摘要"],
    },
    "题材与调性推理": {
        "file": "题材与调性推理.csv",
        "search_cols": {"关键词": 3, "意图与同义词": 4, "题材别名": 3},
        "output_cols": ["编号", "题材/流派", "核心调性", "推荐基础检索表", "推荐动态检索表"],
        "poison_col": "毒点",
        "role": "route",
        "prefix": "GR",
        "required_cols": ["编号", "适用技能", "题材/流派", "核心调性", "推荐基础检索表", "推荐动态检索表"],
    },
    "裁决规则": {
        "file": "裁决规则.csv",
        "search_cols": {"题材": 4},
        "output_cols": ["题材", "风格优先级", "爽点优先级", "节奏默认策略",
                        "毒点权重", "冲突裁决", "contract注入层", "反模式"],
        "poison_col": "",
        "role": "reasoning",
        "prefix": "RS",
        "required_cols": ["编号", "题材", "风格优先级", "爽点优先级", "节奏默认策略", "冲突裁决"],
    },
}
```

- [ ] **Step 4: Run tests to confirm success**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest data_modules/tests/test_csv_config.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/scripts/reference_search.py webnovel-writer/scripts/data_modules/tests/test_csv_config.py
git commit -m "feat: add prefix and required_cols to CSV_CONFIG"
```

---

### Task 4: Create the validate_csv.py validation script

**Files:**
- Create: `webnovel-writer/scripts/validate_csv.py`
- Create: `webnovel-writer/scripts/tests/test_validate_csv.py`

- [ ] **Step 1: Write failing tests: validate_csv imports and runs**

Create `webnovel-writer/scripts/tests/test_validate_csv.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for validate_csv.py."""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).resolve().parents[1] / "validate_csv.py")
CSV_DIR = str(Path(__file__).resolve().parents[2] / "references" / "csv")


def run_validate(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, SCRIPT, "--csv-dir", CSV_DIR, *args],
        capture_output=True,
        text=True,
    )


class TestValidateCsvRuns:
    def test_script_runs_without_crash(self):
        result = run_validate()
        # May exit 0 (all pass) or 1 (errors found), but must not crash
        assert result.returncode in (0, 1)
        assert "Traceback" not in result.stderr

    def test_json_output_mode(self):
        import json
        result = run_validate("--format", "json")
        assert result.returncode in (0, 1)
        data = json.loads(result.stdout)
        assert "errors" in data
        assert "warnings" in data
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/test_validate_csv.py -v`
Expected: FAIL — script not found

- [ ] **Step 3: Implement validate_csv.py**

Create `webnovel-writer/scripts/validate_csv.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV data validation tool.

Validate data quality in all references/csv/ tables using CSV_CONFIG and GENRE_CANONICAL.

Usage:
    python validate_csv.py
    python validate_csv.py --csv-dir path/to/csv
    python validate_csv.py --format json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import config from sibling module
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_search import (
    CSV_CONFIG,
    GENRE_CANONICAL,
    PLATFORM_TO_CANONICAL,
    _LEGACY_GENRE_MAP,
)

_MULTI_SPLIT = re.compile(r"[|,，]+")
_CHINESE_COMMA = re.compile(r"，")


def _split(cell: str) -> List[str]:
    if not cell:
        return []
    return [p.strip() for p in _MULTI_SPLIT.split(cell) if p.strip()]


def _load_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _default_csv_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "csv"


def validate(csv_dir: Path) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    all_ids: Dict[str, str] = {}  # id -> table_name

    valid_genres = GENRE_CANONICAL | {"全部"}

    for table_name, config in CSV_CONFIG.items():
        csv_path = csv_dir / config["file"]
        if not csv_path.exists():
            errors.append(f"[{table_name}] 文件不存在: {config['file']}")
            continue

        rows = _load_csv(csv_path)
        headers = set(rows[0].keys()) if rows else set()
        prefix = config.get("prefix", "")
        required_cols = config.get("required_cols", [])

        # Check: column headers include all declared columns
        declared_cols = set()
        for col in config.get("search_cols", {}):
            declared_cols.add(col)
        for col in config.get("output_cols", []):
            declared_cols.add(col)
        for col in required_cols:
            declared_cols.add(col)
        poison = config.get("poison_col", "")
        if poison:
            declared_cols.add(poison)
        missing_headers = declared_cols - headers
        if missing_headers:
            errors.append(f"[{table_name}] CSV 缺少列头: {missing_headers}")

        for i, row in enumerate(rows, start=2):  # row 1 is header
            row_id = row.get("编号", "").strip()

            # Check: ID uniqueness
            if row_id:
                if row_id in all_ids:
                    errors.append(
                        f"[{table_name}] 行{i} 编号 {row_id} 重复（首次出现于 {all_ids[row_id]}）"
                    )
                else:
                    all_ids[row_id] = table_name

            # Check: prefix consistency
            if prefix and row_id and not row_id.startswith(prefix + "-"):
                errors.append(
                    f"[{table_name}] 行{i} 编号 {row_id} 应以 {prefix}- 开头"
                )

            # Check: required columns non-empty
            for col in required_cols:
                val = row.get(col, "").strip()
                if not val:
                    errors.append(f"[{table_name}] 行{i} ({row_id}) 必填列 {col} 为空")

            # Check: delimiter convention (no Chinese comma in multi-value fields)
            for col in ("适用技能", "关键词", "意图与同义词", "适用题材"):
                val = row.get(col, "")
                if _CHINESE_COMMA.search(val):
                    errors.append(
                        f"[{table_name}] 行{i} ({row_id}) {col} 含中文逗号，应使用 |"
                    )

            # Check: 适用题材 values in canonical set
            genre_cell = row.get("适用题材", "").strip()
            if genre_cell:
                for g in _split(genre_cell):
                    if g not in valid_genres:
                        warnings.append(
                            f"[{table_name}] 行{i} ({row_id}) 适用题材值 '{g}' "
                            f"不在 canonical 枚举中"
                        )

    # Cross-table check: route ↔ reasoning coverage
    route_genres: set[str] = set()
    reasoning_genres: set[str] = set()

    route_path = csv_dir / "题材与调性推理.csv"
    if route_path.exists():
        for row in _load_csv(route_path):
            val = row.get("题材/流派", "").strip()
            if val:
                route_genres.add(val)

    reasoning_path = csv_dir / "裁决规则.csv"
    if reasoning_path.exists():
        for row in _load_csv(reasoning_path):
            val = row.get("题材", "").strip()
            if val:
                reasoning_genres.add(val)

    # Every canonical genre should have at least one reasoning row
    for cg in GENRE_CANONICAL:
        if cg not in reasoning_genres:
            warnings.append(f"[裁决规则] canonical genre '{cg}' 无对应裁决行")

    return {"errors": errors, "warnings": warnings}


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Validate reference CSV files")
    parser.add_argument("--csv-dir", default=None, help="Override CSV directory")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    csv_dir = Path(args.csv_dir) if args.csv_dir else _default_csv_dir()
    result = validate(csv_dir)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for e in result["errors"]:
            print(f"ERROR: {e}")
        for w in result["warnings"]:
            print(f"WARN:  {w}")
        total_e = len(result["errors"])
        total_w = len(result["warnings"])
        print(f"\n--- {total_e} error(s), {total_w} warning(s) ---")

    sys.exit(1 if result["errors"] else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to confirm success**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/test_validate_csv.py -v`
Expected: 2 tests PASS

- [ ] **Step 5: Run validator, inspect actual output, and record current warning count**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python validate_csv.py`
Expected: 0 errors (valid structure), multiple warnings (noncanonical `适用题材` values + missing canonical coverage in reasoning rules)

- [ ] **Step 6: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/scripts/validate_csv.py webnovel-writer/scripts/tests/test_validate_csv.py
git commit -m "feat: add validate_csv.py — schema, ID, prefix, genre, delimiter checks"
```

---

### Task 5: Add canonical_genre column to 题材与调性推理.csv

**Files:**
- Modify: `webnovel-writer/references/csv/题材与调性推理.csv`
- Modify: `webnovel-writer/scripts/reference_search.py` (CSV_CONFIG for 题材与调性推理)
- Modify: `webnovel-writer/scripts/data_modules/story_system_engine.py:115-159`

- [ ] **Step 1: Write failing test: engine route output includes canonical_genre**

Find or create `test_story_system_engine.py` under `webnovel-writer/scripts/data_modules/tests/`, then append:

```python
def test_route_output_includes_canonical_genre(tmp_path):
    """_route() output must contain canonical_genre in meta."""
    # Copy CSV dir to tmp
    import shutil
    csv_src = Path(__file__).resolve().parent.parent.parent.parent / "references" / "csv"
    csv_dst = tmp_path / "csv"
    shutil.copytree(csv_src, csv_dst)

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from data_modules.story_system_engine import StorySystemEngine

    engine = StorySystemEngine(csv_dir=csv_dst)
    route = engine._route("退婚流 三年之约", "玄幻")
    assert "canonical_genre" in route["meta"]
    assert route["meta"]["canonical_genre"] in {
        "都市", "玄幻", "仙侠", "奇幻", "科幻",
        "历史", "悬疑", "游戏", "古言", "现言",
        "幻言", "年代", "种田", "快穿", "衍生",
    }
```

- [ ] **Step 2: Run tests to confirm failure**

Expected: FAIL — `KeyError: 'canonical_genre'`

- [ ] **Step 3: Modify CSV and code**

**3a.** Add `canonical_genre` after `题材/流派` in `题材与调性推理.csv`. Manually fill the corresponding canonical value for every row. Example:

| 编号 | 题材/流派 | canonical_genre | ... |
|------|----------|----------------|-----|
| GR-001 | 玄幻退婚流 | 玄幻 | ... |
| GR-002 | 规则动物园 | 悬疑 | ... |

All eight current rows need `canonical_genre`.

**3b.** In `reference_search.py`, add `"canonical_genre"` to `output_cols` in `CSV_CONFIG["题材与调性推理"]`:

```python
"题材与调性推理": {
    "file": "题材与调性推理.csv",
    "search_cols": {"关键词": 3, "意图与同义词": 4, "题材别名": 3},
    "output_cols": ["编号", "题材/流派", "canonical_genre", "核心调性", "推荐基础检索表", "推荐动态检索表"],
    "poison_col": "毒点",
    "role": "route",
    "prefix": "GR",
    "required_cols": ["编号", "适用技能", "题材/流派", "canonical_genre", "核心调性", "推荐基础检索表", "推荐动态检索表"],
},
```

**3c.** Modify `_route` in `story_system_engine.py` (around lines 141–158), adding `canonical_genre` to returned `meta`:

```python
        primary_genre = str(matched.get("题材/流派") or genre or "").strip()
        canonical = str(matched.get("canonical_genre") or "").strip()
        if not canonical:
            # Fallback: resolve via PLATFORM_TO_CANONICAL
            from reference_search import resolve_genre
            canonical = resolve_genre(primary_genre) or primary_genre
        genre_filter = canonical  # Use canonical for downstream filtering
        return {
            "meta": {
                "primary_genre": primary_genre,
                "canonical_genre": canonical,
                "route_source": route_source,
                "genre_filter": genre_filter,
                ...
            },
            ...
            "genre_filter": genre_filter,
            ...
        }
```

- [ ] **Step 4: Run tests to confirm success**

Run the new test + existing engine tests (if any).

- [ ] **Step 5: Also change _load_reasoning to use canonical_genre**

Modify `_load_reasoning` in `story_system_engine.py` (around lines 261–276): engine `build()` should pass `canonical_genre`, not `primary_genre`, so reasoning rules match canonical values.

Find `_load_reasoning` in `build()` and change the argument from `route["meta"]["primary_genre"]` to `route["meta"]["canonical_genre"]`.

- [ ] **Step 6: Run all related tests**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/ data_modules/tests/test_csv_config.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/references/csv/题材与调性推理.csv webnovel-writer/scripts/reference_search.py webnovel-writer/scripts/data_modules/story_system_engine.py
git commit -m "feat: add canonical_genre column to route table, thread through engine"
```

---

### Task 6: Migrate existing CSV 适用题材 columns to canonical enums

**Files:**
- Modify: `webnovel-writer/references/csv/命名规则.csv`
- Modify: `webnovel-writer/references/csv/场景写法.csv`
- Modify: `webnovel-writer/references/csv/写作技法.csv`
- Modify: `webnovel-writer/references/csv/桥段套路.csv`
- Modify: `webnovel-writer/references/csv/人设与关系.csv`
- Modify: `webnovel-writer/references/csv/爽点与节奏.csv`
- Modify: `webnovel-writer/references/csv/金手指与设定.csv`
- Modify: `webnovel-writer/references/csv/裁决规则.csv`

**Note: this is manual data editing. Inspect every CSV row’s `适用题材` field and replace noncanonical values with canonical enums.**

- [ ] **Step 1: Run validate_csv.py for the complete warning list**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python validate_csv.py --format json > /tmp/csv_warnings.json`

This outputs all warnings that applicable-genre values are outside the canonical enum, forming the migration checklist.

- [ ] **Step 2: Edit each file using the migration mapping**

Open each CSV and apply the existing non-enum value migration mapping in `genre-canonical.md`:

Migration rules:
- `谍战` → `历史`
- `刑侦|惊悚|推理|规则怪谈` → `悬疑`
- `末世|赛博朋克` → `科幻`
- `军事|武侠` → `历史`
- `网游|电竞|竞技|体育` → `游戏`
- `高武` → `都市`
- `系统文|无限流` → use the actual setting genre (`玄幻`/`都市`/`悬疑`)
- `狗血|爽文|深度剧情|现实向|群像|史诗` → remove that value; use a specific applicable genre or `全部`
- `动作|心理|战争|灾难|长篇|知乎短篇` → remove that value; use a specific applicable genre or `全部`
- `校园|青春|娱乐圈|职场` → `现言`
- `商战|商业` → `都市` or `现言`
- `同人|轻小说` → `衍生`

Save each modified file, preserving UTF-8 with BOM.

- [ ] **Step 3: Run validate_csv.py; confirm zero or substantially fewer warnings**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python validate_csv.py`
Expected: 0 errors, zero `适用题材` warnings (only reasoning-coverage warnings remain)

- [ ] **Step 4: Run existing search tests to check regressions**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/test_reference_search.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/references/csv/*.csv
git commit -m "refactor: migrate all CSV 适用题材 values to canonical genre enum"
```

---

### Task 7: Update the CSV README genre section

**Files:**
- Modify: `webnovel-writer/references/csv/README.md:166-170`

- [ ] **Step 1: Replace old Fanqie classification with the canonical enum reference**

Replace the old classification at README.md lines 166–170:

```markdown
## Applicable genres (Fanqie classification)

**Male-oriented:** 都市、玄幻、仙侠、奇幻、武侠、历史、军事、科幻、悬疑、游戏、体育、轻小说

**Female-oriented:** 现言、古言、幻言、悬疑、轻小说
```

With:

````markdown
## Applicable genre enum

The `适用题材` column accepts only these 15 canonical values or `全部`:

```
都市  玄幻  仙侠  奇幻  科幻
历史  悬疑  游戏  古言  现言
幻言  年代  种田  快穿  衍生
```

See `genre-canonical.md` for the complete two-layer system (canonical + Fanqie platform_tag mappings).

**Do not** put these in `适用题材`:
- Fanqie subcategories (e.g. `都市日常`, `战神赘婿`): these are platform_tag values used only in routing tables
- Trope names (e.g. `退婚流`, `系统流`): these belong in `桥段套路.csv`
- Tone/scene/format labels (e.g. `爽文`, `动作`, `短篇`): these are not genres
````

- [ ] **Step 2: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/references/csv/README.md
git commit -m "docs: update CSV README genre section to reference canonical enum"
```

---

### Task 8: Create top-level references/README.md index

**Files:**
- Create: `webnovel-writer/references/README.md`

- [ ] **Step 1: Create file**

````markdown
# References

This directory contains all webnovel-writer references, read by skills and scripts at runtime.

## Directory structure

| Directory/file | Responsibility | Consumption |
|-------------|------|----------|
| `csv/` | Structured knowledge entries (nine tables) | `reference_search.py` BM25 retrieval |
| `csv/README.md` | CSV schemas and entry rules | Human reference |
| `csv/genre-canonical.md` | Authoritative genre enum (canonical + platform_tag mapping) | Human reference + comparison with code constants |
| `genre-profiles.md` | Genre profiles (fallback; common genres moved to Story Contracts) | ContextManager direct Read |
| `reading-power-taxonomy.md` | Reader-retention taxonomy | Skills direct Read |
| `review-schema.md` | Review output format | webnovel-review Read |
| `index/` | Metadata indexes (loading-map, gap-register) | Human reference |
| `outlining/` | Outline references | webnovel-plan Read |
| `review/` | Review references | webnovel-review Read |
| `shared/` | Cross-skill shared references | Multiple skills Read |

## Markdown vs. CSV boundary

- **Markdown**: workflow standards, methodology, review schemas, hard constraints, polishing guidance
- **CSV**: itemized writing knowledge, naming rules, scene techniques, plot templates

Markdown provides behavioral gates for the model; CSV provides a knowledge base for search.

## Consumption pipeline

See `index/reference-loading-map.md` for the full init → plan → write → review reference-consumption path.

## Validation

```bash
cd webnovel-writer/scripts
python validate_csv.py          # Text output
python validate_csv.py --format json  # JSON output
```
````

- [ ] **Step 2: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/references/README.md
git commit -m "docs: add top-level references/README.md directory index"
```

---

### Task 9: End-to-end smoke tests

**Files:**
- Test: `webnovel-writer/scripts/tests/test_reference_search.py`

- [ ] **Step 1: Add end-to-end smoke tests**

Append to `test_reference_search.py`:

```python
class TestEndToEndSmoke:
    """Smoke tests: full pipeline from search to result, across genres."""

    def test_xuanhuan_genre_returns_results(self):
        out = run_search("--skill", "write", "--query", "升级打脸", "--genre", "玄幻")
        assert out["status"] == "success"
        assert out["data"]["total"] >= 1

    def test_guyan_genre_returns_results(self):
        out = run_search("--skill", "write", "--query", "宫斗 嫡庶", "--genre", "古言")
        assert out["status"] == "success"
        # May be 0 if no 古言 rows exist yet, but must not error
        assert isinstance(out["data"]["results"], list)

    def test_platform_tag_as_genre(self):
        """Using a platform_tag like 都市日常 should work as --genre."""
        out = run_search("--skill", "write", "--query", "日常搞笑", "--genre", "都市日常")
        assert out["status"] == "success"
        assert isinstance(out["data"]["results"], list)

    def test_validate_csv_zero_errors(self):
        """validate_csv.py must report 0 errors on current data."""
        import subprocess
        validate_script = str(Path(__file__).resolve().parents[1] / "validate_csv.py")
        result = subprocess.run(
            [sys.executable, validate_script, "--csv-dir", CSV_DIR, "--format", "json"],
            capture_output=True, text=True,
        )
        import json
        data = json.loads(result.stdout)
        assert len(data["errors"]) == 0, f"CSV validation errors: {data['errors']}"
```

- [ ] **Step 2: Run all tests**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/test_reference_search.py tests/test_validate_csv.py data_modules/tests/test_csv_config.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/scripts/tests/test_reference_search.py
git commit -m "test: add end-to-end smoke tests for genre canonical pipeline"
```

---

## Task Summary

| Task | Content | Dependencies |
|------|------|------|
| 1 | GENRE_CANONICAL constants + PLATFORM_TO_CANONICAL mappings + resolve_genre() | None |
| 2 | Integrate resolve_genre into _genre_matches and search() | Task 1 |
| 3 | Add prefix / required_cols to CSV_CONFIG | None (may run alongside Task 1) |
| 4 | validate_csv.py validator | Task 1 + 3 |
| 5 | Add canonical_genre to 题材与调性推理.csv and integrate engine | Task 1 |
| 6 | Migrate all CSV 适用题材 columns to canonical values | Task 2 |
| 7 | Update CSV README genre section | Task 6 |
| 8 | Top-level references/README.md index | None (may run alongside any task) |
| 9 | End-to-end smoke tests | Task 2 + 4 + 6 |
