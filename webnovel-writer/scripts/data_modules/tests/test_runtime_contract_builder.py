#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from data_modules.runtime_contract_builder import RuntimeContractBuilder


def test_runtime_contract_builder_creates_volume_and_review_contracts(tmp_path):
    project_root = tmp_path
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text(
        json.dumps(
            {
                "progress": {"volumes_planned": [{"volume": 1, "chapters_range": "1-20"}]},
                "chapter_meta": {},
                "disambiguation_pending": [],
                "disambiguation_warnings": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project_root / ".story-system" / "MASTER_SETTING.json").parent.mkdir(parents=True, exist_ok=True)
    (project_root / ".story-system" / "MASTER_SETTING.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
                "route": {"primary_genre": "broken-engagement-fantasy"},
                "master_constraints": {"core_tone": "pressure before payoff"},
                "base_context": [],
                "source_trace": [],
                "override_policy": {"locked": ["route.primary_genre"], "append_only": ["anti_patterns"], "override_allowed": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project_root / ".story-system" / "anti_patterns.json").write_text(
        json.dumps([{"text": "supporting characters must not take the protagonist's payoff"}], ensure_ascii=False),
        encoding="utf-8",
    )
    (project_root / "outlines").mkdir(parents=True, exist_ok=True)
    (project_root / "outlines" / "volume-1-outline.md").write_text(
        "### Chapter 3：pressure test\nCBN：continue oppression\nMust-cover nodes：discovers the trap、decides to endure quietly\nChapter prohibitions：do not reveal the plan early",
        encoding="utf-8",
    )

    builder = RuntimeContractBuilder(project_root)
    volume_brief, review_contract = builder.build_for_chapter(3)

    assert volume_brief["meta"]["contract_type"] == "VOLUME_BRIEF"
    assert review_contract["meta"]["contract_type"] == "REVIEW_CONTRACT"
    assert "discovers the trap" in review_contract["must_check"]
    assert "do not reveal the plan early" in review_contract["blocking_rules"]


def test_runtime_contract_builder_surfaces_review_extracted_anti_patterns(tmp_path):
    project_root = tmp_path
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text(
        json.dumps({"progress": {"volumes_planned": []}}, ensure_ascii=False),
        encoding="utf-8",
    )
    story_root = project_root / ".story-system"
    story_root.mkdir(parents=True, exist_ok=True)
    (story_root / "MASTER_SETTING.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
                "route": {"primary_genre": "xianxia"},
                "master_constraints": {"core_tone": "restrained and concrete"},
                "base_context": [],
                "source_trace": [],
                "override_policy": {"locked": [], "append_only": ["anti_patterns"], "override_allowed": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "anti_patterns.json").write_text(
        json.dumps(
            [
                {
                    "text": "the only person who knows the compound-interest formula",
                    "source_table": "review_extracted",
                    "source_id": "ch0002_issue_1",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    volume_brief, review_contract = RuntimeContractBuilder(project_root).build_for_chapter(3)

    assert "the only person who knows the compound-interest formula" in volume_brief["anti_patterns"]
    assert "the only person who knows the compound-interest formula" in review_contract["anti_patterns"]
