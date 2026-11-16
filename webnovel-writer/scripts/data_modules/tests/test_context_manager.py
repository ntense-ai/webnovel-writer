#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ContextManager tests
"""

import json
import logging

import pytest

from data_modules.config import DataModulesConfig
from data_modules.index_manager import (
    IndexManager,
    EntityMeta,
    ChapterReadingPowerMeta,
    ReviewMetrics,
)
from data_modules.context_manager import ContextManager
from data_modules.query_router import QueryRouter


@pytest.fixture
def temp_project(tmp_path):
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    return cfg


def test_context_manager_build_and_filter(temp_project):
    state = {
        "protagonist_state": {"name": "Xiao Yan", "location": {"current": "Skycloud Sect"}},
        "chapter_meta": {"0001": {"hook": "Test"}},
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    # preferences and memory
    (temp_project.webnovel_dir / "preferences.json").write_text(json.dumps({"tone": "passionate"}, ensure_ascii=False), encoding="utf-8")
    (temp_project.webnovel_dir / "project_memory.json").write_text(json.dumps({"patterns": []}, ensure_ascii=False), encoding="utf-8")

    idx = IndexManager(temp_project)
    idx.upsert_entity(
        EntityMeta(
            id="xiaoyan",
            type="character",
            canonical_name="Xiao Yan",
            current={},
            first_appearance=1,
            last_appearance=1,
        )
    )
    idx.upsert_entity(
        EntityMeta(
            id="bad",
            type="character",
            canonical_name="Villain",
            current={},
            first_appearance=1,
            last_appearance=1,
        )
    )
    idx.record_appearance("xiaoyan", 1, ["Xiao Yan"], 1.0)
    idx.record_appearance("bad", 1, ["Villain"], 1.0)
    invalid_id = idx.mark_invalid_fact("entity", "bad", "Error")
    idx.resolve_invalid_fact(invalid_id, "confirm")

    manager = ContextManager(temp_project)
    payload = manager.build_context(1)
    characters = payload["scene"]["appearing_characters"]
    assert any(c.get("entity_id") == "xiaoyan" for c in characters)
    assert not any(c.get("entity_id") == "bad" for c in characters)
    assert payload["preferences"].get("tone") == "passionate"
    assert "long_term_memory" in payload


def test_context_manager_uses_memory_orchestrator_for_working_when_enabled(temp_project, monkeypatch):
    state = {
        "protagonist_state": {"name": "Old snapshot"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    temp_project.context_use_memory_orchestrator = True

    def _fake_pack(self, chapter, task_type="write"):
        return {
            "working_memory": [
                {"layer": "working", "source": "outline", "chapter": chapter, "content": "FAKE_OUTLINE"},
                {
                    "layer": "working",
                    "source": "state_export",
                    "chapter": chapter,
                    "content": {"protagonist_state": {"name": "New snapshot"}},
                },
                {"layer": "working", "source": "summary", "chapter": chapter - 1, "content": "FAKE_SUMMARY"},
            ],
            "episodic_memory": [],
            "semantic_memory": [],
            "long_term_facts": [],
            "active_constraints": [],
            "recent_changes": [],
            "warnings": [],
            "stats": {"total": 0, "injected": 0, "filtered": 0, "conflicts": 0},
        }

    monkeypatch.setattr("data_modules.memory.orchestrator.MemoryOrchestrator.build_memory_pack", _fake_pack)
    manager = ContextManager(temp_project)
    payload = manager.build_context(1)
    core = payload["core"]
    long_term_memory = payload["long_term_memory"]

    assert "working_memory" in long_term_memory
    assert core["chapter_outline"] == "FAKE_OUTLINE"
    assert core["protagonist_snapshot"] == {"name": "New snapshot"}
    assert core["recent_summaries"] == [{"chapter": 0, "summary": "FAKE_SUMMARY"}]


def test_context_manager_skips_memory_orchestrator_when_disabled(temp_project, monkeypatch):
    state = {
        "protagonist_state": {"name": "Xiao Yan"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    temp_project.context_use_memory_orchestrator = False

    def _boom(self, chapter, task_type="write"):
        raise AssertionError("context_use_memory_orchestrator=false should not call when orchestrator")

    monkeypatch.setattr("data_modules.memory.orchestrator.MemoryOrchestrator.build_memory_pack", _boom)
    manager = ContextManager(temp_project)
    payload = manager.build_context(1)

    assert payload["long_term_memory"] == {}


def test_context_manager_loads_volume_outline_file(temp_project):
    state = {
        "progress": {
            "volumes_planned": [
                {"volume": 1, "chapters_range": "1-10"},
            ]
        },
        "protagonist_state": {},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    temp_project.outline_dir.mkdir(parents=True, exist_ok=True)
    (temp_project.outline_dir / "volume-1-outline.md").write_text(
        "### Chapter 2: Test title\nTest outline\n\n### Chapter 3: next chapter",
        encoding="utf-8",
    )

    manager = ContextManager(temp_project)
    payload = manager.build_context(2)

    outline = payload["core"]["chapter_outline"]
    assert "### Chapter 2: Test title" in outline
    assert "Test outline" in outline


def test_context_manager_includes_story_contract_and_prewrite_validation(temp_project):
    state = {
        "progress": {"volumes_planned": [{"volume": 1, "chapters_range": "1-10"}]},
        "protagonist_state": {"name": "Xiao Yan"},
        "chapter_meta": {},
        "disambiguation_warnings": [{"mention": "Sect Leader"}],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    story_root = temp_project.story_system_dir
    story_root.mkdir(parents=True, exist_ok=True)
    (story_root / "MASTER_SETTING.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
                "route": {"primary_genre": "broken-engagement-fantasy"},
                "master_constraints": {"core_tone": "Suppress then erupt"},
                "base_context": [],
                "source_trace": [],
                "override_policy": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "chapters").mkdir(parents=True, exist_ok=True)
    (story_root / "chapters" / "chapter_003.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "CHAPTER_BRIEF", "chapter": 3},
                "override_allowed": {"chapter_focus": "Discover the trap"},
                "dynamic_context": [],
                "source_trace": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "volumes").mkdir(parents=True, exist_ok=True)
    (story_root / "volumes" / "volume_001.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "VOLUME_BRIEF"},
                "volume_goal": {"summary": "Volume One pressure test"},
                "selected_tropes": ["Counterattack after broken engagement"],
                "selected_pacing": {"wave": "Suppress then erupt"},
                "selected_scenes": [],
                "anti_patterns": [],
                "system_constraints": [],
                "overrides": {"locked": {}, "append_only": {}, "override_allowed": {}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "reviews").mkdir(parents=True, exist_ok=True)
    (story_root / "reviews" / "chapter_003.review.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "REVIEW_CONTRACT"},
                "must_check": ["Discover the trap"],
                "blocking_rules": ["Do not reveal the hand early"],
                "genre_specific_risks": [],
                "anti_patterns": [],
                "system_constraints": [],
                "review_thresholds": {},
                "overrides": {"locked": {}, "append_only": {}, "override_allowed": {}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    temp_project.outline_dir.mkdir(parents=True, exist_ok=True)
    (temp_project.outline_dir / "volume-1-outline.md").write_text(
        "### Chapter 3: Trial\nMust-cover nodes: Discover the trap\nChapter prohibitions: Do not reveal the hand early",
        encoding="utf-8",
    )

    manager = ContextManager(temp_project)
    payload = manager.build_context(3)

    assert "story_contract" in payload
    assert "prewrite_validation" in payload
    assert payload["story_contract"]["review_contract"]["meta"]["contract_type"] == "REVIEW_CONTRACT"
    assert payload["prewrite_validation"]["fulfillment_seed"]["planned_nodes"] == ["Discover the trap"]
    payload_keys = list(payload.keys())
    assert payload_keys.index("story_contract") < payload_keys.index("scene")


def test_context_manager_prefers_contract_route_over_legacy_genre_profile(temp_project):
    refs_dir = temp_project.project_root / ".claude" / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    (refs_dir / "genre-profiles.md").write_text("## urban\n- old profile hint", encoding="utf-8")
    (refs_dir / "reading-power-taxonomy.md").write_text("## urban\n- Old category", encoding="utf-8")

    state = {
        "project": {"genre": "urban"},
        "protagonist_state": {"name": "Lin Mo"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    story_root = temp_project.story_system_dir
    story_root.mkdir(parents=True, exist_ok=True)
    (story_root / "MASTER_SETTING.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
                "route": {"primary_genre": "urban-fantasy"},
                "master_constraints": {"core_tone": "Suppress then erupt"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    manager = ContextManager(temp_project)
    payload = manager.build_context(3)

    assert payload["story_contract"]["master_setting"]["route"]["primary_genre"] == "urban-fantasy"
    assert payload["genre_profile"]["genre"] == "urban-fantasy"
    assert payload["writing_guidance"]["signals_used"]["genre"] == "urban-fantasy"
    assert payload["runtime_status"]["fallback_sources"] == [
        "missing_volume_contract",
        "missing_chapter_contract",
        "missing_review_contract",
        "missing_accepted_commit",
    ]


def test_context_manager_exposes_latest_rejected_commit_not_last_accepted(temp_project):
    state = {
        "project": {"genre": "cultivation"},
        "progress": {"current_chapter": 2},
        "protagonist_state": {"name": "Han Li"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    story_root = temp_project.story_system_dir
    (story_root / "chapters").mkdir(parents=True, exist_ok=True)
    (story_root / "reviews").mkdir(parents=True, exist_ok=True)
    (story_root / "commits").mkdir(parents=True, exist_ok=True)
    (story_root / "MASTER_SETTING.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
                "route": {"primary_genre": "cultivation"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "chapters" / "chapter_003.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "CHAPTER_BRIEF", "chapter": 3},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "reviews" / "chapter_003.review.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "REVIEW_CONTRACT", "chapter": 3},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "commits" / "chapter_002.commit.json").write_text(
        json.dumps(
            {"meta": {"schema_version": "story-system/v1", "chapter": 2, "status": "accepted"}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "commits" / "chapter_003.commit.json").write_text(
        json.dumps(
            {"meta": {"schema_version": "story-system/v1", "chapter": 3, "status": "rejected"}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    manager = ContextManager(temp_project)
    payload = manager.build_context(3)

    assert payload["latest_commit"]["meta"]["status"] == "rejected"
    assert payload["runtime_status"]["latest_accepted_commit"]["meta"]["status"] == "accepted"


def test_context_manager_blocks_when_story_contract_missing(temp_project):
    state = {
        "protagonist_state": {"name": "Xiao Yan"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    manager = ContextManager(temp_project)
    payload = manager.build_context(3)

    prewrite = payload["prewrite_validation"]
    assert prewrite["blocking"] is True
    assert any("contract" in reason.lower() for reason in prewrite["blocking_reasons"])


def test_query_router():
    router = QueryRouter()
    assert router.route("Who is the character") == "entity"
    assert router.route("What happened in the plot") == "plot"
    intent = router.route_intent("relationship graph for Xiao Yan and Yao Lao in chapters 10-20")
    assert intent["intent"] == "relationship"
    assert intent["needs_graph"] is True
    assert intent["time_scope"]["from_chapter"] == 10
    assert intent["time_scope"]["to_chapter"] == 20
    plans = router.plan_subqueries(intent)
    assert plans
    assert plans[0]["strategy"] in {"graph_lookup", "graph_hybrid"}
    assert "A" in router.split("A, B; C")


def test_context_manager_applies_ranker_and_contract_meta(temp_project):
    state = {
        "protagonist_state": {"name": "Xiao Yan"},
        "chapter_meta": {
            "0002": {"hook": "steady"},
            "0003": {"hook": "Leave a mystery"},
        },
        "disambiguation_warnings": [
            {"chapter": 1, "message": "Ordinary warning"},
            {"chapter": 3, "message": "critical Conflict warning", "severity": "high"},
        ],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    manager = ContextManager(temp_project)
    payload = manager.build_context(4)

    assert payload["meta"].get("context_contract_version") == "v3"
    recent_meta = payload["core"]["recent_meta"]
    if recent_meta:
        assert recent_meta[0]["chapter"] == 3

    warnings = payload["alerts"]["disambiguation_warnings"]
    if warnings and isinstance(warnings[0], dict):
        assert "critical" in str(warnings[0].get("message", "")) or warnings[0].get("severity") == "high"


def test_context_manager_includes_reader_signal_and_genre_profile(temp_project):
    state = {
        "project": {"genre": "xuanhuan"},
        "protagonist_state": {"name": "Xiao Yan"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    idx = IndexManager(temp_project)
    idx.save_chapter_reading_power(
        ChapterReadingPowerMeta(
            chapter=3,
            hook_type="mystery",
            hook_strength="strong",
            coolpoint_patterns=["Identity revelation"],
        )
    )
    idx.save_review_metrics(
        ReviewMetrics(
            start_chapter=1,
            end_chapter=3,
            overall_score=72,
            dimension_scores={"plot": 72},
            severity_counts={"high": 1},
            critical_issues=["Dragging pace"],
        )
    )

    manager = ContextManager(temp_project)
    payload = manager.build_context(4)

    reader_signal = payload["reader_signal"]
    assert "recent_reading_power" in reader_signal
    assert "pattern_usage" in reader_signal
    assert "hook_type_usage" in reader_signal
    assert "review_trend" in reader_signal
    assert isinstance(reader_signal.get("low_score_ranges"), list)

    genre_profile = payload["genre_profile"]
    assert genre_profile.get("genre") == "xuanhuan"
    assert "profile_excerpt" in genre_profile
    assert "taxonomy_excerpt" in genre_profile


def test_context_manager_genre_section_and_refs_extraction(temp_project):
    refs_dir = temp_project.project_root / ".claude" / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)

    (refs_dir / "genre-profiles.md").write_text(
        """
## shuangwen
- Fast pace
- Frequent humiliation payoffs

## xuanhuan
- Clear progression arc
- Resource competition
""".strip(),
        encoding="utf-8",
    )
    (refs_dir / "reading-power-taxonomy.md").write_text(
        """
## xuanhuan
- Prioritize hook strength strong
- Use defeating stronger opponents as a payoff
""".strip(),
        encoding="utf-8",
    )

    manager = ContextManager(temp_project)

    profile = manager._load_genre_profile({"project": {"genre": "xuanhuan"}})
    assert profile["genre"] == "xuanhuan"
    assert "Clear progression arc" in profile["profile_excerpt"]
    assert "hook strength" in profile["taxonomy_excerpt"].lower()
    assert isinstance(profile["reference_hints"], list)
    assert profile["reference_hints"]

    fallback_excerpt = manager._extract_genre_section("## a\n1\n## b\n2", "unknown")
    assert fallback_excerpt.startswith("## a")


def test_context_manager_reader_signal_with_debt_and_disable_switch(temp_project):
    manager = ContextManager(temp_project)
    manager.config.context_reader_signal_include_debt = True

    signal = manager._load_reader_signal(chapter=5)
    assert "debt_summary" in signal

    manager.config.context_reader_signal_enabled = False
    assert manager._load_reader_signal(chapter=5) == {}

    manager.config.context_genre_profile_enabled = False
    assert manager._load_genre_profile({"project": {"genre": "xuanhuan"}}) == {}


def test_context_manager_includes_writing_guidance(temp_project):
    state = {
        "project": {"genre": "xuanhuan"},
        "protagonist_state": {"name": "Xiao Yan"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    idx = IndexManager(temp_project)
    idx.save_chapter_reading_power(
        ChapterReadingPowerMeta(
            chapter=3,
            hook_type="mystery",
            hook_strength="strong",
            coolpoint_patterns=["Identity revelation"],
        )
    )
    idx.save_review_metrics(
        ReviewMetrics(
            start_chapter=1,
            end_chapter=3,
            overall_score=70,
            dimension_scores={"plot": 70},
            severity_counts={"high": 1},
            critical_issues=["Dragging pace"],
        )
    )

    manager = ContextManager(temp_project)
    payload = manager.build_context(4)

    guidance = payload["writing_guidance"]
    assert guidance.get("chapter") == 4
    items = guidance.get("guidance_items") or []
    assert isinstance(items, list)
    assert items
    assert guidance.get("signals_used", {}).get("genre") == "xuanhuan"
    checklist = guidance.get("checklist") or []
    assert isinstance(checklist, list)
    assert checklist
    checklist_score = guidance.get("checklist_score") or {}
    assert isinstance(checklist_score, dict)
    assert "score" in checklist_score
    assert "completion_rate" in checklist_score
    first_item = checklist[0]
    assert isinstance(first_item, dict)
    assert {"id", "label", "weight", "required", "source", "verify_hint"}.issubset(first_item.keys())

    persisted = idx.get_writing_checklist_score(4)
    assert isinstance(persisted, dict)
    assert persisted.get("chapter") == 4
    assert persisted.get("score") is not None


def test_context_manager_dynamic_weights_and_composite_genre(temp_project):
    refs_dir = temp_project.project_root / ".claude" / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    (refs_dir / "genre-profiles.md").write_text(
        """
## xuanhuan
- Clear progression arc

## realistic
- social-issue parallels
""".strip(),
        encoding="utf-8",
    )
    (refs_dir / "reading-power-taxonomy.md").write_text(
        """
## xuanhuan
- Prioritize hook strength

## realistic
- Consistent character motivation
""".strip(),
        encoding="utf-8",
    )

    state = {
        "project": {"genre": "xuanhuan+realistic"},
        "protagonist_state": {"name": "Xiao Yan"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    manager = ContextManager(temp_project)
    payload_early = manager.build_context(10, template="plot")
    payload_late = manager.build_context(150, template="plot")

    assert payload_early.get("meta", {}).get("context_weight_stage") == "early"
    assert payload_late.get("meta", {}).get("context_weight_stage") == "late"

    profile = payload_early["genre_profile"]
    assert profile.get("composite") is True
    assert profile.get("genre") == "xuanhuan"
    assert isinstance(profile.get("genres"), list)
    assert "realistic" in (profile.get("genres") or [])
    assert isinstance(profile.get("composite_hints"), list)
    assert profile.get("composite_hints")


def test_context_manager_genre_alias_guidance_and_heading_extraction(temp_project):
    refs_dir = temp_project.project_root / ".claude" / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    (refs_dir / "genre-profiles.md").write_text(
        """
### esports
- League progression

### livestream-fiction
- Feedback loop

### cosmic-horror
- The Price of Truth
""".strip(),
        encoding="utf-8",
    )
    (refs_dir / "reading-power-taxonomy.md").write_text(
        """
### esports
- tactical decision point
""".strip(),
        encoding="utf-8",
    )

    state = {
        "project": {"genre": "esports"},
        "protagonist_state": {"name": "Lin Ran"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    manager = ContextManager(temp_project)
    payload = manager.build_context(12, template="plot")
    guidance = payload["writing_guidance"]
    items = guidance.get("guidance_items") or []

    assert any("tactical decision" in str(text) for text in items)
    assert any("Serial pacing baseline" in str(text) for text in items)
    assert any("Payoff baseline" in str(text) for text in items)


def test_context_manager_genre_aliases_normalized_for_profile_lookup(temp_project):
    refs_dir = temp_project.project_root / ".claude" / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    (refs_dir / "genre-profiles.md").write_text(
        """
## esports
- League progression

## livestream-fiction
- Immediate feedback

## cosmic-horror
- The Price of Truth
""".strip(),
        encoding="utf-8",
    )
    (refs_dir / "reading-power-taxonomy.md").write_text(
        """
## esports
- Decision consequences

## livestream-fiction
- Data feedback loop

## cosmic-horror
- Rules first
""".strip(),
        encoding="utf-8",
    )

    manager = ContextManager(temp_project)

    assert manager._parse_genre_tokens("esports fiction") == ["esports"]
    assert manager._parse_genre_tokens("livestreaming") == ["livestream-fiction"]
    assert manager._parse_genre_tokens("cosmic horror") == ["cosmic-horror"]
    assert manager._parse_genre_tokens("cultivation/xuanhuan") == ["cultivation", "xuanhuan"]
    assert manager._parse_genre_tokens("urban fantasy") == ["urban-fantasy"]
    assert manager._parse_genre_tokens("Historical-romance premise") == ["historical-romance"]

    state = {
        "project": {"genre": "esports fiction+livestreaming"},
        "protagonist_state": {"name": "Ye Xiu"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    payload = manager.build_context(20, template="plot")
    profile = payload["genre_profile"]

    assert profile.get("genre") == "esports"
    assert "livestream-fiction" in (profile.get("genres") or [])


def test_context_manager_enables_methodology_for_xianxia(temp_project):
    state = {
        "project": {"genre": "cultivation"},
        "protagonist_state": {"name": "Han Li"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    manager = ContextManager(temp_project)
    manager.config.context_writing_checklist_max_items = 8
    payload = manager.build_context(21, template="plot")

    guidance = payload["writing_guidance"]
    strategy = guidance.get("methodology") or {}
    assert strategy.get("enabled") is True
    assert strategy.get("pilot") == "xianxia"
    assert strategy.get("genre_profile_key") == "xianxia"
    assert guidance.get("signals_used", {}).get("methodology_enabled") is True
    assert isinstance(strategy.get("observability"), dict)


def test_context_manager_enables_methodology_for_non_xianxia_by_default(temp_project):
    state = {
        "project": {"genre": "xuanhuan"},
        "protagonist_state": {"name": "Xiao Yan"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    manager = ContextManager(temp_project)
    payload = manager.build_context(21, template="plot")

    guidance = payload["writing_guidance"]
    strategy = guidance.get("methodology") or {}
    assert strategy.get("enabled") is True
    assert strategy.get("genre_profile_key") == "xuanhuan"
    assert guidance.get("signals_used", {}).get("methodology_enabled") is True


def test_context_manager_allows_methodology_whitelist_restriction(temp_project):
    state = {
        "project": {"genre": "livestream-fiction"},
        "protagonist_state": {"name": "Lin Mo"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    manager = ContextManager(temp_project)
    manager.config.context_methodology_genre_whitelist = ("xianxia",)
    payload = manager.build_context(21, template="plot")

    guidance = payload["writing_guidance"]
    strategy = guidance.get("methodology") or {}
    assert strategy == {}
    assert guidance.get("signals_used", {}).get("methodology_enabled") is False


def test_context_manager_persist_writing_checklist_score_logs_failure(temp_project, monkeypatch, caplog):
    manager = ContextManager(temp_project)

    def _raise_save_error(_meta):
        raise RuntimeError("simulated save failure")

    monkeypatch.setattr(manager.index_manager, "save_writing_checklist_score", _raise_save_error)

    with caplog.at_level(logging.WARNING):
        manager._persist_writing_checklist_score(
            {
                "chapter": 6,
                "score": 70.0,
                "total_items": 3,
                "required_items": 1,
                "completed_items": 1,
                "completed_required": 1,
                "total_weight": 3.0,
                "completed_weight": 1.0,
                "completion_rate": 0.33,
                "pending_items": ["test"],
            }
        )

    message_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "failed to persist writing checklist score" in message_text


def test_context_manager_composite_genre_boundary_three_plus(temp_project):
    manager = ContextManager(temp_project)
    manager.config.context_genre_profile_support_composite = True
    manager.config.context_genre_profile_max_genres = 3

    genre_raw = "esports fiction+livestreaming+cosmic horror+cultivation+esports fiction"
    tokens = manager._parse_genre_tokens(genre_raw)
    assert tokens[:4] == ["esports", "livestream-fiction", "cosmic-horror", "cultivation"]

    state = {
        "project": {"genre": genre_raw},
        "protagonist_state": {"name": "protagonist"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }

    profile = manager._load_genre_profile(state)
    assert profile.get("composite") is True
    assert profile.get("genres") == ["esports", "livestream-fiction", "cosmic-horror"]
    assert profile.get("secondary_genres") == ["livestream-fiction", "cosmic-horror"]

    profile_again = manager._load_genre_profile(state)
    assert profile_again.get("genres") == profile.get("genres")


def test_context_manager_dynamic_weights_from_config_override(temp_project):
    manager = ContextManager(temp_project)
    manager.config.context_dynamic_budget_enabled = True
    manager.config.context_template_weights_dynamic = {
        "early": {
            "plot": {"core": 0.60, "scene": 0.20, "global": 0.20},
        }
    }

    weights = manager._resolve_template_weights("plot", chapter=1)
    assert weights == {"core": 0.60, "scene": 0.20, "global": 0.20}


def test_context_manager_genre_profile_fallbacks_to_project_info(temp_project):
    manager = ContextManager(temp_project)

    profile = manager._load_genre_profile({"project_info": {"genre": "xuanhuan"}})

    assert profile.get("genre_raw") == "xuanhuan"
    assert profile.get("genre") == "xuanhuan"


def test_context_manager_genre_profile_prefers_project_info_over_project(temp_project):
    manager = ContextManager(temp_project)

    profile = manager._load_genre_profile(
        {
            "project": {"genre": "xuanhuan"},
            "project_info": {"genre": "dushi"},
        }
    )

    assert profile.get("genre_raw") == "dushi"
    assert profile.get("genre") == "dushi"


def test_context_manager_includes_plot_structure_when_outline_has_nodes(temp_project):
    state = {
        "project": {"genre": "xuanhuan"},
        "protagonist_state": {"name": "Xiao Yan"},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    temp_project.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    temp_project.outline_dir.mkdir(parents=True, exist_ok=True)
    (temp_project.outline_dir / "volume-1-outline.md").write_text(
        """### Chapter 4: Trial
CBN: Enter the trial grounds
CPNs:
- Observe the rules
- Discover the trap
CEN: decides to turn the scheme against its maker
Must-cover nodes: Discover the trap
Chapter prohibitions: Do not openly turn hostile yet
""",
        encoding="utf-8",
    )

    manager = ContextManager(temp_project)
    payload = manager.build_context(4)

    plot_structure = payload["plot_structure"]
    assert plot_structure.get("cbn") == "Enter the trial grounds"
    assert plot_structure.get("cpns") == ["Observe the rules", "Discover the trap"]
    assert plot_structure.get("cen") == "decides to turn the scheme against its maker"
    assert plot_structure.get("mandatory_nodes") == ["Discover the trap"]
    assert plot_structure.get("prohibitions") == ["Do not openly turn hostile yet"]
