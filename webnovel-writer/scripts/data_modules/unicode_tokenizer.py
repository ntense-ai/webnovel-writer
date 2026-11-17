"""Dependency-free Unicode lexical tokens, not language-specific morphology.

Whitespace-delimited scripts retain letters, numbers and attached marks. East
Asian syllabic/logographic runs emit characters and adjacent bigrams so a query
can match within unspaced prose. This favors recall, not linguistic word counts.
"""
from __future__ import annotations

import unicodedata

TOKENIZER_VERSION = 'unicode-v1-' + unicodedata.unidata_version


def _segmented(character: str) -> bool:
    code = ord(character)
    return (
        0x3400 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF
        or 0x20000 <= code <= 0x323AF
        or 0x3040 <= code <= 0x30FF or 0x31F0 <= code <= 0x31FF
        or 0x1100 <= code <= 0x11FF or 0x3130 <= code <= 0x318F
        or 0xA960 <= code <= 0xA97F or 0xAC00 <= code <= 0xD7FF
    )


def tokenize(text: str) -> list[str]:
    normalized = unicodedata.normalize('NFC', unicodedata.normalize('NFKC', text).casefold())
    tokens: list[str] = []
    run: list[str] = []
    segmented = False

    def flush() -> None:
        if not run:
            return
        if segmented:
            tokens.extend(run)
            tokens.extend(left + right for left, right in zip(run, run[1:]))
        else:
            tokens.append(''.join(run))
        run.clear()

    for character in normalized:
        category = unicodedata.category(character)
        if category.startswith('M'):
            if run:
                run[-1] += character
            continue
        if category[0] not in ('L', 'N'):
            flush()
            continue
        next_segmented = _segmented(character)
        if run and next_segmented != segmented:
            flush()
        segmented = next_segmented
        run.append(character)
    flush()
    return tokens
