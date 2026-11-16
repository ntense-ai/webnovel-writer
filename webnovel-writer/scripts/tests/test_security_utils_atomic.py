from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest

import security_utils
from security_utils import AtomicWriteError, atomic_write_json, read_json_safe


def test_atomic_write_retries_transient_permission_error(tmp_path, monkeypatch):
    """A transient WinError 5 clears within the backoff window: the main issue #125 scenario."""
    target = tmp_path / "memory_scratchpad.json"
    target.write_text('{"old": true}', encoding="utf-8")

    real_replace = security_utils.os.replace
    calls = {"n": 0}

    def flaky_replace(src, dst):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise PermissionError(5, "Access denied.")
        return real_replace(src, dst)

    sleeps: list[float] = []
    monkeypatch.setattr(security_utils.os, "replace", flaky_replace)
    monkeypatch.setattr(security_utils.time, "sleep", sleeps.append)

    atomic_write_json(target, {"new": 1}, use_lock=False, backup=False)

    assert read_json_safe(target) == {"new": 1}
    assert calls["n"] == 3
    assert sleeps == [0.02, 0.04]  # Exponential backoff
    assert not list(tmp_path.glob("*.tmp"))  # No temporary files remain after success


def test_atomic_write_raises_when_target_stays_locked(tmp_path, monkeypatch):
    """Persistent contention raises AtomicWriteError after retries in production mode, preserving the original."""
    monkeypatch.delenv("WEBNOVEL_TEST_RELAX_ATOMIC_REPLACE", raising=False)
    target = tmp_path / "state.json"
    target.write_text("{}", encoding="utf-8")

    def always_denied(src, dst):
        raise PermissionError(5, "Access denied.")

    monkeypatch.setattr(security_utils.os, "replace", always_denied)
    monkeypatch.setattr(security_utils.time, "sleep", lambda _s: None)

    with pytest.raises(AtomicWriteError):
        atomic_write_json(target, {"x": 1}, use_lock=False, backup=False)

    assert read_json_safe(target) == {}
    assert not list(tmp_path.glob("*.tmp"))  # Failure cleans temporary files


def test_atomic_write_relaxed_fallback_still_writes(tmp_path, monkeypatch):
    """The test-sandbox fallback with WEBNOVEL_TEST_RELAX_ATOMIC_REPLACE=1 overwrites after exhausted retries."""
    monkeypatch.setenv("WEBNOVEL_TEST_RELAX_ATOMIC_REPLACE", "1")
    target = tmp_path / "state.json"
    target.write_text("{}", encoding="utf-8")

    def always_denied(src, dst):
        raise PermissionError(5, "Access denied.")

    monkeypatch.setattr(security_utils.os, "replace", always_denied)
    monkeypatch.setattr(security_utils.time, "sleep", lambda _s: None)

    atomic_write_json(target, {"x": 1}, use_lock=False, backup=False)

    assert read_json_safe(target) == {"x": 1}


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific replace sharing conflict")
def test_atomic_write_survives_real_windows_file_hold(tmp_path):
    """Reproduce issue #125: another thread holds the target open without FILE_SHARE_DELETE;
    os.replace raises WinError 5 until the handle is released within the backoff window."""
    target = tmp_path / "memory_scratchpad.json"
    target.write_text('{"old": true}', encoding="utf-8")

    opened = threading.Event()

    def hold():
        with open(target, "r", encoding="utf-8"):
            opened.set()
            time.sleep(0.15)

    t = threading.Thread(target=hold)
    t.start()
    try:
        assert opened.wait(timeout=2)
        atomic_write_json(target, {"new": 1}, use_lock=False, backup=False)
    finally:
        t.join()

    assert read_json_safe(target) == {"new": 1}
