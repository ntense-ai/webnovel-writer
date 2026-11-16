#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schema compatibility tests：protect the projector under LLM (DeepSeek v4pro) actual output schema behavior under。

background：data-agent.md the prompt specifies `{"field": "realm", "new": "..."}`，
but LLM actual output `{"field_path": "physical.condition", "new_value": "..."}`，
entity_deltas use `entity_type` instead of `type`，open_loop_created event payload absent `content`
but contains `description/loop_type/unanswered_question`。

these tests use real DeepSeek v4pro output format as fixture，ensure the projector accepts old and new forms schema。
"""

import json

from data_modules.config import DataModulesConfig
from data_modules.memory.store import ScratchpadManager
from data_modules.memory_projection_writer import MemoryProjectionWriter
from data_modules.state_projection_writer import StateProjectionWriter
from data_modules.vector_projection_writer import VectorProjectionWriter


# ============================================================
# state_projection_writer：accept field_path / new_value
# ============================================================


def test_state_writer_accepts_field_path_alias(tmp_path):
    (tmp_path / ".webnovel").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")
    writer = StateProjectionWriter(tmp_path)

    writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 2},
            "state_deltas": [
                {
                    "entity_id": "luming",
                    "field_path": "physical.condition",
                    "old_value": "weak",
                    "new_value": "weak（ongoing）",
                    "change_type": "confirmed",
                }
            ],
        }
    )

    payload = json.loads((tmp_path / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    luming = payload["entity_state"]["luming"]
    # expand dotted paths into nested dictionaries
    assert luming["physical"]["condition"] == "weak（ongoing）"


def test_state_writer_accepts_flat_field_legacy(tmp_path):
    """existing schema field/new must keep working（backward compatible）。"""
    (tmp_path / ".webnovel").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")
    writer = StateProjectionWriter(tmp_path)

    writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 3},
            "state_deltas": [{"entity_id": "x", "field": "realm", "new": "Dou Shi"}],
        }
    )

    payload = json.loads((tmp_path / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    assert payload["entity_state"]["x"]["realm"] == "Dou Shi"


def test_state_writer_handles_array_value_in_field_path(tmp_path):
    (tmp_path / ".webnovel").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")
    writer = StateProjectionWriter(tmp_path)

    writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 2},
            "state_deltas": [
                {
                    "entity_id": "luming",
                    "field_path": "relationships.acquaintances",
                    "old_value": [],
                    "new_value": [
                        {"entity_id": "liu_dazhu", "type": "fellow servant sharing the room"},
                        {"entity_id": "sun_wang", "type": "fellow servant sharing the room"},
                    ],
                    "change_type": "initialize",
                }
            ],
        }
    )

    payload = json.loads((tmp_path / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    acquaintances = payload["entity_state"]["luming"]["relationships"]["acquaintances"]
    assert len(acquaintances) == 2
    assert acquaintances[0]["entity_id"] == "liu_dazhu"


def test_state_writer_mirrors_protagonist_state_when_entity_is_protagonist(tmp_path):
    """of the protagonist entity state_delta should synchronize to state.json:protagonist_state，keep the old read path available。"""
    (tmp_path / ".webnovel").mkdir(parents=True, exist_ok=True)
    initial = {
        "protagonist_state": {
            "name": "Lu Ming",
            "power": {"realm": "", "layer": 1},
            "location": {"current": "", "last_chapter": 0},
            "golden_finger": {"name": "transmigrator knowledge", "level": 1, "cooldown": 0, "skills": []},
            "attributes": {},
        }
    }
    (tmp_path / ".webnovel" / "state.json").write_text(json.dumps(initial), encoding="utf-8")
    writer = StateProjectionWriter(tmp_path)

    writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 2},
            "state_deltas": [
                {"entity_id": "luming", "field_path": "power.realm", "new_value": "Qi Refining Level Five"},
                {
                    "entity_id": "luming",
                    "field_path": "location.current",
                    "new_value": "Azure Sect servants' courtyard",
                },
            ],
            "entity_deltas": [
                {
                    "entity_id": "luming",
                    "canonical_name": "Lu Ming",
                    "entity_type": "character",
                    "tier": "core",
                    "is_protagonist": True,
                }
            ],
        }
    )

    payload = json.loads((tmp_path / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    assert payload["protagonist_state"]["power"]["realm"] == "Qi Refining Level Five"
    assert payload["protagonist_state"]["location"]["current"] == "Azure Sect servants' courtyard"
    # name must not be affected by delta writeback overwrites
    assert payload["protagonist_state"]["name"] == "Lu Ming"


def test_state_writer_recognizes_protagonist_via_tier_zhujue(tmp_path):
    """actual LLM use tier='protagonist' annotate，rather than is_protagonist=True。"""
    (tmp_path / ".webnovel").mkdir(parents=True, exist_ok=True)
    initial = {
        "protagonist_state": {
            "name": "Lu Ming",
            "power": {"realm": "", "layer": 1},
        }
    }
    (tmp_path / ".webnovel" / "state.json").write_text(json.dumps(initial), encoding="utf-8")
    writer = StateProjectionWriter(tmp_path)

    writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 1},
            "state_deltas": [
                {"entity_id": "luming", "field_path": "power.realm", "new_value": "Qi Refining Level Five"},
            ],
            "entity_deltas": [
                {
                    "entity_id": "luming",
                    "canonical_name": "Lu Ming",
                    "entity_type": "character",
                    "tier": "protagonist",
                }
            ],
        }
    )

    payload = json.loads((tmp_path / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    assert payload["protagonist_state"]["power"]["realm"] == "Qi Refining Level Five"


def test_state_writer_recognizes_protagonist_via_canonical_name_match(tmp_path):
    """absent tier also absent is_protagonist when，match by name state.protagonist_state.name fallback。"""
    (tmp_path / ".webnovel").mkdir(parents=True, exist_ok=True)
    initial = {"protagonist_state": {"name": "Lu Ming", "power": {}}}
    (tmp_path / ".webnovel" / "state.json").write_text(json.dumps(initial), encoding="utf-8")
    writer = StateProjectionWriter(tmp_path)

    writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 1},
            "state_deltas": [
                {"entity_id": "luming", "field_path": "power.realm", "new_value": "Qi Refining Level Five"},
            ],
            "entity_deltas": [
                {"entity_id": "luming", "canonical_name": "Lu Ming", "entity_type": "character"}
            ],
        }
    )

    payload = json.loads((tmp_path / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    assert payload["protagonist_state"]["power"]["realm"] == "Qi Refining Level Five"


# ============================================================
# index_manager.apply_entity_delta：tier=protagonist / entity_type recognize
# ============================================================


def test_index_manager_marks_protagonist_via_tier_zhujue(tmp_path):
    """tier='protagonist' should automatically set is_protagonist=True，let get_protagonist can be found。"""
    from data_modules.index_manager import IndexManager

    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    manager = IndexManager(cfg)

    manager.apply_entity_delta(
        {
            "entity_id": "luming",
            "action": "upsert",
            "entity_type": "character",
            "tier": "protagonist",
            "chapter": 1,
            "payload": {"name": "Lu Ming"},
        }
    )

    protagonist = manager.get_protagonist()
    assert protagonist is not None, "tier=protagonist should be recognized as protagonist"
    assert protagonist["id"] == "luming"


def test_index_manager_preserves_entity_type_for_organization(tmp_path):
    """entity_deltas use entity_type='organization' when，in the index type must also be 'organization' rather than default 'character'。"""
    from data_modules.index_manager import IndexManager

    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    manager = IndexManager(cfg)

    manager.apply_entity_delta(
        {
            "entity_id": "qingyun_zong",
            "action": "upsert",
            "entity_type": "organization",
            "tier": "major",
            "chapter": 1,
            "payload": {"name": "Azure Sect"},
        }
    )

    entity = manager.get_entity("qingyun_zong")
    assert entity is not None
    assert entity["type"] == "organization", f"expected type=organization, got {entity['type']!r}"


def test_index_manager_uses_payload_name_when_canonical_name_missing(tmp_path):
    """LLM actual output often places the name in payload.name，rather than top-level canonical_name。"""
    from data_modules.index_manager import IndexManager

    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    manager = IndexManager(cfg)

    manager.apply_entity_delta(
        {
            "entity_id": "lu_ming",
            "action": "upsert",
            "entity_type": "character",
            "tier": "protagonist",
            "chapter": 1,
            "payload": {"name": "Lu Ming"},
        }
    )

    entity = manager.get_entity("lu_ming")
    assert entity is not None
    assert entity["canonical_name"] == "Lu Ming", (
        f"expected canonical_name=Lu Ming, got {entity['canonical_name']!r}"
    )


def test_index_manager_corrects_entity_type_on_re_upsert(tmp_path):
    """existing entity was misclassified by an old version as 'character' when，replay new commit must be able to type correct to 'organization' etc.。"""
    from data_modules.index_manager import IndexManager

    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    manager = IndexManager(cfg)

    # simulate old bug：first use type='character' persist（default fallback）
    manager.apply_entity_delta(
        {
            "entity_id": "qingyun_zong",
            "tier": "major",
            "chapter": 1,
            "payload": {"name": "Azure Sect"},
        }
    )
    entity = manager.get_entity("qingyun_zong")
    assert entity["type"] == "character"

    # repair and replay commit，explicitly pass entity_type='organization'
    manager.apply_entity_delta(
        {
            "entity_id": "qingyun_zong",
            "entity_type": "organization",
            "tier": "major",
            "chapter": 1,
            "payload": {"name": "Azure Sect"},
        }
    )
    entity = manager.get_entity("qingyun_zong")
    assert entity["type"] == "organization", f"expected type=organization after re-upsert, got {entity['type']!r}"


def test_index_manager_resolves_underscored_id_to_compact_entity(tmp_path):
    """entity registered as 'luming' when，query 'lu_ming' should also be found（LLM fallback for inconsistent naming）。"""
    from data_modules.index_manager import IndexManager

    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    manager = IndexManager(cfg)

    manager.apply_entity_delta(
        {
            "entity_id": "luming",
            "entity_type": "character",
            "tier": "protagonist",
            "chapter": 1,
            "payload": {"name": "Lu Ming"},
        }
    )

    # directly query — already works
    assert manager.get_entity("luming")["id"] == "luming"
    # reverse fallback — underscore variant
    found = manager.get_entity("lu_ming")
    assert found is not None, "lu_ming should resolve to luming"
    assert found["id"] == "luming"


# ============================================================
# memory_writer：accept entity_type / field_path / loop description
# ============================================================


def test_memory_writer_preserves_entity_type_for_organization(tmp_path):
    """entity_deltas use entity_type when the field，organization must not be misclassified as'character'。"""
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    writer = MemoryProjectionWriter(tmp_path)

    writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 1},
            "entity_deltas": [
                {
                    "entity_id": "qingyun_zong",
                    "action": "upsert",
                    "entity_type": "organization",
                    "tier": "major",
                    "payload": {"name": "Azure Sect"},
                }
            ],
            "state_deltas": [],
            "accepted_events": [],
        }
    )

    store = ScratchpadManager(cfg)
    chars = store.query(category="character_state", status="active")
    qingyun = [x for x in chars if x.subject == "qingyun_zong"]
    assert qingyun, "qingyun_zong entity should be recorded"
    assert qingyun[0].payload.get("type") == "organization", (
        f"expected type=organization, got {qingyun[0].payload.get('type')!r}"
    )


def test_memory_writer_accepts_field_path_in_state_delta(tmp_path):
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    writer = MemoryProjectionWriter(tmp_path)

    writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 2},
            "state_deltas": [
                {
                    "entity_id": "luming",
                    "field_path": "physical.condition",
                    "old_value": "weak",
                    "new_value": "weak（ongoing）",
                }
            ],
            "entity_deltas": [],
            "accepted_events": [],
        }
    )

    store = ScratchpadManager(cfg)
    chars = store.query(category="character_state", status="active")
    assert any(
        x.subject == "luming" and "physical" in x.field for x in chars
    ), [(x.subject, x.field) for x in chars]


def test_memory_writer_extracts_open_loop_from_description_when_no_content(tmp_path):
    """open_loop_created event payload absent content when，should come from description / unanswered_question take。"""
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    writer = MemoryProjectionWriter(tmp_path)

    writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 2},
            "state_deltas": [],
            "entity_deltas": [],
            "accepted_events": [
                {
                    "event_id": "evt_002",
                    "chapter": 2,
                    "event_type": "open_loop_created",
                    "subject": "luming",
                    "payload": {
                        "description": "Lu Ming discovers the promissory note'three copies'terms，mysterious guarantor identity",
                        "loop_type": "identity mystery",
                        "unanswered_question": "who is the guarantor？who brought the original host to sign the note？",
                        "narrative_weight": "major",
                    },
                }
            ],
        }
    )

    store = ScratchpadManager(cfg)
    loops = store.query(category="open_loop", status="active")
    assert loops, "open_loop should be recorded"
    # subject must contain meaningful suspense，must not be 'luming'（from event.subject fallback）
    contents = [x.subject for x in loops]
    assert any("guarantor" in c or "promissory note" in c or "identity" in c for c in contents), (
        f"expected meaningful loop content, got {contents}"
    )


def test_memory_writer_extracts_world_rule_from_rule_content(tmp_path):
    """world_rule_revealed event uses rule_content / description when，should fall into world_rule memory。"""
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    writer = MemoryProjectionWriter(tmp_path)

    writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 2},
            "state_deltas": [],
            "entity_deltas": [],
            "accepted_events": [
                {
                    "event_id": "evt_003",
                    "chapter": 2,
                    "event_type": "world_rule_revealed",
                    "subject": "luming",
                    "payload": {
                        "description": "three gaps in Azure City lending market",
                        "rule_category": "finance/economy",
                        "rule_content": "interest-rate monopoly、no credit system、violent debt collection",
                    },
                }
            ],
        }
    )

    store = ScratchpadManager(cfg)
    rules = store.query(category="world_rule", status="active")
    assert rules
    rule_texts = [x.value for x in rules]
    assert any("interest rate" in r or "credit" in r or "finance" in r or "lending" in r for r in rule_texts), (
        f"expected meaningful rule text, got {rule_texts}"
    )


# ============================================================
# vector_projection_writer：accept description / new_state
# ============================================================


def test_vector_writer_handles_character_state_changed_with_description():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    event = {
        "event_type": "character_state_changed",
        "chapter": 2,
        "subject": "luming",
        "payload": {
            "description": "Lu Ming realizes he alone understands finance in this world",
            "previous_state": "confusion after transmigration",
            "new_state": "activate understanding",
            "narrative_weight": "pivotal",
        },
    }
    text = writer._event_to_text(event)
    assert text, "should produce non-empty text"
    assert "Chapter 2" in text
    assert "luming" in text or "Lu Ming" in text or "understanding" in text or "finance" in text


# ============================================================
# integration：use real DeepSeek output commit payload run the complete projection chain
# ============================================================


def test_integration_real_deepseek_commit_projects_full_state(tmp_path):
    """end-to-end：combination state + memory projector handles real commit payload，confirm all data reaches its destination。"""
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    (tmp_path / ".webnovel" / "state.json").write_text(
        json.dumps(
            {
                "protagonist_state": {
                    "name": "Lu Ming",
                    "power": {"realm": "", "layer": 1},
                    "location": {"current": ""},
                }
            }
        ),
        encoding="utf-8",
    )

    # real DeepSeek v4pro output excerpt
    real_payload = {
        "meta": {"status": "accepted", "chapter": 2},
        "state_deltas": [
            {
                "entity_id": "luming",
                "field_path": "physical.condition",
                "old_value": "weak",
                "new_value": "weak（ongoing）",
                "change_type": "confirmed",
            },
            {
                "entity_id": "luming",
                "field_path": "knowledge.lending_ecosystem",
                "old_value": "knows only of the Underworld Debt",
                "new_value": "complete market graph",
                "change_type": "initialize",
            },
        ],
        "entity_deltas": [
            {
                "entity_id": "luming",
                "action": "upsert",
                "entity_type": "character",
                "tier": "core",
                "is_protagonist": True,
                "payload": {"name": "Lu Ming"},
            },
            {
                "entity_id": "qingyun_zong",
                "action": "upsert",
                "entity_type": "organization",
                "tier": "major",
                "payload": {"name": "Azure Sect"},
            },
            {
                "entity_id": "heishi_fangshi",
                "action": "upsert",
                "entity_type": "location",
                "tier": "major",
                "payload": {"name": "Blackstone Market"},
            },
        ],
        "accepted_events": [
            {
                "event_id": "evt_ch002_guarantor_mystery",
                "chapter": 2,
                "event_type": "open_loop_created",
                "subject": "luming",
                "payload": {
                    "description": "unknown guarantor identity",
                    "loop_type": "identity mystery",
                    "unanswered_question": "who is the guarantor？",
                },
            }
        ],
    }

    StateProjectionWriter(tmp_path).apply(real_payload)
    MemoryProjectionWriter(tmp_path).apply(real_payload)

    state = json.loads((tmp_path / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    # entity_state must contain content（must no longer be {}）
    assert state["entity_state"], "entity_state should not be empty"
    assert "luming" in state["entity_state"]
    # mirror protagonist fields to protagonist_state preserve
    assert state["protagonist_state"]["name"] == "Lu Ming"

    # memory_scratchpad：organizations and locations must not be misclassified
    store = ScratchpadManager(cfg)
    chars = store.query(category="character_state", status="active")
    by_id = {x.subject: x for x in chars}
    assert by_id["qingyun_zong"].payload.get("type") == "organization"
    assert by_id["heishi_fangshi"].payload.get("type") == "location"

    # open_loop must contain meaningful content（cannot be 'luming'）
    loops = store.query(category="open_loop", status="active")
    contents = [x.subject for x in loops]
    assert any("guarantor" in c or "identity mystery" in c for c in contents), contents
