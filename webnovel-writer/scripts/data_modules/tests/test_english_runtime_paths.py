"""Runtime readers and diagnostics support canonical and legacy project layouts."""
import json
from pathlib import Path

import pytest

from data_modules.doctor import build_doctor_report
from data_modules.placeholder_scanner import scan_placeholders
from data_modules.project_phase import INIT_REQUIRED_DIRS, INIT_REQUIRED_FILES, resolve_project_phase
from data_modules.user_report import build_user_report, _find_review_report

DIRECTORIES = {'正文': 'chapters', '大纲': 'outlines', '设定集': 'settings', '审查报告': 'reviews'}


FILENAMES = {'世界观.md': 'worldbuilding.md', '力量体系.md': 'power-system.md', '主角卡.md': 'protagonist.md', '反派设计.md': 'antagonist.md', '总纲.md': 'master-outline.md', '第3章审查报告.md': 'chapter-3-review.md'}

def _path(root, relative, english):
    first, *parts = Path(relative).parts
    if english:
        parts = [FILENAMES.get(part, part) for part in parts]
    return root / (DIRECTORIES.get(first, first) if english else first) / Path(*parts)


def _seed(root, english):
    for relative in INIT_REQUIRED_DIRS:
        _path(root, relative, english).mkdir(parents=True, exist_ok=True)
    for relative in INIT_REQUIRED_FILES:
        path = _path(root, relative, english)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'project_info': {'title': 'Novel'}, 'progress': {'current_chapter': 0}}) if path.suffix == '.json' else '# Ready\n', encoding='utf-8')


@pytest.mark.parametrize('english', [True, False], ids=['english', 'legacy'])
def test_init_phase_and_report_resolve_existing_project_layout(tmp_path, english):
    _seed(tmp_path, english)
    snapshot = resolve_project_phase(tmp_path)
    assert snapshot.phase == 'init_ready'
    assert not snapshot.missing_init_dirs and not snapshot.missing_init_files
    report = build_user_report(tmp_path, stage='init')
    assert report['overall_status'] == 'completed'
    paths = {item['path'] for item in report['files']}
    assert ('outlines/master-outline.md' if english else '大纲/总纲.md') in paths
    assert ('settings/worldbuilding.md' if english else '设定集/世界观.md') in paths


@pytest.mark.parametrize('english', [True, False], ids=['english', 'legacy'])
def test_doctor_expected_profile_matches_layout(tmp_path, english):
    _seed(tmp_path, english)
    report = build_doctor_report(tmp_path)
    file_checks = [check for check in report['checks'] if check['id'].startswith(('file.dir.', 'file.required.'))]
    assert file_checks and all(check['status'] == 'ok' for check in file_checks)
    root_name = 'outlines' if english else '大纲'
    filename = 'master-outline.md' if english else '总纲.md'
    assert any(check['path'].endswith(f'{root_name}/{filename}') for check in file_checks)


@pytest.mark.parametrize('english', [True, False], ids=['english', 'legacy'])
def test_placeholder_scan_classifies_outline_and_settings(tmp_path, english):
    _seed(tmp_path, english)
    _path(tmp_path, '大纲/总纲.md', english).write_text('[待补充]', encoding='utf-8')
    _path(tmp_path, '设定集/世界观.md', english).write_text('[待补充]', encoding='utf-8')
    results = scan_placeholders(tmp_path)
    phases = {item['file']: item['suggested_fill_phase'] for item in results}
    assert phases[_path(tmp_path, '大纲/总纲.md', english).relative_to(tmp_path).as_posix()] == 'plan'
    assert phases[_path(tmp_path, '设定集/世界观.md', english).relative_to(tmp_path).as_posix()] == 'setting_update'


@pytest.mark.parametrize('english', [True, False], ids=['english', 'legacy'])
def test_review_report_discovery_without_metrics(tmp_path, english):
    _seed(tmp_path, english)
    path = _path(tmp_path, '审查报告/第3章审查报告.md', english)
    path.write_text('# Review', encoding='utf-8')
    assert _find_review_report(tmp_path, 3) == path


def test_new_project_missing_paths_are_english(tmp_path):
    (tmp_path / '.webnovel').mkdir()
    (tmp_path / '.webnovel/state.json').write_text('{}')
    snapshot = resolve_project_phase(tmp_path)
    assert 'outlines/master-outline.md' in snapshot.missing_init_files
    assert 'chapters' in snapshot.missing_init_dirs
    report = build_user_report(tmp_path, stage='plan')
    assert any(item['path'] == 'outlines/master-outline.md' for item in report['files'])


@pytest.mark.parametrize('name', ['chapter-3-review.md', 'chapter-003-review.md', 'chapter-0003-review.md'])
def test_review_report_accepts_english_padding(tmp_path, name):
    directory = tmp_path / 'reviews'
    directory.mkdir()
    path = directory / name
    path.write_text('# Review')
    assert _find_review_report(tmp_path, 3) == path


@pytest.mark.parametrize('english', [True, False], ids=['english', 'legacy'])
def test_latest_draft_recognizes_both_chapter_filenames(tmp_path, english):
    from data_modules.project_phase import _latest_draft_chapter
    directory = tmp_path / ('chapters' if english else '正文')
    directory.mkdir()
    for number in (1, 12):
        name = f'chapter-{number:04d}-Arrival.md' if english else f'第{number:04d}章-抵达.md'
        (directory / name).write_text('# Draft')
    (directory / 'notes.md').write_text('# Ignore')
    assert _latest_draft_chapter(tmp_path) == 12


@pytest.mark.parametrize('english', [True, False], ids=['english', 'legacy'])
def test_setting_and_style_readers_preserve_legacy_support(tmp_path, english):
    from data_modules.config import DataModulesConfig
    from data_modules.context_manager import ContextManager
    from data_modules.memory_contract_adapter import MemoryContractAdapter
    directory = tmp_path / ('settings' if english else '设定集')
    directory.mkdir()
    (directory / ('worldbuilding.md' if english else '世界观.md')).write_text('World details')
    (directory / ('style-guide.md' if english else '风格契约.md')).write_text('Short clear sentences')
    config = DataModulesConfig.from_project_root(tmp_path)
    assert ContextManager(config)._load_setting('世界观') == 'World details'
    assert MemoryContractAdapter(config)._load_style_contract() == 'Short clear sentences'


def test_index_projection_reads_english_title_and_word_count(tmp_path):
    from data_modules.index_projection_writer import IndexProjectionWriter
    directory = tmp_path / 'chapters'
    directory.mkdir()
    (directory / 'chapter-0001-Arrival.md').write_text('# Chapter 1\n\nThey arrived at dawn.')
    writer = IndexProjectionWriter(tmp_path)
    assert writer._title_from_chapter_file(1) == 'Arrival'
    assert writer._chapter_word_count(1) == 4


@pytest.mark.parametrize('key', ['xuanhuan', 'xianxia', 'urban-power', 'romance', 'shuangwen'])
def test_english_profile_keys_remain_distinct_from_input_taxonomy(key):
    from data_modules.genre_aliases import normalize_genre_token, to_profile_key
    assert normalize_genre_token(key) == key
    assert to_profile_key(key) == key


def test_catalog_messages_are_english_without_losing_legacy_matching():
    import re
    from data_modules.error_catalog import load_catalog, classify_issue, format_author_error
    entries, fallback = load_catalog()
    for error in [entry.error for entry in entries] + [fallback]:
        assert not re.search(r'[\u4e00-\u9fff]', format_author_error(error))
    assert classify_issue('缺少必要字段').code == 'artifact.schema_error'
