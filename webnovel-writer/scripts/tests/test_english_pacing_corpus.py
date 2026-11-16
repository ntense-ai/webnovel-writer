"""English prose must not alter the pacing corpus's machine-readable metadata."""
import csv
import hashlib
import json
from pathlib import Path
import re

CORPUS = Path(__file__).resolve().parents[2] / 'references' / 'csv' / '爽点与节奏.csv'
METADATA = ['编号', '适用技能', '分类', '层级', '适用题材']


def test_english_pacing_prose_preserves_metadata_and_encoding():
    assert CORPUS.read_bytes().startswith(b'\xef\xbb\xbf')
    with CORPUS.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        assert reader.fieldnames == ['编号', '适用技能', '分类', '层级', '关键词', '意图与同义词',
                                    '适用题材', '大模型指令', '核心摘要', '详细展开', '节奏类型', '情绪调动手法', '毒点']
    assert [r['编号'] for r in rows] == [f'PA-{i:03d}' for i in range(1, 105)]
    metadata = [{key: row[key] for key in METADATA} for row in rows]
    digest = hashlib.sha256(json.dumps(metadata, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    assert digest == 'df27fd7dbbe9940e9c6d68f97f123ee6d93a1aa3c1f27809d7ec9df07631d3e9'
    for row in rows:
        for key, value in row.items():
            if key not in METADATA:
                assert value.strip(), (row['编号'], key)
                assert not re.search(r'[\u4e00-\u9fff]', value), (row['编号'], key)
    # Preserve concrete teaching examples rather than replacing rows with boilerplate.
    assert 'dinosaur egg' in rows[35]['详细展开']
    assert 'ration coupons' in rows[84]['大模型指令']
    assert 'seating order' in rows[103]['核心摘要']
