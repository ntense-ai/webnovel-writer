# Phase 1: Remove Obsolete Modules + Consolidate Review + Streamline the Workflow

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove modules that provide no value (workflow, resume), consolidate six checkers into one review agent, and merge Step 2B into Step 4, targeting a 60–70% reduction in tokens per chapter.

**Architecture:** A purely subtractive refactor. Delete workflow_manager.py and its tests, the resume skill, and their references. Merge six independent checker agents into one `reviewer.md` producing a new structured issue-list schema. Reduce webnovel-write SKILL.md from eight steps to seven. Adapt review_pipeline.py to the new schema and remove the workflow command from webnovel.py CLI.

**Tech Stack:** Python 3.13, pytest, Claude Code plugin (markdown agents/skills)

**Spec:** `docs/superpowers/specs/2026-04-02-harness-v6-design.md`

---

## File Structure

### Files to Delete

| File | Reason |
|------|------|
| `scripts/workflow_manager.py` | Replaced by native Claude Code /resume |
| `scripts/data_modules/tests/test_workflow_manager.py` | Corresponding module removed |
| `skills/webnovel-resume/SKILL.md` | Same as above |
| `skills/webnovel-resume/references/workflow-resume.md` | Same as above |
| `agents/consistency-checker.md` | Merged into reviewer.md |
| `agents/continuity-checker.md` | Merged into reviewer.md |
| `agents/ooc-checker.md` | Merged into reviewer.md |
| `agents/high-point-checker.md` | Merged into reviewer.md |
| `agents/pacing-checker.md` | Merged into reviewer.md |
| `agents/reader-pull-checker.md` | Merged into reviewer.md |
| `references/checker-output-schema.md` | Replaced by the new schema |
| `skills/webnovel-write/references/step-3-review-gate.md` | Logic inlined into SKILL.md |
| `skills/webnovel-write/references/step-5-debt-switch.md` | 0.6KB; inline into SKILL.md |
| `skills/webnovel-write/references/workflow-details.md` | Already marked deprecated |
| `skills/webnovel-write/references/step-1.5-contract.md` | context-agent will be refactored |

### Files to Create

| File | Responsibility |
|------|------|
| `agents/reviewer.md` | Unified review agent producing structured issue lists |
| `references/review-schema.md` | New review-output schema definition |
| `scripts/data_modules/review_schema.py` | Python dataclasses and validation for the new schema |
| `scripts/data_modules/tests/test_review_schema.py` | New schema tests |

### Files to Modify

| File | Change |
|------|--------|
| `skills/webnovel-write/SKILL.md` | New seven-step workflow; remove workflow logging and Step 2B; consolidate review |
| `scripts/review_pipeline.py` | Adapt to new schema: no overall_score, with blocking_count |
| `scripts/data_modules/webnovel.py` | Remove workflow command routing |
| `scripts/data_modules/index_manager.py` | Adapt review_metrics schema: remove overall_score, add issues_count/blocking_count |
| `scripts/data_modules/tests/test_webnovel_unified_cli.py` | Remove workflow-related tests |
| `scripts/data_modules/tests/test_coverage_boost.py` | Remove workflow-related references |

---

## Task 1: Define the New Review Schema

**Files:**
- Create: `scripts/data_modules/review_schema.py`
- Create: `scripts/data_modules/tests/test_review_schema.py`
- Create: `references/review-schema.md`

- [ ] **Step 1: Write Schema Tests**

```python
# scripts/data_modules/tests/test_review_schema.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Review schema tests"""
import pytest
from data_modules.review_schema import ReviewIssue, ReviewResult, parse_review_output


def test_review_issue_blocking_defaults():
    """Critical severity defaults to blocking=True"""
    issue = ReviewIssue(
        severity="critical",
        category="continuity",
        location="第3段",
        description="主角使用了已失去的能力",
    )
    assert issue.blocking is True


def test_review_issue_non_critical_not_blocking():
    """Noncritical severity defaults to blocking=False"""
    issue = ReviewIssue(
        severity="high",
        category="setting",
        location="第7段",
        description="时间线矛盾",
    )
    assert issue.blocking is False


def test_review_result_counts():
    """blocking_count is computed automatically"""
    result = ReviewResult(
        chapter=10,
        issues=[
            ReviewIssue(severity="critical", category="continuity", location="p1", description="d1"),
            ReviewIssue(severity="high", category="setting", location="p2", description="d2"),
            ReviewIssue(severity="high", category="timeline", location="p3", description="d3", blocking=True),
        ],
        summary="测试",
    )
    assert result.blocking_count == 2
    assert result.issues_count == 3
    assert result.has_blocking is True


def test_review_result_no_issues():
    result = ReviewResult(chapter=10, issues=[], summary="无问题")
    assert result.blocking_count == 0
    assert result.has_blocking is False


def test_review_result_to_dict_roundtrip():
    result = ReviewResult(
        chapter=10,
        issues=[
            ReviewIssue(severity="medium", category="ai_flavor", location="p5", description="AI味重",
                        evidence="'稳住心神'出现3次", fix_hint="替换为具体动作描写"),
        ],
        summary="1个AI味问题",
    )
    d = result.to_dict()
    assert d["chapter"] == 10
    assert d["blocking_count"] == 0
    assert len(d["issues"]) == 1
    assert d["issues"][0]["category"] == "ai_flavor"
    assert d["issues"][0]["fix_hint"] == "替换为具体动作描写"


def test_parse_review_output_from_dict():
    raw = {
        "issues": [
            {"severity": "critical", "category": "continuity", "location": "p1",
             "description": "矛盾", "evidence": "证据", "fix_hint": "修复"},
        ],
        "summary": "1个严重问题",
    }
    result = parse_review_output(chapter=5, raw=raw)
    assert result.chapter == 5
    assert result.blocking_count == 1


def test_parse_review_output_tolerates_missing_fields():
    raw = {
        "issues": [
            {"severity": "low", "description": "小问题"},
        ],
        "summary": "轻微",
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
        summary="测试",
    )
    metrics = result.to_metrics_dict()
    assert metrics["chapter"] == 10
    assert metrics["issues_count"] == 2
    assert metrics["blocking_count"] == 1
    assert "continuity" in metrics["categories"]
    assert "ai_flavor" in metrics["categories"]
```

- [ ] **Step 2: Run Tests and Confirm Failure**

Run: `cd webnovel-writer/scripts && python -m pytest data_modules/tests/test_review_schema.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'data_modules.review_schema'`

- [ ] **Step 3: Implement review_schema.py**

```python
# scripts/data_modules/review_schema.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Review result schema (v6).

Replace the scoring system from checker-output-schema.md with structured issue lists.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_CATEGORIES = {
    "continuity", "setting", "character", "timeline",
    "ai_flavor", "logic", "pacing", "other",
}


@dataclass
class ReviewIssue:
    severity: str
    category: str = "other"
    location: str = ""
    description: str = ""
    evidence: str = ""
    fix_hint: str = ""
    blocking: Optional[bool] = None

    def __post_init__(self):
        if self.severity not in VALID_SEVERITIES:
            self.severity = "medium"
        if self.category not in VALID_CATEGORIES:
            self.category = "other"
        if self.blocking is None:
            self.blocking = self.severity == "critical"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewResult:
    chapter: int
    issues: List[ReviewIssue] = field(default_factory=list)
    summary: str = ""

    @property
    def issues_count(self) -> int:
        return len(self.issues)

    @property
    def blocking_count(self) -> int:
        return sum(1 for i in self.issues if i.blocking)

    @property
    def has_blocking(self) -> bool:
        return self.blocking_count > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter,
            "issues": [i.to_dict() for i in self.issues],
            "issues_count": self.issues_count,
            "blocking_count": self.blocking_count,
            "has_blocking": self.has_blocking,
            "summary": self.summary,
        }

    def to_metrics_dict(self) -> Dict[str, Any]:
        categories = sorted(set(i.category for i in self.issues))
        return {
            "chapter": self.chapter,
            "issues_count": self.issues_count,
            "blocking_count": self.blocking_count,
            "categories": categories,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }


def parse_review_output(chapter: int, raw: Dict[str, Any]) -> ReviewResult:
    issues = []
    for item in raw.get("issues", []):
        if not isinstance(item, dict):
            continue
        issues.append(ReviewIssue(
            severity=str(item.get("severity", "medium")),
            category=str(item.get("category", "other")),
            location=str(item.get("location", "")),
            description=str(item.get("description", "")),
            evidence=str(item.get("evidence", "")),
            fix_hint=str(item.get("fix_hint", "")),
            blocking=item.get("blocking"),
        ))
    return ReviewResult(
        chapter=chapter,
        issues=issues,
        summary=str(raw.get("summary", "")),
    )
```

- [ ] **Step 4: Run Tests and Confirm Success**

Run: `cd webnovel-writer/scripts && python -m pytest data_modules/tests/test_review_schema.py -v --no-cov`
Expected: 8 passed

- [ ] **Step 5: Write the review-schema.md Reference**

```markdown
# Review Output Schema (v6)

Unified review-agent output format, replacing the scoring system in checker-output-schema.md.

## Core Changes

- **No overall score**: output structured issue lists instead of overall_score
- **Blocking semantics**: replace timeline_gate; severity=critical blocks by default
- **Single agent**: reviewer produces all output instead of six separate checkers

## Issue Schema

| Field | Type | Required | Description |
|------|------|------|------|
| severity | critical/high/medium/low | ✅ | Severity |
| category | continuity/setting/character/timeline/ai_flavor/logic/pacing/other | ✅ | Issue category |
| location | string | ✅ | Location, e.g. paragraph 3 |
| description | string | ✅ | Issue description |
| evidence | string | ❌ | Source quotation or memory comparison |
| fix_hint | string | ❌ | Repair guidance |
| blocking | bool | ❌ | Whether blocking; critical defaults to true |

## Blocking Rules

- Any issue with `blocking=true` → Step 4 must not begin
- `severity=critical` automatically sets `blocking=true`
- For other severity levels, the review agent decides based on context

## Metrics Persistence

Each review writes to `index.db.review_metrics`:
- `chapter, issues_count, blocking_count, categories, timestamp`
- For trend monitoring, not gate decisions
```

- [ ] **Step 6: Commit**

```bash
git add scripts/data_modules/review_schema.py scripts/data_modules/tests/test_review_schema.py references/review-schema.md
git commit -m "feat: new review schema (v6): structured issue lists replace scoring"
```

---

## Task 2: Create the Unified Review Agent

**Files:**
- Create: `agents/reviewer.md`

- [ ] **Step 1: Write reviewer.md**

```markdown
---
name: reviewer
description: Unified review agent. Checks setting consistency, narrative continuity, character consistency, timeline, and AI-like writing, then outputs structured issue lists.
tools: Read, Grep, Bash
model: inherit
---

# reviewer (Unified Review Agent)

## Identity and Goal

You are a chapter reviewer. Read the prose, identify all verifiable problems, and output a structured issue list.

Do not score, offer general advice, or write summary evaluations. Identify problems, supply evidence, and indicate repair directions only.

## Available Tools

- `Read`: read prose, setting documents, and memory data
- `Grep`: search prose for keywords
- `Bash`: query memory modules

```bash
# Query current character state
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" state get-entity --id "{entity_id}"

# Query recent state changes
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" index get-recent-state-changes --limit 20
```

## Reasoning Workflow (ReAct)

For each review dimension:
1. **Read** relevant data: character state, world rules, previous-chapter summary
2. **Compare** the prose against the data
3. **Determine** whether contradictions or problems exist
4. **Record** issues in the list, including evidence and fix_hint

## Inputs

- `chapter`: chapter number
- `chapter_file`: prose file path
- `project_root`: project root
- `scripts_dir`: scripts directory

## Review Dimensions (Run in Order)

### 1. Setting Consistency (category: setting)
- Do character abilities match their current realm?
- Do location descriptions match the world setting?
- Does item/currency use follow established rules?

### 2. Timeline (category: timeline)
- Does this chapter follow the previous chapter in time, with no unexplained regression?
- Do countdowns/deadlines advance correctly?
- Does a character appear in two places at once?

### 3. Narrative Continuity (category: continuity)
- Is the previous chapter’s hook addressed?
- Are scene changes bridged?
- Is the emotional arc continuous, rather than suddenly shifting from anger to calm without transition?

### 4. Character Consistency (category: character)
- Does dialogue match character traits?
- Does behavior match established personality/motivation?
- Character knowledge boundaries: does anyone use information they should not know?

### 5. Logic (category: logic)
- Are causal relationships valid?
- Are character decisions reasonably motivated?
- Do combat/conflict outcomes match established relative power?

### 6. AI-Like Writing (category: ai_flavor)
- Are there banned words/patterns such as “steadied his mind,” “could not help…,” or “the corners of his mouth rose slightly”?
- Does every paragraph follow cause → process → result → realization?
- Is there overexplaining instead of showing?
- Are emotions templated, such as “a trace of X flashed in their eyes”?

## Boundaries and Prohibitions

- **Do not score**: no overall_score or pass/fail output
- **Do not judge prose quality**: “not well written” is not an issue; “contradicts the character’s personality” is
- **Do not suggest plot changes**: “add a reversal here” is not an issue
- **Do not repeat the outline**: issues must not reveal plot that has not happened
- **Report verifiable problems only**: evidence must quote the text or compare data

## Checklist

Before finishing, verify:
- [ ] Every issue includes evidence
- [ ] No subjective impressions
- [ ] Severity is reasonable; critical is reserved for definite factual contradictions
- [ ] Categories are correct
- [ ] blocking is true only for critical issues or confirmed blockers

## Output Format

Output exactly the following JSON format, with no other text:

```json
{
  "issues": [
    {
      "severity": "critical | high | medium | low",
      "category": "continuity | setting | character | timeline | ai_flavor | logic | pacing | other",
      "location": "Paragraph N or specific quotation",
      "description": "Issue description",
      "evidence": "Quoted prose vs. recorded data",
      "fix_hint": "Suggested fix",
      "blocking": true
    }
  ],
  "summary": "N issues: X blocking, Y high-priority"
}
```

## Error Handling

- Cannot read character state → skip setting-consistency checks and note in summary: “Cannot validate setting consistency: data read failed”
- Cannot read the previous summary → skip the continuity item checking the previous chapter’s hook
- Empty prose → output one critical issue: “Prose is empty”
```

- [ ] **Step 2: Commit**

```bash
git add agents/reviewer.md
git commit -m "feat: unified reviewer.md agent replaces six checkers"
```

---

## Task 3: Delete the Workflow Module and Resume Skill

**Files:**
- Delete: `scripts/workflow_manager.py`
- Delete: `scripts/data_modules/tests/test_workflow_manager.py`
- Delete: `skills/webnovel-resume/SKILL.md`
- Delete: `skills/webnovel-resume/references/workflow-resume.md`
- Modify: `scripts/data_modules/webnovel.py`
- Modify: `scripts/data_modules/tests/test_coverage_boost.py`

- [ ] **Step 1: Remove Workflow Command Routing From webnovel.py**

Remove workflow parsers and routing from `scripts/data_modules/webnovel.py`:

Delete parser definitions:
```python
# Delete these two lines
p_workflow = sub.add_parser("workflow", help="转发到 workflow_manager.py")
p_workflow.add_argument("args", nargs=argparse.REMAINDER)
```

Delete the routing branch:
```python
# Delete these two lines
if tool == "workflow":
    raise SystemExit(_run_script("workflow_manager.py", [*forward_args, *rest]))
```

- [ ] **Step 2: Remove Workflow Tests From test_coverage_boost.py**

Delete `test_webnovel_passthrough_workflow_script`.

- [ ] **Step 3: Delete workflow_manager.py and Its Tests**

```bash
git rm scripts/workflow_manager.py
git rm scripts/data_modules/tests/test_workflow_manager.py
```

- [ ] **Step 4: Delete the Resume Skill**

```bash
git rm skills/webnovel-resume/SKILL.md
git rm skills/webnovel-resume/references/workflow-resume.md
rmdir skills/webnovel-resume/references 2>/dev/null || true
rmdir skills/webnovel-resume 2>/dev/null || true
```

- [ ] **Step 5: Run Tests to Confirm Nothing Broke**

Run: `cd "D:\wk\novel skill\webnovel-writer" && python -m pytest --no-cov --tb=short`
Expected: All pass; the total drops because ten test_workflow_manager.py tests were deleted

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: remove workflow_manager and resume skill in favor of Claude Code /resume"
```

---

## Task 4: Delete Six Legacy Checker Agents and the Old Schema

**Files:**
- Delete: `agents/consistency-checker.md`
- Delete: `agents/continuity-checker.md`
- Delete: `agents/ooc-checker.md`
- Delete: `agents/high-point-checker.md`
- Delete: `agents/pacing-checker.md`
- Delete: `agents/reader-pull-checker.md`
- Delete: `references/checker-output-schema.md`
- Delete: `skills/webnovel-write/references/step-3-review-gate.md`

- [ ] **Step 1: Delete Legacy Checker Agents**

```bash
git rm agents/consistency-checker.md
git rm agents/continuity-checker.md
git rm agents/ooc-checker.md
git rm agents/high-point-checker.md
git rm agents/pacing-checker.md
git rm agents/reader-pull-checker.md
```

- [ ] **Step 2: Delete the Old Schema and Review Gate**

```bash
git rm references/checker-output-schema.md
git rm skills/webnovel-write/references/step-3-review-gate.md
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove six legacy checker agents and old schema, replaced by reviewer.md"
```

---

## Task 5: Adapt review_pipeline.py to the New Schema

**Files:**
- Modify: `scripts/review_pipeline.py`
- Modify: `scripts/data_modules/tests/test_webnovel_unified_cli.py`

- [ ] **Step 1: Write Tests for the New review_pipeline Schema**

Update `test_review_pipeline_builds_artifacts` in `test_webnovel_unified_cli.py`, replacing multiple checker results with the new single-reviewer output:

```python
def test_review_pipeline_builds_artifacts_v6(tmp_path):
    _ensure_scripts_on_path()
    import review_pipeline as review_pipeline_module

    project_root = (tmp_path / "book").resolve()
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")

    review_results_path = tmp_path / "review_results.json"
    review_results_path.write_text(
        json.dumps(
            {
                "issues": [
                    {
                        "severity": "critical",
                        "category": "timeline",
                        "location": "第2段",
                        "description": "时间线回跳",
                        "evidence": "上章深夜，本章突然中午",
                        "fix_hint": "补时间过渡",
                        "blocking": True,
                    },
                    {
                        "severity": "medium",
                        "category": "ai_flavor",
                        "location": "第5段",
                        "description": "'稳住心神'出现2次",
                        "fix_hint": "替换为具体动作",
                    },
                ],
                "summary": "1个阻断，1个中等",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = review_pipeline_module.build_review_artifacts(
        project_root=project_root,
        chapter=20,
        review_results_path=review_results_path,
        report_file="",
    )

    assert payload["review_result"]["blocking_count"] == 1
    assert payload["review_result"]["has_blocking"] is True
    assert payload["review_result"]["issues_count"] == 2
    assert payload["metrics"]["issues_count"] == 2
    assert payload["metrics"]["blocking_count"] == 1
```

- [ ] **Step 2: Run Tests and Confirm Failure**

Run: `cd webnovel-writer/scripts && python -m pytest data_modules/tests/test_webnovel_unified_cli.py::test_review_pipeline_builds_artifacts_v6 -v --no-cov`
Expected: FAIL; review_pipeline still uses the old logic

- [ ] **Step 3: Rewrite review_pipeline.py**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3 review-result processing.

Read raw reviewer JSON, parse it as ReviewResult,
and generate metrics for persistence in index.db.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def _ensure_scripts_path() -> None:
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


_ensure_scripts_path()

from data_modules.review_schema import ReviewResult, parse_review_output


def build_review_artifacts(
    project_root: Path,
    chapter: int,
    review_results_path: Path,
    report_file: str = "",
) -> Dict[str, Any]:
    raw = json.loads(review_results_path.read_text(encoding="utf-8"))
    result = parse_review_output(chapter=chapter, raw=raw)
    metrics = result.to_metrics_dict()
    if report_file:
        metrics["report_file"] = report_file

    return {
        "chapter": chapter,
        "review_result": result.to_dict(),
        "metrics": metrics,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Review pipeline v6")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--review-results", required=True)
    parser.add_argument("--metrics-out", default="")
    parser.add_argument("--report-file", default="")

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

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run Tests and Confirm Success**

Run: `cd webnovel-writer/scripts && python -m pytest data_modules/tests/test_webnovel_unified_cli.py -v --no-cov`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add scripts/review_pipeline.py scripts/data_modules/tests/test_webnovel_unified_cli.py
git commit -m "refactor: adapt review_pipeline to v6: structured issues without scores"
```

---

## Task 6: Update webnovel-write SKILL.md (New Seven-Step Workflow)

**Files:**
- Modify: `skills/webnovel-write/SKILL.md`
- Delete: `skills/webnovel-write/references/step-5-debt-switch.md`
- Delete: `skills/webnovel-write/references/workflow-details.md`
- Delete: `skills/webnovel-write/references/step-1.5-contract.md`

- [ ] **Step 1: Delete Obsolete Reference Files**

```bash
git rm skills/webnovel-write/references/step-5-debt-switch.md
git rm skills/webnovel-write/references/workflow-details.md
git rm skills/webnovel-write/references/step-1.5-contract.md
```

- [ ] **Step 2: Rewrite SKILL.md**

Fully rewrite `skills/webnovel-write/SKILL.md` with these core changes:

1. **Reduce eight steps to seven:**
```
Step 0.5 preflight → Step 1 context collection → Step 2 drafting → Step 3 review → Step 4 polish + style + anti-AI → Step 5 data write-back → Step 6 Git
```

2. **Remove all workflow logging commands**, including `workflow start-step` / `complete-step` around each step

3. **Merge Step 2B into Step 4**: Step 4 handles polishing + style adaptation + anti-AI repair

4. **Use a single reviewer agent in Step 3:**
```
Use Task to call reviewer, not six independent checkers
Output: review_results.json (new schema)
Generate metrics through review_pipeline
Block when blocking issues exist
```

5. **Add anti-AI responsibilities to Step 4:**
```
- Consume Step 3 issues and repair each one
- Perform style adaptation, formerly Step 2B
- Final anti-AI gate: recheck after repairs and confirm no blockers remain
```

6. **Update mode definitions:**
```
Standard:Step 0.5 → 1 → 2 → 3 → 4 → 5 → 6
--fast：Step 0.5 → 1 → 2 → 3(lightweight) → 4 → 5 → 6
--minimal：Step 0.5 → 1 → 2 → 4(typesetting only) → 5 → 6
```

7. **Update references**: remove references to deleted files and add `review-schema.md`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor: webnovel-write v6: seven steps, one reviewer, integrated style adaptation"
```

---

## Task 7: Clean Up Legacy review_pipeline Tests and Run Full Regression

**Files:**
- Modify: `scripts/data_modules/tests/test_webnovel_unified_cli.py`

- [ ] **Step 1: Remove Incompatible Assertions From Legacy review_pipeline Tests**

Update `test_review_pipeline_builds_artifacts` and `test_review_pipeline_main_creates_output_directories` for the new schema. Old tests rely on removed fields such as `overall_score` and `timeline_gate`.

If Task 5 tests already cover this behavior, delete the old tests.

- [ ] **Step 2: Run Full Regression Tests**

Run: `cd "D:\wk\novel skill\webnovel-writer" && python -m pytest --tb=short`
Expected: All pass, coverage ≥ 90%

- [ ] **Step 3: Fix Any Failures and Commit**

```bash
git add -A
git commit -m "test: clean up legacy review tests; full regression passes"
```

---

## Task 8: Final Validation

- [ ] **Step 1: Verify Deletion Completeness**

```bash
# These files must not exist
test ! -f webnovel-writer/scripts/workflow_manager.py
test ! -f webnovel-writer/skills/webnovel-resume/SKILL.md
test ! -f webnovel-writer/agents/consistency-checker.md
test ! -f webnovel-writer/agents/continuity-checker.md
test ! -f webnovel-writer/agents/ooc-checker.md
test ! -f webnovel-writer/agents/high-point-checker.md
test ! -f webnovel-writer/agents/pacing-checker.md
test ! -f webnovel-writer/agents/reader-pull-checker.md
test ! -f webnovel-writer/references/checker-output-schema.md

# These files must exist
test -f webnovel-writer/agents/reviewer.md
test -f webnovel-writer/references/review-schema.md
test -f webnovel-writer/scripts/data_modules/review_schema.py
```

- [ ] **Step 2: Run All Tests + Coverage**

Run: `cd "D:\wk\novel skill\webnovel-writer" && python -m pytest`
Expected: All pass, coverage ≥ 90%

- [ ] **Step 3: Confirm Only Three Agents Remain in agents/**

```bash
ls webnovel-writer/agents/
# Expected:context-agent.md  data-agent.md  reviewer.md
```

- [ ] **Step 4: Final Commit (If Any Missing Fixes Remain)**

```bash
git add -A
git commit -m "chore: complete Phase 1; cleanup verification passes"
```
