---
name: polish-guide
purpose: Load during post-generation polishing to repair review issues and strengthen web-fiction readability
---

<context>
For Step 4 polishing: the goal is to fix problems, not rewrite the plot.

Inputs come from two sources:
1. Chapter prose (Step 2 output)
2. Review report (Step 3 aggregated results)

Responsibilities:
- Step 4 handles both style adaptation (remove formulaic, expository, mechanical voice) and issue repair.
- Includes review fixes, final Anti-AI checks, and avoidance of reader-alienating pitfalls.
</context>

<instructions>

## 1. Input contract

```json
{
  "chapter_file": "chapters/chapter-0123-title.md",
  "issues": [
    {"severity": "critical", "category": "setting", "location": "Paragraph 6", "description": "Realm overreach", "evidence": "A Dou Practitioner uses a Dou Master's skill", "fix_hint": "Use a skill available at the current realm", "blocking": true},
    {"severity": "high", "category": "character", "location": "Paragraph 9", "description": "Character voice mismatch", "evidence": "Xiao Yan uses formal written language", "fix_hint": "Use colloquial speech fitting the character"}
  ],
  "summary": "One blocker, one high-priority issue"
}
```

`chapter_file` must be the actual current chapter path; if the project has not migrated to titled filenames, `chapters/chapter-0123.md` is also allowed. See `review-schema.md` for issue format.

## 2. Execution order (must follow in order)

1. Fix review-report issues (`critical/high` first).
2. Validate web-fiction Hard/Soft/Style rules.
3. Perform Phase 1 final Anti-AI checks and rewrite.
4. Perform No-Poison checks for reader-alienating pitfalls.
5. Output polished results and deviations, if any.

## 2A. Anti-AI detection details (execution step 3)

> Word-frequency statistics are **reminders only**, no longer hard thresholds. Repair obvious excesses and briefly explain.
> Even though frequency is only a reminder, obvious AI-template traces in the final text still require `anti_ai_force_check=fail`.
> This section is an execution summary; use it together with the full seven-layer rules and vocabulary in the Phase 1 supplement below.

### Common AI traces

| Feature | Symptom |
|------|------|
| Uniform syntax | Similar sentence lengths and structures |
| Formulaic vocabulary | First, second, finally, notably |
| Excessive connectors | Heavy use of however, therefore, furthermore |
| Flat emotion | Lacks individualized emotional expression |
| Overdense information | Every sentence conveys information; no breathing room |

### Frequent-word reminders

| Type | Keywords (English glosses) |
|------|--------|
| Summaries | Overall / in conclusion / thus we see / all in all |
| Enumeration | First / second / finally / firstly / secondly / thirdly |
| Academic | In terms of / to some extent / essentially |
| Causal connectives | Because / so / due to / therefore |

---

## Naturalness standards (recommended)

| Metric | Below standard | Meets standard |
|-----|-------|------|
| Hesitation words | <0.5 per 500 English words | 1–2 per 500 |
| Uncertain expressions | None | ≥2/chapter |
| Short-sentence proportion | <20% | 30–50% |
| Colloquial expressions | None per 1,000 characters | ≥2 per 1,000 |

> **Note**: more naturalizing devices are not always better; excess feels forced.

### Mandatory execution protocol (new)

- Fully execute the seven-layer rules + vocabulary + final checklist; do not downgrade them to optional advice.
- Check the entire text paragraph by paragraph; no sampling.
- After Step 4, output `anti_ai_force_check: pass/fail`.
- If `fail`, remain in Step 4 and rewrite; do not enter Step 5.
- If a high-risk expression is retained because the plot needs it, record a `deviation` (location + reason + cost).

### Full-text scope (mandatory)

- Every paragraph of the chapter
- Every turn of dialogue
- Beginning, middle, and ending must all pass Anti-AI rules
- Rewrite every match or record a deviation

---

## Phase 1 supplement: Anti-AI rules (seven layers, original)

> Goal: reduce formulaic, expository, and mechanical voice.
> Principle: prioritize readability and believable characters, not mechanical word replacement.

### Layer 1: High-risk vocabulary (200+ terms, initial set)

These examples are diagnostic prompts, not a blacklist. Judge each phrase in context, preserving natural dialogue and the author's voice. For prose in another language, apply equivalent stylistic principles in that language.

#### A. Summary and conclusion
Overall; in conclusion; all in all; it follows that; as we can see; ultimately; in short; to sum up; in other words; broadly speaking; in the final analysis.

#### B. Enumeration templates
First; second; third; finally; on the one hand; on the other hand; additionally; moreover; next; the first point; the next step.

#### C. Formal or academic phrasing
To some extent; fundamentally; in terms of; on a conceptual level; is manifested in; constitutes; facilitates; provides; reflects; embodies; gives rise to; with respect to.

#### D. Overused logical connectives
Therefore; consequently; nevertheless; however; meanwhile; correspondingly; furthermore; as a result; in contrast; conversely; thus.

#### E. Direct emotion statements
He was extremely angry; she was filled with joy; he felt profound sadness; her emotions were complicated; he was deeply moved; she felt helpless; his heart sank; a wave of fear washed over her.

#### F. Stock action phrases
Frowned; sighed; took a deep breath; spoke slowly; said coldly; said softly; the corners of his mouth rose; her eyes narrowed; his gaze flickered; she froze; he stopped in his tracks; took half a step back; slowly nodded; shook her head.

#### G. Stock environmental phrases
The air seemed to freeze; tension filled the room; night was black as ink; the wind cut to the bone; deathly silence; time stood still; the room was filled with; the only source of light; silence fell like a wave; in that instant.

#### H. Narrative filler
In fact; actually; strictly speaking; objectively; generally speaking; under the circumstances; at this moment; on that basis; from a certain perspective; for him; this meant that; this showed that; it was no coincidence; undeniably.

#### I. Vague abstractions
Fate; growth; transformation; transcendence; value; meaning; determination; perseverance; belief; hope; despair; courage; justice; evil; truth; complexity; profundity. Ground abstractions in a specific action, choice, or consequence.

#### J. Mechanical openings and endings
Our story begins; let us turn our attention to; meanwhile, elsewhere; back to the present; little did he know; the wheels of fate began to turn; a new chapter began; to be continued; the real test was yet to come; a storm was brewing; this was only the beginning; only time would tell.

#### K. Stock facial expressions
A look flashed across her eyes; his pupils contracted; the corners of her mouth curved upward; his brow furrowed; her expression changed; his face darkened; she betrayed no emotion. Give characters distinctive reactions instead of repeating the same expressions.

#### L. Generic adverbs
Slowly; faintly; slightly; gently; quietly; silently; secretly; gradually. Remove unnecessary adverbs and convey pace or intensity through action and consequence.

#### M. Stock thought framing
He thought to himself; her heart tightened; he silently considered; she understood inwardly; a feeling rose in his heart; she secretly speculated; he made a mental calculation. Where useful, write the thought directly or externalize it through behavior.

#### N. Formulaic reversals
Be that as it may; at that very moment; but in the next instant; just as; little did they know; unfortunately; however, at that moment; just when everyone thought; even more surprisingly. Use concrete causes and consequences rather than announcing each twist.

### Layer 2: Sentence rules (anti-template)

- No three-part “first/second/finally” exposition.
- No three consecutive structurally identical subject + verb + object sentences.
- No checklist narration such as “He thought he needed to do three things: one, two, three”.
- Vary sentence length at least once every 3–5 paragraphs (short interruption/inserted action/rhetorical dialogue question).
- No cause → process → result → reflection closed loop; remove reflection and leave unresolved resonance.
- No triple emotion labels like “He felt X, also Y, and deep down a trace of Z”; show emotion through behavior.
- Do not end every paragraph/section with a summary (“thus we see”, “he finally understood”); end with action or dialogue.
- Do not establish and resolve the same conflict in one paragraph (standard suppression-release arc); span at least one scene or paragraph.
- Do not repeat the same information 2–3 times in different wording; say it once, accurately.
- Do not consecutively use escalation templates such as “more importantly”, “even more surprisingly”, “what concerned him most”.

### Layer 3: Adjective and adverb limits

- Rewrite by default when more than two consecutive adjectives modify one noun.
- Recommended total of intensifiers (very/extremely/particularly/etc.) is at most four per 300 English words.
- Prefer action + result + cost; reduce abstract evaluative words.

### Layer 4: Four-character clichés/idioms

- Do not densely stack empty four-character expressions (e.g. overlapping clichés about surging, mixed emotions).
- Recommended maximum: three stock four-character phrases per 500 characters, never consecutively.
- Idioms must serve narrative functions (advance information/conflict/character attitude).

### Layer 5: De-AI dialogue

- No manual-like dialogue (complete background explanations and overly full logic).
- Dialogue must have intention (probe/evade/pressure/lead/defend).
- Allow realistic pauses, interruptions, and counterquestions; avoid everyone using formal written language.
- No strict turn-taking; allow interruption, silence, or two consecutive lines by one speaker.
- No narrator explanation immediately after dialogue (“He said this because...”); let readers infer.
- Generic said tags (“X said”, “X said blandly”) must be no more than 30%; prefer preceding action (“He put down his chopsticks. ‘Not going.’”).
- Include subtext and discrepancies between speech and action; characters do not disclose everything they think.

### Layer 6: Paragraph structure

- Recommended single-sentence paragraph ratio: 25%–45% (higher in conflict chapters).
- Recommended paragraph length: 20–100 English words; avoid consecutive large explanatory blocks.
- Prefer action/sound/location changes for transitions rather than “Act One/Act Two” labels.

### Layer 7: Punctuation rhythm

- Do not repeatedly use `......` or `!!!`.
- At most one ellipsis and one exclamation mark per paragraph, except special emotional outbursts.
- Prefer splitting long sentences containing more than four commas.

### Anti-AI rewrite algorithm (actions)

1. Abstract emotional sentence → `physiological reaction + current intention + next action`
2. Conclusion → `concrete fact + cost/risk + decision`
3. Three or more consecutive explanatory sentences → mix dialogue/action/counterquestions
4. Three or more structurally identical sentences → break at least one into a short sentence or insert an action anchor
5. Dialogue paragraph explaining background → intention-driven confrontational dialogue
6. Emotion labels (“he felt X”) → physiology + micro-action + environmental reflection (“His hand shook; tea spilled across half the table”)
7. Instant emotional switch → transition (residue/aftertaste/hesitation: “He suppressed his anger, but his voice remained hoarse”)
8. Identical reactions across characters → tailor reactions to personality (experienced people restrain themselves, young people act impulsively, cautious people retreat and observe)

### Passing thresholds (manual judgment)

- No unhandled three-part enumeration templates remain anywhere.
- Every high-risk expression found has been rewritten or logged as a deviation.
- At least three abstract-to-behavioral sentence rewrites completed across the text.
- Ending contains perceptible next-step pressure or an unresolved question.
- Explain retained high-risk expressions in deviation.

### Phase 1 final checklist (original retained)

- [ ] High-risk vocabulary checked throughout and replaced as necessary.
- [ ] No three-part explanatory sentences (first/second/finally).
- [ ] Dialogue has genuine conflicting intentions, not information lectures.
- [ ] See section 5 for No-Poison red lines; this checklist covers only Anti-AI.
- [ ] Revisions preserve “settings are physics / outline is law”.

## 3. Review-issue repair priority

| Severity | Handling |
|---|---|
| critical | Must fix; if impossible, record deviation and reason |
| high | Prioritize repair; record deviation if impossible |
| medium | Handle according to space and benefit |
| low | Selectively address the most useful |

Repair actions by type:
- `OOC`: restore character speech, risk preferences, and decision boundaries.
- `POWER_CONFLICT`: return abilities to the legal realm, or establish acquisition route + cost.
- `TIMELINE_ISSUE`: add elapsed-time anchors.
- `LOCATION_ERROR`: add travel and spatial anchors.
- `PACING_IMBALANCE`: add missing progression events or remove redundant exposition.
- `CONTINUITY_BREAK`: add connecting sentences and transitional actions.

## 4. Layered web-fiction rules

### Hard (mandatory)

1. At least one clear advancement (information/action/relationship/situation).
2. Key dialogue has identifiable intention (at least probing/pressuring/evading/leading).
3. Replace abstract judgments with action/reaction/cost.

### Soft (recommended)

1. Enter conflict/risk/strong emotion within the first 200–400 English words.
2. Include a pacing pulse in the middle (roughly every 800–1,400 characters; at least once in short chapters).
3. Preserve an unresolved question or next-step anticipation anchor late or at the ending.

### Style (select by chapter type)

1. Avoid consecutive large blocks of pure exposition; prefer alternating information + action/reaction.
2. Calm endings are allowed, but not mechanical cutoffs.

## 5. No-Poison: five reader-alienating pitfalls

1. Plot-driven stupidity: characters ignore common sense merely to advance the story.
2. Forced misunderstanding: something explainable in one sentence is dragged out.
3. Cost-free saintliness: boundaryless forgiveness of high-risk people.
4. Tool-like supporting characters: appear only when needed, with no independent motives.
5. Double-standard judgments: similar behavior evaluated inconsistently without narrative explanation.

For any match, add at least two of motivation/resistance/cost.

## 6. Polishing red lines

- Do not change plot direction (outline is law).
- Do not change the setting's physical boundaries (settings are physics).
- Do not delete key foreshadowing.
- Do not forcibly rewrite baseline character relationships.

## 7. Output format (after polishing)

Required:
1. Polished chapter prose
2. Repair summary in this structure:

```text
[Polishing report]
- Critical issues fixed: N
- High-priority issues fixed: N
- Medium/low-priority issues fixed: N
- Anti-AI rewrites: N
- anti_ai_force_check: pass/fail
- Reader-alienation risk: pass/fail
- Deviations:
- {location}: {reason}
```

If any `critical` issues remain, explicitly mark “Failed” and return to Step 4 for further repair.

</instructions>

<examples>

<example>
<input>AI style: First, he needed evidence; second, he needed to steady his teammates; finally, he would counterattack publicly.</input>
<output>He secured the evidence, then turned to find his teammates. They had to hold steady before his counterattack could strike home.</output>
</example>

<example>
<input>AI style: He was very angry, filled with mixed emotions.</input>
<output>His knuckles whitened, a breath trapped in his throat. One more second and he would strike.</output>
</example>

</examples>

<errors>
❌ Skip critical/high issues and adjust style directly
✅ Clear issues first, then style

❌ Replace risky words without changing sentence-group structure
✅ Rewrite groups from abstract statements into behavior

❌ Change plot facts to remove AI flavor
✅ Change expression only, not event outcomes
</errors>

<checklist>
- [ ] `critical` fixed or deviation recorded
- [ ] `high` fixed or deviation recorded
- [ ] All Hard rules passed
- [ ] Full-text Phase 1 Anti-AI check passed
- [ ] `anti_ai_force_check=pass`
- [ ] All five No-Poison pitfalls checked
- [ ] No polishing red lines crossed
</checklist>
