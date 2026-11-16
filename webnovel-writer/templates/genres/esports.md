# Esports Fiction Template

> Runtime preset identifier: `esports` (English taxonomy and initialization preset).

> **Core appeal**: Comebacks against the odds + competitive pressure + team growth. Match outcomes drive fast pacing and continued readership.

---

## Recommended Creative Constraints (Optional)
- Recommended constraint pack: Pack M12
- General overlay: Pack U01

## 1. Core Subgenres

### Professional League
- **Features**: Progression from youth academy to minor league to top league.
- **Core payoffs**: Recovering from losing streaks, decisive-game comebacks, legendary MVP performances.
- **Best for**: Long serialization and ensemble teams.

### Prodigy Rookie
- **Features**: A gifted newcomer challenges established powerhouses.
- **Core payoffs**: Stunning debuts, dominating lane opponents, reversing public opinion.
- **Best for**: Male-oriented power fantasy and fast-paced chapters.

### Tactical Coach
- **Features**: Drafts, tactical contests, and data analysis take center stage.
- **Core payoffs**: Underdog victories, unconventional formations, live shot-calling.
- **Best for**: Strategic battles and hardcore spectators.

### Retirement Comeback
- **Features**: Returning after injury/suspension/mental collapse.
- **Core payoffs**: Returning from desperation, rematches with rivals, championship redemption.
- **Best for**: Strong emotional threads and character arcs.

---

## 2. Worldbuilding: Competition System

### League Structure
| Tier | Description | Common conflicts |
|------|------|----------|
| Youth academy | Developing newcomers | Selection cuts, unequal resources |
| Minor league | Stepping stone to promotion | Promotion/relegation, sponsor pressure |
| Top league | Highest domestic stage | Powerful teams targeting contenders, do-or-die playoffs |
| International events | Peak competition | Regional rivalries, different understandings of the patch |

### Team Roles
- **Main carry**: High risk and high reward; delivers damage.
- **Tempo role**: Controls the map and initiates fights, influencing the overall pace.
- **Shot-caller**: Makes decisions and adapts in real time, determining key rounds.
- **Support**: Allocates resources and protects teammates, stabilizing the team's baseline.

---

## 3. Classic Payoff Patterns

### Reverse Sweep
- **Scene**: Down 0:2, with morale on the verge of collapse.
- **Payoff**: Tactical adjustments succeed and the team wins three straight games.
- **Key**: Each comeback needs a clear rationale; do not force victories.

### Rival Matchup
- **Scene**: The protagonist faces an old teammate/rival directly.
- **Payoff**: Dominating the matchup, iconic plays, and explosive post-match discussion.
- **Key**: Establish the shared history beforehand.

### Coach Breaks the Deadlock
- **Scene**: Opponents counter the usual strategy and leave the team trapped.
- **Payoff**: An on-the-fly formation change or surprise strategy wins.
- **Key**: Tactical explanations should be understandable without becoming verbose.

### Championship Moment
- **Scene**: The deciding game of the grand final.
- **Payoff**: A decisive teamfight and individual performance pushed to the limit.
- **Key**: Victory's costs must feel real: injuries, psychological pressure, team sacrifices.

---

## 4. Outline Structure (Reference: 2 Million Chinese Characters)

### Volume One: Entering the Game (Chapters 1-80)
- **Core**: Enter the professional system and establish the team's first goal.
- **Climax**: First crucial win.

### Volume Two: Finding Chemistry (Chapters 81-180)
- **Core**: Internal conflict and tactical adjustment.
- **Climax**: An iconic reverse sweep.

### Volume Three: Breaking Through (Chapters 181-320)
- **Core**: Enter the top league as public pressure increases.
- **Climax**: Comeback against a rival.

### Volume Four: Reaching the Summit (Chapters 321-520)
- **Core**: Fight on both playoff and international fronts.
- **Climax**: Win the championship in the deciding game.

### Volume Five: A New Dynasty (Chapters 521-700)
- **Core**: Defend the title, rebuild, and train newcomers.
- **Climax**: Pass on the legacy and bring the story full circle.

---

## 5. Common Pitfalls

### Must Avoid
- ❌ Reporting only match results without the strategic contest.
- ❌ Characters shouting slogans without concrete tactical execution.
- ❌ Long winning streaks with no cost.
- ❌ Completely omitting post-match public opinion and business realities.

### Recommended Practices
- ✅ Explain at least one key decision in every match.
- ✅ Let information, execution, and mentality jointly determine results.
- ✅ Victories have costs; defeats have specific consequences.
- ✅ Build a complete emotional chain before, during, and after each match.

---

## 🛠️ Entity Tag Extensions

```xml
<entity type="team" name="Team name" desc="Style" tier="level" coach="Coach" captain="Captain"/>
<entity type="competitor" name="Competitor name" desc="Role" tier="level" role="Position" style="Playstyle"/>
<entity type="competitive-event" name="Competition name" desc="Competition format" tier="level" stage="Stage" stakes="Stakes"/>
<entity type="tactic" name="Tactic name" desc="Core approach" tier="level" counter="Counter relationships" risk="Risk"/>
```
