# Reference Loading Map

> Actual reference-consumption relationships in the current `skills/*/SKILL.md` files.
> Scope: Markdown/templates explicitly required for direct reading, and CSV explicitly consumed through `reference_search.py` or `story-system`.
> Ordinary project-data reads are excluded, such as `.webnovel/state.json`, `settings/*.md`, `outlines/*.md`, and `index.db`.

---

## Directly Read Markdown/Templates

> Reading modes: **Section** = first `Grep` for `^#{1,4} ` to locate actual heading lines, then `Read` with offset/limit (seven target large files; anchors in the last column). **Full** = read a short file entirely. Use actual headings in the file, not planning shorthand. Target files and anchor sources: `docs/architecture/phase0-slimming-and-read-audit-2026-06-06.md` §A.1.

| Skill | Stage | Trigger | Reference | Mode | Section anchor (match the actual heading) |
|-------|------|------|-----------|---------|-----------|
| webnovel-init | Step 1 | always | `skills/webnovel-init/references/system-data-flow.md` | Full | — |
| webnovel-init | Step 1 | always | `skills/webnovel-init/references/genre-tropes.md` | Section | Current genre section |
| webnovel-init | Selling-point/genre collection | always | `references/genre-profiles.md` | Section | One `### 2.x` section for the current genre; add `## I. Profile Fields` as needed |
| webnovel-init | Step 2 | User characters are flat | `skills/webnovel-init/references/worldbuilding/character-design.md` | Full | — |
| webnovel-init | Step 4 | always | `skills/webnovel-init/references/worldbuilding/faction-systems.md` | Section | Sections needed for the current world |
| webnovel-init | Step 4 | Cultivation/xuanhuan/high-powered martial arts/supernatural abilities | `skills/webnovel-init/references/worldbuilding/power-systems.md` | Section | Relevant power-system section |
| webnovel-init | Step 4 | always | `skills/webnovel-init/references/worldbuilding/world-rules.md` | Full | — |
| webnovel-init | Step 5 | always | `skills/webnovel-init/references/creativity/creativity-constraints.md` | Section | For collection: locate Idea Package schema / Hard Constraints / Scoring System sections; for score presentation: the five-dimensional scoring subsection (8.1) |
| webnovel-init | Step 5 | always | `skills/webnovel-init/references/creativity/selling-points.md` | Section | Section 9 selling-point positioning template; optionally section 1.3 golden formula / section 7 practical checklist |
| webnovel-init | Step 5 | Hybrid genre | `skills/webnovel-init/references/creativity/creative-combination.md` | Section | Section for the current combination axis |
| webnovel-init | Step 5 | Creative block | `skills/webnovel-init/references/creativity/inspiration-collection.md` | Section | Required collection section |
| webnovel-init | Step 5 | Genre mapping match | `skills/webnovel-init/references/creativity/anti-trope-*.md` | Section | Relevant anti-trope entry |
| webnovel-init | Step 6 | always | `skills/webnovel-init/references/worldbuilding/setting-consistency.md` | Section | Consistency-validation section |
| webnovel-plan | Step 4 | always | `templates/output/大纲-卷节拍表.md` | Full | — |
| webnovel-plan | Step 5 | always | `templates/output/大纲-卷时间线.md` | Full | — |
| webnovel-plan | Step 6 | always | `references/genre-profiles.md` | Section | One `### 2.x` section for the current genre; add `## I. Profile Fields` as needed |
| webnovel-plan | Step 6 | always | `references/shared/strand-weave-pattern.md` | Full | — |
| webnovel-plan | Chapter-outline breakdown | always | `references/outlining/plot-signal-vs-spoiler.md` | Full | — |
| webnovel-plan | Step 6 | Payoff design needed | `references/shared/cool-points-guide.md` | Section | Required payoff dimension; genre adaptation: `## IX. Genre Adaptation` |
| webnovel-plan | Step 6/7 | Conflict design needed | `skills/webnovel-plan/references/outlining/conflict-design.md` | Section | Relevant conflict-type section |
| webnovel-plan | Step 7 | Reader-retention analysis needed | `references/reading-power-taxonomy.md` | Section | As needed: `## I. Hook Types` / `## II. Payoff Patterns` / `## III. Instant Gratification / Micro-Payoffs` |
| webnovel-plan | Step 7 | Chapter-outline refinement needed | `skills/webnovel-plan/references/outlining/chapter-planning.md` | Section | Section 10 structured-node specification (CBN/CPNs/CEN); add section 7 chapter-planning template as needed |
| webnovel-plan | Step 6/7 | Genre-specific pacing | `skills/webnovel-plan/references/outlining/genre-volume-pacing.md` | Full | — |
| webnovel-write | Step 4 | always | `skills/webnovel-write/references/polish-guide.md` | Section | Main path: section 2 execution order; final Anti-AI check: section 2A detection details / Phase 1 seven-layer Anti-AI specification supplement |
| webnovel-write | Step 4 | always | `skills/webnovel-write/references/writing/typesetting.md` | Full | — |
| webnovel-write | Step 4 | always | `skills/webnovel-write/references/style-adapter.md` | Full | — |
| webnovel-review | Step 2 | always | `references/shared/core-constraints.md` | Full | — |
| webnovel-review | Step 2 | always | `references/review-schema.md` | Full | — |
| webnovel-review | Step 2 | Review includes payoff/hook analysis | `references/shared/cool-points-guide.md` | Section | Required payoff dimension; genre adaptation: `## IX. Genre Adaptation` |
| webnovel-review | Step 2 | Review includes strand weaving | `references/shared/strand-weave-pattern.md` | Full | — |
| webnovel-review | Step 6 | Blocking issue needs user decision | `references/review/blocking-override-guidelines.md` | Full | — |
| webnovel-query | After query classification | All queries | `skills/webnovel-query/references/system-data-flow.md` | Section | Data-source priority section for the query type |
| webnovel-query | After query classification | Foreshadowing analysis | `skills/webnovel-query/references/advanced/foreshadowing.md` | Full | — |
| webnovel-query | After query classification | Pacing analysis | `references/shared/strand-weave-pattern.md` | Full | — |
| webnovel-query | After query classification | Format query | `skills/webnovel-query/references/tag-specification.md` | Full | — |

> Always read the seven large targets by section (`references/genre-profiles.md`, `skills/webnovel-init/references/creativity/selling-points.md`, `references/reading-power-taxonomy.md`, `skills/webnovel-plan/references/outlining/chapter-planning.md`, `skills/webnovel-init/references/creativity/creativity-constraints.md`, `skills/webnovel-write/references/polish-guide.md`, `references/shared/cool-points-guide.md`) to avoid loading them entirely on every init/plan/write run. Continue full reads for short files.

## CSV Retrieval: Direct `reference_search.py` Calls

| Skill | Stage | Trigger | Actual call |
|-------|------|------|----------|
| webnovel-init | Character/book/faction setup | User begins naming | `--skill init --table 命名规则 --query "{命名对象} {题材}" --genre {题材}` |
| webnovel-plan | Volume planning | always | `--skill plan --table 场景写法 --query "卷级结构 叙事功能"` |
| webnovel-plan | Volume planning | Payoff/conflict design needed | `--skill plan --table 爽点与节奏 --query "{卷级核心冲突}" --genre "${GENRE}"` |
| webnovel-plan | Volume planning | Plot template needed | `--skill plan --table 桥段套路 --query "{卷级核心冲突}" --genre "${GENRE}"` |
| webnovel-plan | Chapter-outline breakdown | New character appears | `--skill plan --table 命名规则 --query "角色命名" --genre {题材}` |
| webnovel-write | Step 2 | First appearance of new character | `--skill write --table 命名规则 --query "角色命名" --genre {题材}` |
| webnovel-write | Step 2 | Combat/confrontation scene | `--skill write --table 场景写法 --query "战斗描写" --genre {题材}` |
| webnovel-write | Step 2 | Multi-character dialogue | `--skill write --table 写作技法 --query "对话声线 口吻区分" --genre {题材}` |
| webnovel-write | Step 2 | Emotional/psychological description | `--skill write --table 写作技法 --query "情感描写 心理" --genre {题材}` |
| webnovel-write | Step 2 | Common trope | `--skill write --table 场景写法 --query "{桥段类型}" --genre {题材}` |

## CSV Retrieval: Indirect Consumption Through `story-system`

| Entry skill | Stage | Trigger | Indirect consumption |
|------------|------|------|----------|
| webnovel-init | Story System initialization | After init: `story-system "${GENRE}" --genre "${GENRE}" --persist --format json` | Route through `题材与调性推理.csv`; retrieve base/dynamic tables from `推荐基础检索表`/`推荐动态检索表`; `裁决规则.csv` injects style/pacing/anti-pattern decisions |
| webnovel-plan | Runtime contract refresh | When planning reaches concrete chapters: `--persist --emit-runtime-contracts --chapter {chapter_num}` | As above; `RuntimeContractBuilder` generates volume/chapter/review contracts |
| webnovel-write | Preparation | Before drafting: `--persist --emit-runtime-contracts --chapter {chapter_num}` | As above; `chapter_focus` in `chapter_{NNN}.json` is CSV reference only; the outline still defines chapter goals |
| webnovel-review | Step 1 | Fill missing runtime contracts for the target chapter | As above; review prioritizes `.story-system/reviews/chapter_{NNN}.review.json` and the latest accepted commit |

Actual `StorySystemEngine` data flow:

| Step | Source | Description |
|------|--------|------|
| `_route()` | `题材与调性推理.csv` | Select route using query, explicit genre, genre aliases, and canonical genre |
| `_collect_tables()` | Base/dynamic tables recommended by the route | Calls `reference_search.search()` with `skill="write"`; knowledge rows in recommended tables must therefore be visible to write |
| `_load_reasoning()` | `裁决规则.csv` | Load style priorities, default pacing, anti-pattern weights, and conflict decisions by canonical genre |
| `_apply_reasoning()` | Base/dynamic retrieval results + decision rules | Prioritize results to order contract injection |
| `_rank_anti_patterns()` | Route anti-patterns + recommended-table anti-patterns + decision anti-patterns | Merge and rank `anti_patterns.json` |

## Skills Without Independent References

| Skill | Description |
|-------|------|
| webnovel-dashboard | Read-only dashboard launch; no independent references; core validation endpoints: `/api/story-runtime/health` and `/api/preflight` |
| webnovel-learn | Read state, then append to `.webnovel/project_memory.json`; no independent references or CSV |

## Currently Not Directly Loaded

These files exist but current `SKILL.md` files do not explicitly require direct loading. Exclude them from the direct loading map until a skill adds a trigger:

| File | Status |
|------|------|
| `skills/webnovel-write/references/style-variants.md` | Not directly loaded by the current write workflow |
| `skills/webnovel-write/references/writing/combat-scenes.md` | Stub; content moved to CSV `场景写法` |
| `skills/webnovel-write/references/writing/dialogue-writing.md` | Stub; content moved to CSV `写作技法` |
| `skills/webnovel-write/references/writing/emotion-psychology.md` | Stub; content moved to CSV `写作技法` |
| `skills/webnovel-write/references/writing/scene-description.md` | Stub; content moved to CSV `写作技法` |
| `skills/webnovel-write/references/writing/desire-description.md` | Original retained conservatively; CSV does not yet cover desire-description details; not directly loaded by SKILL.md |
| `skills/webnovel-write/references/writing/genre-hook-payoff-library.md` | Original retained conservatively; CSV covers only some hook/payoff entries; not directly loaded by SKILL.md |
| `skills/webnovel-review/references/common-mistakes.md` | Not directly loaded by the current review workflow |
| `skills/webnovel-review/references/pacing-control.md` | Not directly loaded by the current review workflow |
