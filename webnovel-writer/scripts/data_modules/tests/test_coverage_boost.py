#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coverage store CLI, compactor Boundary, cli_args Parse, webnovel Routing test coverage for。
"""

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

from data_modules.config import DataModulesConfig
from data_modules.memory.schema import MemoryItem, ScratchpadData, memory_item_key
from data_modules.memory.store import ScratchpadManager
from data_modules.memory.compactor import compact_scratchpad, _key_for, _is_resolved_open_loop
from data_modules.cli_args import normalize_global_project_root, load_json_arg, _extract_flag_value


# ── helpers ──────────────────────────────────────────────────────────────

def _cfg(tmp_path):
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    if not cfg.state_file.exists():
        cfg.state_file.write_text("{}", encoding="utf-8")
    return cfg


def _make_item(id, category="character_state", subject="x", field="f", value="v", chapter=1, **kw):
    return MemoryItem(
        id=id, layer="semantic", category=category,
        subject=subject, field=field, value=value,
        source_chapter=chapter, **kw,
    )


# ═══════════════════════════════════════════════════════════════════════
# 1. cli_args Coverage
# ═══════════════════════════════════════════════════════════════════════

def test_extract_flag_value_equals_form():
    value, rest = _extract_flag_value(["cmd", "--project-root=/my/path", "sub"], "--project-root")
    assert value == "/my/path"
    assert rest == ["cmd", "sub"]


def test_extract_flag_value_dangling_flag():
    value, rest = _extract_flag_value(["--project-root"], "--project-root")
    assert value is None
    assert rest == ["--project-root"]


def test_extract_flag_value_last_wins():
    value, rest = _extract_flag_value(
        ["--project-root", "first", "cmd", "--project-root", "second"],
        "--project-root",
    )
    assert value == "second"
    assert rest == ["cmd"]


def test_normalize_global_project_root_no_flag():
    argv = ["cmd", "--other", "val"]
    assert normalize_global_project_root(argv) is argv


def test_load_json_arg_from_file(tmp_path):
    f = tmp_path / "data.json"
    f.write_text('{"a":1}', encoding="utf-8")
    result = load_json_arg(f"@{f}")
    assert result == {"a": 1}


def test_load_json_arg_rejects_file_outside_base_dir(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "secret.json"
    outside.write_text('{"secret": true}', encoding="utf-8")

    with pytest.raises(ValueError, match="outside allowed directory"):
        load_json_arg(f"@{outside}", base_dir=project)


def test_load_json_arg_rejects_relative_escape_outside_base_dir(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    secret = outside_dir / "secret.json"
    secret.write_text('{"secret": true}', encoding="utf-8")

    with pytest.raises(ValueError, match="outside allowed directory"):
        load_json_arg("@../outside/secret.json", base_dir=project)


def test_load_json_arg_allows_file_inside_base_dir(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    payload = project / "payload.json"
    payload.write_text('{"ok": true}', encoding="utf-8")

    assert load_json_arg(f"@{payload}", base_dir=project) == {"ok": True}


def test_load_json_arg_stdin_ignores_base_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "stdin", StringIO('{"stdin": true}'))

    assert load_json_arg("@-", base_dir=tmp_path) == {"stdin": True}


def test_load_json_arg_from_stdin(monkeypatch):
    monkeypatch.setattr(sys, "stdin", StringIO('{"b":2}'))
    result = load_json_arg("@-")
    assert result == {"b": 2}


def test_load_json_arg_empty_at_raises():
    with pytest.raises(ValueError, match="without path"):
        load_json_arg("@")


def test_load_json_arg_none_raises():
    with pytest.raises(ValueError, match="missing"):
        load_json_arg(None)


# ═══════════════════════════════════════════════════════════════════════
# 2. compactor Boundary coverage
# ═══════════════════════════════════════════════════════════════════════

def test_key_for_unknown_category_falls_back_to_id():
    item = _make_item("x1", category="unknown_cat")
    assert _key_for(item) == ("x1",)


def test_is_resolved_open_loop_various_statuses():
    base = dict(id="ol1", layer="semantic", category="open_loop", subject="x", field="status", value="x", source_chapter=1)
    assert _is_resolved_open_loop(MemoryItem(**base, payload={"status": "resolved"})) is True
    assert _is_resolved_open_loop(MemoryItem(**base, payload={"status": "payoff"})) is True
    assert _is_resolved_open_loop(MemoryItem(**base, payload={"status": "active"})) is False
    assert _is_resolved_open_loop(MemoryItem(**base, payload=None)) is False

    non_loop = _make_item("cs1", category="character_state")
    assert _is_resolved_open_loop(non_loop) is False


def test_compactor_dedup_outdated_keeps_latest():
    """Step1: samekeyofoutdatedretain only the newest entry。"""
    data = ScratchpadData.empty()
    # 3 items: 2 outdated (samekey) + 1 active → dedupbecomes afterward2 items, <= max_items=3
    data.character_state = [
        _make_item("a1", subject="x", field="realm", value="v1", status="outdated", updated_at="2026-01-01T00:00:00"),
        _make_item("a2", subject="x", field="realm", value="v2", status="outdated", updated_at="2026-02-01T00:00:00"),
        _make_item("a3", subject="x", field="realm", value="v3", status="active"),
    ]
    # require1extraitembring the total to=4 > max_items=3，trigger the compaction entry point
    data.world_rules.append(_make_item("wr0", category="world_rule", subject="r0", field="f0", value="v0", chapter=1))
    result = compact_scratchpad(data, max_items=3)
    outdated = [r for r in result.character_state if r.status == "outdated"]
    # dedupremovea1，retaina2 (Update)，total after compaction=3 (a2+a3+wr0)exactly <= max_items
    assert len(outdated) == 1
    assert outdated[0].value == "v2"


def test_compactor_cleans_resolved_open_loops():
    """Step2: alreadyresolvedofopen_loopremoved。"""
    data = ScratchpadData.empty()
    data.open_loops = [
        _make_item("ol1", category="open_loop", subject="foreshadowingA", field="status", value="A", payload={"status": "resolved"}),
        _make_item("ol2", category="open_loop", subject="foreshadowingB", field="status", value="B", payload={"status": "active"}),
    ]
    # add2filler entries to bring the total to=4 > max_items=3
    data.world_rules.append(_make_item("wr0", category="world_rule", subject="r0", field="f0", value="v0", chapter=1))
    data.world_rules.append(_make_item("wr1", category="world_rule", subject="r1", field="f1", value="v1", chapter=1))
    result = compact_scratchpad(data, max_items=3)
    loop_subjects = [r.subject for r in result.open_loops]
    assert "foreshadowingA" not in loop_subjects
    assert "foreshadowingB" in loop_subjects


def test_compactor_replaces_existing_timeline_summary():
    """Step3oftimeline summaryretain only one，even iffieldvalue changes with chapter。"""
    data = ScratchpadData.empty()
    # pre-existing summary with old field value
    data.story_facts = [
        _make_item("sf-old", category="story_fact", subject="timeline_summary", field="<=ch5", value="Old summary"),
    ]
    # old timeline entries (>50 chapters from latest)
    for i in range(3):
        data.timeline.append(_make_item(f"t-old-{i}", category="timeline", subject=f"Old event{i}", field="event", value=f"Old event{i}", chapter=i+1))
    # fresh timeline
    data.timeline.append(_make_item("t-fresh", category="timeline", subject="New event", field="event", value="New event", chapter=60))

    # max_items Set sufficiently high，let step 4 without truncation，Test only step 3 replacement logic
    result = compact_scratchpad(data, max_items=4)
    summaries = [r for r in result.story_facts if r.subject == "timeline_summary"]
    # old summary (field="<=ch5") should be replaced by the new summary (field="<=ch3") replace，instead of coexistence
    assert len(summaries) == 1
    assert "Old event" in summaries[0].value
    assert summaries[0].field != "<=ch5"  # oldfieldalready covered


def test_compactor_resolved_open_loop_integration(tmp_path):
    """Integration tests: compactorpassstore.save()correctly clears when triggeredresolved open_loop。"""
    cfg = _cfg(tmp_path)
    cfg.memory_compactor_enabled = True
    cfg.memory_compactor_threshold = 3
    manager = ScratchpadManager(cfg)

    # Insert oneresolved open_loop
    manager.upsert_item(_make_item("ol-resolved", category="open_loop", subject="Resolved foreshadowing",
                                   field="status", value="Resolved foreshadowing", payload={"status": "resolved"}))
    # Insert oneactive open_loop
    manager.upsert_item(_make_item("ol-active", category="open_loop", subject="Unresolved foreshadowing",
                                   field="status", value="Unresolved foreshadowing", payload={"status": "active"}))
    # Insert additional entries to exceed the total limitthresholdTriggercompaction
    manager.upsert_item(_make_item("w1", category="world_rule", subject="r1", field="f1", value="v1"))
    manager.upsert_item(_make_item("w2", category="world_rule", subject="r2", field="f2", value="v2"))

    data = manager.load()
    loop_subjects = [r.subject for r in data.open_loops]
    assert "Resolved foreshadowing" not in loop_subjects
    assert "Unresolved foreshadowing" in loop_subjects


def test_memory_item_key_shared_function():
    """Verify schema.memory_item_key and compactor._key_for / store._key_for consistent。"""
    item = _make_item("x1", category="character_state", subject="hero", field="realm")
    assert memory_item_key(item) == ("hero", "realm")
    assert _key_for(item) == memory_item_key(item)

    mgr_key = ScratchpadManager.__new__(ScratchpadManager)
    # _key_for is instance method, call directly
    assert ScratchpadManager._key_for(mgr_key, item) == memory_item_key(item)

    unknown = _make_item("u1", category="unknown_category")
    assert memory_item_key(unknown) == ("u1",)


# ═══════════════════════════════════════════════════════════════════════
# 3. store CLI Coverage
# ═══════════════════════════════════════════════════════════════════════

def test_store_cli_stats(tmp_path, monkeypatch, capsys):
    cfg = _cfg(tmp_path)
    manager = ScratchpadManager(cfg)
    manager.upsert_item(_make_item("c1"))

    monkeypatch.setattr(sys, "argv", ["store", "--project-root", str(tmp_path), "stats"])
    from data_modules.memory import store as store_module
    store_module.main()
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    assert out["data"]["total"] >= 1


def test_store_cli_dump(tmp_path, monkeypatch, capsys):
    cfg = _cfg(tmp_path)
    manager = ScratchpadManager(cfg)
    manager.upsert_item(_make_item("c1"))

    monkeypatch.setattr(sys, "argv", ["store", "--project-root", str(tmp_path), "dump"])
    from data_modules.memory import store as store_module
    store_module.main()
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"


def test_store_cli_conflicts(tmp_path, monkeypatch, capsys):
    cfg = _cfg(tmp_path)
    monkeypatch.setattr(sys, "argv", ["store", "--project-root", str(tmp_path), "conflicts"])
    from data_modules.memory import store as store_module
    store_module.main()
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"


def test_store_cli_query(tmp_path, monkeypatch, capsys):
    cfg = _cfg(tmp_path)
    manager = ScratchpadManager(cfg)
    manager.upsert_item(_make_item("c1", subject="hero", field="realm", value="Dou Zhe"))

    monkeypatch.setattr(sys, "argv", [
        "store", "--project-root", str(tmp_path),
        "query", "--category", "character_state", "--subject", "hero",
    ])
    from data_modules.memory import store as store_module
    store_module.main()
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    assert len(out["data"]) >= 1


def test_store_cli_update(tmp_path, monkeypatch, capsys):
    cfg = _cfg(tmp_path)
    payload = json.dumps({
        "state_changes": [{"entity_id": "hero", "field": "realm", "old": "Dou Zhe", "new": "Dou Shi"}],
    })
    monkeypatch.setattr(sys, "argv", [
        "store", "--project-root", str(tmp_path),
        "update", "--chapter", "5", "--data", payload,
    ])
    from data_modules.memory import store as store_module
    store_module.main()
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    assert out["data"]["items_added"] >= 0


# ═══════════════════════════════════════════════════════════════════════
# 4. webnovel Routing coverage
# ═══════════════════════════════════════════════════════════════════════

def _load_webnovel_module():
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import data_modules.webnovel as webnovel_module
    return webnovel_module


def test_webnovel_cmd_where(monkeypatch, tmp_path, capsys):
    module = _load_webnovel_module()
    book_root = tmp_path / "book"
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: book_root)
    monkeypatch.setattr(sys, "argv", ["webnovel", "where"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert str(book_root) in capsys.readouterr().out


def test_webnovel_passthrough_state(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    book_root = tmp_path / "book"
    called = {}

    def _fake_resolve(_=None):
        return book_root

    def _fake_run(mod_name, argv):
        called["mod"] = mod_name
        called["argv"] = list(argv)
        return 0

    monkeypatch.setattr(module, "_resolve_root", _fake_resolve)
    monkeypatch.setattr(module, "_run_data_module", _fake_run)
    monkeypatch.setattr(sys, "argv", ["webnovel", "state", "get-progress"])

    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["mod"] == "state_manager"
    assert "--project-root" in called["argv"]
    assert "get-progress" in called["argv"]


def test_webnovel_passthrough_memory(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    book_root = tmp_path / "book"
    called = {}

    monkeypatch.setattr(module, "_resolve_root", lambda _=None: book_root)
    monkeypatch.setattr(module, "_run_data_module", lambda m, a: (called.update(mod=m, argv=list(a)), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "memory", "stats"])

    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["mod"] == "memory.store"


def test_webnovel_strip_project_root_args():
    module = _load_webnovel_module()
    result = module._strip_project_root_args(["--project-root", "/a", "cmd", "--project-root=/b", "--other"])
    assert result == ["cmd", "--other"]


def test_webnovel_passthrough_rag(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    book_root = tmp_path / "book"
    called = {}
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: book_root)
    monkeypatch.setattr(module, "_run_data_module", lambda m, a: (called.update(mod=m), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "rag", "search", "--query", "test"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["mod"] == "rag_adapter"


def test_webnovel_passthrough_style(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    book_root = tmp_path / "book"
    called = {}
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: book_root)
    monkeypatch.setattr(module, "_run_data_module", lambda m, a: (called.update(mod=m), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "style", "list"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["mod"] == "style_sampler"


def test_webnovel_passthrough_entity(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    called = {}
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: tmp_path)
    monkeypatch.setattr(module, "_run_data_module", lambda m, a: (called.update(mod=m), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "entity", "process"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["mod"] == "entity_linker"


def test_webnovel_passthrough_context(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    called = {}
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: tmp_path)
    monkeypatch.setattr(module, "_run_data_module", lambda m, a: (called.update(mod=m), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "context", "build"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["mod"] == "context_manager"


def test_webnovel_passthrough_migrate(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    called = {}
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: tmp_path)
    monkeypatch.setattr(module, "_run_data_module", lambda m, a: (called.update(mod=m), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "migrate"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["mod"] == "migrate_state_to_sqlite"


def test_webnovel_passthrough_status_script(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    called = {}
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: tmp_path)
    monkeypatch.setattr(module, "_run_script", lambda s, a: (called.update(script=s), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "status"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["script"] == "status_reporter.py"


def test_webnovel_passthrough_update_state_script(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    called = {}
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: tmp_path)
    monkeypatch.setattr(module, "_run_script", lambda s, a: (called.update(script=s), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "update-state", "add-review"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["script"] == "update_state.py"


def test_webnovel_passthrough_backup_script(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    called = {}
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: tmp_path)
    monkeypatch.setattr(module, "_run_script", lambda s, a: (called.update(script=s), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "backup"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["script"] == "backup_manager.py"


def test_webnovel_passthrough_archive_script(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    called = {}
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: tmp_path)
    monkeypatch.setattr(module, "_run_script", lambda s, a: (called.update(script=s), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "archive"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert called["script"] == "archive_manager.py"


def test_webnovel_remainder_strips_leading_double_dash(monkeypatch, tmp_path):
    module = _load_webnovel_module()
    called = {}
    monkeypatch.setattr(module, "_resolve_root", lambda _=None: tmp_path)
    monkeypatch.setattr(module, "_run_data_module", lambda m, a: (called.update(argv=list(a)), 0)[1])
    monkeypatch.setattr(sys, "argv", ["webnovel", "index", "--", "get-core-entities"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    assert "get-core-entities" in called["argv"]
    assert "--" not in called["argv"]


def test_webnovel_cmd_use(monkeypatch, tmp_path, capsys):
    module = _load_webnovel_module()
    book_root = tmp_path / "book"
    (book_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (book_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(module, "write_current_project_pointer", lambda pr, workspace_root=None: None)
    monkeypatch.setattr(module, "update_global_registry_current_project", lambda workspace_root=None, project_root=None: None)
    monkeypatch.setattr(sys, "argv", ["webnovel", "use", str(book_root)])

    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    out = capsys.readouterr().out
    assert "pointer" in out.lower() or "skipped" in out.lower()


def test_webnovel_cmd_use_with_workspace_root(monkeypatch, tmp_path, capsys):
    module = _load_webnovel_module()
    book_root = tmp_path / "book"
    workspace_root = tmp_path / "ws"

    pointer_path = tmp_path / "pointer.txt"
    reg_path = tmp_path / "registry.json"

    monkeypatch.setattr(module, "write_current_project_pointer", lambda pr, workspace_root=None: pointer_path)
    monkeypatch.setattr(module, "update_global_registry_current_project", lambda workspace_root=None, project_root=None: reg_path)
    monkeypatch.setattr(sys, "argv", ["webnovel", "use", str(book_root), "--workspace-root", str(workspace_root)])

    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    out = capsys.readouterr().out
    assert str(pointer_path) in out
    assert str(reg_path) in out


def test_webnovel_run_script_missing_script():
    module = _load_webnovel_module()
    with pytest.raises(FileNotFoundError, match="Script not found"):
        module._run_script("nonexistent_script_xyz.py", [])


def test_webnovel_run_data_module_no_main():
    module = _load_webnovel_module()
    with pytest.raises(RuntimeError, match="has no callable main"):
        module._run_data_module("schemas", [])  # schemas without main()


def test_webnovel_preflight_json_format(monkeypatch, tmp_path, capsys):
    module = _load_webnovel_module()
    project_root = tmp_path / "book"
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["webnovel", "--project-root", str(project_root), "preflight", "--format", "json"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert int(exc.value.code or 0) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True or result["ok"] is False
    assert "checks" in result


def test_webnovel_resolve_root_fallback(monkeypatch):
    module = _load_webnovel_module()
    # _resolve_root with None should call resolve_project_root() without args
    called = {}
    monkeypatch.setattr(module, "resolve_project_root", lambda *a, **kw: (called.update(args=a), Path("/fake"))[1])
    result = module._resolve_root(None)
    assert result == Path("/fake")
    assert called["args"] == ()

