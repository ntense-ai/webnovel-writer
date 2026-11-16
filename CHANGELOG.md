# Changelog

This file records the impact of each stable release on authors and maintainers. Release notes prioritize webnovel authors: explain changes to the writing experience first, then add technical details for maintainers.

## v6.3.0 - English-only author workflows for new books

Release range: `v6.2.1..v6.3.0` on the `ntense` fork.

### Changes for Authors

English project paths, schemas, prompts, dashboard, and the complete reference
corpus now support new English-author book workflows. Unicode story content
remains supported. Portable Codex and Antigravity skills reuse the Claude Code
engine, subject to actual host capabilities and independent-review requirements.

### Do Existing Projects Need Changes?

This fork is for new projects only. Old localized schemas and filename aliases
are no longer supported; no automatic migration is provided. Preserve old books
separately on their compatible version.

### For Maintainers

See [v6.3.0 release notes](releases/v6.3.0.md) for verification and host limits.

## v6.2.1 - Fix intermittent Windows access denial during chapter commits

Release range: `v6.2.0..v6.2.1`.

### Changes for Authors

- Fix intermittent `WinError 5 (Access is denied)` during chapter commits on Windows. When VSCode, antivirus software, or a sync client briefly locks story data under `.webnovel/`, the system now waits and retries instead of failing immediately (#125).
- VSCode users should consider adding `**/.webnovel/**` to `files.watcherExclude` and keeping projects outside synchronized folders to reduce lock conflicts further.

### Do Existing Projects Need Changes?

No. Existing book projects continue to work without migration.

### For Maintainers

- `atomic_write_json` now retries `os.replace` on `PermissionError` with exponential backoff (roughly a 2.6-second window), then propagates the error if retries are exhausted. All JSON projections share this writer and benefit from the fix.
- Add four targeted tests, including reproduction using a real locked Windows handle.

### Verification

- Full pytest suite passed (774 passed).
- Version synchronization, release-note validation, and plugin-package validation passed.

## v6.2.0 - Clearer chapter results and better recovery after failures

Release range: `v6.1.0..v6.2.0`.

### Changes for Authors

- Final reports for writing, review, planning, and initialization now read like a writing assistant's summary, clearly distinguishing completed, partially completed, action required, and not completed.
- After `/webnovel-write` is interrupted, rerunning the same chapter first checks trustworthy checkpoints and resumes near the failure where possible, reducing rewrites and accidental overwrites.
- Less technical interruption during writing. Questions are limited to creative direction, factual choices, file-overwrite risks, or blocking issues requiring a decision.
- More selective context reading keeps initialization, planning, writing, review, and queries focused instead of filling context with unrelated material.
- Stronger intermediate-result validation around chapter commits detects missing review, fact extraction, or story-data synchronization results sooner.
- Documentation now explains final reports, recovery boundaries, logs, and common operations entry points.

### Do Existing Projects Need Changes?

No. Existing book projects remain usable without migrating `.story-system/` or `.webnovel/` data.

### For Maintainers

- Add an author glossary, error catalog, author-facing review view, final-report helper, chapter run ledger, and redacted run logs.
- Add unified CLI subcommands `user-report`, `run-ledger`, and `run-log`.
- Tighten structured validation for commit artifacts, projection writers, write-gate, and postcommit.
- Streamline several Skill/Agent prompts and add reference-loading maps and region-read rules.
- Add prompt-integrity tests, unit tests, and behavioral evals covering artifact ownership, minimal writing mode, projection retries, blocking reviews, checkpoint recovery, and log redaction.
- Change the `Plugin Release` workflow to release automatically after pushes to `master`, retaining a manual fallback.

### Verification

- Relevant pytest tests passed.
- Behavioral evals passed.
- `compileall` passed.
- `git diff --check` passed.
- Version synchronization and plugin-package validation passed.

## v6.1.0 - More reliable health checks and easier troubleshooting

- Add doctor, project-status, write-gate, projection replay, hooks, behavioral evaluation, and plugin-package validation.
- Strengthen Story System runtime health checks and Marketplace release validation.

## v6.0.0 - Story System mainline for more consistent long-form facts

- Introduce contract seeds, runtime contracts, chapter commits, event audits, and projection pipelines.
- Complete integration tests for the mainline.
