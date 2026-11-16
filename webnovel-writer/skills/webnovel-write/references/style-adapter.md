## Role
Step 4 style-adaptation reference: rewrite chapter prose in web-fiction style and remove AI traces.

**Chinese-first principle**: all rewrite explanations, rewrite logs, and change summaries in this step must use Simplified Chinese. Retain English only for immutable machine identifiers such as CLI flags, checker IDs, and JSON keys.

**Responsibilities**: style conversion + AI-trace removal: sentence restructuring, abstract-to-concrete conversion, web-fiction readability, and replacement of generic adverbs/expression templates.

## Inputs
- Rough chapter draft (Step 2A output)
- Chapter type (combat/dialogue/transition/breakthrough)
- Hook requirements (type + strength)

## Outputs
- Web-fiction-style chapter prose (length within ±10%)
- Rewrite log (record major adjustments)

Default length target:
- Standard chapters default to 2,000–2,500 Chinese characters unless the outline or user specifies otherwise.

## Forbidden changes (red lines)
- ❌ Plot direction
- ❌ Event order
- ❌ Results of character actions
- ❌ Setting/ability descriptions
- ❌ Foreshadowing content

## Hard constraints (mandatory)
- ✅ Split long sentences (>40 Chinese characters); avoid consecutive long sentences that burden reading
- ✅ Abstract judgments → actions/reactions/costs
- ✅ Remove summarizing narration and large blocks of pure explanation
- ✅ At least one clear advancement per chapter (information/action/relationship/situation)

## Soft recommendations (prioritize)
- ✅ Enter conflict/risk/strong emotion early (preferably within the first 200–400 characters)
- ✅ Place an unresolved question/anticipation anchor late or at the ending (no fixed character-count window)
- ✅ Arrange 1–3 micro-payoffs according to chapter type, not mechanical equal spacing
- ✅ Prefer one measurable change per chapter (status/resources/relationships/risk)
- ✅ Prefer choice/crisis hooks, but switch according to genre
- ✅ Maintain conflicting intentions in dialogue; reduce empty pleasantries

## Genre-specific style weighting (new)
- **Xuanhuan/cultivation/high-martial**: emphasize actions and results; defer terminology explanations.
- **Urban/livestream/esports**: faster information pacing; strengthen feedback–reaction–counteraction chains.
- **Romance/substitute-lover/melodrama**: foreground emotional arcs; key scenes must shift relationships.
- **Mystery/rules horror/cosmic horror**: clues must support later payoff; fear comes from rules, not piled-up adjectives.

## Quick AI-trace replacements (new)
- Replace “He was very angry” with a three-part expression: action + physiology + decision.
- Replace “In conclusion/one could say” with direct concluding action, not meta-narration.
- If three consecutive sentences share a structure, turn at least one into a short, forceful sentence.
- Generic adverb replacement: “said slowly” → remove the adverb and lead with action (“He set down the cup. ‘No.’”).
- Expression-template replacement: “a trace of X flashed in her eyes” → individualized micro-action (“She unconsciously twisted her cuff”).
- Said-tag replacement: “X said blandly” → action-led dialogue (“He didn't look up. ‘Suit yourself.’”); said tags must account for no more than 30% throughout.
- Inner-monologue cliché replacement: “he thought to himself” → write the thought directly and remove the framing phrase.

## Checkpoints (validate after rewriting)
| Check | Standard | On failure |
|--------|------|-----------|
| Opening conflict | Prefer conflict/risk/strong emotion within 200–400 characters | Add a conflict lead-in |
| Anticipation anchor | Unresolved question/motive for next chapter late or at ending | Add an unresolved question |
| Micro-payoff pacing | 1–3 micro-payoffs, not mechanically equidistant | Merge or rearrange payoffs |
| Long-sentence ratio | Sentences >40 characters are <10% | Split long sentences |
| Exposition | No consecutive block of pure explanation >200 characters | Break up or remove |

## Chapter-type adaptation (by outline, not length)
- **Standard progression chapter (default 2,000–2,500 characters)**: apply all hard constraints and prioritize soft recommendations.
- **Transition chapter (determined by outline)**:
  - Conflict lead-in may extend to the first 400 characters.
  - Micro-payoffs may drop to 0–1, but at least one clear advancement is still required.
  - Anticipation-anchor strength may be weak.
  - Transition status is determined by chapter/volume outline, never by a length threshold.
