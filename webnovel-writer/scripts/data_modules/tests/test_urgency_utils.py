#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""urgency_utils.coerce_urgency unit tests。"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

# ensure scripts/ at sys.path in
_scripts_dir = str(Path(__file__).resolve().parent.parent.parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from data_modules.urgency_utils import coerce_urgency


class TestCoerceUrgencyNumeric:
    """numeric input passes through。"""

    def test_int_input(self):
        assert coerce_urgency(80) == 80.0

    def test_float_input(self):
        assert coerce_urgency(0.9) == pytest.approx(0.9)

    def test_zero(self):
        assert coerce_urgency(0) == 0.0

    def test_large_number_not_clamped(self):
        # current implementation does not clamp the upper bound，normalization only；if needed later clamp，then add separately。
        assert coerce_urgency(150) == 150.0

    def test_negative_number_preserved(self):
        # negative values are unusual but，but coerce must not silently modify it。
        assert coerce_urgency(-5) == -5.0


class TestCoerceUrgencyString:
    """string input is mapped or parsed。"""

    @pytest.mark.parametrize(
        "label,expected",
        [
            ("high", 100.0),
            ("HIGH", 100.0),
            ("  High  ", 100.0),
            ("medium", 60.0),
            ("Medium", 60.0),
            ("low", 20.0),
        ],
    )
    def test_natural_language_label(self, label, expected):
        assert coerce_urgency(label) == expected

    @pytest.mark.parametrize(
        "numeric_str,expected",
        [
            ("100", 100.0),
            ("3.14", 3.14),
            ("1e2", 100.0),
            (" 42 ", 42.0),
        ],
    )
    def test_numeric_string(self, numeric_str, expected):
        assert coerce_urgency(numeric_str) == pytest.approx(expected)

    def test_unknown_label_returns_default(self):
        # "critical"/"urgent" not in the mapping → go default
        assert coerce_urgency("critical") == 0.0
        assert coerce_urgency("critical", default=50.0) == 50.0

    def test_empty_string_returns_default(self):
        assert coerce_urgency("") == 0.0
        assert coerce_urgency("   ") == 0.0

    def test_invalid_string_does_not_raise(self):
        """key：old version would raise，new version must return safely default。"""
        try:
            result = coerce_urgency("not-a-number")
        except Exception as e:  # pragma: no cover - regression guard
            pytest.fail(f"coerce_urgency should not raise on invalid string: {e}")
        assert result == 0.0


class TestCoerceUrgencyOther:
    """other types/edge cases。"""

    def test_none(self):
        assert coerce_urgency(None) == 0.0

    def test_none_with_custom_default(self):
        assert coerce_urgency(None, default=42.0) == 42.0

    def test_bool_returns_default(self):
        # bool is int subclass，but the meaning is not urgency；explicitly return default。
        assert coerce_urgency(True) == 0.0
        assert coerce_urgency(False) == 0.0

    def test_list_returns_default(self):
        assert coerce_urgency([100]) == 0.0

    def test_dict_returns_default(self):
        assert coerce_urgency({"urgency": 100}) == 0.0


class TestRegressionOriginalBug:
    """reproduce Issue：data-agent output string urgency causes downstream ValueError。"""

    def test_high_no_longer_raises(self):
        """old code float("high") raise ValueError，new code must return normally。"""
        result = coerce_urgency("high")
        assert math.isfinite(result)
        assert result > 0
