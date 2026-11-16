#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import sync_plugin_version


ROOT = Path(__file__).resolve().parent.parent.parent
VERSION_RE = sync_plugin_version.VERSION_PATTERN
REQUIRED_RELEASE_HEADINGS = (
    "## Release Scope",
    "## Changes for Authors",
    "## Do Existing Projects Need Changes?",
    "## For Maintainers",
    "## Verification",
)
LEGACY_RELEASE_HEADINGS = (
    "## 发版范围", "## 给作者看的变化", "## 是否需要改旧项目", "## 给维护者", "## 验证",
)
AUTHOR_WORDS = ("author", "chapter", "webnovel", "story", "prose", "作者", "写章", "网文", "故事", "正文")


def _issue(code: str, *, message: str, path: str = "", repair: str = "") -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "repair": repair}


def _load_text(path: Path) -> tuple[str, str]:
    try:
        return path.read_text(encoding="utf-8"), ""
    except FileNotFoundError:
        return "", "missing"
    except OSError as exc:
        return "", f"read_error:{exc}"


def _current_version(root: Path) -> str:
    payload = sync_plugin_version.load_json(root / "webnovel-writer" / ".claude-plugin" / "plugin.json")
    return str(payload.get("version") or "")


def _parse_version_tag(tag: str) -> tuple[int, int, int] | None:
    raw = tag[1:] if tag.startswith("v") else tag
    if not VERSION_RE.fullmatch(raw):
        return None
    major, minor, patch = raw.split(".")
    return int(major), int(minor), int(patch)


def _infer_previous_tag(root: Path, version: str) -> str:
    current = _parse_version_tag(version)
    if current is None:
        return ""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "tag", "--list", "v*"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""
    candidates: list[tuple[tuple[int, int, int], str]] = []
    for line in completed.stdout.splitlines():
        tag = line.strip()
        parsed = _parse_version_tag(tag)
        if parsed and parsed < current:
            candidates.append((parsed, tag))
    if not candidates:
        return ""
    return sorted(candidates)[-1][1]


def _changelog_section(text: str, version: str) -> str:
    heading_re = re.compile(rf"^##\s+v{re.escape(version)}(?:\s|$)", re.MULTILINE)
    match = heading_re.search(text)
    if not match:
        return ""
    next_match = re.search(r"^##\s+", text[match.end():], re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(text)
    return text[match.start():end]


def validate_release_notes(
    root: str | Path | None = None,
    *,
    version: str | None = None,
    previous_tag: str | None = None,
) -> dict[str, Any]:
    repo_root = Path(root) if root is not None else ROOT
    target_version = version or _current_version(repo_root)
    previous = previous_tag or _infer_previous_tag(repo_root, target_version)
    issues: list[dict[str, str]] = []

    if not VERSION_RE.fullmatch(target_version):
        issues.append(_issue("version.invalid", message=f"invalid version: {target_version}", repair="Use an X.Y.Z version number."))

    release_path = repo_root / "releases" / f"v{target_version}.md"
    release_text, release_error = _load_text(release_path)
    if release_error:
        issues.append(
            _issue(
                "release_note.missing",
                message=f"release note {release_path.name} {release_error}",
                path=str(release_path),
                repair="Add releases/vX.Y.Z.md covering all changes since the previous tag.",
            )
        )
    else:
        expected_title = f"# v{target_version} - "
        if not release_text.startswith(expected_title):
            issues.append(
                _issue(
                    "release_note.title",
                    message=f"release note title must start with {expected_title!r}",
                    path=str(release_path),
                    repair="Use '# vX.Y.Z - A one-sentence user benefit' as the title.",
                )
            )
        for heading, legacy in zip(REQUIRED_RELEASE_HEADINGS, LEGACY_RELEASE_HEADINGS):
            if heading not in release_text and legacy not in release_text:
                issues.append(
                    _issue(
                        "release_note.heading",
                        message=f"missing heading: {heading}",
                        path=str(release_path),
                        repair="Use the standard template in releases/README.md.",
                    )
                )
        if previous and previous not in release_text:
            issues.append(
                _issue(
                    "release_note.range",
                    message=f"previous tag {previous} not mentioned",
                    path=str(release_path),
                    repair="State the range from the previous stable tag to this release in Release Scope.",
                )
            )
        if not any(word in release_text.casefold() for word in AUTHOR_WORDS):
            issues.append(
                _issue(
                    "release_note.audience",
                    message="release note does not look author-facing",
                    path=str(release_path),
                    repair="Open the release notes with practical language that webnovel authors understand.",
                )
            )

    changelog_path = repo_root / "CHANGELOG.md"
    changelog_text, changelog_error = _load_text(changelog_path)
    if changelog_error:
        issues.append(
            _issue(
                "changelog.missing",
                message=f"CHANGELOG.md {changelog_error}",
                path=str(changelog_path),
                repair="Add CHANGELOG.md with user-visible changes for each stable version.",
            )
        )
    else:
        current_changelog_section = _changelog_section(changelog_text, target_version)
        if not current_changelog_section:
            issues.append(
                _issue(
                    "changelog.version",
                    message=f"CHANGELOG.md missing v{target_version}",
                    path=str(changelog_path),
                    repair="Add a section for the current version to CHANGELOG.md.",
                )
            )
        if previous and current_changelog_section and previous not in current_changelog_section:
            issues.append(
                _issue(
                    "changelog.range",
                    message=f"CHANGELOG.md does not mention previous tag {previous}",
                    path=str(changelog_path),
                    repair="State the release scope in the current version section.",
                )
            )

    return {
        "schema_version": "webnovel-release-notes-validator/v1",
        "ok": not issues,
        "root": str(repo_root),
        "version": target_version,
        "previous_tag": previous,
        "release_note": str(release_path),
        "changelog": str(changelog_path),
        "issues": issues,
    }


def format_report(report: dict[str, Any], output_format: str = "text") -> str:
    if output_format == "json":
        return json.dumps(report, ensure_ascii=False, indent=2)
    status = "OK" if report.get("ok") else "ERROR"
    lines = [
        f"{status} release notes",
        f"version: {report.get('version')}",
        f"previous_tag: {report.get('previous_tag') or 'unknown'}",
    ]
    for item in report.get("issues") or []:
        lines.append(f"ERROR {item.get('code')}: {item.get('message')}")
        if item.get("path"):
            lines.append(f"  path: {item.get('path')}")
        if item.get("repair"):
            lines.append(f"  repair: {item.get('repair')}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate author-facing release notes and changelog")
    parser.add_argument("--root", default="", help="Repository root; inferred automatically by default")
    parser.add_argument("--version", default="", help="Target version; read from plugin.json by default")
    parser.add_argument("--previous-tag", default="", help="Previous stable tag; inferred from git tags by default")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    report = validate_release_notes(
        args.root or None,
        version=args.version or None,
        previous_tag=args.previous_tag or None,
    )
    print(format_report(report, args.format))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
