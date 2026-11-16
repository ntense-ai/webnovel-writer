#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'Validate reference CSV data quality against CSV_CONFIG and canonical genre values.'
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_search import CSV_CONFIG, GENRE_CANONICAL, split_multi_value
from genre_taxonomy import default_taxonomy_path, load_genre_taxonomy


_CHINESE_COMMA_RE = re.compile(r"，")
_MULTI_VALUE_COLUMNS = ("applicable_skills", "keywords", "intent_synonyms", "applicable_genres")
_ROUTE_TABLE = "genre-routing"
_REASONING_TABLE = "adjudication"
_MIN_ROUTE_ROWS = 16
_MIN_REASONING_ROWS = 14
_VALID_SKILLS = {"init", "plan", "write", "review", "query", "learn", "dashboard", "story-system"}
_VALID_LEVELS = {"reminder", "defect-compensation", "knowledge"}


def _split_multi_value(cell: str) -> List[str]:
    return split_multi_value(cell)


def _default_csv_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "csv"


def _read_csv(path: Path) -> tuple[List[str], List[Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = list(reader.fieldnames or [])
    return headers, rows


def _validate_genre_taxonomy(errors: List[str], warnings: List[str]) -> None:
    taxonomy_path = default_taxonomy_path()
    if not taxonomy_path.exists():
        errors.append(f"[genre-index] File not found: {taxonomy_path}")
        return
    try:
        taxonomy = load_genre_taxonomy(str(taxonomy_path))
    except Exception as exc:
        errors.append(f"[genre-index] Load failed: {exc}")
        return

    templates_dir = Path(__file__).resolve().parent.parent / "templates" / "genres"
    template_files = {path.name for path in templates_dir.glob("*.md")}
    referenced_files = {entry.template_file for entry in taxonomy.entries if entry.template_file}

    missing_templates = sorted(referenced_files - template_files)
    if missing_templates:
        errors.append(f"[genre-index] template_file not found: {', '.join(missing_templates)}")

    unreferenced_templates = sorted(template_files - referenced_files)
    if unreferenced_templates:
        errors.append(f"[genre-index] Templates missing from index: {', '.join(unreferenced_templates)}")

    for entry in taxonomy.entries:
        if entry.template_file and not entry.template_file.endswith(".md"):
            errors.append(f"[genre-index] {entry.label} template_file must end in .md: {entry.template_file}")
        if entry.canonical_genre != "all" and entry.canonical_genre not in GENRE_CANONICAL:
            errors.append(f"[genre-index] {entry.label} Invalid canonical_genre: {entry.canonical_genre}")

    if len(template_files) != 37:
        warnings.append(f"[genre-index] Template count is {len(template_files)}，expected 37")


def validate(csv_dir: Path) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    all_ids: Dict[str, str] = {}
    valid_genres = GENRE_CANONICAL | {"all"}

    _validate_genre_taxonomy(errors, warnings)

    for table_name, config in CSV_CONFIG.items():
        csv_path = csv_dir / config["file"]
        if not csv_path.exists():
            errors.append(f"[{table_name}] File not found: {config['file']}")
            continue

        headers, rows = _read_csv(csv_path)
        header_set = set(headers)
        prefix = str(config.get("prefix", "")).strip()
        required_cols = list(config.get("required_cols", []))

        declared_cols = set(config.get("search_cols", {}).keys())
        declared_cols.update(config.get("output_cols", []))
        declared_cols.update(required_cols)
        poison_col = str(config.get("poison_col", "")).strip()
        if poison_col:
            declared_cols.add(poison_col)

        missing_headers = declared_cols - header_set
        if missing_headers:
            joined = ", ".join(sorted(missing_headers))
            errors.append(f"[{table_name}] CSV missing headers: {joined}")

        for line_no, row in enumerate(rows, start=2):
            row_id = (row.get("id") or "").strip()

            if None in row:
                extras = row.get(None) or []
                errors.append(
                    f"[{table_name}] row {line_no} ({row_id or 'no ID'}) More fields than headers: {extras}"
                )

            if row_id:
                if row_id in all_ids:
                    errors.append(
                        f"[{table_name}] row {line_no} id {row_id} duplicate (first seen at {all_ids[row_id]})"
                    )
                else:
                    all_ids[row_id] = table_name

            if prefix and row_id and not row_id.startswith(f"{prefix}-"):
                errors.append(f"[{table_name}] row {line_no} id {row_id} must start with {prefix}-")

            for col in required_cols:
                value = (row.get(col) or "").strip()
                if not value:
                    errors.append(f"[{table_name}] row {line_no} ({row_id}) required column {col} is empty")

            for col in _MULTI_VALUE_COLUMNS:
                value = row.get(col) or ""
                if _CHINESE_COMMA_RE.search(value):
                    errors.append(
                        f"[{table_name}] row {line_no} ({row_id}) {col} contains a full-width comma; use |"
                    )

            skill_cell = (row.get("applicable_skills") or "").strip()
            if "applicable_skills" in header_set:
                skill_tokens = _split_multi_value(skill_cell)
                if not skill_tokens:
                    errors.append(f"[{table_name}] row {line_no} ({row_id}) applicable_skills is empty")
                for skill in skill_tokens:
                    if skill not in _VALID_SKILLS:
                        errors.append(f"[{table_name}] row {line_no} ({row_id}) Invalid applicable_skills value '{skill}'")

            if "level" in header_set:
                level = (row.get("level") or "").strip()
                allowed_levels = set(_VALID_LEVELS)
                if table_name == _REASONING_TABLE:
                    allowed_levels.add("reasoning")
                if not level:
                    errors.append(f"[{table_name}] row {line_no} ({row_id}) level is empty")
                elif level not in allowed_levels:
                    errors.append(f"[{table_name}] row {line_no} ({row_id}) Invalid level value '{level}'")

            genre_cell = (row.get("applicable_genres") or "").strip()
            if genre_cell:
                for genre in _split_multi_value(genre_cell):
                    if genre not in valid_genres:
                        warnings.append(
                            f"[{table_name}] row {line_no} ({row_id}) applicable_genres value '{genre}' is not canonical"
                        )

    route_path = csv_dir / f"{_ROUTE_TABLE}.csv"
    route_canonicals: set[str] = set()
    route_rows: List[Dict[str, str]] = []
    if route_path.exists():
        _, route_rows = _read_csv(route_path)
        if len(route_rows) < _MIN_ROUTE_ROWS:
            warnings.append(
                f"[{_ROUTE_TABLE}] Route row count {len(route_rows)} below Phase 2 acceptance threshold {_MIN_ROUTE_ROWS}"
            )
        for line_no, row in enumerate(route_rows, start=2):
            row_id = (row.get("id") or "").strip()
            canonical = (row.get("canonical_genre") or "").strip()
            if not canonical:
                warnings.append(f"[{_ROUTE_TABLE}] row {line_no} ({row_id}) canonical_genre is empty")
                continue
            if canonical == "all":
                continue
            if canonical not in GENRE_CANONICAL:
                warnings.append(
                    f"[{_ROUTE_TABLE}] row {line_no} ({row_id}) canonical_genre '{canonical}' is not canonical"
                )
                continue
            route_canonicals.add(canonical)

    reasoning_path = csv_dir / f"{_REASONING_TABLE}.csv"
    reasoning_rows: List[Dict[str, str]] = []
    reasoning_genres: set[str] = set()
    if reasoning_path.exists():
        _, reasoning_rows = _read_csv(reasoning_path)
        if len(reasoning_rows) < _MIN_REASONING_ROWS:
            warnings.append(
                f"[{_REASONING_TABLE}] Adjudication row count {len(reasoning_rows)} below Phase 2 acceptance threshold {_MIN_REASONING_ROWS}"
            )
        for line_no, row in enumerate(reasoning_rows, start=2):
            row_id = (row.get("id") or "").strip()
            genre = (row.get("genre") or "").strip()
            if not genre:
                continue
            if genre not in GENRE_CANONICAL:
                warnings.append(f"[{_REASONING_TABLE}] row {line_no} ({row_id}) genre '{genre}' is not canonical")
                continue
            reasoning_genres.add(genre)

        for canonical_genre in sorted(GENRE_CANONICAL):
            if canonical_genre not in reasoning_genres:
                warnings.append(f"[{_REASONING_TABLE}] canonical genre '{canonical_genre}' has no matching adjudication row")

    for canonical_genre in sorted(route_canonicals):
        if canonical_genre not in reasoning_genres:
            warnings.append(f"[{_ROUTE_TABLE}] canonical genre '{canonical_genre}' has no matching adjudication row")
    for canonical_genre in sorted(reasoning_genres):
        if route_rows and canonical_genre not in route_canonicals:
            warnings.append(f"[{_REASONING_TABLE}] canonical genre '{canonical_genre}' has no matching route row")

    return {"errors": errors, "warnings": warnings}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate reference CSV files")
    parser.add_argument("--csv-dir", default=None, help="Override CSV directory")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    csv_dir = Path(args.csv_dir) if args.csv_dir else _default_csv_dir()
    result = validate(csv_dir)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for error in result["errors"]:
            print(f"ERROR: {error}")
        for warning in result["warnings"]:
            print(f"WARN:  {warning}")
        print(f"\n--- {len(result['errors'])} error(s), {len(result['warnings'])} warning(s) ---")

    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
