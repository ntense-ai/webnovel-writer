"""Language-aware manuscript length, retaining legacy CJK character counts."""
import re


def count_words(text: str) -> int:
    """Count English word tokens; CJK-dominant text keeps legacy character units.

    Apostrophes and hyphens inside words do not split a word. Punctuation
    and Markdown markers alone are not words. Mixed prose selects its dominant
    script using letter counts, so an incidental Chinese name does not turn an
    English chapter into a character count.
    """
    stripped = text.strip()
    cjk = len(re.findall(r"[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]", stripped))
    latin = len(re.findall(r"[A-Za-z]", stripped))
    if cjk and cjk >= latin:
        return len(stripped)
    return len(re.findall(r"[^\W_]+(?:[’'\-][^\W_]+)*", stripped, re.UNICODE))
