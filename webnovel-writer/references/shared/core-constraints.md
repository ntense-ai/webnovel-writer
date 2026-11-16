---
name: core-constraints
purpose: Load before writing each chapter to enforce the three core laws
---

> **Primary skill**: `webnovel-write` Step 2
> **Secondary skill**: `webnovel-review` Step 2
> **Content layer**: Defect compensation (webnovel-specific anti-hallucination protocol)

<context>
This file checks core constraints during chapter creation. Claude already knows general writing conventions; this adds webnovel-specific anti-hallucination rules.
Note: This shared file is the single source of truth. Do not copy and modify it under individual skills' references. Make updates here.
</context>

<instructions>

## Three Core Laws (Low Discretion - Follow Exactly)

| Law | Rule | Check |
|------|------|----------|
| **The outline is law** | Follow the outline strictly; do not improvise beyond it | Compare against the outline in review |
| **The setting is physics** | Power/techniques/items ≤ index.db records | Query and confirm before writing |
| **Inventions must be identified** | Data Agent automatically extracts new entities | Process after completing the chapter |

## New Entity Workflow

Current rule: Prose no longer requires XML tags:

1. **While writing**: Write plain prose; describe new characters/places/items normally.
2. **After completion**: Data Agent identifies new entities and writes them to index.db.
3. **Uncertain entities**: Data Agent marks them uncertain for human confirmation.

## Chapter Constraint Layers

### Hard (Required)

- The chapter must be readable: readers can answer "what happened / who is doing what / why."
- It must make clear progress: at least one identifiable problem, goal, cost, relationship change, or information change.
- If the previous chapter made an explicit promise (hook/unresolved question), respond to it. Partial fulfillment is allowed; full settlement is not required.
- Never output placeholder prose (such as `[待补充]`, `[TODO]`, or `...（省略）...`).

### Soft (Recommended)

- Introduce conflict/risk/strong emotion early, preferably within the first 200-400 English words rather than a fixed 120.
- Put an unresolved question or next-chapter anticipation anchor near the end or in the later section, without requiring the final 80-150 characters.
- Give changes in the situation a rhythm: roughly one pulse per 800-1400 characters; short chapters need at least one substantive change.
- Follow genre-profile guidance for micro-payoff frequency rather than mechanical equal spacing.

### Style (Optional Reinforcement)

- Give dialogue intent (probing/avoidance/pressure/manipulation); reduce purely explanatory lines.
- Avoid consecutive long passages of pure explanation. If explanation is necessary, split it into "information + action/reaction."
- Avoid mechanical endings such as "they went back to rest." A quiet ending must retain unresolved anticipation.

### Anti-AI (Prevent During Writing)

- Do not use the same sentence structure for more than 3 consecutive paragraphs.
- Convey emotion through behavior/physiological cues, not direct labels ("he felt X").
- Include at least one rhythm change every 500 characters (a burst of short sentences, dialogue insertion, scene switch).
- Dialogue must contain conflicting intentions, not pure information transfer.
- No "safe landing" at chapter end: preserve at least one unresolved question or sense of unease.
- Remove generic adverbs (slowly/subtly/slightly) and replace them with concrete actions.

## Payoffs and Pacing (Adjust by Genre Profile)

- Genre and chapter type jointly determine payoff density. Transitional chapters may have low density, but must not deliver "no gains for the entire chapter."
- Assess combined and milestone payoffs over rolling windows (5 chapters / 10-15 chapters), as warnings rather than rigid per-chapter judgments.
- Three consecutive chapters with the same payoff type trigger a risk warning. Prefer type variations or differentiated execution to correct it.

## Strand Balance Warnings

| Plot strand | Warning condition |
|--------|----------|
| Quest (main plot) | 5+ consecutive chapters |
| Fire (relationships) | Absent for >10 chapters |
| Constellation (worldbuilding) | Absent for >15 chapters |

## Prohibitions

- `[待补充]`, `[TODO]`, `...（省略）...` → Write the content in full.
- Battles without aftermath descriptions (urban supernatural fiction).

</instructions>

<examples>

<example>
<input>The protagonist needs "Heavenly Thunder Palm" to defeat an enemy.</input>
<output>
1. Query index.db for the "Heavenly Thunder Palm" skill.
2. If present, use it directly.
3. If absent, describe how it was acquired (mentorship/insight/inheritance) in the prose. Data Agent will extract it automatically.
</output>
</example>

<example type="edge_case">
<input>The plot requires Foundation Establishment power, but index.db records the Qi Refining stage.</input>
<output>
❌ Write Foundation Establishment combat strength directly → Violates "the setting is physics."
✅ First include a breakthrough scene, let Data Agent update index.db, then show the new power.
</output>
</example>

</examples>

<errors>
❌ Vague new entities that cannot be identified automatically → ✅ Give new entities clear names and descriptions
❌ The protagonist suddenly knows a new skill → ✅ Describe its acquisition first
❌ Inconsistent power levels → ✅ Query index.db before writing
❌ No progression in an entire chapter (no goal/cost/change) → ✅ Add at least one identifiable form of progress
</errors>
