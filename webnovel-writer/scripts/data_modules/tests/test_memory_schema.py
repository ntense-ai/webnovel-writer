#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from data_modules.memory.schema import (
    BUCKET_TO_CATEGORY,
    CATEGORY_KEY_RULES,
    CATEGORY_TO_BUCKET,
    MemoryItem,
    ScratchpadData,
)


def test_memory_item_roundtrip_and_payload():
    item = MemoryItem(
        id="m1",
        layer="semantic",
        category="character_state",
        subject="xiaoyan",
        field="realm",
        value="Foundation Establishment Level Three",
        payload={"old_value": "Foundation Establishment Level Two"},
        source_chapter=12,
        evidence=["state_change:xiaoyan:realm:12"],
    )
    raw = item.to_dict()
    rebuilt = MemoryItem.from_dict(raw)
    assert rebuilt.value == "Foundation Establishment Level Three"
    assert rebuilt.payload.get("old_value") == "Foundation Establishment Level Two"
    assert rebuilt.status == "active"


def test_scratchpad_data_default_and_count():
    data = ScratchpadData.empty()
    assert data.count_items() == 0
    raw = data.to_dict()
    assert raw["meta"]["version"] == 1
    assert raw["meta"]["total_items"] == 0


def test_category_bucket_mapping_complete():
    assert set(CATEGORY_TO_BUCKET.values()) == set(BUCKET_TO_CATEGORY.keys())
    assert set(CATEGORY_TO_BUCKET.keys()) == set(CATEGORY_KEY_RULES.keys())

