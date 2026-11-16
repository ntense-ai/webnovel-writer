# Story System Phase 3 Chapter Commit Chain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the `CHAPTER_COMMIT` mainline, accepted / rejected semantics, and four projection writers so all post-writing chapter facts pass through a commit object instead of scattered writes to `state / index / summary / memory`.

**Architecture:** Build on Phase 2 contract-first runtime by introducing `CHAPTER_COMMIT.json` as the sole post-writing factual entry point. Submission first aggregates `review_result / fulfillment_result / disambiguation_result / accepted_events / deltas`; projection writers may distribute to downstream storage only when the commit is accepted. This phase repositions `state_manager / memory writer / index_manager` as projection-writing foundations rather than chapter sources of truth.

**Tech Stack:** Python 3.13, Pydantic, argparse, pytest, SQLite (`index.db`), JSON commit artifacts under `.story-system/commits`

**Spec:** `docs/superpowers/specs/2026-04-12-story-system-evolution-spec.md`

**Companion Plans:** `docs/superpowers/plans/2026-04-12-story-system-phase1-contract-seed.md`, `docs/superpowers/plans/2026-04-12-story-system-phase2-contract-first-runtime.md`

---

## Scope Split

This plan covers only Phase 3:

1. `CHAPTER_COMMIT`
2. Four projection writers
3. Accepted / rejected commit semantics
4. Commit-driven post-writing persistence

Explicit non-goals:

- Do not introduce the global canonical event-log mainline
- Do not expand the override ledger into a complete audit ledger
- Do not complete legacy-pipeline downgrades

Exit criteria:

1. `PROJECT_ROOT/.story-system/commits/chapter_XXX.commit.json` becomes the post-writing factual entry point
2. Rejected commits do not write to downstream storage
3. Only accepted commits trigger `state / index / summary / memory` projections; `StateProjectionWriter` must actually update `state.json`
4. `projection_status` tracks each writer’s completion. Write failures are recorded only in that writer’s status and do not reverse the accepted/rejected commit decision

Append documentation updates to existing `Story System` sections without restructuring the README.

---

## File Structure

### Files to Create

- `webnovel-writer/scripts/chapter_commit.py`
- `webnovel-writer/scripts/data_modules/story_commit_schema.py`
- `webnovel-writer/scripts/data_modules/chapter_commit_service.py`
- `webnovel-writer/scripts/data_modules/state_projection_writer.py`
- `webnovel-writer/scripts/data_modules/index_projection_writer.py`
- `webnovel-writer/scripts/data_modules/summary_projection_writer.py`
- `webnovel-writer/scripts/data_modules/memory_projection_writer.py`
- `webnovel-writer/scripts/data_modules/tests/test_story_commit_schema.py`
- `webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py`
- `webnovel-writer/scripts/data_modules/tests/test_projection_writers.py`
- `docs/architecture/story-system-phase3.md`

### Files to Modify

- `webnovel-writer/scripts/data_modules/story_contracts.py`
- `webnovel-writer/scripts/data_modules/webnovel.py`
- `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`
- `webnovel-writer/scripts/review_pipeline.py`
- `webnovel-writer/scripts/data_modules/state_manager.py`
- `webnovel-writer/scripts/data_modules/memory/writer.py`
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`
- `README.md`
- `docs/architecture/overview.md`
- `docs/guides/commands.md`
- `docs/superpowers/README.md`

---

## Task 1: Define the `CHAPTER_COMMIT` Schema and Persistence Path

**Files:**
- Create: `webnovel-writer/scripts/data_modules/story_commit_schema.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_story_commit_schema.py`
- Modify: `webnovel-writer/scripts/data_modules/story_contracts.py`

- [ ] **Step 1: Write schema tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_story_commit_schema.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from data_modules.story_commit_schema import ChapterCommit


def test_chapter_commit_accepts_required_sections():
    payload = {
        "meta": {"schema_version": "story-system/v1", "chapter": 3, "status": "accepted"},
        "contract_refs": {"master": "MASTER_SETTING.json", "chapter": "chapter_003.json"},
        "outline_snapshot": {"planned_nodes": ["discover the trap"]},
        "review_result": {"blocking_count": 0},
        "fulfillment_result": {"missed_nodes": []},
        "disambiguation_result": {"pending": []},
        "accepted_events": [],
        "state_deltas": [],
        "entity_deltas": [],
        "projection_status": {"state": "pending", "index": "pending", "summary": "pending", "memory": "pending"},
    }
    model = ChapterCommit.model_validate(payload)
    assert model.meta["status"] == "accepted"
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_commit_schema.py -q --no-cov`

Expected: `ModuleNotFoundError: No module named 'data_modules.story_commit_schema'`

- [ ] **Step 3: Implement the schema and commit paths**

```python
# webnovel-writer/scripts/data_modules/story_commit_schema.py
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ChapterCommit(BaseModel):
    meta: Dict[str, Any]
    contract_refs: Dict[str, str]
    outline_snapshot: Dict[str, Any]
    review_result: Dict[str, Any]
    fulfillment_result: Dict[str, Any]
    disambiguation_result: Dict[str, Any]
    accepted_events: List[Dict[str, Any]] = Field(default_factory=list)
    state_deltas: List[Dict[str, Any]] = Field(default_factory=list)
    entity_deltas: List[Dict[str, Any]] = Field(default_factory=list)
    projection_status: Dict[str, str]
```

```python
# webnovel-writer/scripts/data_modules/story_contracts.py
@property
def commits_dir(self) -> Path:
    return self.root / "commits"

def commit_json(self, chapter: int) -> Path:
    return self.commits_dir / f"chapter_{chapter:03d}.commit.json"
```

- [ ] **Step 4: Rerun tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_commit_schema.py -q --no-cov`

Expected: Pass

- [ ] **Step 5: Commit**

```bash
git add webnovel-writer/scripts/data_modules/story_commit_schema.py \
        webnovel-writer/scripts/data_modules/story_contracts.py \
        webnovel-writer/scripts/data_modules/tests/test_story_commit_schema.py
git commit -m "feat: add chapter commit schema and paths"
```

---

## Task 2: Implement `chapter_commit_service` and Commit Validation

**Files:**
- Create: `webnovel-writer/scripts/data_modules/chapter_commit_service.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py`
- Modify: `webnovel-writer/scripts/review_pipeline.py`

- [ ] **Step 1: Write accepted/blocked commit tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from data_modules.chapter_commit_service import ChapterCommitService


def test_commit_service_rejects_when_missed_nodes_exist(tmp_path):
    service = ChapterCommitService(tmp_path)
    payload = service.build_commit(
        chapter=3,
        review_result={"blocking_count": 0},
        fulfillment_result={"planned_nodes": ["discover the trap"], "missed_nodes": ["discover the trap"]},
        disambiguation_result={"pending": []},
        extraction_result={"state_deltas": [], "entity_deltas": [], "accepted_events": []},
    )
    assert payload["meta"]["status"] == "rejected"


def test_commit_service_accepts_when_all_checks_pass(tmp_path):
    service = ChapterCommitService(tmp_path)
    payload = service.build_commit(
        chapter=3,
        review_result={"blocking_count": 0},
        fulfillment_result={"planned_nodes": ["discover the trap"], "covered_nodes": ["discover the trap"], "missed_nodes": [], "extra_nodes": []},
        disambiguation_result={"pending": []},
        extraction_result={"state_deltas": [], "entity_deltas": [], "accepted_events": []},
    )
    assert payload["meta"]["status"] == "accepted"
    assert payload["contract_refs"]["master"] == "MASTER_SETTING.json"
    assert payload["contract_refs"]["chapter"] == "chapter_003.json"
    assert payload["outline_snapshot"]["covered_nodes"] == ["discover the trap"]
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py -q --no-cov`

Expected: `ModuleNotFoundError: No module named 'data_modules.chapter_commit_service'`

- [ ] **Step 3: Implement the commit service**

```python
# webnovel-writer/scripts/data_modules/chapter_commit_service.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from data_modules.index_projection_writer import IndexProjectionWriter
from data_modules.memory_projection_writer import MemoryProjectionWriter
from data_modules.state_projection_writer import StateProjectionWriter
from data_modules.summary_projection_writer import SummaryProjectionWriter


class ChapterCommitService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def build_commit(
        self,
        chapter: int,
        review_result: Dict[str, Any],
        fulfillment_result: Dict[str, Any],
        disambiguation_result: Dict[str, Any],
        extraction_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        rejected = bool(review_result.get("blocking_count")) or bool(fulfillment_result.get("missed_nodes")) or bool(disambiguation_result.get("pending"))
        status = "rejected" if rejected else "accepted"
        return {
            "meta": {"schema_version": "story-system/v1", "chapter": chapter, "status": status},
            "contract_refs": {
                "master": "MASTER_SETTING.json",
                "chapter": f"chapter_{chapter:03d}.json",
                "review": f"chapter_{chapter:03d}.review.json",
            },
            "outline_snapshot": {
                "planned_nodes": fulfillment_result.get("planned_nodes", []),
                "covered_nodes": fulfillment_result.get("covered_nodes", []),
                "missed_nodes": fulfillment_result.get("missed_nodes", []),
                "extra_nodes": fulfillment_result.get("extra_nodes", []),
            },
            "review_result": review_result,
            "fulfillment_result": fulfillment_result,
            "disambiguation_result": disambiguation_result,
            "accepted_events": extraction_result.get("accepted_events", []),
            "state_deltas": extraction_result.get("state_deltas", []),
            "entity_deltas": extraction_result.get("entity_deltas", []),
            "projection_status": {"state": "pending", "index": "pending", "summary": "pending", "memory": "pending"},
        }

    def persist_commit(self, payload: Dict[str, Any]) -> Path:
        target = self.project_root / ".story-system" / "commits"
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"chapter_{int(payload['meta']['chapter']):03d}.commit.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def apply_projections(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if payload["meta"]["status"] != "accepted":
            return payload

        writers = {
            "state": StateProjectionWriter(self.project_root),
            "index": IndexProjectionWriter(self.project_root),
            "summary": SummaryProjectionWriter(self.project_root),
            "memory": MemoryProjectionWriter(self.project_root),
        }
        for name, writer in writers.items():
            try:
                result = writer.apply(payload)
                payload["projection_status"][name] = "done" if result.get("applied") else "skipped"
            except Exception as exc:
                payload["projection_status"][name] = f"failed:{exc}"
        self.persist_commit(payload)
        return payload
```

Add the following Phase 3 / Phase 4 responsibility agreement, which subsequent implementation must follow:

- `ChapterCommitService.apply_projections()` remains the sole orchestration entry point
- The Phase 4 `EventProjectionRouter` only decides which writers should be activated
- `EventProjectionRouter` **does not run another independent projection pass**, avoiding duplicate persistence of `state_deltas` and `accepted_events`

This task must explicitly wire `review_pipeline.py` as follows:

- Aggregate `review_result / fulfillment_result / disambiguation_result / extraction_result`
- Call `ChapterCommitService.build_commit()`
- Call `persist_commit()` first, then use `payload["meta"]["status"]` to decide whether to enter projection

Thus `review_pipeline.py` is not merely listed among modified files; it is the actual invocation entry point for the Phase 3 post-writing mainline.

- [ ] **Step 4: Rerun tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py -q --no-cov`

Expected: Pass

- [ ] **Step 5: Commit**

```bash
git add webnovel-writer/scripts/data_modules/chapter_commit_service.py \
        webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py \
        webnovel-writer/scripts/review_pipeline.py
git commit -m "feat: add chapter commit service and status semantics"
```

---

## Task 3: Implement Four Projection Writers

**Files:**
- Create: `webnovel-writer/scripts/data_modules/state_projection_writer.py`
- Create: `webnovel-writer/scripts/data_modules/index_projection_writer.py`
- Create: `webnovel-writer/scripts/data_modules/summary_projection_writer.py`
- Create: `webnovel-writer/scripts/data_modules/memory_projection_writer.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_projection_writers.py`
- Modify: `webnovel-writer/scripts/data_modules/index_manager.py`
- Modify: `webnovel-writer/scripts/data_modules/state_manager.py`
- Modify: `webnovel-writer/scripts/data_modules/memory/writer.py`

- [ ] **Step 1: Write accepted / rejected projection tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_projection_writers.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from data_modules.chapter_commit_service import ChapterCommitService
from data_modules.state_projection_writer import StateProjectionWriter


def test_state_projection_writer_skips_rejected_commit(tmp_path):
    writer = StateProjectionWriter(tmp_path)
    result = writer.apply({"meta": {"status": "rejected"}, "state_deltas": []})
    assert result["applied"] is False


def test_state_projection_writer_applies_accepted_commit(tmp_path):
    (tmp_path / ".webnovel").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")
    writer = StateProjectionWriter(tmp_path)
    result = writer.apply({"meta": {"status": "accepted"}, "state_deltas": [{"entity_id": "x", "field": "realm", "new": "Dou Zhe"}]})
    assert result["applied"] is True
    payload = json.loads((tmp_path / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    assert payload["entity_state"]["x"]["realm"] == "Dou Zhe"


def test_accepted_commit_updates_state_json_end_to_end(tmp_path):
    (tmp_path / ".webnovel").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")

    service = ChapterCommitService(tmp_path)
    commit_payload = service.build_commit(
        chapter=3,
        review_result={"blocking_count": 0},
        fulfillment_result={"planned_nodes": ["discover the trap"], "covered_nodes": ["discover the trap"], "missed_nodes": [], "extra_nodes": []},
        disambiguation_result={"pending": []},
        extraction_result={"state_deltas": [{"entity_id": "x", "field": "realm", "new": "Dou Zhe"}], "entity_deltas": [], "accepted_events": []},
    )

    StateProjectionWriter(tmp_path).apply(commit_payload)
    payload = json.loads((tmp_path / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    assert payload["entity_state"]["x"]["realm"] == "Dou Zhe"
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_projection_writers.py -q --no-cov`

Expected: `ModuleNotFoundError` for projection writer modules

- [ ] **Step 3: Implement the four writers**

```python
# webnovel-writer/scripts/data_modules/state_projection_writer.py
from data_modules.story_contracts import read_json_if_exists


class StateProjectionWriter:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def apply(self, commit_payload: dict) -> dict:
        if commit_payload["meta"]["status"] != "accepted":
            return {"applied": False, "writer": "state", "reason": "commit_rejected"}

        state_path = self.project_root / ".webnovel" / "state.json"
        state = read_json_if_exists(state_path) or {}
        entity_state = state.setdefault("entity_state", {})
        applied_count = 0
        for delta in commit_payload.get("state_deltas", []):
            entity_id = str(delta.get("entity_id") or "").strip()
            field = str(delta.get("field") or "").strip()
            if not entity_id or not field:
                continue
            entity_state.setdefault(entity_id, {})[field] = delta.get("new")
            applied_count += 1

        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"applied": applied_count > 0, "writer": "state", "applied_count": applied_count}
```

The other three writers may initially provide minimal projections in Phase 3, but **must not be no-op stubs**. At minimum, adapt them thinly to the existing foundations:

```python
class IndexProjectionWriter:
    def apply(self, commit_payload: dict) -> dict:
        if commit_payload["meta"]["status"] != "accepted":
            return {"applied": False, "writer": "index", "reason": "commit_rejected"}
        manager = IndexManager(self.project_root)
        for delta in commit_payload.get("entity_deltas", []):
            manager.apply_entity_delta(delta)
        return {"applied": True, "writer": "index", "applied_count": len(commit_payload.get("entity_deltas", []))}


class SummaryProjectionWriter:
    def apply(self, commit_payload: dict) -> dict:
        if commit_payload["meta"]["status"] != "accepted":
            return {"applied": False, "writer": "summary", "reason": "commit_rejected"}
        return append_summary_projection(self.project_root, commit_payload)


class MemoryProjectionWriter:
    def apply(self, commit_payload: dict) -> dict:
        if commit_payload["meta"]["status"] != "accepted":
            return {"applied": False, "writer": "memory", "reason": "commit_rejected"}
        return MemoryWriter(self.project_root).apply_commit_projection(commit_payload)
```

The delivery requirements are fixed:

- `StateProjectionWriter` must perform actual persistence
- `Index / Summary / Memory` may be thin adapters, but must call real foundations or perform actual file writes
- If `IndexManager.apply_entity_delta()`, `append_summary_projection()`, or `MemoryWriter.apply_commit_projection()` do not yet exist, add minimal adapter scaffolding in this task. Function names may change, but the public writer-layer protocol must remain unchanged
- `projection_status` records `"done"` / `"skipped"` / `"failed:..."`; it must not always return `"pending"`

- [ ] **Step 4: Rerun tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_projection_writers.py -q --no-cov`

Expected: Pass

- [ ] **Step 5: Commit**

```bash
git add webnovel-writer/scripts/data_modules/state_projection_writer.py \
        webnovel-writer/scripts/data_modules/index_projection_writer.py \
        webnovel-writer/scripts/data_modules/summary_projection_writer.py \
        webnovel-writer/scripts/data_modules/memory_projection_writer.py \
        webnovel-writer/scripts/data_modules/tests/test_projection_writers.py \
        webnovel-writer/scripts/data_modules/state_manager.py \
        webnovel-writer/scripts/data_modules/memory/writer.py
git commit -m "feat: add commit-driven projection writers"
```

---

## Task 4: CLI / Skill Integration, Documentation, and Validation

**Files:**
- Create: `webnovel-writer/scripts/chapter_commit.py`
- Modify: `webnovel-writer/scripts/data_modules/webnovel.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py`
- Modify: `webnovel-writer/skills/webnovel-write/SKILL.md`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`
- Create: `docs/architecture/story-system-phase3.md`
- Modify: `README.md`
- Modify: `docs/architecture/overview.md`
- Modify: `docs/guides/commands.md`
- Modify: `docs/superpowers/README.md`

- [ ] **Step 1: Add unified CLI forwarding tests**

```python
def test_webnovel_commit_forwards(monkeypatch, tmp_path):
    from data_modules import webnovel as cli
    project_root = tmp_path / "book"
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")
    called = {}

    def _fake_run_script(script_name, argv):
        called["script_name"] = script_name
        called["argv"] = argv
        return 0

    monkeypatch.setattr(cli, "_run_script", _fake_run_script)
    monkeypatch.setattr(sys, "argv", ["webnovel", "--project-root", str(project_root), "chapter-commit", "--chapter", "3"])
    cli.main()

    assert called["script_name"] == "chapter_commit.py"


def test_chapter_commit_cli_builds_and_persists_commit(tmp_path, monkeypatch):
    review_path = tmp_path / "review.json"
    fulfillment_path = tmp_path / "fulfillment.json"
    disambiguation_path = tmp_path / "disambiguation.json"
    extraction_path = tmp_path / "extraction.json"
    review_path.write_text('{"blocking_count": 0}', encoding="utf-8")
    fulfillment_path.write_text('{"planned_nodes": ["discover the trap"], "covered_nodes": ["discover the trap"], "missed_nodes": [], "extra_nodes": []}', encoding="utf-8")
    disambiguation_path.write_text('{"pending": []}', encoding="utf-8")
    extraction_path.write_text('{"state_deltas": [], "entity_deltas": [], "accepted_events": []}', encoding="utf-8")

    from chapter_commit import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "chapter_commit",
            "--project-root",
            str(tmp_path),
            "--chapter",
            "3",
            "--review-result",
            str(review_path),
            "--fulfillment-result",
            str(fulfillment_path),
            "--disambiguation-result",
            str(disambiguation_path),
            "--extraction-result",
            str(extraction_path),
        ],
    )
    main()

    assert (tmp_path / ".story-system" / "commits" / "chapter_003.commit.json").is_file()
```

- [ ] **Step 2: Integrate CLI and skills**

Add to `webnovel.py`:

```python
# webnovel-writer/scripts/chapter_commit.py
def _read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Chapter commit CLI")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--review-result", required=True)
    parser.add_argument("--fulfillment-result", required=True)
    parser.add_argument("--disambiguation-result", required=True)
    parser.add_argument("--extraction-result", required=True)
    args = parser.parse_args()

    service = ChapterCommitService(Path(args.project_root))
    payload = service.build_commit(
        chapter=args.chapter,
        review_result=_read_json(args.review_result),
        fulfillment_result=_read_json(args.fulfillment_result),
        disambiguation_result=_read_json(args.disambiguation_result),
        extraction_result=_read_json(args.extraction_result),
    )
    service.persist_commit(payload)
    if payload["meta"]["status"] == "accepted":
        payload = service.apply_projections(payload)
    print(json.dumps(payload, ensure_ascii=False))

# webnovel-writer/scripts/data_modules/webnovel.py
p_commit = sub.add_parser("chapter-commit", help="forward to chapter_commit.py")
p_commit.add_argument("args", nargs=argparse.REMAINDER)
```

In `skills/webnovel-write/SKILL.md`, replace direct post-writing state / index / summaries / memory persistence with:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" \
  chapter-commit --chapter {chapter_num} \
  --review-result "{review_json}" \
  --fulfillment-result "{fulfillment_json}" \
  --disambiguation-result "{disambiguation_json}" \
  --extraction-result "{extraction_json}"
```

Also state this operational constraint explicitly in the documentation:

- `chapter_commit.py` is the standalone manual/CLI entry point
- `review_pipeline.py` is the integrated entry point in the main skill workflow
- Each post-writing workflow may use only one entry point. Do not run `chapter_commit.py` after `review_pipeline.py` has already committed

- [ ] **Step 3: Create Phase 3 documentation and run regression tests**

Run:

```bash
python -m pytest \
  webnovel-writer/scripts/data_modules/tests/test_story_commit_schema.py \
  webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py \
  webnovel-writer/scripts/data_modules/tests/test_projection_writers.py \
  webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py \
  webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py \
  -q --no-cov
```

Expected: All pass

- [ ] **Step 4: Final commit**

```bash
git add webnovel-writer/scripts/chapter_commit.py \
        webnovel-writer/scripts/data_modules/webnovel.py \
        webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py \
        webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py \
        webnovel-writer/skills/webnovel-write/SKILL.md \
        webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py \
        README.md \
        docs/architecture/story-system-phase3.md \
        docs/architecture/overview.md \
        docs/guides/commands.md \
        docs/superpowers/README.md
git commit -m "docs: document story system phase3 chapter commit chain"
```

---

## Spec Coverage Check

- `13.4 Phase 3: Chapter commit mainline`
  - `CHAPTER_COMMIT`：Task 1 / Task 2
  - Four projection writers: Task 3
  - Accepted / rejected semantics: Task 2 / Task 3
  - Commit-driven post-writing persistence: Task 3 / Task 4

- `9.2 / 9.3 / 9.5`
  - Minimal structure, commit workflow, and failure semantics: Task 1 / Task 2

- `11.2 / 11.3`
  - Fulfillment / missed-node blocking: Task 2

---

## Placeholder Scan

- No `TODO / TBD` placeholders
- Projection writers are not deferred for later completion
- No premature introduction of the Phase 4 canonical event log

---

## Next Plan

After completing Phase 3, proceed to:

1. `Phase 4 Event Log And Override Ledger`
