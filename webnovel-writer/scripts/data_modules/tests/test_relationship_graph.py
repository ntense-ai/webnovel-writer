#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
relationship event and graph tests
"""

import json
import sys

import pytest

import data_modules.index_manager as index_manager_module
from data_modules.config import DataModulesConfig
from data_modules.index_manager import (
    EntityMeta,
    IndexManager,
    RelationshipEventMeta,
    RelationshipMeta,
)


@pytest.fixture
def temp_project(tmp_path):
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    if not cfg.state_file.exists():
        cfg.state_file.write_text("{}", encoding="utf-8")
    return cfg


def test_relationship_events_timeline_and_subgraph(temp_project):
    manager = IndexManager(temp_project)
    manager.upsert_entity(
        EntityMeta(
            id="xiaoyan",
            type="character",
            canonical_name="Xiao Yan",
            tier="core",
            current={},
            first_appearance=1,
            last_appearance=10,
            is_protagonist=True,
        )
    )
    manager.upsert_entity(
        EntityMeta(
            id="yaolao",
            type="character",
            canonical_name="Yao Lao",
            tier="major",
            current={},
            first_appearance=1,
            last_appearance=10,
        )
    )
    manager.upsert_entity(
        EntityMeta(
            id="lintian",
            type="character",
            canonical_name="Lin Tian",
            tier="major",
            current={},
            first_appearance=2,
            last_appearance=10,
        )
    )
    manager.upsert_relationship(
        RelationshipMeta(
            from_entity="xiaoyan",
            to_entity="yaolao",
            type="mentor-student",
            description="formally accepts the master",
            chapter=3,
        )
    )
    manager.upsert_relationship(
        RelationshipMeta(
            from_entity="yaolao",
            to_entity="lintian",
            type="hostile",
            description="ideological conflict",
            chapter=5,
        )
    )
    event_id = manager.record_relationship_event(
        RelationshipEventMeta(
            from_entity="xiaoyan",
            to_entity="yaolao",
            type="mentor-student",
            chapter=3,
            action="create",
            polarity=1,
            strength=0.9,
            description="become a disciple",
            evidence="publicly accepts a disciple",
            confidence=0.95,
        )
    )
    assert event_id > 0
    manager.record_relationship_event(
        RelationshipEventMeta(
            from_entity="yaolao",
            to_entity="lintian",
            type="hostile",
            chapter=5,
            action="create",
            polarity=-1,
            strength=0.8,
            description="become enemies",
            evidence="mistake during a duel",
            confidence=0.8,
        )
    )

    events = manager.get_relationship_events("xiaoyan", direction="both", limit=20)
    assert events
    timeline = manager.get_relationship_timeline("xiaoyan", "yaolao", limit=20)
    assert timeline
    assert timeline[0]["type"] == "mentor-student"

    graph = manager.build_relationship_subgraph("xiaoyan", depth=2, chapter=10, top_edges=10)
    node_ids = {n["id"] for n in graph["nodes"]}
    assert "xiaoyan" in node_ids
    assert "yaolao" in node_ids
    assert "lintian" in node_ids
    assert graph["edges"]
    mermaid = manager.render_relationship_subgraph_mermaid(graph)
    assert "mermaid" in mermaid
    assert "mentor-student" in mermaid


def test_relationship_subgraph_respects_chapter_slice(temp_project):
    manager = IndexManager(temp_project)
    manager.upsert_entity(
        EntityMeta(
            id="a",
            type="character",
            canonical_name="A",
            current={},
            first_appearance=1,
            last_appearance=3,
            is_protagonist=True,
        )
    )
    manager.upsert_entity(
        EntityMeta(
            id="b",
            type="character",
            canonical_name="B",
            current={},
            first_appearance=1,
            last_appearance=3,
        )
    )
    manager.record_relationship_event(
        RelationshipEventMeta(
            from_entity="a",
            to_entity="b",
            type="alliance",
            chapter=1,
            action="create",
            polarity=1,
            strength=0.6,
        )
    )
    manager.record_relationship_event(
        RelationshipEventMeta(
            from_entity="a",
            to_entity="b",
            type="alliance",
            chapter=2,
            action="remove",
            polarity=0,
            strength=0.0,
        )
    )

    graph_ch1 = manager.build_relationship_subgraph("a", depth=1, chapter=1, top_edges=10)
    graph_ch3 = manager.build_relationship_subgraph("a", depth=1, chapter=3, top_edges=10)
    assert len(graph_ch1["edges"]) == 1
    assert len(graph_ch3["edges"]) == 0


def test_relationship_subgraph_fallbacks_to_snapshot_when_events_missing(temp_project):
    manager = IndexManager(temp_project)
    manager.upsert_entity(
        EntityMeta(
            id="a",
            type="character",
            canonical_name="A",
            current={},
            first_appearance=1,
            last_appearance=5,
            is_protagonist=True,
        )
    )
    manager.upsert_entity(
        EntityMeta(
            id="b",
            type="character",
            canonical_name="B",
            current={},
            first_appearance=1,
            last_appearance=5,
        )
    )
    # write only relationships snapshot，do not write relationship_events
    manager.upsert_relationship(
        RelationshipMeta(
            from_entity="a",
            to_entity="b",
            type="alliance",
            description="old snapshot data",
            chapter=3,
        )
    )

    graph = manager.build_relationship_subgraph("a", depth=1, chapter=3, top_edges=10)
    assert graph["edges"]
    assert graph["edges"][0]["action"] == "snapshot"
    assert graph["edges"][0]["type"] == "alliance"


def test_relationship_graph_cli_commands(temp_project, monkeypatch, capsys):
    manager = IndexManager(temp_project)
    manager.upsert_entity(
        EntityMeta(
            id="hero",
            type="character",
            canonical_name="protagonist",
            current={},
            first_appearance=1,
            last_appearance=1,
            is_protagonist=True,
        )
    )
    manager.upsert_entity(
        EntityMeta(
            id="mentor",
            type="character",
            canonical_name="master",
            current={},
            first_appearance=1,
            last_appearance=1,
        )
    )
    manager.record_relationship_event(
        RelationshipEventMeta(
            from_entity="hero",
            to_entity="mentor",
            type="mentor-student",
            chapter=1,
            action="create",
            polarity=1,
            strength=0.9,
        )
    )

    root = str(temp_project.project_root)

    def run_cli(args):
        monkeypatch.setattr(sys, "argv", ["index_manager"] + args)
        index_manager_module.main()
        output = capsys.readouterr().out.strip().splitlines()
        assert output
        return json.loads(output[-1])

    payload = run_cli(
        [
            "--project-root",
            root,
            "get-relationship-events",
            "--entity",
            "hero",
            "--direction",
            "both",
            "--limit",
            "10",
        ]
    )
    assert payload["status"] == "success"
    assert payload["data"]

    payload = run_cli(
        [
            "--project-root",
            root,
            "get-relationship-graph",
            "--center",
            "hero",
            "--depth",
            "1",
            "--chapter",
            "1",
            "--format",
            "mermaid",
        ]
    )
    assert payload["status"] == "success"
    assert "mermaid" in payload["data"]["mermaid"]

    payload = run_cli(
        [
            "--project-root",
            root,
            "get-relationship-timeline",
            "--a",
            "hero",
            "--b",
            "mentor",
            "--limit",
            "10",
        ]
    )
    assert payload["status"] == "success"
    assert payload["data"]

    payload = run_cli(
        [
            "--project-root",
            root,
            "record-relationship-event",
            "--data",
            json.dumps(
                {
                    "from_entity": "hero",
                    "type": "mentor-student",
                    "chapter": 1,
                },
                ensure_ascii=False,
            ),
        ]
    )
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "INVALID_RELATIONSHIP_EVENT"
