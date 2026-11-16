# Phase 0 Audit: Tool Capabilities and Plugin Registration Names (2026-06-06)

> Read-only audit. This document records evidence only; it changes no skill / agent / plugin.json / test files.
> Purpose: Establish a trustworthy runtime baseline for `context-minimal-writing-flow-plan`, verifying the assumed
> `webnovel-writer:<agent>` registration names, agent/skill frontmatter, and official tool behavior on which the plan depends.
>
> Working directory (Git repository root = worktree): `D:/wk/novel skill/webnovel-writer/.worktrees/context-minimal-flow`
> Plugin directory (nested): the `webnovel-writer/` subdirectory beneath the repository root.

---

## 1. Claude Code Version and Environment

| Item | Value | Evidence |
|----|----|------|
| Host | Claude Code (fixed; this plugin's only target host) | — |
| `claude --version` | `2.1.161 (Claude Code)` | Executed successfully in Bash (not unavailable because of subagent context) |
| Platform | Windows (win32), with both PowerShell and Bash | Environment description |
| Audit executor | subagent (Task 1); local `claude --version` returns normally | — |

Conclusion: Version and environment are confirmed; no degradation recorded.

---

## 2. Plugin Registration (Actual Names)

### 2.1 plugin.json

File: `webnovel-writer/.claude-plugin/plugin.json` (18 lines in full).

```json
{
  "name": "webnovel-writer",
  "version": "6.1.0",
  "description": "Long-form web-novel writing system (skills + agents + data chain + RAG)",
  "author": { "name": "lingfengQAQ" },
  "homepage": "https://github.com/lingfengQAQ/webnovel-writer",
  "repository": "https://github.com/lingfengQAQ/webnovel-writer",
  "license": "GPL-3.0",
  "keywords": ["webnovel", "claude-code", "skills", "agents", "rag"]
}
```

The descriptive value above is translated; the identifiers match the audited manifest.

- Plugin name (source of the namespace prefix): **`webnovel-writer`**.
- The manifest has **no** explicit `agents` / `skills` / `commands` path arrays.
  → All agents and skills therefore use **convention-based auto-discovery**:
  - Official `plugin-structure/SKILL.md:11`: automatic component discovery.
  - Lines 28–32 of the same file: `agents/` (`.md` files) and `skills/` (subdirectories, each containing `SKILL.md`).
  - Official `skill-development/SKILL.md:271-273`: Claude Code discovers skills by scanning `skills/` for subdirectories containing `SKILL.md`.

### 2.2 Actual On-Disk Agent Names (4)

Each agent is a single `.md` file. Its frontmatter `name:` matches the filename without `.md`:

| File | Frontmatter `name:` (line 2) | Matches? |
|------|---------------------------|--------|
| `webnovel-writer/agents/context-agent.md` | `context-agent` | ✅ |
| `webnovel-writer/agents/data-agent.md` | `data-agent` | ✅ |
| `webnovel-writer/agents/deconstruction-agent.md` | `deconstruction-agent` | ✅ |
| `webnovel-writer/agents/reviewer.md` | `reviewer` | ✅ |

There is also `webnovel-writer/agents/evals/` (containing `evals.json` + `files/`). These are evaluation fixtures, not agent definitions; auto-discovery does not treat them as agents because they are not top-level `.md` files. No `agents/references/` directory exists.

### 2.3 Actual On-Disk Skill Names (8)

Each skill is a subdirectory containing `SKILL.md`; its frontmatter `name:` (always on line 2) matches the directory name:

| Directory | Frontmatter `name:` | Matches? |
|------|--------------------|--------|
| `skills/webnovel-write/` | `webnovel-write` | ✅ |
| `skills/webnovel-init/` | `webnovel-init` | ✅ |
| `skills/webnovel-plan/` | `webnovel-plan` | ✅ |
| `skills/webnovel-review/` | `webnovel-review` | ✅ |
| `skills/webnovel-query/` | `webnovel-query` | ✅ |
| `skills/webnovel-learn/` | `webnovel-learn` | ✅ |
| `skills/webnovel-dashboard/` | `webnovel-dashboard` | ✅ |
| `skills/webnovel-doctor/` | `webnovel-doctor` | ✅ |

(The `webnovel-writer/` prefix is omitted.)

### 2.4 Registration Names vs. Names Referenced in the Plan (Critical)

The plan, `docs/architecture/context-minimal-writing-flow-plan-2026-06-05.md`, repeatedly references
all 4 agents as `webnovel-writer:<agent>`, for example:

- L181: must invoke `webnovel-writer:context-agent`
- L195: `... webnovel-writer:reviewer`
- L228: `... webnovel-writer:data-agent`
- L97: `... webnovel-writer:deconstruction-agent`
- L463/L698/L713/L728: `Use the Agent tool to run webnovel-writer:context-agent`, etc.
- L430: the plan itself warns that actual plugin-scoped agent registration names must be checked in Phase 0 (this section).

Findings:

- **On-disk names = `context-agent` / `data-agent` / `deconstruction-agent` / `reviewer`**,
  exactly matching the portion after the colon in the plan. **No incorrect names**.
- Prefix: the official Namespacing section in `agent-development/SKILL.md:281-285` says:
  - Agents are automatically namespaced: single plugin `agent-name`; with subdirectories `plugin:subdir:agent-name`.
  - In other words, the documentation uses the **bare `agent-name`** for a single plugin without subdirectories, reserving the prefixed form for subdirectories (`plugin:subdir:agent`).
  - Supporting command-side evidence: `command-development` and `plugin-features-reference.md:30` show plugin components labeled `(plugin:plugin-name)` in `/help`, indicating that plugin-name/component qualification is visible in Marketplace usage.
  - ⚠️ **Minor risk (name format, not a wrong name)**: official agent-development documentation gives bare `agent-name` as the single-plugin/no-subdirectory pattern; it does not list `plugin:agent` without a subdirectory as canonical. The plan's consistent **plugin-prefixed, no-subdirectory** form, such as `webnovel-writer:context-agent`, is reasonable and more explicit when multiple plugins coexist, but **the official documentation does not designate it the single-plugin standard**.
  - Recommendation: when wiring Phase 1, rely on **runtime testing** of whether the `Agent`/Task tool resolves `webnovel-writer:context-agent`. If only bare `context-agent` resolves and the prefixed form fails, revise the plan to use bare names. This audit cannot run the Agent tool inside a subagent to settle this, so it remains **pending runtime verification**.

---

## 3. Agent Frontmatter Audit (4)

Frontmatter transcribed field by field (line numbers are file-specific; all 4 frontmatter blocks occupy lines 1–7). Descriptions are translated here:

| Agent | name | description (excerpt) | model | color | tools |
|-------|------|------------------|-------|-------|-------|
| context-agent | `context-agent` | Prewrite research; produce a writing brief. | `inherit` | `blue` | `Read, Grep, Bash` |
| data-agent | `data-agent` | Extract facts from prose and generate commit artifacts. | `inherit` | `green` | `Read, Write, Bash` |
| deconstruction-agent | `deconstruction-agent` | Reference-book deconstruction subagent for /webnovel-init… | `inherit` | `purple` | `Read, Grep, Bash` |
| reviewer | `reviewer` | Unified review agent. Check each dimension… | `inherit` | `yellow` | `Read, Grep, Bash` |

Against agent-development rules:

- **Single `.md` file**: ✅ All comply.
- **Required name/description/model/color fields**: ✅ Present for all 4.
  - `model: inherit` follows the official recommendation (`agent-development/SKILL.md:100,105`).
  - Colors: `blue/green/purple/yellow`. ⚠️ Official `agent-development/SKILL.md:111` lists
    `blue, cyan, green, yellow, magenta, red`, **not `purple`**. The deconstruction agent's
    `color: purple` is outside that enumeration (it should be `magenta`). This is a **minor specification deviation**,
    with no functional/registration impact because color is only for the UI.
- **Minimal `tools` set**: ✅ All use small sets of 3 tools (least privilege, consistent with `SKILL.md:134`).
- **FLAG: Do `tools` include `Agent` or `AskUserQuestion`?** → ❌ **None do**.
  All 4 use combinations of `{Read, Grep/Write, Bash}`; **none** have `Agent`/`AskUserQuestion`/`Task`.
  → Consistent with the plan's rule that subagents must not use `Agent`/`AskUserQuestion`; **no violations**.
- **FLAG: Missing required frontmatter fields?** → None. All 4 have every required field.
- **FLAG: Depend on external `agents/references/*` hidden manuals?** → No. `agents/references/` does not exist,
  and none of the agent bodies reference it. (Frequent `${SCRIPTS_DIR}/webnovel.py` references are runtime script calls,
  not hidden manual files.)
- **`skills:` frontmatter?** → **None** of the 4 agents have it (Grep `^(name|skills):` finds only `name:`).
  No agent currently preloads Skill content.

---

## 4. Skill Frontmatter Audit (8)

Field-by-field inventory (`name`/`allowed-tools` below; every skill's `name:` is on line 2). Descriptions are translated:

| Skill | name | Trigger description | allowed-tools |
|-------|------|-------------------|---------------|
| webnovel-write | `webnovel-write` | Produce a publishable chapter through context → drafting → review → polishing → commit → backup. | `Read Write Edit Grep Bash Agent AskUserQuestion` |
| webnovel-init | `webnovel-init` | Deep initialization of a web-novel project. Collect information interactively in stages… | `Read Write Edit Grep Bash Agent AskUserQuestion WebSearch WebFetch` |
| webnovel-plan | `webnovel-plan` | Generate volume outlines, timelines, and chapter outlines from the master outline… | `Read Write Edit Bash AskUserQuestion` |
| webnovel-review | `webnovel-review` | Use the review Agent to assess chapter quality… | `Read Grep Write Edit Bash Agent AskUserQuestion` |
| webnovel-query | `webnovel-query` | Query settings, characters, power systems, factions, foreshadowing… | `Read Grep Bash` |
| webnovel-learn | `webnovel-learn` | Extract successful patterns from the current conversation into project_memory.json | `Read Bash` |
| webnovel-dashboard | `webnovel-dashboard` | Launch the read-only novel-management dashboard… | `Bash Read` |
| webnovel-doctor | `webnovel-doctor` | This skill should be used when the user asks to "/webnovel-doctor", "check the project environment"… | `Read Bash` |

Against skill-development rules:

- **Directory + SKILL.md structure**: ✅ All 8 contain `SKILL.md` (each passed `test -f`).
- **Frontmatter includes `name` + trigger `description`**: ✅ All have both.
  - Officially, only `name` + `description` are required (`skill-development/SKILL.md:33-34`).
  - Trigger wording: 7 use Chinese action/scenario phrases, as preferred by the plan; `webnovel-doctor` uses the official English
    "This skill should be used when…" pattern with embedded Chinese trigger phrases. Both forms satisfy the specific-trigger requirement.
  - `webnovel-doctor` also has `version: 0.1.0` (an extra, harmless field).
- **Presence and values of `allowed-tools`**: ✅ **All 8 skills declare it** (see table).
  - The 4 orchestration skills (write/init/plan/review) include **`Agent`** (write/init/review)
    and **`AskUserQuestion`** (write/init/plan/review). This is the **top-level skill / command layer's** pre-approved tool set
    for delegating to subagents and asking users questions, **not subagent `tools`**. It matches the plan's role division:
    orchestration in skills, execution in agents.
  - Read-only skills (query/learn/dashboard/doctor) limit `allowed-tools` to `Read/Bash(/Grep)`, with no `Agent`/`AskUserQuestion`.

> Note: official `skill-development/SKILL.md` **never mentions** `allowed-tools` (it requires only `name` + `description`).
> Therefore, **local official skill documentation cannot directly establish** that `allowed-tools` means pre-approval rather than restriction. See §5.

---

## 5. Official Tool-Behavior Assumptions Used by the Plan (Runtime Baseline)

Cross-check source (actual path used):
**`C:/Users/lcy/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/`**
(The primary path exists; fallback `.tmp/plugin-dev-official/...` **does not exist** and was not used.)
Three skills were checked: `agent-development/`, `skill-development/`, and `plugin-structure/`, including their `references/` and `examples/`.

Conclusions and local verifiability:

| # | Assumption used by the plan | Verified by local official docs? | Evidence / annotation |
|---|----------------|---------------------|-------------|
| (a) | **A subagent cannot spawn another subagent** | ❌ Not found | Grep across plugin-dev for `spawn / another (sub)?agent / nested / recursi` found only MCP process spawning, **no prohibition on nested subagents**. → **Plan assertion, not locally verified**. Supporting but not conclusive evidence: `command-development/SKILL.md:720` says Claude launches agents with the **Task tool**, a higher-level/command-side action. No example shows a subagent invoking Task, but absence of examples is not an explicit prohibition. |
| (b) | **`Agent` / `AskUserQuestion` are not subagent tools** | ⚠️ Partial, indirect | Official common agent tool sets (`agent-development/SKILL.md:122-140`) contain only `Read/Write/Grep/Glob/Bash`, **never** `Agent`/`AskUserQuestion`. `AskUserQuestion` appears only in **command/skill-level** `allowed-tools` (`plugin-dev/commands/create-plugin.md:12`, `plugin-settings/examples/create-settings-command.md:3`), not agent frontmatter. → Supported by **official convention**, but **not explicitly prohibited**. All 4 local agents also omit these tools (§3). |
| (c) | **`tools` / `disallowedTools` control subagent tool boundaries** | ⚠️ Half verified | `tools`: ✅ Explicit in `agent-development/SKILL.md:124` (restrict to specific tools), `:132` (omitting it gives access to all tools), and `:134` (least privilege). `disallowedTools`: ❌ **No Grep matches** anywhere in plugin-dev. → `tools` locally verified; `disallowedTools` a plan assertion, not locally verified. |
| (d) | **Agent `skills:` frontmatter preloads the entire Skill into the subagent** | ❌ Not found | Official frontmatter docs list only `name/description/model/color/tools` (`SKILL.md:122` section and `:340-342` table), **not `skills:`**. Tree-wide Grep for `skills:` in agent context found nothing. → **Plan assertion, not locally verified**. No local agent uses it (§3), so even if valid it is a future capability. |
| (e) | **Skill `allowed-tools` means pre-approval, not restriction** | ❌ Not found | `skill-development/SKILL.md` **never mentions** `allowed-tools`; official examples use it only in **command** frontmatter (`command-development` / `plugin-settings`). Local official docs **do not define** its pre-approval/non-restriction semantics. → **Plan assertion, not locally verified**. Experience suggests this behavior, but the audit does not invent citations from memory and therefore marks it unverified. |

Additional verified registration/dispatch facts supporting the plan's wiring:

- Auto-discovery scans `agents/*.md` and `skills/*/SKILL.md` (`plugin-structure/SKILL.md:11,28-32`; `skill-development/SKILL.md:271-273`). ✅
- Agent namespaces: bare `agent-name` for one plugin; `plugin:subdir:agent-name` with subdirectories (`agent-development/SKILL.md:283-285`). ✅
- Higher-level orchestration launches agents with the **Task tool** (`command-development/SKILL.md:720`). ✅

---

## 6. Conclusions / Risk Inventory

### Consistent with the Plan (No Blockers)

1. All 4 on-disk agent names (`context-agent` / `data-agent` / `deconstruction-agent` / `reviewer`) **exactly match**
   the portion after the colon in the plan's `webnovel-writer:<agent>` references. No wrong or missing names.
2. All 8 skill directory names match their `name:` values and comply with the structure (directory + SKILL.md, name + trigger description).
3. **No agent's `tools` include `Agent` / `AskUserQuestion` / `Task`**. The plan's no-dispatch-tools-in-subagents boundary
   is **already satisfied**, with no prerequisite fix.
4. No required agent frontmatter fields are missing, and no agent depends on a hidden `agents/references/*` manual (the directory does not exist).
5. No agent uses `skills:` preloading, so even if assumption (d) holds it does not conflict with the current state.
6. All 8 skills explicitly declare `allowed-tools`; orchestration/read-only roles match the plan.

### Risks to Plan Assumptions (Follow-Up / Runtime Tests Required)

- **R1 (name format, pending runtime verification)**: official agent-development documentation uses **bare `agent-name`** as the canonical
  single-plugin/no-subdirectory identifier, not `plugin:agent`. The plan consistently uses prefixed names such as `webnovel-writer:context-agent`.
  **The names themselves are correct**, but Phase 1 must **test at runtime** whether Agent/Task resolves the prefixed form.
  If only bare names resolve, update the plan. This audit cannot run the Agent tool from its subagent context to settle the question.
- **R2 (tool behavior, not locally verified; see §5)**: assumptions (a), no nested subagents; (d), agent `skills:` preloads an entire Skill;
  and (e), skill `allowed-tools` is pre-approval, have **no source in local official plugin-dev documentation**. Neither does
  `disallowedTools` in (c), nor an explicit prohibition for (b). Treat them as **plan assertions, not locally verified**.
  Designing around them is permissible, but key changes such as replacing large references with `skills:` preloading or chained subagent
  delegation require **small runtime tests** during implementation, not documentation alone.
- **R3 (minor specification deviation, non-blocking)**: `deconstruction-agent`'s `color: purple` is outside the official enumeration
  (`blue/cyan/green/yellow/magenta/red`). This affects only UI coloring, not functionality. Strict compliance would use `magenta`.
  This read-only audit makes no change.

### One-Sentence Summary

Registration names and frontmatter are **highly consistent with the plan, with no incorrect names or `Agent`/`AskUserQuestion` violations**;
implementation must still **runtime-test R1's `webnovel-writer:<agent>` prefix format** and **verify R2's locally undocumented tool behavior with tests**.
