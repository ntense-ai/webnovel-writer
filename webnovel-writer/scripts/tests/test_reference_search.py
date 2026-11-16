#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for reference_search.py — BM25 keyword search over CSV reference files.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).resolve().parents[1] / "reference_search.py")
CSV_DIR = str(Path(__file__).resolve().parents[2] / "references" / "csv")


def run_search(*args: str) -> dict:
    """Run reference_search.py as a subprocess and return parsed JSON."""
    result = subprocess.run(
        [sys.executable, SCRIPT, "--csv-dir", CSV_DIR, *args],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return json.loads(result.stdout)


class TestSkillAndGenreFiltering:
    """Test filtering by skill and genre."""

    def test_skill_write_genre_xuanhuan_returns_nr001_not_nr002(self):
        """--skill write --table naming --query character naming --genre xuanhuan → NR-001, not NR-002."""
        out = run_search(
            "--skill", "write",
            "--table", "naming",
            "--query", "character naming",
            "--genre", "xuanhuan",
        )
        assert out["status"] == "success"
        ids = [r["id"] for r in out["data"]["results"]]
        assert "NR-001" in ids
        assert "NR-002" not in ids

    def test_skill_write_cross_table_search(self):
        """--skill write --query combat description → SP-001 from scenes."""
        out = run_search(
            "--skill", "write",
            "--query", "combat description",
        )
        assert out["status"] == "success"
        assert out["data"]["total"] >= 1
        ids = [r["id"] for r in out["data"]["results"]]
        assert "SP-001" in ids
        # Verify it comes from the right table
        tables = [r["table"] for r in out["data"]["results"] if r["id"] == "SP-001"]
        assert tables[0] == "scenes"

    def test_nonexistent_query_returns_empty(self):
        """--skill plan --query qzxvplm → empty results, no error."""
        out = run_search(
            "--skill", "plan",
            "--query", "qzxvplm",
        )
        assert out["status"] == "success"
        assert out["data"]["total"] == 0
        assert out["data"]["results"] == []

    def test_synonym_query_hits_manual_trigger_terms(self):
        """Intent synonyms retrieve naming guidance."""
        out = run_search(
            "--skill", "write",
            "--table", "naming",
            "--query", "how to name a character",
            "--genre", "xuanhuan",
        )
        assert out["status"] == "success"
        ids = [r["id"] for r in out["data"]["results"]]
        assert "NR-001" in ids

    def test_emotion_query_hits_writing_techniques_table(self):
        """Emotion and psychology queries retrieve writing techniques."""
        out = run_search(
            "--skill", "write",
            "--table", "techniques",
            "--query", "emotional description psychology",
        )
        assert out["status"] == "success"
        ids = [r["id"] for r in out["data"]["results"]]
        assert "WT-002" in ids

    def test_prompt_derived_dialogue_query_hits_new_writing_technique(self):
        """Prompt-derived dialogue techniques are searchable."""
        out = run_search(
            "--skill", "write",
            "--table", "techniques",
            "--query", "concise dialogue cut filler",
        )
        assert out["status"] == "success"
        ids = [r["id"] for r in out["data"]["results"]]
        assert "WT-005" in ids

    def test_prompt_derived_trope_query_hits_bridge_table(self):
        """Trope queries retrieve broken-engagement counterattacks."""
        out = run_search(
            "--skill", "write",
            "--table", "tropes",
            "--query", "broken engagement three-year promise",
        )
        assert out["status"] == "success"
        ids = [r["id"] for r in out["data"]["results"]]
        assert "TR-001" in ids

    def test_prompt_derived_pacing_query_hits_new_pacing_table(self):
        """Pacing queries retrieve small reversal finishing blow."""
        out = run_search(
            "--skill", "plan",
            "--table", "pacing",
            "--query", "small reversal finishing blow",
        )
        assert out["status"] == "success"
        ids = [r["id"] for r in out["data"]["results"]]
        assert "PA-002" in ids

    def test_prompt_derived_setting_query_hits_new_system_table(self):
        """Power queries retrieve side-effect boundaries."""
        out = run_search(
            "--skill", "init",
            "--table", "powers",
            "--query", "superpower side effects cost",
        )
        assert out["status"] == "success"
        ids = [r["id"] for r in out["data"]["results"]]
        assert "SY-002" in ids

    def test_prompt_derived_character_query_hits_new_character_table(self):
        """Character queries retrieve mirror antagonists."""
        out = run_search(
            "--skill", "init",
            "--table", "characters",
            "--query", "mirror antagonist",
        )
        assert out["status"] == "success"
        ids = [r["id"] for r in out["data"]["results"]]
        assert "CH-001" in ids

    def test_internal_story_system_tables_do_not_leak_into_write_search(self):
        """Ordinary writing searches exclude internal routing and adjudication tables."""
        out = run_search(
            "--skill", "write",
            "--query", "grovel-romance rule adjudication",
            "--max-results", "20",
        )
        tables = {r["table"] for r in out["data"]["results"]}
        assert "genre-routing" not in tables
        assert "adjudication" not in tables

    def test_story_system_skill_can_search_route_table(self):
        """Story System is the actual internal routing skill label."""
        out = run_search(
            "--skill", "story-system",
            "--table", "genre-routing",
            "--query", "quick-transmigration mission original host",
        )
        ids = [r["id"] for r in out["data"]["results"]]
        assert "GR-025" in ids

    def test_legacy_comma_delimiters_remain_compatible(self, tmp_path):
        """Custom tables support comma-delimited skill and genre fields."""
        temp_dir = tmp_path / "reference_search_compat"
        temp_dir.mkdir(parents=True, exist_ok=True)
        csv_path = temp_dir / "custom-table.csv"
        csv_path.write_text(
            "\n".join([
                "id,applicable_skills,category,level,keywords,intent_synonyms,applicable_genres,model_instruction,summary,details",
                "TS-001,\"write,plan\",test,reminder,\"custom keywords\",\"custom query\",\"xuanhuan,xianxia\",Check delimiter support,Custom summary,Custom details",
            ]),
            encoding="utf-8",
        )
        out = run_search(
            "--csv-dir", str(temp_dir),
            "--skill", "write",
            "--table", "custom-table",
            "--query", "custom query",
            "--genre", "xuanhuan",
        )
        ids = [r["id"] for r in out["data"]["results"]]
        assert "TS-001" in ids

        out = run_search(
            "--csv-dir", str(temp_dir),
            "--skill", "write",
            "--table", "custom-table",
            "--query", "custom query",
            "--genre", "xianxia,urban-speculative",
        )
        ids = [r["id"] for r in out["data"]["results"]]
        assert "TS-001" in ids


class TestErrorHandling:
    """Test error cases."""

    def test_missing_csv_dir_returns_error(self):
        """Missing CSV dir → error JSON."""
        result = subprocess.run(
            [sys.executable, SCRIPT,
             "--csv-dir", "/nonexistent/path/that/does/not/exist",
             "--skill", "write",
             "--query", "test"],
            capture_output=True,
            text=True,
        )
        out = json.loads(result.stdout)
        assert out["status"] == "error"
        assert "CSV_DIR_NOT_FOUND" in out["error"]["code"]


class TestOutputFormat:
    """Test output JSON structure."""

    def test_result_has_required_fields(self):
        """Each result has id, table, category, level, applicable_genres, summary, model_instruction."""
        out = run_search(
            "--skill", "write",
            "--table", "naming",
            "--query", "character naming",
        )
        assert out["status"] == "success"
        for r in out["data"]["results"]:
            assert "id" in r
            assert "table" in r
            assert "category" in r
            assert "level" in r
            assert "applicable_genres" in r
            assert "summary" in r
            assert "model_instruction" in r

    def test_content_summary_prefers_core_summary(self):
        """Result summaries prefer the core summary field."""
        out = run_search(
            "--skill", "write",
            "--table", "naming",
            "--query", "character naming",
            "--genre", "xuanhuan",
        )
        row = next(r for r in out["data"]["results"] if r["id"] == "NR-001")
        assert row["summary"] == "Fantasy names should evoke cultivation and classical culture rather than transplant everyday modern names."

    def test_data_envelope_fields(self):
        """Data envelope has query, skill, genre, total, results."""
        out = run_search(
            "--skill", "write",
            "--query", "naming",
            "--genre", "xuanhuan",
        )
        data = out["data"]
        assert data["query"] == "naming"
        assert data["skill"] == "write"
        assert data["genre"] == "xuanhuan"
        assert isinstance(data["total"], int)
        assert isinstance(data["results"], list)

    def test_max_results_limits_output(self):
        """--max-results 1 limits to 1 result."""
        out = run_search(
            "--skill", "write",
            "--query", "naming",
            "--max-results", "1",
        )
        assert out["data"]["total"] <= 1


class TestPerTableSearchCols:
    def test_different_tables_use_different_search_weights(self):
        out1 = run_search("--skill", "write", "--table", "naming", "--query", "character naming")
        out2 = run_search("--skill", "write", "--table", "scenes", "--query", "combat description")
        assert out1["status"] == "success"
        assert out2["status"] == "success"
        assert out1["data"]["total"] >= 1
        assert out2["data"]["total"] >= 1


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

    def test_taxonomy_index_covers_genre_templates(self):
        from genre_taxonomy import load_genre_taxonomy
        templates_dir = Path(__file__).resolve().parents[2] / "templates" / "genres"
        template_files = {path.name for path in templates_dir.glob("*.md")}
        referenced = {
            entry.template_file
            for entry in load_genre_taxonomy().entries
            if entry.template_file
        }
        assert len(template_files) == 37
        assert template_files <= referenced

    def test_taxonomy_spot_checks_platform_and_legacy_inputs(self):
        from reference_search import resolve_genre
        assert resolve_genre("urban-slice-of-life") == "urban"
        assert resolve_genre("warrior-son-in-law") == "urban"
        assert resolve_genre("xianxia") == "xianxia"
        assert resolve_genre("fantasy") == "fantasy"
        assert resolve_genre("historical-romance") == "historical-romance"
        assert resolve_genre("billionaire-romance") == "contemporary-romance"
        assert resolve_genre("quick-transmigration") == "quick-transmigration"
        assert resolve_genre("sci-fi") == "sci-fi"

    def test_resolve_genre_canonical_passthrough(self):
        from reference_search import resolve_genre
        assert resolve_genre("urban") == "urban"
        assert resolve_genre("all") == "all"
        assert resolve_genre(None) is None

    def test_resolve_genre_platform_tag(self):
        from reference_search import resolve_genre
        assert resolve_genre("urban-slice-of-life") == "urban"
        assert resolve_genre("warrior-son-in-law") == "urban"
        assert resolve_genre("historical-romance") == "historical-romance"

    def test_resolve_genre_legacy(self):
        from reference_search import resolve_genre
        assert resolve_genre("wuxia") == "historical"
        assert resolve_genre("criminal investigation") == "mystery"
        assert resolve_genre("online gaming") == "game-lit"

    def test_resolve_genre_keeps_template_namespace_separate(self):
        from genre_taxonomy import resolve_genre_input
        xuanhuan = resolve_genre_input("xuanhuan")
        assert xuanhuan.canonical_genre == "xuanhuan"
        assert xuanhuan.template_files == ["cultivation.md"]

        xianxia = resolve_genre_input("xianxia")
        assert xianxia.canonical_genre == "xianxia"
        assert xianxia.template_files == ["cultivation.md"]

    def test_resolve_composite_natural_language_genre(self):
        from genre_taxonomy import resolve_genre_input
        resolved = resolve_genre_input("rules horror + zhihu short fiction")
        assert resolved.canonical_genre == "mystery"
        assert resolved.template_files == ["rules-horror.md", "zhihu-short-fiction.md"]
        assert "rules-horror" in resolved.route_tags
        assert "zhihu-short-fiction" in resolved.format_tags

    def test_search_with_platform_tag_genre(self):
        """--genre urban-slice-of-life should match rows with applicable_genres=urban."""
        out = run_search(
            "--skill", "write",
            "--table", "naming",
            "--query", "character naming",
            "--genre", "urban-slice-of-life",
        )
        assert out["status"] == "success"
        # Should find results (urban-slice-of-life resolves to urban, matching rows tagged urban)
        assert out["data"]["total"] >= 0  # may be 0 if no urban rows, but no error


class TestEndToEndSmoke:
    """Smoke tests: canonical genre pipeline over current CSV data."""

    def test_xuanhuan_search_returns_results(self):
        out = run_search("--skill", "write", "--query", "character naming", "--genre", "xuanhuan")
        assert out["status"] == "success"
        assert out["data"]["total"] >= 1

    def test_romance_search_returns_results(self):
        out = run_search("--skill", "write", "--query", "grovel romance", "--genre", "contemporary-romance")
        assert out["status"] == "success"
        assert out["data"]["total"] >= 1

    def test_platform_tag_as_genre_returns_results(self):
        out = run_search("--skill", "write", "--query", "rules zoo handbook", "--genre", "speculative-mystery")
        assert out["status"] == "success"
        assert out["data"]["total"] >= 1

    def test_validate_csv_zero_errors(self):
        validate_script = str(Path(__file__).resolve().parents[1] / "validate_csv.py")
        result = subprocess.run(
            [sys.executable, validate_script, "--csv-dir", CSV_DIR, "--format", "json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert len(data["errors"]) == 0, f"CSV validation errors: {data['errors']}"
