#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .chapter_commit_schema import (
    DisambiguationResult,
    ExtractionResult,
    FulfillmentResult,
    ReviewResult,
)


SCHEMA_VERSION = "webnovel-artifact-validator/v1"

ERROR_SCHEMA = "schema_error"
ERROR_MISSING = "missing_artifact"
ERROR_BLOCKING_REVIEW = "blocking_review"
ERROR_MISSED_OUTLINE_NODE = "missed_outline_node"
ERROR_PENDING_DISAMBIGUATION = "pending_disambiguation"
ERROR_PROJECTION_FAILURE = "projection_failure"
ERROR_PROJECTION_INCOMPLETE = "projection_incomplete"

REQUIRED_PROJECTION_WRITERS = ("state", "index", "summary", "memory", "vector")
OK_PROJECTION_STATUSES = {"done", "skipped"}

ARTIFACT_SCHEMAS = {
    "review_result": ReviewResult,
    "fulfillment_result": FulfillmentResult,
    "disambiguation_result": DisambiguationResult,
    "extraction_result": ExtractionResult,
}


def _issue(
    issue_type: str,
    *,
    message: str,
    severity: str = "blocker",
    path: str = "",
    field: str = "",
    impact: str = "",
    repair: str = "",
) -> dict[str, str]:
    return {
        "type": issue_type,
        "severity": severity,
        "message": message,
        "path": path,
        "field": field,
        "impact": impact,
        "repair": repair,
    }


def _empty_report(artifact: str, path: str = "") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": artifact,
        "path": path,
        "ok": True,
        "errors": [],
        "warnings": [],
        "payload": None,
    }


def _read_json_artifact(path: str | Path) -> tuple[Any, dict[str, Any] | None]:
    artifact_path = Path(path)
    if not artifact_path.is_file():
        return None, _issue(
            ERROR_MISSING,
            message=f"artifact missing: {artifact_path}",
            path=str(artifact_path),
            impact='Precommit artifacts are incomplete; a reliable chapter commit cannot be generated.',
            repair='Rerun the reviewer/data-agent, or complete the JSON according to its schema.',
        )
    try:
        return json.loads(artifact_path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, _issue(
            ERROR_SCHEMA,
            message=f"invalid JSON: {exc}",
            path=str(artifact_path),
            impact='The runtime cannot read this artifact.',
            repair='Repair the JSON format and ensure the file uses UTF-8.',
        )
    except OSError as exc:
        return None, _issue(
            ERROR_SCHEMA,
            message=f"artifact read failed: {exc}",
            path=str(artifact_path),
            impact='The runtime cannot read this artifact.',
            repair='Check file permissions and the path.',
        )


def _schema_error_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "; ".join(str(error.get("msg") or "") for error in exc.errors()) or str(exc)
    return str(exc)


def _policy_issues(artifact: str, payload: dict[str, Any], path: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if artifact == "review_result":
        blocking_count = int(payload.get("blocking_count") or 0)
        if blocking_count > 0:
            issues.append(
                _issue(
                    ERROR_BLOCKING_REVIEW,
                    message=f"review_result has {blocking_count} blocking issue(s)",
                    path=path,
                    field="blocking_count",
                    impact='A chapter with blocking review issues must not be committed.',
                    repair='Fix the blocking issue, or obtain an explicit user decision before continuing.',
                )
            )
    elif artifact == "fulfillment_result":
        missed = payload.get("missed_nodes") or []
        if missed:
            issues.append(
                _issue(
                    ERROR_MISSED_OUTLINE_NODE,
                    message=f"fulfillment_result missed {len(missed)} planned node(s)",
                    path=path,
                    field="missed_nodes",
                    impact='Required outline nodes are missing; committing would make the deviation canonical.',
                    repair='Write the missing nodes, or revise the chapter plan with user approval.',
                )
            )
    elif artifact == "disambiguation_result":
        pending = payload.get("pending") or []
        if pending:
            issues.append(
                _issue(
                    ERROR_PENDING_DISAMBIGUATION,
                    message=f"disambiguation_result has {len(pending)} pending item(s)",
                    path=path,
                    field="pending",
                    impact='Unresolved entities would corrupt character, relationship, and event projections.',
                    repair='Manually resolve pending items, or remove low-confidence entities from extraction.',
                )
            )
    return issues


def validate_artifact_payload(artifact: str, payload: Any, *, path: str = "") -> dict[str, Any]:
    if artifact not in ARTIFACT_SCHEMAS:
        raise ValueError(f"unknown artifact: {artifact}")

    report = _empty_report(artifact, path)
    schema = ARTIFACT_SCHEMAS[artifact]
    try:
        model = schema.model_validate(payload)
    except Exception as exc:
        report["errors"].append(
            _issue(
                ERROR_SCHEMA,
                message=_schema_error_message(exc),
                path=path,
                impact='Artifact fields do not match the authoritative chapter commit schema.',
                repair='Use the top-level fields required by chapter_commit_schema.py; do not add fulfillment/disambiguation/extraction wrappers.',
            )
        )
        report["ok"] = False
        return report

    normalized = model.model_dump()
    report["payload"] = normalized
    report["errors"].extend(_policy_issues(artifact, normalized, path))
    report["ok"] = not any(item.get("severity") == "blocker" for item in report["errors"])
    return report


def validate_artifact_file(artifact: str, path: str | Path) -> dict[str, Any]:
    report = _empty_report(artifact, str(path))
    payload, error = _read_json_artifact(path)
    if error:
        report["errors"].append(error)
        report["ok"] = False
        return report
    return validate_artifact_payload(artifact, payload, path=str(path))


def validate_review_result(path: str | Path) -> dict[str, Any]:
    return validate_artifact_file("review_result", path)


def validate_fulfillment_result(path: str | Path) -> dict[str, Any]:
    return validate_artifact_file("fulfillment_result", path)


def validate_disambiguation_result(path: str | Path) -> dict[str, Any]:
    return validate_artifact_file("disambiguation_result", path)


def validate_extraction_result(path: str | Path) -> dict[str, Any]:
    return validate_artifact_file("extraction_result", path)


def merge_reports(reports: list[dict[str, Any]], *, artifact: str = "chapter_commit_inputs") -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    payloads: dict[str, Any] = {}
    for report in reports:
        errors.extend(report.get("errors") or [])
        warnings.extend(report.get("warnings") or [])
        if report.get("payload") is not None:
            payloads[str(report.get("artifact"))] = report.get("payload")
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": artifact,
        "ok": not any(item.get("severity") == "blocker" for item in errors),
        "errors": errors,
        "warnings": warnings,
        "payloads": payloads,
        "reports": reports,
    }


def validate_commit_artifact_files(
    *,
    review_result: str | Path,
    fulfillment_result: str | Path,
    disambiguation_result: str | Path,
    extraction_result: str | Path,
) -> dict[str, Any]:
    return merge_reports(
        [
            validate_review_result(review_result),
            validate_fulfillment_result(fulfillment_result),
            validate_disambiguation_result(disambiguation_result),
            validate_extraction_result(extraction_result),
        ]
    )


def validate_chapter_commit(path: str | Path) -> dict[str, Any]:
    commit_path = Path(path)
    report = _empty_report("chapter_commit", str(commit_path))
    payload, error = _read_json_artifact(commit_path)
    if error:
        report["errors"].append(error)
        report["ok"] = False
        return report
    if not isinstance(payload, dict):
        report["errors"].append(
            _issue(
                ERROR_SCHEMA,
                message="chapter_commit must be a JSON object",
                path=str(commit_path),
                impact='The commit file cannot be read as canonical story facts.',
                repair='Restore the commit from backup, or rerun chapter-commit.',
            )
        )
        report["ok"] = False
        return report

    nested_reports = []
    for artifact in ARTIFACT_SCHEMAS:
        if artifact not in payload:
            report["errors"].append(
                _issue(
                    ERROR_SCHEMA,
                    message=f"chapter_commit missing {artifact}",
                    path=str(commit_path),
                    field=artifact,
                    impact='The commit file is missing its artifact snapshot.',
                    repair='Rerun chapter-commit to generate a complete commit.',
                )
            )
            continue
        nested_reports.append(validate_artifact_payload(artifact, payload.get(artifact), path=str(commit_path)))

    projection_status = payload.get("projection_status") or {}
    if not isinstance(projection_status, dict):
        projection_status = {}
    for writer in REQUIRED_PROJECTION_WRITERS:
        status = str(projection_status.get(writer) or "").strip()
        if not status:
            report["errors"].append(
                _issue(
                    ERROR_PROJECTION_INCOMPLETE,
                    message=f"projection {writer} status missing",
                    path=str(commit_path),
                    field=f"projection_status.{writer}",
                    impact='Postcommit must verify all five projection statuses: state/index/summary/memory/vector.',
                    repair='Rerun chapter-commit or run projections retry/replay.',
                )
            )
        elif status.startswith("failed:"):
            report["errors"].append(
                _issue(
                    ERROR_PROJECTION_FAILURE,
                    message=f"projection {writer} failed: {status}",
                    path=str(commit_path),
                    field=f"projection_status.{writer}",
                    impact='Committed facts exist, but read-model projections are incomplete.',
                    repair='Fix the failure, then run projection retry/replay.',
                )
            )
        elif status not in OK_PROJECTION_STATUSES:
            report["errors"].append(
                _issue(
                    ERROR_PROJECTION_INCOMPLETE,
                    message=f"projection {writer} status is {status}",
                    path=str(commit_path),
                    field=f"projection_status.{writer}",
                    impact='Postcommit only accepts projection statuses done or skipped.',
                    repair='Wait for projections to finish, or run projections retry/replay.',
                )
            )

    merged = merge_reports(nested_reports, artifact="chapter_commit_nested")
    report["errors"].extend(merged["errors"])
    report["warnings"].extend(merged["warnings"])
    report["payload"] = payload
    report["ok"] = not any(item.get("severity") == "blocker" for item in report["errors"])
    return report
