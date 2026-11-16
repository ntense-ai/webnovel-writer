#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genre alias normalization and profile key mapping.
"""

from __future__ import annotations

from genre_taxonomy import normalize_genre_label_for_profile


# Fallback profile keys are a legacy markdown-section namespace, not canonical
# genre values. User-input aliases live in references/taxonomy/genre-index.csv.
GENRE_PROFILE_KEY_ALIASES: dict[str, str] = {
    "cultivation": "xianxia",
    "power-fantasy/system-fiction": "shuangwen",
    "high-martial-power": "xianxia",
    "western-fantasy": "xianxia",
    "urban-fantasy": "urban-power",
    "urban-speculative": "urban-power",
    "urban-slice-of-life": "urban-power",
    "melodramatic-romance": "romance",
    "historical-romance": "romance",
    "young-sweet-romance": "romance",
    "substitute-romance": "substitute",
    "rules-horror": "rules-mystery",
    "speculative-mystery": "mystery",
    "paranormal-mystery": "mystery",
    "zhihu-short-fiction": "zhihu-short",
    "esports": "esports",
    "livestream-fiction": "livestream",
    "cosmic-horror": "cosmic-horror",
}


def normalize_genre_token(token: str) -> str:
    value = str(token or "").strip()
    if not value:
        return ""
    # Established Markdown profile keys must not be remapped through the
    # new user-facing taxonomy aliases (xuanhuan is not xianxia here).
    if value.lower() in {*GENRE_PROFILE_KEY_ALIASES.values(), "xuanhuan", "game-lit", "history-travel", "general"}:
        return value.lower()
    return normalize_genre_label_for_profile(value)


def to_profile_key(genre: str) -> str:
    value = str(genre or "").strip()
    if not value:
        return ""
    normalized = normalize_genre_token(value)
    return GENRE_PROFILE_KEY_ALIASES.get(normalized, normalized.lower())

