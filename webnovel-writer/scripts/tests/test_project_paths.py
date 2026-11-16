"""English defaults must not create a parallel layout for existing books."""
import json
from pathlib import Path

import pytest

from project_paths import DIRECTORIES, FILENAMES, project_dir, project_path, main


@pytest.mark.parametrize('canonical,legacy', DIRECTORIES.items())
def test_new_project_uses_english_without_creating_files(tmp_path, canonical, legacy):
    assert project_dir(tmp_path, canonical) == tmp_path / canonical
    assert project_dir(tmp_path, legacy) == tmp_path / canonical
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('canonical,legacy', DIRECTORIES.items())
def test_existing_legacy_directory_is_preserved(tmp_path, canonical, legacy):
    (tmp_path / legacy).mkdir()
    assert project_dir(tmp_path, canonical) == tmp_path / legacy
    assert project_dir(tmp_path, legacy) == tmp_path / legacy
    assert not (tmp_path / canonical).exists()


def test_partial_legacy_layout_keeps_missing_directories_legacy(tmp_path):
    (tmp_path / '正文').mkdir()
    assert project_dir(tmp_path, 'reviews') == tmp_path / '审查报告'


def test_english_directory_wins_when_both_exist(tmp_path):
    for name in ('chapters', '正文'):
        (tmp_path / name).mkdir()
    assert project_dir(tmp_path, 'chapters') == tmp_path / 'chapters'
    assert (tmp_path / '正文').exists()


@pytest.mark.parametrize('legacy,english', FILENAMES.items())
def test_known_filenames_default_english_and_preserve_legacy(tmp_path, legacy, english):
    assert project_path(tmp_path, 'settings/' + legacy) == tmp_path / 'settings' / english
    (tmp_path / '设定集').mkdir()
    assert project_path(tmp_path, 'settings/' + english) == tmp_path / '设定集' / legacy


@pytest.mark.parametrize('legacy,english', [
    ('第2卷-详细大纲.md', 'volume-2-outline.md'), ('第2卷-时间线.md', 'volume-2-timeline.md'),
    ('第2卷-节拍表.md', 'volume-2-beats.md'), ('第2卷-总纲写回.json', 'volume-2-master-outline-update.json'),
    ('第2章审查报告.md', 'chapter-2-review.md'),
])
def test_dynamic_filename_aliases(tmp_path, legacy, english):
    assert project_path(tmp_path, 'outlines/' + legacy) == tmp_path / 'outlines' / english
    (tmp_path / '大纲').mkdir()
    assert project_path(tmp_path, 'outlines/' + english) == tmp_path / '大纲' / legacy


def test_english_directory_with_legacy_filename_is_read_in_place(tmp_path):
    (tmp_path / 'settings').mkdir()
    existing = tmp_path / 'settings/世界观.md'
    existing.write_text('Existing world')
    assert project_path(tmp_path, 'settings/worldbuilding.md') == existing
    assert project_path(tmp_path, '设定集/世界观.md') == existing


def test_unknown_file_and_internal_paths_are_unchanged(tmp_path):
    assert project_path(tmp_path, 'settings/alice.md') == tmp_path / 'settings/alice.md'
    assert project_path(tmp_path, '.story-system/MASTER_SETTING.json') == tmp_path / '.story-system/MASTER_SETTING.json'


@pytest.mark.parametrize('relative', ['/tmp/outside', '../outside', 'settings/../../outside'])
def test_project_file_rejects_traversal(tmp_path, relative):
    with pytest.raises(ValueError):
        project_path(tmp_path, relative)


def test_unknown_directory_rejected(tmp_path):
    with pytest.raises(ValueError):
        project_dir(tmp_path, 'other')


@pytest.mark.parametrize('args,expected', [([], None), (['--directory', 'chapters'], 'chapters'), (['--path', 'settings/世界观.md'], 'settings/worldbuilding.md')])
def test_cli_resolves_paths_read_only(tmp_path, monkeypatch, capsys, args, expected):
    monkeypatch.setattr('sys.argv', ['project_paths', '--project-root', str(tmp_path), *args])
    main()
    output = capsys.readouterr().out.strip()
    if expected:
        assert output == str(tmp_path / expected)
    else:
        assert json.loads(output) == {key: str(tmp_path / key) for key in DIRECTORIES}
    assert not list(tmp_path.iterdir())


def test_nested_chapter_aliases(tmp_path):
    from project_paths import project_path
    assert project_path(tmp_path, "正文/第1卷/第0001章.md") == tmp_path / "chapters/volume-1/chapter-0001.md"
    old = tmp_path / "正文/第1卷/第0001章.md"
    old.parent.mkdir(parents=True)
    old.write_text("old", encoding="utf-8")
    assert project_path(tmp_path, "chapters/volume-1/chapter-0001.md") == old
    assert old.read_text() == "old"
