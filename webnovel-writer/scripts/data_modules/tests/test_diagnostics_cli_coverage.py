"""Regression checks for read-only diagnostic CLI and failure reporting."""
import json
import sqlite3
import sys
from pathlib import Path

import pytest

from data_modules import doctor, project_status
from data_modules.project_phase import ProjectPhaseSnapshot
from .test_project_phase import _make_init_ready


@pytest.mark.parametrize("payload,expected", [
    ([], ""), ({"project_info": {"title": "  Novel  "}}, "Novel"),
    ({"project": {"title": "Legacy"}}, "Legacy"),
])
def test_project_title_handles_current_legacy_and_nonobject(tmp_path, payload, expected):
    (tmp_path / ".webnovel").mkdir()
    (tmp_path / ".webnovel/state.json").write_text(json.dumps(payload))
    assert project_status._project_title(tmp_path) == expected


def test_project_title_missing_or_invalid_returns_empty(tmp_path):
    assert project_status._project_title(tmp_path) == ""
    (tmp_path / ".webnovel").mkdir()
    (tmp_path / ".webnovel/state.json").write_text("{")
    assert project_status._project_title(tmp_path) == ""


@pytest.mark.parametrize("phase,expected", [
    ("no_project", "/webnovel-init"), ("init_scaffolded", "fix missing init files"),
    ("init_ready", "/webnovel-plan"), ("plan_in_progress", "chapter 7"),
    ("chapter_contract_ready", "/webnovel-write 7"), ("draft_in_progress", "artifacts for chapter 7"),
    ("ready_to_commit", "chapter-commit --chapter 7"), ("chapter_committed", "chapter 7"),
    ("projection_failed", "repair failed or pending projection"), ("unknown", "doctor --format text"),
])
def test_next_action_matches_phase(phase, expected):
    snapshot = ProjectPhaseSnapshot("", phase, 7, 6)
    assert expected in project_status.next_action_for_phase(snapshot)


def test_status_formats_blockers_and_warnings():
    report = {"phase": "unknown", "blocking": ["missing outline"], "warnings": ["stale index"]}
    assert json.loads(project_status.format_project_status(report, "json")) == report
    text = project_status.format_project_status(report)
    assert "blocking:\n- missing outline" in text
    assert "warnings:\n- stale index" in text


def test_project_status_cli_passes_arguments(monkeypatch, capsys):
    calls = []
    def build(root, chapter=None):
        calls.append((root, chapter))
        return {"phase": "draft_in_progress"}
    monkeypatch.setattr(project_status, "build_project_status", build)
    monkeypatch.setattr(sys, "argv", ["project-status", "--project-root", "/novel", "--chapter", "7", "--format", "json"])
    with pytest.raises(SystemExit) as exc:
        project_status.main()
    assert exc.value.code == 0
    assert calls == [("/novel", 7)]
    assert json.loads(capsys.readouterr().out)["phase"] == "draft_in_progress"


@pytest.mark.parametrize("ok,exit_code", [(True, 0), (False, 1)])
def test_doctor_cli_exit_matches_report(monkeypatch, capsys, ok, exit_code):
    calls = []
    def build(root, *, chapter, deep):
        calls.append((root, chapter, deep))
        return {"ok": ok}
    monkeypatch.setattr(doctor, "build_doctor_report", build)
    monkeypatch.setattr(sys, "argv", ["doctor", "--chapter", "3", "--deep", "--format", "json"])
    with pytest.raises(SystemExit) as exc:
        doctor.main()
    assert exc.value.code == exit_code
    assert calls == [(None, 3, True)]
    assert json.loads(capsys.readouterr().out) == {"ok": ok}


def test_doctor_text_exposes_repairs_without_success_noise():
    report = {"ok": False, "checks": [
        {"status": "ok", "id": "quiet"},
        {"status": "error", "id": "broken", "message": "bad state", "path": "/state.json",
         "actual": "invalid JSON", "impact": "cannot resume", "repair": "restore backup"},
    ], "recommended_actions": [f"repair {i}" for i in range(10)]}
    text = doctor.format_doctor_report(report)
    assert "ERROR webnovel-doctor" in text
    for detail in ("broken: bad state", "path: /state.json", "actual: invalid JSON", "impact: cannot resume", "repair: restore backup"):
        assert detail in text
    assert "quiet" not in text
    assert "- repair 7" in text and "- repair 8" not in text


def test_doctor_json_and_io_errors_are_classified(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    assert doctor._read_json(path) == ({}, "missing")
    path.write_text("{")
    assert doctor._read_json(path)[1].startswith("invalid json:")
    path.write_text("[]")
    assert doctor._read_json(path) == ({}, "json root is not object")
    def denied(*args, **kwargs):
        raise PermissionError("not readable")
    monkeypatch.setattr(Path, "read_text", denied)
    assert doctor._read_json(path) == ({}, "read error: not readable")


def test_doctor_relative_path_preserves_external_path(tmp_path):
    assert doctor._rel(tmp_path, tmp_path / "inside") == "inside"
    assert doctor._rel(tmp_path, tmp_path.parent / "outside") == str(tmp_path.parent / "outside")


def test_sqlite_diagnostics_distinguish_empty_missing_and_corrupt(tmp_path):
    path = tmp_path / "index.db"
    assert doctor._sqlite_table_count(path, "chapters") == (False, 0, "missing")
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE chapters (id INTEGER)")
        conn.executemany("INSERT INTO chapters VALUES (?)", [(1,), (2,)])
    assert doctor._sqlite_table_count(path, "chapters") == (True, 2, "")
    assert doctor._sqlite_table_count(path, "absent") == (False, 0, "table_missing")
    path.write_text("not a database")
    valid, count, error = doctor._sqlite_table_count(path, "chapters")
    assert valid is False and count == 0 and error


def test_deep_dashboard_checks_report_missing_then_present(tmp_path):
    checks = doctor._dashboard_checks(tmp_path)
    assert len(checks) == 4 and all(c["status"] == "warning" and c["repair"] for c in checks)
    (tmp_path / "dashboard/frontend/dist").mkdir(parents=True)
    (tmp_path / "dashboard/frontend/package.json").write_text("{}")
    (tmp_path / "dashboard/requirements.txt").write_text("")
    assert all(c["status"] == "ok" for c in doctor._dashboard_checks(tmp_path))


def test_doctor_runtime_failure_remains_recoverable_warning(tmp_path, monkeypatch):
    _make_init_ready(tmp_path)
    monkeypatch.setattr(doctor, "_python_checks", lambda: [])
    def fail(*args, **kwargs):
        raise ValueError("bad contract")
    monkeypatch.setattr(doctor, "build_story_runtime_health", fail)
    report = doctor.build_doctor_report(tmp_path, deep=True, preflight_report={"checks": [None]})
    health = next(c for c in report["checks"] if c["id"] == "story_runtime.health")
    assert health["status"] == "warning"
    assert health["actual"] == "bad contract" and health["repair"]
    assert report["mode"] == "deep"
    assert any(c["id"] == "dashboard.root" for c in report["checks"])
