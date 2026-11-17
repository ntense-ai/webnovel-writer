"""Multilingual SQLite BM25 retrieval without network or embedding requests.

Escaped Han fixtures test language support, not legacy schema identifiers.
"""
from __future__ import annotations

import sqlite3
import unicodedata

import pytest

from data_modules.config import DataModulesConfig
from data_modules.rag_adapter import RAGAdapter


@pytest.fixture
def adapter(tmp_path, monkeypatch):
    # Any accidental embedding/API use fails: the stub has no API methods.
    monkeypatch.setattr('data_modules.rag_adapter.get_client', lambda config: object())
    return RAGAdapter(DataModulesConfig.from_project_root(tmp_path))


def _insert(adapter, chunk_id, content, chapter=1):
    embedding = b'\x00\x00\x80\x3f\x00\x00\x00\x40'
    with adapter._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO vectors '
            '(chunk_id,chapter,scene_index,content,embedding,parent_chunk_id,chunk_type,source_file,created_at) '
            'VALUES (?,?,?,?,?,?,?,?,?)',
            (chunk_id, chapter, 1, content, embedding, 'parent-original', 'scene',
             f'chapters/chapter-{chapter:04d}.md', '2025-01-02 03:04:05'),
        )
        adapter._update_bm25_index(cursor, chunk_id, content)
        conn.commit()


@pytest.mark.parametrize('content,query', [
    ('The café opens at dawn.', 'cafe\u0301'),
    ('The cafe\u0301 opens at dawn.', 'CAFÉ'),
    ('ПУТЕШЕСТВЕННИК нашёл компас.', 'путешественник'),
    ('المسافر يبحث عن البوصلة', 'البوصلة'),
    ('यात्री रास्ता खोजता है', 'रास्ता'),
    ('カタカナのたびがはじまる', 'たび'),
    ('모험가는길을찾는다', '길을'),
    ('\u65c5\u884c\u8005\u627e\u5230\u6307\u5357\u9488', '\u6307\u5357\u9488'),
    ('The Navigator studies the MAP.', 'NAVIGATOR'),
    ('Route 2048, marker 17!', '2048'),
], ids=['latin-nfd-query', 'latin-nfd-content', 'cyrillic', 'arabic', 'indic', 'kana', 'hangul', 'han', 'english', 'digits'])
def test_multilingual_content_is_retrievable_from_real_sqlite_index(adapter, content, query):
    _insert(adapter, 'wanted', content)
    _insert(adapter, 'unrelated', 'A quiet orchard rests beneath the moon.', chapter=2)
    results = adapter.bm25_search(query, top_k=5, log_query=False)
    assert results, (content, query)
    assert results[0].chunk_id == 'wanted'
    assert results[0].content == content
    assert results[0].source == 'bm25'
    assert results[0].score > 0
    with adapter._get_conn() as conn:
        terms = conn.execute("SELECT term FROM bm25_index WHERE chunk_id='wanted'").fetchall()
        length = conn.execute("SELECT doc_length FROM doc_stats WHERE chunk_id='wanted'").fetchone()[0]
    assert terms and length > 0


def test_normalization_is_canonical_and_case_insensitive(adapter):
    assert adapter._tokenize('CAFÉ') == adapter._tokenize('cafe\u0301') == ['café']
    assert adapter._tokenize('ПУТЬ') == adapter._tokenize('путь') == ['путь']
    assert adapter._tokenize('Straße') == adapter._tokenize('STRASSE') == ['strasse']
    assert adapter._tokenize('ＮＡＶＩＧＡＴＯＲ ２０４８') == ['navigator', '2048']
    assert all(unicodedata.normalize('NFC', term) == term
               for term in adapter._tokenize('cafe\u0301 ПУТЬ'))


def test_english_words_digits_and_punctuation(adapter):
    assert adapter._tokenize('Xiao Yan hello WORLD 2048') == ['xiao', 'yan', 'hello', 'world', '2048']
    assert adapter._tokenize('Hello, world! 17; 2048.') == ['hello', 'world', '17', '2048']
    assert adapter._tokenize('...!? — () [] {}') == []
    assert adapter._tokenize('') == []
    assert adapter.bm25_search('...!?', log_query=False) == []


def test_unspaced_scripts_keep_character_and_bigram_terms(adapter):
    for value in ('\u6307\u5357\u9488', 'かな', '한글'):
        terms = adapter._tokenize(value)
        assert all(char in terms for char in value)
        assert all(value[i:i + 2] in terms for i in range(len(value) - 1))


def _snapshot(adapter):
    with adapter._get_conn() as conn:
        return {
            'vectors': conn.execute('SELECT * FROM vectors ORDER BY chunk_id').fetchall(),
            'terms': conn.execute('SELECT * FROM bm25_index ORDER BY chunk_id, term').fetchall(),
            'stats': conn.execute('SELECT * FROM doc_stats ORDER BY chunk_id').fetchall(),
            'version': conn.execute(
                "SELECT value FROM rag_schema_meta WHERE key='tokenizer_version'"
            ).fetchone(),
        }


def _make_outdated_index(adapter, missing):
    _insert(adapter, 'first', 'CAFÉ ПУТЬ \u6307\u5357\u9488', chapter=1)
    _insert(adapter, 'second', 'البوصلة かな 한글', chapter=2)
    with adapter._get_conn() as conn:
        conn.execute('DELETE FROM bm25_index')
        conn.execute('DELETE FROM doc_stats')
        conn.execute("INSERT INTO bm25_index VALUES ('obsolete', 'first', 1.0)")
        conn.execute("INSERT INTO doc_stats VALUES ('first', 1)")
        conn.execute("INSERT INTO bm25_index VALUES ('orphan', 'deleted-chunk', 1.0)")
        conn.execute("INSERT INTO doc_stats VALUES ('deleted-chunk', 1)")
        conn.execute("DELETE FROM rag_schema_meta WHERE key='tokenizer_version'")
        if not missing:
            conn.execute("INSERT INTO rag_schema_meta(key,value) VALUES ('tokenizer_version','ascii-old')")
        conn.commit()


@pytest.mark.parametrize('missing', [True, False], ids=['missing-marker', 'stale-marker'])
def test_reopen_rebuilds_tokenizer_index_without_touching_vectors(adapter, missing):
    from data_modules.unicode_tokenizer import TOKENIZER_VERSION
    _make_outdated_index(adapter, missing)
    before = _snapshot(adapter)
    reopened = RAGAdapter(adapter.config)
    after = _snapshot(reopened)
    # Includes original content, embedding bytes, parent/source metadata and timestamp.
    assert after['vectors'] == before['vectors']
    assert after['version'] == (TOKENIZER_VERSION,)
    assert {row[0] for row in after['stats']} == {'first', 'second'}
    assert not {'obsolete', 'orphan'} & {row[0] for row in after['terms']}
    for query, expected in [('cafe\u0301', 'first'), ('путь', 'first'),
                            ('البوصلة', 'second'), ('かな', 'second'), ('한글', 'second')]:
        assert reopened.bm25_search(query, log_query=False)[0].chunk_id == expected
    assert _snapshot(RAGAdapter(adapter.config)) == after


def test_current_tokenizer_version_does_not_rebuild(adapter):
    _insert(adapter, 'first', 'café ПУТЬ')
    before = _snapshot(adapter)
    # A destructive reindex at the current version would raise immediately.
    with adapter._get_conn() as conn:
        conn.execute("CREATE TRIGGER prevent_unnecessary_reindex BEFORE DELETE ON bm25_index "
                     "BEGIN SELECT RAISE(ABORT, 'unexpected reindex'); END")
        conn.commit()
    reopened = RAGAdapter(adapter.config)
    assert _snapshot(reopened) == before


def test_failed_rebuild_rolls_back_index_and_version(adapter, monkeypatch):
    _make_outdated_index(adapter, missing=False)
    before = _snapshot(adapter)
    original = RAGAdapter._update_bm25_index
    calls = []

    def fail_after_one_document(self, cursor, chunk_id, content):
        calls.append(chunk_id)
        if len(calls) == 2:
            raise sqlite3.OperationalError('simulated rebuild failure')
        return original(self, cursor, chunk_id, content)

    with monkeypatch.context() as scoped:
        scoped.setattr(RAGAdapter, '_update_bm25_index', fail_after_one_document)
        with pytest.raises(sqlite3.OperationalError, match='simulated rebuild failure'):
            RAGAdapter(adapter.config)
    assert len(calls) == 2
    assert _snapshot(adapter) == before
    # A later clean attempt must still rebuild successfully rather than trust a stale marker.
    reopened = RAGAdapter(adapter.config)
    assert reopened.bm25_search('путь', log_query=False)[0].chunk_id == 'first'
