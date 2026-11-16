#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'Search reference CSV files using BM25 keyword matching.\n\nRead references/csv/, filter by skill and genre, and return JSON.\n\nUsage:\n    python reference_search.py --skill write --query "character naming" --genre xuanhuan\n    python reference_search.py --skill write --query "combat description" --max-results 3\n'
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from genre_taxonomy import GENRE_CANONICAL, resolve_canonical_genre


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

# Stable internal CSV names remain valid; English callers use these public names.
TABLE_ALIASES = {
    "naming": "naming", "scenes": "scenes", "techniques": "techniques",
    "tropes": "tropes", "pacing": "pacing", "characters": "characters",
    "powers": "powers", "genre-routing": "genre-routing", "adjudication": "adjudication",
}


def _load_csv(path: Path) -> List[Dict[str, str]]:
    """Load a single CSV file (UTF-8 with BOM)."""
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_tables(csv_dir: Path, table: Optional[str] = None) -> Dict[str, List[Dict[str, str]]]:
    """
    Load CSV tables from *csv_dir*.

    If *table* is given, load only that file (``<table>.csv``).
    Otherwise load every ``.csv`` file in the directory.

    Returns ``{table_name: [row_dict, ...]}``.
    """
    tables: Dict[str, List[Dict[str, str]]] = {}
    if table:
        target = csv_dir / f"{table}.csv"
        if target.is_file():
            tables[table] = _load_csv(target)
    else:
        for p in sorted(csv_dir.glob("*.csv")):
            tables[p.stem] = _load_csv(p)
    return tables


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

_MULTI_VALUE_SPLIT_RE = re.compile(r"[|,，、；;]+")
_INTERNAL_TABLE_ROLES = {"route", "reasoning"}


def split_multi_value(cell: Any) -> List[str]:
    """Split list-like cells while remaining compatible with legacy comma data."""
    if not cell:
        return []
    return [part.strip() for part in _MULTI_VALUE_SPLIT_RE.split(str(cell)) if part.strip()]


def _split_multi_value(cell: Any) -> List[str]:
    return split_multi_value(cell)


def _skill_matches(row: Dict[str, str], skill: str) -> bool:
    'Return whether skill appears in the pipe-separated applicable-skills column.'
    return skill in _split_multi_value(row.get("applicable_skills", ""))


def _genre_matches(row: Dict[str, str], genre: Optional[str]) -> bool:
    'Return True when genre is None or matches the applicable-genres column; the all-genres value always matches.\n\nNormalize input and cell genres to canonical values before comparison so platform tags and legacy values work transparently.'
    if genre is None:
        return True
    cell = row.get("applicable_genres", "")
    if cell.strip() == "all":
        return True
    requested_genres = [
        resolved
        for raw in _split_multi_value(genre)
        for resolved in [resolve_genre(raw)]
        if resolved
    ]
    cell_genres = [resolve_genre(v) for v in _split_multi_value(cell)]
    return any(resolved in cell_genres for resolved in requested_genres)


def _table_visible_for_search(table_name: str, skill: str, explicit_table: bool) -> bool:
    """Keep story-system internals out of normal cross-table skill searches."""
    if explicit_table or skill == "story-system":
        return True
    cfg = CSV_CONFIG.get(table_name) or {}
    return cfg.get("role") not in _INTERNAL_TABLE_ROLES


# ---------------------------------------------------------------------------
# Genre canonical resolution
# ---------------------------------------------------------------------------


def resolve_genre(genre: Optional[str]) -> Optional[str]:
    """Resolve a user-facing genre string to its canonical form.

    Accepts canonical genres, platform tags, and legacy values.
    Returns the canonical genre string, or the original input if unresolvable.
    """
    if genre is None:
        return None
    return resolve_canonical_genre(genre)


# ---------------------------------------------------------------------------
# CSV_CONFIG – per-table metadata registry
# ---------------------------------------------------------------------------

CSV_CONFIG: Dict[str, Dict[str, Any]] = {
    "naming": {
        "file": "naming.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "naming_target", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "base",
        "contract_inject": "MASTER_SETTING.base_context",
        "prefix": "NR",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "scenes": {
        "file": "scenes.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "pattern_name", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "base",
        "contract_inject": "CHAPTER_BRIEF.dynamic_context",
        "prefix": "SP",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "techniques": {
        "file": "techniques.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "technique_name", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "base",
        "contract_inject": "CHAPTER_BRIEF.dynamic_context",
        "prefix": "WT",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "tropes": {
        "file": "tropes.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "trope_name", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "dynamic",
        "contract_inject": "CHAPTER_BRIEF.dynamic_context",
        "prefix": "TR",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "pacing": {
        "file": "pacing.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "pacing_type", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "dynamic",
        "contract_inject": "CHAPTER_BRIEF.dynamic_context",
        "prefix": "PA",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "characters": {
        "file": "characters.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "character_type", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "base",
        "contract_inject": "MASTER_SETTING.base_context",
        "prefix": "CH",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "powers": {
        "file": "powers.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "summary": 2},
        "output_cols": ["id", "setting_type", "summary", "model_instruction", "details"],
        "poison_col": "pitfalls",
        "role": "base",
        "contract_inject": "MASTER_SETTING.base_context",
        "prefix": "SY",
        "required_cols": ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"],
    },
    "genre-routing": {
        "file": "genre-routing.csv",
        "search_cols": {"keywords": 3, "intent_synonyms": 4, "genre_aliases": 3},
        "output_cols": ["id", "genre_route", "canonical_genre", "core_tone", "recommended_base_tables", "recommended_dynamic_tables"],
        "poison_col": "pitfalls",
        "role": "route",
        "contract_inject": "MASTER_SETTING.route",
        "prefix": "GR",
        "required_cols": ["id", "applicable_skills", "genre_route", "canonical_genre", "core_tone", "recommended_base_tables", "recommended_dynamic_tables"],
    },
    "adjudication": {
        "file": "adjudication.csv",
        "search_cols": {"genre": 4, "keywords": 3, "intent_synonyms": 4},
        "output_cols": ["genre", "style_priority", "payoff_priority", "default_pacing_strategy",
                        "pitfall_weight", "conflict_resolution", "contract_injection_layer", "anti_pattern"],
        "poison_col": "",
        "role": "reasoning",
        "contract_inject": "CHAPTER_BRIEF.writing_guidance",
        "prefix": "RS",
        "required_cols": ["id", "genre", "style_priority", "payoff_priority", "default_pacing_strategy", "conflict_resolution"],
    },
}

# ---------------------------------------------------------------------------
# BM25-lite scoring
# ---------------------------------------------------------------------------

_TOKEN_SPLIT_RE = re.compile(r"[\s|,，、/；;：:（）()【】\[\]<>《》""\"'''!?！？。…]+")
_DEFAULT_SEARCH_WEIGHTS = {
    "intent_synonyms": 4,
    "keywords": 3,
    "summary": 2,
    "details": 1,
}


def _tokenize(text: str) -> List[str]:
    """Split text into reusable search terms without requiring a segmenter."""
    if not text:
        return []
    tokens: List[str] = []
    for part in _TOKEN_SPLIT_RE.split(text):
        token = part.strip()
        if not token:
            continue
        # Drop single-letter noise such as the t from don't to avoid false substring-fallback matches.
        if len(token) == 1 and token.isascii():
            continue
        tokens.append(token)
    return tokens


def _build_doc_terms(row: Dict[str, str], search_weights: Optional[Dict[str, int]] = None) -> List[str]:
    """Build weighted BM25 terms from the configured search fields."""
    weights = search_weights or _DEFAULT_SEARCH_WEIGHTS
    terms: List[str] = []
    for field, weight in weights.items():
        field_terms = _tokenize(row.get(field, ""))
        if not field_terms:
            continue
        terms.extend(field_terms * weight)
    return terms


def _bm25_score(query_terms: List[str], doc_terms: List[str],
                avg_dl: float, k1: float = 1.5, b: float = 0.75,
                idf_map: Optional[Dict[str, float]] = None) -> float:
    """
    Simplified BM25 score for a single document.

    *idf_map* maps each query term to its IDF value.
    """
    if not doc_terms:
        return 0.0
    dl = len(doc_terms)
    score = 0.0
    tf_map: Dict[str, int] = {}
    for t in doc_terms:
        tf_map[t] = tf_map.get(t, 0) + 1
    for qt in query_terms:
        tf = tf_map.get(qt, 0)
        if tf == 0:
            # Also check substring match (important for Chinese compound words)
            for dt in tf_map:
                if qt == dt or (re.search(r"[\u4e00-\u9fff]", qt) and (qt in dt or dt in qt)):
                    tf = max(tf, 1)
                    break
        if tf == 0:
            continue
        idf = idf_map.get(qt, 1.0) if idf_map else 1.0
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * dl / max(avg_dl, 1))
        score += idf * numerator / denominator
    return score


def _compute_idf(query_terms: List[str], all_docs: List[List[str]]) -> Dict[str, float]:
    """Compute IDF for each query term across all documents."""
    n = len(all_docs)
    if n == 0:
        return {}
    idf: Dict[str, float] = {}
    for qt in query_terms:
        df = 0
        for doc in all_docs:
            for dt in doc:
                if qt == dt or (re.search(r"[\u4e00-\u9fff]", qt) and (qt in dt or dt in qt)):
                    df += 1
                    break
        # BM25 IDF: log((N - df + 0.5) / (df + 0.5) + 1)
        idf[qt] = math.log((n - df + 0.5) / (df + 0.5) + 1)
    return idf


# ---------------------------------------------------------------------------
# Content summary builder
# ---------------------------------------------------------------------------

# Hardcoded fallback columns when no CSV_CONFIG entry exists.
_FALLBACK_CONTENT_COLUMNS = [
    "technique_name", "trope_name", "character_type", "pacing_type", "setting_type",
    "rule", "description", "pattern_name",
    "common_mistakes", "setup", "core_payoff", "twist_design",
    "core_motivation", "behavior_logic", "interaction_pattern", "avoid",
    "emotional_techniques", "common_failure_modes",
    "numeric_limits", "plot_interaction",
    "positive_example", "example_excerpt",
    "negative_example", "negative_example",
    "naming_target", "scene_type", "technique_type", "applicable_scenes",
]

_SUMMARY_SKIP_COLS = {"id", "model_instruction", "details", "summary"}


def _build_summary(row: Dict[str, str], table_name: Optional[str] = None) -> str:
    """Merge key content columns into a single summary string."""
    core_summary = row.get("summary", "").strip()
    if core_summary:
        return core_summary

    # Derive fallback columns from CSV_CONFIG if available
    tbl_cfg = CSV_CONFIG.get(table_name) if table_name else None
    if tbl_cfg:
        cols = [c for c in tbl_cfg["output_cols"] if c not in _SUMMARY_SKIP_COLS]
    else:
        cols = _FALLBACK_CONTENT_COLUMNS

    parts: List[str] = []
    for col in cols:
        val = row.get(col, "").strip()
        if val:
            parts.append(val)
    if parts:
        return "；".join(parts)
    return row.get("details", "").strip()


# ---------------------------------------------------------------------------
# Search entry point
# ---------------------------------------------------------------------------

def search(
    csv_dir: Path,
    skill: str,
    query: str,
    table: Optional[str] = None,
    genre: Optional[str] = None,
    max_results: int = 5,
) -> Dict[str, Any]:
    """
    Run a BM25 keyword search across CSV reference tables.

    Returns a result dict suitable for JSON serialisation.
    """
    if not csv_dir.is_dir():
        return {
            "status": "error",
            "error": {
                "code": "CSV_DIR_NOT_FOUND",
                "message": f"CSV directory not found: {csv_dir}",
            },
        }

    table = TABLE_ALIASES.get(table, table)
    tables = load_tables(csv_dir, table=table)
    if not tables:
        return {
            "status": "success",
            "message": "search_results",
            "data": {
                "query": query,
                "skill": skill,
                "genre": genre,
                "total": 0,
                "results": [],
            },
        }

    # 1) Collect filtered rows with table name annotation
    candidates: List[tuple] = []  # (table_name, row)
    for tbl_name, rows in tables.items():
        if not _table_visible_for_search(tbl_name, skill, explicit_table=table is not None):
            continue
        for row in rows:
            if _skill_matches(row, skill) and _genre_matches(row, genre):
                candidates.append((tbl_name, row))

    if not candidates:
        return {
            "status": "success",
            "message": "search_results",
            "data": {
                "query": query,
                "skill": skill,
                "genre": genre,
                "total": 0,
                "results": [],
            },
        }

    # 2) Tokenize
    query_terms = _tokenize(query)
    doc_terms_list = []
    for tbl_name, row in candidates:
        tbl_cfg = CSV_CONFIG.get(tbl_name)
        weights = dict(tbl_cfg["search_cols"]) if tbl_cfg else None
        terms = _build_doc_terms(row, weights)
        doc_terms_list.append(terms)
    avg_dl = sum(len(d) for d in doc_terms_list) / len(doc_terms_list) if doc_terms_list else 1.0
    idf_map = _compute_idf(query_terms, doc_terms_list)

    # 3) Score
    scored: List[tuple] = []
    for idx, (tbl_name, row) in enumerate(candidates):
        score = _bm25_score(query_terms, doc_terms_list[idx], avg_dl, idf_map=idf_map)
        if score > 0:
            scored.append((score, tbl_name, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_results]

    # 4) Format results
    results: List[Dict[str, Any]] = []
    for _score, tbl_name, row in top:
        results.append({
            "id": row.get("id", ""),
            "instruction": row.get("model_instruction", "").strip(),
            "table": tbl_name,
            "category": row.get("category", ""),
            "level": row.get("level", ""),
            "applicable_genres": row.get("applicable_genres", ""),
            "summary": _build_summary(row, table_name=tbl_name),
            "model_instruction": row.get("model_instruction", "").strip(),
        })

    return {
        "status": "success",
        "message": "search_results",
        "data": {
            "query": query,
            "skill": skill,
            "genre": genre,
            "total": len(results),
            "results": results,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _default_csv_dir() -> Path:
    """Auto-detect the csv directory relative to this script's location."""
    return Path(__file__).resolve().parent.parent / "references" / "csv"


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="BM25 keyword search over reference CSV files",
    )
    parser.add_argument("--skill", required=True, help="Filter by skill column")
    parser.add_argument("--table", default=None, help="English table alias (naming, scenes, techniques, tropes, pacing, characters, powers, genre-routing, adjudication) or legacy CSV name")
    parser.add_argument("--query", required=True, help="BM25 search keywords")
    parser.add_argument("--genre", default=None, help="Filter by genre column")
    parser.add_argument("--max-results", type=int, default=5, help="Max results (default 5)")
    parser.add_argument("--csv-dir", default=None, help="Override CSV directory path")

    args = parser.parse_args(argv)
    csv_dir = Path(args.csv_dir) if args.csv_dir else _default_csv_dir()

    result = search(
        csv_dir=csv_dir,
        skill=args.skill,
        query=args.query,
        table=args.table,
        genre=args.genre,
        max_results=args.max_results,
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
