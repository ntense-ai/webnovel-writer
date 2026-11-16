# Typesetting and reading experience (mobile first)

> **Purpose**: make scrolling through the story smoother on phone screens, preventing readers from dropping it because of paragraph, dialogue, or punctuation problems.

---

## 1. Paragraph rules (most important)

- **One action/information unit per paragraph**: each paragraph has one function (advance/show/emotion/information).
- **Keep paragraphs manageable**: prioritize splitting paragraphs longer than five consecutive lines into 2–3 paragraphs, especially exposition.
- **Use “fast paragraphs” at climaxes**: short sentences and paragraphs during climaxes/combat/chases improve speed and impact.
- **Use “slow paragraphs” for setup**: slightly longer paragraphs are acceptable, but each must add information rather than merely pile on descriptions.

---

## 2. Dialogue formatting (default standard)

- **One speaker's line per paragraph**: start a new paragraph when the speaker changes; do not pack 3–4 lines from multiple speakers into one paragraph.
- **Interleave dialogue and action**: actions, expressions, and environment cues identify speakers and control pacing.
- **Avoid “who is speaking?” confusion**: in multi-character scenes, add an explicit speaker or action anchor every 2–3 lines.

**Recommended example**:
```markdown
“Are you sure you want to go in?” Li Xue lowered her voice.

Lin Tian looked toward the cave mouth, black mist churning within. His throat moved. “If I don't, the answer will always stay out of reach.”

“Then don't die.” She pressed a jade talisman into his palm.
```

---

## 3. Punctuation and readability

- **Limit strings of ellipses/exclamation marks**: do not repeatedly use combinations like `……！！！` within one chapter.
- **Avoid essay-like explanations**: avoid formulaic structures such as “first/second/in conclusion/therefore we can see”.
- **Use consistent proper nouns**: standardize character/faction/realm/skill names (record in `设定集/`; accepted `CHAPTER_COMMIT` later projects them into index/state/memory).

---

## 4. Scene transitions and chapter structure

- **Give scene cuts breathing room**: leave a blank line before and after transitions; use `---` when necessary.
- **Make important information visible**: place key settings/clues/turns near paragraph beginnings or endings so readers need not scroll half a screen to find the point.
- **Include an anticipation anchor late in the chapter**: a question/threat/promise/reversal suffices; avoid mechanical endings like “went home to sleep”.

---

## 5. Ten-point pre-publication check

1. Does dialogue start a new paragraph for each new speaker?
2. Are there paragraphs over five lines that could be split?
3. Does one paragraph mix dialogue from multiple characters that could be separated?
4. Are there excessive explanatory paragraphs using a summarizing/listing voice?
5. Are proper nouns consistent with `设定集/`?
6. Is any “???/placeholder prose” exposed to readers?
7. Are scene transitions clear (blank lines/separators/transitional sentences)?
8. Is there at least one clear advancement (information/action/turn) in the chapter?
9. Is there an ending hook?
10. Are new entities clearly introduced (name/identity/memorable trait)? For optional manual annotation, use hidden XML tags (see `${CLAUDE_PLUGIN_ROOT}/skills/webnovel-query/references/tag-specification.md`).
