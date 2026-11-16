#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path

import pytest


def _ensure_scripts_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


def _write_project(project_root: Path) -> None:
    outline_dir = project_root / "outlines"
    outline_dir.mkdir(parents=True)
    (outline_dir / "master-outline.md").write_text(
        "\n".join(
            [
                "# master-outline",
                "",
                "## Volume Plan",
                "| Volume | volume-title | Chapters | Core Conflict | Ending Climax |",
                "|------|------|----------|----------|----------|",
                "| 1 | Underworld Debt | Chapter1-50chapter | debt investigation | debt-contract truth emerges |",
                "",
                "## Foreshadowing Table",
                "| Foreshadowing | Planted Chapter | Payoff Chapter | level |",
                "|----------|--------|--------|------|",
                "| old foreshadowing | Chapter 1 | | volume |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for name in ("volume-1-beats.md", "volume-1-timeline.md", "volume-1-outline.md"):
        (outline_dir / name).write_text(f"# {name}\nvalid content\n", encoding="utf-8")


def _write_writeback(project_root: Path, *, include_free_text: bool = False) -> Path:
    payload = {
        "next_volume_anchor": {
            "volume": 2,
            "volume_name": "Blackwater Ledger",
            "core_conflict": "trace the debt network behind the Blackwater Ledger",
            "volume_end_climax": "ledger owner appears at the sect tournament",
        },
        "foreshadow_writeback": [
            {
                "content": "the red seal on the contract remains unexplained",
                "buried_chapter": "Chapter 12",
                "payoff_chapter": "",
                "level": "volume",
            }
        ],
        "open_loop_writeback": [
            {"content": "Su Yun's identity and the origin of Underworld Debt remain unresolved"}
        ],
    }
    if include_free_text:
        payload["notes"] = "free text mentions a hidden mastermind that must not be appended"
    path = project_root / "outlines" / "volume-1-master-outline-update.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_next_volume_anchor_writeback(tmp_path):
    _ensure_scripts_on_path()
    from update_master_outline import sync_master_outline

    _write_project(tmp_path)
    _write_writeback(tmp_path)

    result = sync_master_outline(tmp_path, 1)

    summary = (tmp_path / "outlines" / "master-outline.md").read_text(encoding="utf-8")
    assert result["next_volume"] == 2
    assert "| 2 | Blackwater Ledger |  | trace the debt network behind the Blackwater Ledger | ledger owner appears at the sect tournament |" in summary
    assert "| 3 |" not in summary


def test_structured_foreshadow_append_only(tmp_path):
    _ensure_scripts_on_path()
    from update_master_outline import sync_master_outline

    _write_project(tmp_path)
    _write_writeback(tmp_path, include_free_text=True)

    result = sync_master_outline(tmp_path, 1)

    summary = (tmp_path / "outlines" / "master-outline.md").read_text(encoding="utf-8")
    assert result["structured_items_appended"] == 2
    assert "the red seal on the contract remains unexplained" in summary
    assert "Su Yun's identity and the origin of Underworld Debt remain unresolved" in summary
    assert "hidden mastermind" not in summary
    assert "|  |  |  |  |" not in summary


def test_master_outline_sync_does_not_create_next_volume_detail_files(tmp_path):
    _ensure_scripts_on_path()
    from update_master_outline import sync_master_outline

    _write_project(tmp_path)
    _write_writeback(tmp_path)

    sync_master_outline(tmp_path, 1)

    assert not (tmp_path / "outlines" / "volume-2-outline.md").exists()
    assert not (tmp_path / "outlines" / "volume-2-beats.md").exists()
    assert not (tmp_path / "outlines" / "volume-2-timeline.md").exists()


def test_master_outline_sync_requires_completed_current_volume_artifacts(tmp_path):
    _ensure_scripts_on_path()
    from update_master_outline import MasterOutlineSyncError, sync_master_outline

    _write_project(tmp_path)
    _write_writeback(tmp_path)
    (tmp_path / "outlines" / "volume-1-timeline.md").unlink()

    with pytest.raises(MasterOutlineSyncError, match="artifacts are incomplete"):
        sync_master_outline(tmp_path, 1)


def test_master_outline_sync_rejects_noncanonical_writeback_source(tmp_path):
    _ensure_scripts_on_path()
    from update_master_outline import MasterOutlineSyncError, sync_master_outline

    _write_project(tmp_path)
    other = tmp_path / "outlines" / "manual note.json"
    other.write_text(
        json.dumps(
            {
                "next_volume_anchor": {
                    "volume": 2,
                    "volume_name": "Blackwater Ledger",
                    "core_conflict": "trace the debt network behind the Blackwater Ledger",
                    "volume_end_climax": "ledger owner appears at the sect tournament",
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(MasterOutlineSyncError, match="structured planning file"):
        sync_master_outline(tmp_path, 1, writeback_file=other)


def test_webnovel_master_outline_sync_cli_forwards_project_root(monkeypatch, tmp_path):
    _ensure_scripts_on_path()
    import data_modules.webnovel as webnovel_module

    project_root = (tmp_path / "book").resolve()
    called = {}

    def _fake_resolve(explicit_project_root=None):
        return project_root

    def _fake_run_script(script_name, argv):
        called["script_name"] = script_name
        called["argv"] = list(argv)
        return 0

    monkeypatch.setattr(webnovel_module, "_resolve_root", _fake_resolve)
    monkeypatch.setattr(webnovel_module, "_run_script", _fake_run_script)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "webnovel",
            "--project-root",
            str(tmp_path),
            "master-outline-sync",
            "--volume",
            "1",
            "--writeback-file",
            "outlines/volume-1-master-outline-update.json",
            "--format",
            "text",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        webnovel_module.main()

    assert int(exc.value.code or 0) == 0
    assert called["script_name"] == "update_master_outline.py"
    assert called["argv"] == [
        "--project-root",
        str(project_root),
        "--volume",
        "1",
        "--format",
        "text",
        "--writeback-file",
        "outlines/volume-1-master-outline-update.json",
    ]
