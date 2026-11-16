"""
Path Traversal Guard

Every file-reading API must validate through this module before disk access.
"""

from pathlib import Path
from fastapi import HTTPException


def safe_resolve(project_root: Path, relative: str) -> Path:
    """Resolve a relative path and ensure it remains inside project_root.

    Raises:
        HTTPException 403 if the resolved path escapes project_root.
    """
    try:
        resolved = (project_root / relative).resolve()
    except (OSError, ValueError):
        raise HTTPException(status_code=403, detail="Invalid path")

    # Require the target to be project_root itself or one of its descendants.
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Path outside project root: access denied")

    return resolved
