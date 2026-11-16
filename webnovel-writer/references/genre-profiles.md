# Genre Profiles

> **Status: Fallback Only**
>
> Primary decisions, tone, and prohibitions for common genres have moved to Story Contracts / CSV route seeds.
> This file supplies supplementary guidance only when contracts are missing, the project has not upgraded, or fallback is explicitly requested.
>
> **Purpose**: Genre-specific reader-retention parameters for Step 1.5 / Context Agent / Checkers.
>
> **Principle**: Profiles adjust weights and recommendations, not hard decisions.
>
> **Note**: Expanded from observed xslca.cc popularity rankings: added history-travel / game-lit and updated key shuangwen / xianxia / urban-power parameters.

---

## I. Profile Fields

### 1.1 Core Fields

| Field | Type | Description |
|------|------|------|
| `id` | string | Unique genre identifier (lowercase English) |
| `name` | string | Chinese genre name (retained runtime value) |
| `description` | string | One-sentence core selling point |
| `tags` | string[] | Stackable genre tags (reserved for multi-tag support) |

### 1.2 Hook Configuration (hook_config)

| Field | Type | Description |
|------|------|------|
| `preferred_types` | string[] | Preferred hook types in priority order |
| `strength_baseline` | string | Default hook intensity: strong/medium/weak |
| `chapter_end_required` | boolean | Chapter-end hook preference (true = strong preference, not mandatory every chapter) |
| `transition_allowance` | number | Transition allowance (consecutive chapters permitted reduced intensity) |

### 1.3 Payoff Configuration (coolpoint_config)

| Field | Type | Description |
|------|------|------|
| `preferred_patterns` | string[] | Preferred payoff patterns in priority order |
| `density_per_chapter` | string | Payoff density per chapter: high(2+)/medium(1)/low(0-1) |
| `combo_interval` | number | Suggested combined-payoff interval (roughly one every N chapters) |
| `milestone_interval` | number | Suggested milestone-victory interval (roughly one every N chapters) |

### 1.4 Micro-Payoff Configuration (micropayoff_config)

| Field | Type | Description |
|------|------|------|
| `preferred_types` | string[] | Preferred micro-payoff types |
| `min_per_chapter` | number | Suggested minimum micro-payoffs per chapter |
| `transition_min` | number | Suggested minimum micro-payoffs in transitional chapters |

### 1.5 Pacing Red Lines (pacing_config)

| Field | Type | Description |
|------|------|------|
| `stagnation_threshold` | number | Stagnation threshold (N chapters without progress = HARD-003) |
| `strand_quest_max` | number | Maximum consecutive Quest chapters |
| `strand_fire_gap_max` | number | Maximum gap between Fire relationship chapters |
| `transition_max_consecutive` | number | Maximum consecutive transitional chapters |

### 1.6 Constraint Overrides (override_config)

| Field | Type | Description |
|------|------|------|
| `allowed_rationale_types` | string[] | Allowed override rationale types |
| `debt_multiplier` | number | Debt multiplier (>1 means stricter genre requirements) |
| `payback_window_default` | number | Default repayment window (chapters) |

---

## II. Built-in Genre Profiles

Chinese `name`, hook, pattern, and micro-payoff values in YAML are retained runtime labels; explanations are in English.

### 2.1 Wish Fulfillment / System Stories (shuangwen)

```yaml
id: shuangwen
name: 爽文/系统流
description: Special advantages, rapid progression, and repeated displays of strength and vindication
tags: [shuangwen]

hook_config:
  preferred_types: [渴望钩, 危机钩, 情绪钩]
  strength_baseline: medium
  chapter_end_required: true
  transition_allowance: 2

coolpoint_config:
  preferred_patterns: [装逼打脸, 扮猪吃虎, 越级反杀, 迪化误解]
  density_per_chapter: high
  combo_interval: 5
  milestone_interval: 10

micropayoff_config:
  preferred_types: [能力兑现, 资源兑现, 认可兑现]
  min_per_chapter: 2
  transition_min: 1

pacing_config:
  stagnation_threshold: 3
  strand_quest_max: 5
  strand_fire_gap_max: 15
  transition_max_consecutive: 2

override_config:
  allowed_rationale_types: [TRANSITIONAL_SETUP, ARC_TIMING]
  debt_multiplier: 1.0
  payback_window_default: 3
```

**Genre characteristics**:
- Readers expect fast pacing and dense payoffs.
- Preserve a clear expectation at chapter end (breakthrough/vindication/wealth approaching).
- Low tolerance for transitions; prefer no more than two consecutively.
- Visualize numerical feedback (combat power 50→180, before/after comparison).
- Give special advantages caps/costs/cooldowns to prevent unlimited use.

---

### 2.2 Cultivation / Xuanhuan (xianxia)

```yaml
id: xianxia
name: 修仙/玄幻
description: Defy fate amid harsh rules, opportunities, and conflict
tags: [xianxia]

hook_config:
  preferred_types: [危机钩, 渴望钩, 选择钩]
  strength_baseline: medium
  chapter_end_required: true
  transition_allowance: 3

coolpoint_config:
  preferred_patterns: [越级反杀, 扮猪吃虎, 身份掉马, 反派翻车]
  density_per_chapter: high
  combo_interval: 5
  milestone_interval: 15

micropayoff_config:
  preferred_types: [能力兑现, 资源兑现, 信息兑现]
  min_per_chapter: 1
  transition_min: 1

pacing_config:
  stagnation_threshold: 4
  strand_quest_max: 6
  strand_fire_gap_max: 12
  transition_max_consecutive: 3

override_config:
  allowed_rationale_types: [TRANSITIONAL_SETUP, WORLD_RULE_CONSTRAINT, ARC_TIMING]
  debt_multiplier: 0.9
  payback_window_default: 5
```

**Genre characteristics**:
- Worldbuilding requires room; more setup chapters are acceptable.
- Realm breakthroughs are the core expectation. Visualize tiers (8-10 levels with before/after numbers).
- Monetized resources (spirit stones/pills/techniques) carry core micro-payoffs.
- Setting constraints can reasonably justify overrides.

---

### 2.3 Romance / Sweet Romance (romance)

```yaml
id: romance
name: 言情/甜宠
description: Emotional interaction and relationship progress, mixing attraction with heartbreak
tags: [romance]

hook_config:
  preferred_types: [情绪钩, 渴望钩, 选择钩]
  strength_baseline: medium
  chapter_end_required: true
  transition_allowance: 2

coolpoint_config:
  preferred_patterns: [甜蜜超预期, 身份掉马, 迪化误解]
  density_per_chapter: medium
  combo_interval: 6
  milestone_interval: 12

micropayoff_config:
  preferred_types: [关系兑现, 情绪兑现, 认可兑现]
  min_per_chapter: 1
  transition_min: 1

pacing_config:
  stagnation_threshold: 4
  strand_quest_max: 4
  strand_fire_gap_max: 5
  transition_max_consecutive: 2

override_config:
  allowed_rationale_types: [TRANSITIONAL_SETUP, CHARACTER_CREDIBILITY, ARC_TIMING]
  debt_multiplier: 1.0
  payback_window_default: 4
```

**Genre characteristics**:
- Relationships are the absolute core; very low tolerance for gaps.
- Emotion hooks are the trump card (protectiveness/attraction/jealousy).
- Relationship progress is the most important micro-payoff.

---

### 2.4 Mystery / Detection (mystery)

```yaml
id: mystery
name: 悬疑/推理
description: Puzzle-driven reasoning gradually reveals the truth
tags: [mystery]

hook_config:
  preferred_types: [悬念钩, 危机钩, 选择钩]
  strength_baseline: medium
  chapter_end_required: true
  transition_allowance: 2

coolpoint_config:
  preferred_patterns: [反派翻车, 身份掉马]
  density_per_chapter: low
  combo_interval: 10
  milestone_interval: 20

micropayoff_config:
  preferred_types: [信息兑现, 线索兑现]
  min_per_chapter: 1
  transition_min: 1

pacing_config:
  stagnation_threshold: 3
  strand_quest_max: 8
  strand_fire_gap_max: 20
  transition_max_consecutive: 2

override_config:
  allowed_rationale_types: [LOGIC_INTEGRITY, TRANSITIONAL_SETUP, ARC_TIMING]
  debt_multiplier: 0.8
  payback_window_default: 5
```

**Genre characteristics**:
- Logical integrity takes priority over payoff density.
- Information is the core micro-payoff; keep clues progressing.
- LOGIC_INTEGRITY reasonably justifies lower hook intensity.

---

### 2.5 Rules-Based Horror (rules-mystery)

```yaml
id: rules-mystery
name: 规则怪谈
description: Uncanny rules, survival reasoning, and turning the tables on horror
tags: [rules-mystery, horror]

hook_config:
  preferred_types: [危机钩, 悬念钩, 选择钩]
  strength_baseline: strong
  chapter_end_required: true
  transition_allowance: 1

coolpoint_config:
  preferred_patterns: [越级反杀, 反派翻车]
  density_per_chapter: medium
  combo_interval: 5
  milestone_interval: 8

micropayoff_config:
  preferred_types: [信息兑现, 线索兑现, 能力兑现]
  min_per_chapter: 1
  transition_min: 1

pacing_config:
  stagnation_threshold: 2
  strand_quest_max: 4
  strand_fire_gap_max: 15
  transition_max_consecutive: 1

override_config:
  allowed_rationale_types: [LOGIC_INTEGRITY, WORLD_RULE_CONSTRAINT]
  debt_multiplier: 1.2
  payback_window_default: 2
```

**Genre characteristics**:
- Tense atmosphere requires strong hooks.
- Extremely low transition tolerance (one chapter).
- Rule constraints reasonably justify overrides.

---

### 2.6 Urban Supernatural (urban-power)

```yaml
id: urban-power
name: 都市异能
description: Modern settings, hidden powers, understated strength, and industry maneuvering
tags: [urban, power, industry]

hook_config:
  preferred_types: [危机钩, 渴望钩, 情绪钩]
  strength_baseline: medium
  chapter_end_required: true
  transition_allowance: 2

coolpoint_config:
  preferred_patterns: [扮猪吃虎, 装逼打脸, 身份掉马, 迪化误解]
  density_per_chapter: high
  combo_interval: 3
  milestone_interval: 10

micropayoff_config:
  preferred_types: [认可兑现, 能力兑现, 关系兑现]
  min_per_chapter: 2
  transition_min: 1

pacing_config:
  stagnation_threshold: 3
  strand_quest_max: 5
  strand_fire_gap_max: 8
  transition_max_consecutive: 2

override_config:
  allowed_rationale_types: [TRANSITIONAL_SETUP, ARC_TIMING]
  debt_multiplier: 1.0
  payback_window_default: 3
```

**Genre characteristics**:
- Repeated displays of strength and vindication are the core payoff.
- Modern settings require controlled pacing from hidden identity to reveal.
- Social-status changes are important micro-payoffs.
- Entertainment/industry settings are popular; relationships carry higher weight (maximum gap reduced to eight chapters).
- Three-chapter peak: chapter 1 predicament, chapter 2 initial ability display, chapter 3 small victory + new resistance.

---

### 2.7 Zhihu Short Fiction (zhihu-short)

```yaml
id: zhihu-short
name: 知乎短篇
description: Short and fast, strong reversals, emotional impact
tags: [short, zhihu]

hook_config:
  preferred_types: [情绪钩, 悬念钩, 选择钩]
  strength_baseline: strong
  chapter_end_required: true
  transition_allowance: 0

coolpoint_config:
  preferred_patterns: [反派翻车, 身份掉马, 甜蜜超预期]
  density_per_chapter: high
  combo_interval: 2
  milestone_interval: 3

micropayoff_config:
  preferred_types: [情绪兑现, 信息兑现, 关系兑现]
  min_per_chapter: 2
  transition_min: 2

pacing_config:
  stagnation_threshold: 1
  strand_quest_max: 2
  strand_fire_gap_max: 3
  transition_max_consecutive: 0

override_config:
  allowed_rationale_types: []
  debt_multiplier: 2.0
  payback_window_default: 1
```

**Genre characteristics**:
- Extremely narrow transition window; give every chapter at least one perceptible gain.
- Very high hook-intensity expectations.
- Highest debt multiplier; short fiction should avoid long-term unpaid promises.

---

### 2.8 Substitute-Lover / Angsty Romance (substitute)

```yaml
id: substitute
name: 替身文/虐文
description: Emotional entanglement, misunderstandings, reversals, and painful attempts to win back a partner
tags: [substitute, angst]

hook_config:
  preferred_types: [情绪钩, 选择钩, 悬念钩]
  strength_baseline: strong
  chapter_end_required: true
  transition_allowance: 2

coolpoint_config:
  preferred_patterns: [身份掉马, 反派翻车, 甜蜜超预期]
  density_per_chapter: medium
  combo_interval: 5
  milestone_interval: 10

micropayoff_config:
  preferred_types: [情绪兑现, 关系兑现, 认可兑现]
  min_per_chapter: 1
  transition_min: 1

pacing_config:
  stagnation_threshold: 3
  strand_quest_max: 3
  strand_fire_gap_max: 4
  transition_max_consecutive: 2

override_config:
  allowed_rationale_types: [CHARACTER_CREDIBILITY, ARC_TIMING, TRANSITIONAL_SETUP]
  debt_multiplier: 1.0
  payback_window_default: 4
```

**Genre characteristics**:
- Emotion hooks are central (heartbreak → protectiveness → anticipation).
- Identity reveal is the signature payoff.
- Extremely low tolerance for relationship-strand gaps.

---

### 2.9 Esports (esports)

```yaml
id: esports
name: 电竞
description: Competitive strategy, team cohesion, comebacks, and championship pursuit
tags: [esports, competition]

hook_config:
  preferred_types: [危机钩, 选择钩, 渴望钩]
  strength_baseline: strong
  chapter_end_required: true
  transition_allowance: 1

coolpoint_config:
  preferred_patterns: [越级反杀, 反派翻车, 迪化误解]
  density_per_chapter: high
  combo_interval: 4
  milestone_interval: 8

micropayoff_config:
  preferred_types: [信息兑现, 认可兑现, 关系兑现]
  min_per_chapter: 2
  transition_min: 1

pacing_config:
  stagnation_threshold: 2
  strand_quest_max: 4
  strand_fire_gap_max: 8
  transition_max_consecutive: 1

override_config:
  allowed_rationale_types: [TRANSITIONAL_SETUP, ARC_TIMING, LOGIC_INTEGRITY]
  debt_multiplier: 1.1
  payback_window_default: 2
```

**Genre characteristics**:
- Match chapters should have trackable victory goals and decision points.
- Disadvantaged matches and comebacks are core payoff sources.
- Low transition tolerance; preserve live feedback (scores/public opinion/status).

---

### 2.10 Livestreaming (livestream)

```yaml
id: livestream
name: 直播文
description: Platform-traffic competition driven by live feedback, public opinion, and commerce
tags: [livestream, urban]

hook_config:
  preferred_types: [危机钩, 情绪钩, 选择钩]
  strength_baseline: strong
  chapter_end_required: true
  transition_allowance: 1

coolpoint_config:
  preferred_patterns: [装逼打脸, 反派翻车, 身份掉马]
  density_per_chapter: high
  combo_interval: 3
  milestone_interval: 6

micropayoff_config:
  preferred_types: [认可兑现, 资源兑现, 信息兑现]
  min_per_chapter: 2
  transition_min: 1

pacing_config:
  stagnation_threshold: 2
  strand_quest_max: 4
  strand_fire_gap_max: 6
  transition_max_consecutive: 1

override_config:
  allowed_rationale_types: [TRANSITIONAL_SETUP, ARC_TIMING, CHARACTER_CREDIBILITY]
  debt_multiplier: 1.1
  payback_window_default: 2
```

**Genre characteristics**:
- Prioritize a closed loop of external feedback → protagonist reaction → changed outcome.
- Public-opinion reversals and business maneuvering need evidence chains, not slogans.
- Metric changes (viewers/rankings/conversions) provide frequent micro-payoffs.

---

### 2.11 Cosmic Horror (cosmic-horror)

```yaml
id: cosmic-horror
name: 克苏鲁
description: Corrupted rules and collapsing reason; approaching truth raises the cost
tags: [horror, mystery, cosmic]

hook_config:
  preferred_types: [悬念钩, 危机钩, 选择钩]
  strength_baseline: strong
  chapter_end_required: true
  transition_allowance: 1

coolpoint_config:
  preferred_patterns: [反派翻车, 迪化误解, 越级反杀]
  density_per_chapter: medium
  combo_interval: 6
  milestone_interval: 10

micropayoff_config:
  preferred_types: [线索兑现, 信息兑现, 情绪兑现]
  min_per_chapter: 1
  transition_min: 1

pacing_config:
  stagnation_threshold: 2
  strand_quest_max: 4
  strand_fire_gap_max: 12
  transition_max_consecutive: 1

override_config:
  allowed_rationale_types: [LOGIC_INTEGRITY, WORLD_RULE_CONSTRAINT, ARC_TIMING]
  debt_multiplier: 1.3
  payback_window_default: 2
```

**Genre characteristics**:
- Horror comes from rules and costs, not atmosphere alone.
- Every advance toward truth should incur a clear loss (sanity/relationships/resources).
- Strong hooks should favor unresolved rule questions over mere scares.

### 2.12 Historical Transmigration (history-travel)

```yaml
id: history-travel
name: 历史穿越
description: A modern soul in ancient times changes history through knowledge, development, and prosperity
tags: [history, travel, knowledge]

hook_config:
  preferred_types: [选择钩, 危机钩, 渴望钩]
  strength_baseline: medium
  chapter_end_required: true
  transition_allowance: 2

coolpoint_config:
  preferred_patterns: [打脸权威, 扮猪吃虎, 反派翻车, 身份掉马]
  density_per_chapter: medium
  combo_interval: 3
  milestone_interval: 10

micropayoff_config:
  preferred_types: [信息兑现, 资源兑现, 认可兑现]
  min_per_chapter: 1
  transition_min: 1

pacing_config:
  stagnation_threshold: 3
  strand_quest_max: 5
  strand_fire_gap_max: 10
  transition_max_consecutive: 2

override_config:
  allowed_rationale_types: [WORLD_RULE_CONSTRAINT, CHARACTER_CREDIBILITY, ARC_TIMING]
  debt_multiplier: 0.9
  payback_window_default: 4
```

**Genre characteristics**:
- Knowledge advantage > force; show the reasoning, not just the answer.
- Three-chapter peak: chapter 1 predicament/transmigration, chapter 2 initial knowledge display, chapter 3 small victory + new resistance.
- Antagonists need reasonable motives (conflicting interests); authorities require repeated proof rather than easy persuasion.
- History has inertia; one change triggers cascading, nonlinear consequences.
- Female protagonists are increasingly common; development/prosperity/industry-reform tags are popular.

---

### 2.13 GameLit (game-lit)

```yaml
id: game-lit
name: 游戏文
description: Gamified worlds, system advantages, numerical feedback, and starkly contrasting starting conditions
tags: [game, system, apocalypse]

hook_config:
  preferred_types: [危机钩, 渴望钩, 选择钩]
  strength_baseline: strong
  chapter_end_required: true
  transition_allowance: 0

coolpoint_config:
  preferred_patterns: [越级反杀, 装逼打脸, 扮猪吃虎, 反派翻车]
  density_per_chapter: high
  combo_interval: 3
  milestone_interval: 10

micropayoff_config:
  preferred_types: [能力兑现, 资源兑现, 认可兑现]
  min_per_chapter: 2
  transition_min: 1

pacing_config:
  stagnation_threshold: 2
  strand_quest_max: 5
  strand_fire_gap_max: 15
  transition_max_consecutive: 0

override_config:
  allowed_rationale_types: [WORLD_RULE_CONSTRAINT, ARC_TIMING]
  debt_multiplier: 1.1
  payback_window_default: 2
```

**Genre characteristics**:
- Reveal the special advantage early, usually within chapters 1-2.
- Visualize numerical feedback (combat power 50→180, before/after comparison).
- Give special advantages caps/costs/cooldowns to prevent unlimited use.
- Very narrow transition window; retain either a payoff or numerical progress.
- IP fusion (LOL/Pokémon, etc.) differentiates stories; apocalyptic survival is rising.
- Introduce a clear opponent early, preferably within three chapters: environment, rules, or a specific antagonist.

---

## III. Profile Loading

### 3.1 When to Load

1. **Step 1.5**: Load the profile matching `state.json → project.genre`.
2. **Context Agent**: Inject relevant profile fields into the writing brief.
3. **Checkers**: Adjust detection thresholds and recommendation weights by profile.

### 3.2 Multi-Tag Support (Reserved)

Currently single-tag. Future multi-tag support will:
- Combine tags through `tags`.
- Use the stricter value for conflicting fields.
- Example: `[romance, mystery]` → relationship gap min(5, 20) = 5.

### 3.3 Custom Profiles

Users may override defaults in `state.json`:

```json
{
  "project": {
    "genre": "xianxia",
    "genre_overrides": {
      "pacing_config": {
        "stagnation_threshold": 5
      }
    }
  }
}
```

---

## IV. Relationship to the Taxonomy

| Taxonomy definition | Profile configuration |
|--------------|-------------|
| Hook-type list | Preferred types |
| Payoff-pattern list | Preferred patterns |
| Micro-payoff types | Preferred types |
| Hard/Soft standards | Threshold adjustments |
| Override rationale types | Allowed rationales |
