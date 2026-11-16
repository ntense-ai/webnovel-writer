#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Writing guidance and checklist builders.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .genre_aliases import to_profile_key


GENRE_GUIDANCE_TEXT: dict[str, str] = {
    "xianxia": "Genre emphasis: show tangible advancement and confrontation outcomes before explaining terminology.",
    "shuangwen": "Genre emphasis: maintain frequent payoffs and add a contrasting secondary payoff.",
    "urban-power": "Genre emphasis: show social consequences through reactions, resource changes, and status shifts.",
    "romance": "Genre emphasis: advance the relationship each chapter instead of repeating emotional stalemates.",
    "mystery": "Genre emphasis: make clues pay off and use conflicting rules to create suspense.",
    "rules-mystery": "Genre emphasis: establish rules before explanations and costs before victory.",
    "zhihu-short": "Genre emphasis: compress setup; prioritize reversals and strong ending hooks.",
    "substitute": "Genre emphasis: advance misunderstanding, tension, and decision without repeating emotional suffering.",
    "esports": "Genre emphasis: show at least one tactical decision and its consequences in each contest.",
    "livestream": "Genre emphasis: connect audience feedback, protagonist response, and measurable results immediately.",
    "cosmic-horror": "Genre emphasis: derive horror from rules and costs rather than vague frightening adjectives.",
}


GENRE_METHOD_ANCHORS: dict[str, dict[str, str]] = {
    "xianxia": {
        "pressure_source": "Resource competition / power-level suppression",
        "release_target": "The protagonist actively breaks the impasse and gains tangible rewards",
    },
    "urban-power": {
        "pressure_source": "Class barriers / abuse of power",
        "release_target": "The protagonist gains status and rewards through resource negotiation",
    },
    "romance": {
        "pressure_source": "Relationship misunderstandings / emotional tension",
        "release_target": "A tangible relationship shift leads to a new commitment",
    },
    "mystery": {
        "pressure_source": "Missing clues / conflicting rules",
        "release_target": "Provide a verifiable new clue while preserving an unknown",
    },
    "rules-mystery": {
        "pressure_source": "Rule backlash / escalating costs",
        "release_target": "Earn a breakthrough at a cost and raise a higher-order rule question",
    },
    "zhihu-short": {
        "pressure_source": "Information gaps / clashing positions",
        "release_target": "Deliver the reversal and create a strong ending hook",
    },
    "substitute": {
        "pressure_source": "Mistaken identity / emotional confrontation",
        "release_target": "Advance the misunderstanding toward a clear decision",
    },
    "esports": {
        "pressure_source": "Tactical pressure / disrupted tempo",
        "release_target": "A key decision pays off and creates a strategic advantage",
    },
    "livestream": {
        "pressure_source": "Shifting public opinion / declining metrics",
        "release_target": "An immediate response produces a measurable recovery",
    },
    "cosmic-horror": {
        "pressure_source": "Distorted perception / eroding rules",
        "release_target": "Pay a clear cost to secure temporary survival",
    },
    "history-travel": {
        "pressure_source": "Historical inertia / restrictive social norms",
        "release_target": "Turn superior knowledge into gains and new cascading consequences",
    },
    "game-lit": {
        "pressure_source": "System constraints / scarce resources",
        "release_target": "Achieve a statistical breakthrough and expose a higher-level threat",
    },
}


def build_methodology_strategy_card(
    *,
    chapter: int,
    reader_signal: Dict[str, Any],
    genre_profile: Dict[str, Any],
    label: str = "digital-serial-v1",
) -> Dict[str, Any]:
    genre = str(genre_profile.get("genre") or "").strip()
    profile_key = to_profile_key(genre) or "general"

    hook_usage = reader_signal.get("hook_type_usage") or {}
    pattern_usage = reader_signal.get("pattern_usage") or {}
    review_trend = reader_signal.get("review_trend") or {}
    low_ranges = reader_signal.get("low_score_ranges") or []

    dominant_hook = ""
    if isinstance(hook_usage, dict) and hook_usage:
        dominant_hook = max(hook_usage.items(), key=lambda kv: kv[1])[0]

    dominant_pattern = ""
    if isinstance(pattern_usage, dict) and pattern_usage:
        dominant_pattern = max(pattern_usage.items(), key=lambda kv: kv[1])[0]

    overall_avg = float(review_trend.get("overall_avg") or 0.0)
    has_low_range = bool(low_ranges)
    hook_variety = len(hook_usage) if isinstance(hook_usage, dict) else 0
    pattern_variety = len(pattern_usage) if isinstance(pattern_usage, dict) else 0

    next_reason_clarity = 70.0 + (4.0 if has_low_range else 8.0)
    anchor_effectiveness = 68.0 + (6.0 if dominant_hook else 0.0) + (4.0 if overall_avg >= 75 else -4.0)
    rhythm_naturalness = 65.0 + min(10.0, float(hook_variety + pattern_variety) * 2.0)

    risk_flags: List[str] = []
    if has_low_range:
        risk_flags.append("low_score_recency")
    if dominant_pattern:
        risk_flags.append("pattern_overuse_watch")
    if overall_avg > 0 and overall_avg < 75:
        risk_flags.append("readability_guard")

    stage_mod = chapter % 5
    if stage_mod in {1, 2}:
        stage = "build_up"
    elif stage_mod in {3, 4}:
        stage = "confront"
    else:
        stage = "release"

    anchor_preset = GENRE_METHOD_ANCHORS.get(
        profile_key,
        {
            "pressure_source": "Survival goals / resource competition",
            "release_target": "The protagonist completes an intermediate goal and gains a new reason to act",
        },
    )

    return {
        "enabled": True,
        "framework": label,
        "pilot": profile_key,
        "genre_profile_key": profile_key,
        "chapter_stage": stage,
        "emotion_anchor": {
            "pressure_source": anchor_preset["pressure_source"],
            "release_target": anchor_preset["release_target"],
            "position_hint": "Establish pressure early and release it later; avoid rigid word-count beats",
        },
        "long_arc_controls": {
            "map_transition": "Carry existing assets and relationships into new stages; do not reset abilities or gains",
            "power_guard": "Explain the mechanism behind key victories: information, resources, costs, or strategy",
            "antagonist_model": "Give antagonists goals, means, and costs rather than treating them as plot devices",
        },
        "serialization_ops": {
            "next_reason": "Give a clear, repeatable reason to read the next chapter near the ending",
            "interaction_note": "Leave one debatable point to encourage reader discussion",
        },
        "observability": {
            "next_reason_clarity": round(max(0.0, min(100.0, next_reason_clarity)), 2),
            "anchor_effectiveness": round(max(0.0, min(100.0, anchor_effectiveness)), 2),
            "rhythm_naturalness": round(max(0.0, min(100.0, rhythm_naturalness)), 2),
        },
        "signals": {
            "dominant_hook": dominant_hook,
            "dominant_pattern": dominant_pattern,
            "risk_flags": risk_flags,
        },
    }


def build_methodology_guidance_items(strategy_card: Dict[str, Any]) -> List[str]:
    if not isinstance(strategy_card, dict) or not strategy_card.get("enabled"):
        return []

    observability = strategy_card.get("observability") or {}
    signals = strategy_card.get("signals") or {}
    risk_flags = list(signals.get("risk_flags") or [])
    stage = str(strategy_card.get("chapter_stage") or "build_up")
    genre_key = str(strategy_card.get("genre_profile_key") or strategy_card.get("pilot") or "general")

    stage_text = {
        "build_up": "Build pressure in this chapter by making threats and costs tangible.",
        "confront": "Focus on direct confrontation and make the resolution understandable and traceable.",
        "release": "Focus on release and aftermath; deliver tangible gains and raise the next question.",
    }.get(stage, "Maintain a complete pressure, breakthrough, and aftermath sequence.")

    items = [
        f"Methodology strategy (general/{genre_key}): {stage_text}",
        "Long-arc control: preserve established assets, abilities, and resources when changing settings.",
        "Mechanism control: explain the mechanism and cost of key victories instead of relying on plot armor.",
        (
            "Reader engagement: leave a debatable point and strengthen the reason to continue."
            f" (next_reason={observability.get('next_reason_clarity')})"
        ),
    ]

    if "pattern_overuse_watch" in risk_flags:
        dominant_pattern = str(signals.get("dominant_pattern") or "").strip()
        if dominant_pattern:
            items.append(f"Risk adjustment: {dominant_pattern} has appeared often; add a contrasting secondary thread to avoid fatigue.")
    if "readability_guard" in risk_flags:
        items.append("Risk adjustment: recent review averages are low; prioritize clear action-result sequences and readability.")

    return items


def build_guidance_items(
    *,
    chapter: int,
    reader_signal: Dict[str, Any],
    genre_profile: Dict[str, Any],
    low_score_threshold: float,
    hook_diversify_enabled: bool,
) -> Dict[str, Any]:
    guidance: List[str] = []

    low_ranges = reader_signal.get("low_score_ranges") or []
    if low_ranges:
        worst = min(
            low_ranges,
            key=lambda row: float(row.get("overall_score", 9999)),
        )
        guidance.append(
            f"Chapter {chapter}: address recent low-scoring issues from chapters {worst.get('start_chapter')}-{worst.get('end_chapter')}; improve conflict progression and ending hooks."
        )

    hook_usage = reader_signal.get("hook_type_usage") or {}
    if hook_usage and hook_diversify_enabled:
        dominant_hook = max(hook_usage.items(), key=lambda kv: kv[1])[0]
        guidance.append(
            f"The {dominant_hook} hook has been overused recently; vary this chapter to avoid repeated structures."
        )

    pattern_usage = reader_signal.get("pattern_usage") or {}
    if pattern_usage:
        top_pattern = max(pattern_usage.items(), key=lambda kv: kv[1])[0]
        guidance.append(
            f"The {top_pattern} payoff pattern is frequent; retain the main payoff but add a fresh secondary payoff."
        )

    review_trend = reader_signal.get("review_trend") or {}
    overall_avg = review_trend.get("overall_avg")
    if isinstance(overall_avg, (int, float)) and float(overall_avg) < low_score_threshold:
        guidance.append(
            f"Recent review average {overall_avg:.1f} is below {low_score_threshold:.1f}; stabilize quality with fewer scene jumps and clear action-result sequences."
        )

    genre = str(genre_profile.get("genre") or "").strip()
    refs = genre_profile.get("reference_hints") or []
    if genre:
        guidance.append(f"Genre anchor: follow the {genre} narrative throughline and consistently meet reader expectations.")
    if refs:
        guidance.append(f"Actionable genre strategy: {refs[0]}")

    guidance.append("Serial pacing baseline: establish a goal and obstacle within the first 300 words; end with an open question.")
    guidance.append("Payoff baseline: offer a small payoff every 600-900 words and at least one measurable change per chapter.")

    normalized_genre = to_profile_key(genre)
    genre_hint = GENRE_GUIDANCE_TEXT.get(normalized_genre)
    if genre_hint:
        guidance.append(genre_hint)

    composite_hints = genre_profile.get("composite_hints") or []
    if composite_hints:
        guidance.append(f"Hybrid genre coordination: {composite_hints[0]}")

    if not guidance:
        guidance.append("Default readability strategy: introduce conflict early, explain later, and end passages with hooks.")

    return {
        "guidance": guidance,
        "low_ranges": low_ranges,
        "hook_usage": hook_usage,
        "pattern_usage": pattern_usage,
        "genre": genre,
    }


def build_writing_checklist(
    *,
    guidance_items: List[str],
    reader_signal: Dict[str, Any],
    genre_profile: Dict[str, Any],
    strategy_card: Dict[str, Any] | None = None,
    min_items: int,
    max_items: int,
    default_weight: float,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    def _add_item(
        item_id: str,
        label: str,
        *,
        weight: float | None = None,
        required: bool = False,
        source: str = "writing_guidance",
        verify_hint: str = "",
    ) -> None:
        if len(items) >= max_items:
            return
        if any(row.get("id") == item_id for row in items):
            return

        item_weight = float(weight if weight is not None else default_weight)
        if item_weight <= 0:
            item_weight = default_weight

        items.append(
            {
                "id": item_id,
                "label": label,
                "weight": round(item_weight, 2),
                "required": bool(required),
                "source": source,
                "verify_hint": verify_hint,
            }
        )

    low_ranges = reader_signal.get("low_score_ranges") or []
    if low_ranges:
        worst = min(low_ranges, key=lambda row: float(row.get("overall_score", 9999)))
        span = f"{worst.get('start_chapter')}-{worst.get('end_chapter')}"
        _add_item(
            "fix_low_score_range",
            f"Address low-scoring sections (see chapters {span})",
            weight=max(default_weight, 1.4),
            required=True,
            source="reader_signal.low_score_ranges",
            verify_hint="Escalate conflict at least once and end the passage with a hook.",
        )

    hook_usage = reader_signal.get("hook_type_usage") or {}
    if hook_usage:
        dominant_hook = max(hook_usage.items(), key=lambda kv: kv[1])[0]
        _add_item(
            "hook_diversification",
            f"Vary hooks (avoid relying only on {dominant_hook})",
            weight=max(default_weight, 1.2),
            required=True,
            source="reader_signal.hook_type_usage",
            verify_hint="Make the ending hook differ from the dominant type in the last 20 chapters.",
        )

    pattern_usage = reader_signal.get("pattern_usage") or {}
    if pattern_usage:
        top_pattern = max(pattern_usage.items(), key=lambda kv: kv[1])[0]
        _add_item(
            "coolpoint_combo",
            f"Combine primary and secondary payoffs (primary: {top_pattern})",
            weight=default_weight,
            required=False,
            source="reader_signal.pattern_usage",
            verify_hint="Add at least one secondary payoff causally linked to the main payoff.",
        )

    review_trend = reader_signal.get("review_trend") or {}
    overall_avg = review_trend.get("overall_avg")
    if isinstance(overall_avg, (int, float)):
        _add_item(
            "readability_loop",
            "Readable paragraph sequence (action, result, emotion)",
            weight=max(default_weight, 1.1),
            required=True,
            source="reader_signal.review_trend",
            verify_hint="Check three paragraphs for a complete action-result sequence.",
        )

    genre = str(genre_profile.get("genre") or "").strip()
    if genre:
        _add_item(
            "genre_anchor_consistency",
            f"Consistent genre anchor ({genre})",
            weight=max(default_weight, 1.1),
            required=True,
            source="genre_profile.genre",
            verify_hint="Keep the main conflict consistent with the core genre promise.",
        )

    if isinstance(strategy_card, dict) and strategy_card.get("enabled"):
        _add_item(
            "methodology_next_reason",
            "Methodology: provide a repeatable reason to continue near the ending",
            weight=default_weight,
            required=False,
            source="methodology.next_reason",
            verify_hint="Summarize in one sentence why the reader should open the next chapter.",
        )
        _add_item(
            "methodology_power_guard",
            "Methodology: explain mechanisms and costs behind breakthroughs and overcoming stronger opponents",
            weight=default_weight,
            required=False,
            source="methodology.power_guard",
            verify_hint="Show at least one explanatory mechanism and one cost."
        )
        _add_item(
            "methodology_antagonist_pressure",
            "Methodology: give antagonist actions goals, means, and costs",
            weight=default_weight,
            required=False,
            source="methodology.antagonist",
            verify_hint="Give antagonists understandable motives rather than using them as plot devices.",
        )

    for idx, text in enumerate(guidance_items, start=1):
        if len(items) >= max_items:
            break
        label = str(text).strip()
        if not label:
            continue
        _add_item(
            f"guidance_item_{idx}",
            label,
            weight=default_weight,
            required=False,
            source="writing_guidance.guidance_items",
            verify_hint="Identify the corresponding passage in the finished chapter.",
        )

    fallback_items = [
        (
            "opening_conflict",
            "Introduce a conflict trigger within the first 300 words",
            "Show a clear goal and obstacle in the opening.",
        ),
        (
            "scene_goal_block",
            "Make scene goals and obstacles clear",
            "Give every scene at least one verifiable goal.",
        ),
        (
            "ending_hook",
            "End with a hook that raises the next question",
            "End with an unresolved question or a next action.",
        ),
    ]
    for item_id, label, verify_hint in fallback_items:
        if len(items) >= min_items or len(items) >= max_items:
            break
        _add_item(
            item_id,
            label,
            weight=default_weight,
            required=False,
            source="fallback",
            verify_hint=verify_hint,
        )

    return items[:max_items]


def is_checklist_item_completed(item: Dict[str, Any], reader_signal: Dict[str, Any]) -> bool:
    item_id = str(item.get("id") or "")
    if item_id in {"fix_low_score_range", "readability_loop"}:
        review_trend = reader_signal.get("review_trend") or {}
        overall = review_trend.get("overall_avg")
        return isinstance(overall, (int, float)) and float(overall) >= 75.0

    if item_id == "hook_diversification":
        hook_usage = reader_signal.get("hook_type_usage") or {}
        return len(hook_usage) >= 2

    if item_id == "coolpoint_combo":
        pattern_usage = reader_signal.get("pattern_usage") or {}
        return len(pattern_usage) >= 2

    if item_id == "genre_anchor_consistency":
        return True

    source = str(item.get("source") or "")
    if source.startswith("fallback"):
        return True

    if source.startswith("methodology."):
        # 方法论条目当前作为软提示，仅做观察与引导，不参与扣分。
        return True

    return False
