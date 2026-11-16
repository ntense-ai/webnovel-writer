#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"Normalize urgency values. LLM-generated commits may use high/medium/low strings while consumers such as MemoryContractAdapter and status_reporter expect numbers from 0 to 100. This shared entry point prevents float('high') errors from being swallowed by fallback handlers that silently return empty results from calls such as get_open_loops(). Mappings match DataModulesConfig.foreshadowing_urgency_score_*: high approximately 100, medium 60, low 20."
from __future__ import annotations

from typing import Any


# Map strings to numeric scores aligned with config.foreshadowing_urgency_score_*.
# Keep module constants so callers can reference their semantics directly.
_URGENCY_STRING_MAP = {
    "high": 100.0,
    "medium": 60.0,
    "low": 20.0,
}


def coerce_urgency(value: Any, default: float = 0.0) -> float:
    "Normalize input to a float from 0 to 100. Accept int/float values, numeric strings such as 100, 3.14, or 1e2, and case/whitespace-insensitive high/medium/low labels mapped to preset scores. Return default for None, empty strings, or unparseable values. A single malformed field must not crash the entire consumer."
    if value is None:
        return default
    if isinstance(value, bool):
        # Exclude bool separately: it subclasses int, but True=1.0 and False=0.0 would be misleading here.
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if not s:
            return default
        if s in _URGENCY_STRING_MAP:
            return _URGENCY_STRING_MAP[s]
        try:
            return float(s)
        except ValueError:
            return default
    return default
