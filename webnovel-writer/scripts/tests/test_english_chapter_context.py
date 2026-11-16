"""English chapter context without losing legacy Chinese book support."""
import json
import re

import pytest

import extract_chapter_context as context


@pytest.mark.parametrize("outline,topic", [
    ("Alice confronts her MENTOR about their broken alliance.", "Character relationships"),
    ("The factions contest a new location beyond the mountains.", "Locations, factions"),
    ("Recover the clues hidden in the library for a later payoff.", "Foreshadowing and clues"),
    ("The truth of the ancient conflict becomes clear at last.", "Key plot evidence"),
    ("The protagonist discovers the secret of a mentor relationship and seeks answers among hostile allies.", "Character relationships"),
])
def test_bilingual_rag_query(outline, topic):
    query = context._build_rag_query(outline, 12, min_chars=20, max_chars=120)
    assert query.startswith(f"Chapter 12 {topic}")
    assert outline in query


def test_rag_avoids_english_substring_false_positive():
    assert not context._build_rag_query("The original draft is a calm walk through fields.", 1, 20, 120)
    assert not context._build_rag_query("clue", 1, 20, 120)


@pytest.mark.parametrize("heading", ["Plot summary", "CHAPTER SUMMARY", "Summary", "Plot summary"])
def test_saved_summary_heading(tmp_path, heading):
    folder = tmp_path / ".webnovel" / "summaries"
    folder.mkdir(parents=True)
    (folder / "ch0001.md").write_text(f"## {heading}\nAlice finds a clue.\n## Metadata\nNot summary.")
    assert context.extract_chapter_summary(tmp_path, 1) == "Alice finds a clue."


@pytest.mark.parametrize("heading", ["Chapter summary", "Chapter summary"])
def test_body_summary_heading(tmp_path, monkeypatch, heading):
    chapter = tmp_path / "chapter.md"
    chapter.write_text(f"# Chapter 1\nText.\n## {heading}\nThe answer.\n## Notes\nExcluded.")
    monkeypatch.setattr(context, "find_chapter_file", lambda *_: chapter)
    assert context.extract_chapter_summary(tmp_path, 1) == "The answer."


def test_generated_state_summary_is_english(tmp_path):
    folder = tmp_path / ".webnovel"
    folder.mkdir()
    (folder / "state.json").write_text(json.dumps({
        "progress": {"current_chapter": 3, "total_words": 6000},
        "protagonist_state": {"power": {"realm": "Apprentice", "layer": 2},
                              "location": "Library", "golden_finger": {"name": "Sight", "level": 1}},
        "strand_tracker": {"history": [{"chapter": 2, "strand": "quest"}]},
        "plot_threads": {"foreshadowing": [{"status": "active", "content": "The key", "urgency": 80}]},
    }))
    result = context.extract_state_summary(tmp_path)
    assert "Chapter 3 / 6000 words" in result
    assert "Urgent foreshadowing" in result
    assert "urgency:80" in result
    assert not re.search(r"[\u4e00-\u9fff]", result)
