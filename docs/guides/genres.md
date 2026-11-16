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
| 玄幻、修真、玄幻修仙 (fantasy/cultivation variants) | 修仙 (cultivation) |
| 都市修真 (urban cultivation) | 都市异能 (urban supernatural powers) |
| 游戏电竞、电竞文 (gaming/esports fiction) | 电竞 (esports) |
| 直播、主播、直播带货 (livestreaming, streamers, live commerce) | 直播文 (livestream fiction) |
| 克系、克系悬疑 (Cthulhu-style fiction/mystery) | 克苏鲁 (Cthulhu fiction) |

## Hybrid-Genre Rules

- Join two genres with `+` (for example, `都市脑洞+规则怪谈`, high-concept urban fiction + rules-based horror). Separators `/`, `、`, and `与` are also supported.
- Combine no more than two genres.
- A 7:3 primary-to-secondary ratio is recommended: the main plot follows the primary genre's logic, while the secondary genre supplies hooks, rules, and satisfying payoffs.

Examples (literal supported genre inputs):

- `都市脑洞+规则怪谈`
- `修仙+系统流`
- `古言+宫斗宅斗`

## Genre Template Outputs

When a project is initialized, the selected genre template is automatically inserted into the reference-genre-template section (`参考题材模板`) of `settings/worldbuilding.md`.

The system also includes six fine-tuned genre configuration directories (`genres/`) with more detailed writing guidance for specific genres:

- `xuanhuan` (Chinese fantasy)
- `dog-blood-romance` (melodramatic romance)
- `period-drama` (period fiction)
- `realistic` (realism)
- `rules-mystery` (rules-based horror)
- `zhihu-short` (Zhihu short fiction)
