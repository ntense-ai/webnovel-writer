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
  "chapter_file": "正文/第0123章-章节标题.md",
  "issues": [
    {"severity": "critical", "category": "setting", "location": "Paragraph 6", "description": "Realm overreach", "evidence": "A Dou Practitioner uses a Dou Master's skill", "fix_hint": "Use a skill available at the current realm", "blocking": true},
    {"severity": "high", "category": "character", "location": "Paragraph 9", "description": "Character voice mismatch", "evidence": "Xiao Yan uses formal written language", "fix_hint": "Use colloquial speech fitting the character"}
  ],
  "summary": "One blocker, one high-priority issue"
}
```

`chapter_file` must be the actual current chapter path; if the project has not migrated to titled filenames, `正文/第0123章.md` is also allowed. See `review-schema.md` for issue format.

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
| Hesitation words | <0.5 per 500 Chinese characters | 1–2 per 500 |
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

The exact Chinese detection terms below are retained intentionally: these are functional matching vocabulary for Chinese prose, not untranslated instructions. Category headings and guidance are in English.

#### A. Summary/conclusion terms（22）

综合、总之、总而言之、由此可见、可以看出、不难发现、归根结底、说到底、总体来看、从这个角度看、换句话说、简而言之、概括来说、可以说、由此得出、结论是、最终可知、总的来说、总括起来、整体而言、总体上、综上。

#### B. Enumeration templates（24）

首先、其次、再次、最后、第一、第二、第三、其一、其二、其三、一方面、另一方面、再者、此外、另外、同时、接着、然后、随后、紧接着、最后一步、下一步、第一点、第二点。

#### C. Formal/academic phrasing（24）

某种程度上、本质上、意义上、维度上、层面上、在于、体现为、构成了、形成了、实现了、完成了、进行了、展开了、推动了、促进了、提供了、具备了、拥有了、达成了、呈现出、表现出、反映出、蕴含着、折射出。

#### D. Overused logical connectives（22）

因此、因而、所以、由于、然而、不过、但是、与此同时、同样地、对应地、相应地、进一步、更进一步、从而、进而、于是、结果是、于是乎、故而、由此、相较之下、反过来说。

#### E. Direct emotion statements（22）

非常愤怒、非常开心、非常难过、心中五味杂陈、百感交集、情绪复杂、内心震撼、不由得感慨、感到无奈、感到痛苦、感到欣慰、感到恐惧、深受触动、心潮起伏、心情沉重、心情复杂、心里一暖、心里一沉、心中一紧、不禁一愣、不由一怔、内心一震。

#### F. Stock action phrases（22）

皱起眉头、叹了口气、深吸一口气、缓缓开口、沉声说道、淡淡说道、冷冷说道、轻声说道、嘴角上扬、嘴角抽了抽、眼神一凝、目光一闪、身形一滞、脚步一顿、浑身一震、心头一跳、不由后退半步、猛地转身、抬手一挥、缓缓点头、轻轻摇头、下意识后退。

#### G. Stock environmental phrases（22）

空气仿佛凝固、气氛骤然紧张、气压陡然下降、夜色如墨、月色如水、寒风刺骨、四周一片寂静、死一般的寂静、时间仿佛静止、空间仿佛扭曲、房间里弥漫着、唯一的光源、摇摇欲坠、压抑得让人喘不过气、沉默像潮水、空气中充满了、一切都显得、世界仿佛、就在这一刻、忽然之间、刹那间、顷刻之间。

#### H. Narrative filler（22）

事实上、实际上、某种意义上、严格来说、客观而言、主观上、一般来说、通常情况下、在这种情况下、在这个时候、在此基础上、在这个意义上、从某种角度、对于他来说、对她而言、这意味着、这说明、这代表着、这并不奇怪、并非偶然、不可否认、毋庸置疑。

#### I. Vague abstractions（22）

命运、成长、蜕变、升华、价值、意义、抉择、坚持、信念、初心、希望、绝望、勇气、正义、邪恶、真实、虚伪、复杂、深刻、宏大、渺小、沉重。

#### J. Mechanical opening/ending phrases（24）

故事要从、让我们把视线、镜头转到、与此同时在另一边、回到现在、再说回、这一切都要从、他并不知道、命运的齿轮开始转动、新的篇章开始了、未完待续、故事才刚刚开始、真正的考验还在后面、一场风暴即将来临、更大的阴谋正在酝酿、这只是开始、答案尚未揭晓、未来会怎样、谁也不知道、他深知、她明白、可他不知道的是、可她不知道的是、然而一切才刚开始。

#### K. Expression templates（15）

眸中闪过、眼底掠过、瞳孔微缩、嘴角微微上扬、嘴角勾起一抹弧度、眉头微蹙、眉心微皱、面色微变、神色一凝、目光微闪、眼神微动、唇角微翘、脸色微沉、面色如常、不露声色。

> Trait: AI gives every character the same expression templates. Instead, design distinctive micro-actions for each character (biting a pen cap = anxiety; twisting a watch = impatience).

#### L. Generic adverbs（10）

缓缓、淡淡、微微、轻轻、静静、默默、悄悄、慢慢、渐渐、暗暗。

> Trait: AI puts these adverbs before almost every action, creating a fixed adverb + verb pattern (speaking slowly, speaking blandly, nodding slightly, sighing gently). Remove the adverb; imply speed/intensity through preceding action or results.

#### M. Stock internal-monologue phrases（10）

心中暗道、心中一凛、心中暗自思量、心下了然、心中不由得、心底涌起一股、心中升起一丝、暗自盘算、暗自揣测、心中有了计较。

> Instead, remove the thought-framing phrase and write the thought directly or externalize it (clenched fist = determination; unconsciously touching chin = thought).

#### N. Reversal/escalation templates（9）

话虽如此、就在此刻、然而下一刻、正当……之际、殊不知、可惜的是、然而就在这时、就在众人以为……的时候、更令人惊讶的是。

> Trait: AI uses these formulas to manufacture a sense of reversal, but readers recognize the coming turn as soon as they see them, eliminating suspense.

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
- Recommended total of intensifiers (very/extremely/particularly/etc.) is at most four per 300 Chinese characters.
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
- Recommended paragraph length: 20–100 Chinese characters; avoid consecutive large explanatory blocks.
- Prefer action/sound/location changes for transitions rather than “Act One/Act Two” labels.

### Layer 7: Punctuation rhythm

- Do not repeatedly use `......` or `！！！`.
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

1. Enter conflict/risk/strong emotion within the first 200–400 Chinese characters.
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
  - {位置}: {原因}
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
