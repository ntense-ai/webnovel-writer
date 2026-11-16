# Maintaining Release Notes

Every stable release must add a `vX.Y.Z.md` file here as the sole source of its GitHub Release body.

Release notes are not a summary of the last commit. They cover all user-visible changes between the previous stable tag and the release commit. Before writing, run:

```bash
git tag --list "v*" --sort=-v:refname
git log --oneline <previous-version-tag>..HEAD
git diff --stat <previous-version-tag>..HEAD
```

## Writing Order

1. Establish the release range, for example `v6.1.0..v6.2.0`.
2. Write “Changes for Authors” first, using practical language webnovel authors understand.
3. Add “Do Existing Projects Need Changes?” and “Known Impact.”
4. Finish with “For Maintainers,” recording CLI, schema, test, CI, and internal structural changes.
5. Run `validate_release_notes.py` to check format and scope.
6. After a push to `master`, the `Plugin Release` workflow automatically creates the tag and GitHub Release. Existing tags and releases are not recreated.

## Standard Template

The current validator requires the original Chinese heading strings. Keep the compatibility comments shown below while writing the visible notes in English.

```md
# vX.Y.Z - One sentence describing the benefit for users

## Release Scope
<!-- Compatibility marker: ## 发版范围 -->

This release covers all changes from `vA.B.C` to the release commit.

## Changes for Authors
<!-- Compatibility marker: ## 给作者看的变化 -->

- ...

## Do Existing Projects Need Changes?
<!-- Compatibility marker: ## 是否需要改旧项目 -->

- ...

## Who Should Upgrade?

- ...

## Known Impact

- ...

## For Maintainers
<!-- Compatibility marker: ## 给维护者 -->

- ...

## Verification
<!-- Compatibility marker: ## 验证 -->

- ...
```

Keep only a brief one-sentence summary in the README. Record complete changes in `CHANGELOG.md` and the version files in this directory.
