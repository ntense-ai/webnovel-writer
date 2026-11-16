"""Runtime readers and diagnostics use canonical English project paths."""
import json
from pathlib import Path

import pytest

from data_modules.doctor import build_doctor_report
from data_modules.placeholder_scanner import scan_placeholders
from data_modules.project_phase import INIT_REQUIRED_DIRS, INIT_REQUIRED_FILES, resolve_project_phase
from data_modules.user_report import build_user_report, _find_review_report

def _path(root, relative):
    return root / relative


def _seed(root):
    for relative in INIT_REQUIRED_DIRS:
        _path(root, relative).mkdir(parents=True, exist_ok=True)
    for relative in INIT_REQUIRED_FILES:
        path = _path(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'project_info': {'title': 'Novel'}, 'progress': {'current_chapter': 0}}) if path.suffix == '.json' else '# Ready\n', encoding='utf-8')


def test_init_phase_and_report_resolve_existing_project_layout(tmp_path):
    _seed(tmp_path)
    snapshot = resolve_project_phase(tmp_path)
    assert snapshot.phase == 'init_ready'
    assert not snapshot.missing_init_dirs and not snapshot.missing_init_files
    report = build_user_report(tmp_path, stage='init')
    assert report['overall_status'] == 'completed'
    paths = {item['path'] for item in report['files']}
    assert 'outlines/master-outline.md' in paths
    assert 'settings/worldbuilding.md' in paths


def test_doctor_expected_profile_matches_layout(tmp_path):
    _seed(tmp_path)
    report = build_doctor_report(tmp_path)
    file_checks = [check for check in report['checks'] if check['id'].startswith(('file.dir.', 'file.required.'))]
    assert file_checks and all(check['status'] == 'ok' for check in file_checks)
    root_name = 'outlines'
    filename = 'master-outline.md'
    assert any(check['path'].endswith(f'{root_name}/{filename}') for check in file_checks)


def test_placeholder_scan_classifies_outline_and_settings(tmp_path):
    _seed(tmp_path)
    _path(tmp_path, 'outlines/master-outline.md').write_text('[TODO]', encoding='utf-8')
    _path(tmp_path, 'settings/worldbuilding.md').write_text('[TODO]', encoding='utf-8')
    results = scan_placeholders(tmp_path)
    phases = {item['file']: item['suggested_fill_phase'] for item in results}
    assert phases[_path(tmp_path, 'outlines/master-outline.md').relative_to(tmp_path).as_posix()] == 'plan'
    assert phases[_path(tmp_path, 'settings/worldbuilding.md').relative_to(tmp_path).as_posix()] == 'setting_update'


def test_review_report_discovery_without_metrics(tmp_path):
    _seed(tmp_path)
    path = _path(tmp_path, 'reviews/chapter-3-review.md')
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


def test_latest_draft_recognizes_numbered_chapter_filenames(tmp_path):
    from data_modules.project_phase import _latest_draft_chapter
    directory = tmp_path / 'chapters'
    directory.mkdir()
    for number in (1, 12):
        name = f'chapter-{number:04d}-Arrival.md'
        (directory / name).write_text('# Draft')
    (directory / 'notes.md').write_text('# Ignore')
    assert _latest_draft_chapter(tmp_path) == 12


def test_setting_and_style_readers_load_canonical_files(tmp_path):
    from data_modules.config import DataModulesConfig
    from data_modules.context_manager import ContextManager
    from data_modules.memory_contract_adapter import MemoryContractAdapter
    directory = tmp_path / 'settings'
    directory.mkdir()
    (directory / 'worldbuilding.md').write_text('World details')
    (directory / 'style-guide.md').write_text('Short clear sentences')
    config = DataModulesConfig.from_project_root(tmp_path)
    assert ContextManager(config)._load_setting('worldbuilding') == 'World details'
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


def test_catalog_messages_and_matching_are_english():
    import re
    from data_modules.error_catalog import load_catalog, classify_issue, format_author_error
    entries, fallback = load_catalog()
    for error in [entry.error for entry in entries] + [fallback]:
        assert not re.search(r'[\u4e00-\u9fff]', format_author_error(error))
    assert classify_issue('missing required field').code == 'artifact.schema_error'


def test_english_layout_preserves_unicode_author_content(tmp_path):
    from data_modules.config import DataModulesConfig
    from data_modules.context_manager import ContextManager
    directory = tmp_path / 'settings'
    directory.mkdir()
    text = 'Zoë meets Émile at the café. Their compass points toward Reykjavík.'
    (directory / 'worldbuilding.md').write_text(text, encoding='utf-8')
    assert ContextManager(DataModulesConfig.from_project_root(tmp_path))._load_setting('worldbuilding') == text
