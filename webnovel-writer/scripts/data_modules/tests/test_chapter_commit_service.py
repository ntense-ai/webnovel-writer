#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

import pytest

from data_modules.chapter_commit_service import ChapterCommitService
from data_modules.config import DataModulesConfig
from data_modules.index_manager import IndexManager


def test_commit_service_rejects_when_missed_nodes_exist(tmp_path):
    service = ChapterCommitService(tmp_path)
    payload = service.build_commit(
        chapter=3,
        review_result={"blocking_count": 0},
        fulfillment_result={
            "planned_nodes": ["Discover the trap"],
            "covered_nodes": [],
            "missed_nodes": ["Discover the trap"],
            "extra_nodes": [],
        },
        disambiguation_result={"pending": []},
        extraction_result={"state_deltas": [], "entity_deltas": [], "accepted_events": []},
    )
    assert payload["meta"]["status"] == "rejected"


def test_commit_service_accepts_when_all_checks_pass(tmp_path):
    service = ChapterCommitService(tmp_path)
    payload = service.build_commit(
        chapter=3,
        review_result={"blocking_count": 0},
        fulfillment_result={"planned_nodes": ["Discover the trap"], "covered_nodes": ["Discover the trap"], "missed_nodes": [], "extra_nodes": []},
        disambiguation_result={"pending": []},
        extraction_result={"state_deltas": [], "entity_deltas": [], "accepted_events": []},
    )
    assert payload["meta"]["status"] == "accepted"
    assert payload["contract_refs"]["master"] == "MASTER_SETTING.json"
    assert payload["contract_refs"]["volume"] == "volume_001.json"
    assert payload["contract_refs"]["chapter"] == "chapter_003.json"
    assert payload["outline_snapshot"]["covered_nodes"] == ["Discover the trap"]
    assert payload["extraction_result"]["accepted_events"] == []
    assert "accepted_events" not in payload
    assert "state_deltas" not in payload
    assert "entity_deltas" not in payload


def test_commit_service_includes_volume_ref_and_write_fact_provenance(tmp_path):
    service = ChapterCommitService(tmp_path)
    payload = service.build_commit(
        chapter=3,
        review_result={"blocking_count": 0},
        fulfillment_result={"planned_nodes": ["Discover the trap"], "covered_nodes": ["Discover the trap"], "missed_nodes": [], "extra_nodes": []},
        disambiguation_result={"pending": []},
        extraction_result={"state_deltas": [], "entity_deltas": [], "accepted_events": []},
    )

    assert payload["contract_refs"]["volume"] == "volume_001.json"
    assert payload["provenance"]["write_fact_role"] == "chapter_commit"
    assert payload["provenance"]["projection_role"] == "derived_read_models"


def test_commit_service_rejects_malformed_gate_artifacts(tmp_path):
    service = ChapterCommitService(tmp_path)
    valid_fulfillment = {
        "planned_nodes": [],
        "covered_nodes": [],
        "missed_nodes": [],
        "extra_nodes": [],
    }
    valid_disambiguation = {"pending": []}
    valid_extraction = {"state_deltas": [], "entity_deltas": [], "accepted_events": []}

    with pytest.raises(ValueError, match="blocking_count"):
        service.build_commit(
            chapter=3,
            review_result={},
            fulfillment_result=valid_fulfillment,
            disambiguation_result=valid_disambiguation,
            extraction_result=valid_extraction,
        )

    with pytest.raises(ValueError, match="fulfillment_result"):
        service.build_commit(
            chapter=3,
            review_result={"blocking_count": 0},
            fulfillment_result={"fulfillment": {"missed_nodes": ["Missed node"]}},
            disambiguation_result=valid_disambiguation,
            extraction_result=valid_extraction,
        )

    with pytest.raises(ValueError, match="disambiguation_result"):
        service.build_commit(
            chapter=3,
            review_result={"blocking_count": 0},
            fulfillment_result=valid_fulfillment,
            disambiguation_result={"disambiguation": {"pending": ["Sect Leader"]}},
            extraction_result=valid_extraction,
        )


def test_commit_service_rejects_nested_extraction_result_shape(tmp_path):
    service = ChapterCommitService(tmp_path)

    with pytest.raises(ValueError, match="top-level"):
        service.build_commit(
            chapter=76,
            review_result={"blocking_count": 0},
            fulfillment_result={
                "planned_nodes": [],
                "covered_nodes": [],
                "missed_nodes": [],
                "extra_nodes": [],
            },
            disambiguation_result={"pending": []},
            extraction_result={
                "chapter": 76,
                "extraction": {
                    "scenes": [{"summary": "Scene segmentation"}],
                    "unresolved_threads": ["Unresolved clue"],
                },
            },
        )


def test_commit_service_rejects_extraction_wrapper_even_with_empty_core_fields(tmp_path):
    service = ChapterCommitService(tmp_path)

    with pytest.raises(ValueError, match="nested under extraction"):
        service.build_commit(
            chapter=76,
            review_result={"blocking_count": 0},
            fulfillment_result={
                "planned_nodes": [],
                "covered_nodes": [],
                "missed_nodes": [],
                "extra_nodes": [],
            },
            disambiguation_result={"pending": []},
            extraction_result={
                "accepted_events": [],
                "state_deltas": [],
                "entity_deltas": [],
                "extraction": {
                    "scenes": [{"summary": "Real scene wrapped at the wrong level"}],
                    "summary_text": "Real summary wrapped at the wrong level",
                },
            },
        )


def test_commit_service_rejects_extraction_result_missing_core_fields(tmp_path):
    service = ChapterCommitService(tmp_path)

    with pytest.raises(ValueError, match="accepted_events"):
        service.build_commit(
            chapter=3,
            review_result={"blocking_count": 0},
            fulfillment_result={
                "planned_nodes": [],
                "covered_nodes": [],
                "missed_nodes": [],
                "extra_nodes": [],
            },
            disambiguation_result={"pending": []},
            extraction_result={"summary_text": "Summary"},
        )


def test_commit_service_rejects_non_object_extraction_items(tmp_path):
    service = ChapterCommitService(tmp_path)

    with pytest.raises(ValueError, match=r"state_deltas\[0\]"):
        service.build_commit(
            chapter=3,
            review_result={"blocking_count": 0},
            fulfillment_result={
                "planned_nodes": [],
                "covered_nodes": [],
                "missed_nodes": [],
                "extra_nodes": [],
            },
            disambiguation_result={"pending": []},
            extraction_result={
                "accepted_events": [],
                "state_deltas": ["realm changed"],
                "entity_deltas": [],
            },
        )


def test_commit_service_rejects_non_object_accepted_event_items(tmp_path):
    service = ChapterCommitService(tmp_path)

    with pytest.raises(ValueError, match=r"accepted_events\[0\]"):
        service.build_commit(
            chapter=3,
            review_result={"blocking_count": 0},
            fulfillment_result={
                "planned_nodes": [],
                "covered_nodes": [],
                "missed_nodes": [],
                "extra_nodes": [],
            },
            disambiguation_result={"pending": []},
            extraction_result={
                "accepted_events": ["not-a-json-object"],
                "state_deltas": [],
                "entity_deltas": [],
            },
        )


def test_commit_service_normalizes_accepted_events_before_projection(tmp_path):
    service = ChapterCommitService(tmp_path)

    payload = service.build_commit(
        chapter=76,
        review_result={"blocking_count": 0},
        fulfillment_result={
            "planned_nodes": [],
            "covered_nodes": [],
            "missed_nodes": [],
            "extra_nodes": [],
        },
        disambiguation_result={"pending": []},
        extraction_result={
            "state_deltas": [],
            "entity_deltas": [],
            "accepted_events": [
                {
                    "type": "mystery_introduction",
                    "characters": ["xiaoyan"],
                    "payload": {"content": "Xiao Yan finds a new clue behind the stone door"},
                }
            ],
        },
    )

    event = payload["extraction_result"]["accepted_events"][0]
    assert event["event_id"].startswith("evt-ch076-001-")
    assert event["chapter"] == 76
    assert event["event_type"] == "open_loop_created"
    assert event["subject"] == "xiaoyan"
    assert "accepted_events" not in payload


def test_apply_projections_normalizes_events_before_router_inspection(
    tmp_path, monkeypatch
):
    captured = {}

    class SpyRouter:
        def required_writers(self, payload):
            captured["events"] = list(payload.get("extraction_result", {}).get("accepted_events") or [])
            return []

    monkeypatch.setitem(
        ChapterCommitService.apply_projection_writers.__globals__,
        "EventProjectionRouter", lambda: SpyRouter(),
    )

    service = ChapterCommitService(tmp_path)
    payload = {
        "meta": {"status": "accepted", "chapter": 76},
        "extraction_result": {
            "accepted_events": [
                {
                    "type": "scene_open",
                    "characters": ["xiaoyan"],
                    "payload": {"content": "Xiao Yan pushes open the stone door，a new mystery emerges"},
                }
            ],
            "state_deltas": [],
            "entity_deltas": [],
            "summary_text": "",
        },
        "projection_status": {
            "state": "pending",
            "index": "pending",
            "summary": "pending",
            "memory": "pending",
            "vector": "pending",
        },
    }

    service.apply_projections(payload)

    event = captured["events"][0]
    assert event["event_id"].startswith("evt-ch076-001-")
    assert event["chapter"] == 76
    assert event["event_type"] == "open_loop_created"
    assert event["subject"] == "xiaoyan"
    assert payload["extraction_result"]["accepted_events"] == captured["events"]


def test_apply_projections_updates_state_for_rejected_commit(tmp_path):
    import json

    (tmp_path / ".webnovel").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")

    service = ChapterCommitService(tmp_path)
    payload = service.build_commit(
        chapter=7,
        review_result={"blocking_count": 1},
        fulfillment_result={
            "planned_nodes": ["Enter the marketplace"],
            "covered_nodes": ["Enter the marketplace"],
            "missed_nodes": [],
            "extra_nodes": [],
        },
        disambiguation_result={"pending": []},
        extraction_result={"state_deltas": [], "entity_deltas": [], "accepted_events": []},
    )

    projected = service.apply_projections(payload)

    state = json.loads((tmp_path / ".webnovel" / "state.json").read_text(encoding="utf-8"))
    assert projected["projection_status"]["state"] == "done"
    assert state["progress"]["chapter_status"]["7"] == "chapter_rejected"


def test_chapter_commit_cli_builds_and_persists_commit(tmp_path, monkeypatch):
    review_path = tmp_path / "review.json"
    fulfillment_path = tmp_path / "fulfillment.json"
    disambiguation_path = tmp_path / "disambiguation.json"
    extraction_path = tmp_path / "extraction.json"
    review_path.write_text('{"blocking_count": 0}', encoding="utf-8")
    fulfillment_path.write_text(
        '{"planned_nodes": ["Discover the trap"], "covered_nodes": ["Discover the trap"], "missed_nodes": [], "extra_nodes": []}',
        encoding="utf-8",
    )
    disambiguation_path.write_text('{"pending": []}', encoding="utf-8")
    extraction_path.write_text('{"state_deltas": [], "entity_deltas": [], "accepted_events": []}', encoding="utf-8")

    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

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


def test_apply_projections_writes_events_and_amend_proposals(tmp_path):
    service = ChapterCommitService(tmp_path)
    payload = service.build_commit(
        chapter=3,
        review_result={"blocking_count": 0},
        fulfillment_result={
            "planned_nodes": ["Discover the trap"],
            "covered_nodes": ["Discover the trap"],
            "missed_nodes": [],
            "extra_nodes": [],
        },
        disambiguation_result={"pending": []},
        extraction_result={
            "state_deltas": [],
            "entity_deltas": [],
            "summary_text": "",
            "accepted_events": [
                {
                    "event_id": "evt-001",
                    "chapter": 3,
                    "event_type": "world_rule_broken",
                    "subject": "Special ability",
                    "payload": {
                        "field": "world_rule",
                        "base_value": "Once daily",
                        "proposed_value": "brief loss of control during breakthrough",
                    },
                }
            ],
        },
    )

    service.apply_projections(payload)

    assert (tmp_path / ".story-system" / "events" / "chapter_003.events.json").is_file()
    manager = IndexManager(DataModulesConfig.from_project_root(tmp_path))
    with manager._get_conn() as conn:
        row = conn.execute(
            """
            SELECT record_type, field, override_value, status
            FROM override_contracts
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row["record_type"] == "amend_proposal"
    assert row["field"] == "world_rule"
    assert row["override_value"] == "brief loss of control during breakthrough"
    assert row["status"] == "pending"
