# Genre Templates

## Overview

The system includes 37 web-novel genre templates (in `templates/genres/`), covering the major web-fiction genres.
It supports a single genre or a hybrid of up to two genres.

## Supported Genre Categories

### Fantasy and Cultivation

Cultivation, system fiction, high-martial-arts fantasy, Western fantasy, infinite-world fiction, apocalypse, and science fiction.

### Contemporary and Urban

Urban supernatural powers, urban slice of life, high-concept urban fiction, realism, esports, and livestream fiction.

### Romance

Historical romance, palace and household intrigue, sweet youth romance, wealthy CEO romance, workplace and marriage romance, Republican-era romance, fantasy romance, high-concept contemporary romance, women-oriented mystery, farming fiction, and period fiction.

### Other Genres

Rules-based horror, high-concept mystery, supernatural mystery, Cthulhu fiction, melodramatic romance, substitute-lover fiction, Zhihu short fiction, and more.

## Genre Aliases

The system automatically recognizes common aliases, for example. The literal inputs below are retained because they are recognized by the parser:

| Input | Automatically mapped to |
|------|-----------|
| xuanhuan、cultivation、xuanhuancultivation (fantasy/cultivation variants) | cultivation (cultivation) |
| urbancultivation (urban cultivation) | urban-fantasy (urban supernatural powers) |
| gaming-esports、esportsfiction (gaming/esports fiction) | esports (esports) |
| livestreaming、streamer、livestream commerce (livestreaming, streamers, live commerce) | livestream-fiction (livestream fiction) |
| cosmic horror、cosmic horrormystery (Cthulhu-style fiction/mystery) | cosmic-horror (Cthulhu fiction) |

## Hybrid-Genre Rules

- Join two genres with `+` (for example, `urban-speculative+rules-horror`, high-concept urban fiction + rules-based horror). Separators `/`, `、`, and `and` are also supported.
- Combine no more than two genres.
- A 7:3 primary-to-secondary ratio is recommended: the main plot follows the primary genre's logic, while the secondary genre supplies hooks, rules, and satisfying payoffs.

Examples (literal supported genre inputs):

- `urban-speculative+rules-horror`
- `cultivation+system-fiction`
- `historical-romance+palace-household-intrigue`

## Genre Template Outputs

When a project is initialized, the selected genre template is automatically inserted into the reference-genre-template section (`referencegenretemplate`) of `settings/worldbuilding.md`.

The system also includes six fine-tuned genre configuration directories (`genres/`) with more detailed writing guidance for specific genres:

- `xuanhuan` (Chinese fantasy)
- `dog-blood-romance` (melodramatic romance)
- `period-drama` (period fiction)
- `realistic` (realism)
- `rules-mystery` (rules-based horror)
- `zhihu-short` (Zhihu short fiction)
