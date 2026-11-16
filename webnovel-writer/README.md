# Webnovel Writer (Plugin Source Directory)

The Claude Code package for the long-form webnovel writing plugin. See the repository's main [README](../README.md) for the full introduction, installation instructions, and documentation index.

> This file is for users and maintainers working with the plugin package itself. It lists packaged components and minimal verification steps.

## Package Contents

| Type | Count | Location |
|------|------|------|
| Skills (slash commands) | 7 | `skills/<name>/SKILL.md` |
| Agents (subagents) | 4 | `agents/*.md` |
| Python tools | Unified entry point | `scripts/webnovel.py` |
| Genre/writing technique data | 9 CSV files | `references/csv/*.csv` |
| Genre templates | By genre | `templates/genres/*.md` |
| Dashboard frontend | Prebuilt | `dashboard/frontend/dist/` (included in the package; no local build required) |

### 7 Skills

| Command | Purpose |
|------|------|
| `/webnovel-init` | Deep initialization of the project structure, setting bible, and master outline |
| `/webnovel-plan` | Break down volume outlines, timelines, and chapter outlines; persist new settings |
| `/webnovel-write` | End-to-end chapters: context → draft → review → polish → commit → backup |
| `/webnovel-review` | Review chapters across multiple dimensions and store metrics |
| `/webnovel-query` | Query settings, characters, foreshadowing, and runtime information (read-only) |
| `/webnovel-learn` | Retain effective writing techniques in project long-term memory |
| `/webnovel-dashboard` | Launch the read-only visual dashboard |

### 4 Agents

| Agent | Responsibility | Called by |
|-------|------|---------|
| `context-agent` | Pre-writing research and writing brief | `/webnovel-write` Step 1 |
| `reviewer` | Dimension-by-dimension factual review | `/webnovel-write` Step 3, `/webnovel-review` |
| `data-agent` | Extract facts from chapter text and generate commit artifacts | `/webnovel-write` Step 5 |
| `deconstruction-agent` | Analyze reference books and extract transferable techniques | `/webnovel-init` Step 1.5 |

## Dependencies and Installation

Install the English `ntense` fork through its separate Claude Code Marketplace:

```bash
claude plugin marketplace add "ezhomelabs/webnovel-writer#ntense" --scope user
claude plugin install webnovel-writer@ntense-webnovel-writer --scope user
```

For Python dependencies, follow the [main Quick Start](../README.md#2-install-python-dependencies) to clone the `ntense` branch and activate a virtual environment. If already in this plugin source directory within that checkout, install both dependency sets:

```bash
python -m pip install -r scripts/requirements.txt -r dashboard/requirements.txt
```

Keep that environment active when starting Claude Code from your book workspace. The quoted branch ref is required; an unpinned fork URL can select the original-language default branch.

Configure `.env` at the book project root for RAG retrieval. Without it, retrieval falls back to BM25 keyword search. See [RAG and configuration](../docs/guides/rag-and-config.md).

## Minimal Verification

```bash
# Preflight paths, project root, and Story System health
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" preflight

# Prompt and data-pipeline tests
python -m pytest -q --no-cov
```

> For clean-room installation checks, use `git archive` or a clean clone so local development artifacts such as `node_modules/`, `__pycache__/`, and `.coverage` do not enter `--plugin-dir` tests.

## License

[GPL-3.0](LICENSE). See the main [README](../README.md) and [docs/](../docs/README.md) for the complete documentation index.
