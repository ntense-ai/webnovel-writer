# Story System Phase 5 Legacy Downgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Formally downgrade legacy hubs to compatibility/projection layers, unify default pre-writing inputs around Story Contracts and default post-writing facts around accepted `CHAPTER_COMMIT`, and make preflight / dashboard / skills / agents explicitly reflect this mainline.

**Architecture:** Add a unified runtime source resolver to answer centrally what the current chapter should trust. `context_manager`, `memory_contract_adapter`, `extract_chapter_context`, skills, and dashboard recognize only `MASTER / VOLUME / CHAPTER / REVIEW + latest accepted CHAPTER_COMMIT`. Retain `state.json / index.db / summaries / memory_scratchpad` solely as commit projections and query read-models. Any remaining `genre-profiles.md`, scattered legacy write commands, and state-first assumptions must be explicitly labeled fallback / compatibility, never presented as the mainline.

**Tech Stack:** Python 3.13, pytest, Pydantic, SQLite (`index.db`), FastAPI dashboard, React frontend, Story System JSON artifacts under `.story-system/`

**Spec:** `docs/superpowers/specs/2026-04-12-story-system-evolution-spec.md`

**Companion Plans:** `docs/superpowers/plans/2026-04-12-story-system-phase2-contract-first-runtime.md`, `docs/superpowers/plans/2026-04-12-story-system-phase3-chapter-commit-chain.md`, `docs/superpowers/plans/2026-04-12-story-system-phase4-event-log-and-override-ledger.md`

---

## Scope Split

This plan covers only Phase 5:

1. Contracts become the default primary input
2. Accepted `CHAPTER_COMMIT` becomes the default post-writing factual entry point
3. Explicitly downgrade `state / index / summary / memory` to projections/read-models
4. Explicitly downgrade `genre-profiles.md` and legacy reference-based decisions to fallbacks
5. Switch preflight / dashboard / query / write / review / context-agent / data-agent to the new mainline model

Explicit non-goals:

- Do not rewrite underlying storage in `StateManager / IndexManager / ScratchpadManager`
- Do not delete `.webnovel/state.json`, `.webnovel/index.db`, or `.webnovel/memory_scratchpad.json`
- Do not rebuild all historical commit / event data
- Do not introduce a second commit / projection system
- Do not undertake a major UI redesign unrelated to Phase 5

Exit criteria:

1. `context_manager`, `memory_contract_adapter`, and `extract_chapter_context` read contracts and the latest accepted commit by default instead of starting with legacy state and assembling decisions
2. Commit metadata from `ChapterCommitService` establishes it as the sole post-writing factual source and reliably locates `MASTER / VOLUME / CHAPTER / REVIEW`
3. Default instructions for `webnovel-write` / `webnovel-query` / `webnovel-review` / `webnovel-plan` and `context-agent` / `data-agent` are contract-first + commit-first
4. preflight and dashboard directly expose mainline readiness, legacy-fallback use, and rejected commits / projection backlog
5. `genre-profiles.md` is explicitly fallback-only and does not participate in global decisions when contracts exist
6. Documentation, command references, and operational guides accurately describe the relationship between the `.story-system` mainline and `.webnovel/*` projections

---

## File Structure

### Files to Create

- `webnovel-writer/scripts/data_modules/story_runtime_sources.py`
- `webnovel-writer/scripts/data_modules/story_runtime_health.py`
- `webnovel-writer/scripts/data_modules/tests/test_story_runtime_sources.py`
- `webnovel-writer/scripts/data_modules/tests/test_story_runtime_health.py`
- `docs/architecture/story-system-phase5.md`

### Files to Modify

- `webnovel-writer/scripts/data_modules/chapter_commit_service.py`
- `webnovel-writer/scripts/data_modules/context_manager.py`
- `webnovel-writer/scripts/data_modules/memory_contract_adapter.py`
- `webnovel-writer/scripts/extract_chapter_context.py`
- `webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py`
- `webnovel-writer/scripts/data_modules/tests/test_context_manager.py`
- `webnovel-writer/scripts/data_modules/tests/test_memory_contract_adapter.py`
- `webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py`
- `webnovel-writer/scripts/data_modules/webnovel.py`
- `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`
- `webnovel-writer/dashboard/app.py`
- `webnovel-writer/dashboard/frontend/src/App.jsx`
- `webnovel-writer/dashboard/frontend/src/api.js`
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- `webnovel-writer/skills/webnovel-review/SKILL.md`
- `webnovel-writer/skills/webnovel-query/SKILL.md`
- `webnovel-writer/skills/webnovel-plan/SKILL.md`
- `webnovel-writer/skills/webnovel-dashboard/SKILL.md`
- `webnovel-writer/agents/context-agent.md`
- `webnovel-writer/agents/data-agent.md`
- `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`
- `webnovel-writer/references/genre-profiles.md`
- `README.md`
- `docs/architecture/overview.md`
- `docs/guides/commands.md`
- `docs/operations/operations.md`
- `docs/superpowers/README.md`

### File Responsibilities

- `story_runtime_sources.py`: centrally resolve current-chapter contracts, latest commit, and fallback status instead of independent entry-point decisions
- `story_runtime_health.py`: aggregate mainline status, legacy fallback, and rejected/backlog into a shared preflight/dashboard health report
- `chapter_commit_service.py`: complete write-fact provenance so commits explicitly reference volume contracts and their post-writing truth role
- `context_manager.py`: organize runtime packs as contract mainline + commit summary + legacy fallback hints
- `memory_contract_adapter.py`: align both `load_context` and `commit_chapter` with the contract/commit mainline
- `extract_chapter_context.py`: upgrade exported text from a legacy-state summary to mainline status + visible fallback information
- `webnovel.py`: expose story runtime health in preflight and unify external CLI semantics
- `dashboard/app.py` + `frontend/src/*`: visualize runtime health, commit status, and legacy fallback
- `skills/*` + `agents/*`: switch default human/agent prompt workflows from scattered legacy writes to the commit mainline

---

## Task 1: Establish Unified Runtime Source Resolution and Commit Provenance

**Files:**
- Create: `webnovel-writer/scripts/data_modules/story_runtime_sources.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_story_runtime_sources.py`
- Modify: `webnovel-writer/scripts/data_modules/chapter_commit_service.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py`

- [ ] **Step 1: Write failing runtime-source and commit-provenance tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_story_runtime_sources.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from data_modules.story_runtime_sources import load_runtime_sources


def test_load_runtime_sources_prefers_latest_accepted_commit(tmp_path):
    story_root = tmp_path / ".story-system"
    (story_root / "chapters").mkdir(parents=True, exist_ok=True)
    (story_root / "volumes").mkdir(parents=True, exist_ok=True)
    (story_root / "reviews").mkdir(parents=True, exist_ok=True)
    (story_root / "commits").mkdir(parents=True, exist_ok=True)

    (story_root / "MASTER_SETTING.json").write_text(
        json.dumps({"meta": {"contract_type": "MASTER_SETTING"}, "route": {"primary_genre": "xuanhuan"}}),
        encoding="utf-8",
    )
    (story_root / "chapters" / "chapter_003.json").write_text(
        json.dumps({"meta": {"contract_type": "CHAPTER_BRIEF", "chapter": 3}}),
        encoding="utf-8",
    )
    (story_root / "volumes" / "volume_001.json").write_text(
        json.dumps({"meta": {"contract_type": "VOLUME_BRIEF", "volume": 1}}),
        encoding="utf-8",
    )
    (story_root / "reviews" / "chapter_003.review.json").write_text(
        json.dumps({"meta": {"contract_type": "REVIEW_CONTRACT", "chapter": 3}}),
        encoding="utf-8",
    )
    (story_root / "commits" / "chapter_003.commit.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "chapter": 3, "status": "accepted"},
                "provenance": {"write_fact_role": "chapter_commit"},
                "projection_status": {"state": "done", "index": "done", "summary": "done", "memory": "done"},
            }
        ),
        encoding="utf-8",
    )

    snapshot = load_runtime_sources(tmp_path, chapter=3)

    assert snapshot.latest_accepted_commit["meta"]["status"] == "accepted"
    assert snapshot.primary_write_source == "chapter_commit"
    assert snapshot.fallback_sources == []
```

```python
# webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py
def test_commit_service_includes_volume_ref_and_write_fact_provenance(tmp_path):
    service = ChapterCommitService(tmp_path)
    payload = service.build_commit(
        chapter=3,
        review_result={"blocking_count": 0},
        fulfillment_result={"planned_nodes": ["discover the trap"], "covered_nodes": ["discover the trap"], "missed_nodes": [], "extra_nodes": []},
        disambiguation_result={"pending": []},
        extraction_result={"state_deltas": [], "entity_deltas": [], "accepted_events": []},
    )

    assert payload["contract_refs"]["volume"] == "volume_001.json"
    assert payload["provenance"]["write_fact_role"] == "chapter_commit"
    assert payload["provenance"]["projection_role"] == "derived_read_models"
```

- [ ] **Step 2: Run tests and confirm that the new tests fail**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_runtime_sources.py webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py -q --no-cov`

Expected:
- `ModuleNotFoundError: No module named 'data_modules.story_runtime_sources'`
- or `KeyError: 'volume' / 'provenance'`

- [ ] **Step 3: Implement the unified runtime source resolver**

```python
# webnovel-writer/scripts/data_modules/story_runtime_sources.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .story_contracts import StoryContractPaths, read_json_if_exists


@dataclass
class RuntimeSourceSnapshot:
    chapter: int
    contracts: dict[str, dict[str, Any]]
    latest_commit: dict[str, Any] | None
    latest_accepted_commit: dict[str, Any] | None
    fallback_sources: list[str] = field(default_factory=list)
    primary_write_source: str = "chapter_commit"

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter,
            "contracts": self.contracts,
            "latest_commit": self.latest_commit,
            "latest_accepted_commit": self.latest_accepted_commit,
            "fallback_sources": self.fallback_sources,
            "primary_write_source": self.primary_write_source,
        }


def load_runtime_sources(project_root: Path, chapter: int) -> RuntimeSourceSnapshot:
    paths = StoryContractPaths.from_project_root(project_root)
    contracts = {
        "master": read_json_if_exists(paths.master_json) or {},
        "chapter": read_json_if_exists(paths.chapter_json(chapter)) or {},
        "volume": read_json_if_exists(paths.volume_json(1)) or {},
        "review": read_json_if_exists(paths.review_json(chapter)) or {},
    }

    latest_commit = read_json_if_exists(paths.commit_json(chapter))
    latest_accepted_commit = latest_commit if (latest_commit or {}).get("meta", {}).get("status") == "accepted" else None

    fallback_sources: list[str] = []
    for key, payload in contracts.items():
        if not payload:
            fallback_sources.append(f"missing_{key}_contract")
    if latest_accepted_commit is None:
        fallback_sources.append("missing_accepted_commit")

    return RuntimeSourceSnapshot(
        chapter=chapter,
        contracts=contracts,
        latest_commit=latest_commit,
        latest_accepted_commit=latest_accepted_commit,
        fallback_sources=fallback_sources,
    )
```

- [ ] **Step 4: Complete provenance fields and volume references in the commit service**

```python
# webnovel-writer/scripts/data_modules/chapter_commit_service.py
from chapter_outline_loader import volume_num_for_chapter_from_state


def build_commit(
    self,
    chapter: int,
    review_result: Dict[str, Any],
    fulfillment_result: Dict[str, Any],
    disambiguation_result: Dict[str, Any],
    extraction_result: Dict[str, Any],
) -> Dict[str, Any]:
    volume = volume_num_for_chapter_from_state(self.project_root, chapter) or 1
    return {
        "meta": {
            "schema_version": "story-system/v1",
            "chapter": chapter,
            "status": status,
        },
        "contract_refs": {
            "master": "MASTER_SETTING.json",
            "volume": f"volume_{volume:03d}.json",
            "chapter": f"chapter_{chapter:03d}.json",
            "review": f"chapter_{chapter:03d}.review.json",
        },
        "provenance": {
            "write_fact_role": "chapter_commit",
            "projection_role": "derived_read_models",
            "legacy_state_role": "projection_only",
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
        "summary_text": extraction_result.get("summary_text", ""),
        "projection_status": {"state": "pending", "index": "pending", "summary": "pending", "memory": "pending"},
    }
```

- [ ] **Step 5: Rerun focused tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_runtime_sources.py webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py -q --no-cov`

Expected: `2 passed`

- [ ] **Step 6: Commit this task**

```bash
git add webnovel-writer/scripts/data_modules/story_runtime_sources.py \
        webnovel-writer/scripts/data_modules/chapter_commit_service.py \
        webnovel-writer/scripts/data_modules/tests/test_story_runtime_sources.py \
        webnovel-writer/scripts/data_modules/tests/test_chapter_commit_service.py
git commit -m "feat: add story runtime source resolver"
```

---

## Task 2: Switch Context Entry Points to Contract-First + Commit-First

**Files:**
- Modify: `webnovel-writer/scripts/data_modules/context_manager.py`
- Modify: `webnovel-writer/scripts/data_modules/memory_contract_adapter.py`
- Modify: `webnovel-writer/scripts/extract_chapter_context.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_context_manager.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_memory_contract_adapter.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py`

- [ ] **Step 1: Add three groups of failing tests to lock in new-mainline semantics**

```python
# webnovel-writer/scripts/data_modules/tests/test_context_manager.py
def test_context_manager_prefers_contract_route_over_legacy_genre_profile(temp_project):
    refs_dir = temp_project.project_root / ".claude" / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    (refs_dir / "genre-profiles.md").write_text("## urban\n- old profile hint", encoding="utf-8")
    (refs_dir / "reading-power-taxonomy.md").write_text("## urban\n- oldcategory", encoding="utf-8")

    state = {
        "project": {"genre": "urban"},
        "protagonist_state": {"name": "Lin Mo"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    story_root = temp_project.story_system_dir
    story_root.mkdir(parents=True, exist_ok=True)
    (story_root / "MASTER_SETTING.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
                "route": {"primary_genre": "urban-fantasy"},
                "master_constraints": {"core_tone": "pressure before release"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    manager = ContextManager(temp_project)
    payload = manager.build_context(3, use_snapshot=False, save_snapshot=False)

    assert payload["sections"]["story_contract"]["content"]["master"]["route"]["primary_genre"] == "urban-fantasy"
    assert payload["sections"]["runtime_status"]["content"]["fallback_sources"] == ["missing_volume_contract", "missing_chapter_contract", "missing_review_contract", "missing_accepted_commit"]
```

```python
# webnovel-writer/scripts/data_modules/tests/test_memory_contract_adapter.py
def test_commit_chapter_delegates_to_chapter_commit_mainline(tmp_path):
    cfg = _make_project(tmp_path)
    adapter = MemoryContractAdapter(cfg)

    result = adapter.commit_chapter(
        3,
        {
            "review_result": {"blocking_count": 0},
            "fulfillment_result": {"planned_nodes": ["discover the trap"], "covered_nodes": ["discover the trap"], "missed_nodes": [], "extra_nodes": []},
            "disambiguation_result": {"pending": []},
            "extraction_result": {"state_deltas": [], "entity_deltas": [], "accepted_events": [], "summary_text": "chapter summary"},
        },
    )

    assert (tmp_path / ".story-system" / "commits" / "chapter_003.commit.json").is_file()
    assert result.chapter == 3
    assert "commit_status=accepted" in result.warnings
```

```python
# webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py
def test_render_text_contains_runtime_status_section(tmp_path):
    from extract_chapter_context import _render_text

    text = _render_text(
        {
            "chapter": 3,
            "outline": "testoutlines",
            "previous_summaries": [],
            "state_summary": "old state summary",
            "context_contract_version": "v2",
            "reader_signal": {},
            "genre_profile": {},
            "writing_guidance": {},
            "runtime_status": {
                "primary_write_source": "chapter_commit",
                "fallback_sources": ["missing_accepted_commit"],
            },
            "latest_commit": {"meta": {"chapter": 3, "status": "rejected"}},
        }
    )

    assert "## Runtime Status" in text
    assert "- post-writing fact entry point: chapter_commit" in text
    assert "- Legacy Fallback: missing_accepted_commit" in text
```

- [ ] **Step 2: Run failing tests to confirm current entry points still favor the legacy pipeline**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_context_manager.py webnovel-writer/scripts/data_modules/tests/test_memory_contract_adapter.py webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py -q --no-cov`

Expected:
- `KeyError: 'runtime_status'`
- `AssertionError`(`commit_chapter` still does not generate `.story-system/commits/chapter_003.commit.json`)
- `_render_text` has no runtime-status section

- [ ] **Step 3: Rewrite ContextManager pack assembly order**

```python
# webnovel-writer/scripts/data_modules/context_manager.py
from .story_runtime_sources import load_runtime_sources


def _build_pack(self, chapter: int) -> Dict[str, Any]:
    runtime_sources = load_runtime_sources(self.config.project_root, chapter)
    state = self._load_state()

    story_contract = {
        "master": runtime_sources.contracts.get("master") or {},
        "volume": runtime_sources.contracts.get("volume") or {},
        "chapter": runtime_sources.contracts.get("chapter") or {},
        "review_contract": runtime_sources.contracts.get("review") or {},
    }

    genre_profile = {}
    if runtime_sources.fallback_sources:
        genre_profile = self._load_genre_profile(state)
        genre_profile["mode"] = "fallback_only"

    reader_signal = self._load_reader_signal(chapter)
    return {
        "story_contract": story_contract,
        "runtime_status": runtime_sources.to_dict(),
        "latest_commit": runtime_sources.latest_accepted_commit or runtime_sources.latest_commit or {},
        "genre_profile": genre_profile,
        "reader_signal": reader_signal,
        "preferences": self._load_json_optional(self.config.webnovel_dir / "preferences.json"),
        "writing_guidance": self._build_writing_guidance(chapter, reader_signal, genre_profile),
    }
```

- [ ] **Step 4: Switch both read and write pipelines in MemoryContractAdapter**

```python
# webnovel-writer/scripts/data_modules/memory_contract_adapter.py
from .chapter_commit_service import ChapterCommitService
from .story_runtime_sources import load_runtime_sources


def load_context(self, chapter: int, budget_tokens: int = 4000) -> ContextPack:
    runtime_sources = load_runtime_sources(self.config.project_root, chapter)
    sections = {
        "story_contracts": runtime_sources.contracts,
        "runtime_status": runtime_sources.to_dict(),
        "latest_commit": runtime_sources.latest_accepted_commit or runtime_sources.latest_commit or {},
    }
    return ContextPack(chapter=chapter, sections=sections, budget_used_tokens=0)


def commit_chapter(self, chapter: int, result: dict) -> CommitResult:
    service = ChapterCommitService(self.config.project_root)
    payload = service.build_commit(
        chapter=chapter,
        review_result=result.get("review_result", {}),
        fulfillment_result=result.get("fulfillment_result", {}),
        disambiguation_result=result.get("disambiguation_result", {}),
        extraction_result=result.get("extraction_result", {}),
    )
    service.persist_commit(payload)
    payload = service.apply_projections(payload) if payload["meta"]["status"] == "accepted" else payload
    summary_path = str(self.config.webnovel_dir / "summaries" / f"ch{chapter:04d}.md")
    return CommitResult(
        chapter=chapter,
        entities_added=len((payload.get("entity_deltas") or [])),
        entities_updated=0,
        state_changes_recorded=len((payload.get("state_deltas") or [])),
        relationships_added=0,
        memory_items_added=0,
        summary_path=summary_path if Path(summary_path).exists() else "",
        warnings=[f"commit_status={payload['meta']['status']}"],
    )
```

- [ ] **Step 5: Update `extract_chapter_context.py` text output to make legacy fallback explicit**

```python
# webnovel-writer/scripts/extract_chapter_context.py
def _render_text(payload: Dict[str, Any]) -> str:
    lines = [f"# Chapter {payload.get('chapter', 0)} context"]
    runtime_status = payload.get("runtime_status") or {}
    latest_commit = payload.get("latest_commit") or {}
    lines.extend(
        [
            "## Runtime Status",
            f"- post-writing fact entry point: {runtime_status.get('primary_write_source', 'unknown')}",
            f"- Legacy Fallback: {', '.join(runtime_status.get('fallback_sources') or ['none'])}",
            f"- Latest Commit: {(latest_commit.get('meta') or {}).get('status', 'missing')}",
        ]
    )
    return "\n".join(lines)
```

- [ ] **Step 6: Rerun focused tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_context_manager.py webnovel-writer/scripts/data_modules/tests/test_memory_contract_adapter.py webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py -q --no-cov`

Expected: `3 passed`, or all tests in the relevant files pass

- [ ] **Step 7: Commit this task**

```bash
git add webnovel-writer/scripts/data_modules/context_manager.py \
        webnovel-writer/scripts/data_modules/memory_contract_adapter.py \
        webnovel-writer/scripts/extract_chapter_context.py \
        webnovel-writer/scripts/data_modules/tests/test_context_manager.py \
        webnovel-writer/scripts/data_modules/tests/test_memory_contract_adapter.py \
        webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py
git commit -m "feat: switch context loading to contract and commit chain"
```

---

## Task 3: Switch Default Skills / Agents Workflows to the Commit Mainline

**Files:**
- Modify: `webnovel-writer/skills/webnovel-write/SKILL.md`
- Modify: `webnovel-writer/skills/webnovel-review/SKILL.md`
- Modify: `webnovel-writer/skills/webnovel-query/SKILL.md`
- Modify: `webnovel-writer/skills/webnovel-plan/SKILL.md`
- Modify: `webnovel-writer/skills/webnovel-dashboard/SKILL.md`
- Modify: `webnovel-writer/agents/context-agent.md`
- Modify: `webnovel-writer/agents/data-agent.md`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`

- [ ] **Step 1: Write failing prompt-integrity tests to lock in the new-mainline description**

```python
# webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py
def test_webnovel_write_skill_uses_chapter_commit_as_step5_mainline():
    text = (SKILLS_DIR / "webnovel-write" / "SKILL.md").read_text(encoding="utf-8")
    assert "chapter-commit" in text
    assert "accepted `CHAPTER_COMMIT`" in text
    assert "state process-chapter" not in text


def test_data_agent_is_described_as_extraction_only_not_direct_write_mainline():
    text = (AGENTS_DIR / "data-agent.md").read_text(encoding="utf-8")
    assert "chapter-commit" in text
    assert "write directly index.db and state.json" not in text


def test_webnovel_query_skill_prefers_story_system_and_memory_contract():
    text = (SKILLS_DIR / "webnovel-query" / "SKILL.md").read_text(encoding="utf-8")
    assert "memory-contract load-context" in text
    assert ".story-system/" in text
    assert 'cat "$PROJECT_ROOT/.webnovel/state.json"' not in text
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py -q --no-cov`

Expected: At least one assertion fails, showing that prompts still use the legacy scattered-write model

- [ ] **Step 3: Rewrite `webnovel-write` so Step 5 success is defined by the commit**

````md
<!-- webnovel-writer/skills/webnovel-write/SKILL.md -->
### Step 5: Build Extraction Artifacts and Submit `CHAPTER_COMMIT`

Required intermediate files:
- `${PROJECT_ROOT}/.webnovel/tmp/review_results.json`
- `${PROJECT_ROOT}/.webnovel/tmp/fulfillment_result.json`
- `${PROJECT_ROOT}/.webnovel/tmp/disambiguation_result.json`
- `${PROJECT_ROOT}/.webnovel/tmp/extraction_result.json`

Main command:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${PROJECT_ROOT}" chapter-commit \
  --chapter {chapter_num} \
  --review-result "${PROJECT_ROOT}/.webnovel/tmp/review_results.json" \
  --fulfillment-result "${PROJECT_ROOT}/.webnovel/tmp/fulfillment_result.json" \
  --disambiguation-result "${PROJECT_ROOT}/.webnovel/tmp/disambiguation_result.json" \
  --extraction-result "${PROJECT_ROOT}/.webnovel/tmp/extraction_result.json"
```

Success criteria:
- `.story-system/commits/chapter_{chapter_num}.commit.json` exists
- `meta.status == accepted`
- In `projection_status`, `state/index/summary/memory` are all `done` or explicitly `skipped`
````

- [ ] **Step 4: Rewrite default read/write descriptions for query / review / plan / context-agent / data-agent**

```md
<!-- webnovel-writer/agents/data-agent.md -->
You generate `extraction_result.json` and supply the following to `chapter-commit`:
- `accepted_events`
- `state_deltas`
- `entity_deltas`
- `summary_text`

You are not the post-writing source of truth.
Final writes to `state.json / index.db / summaries / memory_scratchpad` are performed by projection writers for an accepted `CHAPTER_COMMIT`.
```

```md
<!-- webnovel-writer/skills/webnovel-query/SKILL.md -->
The query order is fixed:
1. `.story-system/MASTER_SETTING.json`
2. `.story-system/volumes/*.json`
3. `.story-system/chapters/*.json`
4. latest accepted `.story-system/commits/chapter_XXX.commit.json`
5. `memory-contract load-context`
6. `.webnovel/state.json` / `index.db`(fallback/read-model only)
```

- [ ] **Step 5: Rerun prompt integrity tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py -q --no-cov`

Expected: `passed`

- [ ] **Step 6: Commit this task**

```bash
git add webnovel-writer/skills/webnovel-write/SKILL.md \
        webnovel-writer/skills/webnovel-review/SKILL.md \
        webnovel-writer/skills/webnovel-query/SKILL.md \
        webnovel-writer/skills/webnovel-plan/SKILL.md \
        webnovel-writer/skills/webnovel-dashboard/SKILL.md \
        webnovel-writer/agents/context-agent.md \
        webnovel-writer/agents/data-agent.md \
        webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py
git commit -m "docs: cut skills over to chapter commit mainline"
```

---

## Task 4: Expose Story Runtime Health to Eliminate Apparent but Incomplete Switchovers

**Files:**
- Create: `webnovel-writer/scripts/data_modules/story_runtime_health.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_story_runtime_health.py`
- Modify: `webnovel-writer/scripts/data_modules/webnovel.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`
- Modify: `webnovel-writer/dashboard/app.py`
- Modify: `webnovel-writer/dashboard/frontend/src/api.js`
- Modify: `webnovel-writer/dashboard/frontend/src/App.jsx`

- [ ] **Step 1: Write failing health-helper and preflight tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_story_runtime_health.py
from data_modules.story_runtime_health import build_story_runtime_health


def test_story_runtime_health_reports_missing_commit_as_not_ready(tmp_path):
    report = build_story_runtime_health(tmp_path, chapter=3)
    assert report["mainline_ready"] is False
    assert "missing_accepted_commit" in report["fallback_sources"]
```

```python
# webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py
def test_preflight_includes_story_runtime_health(monkeypatch, tmp_path, capsys):
    module = _load_webnovel_module()

    project_root = tmp_path / "book"
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["webnovel", "--project-root", str(project_root), "preflight", "--format", "json"])

    with pytest.raises(SystemExit):
        module.main()

    captured = capsys.readouterr()
    assert '"story_runtime"' in captured.out
    assert '"mainline_ready"' in captured.out
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_runtime_health.py webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py -q --no-cov`

Expected:
- `ModuleNotFoundError: No module named 'data_modules.story_runtime_health'`
- preflight JSON does not contain `story_runtime`

- [ ] **Step 3: Implement the health helper and connect it to preflight**

```python
# webnovel-writer/scripts/data_modules/story_runtime_health.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from .story_runtime_sources import load_runtime_sources


def build_story_runtime_health(project_root: Path, chapter: int | None = None) -> dict[str, Any]:
    current_chapter = int(chapter or 0)
    snapshot = load_runtime_sources(project_root, current_chapter) if current_chapter else None
    fallback_sources = list((snapshot.fallback_sources if snapshot else ["chapter_unspecified"]))
    latest_commit = (snapshot.latest_commit if snapshot else None) or {}
    return {
        "chapter": current_chapter,
        "mainline_ready": bool(snapshot and not snapshot.fallback_sources),
        "fallback_sources": fallback_sources,
        "latest_commit_status": (latest_commit.get("meta") or {}).get("status", "missing"),
        "primary_write_source": (snapshot.primary_write_source if snapshot else "chapter_commit"),
    }
```

```python
# webnovel-writer/scripts/data_modules/webnovel.py
from data_modules.story_runtime_health import build_story_runtime_health


def _build_preflight_report(explicit_project_root: Optional[str]) -> dict:
    scripts_dir = _scripts_dir().resolve()
    plugin_root = scripts_dir.parent
    skill_root = plugin_root / "skills" / "webnovel-write"
    entry_script = scripts_dir / "webnovel.py"
    extract_script = scripts_dir / "extract_chapter_context.py"

    checks = [
        {"name": "scripts_dir", "ok": scripts_dir.is_dir(), "path": str(scripts_dir)},
        {"name": "entry_script", "ok": entry_script.is_file(), "path": str(entry_script)},
        {"name": "extract_context_script", "ok": extract_script.is_file(), "path": str(extract_script)},
        {"name": "skill_root", "ok": skill_root.is_dir(), "path": str(skill_root)},
    ]

    project_root = ""
    project_root_error = ""
    try:
        resolved_root = _resolve_root(explicit_project_root)
        project_root = str(resolved_root)
        checks.append({"name": "project_root", "ok": True, "path": project_root})
    except Exception as exc:
        project_root_error = str(exc)
        checks.append({"name": "project_root", "ok": False, "path": explicit_project_root or "", "error": project_root_error})

    story_runtime = build_story_runtime_health(Path(project_root)) if project_root else {}
    return {
        "ok": all(bool(item["ok"]) for item in checks),
        "project_root": project_root,
        "scripts_dir": str(scripts_dir),
        "skill_root": str(skill_root),
        "checks": checks,
        "project_root_error": project_root_error,
        "story_runtime": story_runtime,
    }
```

- [ ] **Step 4: Expose story runtime health and latest-commit status in the dashboard**

```python
# webnovel-writer/dashboard/app.py
from data_modules.story_runtime_health import build_story_runtime_health


@app.get("/api/story-runtime/health")
def story_runtime_health():
    project_root = _get_project_root()
    state_path = project_root / ".webnovel" / "state.json"
    chapter = 0
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        chapter = int(((state.get("progress") or {}).get("current_chapter") or 0))
    return build_story_runtime_health(project_root, chapter=chapter)
```

```jsx
// webnovel-writer/dashboard/frontend/src/App.jsx
const [runtimeHealth, setRuntimeHealth] = useState(null)

useEffect(() => {
  fetchJSON('/api/story-runtime/health').then(setRuntimeHealth).catch(() => setRuntimeHealth(null))
}, [refreshKey])

{runtimeHealth ? (
  <div className="card stat-card">
    <span className="stat-label">Story Runtime</span>
    <span className="stat-value plain">{runtimeHealth.mainline_ready ? 'Mainline' : 'Fallback'}</span>
    <span className="stat-sub">
      {runtimeHealth.latest_commit_status} · {(runtimeHealth.fallback_sources || []).join(', ') || 'no fallback'}
    </span>
  </div>
) : null}
```

- [ ] **Step 5: Run backend tests and the frontend build**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_runtime_health.py webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py -q --no-cov`

Expected: `passed`

Run: `npm --prefix webnovel-writer/dashboard/frontend run build`

Expected: Vite build success, with no new lint/blocking errors

- [ ] **Step 6: Commit this task**

```bash
git add webnovel-writer/scripts/data_modules/story_runtime_health.py \
        webnovel-writer/scripts/data_modules/webnovel.py \
        webnovel-writer/scripts/data_modules/tests/test_story_runtime_health.py \
        webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py \
        webnovel-writer/dashboard/app.py \
        webnovel-writer/dashboard/frontend/src/api.js \
        webnovel-writer/dashboard/frontend/src/App.jsx
git commit -m "feat: surface story runtime health in preflight and dashboard"
```

---

## Task 5: Finalize Legacy Fallback Documentation and Operating Instructions

**Files:**
- Create: `docs/architecture/story-system-phase5.md`
- Modify: `webnovel-writer/references/genre-profiles.md`
- Modify: `README.md`
- Modify: `docs/architecture/overview.md`
- Modify: `docs/guides/commands.md`
- Modify: `docs/operations/operations.md`
- Modify: `docs/superpowers/README.md`

- [ ] **Step 1: Add the architecture-document skeleton first, explicitly stating the mainline switchover**

````md
<!-- docs/architecture/story-system-phase5.md -->
# Story System Phase 5

## Core Conclusions

- Pre-writing source of truth: `MASTER / VOLUME / CHAPTER / REVIEW`
- Post-writing source of truth: accepted `CHAPTER_COMMIT`
- `state / index / summary / memory`: projections/read-models
- `genre-profiles.md`：fallback-only

## Default Pipeline

```text
story-system --persist/--emit-runtime-contracts
    -> context / query / write / review read contracts
chapter-commit --chapter N
    -> accepted commit
    -> projection writers
    -> state / index / summaries / memory
```
````

- [ ] **Step 2: Explicitly mark the `genre-profiles.md` header as fallback-only**

```md
<!-- webnovel-writer/references/genre-profiles.md -->
# genre-profiles

> **Status: Fallback Only**
> Primary genre decisions, tone, and prohibitions for common genres have moved to Story Contract / CSV route seed.
> This file provides supplementary guidance only when contracts are missing, the project has not been upgraded, or fallback is explicitly requested.
```

- [ ] **Step 3: Update README / commands / operations with actionable mainline instructions**

```md
<!-- docs/guides/commands.md -->
## Story System Mainline

1. Generate contracts:
   `python -X utf8 "webnovel-writer/scripts/webnovel.py" --project-root "{WORKSPACE_ROOT}" story-system "{goal}" --chapter {N} --persist --emit-runtime-contracts --format both`
2. Submit a chapter:
   `python -X utf8 "webnovel-writer/scripts/webnovel.py" --project-root "{PROJECT_ROOT}" chapter-commit --chapter {N} --review-result ".webnovel/tmp/review_results.json" --fulfillment-result ".webnovel/tmp/fulfillment_result.json" --disambiguation-result ".webnovel/tmp/disambiguation_result.json" --extraction-result ".webnovel/tmp/extraction_result.json"`
3. Check health:
   `python -X utf8 "webnovel-writer/scripts/webnovel.py" --project-root "{PROJECT_ROOT}" preflight --format json`
```

- [ ] **Step 4: Run final regression tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py webnovel-writer/scripts/data_modules/tests/test_context_manager.py webnovel-writer/scripts/data_modules/tests/test_memory_contract_adapter.py -q --no-cov`

Expected: All pass

- [ ] **Step 5: Commit this task**

```bash
git add docs/architecture/story-system-phase5.md \
        webnovel-writer/references/genre-profiles.md \
        README.md \
        docs/architecture/overview.md \
        docs/guides/commands.md \
        docs/operations/operations.md \
        docs/superpowers/README.md
git commit -m "docs: finalize phase5 legacy downgrade"
```

---

## Self-Review

### Spec Coverage

- `13.6 Phase 5: Legacy pipeline downgrade`
  - Task 1 covers unified runtime sources and commit provenance
  - Task 2 switches default primary inputs and post-writing facts
  - Task 3 switches skills / agents prompts to the new pipeline
  - Task 4 covers preflight / dashboard / health observability
  - Task 5 finalizes fallback-only documentation and the command guide

- `7.2 Runtime priorities`
  - Task 2 explicitly fixes `story_contracts -> latest accepted commit -> legacy fallback` at the entry-point layer

- `7.3 Post-writing source of truth`
  - Tasks 1 and 2 make `CHAPTER_COMMIT` the sole post-writing factual entry point

- `17.1 Documentation update requirements`
  - Task 5 covers architecture, commands, operations, and overview documentation

### Placeholder Scan

- No placeholders defer implementation
- Every task specifies files, tests, commands, and commit messages
- Cross-task references do not replace actual steps

### Type Consistency

Use the following names consistently throughout this plan; do not rename them in subsequent tasks:

- `RuntimeSourceSnapshot`
- `load_runtime_sources(project_root, chapter)`
- `build_story_runtime_health(project_root, chapter=None)`
- `latest_accepted_commit`
- `fallback_sources`
- `write_fact_role = "chapter_commit"`

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-13-story-system-phase5-legacy-downgrade.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
