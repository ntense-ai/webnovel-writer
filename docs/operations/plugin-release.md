# Plugin Release Guide

Release notes for this project prioritize Chinese-language web-novel authors: first explain how the release helps them write, then provide CLI, schema, testing, and CI details for maintainers.

## Pre-Release Audit

Release notes must cover all changes from the previous official version tag to the release commit, not just the latest commit.

First establish the version boundary:

```bash
git tag --list "v*" --sort=-v:refname
git log --oneline vPREVIOUS_VERSION..HEAD
git diff --stat vPREVIOUS_VERSION..HEAD
```

Classify changes into four groups:

- Author-facing changes: noticeable improvements to writing, review, planning, queries, recovery, documentation, and other user workflows.
- Compatibility: whether existing book projects need migration or established `/webnovel-*` usage changes.
- Known impact: skipped items, limitations, and risks to note.
- Maintainer details: new CLI commands, schemas, helpers, tests, CI, and internal refactoring.

## Release Note Sources

Every official release must have two documents:

- `CHANGELOG.md`: The long-term changelog.
- `releases/vX.Y.Z.md`: The sole source for the GitHub Release body.

Keep only a one-sentence author-benefit summary in the README, for example:

```md
| **v6.2.0 (current)** | Clearer writing results and easier recovery after failures |
```

Do not use the README as a complete changelog.

## Version Synchronization

After writing `CHANGELOG.md` and `releases/vX.Y.Z.md`, synchronize the version numbers and README summary:

```bash
python -X utf8 webnovel-writer/scripts/sync_plugin_version.py --version X.Y.Z --release-notes "One-sentence author benefit"
```

This command updates:

- `webnovel-writer/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- The `README.md` version badge
- The `README.md` current-version row

## Local Validation

Before committing, run at least:

```bash
python -X utf8 webnovel-writer/scripts/sync_plugin_version.py --check --expected-version X.Y.Z
python -X utf8 webnovel-writer/scripts/validate_release_notes.py --version X.Y.Z
python -X utf8 webnovel-writer/scripts/validate_plugin_package.py
git diff --check
```

For code or prompt changes, also run the relevant pytest suites, behavioral evaluations, or smoke tests, and record results in the verification section of `releases/vX.Y.Z.md`.

## Automated Releases

1. Confirm that local validation passes.
2. Commit and push release notes and version metadata to `master`.
3. The `Plugin Release` workflow automatically:
   - Checks that versions in `plugin.json`, `marketplace.json`, and README match.
   - Checks that `CHANGELOG.md` and `releases/vX.Y.Z.md` exist and cover changes since the previous tag.
   - Validates the plugin package structure.
   - Creates and pushes the `vX.Y.Z` tag.
   - Creates the GitHub Release using `releases/vX.Y.Z.md`.

If the tag already exists, the workflow does not create it again; it also skips an existing GitHub Release. If a previous attempt created the tag but not the Release, rerunning the workflow creates the missing Release.

You can also manually trigger `Plugin Release` from the Actions page as a fallback. Supply `version`, or leave it empty to read the current version from `plugin.json`.

## Automated Version Checks

The `Plugin Version Check` workflow automatically checks on Push / PR that:

- Version metadata is consistent.
- The README version badge is consistent.
- Release notes exist for the current version.
- `CHANGELOG.md` includes the current version.

Trigger files:

- `.claude-plugin/marketplace.json`
- `webnovel-writer/.claude-plugin/plugin.json`
- `webnovel-writer/scripts/sync_plugin_version.py`
- `webnovel-writer/scripts/validate_release_notes.py`
- `README.md`
- `CHANGELOG.md`
- `releases/**`
