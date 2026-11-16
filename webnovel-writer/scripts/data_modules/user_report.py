#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # pragma: no cover - direct script entry
    scripts_dir = Path(__file__).resolve().parents[1]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

from project_paths import project_dir, project_path

try:
    from chapter_paths import find_chapter_file
except ImportError:  # pragma: no cover
    from scripts.chapter_paths import find_chapter_file

if __package__ in {None, ""}:  # pragma: no cover - direct script entry
    from data_modules.artifact_validator import (
        OK_PROJECTION_STATUSES,
        REQUIRED_PROJECTION_WRITERS,
        validate_artifact_payload,
        validate_disambiguation_result,
        validate_extraction_result,
        validate_fulfillment_result,
        validate_review_result,
    )
    from data_modules.error_catalog import AuthorError, classify_issue
    from data_modules.project_phase import (
        COMMIT_ARTIFACT_FILES,
        INIT_REQUIRED_DIRS,
        INIT_REQUIRED_FILES,
        contract_files_for_chapter,
    )
    from data_modules.project_status import build_project_status
    from data_modules.projection_log import (
        latest_projection_run,
        projection_run_failed,
        projection_run_pending,
        projection_status_from_run,
        read_projection_runs,
    )
    from data_modules.review_author_view import build_review_author_view
else:
    from .artifact_validator import (
        OK_PROJECTION_STATUSES,
        REQUIRED_PROJECTION_WRITERS,
        validate_artifact_payload,
        validate_disambiguation_result,
        validate_extraction_result,
        validate_fulfillment_result,
        validate_review_result,
    )
    from .error_catalog import AuthorError, classify_issue
    from .project_phase import (
        COMMIT_ARTIFACT_FILES,
        INIT_REQUIRED_DIRS,
        INIT_REQUIRED_FILES,
        contract_files_for_chapter,
    )
    from .project_status import build_project_status
    from .projection_log import (
        latest_projection_run,
        projection_run_failed,
        projection_run_pending,
        projection_status_from_run,
        read_projection_runs,
    )
    from .review_author_view import build_review_author_view


SCHEMA_VERSION = "webnovel-user-report/v1"
VALID_STAGES = ("init", "plan", "write", "review")
VALID_FORMATS = ("text", "json")

STATUS_COMPLETED = "completed"
STATUS_PARTIAL = "partial"
STATUS_NEEDS_USER = "needs_user"
STATUS_FAILED = "failed"

STATUS_TEXT = {
    STATUS_COMPLETED: "Completed",
    STATUS_PARTIAL: "Partially completed",
    STATUS_NEEDS_USER: "Action required",
    STATUS_FAILED: "Incomplete",
}


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "missing"
    except json.JSONDecodeError as exc:
        return {}, f"invalid_json:{exc}"
    except OSError as exc:
        return {}, f"read_error:{exc}"
    if not isinstance(payload, dict):
        return {}, "not_object"
    return payload, ""


def _rel(project_root: Path, path: Path | str) -> str:
    raw = Path(path)
    try:
        return raw.resolve().relative_to(project_root.resolve()).as_posix()
    except Exception:
        return str(path)


def _new_report(
    project_root: Path,
    *,
    stage: str,
    chapter: int | None = None,
    volume: int | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "overall_status": STATUS_COMPLETED,
        "project_root": str(project_root),
        "chapter": int(chapter or 0),
        "volume": int(volume or 0),
        "files": [],
        "issues": {
            "auto_handled": [],
            "needs_confirmation": [],
            "must_handle": [],
        },
        "timing": {
            "total_ms": 0,
            "steps": [],
        },
        "next_actions": [],
    }


def _add_file(
    report: dict[str, Any],
    *,
    label: str,
    path: Path | str,
    status: str,
    note: str = "",
) -> None:
    report["files"].append(
        {
            "label": label,
            "path": str(path),
            "status": status,
            "note": note,
        }
    )


def _issue_from_author_error(
    error: AuthorError,
    *,
    source: str = "",
    path: str = "",
    message: str = "",
) -> dict[str, Any]:
    return {
        "code": error.code,
        "title": error.title,
        "reason": error.reason,
        "impact": error.impact,
        "next_action": error.next_action,
        "command": error.command,
        "source": source,
        "path": path,
        "message": message,
        "auto_handle": error.auto_handle,
        "matched": error.matched,
    }


def _add_classified_issue(
    report: dict[str, Any],
    issue: Any,
    *,
    source: str = "",
    path: str = "",
    message: str = "",
    severity: str | None = None,
) -> None:
    error = classify_issue(issue)
    bucket = severity or error.severity
    if bucket not in report["issues"]:
        bucket = "must_handle"
    entry = _issue_from_author_error(error, source=source, path=path, message=message)
    if entry not in report["issues"][bucket]:
        report["issues"][bucket].append(entry)


def _add_manual_issue(
    report: dict[str, Any],
    bucket: str,
    *,
    code: str,
    title: str,
    reason: str,
    impact: str,
    next_action: str,
    command: str = "",
    source: str = "",
    path: str = "",
    message: str = "",
    auto_handle: bool = False,
) -> None:
    if bucket not in report["issues"]:
        bucket = "must_handle"
    entry = {
        "code": code,
        "title": title,
        "reason": reason,
        "impact": impact,
        "next_action": next_action,
        "command": command,
        "source": source,
        "path": path,
        "message": message,
        "auto_handle": auto_handle,
        "matched": True,
    }
    if entry not in report["issues"][bucket]:
        report["issues"][bucket].append(entry)


def _artifact_paths(project_root: Path) -> dict[str, Path]:
    return {
        "review_result": project_root / COMMIT_ARTIFACT_FILES[0],
        "fulfillment_result": project_root / COMMIT_ARTIFACT_FILES[1],
        "disambiguation_result": project_root / COMMIT_ARTIFACT_FILES[2],
        "extraction_result": project_root / COMMIT_ARTIFACT_FILES[3],
    }


def _validate_artifact_for_report(
    report: dict[str, Any],
    artifact: str,
    path: Path,
) -> dict[str, Any]:
    validators = {
        "review_result": validate_review_result,
        "fulfillment_result": validate_fulfillment_result,
        "disambiguation_result": validate_disambiguation_result,
        "extraction_result": validate_extraction_result,
    }
    validator = validators[artifact]
    result = validator(path)
    return _add_artifact_validation_result(
        report,
        artifact=artifact,
        result=result,
        path=path,
        ok_note="Generated",
        error_note="Missing or incomplete format",
    )


def _validate_commit_artifact_for_report(
    report: dict[str, Any],
    artifact: str,
    commit_payload: dict[str, Any],
    commit_path: Path,
) -> dict[str, Any]:
    if artifact not in commit_payload:
        result = {
            "artifact": artifact,
            "ok": False,
            "errors": [
                {
                    "type": "missing_artifact",
                    "message": f"chapter commit missing {artifact}",
                    "impact": "The commit file is missing its artifact snapshot.",
                    "repair": "Run chapter-commit again to generate a complete commit.",
                }
            ],
            "payload": None,
        }
    else:
        result = validate_artifact_payload(artifact, commit_payload.get(artifact), path=str(commit_path))
    return _add_artifact_validation_result(
        report,
        artifact=artifact,
        result=result,
        path=commit_path,
        ok_note="Saved in this chapter commit",
        error_note="Incomplete artifact format in commit",
    )


def _add_artifact_validation_result(
    report: dict[str, Any],
    *,
    artifact: str,
    result: dict[str, Any],
    path: Path,
    ok_note: str,
    error_note: str,
) -> dict[str, Any]:
    file_status = "completed" if result.get("ok") else "failed"
    note = ok_note if result.get("ok") else error_note
    _add_file(report, label=artifact, path=_rel(Path(report["project_root"]), path), status=file_status, note=note)
    for item in result.get("errors") or []:
        issue = {
            "code": item.get("type") or item.get("code") or "",
            "message": item.get("message") or "",
            "impact": item.get("impact") or "",
            "repair": item.get("repair") or "",
        }
        if str(issue["code"]) == "blocking_review":
            _add_classified_issue(
                report,
                {"code": "blocking_review", "message": issue["message"]},
                source=artifact,
                path=_rel(Path(report["project_root"]), path),
                message=str(issue["message"] or ""),
                severity="must_handle",
            )
        else:
            _add_classified_issue(
                report,
                issue,
                source=artifact,
                path=_rel(Path(report["project_root"]), path),
                message=str(issue["message"] or ""),
            )
    return result


def _review_metrics_path(project_root: Path) -> Path:
    return project_root / ".webnovel" / "tmp" / "review_metrics.json"


def _review_report_path_from_metrics(project_root: Path, metrics: dict[str, Any]) -> Path | None:
    report_file = str(metrics.get("report_file") or "").strip()
    if not report_file:
        return None
    path = Path(report_file)
    if not path.is_absolute():
        path = project_root / path
    return path


def _find_review_report(project_root: Path, chapter: int) -> Path | None:
    metrics, _ = _read_json(_review_metrics_path(project_root))
    path = _review_report_path_from_metrics(project_root, metrics)
    if path and path.is_file():
        return path
    reports_dir = project_dir(project_root, "reviews")
    if not reports_dir.is_dir():
        return None
    patterns = (f"chapter-{chapter}-review.md", f"chapter-{chapter:03d}-review.md", f"chapter-{chapter:04d}-review.md")
    for pattern in patterns:
        matches = sorted(reports_dir.rglob(pattern))
        for item in matches:
            if item.is_file():
                return item
    return None


def _commit_path(project_root: Path, chapter: int) -> Path:
    return project_root / ".story-system" / "commits" / f"chapter_{chapter:03d}.commit.json"


def _projection_status_from_commit(payload: dict[str, Any]) -> dict[str, str]:
    raw = payload.get("projection_status") if isinstance(payload, dict) else {}
    if not isinstance(raw, dict):
        return {}
    return {str(key): str(value) for key, value in raw.items()}


def _is_projection_ok(statuses: dict[str, str]) -> bool:
    if not statuses:
        return False
    for writer in REQUIRED_PROJECTION_WRITERS:
        if str(statuses.get(writer) or "") not in OK_PROJECTION_STATUSES:
            return False
    return True


def _projection_failed(statuses: dict[str, str]) -> bool:
    return any(str(value).startswith("failed") for value in statuses.values())


def _projection_pending_or_missing(statuses: dict[str, str]) -> bool:
    if not statuses:
        return True
    return any(
        not str(statuses.get(writer) or "").strip()
        or str(statuses.get(writer) or "") == "pending"
        or str(statuses.get(writer) or "") not in OK_PROJECTION_STATUSES
        for writer in REQUIRED_PROJECTION_WRITERS
    )


def _add_projection_issues(
    report: dict[str, Any],
    project_root: Path,
    chapter: int,
    commit_payload: dict[str, Any],
) -> None:
    runs = read_projection_runs(project_root, chapter=chapter)
    latest_run = latest_projection_run(project_root, chapter=chapter)
    latest_statuses = projection_status_from_run(latest_run) if latest_run else {}
    status_source = "projection_log" if latest_statuses else "commit"
    statuses = latest_statuses or _projection_status_from_commit(commit_payload)

    had_failed_or_pending = any(projection_run_failed(run) or projection_run_pending(run) for run in runs[:-1])
    latest_ok = bool(latest_run and _is_projection_ok(statuses))
    if had_failed_or_pending and latest_ok:
        _add_manual_issue(
            report,
            "auto_handled",
            code="projection retry",
            title="Story data update recovered",
            reason="An earlier data synchronization failed or waited; a later projection succeeded.",
            impact="Chapter facts are synchronized with the story data. You can continue writing.",
            next_action="No action is needed. Check `.webnovel/projection_log.jsonl` to verify.",
            source=status_source,
            path=".webnovel/projection_log.jsonl",
            auto_handle=True,
        )
        return

    if _projection_failed(statuses):
        _add_classified_issue(
            report,
            {"code": "projection_failure", "message": str(statuses)},
            source=status_source,
            path=".webnovel/projection_log.jsonl" if status_source == "projection_log" else _rel(project_root, _commit_path(project_root, chapter)),
            message=str(statuses),
        )
    elif _projection_pending_or_missing(statuses):
        _add_classified_issue(
            report,
            {"code": "projection_status_missing", "message": str(statuses)},
            source=status_source,
            path=".webnovel/projection_log.jsonl" if status_source == "projection_log" else _rel(project_root, _commit_path(project_root, chapter)),
            message=str(statuses),
        )


def _backup_evidence(project_root: Path, chapter: int) -> tuple[bool, str]:
    backup_dir = project_root / ".webnovel" / "backups"
    if backup_dir.is_dir():
        patterns = (f"ch{chapter:04d}*", f"*{chapter:04d}*")
        for pattern in patterns:
            if any(backup_dir.glob(pattern)):
                return True, _rel(project_root, backup_dir)
    return False, _rel(project_root, backup_dir)


def _status_from_issues(report: dict[str, Any], *, core_file_count: int = 0) -> str:
    issues = report.get("issues") or {}
    if issues.get("must_handle"):
        return STATUS_NEEDS_USER if core_file_count > 0 else STATUS_FAILED
    if issues.get("needs_confirmation"):
        return STATUS_PARTIAL
    return STATUS_COMPLETED


def _append_project_status_next_action(report: dict[str, Any], project_root: Path, chapter: int | None) -> None:
    try:
        status = build_project_status(project_root, chapter=chapter)
    except Exception:
        status = {}
    next_action = str(status.get("next_action") or "").strip()
    if next_action:
        report["next_actions"].append(
            {
                "label": "Continue this project",
                "description": next_action,
                "command": next_action if next_action.startswith("/") else "",
            }
        )


def build_write_report(project_root: Path, *, chapter: int, volume: int | None = None) -> dict[str, Any]:
    report = _new_report(project_root, stage="write", chapter=chapter, volume=volume)
    core_files = 0
    commit_path = _commit_path(project_root, chapter)
    commit_payload, commit_error = _read_json(commit_path)

    chapter_file = find_chapter_file(project_root, chapter)
    if chapter_file:
        core_files += 1
        _add_file(report, label="Chapter draft", path=_rel(project_root, chapter_file), status="completed", note="Generated")
    else:
        _add_file(report, label="Chapter draft", path=_rel(project_root, project_dir(project_root, "chapters")), status="missing", note="Chapter draft not found")
        _add_manual_issue(
            report,
            "must_handle",
            code="chapter_file_missing",
            title="Missing chapter draft",
            reason="No draft file was found for this chapter.",
            impact="This chapter cannot be committed as story facts.",
            next_action="Run the same writing command again to resume drafting.",
            command=f"/webnovel-write {chapter}",
            path=_rel(project_root, project_dir(project_root, "chapters")),
        )

    review_report = _find_review_report(project_root, chapter)
    if review_report:
        _add_file(report, label="Review report", path=_rel(project_root, review_report), status="completed", note="Generated")
    else:
        _add_file(report, label="Review report", path=_rel(project_root, project_dir(project_root, "reviews")), status="missing", note="Review report file not found")

    artifact_results: dict[str, dict[str, Any]] = {}
    commit_has_artifact_snapshots = not commit_error and any(
        artifact in commit_payload for artifact in _artifact_paths(project_root)
    )
    if commit_has_artifact_snapshots:
        for artifact in _artifact_paths(project_root):
            artifact_results[artifact] = _validate_commit_artifact_for_report(
                report,
                artifact,
                commit_payload,
                commit_path,
            )
    else:
        for artifact, path in _artifact_paths(project_root).items():
            artifact_results[artifact] = _validate_artifact_for_report(report, artifact, path)

    review_payload = artifact_results.get("review_result", {}).get("payload") or {}
    if isinstance(review_payload, dict) and review_payload.get("review_skipped"):
        _add_manual_issue(
            report,
            "needs_confirmation",
            code="review_skipped",
            title="Writing checks skipped in minimal mode",
            reason="This writing run used a no-review artifact, without a full reviewer assessment.",
            impact="The draft can be saved, but you must decide whether to accept its quality risks.",
            next_action="Run `/webnovel-review` to check this chapter.",
            command="/webnovel-review",
            source="review_result",
            path=COMMIT_ARTIFACT_FILES[0],
        )

    if commit_error:
        _add_file(report, label="Chapter fact commit", path=_rel(project_root, commit_path), status="missing", note="No commit generated")
        _add_classified_issue(
            report,
            {"code": "missing_artifact", "message": "chapter commit missing"},
            source="chapter_commit",
            path=_rel(project_root, commit_path),
            message="chapter commit missing",
        )
    else:
        core_files += 1
        status = str((commit_payload.get("meta") or {}).get("status") or "")
        file_status = "completed" if status == "accepted" else "failed"
        note = f"status={status or 'missing'}"
        _add_file(report, label="Chapter fact commit", path=_rel(project_root, commit_path), status=file_status, note=note)
        if status == "rejected":
            _add_classified_issue(
                report,
                {"code": "chapter-commit rejected", "message": "chapter commit rejected"},
                source="chapter_commit",
                path=_rel(project_root, commit_path),
                message="chapter commit rejected",
            )
        elif status != "accepted":
            _add_manual_issue(
                report,
                "must_handle",
                code="commit_status_unknown",
                title="Chapter commit status is unclear",
                reason=f"Commit status is `{status or 'missing'}`, not accepted.",
                impact="The system cannot confirm that this chapter entered the canonical story.",
                next_action="Run `/webnovel-doctor` for details and recommit chapter facts if needed.",
                command="/webnovel-doctor",
                source="chapter_commit",
                path=_rel(project_root, commit_path),
            )
        else:
            _add_projection_issues(report, project_root, chapter, commit_payload)

    backup_ok, backup_path = _backup_evidence(project_root, chapter)
    _add_file(
        report,
        label="Backup",
        path=backup_path,
        status="completed" if backup_ok else "unknown",
        note="Backup record found" if backup_ok else "No verifiable backup record found",
    )
    if commit_payload and str((commit_payload.get("meta") or {}).get("status") or "") == "accepted" and not backup_ok:
        _add_manual_issue(
            report,
            "needs_confirmation",
            code="backup_unconfirmed",
            title="Backup status unconfirmed",
            reason="No backup evidence for this chapter was found in `.webnovel/backups`.",
            impact="Chapter facts were generated, but rollback protection still needs verification.",
            next_action="Run the backup command or repeat the writing finalization steps.",
            command=f"/webnovel-write {chapter}",
            source="backup",
            path=backup_path,
        )

    report["overall_status"] = _status_from_issues(report, core_file_count=core_files)
    if report["overall_status"] == STATUS_COMPLETED:
        report["next_actions"].append(
            {
                "label": "Write the next chapter",
                "description": f"You can continue with Chapter {chapter + 1}.",
                "command": f"/webnovel-write {chapter + 1}",
            }
        )
    elif report["issues"]["must_handle"]:
        report["next_actions"].append(
            {
                "label": "Resolve blockers first",
                "description": "Resolve the required issues, then rerun the same writing command.",
                "command": f"/webnovel-write {chapter}",
            }
        )
    else:
        _append_project_status_next_action(report, project_root, chapter)
    return report


def _load_review_result(project_root: Path) -> tuple[dict[str, Any], Path, str]:
    path = project_root / ".webnovel" / "tmp" / "review_results.json"
    payload, error = _read_json(path)
    return payload, path, error


def build_review_report(project_root: Path, *, chapter: int, volume: int | None = None) -> dict[str, Any]:
    report = _new_report(project_root, stage="review", chapter=chapter, volume=volume)
    core_files = 0
    review_result, review_path, review_error = _load_review_result(project_root)
    if review_error:
        _add_file(report, label="Review results", path=_rel(project_root, review_path), status="missing", note="review_results.json not found")
        _add_classified_issue(
            report,
            {"code": "missing_artifact", "message": "review_results missing"},
            source="review",
            path=_rel(project_root, review_path),
            message="review_results missing",
        )
    else:
        core_files += 1
        blocking_count = int(review_result.get("blocking_count") or 0)
        _add_file(report, label="Review results", path=_rel(project_root, review_path), status="completed", note=f"blocking={blocking_count}")
        view = build_review_author_view({"review_result": review_result})
        report["review_author_view"] = view.to_dict()
        if blocking_count > 0:
            _add_manual_issue(
                report,
                "must_handle",
                code="blocking_review",
                title="Review found required fixes",
                reason=f"This chapter has {blocking_count} blocking issues.",
                impact="Unresolved issues affect writing, commits, or factual consistency.",
                next_action="Resolve the review blockers first. Keeping this version requires an explicit user decision.",
                command="/webnovel-review",
                source="review",
                path=_rel(project_root, review_path),
            )

    metrics_path = _review_metrics_path(project_root)
    metrics, metrics_error = _read_json(metrics_path)
    if metrics_error:
        _add_file(report, label="Review metrics", path=_rel(project_root, metrics_path), status="missing", note="review_metrics.json not found")
        _add_manual_issue(
            report,
            "needs_confirmation",
            code="review_metrics_missing",
            title="Review metrics not saved",
            reason="`.webnovel/tmp/review_metrics.json` was not found.",
            impact="The review is readable, but the dashboard or trends may lack this chapter.",
            next_action="Rerun the review workflow and save the metrics.",
            command="/webnovel-review",
            source="review",
            path=_rel(project_root, metrics_path),
        )
    else:
        _add_file(report, label="Review metrics", path=_rel(project_root, metrics_path), status="completed", note="Generated")

    report_path = _review_report_path_from_metrics(project_root, metrics) if metrics else None
    if report_path and report_path.is_file():
        _add_file(report, label="Review report file", path=_rel(project_root, report_path), status="completed", note="Generated")
    else:
        found = _find_review_report(project_root, chapter)
        if found:
            _add_file(report, label="Review report file", path=_rel(project_root, found), status="completed", note="Generated")
        else:
            _add_file(report, label="Review report file", path=_rel(project_root, project_dir(project_root, "reviews")), status="missing", note="Review report file not found")
            _add_manual_issue(
                report,
                "needs_confirmation",
                code="review_report_missing",
                title="Review report file not found",
                reason="No readable Markdown review report was found.",
                impact="Review JSON remains available, but the readable suggestions are missing.",
                next_action="Rerun the review workflow and specify a report file.",
                command="/webnovel-review",
                source="review",
                path=_rel(project_root, project_dir(project_root, "reviews")),
            )

    report["overall_status"] = _status_from_issues(report, core_file_count=core_files)
    if report["issues"]["must_handle"]:
        report["next_actions"].append(
            {
                "label": "Resolve review issues",
                "description": "Resolve review blockers before writing or committing.",
                "command": "/webnovel-review",
            }
        )
    else:
        report["next_actions"].append(
            {
                "label": "Continue writing",
                "description": f"If this chapter is satisfactory, continue with Chapter {chapter + 1}.",
                "command": f"/webnovel-write {chapter + 1}",
            }
        )
    return report


def build_init_report(project_root: Path, *, chapter: int | None = None, volume: int | None = None) -> dict[str, Any]:
    report = _new_report(project_root, stage="init", chapter=chapter, volume=volume)
    core_files = 0
    for rel in INIT_REQUIRED_DIRS:
        path = project_path(project_root, rel)
        rel = _rel(project_root, path)
        if path.is_dir():
            core_files += 1
            _add_file(report, label=rel, path=rel, status="completed", note="Created")
        else:
            _add_file(report, label=rel, path=rel, status="missing", note="Missing directory")
            _add_classified_issue(report, {"code": "mainline_ready=false", "message": rel}, source="init", path=rel)
    for rel in INIT_REQUIRED_FILES:
        path = project_path(project_root, rel)
        rel = _rel(project_root, path)
        if path.is_file():
            core_files += 1
            _add_file(report, label=rel, path=rel, status="completed", note="Generated")
        else:
            _add_file(report, label=rel, path=rel, status="missing", note="Missing file")
            _add_classified_issue(report, {"code": "mainline_ready=false", "message": rel}, source="init", path=rel)
    report["overall_status"] = _status_from_issues(report, core_file_count=core_files)
    _append_project_status_next_action(report, project_root, chapter)
    return report


def build_plan_report(project_root: Path, *, chapter: int | None = None, volume: int | None = None) -> dict[str, Any]:
    target_chapter = int(chapter or 1)
    report = _new_report(project_root, stage="plan", chapter=target_chapter, volume=volume)
    core_files = 0
    outline_path = project_path(project_root, "outlines/master-outline.md")
    if outline_path.is_file():
        core_files += 1
        _add_file(report, label="Master outline", path=_rel(project_root, outline_path), status="completed", note="Generated")
    else:
        _add_file(report, label="Master outline", path=_rel(project_root, outline_path), status="missing", note="Missing master outline")
        _add_classified_issue(report, {"code": "mainline_ready=false", "message": "missing outline"}, source="plan", path=_rel(project_root, outline_path))

    for label, path in contract_files_for_chapter(project_root, target_chapter).items():
        if path.is_file():
            core_files += 1
            _add_file(report, label=f"Story System {label}", path=_rel(project_root, path), status="completed", note="Contract generated")
        else:
            _add_file(report, label=f"Story System {label}", path=_rel(project_root, path), status="missing", note="Missing contract")
            _add_classified_issue(report, {"code": "mainline_ready=false", "message": f"missing {label} contract"}, source="plan", path=_rel(project_root, path))

    report["overall_status"] = _status_from_issues(report, core_file_count=core_files)
    _append_project_status_next_action(report, project_root, target_chapter)
    return report


def build_user_report(
    project_root: str | Path,
    *,
    stage: str,
    chapter: int | None = None,
    volume: int | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    stage = str(stage or "").strip()
    if stage not in VALID_STAGES:
        raise ValueError(f"unknown user report stage: {stage}")

    if stage == "write":
        if not chapter:
            status = build_project_status(root)
            chapter = int(status.get("target_chapter") or 0)
        return build_write_report(root, chapter=int(chapter or 0), volume=volume)
    if stage == "review":
        if not chapter:
            status = build_project_status(root)
            chapter = int(status.get("target_chapter") or 0)
        return build_review_report(root, chapter=int(chapter or 0), volume=volume)
    if stage == "init":
        return build_init_report(root, chapter=chapter, volume=volume)
    return build_plan_report(root, chapter=chapter, volume=volume)


def _format_issue_item(item: dict[str, Any]) -> str:
    title = str(item.get("title") or item.get("code") or "Issue")
    impact = str(item.get("impact") or "").strip()
    action = str(item.get("next_action") or "").strip()
    command = str(item.get("command") or "").strip()
    parts = [title]
    if impact:
        parts.append(f"Impact: {impact}")
    if action:
        parts.append(f"Next step: {action}")
    if command:
        parts.append(f"Command: {command}")
    return "；".join(parts)


def _render_issue_bucket(title: str, items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return [f"- {title}: None."]
    return [f"- {title}: {_format_issue_item(item)}" for item in items]


def render_user_report_text(report: dict[str, Any]) -> str:
    status = STATUS_TEXT.get(str(report.get("overall_status") or ""), "Incomplete")
    lines = [
        f"Overall status: {status}.",
        "",
        "1. Files and completion status",
    ]
    files = report.get("files") or []
    if files:
        for item in files:
            label = str(item.get("label") or "File")
            status_text = str(item.get("status") or "unknown")
            path = str(item.get("path") or "")
            note = str(item.get("note") or "")
            suffix = f" ({note})" if note else ""
            path_part = f"{path}: " if path else ""
            lines.append(f"- {label}: {path_part}{status_text}{suffix}")
    else:
        lines.append("- No verified artifacts yet.")

    issues = report.get("issues") or {}
    lines.extend(["", "2. Issues and unusual duration"])
    lines.extend(_render_issue_bucket("Automatically resolved", list(issues.get("auto_handled") or [])))
    lines.extend(_render_issue_bucket("Confirmation recommended", list(issues.get("needs_confirmation") or [])))
    lines.extend(_render_issue_bucket("Required fixes", list(issues.get("must_handle") or [])))
    timing = report.get("timing") or {}
    total_ms = int(timing.get("total_ms") or 0)
    if total_ms > 0:
        lines.append(f"- Unusual duration: approximately {total_ms // 1000} seconds recorded.")
    else:
        lines.append("- Unusual duration: none recorded.")
    if str(report.get("overall_status") or "") == STATUS_FAILED:
        lines.append("- Technical details: include `.webnovel/logs/run_last.log` when reporting a problem.")

    lines.extend(["", "3. Suggested next steps"])
    next_actions = report.get("next_actions") or []
    if next_actions:
        for item in next_actions:
            description = str(item.get("description") or item.get("label") or "").strip()
            command = str(item.get("command") or "").strip()
            if command and command != description:
                lines.append(f"- {description} Run: {command}")
            else:
                lines.append(f"- {description}")
    else:
        lines.append("- No suggested next step. Run `/webnovel-doctor` to inspect the project.")
    return "\n".join(lines).rstrip() + "\n"


def format_user_report(report: dict[str, Any], output_format: str = "text") -> str:
    if output_format == "json":
        return json.dumps(report, ensure_ascii=False, indent=2)
    return render_user_report_text(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render author-friendly webnovel run report")
    parser.add_argument("--project-root", required=True, help="Book project root")
    parser.add_argument("--stage", choices=VALID_STAGES, required=True, help="Report stage")
    parser.add_argument("--chapter", type=int, default=None, help="Target chapter number")
    parser.add_argument("--volume", type=int, default=None, help="Target volume number")
    parser.add_argument("--format", choices=VALID_FORMATS, default="text", help="Output format")
    args = parser.parse_args()

    report = build_user_report(
        args.project_root,
        stage=args.stage,
        chapter=args.chapter,
        volume=args.volume,
    )
    print(format_user_report(report, args.format))


if __name__ == "__main__":
    main()
