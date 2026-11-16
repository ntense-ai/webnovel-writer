#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

from data_modules.story_contract_schema import ChapterBrief, MasterSetting, ReviewContract, VolumeBrief


def test_master_setting_and_chapter_brief_accept_phase1_seed_shape():
    master = MasterSetting.model_validate(
        {
            "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
            "route": {"primary_genre": "broken-engagement-fantasy"},
            "master_constraints": {"core_tone": "pressure before payoff", "pacing_strategy": "first counterattack within three chapters"},
            "base_context": [],
            "source_trace": [],
            "override_policy": {"locked": ["route.primary_genre"], "append_only": ["anti_patterns"], "override_allowed": []},
        }
    )
    chapter = ChapterBrief.model_validate(
        {
            "meta": {"schema_version": "story-system/v1", "contract_type": "CHAPTER_BRIEF"},
            "override_allowed": {"chapter_focus": "counterattack during the broken engagement"},
            "dynamic_context": [],
            "source_trace": [],
        }
    )
    assert master.route["primary_genre"] == "broken-engagement-fantasy"
    assert chapter.override_allowed["chapter_focus"] == "counterattack during the broken engagement"


def test_volume_brief_requires_selected_fields():
    payload = {
        "meta": {"schema_version": "story-system/v1", "contract_type": "VOLUME_BRIEF"},
        "volume_goal": {"summary": "establish a foothold in volume one"},
        "selected_tropes": ["broken-engagement counterattack"],
        "selected_pacing": {"wave": "suppression-then-eruption"},
        "selected_scenes": ["sect hall", "resource competition"],
        "anti_patterns": ["supporting character steals the protagonist's payoff"],
        "system_constraints": ["special advantage limited to once daily"],
        "overrides": {"locked": {}, "append_only": {}, "override_allowed": {}},
    }
    model = VolumeBrief.model_validate(payload)
    assert model.volume_goal["summary"] == "establish a foothold in volume one"


def test_review_contract_requires_blocking_rules_list():
    with pytest.raises(Exception):
        ReviewContract.model_validate(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "REVIEW_CONTRACT"},
                "must_check": ["mandatory_nodes"],
                "blocking_rules": "not-a-list",
                "genre_specific_risks": [],
                "anti_patterns": [],
                "system_constraints": [],
                "review_thresholds": {"blocking_count": 0},
                "overrides": {"locked": {}, "append_only": {}, "override_allowed": {}},
            }
        )
