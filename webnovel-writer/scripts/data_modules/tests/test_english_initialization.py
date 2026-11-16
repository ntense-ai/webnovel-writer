"""English input and generated starter content retain the stable genre schema."""
import json

import pytest

import init_project as initializer
from genre_taxonomy import resolve_genre_input
from project_paths import project_path


@pytest.mark.parametrize('label,canonical', [
    ('fantasy', '奇幻'), ('science fiction', '科幻'), ('Mystery', '悬疑'),
    ('historical romance', '古言'), ('urban fantasy', '都市'),
    ('cultivation', '仙侠'), ('xuanhuan', '玄幻'), ('fanfiction', '衍生'),
])
def test_english_genres_resolve_to_stable_internal_keys(label, canonical):
    assert resolve_genre_input(label).canonical_genre == canonical
    assert initializer._validate_initial_genre_source(label) == label


def test_unknown_english_genre_is_not_silently_accepted():
    with pytest.raises(SystemExit, match='Unknown genre label'):
        initializer._validate_initial_genre_source('mystery+unrecognizedgenre')


def test_template_fields_support_english_and_legacy_labels():
    rendered = initializer._apply_label_replacements('- Name:\n- 姓名：\n- Age:', {'姓名': 'Alice'})
    assert rendered == '- Name: Alice\n- 姓名： Alice\n- Age:'


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
    assert state['project_info']['genre'] == '科幻'
    assert state['project_info']['genre_label'] == 'science fiction'
    protagonist = project_path(tmp_path, 'settings/主角卡.md')
    assert '- Name: Alice' in protagonist.read_text()
    assert '- True desire (possibly unconscious): Find her brother' in protagonist.read_text()
    assert '- Number of continents/planes: Three planets' in project_path(tmp_path, 'settings/世界观.md').read_text()
    assert '- System type: Technology' in project_path(tmp_path, 'settings/力量体系.md').read_text()
    assert '| Alice | Pilot |' in project_path(tmp_path, 'settings/主角组.md').read_text()
    assert '- Name: Eve' in project_path(tmp_path, 'settings/女主卡.md').read_text()
    assert '| Major antagonist | Director | Late stage |' in project_path(tmp_path, 'settings/反派设计.md').read_text()
    outline = project_path(tmp_path, 'outlines/总纲.md').read_text()
    assert '| 1 | | Chapters 1-50 |' in outline
    assert outline.count('| 1 |') == 1
    assert '| 2 |' not in outline
    protagonist.write_text('Custom character biography')
    initializer.init_project(str(tmp_path), 'The Last Star', 'science fiction')
    assert protagonist.read_text() == 'Custom character biography'


def test_legacy_chinese_genre_still_resolves():
    assert resolve_genre_input('规则怪谈').canonical_genre == '悬疑'
    assert initializer._validate_initial_genre_source('规则怪谈') == '规则怪谈'


def test_english_fallback_outline_and_ensemble_detection():
    text = initializer._build_master_outline(80)
    assert 'Volume 1 (Chapters 1-50)' in text
    assert 'Volume 2 (Chapters 51-80)' in text
    assert initializer._needs_protagonist_group('Dual protagonists')
    assert initializer._needs_protagonist_group('双主角')
    assert not initializer._needs_protagonist_group('single protagonist')
