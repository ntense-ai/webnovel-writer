from data_modules.query_router import QueryRouter
from data_modules.state_validator import is_resolved_foreshadowing_status


def test_english_relationship_routing_and_reversed_chapter_range():
    router = QueryRouter()
    result = router.route_intent('relationship between "Xiao Yan" and "Yao Lao" in chapters 12 to 3')
    assert result['intent'] == 'relationship'
    assert result['needs_graph'] is True
    assert result['time_scope'] == {'from_chapter': 3, 'to_chapter': 12}
    assert result['entities'][:2] == ['Xiao Yan', 'Yao Lao']


def test_unicode_names_and_english_query_splitting():
    router = QueryRouter()
    result = router.route_intent('character "Élodie" in Chapter 5')
    assert 'Élodie' in result['entities']
    assert result['time_scope'] == {'from_chapter': 5, 'to_chapter': 5}
    assert router.split('Sandra and Randall; location') == ['Sandra', 'Randall', 'location']


def test_resolved_status_does_not_match_unresolved_substring():
    assert not is_resolved_foreshadowing_status('unresolved')
    assert not is_resolved_foreshadowing_status('UNRESOLVED')
    assert is_resolved_foreshadowing_status('resolved')
