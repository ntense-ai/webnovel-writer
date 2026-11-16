#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import uuid
from pathlib import Path

import pytest

from data_modules.story_system_engine import StorySystemEngine, StorySystemRoutingError
from reference_search import GENRE_CANONICAL


def _write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _make_local_tmp_path() -> Path:
    base_dir = Path(__file__).resolve().parents[4] / ".tmp_story_system_engine"
    base_dir.mkdir(exist_ok=True)
    tmp_dir = base_dir / f"case_{uuid.uuid4().hex}"
    tmp_dir.mkdir()
    return tmp_dir


def test_story_system_routes_explicit_genre_and_collects_anti_patterns():
    csv_dir = _make_local_tmp_path() / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "canonical_genre", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001",
                "applicable_skills": "story-system",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "broken-engagement-fantasy|broken-engagement vindication",
                "intent_synonyms": "broken-engagement story|underdog comeback",
                "applicable_genres": "xuanhuan",
                "model_instruction": "establish pressure first，then deliver the explosive payoff。",
                "summary": "xuanhuan broken-engagement stories need humiliation followed by strong payoff。",
                "details": "",
                "genre_route": "broken-engagement-fantasy",
                "canonical_genre": "xuanhuan",
                "genre_aliases": "broken-engagement story|underdog comeback",
                "core_tone": "build pressure before an explosive counterattack",
                "pacing_strategy": "pressure followed by eruption，first counterattack required within three chapters",
                "pitfalls": "vindication requires the final extra payoff beat|supporting characters must not overshadow the protagonist's payoff",
                "recommended_base_tables": "naming|characters|powers",
                "recommended_dynamic_tables": "tropes|pacing|scenes",
                "default_query": "broken engagement|public vindication|underdog comeback",
            }
        ],
    )

    _write_csv(
        csv_dir / "tropes.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "trope_name", "pitfalls"],
        [
            {
                "id": "TR-001",
                "applicable_skills": "write",
                "category": "trope",
                "level": "knowledge",
                "keywords": "broken engagement|public vindication",
                "applicable_genres": "xuanhuan",
                "summary": "allow space for humiliation and retaliation in the broken-engagement scene",
                "trope_name": "broken-engagement counterattack",
                "pitfalls": "a supporting character acts before the protagonist can counterattack",
            }
        ],
    )

    _write_csv(
        csv_dir / "pacing.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "pitfalls", "pacing_type"],
        [
            {
                "id": "PA-001",
                "applicable_skills": "write",
                "category": "pacing",
                "level": "knowledge",
                "keywords": "public vindication|payoff",
                "applicable_genres": "xuanhuan",
                "summary": "payoff requires a final beat",
                "pitfalls": "vindication ending too weak，missing final emotional payoff",
                "pacing_type": "payoff phase",
            }
        ],
    )

    _write_csv(
        csv_dir / "adjudication.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre", "style_priority", "payoff_priority",
            "default_pacing_strategy", "pitfall_weight", "conflict_resolution", "contract_injection_layer", "anti_pattern",
        ],
        [
            {
                "id": "RS-001",
                "applicable_skills": "story-system",
                "category": "adjudication",
                "level": "reasoning",
                "keywords": "xuanhuan",
                "intent_synonyms": "how to write xuanhuan",
                "applicable_genres": "xuanhuan",
                "model_instruction": "sort matching rows by adjudication priority",
                "summary": "xuanhuan adjudication rules",
                "details": "",
                "genre": "xuanhuan",
                "style_priority": "fiery conflict > cold calculation",
                "payoff_priority": "overwhelming power > comeback against adversity",
                "default_pacing_strategy": "fast buildup and slow resolution",
                "pitfall_weight": "indiscriminate self-sacrifice > labeling emotions > logic discontinuity",
                "conflict_resolution": "pacing > tropes > scenes",
                "contract_injection_layer": "CHAPTER_BRIEF.writing_guidance",
                "anti_pattern": "labeling emotions|illogical character behavior",
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
        "vindication requires the final extra payoff beat",
        "a supporting character acts before the protagonist can counterattack",
        "vindication ending too weak，missing final emotional payoff",
    }


def test_story_system_falls_back_to_explicit_genre():
    csv_dir = _make_local_tmp_path() / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "canonical_genre", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-010",
                "applicable_skills": "story-system",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "sweet romantic daily life",
                "intent_synonyms": "",
                "applicable_genres": "contemporary-romance",
                "model_instruction": "",
                "summary": "",
                "details": "",
                "genre_route": "contemporary-romance",
                "canonical_genre": "contemporary-romance",
                "genre_aliases": "",
                "core_tone": "",
                "pacing_strategy": "",
                "pitfalls": "",
                "recommended_base_tables": "naming|characters",
                "recommended_dynamic_tables": "tropes|pacing|scenes",
                "default_query": "",
            }
        ],
    )

    engine = StorySystemEngine(csv_dir=csv_dir)
    contract = engine.build(query="increase pressure slightly，payoff later", genre="contemporary-romance", chapter=None)

    assert contract["master_setting"]["route"]["primary_genre"] == "contemporary-romance"
    assert contract["master_setting"]["route"]["route_source"] == "explicit_genre_fallback"
    assert contract["master_setting"]["route"]["recommended_dynamic_tables"] == ["tropes", "pacing", "scenes"]


def test_story_system_unmatched_genre_raises_routing_error():
    csv_dir = _make_local_tmp_path() / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "canonical_genre", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001",
                "applicable_skills": "story-system",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "broken-engagement-fantasy|broken-engagement vindication",
                "intent_synonyms": "broken-engagement story|underdog comeback",
                "applicable_genres": "xuanhuan",
                "model_instruction": "",
                "summary": "",
                "details": "",
                "genre_route": "broken-engagement-fantasy",
                "canonical_genre": "xuanhuan",
                "genre_aliases": "broken-engagement story",
                "core_tone": "",
                "pacing_strategy": "",
                "pitfalls": "",
                "recommended_base_tables": "naming",
                "recommended_dynamic_tables": "tropes",
                "default_query": "",
            }
        ],
    )

    engine = StorySystemEngine(csv_dir=csv_dir)

    with pytest.raises(StorySystemRoutingError) as exc:
        engine.build(query="Cyber Chef", genre="Cyber Chef", chapter=None)

    message = str(exc.value)
    assert "Cyber Chef" in message
    assert "no route matched" in message
    assert "broken-engagement-fantasy" not in message


def test_story_system_routes_chinese_rules_mystery_to_canonical_suspense():
    csv_dir = Path(__file__).resolve().parents[3] / "references" / "csv"

    contract = StorySystemEngine(csv_dir=csv_dir).build(
        query="rules-horror",
        genre="rules-horror",
        chapter=None,
    )

    route = contract["master_setting"]["route"]
    assert route["canonical_genre"] == "mystery"
    assert route["genre_filter"] == "mystery"
    assert route["route_source"] != "default_seed_fallback"


def test_story_system_routes_every_real_route_row():
    csv_dir = Path(__file__).resolve().parents[3] / "references" / "csv"
    engine = StorySystemEngine(csv_dir=csv_dir)
    route_rows = engine._load_csv_rows("genre-routing")

    assert route_rows
    for row in route_rows:
        aliases = (
            engine._split_multi_value(row.get("keywords"))
            + engine._split_multi_value(row.get("intent_synonyms"))
            + engine._split_multi_value(row.get("genre_aliases"))
        )
        query = next((value for value in aliases if value), row.get("genre_route") or row.get("canonical_genre") or "")
        contract = engine.build(query=query, genre=None, chapter=None)
        route = contract["master_setting"]["route"]

        canonical = route["canonical_genre"]
        assert canonical in GENRE_CANONICAL or canonical == "all"
        if canonical == "all":
            assert route["genre_filter"] == ""
        else:
            assert route["genre_filter"] == canonical
        assert route["route_source"] in {
            "keyword_or_alias_match",
            "explicit_genre_fallback",
            "inferred_genre_fallback",
        }


def test_story_system_accepts_english_explicit_genre():
    csv_dir = Path(__file__).resolve().parents[3] / "references" / "csv"
    for query in ("rules-mystery", "rules-horror"):
        result = StorySystemEngine(csv_dir=csv_dir).build(
            query=query, genre="rules-horror", chapter=None,
        )
        assert result["master_setting"]["route"]["canonical_genre"] == "mystery"
        assert result["master_setting"]["route"]["primary_genre"] == "rules-horror-zoo"
        assert result["meta"]["explicit_genre"] == "rules-horror"


def test_route_output_includes_canonical_genre():
    csv_dir = _make_local_tmp_path() / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "canonical_genre", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001",
                "applicable_skills": "story-system",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "broken-engagement-fantasy|broken-engagement vindication",
                "intent_synonyms": "broken-engagement story|underdog comeback",
                "applicable_genres": "xuanhuan|xianxia",
                "model_instruction": "establish pressure first，then deliver the explosive payoff。",
                "summary": "xuanhuan broken-engagement stories need humiliation followed by strong payoff。",
                "details": "",
                "genre_route": "broken-engagement-fantasy",
                "canonical_genre": "xuanhuan",
                "genre_aliases": "broken-engagement story|underdog comeback",
                "core_tone": "build pressure before an explosive counterattack",
                "pacing_strategy": "pressure followed by eruption，first counterattack required within three chapters",
                "pitfalls": "",
                "recommended_base_tables": "naming|characters|powers",
                "recommended_dynamic_tables": "tropes|pacing|scenes",
                "default_query": "broken engagement|public vindication|underdog comeback",
            }
        ],
    )

    engine = StorySystemEngine(csv_dir=csv_dir)
    route = engine._route("broken-engagement story three-year challenge", "xuanhuan")

    assert route["meta"]["canonical_genre"] == "xuanhuan"
    assert route["meta"]["genre_filter"] == "xuanhuan"
    assert route["genre_filter"] == "xuanhuan"


def test_route_infers_canonical_genre_from_spaced_query():
    csv_dir = _make_local_tmp_path() / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "canonical_genre", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001",
                "applicable_skills": "story-system",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "broken-engagement-fantasy|broken-engagement story",
                "intent_synonyms": "",
                "applicable_genres": "xuanhuan",
                "model_instruction": "",
                "summary": "",
                "details": "",
                "genre_route": "broken-engagement-fantasy",
                "canonical_genre": "xuanhuan",
                "genre_aliases": "broken-engagement story",
                "core_tone": "pressure before payoff",
                "pacing_strategy": "",
                "pitfalls": "",
                "recommended_base_tables": "naming",
                "recommended_dynamic_tables": "tropes",
                "default_query": "",
            },
            {
                "id": "GR-025",
                "applicable_skills": "story-system",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "transmigration-missions|courtship system",
                "intent_synonyms": "",
                "applicable_genres": "quick-transmigration",
                "model_instruction": "",
                "summary": "",
                "details": "",
                "genre_route": "transmigration-missions",
                "canonical_genre": "quick-transmigration",
                "genre_aliases": "small world|world-hopping mission",
                "core_tone": "task driven",
                "pacing_strategy": "",
                "pitfalls": "",
                "recommended_base_tables": "characters",
                "recommended_dynamic_tables": "tropes",
                "default_query": "",
            },
        ],
    )

    engine = StorySystemEngine(csv_dir=csv_dir)
    route = engine._route("quick-transmigration mission original host", None)

    assert route["meta"]["primary_genre"] == "transmigration-missions"
    assert route["meta"]["canonical_genre"] == "quick-transmigration"
    assert route["meta"]["route_source"] == "inferred_genre_fallback"


def test_build_uses_canonical_genre_for_reasoning_lookup():
    csv_dir = _make_local_tmp_path() / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "canonical_genre", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001",
                "applicable_skills": "story-system",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "broken-engagement-fantasy|broken-engagement vindication",
                "intent_synonyms": "broken-engagement story|underdog comeback",
                "applicable_genres": "xuanhuan|xianxia",
                "model_instruction": "establish pressure first，then deliver the explosive payoff。",
                "summary": "xuanhuan broken-engagement stories need humiliation followed by strong payoff。",
                "details": "",
                "genre_route": "broken-engagement-fantasy",
                "canonical_genre": "xuanhuan",
                "genre_aliases": "broken-engagement story|underdog comeback",
                "core_tone": "build pressure before an explosive counterattack",
                "pacing_strategy": "pressure followed by eruption，first counterattack required within three chapters",
                "pitfalls": "",
                "recommended_base_tables": "naming",
                "recommended_dynamic_tables": "tropes|pacing",
                "default_query": "broken engagement|public vindication|underdog comeback",
            }
        ],
    )

    _write_csv(
        csv_dir / "adjudication.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre", "style_priority", "payoff_priority",
            "default_pacing_strategy", "pitfall_weight", "conflict_resolution", "contract_injection_layer", "anti_pattern",
        ],
        [
            {
                "id": "RS-001",
                "applicable_skills": "story-system",
                "category": "adjudication",
                "level": "reasoning",
                "keywords": "xuanhuan",
                "intent_synonyms": "how to write xuanhuan",
                "applicable_genres": "xuanhuan",
                "model_instruction": "sort matching rows by adjudication priority",
                "summary": "xuanhuan adjudication rules",
                "details": "",
                "genre": "xuanhuan",
                "style_priority": "fiery conflict > cold calculation",
                "payoff_priority": "overwhelming power > comeback against adversity",
                "default_pacing_strategy": "fast buildup and slow resolution",
                "pitfall_weight": "indiscriminate self-sacrifice > labeling emotions > logic discontinuity",
                "conflict_resolution": "tropes > pacing",
                "contract_injection_layer": "CHAPTER_BRIEF.writing_guidance",
                "anti_pattern": "labeling emotions|illogical character behavior",
            }
        ],
    )

    _write_csv(
        csv_dir / "naming.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "naming_target", "pitfalls"],
        [
            {
                "id": "NR-001",
                "applicable_skills": "write",
                "category": "character",
                "level": "knowledge",
                "keywords": "xuanhuan|person name",
                "applicable_genres": "xuanhuan",
                "summary": "xuanhuan names should preserve cultivation imagery。",
                "naming_target": "character names",
                "pitfalls": "",
            }
        ],
    )

    _write_csv(
        csv_dir / "tropes.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "trope_name", "pitfalls"],
        [
            {
                "id": "TR-001",
                "applicable_skills": "write",
                "category": "trope",
                "level": "knowledge",
                "keywords": "broken engagement|public vindication",
                "applicable_genres": "xuanhuan",
                "summary": "allow space for humiliation and retaliation in the broken-engagement scene",
                "trope_name": "broken-engagement counterattack",
                "pitfalls": "a supporting character acts before the protagonist can counterattack",
            }
        ],
    )

    _write_csv(
        csv_dir / "pacing.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "pitfalls", "pacing_type"],
        [
            {
                "id": "PA-001",
                "applicable_skills": "write",
                "category": "pacing",
                "level": "knowledge",
                "keywords": "public vindication|payoff",
                "applicable_genres": "xuanhuan",
                "summary": "payoff requires a final beat",
                "pitfalls": "vindication ending too weak，missing final emotional payoff",
                "pacing_type": "payoff phase",
            }
        ],
    )

    engine = StorySystemEngine(csv_dir=csv_dir)
    contract = engine.build(query="broken-engagement story three-year challenge", genre=None, chapter=1)

    assert contract["master_setting"]["route"]["canonical_genre"] == "xuanhuan"
    assert contract["chapter_brief"]["reasoning"]["genre"] == "xuanhuan"


def test_chapter_focus_uses_directive_goal_not_dynamic_summary():
    csv_dir = _make_local_tmp_path() / "csv"
    csv_dir.mkdir()
    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "canonical_genre", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001", "applicable_skills": "story-system", "category": "genre-routing", "level": "knowledge",
                "keywords": "xianxia", "intent_synonyms": "", "applicable_genres": "xianxia", "model_instruction": "",
                "summary": "", "details": "", "genre_route": "xianxia", "canonical_genre": "xianxia",
                "genre_aliases": "", "core_tone": "", "pacing_strategy": "", "pitfalls": "",
                "recommended_base_tables": "", "recommended_dynamic_tables": "scenes", "default_query": "",
            }
        ],
    )
    _write_csv(
        csv_dir / "scenes.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "pitfalls"],
        [
            {
                "id": "SP-087", "applicable_skills": "write", "category": "scene", "level": "knowledge",
                "keywords": "philosophical debate", "applicable_genres": "xianxia", "summary": "verbal combat is tense when arguments strike at cultivation foundations。",
                "pitfalls": "",
            }
        ],
    )

    contract = StorySystemEngine(csv_dir).build(
        query="xianxia",
        genre="xianxia",
        chapter=2,
        chapter_directive={"goal": "gather lending information in a conversation at the well"},
    )

    brief = contract["chapter_brief"]
    assert brief["chapter_directive"]["goal"] == "gather lending information in a conversation at the well"
    assert brief["override_allowed"]["chapter_focus"] == "gather lending information in a conversation at the well"


def test_chapter_focus_never_taken_from_dynamic_context_summary_for_placeholder_query():
    engine = StorySystemEngine(_make_local_tmp_path())
    focus = engine._suggest_chapter_focus("{chapter outline goal}", {})

    assert focus == ""


def test_story_system_reference_matching_prefers_chapter_keywords_with_same_priority():
    csv_dir = _make_local_tmp_path() / "csv"
    csv_dir.mkdir()
    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "canonical_genre", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001", "applicable_skills": "story-system", "category": "genre-routing", "level": "knowledge",
                "keywords": "xianxia", "intent_synonyms": "", "applicable_genres": "xianxia", "model_instruction": "",
                "summary": "", "details": "", "genre_route": "xianxia", "canonical_genre": "xianxia",
                "genre_aliases": "", "core_tone": "", "pacing_strategy": "", "pitfalls": "",
                "recommended_base_tables": "", "recommended_dynamic_tables": "scenes", "default_query": "sect",
            }
        ],
    )
    _write_csv(
        csv_dir / "scenes.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "applicable_scenes", "summary", "pitfalls"],
        [
            {
                "id": "SP-001", "applicable_skills": "write", "category": "scene", "level": "knowledge",
                "keywords": "sect|philosophical debate", "applicable_genres": "xianxia", "applicable_scenes": "philosophical debate",
                "summary": "sect debates should show clashing viewpoints。", "pitfalls": "",
            },
            {
                "id": "FIN-001", "applicable_skills": "write", "category": "scene", "level": "knowledge",
                "keywords": "promissory note|interest|compound interest|debt", "applicable_genres": "xianxia", "applicable_scenes": "lending investigation",
                "summary": "lending scenes must clarify contractual traps。", "pitfalls": "",
            },
        ],
    )

    contract = StorySystemEngine(csv_dir).build(
        query="sees the absurdity of the note's terms",
        genre="xianxia",
        chapter=1,
        chapter_directive={"goal": "sees the absurdity of the note's terms", "key_entities": ["promissory note", "interest", "compound interest"]},
    )

    selected = contract["chapter_brief"]["dynamic_context"]
    assert selected[0]["id"] == "FIN-001"


def test_story_system_reference_matching_combines_priority_and_chapter_keywords():
    csv_dir = _make_local_tmp_path() / "csv"
    csv_dir.mkdir()
    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "canonical_genre", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001", "applicable_skills": "story-system", "category": "genre-routing", "level": "knowledge",
                "keywords": "xianxia", "intent_synonyms": "", "applicable_genres": "xianxia", "model_instruction": "",
                "summary": "", "details": "", "genre_route": "xianxia", "canonical_genre": "xianxia",
                "genre_aliases": "", "core_tone": "", "pacing_strategy": "", "pitfalls": "",
                "recommended_base_tables": "", "recommended_dynamic_tables": "tropes|scenes", "default_query": "sect",
            }
        ],
    )
    _write_csv(
        csv_dir / "adjudication.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre", "style_priority", "payoff_priority",
            "default_pacing_strategy", "pitfall_weight", "conflict_resolution", "contract_injection_layer", "anti_pattern",
        ],
        [
            {
                "id": "RS-001", "applicable_skills": "story-system", "category": "adjudication", "level": "reasoning",
                "keywords": "xianxia", "intent_synonyms": "", "applicable_genres": "xianxia", "model_instruction": "",
                "summary": "", "details": "", "genre": "xianxia", "style_priority": "",
                "payoff_priority": "", "default_pacing_strategy": "", "pitfall_weight": "",
                "conflict_resolution": "tropes > scenes", "contract_injection_layer": "CHAPTER_BRIEF", "anti_pattern": "",
            }
        ],
    )
    _write_csv(
        csv_dir / "tropes.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "trope_name", "pitfalls"],
        [
            {
                "id": "TR-001", "applicable_skills": "write", "category": "trope", "level": "knowledge",
                "keywords": "sect|philosophical debate", "applicable_genres": "xianxia", "summary": "sect philosophical dispute。",
                "trope_name": "philosophical debate", "pitfalls": "",
            }
        ],
    )
    _write_csv(
        csv_dir / "scenes.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "applicable_scenes", "summary", "pitfalls"],
        [
            {
                "id": "FIN-001", "applicable_skills": "write", "category": "scene", "level": "knowledge",
                "keywords": "promissory note|interest|compound interest|debt", "applicable_genres": "xianxia", "applicable_scenes": "lending investigation",
                "summary": "lending scenes must clarify contractual traps。", "pitfalls": "",
            }
        ],
    )

    contract = StorySystemEngine(csv_dir).build(
        query="sees the absurdity of the note's terms",
        genre="xianxia",
        chapter=1,
        chapter_directive={"goal": "sees the absurdity of the note's terms", "key_entities": ["promissory note", "interest", "compound interest"]},
    )

    selected = contract["chapter_brief"]["dynamic_context"]
    assert [row["id"] for row in selected[:2]] == ["FIN-001", "TR-001"]
    trace_by_id = {row["id"]: row for row in contract["chapter_brief"]["source_trace"]}
    assert trace_by_id["FIN-001"]["combined_rank_score"] > trace_by_id["TR-001"]["combined_rank_score"]


def test_story_system_composite_platform_genre_filters_dynamic_context():
    csv_dir = _make_local_tmp_path() / "csv"
    csv_dir.mkdir()
    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "canonical_genre", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-CITY", "applicable_skills": "story-system", "category": "genre-routing", "level": "knowledge",
                "keywords": "", "intent_synonyms": "", "applicable_genres": "urban", "model_instruction": "",
                "summary": "", "details": "", "genre_route": "urban-speculative", "canonical_genre": "urban",
                "genre_aliases": "", "core_tone": "", "pacing_strategy": "", "pitfalls": "",
                "recommended_base_tables": "", "recommended_dynamic_tables": "scenes", "default_query": "",
            }
        ],
    )
    _write_csv(
        csv_dir / "scenes.csv",
        ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "applicable_scenes", "summary", "pitfalls"],
        [
            {
                "id": "FOOD-001", "applicable_skills": "write", "category": "scene", "level": "knowledge",
                "keywords": "food|shop", "applicable_genres": "urban", "applicable_scenes": "Midnight Diner",
                "summary": "urban food scenes need everyday bustle。", "pitfalls": "",
            },
            {
                "id": "ELIXIR-001", "applicable_skills": "write", "category": "scene", "level": "knowledge",
                "keywords": "food|elixir", "applicable_genres": "xianxia", "applicable_scenes": "alchemy",
                "summary": "xianxia alchemy emphasizes spiritual materials。", "pitfalls": "",
            },
        ],
    )

    contract = StorySystemEngine(csv_dir).build(
        query="food shop",
        genre="urban-speculative,food,sweet romance",
        chapter=1,
    )

    route = contract["master_setting"]["route"]
    assert route["canonical_genre"] == "urban"
    assert route["route_source"] == "explicit_genre_fallback"
    selected_ids = [row["id"] for row in contract["chapter_brief"]["dynamic_context"]]
    assert selected_ids == ["FOOD-001"]
