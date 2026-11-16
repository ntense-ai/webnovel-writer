# Melodramatic Romance Template

> Runtime preset identifier: `melodramatic-romance` (English taxonomy and initialization preset).

> **Core appeal**: Emotional conflict + anguished devotion + painful redemption and pursuit. Melodrama is not a derogatory label here; it is a powerful way to strike readers' emotional sore spots.

---

## Recommended Creative Constraints (Optional)
- Recommended constraint pack: Pack F15
- General overlay: Pack U01

## 1. Core Subgenres

### Domineering CEO Sweet Romance
- **Features**: Powerful man and less powerful woman, possessive devotion, more sweetness than suffering.
- **Core payoffs**: Lavish affection, humiliating romantic rivals, elite lifestyles.
- **Typical pairing**: Domineering CEO × Cinderella.

### Painful Redemption and Pursuit
- **Features**: The heroine suffers early; later the male lead humbly seeks forgiveness.
- **Core payoffs**: Her comeback, his bitter regret, desperate pleas to reunite.
- **Key**: Suffering must be substantial, and winning her back must be painful.

### Rebirth and Revenge
- **Features**: The heroine returns with memories and proceeds strategically.
- **Core payoffs**: Defeat unfaithful lovers and malicious rivals, change fate, find true love.
- **Key**: The past life must be tragic enough and the new life satisfying enough.

### Substitute-Lover Fiction
- **Features**: The heroine substitutes for an idealized former love, causing deep anguish.
- **Core payoffs**: The substitute rises, the idealized love's image collapses, the male lead regrets everything.
- **Key**: Anguished scenes must genuinely hurt.

---

## 2. Classic Plot Formulas

### Domineering CEO Formula
```
Domineering CEO + Cinderella = Power gap → Collision → Winning over → Sweetness
```

**Essential elements**:
- **Male lead**: Young and accomplished (28-35), worth over 100 million, cold outside and warm inside.
- **Heroine**: Ordinary, kind, resilient, and self-respecting.
- **Classic scenes**: Contract marriage, wall-pinning and forceful kiss, possessive declaration.

### Substitute-Lover Formula
```
Heroine is a substitute → Mistreatment → Leaves with a deadened heart → His painful pursuit
```

**Anguish design**:
1. He channels longing for his former love through the heroine.
2. He makes her wear the former love's clothes.
3. The former love returns and the heroine is discarded.
4. Once the truth emerges, regret comes too late.

### Redemption-and-Pursuit Formula
```
Her early suffering → Misunderstanding and separation → Her comeback → His humble pursuit → Happy ending
```

**Five movements of pursuit**:
1. Discover the truth; shock and remorse.
2. Search desperately and humbly beg to meet.
3. Bring gifts and apologies; be turned away.
4. Risk his life to protect her and move her.
5. Long atonement finally earns forgiveness.

---

## 3. Outline Structure (Standard: 800,000 Chinese Characters)

### Volume One: Illusion of Sweetness (Chapters 1-50, 15%)
- **Opening hook**: A contractual union shows unequal status.
- **Introductions**: Leads, idealized former love, romantic rival.
- **Central conflict**: His coldness and her restraint.
- **Minor climax**: First attraction/misunderstanding.

### Volume Two: Abyss of Anguish (Chapters 51-130, 25%)
- **Escalation**: Former love appears; misunderstandings deepen.
- **Concentrated anguish**: Misunderstanding, betrayal, harm.
- **Turning point**: Her feelings die and she decides to leave.
- **Climax**: Miscarriage/serious illness/framing.

### Volume Three: Breaking Away (Chapters 131-180, 15%)
- **Partial revelation**: The former love's true nature.
- **Heroine leaves**: Leaves while pregnant/without assets/fakes her death.
- **His shock**: Recognizes the value of what he lost.

### Volume Four: The Road to Redemption (Chapters 181-280, 30%)
- **His remorse**: Searching, waiting, humility.
- **Her growth**: Career success, confidence, independence.
- **Push and pull**: Old love is hard to forget, but forgiveness is difficult.
- **Climax**: She has a new love interest; he breaks down.

### Volume Five: Reconciliation (Chapters 281-350, 15%)
- **Full truth**: Every misunderstanding is resolved.
- **His atonement**: Risks his life/gives up everything.
- **Reconciliation process**: Slowly rebuild trust.
- **Finale**: Happy ending, wedding/children.

---

## 4. Emotional Tension

### Four Elements of Anguish
```
1. Misunderstanding: They love each other but cause mutual pain.
2. Missed chances: They repeatedly pass each other by.
3. Sacrifice: Quiet efforts for the other go unknown.
4. Regret: Realization comes too late.
```

### Sweetness Triggers
```
1. Possessiveness: "You're mine."
2. Jealousy: He loses control seeing her talk to someone else.
3. Devotion: She alone receives his tenderness.
4. Protection: He steps in front of her.
5. Confession: "I've loved you for a very long time."
```

---

## 5. Classic Scene Quick Reference

### Anguished Scenes
```markdown
[Substitute Dialogue]
"You thought I married you because I loved you? No. You're only her shadow."
He spoke coldly, holding a photograph of his former love.

[Leaving with a Broken Heart]
"I'm sorry. I'm not the person you love, and I no longer love you either."
She turned and walked into the rain without looking back.

[Begging for Her Return]
"I was wrong. Please come back..."
He knelt in the rain, but she never turned around.
```

### Sweet Scenes
```markdown
[Possessive Declaration]
"Woman, you've succeeded in getting my attention."
CEO Lu fixed her with a dangerous gaze.

[Wall-Pinning Confession]
He braced one hand against the wall, enclosing her in his arms.
"Trying to escape? Too late. From now on, you can only be mine."

[Everyday Affection]
"Cold?" He removed his suit jacket and draped it over her.
"No..."
"Wear it anyway. You look cold to me."
```

---

## 6. Strand Weave Configuration

```json
{
  "strand_ratio": {
    "quest": 30,    // Career/external conflict
    "fire": 55,     // Romance: the core
    "constellation": 15  // Relationship network
  },
  "fire_sub_strands": {
    "sweet": 40,    // Sweet scenes
    "abuse": 35,    // Anguished scenes
    "chase": 25     // Pursuit scenes
  }
}
```

**Pacing notes**:
- Romance should devote at least 50% to the Fire strand.
- Adjust sweetness/anguish to positioning: sweet romance 7:3, anguished romance 4:6.
- The pursuit phase must be long enough and sufficiently painful for the male lead.

---

## 🛠️ Entity Tag Extensions

```xml
<entity type="romantic-rival" name="Romantic rival name" desc="Relationship to protagonist" tier="level" rival_type="idealized-first-love/manipulative-rival/backup-partner" ending="ending"/>
<entity type="emotional-event" name="Event type" desc="Emotional change value" tier="level" trigger="Trigger condition"/>
<entity type="relationship-status" name="Current state" desc="ambiguous-attraction/in-love/cold-war/separated/reconciled" tier="level" affection="Affection"/>
```
