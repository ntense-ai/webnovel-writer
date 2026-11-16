# Outline Structure Guide

> Archive note: this is a historical methodology reference, not automatically loaded by the `/webnovel-plan` main workflow.
> To integrate it, first add explicit step triggers and reading instructions to `SKILL.md`.

> **Core principle**: an outline is a map, not a shackle. A good outline guides direction while leaving room for inspiration.

---

## 1. Three-layer outline architecture

### Layer 1: Skeleton outline (required, 30%)
**Purpose**: give the story a clear beginning, development, turn, and conclusion.

```markdown
## Skeleton example
**Opening (Chapters 1–50)**: failed youth Lin Tian suffers a broken engagement and gains a devouring system by chance
**Early (51–200)**: rises in his sect, humiliates former mockers, discovers his sister was abducted
**Middle (201–500)**: travels the cultivation world to rescue her, navigates major factions, rapidly gains strength
**Late (501–800)**: uncovers his origins as an ancient powerhouse's reincarnation; final confrontation with Blood God Cult leader
**Ending (801–850)**: defeats Blood God, rescues sister, ascends to the immortal realm (sequel opening)
```

**Skeleton checklist**:
- [ ] **Clear starting point**: protagonist's initial state and core contradiction?
- [ ] **Turning points**: at least three major turns (e.g. special ability gained, joins sect, master killed).
- [ ] **Clear destination**: ultimate goal (defeat demon king/ascend/dominate).

---

### Layer 2: Volume outlines (recommended, 50%)
**Purpose**: divide a long novel into smaller climaxes to prevent reader fatigue.

#### Principles
- **One smaller goal per volume**: e.g. “growth in the starter village”, then “sect trials”.
- **Every volume ends in a climax**: defeat minor boss, obtain divine artifact, break through a realm.
- **Transition between volumes**: prepare map changes rather than switching abruptly.

#### Template
```markdown
## Volume 1: Road to Ascendance (Chapters 1–150)
**Core goal**: rise from failure to genius
**Main conflicts**: family infighting, broken engagement, sect selection
**Climax**: win sect tournament, humiliate Ye Liangchen
**Foreshadowing**: hint at unusual origins; plant ancient-bloodline clues

## Volume 2: Sect Turmoil (151–300)
**Core goal**: establish a foothold in Heavenly Sword Sect
**Main conflicts**: exclusion by inner disciples, elder faction struggles, secret-realm treasure contest
**Climax**: obtain Sword Tomb inheritance in secret realm; power surges
**Foreshadowing**: discover clues that Blood God Cult abducted sister

## Volume 3: Rescue Journey (301–500)
**Core goal**: track Blood God Cult and rescue sister
**Main conflicts**: repeated clashes with cult, misunderstandings between righteous and evil sides, anxiety about insufficient power
**Climax**: enter cult headquarters alone; first clash with leader (defeated but survives)
**Foreshadowing**: learn sister's special constitution is key to Blood God's resurrection
```

---

### Layer 3: Chapter outlines (optional, 20%)
**Purpose**: specify each chapter's content, useful for beginners or writer's block.

#### Template
```markdown
## Chapter 1: The Humiliation of a Broken Engagement
**Length**: 3,000 English words
**Main plot**:
  - Ye clan heir Ye Liangchen arrives to break the engagement
  - Lin Tian is humiliated; the whole family loses face
  - Lin Tian is angry but powerless to resist (establish failed status)
**Subplot**:
  - Father sighs; sister comforts him
  - Foreshadowing: the jade pendant in Lin Tian's hand glows faintly
**Gratification**: none (pressure-building chapter preparing later comeuppance)
**Ending hook**: “At that moment, a mechanical voice sounded in Lin Tian's mind: ‘Devouring system activating...’”
```

**Flexibility**:
- Outline only the core content; develop dialogue and details during writing.
- Inspiration may justify departing from the outline, but remember to revise the outline afterward.

---

## 2. Choosing detail level

### Broad-outline approach (experienced writers)
- **Content**: skeleton + volume outlines only.
- **Strength**: freedom and easy adjustment.
- **Weakness**: easier to drift or get stuck.

### Detailed-outline approach (beginners)
- **Content**: skeleton + volumes + chapters (at least the first fifty).
- **Strength**: no uncertainty about what to write each day.
- **Weakness**: lengthy preparation.

### Hybrid approach (recommended)
- **Content**: skeleton (whole book) + volumes (whole book) + chapters (next 10–20).
- **Strength**: direction with flexibility.
- **Method**: after each completed volume, add the next volume's chapter outlines.

---

## 3. Dynamic outline adjustment

### When to adjust
1. **Reader feedback**: increase attention to particularly popular characters/plots.
2. **Inspiration**: a better plot direction occurs to you.
3. **Abnormal metrics**: a sharp subscription/bookmark decline may indicate a plot problem.

### How to adjust
```markdown
## Outline change log
**Date**: 2025-01-03
**Change**: sister was scheduled to die in Volume 2 (heartbreak), but readers find her very popular
**New plan**: abduct her instead; delay revealing whether she survives until Volume 3 (extend suspense)
**Impact**: redesign Volume 2 climax as obtaining Sword Tomb inheritance
```

### Red lines
- **Protagonist characterization**: no abrupt good-to-evil change (or reverse) without sufficient setup.
- **Power system**: no arbitrary realm changes that invalidate earlier comparisons.
- **Core plot**: subplots can change; core goals such as rescuing the sister should not be casually abandoned.

---

## 4. Outline tools

### Tool A: Markdown + Git
```
outlines/
├── master-outline.md
├── volume-1-outline.md
├── volume-1-timeline.md
├── volume-1-beats.md
├── volume-2-outline.md
└── outline-change-log.md   # Optional manual change log
```
**Strength**: plain text, easy version control and search. New projects use English paths. For existing projects, resolve the actual paths before reading or writing; retain legacy filenames.

### Tool B: Mind map (XMind/MindNode)
```
Main plot: rescue sister
├── Volume 1: rise in starter village
│   ├── Chapters 1–10: broken engagement
│   ├── 11–30: obtain system
│   └── 31–50: sect selection
├── Volume 2: sect turmoil
│   └── ...
```
**Strength**: strong visualization and clear hierarchy.

### Tool C: Spreadsheet (Excel/Notion)
| Chapter | Main plot | Subplot | Gratification | Foreshadowing | Length |
|------|---------|---------|------|------|------|
| 1 | Broken engagement | Sister comforts him | None | Glowing pendant | 3,000 |
| 2 | Activate system | Test abilities | Devour beast | System has hidden features | 3,000 |
**Strength**: data-driven management and easy gratification-density tracking.

---

## 5. Linking outline and setting collection

An outline cannot stand alone; coordinate it with settings.

### Checklist
- [ ] **Character sheets**: is each important character's sheet established before introduction?
- [ ] **Faction relationships**: do faction conflicts match the setting collection's relationship network?
- [ ] **Power system**: does protagonist progression follow the specified pacing?
- [ ] **Timeline**: is each volume's duration reasonable? (No sudden ten-year jump.)

### Example conflict
```markdown
## Problem
Outline: protagonist reaches Golden Core in Chapter 50
Settings: protagonist is sixteen; normal cultivation takes twenty years to reach Golden Core
Conflict: implausible timeline

## Solutions
A: change the outline to Foundation Establishment
B: add “devouring system accelerates cultivation 100-fold” to settings
C: add a fortuitous encounter (eating a ten-thousand-year spirit fruit)
```

---

## 🛠️ Outline self-check

Before writing, check:
- [ ] **Completeness**: beginning, middle, and ending all present?
- [ ] **Pacing**: clear alternation of highs and lows? (Not endless climaxes or flatness.)
- [ ] **Logic**: reasonable progression, not characters suddenly becoming stupid?
- [ ] **Gratification**: at least one payoff every 10–20 chapters?
- [ ] **Foreshadowing**: planned resolution for every planted thread, with chapter marked?
- [ ] **Length**: estimated total fits platform requirements? (Qidian: at least one million English words.)

---

## Appendix: Classic outline case studies

### Case 1: A Record of a Mortal's Journey to Immortality
- **Skeleton**: ordinary youth cultivates → becomes an immortal-realm powerhouse (very long arc, eight million English words).
- **Volumes**: divided by map (mortal realm → spirit realm → immortal realm); strength positioning resets with each move.
- **Pacing**: each sub-realm has its own smaller climax (treasure gained/enemy defeated).

### Case 2: Battle Through the Heavens
- **Skeleton**: genius youth falls → rises and takes revenge → becomes Dou Emperor.
- **Volumes**: divided by power rank (Dou Practitioner → Dou King → Dou Saint), one volume per major realm.
- **Pacing**: explicit deadlines such as the three-year agreement create urgency.
