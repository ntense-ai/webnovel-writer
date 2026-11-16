#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StyleSampler extra tests + CLI
"""

import sys
import json

import pytest

import data_modules.style_sampler as sampler_module
from data_modules.style_sampler import StyleSampler, StyleSample, SceneType
from data_modules.config import DataModulesConfig


@pytest.fixture
def temp_project(tmp_path):
    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    if not cfg.state_file.exists():
        cfg.state_file.write_text("{}", encoding="utf-8")
    return cfg


def test_style_sampler_more(temp_project):
    sampler = StyleSampler(temp_project)

    sample = StyleSample(
        id="ch1_s1",
        chapter=1,
        scene_type=SceneType.BATTLE.value,
        content="excellent combat description",
        score=0.9,
        tags=["combat"],
    )
    assert sampler.add_sample(sample) is True
    assert sampler.add_sample(sample) is False

    best = sampler.get_best_samples(limit=5)
    assert len(best) == 1

    stats = sampler.get_stats()
    assert stats["total"] == 1

    # scene type inference
    assert sampler._infer_scene_types("a battle") == [SceneType.BATTLE.value]
    assert sampler._infer_scene_types("dialogue and conversation") == [SceneType.DIALOGUE.value]
    assert sampler._infer_scene_types("psychological and emotional description") == [SceneType.EMOTION.value]

    # classify and tags
    scene_type = sampler._classify_scene_type({"summary": "tension", "content": ""})
    assert scene_type == SceneType.TENSION.value

    tags = sampler._extract_tags("combat cultivation conversation description")
    assert "combat" in tags


def test_style_sampler_ignores_corrupt_tag_json(temp_project):
    sampler = StyleSampler(temp_project)
    with sampler._get_conn() as conn:
        conn.execute(
            """
            INSERT INTO samples
            (id, chapter, scene_type, content, score, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ("bad-tags", 1, SceneType.BATTLE.value, "combat description" * 50, 0.8, "[bad-json"),
        )
        conn.commit()

    samples = sampler.get_best_samples(limit=5)

    assert samples[0].id == "bad-tags"
    assert samples[0].tags == []


def test_style_sampler_cli(temp_project, monkeypatch, capsys):
    root = str(temp_project.project_root)

    def run_cli(args):
        monkeypatch.setattr(sys, "argv", ["style_sampler"] + args)
        sampler_module.main()

    run_cli(["--project-root", root, "stats"])
    run_cli(["--project-root", root, "list", "--limit", "5"])
    run_cli(
        [
            "--project-root",
            root,
            "extract",
            "--chapter",
            "1",
            "--score",
            "90",
            "--scenes",
            json.dumps(
                [
                    {
                        "index": 1,
                        "summary": "combat scene",
                        "content": "combat" + "a" * 300,
                    }
                ],
                ensure_ascii=False,
            ),
        ]
    )
    run_cli(["--project-root", root, "list", "--type", "combat", "--limit", "5"])
    run_cli(["--project-root", root, "select", "--outline", "this chapter contains a battle", "--max", "2"])

    capsys.readouterr()
