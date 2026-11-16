#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import json


def test_init_skips_dead_templates_and_empty_libraries_for_single_protagonist(tmp_path, monkeypatch):
    import init_project as init_project_module

    monkeypatch.setattr(init_project_module, "is_git_available", lambda: False)
    project_root = tmp_path / "book"

    init_project_module.init_project(
        str(project_root),
        title="Test Book",
        genre="xianxia",
        protagonist_name="Lu Ming",
        protagonist_structure="single protagonist with supporting viewpoints",
        heroine_config="none",
        target_chapters=50,
    )

    assert (project_root / "settings" / "protagonist.md").is_file()
    assert not (project_root / "settings" / "protagonist-team.md").exists()
    assert not (project_root / "settings" / "heroine.md").exists()
    assert not (project_root / "settings" / "special-advantage.md").exists()
    assert not (project_root / "settings" / "hybrid-genre.md").exists()
    assert not (project_root / "outlines" / "payoff-plan.md").exists()
    assert not (project_root / "settings" / "characters").exists()
    assert not (project_root / "settings" / "items").exists()
    assert not (project_root / "settings" / "other-settings").exists()


def test_init_master_outline_does_not_prefill_future_volume_rows(tmp_path, monkeypatch):
    import init_project as init_project_module

    monkeypatch.setattr(init_project_module, "is_git_available", lambda: False)
    project_root = tmp_path / "book"

    init_project_module.init_project(
        str(project_root),
        title="Test Book",
        genre="xianxia",
        protagonist_name="Lu Ming",
        target_chapters=600,
    )

    summary = (project_root / "outlines" / "master-outline.md").read_text(encoding="utf-8")
    assert "| 1 |" in summary
    assert "| 2 |" not in summary
    assert "| 20 |" not in summary


def test_init_generates_conditional_protagonist_group_and_heroine(tmp_path, monkeypatch):
    import init_project as init_project_module

    monkeypatch.setattr(init_project_module, "is_git_available", lambda: False)
    project_root = tmp_path / "book"

    init_project_module.init_project(
        str(project_root),
        title="Test Book",
        genre="xianxia",
        protagonist_name="Lu Ming",
        protagonist_structure="dual",
        heroine_config="single",
        heroine_names="Eve",
        target_chapters=50,
    )

    assert (project_root / "settings" / "protagonist-team.md").is_file()
    assert (project_root / "settings" / "heroine.md").is_file()


def test_init_persists_canonical_genre_and_template_tags(tmp_path, monkeypatch):
    import init_project as init_project_module

    monkeypatch.setattr(init_project_module, "is_git_available", lambda: False)
    project_root = tmp_path / "book"

    init_project_module.init_project(
        str(project_root),
        title="Test Book",
        genre="rules-horror+zhihu-short-fiction",
        protagonist_name="Lu Ming",
        target_chapters=50,
    )

    state = json.loads((project_root / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    project_info = state["project_info"]
    assert project_info["genre"] == "mystery"
    assert project_info["genre_label"] == "rules-horror+zhihu-short-fiction"
    assert project_info["genre_tags"]["route"] == ["rules-horror"]
    assert project_info["genre_tags"]["format"] == ["zhihu-short-fiction"]
    assert project_info["genre_tags"]["templates"] == ["rules-horror", "zhihu-short-fiction"]

    worldview = (project_root / "settings" / "worldbuilding.md").read_text(encoding="utf-8")
    assert "rules-horror" in worldview
    assert "zhihu-short-fiction" in worldview


def test_init_accepts_english_genre_and_preserves_stable_schema(tmp_path, monkeypatch):
    import init_project as init_project_module

    monkeypatch.setattr(init_project_module, "is_git_available", lambda: False)
    project_root = tmp_path / "book"
    init_project_module.init_project(
        str(project_root), title="The Rules", genre="rules horror",
        protagonist_name="Alice", target_chapters=50,
    )
    state = json.loads((project_root / ".webnovel" / "state.json").read_text())
    assert state["project_info"]["genre"] == "mystery"
    assert state["project_info"]["genre_label"] == "rules horror"
    assert state["project_info"]["genre_tags"]["route"] == ["rules-horror"]
    assert (project_root / "settings" / "worldbuilding.md").is_file()


def test_init_preserves_corrupt_state_json_before_rebuilding(tmp_path, monkeypatch, capsys):
    import init_project as init_project_module

    monkeypatch.setattr(init_project_module, "is_git_available", lambda: False)
    project_root = tmp_path / "book"
    state_dir = project_root / ".webnovel"
    state_dir.mkdir(parents=True)
    corrupt_text = '{"project_info": '
    (state_dir / "state.json").write_text(corrupt_text, encoding="utf-8")

    init_project_module.init_project(
        str(project_root),
        title="Test Book",
        genre="xianxia",
        protagonist_name="Lu Ming",
        target_chapters=50,
    )

    corrupt_copies = sorted(state_dir.glob("state.corrupt_*.json"))
    assert len(corrupt_copies) == 1
    assert corrupt_copies[0].read_text(encoding="utf-8") == corrupt_text
    assert "Warning: damaged state.json" in capsys.readouterr().out


def test_init_reuses_existing_directories_without_moving_user_files(tmp_path, monkeypatch):
    import init_project as init_project_module

    monkeypatch.setattr(init_project_module, "is_git_available", lambda: False)
    project_root = tmp_path / "existing-book"
    for name in ("settings", "outlines", "chapters", "reviews"):
        (project_root / name).mkdir(parents=True)
    existing = project_root / "settings" / "worldbuilding.md"
    existing.write_text("My existing world", encoding="utf-8")
    init_project_module.init_project(
        str(project_root), title="Existing book", genre="fantasy",
        protagonist_name="Alice", target_chapters=50,
    )
    assert existing.read_text(encoding="utf-8") == "My existing world"
    assert (project_root / "settings" / "protagonist.md").is_file()
    assert (project_root / "outlines" / "master-outline.md").is_file()
    for name in ("settings", "outlines", "chapters", "reviews"):
        assert (project_root / name).is_dir()
