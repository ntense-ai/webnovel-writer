---
name: tag-specification
purpose: XML tag format reference
---

<context>
This file is an XML tag format reference.

**Current conventions**:
- XML tags are **no longer required** when writing chapters.
- Data Agent automatically extracts entities from plain chapter prose and writes them to index.db.
- Tags are only for **manual annotation** (e.g. explicitly marking important entities or supplementing missed extractions).
- If you choose to use tags, follow the specification below.
</context>

<instructions>

## Tag overview

| Tag | Purpose | Required attributes |
|------|------|----------|
| `<entity>` | Create/automatically update entities (characters/locations/items/factions/moves) | type, name |
| `<entity-alias>` | Register entity aliases/titles | id/ref, alias |
| `<entity-update>` | Update entity attributes (set/unset/add/remove/inc + history tracking) | id/ref, `<set>`, etc. |
| `<skill>` | Special-ability skill | name, level, desc, cooldown |
| `<foreshadow>` | Plant foreshadowing | content, tier |
| `<relationship>` | Character relationship | char1, char2, type |
| `<deviation>` | Mark outline deviation | reason |

## Attribute details

### tier (importance tier)
- **核心** (core): affects the main plot; must track.
- **支线** (subplot): enriches the plot; should track.
- **装饰** (decorative): adds realism; tracking optional.

### type (entity type)
Runtime values: 角色 / 地点 / 物品 / 势力 / 招式 (character / location / item / faction / move).

### id / ref (entity reference)
- **id (recommended)**: stable unique identifier (facilitates later updates/alias additions).
- **ref**: reference by a previously used name/alias (automatically resolved through index.db's aliases table).
- **type (optional)**: disambiguate an ambiguous ref (e.g. different people with the same name); if ambiguity remains, use `id`.

### `<entity-update>` suboperations
- **set**: `<set key="k" value="v" reason="optional"/>`
- **unset**: `<unset key="k" reason="optional"/>`
- **add**: `<add key="k" value="v" reason="optional"/>` (append to an array, automatically deduplicated)
- **remove**: `<remove key="k" value="v" reason="optional"/>` (remove from an array)
- **inc**: `<inc key="k" delta="1" reason="optional"/>` (numeric increment, default +1)

**Top-level field allowlist** (update the entity's top level directly rather than current): `tier`, `desc`, `canonical_name`, `importance`, `status`, `parent`

> **Recommendation**: strongly prefer including `desc` and `tier` in `<entity>`; otherwise later retrieval and consistency checks will be less effective.

## Placement rules

- **Recommended**: group at the end of the chapter (easier management).
- **Allowed**: at the end of the paragraph where the entity first appears.
- **Required**: tags occupy their own lines; do not insert into prose sentences.

### Hidden form (recommended)

```markdown
Chapter prose...

<!--
<entity type="角色" id="luchen" name="Lu Chen" desc="Protagonist, awakened spacetime abilities" tier="核心"/>
<entity-alias id="luchen" alias="Captain Lu" context="After joining the special task force"/>
<entity-update id="luchen"><set key="realm" value="F-rank Awakened" reason="Awakening completed"/></entity-update>
<skill name="Time Rewind" level="1" desc="Return ten seconds into the past" cooldown="24 hours"/>
<foreshadow content="The mysterious elder's jade pendant" tier="核心" target="50"/>
<relationship char1_id="luchen" char2_id="liwe" type="ally" intensity="60" desc="Initial cooperation"/>
-->
```

</instructions>

<examples>

<example>
<input>Mark new characters</input>
<output>
```xml
<entity type="角色" id="luchen" name="Lu Chen" desc="Protagonist, university student with awakened spacetime abilities" tier="核心"/>
<entity type="角色" id="liwe" name="Li Wei" desc="Heroine, campus beauty with a mysterious background" tier="核心"/>
<entity type="角色" name="Cafe owner" desc="Apparently ordinary but concealing great ability" tier="装饰"/>
```
</output>
</example>

<example>
<input>Register new titles/aliases</input>
<output>
```xml
<entity-alias id="luchen" alias="Captain Lu" context="After joining the special task force"/>
<entity-alias ref="Lu Chen" alias="The Heir" context="After the system confirms his identity"/>
```
</output>
</example>

<example>
<input>Update entity attributes (realm/location/status/affiliation, etc.)</input>
<output>
```xml
<entity-update id="luchen">
  <set key="realm" value="E-rank Controller" reason="Breakthrough during a crisis"/>
  <set key="location" value="Abandoned laboratory in western city"/>
</entity-update>
```
</output>
</example>

<example>
<input>Mark new skills</input>
<output>
```xml
<skill name="Time Rewind" level="1" desc="Return to the state ten seconds earlier" cooldown="24 hours"/>
<skill name="Spatial Anchor" level="2" desc="Set a teleportation anchor and instantly return" cooldown="1 hour"/>
<skill name="Temporal Sense" level="1" desc="Passive skill; foresee danger within three seconds" cooldown="None"/>
```
</output>
</example>

<example>
<input>Plant foreshadowing</input>
<output>
```xml
<foreshadow content="The jade pendant left by the mysterious elder starts glowing" tier="核心" target="50" location="Abandoned laboratory"/>
<foreshadow content="The strange tattoo on Li Wei's wrist" tier="支线" target="30" characters="Li Wei,Lu Chen"/>
<foreshadow content="The cafe owner's meaningful look" tier="装饰"/>
```
</output>
</example>

<example>
<input>Mark outline deviations</input>
<output>
```xml
<deviation reason="Spontaneous inspiration: add emotional interaction between Li Wei and Lu Chen to set up the later romance"/>
<deviation reason="Breakthrough originally planned for this chapter, but pacing is too fast; postpone to the next chapter"/>
```
</output>
</example>

</examples>

<errors>
❌ `<entity type='角色' .../>` → ✅ Use double quotes `type="角色"`
❌ `<entity type="角色" ...>` → ✅ Self-close with `.../>` or add `</entity>`
❌ `<Entity type="角色" .../>` → ✅ Lowercase tag name `<entity`
❌ `[NEW_ENTITY: character, Lu Chen, ...]` → ✅ Use XML format
❌ `<entity-update ref="xxx"></entity-update>` → ✅ Include at least one `<set key="..." value="..."/>`
</errors>
