"""English input and generated starter content retain the stable genre schema."""
import json

import pytest

import init_project as initializer
from genre_taxonomy import resolve_genre_input
from project_paths import project_path


@pytest.mark.parametrize('label,canonical', [
    ('fantasy', 'fantasy'), ('science fiction', 'sci-fi'), ('Mystery', 'mystery'),
    ('historical romance', 'historical-romance'), ('urban fantasy', 'urban'),
    ('cultivation', 'xianxia'), ('xuanhuan', 'xuanhuan'), ('fanfiction', 'fanfiction'),
])
def test_english_genres_resolve_to_stable_internal_keys(label, canonical):
    assert resolve_genre_input(label).canonical_genre == canonical
    assert initializer._validate_initial_genre_source(label) == label


def test_unknown_english_genre_is_not_silently_accepted():
    with pytest.raises(SystemExit, match='Unknown genre label'):
        initializer._validate_initial_genre_source('mystery+unrecognizedgenre')


def test_template_fields_preserve_unicode_values_and_punctuation():
    rendered = initializer._apply_label_replacements('- Name:\n- Name：\n- Age:', {'Name': 'Élodie'})
    assert rendered == '- Name: Élodie\n- Name： Élodie\n- Age:'


def test_english_init_populates_content_and_preserves_custom_files(tmp_path, monkeypatch):
    monkeypatch.setattr(initializer, 'is_git_available', lambda: False)
    monkeypatch.setattr(initializer, 'write_current_project_pointer', lambda _: None)
    initializer.init_project(str(tmp_path), 'The Last Star', 'science fiction',
        protagonist_name='Alice', protagonist_desire='Find her brother', protagonist_flaw='Impatience',
        world_scale='Three planets', factions='The Union', power_system_type='Technology',
        protagonist_structure='ensemble', co_protagonists='Alice,Bob', co_protagonist_roles='Pilot,Medic',
        heroine_config='single', heroine_names='Eve', heroine_role='Ally',
        antagonist_tiers='Minor antagonist:Captain;Major antagonist:Director', target_chapters=80)
    state = json.loads((tmp_path / '.webnovel/state.json').read_text())
    assert state['project_info']['genre'] == 'sci-fi'
    assert state['project_info']['genre_label'] == 'science fiction'
    protagonist = project_path(tmp_path, 'settings/protagonist.md')
    assert '- Name: Alice' in protagonist.read_text()
    assert '- True desire (possibly unconscious): Find her brother' in protagonist.read_text()
    assert '- Number of continents/planes: Three planets' in project_path(tmp_path, 'settings/worldbuilding.md').read_text()
    assert '- System type: Technology' in project_path(tmp_path, 'settings/power-system.md').read_text()
    assert '| Alice | Pilot |' in project_path(tmp_path, 'settings/protagonist-team.md').read_text()
    assert '- Name: Eve' in project_path(tmp_path, 'settings/heroine.md').read_text()
    assert '| Major antagonist | Director | Late stage |' in project_path(tmp_path, 'settings/antagonist.md').read_text()
    outline = project_path(tmp_path, 'outlines/master-outline.md').read_text()
    assert '| 1 | | Chapters 1-50 |' in outline
    assert outline.count('| 1 |') == 1
    assert '| 2 |' not in outline
    protagonist.write_text('Custom character biography')
    initializer.init_project(str(tmp_path), 'The Last Star', 'science fiction')
    assert protagonist.read_text() == 'Custom character biography'


def test_english_route_genre_resolves():
    assert resolve_genre_input('rules-horror').canonical_genre == 'mystery'
    assert initializer._validate_initial_genre_source('rules-horror') == 'rules-horror'


def test_english_fallback_outline_and_ensemble_detection():
    text = initializer._build_master_outline(80)
    assert 'Volume 1 (Chapters 1-50)' in text
    assert 'Volume 2 (Chapters 51-80)' in text
    assert initializer._needs_protagonist_group('Dual protagonists')
    assert initializer._needs_protagonist_group('dual')
    assert not initializer._needs_protagonist_group('single protagonist')
