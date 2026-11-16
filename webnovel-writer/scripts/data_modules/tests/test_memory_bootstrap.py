#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from data_modules.config import DataModulesConfig
from data_modules.index_manager import EntityMeta, RelationshipMeta, StateChangeMeta, IndexManager
from data_modules.memory.bootstrap import bootstrap_from_index
from data_modules.memory.store import ScratchpadManager


def _cfg(tmp_path):
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    return cfg


def test_bootstrap_from_index_includes_state_changes_and_open_loops(tmp_path):
    cfg = _cfg(tmp_path)
    idx = IndexManager(cfg)
    idx.upsert_entity(
        EntityMeta(
            id="xiaoyan",
            type="character",
            canonical_name="Xiao Yan",
            current={"realm": "Dou Zhe"},
            first_appearance=1,
            last_appearance=2,
        )
    )
    idx.record_state_change(
        StateChangeMeta(
            entity_id="xiaoyan",
            field="realm",
            old_value="Dou Zhe",
            new_value="Dou Shi",
            reason="Breakthrough",
            chapter=3,
        )
    )
    idx.record_state_change(
        StateChangeMeta(
            entity_id="xiaoyan",
            field="realm",
            old_value="Dou Shi",
            new_value="Da Dou Shi",
            reason="Another breakthrough",
            chapter=8,
        )
    )
    idx.upsert_relationship(
        RelationshipMeta(
            from_entity="xiaoyan",
            to_entity="yaolao",
            type="mentor-student",
            description="Teaching skills",
            chapter=2,
        )
    )

    summaries_dir = cfg.webnovel_dir / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    (summaries_dir / "ch0008.md").write_text(
        "## Plot Summary\nContent\n\n## foreshadowing\n- three-year challenge\n- the origin of the mysterious jade pendant\n",
        encoding="utf-8",
    )

    result = bootstrap_from_index(cfg)
    assert result["items_created"] > 0
    assert result["categories"].get("character_state", 0) >= 2
    assert result["categories"].get("open_loop", 0) >= 2

    store = ScratchpadManager(cfg)
    active_realm = store.query(category="character_state", subject="xiaoyan", status="active")
    assert any(item.field == "realm" and item.value == "Da Dou Shi" for item in active_realm)
    outdated_realm = store.query(category="character_state", subject="xiaoyan", status="outdated")
    assert any(item.field == "realm" and item.value == "Dou Shi" for item in outdated_realm)
    loops = store.query(category="open_loop", status="active")
    assert any("three-year challenge" in item.value for item in loops)

