#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'Process Step 3 review results.\n\nParse reviewer-agent JSON output as ReviewResult and generate metrics for persistence in index.db.'
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from runtime_compat import enable_windows_utf8_stdio
from project_paths import project_path


def _ensure_scripts_path() -> None:
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


_ensure_scripts_path()

from data_modules.review_author_view import render_review_author_view
from data_modules.review_schema import append_ai_flavor_anti_patterns, parse_review_output


def _resolve_report_path(project_root: Path, report_file: str) -> Path:
    root = project_root.expanduser().resolve()
    report_path = Path(report_file).expanduser()
    if not report_path.is_absolute():
        report_path = project_path(root, report_path)
    report_path = report_path.resolve()
    try:
        report_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("report-file must be within project_root") from exc
    return report_path


def _format_issue(issue: Dict[str, Any], index: int) -> List[str]:
    description = str(issue.get("description") or "No issue description provided")
    severity = str(issue.get("severity") or "medium")
    category = str(issue.get("category") or "other")
    location = str(issue.get("location") or "Location not specified")
    evidence = str(issue.get("evidence") or "No evidence provided")
    fix_hint = str(issue.get("fix_hint") or "No fix direction provided")
    blocking = "yes" if issue.get("blocking") else "no"

    return [
        f"{index}. **{description}**",
        f"   - Severity: {severity}",
        f"   - Category: {category}",
        f"   - Location: {location}",
        f"   - Blocking: {blocking}",
        f"   - Evidence: {evidence}",
        f"   - Fix direction: {fix_hint}",
    ]


def render_review_report(payload: Dict[str, Any]) -> str:
    result = payload["review_result"]
    metrics = payload["metrics"]
    issues = list(result.get("issues", []))
    blocking_issues = [issue for issue in issues if issue.get("blocking")]
    non_blocking_issues = [issue for issue in issues if not issue.get("blocking")]
    severity_counts = metrics.get("severity_counts", {})

    lines: List[str] = [
        f"# Chapter {payload['chapter']} Review Report",
        "",
        render_review_author_view(payload).rstrip(),
        "",
        "## Overview",
        "",
        f"- Issues: {result.get('issues_count', 0)}",
        f"- Blocking issues: {result.get('blocking_count', 0)}",
        f"- Verdict: {'Fix and review again' if result.get('has_blocking') else 'No blocking issues'}",
    ]
    summary = str(result.get("summary") or "").strip()
    if summary:
        lines.append(f"- Summary: {summary}")
    if severity_counts:
        ordered = [
            f"{level}={severity_counts.get(level, 0)}"
            for level in ("critical", "high", "medium", "low")
        ]
        lines.append(f"- Severity counts: {', '.join(ordered)}")

    lines.extend(["", "## Blocking Issues", ""])
    if blocking_issues:
        for index, issue in enumerate(blocking_issues, start=1):
            lines.extend(_format_issue(issue, index))
            lines.append("")
    else:
        lines.append("None.")
        lines.append("")

    lines.extend(["## Other Issues", ""])
    if non_blocking_issues:
        for index, issue in enumerate(non_blocking_issues, start=1):
            lines.extend(_format_issue(issue, index))
            lines.append("")
    else:
        lines.append("None.")
        lines.append("")

    lines.extend(["## Fix Directions", ""])
    if issues:
        ordered_issues = [*blocking_issues, *non_blocking_issues]
        for index, issue in enumerate(ordered_issues, start=1):
            description = str(issue.get("description") or "No issue description provided")
            fix_hint = str(issue.get("fix_hint") or "No fix direction provided")
            lines.append(f"{index}. {description}: {fix_hint}")
    else:
        lines.append("No issues need fixing.")

    return "\n".join(lines).rstrip() + "\n"


def write_review_report(project_root: Path, report_file: str, payload: Dict[str, Any]) -> Path:
    report_path = _resolve_report_path(project_root, report_file)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_review_report(payload), encoding="utf-8")
    return report_path


def _build_review_metrics_record(metrics: Dict[str, Any]):
    from data_modules.index_manager import ReviewMetrics

    return ReviewMetrics(
        start_chapter=int(metrics["start_chapter"]),
        end_chapter=int(metrics["end_chapter"]),
        overall_score=float(metrics.get("overall_score", 0.0)),
        dimension_scores=dict(metrics.get("dimension_scores", {})),
        severity_counts=dict(metrics.get("severity_counts", {})),
        critical_issues=list(metrics.get("critical_issues", [])),
        report_file=str(metrics.get("report_file", "")),
        notes=str(metrics.get("notes", "")),
    )


def build_review_artifacts(
    project_root: Path,
    chapter: int,
    review_results_path: Path,
    report_file: str = "",
) -> Dict[str, Any]:
    raw = json.loads(review_results_path.read_text(encoding="utf-8"))
    result = parse_review_output(chapter=chapter, raw=raw)
    anti_patterns_added = append_ai_flavor_anti_patterns(project_root, result)
    if report_file:
        report_file = _resolve_report_path(project_root, report_file).relative_to(project_root.resolve()).as_posix()
    metrics = result.to_metrics_dict(report_file=report_file)
    normalized_review = result.to_dict()
    review_results_path.parent.mkdir(parents=True, exist_ok=True)
    review_results_path.write_text(
        json.dumps(normalized_review, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "chapter": chapter,
        "review_result": normalized_review,
        "metrics": metrics,
        "anti_patterns_added": anti_patterns_added,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Review pipeline v6")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--review-results", required=True)
    parser.add_argument("--metrics-out", default="")
    parser.add_argument("--report-file", default="")
    parser.add_argument("--save-metrics", action="store_true",
                        help="Write directly to index.db without a separate save-review-metrics call")

    args = parser.parse_args()
    project_root = Path(args.project_root)
    review_results_path = Path(args.review_results)

    payload = build_review_artifacts(
        project_root=project_root,
        chapter=args.chapter,
        review_results_path=review_results_path,
        report_file=args.report_file,
    )

    if args.metrics_out:
        out_path = Path(args.metrics_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(payload["metrics"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if args.report_file:
        write_review_report(
            project_root=project_root,
            report_file=args.report_file,
            payload=payload,
        )

    if args.save_metrics:
        from data_modules.config import DataModulesConfig
        from data_modules.index_manager import IndexManager
        config = DataModulesConfig.from_project_root(project_root)
        manager = IndexManager(config)
        manager.save_review_metrics(_build_review_metrics_record(payload["metrics"]))

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if sys.platform == "win32":
        enable_windows_utf8_stdio()
    main()
