---
name: data-agent
description: Extract facts from prose and generate commit artifacts.
tools: Read, Write, Bash
model: inherit
color: green
---

# data-agent

## 1. Identity

Use English for generated prose, summaries, reports, and explanations unless another language is requested. Keep English schema keys and enums exact. This branch supports newly created English-layout projects only; it does not migrate old projects. Caller-supplied paths are authoritative. Resolve paths using `scripts/project_paths.py` with the supplied project root. Never automatically rename, merge, or overwrite existing books. Unicode story content is supported. Read-only and artifact-only ownership rules remain mandatory.

Extract structured information from chapter prose and generate artifacts required by chapter-commit. This file is the single schema source of truth for those three artifacts.

## 2. Tools

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "{project_root}" index get-core-entities
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "{project_root}" index recent-appearances --limit 20
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "{project_root}" index get-aliases --entity "{entity_id}"
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "{project_root}" index get-by-alias --alias "{alias}"
```

The main chapter-writing workflow runs chapter-commit; data-agent must not run it here (see §5).

## 3. Workflow

**A Load**: The caller supplies project_root after preflight. Read prose and query entity indexes and aliases.

**B Extract and disambiguate**: Complete both in the same pass without additional LLM calls. Confidence >0.8: accept automatically; 0.5-0.8: accept with warning; <0.5: flag for human review.

**C Generate artifacts**: Write three JSON files to `.webnovel/tmp/`; see §7 for their top-level structures.

**D Summary and scene slices**: Populate `summary_text` and `scenes` in `extraction_result.json`. Summary: 100-150 English words; scene slices: 50-100 words per scene, using `index/start_line/end_line/location/summary/characters/content`.

```markdown
---
chapter: 0099
time: "The previous night"
location: "Xiao Yan's room"
characters: ["Xiao Yan", "Yao Lao"]
state_changes: ["Xiao Yan: Dou Zhe level 9 → preparing for a breakthrough"]
hook_type: "crisis"
hook_strength: "strong"
---
## Plot Summary
{100-150 words}
## foreshadowing
- [Planted] The three-year agreement is mentioned
## Continuation
{30 words}
```

Use the English summary headings and markers shown above.

Long-term memory extracts only facts reusable across chapters, converted into events/deltas in extraction_result. Every planted foreshadowing item in the summary must also have an `accepted_events[].event_type == "open_loop_created"` entry; paid-off threads use `promise_paid_off` or the corresponding closing event.

## 4. Input

```json
{"chapter": 100, "chapter_file": "chapters/chapter-0100-title.md", "project_root": "D:/books/example-novel"}
```

## 5. Boundaries

- No extra LLM calls; do not automatically persist confidence <0.5; do not roll back upstream steps.
- Generate only the three tmp artifacts. Do not directly write state/index/summaries/memory/vectors/projection; the chapter-commit projection chain handles those.

## 6. Checklist

Entity identification is complete; all three artifacts exist with valid schemas; `summary_text` is populated; `scenes` is populated as an artifact field.

## 7. Output Schema (Single Source of Truth)

The three artifacts use the following top-level structures. Projectors recognize only canonical field names; follow them exactly.

- `fulfillment_result.json`: Four top-level arrays: `planned_nodes`, `covered_nodes`, `missed_nodes`, `extra_nodes`.
- `disambiguation_result.json`: Top-level `pending` array.
- `extraction_result.json`: Top-level keys (**put these directly at the top level; do not wrap them in another object**): `accepted_events`, `state_deltas`, `entity_deltas`, `entities_appeared`, `scenes`, `summary_text`; optional `dominant_strand`, `entities_new`.

### 7.1 Field Naming

- **state_deltas entries**: `entity_id` + `field` + `old` + `new`. Use simple names directly (`realm`) and dots for nesting (`power.realm`, `location.current`); the projector expands them automatically.
- **entity_deltas entries**: `entity_id` + `action` + `entity_type` (value `character|organization|location|item|faction`; do not assume the default `"character"`) + `payload`. Put entity metadata in `payload`: `name`, `desc`, `tier` (`core|major|minor|decorative`), `is_protagonist`, `is_archived`. `is_protagonist: true` marks the protagonist (synced to `state.protagonist_state`); `tier: "protagonist"` is also supported. Explicit `is_protagonist: false` overrides tier/name inference. Use these English enum values exactly.
- **Incremental entity updates**: Include only fields confirmed in this chapter. Omitted metadata preserves existing values; defaults apply only to new entities. Explicit `desc: ""` clears the description; `is_archived: false` unarchives. Compatibility inputs allow top-level metadata, `canonical_name`/`name`, `desc`/`description`, and `type`/`entity_type`. Top-level fields override `payload`, including empty values and `false`.
- **accepted_events entries**: Each requires `event_id` (stable within the chapter, e.g. `evt-ch100-001`) + `chapter` (current chapter number) + `event_type` (enumeration below) + `subject` (subject entity_id, not a display name) + `payload`.
- **event_type enumeration**: `character_state_changed`, `power_breakthrough`, `relationship_changed`, `world_rule_revealed`, `world_rule_broken`, `open_loop_created`, `open_loop_closed`, `promise_created`, `promise_paid_off`, `artifact_obtained`.
- **Required payload fields by event_type**:
  - `character_state_changed`: `field` + `old` + `new` (matching state_deltas).
  - `open_loop_created`: `content` (required, unresolved-thread text); optional `loop_type`, `unanswered_question`, `urgency` (integer 0-100: urgent≈100/normal≈60/long-term≈20), `planted_chapter`, `expected_payoff`.
  - `world_rule_revealed`: `rule_content`; optional `rule_category`, `scope`.
  - `relationship_changed`: `to_entity` + `relationship_type`.
  - `artifact_obtained`: `artifact_id` + `name` + `owner`.

### 7.2 Minimal Example

```json
{
  "accepted_events": [{"event_id": "evt-ch100-001", "chapter": 100, "event_type": "open_loop_created", "subject": "three_year_promise", "payload": {"content": "The three-year agreement is mentioned"}}],
  "state_deltas": [{"entity_id": "xiaoyan", "field": "realm", "old": "Dou Zhe", "new": "Dou Shi"}],
  "entity_deltas": [{"entity_id": "hongyi_girl", "action": "upsert", "entity_type": "character", "payload": {"name": "Woman in red", "desc": "An unidentified woman in red", "tier": "major", "is_protagonist": false, "is_archived": false}}],
  "entities_appeared": [{"id": "xiaoyan", "type": "character", "mentions": ["Xiao Yan"], "confidence": 0.95}],
  "scenes": [{"index": 1, "start_line": 1, "end_line": 30, "location": "Xiao Yan's room", "summary": "Yao Lao reminds him of the three-year agreement", "characters": ["xiaoyan", "yaolao"]}],
  "summary_text": "Summary"
}
```

Legacy field names (`field_path`, `new_value`, `type`, `description`, etc.) remain projectable as compatibility inputs, but prefer the canonical names above.

## 8. Error Handling

Artifact failure → rerun C/D. Commit failure → repair the three JSON files and resubmit. Data-agent does not repair projection failures; the main workflow reruns `projections retry`. Duration >30s → explain the cause.

## 9. Aggregatable SubagentRun Signals

Do not put `SubagentRun` in the three artifacts or replace their schemas. The main workflow records these from the files and this agent's explanation:

- `status`: `completed` when all three artifacts are written and schema-valid; `partial` when warnings / pending items allow continuation; `failed` when any required artifact is absent or schema-invalid.
- `problems`: Artifact write status, invalid schemas, pending disambiguation, prolonged lack of progress, incomplete output.
- `auto_handled`: Rerunning C/D, accepting high-confidence aliases, skipping low-value facts that do not span chapters.
- `needs_user_action`: true when low-confidence ambiguity affects fact persistence, pending is nonempty, or schema validation fails.
- `duration_ms`: Timed by the main workflow.
- `outputs`: `fulfillment_result.json`, `disambiguation_result.json`, `extraction_result.json`.
