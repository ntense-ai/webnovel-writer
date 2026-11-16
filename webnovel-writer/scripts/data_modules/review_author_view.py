#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MAX_ACTIONS = 3


@dataclass(frozen=True)
class ReviewAuthorView:
    verdict: str
    status: str
    actions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "status": self.status,
            "actions": list(self.actions),
        }


def _issue_priority(issue: dict[str, Any]) -> tuple[int, int]:
    severity_rank = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    blocking_rank = 0 if issue.get("blocking") else 1
    severity = str(issue.get("severity") or "medium")
    return blocking_rank, severity_rank.get(severity, 2)


def _action_from_issue(issue: dict[str, Any]) -> str:
    description = str(issue.get("description") or "No issue description provided").strip()
    fix_hint = str(issue.get("fix_hint") or "").strip()
    location = str(issue.get("location") or "").strip()

    prefix = f"{location}: " if location else ""
    if fix_hint:
        return f"{prefix}{description}. Suggestion: {fix_hint}"
    return f"{prefix}{description}"


def build_review_author_view(payload: dict[str, Any]) -> ReviewAuthorView:
    result = payload.get("review_result") or {}
    issues = [item for item in result.get("issues") or [] if isinstance(item, dict)]
    blocking_issues = [issue for issue in issues if issue.get("blocking")]
    sorted_issues = sorted(issues, key=_issue_priority)

    blocking_count = int(result.get("blocking_count") or len(blocking_issues))
    if blocking_count > 0:
        source = blocking_issues or sorted_issues
        actions = tuple(_action_from_issue(issue) for issue in source[:MAX_ACTIONS])
        return ReviewAuthorView(
            verdict="⛔ Fix before continuing",
            status="must_fix",
            actions=actions or ("Resolve blocking issues before writing the next chapter.",),
        )

    if sorted_issues:
        actions = tuple(_action_from_issue(issue) for issue in sorted_issues[:MAX_ACTIONS])
        return ReviewAuthorView(
            verdict="⚠️ Changes recommended",
            status="suggest_fix",
            actions=actions,
        )

    summary = str(result.get("summary") or "").strip()
    action = summary if summary else "No blocking issues were found. You can continue."
    return ReviewAuthorView(
        verdict="✅ Ready to continue",
        status="can_continue",
        actions=(action,),
    )


def render_review_author_view(payload: dict[str, Any]) -> str:
    view = build_review_author_view(payload)
    lines = [
        "## Author view",
        "",
        f"Chapter verdict: {view.verdict}",
        "",
        "Top 1–3 issues to address:",
    ]
    lines.extend(f"- {action}" for action in view.actions[:MAX_ACTIONS])
    return "\n".join(lines).rstrip() + "\n"
