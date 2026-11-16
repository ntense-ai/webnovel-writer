---
name: system-data-flow
purpose: Load during project initialization and status queries to understand data structures
---

<context>
This is a project data-structure reference. Claude already knows general file organization; this adds only directory conventions and script responsibilities specific to the webnovel workflow.
</context>

<instructions>

> ⚠️ This file describes `.webnovel/` projection-layer data structures and the early writing workflow to explain the read model during queries. Since v6.0.0, the post-writing main pipeline uses Story System (the `.story-system/` contract tree + accepted `CHAPTER_COMMIT`). Descriptions below of the dual-Agent architecture, per-chapter data pipeline, and direct Data Agent writes are historical; Story System is authoritative.

## Directory conventions

```
project-root/
├── 正文/           # Chapter files (第0001章.md or 第1卷/第001章-标题.md)
├── 大纲/           # Volume/chapter/scene outlines
├── 设定集/         # Worldbuilding/power systems/character sheets/item sheets
└── .webnovel/
    ├── state.json          # Slim state (< 5KB): progress/protagonist/strand_tracker/disambiguation
    ├── index.db            # Main SQLite storage: entities/aliases/relationships/state changes/chapters/scenes
    ├── workflow_state.json # Workflow checkpoints (legacy; v6 chapter-writing pipeline uses Story System chapter-commit)
    ├── vectors.db          # RAG vector database
    ├── summaries/          # Chapter summaries (chNNNN.md)
    └── archive/            # Archived data (inactive characters/resolved foreshadowing)
```

## Architecture changes

**Core change**: resolve state.json bloat (token explosion after 20 chapters)

| Data type | Previous storage | Current storage |
|----------|--------------|--------------|
| entities_v3 | state.json | **index.db** (entities table) |
| alias_index | state.json | **index.db** (aliases table) |
| state_changes | state.json | **index.db** (state_changes table) |
| structured_relationships | state.json | **index.db** (relationships table) |
| progress | state.json | state.json (retained) |
| protagonist_state | state.json | state.json (retained) |
| strand_tracker | state.json | state.json (retained) |
| disambiguation_* | state.json | state.json (retained) |

## Dual-Agent architecture

```
Before writing: Context Agent reads data → assembles context package
        ├── Read slim data from state.json (progress/configuration)
        └── Query index.db via SQL on demand (entities/relationships)

During writing: Writer uses the context package to generate plain prose (no XML tags)

After writing: Data Agent processes prose → AI extracts entities → writes data pipeline
        ├── Write index.db (entities/aliases/state changes/relationships)
        ├── Update state.json (progress/protagonist snapshot + chapter_meta)
        └── Write summaries/chNNNN.md (chapter summary)

Context Agent (reads) ←→ index.db + state.json ←→ Data Agent (writes)
```

## Script/module responsibility reference

### Core scripts

| Script | Input | Output |
|------|------|------|
| `init_project.py` | Project information | Generate `.webnovel/state.json` + initialize `index.db` |
| `update_state.py` | Arguments | Atomically update `state.json` fields (progress/protagonist/strand_tracker) |
| `backup_manager.py` | Chapter number | Automatic Git backup |
| `status_reporter.py` | None | Generate health report/foreshadowing urgency |
| `archive_manager.py` | None | Archive inactive data |
| `data_modules/migrate_state_to_sqlite.py` | Project path | Migrate old state.json to SQLite |

### data_modules modules

| Module | Responsibility |
|------|------|
| `state_manager.py` | Entity state management (slim state.json + SQLite synchronization) |
| `sql_state_manager.py` | SQLite state management (replaces JSON writes) |
| `index_manager.py` | SQLite index management (entities/aliases/relationships/state changes/chapters/scenes) |
| `entity_linker.py` | Alias registration and disambiguation |
| `rag_adapter.py` | Vector embedding and semantic retrieval |
| `style_sampler.py` | Style-sample extraction and management |
| `api_client.py` | LLM API call wrapper |
| `config.py` | Configuration management |

## Per-chapter data pipeline

```
1. Context Agent assembles the writing brief
   → Read state.json (slim: progress/configuration)
   → Query index.db with SQL (core/on-demand entities)
   → RAG retrieval (related scenes)

2. Step 1.5 Chapter design
   → Choose opening/hook/gratification patterns (avoid those in the last three chapters)

3. Writer generates chapter content
   → 2A Rough draft (plain prose)
   → 2B Style adaptation (optional)

4. Review (unified reviewer agent)
   → Five-dimensional checks: setting consistency/timeline/narrative continuity/character consistency/logic
   → Output review report

5. Polish for web-fiction style
   → Fix issues based on the review report
   → Strengthen readability and prose texture rules

6. Data Agent handles the data pipeline
   → AI entity extraction (replaces XML tag parsing)
   → Entity disambiguation (confidence policy)
   → Write index.db (entities/aliases/state changes/relationships)
   → Update state.json (progress/protagonist snapshot + chapter_meta)
   → Write summaries/chNNNN.md (chapter summary)
   → Vector embeddings (RAG)
   → Style-sample assessment

7. Git backup (mandatory)
```

> `update_state.py` manually/programmatically updates fields such as `progress`/`protagonist_state`/`strand_tracker`; normally Data Agent advances progress while processing the data pipeline.

## Slim state.json structure

```json
{
  "project_info": {"title": "", "genre": ""},
  "progress": {"current_chapter": N, "total_words": W, "current_volume": 1},
  "protagonist_state": {
    "name": "",
    "power": {"realm": "", "layer": 1, "bottleneck": ""},
    "location": {"current": "", "last_chapter": 0},
    "golden_finger": {"name": "", "level": 1, "skills": []}
  },
  "strand_tracker": {
    "last_quest_chapter": 0,
    "last_fire_chapter": 0,
    "last_constellation_chapter": 0,
    "current_dominant": "quest",
    "chapters_since_switch": 0,
    "history": []
  },
  "relationships": {},
  "plot_threads": {"active_threads": [], "foreshadowing": []},
  "world_settings": {},
  "disambiguation_warnings": [],
  "disambiguation_pending": [],
  "review_checkpoints": [],
  "chapter_meta": {},
  "_migrated_to_sqlite": true
}
```

> **Current structure**: entities_v3, alias_index, state_changes, and structured_relationships have moved to index.db and are no longer stored in state.json.

## index.db table schemas

```sql
-- Entities table
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,           -- Character/location/item/faction/move
    canonical_name TEXT NOT NULL,
    tier TEXT DEFAULT '装饰',     -- Core/important/secondary/decorative
    desc TEXT,
    current_json TEXT,            -- JSON: {realm, location, ...}
    first_appearance INTEGER,
    last_appearance INTEGER,
    is_protagonist INTEGER DEFAULT 0,
    is_archived INTEGER DEFAULT 0
);

-- Aliases table (one-to-many)
CREATE TABLE aliases (
    alias TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    PRIMARY KEY (alias, entity_id, entity_type)
);

-- State changes table
CREATE TABLE state_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    chapter INTEGER NOT NULL
);

-- Relationships table
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entity TEXT NOT NULL,
    to_entity TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    chapter INTEGER NOT NULL,
    UNIQUE(from_entity, to_entity, type)
);

-- Existing tables (retained)
CREATE TABLE chapters (...);
CREATE TABLE scenes (...);
CREATE TABLE appearances (...);
```

## Data Agent AI extraction procedure

The current main workflow no longer requires XML tags; Data Agent extracts intelligently:

1. **Entity recognition**: identify characters/locations/items/factions from prose semantics
2. **Entity matching**: prioritize existing entities (through alias_index)
3. **Disambiguation**:
   - Confidence > 0.8: accept automatically
   - Confidence 0.5–0.8: accept but record a warning
   - Confidence < 0.5: flag for human confirmation
4. **State-change recognition**: realm breakthroughs/location changes/relationship changes
5. **Persistence**: write directly to index.db (entities/aliases/relationships/state changes)

## Foreshadowing field specification

| Field | Canonical values | Compatibility values (historical) |
|------|--------|---------------|
| status | `未回收` / `已回收` | 待回收/进行中/active/pending |

**Recommended fields**: content, status, planted_chapter, target_chapter, tier

## alias_index format (one-to-many)

```json
{
  "林天": [{"type": "角色", "id": "lintian"}],
  "天云宗": [
    {"type": "地点", "id": "loc_tianyunzong"},
    {"type": "势力", "id": "faction_tianyunzong"}
  ]
}
```

One alias may map to multiple entities; disambiguate using type or context.

</instructions>

<examples>

<example>
<input>Query current progress</input>
<output>
```bash
cat "$PROJECT_ROOT/.webnovel/state.json" | jq '.progress'
# Output: { "current_chapter": 45, "total_words": 135000 }
```
</output>
</example>

<example>
<input>Query entities (SQL)</input>
<output>
```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "$PROJECT_ROOT" index get-entity --id "xiaoyan"
# Output: {"id": "xiaoyan", "type": "角色", "canonical_name": "萧炎", ...}

python "${SCRIPTS_DIR}/webnovel.py" --project-root "$PROJECT_ROOT" index get-core-entities
# Output: all core entities (protagonist + tier=核心/重要)
```
</output>
</example>

<example>
<input>Find entities by alias (one-to-many)</input>
<output>
```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "$PROJECT_ROOT" index get-by-alias --alias "天云宗"
# Output: [{"id": "loc_tianyunzong", "type": "地点"}, {"id": "faction_tianyunzong", "type": "势力"}]
```
</output>
</example>

<example>
<input>Query state changes</input>
<output>
```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "$PROJECT_ROOT" index get-state-changes --entity "xiaoyan" --limit 10
# Output: [{entity_id, field, old_value, new_value, reason, chapter}, ...]
```
</output>
</example>

<example>
<input>Query relationships</input>
<output>
```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "$PROJECT_ROOT" index get-relationships --entity "xiaoyan"
# Output: [{from_entity, to_entity, type, description, chapter}, ...]
```
</output>
</example>

<example>
<input>Check foreshadowing urgency</input>
<output>
```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "$PROJECT_ROOT" status -- --focus urgency
```
</output>
</example>

<example>
<input>Query entity appearances</input>
<output>
```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "$PROJECT_ROOT" index entity-appearances --entity "lintian"
```
</output>
</example>

<example>
<input>Migrate old state.json to SQLite</input>
<output>
```bash
python "${SCRIPTS_DIR}/webnovel.py" --project-root "$PROJECT_ROOT" migrate -- --backup
# Automatically back up state.json, migrate data to index.db, and slim state.json
```
</output>
</example>

</examples>

<errors>
❌ Foreshadowing status set to "待回收" → ✅ Use canonical "未回收"
❌ Manual update omits planted_chapter → ✅ Script fills it automatically
❌ Confusing archive paths → ✅ Fixed at `.webnovel/archive/*.json`
❌ Expecting a single alias_index object → ✅ Current structure uses arrays (one-to-many)
❌ Expecting XML tag extraction → ✅ Current main workflow uses automatic Data Agent AI extraction
❌ Using old data_modules.state_manager schema → ✅ Consistently use entities_v3 structure
❌ Still reading entities_v3 from state.json → ✅ Query index.db with SQL instead
❌ Still writing large data to state.json → ✅ Use incremental SQLite writes instead
❌ Letting state.json keep growing → ✅ Run the migration script: `python "${SCRIPTS_DIR}/webnovel.py" migrate`
</errors>
