#!/usr/bin/env python3
'Chapter file path helpers.\n\nSupported conventions include English paths such as chapters/chapter-0007.md and chapters/volume-1/chapter-0007-title.md, using a consistent English filename convention.\n\nAlways resolve chapter files through these helpers rather than hardcoding a format.'

from __future__ import annotations

import re
from pathlib import Path

from project_paths import project_dir
from typing import Optional


_CHAPTER_NUM_RE = re.compile(r"chapter[-_ ]?(?P<num>\d+)(?=[-_. ]|$)", re.IGNORECASE)
_OUTLINE_HEADING_RE = re.compile(r"^#{1,6}\s*Chapter\s+(?P<num>\d+)\s*[：:]\s*(?P<title>.+?)\s*$", re.MULTILINE | re.IGNORECASE)
_SPLIT_OUTLINE_FILENAME_RE = re.compile(r"^chapter[-_ ]0*(?P<num>\d+)[-—_ ]+(?P<title>.+?)\.md$", re.IGNORECASE)


def volume_num_for_chapter(chapter_num: int, *, chapters_per_volume: int = 50) -> int:
    if chapter_num <= 0:
        raise ValueError("chapter_num must be >= 1")
    return (chapter_num - 1) // chapters_per_volume + 1


def extract_chapter_num_from_filename(filename: str) -> Optional[int]:
    m = _CHAPTER_NUM_RE.search(filename)
    if not m:
        return None
    try:
        return int(m.group("num"))
    except ValueError:
        return None


def _safe_title_for_filename(title: str) -> str:
    cleaned = title.strip()
    if not cleaned:
        return ""

    try:
        from security_utils import sanitize_filename
    except ImportError:  # pragma: no cover
        from scripts.security_utils import sanitize_filename

    safe_title = sanitize_filename(cleaned, max_length=60)
    return "" if safe_title == "unnamed_entity" else safe_title


def _extract_title_from_outline_text(outline_text: str, chapter_num: int) -> str:
    for match in _OUTLINE_HEADING_RE.finditer(outline_text):
        if int(match.group("num")) != chapter_num:
            continue
        return _safe_title_for_filename(match.group("title"))
    return ""


def _extract_title_from_split_outline_filename(outline_dir: Path, chapter_num: int) -> str:
    patterns = [
        f"chapter-{chapter_num:04d}*.md",
        f"chapter-{chapter_num:03d}*.md",
        f"chapter-{chapter_num}*.md",
    ]
    for pattern in patterns:
        for path in sorted(outline_dir.glob(pattern)):
            match = _SPLIT_OUTLINE_FILENAME_RE.match(path.name)
            if not match:
                continue
            if int(match.group("num")) != chapter_num:
                continue
            title = _safe_title_for_filename(match.group("title"))
            if title:
                return title
    return ""


def extract_chapter_title(project_root: Path, chapter_num: int) -> str:
    'Extract the chapter title from its detailed outline for a more descriptive filename.'
    try:
        from chapter_outline_loader import load_chapter_outline
    except ImportError:  # pragma: no cover
        from scripts.chapter_outline_loader import load_chapter_outline

    outline_text = load_chapter_outline(project_root, chapter_num, max_chars=None)
    if not outline_text.startswith("⚠️"):
        title = _extract_title_from_outline_text(outline_text, chapter_num)
        if title:
            return title

    outline_dir = project_dir(project_root, "outlines")
    if outline_dir.exists():
        return _extract_title_from_split_outline_filename(outline_dir, chapter_num)
    return ""


def _build_chapter_filename(project_root: Path, chapter_num: int, *, use_volume_layout: bool) -> str:
    padded = f"{chapter_num:04d}"
    title = extract_chapter_title(project_root, chapter_num)
    return f"chapter-{padded}-{title}.md" if title else f"chapter-{padded}.md"


def find_chapter_file(project_root: Path, chapter_num: int) -> Optional[Path]:
    "Find an existing chapter file under the project's chapter directory.\nReturn the first match in stable sorted order, or None."
    chapters_dir = project_dir(project_root, "chapters")
    if not chapters_dir.exists():
        return None

    # Prefer the canonical untitled filename, then discover titled files.
    candidate = chapters_dir / f"chapter-{chapter_num:04d}.md"
    if candidate.is_file():
        return candidate
    candidates = sorted(chapters_dir.rglob("*.md"))
    for candidate in candidates:
        if candidate.is_file() and extract_chapter_num_from_filename(candidate.name) == chapter_num:
            return candidate

    return None


def default_chapter_draft_path(project_root: Path, chapter_num: int, *, use_volume_layout: bool = False) -> Path:
    'Choose a draft path for a new chapter.\n\nArgs:\n    project_root: Project root directory.\n    chapter_num: Chapter number.\n    use_volume_layout: Use volume subdirectories if True, otherwise a flat layout.\n\nThe default layout is flat. Append a title from the detailed outline when available to improve discoverability.'
    if use_volume_layout:
        chapters_dir = project_dir(project_root, "chapters")
        volume = volume_num_for_chapter(chapter_num)
        volume_name = f"volume-{volume}"
        vol_dir = chapters_dir / volume_name
        return vol_dir / _build_chapter_filename(project_root, chapter_num, use_volume_layout=True)
    else:
        return project_dir(project_root, "chapters") / _build_chapter_filename(project_root, chapter_num, use_volume_layout=False)

