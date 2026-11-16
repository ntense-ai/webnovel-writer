#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'Unified webnovel entry point requiring no directory change.\n\nExamples:\n  python "<SCRIPTS_DIR>/webnovel.py" preflight\n  python "<SCRIPTS_DIR>/webnovel.py" where\n  python "<SCRIPTS_DIR>/webnovel.py" index stats\n\nAdd this script\'s scripts/ directory to sys.path, then forward to data_modules.webnovel. Supports project-level and user-level (~/.claude) skill/agent installations.'

from __future__ import annotations

import sys
from pathlib import Path

from runtime_compat import enable_windows_utf8_stdio


def main() -> None:
    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))

    # Defer import until sys.path is ready.
    from data_modules.webnovel import main as _main

    _main()


if __name__ == "__main__":
    enable_windows_utf8_stdio(skip_in_pytest=True)
    main()
