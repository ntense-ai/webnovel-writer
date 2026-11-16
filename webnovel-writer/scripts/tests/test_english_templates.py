"""English templates remain readable and their structured examples remain valid."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

TEMPLATES = Path(__file__).resolve().parents[2] / 'templates'


def test_all_template_paths_and_contents_are_english():
    templates = list(TEMPLATES.rglob('*.md'))
    assert len(templates) >= 40
    for path in templates:
        assert not re.search(r'[\u3400-\u9fff\uf900-\ufaff]', str(path.relative_to(TEMPLATES)))
        text = path.read_text()
        assert text.strip()
        assert not re.search(r'[\u3400-\u9fff\uf900-\ufaff]', text), path


def test_entity_examples_have_valid_unique_attributes_and_english_values():
    count = 0
    for path in TEMPLATES.rglob('*.md'):
        for snippet in re.findall(r'<entity\b[^\n]*?/>', path.read_text()):
            entity = ET.fromstring(snippet)
            assert {'type', 'name', 'desc', 'tier'} <= entity.attrib.keys(), path
            assert entity.attrib['type'].isascii()
            assert entity.attrib['name'].strip()
            count += 1
    assert count >= 100
