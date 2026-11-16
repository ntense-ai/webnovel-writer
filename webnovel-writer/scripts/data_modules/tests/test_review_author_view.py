#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from data_modules.review_author_view import build_review_author_view, render_review_author_view


def _payload(issues, *, summary=""):
    return {
        "chapter": 1,
        "review_result": {
            "issues": issues,
            "issues_count": len(issues),
            "blocking_count": sum(1 for issue in issues if issue.get("blocking")),
            "has_blocking": any(issue.get("blocking") for issue in issues),
            "summary": summary,
        },
        "metrics": {},
    }


def test_review_author_view_marks_blocking_as_must_fix():
    view = build_review_author_view(
        _payload(
            [
                {
                    "severity": "critical",
                    "category": "timeline",
                    "location": "Chapter2paragraph",
                    "description": "timeline jumps backward",
                    "fix_hint": "add a transition from late night to dawn",
                    "blocking": True,
                },
                {
                    "severity": "medium",
                    "description": "pacing slightly slow",
                    "fix_hint": "shorten explanations",
                },
            ]
        )
    )

    assert view.status == "must_fix"
    assert view.verdict == "⛔ Fix before continuing"
    assert len(view.actions) == 1
    assert "timeline jumps backward" in view.actions[0]
    assert "add a transition" in view.actions[0]


def test_review_author_view_limits_actions_to_three_and_prioritizes_severity():
    issues = [
        {"severity": "low", "description": "low priority"},
        {"severity": "medium", "description": "medium priority"},
        {"severity": "high", "description": "high priority"},
        {"severity": "critical", "description": "serious but nonblocking", "blocking": False},
    ]

    view = build_review_author_view(_payload(issues))

    assert view.status == "suggest_fix"
    assert view.verdict == "⚠️ Changes recommended"
    assert len(view.actions) == 3
    assert "serious but nonblocking" in view.actions[0]
    assert "high priority" in view.actions[1]
    assert "medium priority" in view.actions[2]


def test_review_author_view_allows_clean_chapter_to_continue():
    view = build_review_author_view(_payload([], summary="overall continuation allowed"))

    assert view.status == "can_continue"
    assert view.verdict == "✅ Ready to continue"
    assert view.actions == ("overall continuation allowed",)


def test_review_author_view_render_has_author_section():
    rendered = render_review_author_view(
        _payload(
            [
                {
                    "severity": "high",
                    "location": "Chapter5paragraph",
                    "description": "unclear character motivation",
                    "fix_hint": "add an internal dilemma",
                }
            ]
        )
    )

    assert rendered.startswith("## Author view")
    assert "Chapter verdict: ⚠️ Changes recommended" in rendered
    assert "unclear character motivation" in rendered
