# Documentation Center

The `docs/` directory is organized by function for easy reference.

## Directory Index

### Architecture

- [`architecture/overview.md`](./architecture/overview.md): System architecture, agent responsibilities, and Story System design
- [`architecture/plugin-runtime-hardening-spec-2026-06-04.md`](./architecture/plugin-runtime-hardening-spec-2026-06-04.md): Runtime reliability refactoring specification based on research into high-quality Claude Code plugins
- [`architecture/plugin-runtime-hardening-plan-2026-06-04.md`](./architecture/plugin-runtime-hardening-plan-2026-06-04.md): Runtime reliability implementation plan, scope of changes, and impact analysis
- [`architecture/multi-agent-adaptation-spec-2026-06-05.md`](./architecture/multi-agent-adaptation-spec-2026-06-05.md): Multi-host and multi-agent adaptation specification based on v6.1.0
- [`architecture/context-minimal-writing-flow-plan-2026-06-05.md`](./architecture/context-minimal-writing-flow-plan-2026-06-05.md): Refactoring plan for reducing Skills / Agents / References context, improving read strategies, and optimizing tokens (v3)
- [`archive/architecture/current-system-diagnosis.md`](./archive/architecture/current-system-diagnosis.md): Historical system-state diagnosis

### User Guides

- [`guides/commands.md`](./guides/commands.md): Skill command and CLI subcommand quick reference
- [`guides/rag-and-config.md`](./guides/rag-and-config.md): RAG retrieval pipeline, environment variables, and configuration
- [`guides/genres.md`](./guides/genres.md): The 37 genre templates and hybrid-genre rules

### Operations

- [`operations/operations.md`](./operations/operations.md): Project directory structure, operational commands, backup, and recovery
- [`operations/plugin-release.md`](./operations/plugin-release.md): Plugin release workflow and version synchronization

### Memory System

- [`memory/long-term-memory-architecture-v2.md`](./memory/long-term-memory-architecture-v2.md): Long-term memory architecture

### Research and External Approaches

- [`research/long-term-memory-research-report.md`](./research/long-term-memory-research-report.md): Research into long-term memory papers and open-source approaches
- [`research/storyteller-paper-summary.md`](./research/storyteller-paper-summary.md): Summary of the STORYTELLER paper

### Archive

- [`archive/superpowers/README.md`](./archive/superpowers/README.md): Index of historical architecture specifications and design documents

## Organization Principles

- `architecture/`: System structure and technical architecture
- `guides/`: Commands, configuration, and genre information for users
- `operations/`: Operations, releases, backup, and recovery
- `memory/`: Long-term memory architecture
- `research/`: Paper summaries and research into external approaches
- `archive/`: Historical architecture snapshots, specifications, and design plans

## Suggested Reading Order

1. Start with [`../README.md`](../README.md) for installation and basic usage.
2. Read [`architecture/overview.md`](./architecture/overview.md) for the overall architecture.
3. Consult [`guides/rag-and-config.md`](./guides/rag-and-config.md) when configuring retrieval.
4. Consult [`guides/commands.md`](./guides/commands.md) when using commands.
5. Consult [`operations/operations.md`](./operations/operations.md) when troubleshooting runtime issues.
