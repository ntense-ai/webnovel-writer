#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MemoryContractAdapter Integration tests。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ensure scripts/ at sys.path in
_scripts_dir = str(Path(__file__).resolve().parent.parent.parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from data_modules.config import DataModulesConfig
from data_modules.memory_contract import (
    CommitResult,
    ContextPack,
    EntitySnapshot,
    MemoryContract,
    OpenLoop,
    Rule,
    TimelineEvent,
)
from data_modules.memory_contract_adapter import MemoryContractAdapter


def _make_project(tmp_path: Path) -> DataModulesConfig:
    """Create a minimal project and return its configuration。"""
    webnovel_dir = tmp_path / ".webnovel"
    webnovel_dir.mkdir(parents=True, exist_ok=True)
    (webnovel_dir / "state.json").write_text("{}", encoding="utf-8")
    (webnovel_dir / "summaries").mkdir(exist_ok=True)
    return DataModulesConfig.from_project_root(tmp_path)


class TestAdapterSatisfiesProtocol:
    def test_isinstance_check(self, tmp_path):
        cfg = _make_project(tmp_path)
        adapter = MemoryContractAdapter(cfg)
        assert isinstance(adapter, MemoryContract)


class TestReadSummary:
    def test_read_existing_summary(self, tmp_path):
        cfg = _make_project(tmp_path)
        summary_dir = cfg.webnovel_dir / "summaries"
        summary_dir.mkdir(parents=True, exist_ok=True)
        (summary_dir / "ch0010.md").write_text("Chapter 10 summary", encoding="utf-8")

        adapter = MemoryContractAdapter(cfg)
        text = adapter.read_summary(10)
        assert text == "Chapter 10 summary"

    def test_read_missing_summary(self, tmp_path):
        cfg = _make_project(tmp_path)
        adapter = MemoryContractAdapter(cfg)
        assert adapter.read_summary(999) == ""


class TestQueryEntity:
    def test_query_nonexistent_entity(self, tmp_path):
        cfg = _make_project(tmp_path)
        adapter = MemoryContractAdapter(cfg)
        assert adapter.query_entity("nobody") is None

    def test_query_existing_entity(self, tmp_path):
        cfg = _make_project(tmp_path)
        # Write an entity-containing state.json
        state = {
            "entities_v3": {
                "character": {
                    "xiaoyan": {
                        "name": "Xiao Yan",
                        "tier": "core",
                        "aliases": ["he"],
                        "realm": "Dou Di",
                        "first_appearance": 1,
                        "last_appearance": 100,
                    }
                }
            },
            "state_changes": [
                {"entity_id": "xiaoyan", "field": "realm", "old": "Battle Saint", "new": "Dou Di", "chapter": 100}
            ],
        }
        (cfg.state_file).write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

        adapter = MemoryContractAdapter(cfg)
        snap = adapter.query_entity("xiaoyan")
        assert snap is not None
        assert snap.name == "Xiao Yan"
        assert snap.type == "character"
        assert snap.tier == "core"
        assert "he" in snap.aliases
        assert len(snap.recent_state_changes) == 1


class TestQueryRules:
    def test_query_rules_empty(self, tmp_path):
        cfg = _make_project(tmp_path)
        adapter = MemoryContractAdapter(cfg)
        assert adapter.query_rules() == []

    def test_query_rules_with_data(self, tmp_path):
        cfg = _make_project(tmp_path)
        # write scratchpad Data
        from data_modules.memory.schema import MemoryItem
        from data_modules.memory.store import ScratchpadManager

        store = ScratchpadManager(cfg)
        store.upsert_item(MemoryItem(
            id="rule-1", layer="semantic", category="world_rule",
            subject="power-system", field="number of exotic flames", value="23kinds",
            status="active", source_chapter=1,
        ))

        adapter = MemoryContractAdapter(cfg)
        rules = adapter.query_rules()
        assert len(rules) == 1
        assert rules[0].value == "23kinds"
        assert rules[0].domain == "power-system"

    def test_query_rules_filter_by_domain(self, tmp_path):
        cfg = _make_project(tmp_path)
        from data_modules.memory.schema import MemoryItem
        from data_modules.memory.store import ScratchpadManager

        store = ScratchpadManager(cfg)
        store.upsert_item(MemoryItem(
            id="rule-1", layer="semantic", category="world_rule",
            subject="power-system", field="number of exotic flames", value="23kinds",
            status="active", source_chapter=1,
        ))
        store.upsert_item(MemoryItem(
            id="rule-2", layer="semantic", category="world_rule",
            subject="Social structure", field="number of empires", value="4items",
            status="active", source_chapter=2,
        ))

        adapter = MemoryContractAdapter(cfg)
        rules = adapter.query_rules(domain="power-system")
        assert len(rules) == 1
        assert rules[0].field == "number of exotic flames"


class TestGetOpenLoops:
    def test_get_open_loops_empty(self, tmp_path):
        cfg = _make_project(tmp_path)
        adapter = MemoryContractAdapter(cfg)
        assert adapter.get_open_loops() == []

    def test_get_open_loops_with_data(self, tmp_path):
        cfg = _make_project(tmp_path)
        from data_modules.memory.schema import MemoryItem
        from data_modules.memory.store import ScratchpadManager

        store = ScratchpadManager(cfg)
        store.upsert_item(MemoryItem(
            id="ol-1", layer="semantic", category="open_loop",
            subject="three-year challenge", field="", value="Xiao Yan and Nalan Yanran's three-year challenge",
            status="active", source_chapter=1,
            payload={"expected_payoff": "Tournament", "urgency": 0.9},
        ))

        adapter = MemoryContractAdapter(cfg)
        loops = adapter.get_open_loops()
        assert len(loops) == 1
        assert loops[0].content == "Xiao Yan and Nalan Yanran's three-year challenge"
        assert loops[0].urgency == 0.9

    def test_get_open_loops_with_string_urgency_does_not_crash(self, tmp_path):
        """Regression tests: data-agent Output string urgency when，The whole batch of foreshadowing must not disappear。

        Issue root cause: ``get_open_loops`` Internal use ``float("high")`` raise
        ``ValueError``，outer ``except`` fallback return ``[]``，all foreshadowing disappears together。
        """
        cfg = _make_project(tmp_path)
        from data_modules.memory.schema import MemoryItem
        from data_modules.memory.store import ScratchpadManager

        store = ScratchpadManager(cfg)
        # Simulation LLM three typical string values written，plus one normal numeric value
        for idx, urgency in enumerate(["high", "medium", "low", 75]):
            store.upsert_item(MemoryItem(
                id=f"ol-str-{idx}",
                layer="semantic",
                category="open_loop",
                subject=f"loop-{idx}",
                field="",
                value=f"foreshadowing {idx}",
                status="active",
                source_chapter=idx + 1,
                payload={"urgency": urgency, "expected_payoff": ""},
            ))

        adapter = MemoryContractAdapter(cfg)
        loops = adapter.get_open_loops()
        # key: 4 return all entries，not because one string triggered it except the entire batch disappears afterward
        assert len(loops) == 4
        urgencies = sorted(loop.urgency for loop in loops)
        # high=100, medium=60, low=20, numeric=75 → after sorting, expect [20, 60, 75, 100]
        assert urgencies == [20.0, 60.0, 75.0, 100.0]


class TestGetTimeline:
    def test_get_timeline_empty(self, tmp_path):
        cfg = _make_project(tmp_path)
        adapter = MemoryContractAdapter(cfg)
        assert adapter.get_timeline(1, 100) == []

    def test_get_timeline_filters_by_range(self, tmp_path):
        cfg = _make_project(tmp_path)
        from data_modules.memory.schema import MemoryItem
        from data_modules.memory.store import ScratchpadManager

        store = ScratchpadManager(cfg)
        for ch in [5, 10, 50, 100]:
            store.upsert_item(MemoryItem(
                id=f"tl-{ch}", layer="semantic", category="timeline",
                subject="event", field=f"No.{ch}at chapter", value=f"event{ch}",
                status="active", source_chapter=ch,
            ))

        adapter = MemoryContractAdapter(cfg)
        events = adapter.get_timeline(8, 55)
        assert len(events) == 2
        assert events[0].chapter == 10
        assert events[1].chapter == 50


class TestLoadContext:
    def test_load_context_returns_context_pack(self, tmp_path):
        cfg = _make_project(tmp_path)
        adapter = MemoryContractAdapter(cfg)
        pack = adapter.load_context(10)
        assert isinstance(pack, ContextPack)
        assert pack.chapter == 10

    def test_load_context_includes_protagonist(self, tmp_path):
        cfg = _make_project(tmp_path)
        state = {
            "progress": {"current_chapter": 9},
            "protagonist_state": {"location": "Jianan Academy", "power": {"realm": "Dou Shi"}},
        }
        cfg.state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

        adapter = MemoryContractAdapter(cfg)
        pack = adapter.load_context(10)
        assert "protagonist" in pack.sections
        assert pack.sections["protagonist"]["location"] == "Jianan Academy"
        assert "progress" in pack.sections

    def test_load_context_includes_recent_summaries(self, tmp_path):
        cfg = _make_project(tmp_path)
        summary_dir = cfg.webnovel_dir / "summaries"
        summary_dir.mkdir(parents=True, exist_ok=True)
        (summary_dir / "ch0008.md").write_text("chapter-8-summary content", encoding="utf-8")
        (summary_dir / "ch0009.md").write_text("chapter-9-summary content", encoding="utf-8")

        adapter = MemoryContractAdapter(cfg)
        pack = adapter.load_context(10)
        assert "recent_summaries" in pack.sections
        assert "ch0008" in pack.sections["recent_summaries"]
        assert "ch0009" in pack.sections["recent_summaries"]

    def test_load_context_includes_rules_and_loops(self, tmp_path):
        cfg = _make_project(tmp_path)
        from data_modules.memory.schema import MemoryItem
        from data_modules.memory.store import ScratchpadManager

        store = ScratchpadManager(cfg)
        store.upsert_item(MemoryItem(
            id="rule-1", layer="semantic", category="world_rule",
            subject="power-system", field="exotic flame", value="23kinds",
            status="active", source_chapter=1,
        ))
        store.upsert_item(MemoryItem(
            id="ol-1", layer="semantic", category="open_loop",
            subject="three-year challenge", field="", value="Xiao Yan and Nalan Yanran's three-year challenge",
            status="active", source_chapter=1,
        ))

        adapter = MemoryContractAdapter(cfg)
        pack = adapter.load_context(10)
        assert "active_rules" in pack.sections
        assert len(pack.sections["active_rules"]) == 1
        assert "urgent_loops" in pack.sections
        assert len(pack.sections["urgent_loops"]) == 1

    def test_load_context_includes_story_runtime_sections(self, tmp_path):
        cfg = _make_project(tmp_path)
        story_root = tmp_path / ".story-system"
        (story_root / "chapters").mkdir(parents=True, exist_ok=True)
        (story_root / "volumes").mkdir(parents=True, exist_ok=True)
        (story_root / "reviews").mkdir(parents=True, exist_ok=True)
        (story_root / "commits").mkdir(parents=True, exist_ok=True)

        (story_root / "MASTER_SETTING.json").write_text(
            json.dumps(
                {
                    "meta": {"contract_type": "MASTER_SETTING"},
                    "route": {"primary_genre": "xuanhuan"},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (story_root / "volumes" / "volume_001.json").write_text(
            json.dumps({"meta": {"contract_type": "VOLUME_BRIEF"}}, ensure_ascii=False),
            encoding="utf-8",
        )
        (story_root / "chapters" / "chapter_003.json").write_text(
            json.dumps({"meta": {"contract_type": "CHAPTER_BRIEF", "chapter": 3}}, ensure_ascii=False),
            encoding="utf-8",
        )
        (story_root / "reviews" / "chapter_003.review.json").write_text(
            json.dumps({"meta": {"contract_type": "REVIEW_CONTRACT", "chapter": 3}}, ensure_ascii=False),
            encoding="utf-8",
        )
        (story_root / "commits" / "chapter_003.commit.json").write_text(
            json.dumps(
                {
                    "meta": {"chapter": 3, "status": "accepted"},
                    "provenance": {"write_fact_role": "chapter_commit"},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        adapter = MemoryContractAdapter(cfg)
        pack = adapter.load_context(3)

        assert pack.sections["story_contracts"]["master"]["route"]["primary_genre"] == "xuanhuan"
        assert pack.sections["runtime_status"]["primary_write_source"] == "chapter_commit"
        assert pack.sections["latest_commit"]["meta"]["status"] == "accepted"

    def test_load_context_genre_profile_fallback_reads_project_info(self, tmp_path):
        cfg = _make_project(tmp_path)
        (cfg.webnovel_dir / "state.json").write_text(
            json.dumps({"project_info": {"genre": "rules-horror"}}, ensure_ascii=False),
            encoding="utf-8",
        )
        refs_dir = tmp_path / ".claude" / "references"
        refs_dir.mkdir(parents=True, exist_ok=True)
        (refs_dir / "genre-profiles.md").write_text("## rules-horror\n- Rules first", encoding="utf-8")

        adapter = MemoryContractAdapter(cfg)
        pack = adapter.load_context(1)

        assert "Rules first" in pack.sections["genre_profile_excerpt"]

    def test_load_context_prefers_actual_latest_commit_status(self, tmp_path):
        cfg = _make_project(tmp_path)
        story_root = tmp_path / ".story-system"
        (story_root / "chapters").mkdir(parents=True, exist_ok=True)
        (story_root / "reviews").mkdir(parents=True, exist_ok=True)
        (story_root / "commits").mkdir(parents=True, exist_ok=True)
        (story_root / "MASTER_SETTING.json").write_text(
            json.dumps({"meta": {"contract_type": "MASTER_SETTING"}}, ensure_ascii=False),
            encoding="utf-8",
        )
        (story_root / "chapters" / "chapter_003.json").write_text(
            json.dumps({"meta": {"contract_type": "CHAPTER_BRIEF", "chapter": 3}}, ensure_ascii=False),
            encoding="utf-8",
        )
        (story_root / "reviews" / "chapter_003.review.json").write_text(
            json.dumps({"meta": {"contract_type": "REVIEW_CONTRACT", "chapter": 3}}, ensure_ascii=False),
            encoding="utf-8",
        )
        (story_root / "commits" / "chapter_002.commit.json").write_text(
            json.dumps({"meta": {"chapter": 2, "status": "accepted"}}, ensure_ascii=False),
            encoding="utf-8",
        )
        (story_root / "commits" / "chapter_003.commit.json").write_text(
            json.dumps({"meta": {"chapter": 3, "status": "rejected"}}, ensure_ascii=False),
            encoding="utf-8",
        )

        adapter = MemoryContractAdapter(cfg)
        pack = adapter.load_context(3)

        assert pack.sections["latest_commit"]["meta"]["status"] == "rejected"
        assert pack.sections["runtime_status"]["latest_accepted_commit"]["meta"]["status"] == "accepted"


class TestCommitChapter:
    def test_commit_chapter_basic(self, tmp_path):
        cfg = _make_project(tmp_path)
        adapter = MemoryContractAdapter(cfg)
        result = adapter.commit_chapter(1, {
            "entities_appeared": [{"id": "xiaoyan", "type": "character"}],
            "entities_new": [],
            "state_changes": [],
            "relationships_new": [],
        })
        assert isinstance(result, CommitResult)
        assert result.chapter == 1
        assert result.entities_updated == 1

    def test_commit_chapter_delegates_to_chapter_commit_mainline(self, tmp_path):
        cfg = _make_project(tmp_path)
        adapter = MemoryContractAdapter(cfg)

        result = adapter.commit_chapter(
            3,
            {
                "review_result": {"blocking_count": 0},
                "fulfillment_result": {
                    "planned_nodes": ["Discover the trap"],
                    "covered_nodes": ["Discover the trap"],
                    "missed_nodes": [],
                    "extra_nodes": [],
                },
                "disambiguation_result": {"pending": []},
                "extraction_result": {
                    "state_deltas": [],
                    "entity_deltas": [],
                    "accepted_events": [],
                    "summary_text": "Chapter summary",
                },
            },
        )

        assert (tmp_path / ".story-system" / "commits" / "chapter_003.commit.json").is_file()
        assert result.chapter == 3
        assert "commit_status=accepted" in result.warnings


class TestLoadContextAuthorStyle:
    """issue #131: load_context must consume project_memory.json and style-guide.md。"""

    def _write_memory(self, tmp_path: Path, patterns) -> None:
        (tmp_path / ".webnovel" / "project_memory.json").write_text(
            json.dumps({"patterns": patterns}, ensure_ascii=False), encoding="utf-8"
        )

    def test_author_style_patterns_present(self, tmp_path):
        cfg = _make_project(tmp_path)
        self._write_memory(
            tmp_path,
            [
                {
                    "pattern_type": "Writing style",
                    "description": 'Avoid vague references such as "something".',
                    "source_chapter": 1,
                    "importance": "5",
                },
                {
                    "pattern_type": "pacing",
                    "description": "Introduce conflict within the first three paragraphs。",
                    "importance": "low",
                },
            ],
        )
        pack = MemoryContractAdapter(cfg).load_context(chapter=3)
        section = pack.sections.get("author_style_patterns")
        assert section, "load_context Not returned author_style_patterns (issue #131 Main complaint)"
        assert any("vague reference" in str(p.get("description", "")) for p in section)

    def test_patterns_sorted_by_importance_and_capped(self, tmp_path):
        cfg = _make_project(tmp_path)
        patterns = [
            {"pattern_type": "low", "description": f"low-priority rule{i}", "importance": "low"}
            for i in range(12)
        ]
        patterns.append(
            {"pattern_type": "high", "description": "most important rule", "importance": "5"}
        )
        self._write_memory(tmp_path, patterns)
        pack = MemoryContractAdapter(cfg).load_context(chapter=2)
        section = pack.sections["author_style_patterns"]
        assert len(section) <= 10, "patterns not according to token Budget truncation"
        assert section[0]["description"] == "most important rule", "high importance was not ranked first"

    def test_style_contract_present(self, tmp_path):
        cfg = _make_project(tmp_path)
        settings = tmp_path / "settings"
        settings.mkdir(exist_ok=True)
        (settings / "style-guide.md").write_text("Prefer short sentences，Use fewer idioms。", encoding="utf-8")
        pack = MemoryContractAdapter(cfg).load_context(chapter=2)
        assert "Prefer short sentences" in str(pack.sections.get("style_contract", ""))

    def test_absent_files_sections_omitted(self, tmp_path):
        cfg = _make_project(tmp_path)
        pack = MemoryContractAdapter(cfg).load_context(chapter=2)
        assert "author_style_patterns" not in pack.sections
        assert "style_contract" not in pack.sections

    def test_malformed_memory_does_not_crash(self, tmp_path):
        cfg = _make_project(tmp_path)
        (tmp_path / ".webnovel" / "project_memory.json").write_text(
            "{broken json", encoding="utf-8"
        )
        pack = MemoryContractAdapter(cfg).load_context(chapter=2)
        assert "author_style_patterns" not in pack.sections
