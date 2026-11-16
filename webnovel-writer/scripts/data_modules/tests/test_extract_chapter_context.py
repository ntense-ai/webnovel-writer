#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path


def test_extract_state_summary_accepts_dominant_key(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import extract_state_summary

    state = {
        "progress": {"current_chapter": 12, "total_words": 12345},
        "protagonist_state": {
            "power": {"realm": "foundation-establishment", "layer": 2},
            "location": "sect",
            "golden_finger": {"name": "System", "level": 1},
        },
        "strand_tracker": {
            "history": [
                {"chapter": 10, "dominant": "quest"},
                {"chapter": 11, "dominant": "fire"},
            ]
        },
    }

    webnovel_dir = tmp_path / ".webnovel"
    webnovel_dir.mkdir(parents=True, exist_ok=True)
    (webnovel_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    text = extract_state_summary(tmp_path)
    assert "Ch10:quest" in text
    assert "Ch11:fire" in text


def test_extract_chapter_outline_supports_hyphen_filename(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import extract_chapter_outline

    outline_dir = tmp_path / "outlines"
    outline_dir.mkdir(parents=True, exist_ok=True)
    (outline_dir / "volume-1-outline.md").write_text("### Chapter 1: Test title\nTest outline", encoding="utf-8")

    outline = extract_chapter_outline(tmp_path, 1)
    assert "### Chapter 1: Test title" in outline
    assert "Test outline" in outline


def test_extract_chapter_outline_prefers_state_volume_mapping(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import extract_chapter_outline

    webnovel_dir = tmp_path / ".webnovel"
    webnovel_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "progress": {
            "volumes_planned": [
                {"volume": 1, "chapters_range": "1-10"},
                {"volume": 2, "chapters_range": "11-20"},
            ]
        }
    }
    (webnovel_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    outline_dir = tmp_path / "outlines"
    outline_dir.mkdir(parents=True, exist_ok=True)
    (outline_dir / "volume-2-outline.md").write_text("### Chapter 12: V2Title\nV2outlines", encoding="utf-8")

    outline = extract_chapter_outline(tmp_path, 12)
    assert "### Chapter 12: V2Title" in outline
    assert "V2outlines" in outline


def test_extract_chapter_outline_falls_back_when_state_has_no_match(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import extract_chapter_outline

    webnovel_dir = tmp_path / ".webnovel"
    webnovel_dir.mkdir(parents=True, exist_ok=True)
    state = {"progress": {"volumes_planned": [{"volume": 1, "chapters_range": "1-10"}]}}
    (webnovel_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    outline_dir = tmp_path / "outlines"
    outline_dir.mkdir(parents=True, exist_ok=True)
    (outline_dir / "volume-2-outline.md").write_text("### Chapter 60: V2Title\nV2outlines", encoding="utf-8")

    outline = extract_chapter_outline(tmp_path, 60)
    assert "### Chapter 60: V2Title" in outline
    assert "V2outlines" in outline


def test_build_chapter_context_payload_includes_contract_sections(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import build_chapter_context_payload
    from data_modules.config import DataModulesConfig
    from data_modules.index_manager import IndexManager, ChapterReadingPowerMeta, ReviewMetrics

    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()

    state = {
        "project": {"genre": "xuanhuan"},
        "progress": {"current_chapter": 3, "total_words": 9000},
        "protagonist_state": {
            "power": {"realm": "foundation-establishment", "layer": 2},
            "location": "sect",
            "golden_finger": {"name": "System", "level": 1},
        },
        "strand_tracker": {"history": [{"chapter": 2, "dominant": "quest"}]},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    (cfg.webnovel_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    summaries_dir = cfg.webnovel_dir / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    (summaries_dir / "ch0002.md").write_text("## Plot Summary\nPrevious chapter summary", encoding="utf-8")

    outline_dir = tmp_path / "outlines"
    outline_dir.mkdir(parents=True, exist_ok=True)
    (outline_dir / "volume-1-outline.md").write_text("### Chapter 3: Test title\nTest outline", encoding="utf-8")

    refs_dir = tmp_path / ".claude" / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    (refs_dir / "genre-profiles.md").write_text("## xuanhuan\n- Clear progression arc", encoding="utf-8")
    (refs_dir / "reading-power-taxonomy.md").write_text("## xuanhuan\n- Prioritize suspense hooks", encoding="utf-8")

    idx = IndexManager(cfg)
    idx.save_chapter_reading_power(
        ChapterReadingPowerMeta(chapter=2, hook_type="mystery", hook_strength="strong", coolpoint_patterns=["Identity revelation"])
    )
    idx.save_review_metrics(
        ReviewMetrics(start_chapter=1, end_chapter=2, overall_score=71, dimension_scores={"plot": 71})
    )

    story_root = tmp_path / ".story-system"
    (story_root / "chapters").mkdir(parents=True, exist_ok=True)
    (story_root / "volumes").mkdir(parents=True, exist_ok=True)
    (story_root / "reviews").mkdir(parents=True, exist_ok=True)
    (story_root / "commits").mkdir(parents=True, exist_ok=True)
    (story_root / "MASTER_SETTING.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
                "route": {"primary_genre": "xuanhuan"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "volumes" / "volume_001.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "VOLUME_BRIEF"},
                "volume_goal": {"summary": "Volume One goal"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "chapters" / "chapter_003.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "CHAPTER_BRIEF", "chapter": 3},
                "override_allowed": {"chapter_focus": "Test title"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "reviews" / "chapter_003.review.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "REVIEW_CONTRACT", "chapter": 3},
                "blocking_rules": ["Do not reveal the hand early"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (story_root / "commits" / "chapter_003.commit.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "chapter": 3, "status": "accepted"},
                "provenance": {"write_fact_role": "chapter_commit"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = build_chapter_context_payload(tmp_path, 3)
    assert payload["context_contract_version"] == "v3"
    assert payload.get("context_weight_stage") in {"early", "mid", "late"}
    assert "writing_guidance" in payload
    assert isinstance(payload["writing_guidance"].get("guidance_items"), list)
    assert isinstance(payload["writing_guidance"].get("checklist"), list)
    assert isinstance(payload["writing_guidance"].get("checklist_score"), dict)
    assert payload["genre_profile"].get("genre") == "xuanhuan"
    assert "rag_assist" in payload
    assert isinstance(payload["rag_assist"], dict)
    assert payload["rag_assist"].get("invoked") is False
    assert "long_term_memory" in payload
    assert payload["runtime_status"]["primary_write_source"] == "chapter_commit"
    assert payload["latest_commit"]["meta"]["status"] == "accepted"


def test_build_chapter_context_payload_exposes_latest_rejected_commit(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import build_chapter_context_payload
    from data_modules.config import DataModulesConfig

    cfg = DataModulesConfig.from_project_root(tmp_path)
    cfg.ensure_dirs()
    cfg.state_file.write_text(
        json.dumps(
            {
                "project": {"genre": "cultivation"},
                "progress": {"current_chapter": 2},
                "protagonist_state": {"name": "Han Li"},
                "chapter_meta": {},
                "disambiguation_warnings": [],
                "disambiguation_pending": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    outline_dir = tmp_path / "outlines"
    outline_dir.mkdir(parents=True, exist_ok=True)
    (outline_dir / "volume-1-outline.md").write_text("### Chapter 3: Test title\nTest outline", encoding="utf-8")

    story_root = tmp_path / ".story-system"
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

    payload = build_chapter_context_payload(tmp_path, 3)

    assert payload["latest_commit"]["meta"]["status"] == "rejected"


def test_render_text_contains_writing_guidance_section(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import _render_text

    payload = {
        "chapter": 10,
        "outline": "Test outline",
        "previous_summaries": ["### Chapter 9 summary\nprevious chapter"],
        "state_summary": "State",
        "context_contract_version": "v2",
        "context_weight_stage": "early",
        "reader_signal": {"review_trend": {"overall_avg": 72}, "low_score_ranges": [{"start_chapter": 8, "end_chapter": 9}]},
        "genre_profile": {
            "genre": "xuanhuan",
            "genres": ["xuanhuan", "realistic"],
            "composite_hints": ["Advance the xuanhuan main plot，retain commentary on real-world issues"],
            "reference_hints": ["Clear progression arc"],
        },
        "writing_guidance": {
            "guidance_items": ["Fix low scores first", "Hook differentiation"],
            "checklist": [
                {
                    "id": "fix_low_score_range",
                    "label": "Fix issues in the low-scoring range",
                    "weight": 1.4,
                    "required": True,
                    "source": "reader_signal.low_score_ranges",
                    "verify_hint": "Complete at least1conflict escalations",
                }
            ],
            "checklist_score": {
                "score": 81.5,
                "completion_rate": 0.66,
                "required_completion_rate": 0.75,
            },
            "methodology": {
                "enabled": True,
                "framework": "digital-serial-v1",
                "pilot": "xianxia",
                "genre_profile_key": "xianxia",
                "chapter_stage": "confront",
                "observability": {
                    "next_reason_clarity": 78.0,
                    "anchor_effectiveness": 74.0,
                    "rhythm_naturalness": 72.0,
                },
                "signals": {"risk_flags": ["pattern_overuse_watch"]},
            },
        },
    }

    text = _render_text(payload)
    parsed = json.loads(text)
    assert "writing_guidance" in parsed
    assert parsed["writing_guidance"]["guidance_items"][0] == "Fix low scores first"
    assert parsed["context_contract_version"] == "v2"
    assert parsed["context_weight_stage"] == "early"
    assert parsed["writing_guidance"]["checklist"][0]["label"] == "Fix issues in the low-scoring range"
    assert parsed["writing_guidance"]["checklist_score"]["score"] == 81.5
    assert parsed["genre_profile"]["genres"] == ["xuanhuan", "realistic"]
    assert parsed["writing_guidance"]["methodology"]["enabled"] is True
    assert parsed["writing_guidance"]["methodology"]["genre_profile_key"] == "xianxia"


def test_render_text_contains_rag_assist_section_when_hits_exist(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import _render_text

    payload = {
        "chapter": 12,
        "outline": "Test outline",
        "previous_summaries": [],
        "state_summary": "State",
        "context_contract_version": "v2",
        "reader_signal": {},
        "genre_profile": {},
        "writing_guidance": {},
        "rag_assist": {
            "invoked": True,
            "mode": "auto",
            "intent": "relationship",
            "query": "Chapter 12 Character relationships and motivation: Xiao Yan and Yao Lao clash",
            "hits": [
                {
                    "chapter": 9,
                    "scene_index": 2,
                    "source": "graph_hybrid",
                    "score": 0.91,
                    "content": "Xiao Yan and Yao Lao disagree about cultivation。",
                }
            ],
        },
    }

    text = _render_text(payload)
    parsed = json.loads(text)
    assert parsed["rag_assist"]["invoked"] is True
    assert parsed["rag_assist"]["mode"] == "auto"
    assert parsed["rag_assist"]["hits"][0]["source"] == "graph_hybrid"
    assert "Xiao Yan and Yao Lao" in parsed["rag_assist"]["hits"][0]["content"]


def test_build_chapter_context_payload_includes_plot_structure(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import build_chapter_context_payload

    webnovel_dir = tmp_path / ".webnovel"
    webnovel_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "project": {"genre": "xuanhuan"},
        "progress": {"current_chapter": 5, "total_words": 15000},
        "protagonist_state": {},
        "chapter_meta": {},
        "disambiguation_warnings": [],
        "disambiguation_pending": [],
    }
    (webnovel_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    outline_dir = tmp_path / "outlines"
    outline_dir.mkdir(parents=True, exist_ok=True)
    (outline_dir / "volume-1-outline.md").write_text(
        """### Chapter 5: Trial Opening
CBN: Xiao Yan reaches the outer-court trial grounds
CPNs:
- The mentor announces the trial rules
- Xiao Yan discovers someone tampered with the rules
CEN: Xiao Yan decides to endure and observe
Must-cover nodes: expose abnormal rules、Decides to endure
Chapter prohibitions: Do not expose the mastermind directly
""",
        encoding="utf-8",
    )

    payload = build_chapter_context_payload(tmp_path, 5)
    plot_structure = payload.get("plot_structure") or {}
    assert plot_structure.get("cbn") == "Xiao Yan reaches the outer-court trial grounds"
    assert plot_structure.get("cpns") == ["The mentor announces the trial rules", "Xiao Yan discovers someone tampered with the rules"]
    assert plot_structure.get("cen") == "Xiao Yan decides to endure and observe"
    assert plot_structure.get("mandatory_nodes") == ["expose abnormal rules", "Decides to endure"]
    assert plot_structure.get("prohibitions") == ["Do not expose the mastermind directly"]


def test_render_text_contains_plot_structure_section(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import _render_text

    payload = {
        "chapter": 8,
        "outline": "Test outline",
        "previous_summaries": [],
        "state_summary": "State",
        "context_contract_version": "v2",
        "plot_structure": {
            "cbn": "The protagonist enters the ruins",
            "cpns": ["discover an anomaly in the stone tablet", "brief clash with the guard"],
            "cen": "decides to enter the heart of the ruins",
            "mandatory_nodes": ["discover an anomaly in the stone tablet"],
            "prohibitions": ["Do not obtain the ultimate inheritance early"],
        },
        "reader_signal": {},
        "genre_profile": {},
        "writing_guidance": {},
        "rag_assist": {"invoked": False, "hits": []},
    }

    text = _render_text(payload)
    parsed = json.loads(text)
    assert parsed["plot_structure"]["cbn"] == "The protagonist enters the ruins"
    assert parsed["plot_structure"]["cpns"] == ["discover an anomaly in the stone tablet", "brief clash with the guard"]
    assert parsed["plot_structure"]["cen"] == "decides to enter the heart of the ruins"
    assert "Do not obtain the ultimate inheritance early" in parsed["plot_structure"]["prohibitions"]


def test_render_text_contains_contract_first_runtime_section(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import _render_text

    payload = {
        "chapter": 12,
        "outline": "Test outline",
        "previous_summaries": [],
        "state_summary": "State",
        "context_contract_version": "v2",
        "context_weight_stage": "mid",
        "story_contract": {
            "review_contract": {
                "blocking_rules": ["Do not reveal the hand early", "Do not let a supporting character deliver the protagonist's payoff"],
            }
        },
        "prewrite_validation": {
            "blocking": False,
            "forbidden_zones": ["Do not reveal the hand early"],
            "fulfillment_seed": {"planned_nodes": ["Discover the trap", "Decides to endure"]},
        },
        "plot_structure": {},
        "reader_signal": {},
        "genre_profile": {},
        "writing_guidance": {},
        "rag_assist": {"invoked": False, "hits": []},
    }

    text = _render_text(payload)
    parsed = json.loads(text)
    assert len(parsed["story_contract"]["review_contract"]["blocking_rules"]) == 2
    assert parsed["prewrite_validation"]["blocking"] is False


def test_render_text_contains_runtime_status_section(tmp_path):
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from extract_chapter_context import _render_text

    text = _render_text(
        {
            "chapter": 3,
            "outline": "Test outline",
            "previous_summaries": [],
            "state_summary": "old state summary",
            "context_contract_version": "v2",
            "reader_signal": {},
            "genre_profile": {},
            "writing_guidance": {},
            "runtime_status": {
                "primary_write_source": "chapter_commit",
                "fallback_sources": ["missing_accepted_commit"],
            },
            "latest_commit": {"meta": {"chapter": 3, "status": "rejected"}},
        }
    )

    parsed = json.loads(text)
    assert parsed["runtime_status"]["primary_write_source"] == "chapter_commit"
    assert parsed["runtime_status"]["fallback_sources"] == ["missing_accepted_commit"]
