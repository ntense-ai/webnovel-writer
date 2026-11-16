# Story System Phase 1 Contract Seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Story System Phase 1 contract seed layer without breaking existing `reference_search.py`, `context_manager.py`, or the main writing workflow: `genre-routing.csv`, minimal `MASTER_SETTING` / `CHAPTER_BRIEF` / `anti_patterns` persistence, and contract reading in `context_manager`.

**Architecture:** Use four stages: data layer → contract aggregator → `.story-system/` persistence → runtime injection. Phase 1 establishes only a minimal contract source of truth, without `VOLUME_BRIEF`, `REVIEW_CONTRACT`, or `CHAPTER_COMMIT`, and retains `genre-profiles.md` as a fallback.

**Tech Stack:** Python 3.13, argparse, pytest, CSV (UTF-8 with BOM), Markdown + JSON contract files, unified CLI `webnovel.py`

**Spec:** `docs/superpowers/specs/2026-04-12-story-system-evolution-spec.md`

**Companion Spec:** `docs/superpowers/specs/2026-04-12-story-system-pro-max-retrofit-spec.md`

---

## Scope Split

This plan **covers only Phase 1 of the evolution specification**, because:

- `Phase 2` and later introduce `VOLUME_BRIEF`, `REVIEW_CONTRACT`, outline fulfillment diffs, and review blocking rules.
- `Phase 3` adds `CHAPTER_COMMIT` and four projection writers.
- `Phase 4` adds a canonical event log.
- Only `Phase 5` can safely downgrade the legacy pipeline.

Combining them into one implementation plan would cause:

- Distorted file-responsibility boundaries
- Unmanageable TDD granularity
- Documentation/code changes without verifiable phase deliverables

Therefore the exit criteria are fixed:

1. `PROJECT_ROOT/.story-system/` can generate minimal `MASTER_SETTING`, `chapter_XXX`, and `anti_patterns`
2. `context_manager` can read and inject a `story_contract` section
3. Legacy `genre_profile` remains available as a fallback
4. Documentation defines Phase 1 path semantics, schemas, and usage

Write three separate follow-up plans:

- `Phase 2 Contract-First Runtime`
- `Phase 3 Chapter Commit Chain`
- `Phase 4 Event Log + Override Ledger`

Fix documentation boundaries in this phase as well:

- Add only a top-level `Story System` section and basic directory explanation to `README.md`
- Later Phases 2/3/4 may append within existing sections, not rewrite their overall structure

---

## File Structure

### Files to Create

- `webnovel-writer/references/csv/genre-routing.csv`
- `webnovel-writer/scripts/data_modules/story_contracts.py`
- `webnovel-writer/scripts/data_modules/story_system_engine.py`
- `webnovel-writer/scripts/data_modules/tests/test_story_contracts.py`
- `webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py`
- `webnovel-writer/scripts/data_modules/tests/test_story_system_cli.py`
- `webnovel-writer/scripts/story_system.py`
- `docs/architecture/story-system-phase1.md`

### Files to Modify

- `webnovel-writer/references/csv/README.md`
- `webnovel-writer/references/csv/tropes.csv`
- `webnovel-writer/scripts/data_modules/config.py`
- `webnovel-writer/scripts/data_modules/context_manager.py`
- `webnovel-writer/scripts/data_modules/tests/test_context_manager.py`
- `webnovel-writer/scripts/extract_chapter_context.py`
- `webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py`
- `webnovel-writer/scripts/data_modules/webnovel.py`
- `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`
- `README.md`
- `docs/architecture/overview.md`
- `docs/guides/commands.md`
- `docs/superpowers/README.md`

### File Responsibilities

- `story_contracts.py`: contract paths, merge rules, JSON/Markdown persistence, and safe marker updates
- `story_system_engine.py`: genre routing, multi-table retrieval orchestration, anti-pattern aggregation, and minimal contract dictionaries
- `story_system.py`: CLI entry point for `query -> build -> render -> persist`
- `context_manager.py`: read `MASTER_SETTING` / `chapter_XXX` / `anti_patterns` and inject `story_contract`
- `extract_chapter_context.py`: include `story_contract` in readable text/JSON extraction results
- `docs/architecture/story-system-phase1.md`: Phase 1 contract schemas, directory structure, override rules, and migration notes

---

## Task 1: Establish the Contract Path Layer and Minimal Merge Rules

**Files:**
- Create: `webnovel-writer/scripts/data_modules/story_contracts.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_story_contracts.py`
- Modify: `webnovel-writer/scripts/data_modules/config.py`

- [ ] **Step 1: Write Failing `story_contracts` Tests First**

```python
# webnovel-writer/scripts/data_modules/tests/test_story_contracts.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from data_modules.config import DataModulesConfig
from data_modules.story_contracts import StoryContractPaths, merge_contract_layers, merge_anti_patterns


def test_story_contract_paths_live_under_project_root(tmp_path):
    cfg = DataModulesConfig.from_project_root(tmp_path)
    paths = StoryContractPaths.from_project_root(cfg.project_root)

    assert paths.root == tmp_path / ".story-system"
    assert paths.master_json == tmp_path / ".story-system" / "MASTER_SETTING.json"
    assert paths.anti_patterns_json == tmp_path / ".story-system" / "anti_patterns.json"
    assert paths.chapter_json(1) == tmp_path / ".story-system" / "chapters" / "chapter_001.json"


def test_merge_contract_layers_respects_lock_categories():
    master = {
        "locked": {
            "core_tone": "hard-edged progression",
            "golden_finger_limit": "can trigger only once per day",
        },
        "append_only": {
            "anti_patterns": ["supporting-characterconsecutively steals the spotlight for more than 300 words"],
        },
        "override_allowed": {
            "scene_focus": "auction-room vindication",
        },
    }
    chapter = {
        "locked": {
            "core_tone": "light comedyeveryday-life",
        },
        "append_only": {
            "anti_patterns": ["no explanatory narration in this chapter"],
        },
        "override_allowed": {
            "scene_focus": "immediate counterattack after a broken engagement",
        },
    }

    merged = merge_contract_layers(master, chapter)

    assert merged["locked"]["core_tone"] == "hard-edged progression"
    assert merged["locked"]["golden_finger_limit"] == "can trigger only once per day"
    assert merged["append_only"]["anti_patterns"] == [
        "supporting-characterconsecutively steals the spotlight for more than 300 words",
        "no explanatory narration in this chapter",
    ]
    assert merged["override_allowed"]["scene_focus"] == "immediate counterattack after a broken engagement"


def test_merge_anti_patterns_deduplicates_by_text():
    rows = merge_anti_patterns(
        [{"text": "vindicationpacingmust include decisive follow-through", "source_table": "genre-routing", "source_id": "GR-001"}],
        [{"text": "vindicationpacingmust include decisive follow-through", "source_table": "pacing", "source_id": "PA-002"}],
    )

    assert [item["text"] for item in rows] == ["vindicationpacingmust include decisive follow-through"]
    assert rows[0]["source_table"] == "genre-routing"
```

- [ ] **Step 2: Run Tests and Confirm the Expected Failures**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_contracts.py -q --no-cov`

Expected: `ModuleNotFoundError: No module named 'data_modules.story_contracts'`

- [ ] **Step 3: Add `.story-system` Path Properties to `config.py`**

```python
# webnovel-writer/scripts/data_modules/config.py
@property
def story_system_dir(self) -> Path:
    return self.project_root / ".story-system"

@property
def story_system_chapters_dir(self) -> Path:
    return self.story_system_dir / "chapters"

@property
def story_system_master_json(self) -> Path:
    return self.story_system_dir / "MASTER_SETTING.json"

@property
def story_system_anti_patterns_json(self) -> Path:
    return self.story_system_dir / "anti_patterns.json"
```

- [ ] **Step 4: Implement `StoryContractPaths`, Merge Rules, and Marker-Update Helpers**

```python
# webnovel-writer/scripts/data_modules/story_contracts.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List


MARKER_BEGIN = "<!-- STORY-SYSTEM:BEGIN -->"
MARKER_END = "<!-- STORY-SYSTEM:END -->"


@dataclass(frozen=True)
class StoryContractPaths:
    project_root: Path

    @classmethod
    def from_project_root(cls, project_root: str | Path) -> "StoryContractPaths":
        return cls(Path(project_root).expanduser().resolve())

    @property
    def root(self) -> Path:
        return self.project_root / ".story-system"

    @property
    def chapters_dir(self) -> Path:
        return self.root / "chapters"

    @property
    def master_json(self) -> Path:
        return self.root / "MASTER_SETTING.json"

    @property
    def anti_patterns_json(self) -> Path:
        return self.root / "anti_patterns.json"

    def chapter_json(self, chapter: int) -> Path:
        return self.chapters_dir / f"chapter_{chapter:03d}.json"


def merge_contract_layers(master: Dict[str, Any], chapter: Dict[str, Any] | None) -> Dict[str, Any]:
    chapter = chapter or {}
    return {
        "locked": dict(master.get("locked") or {}),
        "append_only": _merge_append_only(master.get("append_only") or {}, chapter.get("append_only") or {}),
        "override_allowed": {
            **(master.get("override_allowed") or {}),
            **(chapter.get("override_allowed") or {}),
        },
    }


def merge_anti_patterns(*groups: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    merged: List[Dict[str, Any]] = []
    for group in groups:
        for row in group:
            text = str(row.get("text") or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            merged.append(dict(row))
    return merged


def read_json_if_exists(path: Path) -> Any | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Bad JSON in {path}") from exc
```

Also add a unified read convention for reuse in Phases 2–4:

- `read_json_if_exists(path) -> dict | list | None`
- Return `None` when a file does not exist
- Raise `ValueError` including the path for malformed JSON
- Implement this helper in `story_contracts.py` now; later projection/runtime builders must not create separate error-swallowing logic

- [ ] **Step 5: Rerun Tests and Confirm the Foundation Passes**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_contracts.py -q --no-cov`

Expected: Pass

- [ ] **Step 6: Commit**

```bash
git add webnovel-writer/scripts/data_modules/config.py \
        webnovel-writer/scripts/data_modules/story_contracts.py \
        webnovel-writer/scripts/data_modules/tests/test_story_contracts.py
git commit -m "feat: add story contract path helpers and merge rules"
```

---

## Task 2: Implement the Genre Routing Table and Contract Aggregator

**Files:**
- Create: `webnovel-writer/references/csv/genre-routing.csv`
- Create: `webnovel-writer/scripts/data_modules/story_system_engine.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py`
- Modify: `webnovel-writer/references/csv/README.md`
- Modify: `webnovel-writer/references/csv/tropes.csv`

- [ ] **Step 1: Write Failing `story_system_engine` Tests First**

```python
# webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv

from data_modules.story_system_engine import StorySystemEngine


def _write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def test_story_system_routes_explicit_genre_and_collects_anti_patterns(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "genre_aliases", "core_tone",
            "pacing_strategy", "mandatory prohibitions/pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001",
                "applicable_skills": "write|plan",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "broken-engagement-fantasy|broken-engagement vindication",
                "intent_synonyms": "broken-engagement fiction|underdog comeback",
                "applicable_genres": "xuanhuan",
                "model_instruction": "establish pressure first，then deliver an explosive payoff。",
                "summary": "Broken-engagement fantasy requires initial humiliation and a strong payoff。",
                "details": "",
                "genre_route": "broken-engagement-fantasy",
                "genre_aliases": "broken-engagement fiction|underdog comeback",
                "core_tone": "build pressure before an explosive counterattack",
                "pacing_strategy": "pressure before release，first counterattack must occur within three chapters",
                "mandatory prohibitions/pitfalls": "Vindication pacing must include the final decisive beat|Supporting characters must not overshadow the payoff earned by the protagonist",
                "recommended_base_tables": "naming|characters|powers",
                "recommended_dynamic_tables": "tropes|pacing|scenes",
                "default_query": "broken engagement|vindication|underdog comeback",
            }
        ],
    )

    _write_csv(
        csv_dir / "tropes.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "trope_name", "prohibited approaches"],
        [
            {
                "id": "TR-001",
                "applicable_skills": "write",
                "category": "trope",
                "level": "knowledge",
                "keywords": "broken engagement|vindication",
                "applicable_genres": "xuanhuan",
                "summary": "allow sufficient humiliation and counterattack in the broken-engagement scene",
                "trope_name": "broken-engagement counterattack",
                "prohibited approaches": "A supporting character intervenes on behalf of the protagonist before the protagonist can counterattack",
            }
        ],
    )

    _write_csv(
        csv_dir / "pacing.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "common failure modes", "pacing_type"],
        [
            {
                "id": "PA-001",
                "applicable_skills": "write",
                "category": "pacing",
                "level": "knowledge",
                "keywords": "vindication|payoff",
                "applicable_genres": "xuanhuan",
                "summary": "payoffs require decisive follow-through",
                "common failure modes": "vindication ends too weakly，without readeremotiondecisive follow-through",
                "pacing_type": "eruption phase",
            }
        ],
    )

    engine = StorySystemEngine(csv_dir=csv_dir)
    contract = engine.build(query="broken-engagement-fantasy", genre=None, chapter=None)

    assert contract["master_setting"]["route"]["primary_genre"] == "broken-engagement-fantasy"
    assert contract["master_setting"]["master_constraints"]["core_tone"] == "build pressure before an explosive counterattack"
    assert "naming" in contract["master_setting"]["route"]["recommended_base_tables"]
    assert {
        item["text"] for item in contract["anti_patterns"]
    } >= {
        "Vindication pacing must include the final decisive beat",
        "A supporting character intervenes on behalf of the protagonist before the protagonist can counterattack",
        "vindication ends too weakly，without readeremotiondecisive follow-through",
    }


def test_story_system_falls_back_to_explicit_genre(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "genre_aliases", "core_tone",
            "pacing_strategy", "mandatory prohibitions/pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [],
    )

    engine = StorySystemEngine(csv_dir=csv_dir)
    contract = engine.build(query="add some pressure，release it later", genre="contemporary-romance", chapter=None)

    assert contract["master_setting"]["route"]["primary_genre"] == "contemporary-romance"
    assert contract["master_setting"]["route"]["route_source"] == "explicit_genre_fallback"
    assert contract["master_setting"]["route"]["recommended_dynamic_tables"] == ["tropes", "pacing", "scenes"]
```

- [ ] **Step 2: Confirm Tests Fail Because the Aggregator Is Missing, Not Because Tests Are Invalid**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py -q --no-cov`

Expected: `ModuleNotFoundError: No module named 'data_modules.story_system_engine'`

- [ ] **Step 3: Implement `StorySystemEngine` and Anti-Pattern Normalization Mappings**

```python
# webnovel-writer/scripts/data_modules/story_system_engine.py
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from reference_search import search as search_reference

from .story_contracts import merge_anti_patterns


ANTI_PATTERN_SOURCE_FIELDS = {
    "scenes": ["negative examples"],
    "techniques": ["common pitfalls"],
    "pacing": ["common failure modes"],
    "characters": ["prohibited approaches"],
    "tropes": ["prohibited approaches"],
    "genre-routing": ["mandatory prohibitions/pitfalls"],
}


class StorySystemEngine:
    def __init__(self, csv_dir: str | Path):
        self.csv_dir = Path(csv_dir)

    def build(self, query: str, genre: Optional[str], chapter: Optional[int]) -> Dict[str, Any]:
        route = self._route(query=query, genre=genre)
        base_context = self._collect_tables(query, route["recommended_base_tables"], genre=route["genre_filter"], top_k=1)
        dynamic_context = self._collect_tables(query, route["recommended_dynamic_tables"], genre=route["genre_filter"], top_k=2)
        source_trace = route["source_trace"] + self._build_source_trace(base_context, dynamic_context)
        anti_patterns = merge_anti_patterns(
            route["route_anti_patterns"],
            self._extract_anti_patterns(base_context),
            self._extract_anti_patterns(dynamic_context),
        )
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
                "base_context": base_context,
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
                    "dynamic_context": dynamic_context,
                    "source_trace": source_trace,
                }
                if chapter is not None
                else None
            ),
            "anti_patterns": anti_patterns,
        }

    def _route(self, query: str, genre: Optional[str]) -> Dict[str, Any]:
        route_rows = self._load_csv_rows("genre-routing")
        query_text = self._normalize_text(" ".join([query or "", genre or ""]))

        # Fixed match order: keyword/synonym match -> explicit genre fallback -> default first-row fallback
        matched = None
        for row in route_rows:
            aliases = self._split_multi_value(row.get("keywords")) + self._split_multi_value(row.get("intent_synonyms")) + self._split_multi_value(row.get("genre_aliases"))
            if any(alias and alias in query_text for alias in aliases):
                matched = row
                route_source = "keyword_or_alias_match"
                break
        if matched is None and genre:
            matched = self._fallback_row_for_genre(route_rows, genre)
            route_source = "explicit_genre_fallback"
        if matched is None and route_rows:
            matched = route_rows[0]
            route_source = "default_seed_fallback"
        if matched is None:
            return self._empty_route(query=query, genre=genre)

        primary_genre = str(matched.get("genre_route") or genre or "").strip()
        genre_filter = str(matched.get("applicable_genres") or genre or primary_genre).strip()
        return {
            "meta": {
                "primary_genre": primary_genre,
                "route_source": route_source,
                "genre_filter": genre_filter,
                "recommended_base_tables": self._split_multi_value(matched.get("recommended_base_tables")),
                "recommended_dynamic_tables": self._split_multi_value(matched.get("recommended_dynamic_tables")),
            },
            "core_tone": str(matched.get("core_tone") or "").strip(),
            "pacing_strategy": str(matched.get("pacing_strategy") or "").strip(),
            "route_anti_patterns": self._extract_route_anti_patterns(matched),
            "recommended_base_tables": self._split_multi_value(matched.get("recommended_base_tables")),
            "recommended_dynamic_tables": self._split_multi_value(matched.get("recommended_dynamic_tables")),
            "genre_filter": genre_filter,
            "source_trace": [{"table": "genre-routing", "id": matched.get("id", ""), "reason": route_source}],
        }

    def _collect_tables(self, query: str, tables: List[str], genre: str, top_k: int) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for table_name in tables:
            result = search_reference(
                csv_dir=self.csv_dir,
                skill="write",
                query=query,
                table=table_name,
                genre=genre,
                max_results=top_k,
            )
            rows.extend(result.get("data", {}).get("results", []))
        return rows

    def _extract_anti_patterns(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        extracted: List[Dict[str, Any]] = []
        for row in rows:
            table_name = str(row.get("_table") or "")
            for field_name in ANTI_PATTERN_SOURCE_FIELDS.get(table_name, []):
                for text in self._split_multi_value(row.get(field_name)):
                    extracted.append({"text": text, "source_table": table_name, "source_id": row.get("id", "")})
        return extracted

    def _suggest_chapter_focus(self, query: str, dynamic_rows: List[Dict[str, Any]]) -> str:
        for row in dynamic_rows:
            summary = str(row.get("summary") or "").strip()
            if summary:
                return summary
        return query

    def _build_source_trace(self, *groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        trace: List[Dict[str, Any]] = []
        for group in groups:
            for row in group:
                trace.append(
                    {
                        "table": row.get("_table", ""),
                        "id": row.get("id", ""),
                        "summary": row.get("summary", ""),
                    }
                )
        return trace

    def _load_csv_rows(self, table_name: str) -> List[Dict[str, Any]]:
        csv_path = self.csv_dir / f"{table_name}.csv"
        if not csv_path.is_file():
            return []
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def _normalize_text(self, text: str) -> str:
        return str(text or "").strip().lower()

    def _split_multi_value(self, raw: Any) -> List[str]:
        return [item.strip() for item in str(raw or "").split("|") if item.strip()]

    def _fallback_row_for_genre(self, rows: List[Dict[str, Any]], genre: str) -> Dict[str, Any] | None:
        genre = str(genre or "").strip()
        for row in rows:
            if genre and genre in self._split_multi_value(row.get("applicable_genres")):
                return row
        return None

    def _extract_route_anti_patterns(self, row: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {"text": text, "source_table": "genre-routing", "source_id": row.get("id", "")}
            for text in self._split_multi_value(row.get("mandatory prohibitions/pitfalls"))
        ]

    def _empty_route(self, query: str, genre: Optional[str]) -> Dict[str, Any]:
        fallback_genre = str(genre or "no matchgenre").strip()
        return {
            "meta": {
                "primary_genre": fallback_genre,
                "route_source": "empty_csv_fallback",
                "genre_filter": fallback_genre,
                "recommended_base_tables": ["naming", "characters"],
                "recommended_dynamic_tables": ["tropes", "pacing", "scenes"],
            },
            "core_tone": "",
            "pacing_strategy": "",
            "route_anti_patterns": [],
            "recommended_base_tables": ["naming", "characters"],
            "recommended_dynamic_tables": ["tropes", "pacing", "scenes"],
            "genre_filter": fallback_genre,
            "source_trace": [{"table": "genre-routing", "id": "", "reason": f"empty_route_for:{query}"}],
        }
```

Explicit test-strategy constraints:

- Pass `tmp_path / csv` directly to `reference_search.search()`
- Do not monkeypatch the search function
- If `reference_search.search()` changes later, update the aggregator wrapper instead of bypassing the real interface in tests

- [ ] **Step 4: Add Real CSV Data and Field Documentation**

Start `genre-routing.csv` with at least three manually curated seed rows covering:

```csv
id,applicable_skills,category,level,keywords,intent_synonyms,applicable_genres,model_instruction,summary,details,genre_route,genre_aliases,core_tone,pacing_strategy,main-conflict template,requiredpayoff,mandatory prohibitions/pitfalls,recommended_base_tables,recommended_dynamic_tables,base retrieval weights,dynamic retrieval weights,default_query
GR-001,write|plan,genre-routing,knowledge,broken-engagement-fantasy|broken-engagement vindication,broken-engagement fiction|underdog comeback,xuanhuan,pressure before release，the first counterattack must rebound from humiliation,Broken-engagement fantasy requires initial humiliation and a strong payoff,,broken-engagement-fantasy,broken-engagement fiction|underdog comeback,build pressure before an explosive counterattack,pressure before release，first counterattack must occur within three chapters,humiliation from a broken engagement→resource competition→immediate counterattack,public counterattack|identity-based comeback,Vindication pacing must include the final decisive beat|Supporting characters must not overshadow the payoff earned by the protagonist,naming|characters|powers,tropes|pacing|scenes,naming:1.0|characters:0.9,tropes:1.0|pacing:0.9,broken engagement|vindication|underdog comeback
GR-002,write|plan,genre-routing,knowledge,rules-horror-zoo|uncanny talesscenario,rules-horror|zoorule,mystery|light novel,ruleestablish firmly first，costs must materialize,rules-horror-zoofocuses onrulepressure and the cost of trial and error,,rules-horror-zoo,rules-horror|zoorule,uncannypressure and detached observation,at least one per chapterrulevalidation or consequence of misjudgment,park entryrule→sacrifice during trial and error→discover hiddenrule,rulereversal|make the cost of mistakes tangible,ruleexcessive explanation|the system reveals the truth prematurely,naming|characters,tropes|scenes|techniques,naming:0.7|characters:0.8,scenes:1.0|techniques:0.9,rule|zoo|scenario
GR-003,write|plan,genre-routing,knowledge,suppression-then-eruption|later stagescomeback,build pressure before releasing it later|early frustration followed bycomeback,contemporary-romance|urban,pressure must not be wasted，must attach to a later payoff asset,suppression-then-eruptionthe route must continually accumulate potential for a reversal,,suppression-then-eruption,frustration before eruption|later stagescomeback,concentrated eruption after sustained pressure,every 2-3 chapters must include one visible signal of resistance,accumulating pressure→counterattack after misjudgment→emotionoverall payoff,emotionclimactic beat|identityreversal,pressure without reward|humiliation conveyed only through forced narration,naming|characters|techniques,pacing|scenes|tropes,techniques:0.9|characters:0.8,pacing:1.0|scenes:0.8,pressure|comeback|rebound
```

Also add `prohibited approaches` to `tropes.csv` and add the following to `references/csv/README.md`:

```markdown
### genre-routing.csv

| Column | Description |
|------|------|
| `genre_route` | Primary routing label |
| `genre_aliases` | Synonyms / platform slang |
| `core_tone` | Global emotional tone |
| `pacing_strategy` | Opening and payoff pacing |
| `mandatory prohibitions/pitfalls` | Absolute genre-level red lines |
| `recommended_base_tables` | Default base retrieval tables |
| `recommended_dynamic_tables` | Default dynamic retrieval tables |
```

- [ ] **Step 5: Rerun Tests and Confirm Routing + Aggregation Contracts Pass**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py -q --no-cov`

Expected: Pass

- [ ] **Step 6: Commit**

```bash
git add webnovel-writer/references/csv/genre-routing.csv \
        webnovel-writer/references/csv/tropes.csv \
        webnovel-writer/references/csv/README.md \
        webnovel-writer/scripts/data_modules/story_system_engine.py \
        webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py
git commit -m "feat: add genre routing csv and story system engine"
```

---

## Task 3: Implement `.story-system` Persistence and Unified CLI Integration

**Files:**
- Create: `webnovel-writer/scripts/story_system.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_story_system_cli.py`
- Modify: `webnovel-writer/scripts/data_modules/story_contracts.py`
- Modify: `webnovel-writer/scripts/data_modules/webnovel.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`

- [ ] **Step 1: Write Failing `--persist` and Unified CLI Forwarding Tests First**

```python
# webnovel-writer/scripts/data_modules/tests/test_story_system_cli.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import sys


def _write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def test_story_system_persist_writes_master_chapter_and_anti_patterns(tmp_path, monkeypatch):
    project_root = tmp_path / "book"
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")

    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()
    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "genre_aliases", "core_tone",
            "pacing_strategy", "mandatory prohibitions/pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001",
                "applicable_skills": "write",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "broken-engagement-fantasy",
                "intent_synonyms": "broken-engagement fiction",
                "applicable_genres": "xuanhuan",
                "model_instruction": "pressure before release",
                "summary": "open with a broken engagement",
                "details": "",
                "genre_route": "broken-engagement-fantasy",
                "genre_aliases": "broken-engagement fiction",
                "core_tone": "pressure before release",
                "pacing_strategy": "counterattack within three chapters",
                "mandatory prohibitions/pitfalls": "vindication must not end weakly",
                "recommended_base_tables": "naming",
                "recommended_dynamic_tables": "tropes",
                "default_query": "broken engagement|vindication",
            }
        ],
    )
    _write_csv(csv_dir / "naming.csv", ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"], [])
    _write_csv(csv_dir / "tropes.csv", ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "prohibited approaches"], [])

    from story_system import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "story_system",
            "broken-engagement-fantasy",
            "--project-root",
            str(project_root),
            "--chapter",
            "1",
            "--persist",
            "--csv-dir",
            str(csv_dir),
            "--format",
            "both",
        ],
    )
    main()

    story_root = project_root / ".story-system"
    assert (story_root / "MASTER_SETTING.json").is_file()
    assert (story_root / "MASTER_SETTING.md").is_file()
    assert (story_root / "anti_patterns.json").is_file()
    assert (story_root / "chapters" / "chapter_001.json").is_file()
    assert (story_root / "chapters" / "chapter_001.md").is_file()

    payload = json.loads((story_root / "MASTER_SETTING.json").read_text(encoding="utf-8"))
    assert payload["route"]["primary_genre"] == "broken-engagement-fantasy"


def test_markdown_writer_preserves_manual_notes_outside_markers(tmp_path):
    from data_modules.story_contracts import write_marked_markdown

    target = tmp_path / "MASTER_SETTING.md"
    target.write_text(
        "# manualdescription\nmanual note\n<!-- STORY-SYSTEM:BEGIN -->\nold content\n<!-- STORY-SYSTEM:END -->\n",
        encoding="utf-8",
    )

    write_marked_markdown(target, "## Auto\nnew content\n")

    text = target.read_text(encoding="utf-8")
    assert "# manualdescription" in text
    assert "manual note" in text
    assert "## Auto" in text
    assert "old content" not in text
```

Add to `test_webnovel_unified_cli.py`:

```python
def test_webnovel_story_system_forwards_with_resolved_project_root(monkeypatch, tmp_path):
    from data_modules import webnovel as cli

    project_root = tmp_path / "book"
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")

    called = {}

    def _fake_run_script(script_name, argv):
        called["script_name"] = script_name
        called["argv"] = argv
        return 0

    monkeypatch.setattr(cli, "_run_script", _fake_run_script)
    monkeypatch.setattr(sys, "argv", ["webnovel", "--project-root", str(project_root), "story-system", "broken-engagement-fantasy"])

    cli.main()

    assert called["script_name"] == "story_system.py"
    assert called["argv"][:2] == ["--project-root", str(project_root.resolve())]
```

- [ ] **Step 2: Run and Confirm Failing Tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_system_cli.py webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py -q --no-cov`

Expected: Failure due to `No module named 'story_system'` or unimplemented `write_marked_markdown`

- [ ] **Step 3: Implement Persistence Writers and the `story_system.py` CLI**

Add persistence functions to `story_contracts.py`. Enforce this boundary: **each `.md` file may contain only one `<!-- STORY-SYSTEM:BEGIN/END -->` marker pair**. Raise `ValueError` for multiple pairs to prevent leftover partial overrides in Phase 2 and later.

```python
def write_marked_markdown(path: Path, generated_block: str) -> None:
    wrapped = f"{MARKER_BEGIN}\n{generated_block.rstrip()}\n{MARKER_END}\n"
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if current.count(MARKER_BEGIN) > 1 or current.count(MARKER_END) > 1:
            raise ValueError(f"{path} contains multiple STORY-SYSTEM markers")
        if MARKER_BEGIN in current and MARKER_END in current:
            before, _, rest = current.partition(MARKER_BEGIN)
            _, _, after = rest.partition(MARKER_END)
            path.write_text(f"{before}{wrapped}{after.lstrip()}", encoding="utf-8")
            return
    path.write_text(wrapped, encoding="utf-8")


def render_master_markdown(master_payload: dict) -> str:
    route = master_payload.get("route") or {}
    constraints = master_payload.get("master_constraints") or {}
    return "\n".join(
        [
            "# MASTER_SETTING",
            f"- genre：{route.get('primary_genre', '')}",
            f"- tone：{constraints.get('core_tone', '')}",
            f"- pacing：{constraints.get('pacing_strategy', '')}",
        ]
    )


def render_anti_patterns_markdown(anti_patterns: list[dict]) -> str:
    lines = ["# ANTI_PATTERNS"]
    for row in anti_patterns:
        lines.append(f"- {row.get('text', '')}")
    return "\n".join(lines)


def render_chapter_markdown(chapter_payload: dict) -> str:
    focus = (chapter_payload.get("override_allowed") or {}).get("chapter_focus", "")
    return "\n".join(
        [
            f"# CHAPTER_{int(chapter_payload['meta']['chapter']):03d}",
            f"- chapterfocus：{focus}",
        ]
    )


def persist_story_seed(project_root: Path, master_payload: dict, chapter_payload: dict | None, anti_patterns: list[dict]) -> None:
    paths = StoryContractPaths.from_project_root(project_root)
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.chapters_dir.mkdir(parents=True, exist_ok=True)
    write_json(paths.master_json, master_payload)
    write_json(paths.anti_patterns_json, anti_patterns)
    write_marked_markdown(paths.master_json.with_suffix(".md"), render_master_markdown(master_payload))
    write_marked_markdown(paths.anti_patterns_json.with_suffix(".md"), render_anti_patterns_markdown(anti_patterns))
    if chapter_payload is not None:
        chapter_num = int(chapter_payload["meta"]["chapter"])
        write_json(paths.chapter_json(chapter_num), chapter_payload)
        write_marked_markdown(paths.chapter_json(chapter_num).with_suffix(".md"), render_chapter_markdown(chapter_payload))
```

Add the CLI entry point:

```python
# webnovel-writer/scripts/story_system.py
def main() -> None:
    parser = argparse.ArgumentParser(description="Story System aggregator")
    parser.add_argument("query", help="genredescription or current intent")
    parser.add_argument("--project-root", help="book project root or workspace root")
    parser.add_argument("--genre", default="", help="explicitgenre")
    parser.add_argument("--chapter", type=int, default=0, help="chapternumber")
    parser.add_argument("--persist", action="store_true", help="write PROJECT_ROOT/.story-system/")
    parser.add_argument("--format", choices=["json", "markdown", "both"], default="json")
    parser.add_argument("--csv-dir", default="", help="override during tests CSV directory")
    args = parser.parse_args()

    project_root = resolve_project_root(args.project_root) if args.project_root else resolve_project_root()
    csv_dir = Path(args.csv_dir) if args.csv_dir else Path(__file__).resolve().parent.parent / "references" / "csv"

    engine = StorySystemEngine(csv_dir=csv_dir)
    payload = engine.build(query=args.query, genre=args.genre or None, chapter=args.chapter or None)
    if args.persist:
        persist_story_seed(project_root, payload["master_setting"], payload.get("chapter_brief"), payload["anti_patterns"])
```

- [ ] **Step 4: Register `story-system` in the Unified `webnovel.py` CLI**

```python
# webnovel-writer/scripts/data_modules/webnovel.py
p_story_system = sub.add_parser("story-system", help="forward to story_system.py")
p_story_system.add_argument("args", nargs=argparse.REMAINDER)

# main() routing branch
elif args.tool == "story-system":
    forward_args = ["--project-root", str(project_root), *(_strip_project_root_args(args.args))]
    raise SystemExit(_run_script("story_system.py", forward_args))
```

- [ ] **Step 5: Rerun Tests and Confirm Persistence and CLI Contracts Pass**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_system_cli.py webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py -q --no-cov`

Expected: Pass

- [ ] **Step 6: Commit**

```bash
git add webnovel-writer/scripts/story_system.py \
        webnovel-writer/scripts/data_modules/story_contracts.py \
        webnovel-writer/scripts/data_modules/webnovel.py \
        webnovel-writer/scripts/data_modules/tests/test_story_system_cli.py \
        webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py
git commit -m "feat: persist story system seed contracts and expose unified cli"
```

---

## Task 4: Connect Contract Seeds to `context_manager` and `extract_chapter_context`

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/context_manager.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_context_manager.py`
- Modify: `webnovel-writer/scripts/extract_chapter_context.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py`

- [ ] **Step 1: Write Failing Contract-Read Entry-Point Tests First**

Add to `test_context_manager.py`:

```python
def test_context_manager_includes_story_contract_section_before_genre_profile(temp_project):
    state = {
        "genre": "xuanhuan",
        "protagonist_state": {"name": "Xiao Yan"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    story_root = temp_project.project_root / ".story-system"
    (story_root / "chapters").mkdir(parents=True, exist_ok=True)
    (story_root / "MASTER_SETTING.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING", "query": "broken-engagement-fantasy"},
                "route": {"primary_genre": "broken-engagement-fantasy"},
                "master_constraints": {"core_tone": "pressure before release"},
                "base_context": [],
                "source_trace": [],
                "override_policy": {"locked": ["route.primary_genre"], "append_only": ["anti_patterns"], "override_allowed": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "anti_patterns.json").write_text(
        json.dumps([{"text": "vindication must not end weakly"}], ensure_ascii=False),
        encoding="utf-8",
    )
    (story_root / "chapters" / "chapter_001.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "CHAPTER_BRIEF", "chapter": 1},
                "override_allowed": {"chapter_focus": "counterattack at the broken-engagement scene"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = ContextManager(temp_project).build_context(1, use_snapshot=False, save_snapshot=False)

    assert "story_contract" in payload["sections"]
    assert payload["sections"]["story_contract"]["content"]["route"]["primary_genre"] == "broken-engagement-fantasy"
    assert payload["sections"]["story_contract"]["content"]["chapter_brief"]["override_allowed"]["chapter_focus"] == "counterattack at the broken-engagement scene"
    assert ContextManager.SECTION_ORDER.index("story_contract") < ContextManager.SECTION_ORDER.index("genre_profile")
```

Add to `test_extract_chapter_context.py`:

```python
def test_build_chapter_context_payload_includes_story_contract(tmp_path):
    from extract_chapter_context import build_chapter_context_payload

    project_root = tmp_path
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text(
        json.dumps({"protagonist_state": {}, "chapter_meta": {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    story_root = project_root / ".story-system"
    (story_root / "chapters").mkdir(parents=True, exist_ok=True)
    (story_root / "MASTER_SETTING.json").write_text(
        json.dumps({"route": {"primary_genre": "rules-horror-zoo"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    (story_root / "anti_patterns.json").write_text(
        json.dumps([{"text": "do not explain the truth prematurely"}], ensure_ascii=False),
        encoding="utf-8",
    )
    (story_root / "chapters" / "chapter_001.json").write_text(
        json.dumps({"override_allowed": {"chapter_focus": "first activation of visitor instructions"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    payload = build_chapter_context_payload(project_root, 1)

    assert payload["story_contract"]["route"]["primary_genre"] == "rules-horror-zoo"
    assert payload["story_contract"]["anti_patterns"][0]["text"] == "do not explain the truth prematurely"
```

- [ ] **Step 2: Run and Confirm Failing Tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_context_manager.py webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py -q --no-cov`

Expected: The `story_contract` section / payload field is missing

- [ ] **Step 3: Add Contract Loading and Section Injection to `context_manager.py`**

```python
# webnovel-writer/scripts/data_modules/context_manager.py
SECTION_ORDER = [
    "core",
    "story_contract",
    "scene",
    "global",
    "reader_signal",
    "genre_profile",
    "writing_guidance",
    "plot_structure",
    "story_skeleton",
    "memory",
    "long_term_memory",
    "preferences",
    "alerts",
]

def _load_story_contract(self, chapter: int) -> Dict[str, Any]:
    paths = StoryContractPaths.from_project_root(self.config.project_root)
    master = read_json_if_exists(paths.master_json)
    chapter_payload = read_json_if_exists(paths.chapter_json(chapter))
    anti_patterns = read_json_if_exists(paths.anti_patterns_json) or []
    if not master and not chapter_payload and not anti_patterns:
        return {}
    return {
        "master_setting": master,
        "chapter_brief": chapter_payload,
        "route": (master or {}).get("route", {}),
        "master_constraints": (master or {}).get("master_constraints", {}),
        "anti_patterns": anti_patterns,
    }

# Insert during pack assembly in _build_pack():
story_contract = self._load_story_contract(chapter)
pack = {
    "meta": {"chapter": chapter},
    "core": core,
    "scene": scene,
    "global": global_ctx,
    "reader_signal": reader_signal,
    "genre_profile": genre_profile,
    "writing_guidance": writing_guidance,
    "plot_structure": plot_structure,
    "story_skeleton": story_skeleton,
    "memory": memory_ctx,
    "long_term_memory": long_term_memory,
    "preferences": preferences,
    "alerts": alerts,
}
if story_contract:
    pack["story_contract"] = story_contract
```

- [ ] **Step 4: Expose `story_contract` Through `extract_chapter_context.py`**

```python
# webnovel-writer/scripts/extract_chapter_context.py
def _load_contract_context(project_root: Path, chapter_num: int) -> Dict[str, Any]:
    manager = ContextManager(get_config(project_root))
    payload = manager.build_context(chapter_num, use_snapshot=False, save_snapshot=False)
    sections = payload.get("sections") or {}
    return {
        "reader_signal": (sections.get("reader_signal") or {}).get("content", {}),
        "genre_profile": (sections.get("genre_profile") or {}).get("content", {}),
        "story_contract": (sections.get("story_contract") or {}).get("content", {}),
        "writing_guidance": (sections.get("writing_guidance") or {}).get("content", {}),
        "plot_structure": (sections.get("plot_structure") or {}).get("content", {}),
        "long_term_memory": (sections.get("long_term_memory") or {}).get("content", {}),
    }
```

Add a compact section to text rendering:

```python
story_contract = payload.get("story_contract") or {}
if story_contract:
    lines.append("## Story Contract")
    route = story_contract.get("route") or {}
    if route.get("primary_genre"):
        lines.append(f"- primary routinggenre: {route['primary_genre']}")
    anti_patterns = story_contract.get("anti_patterns") or []
    for row in anti_patterns[:5]:
        lines.append(f"- red line: {row.get('text')}")
```

- [ ] **Step 5: Rerun Tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_context_manager.py webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py -q --no-cov`

Expected: Pass

- [ ] **Step 6: Commit**

```bash
git add webnovel-writer/scripts/data_modules/context_manager.py \
        webnovel-writer/scripts/data_modules/tests/test_context_manager.py \
        webnovel-writer/scripts/extract_chapter_context.py \
        webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py
git commit -m "feat: load story contract seed into context assembly"
```

---

## Task 5: Update Architecture and Command Documentation; Run Regression Validation

**Files:**
- Create: `docs/architecture/story-system-phase1.md`
- Modify: `README.md`
- Modify: `docs/architecture/overview.md`
- Modify: `docs/guides/commands.md`
- Modify: `docs/superpowers/README.md`

- [ ] **Step 1: Create Phase 1 Architecture Documentation**

Document at least these four sections in `docs/architecture/story-system-phase1.md` so deployed Phase 1 behavior does not revert to implicit conventions:

```markdown
# Story System Phase 1

## JSON Source of Truth
- `PROJECT_ROOT/.story-system/MASTER_SETTING.json`
- `PROJECT_ROOT/.story-system/anti_patterns.json`
- `PROJECT_ROOT/.story-system/chapters/chapter_XXX.json`

## Override Rules
- `locked`: Chapter cannot override
- `append_only`: Chapter may only append
- `override_allowed`: Chapter may override locally

## Runtime Read Order
1. chapter brief
2. master setting
3. anti-patterns
4. genre profile fallback

## Migration Boundaries
- Phase 1 does not introduce `VOLUME_BRIEF`
- Phase 1 does not change the post-writing persistence mainline
- Retain `genre-profiles.md` as a fallback
```

- [ ] **Step 2: Update Command and Overview Documentation**

Add to `docs/guides/commands.md`:

````markdown
## Story System (Phase 1)

```bash
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" \
  --project-root "<WORKSPACE_ROOT>" \
  story-system "broken-engagement-fantasy" --chapter 1 --persist --format both
```

Notes:
- `--project-root` accepts either the workspace root or book-project root
- The actual persistence location is always `PROJECT_ROOT/.story-system/`
- `*.json` is the source of truth; `*.md` is a projection view
````

Add a Phase 1 note to `README.md` and `docs/architecture/overview.md`:

```markdown
- Story System Phase 1 adds a minimal contract seed layer (`MASTER_SETTING` / `chapter_XXX` / `anti_patterns`)
  upstream of `context_manager` contract input.
```

- [ ] **Step 3: Update Navigation in `docs/superpowers/README.md`**

```markdown
- [`plans/2026-04-12-story-system-phase1-contract-seed.md`](./plans/2026-04-12-story-system-phase1-contract-seed.md): Story System Phase 1 contract seed layer implementation plan
```

- [ ] **Step 4: Run the Targeted Phase 1 Test Suite**

Run:

```bash
python -m pytest \
  webnovel-writer/scripts/data_modules/tests/test_story_contracts.py \
  webnovel-writer/scripts/data_modules/tests/test_story_system_engine.py \
  webnovel-writer/scripts/data_modules/tests/test_story_system_cli.py \
  webnovel-writer/scripts/data_modules/tests/test_context_manager.py \
  webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py \
  webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py \
  -q --no-cov
```

Expected: All pass

- [ ] **Step 5: Run `reference_search.py` Regression Tests to Verify the Primitive Is Unbroken**

Run: `python -m pytest webnovel-writer/scripts/tests/test_reference_search.py -q --no-cov`

Expected: Pass

- [ ] **Step 6: Final Commit**

```bash
git add README.md \
        docs/architecture/story-system-phase1.md \
        docs/architecture/overview.md \
        docs/guides/commands.md \
        docs/superpowers/README.md
git commit -m "docs: document story system phase1 contract seed layer"
```

---

## Spec Coverage Check

This plan covers `2026-04-12-story-system-evolution-spec.md` as follows:

- `13.2 Phase 1: Contract seed layer`
  - `genre-routing.csv`: Task 2
  - Minimal `MASTER_SETTING`: Task 3
  - Minimal `CHAPTER_BRIEF`: Task 3
  - `anti_patterns.json`：Task 3
  - Contract reading in `context_manager`: Task 4

- `14.1 / 14.1.1 Path-resolution constraints`
  - `PROJECT_ROOT/.story-system`：Task 1 / Task 3
  - `resolve_project_root(args.project_root)` injected through unified CLI: Task 3

- `15.3 Current-phase conclusion`
  - Retain the CSV + Markdown dual system without automatic migration: Task 2

- `17.1 Documentation update requirements`
  - Contract schemas / directories / workflows / migration documentation: Task 5

- `19. Implementation recommendations`
  - Implement the contract seed layer first without prematurely adding `CHAPTER_COMMIT` or the event log: entire plan

---

## Placeholder Scan

Avoided the following placeholder approaches:

- No “TODO / TBD / fill in later” placeholders
- Test-writing instructions include actual scaffolding, not vague slogans
- Documentation updates name target files rather than merely saying “update docs”
- No Phase 2–4 work is mixed into Phase 1 tasks

---

## Next Plan

After Phase 1 is complete and stable, proceed to the next plans:

1. `Phase 2 Contract-First Runtime`: `VOLUME_BRIEF`, `REVIEW_CONTRACT`, pre-writing prohibitions, fulfillment diffs
2. `Phase 3 Chapter Commit Chain`: `CHAPTER_COMMIT`, accepted/rejected semantics, projection writers
3. `Phase 4 Event Log + Override Ledger`：canonical event log、`contract_override` / `amend_proposal`
