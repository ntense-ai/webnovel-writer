#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sqlite3
import sys
from pathlib import Path
from typing import Any

from project_paths import project_dir, project_path


from .config import DataModulesConfig
from .project_phase import (
    INIT_REQUIRED_DIRS,
    INIT_REQUIRED_FILES,
    PHASE_INIT_READY,
    PHASE_INIT_SCAFFOLDED,
    PHASE_NO_PROJECT,
    ProjectPhaseSnapshot,
    contract_files_for_chapter,
    resolve_project_phase,
)
from .projection_log import (
    latest_projection_run,
    projection_log_path,
    projection_run_failed,
    projection_run_pending,
)
from .story_runtime_health import build_story_runtime_health


SCHEMA_VERSION = "webnovel-doctor/v1"
CHECK_OK = "ok"
CHECK_WARNING = "warning"
CHECK_ERROR = "error"
CHECK_SKIPPED = "skipped"


def _check(
    check_id: str,
    *,
    status: str,
    severity: str,
    message: str,
    path: str = "",
    expected: str = "",
    actual: str = "",
    impact: str = "",
    repair: str = "",
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "severity": severity,
        "message": message,
        "path": path,
        "expected": expected,
        "actual": actual,
        "impact": impact,
        "repair": repair,
    }


def _rel(project_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "missing"
    except json.JSONDecodeError as exc:
        return {}, f"invalid json: {exc}"
    except OSError as exc:
        return {}, f"read error: {exc}"
    if not isinstance(payload, dict):
        return {}, "json root is not object"
    return payload, ""


def _expected_profile(snapshot: ProjectPhaseSnapshot) -> dict[str, Any]:
    expected_files = [_rel(Path(snapshot.project_root), project_path(snapshot.project_root, rel)) for rel in INIT_REQUIRED_FILES]
    expected_dirs = [_rel(Path(snapshot.project_root), project_path(snapshot.project_root, rel)) for rel in INIT_REQUIRED_DIRS]
    if snapshot.phase not in {PHASE_NO_PROJECT, PHASE_INIT_SCAFFOLDED, PHASE_INIT_READY}:
        expected_files.extend(snapshot.missing_contract_files)
    if snapshot.target_chapter > 0 and snapshot.phase not in {PHASE_NO_PROJECT, PHASE_INIT_SCAFFOLDED, PHASE_INIT_READY}:
        expected_files.extend(
            str(path.relative_to(Path(snapshot.project_root)))
            for path in contract_files_for_chapter(Path(snapshot.project_root), snapshot.target_chapter).values()
        )
    return {
        "phase": snapshot.phase,
        "target_chapter": snapshot.target_chapter,
        "files": sorted(set(expected_files)),
        "dirs": sorted(set(expected_dirs)),
    }


def _preflight_checks(preflight_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not preflight_report:
        return []
    checks: list[dict[str, Any]] = []
    for item in preflight_report.get("checks") or []:
        if not isinstance(item, dict):
            continue
        ok = bool(item.get("ok"))
        name = str(item.get("name") or "unknown")
        checks.append(
            _check(
                f"preflight.{name}",
                status=CHECK_OK if ok else CHECK_ERROR,
                severity="info" if ok else "blocker",
                message=f"preflight {name} {'ok' if ok else 'failed'}",
                path=str(item.get("path") or ""),
                actual=str(item.get("error") or ""),
                impact="" if ok else 'The unified CLI or project resolver may be unavailable.',
                repair="" if ok else 'Fix the path or project_root issues reported by preflight.',
            )
        )
    return checks


def _file_checks(project_root: Path, snapshot: ProjectPhaseSnapshot) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for rel in INIT_REQUIRED_DIRS:
        path = project_path(project_root, rel)
        rel = _rel(project_root, path)
        exists = path.is_dir()
        checks.append(
            _check(
                f"file.dir.{rel}",
                status=CHECK_OK if exists else CHECK_ERROR,
                severity="info" if exists else "blocker",
                message=f"required directory {rel}",
                path=str(path),
                expected="directory exists",
                actual="exists" if exists else "missing",
                impact="" if exists else 'The project scaffold is incomplete. Writing, backups, or reports may fail.',
                repair="" if exists else 'Rerun /webnovel-init, or create the directory manually and rerun doctor.',
            )
        )
    for rel in INIT_REQUIRED_FILES:
        path = project_path(project_root, rel)
        rel = _rel(project_root, path)
        exists = path.is_file()
        checks.append(
            _check(
                f"file.required.{rel}",
                status=CHECK_OK if exists else CHECK_ERROR,
                severity="info" if exists else "blocker",
                message=f"required file {rel}",
                path=str(path),
                expected="file exists",
                actual="exists" if exists else "missing",
                impact="" if exists else 'Required initialization files are missing. Phase detection and later workflows may be unreliable.',
                repair="" if exists else 'Use /webnovel-init to complete the scaffold, or restore files from the init_project.py templates.',
            )
        )

    if snapshot.phase not in {PHASE_NO_PROJECT, PHASE_INIT_SCAFFOLDED, PHASE_INIT_READY} and snapshot.target_chapter > 0:
        for name, path in contract_files_for_chapter(project_root, snapshot.target_chapter).items():
            exists = path.is_file()
            checks.append(
                _check(
                    f"file.contract.{name}",
                    status=CHECK_OK if exists else CHECK_ERROR,
                    severity="info" if exists else "blocker",
                    message=f"story contract {name}",
                    path=str(path),
                    expected="file exists",
                    actual="exists" if exists else "missing",
                    impact="" if exists else 'The writing context lacks canonical contracts and may rely on stale state or outlines.',
                    repair="" if exists else 'Run webnovel.py story-system ... --persist --emit-runtime-contracts --chapter N.',
                )
            )
    return checks


def _json_checks(project_root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    json_files = [
        project_root / ".webnovel" / "state.json",
        project_root / ".story-system" / "MASTER_SETTING.json",
    ]
    for path in json_files:
        if not path.exists():
            checks.append(
                _check(
                    f"json.{_rel(project_root, path)}",
                    status=CHECK_SKIPPED,
                    severity="info",
                    message=f"{_rel(project_root, path)} not present",
                    path=str(path),
                    expected="valid JSON object when present",
                    actual="missing",
                )
            )
            continue
        payload, error = _read_json(path)
        checks.append(
            _check(
                f"json.{_rel(project_root, path)}",
                status=CHECK_OK if not error else CHECK_ERROR,
                severity="info" if not error else "blocker",
                message=f"{_rel(project_root, path)} json parse",
                path=str(path),
                expected="valid JSON object",
                actual="ok" if not error else error,
                impact="" if not error else 'Unreadable JSON can break the CLI, dashboard, or state inference.',
                repair="" if not error else 'Repair the UTF-8 JSON format; restore from git or a backup if needed.',
            )
        )
        if path.name == "state.json" and not error:
            for key in ("project_info", "progress"):
                checks.append(
                    _check(
                        f"json.state.{key}",
                        status=CHECK_OK if isinstance(payload.get(key), dict) else CHECK_WARNING,
                        severity="info" if isinstance(payload.get(key), dict) else "warning",
                        message=f"state.json contains {key}",
                        path=str(path),
                        expected="object field",
                        actual=type(payload.get(key)).__name__,
                        impact="" if isinstance(payload.get(key), dict) else 'Legacy projects or manually edited state may lack runtime fields.',
                        repair="" if isinstance(payload.get(key), dict) else 'Run webnovel.py init in the same directory to fill in missing schema fields.',
                    )
                )
    return checks


def _sqlite_table_count(path: Path, table: str) -> tuple[bool, int, str]:
    if not path.is_file():
        return False, 0, "missing"
    try:
        with sqlite3.connect(str(path)) as conn:
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if not row:
                return False, 0, "table_missing"
            count_row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            return True, int(count_row[0] or 0) if count_row else 0, ""
    except sqlite3.Error as exc:
        return False, 0, str(exc)


def _sqlite_checks(project_root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    cfg = DataModulesConfig.from_project_root(project_root)
    for db_path, table, check_id, impact in (
        (cfg.index_db, "chapters", "sqlite.index_db.chapters", 'Queries, relationship graphs, and dashboard chapter statistics will be degraded.'),
        (cfg.vector_db, "vectors", "sqlite.vector_db.vectors", 'RAG vector retrieval is unavailable; keyword or empty retrieval will be used.'),
    ):
        exists = db_path.is_file()
        table_ok, count, error = _sqlite_table_count(db_path, table)
        if not exists:
            checks.append(
                _check(
                    check_id,
                    status=CHECK_WARNING,
                    severity="warning",
                    message=f"{db_path.name} missing",
                    path=str(db_path),
                    expected=f"sqlite db with {table} table",
                    actual="missing",
                    impact=impact,
                    repair='Run the corresponding index/rag command to build the database. This can be deferred immediately after initialization.',
                )
            )
            continue
        checks.append(
            _check(
                check_id,
                status=CHECK_OK if table_ok else CHECK_WARNING,
                severity="info" if table_ok else "warning",
                message=f"{db_path.name}.{table}",
                path=str(db_path),
                expected=f"{table} table readable",
                actual=f"rows={count}" if table_ok else error,
                impact="" if table_ok else impact,
                repair="" if table_ok else 'Rerun the index/RAG build command. Restore corrupted SQLite databases from backup.',
            )
        )
    return checks


def _rag_checks(project_root: Path) -> list[dict[str, Any]]:
    cfg = DataModulesConfig.from_project_root(project_root)
    checks: list[dict[str, Any]] = []
    for key, present, base_url, model in (
        ("embed", bool(str(cfg.embed_api_key or "").strip()), cfg.embed_base_url, cfg.embed_model),
        ("rerank", bool(str(cfg.rerank_api_key or "").strip()), cfg.rerank_base_url, cfg.rerank_model),
    ):
        checks.append(
            _check(
                f"rag.{key}.api_key",
                status=CHECK_OK if present else CHECK_WARNING,
                severity="info" if present else "warning",
                message=f"{key} api key configured",
                expected="api key present in env or .env",
                actual=f"present; model={model}; base_url={base_url}" if present else f"missing; model={model}; base_url={base_url}",
                impact="" if present else 'RAG calls will be unavailable or degraded.',
                repair="" if present else 'Copy .env.example to .env and enter the required API keys. Never commit real keys.',
            )
        )
    return checks


def _projection_log_checks(project_root: Path, snapshot: ProjectPhaseSnapshot) -> list[dict[str, Any]]:
    log_path = projection_log_path(project_root)
    latest_commit = snapshot.latest_commit
    if latest_commit is None:
        return [
            _check(
                "projection_log.present",
                status=CHECK_SKIPPED,
                severity="info",
                message="no commit yet; projection log not required",
                path=str(log_path),
                expected="projection log after first commit",
                actual="no commit",
            )
        ]
    if not log_path.is_file():
        return [
            _check(
                "projection_log.present",
                status=CHECK_WARNING,
                severity="warning",
                message="projection log missing for project with commits",
                path=str(log_path),
                expected="projection_log.jsonl exists after projection run",
                actual="missing",
                impact='Independent projection history is unavailable. Embedded commit projection_status remains supported.',
                repair='Later chapter-commit runs will write projection_log automatically. Legacy projects can defer this.',
            )
        ]
    latest = latest_projection_run(project_root, chapter=latest_commit.chapter)
    if not latest:
        return [
            _check(
                "projection_log.latest_run",
                status=CHECK_WARNING,
                severity="warning",
                message="projection log has no run for latest commit",
                path=str(log_path),
                expected=f"run for chapter {latest_commit.chapter}",
                actual="missing",
                impact='The latest commit has no visible projection execution history.',
                repair='Projection retry/replay can fill this in later. Embedded commit projection_status remains supported.',
            )
        ]
    failed = projection_run_failed(latest)
    pending = projection_run_pending(latest)
    status_ok = not failed and not pending
    return [
        _check(
            "projection_log.latest_run",
            status=CHECK_OK if status_ok else CHECK_ERROR,
            severity="info" if status_ok else "blocker",
            message="latest projection log run",
            path=str(log_path),
            expected="latest run status done/skipped",
            actual=f"chapter={latest.get('chapter')} status={latest.get('status')}",
            impact='Read-model projections failed or remain incomplete and need to be rerun.' if not status_ok else "",
            repair='Inspect the writers field in projection_log.jsonl, fix the issue, and run projection retry/replay.' if not status_ok else "",
        )
    ]


def _python_checks() -> list[dict[str, Any]]:
    checks = [
        _check(
            "python.version",
            status=CHECK_OK if sys.version_info >= (3, 10) else CHECK_ERROR,
            severity="info" if sys.version_info >= (3, 10) else "blocker",
            message="python version",
            expected=">= 3.10",
            actual=platform.python_version(),
            impact="" if sys.version_info >= (3, 10) else 'The runtime requires Python 3.10+ syntax and library behavior.',
            repair="" if sys.version_info >= (3, 10) else 'Switch to Python 3.10 or newer.',
        )
    ]
    for module_name in ("aiohttp", "filelock", "pydantic"):
        found = importlib.util.find_spec(module_name) is not None
        checks.append(
            _check(
                f"python.import.{module_name}",
                status=CHECK_OK if found else CHECK_ERROR,
                severity="info" if found else "blocker",
                message=f"import {module_name}",
                expected="module importable",
                actual="present" if found else "missing",
                impact="" if found else 'Core data modules may not run.',
                repair="" if found else 'Run python -m pip install -r scripts/requirements.txt.',
            )
        )
    for module_name in ("fastapi", "uvicorn", "watchdog"):
        found = importlib.util.find_spec(module_name) is not None
        checks.append(
            _check(
                f"python.import.dashboard.{module_name}",
                status=CHECK_OK if found else CHECK_WARNING,
                severity="info" if found else "warning",
                message=f"import {module_name}",
                expected="module importable for dashboard",
                actual="present" if found else "missing",
                impact="" if found else 'The dashboard server may not start.',
                repair="" if found else 'Run python -m pip install -r dashboard/requirements.txt.',
            )
        )
    return checks


def _dashboard_checks(plugin_root: Path | None = None) -> list[dict[str, Any]]:
    if plugin_root is None:
        plugin_root = Path(__file__).resolve().parents[2]
    dashboard_root = plugin_root / "dashboard"
    dist = dashboard_root / "frontend" / "dist"
    package_json = dashboard_root / "frontend" / "package.json"
    requirements = dashboard_root / "requirements.txt"
    checks: list[dict[str, Any]] = []
    for check_id, path, expected in (
        ("dashboard.root", dashboard_root, "directory exists"),
        ("dashboard.frontend.dist", dist, "built frontend dist exists"),
        ("dashboard.frontend.package_json", package_json, "package.json exists"),
        ("dashboard.requirements", requirements, "requirements.txt exists"),
    ):
        exists = path.is_dir() if expected.startswith("directory") or path == dist else path.is_file()
        checks.append(
            _check(
                check_id,
                status=CHECK_OK if exists else CHECK_WARNING,
                severity="info" if exists else "warning",
                message=check_id,
                path=str(path),
                expected=expected,
                actual="exists" if exists else "missing",
                impact="" if exists else 'The dashboard may not open, or frontend artifacts may be missing from the release.',
                repair="" if exists else 'Build the frontend following the dashboard documentation, or check that dist is included.',
            )
        )
    return checks


def build_doctor_report(
    project_root: str | Path | None,
    *,
    chapter: int | None = None,
    deep: bool = False,
    preflight_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = resolve_project_phase(project_root, chapter=chapter)
    checks: list[dict[str, Any]] = []
    checks.extend(_preflight_checks(preflight_report))

    if snapshot.phase == PHASE_NO_PROJECT or not snapshot.project_root:
        checks.append(
            _check(
                "project.root",
                status=CHECK_ERROR,
                severity="blocker",
                message="project root not resolved",
                path=str(project_root or ""),
                expected=".webnovel/state.json",
                actual="missing",
                impact='Project state cannot be determined and the writing workflow cannot run safely.',
                repair='Run /webnovel-init, or bind an existing project with webnovel.py use <project_root>.',
            )
        )
    else:
        root = Path(snapshot.project_root)
        checks.extend(_file_checks(root, snapshot))
        checks.extend(_json_checks(root))
        try:
            runtime_health = build_story_runtime_health(root, chapter=chapter)
        except Exception as exc:
            runtime_health = {"error": str(exc)}
            checks.append(
                _check(
                    "story_runtime.health",
                    status=CHECK_WARNING,
                    severity="warning",
                    message="story runtime health failed",
                    actual=str(exc),
                    impact='The canonical Story System health summary is unavailable.',
                    repair='Check that .story-system contracts and commit JSON are readable.',
                )
            )
        else:
            checks.append(
                _check(
                    "story_runtime.health",
                    status=CHECK_OK if runtime_health.get("mainline_ready") else CHECK_WARNING,
                    severity="info" if runtime_health.get("mainline_ready") else "warning",
                    message="story runtime health",
                    expected="mainline_ready true when writing stage",
                    actual=json.dumps(runtime_health, ensure_ascii=False),
                    impact="" if runtime_health.get("mainline_ready") else 'The current chapter may use a fallback source.',
                    repair="" if runtime_health.get("mainline_ready") else 'Complete the Story System contracts and accepted commit before writing.',
                )
            )
        checks.extend(_sqlite_checks(root))
        checks.extend(_projection_log_checks(root, snapshot))
        checks.extend(_rag_checks(root))

    checks.extend(_python_checks())
    if deep:
        checks.extend(_dashboard_checks())

    blocking = [item for item in checks if item["severity"] == "blocker" and item["status"] == CHECK_ERROR]
    warnings = [item for item in checks if item["status"] == CHECK_WARNING]
    recommended_actions = [item["repair"] for item in checks if item.get("repair")]
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": not blocking,
        "project_root": snapshot.project_root,
        "mode": "deep" if deep else "standard",
        "phase": snapshot.phase,
        "expected_profile": _expected_profile(snapshot),
        "blocking_count": len(blocking),
        "warning_count": len(warnings),
        "checks": checks,
        "recommended_actions": list(dict.fromkeys(recommended_actions)),
    }


def format_doctor_report(report: dict[str, Any], output_format: str = "text") -> str:
    if output_format == "json":
        return json.dumps(report, ensure_ascii=False, indent=2)
    status = "OK" if report.get("ok") else "ERROR"
    lines = [
        f"{status} webnovel-doctor",
        f"project_root: {report.get('project_root') or '(Unresolved)'}",
        f"phase: {report.get('phase')}",
        f"blocking: {report.get('blocking_count')} warnings: {report.get('warning_count')}",
    ]
    for item in report.get("checks") or []:
        if item.get("status") == CHECK_OK:
            continue
        lines.append(f"{str(item.get('status')).upper()} {item.get('id')}: {item.get('message')}")
        if item.get("path"):
            lines.append(f"  path: {item.get('path')}")
        if item.get("actual"):
            lines.append(f"  actual: {item.get('actual')}")
        if item.get("impact"):
            lines.append(f"  impact: {item.get('impact')}")
        if item.get("repair"):
            lines.append(f"  repair: {item.get('repair')}")
    actions = report.get("recommended_actions") or []
    if actions:
        lines.append("recommended_actions:")
        lines.extend(f"- {action}" for action in actions[:8])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run read-only webnovel project doctor")
    parser.add_argument("--project-root", default="", help="Book project root")
    parser.add_argument("--chapter", type=int, default=None, help="Target chapter number")
    parser.add_argument("--deep", action="store_true", help="Include deeper checks such as the dashboard")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    report = build_doctor_report(args.project_root or None, chapter=args.chapter, deep=args.deep)
    print(format_doctor_report(report, args.format))
    raise SystemExit(0 if report.get("ok") else 1)


if __name__ == "__main__":
    main()
