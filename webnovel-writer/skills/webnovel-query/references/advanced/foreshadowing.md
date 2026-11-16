---
name: foreshadowing
purpose: Load for foreshadowing urgency analysis and management
---

<context>
This is a foreshadowing-management reference. Claude already knows general narrative foreshadowing; this adds tiers, payoff cycles, and urgency calculations specific to web fiction.
</context>

<instructions>

## Foreshadowing tiers

| Tier | Payoff cycle | Weight | Examples |
|------|---------|------|------|
| **Core** | 50–300 chapters | 3.0x | Protagonist's origins, ultimate enemy, special ability's origin |
| **Subplot** | 30–100 chapters | 2.0x | Supporting character's motives, mysterious item, sect secrets |
| **Decorative** | 10–30 chapters | 1.0x | Scene details, small habits, a passerby's remark |

## Urgency calculation

```
Urgency = (elapsed chapters / target chapters) × tier weight
```

**Status rules**:
- 🔴 Critical: past target chapter OR core foreshadowing unresolved for >50 chapters
- 🟡 Warning: >80% of target OR subplot foreshadowing unresolved for >80 chapters
- 🟢 Normal: within the planned range

## Planting techniques

| Technique | Method | Example |
|------|------|------|
| Incidental mention | Mention in passing during normal plot | Reading a legend about the “Heaven-Devouring Demonic Art” in the library |
| Dialogue | Reveal through character conversation | “Your constitution is unusual...” |
| Detail | An inconspicuous detail | A ruined temple's statue is missing an arm |
| Dream | Hint at the future through dreams | Dreaming of a blood-red world and an indistinct figure |

## Payoff methods

| Method | Suitable depth | Effect |
|------|---------|------|
| Direct revelation | Shallow | Quick explanation |
| Layered revelation | Medium | Gradually reveal the truth |
| Unexpected reversal | Deep | Surprise and shock |

## Recommended density

| Work length | Shallow | Medium | Deep |
|---------|------|------|------|
| Short (100,000 English words) | 5–10 threads | 2–3 threads | 1 thread |
| Medium (500,000 characters) | 20–30 threads | 5–10 threads | 2–3 threads |
| Long (2 million+ characters) | 50+ threads | 20+ threads | 5–10 threads |

**Principle**: no more than five active foreshadowing threads at once.

## Avoid

- Planting without payoff (unfulfilled reader expectations)
- Forced explanations (obvious retroactive patches)
- Overly obvious hints (readers see through them immediately)
- Too many threads (readers cannot remember them)

</instructions>

<examples>

<example>
<input>Design foreshadowing for the protagonist's origins (core tier)</input>
<output>
**Plant in Chapter 1**: Protagonist's father mysteriously disappears
**Clue in Chapter 50**: Find a letter left by the father mentioning the Northern Region
**Clue in Chapter 100**: Find traces of the father in the Northern Region
**Payoff in Chapter 200**: Father appears; he had been sealing a demon god!

**Payoff method**: Layered revelation
**Planting techniques**: Dialogue (mother's dying words) + detail (father's jade pendant)
</output>
</example>

<example>
<input>Analyze foreshadowing urgency</input>
<output>
**Current chapter**: 80
**Foreshadowing F-001**: Mysterious jade pendant (core, target=50)
  Urgency = (80/50) × 3.0 = 4.8
  Status: 🔴 Critical (past target!)

**Foreshadowing F-002**: Junior sister's identity (subplot, target=100)
  Urgency = (80/100) × 2.0 = 1.6
  Status: 🟡 Warning (>80%)

**Foreshadowing F-003**: Ruined-temple detail (decorative, target=120)
  Urgency = (80/120) × 1.0 = 0.67
  Status: 🟢 Normal
</output>
</example>

<example>
<input>Design a subtle recurring thread</input>
<output>
**Chapter 10**: Protagonist meets an elderly beggar and gives him a pill
**Chapter 30**: Meets the old man again; he smiles without speaking
**Chapter 50**: At a crucial moment, the old man intervenes to save him
**Chapter 100**: Old man's identity revealed: an ancient powerhouse!

**Technique**: Leave a question at every appearance without explaining it directly.
</output>
</example>

</examples>

<errors>
❌ Planting without payoff (readers complain of abandoned threads) → ✅ Keep a foreshadowing checklist and pay it off regularly
❌ Forced explanations (strained connections) → ✅ The earlier the setup, the more convincing its payoff must be
❌ Overly obvious hints → ✅ Suggest subtly rather than stating directly
❌ 10+ simultaneous threads → ✅ No more than five active at once
❌ Core foreshadowing unresolved for >50 chapters → ✅ Check urgency and deliver timely payoff
</errors>
