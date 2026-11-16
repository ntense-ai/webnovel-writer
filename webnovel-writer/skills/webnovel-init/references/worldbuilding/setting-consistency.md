# Setting Consistency Guide

> **Core principle**: Settings can be wildly imaginative, but their logic must hold together. Readers accept that magic exists; they do not accept magic working only when convenient.

---

## 1. Three Pillars of Consistency

### Physical Rules
Once established, the world's basic rules cannot be broken arbitrarily.

#### Positive Example ✅
```
Rule: Cultivators consume spiritual power to fly
→ Chapter 100: The protagonist exhausts that power and falls
→ Internally consistent; readers accept it
```

#### Negative Example ❌
```
Rule: Mortals cannot cultivate without awakened spiritual roots
→ Chapter 50: The mortal protagonist succeeds through hard work alone
→ Contradiction; readers ask, “Then why are spiritual roots necessary?”

Repairs:
A: The protagonist has dormant roots that awaken later
B: The protagonist obtains a special item, such as a pearl that steals others' spiritual roots
```

### Power System
Level suppression and comparisons of strength must remain consistent.

#### Common Problems
| Problem | Example | Repair |
|---------|------|---------|
| **Power collapse** | Chapter 10 says a Golden Core expert can destroy a city with one palm strike;<br/>in chapter 100 they can barely destroy a house | Introduce a new factor, such as a city-protection formation, or acknowledge earlier exaggeration through a corrective flashback |
| **Unlimited level jumping** | A Qi Refining protagonist defeats Golden Core, then at Qi Refining level 10 cannot defeat Foundation Establishment | Establish exceptional conditions: divine weapon, formation, ambush; not a routine feat |
| **Meaningless realms** | Higher realms supposedly extend lifespan, yet a Nascent Soul elder has lived 100,000 years | Explain a special constitution, possession, or different time flow |

### Social Ecology
Economics, politics, and culture must follow basic logic.

#### Checklist
- [ ] **Currency**: Is purchasing power stable? Do not price the same pill at 1,000 spirit stones in chapter 10 and 10 in chapter 50.
- [ ] **Balance of power**: Why have righteous and demonic factions coexisted for a millennium? Establish checks such as agreements between supreme experts, a common enemy, or complementary resources.
- [ ] **Population**: Is the cultivator-to-mortal ratio plausible? If everyone cultivates, who farms?

---

## 2. Common Plot Holes and Repairs

### Hole 1: The Antagonist Suddenly Becomes Stupid
**Symptom**: A previously calculating enemy becomes foolish just when the protagonist needs a victory.

**Repairs**:
- **Prepared trap**: Apparent foolishness is bait, turning the opponent's plan against them.
- **Information gap**: The enemy does not know about the protagonist's breakthrough or divine weapon and underestimates them.
- **Internal division**: A traitor deliberately leaks information.

### Hole 2: Rules Distorted for Plot Convenience
**Symptom**:
- Rule: Forbidden arts burn lifespan.
- Plot: The protagonist uses them ten times without side effects.
- Reader: “What happened to the cost?”

**Repairs**:
- **Advance setup**: Establish an immortality-type advantage that neutralizes the effect.
- **Delayed payment**: Lifespan is being consumed invisibly, leading to a later crisis and new plot.
- **Equivalent exchange**: Show the price each time: white hair, falling cultivation, or another tangible loss.

### Hole 3: Timeline Confusion
**Symptom**:
- Chapter 30: “The realm opens only on the once-a-century blood moon. It last opened 50 years ago.”
- Chapter 80: “That elder vanished inside during the blood moon 50 years ago.”
- Reader: “Which blood moon is this? The timing does not add up!”

**Repairs**:
- **Maintain a timeline**: Record dates for all major events using the template below.
- **Use one calendar**: Anchor events to a cultivation-calendar year or the protagonist's age.

---

## 3. Consistency Templates

### World Rules Audit
```markdown
## Core Rules (Unbreakable)
1. **Death is irreversible**: The dead cannot return, except under specified special conditions
2. **Realm suppression**: Lower realms cannot harm higher realms, except through specified advantages/formations
3. **Energy conservation**: Power always consumes spiritual energy, stamina, or lifespan

## Conditional Rules (Exceptions Require Prerequisites)
1. **Flight**: Below Foundation Establishment, independent flight is impossible
   - Exceptions: Flying boats or transport by an expert
2. **Lifespan**: Golden Core lifespan is 500 years
   - Exceptions: Life-extending pills or special constitutions

## Current Version
v1.2 (increment whenever settings change and record the reason)
```

### Power System Audit
```markdown
## Realm Comparison
| Realm | Representative feat | Lifespan | Spiritual power |
|------|-----------|------|---------|
| Qi Refining | Break stone barehanded | 100 years | 100 |
| Foundation Establishment | Fly on a sword; defeat a 100-person army alone | 200 years | 1,000 |
| Golden Core | Destroy a town with one strike; briefly reshape terrain | 500 years | 10,000 |
| Nascent Soul | Destroy a nation; overturn rivers and seas | 1,000 years | 100,000 |

## Fighting Above One's Level
- **Maximum gap**: One major realm, such as Qi Refining defeating Foundation Establishment
- **Required conditions**: Divine weapon + formation + ambush + overconfident enemy
- **Exceptional only**: Every such victory must carry a severe cost, such as grave injury or an expended trump card
```

### Timeline Audit
```markdown
## Main Timeline
| Event | Protagonist's age | Cultivation-calendar year | Notes |
|------|---------|-----------|------|
| Birth | 0 | 10050 | - |
| Spiritual roots awaken | 15 | 10065 | Dual roots, average aptitude |
| Enters sect | 16 | 10066 | Heavenly Sword Sect outer disciple |
| Obtains system | 17 | 10067 | Falls off a cliff; extraordinary encounter |
| Foundation Establishment | 20 | 10070 | Three years, fastest of the generation |

## Secondary Timeline (Antagonist)
| Event | Time | Impact |
|------|------|------|
| Blood God Cult founded | 5,000 years ago | War between righteous and demonic factions begins |
| Previous cult leader dies | 100 years ago | Current leader takes power before fully recovering strength |
| Cult plots to resurrect Blood God | Present | Cause of the main conflict |
```

---

## 4. Ongoing Maintenance: Setting Files

Projects generated by `/webnovel-init` should contain these files. Preserve the Chinese runtime paths:

```
设定集/
├── 世界观设定.md        # Physical rules, geography, history
├── 力量体系设定.md      # Realms, techniques, power comparisons
├── 势力设定.md          # Major sects, clans, faction relationships
├── 人物卡/             # One file per important character
│   ├── 主角-林天.md
│   ├── 反派-叶良辰.md
│   └── 师尊-云仙子.md
├── 时间轴.md            # Main and secondary timelines
└── 设定变更日志.md      # Reasons for each setting change
```

### Setting Change Log
```markdown
## v1.0 → v1.1 Changes
**Date**: 2025-01-01
**Changes**:
- Change: Golden Core lifespan from 300 to 500 years
- Reason: Conflicts with chapter 50's statement that an elder lived 400 years
- Scope: Recheck all Golden Core lifespan references in the first 30 chapters

## v1.1 → v1.2 Changes
**Date**: 2025-01-10
**Changes**:
- Addition: Introduce understanding of cosmic laws
- Reason: Prevent late-story numerical inflation; total spiritual power cannot decide every battle
- Scope: From Nascent Soul onward, law comprehension becomes another dimension of combat strength
```

---

## 5. Live Checking Workflow

### Before Each New Chapter
1. **Review the setting bible**: Confirm relevant realms, factions, and dates.
2. **Search previous chapters**: Use keywords to find earlier references to similar settings.
3. **Flag contradictions**: Immediately record inconsistencies in `设定变更日志.md`.

### After Each Major Arc
1. **Update the timeline**: Record when events occurred.
2. **Update power comparisons**: Add new realms or powerful characters.
3. **Check side effects**: Show subsequent costs of forbidden arts or special advantages already used.

---

## 🛠️ Consistency Checklist

After `/webnovel-write` generates a chapter, check:
- [ ] **Power levels**: Do battles obey the power system?
- [ ] **Timeline**: Do event dates contradict prior events?
- [ ] **Characterization**: Do actions fit personalities and allegiances?
- [ ] **Item limits**: Are artifacts, pills, and weapons used within established limits?
- [ ] **Faction relationships**: Do interactions match the existing relationship network?

---

## Appendix: Common Reader Objections

### Case 1: “Why Doesn't the Protagonist Just Use X?”
- **Problem**: An easier solution exists, but the protagonist chooses a convoluted route.
- **Cause**: The author forgot an earlier ability or item.
- **Prevention**: Maintain and review a current abilities list before writing.

### Case 2: “How Is This Villain Alive Again?”
- **Problem**: An explicitly dead antagonist returns without a reasonable explanation.
- **Cause**: The author wants further conflict but did not prepare the return.
- **Repair**: Explain a clone, feigned death, or rescue, and mark the unresolved setup in the setting bible.

### Case 3: “The Economy Makes No Sense”
- **Problem**: Spirit-stone purchasing power changes a hundredfold.
- **Cause**: No price anchor was established, such as 500 grams of spirit rice costing 10 spirit stones.
- **Prevention**: Keep a reference price list with stable prices for core goods.
