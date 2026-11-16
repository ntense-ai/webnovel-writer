param(
    [ValidateSet("smoke", "full")]
    [string]$Mode = "smoke",
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
} else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}

Set-Location $ProjectRoot

$tmpRoot = Join-Path $ProjectRoot ".tmp\\pytest"
New-Item -ItemType Directory -Path $tmpRoot -Force | Out-Null

$env:TMP = $tmpRoot
$env:TEMP = $tmpRoot
$env:PYTHONPATH = ".claude/scripts"

# Avoid basetemp permissions or stale locks breaking Windows test setup.
$runId = Get-Date -Format "yyyyMMdd_HHmmssfff"
$baseTemp = Join-Path $tmpRoot ("run-" + $Mode + "-" + $runId)

Write-Host "ProjectRoot: $ProjectRoot"
Write-Host "TMP/TEMP: $tmpRoot"
Write-Host "Mode: $Mode"

# Preflight: WindowsApps Python may create inaccessible temporary directories.
# This causes WinError 5 during temporary-directory creation or cleanup.
@'
import tempfile
from pathlib import Path
import sys

try:
    d = Path(tempfile.mkdtemp(prefix="webnovel_writer_pytest_"))
    # Both directory listing and file writing must work for pytest.
    list(d.iterdir())
    (d / "probe.txt").write_text("ok", encoding="utf-8")
except Exception as exc:
    print(f"PYTEST_TMPDIR_PRECHECK_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
    raise
'@ | python - 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Python temporary-directory preflight failed (WindowsApps shim or permissions)."
    Write-Host "Use standard Python from python.org or an interpreter provided by uv/uvx."
    exit 1
}

if ($Mode -eq "smoke") {
    python -m pytest -q `
        .claude/scripts/data_modules/tests/test_extract_chapter_context.py `
        .claude/scripts/data_modules/tests/test_rag_adapter.py `
        --basetemp $baseTemp `
        --no-cov `
        -p no:cacheprovider
    exit $LASTEXITCODE
}

python -m pytest -q `
    .claude/scripts/data_modules/tests `
    --basetemp $baseTemp `
    -p no:cacheprovider
exit $LASTEXITCODE
