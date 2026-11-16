#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from chapter_outline_loader import load_chapter_execution_directive


def test_load_chapter_execution_directive_from_volume_outline(tmp_path):
    outline_dir = tmp_path / "outlines"
    outline_dir.mkdir()
    (tmp_path / ".webnovel").mkdir()
    (tmp_path / ".webnovel" / "state.json").write_text(
        json.dumps({"progress": {"volumes_planned": [{"volume": 1, "chapters_range": "1-50"}]}}),
        encoding="utf-8",
    )
    (outline_dir / "volume-1-outline.md").write_text(
        "\n".join(
            [
                "### Chapter 1: Debt from Nowhere",
                "- Goal: Understand the absurd terms of the debt note",
                "- Obstacle: Servants cannot leave the sect freely",
                "- Cost: reveal knowledge of accounting",
                "- Time anchor: D-Day dawn",
                "- Chapter span: one incense stick",
                "- Countdown status: repay within three days",
                "- Strand: Debt investigation",
                "- Antagonist tier: minor",
                "- Key entities: Lu Ming、debt note、Interest",
                "- CBN: wake to discover a debt",
                "- CPNs: Inspect the debt note; discover the compound-interest trap",
                "- CEN: decides to ask around the well",
                "- Must-cover nodes: debt-note amount; compound-interest formula",
                "- Chapter prohibitions: Do not leave the sect; Do not reveal the hand early",
                "- Chapter-end open question: Who changed the debt note？",
                "- Hook type: information",
                "- Hook strength: medium",
                "",
                "### Chapter 2: Rumors at the well",
                "- Goal: investigate the creditor's origins",
            ]
        ),
        encoding="utf-8",
    )

    directive = load_chapter_execution_directive(tmp_path, 1)

    assert directive["goal"] == "Understand the absurd terms of the debt note"
    assert directive["time_anchor"] == "D-Day dawn"
    assert directive["chapter_span"] == "one incense stick"
    assert directive["countdown"] == "repay within three days"
    assert directive["cpns"] == ["Inspect the debt note", "discover the compound-interest trap"]
    assert "Do not leave the sect" in directive["forbidden_zones"]
    assert "debt note" in directive["key_entities"]
    assert directive["chapter_end_open_question"] == "Who changed the debt note？"
