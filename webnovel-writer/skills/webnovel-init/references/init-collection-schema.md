# Initialization collection object (internal data model)

> During Deep collection, `/webnovel-init` collects information field by field using this structure. Run `webnovel.py init` only after fields are complete and the sufficiency gate passes. This file is a field reference, not an executable script.

```json
{
  "project": {
    "title": "",
    "genre": "",
    "target_words": 0,
    "target_chapters": 0,
    "one_liner": "",
    "core_conflict": "",
    "target_reader": "",
    "platform": ""
  },
  "protagonist": {
    "name": "",
    "desire": "",
    "flaw": "",
    "archetype": "",
    "structure": "单主角"
  },
  "relationship": {
    "heroine_config": "",
    "heroine_names": [],
    "heroine_role": "",
    "co_protagonists": [],
    "co_protagonist_roles": [],
    "antagonist_tiers": {},
    "antagonist_level": "",
    "antagonist_mirror": ""
  },
  "golden_finger": {
    "type": "",
    "name": "",
    "style": "",
    "visibility": "",
    "irreversible_cost": "",
    "growth_rhythm": ""
  },
  "world": {
    "scale": "",
    "factions": "",
    "power_system_type": "",
    "social_class": "",
    "resource_distribution": "",
    "currency_system": "",
    "currency_exchange": "",
    "sect_hierarchy": "",
    "cultivation_chain": "",
    "cultivation_subtiers": ""
  },
  "constraints": {
    "anti_trope": "",
    "hard_constraints": [],
    "core_selling_points": [],
    "opening_hook": ""
  }
}
```

## Field-to-collection-step mapping

| Field group | Step | Description |
|--------|-----------|------|
| `project.*` | Step 2 | Story core and commercial positioning (title/genre/scale/one-liner/core conflict/readers/platform) |
| `protagonist.*` | Step 3 | Protagonist skeleton (name/desire/flaw/archetype/structure) |
| `relationship.*` | Step 3 | Romance, antagonist tiers, and mirror conflict |
| `golden_finger.*` | Step 4 | Special-ability type, style, visibility, irreversible cost, and growth pacing |
| `world.*` | Step 5 | World scale, power system, factions, social classes, currency, and realm chain |
| `constraints.*` | Step 6 | Anti-trope, hard constraints, core selling points, and opening hook |

Required fields are governed by the sufficiency gate in SKILL.md; optional fields may be left empty or set to “none”. The runtime value `单主角` means “single protagonist”.
