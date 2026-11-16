# Realistic Fiction Template

> Runtime preset identifier: `realistic-fiction` (English taxonomy and initialization preset).

> **Core appeal**: Authenticity + social resonance + human depth. Ground the story in real life to create strong identification and emotional connection.

---

## Recommended Creative Constraints (Optional)
- Recommended constraint pack: Pack M15
- General overlay: Pack U02

## 1. Core Subgenres

### Career Struggle
- **Features**: Workplace challenges and advancement alongside emotional development.
- **Core payoffs**: Rising against the odds, silencing obstructive rivals, career and romantic success.
- **Typical pattern**: Junior employee → industry elite.

### Marriage and Relationships
- **Features**: Authentic marriage and family life with emotional entanglements.
- **Core payoffs**: Consequences for unfaithful partners, true love, happy endings.
- **Typical pattern**: Marriage crisis → self-awakening → new life.

### Comeback and Growth
- **Features**: A disadvantaged person's struggle against fate.
- **Core payoffs**: Reversal of fortune, proving oneself, achieving dreams.
- **Typical pattern**: Rock bottom → rise → pinnacle.

### Family Ethics
- **Features**: Family conflicts, kinship bonds, tests of character.
- **Core payoffs**: Resolving conflict, restoring affection, emotional healing.
- **Typical pattern**: Conflict → understanding → reconciliation.

---

## 2. Anchoring Authenticity

### Authentic Details
```
Setting details:
- Crowded rush-hour subway.
- A cramped, cluttered rented room.
- Exhaustion after late-night overtime.
- Anxiety over month-end Huabei credit repayments.

Professional details:
- Industry jargon/terminology.
- Workflows.
- Unwritten workplace rules.
- Overtime culture.
```

### Authentic Emotion
```
Avoid:
❌ "He fell in love with her beautiful appearance."
❌ "She was attracted to his wealth."

Instead:
✅ "Working until dawn, she noticed the hot coffee he had quietly left on her desk."
✅ "After the argument, she discovered he had secretly paid this month's rent."
```

### Authentic Dialogue
```
❌ Formal written language:
"I believe this proposal presents feasibility problems."

✅ Conversational:
"This plan... I'm not sure it'll work."

❌ Excessively literary:
"My heart fell into an abyss."

✅ Authentic expression:
"At that moment, I felt hollow. I couldn't say a word."
```

---

## 3. Handling Social Issues

### Common Issues
| Issue | Approach | Cautions |
|------|----------|----------|
| Workplace gender discrimination | Experience → resistance → change | Tell a story rather than preach |
| Family of origin | Parental manipulation → awakening → boundaries | Show complexity; do not demonize parents |
| Marital difficulties | Effectively solo parenting/in-law conflict | Offer ways forward rather than selling anxiety |
| Workplace overcompetition | 996 schedules/layoffs/age discrimination | Provide hope as well as recognition |
| Appearance anxiety | Appearance judgments → self-acceptance | Avoid only using makeover-and-revenge plots |

### Principles
```
1. Present problems without amplifying anxiety.
2. Show predicaments and possible exits.
3. Critique phenomena without attacking groups.
4. Create resonance and convey strength.
```

---

## 4. Outline Structure (Standard: 600,000 Chinese Characters)

### Volume One: The Predicament (Chapters 1-50, 20%)
- **Opening hook**: Show the protagonist's current difficulty.
- **Introductions**: Protagonist, opponent, ally, lover.
- **Central conflict**: Workplace/marital/family difficulties.
- **Minor climax**: First attempt to break free fails.

### Volume Two: Struggle and Awakening (Chapters 51-130, 30%)
- **Escalation**: The predicament deepens and pressure grows.
- **Changed understanding**: Awakening/change begins.
- **Accumulating ability**: Learning, growth, preparation.
- **Turning point**: A crucial event drives change.

### Volume Three: Fighting Free (Chapters 131-220, 30%)
- **Action**: Take the initiative to change circumstances.
- **Obstacles**: Opposing forces interfere.
- **Help**: A crucial benefactor appears.
- **Climax**: Decisive victory.

### Volume Four: New Life (Chapters 221-280, 20%)
- **Results**: Career/romantic fulfillment.
- **Reconciliation**: Make peace with the past.
- **New challenges**: Higher aspirations.
- **Ending**: Open or happy resolution.

---

## 5. Deep Characterization

### Three-Dimensional Method
```
Dimension One: External features.
- Appearance, occupation, social identity.
- Habits and speech.

Dimension Two: Inner personality.
- Strengths and weaknesses.
- Fears and desires.
- Values and principles.

Dimension Three: Growth arc.
- Starting state.
- Catalyst for change.
- Final state.
```

### Morally Gray Characters
```
Antagonists are not entirely dark:
- The difficult mother-in-law believes she is protecting her son.
- The suppressive manager is also being exploited.
- The unfaithful husband acts within an already troubled marriage.

Protagonists are not entirely pure:
- Have selfish sides.
- Make mistakes.
- Need to grow.
```

---

## 6. Classic Scene Library

### Workplace Scenes
```
Crises:
- A newcomer steals credit.
- A manager deliberately obstructs.
- Workplace sexual harassment.
- Being "optimized out" at age 35.

Comebacks:
- Save a critical project.
- Outperform the former employer after changing jobs.
- Build a successful business.
- Expose unwritten workplace practices.
```

### Marriage Scenes
```
Crises:
- Discover evidence of infidelity.
- Mother/daughter-in-law conflict.
- Effectively solo parenting.
- Financial control.

Awakening:
- Decide to divorce.
- Become financially independent.
- Redefine oneself.
- Meet true love.
```

### Family Scenes
```
Conflicts:
- Pressure to marry/have children.
- Favoritism toward siblings.
- Parental manipulation.
- Financial disputes.

Reconciliation:
- Understand parents' limitations.
- Establish healthy boundaries.
- Choose what to forgive.
- Create new relationship patterns.
```

---

## 7. Strand Weave Configuration

```json
{
  "strand_ratio": {
    "quest": 40,    // Career/main plot
    "fire": 35,     // Emotional strand
    "constellation": 25  // Social network
  },
  "reality_anchors": {
    "daily_life": 30,    // Everyday-life description
    "social_issue": 25,  // Social issues
    "emotion": 45        // Emotional resonance
  }
}
```

---

## 8. Dialogue Examples

### Workplace Dialogue
```markdown
[Deliberate Obstruction]
"Redo this report." The supervisor tossed the file onto the desk.
"What's wrong with it?" She held back her anger.
"If I say there's a problem, there's a problem. Newcomers shouldn't ask so many questions."

[Turning the Tables]
"Manager Wang, I prepared this proposal. The meeting minutes record that."
She spoke without arrogance or submission; the room erupted.
```

### Relationship Dialogue
```markdown
[Argument]
"Work, work, work. Have you ever looked after this family?"
"Where would the money come from if I didn't work? Do you think the mortgage and car payments fall from the sky?"
Both fell silent. The air seemed frozen.

[Reconciliation]
"I'm sorry. I shouldn't have shouted."
"I was wrong too. Can we... talk properly?"
```

---

## 🛠️ Entity Tag Extensions

```xml
<entity type="social-issue" name="Issue name" desc="Presentation" tier="level" attitude="critique/reflection/healing"/>
<entity type="real-world-scene" name="Scene name" desc="Key descriptive details" tier="level" emotion="Emotional tone"/>
<entity type="workplace" name="Company name" desc="Workplace culture" tier="level" industry="Industry"/>
<entity type="relationship" name="Relationship type" desc="Central conflict" tier="level" direction="Development direction"/>
```
