# Gaming and Sports Fiction Template

> Runtime preset identifier: `gaming-and-sports` (English taxonomy and initialization preset).

> **Core appeal**: Competitive contests + strategic use of rules + team growth. Burn bright in the arena and prove everything through skill.

---

## Recommended Creative Constraints (Optional)
- Recommended constraint pack: Pack M09
- General overlay: Pack U03

## 1. Core Subgenres

### Esports
- **Features**: Professional esports, team matches, the road to a championship.
- **Core payoffs**: Mechanical dominance, tactical reversals, championship glory.
- **Representative works**: *The King's Avatar*, *You Are My Glory*, *Go Go Squid!*, *Cross Fire*.

### Traditional Sports
- **Features**: Football/basketball/tennis and other traditional sports.
- **Core payoffs**: Last-second winners, comeback victories, championship dreams.
- **Representative works**: *Slam Dunk*, *Captain Tsubasa*, *The Prince of Tennis*, *Boyhood*.

### Board-Game Competition
- **Features**: Intellectual contests such as Go/Chinese chess/mahjong.
- **Core payoffs**: Intellectual dominance, brilliant moves, prodigy showdowns.
- **Representative works**: *Hikaru no Go*, *Tianyuan*, *Go Player*.

### Games and Life
- **Features**: Games and reality intertwine; games change lives.
- **Core payoffs**: In-game achievements, real-world comebacks, virtual versus real.
- **Representative works**: *Starting from Zero*, *Virtual World: Close Combat Mage*, *Thriller Paradise*.

---

## 2. Worldbuilding: Competitive Society

### Esports Ecosystem
| Tier | Features | Income |
|------|------|------|
| Elite teams | Regular world-championship attendees | Tens of millions |
| First-tier teams | Strong league competitors | Millions |
| Second-tier teams | Mid-table league teams | Hundreds of thousands |
| Academy teams | Train newcomers | Basic salary |
| Ranked-ladder stars | Elite solo-queue players | No fixed income |

### Event System
| Rank | Event | Importance |
|------|------|--------|
| S | World championship | Highest honor |
| A | Intercontinental event | Regional honor |
| B | League | Regular season |
| C | Cup | Additional honors |
| D | Offline event | Practice/exposure |

### Team Structure
| Role | Responsibilities | Importance |
|------|------|--------|
| Captain | Command and decisions | Central |
| Main carry | Core damage | Crucial |
| Support | Protection/control | Important |
| Coach | Tactical planning | Behind the scenes |
| Analyst | Data analysis | Supporting |

---

## 3. Competition System Design

### Player Growth
```
Talent awakens → Basic training → Team tryout → Substitute appearance → Starting position → Star player → Legend
```

### Ability Dimensions
| Dimension | Description | Training |
|------|------|----------|
| Mechanics | Speed/precision | Repetition |
| Awareness | Big-picture understanding/anticipation | Replay analysis |
| Mentality | Pressure resistance/consistency | Match experience |
| Coordination | Team chemistry | Joint practice |
| Tactics | Understanding and execution | Coaching |

### Match Pacing
```
Draft (10%):
- Lineup contest.
- Tactical intentions.

Early game (25%):
- Laning/development.
- Small skirmishes.

Midgame (35%):
- Resource contests.
- Teamfights erupt.

Late game (25%):
- Decisive confrontation.
- Victory and defeat become clear.

Post-match (5%):
- Review and conclusions.
- Emotional processing.
```

---

## 4. Classic Payoff Patterns

### Desperate Comeback
- **Scene**: Behind in score and facing elimination.
- **Payoff**: A sequence of outstanding protagonist plays reverses the match.
- **Key**: Build it up and show the pressure.

### Prodigy Showdown
- **Scene**: Two gifted players face each other.
- **Payoff**: Extraordinary play from both sides.
- **Key**: Give both players standout moments.

### Tactical Dominance
- **Scene**: A unique strategy defeats a formidable opponent.
- **Payoff**: Superior thinking leaves the opponent bewildered.
- **Key**: Tactics must be plausible and credible.

### Successful Revenge
- **Scene**: Face an opponent who previously defeated the protagonist.
- **Payoff**: Avenge the loss and demonstrate growth.
- **Key**: Establish the emotional stakes beforehand.

---

## 5. Outline Structure (Standard: 1.5 Million Chinese Characters)

### Volume One: Initiation (Chapters 1-60)
- **Core**: Show talent and join a team.
- **Status**: Substitute/academy player.
- **Climax**: A stunning first appearance.

### Volume Two: Growth (Chapters 61-150)
- **Core**: Become a starter and compete in the league.
- **Status**: Starting player.
- **Climax**: A strong league result.

### Volume Three: Rise (Chapters 151-280)
- **Core**: Become a star.
- **Status**: First-tier player.
- **Climax**: Win the league championship.

### Volume Four: Pinnacle (Chapters 281-400)
- **Core**: Challenge the world championship.
- **Status**: Elite player.
- **Climax**: Win the world title.

### Volume Five: Legend (Chapters 401-500)
- **Core**: Become legendary and retire after success.
- **Status**: Legendary player.
- **Climax**: Satisfying resolution.

---

## 6. Team Design

### Team Composition
| Character | Role | Personality | Function |
|------|------|------|------|
| Protagonist | Main carry | Growth-oriented | Carries at crucial moments |
| Captain | Shot-caller | Steady | Team anchor |
| Prodigy | Secondary carry | Proud | Second damage core |
| Veteran | Support | Composed | Passes on experience |
| Newcomer | Substitute | Passionate | Growth foil |

### Team Development
- **Early**: Weak/new team, finding chemistry.
- **Middle**: Mid-table league team, rising steadily.
- **Late**: Elite powerhouse competing for titles.

---

## 7. Match-Writing Techniques

### Description Essentials
- **Mechanical details**: Specific inputs/positioning.
- **Tactical interpretation**: Explain why a choice is made.
- **Inner thoughts**: What players are thinking.
- **Commentary viewpoint**: Third-party assessment.
- **Audience reactions**: Reinforce the atmosphere.

### Pacing Control
- **Routine matches**: Brief coverage emphasizing key points.
- **Important matches**: Detailed, progressive escalation.
- **Finals**: All-round coverage and emotional release.

---

## 8. Common Pitfalls

### Must Avoid
- ❌ Endless matches without characterization.
- ❌ Vague, unprofessional tactical descriptions.
- ❌ An invincible protagonist without challenges.
- ❌ Supporting characters reduced to tools.

### Recommended Practices
- ✅ Link matches to character growth.
- ✅ Make tactics informed and credible.
- ✅ Let the protagonist fail and grow.
- ✅ Give teammates independent personalities.

---

## 🛠️ Entity Tag Extensions

```xml
<entity type="competitor" name="Competitor name" desc="Characteristics" tier="level" position="Position" team="team" skill="Signature move"/>
<entity type="team" name="Team name" desc="Style" tier="level" rank="Ranking" roster="Lineup"/>
<entity type="match" name="Match name" desc="Competition format" tier="level" importance="Importance" result="Result"/>
<entity type="tactic" name="Tactic name" desc="Content" tier="level" counter="Counters" weakness="Weakness"/>
<entity type="hero/character" name="Character name" desc="Role" tier="level" skill="Skill" meta="Current-version strength"/>
```
