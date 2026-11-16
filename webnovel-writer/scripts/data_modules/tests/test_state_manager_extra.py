#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StateManager extra tests
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

from data_modules.state_manager import StateManager, EntityState
from data_modules.index_manager import IndexManager, EntityMeta
from project_locator import write_current_project_pointer


@pytest.fixture
def temp_project(tmp_path):
    from data_modules.config import DataModulesConfig
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    return cfg


def test_ensure_state_schema_and_progress(temp_project):
    # relationships as list should be migrated to structured_relationships
    state = {
        "relationships": [
            {"from_entity": "a", "to_entity": "b", "type": "mentor-student", "chapter": 1}
        ],
        "progress": {"current_chapter": "2", "total_words": "10"},
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    manager = StateManager(temp_project, enable_sqlite_sync=False)
    assert isinstance(manager._state.get("relationships"), dict)
    assert isinstance(manager._state.get("structured_relationships"), list)
    assert int(manager.get_current_chapter()) == 2

    manager.update_progress(3)
    assert manager.get_current_chapter() == 3


def test_add_update_entities_and_alias(temp_project):
    manager = StateManager(temp_project, enable_sqlite_sync=False)

    entity = EntityState(id="xiaoyan", name="Xiao Yan", type="character", tier="core", aliases=["Flame Emperor"])
    assert manager.add_entity(entity) is True
    assert manager.add_entity(entity) is False

    manager.update_entity("xiaoyan", {"current": {"realm": "Dou Shi"}})
    updated = manager.get_entity("xiaoyan")
    assert updated["current"]["realm"] == "Dou Shi"

    assert manager.get_entity_type("xiaoyan") == "character"
    assert manager.get_entity_type("missing") is None

    assert "xiaoyan" in manager.get_all_entities()
    assert "xiaoyan" in manager.get_entities_by_type("character")
    assert "xiaoyan" in manager.get_entities_by_tier("core")

    # unknown type update
    assert manager.update_entity("missing", {"current": {"realm": "Dou Zhe"}}, "character") is False


def test_update_entity_appearance_and_relationships(temp_project):
    manager = StateManager(temp_project, enable_sqlite_sync=False)
    manager.add_entity(EntityState(id="xiaoyan", name="Xiao Yan", type="character"))

    manager.update_entity_appearance("xiaoyan", 5, "character")
    entity = manager.get_entity("xiaoyan")
    assert entity.get("first_appearance") == 5
    assert entity.get("last_appearance") == 5

    # unknown entity should no-op
    manager.update_entity_appearance("missing", 3, "character")

    manager.add_relationship("xiaoyan", "yaolao", "mentor-student", "accept a disciple", 1)
    rels = manager.get_relationships("xiaoyan")
    assert len(rels) == 1


def test_disambiguation_and_save_state(temp_project):
    manager = StateManager(temp_project, enable_sqlite_sync=False)
    warnings = manager._record_disambiguation(
        1,
        [
            {
                "mention": "sect leader",
                "candidates": ["zongzhu", "lintian"],
                "suggested": "zongzhu",
                "confidence": 0.4,
            },
            {
                "mention": "Xiao Yan",
                "candidates": [{"type": "character", "id": "xiaoyan"}],
                "suggested": "xiaoyan",
                "confidence": 0.6,
            },
        ],
    )
    assert any("Disambiguation requires manual confirmation" in w for w in warnings)
    assert any("Disambiguation warning" in w for w in warnings)

    manager.save_state()
    assert temp_project.state_file.exists()


def test_save_state_no_pending(temp_project):
    manager = StateManager(temp_project, enable_sqlite_sync=False)
    manager.save_state()
    assert not temp_project.state_file.exists()


def test_save_state_with_sqlite_sync_and_protagonist(temp_project):
    manager = StateManager(temp_project)
    manager.add_entity(EntityState(id="xiaoyan", name="Xiao Yan", type="character", tier="core"))
    manager.update_entity("xiaoyan", {"current": {"realm": "Dou Shi", "location": "Skycloud Sect"}})
    manager.update_progress(10, words=500)
    manager.save_state()

    state = json.loads(temp_project.state_file.read_text(encoding="utf-8"))
    assert state.get("_migrated_to_sqlite") is True
    assert state.get("progress", {}).get("current_chapter") == 10

    # mark protagonist and synchronize
    idx = IndexManager(temp_project)
    idx.upsert_entity(
        EntityMeta(
            id="xiaoyan",
            type="character",
            canonical_name="Xiao Yan",
            tier="core",
            current={"realm": "Dou Wang", "location": "Skycloud Sect"},
            first_appearance=1,
            last_appearance=10,
            is_protagonist=True,
        ),
        update_metadata=True,
    )
    manager.sync_protagonist_from_entity()
    assert manager._state.get("protagonist_state", {}).get("power", {}).get("realm") == "Dou Wang"

    manager._state["protagonist_state"] = {
        "power": {"realm": "Combat Emperor", "layer": 2},
        "location": {"current": "Central Province"},
    }
    manager._state.setdefault("entities_v3", {"character": {}})
    manager._state["entities_v3"]["character"]["xiaoyan"] = {
        "canonical_name": "Xiao Yan",
        "tier": "core",
        "desc": "",
        "current": {"realm": "Dou Wang", "location": "Skycloud Sect"},
        "first_appearance": 1,
        "last_appearance": 10,
        "history": [],
    }
    manager.sync_protagonist_to_entity("xiaoyan")
    manager.save_state()
    updated = idx.get_entity("xiaoyan")
    assert updated["current_json"]["realm"] == "Combat Emperor"

    # export context
    exported = manager.export_for_context()
    assert exported.get("alias_index") == {}


def test_process_chapter_result_and_sqlite_sync(temp_project):
    manager = StateManager(temp_project)
    manager.add_entity(EntityState(id="xiaoyan", name="Xiao Yan", type="character", tier="core"))

    result = {
        "entities_appeared": [
            {"id": "xiaoyan", "type": "character", "mentions": ["Xiao Yan", "Young Yan"], "confidence": 0.9}
        ],
        "entities_new": [
            {
                "suggested_id": "yaolao",
                "name": "Yao Lao",
                "type": "character",
                "tier": "major",
                "mentions": ["Yao Lao"],
                "aliases": ["Yao Lao"],
            }
        ],
        "state_changes": [
            {"entity_id": "xiaoyan", "field": "realm", "old": "Dou Zhe", "new": "Dou Shi", "reason": "breakthrough"}
        ],
        "relationships_new": [
            {"from": "xiaoyan", "to": "yaolao", "type": "mentor-student", "description": "accept a disciple"}
        ],
        "uncertain": [
            {"mention": "sect leader", "candidates": ["zongzhu", "lintian"], "suggested": "zongzhu", "confidence": 0.2},
            {
                "mention": "Xiao Yan",
                "candidates": [{"type": "character", "id": "xiaoyan"}],
                "suggested": "xiaoyan",
                "confidence": 0.8,
                "adopted": True,
            },
        ],
        "chapter_meta": {"hook": "test", "end": "ok"},
        "memory_facts": {
            "timeline_events": [{"event": "Xiao Yan leaves Skycloud Sect", "chapter": 12, "time_hint": "night"}],
            "world_rules": [{"rule": "nine cultivation realms", "scope": "global", "domain": "cultivation system", "field": "realm tiers"}],
            "open_loops": [{"content": "three-year challenge", "status": "active", "urgency": 80}],
            "reader_promises": [{"content": "Nalan Yanran appears", "type": "encounter"}],
        },
    }
    warnings = manager.process_chapter_result(12, result)
    assert any("Disambiguation requires manual confirmation" in w for w in warnings)
    assert any("Disambiguation warning" in w for w in warnings)

    manager.save_state()

    idx = IndexManager(temp_project)
    assert idx.get_entity("yaolao") is not None
    assert idx.get_entity("Yao Lao")["id"] == "yaolao"
    assert idx.get_entity("Young Yan")["id"] == "xiaoyan"
    assert "Yao Lao" in idx.get_entity_aliases("yaolao")
    assert idx.get_relationship_between("xiaoyan", "yaolao")
    assert idx.get_entity_state_changes("xiaoyan")

    by_type = manager.get_entities_by_type("character")
    by_tier = manager.get_entities_by_tier("core")
    assert "xiaoyan" in by_type
    assert "xiaoyan" in by_tier
    assert temp_project.scratchpad_file.exists()


def test_export_context_and_protagonist_alias(temp_project):
    manager = StateManager(temp_project, enable_sqlite_sync=False)
    manager.add_entity(EntityState(id="xiaoyan", name="Xiao Yan", type="character", tier="core"))
    manager._state["disambiguation_warnings"] = [{"chapter": 1, "mention": "Xiao Yan"}]
    manager._state["disambiguation_pending"] = [{"chapter": 2, "mention": "sect leader"}]

    exported = manager.export_for_context()
    assert "xiaoyan" in exported.get("entities", {})
    assert exported["disambiguation"]["warnings"]
    assert exported["disambiguation"]["pending"]

    manager_sql = StateManager(temp_project)
    idx = IndexManager(temp_project)
    idx.upsert_entity(
        EntityMeta(
            id="xiaoyan",
            type="character",
            canonical_name="Xiao Yan",
            tier="core",
            current={},
            first_appearance=1,
            last_appearance=1,
            is_protagonist=False,
        ),
        update_metadata=True,
    )
    idx.register_alias("Young Yan", "xiaoyan", "character")
    manager_sql._state["protagonist_state"] = {"name": "Young Yan"}
    assert manager_sql.get_protagonist_entity_id() == "xiaoyan"

    idx.upsert_entity(
        EntityMeta(
            id="xiaoyan",
            type="character",
            canonical_name="Xiao Yan",
            tier="core",
            current={},
            first_appearance=1,
            last_appearance=1,
            is_protagonist=True,
        ),
        update_metadata=True,
    )
    assert manager_sql.get_protagonist_entity_id() == "xiaoyan"


def test_sqlite_metadata_update_and_alias_sync(temp_project):
    manager = StateManager(temp_project)
    idx = IndexManager(temp_project)
    idx.upsert_entity(
        EntityMeta(
            id="xiaoyan",
            type="character",
            canonical_name="Xiao Yan",
            tier="core",
            current={"realm": "Dou Zhe"},
            first_appearance=1,
            last_appearance=1,
            is_protagonist=False,
        )
    )

    manager._state.setdefault("entities_v3", {"character": {}})
    manager._state["entities_v3"]["character"]["xiaoyan"] = {
        "canonical_name": "Xiao Yan",
        "tier": "core",
        "desc": "",
        "current": {"realm": "Dou Zhe"},
        "first_appearance": 1,
        "last_appearance": 1,
        "history": [],
    }

    manager.update_entity(
        "xiaoyan",
        {"canonical_name": "Xiao Yan·new", "tier": "major", "current": {"realm": "Dou Wang"}},
        "character",
    )
    manager.update_entity("xiaoyan", {"location": "Central Province"}, "character")
    manager.update_entity_appearance("xiaoyan", 2, "character")
    manager._pending_alias_entries["Young Yan"] = [{"type": "character", "id": "xiaoyan"}]

    manager.save_state()

    updated = idx.get_entity("xiaoyan")
    assert updated["canonical_name"] == "Xiao Yan·new"
    assert updated["current_json"]["realm"] == "Dou Wang"
    assert updated["current_json"]["location"] == "Central Province"
    assert updated["last_appearance"] == 2

    aliases = idx.get_entity_aliases("xiaoyan")
    assert "Xiao Yan·new" in aliases
    assert "Young Yan" in aliases


def test_ensure_state_schema_invalid_inputs(temp_project):
    manager = StateManager(temp_project, enable_sqlite_sync=False)
    schema = manager._ensure_state_schema("bad")
    assert isinstance(schema, dict)

    schema2 = manager._ensure_state_schema({
        "progress": "bad",
        "relationships": "bad",
        "disambiguation_warnings": "bad",
        "disambiguation_pending": "bad",
    })
    assert isinstance(schema2["progress"], dict)
    assert isinstance(schema2["relationships"], dict)
    assert isinstance(schema2["disambiguation_warnings"], list)
    assert isinstance(schema2["disambiguation_pending"], list)


def test_save_state_preserves_sqlite_pending_on_sync_failure(temp_project):
    manager = StateManager(temp_project)

    manager.add_entity(EntityState(id="e1", name="Test Character", type="character", first_appearance=1, last_appearance=1))
    manager.update_entity("e1", {"current": {"realm": "qi-refining"}}, "character")

    class _BrokenSQLManager:
        def process_chapter_entities(self, **kwargs):
            raise RuntimeError("boom")

    manager._sql_state_manager = _BrokenSQLManager()
    manager._pending_sqlite_data["chapter"] = 1

    manager.save_state()

    state = json.loads(temp_project.state_file.read_text(encoding="utf-8"))
    assert state.get("_migrated_to_sqlite") is True

    # SQLite after synchronization failure，SQLite related pending must not be cleared，for later retries
    assert manager._pending_entity_patches
    assert manager._pending_sqlite_data.get("chapter") == 1


def test_save_state_progress_and_disambiguation_merge(temp_project):
    state = {
        "progress": {"current_chapter": "bad", "total_words": "bad"},
        "disambiguation_warnings": "bad",
        "disambiguation_pending": "bad",
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    manager = StateManager(temp_project, enable_sqlite_sync=False)
    manager.config.max_disambiguation_warnings = 1
    manager.config.max_disambiguation_pending = 1
    manager._pending_progress_chapter = 5
    manager._pending_progress_words_delta = 10
    manager._pending_disambiguation_warnings = [
        {"chapter": 1, "mention": "a", "chosen_id": "x", "confidence": 0.5},
        {"chapter": 1, "mention": "a", "chosen_id": "x", "confidence": 0.5},
        "bad",
    ]
    manager._pending_disambiguation_pending = [
        {"chapter": 2, "mention": "b", "suggested_id": "y", "confidence": 0.4},
        {"chapter": 2, "mention": "b", "suggested_id": "y", "confidence": 0.4},
        "bad",
    ]
    manager.save_state()

    saved = json.loads(temp_project.state_file.read_text(encoding="utf-8"))
    assert saved["progress"]["current_chapter"] == 5
    assert saved["progress"]["total_words"] == 10
    assert len(saved["disambiguation_warnings"]) == 1
    assert len(saved["disambiguation_pending"]) == 1


def test_set_chapter_status_preserves_existing_disk_state(temp_project):
    temp_project.state_file.write_text(
        json.dumps({"progress": {"current_chapter": 4}}, ensure_ascii=False),
        encoding="utf-8",
    )

    manager = StateManager(temp_project, enable_sqlite_sync=False)

    external_state = {
        "progress": {
            "current_chapter": 8,
            "chapter_status": {"3": "chapter_committed"},
        },
        "disambiguation_warnings": [{"chapter": 4, "mention": "sect leader"}],
    }
    temp_project.state_file.write_text(
        json.dumps(external_state, ensure_ascii=False),
        encoding="utf-8",
    )

    manager.set_chapter_status(5, "chapter_drafted")

    saved = json.loads(temp_project.state_file.read_text(encoding="utf-8"))
    assert saved["progress"]["current_chapter"] == 8
    assert saved["progress"]["chapter_status"]["3"] == "chapter_committed"
    assert saved["progress"]["chapter_status"]["5"] == "chapter_drafted"
    assert saved["disambiguation_warnings"] == [{"chapter": 4, "mention": "sect leader"}]


def test_set_chapter_status_does_not_rollback_same_chapter_disk_state(temp_project):
    temp_project.state_file.write_text(
        json.dumps({"progress": {"chapter_status": {}}}, ensure_ascii=False),
        encoding="utf-8",
    )
    manager = StateManager(temp_project, enable_sqlite_sync=False)

    temp_project.state_file.write_text(
        json.dumps(
            {"progress": {"chapter_status": {"5": "chapter_reviewed"}}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    manager.set_chapter_status(5, "chapter_drafted")

    saved = json.loads(temp_project.state_file.read_text(encoding="utf-8"))
    assert saved["progress"]["chapter_status"]["5"] == "chapter_reviewed"
    assert manager.get_chapter_status(5) == "chapter_reviewed"


def test_sync_to_sqlite_exceptions_and_no_sql_manager(temp_project, monkeypatch):
    manager = StateManager(temp_project)
    manager._pending_progress_chapter = 1
    manager._pending_sqlite_data["chapter"] = 1
    manager._pending_alias_entries["alias"] = [{"type": "character", "id": "xiaoyan"}]

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(manager._sql_state_manager, "process_chapter_entities", boom)
    monkeypatch.setattr(manager._sql_state_manager, "register_alias", boom)

    manager.save_state()

    manager_no_sql = StateManager(temp_project, enable_sqlite_sync=False)
    manager_no_sql._sync_pending_patches_to_sqlite()


def test_entity_fallbacks_and_updates(temp_project):
    manager = StateManager(temp_project, enable_sqlite_sync=False)

    manager.add_entity(EntityState(id="hero", name="protagonist", type="unknown", tier="core"))
    manager.add_entity(EntityState(id="place", name="Wutan City", type="location", tier="major"))

    assert manager.get_entity("hero", "character")["canonical_name"] == "protagonist"
    assert manager.get_entity("place")["canonical_name"] == "Wutan City"
    assert manager.get_entity_type("place") == "location"

    assert "hero" in manager.get_entities_by_type("character")
    assert "hero" in manager.get_entities_by_tier("core")
    assert "hero" in manager.get_all_entities()

    assert manager.update_entity("missing", {"current": {"a": 1}}) is False

    manager.update_entity("hero", {"attributes": {"hp": 1}}, "character")
    manager._state["entities_v3"]["character"]["hero"].pop("current", None)
    manager.update_entity("hero", {"current": {"mp": 2}}, "character")
    manager.update_entity("hero", {"tier": "major"}, "character")

    manager._state["entities_v3"] = "bad"
    manager.update_entity_appearance("hero", 1, "character")
    manager._state["entities_v3"]["character"]["hero"] = {"first_appearance": 0, "last_appearance": 0}
    manager.update_entity_appearance("hero", 1, "character")
    manager.update_entity_appearance("hero", 2, "character")


def test_register_alias_internal_and_get_all_entities_sqlite(temp_project):
    manager = StateManager(temp_project)
    manager._register_alias_internal("xiaoyan", "character", "")
    manager._register_alias_internal("xiaoyan", "character", "Xiao Yan")

    idx = IndexManager(temp_project)
    idx.upsert_entity(
        EntityMeta(
            id="xiaoyan",
            type="character",
            canonical_name="Xiao Yan",
            tier="core",
            current={},
            first_appearance=1,
            last_appearance=1,
            is_protagonist=False,
        )
    )
    all_entities = manager.get_all_entities()
    assert "xiaoyan" in all_entities


def test_record_disambiguation_and_process_chapter_existing(temp_project):
    manager = StateManager(temp_project, enable_sqlite_sync=False)
    warnings = manager._record_disambiguation(
        1,
        [
            "bad",
            {"mention": "", "confidence": 0.1},
            {"mention": "sect leader", "confidence": "bad", "adopted": "zongzhu"},
        ],
    )
    assert warnings

    manager.add_entity(EntityState(id="xiaoyan", name="Xiao Yan", type="character"))
    warnings = manager.process_chapter_result(2, {"entities_new": [{"id": "xiaoyan", "name": "Xiao Yan"}]})
    assert any("Entity already exists" in w for w in warnings)


def test_sync_protagonist_from_string_and_empty_updates(temp_project):
    manager = StateManager(temp_project, enable_sqlite_sync=False)
    manager._state.setdefault("entities_v3", {"character": {}})
    manager._state["entities_v3"]["character"]["bad"] = {
        "current": None,
        "current_json": "not-json",
    }
    manager._state["entities_v3"]["character"]["hero"] = {
        "current": None,
        "current_json": json.dumps({"realm": "Dou Shi", "layer": 2, "location": "Wutan City", "last_chapter": 3}),
    }
    manager.sync_protagonist_from_entity("bad")
    manager.sync_protagonist_from_entity("hero")
    assert manager._state["protagonist_state"]["power"]["realm"] == "Dou Shi"

    manager._state["protagonist_state"] = {}
    manager.sync_protagonist_to_entity()


def test_state_manager_cli_commands(temp_project, monkeypatch, capsys):
    # CLI of resolve_project_root requires state.json exists
    if not temp_project.state_file.exists():
        temp_project.state_file.write_text("{}", encoding="utf-8")

    idx = IndexManager(temp_project)
    idx.upsert_entity(
        EntityMeta(
            id="xiaoyan",
            type="character",
            canonical_name="Xiao Yan",
            tier="core",
            current={},
            first_appearance=1,
            last_appearance=1,
            is_protagonist=False,
        )
    )

    def run_cli(args):
        monkeypatch.setattr(sys, "argv", args)
        from data_modules import state_manager as sm

        sm.main()
        out = capsys.readouterr().out
        return json.loads(out)

    out = run_cli(["state_manager", "--project-root", str(temp_project.project_root), "get-progress"])
    assert out["status"] == "success"
    assert "current_chapter" in out.get("data", {})

    out = run_cli(["state_manager", "--project-root", str(temp_project.project_root), "get-entity", "--id", "missing"])
    assert out["status"] == "error"

    out = run_cli(["state_manager", "--project-root", str(temp_project.project_root), "get-entity", "--id", "xiaoyan"])
    assert out["status"] == "success"
    assert out["data"].get("id") == "xiaoyan"

    out = run_cli(["state_manager", "--project-root", str(temp_project.project_root), "list-entities", "--type", "character"])
    assert out["status"] == "success"
    assert any(e.get("id") == "xiaoyan" for e in out.get("data", []))

    out = run_cli(["state_manager", "--project-root", str(temp_project.project_root), "list-entities", "--tier", "core"])
    assert out["status"] == "success"
    assert any(e.get("id") == "xiaoyan" for e in out.get("data", []))

    payload = json.dumps({"entities_appeared": [], "entities_new": [], "state_changes": [], "relationships_new": []})
    out = run_cli([
        "state_manager",
        "--project-root",
        str(temp_project.project_root),
        "process-chapter",
        "--chapter",
        "1",
        "--data",
        payload,
    ])
    assert out["status"] == "success"


def test_process_chapter_cli_fails_when_sqlite_sync_fails(temp_project, monkeypatch, capsys):
    if not temp_project.state_file.exists():
        temp_project.state_file.write_text("{}", encoding="utf-8")

    from data_modules import state_manager as sm

    def fail_sync(self, processed_appearances=None):
        raise RuntimeError("sqlite sync boom")

    payload = json.dumps(
        {
            "entities_appeared": [],
            "entities_new": [],
            "state_changes": [],
            "relationships_new": [],
        }
    )
    monkeypatch.setattr(sm.StateManager, "_sync_pending_patches_to_sqlite", fail_sync)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "state_manager",
            "--project-root",
            str(temp_project.project_root),
            "process-chapter",
            "--chapter",
            "7",
            "--data",
            payload,
        ],
    )

    with pytest.raises(SystemExit) as exc:
        sm.main()

    assert int(exc.value.code or 0) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "error"
    assert out["error"]["code"] == "SQLITE_SYNC_FAILED"
    assert "webnovel.py projections retry --chapter 7" in out["error"]["suggestion"]


def test_state_manager_cli_rejects_json_file_outside_resolved_book_root(tmp_path, monkeypatch):
    from data_modules.config import DataModulesConfig

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".git").mkdir()
    (workspace / ".claude").mkdir()
    project_root = workspace / "book"
    cfg = DataModulesConfig.from_project_root(project_root)
    cfg.ensure_dirs()
    if not cfg.state_file.exists():
        cfg.state_file.write_text("{}", encoding="utf-8")
    write_current_project_pointer(project_root, workspace_root=workspace)

    outside = workspace / "outside.json"
    outside.write_text('{"entities_appeared": []}', encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "state_manager",
            "--project-root",
            str(workspace),
            "process-chapter",
            "--chapter",
            "1",
            "--data",
            f"@{outside}",
        ],
    )

    from data_modules import state_manager as sm

    with pytest.raises(ValueError, match="outside allowed directory"):
        sm.main()


def test_state_manager_cli_rejects_invalid_project_root(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("WEBNOVEL_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setenv("WEBNOVEL_CLAUDE_HOME", str(tmp_path / "empty-claude-home"))

    (tmp_path / ".git").mkdir(parents=True, exist_ok=True)
    invalid_root = tmp_path / "not-a-project"
    invalid_root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        sys,
        "argv",
        ["state_manager", "--project-root", str(invalid_root), "get-progress"],
    )

    from data_modules import state_manager as sm

    with pytest.raises(SystemExit) as exc:
        sm.main()
    out = json.loads(capsys.readouterr().out)
    assert int(exc.value.code or 0) == 1
    assert out["status"] == "error"
    assert out["error"]["code"] == "INVALID_PROJECT_ROOT"


def test_save_state_timeout(monkeypatch, temp_project):
    import filelock
    from data_modules import state_manager as sm

    manager = StateManager(temp_project, enable_sqlite_sync=False)
    manager.update_progress(1)

    class FakeLock:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            raise filelock.Timeout("timeout")

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(sm.filelock, "FileLock", FakeLock)
    with pytest.raises(RuntimeError):
        manager.save_state()
