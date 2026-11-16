#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review schema test"""
import json

import pytest
from data_modules.review_schema import (
    ReviewIssue,
    ReviewResult,
    append_ai_flavor_anti_patterns,
    parse_review_output,
)


def test_review_issue_blocking_defaults():
    """critical severity default blocking=True"""
    issue = ReviewIssue(
        severity="critical",
        category="continuity",
        location="Chapter3paragraph",
        description="the protagonist used an ability they had lost",
    )
    assert issue.blocking is True


def test_review_issue_non_critical_not_blocking():
    """non- critical default blocking=False"""
    issue = ReviewIssue(
        severity="high",
        category="setting",
        location="Chapter7paragraph",
        description="timeline contradiction",
    )
    assert issue.blocking is False


def test_review_result_counts():
    """blocking_count calculate automatically"""
    result = ReviewResult(
        chapter=10,
        issues=[
            ReviewIssue(severity="critical", category="continuity", location="p1", description="d1"),
            ReviewIssue(severity="high", category="setting", location="p2", description="d2"),
            ReviewIssue(severity="high", category="timeline", location="p3", description="d3", blocking=True),
        ],
        summary="test",
    )
    assert result.blocking_count == 2
    assert result.issues_count == 3
    assert result.has_blocking is True


def test_review_result_no_issues():
    result = ReviewResult(chapter=10, issues=[], summary="no issues")
    assert result.blocking_count == 0
    assert result.has_blocking is False


def test_review_result_to_dict_roundtrip():
    result = ReviewResult(
        chapter=10,
        issues=[
            ReviewIssue(severity="medium", category="ai_flavor", location="p5", description="AIstrong flavor",
                        evidence="'steady oneself'appears3 times", fix_hint="replace with concrete action description"),
        ],
        summary="1itemsAIflavor issue",
    )
    d = result.to_dict()
    assert d["chapter"] == 10
    assert d["blocking_count"] == 0
    assert len(d["issues"]) == 1
    assert d["issues"][0]["category"] == "ai_flavor"
    assert d["issues"][0]["fix_hint"] == "replace with concrete action description"


def test_parse_review_output_from_dict():
    raw = {
        "issues": [
            {"severity": "critical", "category": "continuity", "location": "p1",
             "description": "contradiction", "evidence": "evidence", "fix_hint": "repair"},
        ],
        "summary": "1serious issues",
    }
    result = parse_review_output(chapter=5, raw=raw)
    assert result.chapter == 5
    assert result.blocking_count == 1


def test_parse_review_output_tolerates_missing_fields():
    raw = {
        "issues": [
            {"severity": "low", "description": "minor issue"},
        ],
        "summary": "minor",
    }
    result = parse_review_output(chapter=1, raw=raw)
    assert result.issues[0].category == "other"
    assert result.issues[0].location == ""


def test_review_result_to_metrics_dict():
    result = ReviewResult(
        chapter=10,
        issues=[
            ReviewIssue(severity="critical", category="continuity", location="p1", description="d1"),
            ReviewIssue(severity="high", category="ai_flavor", location="p2", description="d2"),
        ],
        summary="test",
    )
    metrics = result.to_metrics_dict()
    assert metrics["chapter"] == 10
    assert metrics["start_chapter"] == 10
    assert metrics["end_chapter"] == 10
    assert metrics["issues_count"] == 2
    assert metrics["blocking_count"] == 1
    assert "continuity" in metrics["categories"]
    assert "ai_flavor" in metrics["categories"]
    assert metrics["severity_counts"]["critical"] == 1
    assert metrics["severity_counts"]["high"] == 1
    assert metrics["critical_issues"] == ["d1"]
    assert metrics["report_file"] == ""
    assert metrics["overall_score"] < 100
    assert metrics["dimension_scores"]["continuity"] < 100
    assert metrics["dimension_scores"]["ai_flavor"] < 100


def test_ai_flavor_review_issue_added_to_anti_patterns(tmp_path):
    result = ReviewResult(
        chapter=2,
        issues=[
            ReviewIssue(
                severity="medium",
                category="ai_flavor",
                evidence="the only person who knows the compound-interest formula。the only person who knows the ledger secret。",
            ),
            ReviewIssue(severity="low", category="ai_flavor", evidence="low-risk phrasing"),
            ReviewIssue(severity="high", category="logic", evidence="logic issue"),
        ],
    )

    added = append_ai_flavor_anti_patterns(tmp_path, result)

    patterns = json.loads((tmp_path / ".story-system" / "anti_patterns.json").read_text(encoding="utf-8"))
    assert added == 1
    assert any("the only person who knows" in item["text"] for item in patterns)
    assert patterns[0]["source_id"].startswith("ch0002_issue_")


def test_ai_flavor_review_feedback_dedupes_evidence(tmp_path):
    existing = tmp_path / ".story-system" / "anti_patterns.json"
    existing.parent.mkdir(parents=True)
    existing.write_text(
        json.dumps([{"text": "first chunk / second chunk / third chunk", "source_table": "review_extracted"}], ensure_ascii=False),
        encoding="utf-8",
    )
    result = ReviewResult(
        chapter=3,
        issues=[
            ReviewIssue(
                severity="high",
                category="ai_flavor",
                evidence="first chunk / second chunk / third chunk",
            )
        ],
    )

    added = append_ai_flavor_anti_patterns(tmp_path, result)

    patterns = json.loads(existing.read_text(encoding="utf-8"))
    assert added == 0
    assert len(patterns) == 1
