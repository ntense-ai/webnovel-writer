"""Top-level help is English without changing persisted enum values."""
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


@pytest.mark.parametrize('module', [
    'webnovel', 'migrate_state_to_sqlite', 'index_manager', 'entity_linker',
    'rag_adapter', 'state_manager', 'run_logger', 'run_ledger',
    'sql_state_manager', 'style_sampler', 'memory.store',
])
def test_cli_help_is_english(module):
    scripts = Path(__file__).resolve().parents[2]
    env = {**os.environ, 'PYTHONPATH': str(scripts)}
    result = subprocess.run(
        [sys.executable, '-c', f'from data_modules.{module} import main; main()', '--help'],
        cwd=scripts, env=env, text=True, capture_output=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert 'usage:' in result.stdout
    assert not re.search(r'[\u4e00-\u9fff]', result.stdout)
