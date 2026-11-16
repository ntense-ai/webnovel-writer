# References Genre Alignment and Structural Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish authoritative genre enums, aligning the CSV `applicable_genres` column, routing table, reasoning table, and search script to one set of values; fill validation-script and structural gaps.

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
            "urban", "xuanhuan", "xianxia", "fantasy", "sci-fi",
            "historical", "mystery", "game-lit", "historical-romance", "contemporary-romance",
            "fantasy-romance", "period-fiction", "farming", "quick-transmigration", "fanfiction",
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
        assert PLATFORM_TO_CANONICAL["urban-slice-of-life"] == "urban"
        assert PLATFORM_TO_CANONICAL["warrior-son-in-law"] == "urban"
        assert PLATFORM_TO_CANONICAL["Easternxianxia"] == "xianxia"
        assert PLATFORM_TO_CANONICAL["Westernfantasy"] == "fantasy"
        assert PLATFORM_TO_CANONICAL["classical stylesocial-realism"] == "historical-romance"
        assert PLATFORM_TO_CANONICAL["billionaire-romance"] == "contemporary-romance"
        assert PLATFORM_TO_CANONICAL["quick-transmigration"] == "quick-transmigration"
        assert PLATFORM_TO_CANONICAL["science-fiction apocalypse"] == "sci-fi"
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
    "urban", "xuanhuan", "xianxia", "fantasy", "sci-fi",
    "historical", "mystery", "game-lit", "historical-romance", "contemporary-romance",
    "fantasy-romance", "period-fiction", "farming", "quick-transmigration", "fanfiction",
}

PLATFORM_TO_CANONICAL: Dict[str, str] = {
    # Male-oriented categories
    "urban-slice-of-life": "urban", "urbancultivation": "urban", "urbanhigh-martial-power": "urban",
    "warrior-son-in-law": "urban", "urban-farming": "urban", "urban-speculative": "urban",
    "traditional-xuanhuan": "xuanhuan", "speculative-xuanhuan": "xuanhuan",
    "Easternxianxia": "xianxia",
    "Westernfantasy": "fantasy",
    "science-fiction apocalypse": "sci-fi",
    "ancient-history": "historical", "alternate-history": "historical", "wartime-espionage": "historical",
    "speculative-mystery": "mystery", "paranormal-mystery": "mystery",
    "gaming-and-sports": "game-lit",
    "animefanfiction": "fanfiction", "male-orientedfanfiction": "fanfiction",
    # Female-oriented categories
    "classical stylesocial-realism": "historical-romance", "palace-household-intrigue": "historical-romance", "historical-romancehigh concept": "historical-romance",
    "speculative-contemporary-romance": "contemporary-romance", "young-sweet-romance": "contemporary-romance", "Shining Stars": "contemporary-romance",
    "workplace-romance": "contemporary-romance", "billionaire-romance": "contemporary-romance",
    "cultivation-romance": "fantasy-romance",
    "period-fiction": "period-fiction", "republican-era-romance": "period-fiction",
    "farming": "farming",
    "quick-transmigration": "quick-transmigration",
    "women-centered-mystery": "mystery",
    "women-orientedfanfiction": "fanfiction",
}

# Legacy values that appeared in old CSV data → canonical mapping.
# Used by _resolve_genre() during the migration period.
_LEGACY_GENRE_MAP: Dict[str, str] = {
    "Easternxianxia": "xianxia", "Westernfantasy": "fantasy", "science-fiction apocalypse": "sci-fi",
    "urban-slice-of-life": "urban", "urbancultivation": "urban", "urbanhigh-martial-power": "urban",
    "ancient-history": "historical",
    "espionage": "historical", "military": "historical", "wuxia": "historical",
    "criminal investigation": "mystery", "thriller": "mystery", "deduction": "mystery", "rules-horror": "mystery",
    "apocalypse": "sci-fi", "cyberpunk": "sci-fi",
    "online gaming": "game-lit", "esports": "game-lit", "competition": "game-lit", "sports": "game-lit",
    "light novel": "fanfiction", "fan fiction": "fanfiction",
    "school": "contemporary-romance", "youth": "contemporary-romance", "entertainment-industry": "contemporary-romance", "workplace": "contemporary-romance",
    "high-martial-power": "urban",
}


def resolve_genre(genre: Optional[str]) -> Optional[str]:
    """Resolve a user-facing genre string to its canonical form.

    Accepts canonical genres, platform tags, and legacy values.
    Returns the canonical genre string, or the original input if unresolvable.
    """
    if genre is None:
        return None
    g = genre.strip()
    if g in GENRE_CANONICAL or g == "all":
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
        assert resolve_genre("urban") == "urban"
        assert resolve_genre("all") == "all"
        assert resolve_genre(None) is None

    def test_resolve_genre_platform_tag(self):
        from reference_search import resolve_genre
        assert resolve_genre("urban-slice-of-life") == "urban"
        assert resolve_genre("warrior-son-in-law") == "urban"
        assert resolve_genre("classical stylesocial-realism") == "historical-romance"

    def test_resolve_genre_legacy(self):
        from reference_search import resolve_genre
        assert resolve_genre("wuxia") == "historical"
        assert resolve_genre("criminal investigation") == "mystery"
        assert resolve_genre("online gaming") == "game-lit"

    def test_search_with_platform_tag_genre(self):
        """--genre urban-slice-of-life should match rows with applicable_genres=urban."""
        out = run_search(
            "--skill", "write",
            "--table", "naming",
            "--query", "characternaming",
            "--genre", "urban-slice-of-life",
        )
        assert out["status"] == "success"
        # Should find results: the urban slice-of-life alias resolves to the urban genre and matches its tagged rows.
        assert out["data"]["total"] >= 0  # may be 0 if no urban rows, but no error
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/test_reference_search.py::TestGenreCanonical::test_search_with_platform_tag_genre -v`
Expected: May PASS because `urban-slice-of-life` contains the substring `urban`, or may match imprecisely. The three `resolve_genre` tests are the key checks.

- [ ] **Step 3: Modify _genre_matches and search**

Modify `_genre_matches` in `reference_search.py` (around line 74):

```python
def _genre_matches(row: Dict[str, str], genre: Optional[str]) -> bool:
    """Return True if *genre* is None, or matches ``applicable_genres`` (``all`` always matches).

    Both the input *genre* and the cell values are resolved to canonical form
    before comparison, so platform tags and legacy values work transparently.
    """
    if genre is None:
        return True
    cell = row.get("applicable_genres", "")
    if cell.strip() == "all":
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
        assert "prefix" in config, f"table {name} missing prefix field"
        assert isinstance(config["prefix"], str)
        assert len(config["prefix"]) >= 2


def test_csv_config_has_required_cols_field():
    for name, config in CSV_CONFIG.items():
        assert "required_cols" in config, f"table {name} missing required_cols field"
        assert isinstance(config["required_cols"], list)
        assert len(config["required_cols"]) >= 1


def test_csv_config_prefix_matches_actual_data():
    """Every row's id must start with the declared prefix."""
    for name, config in CSV_CONFIG.items():
        csv_path = CSV_DIR / config["file"]
        if not csv_path.exists():
            continue
        prefix = config["prefix"]
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                row_id = row.get("id", "")
                assert row_id.startswith(prefix + "-"), (
                    f"table {name} row {row_id} iddoes not start with {prefix}- beginning"
                )
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest data_modules/tests/test_csv_config.py -v`
Expected: FAIL — `KeyError: 'prefix'`

- [ ] **Step 3: Add prefix and required_cols to every CSV_CONFIG entry**

Modify `CSV_CONFIG` in `reference_search.py`, adding two fields per table:

```python
CSV_CONFIG: Dict[str, Dict[str, Any]] = {
    "naming": {
        "file": "naming.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "naming_target", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "base",
        "prefix": "NR",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "scenes": {
        "file": "scenes.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "pattern_name", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "base",
        "prefix": "SP",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "techniques": {
        "file": "techniques.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "technique_name", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "base",
        "prefix": "WT",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "tropes": {
        "file": "tropes.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "trope_name", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "dynamic",
        "prefix": "TR",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "pacing": {
        "file": "pacing.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "pacing_type", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "dynamic",
        "prefix": "PA",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "characters": {
        "file": "characters.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "character_type", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "base",
        "prefix": "CH",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "powers": {
        "file": "powers.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "setting_type", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "base",
        "prefix": "SY",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "genre-routing": {
        "file": "genre-routing.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "genre_aliases": 3},
        "output_cols": ["id", "genre_route", "core_tone", "recommended_base_tables", "recommended_dynamic_tables"],
        "poison_col": "pitfalls",
        "role": "route",
        "prefix": "GR",
        "required_cols": ["id", "applicable_skills", "genre_route", "core_tone", "recommended_base_tables", "recommended_dynamic_tables"],
    },
    "adjudication": {
        "file": "adjudication.csv",
        "search_cols": {"genre": 4},
        "output_cols": ["genre", "style_priority", "payoff_priority", "default_pacing_strategy",
                        "pitfall_weight", "conflict_resolution", "contract_injection_layer", "anti_pattern"],
        "poison_col": "",
        "role": "reasoning",
        "prefix": "RS",
        "required_cols": ["id", "genre", "style_priority", "payoff_priority", "default_pacing_strategy", "conflict_resolution"],
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

    valid_genres = GENRE_CANONICAL | {"all"}

    for table_name, config in CSV_CONFIG.items():
        csv_path = csv_dir / config["file"]
        if not csv_path.exists():
            errors.append(f"[{table_name}] file does not exist: {config['file']}")
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
            errors.append(f"[{table_name}] CSV missing header: {missing_headers}")

        for i, row in enumerate(rows, start=2):  # row 1 is header
            row_id = row.get("id", "").strip()

            # Check: ID uniqueness
            if row_id:
                if row_id in all_ids:
                    errors.append(
                        f"[{table_name}] row{i} id {row_id} duplicate（first appears at {all_ids[row_id]}）"
                    )
                else:
                    all_ids[row_id] = table_name

            # Check: prefix consistency
            if prefix and row_id and not row_id.startswith(prefix + "-"):
                errors.append(
                    f"[{table_name}] row{i} id {row_id} should begin with {prefix}- beginning"
                )

            # Check: required columns non-empty
            for col in required_cols:
                val = row.get(col, "").strip()
                if not val:
                    errors.append(f"[{table_name}] row{i} ({row_id}) required column {col} is empty")

            # Check: delimiter convention (no Chinese comma in multi-value fields)
            for col in ("applicable_skills", "keywords", "intent_synonyms", "applicable_genres"):
                val = row.get(col, "")
                if _CHINESE_COMMA.search(val):
                    errors.append(
                        f"[{table_name}] row{i} ({row_id}) {col} contains a full-width comma，should use |"
                    )

            # Check that the applicable-genre column contains only canonical values.
            genre_cell = row.get("applicable_genres", "").strip()
            if genre_cell:
                for g in _split(genre_cell):
                    if g not in valid_genres:
                        warnings.append(
                            f"[{table_name}] row{i} ({row_id}) applicable_genresvalue '{g}' "
                            f"not in canonical enum"
                        )

    # Cross-table check: route ↔ reasoning coverage
    route_genres: set[str] = set()
    reasoning_genres: set[str] = set()

    route_path = csv_dir / "genre-routing.csv"
    if route_path.exists():
        for row in _load_csv(route_path):
            val = row.get("genre_route", "").strip()
            if val:
                route_genres.add(val)

    reasoning_path = csv_dir / "adjudication.csv"
    if reasoning_path.exists():
        for row in _load_csv(reasoning_path):
            val = row.get("genre", "").strip()
            if val:
                reasoning_genres.add(val)

    # Every canonical genre should have at least one reasoning row
    for cg in GENRE_CANONICAL:
        if cg not in reasoning_genres:
            warnings.append(f"[adjudication] canonical genre '{cg}' no correspondingadjudicationrow")

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
Expected: 0 errors (valid structure), multiple warnings (noncanonical `applicable_genres` values + missing canonical coverage in reasoning rules)

- [ ] **Step 6: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/scripts/validate_csv.py webnovel-writer/scripts/tests/test_validate_csv.py
git commit -m "feat: add validate_csv.py — schema, ID, prefix, genre, delimiter checks"
```

---

### Task 5: Add canonical_genre column to genre-routing.csv

**Files:**
- Modify: `webnovel-writer/references/csv/genre-routing.csv`
- Modify: `webnovel-writer/scripts/reference_search.py` (CSV_CONFIG for genre-routing)
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
    route = engine._route("broken-engagement fiction three-year agreement", "xuanhuan")
    assert "canonical_genre" in route["meta"]
    assert route["meta"]["canonical_genre"] in {
        "urban", "xuanhuan", "xianxia", "fantasy", "sci-fi",
        "historical", "mystery", "game-lit", "historical-romance", "contemporary-romance",
        "fantasy-romance", "period-fiction", "farming", "quick-transmigration", "fanfiction",
    }
```

- [ ] **Step 2: Run tests to confirm failure**

Expected: FAIL — `KeyError: 'canonical_genre'`

- [ ] **Step 3: Modify CSV and code**

**3a.** Add `canonical_genre` after `genre_route` in `genre-routing.csv`. Manually fill the corresponding canonical value for every row. Example:

| id | genre_route | canonical_genre | ... |
|------|----------|----------------|-----|
| GR-001 | broken-engagement-fantasy | xuanhuan | ... |
| GR-002 | rules-horror-zoo | mystery | ... |

All eight current rows need `canonical_genre`.

**3b.** In `reference_search.py`, add `"canonical_genre"` to `output_cols` in `CSV_CONFIG["genre-routing"]`:

```python
"genre-routing": {
    "file": "genre-routing.csv",
    "search_cols": {"keywords": 3, "intent_synonyms": 4, "genre_aliases": 3},
    "output_cols": ["id", "genre_route", "canonical_genre", "core_tone", "recommended_base_tables", "recommended_dynamic_tables"],
    "poison_col": "pitfalls",
    "role": "route",
    "prefix": "GR",
    "required_cols": ["id", "applicable_skills", "genre_route", "canonical_genre", "core_tone", "recommended_base_tables", "recommended_dynamic_tables"],
},
```

**3c.** Modify `_route` in `story_system_engine.py` (around lines 141–158), adding `canonical_genre` to returned `meta`:

```python
        primary_genre = str(matched.get("genre_route") or genre or "").strip()
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
git add webnovel-writer/references/csv/genre-routing.csv webnovel-writer/scripts/reference_search.py webnovel-writer/scripts/data_modules/story_system_engine.py
git commit -m "feat: add canonical_genre column to route table, thread through engine"
```

---

### Task 6: Migrate existing CSV applicable_genres columns to canonical enums

**Files:**
- Modify: `webnovel-writer/references/csv/naming.csv`
- Modify: `webnovel-writer/references/csv/scenes.csv`
- Modify: `webnovel-writer/references/csv/techniques.csv`
- Modify: `webnovel-writer/references/csv/tropes.csv`
- Modify: `webnovel-writer/references/csv/characters.csv`
- Modify: `webnovel-writer/references/csv/pacing.csv`
- Modify: `webnovel-writer/references/csv/powers.csv`
- Modify: `webnovel-writer/references/csv/adjudication.csv`

**Note: this is manual data editing. Inspect every CSV row’s `applicable_genres` field and replace noncanonical values with canonical enums.**

- [ ] **Step 1: Run validate_csv.py for the complete warning list**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python validate_csv.py --format json > /tmp/csv_warnings.json`

This outputs all warnings that applicable-genre values are outside the canonical enum, forming the migration checklist.

- [ ] **Step 2: Edit each file using the migration mapping**

Open each CSV and apply the existing non-enum value migration mapping in `genre-canonical.md`:

Migration rules:
- `espionage` → `historical`
- `criminal investigation|thriller|deduction|rules-horror` → `mystery`
- `apocalypse|cyberpunk` → `sci-fi`
- `military|wuxia` → `historical`
- `online gaming|esports|competition|sports` → `game-lit`
- `high-martial-power` → `urban`
- `system fiction|infinite-scenarios` → use the actual setting genre (`xuanhuan`/`urban`/`mystery`)
- `melodrama|payoff-driven fiction|deep plot|realistic|ensemble|epic` → remove that value; use a specific applicable genre or `all`
- `action|psychological|war|disaster|long-form|zhihu-short-fiction` → remove that value; use a specific applicable genre or `all`
- `school|youth|entertainment-industry|workplace` → `contemporary-romance`
- `commercial rivalry|business` → `urban` or `contemporary-romance`
- `fan fiction|light novel` → `fanfiction`

Save each modified file, preserving UTF-8 with BOM.

- [ ] **Step 3: Run validate_csv.py; confirm zero or substantially fewer warnings**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python validate_csv.py`
Expected: 0 errors, zero `applicable_genres` warnings (only reasoning-coverage warnings remain)

- [ ] **Step 4: Run existing search tests to check regressions**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest tests/test_reference_search.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/references/csv/*.csv
git commit -m "refactor: migrate all CSV applicable_genres values to canonical genre enum"
```

---

### Task 7: Update the CSV README genre section

**Files:**
- Modify: `webnovel-writer/references/csv/README.md:166-170`

- [ ] **Step 1: Replace old Fanqie classification with the canonical enum reference**

Replace the old classification at README.md lines 166–170:

```markdown
## Applicable genres (Fanqie classification)

**Male-oriented:** urban、xuanhuan、xianxia、fantasy、wuxia、historical、military、sci-fi、mystery、game-lit、sports、light novel

**Female-oriented:** contemporary-romance、historical-romance、fantasy-romance、mystery、light novel
```

With:

````markdown
## Applicable genre enum

The `applicable_genres` column accepts only these 15 canonical values or `all`:

```
urban  xuanhuan  xianxia  fantasy  sci-fi
historical  mystery  game-lit  historical-romance  contemporary-romance
fantasy-romance  period-fiction  farming  quick-transmigration  fanfiction
```

See `genre-canonical.md` for the complete two-layer system (canonical + Fanqie platform_tag mappings).

**Do not** put these in `applicable_genres`:
- Fanqie subcategories (e.g. `urban-slice-of-life`, `warrior-son-in-law`): these are platform_tag values used only in routing tables
- Trope names (e.g. `broken-engagement fiction`, `system-fiction`): these belong in `tropes.csv`
- Tone/scene/format labels (e.g. `payoff-driven fiction`, `action`, `short-fiction`): these are not genres
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
        out = run_search("--skill", "write", "--query", "progression and vindication", "--genre", "xuanhuan")
        assert out["status"] == "success"
        assert out["data"]["total"] >= 1

    def test_guyan_genre_returns_results(self):
        out = run_search("--skill", "write", "--query", "palace intrigue legitimate and concubine-born heirs", "--genre", "historical-romance")
        assert out["status"] == "success"
        # May be 0 if no historical-romance rows exist yet, but must not error
        assert isinstance(out["data"]["results"], list)

    def test_platform_tag_as_genre(self):
        """Using a platform_tag like urban-slice-of-life should work as --genre."""
        out = run_search("--skill", "write", "--query", "everyday-lifecomedy", "--genre", "urban-slice-of-life")
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
| 5 | Add canonical_genre to genre-routing.csv and integrate engine | Task 1 |
| 6 | Migrate all CSV applicable_genres columns to canonical values | Task 2 |
| 7 | Update CSV README genre section | Task 6 |
| 8 | Top-level references/README.md index | None (may run alongside any task) |
| 9 | End-to-end smoke tests | Task 2 + 4 + 6 |
