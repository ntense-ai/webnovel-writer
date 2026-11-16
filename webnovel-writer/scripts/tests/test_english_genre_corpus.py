"""English-only route guidance and taxonomy schemas."""
import csv
import hashlib
import json
from pathlib import Path
import re

import pytest
from genre_taxonomy import load_genre_taxonomy, resolve_genre_input
from data_modules.genre_aliases import to_profile_key

ROOT = Path(__file__).resolve().parents[2] / 'references'
ROUTE_PROSE = {'keywords', 'intent_synonyms', 'model_instruction', 'summary', 'details', 'core_tone', 'pacing_strategy', 'pitfalls', 'default_query'}


def rows_at(path):
    assert path.read_bytes().startswith(b'\xef\xbb\xbf')
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source))


def digest_metadata(rows, exclude):
    values = [{k: v for k, v in row.items() if k not in exclude} for row in rows]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def test_genre_routes_are_english_with_stable_routing_metadata():
    rows = rows_at(ROOT / 'csv' / 'genre-routing.csv')
    assert [row['id'] for row in rows] == [f'GR-{i:03d}' for i in range(1, 27)]
    assert digest_metadata(rows, ROUTE_PROSE | {'genre_aliases'}) == '834643fa00053c84676d8f3ec224f25bc39dd3ec37d23707c5caf678f7a72ce9'
    for row in rows:
        for key in ROUTE_PROSE:
            assert row[key].strip()
            assert not re.search(r'[\u4e00-\u9fff]', row[key]), (row['id'], key)
        aliases = row['genre_aliases'].split('|')
        assert aliases and all(alias.isascii() for alias in aliases)
    assert 'three-year challenge' in rows[0]['intent_synonyms']
    assert 'identity replacement' in rows[8]['details']


def test_taxonomy_routing_fields_and_templates_remain_stable():
    rows = rows_at(ROOT / 'taxonomy' / 'genre-index.csv')
    assert len(rows) == 56
    assert digest_metadata(rows, {'aliases'}) == '091d536f8654520aaf97477735be7b9aae3469c5d3213cea14c113a60cb53c22'
    for row in rows:
        assert all(value.isascii() for value in row.values())
        if row['template_file']:
            assert (ROOT.parent / 'templates' / 'genres' / row['template_file']).is_file()
        english = [alias for alias in row['aliases'].split(';') if alias.isascii()]
        assert english, row['label']
        # Every label has at least one English alias retaining its canonical genre.
        assert any(resolve_genre_input(alias).canonical_genre == row['canonical_genre']
                   for alias in english), row['label']


@pytest.mark.parametrize('value', ['game-lit', 'history-travel', 'general', 'xuanhuan'])
def test_stable_english_profile_identity(value):
    assert to_profile_key(value) == value
    assert to_profile_key(value.upper()) == value


@pytest.mark.parametrize('english,identifier', [
    ('grovel romance', 'melodramatic-romance'), ('academy progression', 'academy-fiction'),
    ('cosmic horror', 'cosmic-horror'), ('apocalyptic survival', 'apocalypse'),
    ('workplace romance', 'workplace-romance'), ('fanfiction', 'fanfiction'),
])
def test_aliases_and_english_identifiers_agree(english, identifier):
    assert resolve_genre_input(english).canonical_genre == resolve_genre_input(identifier).canonical_genre


def test_english_aliases_never_route_to_conflicting_labels():
    lookup = {}
    for row in rows_at(ROOT / 'taxonomy' / 'genre-index.csv'):
        for alias in [row['label'], *row['aliases'].split(';')]:
            key = re.sub(r'\s+', '', alias.casefold())
            if not key:
                continue
            assert key not in lookup or lookup[key] == row['label'], (alias, lookup.get(key), row['label'])
            lookup[key] = row['label']
    assert resolve_genre_input('esports fiction').canonical_genre == 'game-lit'
    assert to_profile_key('esports fiction') == 'esports'
