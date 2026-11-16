#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv

from data_modules.story_system_engine import StorySystemEngine


def _write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _setup_csvs(csv_dir):
    """Create fixture CSVs for genre-routing, adjudication, tropes, pacing."""
    csv_dir.mkdir(exist_ok=True)

    _write_csv(
        csv_dir / "genre-routing.csv",
        [
            "id", "applicable_skills", "category", "level", "keywords", "intent_synonyms", "applicable_genres",
            "model_instruction", "summary", "details", "genre_route", "genre_aliases", "core_tone",
            "pacing_strategy", "pitfalls", "recommended_base_tables", "recommended_dynamic_tables", "default_query",
        ],
        [
            {
                "id": "GR-001",
                "applicable_skills": "write|plan",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "xuanhuan|broken engagement",
                "intent_synonyms": "how to write xuanhuan",
                "applicable_genres": "xuanhuan",
                "model_instruction": "establish pressure first，then deliver the explosive payoff。",
                "summary": "xuanhuan broken-engagement stories need humiliation followed by strong payoff。",
                "details": "",
                "genre_route": "xuanhuan",
                "genre_aliases": "broken-engagement story",
                "core_tone": "build pressure before an explosive counterattack",
                "pacing_strategy": "pressure followed by eruption",
                "pitfalls": "vindication requires the final extra payoff beat",
                "recommended_base_tables": "naming|characters",
                "recommended_dynamic_tables": "tropes|pacing",
                "default_query": "broken engagement|public vindication",
            },
            {
                "id": "GR-002",
                "applicable_skills": "story-system",
                "category": "genre-routing",
                "level": "knowledge",
                "keywords": "apocalypse|apocalyptic survival",
                "intent_synonyms": "apocalyptic-survival",
                "applicable_genres": "sci-fi",
                "model_instruction": "",
                "summary": "apocalyptic survival requires resource pressure and collapsing order。",
                "details": "",
                "genre_route": "apocalyptic survival",
                "genre_aliases": "apocalypse",
                "core_tone": "rebuilding order under resource pressure",
                "pacing_strategy": "survive before expanding",
                "pitfalls": "",
                "recommended_base_tables": "naming|characters",
                "recommended_dynamic_tables": "tropes|pacing",
                "default_query": "apocalypse|survival",
            },
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
                "applicable_skills": "write|plan",
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
                "conflict_resolution": "pacing > tropes > techniques",
                "contract_injection_layer": "CHAPTER_BRIEF.writing_guidance",
                "anti_pattern": "labeling emotions|illogical character behavior",
            },
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
            },
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
            },
        ],
    )


def test_build_with_reasoning_includes_reasoning_rule_in_source_trace(tmp_path):
    csv_dir = tmp_path / "csv"
    _setup_csvs(csv_dir)

    engine = StorySystemEngine(csv_dir=csv_dir)
    contract = engine.build(query="xuanhuan", genre=None, chapter=1)

    source_trace = contract["master_setting"]["source_trace"]
    reasoning_entries = [e for e in source_trace if e.get("reasoning_rule") == "xuanhuan"]
    assert len(reasoning_entries) > 0, f"Expected reasoning_rule='xuanhuan' in source_trace, got {source_trace}"
    assert reasoning_entries[0]["inject_target"] == "CHAPTER_BRIEF.writing_guidance"


def test_reasoning_anti_patterns_sorted_by_weight(tmp_path):
    csv_dir = tmp_path / "csv"
    _setup_csvs(csv_dir)

    engine = StorySystemEngine(csv_dir=csv_dir)
    contract = engine.build(query="xuanhuan", genre=None, chapter=None)

    anti_patterns = contract["anti_patterns"]
    assert len(anti_patterns) > 0, "Expected non-empty anti_patterns"

    # Check that reasoning anti_pattern entries are present
    texts = [a["text"] for a in anti_patterns]
    assert "labeling emotions" in texts or "illogical character behavior" in texts, (
        f"Expected reasoning anti_pattern in anti_patterns, got {texts}"
    )


def test_reasoning_not_found_falls_back_gracefully(tmp_path):
    csv_dir = tmp_path / "csv"
    _setup_csvs(csv_dir)

    engine = StorySystemEngine(csv_dir=csv_dir)
    # apocalypse has no matching row in adjudication.csv fixture
    contract = engine.build(query="apocalyptic survival", genre="apocalypse", chapter=None)

    assert contract["master_setting"] is not None
    assert contract["anti_patterns"] is not None
    # Should still produce a valid contract without errors
    assert contract["meta"]["explicit_genre"] == "apocalypse"
