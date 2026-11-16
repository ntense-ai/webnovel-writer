"""English project directories and unchanged legacy project compatibility."""
from pathlib import Path

import pytest

import backup_manager
from backup_manager import GitBackupManager
from chapter_paths import default_chapter_draft_path, find_chapter_file, extract_chapter_title
from chapter_outline_loader import load_chapter_outline
from review_pipeline import _resolve_report_path
from update_master_outline import _require_current_volume_artifacts, _resolve_writeback_source


@pytest.mark.parametrize('chapters,outlines,reviews', [
    ('chapters', 'outlines', 'reviews'), ('正文', '大纲', '审查报告'),
])
def test_chapter_and_outline_paths_reuse_existing_layout(tmp_path, chapters, outlines, reviews):
    chapter_dir = tmp_path / chapters
    outline_dir = tmp_path / outlines
    chapter_dir.mkdir()
    outline_dir.mkdir()
    (tmp_path / reviews).mkdir()
    outline = outline_dir / '第1卷-详细大纲.md'
    outline.write_text('### 第1章：Arrival\nA traveler arrives.\n', encoding='utf-8')
    assert 'A traveler arrives.' in load_chapter_outline(tmp_path, 1)
    assert extract_chapter_title(tmp_path, 1) == 'Arrival'
    draft = default_chapter_draft_path(tmp_path, 1)
    assert draft == chapter_dir / ('chapter-0001-Arrival.md' if chapters == 'chapters' else '第0001章-Arrival.md')
    draft.write_text('Chapter prose')
    assert find_chapter_file(tmp_path, 1) == draft
    assert default_chapter_draft_path(tmp_path, 2, use_volume_layout=True).parent == chapter_dir / ('volume-1' if chapters == 'chapters' else '第1卷')
    assert _resolve_report_path(tmp_path, '审查报告/review.md') == tmp_path / reviews / 'review.md'
    assert _resolve_report_path(tmp_path, 'reviews/review.md') == tmp_path / reviews / 'review.md'


def test_new_draft_defaults_to_english_directory(tmp_path):
    assert default_chapter_draft_path(tmp_path, 1) == tmp_path / 'chapters/chapter-0001.md'


@pytest.mark.parametrize('folder', ['outlines', '大纲'])
def test_master_outline_artifacts_and_writeback_resolve_both_layouts(tmp_path, folder):
    outlines = tmp_path / folder
    outlines.mkdir()
    names = ['第1卷-节拍表.md', '第1卷-时间线.md', '第1卷-详细大纲.md']
    for name in names:
        (outlines / name).write_text('complete')
    assert _require_current_volume_artifacts(tmp_path, 1) == names
    expected = outlines / ('volume-1-master-outline-update.json' if folder == 'outlines' else '第1卷-总纲写回.json')
    assert _resolve_writeback_source(tmp_path, outlines, 1, 'outlines/第1卷-总纲写回.json') == expected
    assert _resolve_writeback_source(tmp_path, outlines, 1, '大纲/第1卷-总纲写回.json') == expected


def test_review_path_mapping_does_not_allow_traversal(tmp_path):
    with pytest.raises(ValueError, match='relative|project_root'):
        _resolve_report_path(tmp_path, 'reviews/../../outside.md')


def test_local_backup_preserves_both_directory_spellings(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_manager, 'is_git_available', lambda: False)
    names = ('chapters', 'outlines', 'settings', 'reviews', '正文', '大纲', '设定集', '审查报告')
    for name in names:
        (tmp_path / name).mkdir()
        (tmp_path / name / 'content.md').write_text(name, encoding='utf-8')
    manager = GitBackupManager(str(tmp_path))
    assert manager._local_backup(1) is True
    backup = next((tmp_path / '.webnovel/backups').glob('snapshot_ch*'))
    for name in names:
        assert (backup / name / 'content.md').read_text(encoding='utf-8') == name


def test_english_outline_headings_and_directives(tmp_path):
    from chapter_outline_loader import load_chapter_execution_directive
    outlines = tmp_path / 'outlines'
    outlines.mkdir()
    (outlines / 'volume-1-outline.md').write_text(
        "### Chapter 1: Arrival\n- Goal: Reach the city\n"
        "- Must-cover nodes: Meet the guide; Find the map\n"
        "- Chapter prohibitions: No secret reveal\n"
        "### Chapter 2: Departure\n- Goal: Leave the city\n"
    )
    text = load_chapter_outline(tmp_path, 1)
    assert 'Reach the city' in text
    assert 'Leave the city' not in text
    directive = load_chapter_execution_directive(tmp_path, 1)
    assert directive['goal'] == 'Reach the city'
    assert 'Meet the guide' in directive['must_cover_nodes']
    assert directive['forbidden_zones'] == ['No secret reveal']
    assert default_chapter_draft_path(tmp_path, 1).name == 'chapter-0001-Arrival.md'


def test_split_outline_does_not_confuse_chapter_one_and_ten(tmp_path):
    outlines = tmp_path / 'outlines'
    outlines.mkdir()
    (outlines / 'chapter-10.md').write_text('Wrong chapter')
    assert load_chapter_outline(tmp_path, 1).startswith('⚠️')


def test_review_metrics_reference_actual_english_report(tmp_path):
    from review_pipeline import build_review_artifacts, write_review_report
    source = tmp_path / 'review.json'
    source.write_text('{"issues": [], "summary": "Clear"}')
    payload = build_review_artifacts(tmp_path, 1, source, '审查报告/第1章审查报告.md')
    assert payload['metrics']['report_file'] == 'reviews/chapter-1-review.md'
    report = write_review_report(tmp_path, payload['metrics']['report_file'], payload)
    assert report.is_file()
    assert '# Chapter 1 Review' in report.read_text()
    assert '## Overview' in report.read_text()


@pytest.mark.parametrize('text,expected', [
    ('Hello, world!', 2), ("Don't stop the well-known traveler.", 5),
    ('### Chapter 1: Arrival', 3), ('   ', 0), ('山川异域。', 5),
    ('A traveler named 李 arrived.', 5),
])
def test_language_aware_word_counts(text, expected):
    from text_metrics import count_words
    assert count_words(text) == expected


def test_english_master_outline_sync_is_idempotent(tmp_path):
    import json
    from update_master_outline import sync_master_outline
    outlines = tmp_path / 'outlines'
    outlines.mkdir()
    master = outlines / 'master-outline.md'
    master.write_text('# Master Outline\n\n## Volume Plan\n'
        '| Volume | Title | Chapters | Core Conflict | Ending Climax |\n'
        '|---|---|---|---|---|\n| 1 | Arrival | 1-50 | Debt | Discovery |\n'
        '\n## Foreshadowing\n| Foreshadowing | Planted | Payoff | Level |\n'
        '|---|---|---|---|\n')
    for kind in ('beats', 'timeline', 'outline'):
        (outlines / f'volume-1-{kind}.md').write_text('Completed plan')
    (outlines / 'volume-1-master-outline-update.json').write_text(json.dumps({
        'next_volume_anchor': {'volume': 2, 'volume_name': 'Departure',
            'core_conflict': 'Escape', 'volume_end_climax': 'Freedom'},
        'foreshadow_writeback': [{'content': 'The lost key'}],
    }))
    result = sync_master_outline(tmp_path, 1)
    assert result['next_volume'] == 2
    first = master.read_text()
    assert '| 2 | Departure |' in first
    assert 'The lost key' in first
    sync_master_outline(tmp_path, 1)
    assert master.read_text() == first
    assert not (tmp_path / '大纲').exists()
