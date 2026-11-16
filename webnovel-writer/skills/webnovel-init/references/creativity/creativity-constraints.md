# Creativity Constraints

> **Purpose**: Define structured constraints for generating unconventional ideas.
> **Principle**: Constraints are catalysts, not merely restrictions. Structured constraints encourage novelty and differentiation.

## Contents
- I. Idea Package Schema
- II. Three-Axis Mashup
- III. Anti-Trope Triggers
- IV. Antagonist Mirror
- V. Hook-First Design
- VI. Hard Constraints
- VII. Three-Question Filter
- VIII. Scoring System
- IX. Output Format

---

## I. Idea Package Schema

Every idea must contain these fields:

```json
{
  "id": "uuid",
  "title": "Book title",
  "one_liner": "One-sentence selling point: a 10-second elevator pitch",
  "genre": "Genre",
  "novelty_axes": {
    "genre_base": "Genre foundation",
    "rule_constraint": "Rule constraint: at least one unconventional rule",
    "character_conflict": "Character conflict"
  },
  "anti_trope": "Selected anti-trope rule",
  "protagonist": {
    "flaw": "Protagonist flaw: required",
    "desire": "Core desire"
  },
  "antagonist_mirror": {
    "shared_trait": "Desire/flaw shared with protagonist",
    "opposite_path": "Opposite path taken"
  },
  "opening_hook": {
    "hook_sentence": "One-sentence hook",
    "opening_scene": "Opening scene summary",
    "chapter_end_suspense": "Chapter 1 closing suspense"
  },
  "hard_constraints": ["Hard constraint 1", "Hard constraint 2"],
  "score": {
    "novelty": 0,
    "market_fit": 0,
    "writability": 0,
    "cool_point_density": 0,
    "long_term_potential": 0,
    "total": 0
  },
  "three_questions": {
    "q1_why_this_way": "Why must this genre be written this way?",
    "q2_protagonist_swap": "Would replacing the protagonist with a conventional archetype break the story?",
    "q3_one_liner_unique": "Can the pitch be expressed clearly in one sentence without repeating common tropes?"
  },
  "status": "pending|selected|rejected",
  "created_at": "ISO date"
}
```

---

## II. Three-Axis Mashup

### 2.1 Axis Definitions

| Axis | Description | Examples |
|---|------|------|
| **Genre foundation** | Type of story world | Cultivation, urban, rule-based horror |
| **Rule constraint** | Hard limits on the world, abilities, or behavior | Scarcity, costly advantages, no direct combat |
| **Character conflict** | Inner conflict or conflict with the world | Rejecting domination, moral dilemmas, identity |

### 2.2 Mashup Rule

**At least 2 of the 3 axes must differ from the genre's default choices.**

| Genre | Default choices | Recommended alternatives |
|------|---------|------------------|
| Cultivation | Abundant resources, free advantages, pursuit of domination | Scarcity, costly advantages, cautious survival or rejection of easy gratification |
| Urban | Modern technology, hidden identity, ostentatious vindication | Intruding rules, public identity, intellectual contests |
| Romance | Strong man/weak woman, misunderstandings, happy ending | Equal partners, transparent information, open ending |
| Rule-based horror | Solvable rules, special protagonist ability, escape | Irreversible rules, ordinary protagonist, survival at a cost |

### 2.3 Examples

```
✅ Strong mashup:
Cultivation (genre) + extreme scarcity (rules) + protagonist rejects easy domination (character)
→ Source rubric: 3/3 non-default axes; broad creative possibilities

⚠️ Average mashup:
Cultivation (genre) + costly special advantage (rules) + pursuit of domination (character)
→ Source rubric: 2/3 non-default axes; acceptable

❌ Formulaic mashup:
Cultivation (genre) + abundant resources (rules) + pursuit of domination (character)
→ Source rubric: 0/3 non-default axes; reject
```

---

## III. Anti-Trope Triggers

### 3.1 Mandatory Rule

**Every project must choose at least one unconventional rule.**

### 3.2 General Anti-Trope Library

| ID | Rule | Genres | Creative driver |
|----|-----------|---------|---------|
| AT-001 | The advantage has an irreversible cost | All | Every use is a choice |
| AT-002 | The protagonist cannot directly humiliate rivals; victories must exploit rules/systems | Payoff-driven fiction/cultivation | Intelligence replaces brute force |
| AT-003 | The protagonist's strength is also a fatal weakness | All | Double-edged design |
| AT-004 | Antagonist and protagonist share the same advantage/ability | All | Mirrored opposition |
| AT-005 | The protagonist's goal opposes reader expectations | All | Expectation reversal |
| AT-006 | World rules disadvantage the protagonist rather than grant privilege | Rule-based horror/cultivation | Fair competition |
| AT-007 | Growth requires losing something | All | Growth has weight |
| AT-008 | Information is symmetric: protagonist knows no more than the reader | Mystery/rule-based horror | Shared deduction |
| AT-009 | The “right choice” causes negative consequences | All | Moral ambiguity |
| AT-010 | The advantage has usage or cooldown limits | System fiction | Resource management |

### 3.3 Genre-Specific Libraries

See:
- `anti-trope-xianxia.md`: cultivation/fantasy
- `anti-trope-urban.md`: urban/historical
- `anti-trope-game.md`: game/science fiction
- `anti-trope-rules-mystery.md`: rule-based horror

---

## IV. Antagonist Mirror

### 4.1 Core Principle

**The antagonist shares the protagonist's desire or flaw but takes the opposite path.**

### 4.2 Mirror Templates

| Shared trait | Protagonist's path | Antagonist's path |
|---------|---------|---------|
| Desire for power | Earn through effort/sacrifice | Gain through plunder/betrayal |
| Fear of loss | Learn acceptance and letting go | Control and possess everything |
| Need for recognition | Prove personal worth | Force others' approval |
| Escape from the past | Face it and reconcile | Destroy all evidence |
| Protecting loved ones | Help them grow | Imprison/control them |

### 4.3 Example

```
Protagonist: Lin Tian seeks power to protect his family
Antagonist: Murong Zhan seeks power to rule everything

Shared trait: Hunger for power
Protagonist's path: Cultivation and sacrifice
Antagonist's path: Devouring others

Mirror conflict: Their confrontation concerns not only strength but how strength is acquired
```

---

## V. Hook-First Design

### 5.1 Core Principle

**Create the hook before the outline.**

Before establishing the complete outline, design:
1. One hook sentence, within 10 English words
2. An opening scene, within 50 English words
3. A chapter 1 cliffhanger, within 30 English words

### 5.2 Hook Templates

| Type | Template | Example |
|---------|------|------|
| Contrast | [Identity A], yet [behavior B] | The useless heir makes the sect master kneel |
| Mystery | [Anomaly], [question] | He died three times and remembers each death |
| Cost | Gain [X], at the cost of [Y] | A divine system paid for with lifespan |
| Choice | [Dilemma], but chooses [unexpected option] | Save his wife or the world? He chooses a third path |
| Reversal | Expected [A], actually [B] | Everyone thought he was dead, including himself |

### 5.3 Opening Scenes

| Scene type | Feature | Suitable genres |
|---------|------|---------|
| Crisis | Protagonist on the edge of death | Rule-based horror, cultivation |
| Contrast | Identity/ability conflicts with appearance | Hidden-strength stories, urban |
| Mystery | An unanswered puzzle | Mystery, rule-based horror |
| Conflict | Direct confrontation with others | Payoff-driven fiction, romance |
| Disrupted routine | Peaceful daily life breaks apart | All |

---

## VI. Hard Constraints

### 6.1 Core Principle

**Define 2–3 hard constraints to force distinctive plot solutions.**

### 6.2 Constraint Types

| Type | Description | Example |
|------|------|------|
| World | Unbreakable operating rules | Cultivators cannot kill mortals |
| Ability | Firm limits on protagonist powers | The advantage works once daily |
| Behavior | Forbidden actions | The protagonist cannot attack first |
| Information | Boundaries of knowledge | The protagonist does not know they transmigrated |
| Resources | Fixed scarcity | Only 100 spirit stones exist worldwide |

### 6.3 Combined Example

```
Project: The Cage of Rules

Constraint 1 (world): A triggered rule cannot be revoked
Constraint 2 (ability): The protagonist can see rules, not change them
Constraint 3 (behavior): Every warning given to another person erases one of the protagonist's memories

Creative drivers:
- How can the protagonist help others without changing rules?
- How do they decide when memory loss is the cost?
- How does irreversibility generate tension?
```

---

## VII. Three-Question Filter

### 7.1 Questions

| # | Question | Pass criterion |
|---|------|---------|
| Q1 | Why must this genre be written this way? | At least one distinctive reason |
| Q2 | Would a conventional protagonist break the story? | Yes: character and story are deeply linked |
| Q3 | Is the selling point clear in one sentence and different from common tropes? | Yes: clear and distinctive |

### 7.2 Process

```
Generate 3–5 ideas
    ↓
Three-question filter
    ↓
Pass 3/3 → Score
Pass 2/3 → Revise and filter again
Pass 1/3 or 0/3 → Eliminate
```

---

## VIII. Scoring System

### 8.1 Five Dimensions

| Dimension | Weight | 1 point | 3 points | 5 points |
|------|------|-----|-----|-----|
| Novelty | 25% | Everywhere already | Small innovation | Creates a new category |
| Market fit | 20% | Obscure niche | Moderate audience | Broad popularity |
| Writability | 20% | Extremely difficult | Moderate difficulty | Easy to execute |
| Payoff density | 20% | Sparse | Moderate | High |
| Long-term potential | 15% | Hard to continue | Sustainable | Unlimited expansion |

### 8.2 Formula

```
Total = novelty×2.5 + market_fit×2 + writability×2 + cool_point_density×2 + long_term_potential×1.5
Maximum = 50
Passing = 30
Recommended = 40
```

---

## IX. Output Format

### 9.1 Idea Card

```markdown
## Idea #{N}: {title}

**One-sentence pitch**: {one_liner}

**Three-axis mashup**:
- Genre foundation: {genre_base}
- Rule constraint: {rule_constraint}
- Character conflict: {character_conflict}

**Anti-trope rule**: {anti_trope}

**Protagonist**:
- Flaw: {flaw}
- Desire: {desire}

**Antagonist mirror**:
- Shared trait: {shared_trait}
- Opposite path: {opposite_path}

**Opening hook**:
- Hook: {hook_sentence}
- Opening: {opening_scene}
- Suspense: {chapter_end_suspense}

**Hard constraints**:
1. {constraint_1}
2. {constraint_2}

**Three-question filter**:
- Q1: {answer_1}
- Q2: {answer_2}
- Q3: {answer_3}

**Score**: {total}/50
- Novelty: {novelty}/5
- Market fit: {market_fit}/5
- Writability: {writability}/5
- Payoff density: {cool_point_density}/5
- Long-term potential: {long_term_potential}/5
```
