#!/usr/bin/env python3
"""Install project-local portable skills, without changing host settings."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile

REPO = Path(__file__).resolve().parents[1]
ENGINE = ".webnovel-writer-engine"


def install(workspace: Path, host: str, *, dry_run: bool = False, legacy: bool = False) -> list[Path]:
    if host not in {"codex", "antigravity"}:
        raise ValueError("Host must be codex or antigravity")
    if legacy and host != "antigravity":
        raise ValueError("Legacy .agent discovery is only for Antigravity")
    workspace = workspace.expanduser().resolve()
    source = REPO / "webnovel-writer"
    skills = sorted((source / "skills").glob("*/SKILL.md"))
    if not skills or not (source / "scripts" / "webnovel.py").is_file():
        raise ValueError("Run this installer from a complete repository checkout")
    discovery = workspace / (".agent" if legacy else ".agents") / "skills"
    targets = [workspace / ENGINE] + [discovery / p.parent.name for p in skills]
    for target in targets:
        for parent in target.parents:
            if parent == workspace:
                break
            if parent.is_symlink():
                raise ValueError(f"Refusing symlinked installation parent: {parent}")
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Refusing to overwrite existing installation: {target}")
    if dry_run:
        return targets
    workspace.mkdir(parents=True, exist_ok=True)
    # Stage the complete engine and wrappers before publishing any of them.
    with tempfile.TemporaryDirectory(prefix="webnovel-install-", dir=workspace) as temp:
        staging = Path(temp)
        shutil.copytree(source, staging / ENGINE, ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", ".pytest_cache", "node_modules", ".env", ".DS_Store"))
        template = (REPO / "integrations" / "adapter.md").read_text(encoding="utf-8")
        for skill in skills:
            name = skill.parent.name
            folder = staging / name
            folder.mkdir()
            description = next(line.removeprefix("description: ") for line in
                               skill.read_text(encoding="utf-8").splitlines()
                               if line.startswith("description: "))
            content = template.replace("{{NAME}}", name).replace("{{DESCRIPTION}}", description)
            (folder / "SKILL.md").write_text(content, encoding="utf-8")
        (staging / ENGINE / "portable-install.json").write_text(json.dumps({
            "host": host, "source": str(REPO), "skills": [p.parent.name for p in skills]
        }, indent=2), encoding="utf-8")
        discovery.mkdir(parents=True, exist_ok=True)
        (staging / ENGINE).rename(targets[0])
        for skill, target in zip(skills, targets[1:]):
            (staging / skill.parent.name).rename(target)
    return targets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--host", choices=("codex", "antigravity"), required=True)
    parser.add_argument("--dry-run", action="store_true", help="Print destinations without writing")
    parser.add_argument("--legacy-antigravity", action="store_true", help="Use .agent instead of .agents")
    args = parser.parse_args()
    try:
        paths = install(args.workspace, args.host, dry_run=args.dry_run, legacy=args.legacy_antigravity)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Installation stopped: {exc}\n")
    print("Planned destinations:" if args.dry_run else "Installed project-local skills:")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
