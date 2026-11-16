---
name: strand-weave-pattern
purpose: Check three-strand balance during chapter planning to avoid monotonous pacing
---

<context>
This file controls plot-strand balance. Claude already knows multi-strand narration; this adds webnovel-specific three-strand weaving and the tracker structure in state.json.
Note: This shared file is the single source of truth. Do not copy and modify it under individual skills' references. Make updates here.
</context>

<instructions>

## Three Strands and Their Proportions

| Strand | Share | Definition | Typical plot |
|------|------|------|----------|
| **Quest (main plot)** | 55-65% | Core tasks, advancement, battles, treasure hunts | Sect tournaments, hidden realms, cultivation breakthroughs, revenge and vindication |
| **Fire (relationships)** | 20-30% | Emotional relationships (romance/friendship/mentorship) | Meeting and attraction, heroic rescues, confirming a relationship |
| **Constellation (worldbuilding)** | 10-20% | Expanded settings, new factions/places, faction relationships, social networks | Hidden factions, new continents, the protagonist's origins |

## Weaving Rules (Low Discretion - Mandatory)

| Rule | Warning condition | Suggested action |
|------|----------|----------|
| No more than 5 consecutive Quest chapters | chapters_since_switch >= 5 | Switch to Fire or Constellation |
| Fire must not disappear for more than 10 chapters | current - last_fire > 10 | Add a relationship scene (affection/jealousy) |
| Constellation must not disappear for more than 15 chapters | current - last_constellation > 15 | Show new setting/faction/foreshadowing |

## strand_tracker Structure in state.json

```json
{
  "strand_tracker": {
    "last_quest_chapter": 45,
    "last_fire_chapter": 43,
    "last_constellation_chapter": 40,
    "current_dominant": "quest",
    "chapters_since_switch": 3,
    "history": [{"chapter": 46, "dominant": "quest"}, ...]
  }
}
```

Compatibility notes:
- `history[].dominant` is the current standard field (written by update_state.py).
- When legacy `history[].strand` data exists, map it to dominant when reading.

## Weaving Template for the First 30 Chapters

```
Chapters 1-5:   Quest ×5 (rapid opening main-plot progression)
Chapter 6:      Fire (first meeting with the heroine)
Chapters 7-10:  Quest ×4 (sect tournament)
Chapter 11:     Fire (heroic rescue)
Chapters 12-14: Quest ×3 (treasure hunt in a hidden realm)
Chapter 15:     Constellation (reveal the existence of a "sacred land")
Chapters 16-19: Quest ×4 (defeat a formidable enemy)
Chapter 20:     Fire (confirm the relationship)
Chapters 21-24: Quest ×4 (cultivation breakthrough)
Chapter 25:     Constellation (discover clues to the protagonist's origins)
Chapters 26-30: Quest ×5 (volume-ending climax)
```

</instructions>

<examples>

<example>
<input>Current chapter 46; last_quest=45, last_fire=43, last_constellation=40, current_dominant="quest", chapters_since_switch=3</input>
<output>
**Warning check**:
- Quest for 3 consecutive chapters < 5 → no warning yet
- 3 chapters since Fire < 10 → no warning yet
- 6 chapters since Constellation < 15 → no warning yet

**Chapter recommendation**: Quest may continue, but schedule Fire within the next 1-2 chapters to vary the pace.
</output>
</example>

<example>
<input>Current chapter 55; last_fire=42; no relationship strand for 13 chapters</input>
<output>
⚠️ **Warning**: More than 10 chapters since the last relationship strand!

**Recommendation**: Use Fire in this chapter.
- Option A: The heroine appears for a tender interaction.
- Option B: A heroic rescue scene.
- Option C: A small jealousy/misunderstanding episode.
</output>
</example>

<example type="edge_case">
<input>The first 10 chapters need to establish the main plot quickly. Can there be fewer relationship scenes?</input>
<output>
✅ Yes. Adjust the first 10 chapters to:
- Quest: 70-80%
- Fire: 10-15%
- Constellation: 5-10%

However, chapters 6-8 must include at least one Fire scene (first meeting/initial impression).
</output>
</example>

</examples>

<errors>
❌ 10 consecutive pure Quest chapters → ✅ Switch after at most 5
❌ No relationship strand for over 10 chapters → ✅ Include one every 5-10 chapters
❌ No worldbuilding strand for over 15 chapters → ✅ Show new setting elements every 10-15 chapters
❌ Forget strand_tracker after switching strands → ✅ Update automatically after each chapter
</errors>
