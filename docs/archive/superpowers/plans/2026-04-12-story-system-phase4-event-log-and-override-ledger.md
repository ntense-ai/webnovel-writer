# Story System Phase 4 Event Log And Override Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a canonical event log, stable event-to-projection mappings, and event-triggered `amend proposal` rules, while evolving existing `override_contracts` into the foundation of a unified override ledger.

**Architecture:** Build on Phase 3 `CHAPTER_COMMIT.accepted_events` with persistence in `.story-system/events/` and an `index.db` audit mirror, making events official inputs rather than scattered traces in `state_changes / relationship_events / memory_facts`. Expand `override_contracts` from a reader-retention debt mechanism into a unified ledger containing `soft_deviation / contract_override / amend_proposal`. By default, runtime consumes only summaries relevant to the current chapter, not the entire ledger in the prompt.

**Tech Stack:** Python 3.13, Pydantic, pytest, SQLite (`index.db`), JSON event artifacts, dashboard / observability hooks

**Spec:** `docs/superpowers/specs/2026-04-12-story-system-evolution-spec.md`

**Companion Plans:** `docs/superpowers/plans/2026-04-12-story-system-phase3-chapter-commit-chain.md`, `docs/superpowers/specs/2026-04-12-webnovel-story-intelligence-system-spec.md`

---

## Scope Split

This plan covers only Phase 4:

1. canonical event log
2. Stable event-to-projection mappings
3. Event-triggered `amend proposal` rules
4. Override ledger expansion

Explicit non-goals:

- Do not perform Phase 5 legacy-pipeline downgrades
- Do not clean up the `genre-profiles.md` fallback pipeline
- Do not inject all historical overrides directly into runtime prompts

Exit criteria:

1. Accepted commits reliably produce event files and synchronously write `.webnovel/index.db.story_events`
2. The projection layer prioritizes events over final overwrite values
3. Setting changes requiring promotion generate an `amend proposal`
4. `override_contracts` supports all three record types while retaining compatibility with legacy reader-retention debt data
5. dashboard / preflight / health / backup have at least minimal integration instructions and read-only inspection entry points

Append documentation updates to existing `Story System` sections without restructuring the README.

---

## File Structure

### Files to Create

- `webnovel-writer/scripts/story_events.py`
- `webnovel-writer/scripts/data_modules/story_event_schema.py`
- `webnovel-writer/scripts/data_modules/event_log_store.py`
- `webnovel-writer/scripts/data_modules/event_projection_router.py`
- `webnovel-writer/scripts/data_modules/amend_proposal_schema.py`
- `webnovel-writer/scripts/data_modules/override_ledger_service.py`
- `webnovel-writer/scripts/data_modules/tests/test_story_event_schema.py`
- `webnovel-writer/scripts/data_modules/tests/test_event_log_store.py`
- `webnovel-writer/scripts/data_modules/tests/test_event_projection_router.py`
- `webnovel-writer/scripts/data_modules/tests/test_override_ledger_service.py`
- `docs/architecture/story-system-phase4.md`

### Files to Modify

- `webnovel-writer/scripts/data_modules/chapter_commit_service.py`
- `webnovel-writer/scripts/data_modules/index_manager.py`
- `webnovel-writer/scripts/data_modules/index_debt_mixin.py`
- `webnovel-writer/scripts/data_modules/index_observability_mixin.py`
- `webnovel-writer/scripts/data_modules/webnovel.py`
- `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`
- `webnovel-writer/dashboard/app.py`
- `README.md`
- `docs/architecture/overview.md`
- `docs/guides/commands.md`
- `docs/operations/operations.md`
- `docs/superpowers/README.md`

---

## Task 1: Define the event schema and canonical event persistence

**Files:**
- Create: `webnovel-writer/scripts/data_modules/story_event_schema.py`
- Create: `webnovel-writer/scripts/data_modules/event_log_store.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_story_event_schema.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_event_log_store.py`
- Modify: `webnovel-writer/scripts/data_modules/chapter_commit_service.py`

- [ ] **Step 1: Write event schema / store tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_story_event_schema.py
from data_modules.story_event_schema import StoryEvent


def test_story_event_supports_power_breakthrough():
    event = StoryEvent.model_validate(
        {
            "event_id": "evt-001",
            "chapter": 3,
            "event_type": "power_breakthrough",
            "subject": "xiaoyan",
            "payload": {"from": "third-stage Dou Qi", "to": "Dou Zhe"},
        }
    )
    assert event.event_type == "power_breakthrough"
```

```python
# webnovel-writer/scripts/data_modules/tests/test_event_log_store.py
import sqlite3

from data_modules.event_log_store import EventLogStore


def test_event_log_store_writes_per_chapter_file_and_sqlite_mirror(tmp_path):
    store = EventLogStore(tmp_path)
    store.write_events(3, [{"event_id": "evt-001", "event_type": "open_loop_created", "subject": "three-year agreement", "payload": {}}])
    assert (tmp_path / ".story-system" / "events" / "chapter_003.events.json").is_file()

    conn = sqlite3.connect(tmp_path / ".webnovel" / "index.db")
    try:
        row = conn.execute("SELECT event_id, chapter, event_type FROM story_events").fetchone()
    finally:
        conn.close()
    assert row == ("evt-001", 3, "open_loop_created")
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_event_schema.py webnovel-writer/scripts/data_modules/tests/test_event_log_store.py -q --no-cov`

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement schema and store**

```python
# webnovel-writer/scripts/data_modules/story_event_schema.py
from __future__ import annotations

from typing import Any, Dict, Literal

from pydantic import BaseModel


class StoryEvent(BaseModel):
    event_id: str
    chapter: int
    event_type: Literal[
        "character_state_changed",
        "relationship_changed",
        "world_rule_revealed",
        "world_rule_broken",
        "power_breakthrough",
        "artifact_obtained",
        "promise_created",
        "promise_paid_off",
        "open_loop_created",
        "open_loop_closed",
    ]
    subject: str
    payload: Dict[str, Any]
```

```python
# webnovel-writer/scripts/data_modules/event_log_store.py
import json
import sqlite3
from pathlib import Path


class EventLogStore:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def write_events(self, chapter: int, events: list[dict]) -> Path:
        target = self.project_root / ".story-system" / "events"
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"chapter_{chapter:03d}.events.json"
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        self._write_sqlite_mirror(chapter, events)
        return path

    def _write_sqlite_mirror(self, chapter: int, events: list[dict]) -> None:
        db_path = self.project_root / ".webnovel" / "index.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS story_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    chapter INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.executemany(
                "INSERT OR IGNORE INTO story_events(event_id, chapter, event_type, subject, payload_json) VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        event["event_id"],
                        chapter,
                        event["event_type"],
                        event["subject"],
                        json.dumps(event.get("payload") or {}, ensure_ascii=False),
                    )
                    for event in events
                ],
            )
            conn.commit()
        finally:
            conn.close()
```

- [ ] **Step 4: Have `chapter_commit_service` write event files after an accepted commit**

```python
if payload["meta"]["status"] == "accepted":
    EventLogStore(self.project_root).write_events(chapter, payload["accepted_events"])
```

- [ ] **Step 5: Rerun tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_event_schema.py webnovel-writer/scripts/data_modules/tests/test_event_log_store.py -q --no-cov`

Expected: Pass

- [ ] **Step 6: Commit**

```bash
git add webnovel-writer/scripts/data_modules/story_event_schema.py \
        webnovel-writer/scripts/data_modules/event_log_store.py \
        webnovel-writer/scripts/data_modules/tests/test_story_event_schema.py \
        webnovel-writer/scripts/data_modules/tests/test_event_log_store.py \
        webnovel-writer/scripts/data_modules/chapter_commit_service.py
git commit -m "feat: add canonical event schema and per-chapter event store"
```

---

## Task 2: Establish Stable Event-to-Projection Mappings

**Files:**
- Create: `webnovel-writer/scripts/data_modules/event_projection_router.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_event_projection_router.py`
- Modify: `webnovel-writer/scripts/data_modules/state_projection_writer.py`
- Modify: `webnovel-writer/scripts/data_modules/index_projection_writer.py`
- Modify: `webnovel-writer/scripts/data_modules/memory_projection_writer.py`

- [ ] **Step 1: Write event-routing tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_event_projection_router.py
from data_modules.event_projection_router import EventProjectionRouter


def test_router_maps_power_breakthrough_to_state_and_memory():
    router = EventProjectionRouter()
    targets = router.route({"event_type": "power_breakthrough", "subject": "xiaoyan", "payload": {}})
    assert targets == ["state", "memory"]


def test_router_maps_relationship_changed_to_index():
    router = EventProjectionRouter()
    targets = router.route({"event_type": "relationship_changed", "subject": "xiaoyan", "payload": {"to": "yaolao"}})
    assert "index" in targets
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_event_projection_router.py -q --no-cov`

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement the router and make writers consume events**

```python
# webnovel-writer/scripts/data_modules/event_projection_router.py
class EventProjectionRouter:
    TABLE = {
        "character_state_changed": ["state", "memory"],
        "power_breakthrough": ["state", "memory"],
        "relationship_changed": ["index"],
        "world_rule_revealed": ["memory", "index"],
        "world_rule_broken": ["memory", "index"],
        "open_loop_created": ["memory"],
        "open_loop_closed": ["memory"],
        "promise_created": ["memory"],
        "promise_paid_off": ["memory"],
        "artifact_obtained": ["state", "index"],
    }

    def route(self, event: dict) -> list[str]:
        return list(self.TABLE.get(event.get("event_type"), []))
```

Fix the P3 / P4 relationship explicitly here to prevent duplicate projection during implementation:

- `EventProjectionRouter` is a **declarative activation table**
- The actual execution entry point remains `ChapterCommitService.apply_projections()`
- `apply_projections()` first collects the writers matched by `accepted_events`, then calls only the required writers
- Phase 4 **does not introduce a second independent projection loop**

- [ ] **Step 4: Rerun tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_event_projection_router.py -q --no-cov`

Expected: Pass

- [ ] **Step 5: Commit**

```bash
git add webnovel-writer/scripts/data_modules/event_projection_router.py \
        webnovel-writer/scripts/data_modules/tests/test_event_projection_router.py \
        webnovel-writer/scripts/data_modules/state_projection_writer.py \
        webnovel-writer/scripts/data_modules/index_projection_writer.py \
        webnovel-writer/scripts/data_modules/memory_projection_writer.py
git commit -m "feat: route accepted events into projection writers"
```

---

## Task 3: Expand `override_contracts` Into a Unified Override Ledger

**Files:**
- Create: `webnovel-writer/scripts/data_modules/amend_proposal_schema.py`
- Create: `webnovel-writer/scripts/data_modules/override_ledger_service.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_override_ledger_service.py`
- Modify: `webnovel-writer/scripts/data_modules/index_manager.py`
- Modify: `webnovel-writer/scripts/data_modules/index_debt_mixin.py`
- Modify: `webnovel-writer/scripts/data_modules/index_observability_mixin.py`

- [ ] **Step 1: Write ledger / amend proposal tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_override_ledger_service.py
from data_modules.override_ledger_service import AmendProposalTrigger, normalize_override_record


def test_normalize_override_record_sets_record_type():
    row = normalize_override_record(
        record_type="contract_override",
        field="core_tone",
        base_value="pressure before release",
        override_value="immediate eruption",
        source_level="chapter",
    )
    assert row["record_type"] == "contract_override"
    assert row["field"] == "core_tone"


def test_normalize_override_record_supports_amend_proposal():
    row = normalize_override_record(
        record_type="amend_proposal",
        field="world_rule",
        base_value="special power limited to once daily",
        override_value="uncontrolled special-power breakthrough",
        source_level="master",
    )
    assert row["record_type"] == "amend_proposal"


def test_world_rule_broken_generates_amend_proposal():
    trigger = AmendProposalTrigger()
    proposals = trigger.check(
        chapter=3,
        events=[
            {
                "event_id": "evt-001",
                "event_type": "world_rule_broken",
                "subject": "special power",
                "payload": {"field": "world_rule", "base_value": "once daily", "proposed_value": "brief uncontrolled breakthrough"},
            }
        ],
    )
    assert len(proposals) == 1
    assert proposals[0]["target_level"] == "master"
    assert proposals[0]["field"] == "world_rule"
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_override_ledger_service.py -q --no-cov`

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement ledger normalization and incremental migration**

```python
# webnovel-writer/scripts/data_modules/amend_proposal_schema.py
from pydantic import BaseModel


class AmendProposal(BaseModel):
    proposal_id: str
    chapter: int
    target_level: str
    field: str
    base_value: str
    proposed_value: str
    reason_tag: str

# webnovel-writer/scripts/data_modules/override_ledger_service.py
def normalize_override_record(*, record_type: str, field: str, base_value: str, override_value: str, source_level: str) -> dict:
    return {
        "record_type": record_type,
        "field": field,
        "base_value": base_value,
        "override_value": override_value,
        "source_level": source_level,
    }


class AmendProposalTrigger:
    RULES = {
        "world_rule_broken": {"target_level": "master", "reason_tag": "world_rule_broken"},
        "relationship_changed": None,
        "power_breakthrough": None,
        "artifact_obtained": None,
    }

    def check(self, chapter: int, events: list[dict]) -> list[dict]:
        proposals: list[dict] = []
        for event in events:
            rule = self.RULES.get(event.get("event_type"))
            if not rule:
                continue
            payload = event.get("payload") or {}
            proposals.append(
                {
                    "proposal_id": f"amend-{chapter}-{event.get('event_id')}",
                    "chapter": chapter,
                    "target_level": rule["target_level"],
                    "field": payload.get("field", ""),
                    "base_value": payload.get("base_value", ""),
                    "proposed_value": payload.get("proposed_value", ""),
                    "reason_tag": rule["reason_tag"],
                }
            )
        return proposals


def persist_amend_proposals(conn, chapter: int, proposals: list[dict]) -> int:
    inserted = 0
    for proposal in proposals:
        row = normalize_override_record(
            record_type="amend_proposal",
            field=proposal["field"],
            base_value=proposal["base_value"],
            override_value=proposal["proposed_value"],
            source_level=proposal["target_level"],
        )
        conn.execute(
            """
            INSERT INTO override_contracts (
                chapter,
                record_type,
                field,
                base_value,
                override_value,
                source_level,
                reason_tag,
                rationale_type,
                rationale_text,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chapter,
                row["record_type"],
                row["field"],
                row["base_value"],
                row["override_value"],
                row["source_level"],
                proposal["reason_tag"],
                "story_amend_proposal",
                f"eventtrigger a contract-amendment proposal: {proposal['proposal_id']}",
                "pending",
            ),
        )
        inserted += 1
    return inserted
```

Add backward-compatible columns to `override_contracts` in `index_manager.py`:

```python
def ensure_override_ledger_columns(conn) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(override_contracts)").fetchall()}
    wanted = {
        "record_type": "TEXT DEFAULT 'soft_deviation'",
        "field": "TEXT DEFAULT ''",
        "base_value": "TEXT DEFAULT ''",
        "override_value": "TEXT DEFAULT ''",
        "source_level": "TEXT DEFAULT ''",
        "reason_tag": "TEXT DEFAULT ''",
    }
    for name, ddl in wanted.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE override_contracts ADD COLUMN {name} {ddl}")
```

Also add a complete invocation in the accepted branch of `chapter_commit_service.py`:

```python
if payload["meta"]["status"] == "accepted":
    proposals = AmendProposalTrigger().check(chapter, payload["accepted_events"])
    if proposals:
        with IndexManager(self.project_root)._get_conn() as conn:
            ensure_override_ledger_columns(conn)
            persist_amend_proposals(conn, chapter, proposals)
            conn.commit()
```

This completes the intermediate Phase 4 mainline: event → amend proposal → contract promotion after human confirmation.

- [ ] **Step 4: Rerun tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_override_ledger_service.py webnovel-writer/scripts/data_modules/tests/test_data_modules.py -q --no-cov`

Expected: Pass

- [ ] **Step 5: Commit**

```bash
git add webnovel-writer/scripts/data_modules/amend_proposal_schema.py \
        webnovel-writer/scripts/data_modules/override_ledger_service.py \
        webnovel-writer/scripts/data_modules/tests/test_override_ledger_service.py \
        webnovel-writer/scripts/data_modules/index_manager.py \
        webnovel-writer/scripts/data_modules/index_debt_mixin.py \
        webnovel-writer/scripts/data_modules/index_observability_mixin.py
git commit -m "feat: extend override contracts into story override ledger"
```

---

## Task 4: CLI / Dashboard / Documentation and Validation

**Files:**
- Create: `webnovel-writer/scripts/story_events.py`
- Modify: `webnovel-writer/scripts/data_modules/webnovel.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_event_log_store.py`
- Modify: `webnovel-writer/dashboard/app.py`
- Create: `docs/architecture/story-system-phase4.md`
- Modify: `README.md`
- Modify: `docs/architecture/overview.md`
- Modify: `docs/guides/commands.md`
- Modify: `docs/operations/operations.md`
- Modify: `docs/superpowers/README.md`

- [ ] **Step 1: Add CLI forwarding and read tests**

```python
def test_webnovel_story_events_forwards(monkeypatch, tmp_path):
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
    monkeypatch.setattr(sys, "argv", ["webnovel", "--project-root", str(project_root), "story-events", "--chapter", "3"])
    cli.main()
    assert called["script_name"] == "story_events.py"
```

Append a direct-read test to `test_event_log_store.py`:

```python
def test_story_events_cli_reads_chapter_file(tmp_path, monkeypatch, capsys):
    events_dir = tmp_path / ".story-system" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    (events_dir / "chapter_003.events.json").write_text(
        '[{"event_id":"evt-001","chapter":3,"event_type":"open_loop_created","subject":"three-year agreement","payload":{}}]',
        encoding="utf-8",
    )

    from story_events import main

    monkeypatch.setattr(sys, "argv", ["story_events", "--project-root", str(tmp_path), "--chapter", "3"])
    main()

    out = capsys.readouterr().out
    assert "open_loop_created" in out
```

- [ ] **Step 2: Expose the query entry point and update the dashboard**

Add to `webnovel.py`:

```python
# webnovel-writer/scripts/story_events.py
import json
import sqlite3
from pathlib import Path


def _events_file(project_root: Path, chapter: int) -> Path:
    return project_root / ".story-system" / "events" / f"chapter_{chapter:03d}.events.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Story events CLI")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--chapter", type=int, default=0)
    parser.add_argument("--health", action="store_true")
    args = parser.parse_args()
    project_root = Path(args.project_root)

    if args.health:
        db_path = project_root / ".webnovel" / "index.db"
        conn = sqlite3.connect(db_path)
        try:
            try:
                row_count = conn.execute("SELECT COUNT(*) FROM story_events").fetchone()[0]
            except sqlite3.OperationalError:
                row_count = 0
        finally:
            conn.close()
        file_count = len(list((project_root / ".story-system" / "events").glob("chapter_*.events.json")))
        print(json.dumps({"ok": row_count >= 0, "sqlite_rows": row_count, "event_files": file_count}, ensure_ascii=False))
        return

    if args.chapter:
        path = _events_file(project_root, args.chapter)
        events = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        print(json.dumps({"chapter": args.chapter, "events": events}, ensure_ascii=False))
        return

    db_path = project_root / ".webnovel" / "index.db"
    conn = sqlite3.connect(db_path)
    try:
        columns = ["event_id", "chapter", "event_type", "subject", "payload_json"]
        rows = conn.execute(
            "SELECT event_id, chapter, event_type, subject, payload_json FROM story_events ORDER BY chapter DESC, id DESC LIMIT 200"
        ).fetchall()
    finally:
        conn.close()
    print(json.dumps({"events": [dict(zip(columns, row)) for row in rows]}, ensure_ascii=False))

# webnovel-writer/scripts/data_modules/webnovel.py
p_story_events = sub.add_parser("story-events", help="forward to story_events.py")
p_story_events.add_argument("args", nargs=argparse.REMAINDER)
```

Add read-only endpoints to `dashboard/app.py` following the existing `_get_db()` + `_fetchall_safe()` pattern:

```python
@app.get("/api/story-events")
def list_story_events(chapter: Optional[int] = None, limit: int = 200):
    with closing(_get_db()) as conn:
        if chapter is not None:
            return _fetchall_safe(
                conn,
                "SELECT * FROM story_events WHERE chapter = ? ORDER BY id DESC LIMIT ?",
                (chapter, limit),
            )
        return _fetchall_safe(
            conn,
            "SELECT * FROM story_events ORDER BY chapter DESC, id DESC LIMIT ?",
            (limit,),
        )


@app.get("/api/story-events/health")
def story_event_health():
    with closing(_get_db()) as conn:
        event_rows = _fetchall_safe(conn, "SELECT COUNT(*) AS count FROM story_events")
        proposal_rows = _fetchall_safe(
            conn,
            "SELECT COUNT(*) AS count FROM override_contracts WHERE record_type = 'amend_proposal' AND status = 'pending'",
        )
        return {
            "story_events": event_rows[0]["count"] if event_rows else 0,
            "pending_amend_proposals": proposal_rows[0]["count"] if proposal_rows else 0,
        }
```

Add three minimal operational sections to `docs/operations/operations.md` in this round:

- `preflight`: check whether `.story-system/events/` exists and the `story_events` table can be queried
- `health`: run `webnovel story-events --health`
- `backup`: back up `.story-system/` and `.webnovel/index.db`

- [ ] **Step 3: Create documentation and run Phase 4 regression tests**

Run:

```bash
python -m pytest \
  webnovel-writer/scripts/data_modules/tests/test_story_event_schema.py \
  webnovel-writer/scripts/data_modules/tests/test_event_log_store.py \
  webnovel-writer/scripts/data_modules/tests/test_event_projection_router.py \
  webnovel-writer/scripts/data_modules/tests/test_override_ledger_service.py \
  webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py \
  -q --no-cov
```

Expected: All pass

- [ ] **Step 4: Final commit**

```bash
git add webnovel-writer/scripts/story_events.py \
        webnovel-writer/scripts/data_modules/webnovel.py \
        webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py \
        webnovel-writer/scripts/data_modules/tests/test_event_log_store.py \
        webnovel-writer/dashboard/app.py \
        README.md \
        docs/architecture/story-system-phase4.md \
        docs/architecture/overview.md \
        docs/guides/commands.md \
        docs/operations/operations.md \
        docs/superpowers/README.md
git commit -m "docs: document story system phase4 event log and override ledger"
```

---

## Spec Coverage Check

- `13.5 Phase 4: Unified event mainline`
  - canonical event log：Task 1
  - Stable event-to-projection mapping: Task 2
  - Event-to-amend-proposal trigger rules: Task 3

- `8.5 New role of the override ledger`
  - `soft_deviation / contract_override / amend_proposal`：Task 3

- `10.2 / 10.4`
  - Accepted-event persistence and amend proposals: Task 1 / Task 3

- `17.2 / 17.3`
  - dashboard / health / ops integration: Task 4

---

## Placeholder Scan

- No `TODO / TBD` placeholders
- The override ledger is not deferred to a future expansion
- No premature Phase 5 legacy-pipeline downgrade

---

## Next Plan

Only after Phase 4, proceed to:

1. `Phase 5 Legacy Downgrade`
