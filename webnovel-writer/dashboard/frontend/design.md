# PIXEL WRITER HUB Design Specification

> Dashboard frontend specification. All pages must comply.
> Prototype preview: `docs/archive/architecture/dashboard-prototype.html`

## Visual Style: Retro Pixels / 8-bit Games

An RPG status panel meets a writing dashboard. Fun, nerdy, pixel-perfect.

## Palette

| Variable | Color | Purpose |
|------|------|------|
| `--bg-main` | `#fff7e8` | Page background (14px grid lines) |
| `--bg-panel` | `#fffdf6` | Table/panel interior |
| `--bg-card` | `#fffaf0` | Card background |
| `--bg-card-2` | `#fff3d5` | Table headers, secondary cards |
| `--text-main` | `#2a220f` | Primary text |
| `--text-sub` | `#5d5035` | Secondary text |
| `--text-mute` | `#8f7f5c` | Labels, placeholders |
| `--accent-blue` | `#26a8ff` | Primary accent (values, active states) |
| `--accent-purple` | `#7f5af0` | Secondary accent (Strand, badges) |
| `--accent-green` | `#2ec27e` | Success (review passed, resolved threads) |
| `--accent-amber` | `#f5a524` | Warning (urgent threads, medium scores) |
| `--accent-red` | `#d7263d` | Danger (blocking, overdue) |
| `--accent-cyan` | `#00b8d4` | Information (badges) |
| `--border-main` | `#2a220f` | Primary borders |
| `--border-soft` | `#8f7f5c` | Secondary borders |

### ECharts Series Color Order

```
['#26a8ff', '#f5a524', '#7f5af0', '#2ec27e', '#d7263d', '#00b8d4', '#ff5c8a']
```

### Strand Colors

| Strand | Color | CSS class |
|--------|------|--------|
| Quest | `#26a8ff` | `.strand-quest` |
| Fire | `#ff5c8a` | `.strand-fire` |
| Constellation | `#7f5af0` | `.strand-constellation` |

### Foreshadowing Status Colors

| Status | Color | Badge |
|------|------|-------|
| Overdue | `#d7263d` | `.badge-red` |
| Urgent | `#f5a524` | `.badge-amber` |
| Active | `#26a8ff` | `.badge-blue` |
| Resolved | `#2ec27e` | `.badge-green` |

## Typography

- **Headings/logo**: `Press Start 2P`, 11px, letter spacing 0.08em
- **Body/data**: `Noto Sans SC`, 14px, font-weight 500-700
- **Numbers**: tabular-nums (equal-width numerals)
- **Legends/small labels**: `Noto Sans SC` 13px, font-weight 600

## Borders and Shadows

- Cards: `3px solid #2a220f`, shadow `6px 6px 0 #2a220f`
- Secondary containers: `2px solid #8f7f5c`, shadow `3px 3px 0 #8f7f5c`
- No rounded corners (0px): pixel art uses square corners.
- All borders are hard straight lines.

## Components

**Badge**: `2px solid #2a220f`, padding `3px 8px`; see `.badge-*` classes for colors.

**Table**: Wrap in `.table-wrap`; header background `--bg-card-2`; row hover `#fff4d8`; support pagination.

**Progress bar**: `12px` high, `2px` hard border, gradient fill `#26a8ff → #7f5af0`.

**Buttons/navigation**: `2px solid` border; hover offset `-1px, -1px`. Blue active background.

**Stat card**: `.stat-card` contains `.stat-label` (mute, 13px), `.stat-value` (accent-blue, 28px), `.stat-sub` (sub, 13px).

**Pager**: `← Previous N` / `page information` / `Next page →` / `Jump to latest →`; use `.page-btn`.

**Filter button group**: `.filter-group` flex layout; `.filter-btn` 2px border; blue background and border when active.

## ECharts Pixel Theme

Register as `pixel`; initialize all charts with `echarts.init(el, 'pixel')`.

### Key Theme Configuration

```js
{
  color: ['#26a8ff','#f5a524','#7f5af0','#2ec27e','#d7263d','#00b8d4','#ff5c8a'],
  backgroundColor: 'transparent',
  tooltip: {
    backgroundColor: '#fffaf0',
    borderColor: '#2a220f',
    borderWidth: 2,
    extraCssText: 'border-radius:0;box-shadow:3px 3px 0 #2a220f;'
  },
  // Axes
  axisLine:  { lineStyle: { color: '#8f7f5c', width: 2 } },
  axisLabel: { color: '#8f7f5c', fontSize: 12 },
  splitLine: { lineStyle: { color: '#e8dcc4', type: 'dashed' } }
}
```

### Shared Chart Rules

| Rule | Description |
|------|------|
| No rounded corners | No borderRadius for tooltips, bars, or nodes |
| Hard outlines | Every item uses `borderColor: '#2a220f', borderWidth: 2` |
| Square symbols | Line-chart points use `symbol: 'rect', symbolSize: 8` |
| 3px lines | `lineStyle.width: 3`; no smooth lines |
| Square bars | Default rectangular bar charts |
| Area fill | Linear gradient from 20% opacity to transparent |
| markLine | Mean/current-chapter lines use `type: 'dashed'` or `solid`, with semantically appropriate colors |

## Per-Page Chart Specifications

### OverviewPage

| Chart | Type | Data | Interaction |
|------|------|------|------|
| Review-score trend | Line | overall_score per chapter | Pagination (50 chapters/page) + mean markLine |
| Character-count distribution | Bar | Counts aggregated by volume | Labels in units of 10,000 characters |
| Overall Strand distribution | Doughnut (pie) | quest/fire/constellation counts | Percentage labels |
| Top 5 urgent threads | Table | Content, status, planted chapter, target chapter, urgency | — |

### CharactersPage

| Chart | Type | Data | Interaction |
|------|------|------|------|
| Relationship network | Force-directed graph | entities + relationships | **Chapter timeline slider** + play/pause |

**Relationship timeline specification:**
- Slider (`<input type="range">`) controls the current chapter, from 1 to latest.
- Show nodes where `first_appearance <= current chapter`.
- Show edges where `chapter <= current chapter`; labels can evolve (e.g. "first meeting" → "archenemies").
- Play button: advance 5 chapters every 120ms.
- Right-hand badge shows current chapter + visible node count live.
- Nodes: square (`symbol: 'rect'`); protagonist larger and gold (`#f5a524`).
- Edges: lines + labels, `curveness: 0.1`.
- Category colors: characters `#26a8ff`, factions `#7f5af0`, places `#2ec27e`.

### PacingPage

| Chart | Type | Data | Interaction |
|------|------|------|------|
| Hook-strength trend | Area line (line+areaStyle) | hook_strength per chapter | Pagination (50 chapters/page) |
| Strand distribution | Stacked bar (bar, stack) | Per-chapter strand allocation | Pagination |
| Character-count distribution | Boxplot | Grouped by volume | — |

### ForeshadowingPage

| Chart | Type | Data | Interaction |
|------|------|------|------|
| Foreshadowing timeline | Custom bar (custom series) | Planted chapter → target chapter | Blue current-chapter line (`z:10` on top), colored by status |

**Gantt specification:**
- Y axis: Thread names (reversed, urgent at top).
- X axis: Chapter range; the existing label format is `axisLabel: 'Chapter N'` (Chapter N).
- Bar colors: overdue `#d7263d`, urgent `#f5a524`, active `#26a8ff`, resolved `#2ec27e`.
- Current-chapter vertical line: `markLine` + `z: 10` (above bars), `label.position: 'end'`.
- Show only active + urgent by default; collapse resolved threads.
- Adapt horizontal range automatically instead of filling 1 through maximum chapter.

### SystemPage

Stat cards + tables only; no charts.

## Layout

- Sidebar 240px (gold gradient `#ffe8b8 → #ffe19f`), `3px` right border.
- Scrollable main area, padding 22px.
- Stat-card grid: `repeat(auto-fill, minmax(220px, 1fr))`.
- Full-width chart cards: height 320px (default) / 420px (relationship graphs and other `.tall` cards) / 380px (Gantt `.gantt`).

## Navigation

| Icon | Label | Route |
|------|------|------|
| 📊 | Overview | `/` |
| 👤 | Characters | `/characters` |
| 📈 | Pacing Radar | `/pacing` |
| 🔖 | Foreshadowing | `/foreshadowing` |
| 📁 | File Browser | `/files` |
| ⚙️ | System Status | `/system` |

## Large Datasets

- All time-series charts default to the latest 50 chapters, with pagination + "Jump to latest."
- Group character counts by volume rather than showing every chapter at once.
- Gantt defaults to active + urgent; resolved threads can be expanded.
- Relationship timeline playback advances 5 chapters/120ms, not one chapter per render.

## Icons

Use [Pixelarticons](https://pixelarticons.com/) (`pixelarticons` npm package).

- 24×24 grid, no antialiasing, pure pixel style.
- SVG `fill="currentColor"` inherits the parent color and fits the palette naturally.
- Import React components; tree-shakeable.
- Use multiples of 24px (24/48) for pixel alignment.

### Navigation Icon Mapping

| Page | Icon name | Component |
|------|--------|------|
| Overview | `chart-bar` | `<ChartBar />` |
| Characters | `users` | `<Users />` |
| Pacing Radar | `trending-up` | `<TrendingUp />` |
| Foreshadowing | `bookmark` | `<Bookmark />` |
| File Browser | `folder` | `<Folder />` |
| System Status | `sliders` | `<Sliders />` |

### Other Common Icons

| Purpose | Icon name |
|------|--------|
| Play/pause | `play` / `pause` |
| Pagination | `chevron-left` / `chevron-right` |
| Jump to latest | `chevrons-right` |
| Refresh/diagnostics | `reload` |
| Connection status | `wifi` / `wifi-off` |
| Search/filter | `search` / `filter` |

## Avoid

- Rounded corners.
- Gradient backgrounds (except progress bars).
- Soft shadows.
- Glassmorphism / neumorphism.
- Emoji icons: use Pixelarticons.
- 3D charts (replace the former react-force-graph-3d with ECharts 2D graph).
