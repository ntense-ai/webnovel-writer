"""English project directories with non-destructive legacy layout discovery.

Directory names are presentation, not schema keys. Existing Chinese projects
keep their directories; new projects use English. This module never renames or
creates directories. If both spellings exist, the English directory wins.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DIRECTORIES = {
    'chapters': '正文',
    'outlines': '大纲',
    'settings': '设定集',
    'reviews': '审查报告',
}


def project_dir(root: str | Path, name: str) -> Path:
    root = Path(root)
    canonical = next((key for key, legacy in DIRECTORIES.items() if name in (key, legacy)), None)
    if canonical is None:
        raise ValueError(f'Unknown project directory: {name}')
    english = root / canonical
    legacy = root / DIRECTORIES[canonical]
    if english.exists():
        return english
    if legacy.exists():
        return legacy
    # Keep partial legacy projects in one layout; never auto-migrate old books.
    legacy_layout = any((root / old).exists() for old in DIRECTORIES.values()) and not any((root / key).exists() for key in DIRECTORIES)
    return legacy if legacy_layout else english


FILENAMES = {
    '世界观.md': 'worldbuilding.md', '力量体系.md': 'power-system.md',
    '主角卡.md': 'protagonist.md', '女主卡.md': 'heroine.md',
    '主角组.md': 'protagonist-team.md', '反派设计.md': 'antagonist.md',
    '风格契约.md': 'style-guide.md', '总纲.md': 'master-outline.md',
    '复合题材-融合逻辑.md': 'hybrid-genre.md', '爽点规划.md': 'payoff-plan.md',
}
_VOLUME_SUFFIXES = {'详细大纲.md': 'outline.md', '时间线.md': 'timeline.md',
                    '节拍表.md': 'beats.md', '总纲写回.json': 'master-outline-update.json'}


def _english_filename(name: str) -> str:
    if name in FILENAMES:
        return FILENAMES[name]
    match = re.fullmatch(r'第(\d+)章(?:[-—_ ](.+))?\.md', name)
    if match:
        suffix = f'-{match[2]}' if match[2] else ''
        return f'chapter-{int(match[1]):04d}{suffix}.md'
    match = re.fullmatch(r'第(\d+)卷', name)
    if match:
        return f'volume-{int(match[1])}'
    match = re.fullmatch(r'第(\d+)卷-(.+)', name)
    if match and match[2] in _VOLUME_SUFFIXES:
        return f'volume-{int(match[1])}-{_VOLUME_SUFFIXES[match[2]]}'
    match = re.fullmatch(r'第(\d+)章审查报告\.md', name)
    if match:
        return f'chapter-{int(match[1])}-review.md'
    return name


def _legacy_filename(name: str) -> str:
    reverse = {value: key for key, value in FILENAMES.items()}
    if name in reverse:
        return reverse[name]
    match = re.fullmatch(r'chapter-(\d+)(?:-(.+))?\.md', name)
    if match and match[2] != 'review':
        suffix = f'-{match[2]}' if match[2] else ''
        return f'第{int(match[1]):04d}章{suffix}.md'
    match = re.fullmatch(r'volume-(\d+)', name)
    if match:
        return f'第{int(match[1])}卷'
    match = re.fullmatch(r'volume-(\d+)-(.+)', name)
    suffixes = {value: key for key, value in _VOLUME_SUFFIXES.items()}
    if match and match[2] in suffixes:
        return f'第{int(match[1])}卷-{suffixes[match[2]]}'
    match = re.fullmatch(r'chapter-(\d+)-review\.md', name)
    if match:
        return f'第{int(match[1])}章审查报告.md'
    return name


def project_path(root: str | Path, relative: str | Path) -> Path:
    """Resolve a known project file; existing spellings win over new defaults."""
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Project path must be relative and cannot contain ..')
    if not relative.parts or relative.parts[0] not in (*DIRECTORIES, *DIRECTORIES.values()):
        return Path(root) / relative
    directory = project_dir(root, relative.parts[0])
    tail = relative.parts[1:]
    if not tail:
        return directory
    parent = directory
    for part in tail:
        english, legacy = _english_filename(part), _legacy_filename(part)
        english = _english_filename(legacy)
        legacy = _legacy_filename(english)
        preferred = english if directory.name in DIRECTORIES else legacy
        candidates = [parent / name for name in (preferred, part, legacy, english)]
        parent = next((candidate for candidate in candidates if candidate.exists()), parent / preferred)
    return parent



def main() -> None:
    parser = argparse.ArgumentParser(description='Resolve English or legacy book directories without changing files')
    parser.add_argument('--project-root', required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--directory', choices=list(DIRECTORIES))
    group.add_argument('--path', help='Logical relative project file, in either naming convention')
    args = parser.parse_args()
    if args.path:
        print(project_path(args.project_root, args.path))
    elif args.directory:
        print(project_dir(args.project_root, args.directory))
    else:
        print(json.dumps({key: str(project_dir(args.project_root, key)) for key in DIRECTORIES}, ensure_ascii=False))


if __name__ == '__main__':
    main()
