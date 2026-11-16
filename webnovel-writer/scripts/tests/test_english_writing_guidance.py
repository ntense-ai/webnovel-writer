import json
import re
import pytest
from data_modules import writing_guidance_builder as builder


@pytest.mark.parametrize('genre', list(builder.GENRE_METHOD_ANCHORS) + ['unknown'])
def test_all_generated_guidance_is_english_and_schema_stable(genre):
    signal = {
        'low_score_ranges': [{'start_chapter': 1, 'end_chapter': 3, 'overall_score': 60}],
        'hook_type_usage': {'mystery': 5}, 'pattern_usage': {'reversal': 4},
        'review_trend': {'overall_avg': 60},
    }
    profile = {'genre': genre, 'reference_hints': ['Make decisions matter'], 'composite_hints': ['Connect both arcs']}
    card = builder.build_methodology_strategy_card(chapter=5, reader_signal=signal, genre_profile=profile)
    assert card['chapter_stage'] == 'release'
    assert card['signals']['risk_flags'] == ['low_score_recency', 'pattern_overuse_watch', 'readability_guard']
    guidance = builder.build_guidance_items(chapter=5, reader_signal=signal, genre_profile=profile,
                                            low_score_threshold=75, hook_diversify_enabled=True)
    method = builder.build_methodology_guidance_items(card)
    checklist = builder.build_writing_checklist(guidance_items=guidance['guidance'] + method,
        reader_signal=signal, genre_profile=profile, strategy_card=card, min_items=3, max_items=30, default_weight=1)
    assert 'fix_low_score_range' in {item['id'] for item in checklist}
    assert next(item for item in checklist if item['id'] == 'fix_low_score_range')['required']
    assert not re.search(r'[\u4e00-\u9fff]', json.dumps([card, guidance, method, checklist], ensure_ascii=False))


def test_fallback_checklist_english():
    checklist = builder.build_writing_checklist(guidance_items=[], reader_signal={}, genre_profile={},
                                                min_items=3, max_items=3, default_weight=1)
    assert [row['id'] for row in checklist] == ['opening_conflict', 'scene_goal_block', 'ending_hook']
    assert all(row['verify_hint'].isascii() for row in checklist)
