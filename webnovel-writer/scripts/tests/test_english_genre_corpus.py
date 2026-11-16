"""English route guidance and bilingual aliases retain the storage taxonomy."""
import csv
import hashlib
import json
from pathlib import Path
import re

import pytest
from genre_taxonomy import load_genre_taxonomy, resolve_genre_input
from data_modules.genre_aliases import to_profile_key

ROOT = Path(__file__).resolve().parents[2] / 'references'
ROUTE_PROSE = {'关键词', '意图与同义词', '大模型指令', '核心摘要', '详细展开', '核心调性', '节奏策略', '毒点', '默认查询词'}


def rows_at(path):
    assert path.read_bytes().startswith(b'\xef\xbb\xbf')
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source))


def digest_metadata(rows, exclude):
    values = [{k: v for k, v in row.items() if k not in exclude} for row in rows]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def test_genre_routes_are_english_with_stable_routing_metadata():
    rows = rows_at(ROOT / 'csv' / '题材与调性推理.csv')
    assert [row['编号'] for row in rows] == [f'GR-{i:03d}' for i in range(1, 27)]
    assert digest_metadata(rows, ROUTE_PROSE | {'题材别名'}) == '8f8d6399c1ac3874b3a39371c283e8f24a6778a22f3f2db49e9e08d23ec2c78e'
    for row in rows:
        for key in ROUTE_PROSE:
            assert row[key].strip()
            assert not re.search(r'[\u4e00-\u9fff]', row[key]), (row['编号'], key)
        aliases = row['题材别名'].split('|')
        assert any(alias.isascii() for alias in aliases)
        assert any(re.search(r'[\u4e00-\u9fff]', alias) for alias in aliases)
    assert 'three-year challenge' in rows[0]['意图与同义词']
    assert 'identity replacement' in rows[8]['详细展开']


def test_taxonomy_routing_fields_and_templates_remain_stable():
    rows = rows_at(ROOT / 'taxonomy' / 'genre-index.csv')
    assert len(rows) == 56
    assert digest_metadata(rows, {'aliases'}) == '9f83a2faed743796b4877bcb93c4b18ba7e1a1af1c384e1a6cc34f0893bab8b8'
    for row in rows:
        english = [alias for alias in row['aliases'].split(';') if alias.isascii()]
        assert english, row['label']
        # Every label has at least one English alias retaining its canonical genre.
        assert any(resolve_genre_input(alias).canonical_genre == row['canonical_genre']
                   for alias in english), row['label']


@pytest.mark.parametrize('value', ['game-lit', 'history-travel', 'general', 'xuanhuan'])
def test_stable_english_profile_identity(value):
    assert to_profile_key(value) == value
    assert to_profile_key(value.upper()) == value


@pytest.mark.parametrize('english,legacy', [
    ('grovel romance', '狗血言情'), ('academy progression', '学院流'),
    ('cosmic horror', '克苏鲁'), ('apocalyptic survival', '末世'),
    ('workplace romance', '职场婚恋'), ('fanfiction', '衍生'),
])
def test_new_aliases_and_legacy_labels_agree(english, legacy):
    assert resolve_genre_input(english).canonical_genre == resolve_genre_input(legacy).canonical_genre
