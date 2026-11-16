"""Keep the English fork's advertised installation on the intended branch."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_fork_marketplace_identity_and_local_plugin_source():
    marketplace = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
    plugin = marketplace['plugins'][0]
    manifest = json.loads((ROOT / 'webnovel-writer/.claude-plugin/plugin.json').read_text())
    assert marketplace['name'] == 'ntense-webnovel-writer'
    assert marketplace['owner']['name'] == 'ezhomelabs'
    assert plugin['name'] == manifest['name'] == 'webnovel-writer'
    assert plugin['source'] == './webnovel-writer'
    assert manifest['repository'] == 'https://github.com/ezhomelabs/webnovel-writer'
    assert plugin['homepage'] == manifest['homepage'] == 'https://github.com/ezhomelabs/webnovel-writer/tree/ntense'
    # Keep upstream attribution instead of claiming original authorship.
    assert manifest['author']['name'] == plugin['author']['name'] == 'lingfengQAQ'


def test_readmes_install_branch_pinned_fork():
    for path in [ROOT / 'README.md', ROOT / 'webnovel-writer/README.md']:
        text = path.read_text()
        assert 'claude plugin marketplace add "ezhomelabs/webnovel-writer#ntense" --scope user' in text
        assert 'claude plugin install webnovel-writer@ntense-webnovel-writer --scope user' in text
        assert 'claude plugin marketplace add lingfengQAQ/' not in text
    text = (ROOT / 'README.md').read_text()
    assert '`ntense` (this fork)' in text
    assert '`master` (this branch)' not in text
    assert 'git clone --branch ntense --single-branch https://github.com/ezhomelabs/webnovel-writer.git' in text
    assert 'raw.githubusercontent.com/lingfengQAQ/webnovel-writer/HEAD/requirements.txt' not in text
    assert 'python -m pip install -r requirements.txt' in text


def test_root_dependency_includes_resolve_in_branch_checkout():
    includes = [line[3:].strip() for line in (ROOT / 'requirements.txt').read_text().splitlines() if line.startswith('-r ')]
    assert set(includes) == {'webnovel-writer/scripts/requirements.txt', 'webnovel-writer/dashboard/requirements.txt'}
    assert all((ROOT / path).is_file() for path in includes)
