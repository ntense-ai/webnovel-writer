#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys

import pytest

from data_modules.placeholder_scanner import scan_placeholders


def test_placeholder_scanner_finds_pending_marks(tmp_path):
    outline_dir = tmp_path / "outlines"
    settings_dir = tmp_path / "settings"
    outline_dir.mkdir()
    settings_dir.mkdir()
    (outline_dir / "volume-1-outline.md").write_text(
        "first heroine(working title)| [Pending outline: design during chapter planning]\n",
        encoding="utf-8",
    )
    (settings_dir / "protagonist.md").write_text("- siblings：{placeholder}\n", encoding="utf-8")

    results = scan_placeholders(tmp_path)

    assert len(results) == 3
    assert any(item["pattern"] == "(working title)" for item in results)
    assert any(item["pattern"].startswith("[Pending outline") for item in results)
    assert any(item["pattern"] == "{placeholder}" for item in results)


def test_webnovel_placeholder_scan_cli_forwards_project_root(monkeypatch, tmp_path, capsys):
    import data_modules.webnovel as webnovel_module

    project_root = tmp_path / "book"
    (project_root / ".webnovel").mkdir(parents=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")
    (project_root / "outlines").mkdir()
    (project_root / "outlines" / "master-outline.md").write_text("[To be completed]\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["webnovel", "--project-root", str(project_root), "placeholder-scan"])

    with pytest.raises(SystemExit) as exc:
        webnovel_module.main()

    assert int(exc.value.code or 0) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["placeholders"][0]["file"] == "outlines/master-outline.md"
