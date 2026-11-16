"""The English-only layout is deterministic, read-only and traversal-safe."""
import json
import pytest
from project_paths import DIRECTORIES, project_dir, project_path, main

@pytest.mark.parametrize('name', DIRECTORIES)
def test_new_directory_resolution_does_not_create_files(tmp_path, name):
    assert project_dir(tmp_path, name) == tmp_path / name
    assert not list(tmp_path.iterdir())

@pytest.mark.parametrize('name', DIRECTORIES)
def test_existing_directory_and_content_preserved(tmp_path, name):
    folder = tmp_path / name
    folder.mkdir()
    existing = folder / 'content.md'
    existing.write_text('An existing story')
    assert project_dir(tmp_path, name) == folder
    assert existing.read_text() == 'An existing story'

@pytest.mark.parametrize('relative', [
    'settings/worldbuilding.md', 'settings/power-system.md',
    'settings/protagonist.md', 'settings/heroine.md',
    'settings/protagonist-team.md', 'settings/antagonist.md',
    'settings/style-guide.md', 'outlines/master-outline.md',
    'outlines/volume-2-outline.md', 'outlines/volume-2-timeline.md',
    'outlines/volume-2-beats.md', 'outlines/volume-2-master-outline-update.json',
    'reviews/chapter-2-review.md', 'chapters/volume-1/chapter-0001.md',
    '.story-system/MASTER_SETTING.json', 'settings/café.md',
])
def test_paths_resolve_exactly_without_rewriting_content(tmp_path, relative):
    expected = tmp_path / relative
    assert project_path(tmp_path, relative) == expected
    expected.parent.mkdir(parents=True, exist_ok=True)
    expected.write_text('Unicode prose: café, Ελληνικά, العربية')
    assert project_path(tmp_path, relative) == expected
    assert expected.read_text() == 'Unicode prose: café, Ελληνικά, العربية'

@pytest.mark.parametrize('relative', ['/tmp/outside', '../outside', 'settings/../../outside'])
def test_project_file_rejects_traversal(tmp_path, relative):
    with pytest.raises(ValueError):
        project_path(tmp_path, relative)

def test_unknown_directory_rejected(tmp_path):
    with pytest.raises(ValueError):
        project_dir(tmp_path, 'other')

@pytest.mark.parametrize('args,expected', [([], None), (['--directory', 'chapters'], 'chapters'), (['--path', 'settings/worldbuilding.md'], 'settings/worldbuilding.md')])
def test_cli_resolves_paths_read_only(tmp_path, monkeypatch, capsys, args, expected):
    monkeypatch.setattr('sys.argv', ['project_paths', '--project-root', str(tmp_path), *args])
    main()
    output = capsys.readouterr().out.strip()
    if expected:
        assert output == str(tmp_path / expected)
    else:
        assert json.loads(output) == {key: str(tmp_path / key) for key in DIRECTORIES}
    assert not list(tmp_path.iterdir())
