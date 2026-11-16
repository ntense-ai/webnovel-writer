# Webnovel Writer Multi-Host and Multi-Agent Adaptation Spec

> Date: 2026-06-05
> Status: Draft v2
> Baseline: Current `master` plugin; `.claude-plugin/plugin.json` and marketplace version `6.1.0`
> Source: Rewritten from the PR #110 review, correcting obsolete descriptions of seven Skills / hooks / doctor / runtime
> Purpose: Evolve Webnovel Writer into a verifiable, generatable, gracefully degradable multi-host writing plugin without disrupting Claude Code

---

## 1. Background

PR #110 points in the right direction: Webnovel Writer should not remain bound exclusively to Claude Code's conventions. It already has a complete writing runtime, Story System, RAG, Dashboard, Agent responsibilities, and release validation. Multi-host adaptation is a reasonable next step.

However, the original PR #110 spec used an outdated baseline:

- It listed seven Skills, omitting `/webnovel-doctor`.
- It described hooks as lacking bootstrap, although main already has `hooks/hooks.json`, `session_start.py`, and `guard_runtime_write.py`.
- It omitted `project-status`, `doctor`, `write-gate`, `projections retry/replay`, and `.webnovel/projection_log.jsonl` from the target design.
- It put new documents under `docs/superpowers/specs/`, although `superpowers` is now archived under `docs/archive/superpowers/`.

This spec therefore redefines multi-host adaptation against the current `v6.1.0` runtime.

---

## 2. Actual Current Baseline

### 2.1 Claude Code Plugin Structure

The plugin root is `webnovel-writer/`, following the official `plugin-dev` Claude Code structure:

```text
webnovel-writer/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── context-agent.md
│   ├── data-agent.md
│   ├── deconstruction-agent.md
│   └── reviewer.md
├── skills/
│   ├── webnovel-init/
│   ├── webnovel-plan/
│   ├── webnovel-write/
│   ├── webnovel-review/
│   ├── webnovel-query/
│   ├── webnovel-learn/
│   ├── webnovel-dashboard/
│   └── webnovel-doctor/
├── hooks/
│   ├── hooks.json
│   ├── session_start.py
│   └── guard_runtime_write.py
├── scripts/
├── references/
├── templates/
├── genres/
└── dashboard/
```

### 2.2 Current Eight Skills

| Skill | Current responsibility | Multi-host role |
|---|---|---|
| `/webnovel-init` | Initialize a book project | Retain as project-creation entry |
| `/webnovel-plan` | Plan volume/chapter outlines and runtime contracts | Retain as planning entry |
| `/webnovel-write` | Main chapter workflow: gates, agents, commit, projection | Highest-priority multi-host workflow |
| `/webnovel-review` | Review a chapter range | Retain as independently callable quality entry |
| `/webnovel-query` | Read-only project-state, setting, and memory queries | Cross-host read-only query entry |
| `/webnovel-learn` | Append project experience memory | Controlled-write entry |
| `/webnovel-dashboard` | Launch read-only Dashboard | Preserve Claude Code main path; other hosts may fall back to CLI guidance |
| `/webnovel-doctor` | Phase-aware checks of directories, files, DB, RAG, dependencies | Required post-installation self-check on every host |

### 2.3 Current Four Agents

| Current file | Responsibility | Target canonical name |
|---|---|---|
| `context-agent.md` | Assemble pre-writing context and brief | `webnovel-context-agent` |
| `reviewer.md` | Multidimensional review and blocking issues | `webnovel-reviewer` |
| `data-agent.md` | Extract commit artifacts; never write projections directly | `webnovel-data-agent` |
| `deconstruction-agent.md` | Reference-book analysis and structural learning | `webnovel-deconstruction-agent` |

Do not immediately delete or rename current files: existing Skills and user habits may reference them. Introduce canonical names through compatible migration.

### 2.4 Current Runtime CLI

All deterministic actions enter through `scripts/webnovel.py`. Reuse these commands across hosts rather than rewriting business logic per host.

| Command | Purpose |
|---|---|
| `preflight` | Quick environment and project-root checks |
| `project-status` | Short machine-readable status, phase, next step |
| `doctor` | Phase-aware project diagnostics and repair advice |
| `write-gate` | Validate three natural boundaries: prewrite, precommit, postcommit |
| `story-system` | Story System contracts and runtime data |
| `chapter-commit` | Commit chapter facts and drive projection |
| `projections retry/replay` | Retry/replay projections from existing commits |
| `status` | Existing high-level creative-health report; preserve its semantics |

### 2.5 Current Hooks

Claude Code plugin-level hooks already exist:

- `SessionStart`: Runs only `project-status --format summary` to give a new session short status.
- `PreToolUse`: Fallback protection against direct writes to dangerous paths such as `.story-system/commits/`, `.webnovel/state.json`, `index.db`, `vectors.db`, `memory_scratchpad.json`, and `projection_log.jsonl`.

Hooks are lightweight guards, not business state machines.

### 2.6 Current Validation

Two foundations already exist:

- `scripts/validate_plugin_package.py`: Applies official `plugin-dev` principles to manifest, Skill/Agent frontmatter, hook wrapper, README version, and portable paths.
- `scripts/run_behavior_evals.py` + `evals/fixtures/behavior/fast.json`: Checks key behavioral contracts of eight Skills, Agent boundaries, commit/projection, and read-only Dashboard semantics.

Extend these foundations rather than inventing unrelated validation systems.

---

## 3. Goals

### 3.1 One-Sentence Goal

Upgrade Webnovel Writer from a Claude Code-only plugin to:

> A long-form writing plugin whose sole business core is the existing Python runtime and Story System, with lightweight generated adapters for multiple hosts.

### 3.2 Specific Goals

1. Preserve existing Claude Code installation, Skills, Agents, hooks, and CLI experience.
2. Let Codex, Cursor, Gemini CLI, OpenCode, GitHub Copilot CLI, and other hosts consume the same capabilities through adapters.
3. Reuse `scripts/webnovel.py` and `data_modules` everywhere; do not duplicate Story System, commit, projection, doctor, or gate logic.
4. Verify each host's support through manifest validation, smoke tests, and behavior evals.
5. Define explicit fallbacks for hosts without subagents/hooks; never pretend unsupported capabilities were invoked.
6. Keep all new components compliant with official `plugin-dev` structure, frontmatter, hooks, paths, and validation requirements.

---

## 4. Non-Goals

This spec does not:

- Rewrite the Story System main workflow.
- Dismantle the existing eight Skills.
- Change the old creative-health semantics of `webnovel.py status`.
- Redesign `doctor`, `project-status`, `write-gate`, or `projection_log` into a parallel system.
- Turn hooks into hidden business workflows.
- Automatically start Docker, Dashboard, RAG services, or external dependencies.
- Reactivate `docs/superpowers/`; active architecture specs belong in `docs/architecture/`.
- Promise external host capabilities without official documentation and local verification.

---

## 5. Design Principles

### 5.1 Runtime Is the Sole Business Source of Truth

Skills, Agents, hooks, and adapters are entry/scheduling layers. Actions that modify project facts must enter runtime:

```text
Skill / host command
    ↓
webnovel.py
    ↓
data_modules
    ↓
.story-system commit
    ↓
projection read-models
```

No host adapter may directly write `.story-system/commits/` or `.webnovel/*` read models.

### 5.2 Claude Code Remains the Primary Host

Preserve its current experience:

- Keep `.claude-plugin/plugin.json` in the official location.
- Keep `skills/`, `agents/`, and `hooks/` at plugin-root level.
- Continue `${CLAUDE_PLUGIN_ROOT}` in Claude hooks, as required by official `plugin-dev`.
- Keep `/webnovel-*` Skill names valid.

### 5.3 Keep Adapters Thin

Adapters handle only:

- Manifest / metadata
- Tool-name mapping
- Agent frontmatter conversion
- Command exposure
- Hook capability fallback
- Smoke/eval invocation

Adapters do not:

- Rewrite writing workflows
- Interpret Story System
- Validate chapter artifacts
- Execute projections
- Maintain their own project state

### 5.4 Do Not Trust Handwritten Capability Matrices

External hosts change quickly. Do not treat unverified claims about current support as permanent facts.

Each adapter needs `support.md` or equivalent containing:

- Official documentation links
- Verification date
- Supported manifest fields
- Supported skill / command / agent / hook / MCP capabilities
- Fallbacks for unsupported capabilities
- Corresponding repository smoke-test commands

### 5.5 UTF-8 First

All new scripts and adapter generators must explicitly use UTF-8:

- Retain UTF-8 Python file headers.
- Read/write text with `encoding="utf-8"`.
- Prefer `python -X utf8` for Windows subprocesses.
- Do not depend on system-default GBK.

### 5.6 Incremental Migration

Introduce multi-host support gradually:

1. Lock down the baseline and validation.
2. Add adapter directories and generator.
3. Migrate canonical Agent names and Skill wording.
4. Add cross-host smoke/evals.

Do not rename all Agents or overhaul Skills in one step; protect existing Claude Code users.

---

## 6. Target Architecture

### 6.1 Proposed Structure

```text
webnovel-writer/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── webnovel-init/
│   ├── webnovel-plan/
│   ├── webnovel-write/
│   ├── webnovel-review/
│   ├── webnovel-query/
│   ├── webnovel-learn/
│   ├── webnovel-dashboard/
│   ├── webnovel-doctor/
│   └── using-webnovel-writer/        # Optional cross-host usage and tool mapping
├── agents/
│   ├── context-agent.md              # Legacy-name compatibility
│   ├── reviewer.md                   # Legacy-name compatibility
│   ├── data-agent.md                 # Legacy-name compatibility
│   ├── deconstruction-agent.md       # Legacy-name compatibility
│   └── aliases.json                  # Optional legacy-to-canonical mapping
├── hooks/
│   ├── hooks.json                    # Claude Code source hooks
│   ├── session_start.py
│   └── guard_runtime_write.py
├── adapters/
│   ├── README.md
│   ├── registry.json                 # Host adapter registry
│   ├── claude/
│   ├── codex/
│   ├── cursor/
│   ├── gemini/
│   ├── opencode/
│   └── copilot/
├── scripts/
│   ├── webnovel.py
│   ├── validate_plugin_package.py
│   ├── run_behavior_evals.py
│   └── generate_host_artifacts.py    # New non-Claude adapter generator
├── evals/
│   └── fixtures/
├── references/
├── templates/
├── genres/
└── dashboard/
```

Notes:

- `adapters/` contains adapter sources/templates, not generated output.
- `dist/` holds generated host packages and is not committed by default.
- Only small, stable manifests requiring direct host discovery may be committed, after passing drift checks.

### 6.2 Business Sources and Generated Output

| Type | Path | Source of truth? | Commit? |
|---|---|---:|---:|
| Claude plugin manifest | `.claude-plugin/plugin.json` | Yes | Yes |
| Skill sources | `skills/*/SKILL.md` | Yes | Yes |
| Agent sources | `agents/*.md` | Yes | Yes |
| Claude hook sources | `hooks/hooks.json`, `hooks/*.py` | Yes | Yes |
| Runtime | `scripts/`, `data_modules/` | Yes | Yes |
| Adapter templates | `adapters/<host>/` | Yes | Yes |
| Generator | `scripts/generate_host_artifacts.py` | Yes | Yes |
| Generated non-Claude package | `dist/<host>/webnovel-writer/` | No | No |
| Small host-manifest snapshot | `.codex-plugin/plugin.json`, etc. | Host-dependent | Requires drift check |

---

## 7. Environment Variables and Paths

### 7.1 Preserve Claude Code Paths

Continue using this in Claude Code plugin components:

```text
${CLAUDE_PLUGIN_ROOT}
```

Official `plugin-dev` recommends it. Do not blindly replace paths in Claude hooks or Skills for cross-host compatibility.

### 7.2 Compatible Runtime Resolution

Python runtime may support a generic plugin-root resolution order:

1. Explicit CLI argument.
2. `WEBNOVEL_PLUGIN_ROOT`.
3. `CLAUDE_PLUGIN_ROOT`.
4. Derivation upward from the current script path.

This is runtime compatibility, not a reason to rename the primary variable in Claude plugin documentation.

### 7.3 Paths in Skill Instructions

Keep executable Claude Code examples in this form:

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/scripts/webnovel.py" ...
```

Put cross-host explanations in `using-webnovel-writer` or `skills/*/references/host-tools.md`; do not pack every host's variables into every Skill body.

---

## 8. Skill Adaptation

### 8.1 Preserve All Eight Business Skills

Do not remove existing Skills or accidentally leave `/webnovel-doctor` Claude-only.

Every Skill must have:

- `name` and a concrete trigger-oriented `description` in `SKILL.md`.
- Only workflow, boundaries, and necessary commands in the main body.
- Detailed tool mappings, host differences, and reference rules in `references/`.
- Deterministic validation through runtime commands, not natural-language reminders.

### 8.2 Optional General Entry Skill

May add:

```text
skills/using-webnovel-writer/SKILL.md
```

Purposes:

- Unified usage guidance for non-Claude hosts.
- Tool-name mapping for the current host.
- Start with `project-status`, then `doctor` when needed.
- Explain fallback modes without subagents/hooks.

Limits:

- Does not replace the eight business Skills.
- Does not duplicate their complete workflows.
- Does not contain genre knowledge or Story System schemas.

### 8.3 Chapter-Writing Requirements

`webnovel-write` is the core acceptance target. Every host must preserve:

1. `write-gate --stage prewrite` before writing.
2. `write-gate --stage precommit` before committing.
3. Fact submission exclusively through `chapter-commit`.
4. `write-gate --stage postcommit` after committing.
5. `projections retry --chapter N` guidance after projection failure.
6. No direct manual read-model writes.

---

## 9. Agent Adaptation

### 9.1 Canonical Names and Legacy Compatibility

Use the `webnovel-` prefix:

| Legacy name | Canonical name |
|---|---|
| `context-agent` | `webnovel-context-agent` |
| `reviewer` | `webnovel-reviewer` |
| `data-agent` | `webnovel-data-agent` |
| `deconstruction-agent` | `webnovel-deconstruction-agent` |

Migration:

1. Declare mappings in documentation and adapter registry.
2. Make the generator emit canonical names for each host.
3. Gradually update Skill bodies to canonical names.
4. Retain legacy names for at least one minor-version cycle.

### 9.2 Agent Boundaries

Every host must preserve:

- `context-agent`: Pre-writing context and brief only.
- `reviewer`: Review and blocking output only.
- `data-agent`: Commit artifacts only; no direct projection writes.
- `deconstruction-agent`: Reference analysis and accumulated learning only.

### 9.3 Hosts Without Subagents

If reliable subagent invocation is unavailable:

- Enter compatibility mode.
- The main agent follows the same brief and artifact schemas.
- Explicitly report "No subagent invoked; compatibility mode used."
- Still pass `artifact_validator`, `write-gate`, and behavior evals.
- Never claim an unavailable subagent was called.

---

## 10. Hook Adaptation

### 10.1 Preserve Claude Code Hooks

The valid baseline is:

```text
hooks/hooks.json
hooks/session_start.py
hooks/guard_runtime_write.py
```

Continue official `plugin-dev` compliance:

- `hooks/hooks.json` uses the wrapper format with outer `description` and `hooks`.
- Command hooks use `${CLAUDE_PLUGIN_ROOT}`.
- Hook scripts perform only lightweight, deterministic, quick-exit checks.

### 10.2 Other Host Hooks Are Optional

Support is determined by the adapter's `support.md` and smoke tests.

Without hooks:

- Core writing still works.
- Explicit `project-status` / `doctor` / `write-gate` commands fill the gap.
- No critical capability may exist only in a hook.

### 10.3 Hook Prohibitions

Hooks must not:

- Automatically write commits.
- Automatically edit prose.
- Automatically edit settings.
- Automatically install dependencies.
- Automatically start persistent services.
- Write chapter-workflow state.

---

## 11. Doctor and Status Entry Points

### 11.1 Shared Status Entry

All hosts use:

```bash
python -X utf8 "<PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" project-status --format summary
```

When short status reports a problem, run:

```bash
python -X utf8 "<PLUGIN_ROOT>/scripts/webnovel.py" --project-root "<PROJECT_ROOT>" doctor --format text
```

### 11.2 No Second Status System

`status` retains high-level creative-health reporting.

Only `project-status` supplies short status.

Only `doctor` supplies deep diagnostics.

### 11.3 Cross-Host Doctor Value

`doctor` is the first post-installation check and must answer:

- Was the project root resolved correctly?
- What is the current phase?
- Which files should exist in that phase?
- Are directories, JSON, and SQLite intact?
- Is RAG configured?
- Are Python dependencies installed?
- Do Dashboard build artifacts exist?
- Have projections failed?
- How should missing items be repaired?

---

## 12. Adapter Design

### 12.1 Registry

Add:

```text
adapters/registry.json
```

Suggested structure:

```json
{
  "schema_version": "webnovel-host-adapter-registry/v1",
  "hosts": {
    "claude": {
      "tier": "primary",
      "source": ".claude-plugin/plugin.json",
      "supports": ["skills", "agents", "hooks"],
      "smoke": "python -X utf8 scripts/validate_plugin_package.py --format json"
    },
    "codex": {
      "tier": "adapter",
      "source": "adapters/codex/",
      "supports": [],
      "smoke": ""
    }
  }
}
```

Do not guess `supports`; substantiate it with that host's `support.md` and smoke tests.

### 12.2 Per-Host Directory

Each adapter contains at least:

```text
adapters/<host>/
├── support.md              # Official-documentation verification record
├── manifest.template.*     # Only when needed
├── tool-mapping.md         # Tool names and fallback rules
├── agent-mapping.json      # Canonical Agent names and host representation
└── smoke.md                # Local verification commands
```

### 12.3 Generator

Add:

```bash
python -X utf8 scripts/generate_host_artifacts.py --target all
python -X utf8 scripts/generate_host_artifacts.py --target codex
python -X utf8 scripts/generate_host_artifacts.py --check
```

The generator:

- Reads adapter registry.
- Reads Skill / Agent / hook sources.
- Generates host manifests.
- Generates host Agent configuration.
- Generates host command / Skill entries.
- Generates a drift manifest.

It does not:

- Modify business sources.
- Download dependencies.
- Rewrite Story System schemas.
- Run writing workflows.

---

## 13. Validation and CI

### 13.1 Package Validator Extensions

Keep `validate_plugin_package.py` as the foundation. Add checks for:

- `adapters/registry.json` schema.
- `support.md` for each adapter.
- Declared smoke commands for each adapter.
- Machine-local absolute paths in generated output.
- Agreement between committed small manifests and generator output.
- Active-spec indexing in `docs/README.md`.

### 13.2 Behavior Eval Extensions

Fast eval already covers eight Skills. Add:

- At least one install / discovery smoke per host.
- At least one `project-status` smoke per host.
- Executable `webnovel-doctor` guidance on every host.
- `webnovel-write` compatibility-mode acceptance on at least one non-Claude host.
- No claims of subagent invocation on hosts without subagents.

### 13.3 Drift Check

If any generated manifests/adapters are committed, CI must run:

```bash
python -X utf8 scripts/generate_host_artifacts.py --check
```

On failure, explain:

- Which source change caused drift.
- Which generation command to rerun.
- Which generated files to commit.

### 13.4 Verify External Capabilities

Recheck official documentation before implementing each host adapter.

Record findings in:

```text
adapters/<host>/support.md
```

Include at least:

- Verification date.
- Official links.
- Supported capabilities.
- Unsupported capabilities.
- This repository's fallback strategy.

---

## 14. Migration Plan

### Phase 0: Lock the Baseline

Goal: Align the spec with current main.

Changes:

- Add this spec under `docs/architecture/`.
- Update `docs/README.md`.
- Do not create an active `docs/superpowers/` directory.

Acceptance:

- Eight Skills documented.
- Current hooks documented.
- doctor, project-status, write-gate, projections, projection_log documented.
- `git diff --check` passes.

### Phase 1: Adapter Research Records and Registry

Goal: Verify external capabilities before building a large generator.

Changes:

- Add `adapters/README.md`.
- Add `adapters/registry.json`.
- Add `support.md` for every target host.
- Record only official-documentation verification and project fallback strategy.

Impact:

- No impact on current Claude Code users.
- No runtime impact.

### Phase 2: Canonical Agent Names and Compatibility Mapping

Goal: Introduce `webnovel-*` names without breaking legacy names.

Changes:

- Add `agents/aliases.json` or equivalent.
- Use canonical names in adapter registry.
- Update behavior evals to prevent legacy/canonical drift.

Impact:

- Existing Claude Code Skills can still call old names.
- Future host generation prefers canonical names.

### Phase 3: Slim Skills and Map Host Tools

Goal: Reduce Claude-only tool expressions in Skill bodies.

Changes:

- Add `skills/using-webnovel-writer/`.
- Put cross-host tool mapping in references.
- Preserve `${CLAUDE_PLUGIN_ROOT}` in Claude Code examples.
- Do not duplicate complete host instructions across eight Skills.

Impact:

- Shorter Skills, easier host consumption.
- Existing Claude Code commands unchanged.

### Phase 4: Generator and Drift Check

Goal: Generate and verify non-Claude adapters.

Changes:

- Add `scripts/generate_host_artifacts.py`.
- Generate `dist/<host>/webnovel-writer/`.
- Extend `validate_plugin_package.py` for adapters.
- Add CI drift check.

Impact:

- New developer tooling; no user-project data changes.
- Generated files uncommitted by default.

### Phase 5: Cross-Host Smoke and Behavior Evals

Goal: Prove discovery, diagnostics, and core execution or explicit fallback.

Changes:

- Extend `run_behavior_evals.py`.
- Discovery / project-status / doctor smoke for every host.
- `webnovel-write` compatibility acceptance on at least one non-Claude host.

Impact:

- Longer pre-release checks.
- More credible adaptation claims.

### Phase 6: Release Documentation and Version Governance

Goal: Users understand each host's support level.

Changes:

- Add README multi-host support table.
- Add non-Claude usage guidance to `docs/guides/commands.md`.
- Add adapter release checks to `docs/operations/plugin-release.md`.
- State per-host support tiers in release notes.

Impact:

- Avoid implying full support everywhere.
- Reduce environment misunderstandings in issues.

---

## 15. Risks and Controls

| Risk | Impact | Control |
|---|---|---|
| Outdated external-host capability claims | Spec quickly becomes inaccurate | Official verification date and links in each `support.md` |
| Duplicated business workflows per host | Logic drift | Adapters call `webnovel.py`; no runtime duplication |
| Agent renaming breaks old workflows | Existing calls fail | Legacy compatibility for at least one minor-version cycle |
| Hooks mistaken for business workflows | Hidden side effects | Only status hints and dangerous-write guards |
| Skill bodies keep growing | High token cost | Details in references, deterministic actions in scripts |
| Generated output drifts | Package/source mismatch | `generate_host_artifacts.py --check` |
| Chinese Windows paths fail | Users cannot run | UTF-8 Python I/O; `python -X utf8` commands |

---

## 16. Acceptance Checklist

- [ ] Existing Claude Code installation remains intact.
- [ ] All eight existing Skills remain discoverable.
- [ ] `/webnovel-doctor` remains and participates in cross-host self-checks.
- [ ] Current hooks retain the plugin-dev wrapper format.
- [ ] `project-status`, `doctor`, `write-gate`, and `projections` are shared cross-host runtime entries.
- [ ] `status` retains its old high-level health-report semantics.
- [ ] Canonical Agent names use `webnovel-`; legacy names have mappings.
- [ ] Every adapter has `support.md` with official verification date and links.
- [ ] Every adapter has a smoke command or explicit blocker.
- [ ] Generator produces non-Claude artifacts.
- [ ] Drift checks detect inconsistent generated output.
- [ ] Package validator covers registry, support.md, and manifest drift.
- [ ] Behavior eval covers eight Skills and at least one non-Claude compatible writing workflow.
- [ ] README/release notes clearly state per-host support tiers.

---

## 17. Conclusion

The point is not to write another plugin, but to:

- Preserve the runtime baseline already delivered in `v6.1.0`.
- Maintain Claude Code as the primary host.
- Expose the same capabilities elsewhere through adapters and a generator.
- Prove usability with doctor, project-status, write-gate, projection logs, and evals.

This keeps future host expansion from fragmenting the project or confusing users with similar-looking entry points that behave differently.
