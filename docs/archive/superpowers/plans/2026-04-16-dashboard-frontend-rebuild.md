# Dashboard Frontend Rebuild Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the dashboard frontend: remove unused data, add visualizations, split files, and add foreshadowing tracking and system-status pages.

**Architecture:** React 19 + Vite, with a chart library and routing. Add aggregation APIs to the backend.

**Tech Stack:** React 19, Vite, react-router-dom v7, Apache ECharts (echarts + echarts-for-react), Pixelarticons (pixelarticons)

**Design:** Visual style and specific chart forms await confirmation; see `dashboard/frontend/design.md` (to be updated).

---

## File Structure

### Frontend (dashboard/frontend/src/)

```text
src/
├── main.jsx                    # Entry point; mount Router
├── App.jsx                     # Layout shell (sidebar + Router Outlet + SSE)
├── api.js                      # API requests (retain; add endpoints)
├── index.css                   # Global styles
├── components/
│   ├── ChartWrapper.jsx        # Chart wrapper with consistent styling
│   ├── Badge.jsx               # Badge component
│   ├── Pager.jsx               # Pagination controls for windowed large datasets
│   └── DataTable.jsx           # Paginated table extracted from MiniTable
└── pages/
    ├── OverviewPage.jsx        # Overview
    ├── CharactersPage.jsx      # Character directory (entities + relationship graph)
    ├── PacingPage.jsx          # Pacing radar
    ├── ForeshadowingPage.jsx   # Foreshadowing tracking
    ├── FilesPage.jsx           # Document browser (migrated)
    └── SystemPage.jsx          # System status
```

### Backend (Add APIs to dashboard/app.py)

```text
/api/stats/chapter-trend       # Aggregate chapter length + review score + hook strength
/api/commits                   # Latest N commits: meta + projection_status
/api/contracts/summary         # MASTER_SETTING summary + current volume/chapter contract existence
/api/env-status                # RAG/Rerank environment configuration status (PR #50)
/api/env-status/probe          # Active RAG/Rerank probes (PR #50)
```

---

## Task 1: Add Backend Aggregation APIs

**Files:**
- Modify: `webnovel-writer/dashboard/app.py`

- [ ] **Step 1: Add `/api/stats/chapter-trend`**

Aggregate index.db queries into a single response containing each chapter's character count, review score, hook type, and strength. Support `limit` and `offset`; return the latest 50 chapters by default.

- [ ] **Step 2: Add `/api/commits`**

Read commit JSON files from `.story-system/commits/` and return chapter, status, and projection_status. Support `limit`.

- [ ] **Step 3: Add `/api/contracts/summary`**

Read contract-tree file existence and key fields: MASTER_SETTING primary_genre/core_tone and counts of volume/chapter/review contracts.

- [ ] **Step 4: Merge the env-status APIs From PR #50**

Extract `/api/env-status` and `/api/env-status/probe` code from PR #50.

- [ ] **Step 5: Test + Commit**

---

## Task 2: Frontend Infrastructure (Routing + File Splitting + Shared Components)

**Files:**
- Modify: `dashboard/frontend/package.json`
- Modify: `dashboard/frontend/src/main.jsx`
- Modify: `dashboard/frontend/src/App.jsx`
- Modify: `dashboard/frontend/src/api.js`
- Create: `dashboard/frontend/src/components/*.jsx`

- [ ] **Step 1: Install Dependencies**

```bash
npm install echarts echarts-for-react react-router-dom pixelarticons
```

- [ ] **Step 2: Extract Shared Components**

Extract Badge, DataTable (formerly MiniTable), and Pager (pagination controls) from the existing App.jsx.

Pager requirements:
- Support window size (N items per page), pagination, and “jump to latest.”
- Handle data for 500+ chapters.

- [ ] **Step 3: Add Routing to main.jsx**

Use lazy imports for each page component with React Router.

- [ ] **Step 4: Reduce App.jsx to a Pure Layout Shell**

Keep only sidebar navigation, the SSE connection, and Router Outlet. Move all page logic into pages/.

- [ ] **Step 5: Update api.js**

Add fetch functions for chapter-trend, commits, contracts-summary, env-status, and env-probe.

- [ ] **Step 6: Verify Build + Commit**

---

## Task 3: Overview Page

**Files:**
- Create: `dashboard/frontend/src/pages/OverviewPage.jsx`

**Features:**
- Statistics cards: total character count/progress, current chapter/volume, Story Runtime status, average review score, urgent foreshadowing count
- Review-score visualization: ECharts line chart with pagination, showing the latest N chapters by default
- Character-count visualization: ECharts bar chart grouped by volume
- Overall Strand Weave distribution
- Top-five urgent foreshadowing table
- Summary cards for the latest three chapters

**Remove:**
- MergedDataView (full-data view)
- FULL_DATA_GROUPS / FULL_DATA_DOMAINS constants

**Large-Dataset Support:**
- Visualizations default to the latest window and support pagination.
- Group character counts by volume rather than displaying every chapter at once.

- [ ] **Step 1: Implement + Verify Build + Commit**

---

## Task 4: Character Directory Page

**Files:**
- Create: `dashboard/frontend/src/pages/CharactersPage.jsx`

**Features:**
- Tab 1, list view: entity list, filters, detail panel, and state-change history (retain existing logic)
- Tab 2, relationship graph: ECharts graph series with force-directed layout and a chapter timeline slider

Relationship-graph timeline requirements:
- The slider controls the current chapter; filter nodes/edges by `first_appearance` / `chapter`.
- Relationship labels may change by chapter, such as “new acquaintances” → “archenemies.”
- Play/pause button for automatic chapter advancement
- Show the current chapter number and visible node count.

- [ ] **Step 1: Implement + Commit**

---

## Task 5: Pacing Radar Page

**Files:**
- Create: `dashboard/frontend/src/pages/PacingPage.jsx`

**Features:**
- Hook-strength trend: ECharts area line chart with pagination, N chapters per page
- Strand distribution: ECharts stacked bar chart showing per-chapter Strand distribution
- Character-count distribution: ECharts bar chart grouped by volume

**Large-Dataset Support:**
- Every component supports pagination and “jump to latest.”

- [ ] **Step 1: Implement + Commit**

---

## Task 6: Foreshadowing Tracking Page

**Files:**
- Create: `dashboard/frontend/src/pages/ForeshadowingPage.jsx`

**Features:**
- Statistics cards: total, active, resolved, urgent/overdue foreshadowing
- Status filters: all / urgent / active / resolved
- Foreshadowing timeline: ECharts custom bar series (horizontal Gantt), from setup chapter to target chapter; status-based colors and a blue line for the current chapter
- Complete foreshadowing table: content, status, setup chapter, target chapter, urgency

**Large-Dataset Support:**
- Gantt defaults to active + urgent items; resolved items are collapsed.
- The horizontal axis adapts automatically rather than always spanning chapters 1–500.

- [ ] **Step 1: Implement + Commit**

---

## Task 7: System Status Page

**Files:**
- Create: `dashboard/frontend/src/pages/SystemPage.jsx`

**Features:**
- Story Runtime health (mainline/fallback, latest commit)
- Contract-tree overview (MASTER_SETTING genre/tone and volume/chapter/review counts)
- Recent commit history table (chapter, accepted/rejected, five projection_status channels)
- RAG environment status (embed/rerank key, vector_db size, rag_mode) and diagnostic button

- [ ] **Step 1: Implement + Commit**

---

## Task 8: Migrate Document Browser + Final Cleanup

**Files:**
- Create: `dashboard/frontend/src/pages/FilesPage.jsx`
- Modify: `dashboard/frontend/src/App.jsx`

- [ ] **Step 1: Migrate FilesPage Without Changing Its Logic**
- [ ] **Step 2: Final App.jsx Cleanup: Remove All Migrated Components and Constants**
- [ ] **Step 3: Build Frontend + Launch and Verify All Six Pages + Commit**

---

## Navigation Changes

| Old Navigation | New Navigation | Icon (Pixelarticons) | Change |
|----------------|----------------|---------------------|--------|
| 📊 Data Overview | Overview | `chart-bar` | Remove full-data view; add visualizations |
| 👤 Setting Dictionary | Character Directory | `users` | Merge relationship graph, replace 3D with 2D, add timeline |
| 🕸️ Relationship Graph | _(merged into Characters)_ | — | Remove standalone page |
| 📝 Chapter List | Pacing Radar | `trending-up` | New page |
| 📁 Document Browser | Document Browser | `folder` | Unchanged |
| 🔥 Reader Retention | Foreshadowing Tracking | `bookmark` | New page |
| _(none)_ | System Status | `sliders` | New page |

## Removed Data

- RAG query logs, tool-call statistics, Override contract details, debt-event details
- Invalid-fact lists, raw writing-checklist scores, full-data view (MergedDataView)

## Items Awaiting Confirmation (Updated After Design Discussion)

- [x] ~~Confirm visual style~~ → Retain pixel art
- [x] ~~Choose chart library~~ → Apache ECharts (echarts + echarts-for-react)
- [x] ~~Choose relationship graph library~~ → ECharts graph series (force-directed layout)
- [x] ~~Review-score chart form~~ → Line chart
- [x] ~~Character-count chart form~~ → Bar chart grouped by volume
- [x] ~~Hook-strength chart form~~ → Area line chart
- [x] ~~Strand distribution chart form~~ → Stacked bar chart
