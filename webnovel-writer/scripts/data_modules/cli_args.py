#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'CLI argument compatibility helpers. Most data_modules commands use argparse subparsers, whose global options must precede the subcommand: python -m data_modules.index_manager --project-root X get-core-entities. Writing workflows frequently put --project-root afterward: python -m data_modules.index_manager get-core-entities --project-root X. This normally raises "unrecognized arguments" (see the issues7 logs). Lightweight argv preprocessing extracts --project-root from any position and moves it to the front, supporting both forms without rewriting the parsers.'

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from typing import List, Optional, Tuple


def _extract_flag_value(argv: List[str], flag: str) -> Tuple[Optional[str], List[str]]:
    """
    Extract a flag value from argv.

    Supports:
    - --flag VALUE
    - --flag=VALUE

    Returns:
    - (value, remaining_argv)
    - value uses the *last* occurrence when repeated.
    - if a dangling `--flag` has no value, it is kept in remaining_argv for argparse to raise.
    """
    value: Optional[str] = None
    rest: List[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == flag:
            if i + 1 < len(argv):
                value = argv[i + 1]
                i += 2
                continue
            # Dangling flag; keep it so argparse can error out properly.
            rest.append(token)
            i += 1
            continue
        if token.startswith(flag + "="):
            value = token.split("=", 1)[1]
            i += 1
            continue
        rest.append(token)
        i += 1
    return value, rest


def normalize_global_project_root(argv: List[str], *, flag: str = "--project-root") -> List[str]:
    """
    Normalize argv so a global `--project-root` (when present) is moved before subcommands.

    This makes argparse+subparsers accept both:
    - `... --project-root X cmd ...`
    - `... cmd ... --project-root X`
    """
    value, rest = _extract_flag_value(argv, flag)
    if value is None:
        return argv
    return [flag, value] + rest


def _resolve_json_arg_file(target: str, *, base_dir: str | Path | None = None) -> Path:
    path = Path(target).expanduser()
    if not path.is_absolute() and base_dir is not None:
        path = Path(base_dir) / path
    resolved = path.resolve()
    if base_dir is not None:
        base = Path(base_dir).expanduser().resolve()
        try:
            resolved.relative_to(base)
        except ValueError as exc:
            raise ValueError(f"json arg file outside allowed directory: {resolved}") from exc
    return resolved


def load_json_arg(raw: str, *, base_dir: str | Path | None = None) -> Any:
    'Parse a CLI JSON argument as either an inline JSON string such as \'{"a":1}\' or an @file path such as \'@data.json\', avoiding shell-quoting problems. The special value \'@-\' reads stdin. When base_dir is supplied, the referenced file must be inside that directory.'
    if raw is None:
        raise ValueError("missing json arg")
    text = str(raw).strip()
    if text.startswith("@"):
        target = text[1:].strip()
        if not target:
            raise ValueError("invalid json arg: '@' without path")
        if target == "-":
            content = sys.stdin.read()
        else:
            content = _resolve_json_arg_file(target, base_dir=base_dir).read_text(encoding="utf-8")
        return json.loads(content)
    return json.loads(text)
