#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from ..artifact_validator import validate_chapter_commit
from ..artifact_validator import OK_PROJECTION_STATUSES, REQUIRED_PROJECTION_WRITERS
from ..config import DataModulesConfig
from ..project_phase import resolve_project_phase
from ..projection_log import latest_projection_run, projection_status_from_run
from . import gate_report, issue


def _commit_path(project_root: Path, chapter: int) -> Path:
    return project_root / ".story-system" / "commits" / f"chapter_{chapter:03d}.commit.json"


def _projection_status_from_runtime(
    project_root: Path,
    chapter: int,
    payload: dict,
) -> tuple[dict[str, str], str, dict]:
    try:
        latest_run = latest_projection_run(project_root, chapter=chapter)
        logged_status = projection_status_from_run(latest_run)
    except Exception:
        latest_run = None
        logged_status = {}
    if logged_status:
        return logged_status, "projection_log", latest_run or {}

    raw_status = payload.get("projection_status") if isinstance(payload, dict) else {}
    if isinstance(raw_status, dict):
        return {str(key): str(value) for key, value in raw_status.items()}, "commit", {}
    return {}, "commit", {}


def run_postcommit_gate(project_root: Path, chapter: int) -> dict:
    snapshot = resolve_project_phase(project_root, chapter=chapter)
    errors: list[dict] = []
    warnings: list[dict] = []
    commit_path = _commit_path(project_root, chapter)
    commit_report = validate_chapter_commit(commit_path)

    for item in commit_report.get("errors") or []:
        errors.append(
            issue(
                f"commit.{item.get('type')}",
                message=str(item.get("message") or ""),
                path=str(item.get("path") or commit_path),
                impact=str(item.get("impact") or ""),
                repair=str(item.get("repair") or ""),
                details=item,
            )
        )

    payload = commit_report.get("payload") if isinstance(commit_report.get("payload"), dict) else {}
    meta = payload.get("meta") if isinstance(payload, dict) else {}
    status = str((meta or {}).get("status") or "")
    if commit_path.is_file() and status != "accepted":
        errors.append(
            issue(
                "commit_not_accepted",
                message=f"chapter commit status is {status or 'missing'}",
                path=str(commit_path),
                impact="The chapter sufficiency gate requires an accepted commit before backup or the next chapter.",
                repair="Resolve blocking review, fulfillment, or disambiguation issues, then resubmit.",
            )
        )

    projection_status, projection_source, projection_run = _projection_status_from_runtime(
        project_root,
        chapter,
        payload,
    )
    if isinstance(projection_status, dict):
        for writer in REQUIRED_PROJECTION_WRITERS:
            status_text = str(projection_status.get(writer) or "").strip()
            if not status_text:
                errors.append(
                    issue(
                        "projection_status_missing",
                        message=f"projection {writer} status missing",
                        path=str(commit_path),
                        impact="Postcommit must confirm all five projection statuses: state, index, summary, memory, and vector.",
                        repair="Rerun chapter-commit or use projection retry/replay.",
                        details={"source": projection_source},
                    )
                )
            elif status_text.startswith("failed"):
                errors.append(
                    issue(
                        "projection_failure",
                        message=f"projection {writer} failed: {status_text}",
                        path=str(commit_path),
                        impact="The latest projection_log shows a failed read-model projection.",
                        repair="Inspect the writers field in projection_log.jsonl, repair the problem, then use projection retry/replay.",
                        details={"source": projection_source, "run": projection_run},
                    )
                )
            elif status_text == "pending":
                errors.append(
                    issue(
                        "projection_pending",
                        message=f"projection {writer} is still pending",
                        path=str(commit_path),
                        impact="The read-model write has not yet been confirmed complete.",
                        repair="Run chapter-commit again or use projection retry/replay afterward.",
                    )
                )
            elif status_text not in OK_PROJECTION_STATUSES:
                errors.append(
                    issue(
                        "projection_status_invalid",
                        message=f"projection {writer} status is {status_text}",
                        path=str(commit_path),
                        impact="Postcommit accepts only done or skipped projection states.",
                        repair="Wait for projection completion or use projection retry/replay.",
                    )
                )

    cfg = DataModulesConfig.from_project_root(project_root)
    if isinstance(projection_status, dict) and projection_status.get("summary") == "done":
        summary_path = cfg.webnovel_dir / "summaries" / f"ch{chapter:04d}.md"
        if not summary_path.is_file():
            errors.append(
                issue(
                    "summary_projection_missing",
                    message="summary projection marked done but file is missing",
                    path=str(summary_path),
                    impact="Subsequent context cannot read this chapter's summary.",
                    repair="Retry the summary projection or rerun chapter-commit.",
                )
            )
    if isinstance(projection_status, dict) and projection_status.get("index") == "done" and not cfg.index_db.is_file():
        errors.append(
            issue(
                "index_projection_missing",
                message="index projection marked done but index.db is missing",
                path=str(cfg.index_db),
                impact="Query, dashboard, and entity-relationship read models are unavailable.",
                repair="Retry the index projection or rerun chapter-commit.",
            )
        )
    if isinstance(projection_status, dict) and projection_status.get("memory") == "done" and not cfg.scratchpad_file.is_file():
        warnings.append(
            issue(
                "memory_projection_missing",
                message="memory projection marked done but scratchpad is missing",
                severity="warning",
                path=str(cfg.scratchpad_file),
                impact="Long-term memory may not have been written.",
                repair="Check the memory projection output and retry if necessary.",
            )
        )

    return gate_report(
        stage="postcommit",
        project_root=project_root,
        chapter=chapter,
        phase=snapshot.phase,
        errors=errors,
        warnings=warnings,
        details={
            "phase": snapshot.to_dict(),
            "commit_path": str(commit_path),
            "commit_report": commit_report,
            "projection_source": projection_source,
            "projection_run": projection_run,
        },
    )
