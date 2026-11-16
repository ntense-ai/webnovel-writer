# v6 Migration Completion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the remaining v6 migration: remove legacy code, implement the chapter-status model, reconcile specification/implementation discrepancies, and verify exit criteria.

**Architecture:** Three workstreams: (A) legacy-code deletion and cleanup, (B) a new chapter-status model, and (C) specification/reference corrections. A and C are independent and may run in parallel; B is a new feature requiring separate development and tests.

**Tech Stack:** Python 3.13, pytest, SQLite (state.json + index.db), Claude Code plugin (markdown skills/agents)

**Spec:** `docs/superpowers/specs/2026-04-02-harness-v6-design.md` (v6)

**Prerequisites:** Phase 1 module creation is complete: reviewer.md, review_schema.py, and review_pipeline.py exist and pass tests. Phase 3 (memory_contract) and Phase 4 (context-agent research mode) are complete.

---

## Current Gap Summary

| Category | Remaining item | File |
|------|--------|------|
| Legacy checker functions | `_normalize_checker_issue`, `_build_timeline_gate`, `_aggregate_checker_results`, `ReviewAggregateResult` | `index_manager.py:208-232, 678-808` |
| Legacy checker CLI | `aggregate-review-results`, `materialize-review-metrics` | `index_manager.py:963-969, 1318-1327` |
| Legacy checker script | Entire 570-line file | `golden_three_checker.py` |
| Legacy checker tests | `test_aggregate_checker_results_cli` (L1428-1551), `test_aggregate_checker_results_blocks_...` (L1553-1596) | `test_data_modules.py` |
| Legacy checker tests | `test_index_aggregate_review_results_forwards_...` (L173) | `test_webnovel_unified_cli.py:173-218` |
| Legacy checker references | `continuity-checker` in the known-checker list | `test_prompt_integrity.py:247` |
| Workflow remnants | Comment references + test allowlist | `webnovel.py:94`, `test_prompt_integrity.py:221` |
| Step 2B remnants | Responsibility-boundary explanation | `polish-guide.md:13-17` |
| Legacy references | `continuity-checker` mapping table | `reading-power-taxonomy.md:343-348` |
| Legacy consumption | `overall_score` used for low-score alerts | `context_manager.py:310-318` |
| Missing functionality | Chapter-status model | None (must be added to `state_manager.py`) |
| Specification discrepancy | Claims v0 is unimplemented, although it is implemented | spec 4.5 |

---

## File Structure

### Files to Delete

| File | Reason |
|------|------|
| `scripts/golden_three_checker.py` | Legacy checker model, 570 lines, superseded by reviewer |

### Files to Modify

| File | Change |
|------|--------|
| `scripts/data_modules/index_manager.py` | Remove `ReviewAggregateResult`, legacy checker functions, and legacy CLI commands |
| `scripts/data_modules/context_manager.py` | Replace `overall_score` low-score checks with severity_counts |
| `scripts/data_modules/tests/test_data_modules.py` | Delete legacy checker aggregation tests (~170 lines) |
| `scripts/data_modules/tests/test_webnovel_unified_cli.py` | Delete legacy aggregate-review-results forwarding tests |
| `scripts/data_modules/tests/test_prompt_integrity.py` | Clean up checker and workflow_manager allowlists |
| `scripts/data_modules/webnovel.py` | Clean up workflow_manager comments |
| `scripts/data_modules/state_manager.py` | Add chapter_status management |
| `skills/webnovel-write/references/polish-guide.md` | Remove the Step 2B boundary section |
| `references/reading-power-taxonomy.md` | Update the checker mapping table |
| `docs/superpowers/specs/2026-04-02-harness-v6-design.md` | Correct Specification/Implementation Discrepancies |

### Files to Create

| File | Responsibility |
|------|------|
| `scripts/data_modules/tests/test_chapter_status.py` | Chapter-status model tests |

---

## Task 1: Remove Legacy Checker Aggregation Functions and CLI

**Files:**
- Modify: `scripts/data_modules/index_manager.py`
- Modify: `scripts/data_modules/tests/test_data_modules.py`
- Modify: `scripts/data_modules/tests/test_webnovel_unified_cli.py`

- [ ] **Step 1: Remove the ReviewAggregateResult Dataclass From index_manager.py**

Delete the `ReviewAggregateResult` dataclass and its `to_review_metrics` method at index_manager.py lines 208–232. Retain `ReviewMetrics`, which is still used by the `save-review-metrics` CLI.

```python
# Remove this block (approximately 25 lines):
@dataclass
class ReviewAggregateResult:
    """Step 3 aggregated review results"""
    chapter: int
    start_chapter: int
    end_chapter: int
    selected_checkers: List[str] = field(default_factory=list)
    checkers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    overall_score: float = 0.0
    severity_counts: Dict[str, int] = field(default_factory=dict)
    timeline_gate: Dict[str, Any] = field(default_factory=dict)
    # ... and all its methods
```

- [ ] **Step 2: Remove Legacy Checker Functions From index_manager.py**

Delete these three functions (lines 678–808):

```python
# Delete these three functions:
def _normalize_checker_issue(issue: object) -> dict: ...
def _build_timeline_gate(issues: ...) -> Dict[str, Any]: ...
def _aggregate_checker_results(chapter: int, raw_data: object) -> dict: ...
```

- [ ] **Step 3: Remove Legacy CLI Command Registration From index_manager.py**

Delete parser registration for `aggregate-review-results` and `materialize-review-metrics` (lines 963–969):

```python
# Delete:
review_aggregate_parser = subparsers.add_parser("aggregate-review-results")
review_aggregate_parser.add_argument("--chapter", ...)
review_aggregate_parser.add_argument("--data", ...)

review_materialize_parser = subparsers.add_parser("materialize-review-metrics")
review_materialize_parser.add_argument("--chapter", ...)
review_materialize_parser.add_argument("--data", ...)
```

Delete the corresponding CLI handler branches (lines 1318–1327):

```python
# Delete:
elif args.command == "aggregate-review-results":
    ...
elif args.command == "materialize-review-metrics":
    ...
```

- [ ] **Step 4: Delete Legacy Checker Tests**

Delete these tests from `test_data_modules.py` (lines 1428–1596, approximately 170 lines):

```python
# Delete these two test functions:
def test_aggregate_checker_results_cli(temp_project, monkeypatch, capsys): ...
def test_aggregate_checker_results_blocks_overall_pass_for_high_timeline_issue(temp_project, monkeypatch, capsys): ...
```

Delete the legacy aggregate forwarding test from `test_webnovel_unified_cli.py` (lines 173–218):

```python
# Delete:
def test_index_aggregate_review_results_forwards_with_resolved_project_root(monkeypatch, tmp_path): ...
```

- [ ] **Step 5: Run Tests to Confirm Nothing Broke**

Run: `cd "D:/wk/novel skill/webnovel-writer" && python -m pytest webnovel-writer/scripts -x --tb=short --no-cov`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/scripts/data_modules/index_manager.py webnovel-writer/scripts/data_modules/tests/test_data_modules.py webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py
git commit -m "$(cat <<'EOF'
refactor: remove legacy checker aggregation functions and CLI

Remove ReviewAggregateResult, _aggregate_checker_results,
_build_timeline_gate, _normalize_checker_issue, and corresponding CLI
commands and tests. reviewer + review_pipeline fully supersede them.
EOF
)"
```

---

## Task 2: Delete golden_three_checker.py

**Files:**
- Delete: `scripts/golden_three_checker.py`

- [ ] **Step 1: Confirm No Runtime Dependencies**

Run: `cd "D:/wk/novel skill/webnovel-writer" && grep -r "golden_three" webnovel-writer/ --include="*.py" --include="*.md" | grep -v golden_three_checker.py`
Expected: No matches, except possibly in the test_prompt_integrity allowlist

- [ ] **Step 2: Delete the File**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git rm webnovel-writer/scripts/golden_three_checker.py
```

- [ ] **Step 3: Run Tests**

Run: `cd "D:/wk/novel skill/webnovel-writer" && python -m pytest webnovel-writer/scripts -x --tb=short --no-cov`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor: Delete golden_three_checker.py (570 lines), superseded by reviewer"
```

---

## Task 3: Clean Up Scattered Legacy References

**Files:**
- Modify: `scripts/data_modules/webnovel.py`
- Modify: `scripts/data_modules/tests/test_prompt_integrity.py`
- Modify: `skills/webnovel-write/references/polish-guide.md`
- Modify: `references/reading-power-taxonomy.md`

- [ ] **Step 1: Clean Up workflow_manager Comments in webnovel.py**

Update `webnovel.py:94` to stop mentioning workflow_manager:

```python
# Old:
#     Purpose: support scripts without main(), such as workflow_manager.py.
# New:
#     Purpose: support scripts without main().
```

- [ ] **Step 2: Clean Up test_prompt_integrity.py**

Add `golden_three_checker.py` to `KNOWN_DELETED_FILES` (lines 215–223) if necessary, and remove legacy names such as `continuity-checker` from any checker allowlists (line 247).

Check the context of the line 247 `continuity-checker` reference. Retain it if it checks that the name must not appear in prompts; remove it if it permits the name.

- [ ] **Step 3: Clean Up the Step 2B Section in polish-guide.md**

Delete the Step 2B responsibility-boundary explanation in `polish-guide.md:13-17`:

```markdown
# Delete the following:
Responsibility boundary with Step 2B:
- Step 2B: style transformation (expression layer)
- Step 4: issue repair (quality layer), including review fixes, final Anti-AI checks, and reader-turn-off avoidance

If Step 2B has run, do not repeat a full sentence rewrite; make only necessary changes.
```

Replace with:

```markdown
Responsibilities:
- Step 4 handles both style adaptation (removing templated, explanatory, and mechanical tone) and issue repair
- Include review fixes, final Anti-AI checks, and reader-turn-off avoidance
```

- [ ] **Step 4: Clean Up the Checker Mapping Table in reading-power-taxonomy.md**

Update the legacy checker mapping table in `reading-power-taxonomy.md:343-349`:

```markdown
# Old:
| Existing Checker | Taxonomy Used |
|--------------|----------------|
| `reader-pull-checker` | Hook type, hook strength, Hard-002 |
| `high-point-checker` | Payoff patterns, micro-payoffs |
| `pacing-checker` | Hard-003 (Pacing disaster) |
| `continuity-checker` | Hard-001 (Readability floor) |

# New:
| Review Dimension (reviewer) | Taxonomy Used |
|---------------------|----------------|
| continuity | Hard-001 (Readability floor)、Hard-002 (Structural completeness) |
| pacing | Hard-003 (Pacing disaster)、Payoff patterns, micro-payoffs |
| ai_flavor | Hook type, hook strength |
```

- [ ] **Step 5: Run Tests**

Run: `cd "D:/wk/novel skill/webnovel-writer" && python -m pytest webnovel-writer/scripts -x --tb=short --no-cov`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/scripts/data_modules/webnovel.py webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py webnovel-writer/skills/webnovel-write/references/polish-guide.md webnovel-writer/references/reading-power-taxonomy.md
git commit -m "$(cat <<'EOF'
refactor: clean up legacy references: workflow_manager comments, Step 2B boundaries, old checker mappings
EOF
)"
```

---

## Task 4: Migrate overall_score Consumption in context_manager.py

**Files:**
- Modify: `scripts/data_modules/context_manager.py`

- [ ] **Step 1: Inspect overall_score Consumers**

`context_manager.py:310-318` uses `overall_score < 75` for low-score alerts. Change this to use `severity_counts` or `notes`:

```python
# Old logic (lines 310–318):
for row in review_trend.get("recent_ranges", []):
    score = row.get("overall_score")
    if isinstance(score, (int, float)) and float(score) < 75:
        low_score_ranges.append({
            "start_chapter": row.get("start_chapter"),
            "end_chapter": row.get("end_chapter"),
            "overall_score": score,
        })

# New logic:
for row in review_trend.get("recent_ranges", []):
    score = row.get("overall_score")
    notes = row.get("notes", "")
    has_issues = "blocking=" in notes and "blocking=0" not in notes
    is_low_score = isinstance(score, (int, float)) and float(score) < 75
    if is_low_score or has_issues:
        low_score_ranges.append({
            "start_chapter": row.get("start_chapter"),
            "end_chapter": row.get("end_chapter"),
            "overall_score": score if isinstance(score, (int, float)) else 0.0,
            "notes": notes,
        })
```

- [ ] **Step 2: Run Related Tests**

Run: `cd "D:/wk/novel skill/webnovel-writer" && python -m pytest webnovel-writer/scripts/data_modules/tests/test_context_manager.py -x --tb=short --no-cov`
Expected: Pass

- [ ] **Step 3: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/scripts/data_modules/context_manager.py
git commit -m "refactor: adapt context_manager low-score alerts to v6 severity_counts"
```

---

## Task 5: Implement the Chapter-Status Model

**Files:**
- Modify: `scripts/data_modules/state_manager.py`
- Create: `scripts/data_modules/tests/test_chapter_status.py`

- [ ] **Step 1: Write Tests**

```python
# scripts/data_modules/tests/test_chapter_status.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chapter-status model tests"""
import json
import pytest
from pathlib import Path


@pytest.fixture
def state_project(tmp_path):
    webnovel_dir = tmp_path / ".webnovel"
    webnovel_dir.mkdir()
    state_file = webnovel_dir / "state.json"
    state_file.write_text(json.dumps({
        "progress": {"current_chapter": 5}
    }), encoding="utf-8")
    return tmp_path


def _make_manager(project_root):
    import sys
    scripts_dir = str(Path(__file__).resolve().parent.parent.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from data_modules.config import DataModulesConfig
    from data_modules.state_manager import StateManager
    config = DataModulesConfig(
        project_root=project_root,
        webnovel_dir=project_root / ".webnovel",
    )
    return StateManager(config)


def test_get_chapter_status_default(state_project):
    sm = _make_manager(state_project)
    sm._load_state()
    status = sm.get_chapter_status(5)
    assert status is None  # not previously set


def test_set_chapter_status_drafted(state_project):
    sm = _make_manager(state_project)
    sm._load_state()
    sm.set_chapter_status(5, "chapter_drafted")
    status = sm.get_chapter_status(5)
    assert status == "chapter_drafted"


def test_set_chapter_status_monotonic(state_project):
    sm = _make_manager(state_project)
    sm._load_state()
    sm.set_chapter_status(5, "chapter_reviewed")
    # must not regress to drafted
    with pytest.raises(ValueError, match="不可回退"):
        sm.set_chapter_status(5, "chapter_drafted")


def test_set_chapter_status_progression(state_project):
    sm = _make_manager(state_project)
    sm._load_state()
    sm.set_chapter_status(5, "chapter_drafted")
    sm.set_chapter_status(5, "chapter_reviewed")
    sm.set_chapter_status(5, "chapter_committed")
    assert sm.get_chapter_status(5) == "chapter_committed"


def test_chapter_status_persists(state_project):
    sm = _make_manager(state_project)
    sm._load_state()
    sm.set_chapter_status(3, "chapter_drafted")
    sm._save_state()

    # reload
    sm2 = _make_manager(state_project)
    sm2._load_state()
    assert sm2.get_chapter_status(3) == "chapter_drafted"
```

- [ ] **Step 2: Run Tests and Confirm Failure**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest data_modules/tests/test_chapter_status.py -v --no-cov`
Expected: FAIL — `AttributeError: 'StateManager' object has no attribute 'get_chapter_status'`

- [ ] **Step 3: Implement chapter_status in state_manager.py**

Add these methods to `StateManager`:

```python
CHAPTER_STATUS_ORDER = ["chapter_drafted", "chapter_reviewed", "chapter_committed"]

def get_chapter_status(self, chapter: int) -> Optional[str]:
    """Query chapter status."""
    statuses = self._state.get("progress", {}).get("chapter_status", {})
    return statuses.get(str(chapter))

def set_chapter_status(self, chapter: int, status: str) -> None:
    """Set chapter status (monotonic progression; no regression)."""
    if status not in self.CHAPTER_STATUS_ORDER:
        raise ValueError(f"无效状态: {status}，有效值: {self.CHAPTER_STATUS_ORDER}")

    current = self.get_chapter_status(chapter)
    if current is not None:
        current_idx = self.CHAPTER_STATUS_ORDER.index(current)
        new_idx = self.CHAPTER_STATUS_ORDER.index(status)
        if new_idx < current_idx:
            raise ValueError(
                f"章节 {chapter} 状态不可回退: {current} -> {status}"
            )
        if new_idx == current_idx:
            return  # idempotent

    progress = self._state.setdefault("progress", {})
    chapter_status = progress.setdefault("chapter_status", {})
    chapter_status[str(chapter)] = status
    self._save_state()
```

- [ ] **Step 4: Run Tests and Confirm Success**

Run: `cd "D:/wk/novel skill/webnovel-writer/webnovel-writer/scripts" && python -m pytest data_modules/tests/test_chapter_status.py -v --no-cov`
Expected: 5 passed

- [ ] **Step 5: Add CLI Subcommands**

Add `get-chapter-status` and `set-chapter-status` subcommands to the CLI section of `state_manager.py`:

```python
# Parser registration
status_get_parser = subparsers.add_parser("get-chapter-status")
status_get_parser.add_argument("--chapter", type=int, required=True)

status_set_parser = subparsers.add_parser("set-chapter-status")
status_set_parser.add_argument("--chapter", type=int, required=True)
status_set_parser.add_argument("--status", required=True,
    choices=["chapter_drafted", "chapter_reviewed", "chapter_committed"])
```

```python
# Command handling
elif args.command == "get-chapter-status":
    manager._load_state()
    status = manager.get_chapter_status(args.chapter)
    emit_success({"chapter": args.chapter, "status": status},
                 message="chapter_status")

elif args.command == "set-chapter-status":
    manager._load_state()
    manager.set_chapter_status(args.chapter, args.status)
    emit_success({"chapter": args.chapter, "status": args.status},
                 message="chapter_status_set")
```

- [ ] **Step 6: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add webnovel-writer/scripts/data_modules/state_manager.py webnovel-writer/scripts/data_modules/tests/test_chapter_status.py
git commit -m "$(cat <<'EOF'
feat: chapter-status model: chapter_drafted/reviewed/committed

Monotonically advancing state machine with CLI query/set support.
Used for sufficiency gates in the v6 Write workflow.
EOF
)"
```

---

## Task 6: Correct Specification/Implementation Discrepancies

**Files:**
- Modify: `docs/superpowers/specs/2026-04-02-harness-v6-design.md`

- [ ] **Step 1: Correct the Memory Contract v0 Description**

In section 4.5, change:

```
**v0 (target interface for Phase 1/2A prompt refactoring):**

> Note: v0 is not yet implemented. Existing `webnovel.py` CLI subcommands such as `state get-entity` and `index get-recent-state-changes` currently fill this role. Phase 3 will consolidate them into the unified contract below.
```

To:

```
**v0 (implemented and currently frozen):**

> v0 is implemented through `memory_contract.py` (Protocol + types) and `memory_contract_adapter.py` (adapter). Its CLI entry point is `webnovel.py memory-contract`, already used by context-agent.
```

- [ ] **Step 2: Update Phase Table Status**

Mark Phase 3 and Phase 4 as complete in the implementation roadmap table:

```markdown
| Phase 3 | Memory-module interface contract design | None | **✅ Complete** |
| Phase 4 | Context-agent research-mode refactor | Phase 3 (contract) | **✅ Complete** |
```

- [ ] **Step 3: Update Version Number**

```
> Status: Draft v7 (v6 + implementation-alignment corrections)
```

- [ ] **Step 4: Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add docs/superpowers/specs/2026-04-02-harness-v6-design.md
git commit -m "docs: spec v7: correct memory contract status and mark Phase 3/4 complete"
```

---

## Task 7: Full Regression Validation + Exit Criteria Checks

**Files:** No new files

- [ ] **Step 1: Run All Tests**

Run: `cd "D:/wk/novel skill/webnovel-writer" && python -m pytest webnovel-writer/scripts --tb=short`
Expected: All pass

- [ ] **Step 2: Verify Each Exit Criterion**

```bash
cd "D:/wk/novel skill/webnovel-writer"

# Criterion 1: no legacy checker runtime references
echo "--- Criterion 1: legacy checker references ---"
grep -rn "continuity-checker\|setting-checker\|ooc-checker\|high-point-checker\|pacing-checker\|reader-pull-checker" \
  webnovel-writer/skills/ webnovel-writer/agents/ webnovel-writer/scripts/*.py \
  --include="*.md" --include="*.py" || echo "PASS: no legacy checker references"

# Criterion 2: a single review path
echo "--- Criterion 2: review path ---"
grep -l "reviewer" webnovel-writer/skills/webnovel-write/SKILL.md webnovel-writer/skills/webnovel-review/SKILL.md && echo "PASS: both use reviewer"

# Criterion 3: workflow_manager removed
echo "--- Criterion 3: workflow_manager ---"
test ! -f webnovel-writer/scripts/workflow_manager.py && echo "PASS: file deleted" || echo "FAIL: file still exists"

# Criterion 4: legacy terminology (runtime paths)
echo "--- Criterion 4: legacy terminology ---"
grep -rn "timeline_gate\|_aggregate_checker\|_normalize_checker\|_build_timeline_gate" \
  webnovel-writer/scripts/ --include="*.py" | grep -v "test_" | grep -v "__pycache__" || echo "PASS: no legacy runtime references"

# Criterion 6: chapter-status model
echo "--- Criterion 6: chapter-status CLI ---"
cd webnovel-writer/scripts && python -X utf8 data_modules/state_manager.py --help 2>&1 | grep -q "get-chapter-status" && echo "PASS: CLI registered" || echo "FAIL: CLI not registered"
```

- [ ] **Step 3: Fix Any Failures and Commit**

```bash
cd "D:/wk/novel skill/webnovel-writer"
git add -A
git commit -m "chore: verify v6 migration exit criteria"
```
