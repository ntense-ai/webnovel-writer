"""English reference prose and retrieval, including English routing metadata."""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from reference_search import search

CSV_DIR = SCRIPTS.parent / 'references' / 'csv'
HAN = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')
# These are identifiers/routing expressions, not generated author-facing prose.
METADATA = {'id', 'applicable_skills', 'category', 'level', 'applicable_genres', 'genre_route',
            'canonical_genre', 'genre_aliases', 'recommended_base_tables', 'recommended_dynamic_tables',
            'genre', 'conflict_resolution', 'contract_injection_layer'}
TABLES = {
    'naming': ('naming', 'NR', 79),
    'scenes': ('scenes', 'SP', 96),
    'techniques': ('techniques', 'WT', 104),
    'tropes': ('tropes', 'TR', 108),
    'pacing': ('pacing', 'PA', 104),
    'characters': ('characters', 'CH', 101),
    'powers': ('powers', 'SY', 104),
    'genre-routing': ('genre-routing', 'GR', 26),
    'adjudication': ('adjudication', 'RS', 17),
}


@pytest.mark.parametrize('alias', TABLES)
def test_reference_prose_is_english_and_rows_keep_stable_ids(alias):
    stem, prefix, count = TABLES[alias]
    path = CSV_DIR / f'{stem}.csv'
    assert path.read_bytes().startswith(b'\xef\xbb\xbf'), f'{stem}: UTF-8 BOM missing'
    with path.open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        rows = list(reader)
    assert headers == EXPECTED_HEADERS[alias]
    assert len(rows) == count
    assert [row['id'] for row in rows] == [f'{prefix}-{i:03d}' for i in range(1, count + 1)]
    for row in rows:
        assert None not in row, f'{row["id"]}: extra CSV cells'
        for column, value in row.items():
            assert value is not None, f'{row["id"]}: missing {column}'
            assert not HAN.search(value), f'{row["id"]}: untranslated prose in {column}: {value}'
        for required in ('keywords', 'model_instruction', 'summary'):
            assert row[required].strip(), f'{row["id"]}: empty {required}'


@pytest.mark.parametrize('alias,skill,query,expected', [
    ('naming', 'write', 'xuanhuan personal names', 'NR-001'),
    ('scenes', 'write', 'combat description battle', 'SP-001'),
    ('techniques', 'write', 'distinct dialogue voices subtext', 'WT-001'),
    ('pacing', 'write', 'suppression eruption catharsis', 'PA-001'),
    ('tropes', 'write', 'broken engagement three-year challenge', 'TR-001'),
    ('powers', 'write', 'power system levels', 'SY-001'),
    ('genre-routing', 'story-system', 'broken engagement', 'GR-001'),
    ('characters', 'write', 'mirror antagonist nemesis', 'CH-001'),
    ('adjudication', 'story-system', 'Western fantasy', 'RS-001'),
])
def test_real_english_queries_retrieve_relevant_rows_with_english_aliases(alias, skill, query, expected):
    out = search(CSV_DIR, skill=skill, query=query, table=alias, max_results=5)
    assert out['status'] == 'success'
    results = out['data']['results']
    assert expected in [item['id'] for item in results]
    for item in results:
        assert item['table'] == alias
        assert item['table'] == TABLES[alias][0]
        assert re.fullmatch(r'[A-Z]{2}-[0-9]{3}', item['id'])
        assert item['instruction'] == item['model_instruction']
        assert item['summary'] and item['instruction']
        assert not HAN.search(item['summary'] + item['instruction'])


@pytest.mark.parametrize('query,expected', [('xuanhuan personal names', 'NR-001'), ('combat description', 'SP-001')])
def test_plain_english_query_recall_has_english_results(query, expected):
    out = search(CSV_DIR, skill='write', query=query, max_results=5)
    results = out['data']['results']
    assert expected in [item['id'] for item in results]
    assert all(not HAN.search(item['summary'] + item['instruction']) for item in results)


def test_english_cross_table_search_excludes_internal_routing():
    out = search(CSV_DIR, skill='write', query='fantasy protagonist dialogue', max_results=100)
    assert out['data']['results']
    assert not {'genre-routing', 'adjudication'} & {row['table'] for row in out['data']['results']}


def test_english_nonmatching_query_has_no_fabricated_results():
    out = search(CSV_DIR, skill='write', query='qzxvplm')
    assert out['status'] == 'success'
    assert out['data']['total'] == 0
    assert out['data']['results'] == []


# Fixed schemas detect accidental column changes during translation.
EXPECTED_HEADERS = {'naming': ['id',
            'applicable_skills',
            'category',
            'level',
            'keywords',
            'intent_synonyms',
            'applicable_genres',
            'model_instruction',
            'summary',
            'details',
            'naming_target',
            'rule',
            'positive_example',
            'negative_example',
            'pitfalls'],
 'scenes': ['id',
            'applicable_skills',
            'category',
            'level',
            'keywords',
            'intent_synonyms',
            'applicable_genres',
            'model_instruction',
            'summary',
            'details',
            'scene_type',
            'pattern_name',
            'description',
            'example_excerpt',
            'pitfalls'],
 'techniques': ['id',
                'applicable_skills',
                'category',
                'level',
                'keywords',
                'intent_synonyms',
                'applicable_genres',
                'model_instruction',
                'summary',
                'details',
                'technique_type',
                'technique_name',
                'applicable_scenes',
                'pitfalls',
                'positive_example',
                'negative_example'],
 'tropes': ['id',
            'applicable_skills',
            'category',
            'level',
            'keywords',
            'intent_synonyms',
            'applicable_genres',
            'model_instruction',
            'summary',
            'details',
            'trope_name',
            'setup',
            'core_payoff',
            'twist_design',
            'subversive_variant',
            'pitfalls'],
 'pacing': ['id',
            'applicable_skills',
            'category',
            'level',
            'keywords',
            'intent_synonyms',
            'applicable_genres',
            'model_instruction',
            'summary',
            'details',
            'pacing_type',
            'emotional_techniques',
            'pitfalls'],
 'characters': ['id',
                'applicable_skills',
                'category',
                'level',
                'keywords',
                'intent_synonyms',
                'applicable_genres',
                'model_instruction',
                'summary',
                'details',
                'character_type',
                'core_motivation',
                'behavior_logic',
                'interaction_pattern',
                'pitfalls'],
 'powers': ['id',
            'applicable_skills',
            'category',
            'level',
            'keywords',
            'intent_synonyms',
            'applicable_genres',
            'model_instruction',
            'summary',
            'details',
            'setting_type',
            'numeric_limits',
            'plot_interaction',
            'pitfalls'],
 'genre-routing': ['id',
                   'applicable_skills',
                   'category',
                   'level',
                   'keywords',
                   'intent_synonyms',
                   'applicable_genres',
                   'model_instruction',
                   'summary',
                   'details',
                   'genre_route',
                   'canonical_genre',
                   'genre_aliases',
                   'core_tone',
                   'pacing_strategy',
                   'pitfalls',
                   'recommended_base_tables',
                   'recommended_dynamic_tables',
                   'default_query'],
 'adjudication': ['id',
                  'applicable_skills',
                  'category',
                  'level',
                  'keywords',
                  'intent_synonyms',
                  'applicable_genres',
                  'model_instruction',
                  'summary',
                  'details',
                  'genre',
                  'style_priority',
                  'payoff_priority',
                  'default_pacing_strategy',
                  'pitfall_weight',
                  'conflict_resolution',
                  'contract_injection_layer',
                  'anti_pattern']}


def test_english_tokens_do_not_match_arbitrary_substrings():
    out = search(CSV_DIR, 'write', 'qzxvplmzznotaword')
    assert out['data']['results'] == []
    combat = search(CSV_DIR, 'write', 'combat', table='scenes')
    assert combat['data']['results']
