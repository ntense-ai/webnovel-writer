"""Regression coverage for payload metadata and partial entity updates (issue #201)."""

import json

import pytest

from data_modules.chapter_commit_service import ChapterCommitService
from data_modules.config import DataModulesConfig
from data_modules.index_manager import IndexManager
from data_modules.index_projection_writer import IndexProjectionWriter
from data_modules.state_projection_writer import StateProjectionWriter


def _commit(chapter, delta, state_deltas=None):
    return {
        "meta": {"status": "accepted", "chapter": chapter},
        "extraction_result": {
            "accepted_events": [],
            "state_deltas": state_deltas or [],
            "entity_deltas": [{"chapter": chapter, **delta}],
        },
    }


@pytest.fixture
def manager(tmp_path):
    config = DataModulesConfig.from_project_root(tmp_path)
    config.ensure_dirs()
    return IndexManager(config)


@pytest.mark.parametrize("desc_key", ["desc", "description"])
def test_index_projection_reads_payload_metadata(tmp_path, manager, desc_key):
    commit = _commit(1, {
        "entity_id": "hong_bagong",
        "action": "upsert",
        "entity_type": "character",
        "payload": {"name": "Hong Bagong", desc_key: "Important supporting character", "tier": "major"},
    })
    IndexProjectionWriter(tmp_path).apply(commit)

    entity = manager.get_entity("hong_bagong")
    assert entity["canonical_name"] == "Hong Bagong"
    assert entity["desc"] == "Important supporting character"
    assert entity["tier"] == "major"
    assert [row["id"] for row in manager.get_core_entities()] == ["hong_bagong"]

    commit["extraction_result"]["entity_deltas"][0]["payload"]["is_archived"] = True
    IndexProjectionWriter(tmp_path).apply(commit)
    assert manager.get_entity("hong_bagong")["is_archived"] == 1
    assert manager.get_core_entities() == []


def test_sparse_delta_preserves_existing_metadata_and_merges_current(manager):
    manager.apply_entity_delta({
        "entity_id": "qingyun_zong", "chapter": 1, "entity_type": "organization",
        "canonical_name": "Azure Cloud Sect", "tier": "major", "desc": "Existing description",
        "is_protagonist": True, "is_archived": True, "current": {"realm": "Dou Zhe"},
    })
    manager.apply_entity_delta({
        "entity_id": "qingyun_zong", "chapter": 2, "current": {"location": "Sect Gate"},
    })

    entity = manager.get_entity("qingyun_zong")
    assert entity["canonical_name"] == "Azure Cloud Sect"
    assert entity["type"] == "organization"
    assert entity["tier"] == "major"
    assert entity["desc"] == "Existing description"
    assert entity["is_protagonist"] == 1
    assert entity["is_archived"] == 1
    assert entity["current_json"] == {"realm": "Dou Zhe", "location": "Sect Gate"}
    assert entity["first_appearance"] == 1
    assert entity["last_appearance"] == 2


def test_top_level_aliases_take_precedence_over_payload(manager):
    manager.apply_entity_delta({
        "entity_id": "hero", "entity_type": "organization", "name": "Top-level name",
        "description": "Top-level description", "tier": "minor",
        "is_protagonist": False, "is_archived": False,
        "payload": {
            "canonical_name": "Nested name", "type": "character", "desc": "Nested description",
            "tier": "protagonist", "is_protagonist": True, "is_archived": True,
        },
    })

    entity = manager.get_entity("hero")
    assert entity["canonical_name"] == "Top-level name"
    assert entity["type"] == "organization"
    assert entity["desc"] == "Top-level description"
    assert entity["tier"] == "minor"
    assert entity["is_protagonist"] == 0
    assert entity["is_archived"] == 0


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("desc", ["", None])
def test_explicit_empty_description_and_false_flags_clear_existing_values(manager, nested, desc):
    manager.apply_entity_delta({
        "entity_id": "hero", "tier": "protagonist", "desc": "Old description", "is_archived": True,
    })
    metadata = {"desc": desc, "is_protagonist": False, "is_archived": False}
    manager.apply_entity_delta({"entity_id": "hero", **({"payload": metadata} if nested else metadata)})

    entity = manager.get_entity("hero")
    assert entity["desc"] == ""
    assert entity["tier"] == "protagonist"
    assert entity["is_protagonist"] == 0
    assert entity["is_archived"] == 0


@pytest.mark.parametrize("metadata", [{"is_protagonist": True}, {"tier": "protagonist"}])
def test_payload_protagonist_signal_reaches_both_projections(tmp_path, manager, metadata):
    commit = _commit(1, {
        "entity_id": "hero", "entity_type": "character",
        "payload": {"canonical_name": "Lu Ming", **metadata},
    }, [{"entity_id": "hero", "field": "power.realm", "new": "Qi Refining Level Five"}])
    IndexProjectionWriter(tmp_path).apply(commit)
    StateProjectionWriter(tmp_path).apply(commit)

    assert manager.get_protagonist()["canonical_name"] == "Lu Ming"
    state = json.loads((tmp_path / ".webnovel/state.json").read_text(encoding="utf-8"))
    assert state["protagonist_state"]["power"]["realm"] == "Qi Refining Level Five"


@pytest.mark.parametrize("nested", [False, True])
def test_state_projection_respects_explicit_false_protagonist(tmp_path, nested):
    state_path = tmp_path / ".webnovel/state.json"
    state_path.parent.mkdir()
    state_path.write_text(json.dumps({
        "protagonist_state": {"entity_id": "hero", "name": "Lu Ming", "power": {"realm": "Old realm"}},
    }), encoding="utf-8")
    metadata = {"is_protagonist": False, "tier": "protagonist", "name": "Lu Ming"}
    delta = {"entity_id": "hero", **({"payload": metadata} if nested else metadata)}
    StateProjectionWriter(tmp_path).apply(_commit(2, delta, [
        {"entity_id": "hero", "field": "power.realm", "new": "New realm"},
    ]))

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["entity_state"]["hero"]["power"]["realm"] == "New realm"
    assert state["protagonist_state"]["power"]["realm"] == "Old realm"


def test_chapter_commit_and_projection_replay_preserve_payload_metadata(tmp_path, manager):
    service = ChapterCommitService(tmp_path)
    commits = []
    for chapter, payload in [(1, {"name": "Hong Bagong", "tier": "major", "desc": "Important supporting character"}),
                             (2, {"name": "Hong Bagong"})]:
        commit = service.build_commit(
            chapter=chapter,
            review_result={"blocking_count": 0},
            fulfillment_result={"planned_nodes": [], "covered_nodes": [], "missed_nodes": [], "extra_nodes": []},
            disambiguation_result={"pending": []},
            extraction_result=_commit(chapter, {
                "entity_id": "hong_bagong", "action": "upsert", "entity_type": "character", "payload": payload,
            })["extraction_result"],
        )
        assert commit["meta"]["status"] == "accepted"
        service.apply_projections(commit)
        commits.append(commit)

    for commit in commits:
        service.apply_projections(commit)
    entity = manager.get_entity("hong_bagong")
    assert entity["tier"] == "major"
    assert entity["desc"] == "Important supporting character"
    assert entity["last_appearance"] == 2
