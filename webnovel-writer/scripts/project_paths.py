"""Validate and resolve the English-only project layout without changing files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DIRECTORIES = {name: name for name in ('chapters', 'outlines', 'settings', 'reviews')}


def project_dir(root: str | Path, name: str) -> Path:
    if name not in DIRECTORIES:
        raise ValueError(f'Unknown project directory: {name}')
    return Path(root) / name


def project_path(root: str | Path, relative: str | Path) -> Path:
    """Resolve a relative path without renaming or translating user content."""
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Project path must be relative and cannot contain ..')
    return Path(root) / relative


def main() -> None:
    parser = argparse.ArgumentParser(description='Resolve English book directories without changing files')
    parser.add_argument('--project-root', required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--directory', choices=list(DIRECTORIES))
    group.add_argument('--path', help='Relative project file')
    args = parser.parse_args()
    if args.path:
        print(project_path(args.project_root, args.path))
    elif args.directory:
        print(project_dir(args.project_root, args.directory))
    else:
        print(json.dumps({key: str(project_dir(args.project_root, key)) for key in DIRECTORIES}))


if __name__ == '__main__':
    main()
