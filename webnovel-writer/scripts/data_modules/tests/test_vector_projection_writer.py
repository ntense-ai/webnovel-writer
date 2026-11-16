#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VectorProjectionWriter unit tests。"""
import pytest

from data_modules.vector_projection_writer import VectorProjectionWriter


def test_event_to_text_formats_power_breakthrough():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    event = {
        "event_type": "power_breakthrough",
        "chapter": 47,
        "subject": "Han Li",
        "payload": {"field": "realm", "new": "Early Foundation Establishment"},
    }
    text = writer._event_to_text(event)
    assert "Chapter 47" in text
    assert "Han Li" in text
    assert "Early Foundation Establishment" in text


def test_delta_to_text_formats_relationship():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    delta = {
        "from_entity": "Han Li",
        "to_entity": "Chen Qiaoqian",
        "relationship_type": "cooperation",
        "chapter": 47,
    }
    text = writer._delta_to_text(delta)
    assert "Chapter 47" in text
    assert "Han Li" in text
    assert "Chen Qiaoqian" in text
    assert "cooperation" in text


def test_collect_chunks_from_commit():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    payload = {
        "meta": {"chapter": 47, "status": "accepted"},
        "accepted_events": [
            {
                "event_type": "power_breakthrough",
                "chapter": 47,
                "subject": "Han Li",
                "payload": {"field": "realm", "new": "Early Foundation Establishment"},
            },
        ],
        "entity_deltas": [
            {
                "from_entity": "Han Li",
                "to_entity": "Chen Qiaoqian",
                "relationship_type": "cooperation",
                "chapter": 47,
            },
        ],
    }
    chunks = writer._collect_chunks(payload)
    assert len(chunks) == 2
    assert chunks[0]["chunk_type"] == "event"
    assert chunks[1]["chunk_type"] == "entity_delta"
    assert chunks[0]["chunk_id"] != chunks[1]["chunk_id"]


def test_collect_chunks_assigns_unique_ids_for_same_chapter_events():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    payload = {
        "meta": {"chapter": 47, "status": "accepted"},
        "accepted_events": [
            {
                "event_type": "character_state_changed",
                "chapter": 47,
                "subject": "Han Li",
                "payload": {"field": "state", "new": "alert"},
            },
            {
                "event_type": "character_state_changed",
                "chapter": 47,
                "subject": "Chen Qiaoqian",
                "payload": {"field": "state", "new": "hesitates"},
            },
        ],
        "entity_deltas": [],
    }

    chunks = writer._collect_chunks(payload)

    assert len(chunks) == 2
    assert len({chunk["chunk_id"] for chunk in chunks}) == 2
    assert all(chunk["scene_index"] == 0 for chunk in chunks)


def test_collect_chunks_keeps_event_id_stable_when_order_changes():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    event_a = {
        "event_id": "evt-a",
        "event_type": "character_state_changed",
        "chapter": 47,
        "subject": "Han Li",
        "payload": {"field": "state", "new": "alert"},
    }
    event_b = {
        "event_id": "evt-b",
        "event_type": "character_state_changed",
        "chapter": 47,
        "subject": "Chen Qiaoqian",
        "payload": {"field": "state", "new": "hesitates"},
    }

    first = writer._collect_chunks(
        {"meta": {"chapter": 47}, "accepted_events": [event_a, event_b], "entity_deltas": []}
    )
    second = writer._collect_chunks(
        {"meta": {"chapter": 47}, "accepted_events": [event_b, event_a], "entity_deltas": []}
    )

    first_ids = {chunk["content"]: chunk["chunk_id"] for chunk in first}
    second_ids = {chunk["content"]: chunk["chunk_id"] for chunk in second}
    assert first_ids == second_ids


def test_rejected_commit_returns_not_applied():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    writer.project_root = None
    result = writer.apply({"meta": {"status": "rejected", "chapter": 1}})
    assert result["applied"] is False


def test_store_zero_for_required_chunks_is_error(monkeypatch, tmp_path):
    writer = VectorProjectionWriter(tmp_path)
    monkeypatch.setattr(writer, "_store_chunks", lambda chunks: 0)

    result = writer.apply(
        {
            "meta": {"status": "accepted", "chapter": 47},
            "summary_text": "Han Li discovers an alchemy-recipe clue at the market。",
            "accepted_events": [],
            "entity_deltas": [],
        }
    )

    assert result["applied"] is False
    assert result["reason"] == "error:store_failed"


def test_collect_chunks_includes_summary_and_scenes():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)
    payload = {
        "meta": {"chapter": 47, "status": "accepted"},
        "summary_text": "Han Li discovers an alchemy-recipe clue at the market。",
        "scenes": [
            {"index": 1, "summary": "Han Li examines market stalls", "location": "market"},
            {"scene_index": 2, "content": "Chen Qiaoqian secretly warns Han Li that someone is following him。"},
        ],
        "accepted_events": [],
        "entity_deltas": [],
    }

    chunks = writer._collect_chunks(payload)
    by_type = {}
    for chunk in chunks:
        by_type.setdefault(chunk["chunk_type"], []).append(chunk)

    assert by_type["summary"][0]["chunk_id"] == "ch0047_summary"
    assert by_type["summary"][0]["parent_chunk_id"] is None
    assert by_type["scene"][0]["parent_chunk_id"] == "ch0047_summary"
    assert by_type["scene"][0]["content"].startswith("market：")
    assert any(chunk["scene_index"] == 2 for chunk in by_type["scene"])


@pytest.mark.asyncio
async def test_run_store_coro_works_inside_active_event_loop():
    writer = VectorProjectionWriter.__new__(VectorProjectionWriter)

    async def store():
        return 3

    assert writer._run_store_coro(store()) == 3
