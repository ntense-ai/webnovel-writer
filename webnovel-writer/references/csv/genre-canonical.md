# Genre Canonical List

> Status: `draft` (2026-04-16)
> Source: Actual Fanqie Novel ranking categories (captured 2026-04).

## Design Goal

Establish a two-level genre system with aligned enumerations for every CSV `适用题材` column, routing-table `题材/流派`, and decision-table `题材`. Chinese genre names, platform tags, aliases, filenames, and column names below are literal values used by the unchanged runtime and CSV data.

## Genre vs Trope: The Core Distinction

**Genre** answers "what kind of world hosts the story": urban, xuanhuan, xianxia, historical romance, etc.

**Trope** answers "what pattern tells the story": broken engagement, system, infinite scenarios, rebirth, live-in son-in-law, quick-transmigration missions, etc.

A trope can span genres: system stories can be xuanhuan or urban. Therefore pattern labels such as broken-engagement, system, infinite-scenario, live-in-son-in-law, rebirth, and instance-based stories are **not genres**; they belong in `桥段套路.csv`.

When a user requests a broken-engagement story, routing must do two things:
1. **Identify genre**: Broken-engagement stories most commonly fit traditional xuanhuan → canonical_genre = `玄幻`.
2. **Match trope**: Search `桥段套路.csv` for `退婚` entries.

The routing table `题材与调性推理.csv` may include trope names in `题材别名` for recognition, but `题材/流派` itself accepts platform_tag values (Fanqie category names), not tropes.

---

## Two-Level Structure

```
Layer 1: canonical_genre  (15, defined here)
    ├── Used in every CSV table's `适用题材` column
    ├── Used in 裁决规则.csv `题材` (at least one decision row per canonical genre)
    └── Used for reference_search.py --genre filtering

Layer 2: platform_tag  (37 original Fanqie categories)
    ├── Used in 题材与调性推理.csv `题材/流派` (routing-entry granularity)
    ├── Used in 题材与调性推理.csv `题材别名` (input recognition; tropes may improve recall)
    └── Each platform_tag maps to exactly one canonical_genre

Concepts outside the genre system (stored elsewhere):
    - Tropes/patterns (broken engagement, systems, infinite scenarios, rebirth...) → 桥段套路.csv
    - Tone tags (wish fulfillment, deep plot, realism...) → 裁决规则.csv style priorities
    - Scene tags (combat, reasoning, daily life...) → 场景写法.csv
    - Format tags (short fiction, interactive fiction...) → not stored
```

**Rules**:
- `适用题材` accepts only canonical_genre values or `全部`.
- `题材与调性推理.csv` `题材/流派` uses platform_tag (Fanqie subcategory level).
- `裁决规则.csv` `题材` uses canonical_genre (broad category).
- Arbitrary user input during init → `_route()` matches platform_tag → maps to canonical_genre.
- One canonical_genre may have multiple platform_tag values, but each platform_tag belongs to only one canonical_genre.
- Tropes may appear in routing `题材别名` for recognition, never as genre enum values.

---

## Layer 1: Canonical Genre Enumeration

### Male-Audience

| # | canonical_genre | Description | Included platform_tag values |
|---|----------------|------|-------------------|
| 1 | `都市` | Modern urban settings: daily life/cultivation/martial powers/live-in son-in-law/development/high concept | 都市日常、都市修真、都市高武、战神赘婿、都市种田、都市脑洞 |
| 2 | `玄幻` | Eastern fantasy: progression/combat/continental conquest | 传统玄幻、玄幻脑洞 |
| 3 | `仙侠` | Daoist cultivation: sects/tribulations/ascension | 东方仙侠 |
| 4 | `奇幻` | Western fantasy: magic/races/epics | 西方奇幻 |
| 5 | `科幻` | Science fiction/apocalypse/cyberpunk | 科幻末世 |
| 6 | `历史` | History/ancient eras/alternate history/military/espionage | 历史古代、历史脑洞、抗战谍战 |
| 7 | `悬疑` | Mystery/detection/supernatural/thriller | 悬疑脑洞、悬疑灵异 |
| 8 | `游戏` | Games/esports/sports | 游戏体育 |

### Female-Audience

| # | canonical_genre | Description | Included platform_tag values |
|---|----------------|------|-------------------|
| 9 | `古言` | Historical romance: court/household intrigue/martial world | 古风世情、宫斗宅斗、古言脑洞 |
| 10 | `现言` | Contemporary romance: sweet romance/wealthy families/workplace/entertainment | 现言脑洞、青春甜宠、星光璀璨、职场婚恋、豪门总裁 |
| 11 | `幻言` | Xuanhuan/xianxia + romance | 玄幻言情 |
| 12 | `年代` | Republican-era/period/modern historical romance | 年代、民国言情 |
| 13 | `种田` | Farming/business/infrastructure/slow living | 种田 |
| 14 | `快穿` | Quick transmigration/world travel/multi-world missions | 快穿 |

### Cross-Audience

| # | canonical_genre | Description | Included platform_tag values |
|---|----------------|------|-------------------|
| — | `科幻` | Shared across audiences | 科幻末世 (same female-audience tag) |
| — | `悬疑` | Shared across audiences | 悬疑脑洞 (same female-audience tag)、女频悬疑 |
| — | `游戏` | Shared across audiences | 游戏体育 (same female-audience tag) |
| 15 | `衍生` | Fan fiction/derivative works (low priority) | 动漫衍生、男频衍生、女频衍生 |

### Reserved Value

| Value | Meaning |
|----|------|
| `全部` | Applies to every genre; no genre filtering |

---

## Layer 2: Complete Platform Tag → Canonical Mapping

### Male-Audience(19 platform_tag values)

| platform_tag | canonical_genre | Audience | Tone (distinguishes routes within a canonical genre) |
|-------------|----------------|------|-------------------------------------------|
| 都市日常 | `都市` | Male | Light daily life, low conflict, warmth/comedy |
| 都市修真 | `都市` | Male | Modern setting + cultivation system, hidden cultivators |
| 都市高武 | `都市` | Male | Modern setting + martial/supernatural powers, dense combat |
| 战神赘婿 | `都市` | Male | Identity contrast, suppression then eruption, vindication main plot |
| 都市种田 | `都市` | Male | Urban setting + business/accumulation/slow growth |
| 都市脑洞 | `都市` | Male | Urban setting + high-concept/imaginative premise |
| 传统玄幻 | `玄幻` | Male | Classic continents/progression/sects/conquest |
| 玄幻脑洞 | `玄幻` | Male | Xuanhuan + unconventional premise/subverted tropes |
| 东方仙侠 | `仙侠` | Male | Daoist cultivation, sects/tribulations/ascension/causality |
| 西方奇幻 | `奇幻` | Male | Magic/races/knights/epic narrative |
| 科幻末世 | `科幻` | Male | Technology/apocalypse/survival/interstellar |
| 历史古代 | `历史` | Male | Conventional history/fictional dynasties/power struggles/development |
| 历史脑洞 | `历史` | Male | Historical setting + transmigration/systems/high concept |
| 抗战谍战 | `历史` | Male | Modern-era war/espionage/military operations |
| 悬疑脑洞 | `悬疑` | Male | Mystery + imaginative premise/rules |
| 悬疑灵异 | `悬疑` | Male | Supernatural/ghosts/folk horror |
| 游戏体育 | `游戏` | Male | Esports/game worlds/sports competition |
| 动漫衍生 | `衍生` | Male | Anime/manga IP derivative fiction |
| 男频衍生 | `衍生` | Male | Other IP derivative fiction |

### Female-Audience(18 platform_tag values)

| platform_tag | canonical_genre | Audience | Tone |
|-------------|----------------|------|---------|
| 古风世情 | `古言` | Female | Ancient daily life/families/social relationships |
| 宫斗宅斗 | `古言` | Female | Court/household intrigue and female power struggles |
| 古言脑洞 | `古言` | Female | Ancient setting + transmigration/rebirth/high concept |
| 现言脑洞 | `现言` | Female | Contemporary romance + imaginative premise |
| 青春甜宠 | `现言` | Female | School/youth/sweet romance/low angst |
| 星光璀璨 | `现言` | Female | Entertainment/celebrities/idols |
| 职场婚恋 | `现言` | Female | Workplace + marriage/romance/contracts/urban life |
| 豪门总裁 | `现言` | Female | Wealthy families/conglomerates/class gaps |
| 玄幻言情 | `幻言` | Female | Xuanhuan/xianxia world + romance main plot |
| 年代 | `年代` | Female | 1950s-1990s China/modern-era daily life |
| 民国言情 | `年代` | Female | Republican-era setting + romance |
| 种田 | `种田` | Female | Rural life/business/infrastructure/slow accumulation |
| 快穿 | `快穿` | Female | Travel across worlds/missions/winning over targets |
| 科幻末世 | `科幻` | Female | Science fiction/apocalypse + survival/romance |
| 悬疑脑洞 | `悬疑` | Female | Mystery + imaginative premise |
| 女频悬疑 | `悬疑` | Female | Female-perspective mystery/detection |
| 游戏体育 | `游戏` | Female | Esports/games/sports + romance |
| 女频衍生 | `衍生` | Female | Female-audience IP derivative fiction |

---

## Common User Aliases → Genre Mapping

> Use this table to expand `题材与调性推理.csv` `题材别名` and improve routing recall.
> Trope names (broken engagement, systems, infinite scenarios...) may identify user intent as aliases, but ultimately map to platform_tag rather than the trope itself.

### Genre-Only Aliases

| Possible input | Maps to platform_tag | canonical_genre |
|-------------|-------------------|----------------|
| 修仙、修真、修道 | 东方仙侠 / 都市修真 | 仙侠 / 都市 |
| 末世、丧尸、废土 | 科幻末世 | 科幻 |
| 甜宠、纯甜、齁甜 | 青春甜宠 | 现言 |
| 宫斗、宅斗、后宫争斗 | 宫斗宅斗 | 古言 |
| 总裁文、霸总 | 豪门总裁 | 现言 |
| 娱乐圈、明星 | 星光璀璨 | 现言 |
| 基建、经营、种地 | 种田 | 种田 |
| 民国 | 民国言情 | 年代 |
| 电竞、网游 | 游戏体育 | 游戏 |
| 同人、二创 | 动漫衍生 / 女频衍生 | 衍生 |
| 克苏鲁、诡秘 | 悬疑灵异 | 悬疑 |
| 谍战、抗日 | 抗战谍战 | 历史 |
| 赛博朋克、星际 | 科幻末世 | 科幻 |
| 异能 | 都市高武 | 都市 |

### Trope Aliases (Routing Recognition; Tropes Belong in `桥段套路.csv`)

| Possible input | Maps to platform_tag | canonical_genre | 同时触发桥段套路检索 |
|-------------|-------------------|----------------|-------------------|
| 退婚流、莫欺少年穷、三年之约 | 传统玄幻 | 玄幻 | 退婚、废材逆袭 |
| 赘婿流、上门女婿 | 战神赘婿 | 都市 | 赘婿、身份反转 |
| 系统流、面板流、系统文 | 传统玄幻 / 都市修真 | 玄幻 / 都市 | 系统激活、系统升级 |
| 无限流、副本流 | 悬疑脑洞 | 悬疑 | 副本、规则挑战 |
| 规则怪谈、规则动物园 | 悬疑脑洞 | 悬疑 | 规则解读、违规惩罚 |
| 重生、重生复仇 | 都市脑洞 / 古言脑洞 | 都市 / 古言 | 重生、信息差碾压 |
| 穿越、穿书 | 历史脑洞 / 古言脑洞 | 历史 / 古言 | 穿越适应、知识碾压 |

**Note**: Some aliases (such as `系统流`, `重生`, `穿越`) map to multiple platform_tag values. Routing must jointly use `关键词` + `意图与同义词` + `适用题材`, not aliases alone.

---

## Alignment with Existing CSV Tables

### 1. `适用题材` Column (All 9 Tables)

- Accept only the 15 canonical_genre values above or `全部`.
- Separate multiple values with `|`: `都市|玄幻|仙侠`.
- **Migration plan**: Map existing non-enumerated values individually to canonical genres; see the [migration mapping](#migration-mapping-for-existing-non-enumerated-values).

### 2. `题材` in `裁决规则.csv`

- Use canonical_genre only.
- At least one decision-rule row per canonical_genre.
- Broad-category granularity; do not split rows by platform_tag.

### 3. `题材/流派` in `题材与调性推理.csv`

- Use platform_tag (subcategory level).
- One routing-rule row per platform_tag.
- Put all aliases for that platform_tag in `题材别名`.
- Add `canonical_genre` to explicitly identify the row's canonical genre.

### 4. `reference_search.py --genre` Argument

- Accept canonical_genre or platform_tag.
- Map platform_tag input to canonical_genre before filtering.
- `_genre_matches()` matches canonical_genre against CSV `适用题材`.

---

## Migration Mapping for Existing Non-Enumerated Values

> The following values exist in CSV `适用题材` columns but are outside the canonical enumeration and require migration.

| Existing value | → canonical_genre | Description |
|--------|------------------|------|
| 东方仙侠 | `仙侠` | platform_tag; normalize to canonical |
| 西方奇幻 | `奇幻` | Same as above |
| 科幻末世 | `科幻` | Same as above |
| 都市日常 | `都市` | Same as above |
| 都市修真 | `都市` | Same as above |
| 都市高武 | `都市` | Same as above |
| 历史古代 | `历史` | Same as above |
| 谍战 | `历史` | Map to history |
| 刑侦 | `悬疑` | Map to mystery |
| 惊悚 | `悬疑` | Map to mystery |
| 推理 | `悬疑` | Map to mystery |
| 规则怪谈 | `悬疑` | Map to mystery |
| 末世 | `科幻` | Map to science fiction |
| 赛博朋克 | `科幻` | Map to science fiction |
| 军事 | `历史` | Map to history |
| 武侠 | `历史` | Fanqie no longer has a separate wuxia category; map to history |
| 权谋 | `古言` / `历史` | By audience/category: historical-romance intrigue → 古言; historical intrigue → 历史 |
| 轻小说 | `衍生` | Fanqie groups this under derivative fiction |
| 网游 | `游戏` | Map to games |
| 电竞 | `游戏` | Map to games |
| 竞技 | `游戏` | Map to games |
| 体育 | `游戏` | Fanqie combines this under `游戏体育` |
| 系统文 | Remove | Trope, not genre. Set `适用题材` to the actual setting genre (`玄幻`/`都市`); put the trope in `桥段套路.csv`. |
| 无限流 | Remove | Trope. Set genre to `悬疑`; put the trope in `桥段套路.csv`. |
| 狗血 | Remove | Tone tag, not genre |
| 爽文 | Remove | Tone tag |
| 深度剧情 | Remove | Tone tag |
| 现实向 | Remove | Tone tag |
| 群像 | Remove | Narrative-structure tag |
| 史诗 | Remove | Tone tag |
| 动作 | Remove | Scene tag |
| 心理 | Remove | Scene tag |
| 战争 | Remove | Scene tag |
| 灾难 | Remove | Scene tag |
| 长篇 | Remove | Format tag |
| 知乎短篇 | Remove | Format tag |
| 商战 / 商业 | `都市` / `现言` | By audience/category |
| 校园 / 青春 | `现言` | Map to contemporary romance |
| 娱乐圈 | `现言` | Fanqie `星光璀璨` |
| 职场 | `现言` | Fanqie `职场婚恋` |
| 冒险 / 探险 | `奇幻` / `玄幻` | Decide by world setting |
| 同人 | `衍生` | |
| 互动小说 / 小程序短篇风 / 知乎短篇风 | Remove | Format tag, outside the genre system |
| 高武 | `都市` | Fanqie `都市高武` |
| 古董文 | `悬疑` / `历史` | Decide by emphasis |

### Handling "Remove"

"Remove" applies to the value, not the entry: replace its `适用题材` with the actual canonical_genre or `全部`.

For example, a trope marked `适用题材=狗血` should become `适用题材=现言|古言` if limited to romance, or `全部` if applicable across genres.

---

## Canonical Enumeration (Quick Reference)

```
都市  玄幻  仙侠  奇幻  科幻
历史  悬疑  游戏  古言  现言
幻言  年代  种田  快穿  衍生
全部 (reserved value)
```

15 canonical_genre values + 1 reserved value.
