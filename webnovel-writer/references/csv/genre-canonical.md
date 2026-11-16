# Genre Canonical List

> Status: `draft` (2026-04-16)
> Source: Actual Fanqie Novel ranking categories (captured 2026-04).

## Design Goal

Establish a two-level genre system with aligned enumerations for every CSV `applicable_genres` column, routing-table `genre_route`, and decision-table `genre`. Genre identifiers, platform tags, aliases, filenames, and column names use English runtime values.

## Genre vs Trope: The Core Distinction

**Genre** answers "what kind of world hosts the story": urban, xuanhuan, xianxia, historical romance, etc.

**Trope** answers "what pattern tells the story": broken engagement, system, infinite scenarios, rebirth, live-in son-in-law, quick-transmigration missions, etc.

A trope can span genres: system stories can be xuanhuan or urban. Therefore pattern labels such as broken-engagement, system, infinite-scenario, live-in-son-in-law, rebirth, and instance-based stories are **not genres**; they belong in `tropes.csv`.

When a user requests a broken-engagement story, routing must do two things:
1. **Identify genre**: Broken-engagement stories most commonly fit traditional xuanhuan → canonical_genre = `xuanhuan`.
2. **Match trope**: Search `tropes.csv` for `broken engagement` entries.

The routing table `genre-routing.csv` may include trope names in `genre_aliases` for recognition, but `genre_route` itself accepts platform_tag values (Fanqie category names), not tropes.

---

## Two-Level Structure

```
Layer 1: canonical_genre  (15, defined here)
    ├── Used in every CSV table's `applicable_genres` column
    ├── Used in adjudication.csv `genre` (at least one decision row per canonical genre)
    └── Used for reference_search.py --genre filtering

Layer 2: platform_tag  (37 original Fanqie categories)
    ├── Used in genre-routing.csv `genre_route` (routing-entry granularity)
    ├── Used in genre-routing.csv `genre_aliases` (input recognition; tropes may improve recall)
    └── Each platform_tag maps to exactly one canonical_genre

Concepts outside the genre system (stored elsewhere):
    - Tropes/patterns (broken engagement, systems, infinite scenarios, rebirth...) → tropes.csv
    - Tone tags (wish fulfillment, deep plot, realism...) → adjudication.csv style priorities
    - Scene tags (combat, reasoning, daily life...) → scenes.csv
    - Format tags (short fiction, interactive fiction...) → not stored
```

**Rules**:
- `applicable_genres` accepts only canonical_genre values or `all`.
- `genre-routing.csv` `genre_route` uses platform_tag (Fanqie subcategory level).
- `adjudication.csv` `genre` uses canonical_genre (broad category).
- Arbitrary user input during init → `_route()` matches platform_tag → maps to canonical_genre.
- One canonical_genre may have multiple platform_tag values, but each platform_tag belongs to only one canonical_genre.
- Tropes may appear in routing `genre_aliases` for recognition, never as genre enum values.

---

## Layer 1: Canonical Genre Enumeration

### Male-Audience

| # | canonical_genre | Description | Included platform_tag values |
|---|----------------|------|-------------------|
| 1 | `urban` | Modern urban settings: daily life/cultivation/martial powers/live-in son-in-law/development/high concept | urban-slice-of-life、urbancultivation、urbanhigh-martial-power、warrior-son-in-law、urban-farming、urban-speculative |
| 2 | `xuanhuan` | Eastern fantasy: progression/combat/continental conquest | traditional-xuanhuan、speculative-xuanhuan |
| 3 | `xianxia` | Daoist cultivation: sects/tribulations/ascension | Easternxianxia |
| 4 | `fantasy` | Western fantasy: magic/races/epics | Westernfantasy |
| 5 | `sci-fi` | Science fiction/apocalypse/cyberpunk | sci-fiapocalypse |
| 6 | `historical` | History/ancient eras/alternate history/military/espionage | ancient-history、alternate-history、wartime-espionage |
| 7 | `mystery` | Mystery/detection/supernatural/thriller | speculative-mystery、paranormal-mystery |
| 8 | `game-lit` | Games/esports/sports | gaming-and-sports |

### Female-Audience

| # | canonical_genre | Description | Included platform_tag values |
|---|----------------|------|-------------------|
| 9 | `historical-romance` | Historical romance: court/household intrigue/martial world | classical stylesocial-realism、palace-household-intrigue、historical-romancehigh concept |
| 10 | `contemporary-romance` | Contemporary romance: sweet romance/wealthy families/workplace/entertainment | speculative-contemporary-romance、young-sweet-romance、Shining Stars、workplace-romance、billionaire-romance |
| 11 | `fantasy-romance` | Xuanhuan/xianxia + romance | cultivation-romance |
| 12 | `period-fiction` | Republican-era/period/modern historical romance | period-fiction、republican-era-romance |
| 13 | `farming` | Farming/business/infrastructure/slow living | farming |
| 14 | `quick-transmigration` | Quick transmigration/world travel/multi-world missions | quick-transmigration |

### Cross-Audience

| # | canonical_genre | Description | Included platform_tag values |
|---|----------------|------|-------------------|
| — | `sci-fi` | Shared across audiences | sci-fiapocalypse (same female-audience tag) |
| — | `mystery` | Shared across audiences | speculative-mystery (same female-audience tag)、women-centered-mystery |
| — | `game-lit` | Shared across audiences | gaming-and-sports (same female-audience tag) |
| 15 | `fanfiction` | Fan fiction/derivative works (low priority) | animefanfiction、male-orientedfanfiction、women-orientedfanfiction |

### Reserved Value

| Value | Meaning |
|----|------|
| `all` | Applies to every genre; no genre filtering |

---

## Layer 2: Complete Platform Tag → Canonical Mapping

### Male-Audience(19 platform_tag values)

| platform_tag | canonical_genre | Audience | Tone (distinguishes routes within a canonical genre) |
|-------------|----------------|------|-------------------------------------------|
| urban-slice-of-life | `urban` | Male | Light daily life, low conflict, warmth/comedy |
| urbancultivation | `urban` | Male | Modern setting + cultivation system, hidden cultivators |
| urbanhigh-martial-power | `urban` | Male | Modern setting + martial/supernatural powers, dense combat |
| warrior-son-in-law | `urban` | Male | Identity contrast, suppression then eruption, vindication main plot |
| urban-farming | `urban` | Male | Urban setting + business/accumulation/slow growth |
| urban-speculative | `urban` | Male | Urban setting + high-concept/imaginative premise |
| traditional-xuanhuan | `xuanhuan` | Male | Classic continents/progression/sects/conquest |
| speculative-xuanhuan | `xuanhuan` | Male | Xuanhuan + unconventional premise/subverted tropes |
| Easternxianxia | `xianxia` | Male | Daoist cultivation, sects/tribulations/ascension/causality |
| Westernfantasy | `fantasy` | Male | Magic/races/knights/epic narrative |
| sci-fiapocalypse | `sci-fi` | Male | Technology/apocalypse/survival/interstellar |
| ancient-history | `historical` | Male | Conventional history/fictional dynasties/power struggles/development |
| alternate-history | `historical` | Male | Historical setting + transmigration/systems/high concept |
| wartime-espionage | `historical` | Male | Modern-era war/espionage/military operations |
| speculative-mystery | `mystery` | Male | Mystery + imaginative premise/rules |
| paranormal-mystery | `mystery` | Male | Supernatural/ghosts/folk horror |
| gaming-and-sports | `game-lit` | Male | Esports/game worlds/sports competition |
| animefanfiction | `fanfiction` | Male | Anime/manga IP derivative fiction |
| male-orientedfanfiction | `fanfiction` | Male | Other IP derivative fiction |

### Female-Audience(18 platform_tag values)

| platform_tag | canonical_genre | Audience | Tone |
|-------------|----------------|------|---------|
| classical stylesocial-realism | `historical-romance` | Female | Ancient daily life/families/social relationships |
| palace-household-intrigue | `historical-romance` | Female | Court/household intrigue and female power struggles |
| historical-romancehigh concept | `historical-romance` | Female | Ancient setting + transmigration/rebirth/high concept |
| speculative-contemporary-romance | `contemporary-romance` | Female | Contemporary romance + imaginative premise |
| young-sweet-romance | `contemporary-romance` | Female | School/youth/sweet romance/low angst |
| Shining Stars | `contemporary-romance` | Female | Entertainment/celebrities/idols |
| workplace-romance | `contemporary-romance` | Female | Workplace + marriage/romance/contracts/urban life |
| billionaire-romance | `contemporary-romance` | Female | Wealthy families/conglomerates/class gaps |
| cultivation-romance | `fantasy-romance` | Female | Xuanhuan/xianxia world + romance main plot |
| period-fiction | `period-fiction` | Female | 1950s-1990s China/modern-era daily life |
| republican-era-romance | `period-fiction` | Female | Republican-era setting + romance |
| farming | `farming` | Female | Rural life/business/infrastructure/slow accumulation |
| quick-transmigration | `quick-transmigration` | Female | Travel across worlds/missions/winning over targets |
| sci-fiapocalypse | `sci-fi` | Female | Science fiction/apocalypse + survival/romance |
| speculative-mystery | `mystery` | Female | Mystery + imaginative premise |
| women-centered-mystery | `mystery` | Female | Female-perspective mystery/detection |
| gaming-and-sports | `game-lit` | Female | Esports/games/sports + romance |
| women-orientedfanfiction | `fanfiction` | Female | Female-audience IP derivative fiction |

---

## Common User Aliases → Genre Mapping

> Use this table to expand `genre-routing.csv` `genre_aliases` and improve routing recall.
> Trope names (broken engagement, systems, infinite scenarios...) may identify user intent as aliases, but ultimately map to platform_tag rather than the trope itself.

### Genre-Only Aliases

| Possible input | Maps to platform_tag | canonical_genre |
|-------------|-------------------|----------------|
| cultivation、cultivation、Daoist cultivation | Easternxianxia / urbancultivation | xianxia / urban |
| apocalypse、zombies、wasteland | sci-fiapocalypse | sci-fi |
| sweet romance、pure sweetness、extremely sweet | young-sweet-romance | contemporary-romance |
| palace intrigue、household intrigue、harem intrigue | palace-household-intrigue | historical-romance |
| CEO romance、domineering CEO | billionaire-romance | contemporary-romance |
| entertainment-industry、celebrity | Shining Stars | contemporary-romance |
| infrastructure building、management、farming | farming | farming |
| Republican-era China | republican-era-romance | period-fiction |
| esports、online gaming | gaming-and-sports | game-lit |
| fan fiction、transformative works | animefanfiction / women-orientedfanfiction | fanfiction |
| cosmic-horror、occult mystery | paranormal-mystery | mystery |
| espionage、resistance to Japanese invasion | wartime-espionage | historical |
| cyberpunk、interstellar | sci-fiapocalypse | sci-fi |
| superpowers | urbanhigh-martial-power | urban |

### Trope Aliases (Routing Recognition; Tropes Belong in `tropes.csv`)

| Possible input | Maps to platform_tag | canonical_genre | also triggerstropesretrieval |
|-------------|-------------------|----------------|-------------------|
| broken-engagement fiction、Never underestimate a poor young man、three-year agreement | traditional-xuanhuan | xuanhuan | broken engagement、underdog comeback |
| marrying-into-the-family fiction、live-in son-in-law | warrior-son-in-law | urban | married-in son-in-law、identityreversal |
| system-fiction、status-panel fiction、system fiction | traditional-xuanhuan / urbancultivation | xuanhuan / urban | system activation、system upgrade |
| infinite-scenarios、scenario-fiction | speculative-mystery | mystery | scenario、rulechallenge |
| rules-horror、rules-horror-zoo | speculative-mystery | mystery | ruleinterpretation、penalty for violations |
| rebirth、rebirthrevenge | urban-speculative / historical-romancehigh concept | urban / historical-romance | rebirth、dominance through information advantage |
| transmigration、entering a fictional book | alternate-history / historical-romancehigh concept | historical / historical-romance | adapting after transmigration、dominance through knowledge |

**Note**: Some aliases (such as `system-fiction`, `rebirth`, `transmigration`) map to multiple platform_tag values. Routing must jointly use `keywords` + `intent_synonyms` + `applicable_genres`, not aliases alone.

---

## Alignment with Existing CSV Tables

### 1. `applicable_genres` Column (All 9 Tables)

- Accept only the 15 canonical_genre values above or `all`.
- Separate multiple values with `|`: `urban|xuanhuan|xianxia`.
- **Migration plan**: Map existing non-enumerated values individually to canonical genres; see the [migration mapping](#migration-mapping-for-existing-non-enumerated-values).

### 2. `genre` in `adjudication.csv`

- Use canonical_genre only.
- At least one decision-rule row per canonical_genre.
- Broad-category granularity; do not split rows by platform_tag.

### 3. `genre_route` in `genre-routing.csv`

- Use platform_tag (subcategory level).
- One routing-rule row per platform_tag.
- Put all aliases for that platform_tag in `genre_aliases`.
- Add `canonical_genre` to explicitly identify the row's canonical genre.

### 4. `reference_search.py --genre` Argument

- Accept canonical_genre or platform_tag.
- Map platform_tag input to canonical_genre before filtering.
- `_genre_matches()` matches canonical_genre against CSV `applicable_genres`.

---

## Migration Mapping for Existing Non-Enumerated Values

> The following values exist in CSV `applicable_genres` columns but are outside the canonical enumeration and require migration.

| Existing value | → canonical_genre | Description |
|--------|------------------|------|
| Easternxianxia | `xianxia` | platform_tag; normalize to canonical |
| Westernfantasy | `fantasy` | Same as above |
| sci-fiapocalypse | `sci-fi` | Same as above |
| urban-slice-of-life | `urban` | Same as above |
| urbancultivation | `urban` | Same as above |
| urbanhigh-martial-power | `urban` | Same as above |
| ancient-history | `historical` | Same as above |
| espionage | `historical` | Map to history |
| criminal investigation | `mystery` | Map to mystery |
| thriller | `mystery` | Map to mystery |
| deduction | `mystery` | Map to mystery |
| rules-horror | `mystery` | Map to mystery |
| apocalypse | `sci-fi` | Map to science fiction |
| cyberpunk | `sci-fi` | Map to science fiction |
| military | `historical` | Map to history |
| wuxia | `historical` | Fanqie no longer has a separate wuxia category; map to history |
| political intrigue | `historical-romance` / `historical` | By audience/category: historical-romance intrigue → historical-romance; historical intrigue → historical |
| light novel | `fanfiction` | Fanqie groups this under derivative fiction |
| online gaming | `game-lit` | Map to games |
| esports | `game-lit` | Map to games |
| competition | `game-lit` | Map to games |
| sports | `game-lit` | Fanqie combines this under `gaming-and-sports` |
| system fiction | Remove | Trope, not genre. Set `applicable_genres` to the actual setting genre (`xuanhuan`/`urban`); put the trope in `tropes.csv`. |
| infinite-scenarios | Remove | Trope. Set genre to `mystery`; put the trope in `tropes.csv`. |
| melodrama | Remove | Tone tag, not genre |
| payoff-driven fiction | Remove | Tone tag |
| deep plot | Remove | Tone tag |
| realistic | Remove | Tone tag |
| ensemble | Remove | Narrative-structure tag |
| epic | Remove | Tone tag |
| action | Remove | Scene tag |
| psychological | Remove | Scene tag |
| war | Remove | Scene tag |
| disaster | Remove | Scene tag |
| long-form | Remove | Format tag |
| zhihu-short-fiction | Remove | Format tag |
| commercial rivalry / business | `urban` / `contemporary-romance` | By audience/category |
| school / youth | `contemporary-romance` | Map to contemporary romance |
| entertainment-industry | `contemporary-romance` | Fanqie `Shining Stars` |
| workplace | `contemporary-romance` | Fanqie `workplace-romance` |
| adventure / exploration | `fantasy` / `xuanhuan` | Decide by world setting |
| fan fiction | `fanfiction` | |
| interactive fiction / mini-app-short-style / zhihu-short-style | Remove | Format tag, outside the genre system |
| high-martial-power | `urban` | Fanqie `urbanhigh-martial-power` |
| antique-themed fiction | `mystery` / `historical` | Decide by emphasis |

### Handling "Remove"

"Remove" applies to the value, not the entry: replace its `applicable_genres` with the actual canonical_genre or `all`.

For example, a trope marked `applicable_genres=melodrama` should become `applicable_genres=contemporary-romance|historical-romance` if limited to romance, or `all` if applicable across genres.

---

## Canonical Enumeration (Quick Reference)

```
urban  xuanhuan  xianxia  fantasy  sci-fi
historical  mystery  game-lit  historical-romance  contemporary-romance
fantasy-romance  period-fiction  farming  quick-transmigration  fanfiction
all (reserved value)
```

15 canonical_genre values + 1 reserved value.
