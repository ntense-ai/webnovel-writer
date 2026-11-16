# Context Agent Writing Brief Consolidation Design

> **Date**: 2026-04-14
> **Status**: Draft v1
> **Purpose**: Consolidate the pre-writing entry point and redefine the input boundaries of `context-agent` and `writer`

---

## 1. Document Purpose

### 1.1 Problems This Design Addresses

The current pre-writing pipeline has three problems:

1. `Step 0.5` and `context-agent` have overlapping responsibilities.
2. The existing creative package resembles an audit form rather than a commission an author would welcome.
3. `writer` still indirectly accesses too much raw material, so its input boundary has not truly narrowed.

This design does not introduce another working document. Instead, it will:

- Make `context-agent` the sole pre-writing assembly entry point.
- Keep the package assembled by current research as the **internal working document**.
- Generate a **writing brief** on top of it, exclusively for `writer`.

### 1.2 One-Sentence Conclusion

The mainline should become:

```text
context-agent
  -> research
  -> current task package (internal working document)
  -> writing brief
  -> writer
```

Here:

- The internal working document continues to serve the agent itself.
- `writer` receives only the writing brief.
- This is enforced **at the invocation layer**, not stated as an explicit constraint in the `writer` prompt.

---

## 2. Goals and Non-Goals

### 2.1 Goals

This change has exactly six goals:

1. Absorb `Step 0.5` into `context-agent`.
2. Keep the existing task package as the internal working document without inventing a new format.
3. Add the final writing brief artifact.
4. Narrow `writer` input to a single brief in practice.
5. Translate rigid rules into a natural commissioning voice.
6. Retain `anti-ai-guide.md` and `core-constraints.md` as pre-writing sources of truth.

### 2.2 Non-Goals

This design explicitly does not:

1. Redesign the `story_contract` schema.
2. Require showing contracts, checklists, or rule sources to `writer`.
3. Require a field-mapping table for the brief.
4. Split `anti-ai-guide.md` into CSV.
5. Pass every part of `core-constraints.md` to `writer`.

---

## 3. Core Principles

### 3.1 Enforce Isolation, Rather Than Stating It

The invocation layer must ensure `writer` reads only the brief.

Do not put statements like these in the `writer` prompt:

- “You may only read the brief.”
- “Do not read other material.”
- “The contract is located elsewhere.”

The reason is simple:

- If the boundary needs emphasis in the prompt, it has not actually been established in orchestration.
- If `writer` still lacks information, investigate the quality of the brief rather than expanding its access.

### 3.2 A Writing Brief Should Read Like a Commission, Not a Manual

The text shown to `writer` should no longer consist of:

- Contract clauses
- Checklists
- Flat lists of prohibitions
- Audit-style field expansions

Instead, it should sound like a creative partner explaining the chapter:

- What to write
- Who is present
- What will happen
- What feeling to capture
- Where to end

### 3.3 Prefer Semantic Generation Over Rigid Mapping Tables

`context-agent` should generate the brief semantically from the internal working document.

This means:

- No mapping table saying “field A must go in paragraph B.”
- Specify only what the brief must make clear.
- Do not mandate a fixed field order for mechanical assembly.

### 3.4 Retain General Guidelines in Full; Naturalize the Final Wording

`anti-ai-guide.md` and `core-constraints.md` remain pre-writing sources of truth.

When incorporated into the final brief, they must be rewritten in a natural voice.

The body must not contain:

- `Anti-AI`
- “check”
- “constraint”
- “contract”
- `blocking_rules`
- File names or paths

---

## 4. Two-Layer Structure

### 4.1 Internal Working Document

Do not introduce a new data structure. Reuse the task package currently assembled through `context-agent` research.

It continues to include:

- Chapter outline
- Previous-story summaries
- `story_contract`
- Latest accepted `CHAPTER_COMMIT`
- `plot_structure`
- `prewrite_validation`
- `reader_signal`
- `genre_profile`
- `writing_guidance`
- `long_term_memory`
- Other research results as needed

Before generating the brief, `context-agent` must also read these in full:

- `references/shared/core-constraints.md`
- `skills/webnovel-write/references/anti-ai-guide.md`

Both feed the internal working document but must not appear verbatim in the final brief.

### 4.2 Writing Brief

The writing brief is the sole input to `writer`.

It retains only information directly useful for drafting, rewritten in a commissioning voice.

It does not expose:

- Sources
- File names
- Contract hierarchy
- Validation procedures
- Data-processing procedures

---

## 5. What Must Stay Out of CSV

### 5.1 Explicit Exclusions

Keep these as Markdown or template-layer assets:

1. `anti-ai-guide.md`
2. Global processes and general guidelines in `core-constraints.md`
3. The writing brief template itself
4. The role boundaries of `context-agent` / `writer`
5. Complete style-anchor passages

The reasons are the same:

- These are not on-demand retrieval entries.
- Retrieving a few matching items is not enough.
- Their order, tone, and overall structure are themselves information.

### 5.2 Content That Can Still Move Into CSV

These remain suitable for further structuring:

1. Genre-specific payoff types
2. Genre-specific pacing risks
3. Scene-specific writing redirections
4. Genre-specific reader turn-offs and pitfalls
5. Reusable plot-progression techniques

In other words:

- General writing operating guidelines stay out of CSV.
- Genre-specific, scene-specific, retrievable knowledge continues to move into CSV.

---

## 6. Handling `core-constraints` and `anti-ai-guide`

### 6.1 `anti-ai-guide.md`

The fixed rules are:

1. Read it in full.
2. Do not split it into CSV.
3. Do not pass it verbatim to `writer`.
4. Convert it only into natural reminders within the brief.

### 6.2 `core-constraints.md`

The fixed rules are:

1. Read it in full.
2. Do not pass it verbatim to `writer`.
3. Extract only the parts that directly affect drafting this chapter.

These should generally not enter the final brief:

- Data Agent
- `index.db`
- New-entity processing procedures
- Paths, commands, and system processes
- Background rules relevant only to system operation

### 6.3 Final Presentation

In the final brief, both sources may appear only as wording such as:

- “Move the people and events forward first in this chapter; do not rush to explain.”
- “Let emotion come through actions and reactions rather than spelling it all out immediately.”
- “Do not settle everything at the end; leave something not quite resolved.”

Not:

- “Execute Anti-AI rule 3.”
- “Follow the three laws.”
- “Check blocking rules.”

---

## 7. Fixed Writing Brief Structure

The final brief has five sections.

### 7.1 Opening Commission

First clarify the book, chapter, and one-sentence objective for this chapter.

For example:

- You are writing chapter 12, “Chapter Title,” of *Book Title*.
- This chapter is mainly about…
- The focus is not… but…

### 7.2 This Chapter’s Story

Explain:

- Who needs to do what
- Why they must do it
- What makes it truly difficult
- How the situation will progress

### 7.3 This Chapter’s Characters

Include only character information directly useful for drafting:

- Current state
- Immediate motivation
- Main role in this chapter
- Speech and action tendencies

### 7.4 How to Make This Chapter Flow

This section incorporates:

- Pacing reminders
- Emotional expression
- Dialogue approach
- Reference atmosphere
- Style anchors
- Natural reminders translated from `anti-ai-guide` and `core-constraints`

This is the most important part of the entire brief.

### 7.5 Where This Chapter Ends

Describe only the feeling on which the ending should stop:

- An action
- An image
- A line of dialogue
- A sense of incompletion

Do not resolve everything.

---

## 8. Language Requirements

The writing brief must use:

1. Concise Chinese
2. Short sentences where possible
3. An unpretentious voice
4. No lecturing
5. No institutional tone
6. No exposed system terminology

Recommended voice:

- Like a co-author who understands creative writing
- Like someone explaining how to make the chapter flow better
- Like a commission, not an operating manual

---

## 9. Workflow Changes

### 9.1 New Workflow

The pre-writing mainline becomes:

```text
Step 1: context-agent
  -> research
  -> generate internal working document
  -> generate writing brief

Step 2: writer
  -> receive only the writing brief
  -> draft the chapter directly
```

### 9.2 Handling `Step 0.5`

All existing `Step 0.5` responsibilities should return to `context-agent`.

No longer allow:

- Some information to be prepared by `context-agent`
- Other information to be supplied by `writer` itself
- Other reminders to be assembled ad hoc during writing

### 9.3 Failure Semantics

If `writer`, while reading only the brief, still shows:

- Insufficient information
- Incorrect emotional tone
- Unclear conflict
- Stiff pacing

First conclude that:

- The brief produced by `context-agent` is not good enough.

Do not respond by giving `writer` more access to raw material.

---

## 10. Acceptance Criteria

After the change, at minimum:

1. `context-agent` is the sole pre-writing assembly entry point.
2. The existing task package remains the internal working document.
3. The final input to `writer` is a single writing brief.
4. The brief body contains no terms such as “constraint / check / contract / Anti-AI.”
5. The brief reads like a commission, not a policy document.
6. The full `anti-ai-guide.md` still participates in generation without being exposed verbatim.
7. The full `core-constraints.md` still participates in generation, with only drafting-relevant content translated into the brief.

---

## 11. Implementation Recommendations

Recommended implementation order:

1. Update the responsibility description for `context-agent`.
2. Update the brief-generation template.
3. Remove the duplicated responsibilities of `Step 0.5`.
4. Finally, restrict `writer` input to the brief alone.

Do not start by changing the contract schema or expanding CSV.

Consolidating the pre-writing entry point and final wording first offers the greatest benefit with the least risk.
