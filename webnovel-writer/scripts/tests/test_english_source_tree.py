"""Keep the maintained source tree English without restricting story Unicode."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HAN = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')


def test_repository_paths_and_text_have_no_han_literals():
    result = subprocess.run(
        ['git', 'ls-files', '-co', '--exclude-standard', '-z'],
        cwd=ROOT, capture_output=True, check=True,
    )
    problems = []
    for relative in sorted(set(result.stdout.decode().split('\0'))):
        if not relative:
            continue
        path = ROOT / relative
        if not path.is_file():
            continue  # Staged file renames can leave removed source paths in the index.
        if HAN.search(relative):
            problems.append(f'filename: {relative}')
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(content.splitlines(), 1):
            if HAN.search(line):
                problems.append(f'{relative}:{number}')
    assert not problems, 'Non-English source literals remain:\n' + '\n'.join(problems[:40])
