---
name: webnovel-dashboard
description: Start a read-only novel management dashboard to view project status, entity graphs, and chapter content.
allowed-tools: Bash Read
---

# Webnovel Dashboard

## Project paths and output language

Use English for generated story content, headings, summaries, reports, and user-facing explanations unless the user explicitly requests another language. Preserve runtime schema keys, enum values, and machine-readable identifiers exactly.

New books use `chapters/`, `outlines/`, `settings/`, and `reviews/`. Examples below use that layout. Before directly reading or writing an existing book, run `python "${SCRIPTS_DIR}/project_paths.py" --project-root "${PROJECT_ROOT}"` and use the returned paths. Resolve a specific example file with `--path outlines/master-outline.md` (substitute its logical English path) so legacy filenames are respected; an existing book may still use `正文/`, `大纲/`, `设定集/`, and `审查报告/`. Never rename existing directories, create parallel English copies, or overwrite legacy content merely to match an example. If both aliases exist, inspect them and resolve any conflict before writing. Pass actual resolved paths to subagents.

## Goal

- Start a local read-only web dashboard to view writing progress, the setting dictionary, relationship graphs, chapter content, and reader-retention data.
- Expose the main Story Runtime pipeline status: `/api/story-runtime/health`, latest commit, and fallback status.
- May watch `.webnovel/` for changes, but must not modify any project files.

## Procedure

### Step 1: Verify the environment and module directory

```bash
export WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"

if [ -z "${CLAUDE_PLUGIN_ROOT}" ] || [ ! -d "${CLAUDE_PLUGIN_ROOT}/dashboard" ]; then
  echo "ERROR: dashboard module not found: ${CLAUDE_PLUGIN_ROOT}/dashboard" >&2
  exit 1
fi

export DASHBOARD_DIR="${CLAUDE_PLUGIN_ROOT}/dashboard"
export SCRIPTS_DIR="${CLAUDE_PLUGIN_ROOT}/scripts"
```

### Step 2: Resolve the project root

```bash
export PROJECT_ROOT="$(python "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" where)"
echo "Project path: ${PROJECT_ROOT}"
```

`PROJECT_ROOT` must resolve successfully.

### Step 3: Validate frontend build artifacts and dependencies

```bash
if [ -n "${PYTHONPATH:-}" ]; then
  export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}:${PYTHONPATH}"
else
  export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
fi

if [ ! -f "${DASHBOARD_DIR}/frontend/dist/index.html" ]; then
  echo "ERROR: Missing frontend build artifact ${DASHBOARD_DIR}/frontend/dist/index.html (dist should ship with the plugin; verify the plugin installation is complete)" >&2
  exit 1
fi
```

Do not install dependencies by default. Only if Step 4 fails to start because dependencies are missing, prompt the user to run this manually:

```bash
python -m pip install -r "${DASHBOARD_DIR}/requirements.txt"
```

### Step 4: Start the Dashboard

```bash
python -m dashboard.server --project-root "${PROJECT_ROOT}"
```

Add `--no-browser` to avoid automatically opening a browser; add `--port 9000` to use a custom port.

After startup, first verify that the endpoints are available: `/api/story-runtime/health` and `/api/preflight`.

## Success criteria

- The Dashboard process has started and printed an accessible URL; the page displays project data (chapter list, entity graph, etc.).

## Failure recovery

| Failure | Recovery |
|------|---------|
| Missing dependencies at startup | Manually run `pip install -r "${DASHBOARD_DIR}/requirements.txt"`; check the Python version and network |
| Missing frontend `dist/` | Verify the plugin installation is complete; dist should ship with the plugin |
| Project root resolution failed | Check that `.webnovel/state.json` exists and `WORKSPACE_ROOT` is correct |
| Port in use | Use `--port <another-port>` or stop the process occupying the port |
| Blank page/missing data | Verify that `.webnovel/` contains data files such as state.json and index.db |

## Safety boundaries

- A strictly read-only dashboard: no modification endpoints and no changes to any project files.
- File access is restricted to `PROJECT_ROOT`; listens on localhost only by default.
