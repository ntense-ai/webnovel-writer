"""Dashboard document browsing uses English paths and preserves Unicode content."""
import pytest

from .test_dashboard_security import _create_dashboard_client


@pytest.mark.parametrize('document', ['document.md', 'nested/document.md'])
def test_dashboard_lists_and_reads_canonical_layout(monkeypatch, tmp_path, document):
    folders = ('chapters', 'outlines', 'settings', 'reviews')
    for folder in folders:
        file = tmp_path / folder / document
        file.parent.mkdir(parents=True)
        file.write_text(f'# {folder}', encoding='utf-8')
    client = _create_dashboard_client(monkeypatch, tmp_path)
    response = client.get('/api/files/tree')
    assert response.status_code == 200
    tree = response.json()
    assert set(tree) == set(folders)
    for folder in folders:
        path = f'{folder}/{document}'
        entry = tree[folder][0]
        if '/' in document:
            assert entry['type'] == 'dir'
            entry = entry['children'][0]
        assert entry['path'] == path
        response = client.get('/api/files/read', params={'path': path})
        assert response.status_code == 200
        assert response.json()['content'] == f'# {folder}'


def test_dashboard_preserves_unicode_story_content(monkeypatch, tmp_path):
    folder = tmp_path / 'chapters'
    folder.mkdir()
    content = '# Caf\u00e9\n\u4f60\u597d, world! \U0001f30d'
    (folder / 'chapter.md').write_text(content, encoding='utf-8')
    client = _create_dashboard_client(monkeypatch, tmp_path)
    assert client.get('/api/files/tree').json()['chapters'][0]['path'] == 'chapters/chapter.md'
    assert client.get('/api/files/read', params={'path': 'chapters/chapter.md'}).json()['content'] == content


def test_dashboard_new_layout_keeps_read_allowlist(monkeypatch, tmp_path):
    (tmp_path / 'chapters').mkdir()
    (tmp_path / '.env').write_text('private')
    client = _create_dashboard_client(monkeypatch, tmp_path)
    assert client.get('/api/files/read', params={'path': '.env'}).status_code == 403
    assert client.get('/api/files/read', params={'path': 'chapters/../.env'}).status_code == 403
    assert client.get('/api/files/read', params={'path': '../outside'}).status_code == 403
    assert client.get('/api/files/read', params={'path': 'chapters/missing.md'}).status_code == 404
