#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from data_modules.config import DataModulesConfig
from data_modules.memory.store import ScratchpadManager
from data_modules.memory.writer import MemoryWriter


def _cfg(tmp_path):
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    return cfg


def test_writer_stage2_mapping(tmp_path):
    cfg = _cfg(tmp_path)
    writer = MemoryWriter(cfg)
    result = {
        "entities_new": [{"suggested_id": "yaolao", "name": "Yao Lao", "type": "character", "tier": "major"}],
        "state_changes": [{"entity_id": "xiaoyan", "field": "realm", "old": "Dou Zhe", "new": "Dou Shi"}],
        "relationships_new": [{"from": "xiaoyan", "to": "yaolao", "type": "mentor-student", "description": "Accept apprentice"}],
        "chapter_meta": {"hook": {"content": "the three-year challenge approaches", "type": "mystery", "strength": "strong"}},
    }
    summary = writer.update_from_chapter_result(12, result)
    assert summary["items_added"] >= 4
    store = ScratchpadManager(cfg)
    chars = store.query(category="character_state", status="active")
    assert any(x.subject == "xiaoyan" and x.field == "realm" for x in chars)
    rels = store.query(category="relationship", status="active")
    assert any(x.subject == "xiaoyan" and x.field == "yaolao" for x in rels)


def test_writer_stage4_memory_facts_mapping(tmp_path):
    cfg = _cfg(tmp_path)
    writer = MemoryWriter(cfg)
    result = {
        "memory_facts": {
            "timeline_events": [{"event": "Xiao Yan leaves Skycloud Sect", "chapter": 100, "time_hint": "the eve of the three-year challenge"}],
            "world_rules": [{"rule": "nine realms in the cultivation system", "scope": "global", "domain": "cultivation system", "field": "realm divisions"}],
            "open_loops": [{"content": "three-year challenge", "status": "active", "urgency": 80}],
            "reader_promises": [{"content": "Nalan Yanran will appear", "type": "encounter", "target": "Nalan Yanran"}],
        }
    }
    summary = writer.update_from_chapter_result(100, result)
    assert summary["items_added"] >= 4
    store = ScratchpadManager(cfg)
    assert store.query(category="timeline", status="active")
    assert store.query(category="world_rule", status="active")
    assert store.query(category="open_loop", status="active")
    assert store.query(category="reader_promise", status="active")

