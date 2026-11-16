"""English prose must not alter the pacing corpus's machine-readable metadata."""
import csv
import hashlib
import json
from pathlib import Path
import re

CORPUS = Path(__file__).resolve().parents[2] / 'references' / 'csv' / 'pacing.csv'
METADATA = ['id', 'applicable_skills', 'category', 'level', 'applicable_genres']


def test_english_pacing_prose_preserves_metadata_and_encoding():
    assert CORPUS.read_bytes().startswith(b'\xef\xbb\xbf')
    with CORPUS.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        assert reader.fieldnames == ['id', 'applicable_skills', 'category', 'level', 'keywords', 'intent_synonyms',
                                    'applicable_genres', 'model_instruction', 'summary', 'details', 'pacing_type', 'emotional_techniques', 'pitfalls']
    assert [r['id'] for r in rows] == [f'PA-{i:03d}' for i in range(1, 105)]
    metadata = [{key: row[key] for key in METADATA} for row in rows]
    digest = hashlib.sha256(json.dumps(metadata, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    assert digest == '227a85331ec1297a3976ae31a2e3094545f3828d571f4b6dd76b0eb47f314f23'
    for row in rows:
        for key, value in row.items():
            assert value.strip(), (row['id'], key)
            assert not re.search(r'[\u4e00-\u9fff]', value), (row['id'], key)
    # Preserve concrete teaching examples rather than replacing rows with boilerplate.
    assert 'dinosaur egg' in rows[35]['details']
    assert 'ration coupons' in rows[84]['model_instruction']
    assert 'seating order' in rows[103]['summary']
