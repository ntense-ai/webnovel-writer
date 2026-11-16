# Plugin Best Practices Deep Review

Scope: `webnovel-writer/` Claude Code plugin source directory
Review date: 2026-06-03
Rollback correction: 2026-06-04

## Current Conclusion

**Best-practice compliance: medium-high.**

The plugin has solid engineering foundations, directory organization, version synchronization, test coverage, and source packaging. However, some non-blocking gaps remain under the strict agent/skill metadata criteria of Anthropic's official `plugin-dev` guidance.

This report reflects the rollback on 2026-06-04: Codex's additional English agent trigger descriptions, `When to invoke` sections, and the `deconstruction-agent` color change to `magenta` have been reverted.

## Completed / Verified

- `.claude-plugin/plugin.json` exists and its manifest is readable.
- Version synchronization passes: `Versions are in sync: 6.0.0`.
- Prompt integrity tests pass.
- The full pytest suite passes.
- The plugin source subdirectory contains `README.md` and `LICENSE`.
- The initialization collection model for `webnovel-init` has moved to `references/init-collection-schema.md`.
- Structured node examples for `webnovel-plan` have moved to `references/outlining/chapter-planning.md`.
- `webnovel-query/references/system-data-flow.md` is marked legacy; outdated references to `/webnovel-resume` and "6 agents in parallel" have been corrected.
- `docs/superpowers/` has been archived to `docs/archive/superpowers/`, and active entry links have been corrected.
- Historical snapshots in `docs/architecture/` have been archived to `docs/archive/architecture/`, and active entry links have been corrected.

## Rollback Details

The following additional Codex changes were reverted:

- English `Use this agent when...` trigger descriptions for 4 agents.
- `## When to invoke` scenario sections at the start of those 4 agent bodies.
- `deconstruction-agent`'s `color: magenta`, restored to `color: purple`.

Agent frontmatter at the time of this review:

- `context-agent`: Short Chinese description, `model: inherit`, `color: blue`
- `data-agent`: Short Chinese description, `model: inherit`, `color: green`
- `deconstruction-agent`: Chinese description, `model: inherit`, `color: purple`
- `reviewer`: Chinese description, `model: inherit`, `color: yellow`

## Remaining Best-Practice Gaps

### Agent metadata

The official `agent-development` documentation recommends more explicit trigger wording in agent descriptions and invocation scenarios in the body. The requested rollback restored the state from the original Claude conversation, so these gaps remain:

- Descriptions are short or rely on internal terminology.
- No `When to invoke` scenarios.
- `deconstruction-agent`'s `purple` is not among the colors listed by the official `validate-agent.sh`; that script lists `blue`, `cyan`, `green`, `yellow`, `magenta`, and `red`.

These are not runtime blockers. Strict compliance with the official validator would require separate confirmation that these metadata changes are acceptable.

### Cross-platform shell assumptions

Several SKILL.md files still contain Bash-style snippets such as `export`, `${VAR}`, `cat`, and `for ch in $(seq ...)`. The README or operations documentation should explain that these assume the Claude Code Bash tool or a compatible shell.

### Live loading validation

File-level and test-level validation passed, but an actual Claude Code plugin enable/load flow has not yet been tested in a clean directory.

## Verification Record

```powershell
python -X utf8 webnovel-writer\scripts\sync_plugin_version.py --check --expected-version 6.0.0
$env:PYTHONUTF8='1'; python -m pytest webnovel-writer\scripts\data_modules\tests\test_prompt_integrity.py -q --no-cov
$env:PYTHONUTF8='1'; python -m pytest -q --no-cov
```

Results:

- Version synchronization: passed
- Prompt integrity: passed
- Full pytest suite: passed

## Final Assessment

The B/C completion work requested in the original Claude conversation is complete, with the rolled-back agent metadata preserved. If the next goal is strict official-validator compliance, explicit user agreement is needed before changing agent descriptions, invocation scenarios, and the `deconstruction-agent` color again.
