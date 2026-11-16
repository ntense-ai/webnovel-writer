# Historical Romance Template

> Runtime preset identifier: `historical-romance` (English taxonomy and initialization preset).

> **Core appeal**: Classical atmosphere + political struggles + deep love constrained by fate. Explore love, hatred, and power in a fictional or real historical setting.

---

## Recommended Creative Constraints (Optional)
- Recommended constraint packs: Pack F01 / Pack F18
- General overlay: Pack U01

## 1. Core Subgenres

### Palace Intrigue
- **Features**: Consorts compete for favor through careful strategy.
- **Core payoffs**: Outsmart rivals, gain imperial affection, rise through the ranks.
- **Typical pattern**: Palace maid/low-ranking consort → favored consort/empress.

### Household Intrigue
- **Features**: Great-family disputes, in-law tensions, competition to manage the household.
- **Core payoffs**: Defeat a malicious mother-in-law, gain authority, marital unity.
- **Typical pattern**: New bride → mistress of the household.

### Political Intrigue
- **Features**: Court maneuvering, national affairs, strategic contests.
- **Core payoffs**: Masterful planning, reshaping events, leaving a historical legacy.
- **Typical pattern**: Drawn into politics → influences the court.

### Sweet Romance
- **Features**: Romance first, politics second; abundant sweetness.
- **Core payoffs**: Exclusive devotion, others' envy, affectionate daily life.
- **Typical pattern**: Meeting → understanding → love → happy ending.

---

## 2. Classic Plot Frameworks

### Palace Intrigue
```
Enter palace → Gain foothold → Compete for favor → Crisis → Reach the top/leave

Detailed stages:
1. Enter through selection/imperial marriage/family arrangements.
2. Initial palace life: bullied/seeking a patron.
3. Gain imperial favor through talent/personality/opportunity.
4. Make enemies: suppression by empress/favored consort.
5. Rise through promotion/childbirth.
6. Major crisis: framing/loss of favor.
7. Desperate counterattack: expose truth/reverse fortunes.
8. Ending: become empress/leave palace/harmonious imperial marriage.
```

### Household Intrigue
```
Marry in → Gain foothold → Manage household → Crisis → Become mistress

Detailed stages:
1. Marry above/below one's status, or into a marriage intended to ward off illness.
2. Mother-in-law clashes: imposed rules/deliberate difficulties.
3. Sisters-in-law compete over resources/favor.
4. Marriage develops: coldness/warming feelings/misunderstandings.
5. Struggle for household authority.
6. Family crisis: confiscation/decline.
7. Turn the situation around.
8. Become mistress of the household.
```

### Political Intrigue
```
Drawn in → Choose sides → Maneuver → Decisive battle → New order

Detailed stages:
1. Drawn into a political maelstrom.
2. Choose a faction/be forced to align.
3. Participate in planning.
4. Multiple factions contend.
5. Crucial intelligence/turning point.
6. Final confrontation.
7. A new balance of power.
```

---

## 3. Outline Structure (Standard: 1 Million Chinese Characters)

### Volume One: Entering Palace/Mansion (Chapters 1-80, 20%)
- **Opening**: The opportunity to enter palace/marry.
- **Introductions**: Main factions and key supporting characters.
- **Core task**: Establish a foothold and learn the environment.
- **Minor climax**: Resolve the first crisis.

### Volume Two: Careful Advancement (Chapters 81-180, 25%)
- **Faction building**: Recruit allies and face enemies.
- **Romance**: Relationship with the male lead warms.
- **Central conflict**: First clash with the main opponent.
- **Climax**: An interim victory.

### Volume Three: Shifting Fortunes (Chapters 181-300, 30%)
- **Broader scope**: Higher-level contests.
- **Deeper crisis**: Framing/loss of favor/family implicated.
- **Darkest moment**: Hit rock bottom.
- **Turn**: Crucial help appears.

### Volume Four: Desperate Counterattack (Chapters 301-380, 20%)
- **Preparation**: Collect evidence and unite allies.
- **Revelation**: Expose the mastermind.
- **Final showdown**: Direct confrontation.
- **Reckoning**: Enemies face justice.

### Volume Five: Happy Resolution (Chapters 381-420, 15%)
- **Aftermath**: Establish a new order.
- **Romantic fulfillment**: Happy ending with the male lead.
- **Extras/everyday life**: Their happiness together.

---

## 4. Classical Dialogue Guidelines

### Forms of Address
```
Imperial household:
- Emperor: Your Majesty, His Majesty, the Sovereign.
- Empress: Your Majesty the Empress, Imperial Mother.
- Consorts: Consort X, Your Highness.
- Princes: Your Highness, Prince X.

Official families:
- Officials: Your Excellency, Lord X.
- Officials' wives: Madam, Lady X.
- Young ladies: Miss X, Young Lady X.

Commoners:
- Men: Young Master, Master X.
- Women: Miss, Mistress X.
```

### Common Classical Vocabulary
```
Self-reference and address:
- I: your consort, this humble wife, this palace's mistress, your servant, this humble woman.
- You: you/thou, Your Excellency, honored sir.
- He: that person, this person.

Actions:
- Look: glance, gaze, behold.
- Speak: say, declare, pronounce.
- Go: proceed, depart, travel toward.
- Come: arrive, approach, reach.

Descriptions:
- Beautiful: city-toppling beauty, peerless beauty, national beauty and heavenly fragrance.
- Clever: wise, quick-witted, delicately perceptive.
- Angry: vexed, angered, thunderously enraged.
```

### Dialogue Examples
```markdown
[Formal Greeting]
"Your consort pays her respects, Your Majesty. May you enjoy every blessing and peace."
She bowed gracefully, respectful without abasing herself.

[Verbal Clash]
"Sister, you flatter me. I would not dare claim such praise."
She covered her lips with a soft laugh, but her eyes were cold.

[Love Declaration]
"I could give up this empire. I cannot give up you."
He drew her into his arms, his voice low and resolute.
```

---

## 5. Classic Scene Library

### Meetings
```
1. Life-saving debt: She saves him without knowing his identity.
2. Accidental offense: She inadvertently offends someone important.
3. Unforgettable glimpse: One look at an event leaves a lasting impression.
4. Childhood companions: Childhood friends reunite.
5. Substitute bride/assumed identity: She marries in someone else's place.
```

### Winning Favor
```
1. Astonishing talent: A song/dance/poem amazes the gathering.
2. Clever solution: Intelligence shines during a crisis.
3. Rescue: Saves a powerful person at a crucial moment.
4. Retreat to advance: Appears vulnerable to gain sympathy.
5. Redirecting force: Uses an opponent's scheme against them.
```

### Framing and Reversal
```
Framing methods:
- Planting forbidden objects in a room.
- False accusations through fabricated evidence/bribed witnesses.
- Blaming someone for poisoning another person.
- Sowing discord with allies/the male lead.

Reversal methods:
- Crucial physical evidence and testimony.
- Allies testifying at the decisive moment.
- A scheme that draws the opponent out and exposes inconsistencies.
- Protection from someone of higher rank.
```

---

## 6. Strand Weave Configuration

```json
{
  "strand_ratio": {
    "quest": 45,    // Palace/household/political intrigue
    "fire": 35,     // Romance
    "constellation": 20  // Factions and relationships
  },
  "sub_types": {
    "power_struggle": 50,  // Power struggles
    "romance": 30,         // Romantic development
    "family": 20           // Family relationships
  }
}
```

---

## 7. Historical Background Quick Reference

### Common Fictional Dynasty Templates
```
Prosperous era:
- Strong nation, flourishing culture.
- Suitable for palace intrigue and sweet romance.
- References: High Tang, Kangxi-Qianlong Qing prosperity.

Turbulent era:
- Frequent war and transfers of power.
- Suitable for political intrigue and national stakes.
- References: Five Dynasties and Ten Kingdoms, Northern and Southern Dynasties.

Declining era:
- A weakening dynasty with internal and external threats.
- Suitable for tragedy and rebirth.
- References: Late Ming, late Qing.
```

---

## 🛠️ Entity Tag Extensions

```xml
<entity type="court-rank" name="Court rank name" desc="Privilege" tier="level" rank="Level"/>
<entity type="faction" name="Faction name" desc="Relationship to heroine" tier="level" leader="Key figure" relation="enemy/ally/neutral"/>
<entity type="scheme" name="Scheme name" desc="Result" tier="level" initiator="Initiator" target="Goal"/>
<entity type="archaic-term" name="Term" desc="Meaning" tier="level" usage="Usage context"/>
```
