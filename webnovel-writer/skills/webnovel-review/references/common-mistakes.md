---
name: common-mistakes
purpose: Quick self-check during quality review to identify common mistakes
---

<context>
This is a quick chapter-quality self-check. Claude already knows general writing mistakes; only common problems specific to web-fiction writing are listed here.
</context>

<instructions>

## Quick self-check

| Check | Passing standard | Consequence of violation |
|--------|----------|----------|
| Reasonable combat strength | Protagonist strength ≤ state.json | Breaks the power system |
| Gratification present | At least one gratification beat/chapter | Reader loss |
| Entity recognition | Data Agent can automatically extract new entities | Setting confusion |
| Character consistency | Dialogue/actions fit characterization | Immersion-breaking OOC |
| Balanced pacing | Not 5+ consecutive chapters on one Strand | Reader fatigue |
| Foreshadowing tracking | Foreshadowing can be recognized and recorded | Forgotten threads |

</instructions>

<examples>

<example>
<input>Error: protagonist at Foundation Establishment level 3 defeats a Golden Core enemy</input>
<output>
❌ **Broken power scaling**

✅ Fix: if fighting above one's level is necessary, provide:
- Special-ability/secret-technique enhancement
- An injured/weakened opponent
- Environmental advantage/trap assistance
</output>
</example>

<example>
<input>Error: protagonist travels for the entire chapter, with no conflict or gratification</input>
<output>
❌ **Missing gratification**

✅ Fix: during the journey, arrange:
- An incident (bandits/beasts/fortuitous encounter)
- A character encounter (companion/enemy/heroine)
- Discovery of a hidden location/treasure
</output>
</example>

<example>
<input>Error: “Purple Cloud Sect” suddenly appears but is absent from the setting collection</input>
<output>
❌ **Unauthorized invention**

✅ Fix:
- Ensure the new faction has a clear name and description.
- Data Agent will extract it automatically and ask whether to add it to the setting collection.
</output>
</example>

<example>
<input>Error: a “patient and composed” protagonist suddenly flies into an uncontrolled rage</input>
<output>
❌ **Out-of-character behavior**

✅ Fix:
- Refer to the character sheet's personality.
- A change needs setup (crossed red line/major provocation).
- Note the reason for the personality change.
</output>
</example>

<example>
<input>Error: every antagonist line is “You ant!” or “Know your place!”</input>
<output>
❌ **Stereotyped dialogue**

✅ Fix:
- Grade C antagonists may be stereotyped.
- Grade B and above need intelligence and individuality.
- Taunts should be natural and informative.
</output>
</example>

</examples>

<errors>
❌ Broken power scaling (unexplained instant wins above one's level) → ✅ Check state.json and set opponents appropriately
❌ Missing gratification (no conflict throughout chapter) → ✅ At least one gratification beat, even in transition chapters
❌ Unauthorized invention (vaguely described new entities) → ✅ Give new entities clear names and descriptions
❌ OOC behavior (sudden personality change without setup) → ✅ Refer to character sheets; set up changes
❌ Monotonous pacing (ten consecutive combat-only chapters) → ✅ Check strand_tracker and switch Strands
❌ Forgotten foreshadowing (unresolved for over 100 chapters) → ✅ Resolve core foreshadowing within 50 chapters
❌ Stereotyped dialogue (antagonists only shout slogans) → ✅ Grade B+ antagonists need intelligence
</errors>
