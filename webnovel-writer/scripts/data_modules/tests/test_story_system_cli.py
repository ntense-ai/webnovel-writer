#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import sys

import pytest


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
                "intent_synonyms": "broken-engagement story",
                "applicable_genres": "xuanhuan",
                "model_instruction": "pressure before payoff",
                "summary": "broken-engagement opening",
                "details": "",
                "genre_route": "broken-engagement-fantasy",
                "genre_aliases": "broken-engagement story",
                "core_tone": "pressure before payoff",
                "pacing_strategy": "counterattack within three chapters",
                "mandatory prohibitions/pitfalls": "vindication must not end weakly",
                "recommended_base_tables": "naming",
                "recommended_dynamic_tables": "tropes",
                "default_query": "broken engagement|public vindication",
            }
        ],
    )
    _write_csv(csv_dir / "naming.csv", ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary"], [])
    _write_csv(csv_dir / "tropes.csv", ["id", "applicable_skills", "category", "level", "keywords", "applicable_genres", "summary", "prohibited phrasing"], [])

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
        "# manual explanation\nmanual note\n<!-- STORY-SYSTEM:BEGIN -->\nold content\n<!-- STORY-SYSTEM:END -->\n",
        encoding="utf-8",
    )

    write_marked_markdown(target, "## Auto\nnew content\n")

    text = target.read_text(encoding="utf-8")
    assert "# manual explanation" in text
    assert "manual note" in text
    assert "## Auto" in text
    assert "old content" not in text


def test_story_system_default_csv_dir_routes_real_genre_seed(tmp_path, monkeypatch, capsys):
    project_root = tmp_path / "book"
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")

    from story_system import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "story_system",
            "broken-engagement-fantasy",
            "--project-root",
            str(project_root),
            "--format",
            "json",
        ],
    )
    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["master_setting"]["route"]["primary_genre"] == "broken-engagement-fantasy"
    assert payload["master_setting"]["route"]["route_source"] != "empty_csv_fallback"


def test_story_system_warns_on_placeholder_query(tmp_path, monkeypatch, capsys):
    project_root = tmp_path / "book"
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()
    _write_csv(csv_dir / "genre-routing.csv", ["id", "keywords"], [])

    from story_system import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "story_system",
            "{chapter outline goal}",
            "--project-root",
            str(project_root),
            "--chapter",
            "1",
            "--csv-dir",
            str(csv_dir),
            "--format",
            "json",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 2

    captured = capsys.readouterr()
    assert "placeholder" in captured.err
    assert "Cannot match story-system genre-routing" in captured.err


def test_story_system_persist_unroutable_exits_without_contracts(tmp_path, monkeypatch, capsys):
    project_root = tmp_path / "book"
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")

    csv_dir = tmp_path / "csv"
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
                "keywords": "broken-engagement-fantasy",
                "intent_synonyms": "broken-engagement story",
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

    from story_system import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "story_system",
            "rules-mystery",
            "--genre",
            "rules-mystery",
            "--project-root",
            str(project_root),
            "--persist",
            "--csv-dir",
            str(csv_dir),
            "--format",
            "json",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "rules-mystery" in captured.err
    assert "rules-horror" in captured.err
    assert not (project_root / ".story-system").exists()
