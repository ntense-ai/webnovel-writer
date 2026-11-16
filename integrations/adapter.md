---
name: {{NAME}}
description: {{DESCRIPTION}}
---

# {{NAME}}: portable host adapter

Use this adapter for Codex or Antigravity. It reuses the English Webnovel Writer
engine and its complete workflow, not a second implementation.

## Resolve the installation

Find the workspace by walking three parents up from **this SKILL.md's directory**
(`.agents/skills/{{NAME}}`, or legacy `.agent/skills/{{NAME}}`). The engine is
`<workspace>/.webnovel-writer-engine`. Resolve paths from this file, not the shell's
current directory. Set these values explicitly in each shell command/session:

- `CLAUDE_PLUGIN_ROOT`: absolute path to that engine (compatibility variable only).
- `SCRIPTS_DIR`: its `scripts` directory.
- `WORKSPACE_ROOT` and `CLAUDE_PROJECT_DIR`: the workspace containing the books.
- `PROJECT_ROOT`: the explicit selected book, once resolved. Do not guess a book
  from another project's saved pointer. Initialization selects a new target first.

Use the user's configured Python environment. Inspect
`python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --help` before running unfamiliar
commands. Dependencies are not installed by this adapter.

Read `<engine>/skills/{{NAME}}/SKILL.md` and its relevant references, interpreting
relative reference links from that original file. Run its ordered workflow with
the following host translations. Do not execute its Claude-only environment
bootstrap literally; use the resolved paths above instead.

## Host translations and safeguards

- `Read`, `Write`, `Edit`, `Grep`, and `Bash` mean the host's available file/search
  and shell tools. `AskUserQuestion` means asking the user directly when no
  dedicated question tool exists. `WebSearch`/`WebFetch` require available browsing;
  disclose when current external evidence cannot be checked.
- `/webnovel-*` denotes a workflow, not a guaranteed host slash command. Read the
  corresponding engine skill when another workflow is required. In Codex users
  can explicitly select `$webnovel-*`; Antigravity can select skills by name.
- A role such as `webnovel-writer:context-agent` is defined by
  `<engine>/agents/context-agent.md`, not by an installed host agent registry.
  If the host supports subagents, pass that file's instructions, resolved project
  paths, required input, and expected output to an actual isolated worker.
  Map review roles to their corresponding files. Preserve each output contract.
- Never invent `Agent`, `Task`, `invoke_subagent`, plugin registrations, or a
  successful review. If a required independent worker cannot be launched, stop
  that gated workflow and report the missing capability. You may offer a draft
  outside the gated pipeline, clearly labeled unreviewed, but never claim a
  chapter was committed or validated. Do not silently replace mandatory
  independent review with self-review or fabricate provenance.
- Claude lifecycle hooks are **not installed or automatically run** by this
  adapter. Execute every explicit preflight, write gate, review artifact check,
  fact extraction, state projection, and backup step in the original workflow.
  Never bypass a gate merely because a host hook is absent.
- Preserve project schemas and legacy aliases. Use `project_paths.py` to resolve
  existing books. Generate new content in English unless requested otherwise.
- Keep approvals, sandboxing, and user instructions in force. Do not disable host
  safeguards, start persistent background processes, install packages, or add
  credentials just because an upstream example does so.

Report which steps actually ran, the artifacts produced, and any blocked stages.
