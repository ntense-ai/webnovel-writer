# Webnovel Writer System Architecture Diagrams

> Historical design record: project-directory examples retain their original names. New projects use `chapters/`, `outlines/`, `settings/`, and `reviews/`; existing legacy projects remain supported without renaming. Resolve actual paths with `scripts/project_paths.py` before using these examples.

> Generated: 2026-04-15
> Scope: read/write relationships across the complete init → plan → write pipeline

## Overall Pipeline

```mermaid
graph TB
    subgraph USER["User"]
        U_INPUT["User input"]
    end

    subgraph INIT["/webnovel-init（Project initialization）"]
        INIT_COLLECT["Step 1-7: Interactive collection"]
        INIT_GEN["Run generation"]
        INIT_STORY["story-system initialization"]
    end

    subgraph PLAN["/webnovel-plan（Outline planning）"]
        PLAN_LOAD["Step 1: Load data"]
        PLAN_SETTING["Step 2: Complete settings"]
        PLAN_VOLUME["Step 3-6: Volume planning"]
        PLAN_CHAPTER["Step 7: Break down chapter outlines"]
        PLAN_WRITEBACK["Step 8: Write settings back"]
        PLAN_STORY["story-system refresh"]
    end

    subgraph WRITE["/webnovel-write（Chapter-writing workflow）"]
        W_PREFLIGHT["Preparation: preflight"]
        W_STORY["Preparation: story-system refresh contract tree"]
        W_STEP1["Step 1: context-agent"]
        W_STEP2["Step 2: Draft prose"]
        W_STEP3["Step 3: reviewer assessment"]
        W_STEP4["Step 4: Polishing"]
        W_STEP5["Step 5: data-agent + commit"]
        W_STEP6["Step 6: Git backup"]
    end

    U_INPUT --> INIT_COLLECT
    INIT_COLLECT --> INIT_GEN --> INIT_STORY
    INIT_STORY --> PLAN_LOAD
    PLAN_LOAD --> PLAN_SETTING --> PLAN_VOLUME --> PLAN_CHAPTER --> PLAN_WRITEBACK
    PLAN_CHAPTER --> PLAN_STORY
    PLAN_STORY --> W_PREFLIGHT
    W_PREFLIGHT --> W_STORY --> W_STEP1 --> W_STEP2 --> W_STEP3 --> W_STEP4 --> W_STEP5 --> W_STEP6
```

## Init Read/Write Flow

```mermaid
graph LR
    subgraph INIT["/webnovel-init"]
        I1["Interactive collection (7 steps)"]
        I2["init_project.py"]
        I3["Patch master outline"]
        I4["story-system CLI"]
    end

    subgraph STORE_INIT["Output files"]
        S_STATE["state.json"]
        S_SETTING["设定集/*.md"]
        S_OUTLINE["大纲/总纲.md"]
        S_IDEA["idea_bank.json"]
        S_MASTER["MASTER_SETTING.json"]
        S_ANTI["anti_patterns.json"]
    end

    subgraph REF_INIT["Reference inputs"]
        R_GENRE_TROPES["genre-tropes.md"]
        R_GENRE_PROFILE["genre-profiles.md"]
        R_WORLD["worldbuilding/*.md"]
        R_CREATIVE["creativity/*.md"]
        R_CSV_NAME["命名规则.csv"]
    end

    R_GENRE_TROPES -->|"Read"| I1
    R_GENRE_PROFILE -->|"Read"| I1
    R_WORLD -->|"Read (as needed)"| I1
    R_CREATIVE -->|"Read (as needed)"| I1
    R_CSV_NAME -->|"reference_search (naming)"| I1

    I1 --> I2
    I2 -->|"Write"| S_STATE
    I2 -->|"Write"| S_SETTING
    I2 -->|"Write"| S_OUTLINE
    I1 --> I3
    I3 -->|"Write"| S_OUTLINE
    I1 -->|"Write"| S_IDEA

    I2 --> I4
    S_STATE -->|"Read genre"| I4
    I4 -->|"Write"| S_MASTER
    I4 -->|"Write"| S_ANTI

    subgraph CSV_ENGINE["story-system engine"]
        CSV_ROUTE["题材与调性推理.csv (routing)"]
        CSV_REASON["裁决规则.csv (adjudication)"]
        CSV_BASE["5 base tables (naming/characters/techniques/settings/scenes)"]
        CSV_DYN["2 dynamic tables (plot beats/payoffs)"]
    end

    CSV_ROUTE -->|"Read (route matching)"| I4
    CSV_REASON -->|"Read (adjudication matching)"| I4
    CSV_BASE -->|"Read (BM25 retrieval)"| I4
    CSV_DYN -->|"Read (BM25 retrieval)"| I4
```

## Plan Read/Write Flow

```mermaid
graph LR
    subgraph PLAN["/webnovel-plan"]
        P1["Step 1: Load"]
        P2["Step 2: Complete settings"]
        P3["Step 4-5: Beat sheet + timeline"]
        P4["Step 6: Volume outline"]
        P5["Step 7: Break down chapter outlines"]
        P6["Step 8: Write settings back"]
        P7["story-system"]
    end

    subgraph READ_PLAN["Inputs"]
        R_STATE2["state.json"]
        R_OUTLINE2["大纲/总纲.md"]
        R_SETTING2["设定集/*.md"]
        R_IDEA2["idea_bank.json"]
        R_SUMMARY["summaries/ (between volumes)"]
        R_KNOWLEDGE["knowledge query (between volumes)"]
        R_LOOPS["memory-contract get-open-loops (between volumes)"]
        R_MASTER2["MASTER_SETTING.json"]
    end

    subgraph WRITE_PLAN["Outputs"]
        W_BEAT["大纲/第X卷-节拍表.md"]
        W_TIMELINE["大纲/第X卷-时间线.md"]
        W_DETAIL["大纲/第X卷-详细大纲.md"]
        W_SETTING2["设定集/*.md (incremental)"]
        W_VOLUME["volumes/volume_NNN.json"]
        W_CHAP_CONTRACT["chapters/chapter_NNN.json"]
        W_REVIEW_CONTRACT["reviews/chapter_NNN.review.json"]
    end

    subgraph REF_PLAN["References"]
        R_GP["genre-profiles.md"]
        R_STRAND["strand-weave-pattern.md"]
        R_COOL["cool-points-guide.md"]
        R_CSV_PLAN["CSV retrieval (scenes/naming)"]
    end

    R_STATE2 -->|"Read"| P1
    R_OUTLINE2 -->|"Read"| P1
    R_SETTING2 -->|"Read"| P1
    R_IDEA2 -->|"Read (as needed)"| P1
    R_SUMMARY -->|"Read (between volumes)"| P1
    R_KNOWLEDGE -->|"Bash (between volumes)"| P1
    R_LOOPS -->|"Bash (between volumes)"| P1
    R_MASTER2 -->|"Read (tone reference)"| P4

    P2 -->|"Write (incremental)"| W_SETTING2
    P3 -->|"Write"| W_BEAT
    P3 -->|"Write"| W_TIMELINE
    P4 --> P5
    P5 -->|"Write"| W_DETAIL

    R_GP -->|"Read"| P4
    R_STRAND -->|"Read"| P4
    R_COOL -->|"Read (as needed)"| P4
    R_CSV_PLAN -->|"Bash (retrieval)"| P4

    P6 -->|"Write (incremental)"| W_SETTING2

    P5 --> P7
    R_STATE2 -->|"Read genre"| P7
    P7 -->|"Write"| W_VOLUME
    P7 -->|"Write"| W_CHAP_CONTRACT
    P7 -->|"Write"| W_REVIEW_CONTRACT
```

## Write Read/Write Flow (Core Pipeline)

```mermaid
graph TB
    subgraph PREP["Preparation"]
        PRE1["preflight + where"]
        PRE2["story-system CLI"]
    end

    subgraph STEP1["Step 1: context-agent (subagent)"]
        CA_LOAD["load-context"]
        CA_READ["Read original chapter outline"]
        CA_QUERY["query-entity / query-rules as needed"]
        CA_OUT["Output: writing brief"]
    end

    subgraph STEP2["Step 2: Draft prose"]
        S2_WRITE["Write prose"]
        S2_CSV["reference_search (as needed)"]
    end

    subgraph STEP3["Step 3: reviewer (subagent)"]
        REV_READ["Read prose"]
        REV_CONTRACT["Read review contract"]
        REV_OUT["Write review_results.json"]
        REV_PIPE["review-pipeline --save-metrics"]
    end

    subgraph STEP4["Step 4: Polishing"]
        S4_REF["Read polish-guide / typesetting / style-adapter"]
        S4_EDIT["Edit prose"]
    end

    subgraph STEP5["Step 5: data-agent + commit"]
        DA_READ["Read prose"]
        DA_ENTITY["Bash: get-core-entities / recent-appearances"]
        DA_ARTIFACTS["Write 4 artifacts"]
        COMMIT["chapter-commit CLI"]
        PROJ["projection writers x5"]
    end

    subgraph STEP6["Step 6: Git"]
        GIT["git add + commit"]
    end

    %% Data stores
    subgraph STORES["Data stores"]
        ST_STATE["state.json (state)"]
        ST_INDEX["index.db (entities/relationships)"]
        ST_SUMMARY["summaries/chNNNN.md (summaries)"]
        ST_MEMORY["memory_scratchpad.json (memory)"]
        ST_VECTOR["vector_db (vector index)"]
        ST_COMMIT["commits/chapter_NNN.commit.json (post-writing source of truth)"]
        ST_CHAPTER["正文/第NNNN章.md"]
        ST_TMP["tmp/*.json (intermediate artifacts)"]
    end

    subgraph CONTRACTS["Contract tree (.story-system/)"]
        CT_MASTER["MASTER_SETTING.json"]
        CT_VOLUME["volumes/volume_NNN.json"]
        CT_CHAPTER["chapters/chapter_NNN.json"]
        CT_REVIEW["reviews/chapter_NNN.review.json"]
        CT_ANTI["anti_patterns.json"]
    end

    subgraph OUTLINE["Outline"]
        OL_DETAIL["大纲/第X卷-详细大纲.md"]
    end

    subgraph CSV["CSV knowledge layer"]
        CSV_R["题材与调性推理.csv (routing)"]
        CSV_J["裁决规则.csv (adjudication)"]
        CSV_ALL["7 base + dynamic tables"]
    end

    subgraph REFS["Polishing references"]
        REF_POLISH["polish-guide.md"]
        REF_TYPE["typesetting.md"]
        REF_STYLE["style-adapter.md"]
    end

    %% Preparation
    ST_STATE -->|"Read genre"| PRE2
    CSV_R -->|"Read (routing)"| PRE2
    CSV_J -->|"Read (adjudication)"| PRE2
    CSV_ALL -->|"Read (BM25)"| PRE2
    PRE2 -->|"Write"| CT_MASTER
    PRE2 -->|"Write"| CT_VOLUME
    PRE2 -->|"Write"| CT_CHAPTER
    PRE2 -->|"Write"| CT_REVIEW
    PRE2 -->|"Write"| CT_ANTI

    %% Step 1
    PRE2 --> CA_LOAD
    CA_LOAD -->|"Bash: load-context"| ST_STATE
    CA_LOAD -.->|"includes contracts"| CT_MASTER
    CA_LOAD -.->|"includes summaries"| ST_SUMMARY
    CA_LOAD -.->|"includes protagonist"| ST_STATE
    CA_LOAD -.->|"includes loops"| ST_STATE
    CA_READ -->|"Read"| OL_DETAIL
    CA_QUERY -->|"Bash (as needed)"| ST_INDEX
    CA_OUT -->|"Output brief"| STEP2

    %% Step 2
    S2_CSV -->|"Bash: reference_search"| CSV_ALL
    S2_WRITE -->|"Write"| ST_CHAPTER

    %% Step 3
    REV_READ -->|"Read"| ST_CHAPTER
    REV_CONTRACT -->|"Read"| CT_REVIEW
    REV_OUT -->|"Write"| ST_TMP
    REV_PIPE -->|"Bash + Write index.db"| ST_INDEX

    %% Step 4
    S4_REF -->|"Read"| REF_POLISH
    S4_REF -->|"Read"| REF_TYPE
    S4_REF -->|"Read"| REF_STYLE
    S4_EDIT -->|"Edit"| ST_CHAPTER

    %% Step 5
    DA_READ -->|"Read"| ST_CHAPTER
    DA_ENTITY -->|"Bash"| ST_INDEX
    DA_ARTIFACTS -->|"Write x4"| ST_TMP
    ST_TMP -->|"Read artifacts"| COMMIT
    COMMIT -->|"Write"| ST_COMMIT

    %% Projection
    COMMIT --> PROJ
    PROJ -->|"Write state_deltas"| ST_STATE
    PROJ -->|"Write entity_deltas"| ST_INDEX
    PROJ -->|"Write summary_text"| ST_SUMMARY
    PROJ -->|"Write memory_facts"| ST_MEMORY
    PROJ -->|"Write event+delta chunks"| ST_VECTOR

    %% Step 6
    PROJ --> GIT
```

## Six-Layer Mainline Overview

```mermaid
graph TB
    subgraph L1["Layer 1: Knowledge"]
        CSV_TABLES["9 CSV tables"]
        CSV_CONFIG["CSV_CONFIG (per-table registration)"]
        REF_MD["reference Markdown files"]
    end

    subgraph L2["Layer 2: Reasoning"]
        ROUTE["题材与调性推理.csv → _route()"]
        REASON["裁决规则.csv → _load_reasoning()"]
        APPLY["_apply_reasoning() + _rank_anti_patterns()"]
    end

    subgraph L3["Layer 3: Contract"]
        MASTER["MASTER_SETTING.json"]
        VOLUME["VOLUME_BRIEF"]
        CHAPTER["CHAPTER_BRIEF + reasoning"]
        REVIEW["REVIEW_CONTRACT"]
        ANTI_P["anti_patterns.json"]
    end

    subgraph L4["Layer 4: Context"]
        CTX_MGR["context_manager.py (pure JSON)"]
        LOAD_CTX["load-context (lightweight base package)"]
        KNOW_Q["knowledge_query.py (temporal queries)"]
    end

    subgraph L5["Layer 5: Commit"]
        DA["data-agent (extract facts)"]
        COMMIT_SVC["chapter-commit (post-writing source of truth)"]
        PROJ_ROUTER["EventProjectionRouter"]
    end

    subgraph L6["Layer 6: Projection"]
        PW_STATE["state_projection_writer"]
        PW_INDEX["index_projection_writer"]
        PW_SUMMARY["summary_projection_writer"]
        PW_MEMORY["memory_projection_writer"]
        PW_VECTOR["vector_projection_writer"]
    end

    subgraph STORES["Storage"]
        S_STATE["state.json"]
        S_INDEX["index.db"]
        S_SUMMARY["summaries/"]
        S_MEMORY["memory_scratchpad"]
        S_VECTOR["vector_db"]
    end

    CSV_TABLES --> ROUTE
    CSV_TABLES --> REASON
    ROUTE --> APPLY
    REASON --> APPLY
    APPLY --> MASTER
    APPLY --> CHAPTER
    APPLY --> ANTI_P

    MASTER --> CTX_MGR
    VOLUME --> CTX_MGR
    CHAPTER --> CTX_MGR
    REVIEW --> CTX_MGR
    CTX_MGR --> LOAD_CTX

    S_STATE --> KNOW_Q
    S_INDEX --> KNOW_Q

    DA --> COMMIT_SVC
    COMMIT_SVC --> PROJ_ROUTER

    PROJ_ROUTER --> PW_STATE
    PROJ_ROUTER --> PW_INDEX
    PROJ_ROUTER --> PW_SUMMARY
    PROJ_ROUTER --> PW_MEMORY
    PROJ_ROUTER --> PW_VECTOR

    PW_STATE -->|"Write"| S_STATE
    PW_INDEX -->|"Write"| S_INDEX
    PW_SUMMARY -->|"Write"| S_SUMMARY
    PW_MEMORY -->|"Write"| S_MEMORY
    PW_VECTOR -->|"Write"| S_VECTOR
```

## Genre Data Flow

```mermaid
graph LR
    INIT_USER["User selects a genre (e.g. '修仙', cultivation)"]
    STATE_GENRE["state.json<br/>project.genre='修仙'<br/> (init configuration snapshot / read-model)"]
    
    STORY_CLI["story-system CLI<br/>--genre '修仙'"]
    
    ROUTE_TABLE["题材与调性推理.csv<br/>_route(): fallback"]
    REASON_TABLE["裁决规则.csv<br/>_load_reasoning('修仙')<br/>alias match → 东方仙侠 (Eastern xianxia)"]
    
    MASTER_OUT["MASTER_SETTING.json<br/>route.primary_genre"]
    CHAPTER_OUT["chapter_NNN.json<br/>reasoning.genre='东方仙侠'<br/>reasoning.style_priority<br/>reasoning.pacing_strategy"]
    
    CTX_AGENT["context-agent<br/>Read reasoning fields<br/>from load-context"]
    
    BRIEF["Writing brief, section 4<br/>'Keep a cold, calculating feel...'"]

    INIT_USER -->|"init writes"| STATE_GENRE
    STATE_GENRE -->|"Read genre"| STORY_CLI
    STORY_CLI -->|"query"| ROUTE_TABLE
    STORY_CLI -->|"genre fallback"| REASON_TABLE
    STORY_CLI -->|"persist"| MASTER_OUT
    STORY_CLI -->|"persist"| CHAPTER_OUT
    CHAPTER_OUT -->|"load-context"| CTX_AGENT
    CTX_AGENT -->|"Translate into natural language"| BRIEF
```
