#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from data_modules.prewrite_validator import PrewriteValidator


def test_prewrite_validator_builds_disambiguation_domain_and_fulfillment_seed(tmp_path):
    project_root = tmp_path
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text(
        json.dumps(
            {
                "disambiguation_pending": [],
                "disambiguation_warnings": [{"mention": "sect leader"}],
                "chapter_meta": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    review_contract = {"must_check": ["discovers the trap"], "blocking_rules": ["do not reveal the plan early"]}
    plot_structure = {"mandatory_nodes": ["discovers the trap"], "prohibitions": ["do not reveal the plan early"]}

    payload = PrewriteValidator(project_root).build(
        chapter=3,
        review_contract=review_contract,
        plot_structure=plot_structure,
    )

    assert payload["blocking"] is False
    assert payload["fulfillment_seed"]["planned_nodes"] == ["discovers the trap"]
    assert payload["disambiguation_domain"]["pending_count"] == 0


def test_prewrite_validator_blocks_when_required_contracts_missing(tmp_path):
    project_root = tmp_path
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text(
        json.dumps(
            {
                "disambiguation_pending": [],
                "disambiguation_warnings": [],
                "chapter_meta": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = PrewriteValidator(project_root).build(
        chapter=3,
        review_contract={},
        plot_structure={},
        story_contract={
            "master_setting": {},
            "chapter_brief": {},
            "volume_brief": {},
            "review_contract": {},
        },
    )

    assert payload["blocking"] is True
    assert "missing_contracts" in payload
    assert set(payload["missing_contracts"]) >= {"master_setting", "review_contract"}


def test_prewrite_validator_blocks_related_entity_placeholders(tmp_path):
    project_root = tmp_path
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text(
        json.dumps(
            {
                "disambiguation_pending": [],
                "disambiguation_warnings": [],
                "chapter_meta": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    settings_dir = project_root / "settings"
    settings_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "Su Yun.md").write_text("Su Yun：first heroine(working title)\n", encoding="utf-8")
    (settings_dir / "future character.md").write_text("later siblings：[To be completed]\n", encoding="utf-8")

    payload = PrewriteValidator(project_root).build(
        chapter=8,
        review_contract={},
        plot_structure={},
        story_contract={
            "master_setting": {"ok": True},
            "chapter_brief": {"chapter_directive": {"key_entities": ["Su Yun"]}},
            "volume_brief": {"ok": True},
            "review_contract": {"ok": True},
        },
    )

    assert payload["blocking"] is True
    assert any("placeholder" in reason for reason in payload["blocking_reasons"])
    assert [item["file"] for item in payload["related_placeholders"]] == ["settings/Su Yun.md"]
