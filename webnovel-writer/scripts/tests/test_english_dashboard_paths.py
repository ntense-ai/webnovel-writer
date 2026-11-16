"""Dashboard document browsing works for English and pre-existing layouts."""
import pytest

from .test_dashboard_security import _create_dashboard_client


@pytest.mark.parametrize('folders', [
    ('chapters', 'outlines', 'settings', 'reviews'),
    ('正文', '大纲', '设定集', '审查报告'),
])
def test_dashboard_lists_and_reads_both_layouts(monkeypatch, tmp_path, folders):
    for folder in folders:
        directory = tmp_path / folder
        directory.mkdir()
        (directory / 'document.md').write_text(f'# {folder}', encoding='utf-8')
    client = _create_dashboard_client(monkeypatch, tmp_path)
    response = client.get('/api/files/tree')
    assert response.status_code == 200
    tree = response.json()
    assert set(tree) == set(folders)
    for folder in folders:
        path = f'{folder}/document.md'
        assert tree[folder][0]['path'] == path
        response = client.get('/api/files/read', params={'path': path})
        assert response.status_code == 200
        assert response.json()['content'] == f'# {folder}'


def test_dashboard_preserves_visibility_of_mixed_layout(monkeypatch, tmp_path):
    for folder in ('chapters', '正文'):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / 'chapter.md').write_text(folder, encoding='utf-8')
    client = _create_dashboard_client(monkeypatch, tmp_path)
    tree = client.get('/api/files/tree').json()
    assert tree['chapters'][0]['path'] == 'chapters/chapter.md'
    assert tree['正文'][0]['path'] == '正文/chapter.md'
    assert client.get('/api/files/read', params={'path': '正文/chapter.md'}).status_code == 200


def test_dashboard_new_layout_keeps_read_allowlist(monkeypatch, tmp_path):
    (tmp_path / 'chapters').mkdir()
    (tmp_path / '.env').write_text('private')
    client = _create_dashboard_client(monkeypatch, tmp_path)
    assert client.get('/api/files/read', params={'path': '.env'}).status_code == 403
    assert client.get('/api/files/read', params={'path': 'chapters/../.env'}).status_code == 403
    assert client.get('/api/files/read', params={'path': '../outside'}).status_code == 403
    assert client.get('/api/files/read', params={'path': 'chapters/missing.md'}).status_code == 404
