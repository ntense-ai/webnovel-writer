# Reference Gap Register

> Baseline and confirmed gaps for this skills/references restructuring round.
> Source: `docs/archive/superpowers/specs/2026-04-09-skills-restructure-and-reference-gaps.md`

---

## I. Skill Baseline and Rewrite Direction

| Skill | Priority | Current problem | Target role | Existing references | Missing references |
| --- | --- | --- | --- | --- | --- |
| webnovel-write | P0 | 326 lines; heavy main workflow; flat reference listing | Main orchestrator: workflow + gates + deliverables + recovery | anti-ai-guide, polish-guide, style-adapter, style-variants, writing/* (6 files), reading-power-taxonomy, genre-profiles, core-constraints | Naming rules CSV, scene writing CSV, writing techniques CSV |
| webnovel-review | P0 | 135 lines; unclear blocking adjudication chain | Independent review entry: reviewer call → report → blocking handling | review-schema, core-constraints | blocking-override-guidelines |
| webnovel-plan | P0 | 272 lines; genre/conflict/pacing rules mixed into main text | Planning entry: volume outline → timeline → chapter outlines | No independent references | plot-signal-vs-spoiler, scene writing CSV (volume structure) |
| webnovel-init | P1 | 434 lines; nearly a mini-spec; collection/strategy/constraints mixed | Initialization interview and generation workflow | genre-profiles | Naming rules CSV |
| webnovel-query | P1 | 192 lines; manual-like, too many low-level commands exposed | Query/analysis skill | Inline | No urgent need |
| webnovel-dashboard | P2 | 74 lines; too light, lacks validation and recovery | Tool-launch skill | None | No urgent need |
| webnovel-learn | P2 | 45 lines; too light, lacks boundaries and recovery | Lightweight recording skill | None | No urgent need |

## II. Confirmed Gaps

### New Markdown References

| Reference | Main skill | Step/trigger | Gap type | Why not inline |
| --- | --- | --- | --- | --- |
| `references/review/blocking-override-guidelines.md` | webnovel-review | Step 6 / blocking issue needs user decision | Defect compensation | Override eligibility needs independent positive/negative examples |
| `references/outlining/plot-signal-vs-spoiler.md` | webnovel-plan | Chapter-outline breakdown / always | Reminder + supplementary knowledge | Signal/spoiler criteria need more than one line in the skill |
| `references/shared/naming-and-voice-gaps.md` | webnovel-write (primary), init/plan (secondary) | Step 2 / multi-character dialogue, new names | Defect compensation | Homogeneous names, converging voices, and genre vocabulary drift are recurring error classes |

### New CSV Knowledge Bases

| CSV file | Main source | Skills served | Description |
| --- | --- | --- | --- |
| `references/csv/命名规则.csv` | New | init, plan, write | Naming rules and positive/negative examples for characters/places/factions/techniques/items/books |
| `references/csv/场景写法.csv` | Existing writing/*.md + new material | write, plan | Combat/dialogue/emotion/plot/volume-structure techniques and examples |
| `references/csv/写作技法.csv` | Existing writing/*.md | write | Dialogue voice, emotional description, scene description, pacing techniques |

### Existing Markdown to Migrate to CSV

| Existing Markdown | Target CSV | Post-migration handling |
| --- | --- | --- |
| `writing/combat-scenes.md` (229 lines) | 场景写法.csv (`场景类型=战斗`) | Delete or keep a stub pointing to CSV |
| `writing/dialogue-writing.md` (231 lines) | 写作技法.csv (`分类=对话`) | Same |
| `writing/emotion-psychology.md` (265 lines) | 写作技法.csv (`分类=情感`) | Same |
| `writing/scene-description.md` (263 lines) | 写作技法.csv (`分类=场景`) | Same |
| `writing/desire-description.md` (311 lines) | 写作技法.csv (`分类=情感`) | Conservatively retain original; CSV does not yet cover desire-description detail |
| `writing/genre-hook-payoff-library.md` (85 lines) | 场景写法.csv (`场景类型=钩子/兑现`) | Conservatively retain original; CSV covers only some hook/payoff entries |

### Deferred (Revisit When Triggered)

| Original proposal | Reason to defer | Reinstatement condition |
| --- | --- | --- |
| init/title-patterns-and-anti-patterns.md | A few rows in 命名规则.csv suffice | Upgrade if CSV coverage is inadequate and titles become heavily formulaic |
| init/protagonist-flaw-patterns.md | Covered by Claude's general abilities | Add CSV entries if webnovel flaw design becomes vague |
| query/entity-alias-resolution.md | Alias resolution is code logic (entity_linker.py) | Add if semantic ambiguity becomes frequent |
| query/foreshadowing-urgency-rules.md | context-agent already ranks urgency | Add if output explanations are inconsistent |
| learn/pattern-taxonomy.md | Classification rules can be inline | Add CSV if classification quality remains unstable |

---

## III. Reference Completion Status, 2026-04-16

| Item | Status | Description |
|------|------|------|
| `references/review/blocking-override-guidelines.md` | Complete | Review blocking-decision reference in place |
| `references/outlining/plot-signal-vs-spoiler.md` | Complete | Plan chapter-breakdown reference in place |
| `references/shared/naming-and-voice-gaps.md` | Complete | Naming/voice defect-compensation reference in place |
| `references/README.md` | Complete | Top-level reference index added |
| `references/csv/genre-canonical.md` | Complete | 15 canonical genres + platform_tag mapping in place |
| `reference_search.py` canonical genre parsing | Complete | Normalizes canonical, platform_tag, and legacy values |
| `CSV_CONFIG` structural metadata | Complete | Added `prefix`, `required_cols`, `contract_inject` |
| `validate_csv.py` | Complete | Validates headers, IDs, prefixes, required columns, separators, genres, routing/decision coverage |
| `题材与调性推理.csv` | Expanded | 8 → 26 rows, covering 15 canonical genres |
| `裁决规则.csv` | Expanded | 7 → 17 rows, covering 15 canonical genres |
| CSV `适用题材` canonical migration | Complete | `validate_csv.py` currently reports 0 errors / 0 warnings |

## IV. Remaining Knowledge-Layer Gaps

| Gap | Priority | Description |
|------|--------|------|
| Female-audience naming conventions | P1 | Expand historical/contemporary romance, sweet romance, and entertainment-industry distinctions in `命名规则.csv` |
| Core romance scenes | P1 | Expand attraction, misunderstandings, reunions, breakups, and winning-back-a-partner scenes in `场景写法.csv` |
| Mystery reasoning techniques | P1 | Expand clues, fair misdirection, and truth reveals in `写作技法.csv` and `桥段套路.csv` |
| Shared Markdown migration review | P2 | Itemizable content in `cool-points-guide.md` and `naming-and-voice-gaps.md` awaits manual entry-by-entry migration |
