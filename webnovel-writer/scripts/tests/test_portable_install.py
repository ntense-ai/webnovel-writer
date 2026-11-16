"""Portable host adapters must preserve local skills and the shared engine."""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("portable_install", REPO / "integrations" / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


@pytest.mark.parametrize("host,legacy,folder", [
    ("codex", False, ".agents"), ("antigravity", False, ".agents"),
    ("antigravity", True, ".agent"),
])
def test_install_complete_engine_and_eight_resolvable_skills(tmp_path, host, legacy, folder):
    workspace = tmp_path / "workspace with spaces"
    destinations = installer.install(workspace, host, legacy=legacy)
    assert len(destinations) == 9
    for skill in (workspace / folder / "skills").iterdir():
        text = (skill / "SKILL.md").read_text()
        assert f"name: {skill.name}" in text
        assert "{{" not in text
        assert "Never invent" in text
        engine = skill.parents[2] / ".webnovel-writer-engine"
        assert (engine / "skills" / skill.name / "SKILL.md").is_file()
        assert (engine / "scripts" / "webnovel.py").is_file()
    result = subprocess.run([sys.executable, str(destinations[0] / "scripts" / "webnovel.py"), "--help"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "preflight" in result.stdout
    assert not (workspace / "AGENTS.md").exists()
    assert not (workspace / ".claude").exists()


def test_dry_run_does_not_create_workspace(tmp_path):
    workspace = tmp_path / "absent"
    assert len(installer.install(workspace, "codex", dry_run=True)) == 9
    assert not workspace.exists()


def test_conflict_leaves_other_files_untouched(tmp_path):
    custom = tmp_path / ".agents" / "skills" / "webnovel-write"
    custom.mkdir(parents=True)
    marker = custom / "SKILL.md"
    marker.write_text("Custom instructions")
    with pytest.raises(FileExistsError):
        installer.install(tmp_path, "codex")
    assert marker.read_text() == "Custom instructions"
    assert not (tmp_path / ".webnovel-writer-engine").exists()


def test_refuses_symlinked_discovery_parent(tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".agents").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinked"):
        installer.install(workspace, "codex")
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("host,legacy", [("unknown", False), ("codex", True)])
def test_invalid_options(tmp_path, host, legacy):
    with pytest.raises(ValueError):
        installer.install(tmp_path, host, legacy=legacy)
