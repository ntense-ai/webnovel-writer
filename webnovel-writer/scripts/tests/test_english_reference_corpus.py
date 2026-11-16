"""English reference prose and retrieval, with stable legacy routing metadata."""
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
METADATA = {'编号', '适用技能', '分类', '层级', '适用题材', '题材/流派',
            'canonical_genre', '题材别名', '推荐基础检索表', '推荐动态检索表',
            '题材', '冲突裁决', 'contract注入层'}
TABLES = {
    'naming': ('命名规则', 'NR', 79),
    'scenes': ('场景写法', 'SP', 96),
    'techniques': ('写作技法', 'WT', 104),
    'tropes': ('桥段套路', 'TR', 108),
    'pacing': ('爽点与节奏', 'PA', 104),
    'characters': ('人设与关系', 'CH', 101),
    'powers': ('金手指与设定', 'SY', 104),
    'genre-routing': ('题材与调性推理', 'GR', 26),
    'adjudication': ('裁决规则', 'RS', 17),
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
    assert [row['编号'] for row in rows] == [f'{prefix}-{i:03d}' for i in range(1, count + 1)]
    for row in rows:
        assert None not in row, f'{row["编号"]}: extra CSV cells'
        for column, value in row.items():
            assert value is not None, f'{row["编号"]}: missing {column}'
            if column not in METADATA:
                assert not HAN.search(value), f'{row["编号"]}: untranslated prose in {column}: {value}'
        for required in ('关键词', '大模型指令', '核心摘要'):
            assert row[required].strip(), f'{row["编号"]}: empty {required}'


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
        assert item['表'] == TABLES[alias][0]
        assert item['id'] == item['编号']
        assert item['summary'] == item['内容摘要']
        assert item['instruction'] == item['大模型指令']
        assert item['summary'] and item['instruction']
        assert not HAN.search(item['summary'] + item['instruction'])


@pytest.mark.parametrize('query,expected', [('角色命名', 'NR-001'), ('战斗描写', 'SP-001')])
def test_legacy_query_recall_does_not_leak_legacy_prose(query, expected):
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
EXPECTED_HEADERS = {'naming': ['编号',
            '适用技能',
            '分类',
            '层级',
            '关键词',
            '意图与同义词',
            '适用题材',
            '大模型指令',
            '核心摘要',
            '详细展开',
            '命名对象',
            '规则',
            '正例',
            '反例',
            '毒点'],
 'scenes': ['编号',
            '适用技能',
            '分类',
            '层级',
            '关键词',
            '意图与同义词',
            '适用题材',
            '大模型指令',
            '核心摘要',
            '详细展开',
            '场景类型',
            '模式名称',
            '说明',
            '示例片段',
            '毒点'],
 'techniques': ['编号',
                '适用技能',
                '分类',
                '层级',
                '关键词',
                '意图与同义词',
                '适用题材',
                '大模型指令',
                '核心摘要',
                '详细展开',
                '技法类型',
                '技法名称',
                '适用场景',
                '毒点',
                '正例',
                '反例'],
 'tropes': ['编号',
            '适用技能',
            '分类',
            '层级',
            '关键词',
            '意图与同义词',
            '适用题材',
            '大模型指令',
            '核心摘要',
            '详细展开',
            '桥段名称',
            '前置铺垫',
            '核心爽点',
            '转折设计',
            '反套路变种',
            '毒点'],
 'pacing': ['编号',
            '适用技能',
            '分类',
            '层级',
            '关键词',
            '意图与同义词',
            '适用题材',
            '大模型指令',
            '核心摘要',
            '详细展开',
            '节奏类型',
            '情绪调动手法',
            '毒点'],
 'characters': ['编号',
                '适用技能',
                '分类',
                '层级',
                '关键词',
                '意图与同义词',
                '适用题材',
                '大模型指令',
                '核心摘要',
                '详细展开',
                '人设类型',
                '核心动机',
                '行为逻辑',
                '互动模式',
                '毒点'],
 'powers': ['编号',
            '适用技能',
            '分类',
            '层级',
            '关键词',
            '意图与同义词',
            '适用题材',
            '大模型指令',
            '核心摘要',
            '详细展开',
            '设定类型',
            '数值控制边界',
            '与剧情交互方式',
            '毒点'],
 'genre-routing': ['编号',
                   '适用技能',
                   '分类',
                   '层级',
                   '关键词',
                   '意图与同义词',
                   '适用题材',
                   '大模型指令',
                   '核心摘要',
                   '详细展开',
                   '题材/流派',
                   'canonical_genre',
                   '题材别名',
                   '核心调性',
                   '节奏策略',
                   '毒点',
                   '推荐基础检索表',
                   '推荐动态检索表',
                   '默认查询词'],
 'adjudication': ['编号',
                  '适用技能',
                  '分类',
                  '层级',
                  '关键词',
                  '意图与同义词',
                  '适用题材',
                  '大模型指令',
                  '核心摘要',
                  '详细展开',
                  '题材',
                  '风格优先级',
                  '爽点优先级',
                  '节奏默认策略',
                  '毒点权重',
                  '冲突裁决',
                  'contract注入层',
                  '反模式']}


def test_english_tokens_do_not_match_arbitrary_substrings():
    out = search(CSV_DIR, 'write', 'qzxvplmzznotaword')
    assert out['data']['results'] == []
    combat = search(CSV_DIR, 'write', 'combat', table='scenes')
    assert combat['data']['results']
