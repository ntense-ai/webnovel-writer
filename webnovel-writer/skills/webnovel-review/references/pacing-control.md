---
name: pacing-control
purpose: Load during pacing review to diagnose padding and sluggishness
---

<context>
This file supports pacing review and padding diagnosis. Claude already knows narrative pacing; this adds information-density standards and fast-paced techniques specific to web fiction.
</context>

<instructions>

## Information-density standards

**Core metric**: advance at least one substantive plot point per 1,000 Chinese characters.

A **substantive plot point** means:
- ✅ Protagonist gains new information/clue/ability
- ✅ Relationship changes (affection ±10, hostility ±10)
- ✅ Power gain/breakthrough/new technique
- ✅ Plot turn (new conflict/goal/crisis)
- ✅ Foreshadowing planted or paid off
- ❌ Pure scenery description (unless strongly plot-relevant)
- ❌ Repeated internal monologue
- ❌ Meaningless dialogue (greetings/pleasantries)

**Scoring standards**:

| Information density | Gratification beats | Ineffective content | Rating |
|---------|---------|---------|------|
| <800 characters/point | ≥2 | None | Excellent 90–100 |
| 800–1,000 characters/point | 1 | Very little | Good 70–89 |
| 1,000–1,500 characters/point | 1 | Some | Pass 50–69 |
| >1,500 characters/point | 0 | Substantial | Fail; rewrite needed |

## Fast vs. slow pacing

| Dimension | Slow (traditional novels) | Fast (web fiction) |
|------|--------------------|----------------|
| Cultivation | Three chapters describe training | Three paragraphs explain; breakthrough in the fourth |
| Setup | 5,000 characters establish antagonist | 500 characters, then direct conflict |
| Decision | Protagonist agonizes for two chapters | Two paragraphs of indecision, then immediate action |
| Adventure instance | Completed in 20 chapters | Completed in 5–8 chapters |

## Chapter-structure templates

**Standard chapter (3,000–5,000 Chinese characters)**:
```
Opening 300–500 characters: connect to previous chapter + establish scene
Setup 800–1,200 characters: introduce this chapter's core conflict
Development 1,000–1,500 characters: advance plot + prepare gratification
Climax 500–800 characters: chapter gratification erupts
Ending 300–500 characters: aftermath + suspense for next chapter
```

**Transition chapter (avoid padding)**:
```
Recap 200–300 characters: gains from the previous stage
New goal 500–700 characters: establish the next plan
Preparation 1,000–1,500 characters: prepare for the next arc
Minor conflict 500–800 characters: insert a small gratification beat (mandatory!)
Suspense 200–300 characters: introduce the next arc
```

## Genre-specific pacing standards

| Genre | Gratification density | Information density | Setup tolerance |
|------|---------|---------|-----------|
| Xuanhuan/cultivation | One major payoff every 5–8 chapters | 500–1,000 characters/point | Moderate |
| Urban power fantasy | One major payoff every 3–5 chapters | 400–800 characters/point | Low |
| Mystery/detective | One major payoff every 10–15 chapters | 600–1,200 characters/point | High |
| Zhihu short fiction | At least one small payoff/chapter | 300–500 characters/point | Extremely low |

</instructions>

<examples>

<example>
<input>Cultivation breakthrough chapter: original 1,200 characters, one plot point</input>
<output>
❌ **Padded version** (1,200 characters, one plot point):
Lin Tian sat cross-legged and began circulating his cultivation technique... (500 characters of detail)
Spiritual energy slowly entered his body... (300 characters describing the process)
Time passed second by second... (200 characters)
Finally, a breakthrough! (50 characters)
→ Information density = 1,200 characters/point → seriously sluggish

✅ **Condensed version** (90 characters in the Chinese original, three plot points):
Lin Tian sat cross-legged as the devouring system frantically absorbed the Heavenly Thunder Fruit's energy.
Six hours later: boom! Foundation Establishment, eighth level!
He opened his eyes and clenched a fist; the air cracked.
A cry came from outside: “A breakthrough in just three days?”
→ Information density = 30 characters/point → tight pacing
</output>
</example>

<example>
<input>Travel transition scene</input>
<output>
❌ **Padded version** (800 characters):
Lin Tian walked along the mountain path, looking at the trees... (300 characters of internal monologue)
He encountered a rabbit... (200 characters observing it)
Clouds drifted across the sky... (300 characters describing weather)

✅ **Condensed version** (80 characters in the Chinese original):
After three days' travel, Lin Tian finally reached the Bloodbane Secret Realm's entrance. As soon as he stepped inside, an aura of danger struck him.
</output>
</example>

<example>
<input>Detected 500 consecutive characters without plot advancement</input>
<output>
🔴 **Severe sluggishness flag**

Fix options:
A) Delete the passage
B) Condense it to 1–2 sentences
C) Insert micro-conflict (a passerby's provocation/an unexpected incident)
</output>
</example>

</examples>

<errors>
❌ Information density >1,500 characters/point → ✅ Compress or add plot points
❌ No gratification throughout chapter → ✅ Insert at least one small payoff
❌ Setup exceeds 2,000 characters without conflict → ✅ Accelerate immediately
❌ Transition chapter only transitions, with no conflict → ✅ Include a small payoff
❌ 500 consecutive characters of pure description → ✅ Delete or condense
</errors>
