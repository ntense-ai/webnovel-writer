#!/usr/bin/env python3
'Shared security utilities for webnovel-writer.\n\nCreated 2026-01-02 after an audit identified path traversal and command injection risks. Centralize security-related input sanitization here.'

import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

from runtime_compat import enable_windows_utf8_stdio
from typing import Any, Dict, Optional, Union

# Try importing filelock, an optional dependency.
try:
    from filelock import FileLock
    HAS_FILELOCK = True
except (ImportError, OSError):
    FileLock = None  # type: ignore[assignment]
    HAS_FILELOCK = False


def sanitize_filename(name: str, max_length: int = 100) -> str:
    'Sanitize a filename against path traversal (CWE-22).\n\nSecurity-critical: addresses traversal in extract_entities.py.\n\nArgs:\n    name: Original filename, potentially containing traversal characters.\n    max_length: Maximum filename length, default 100.\n\nReturn a safe basename with all path information removed. For example, ../../../etc/passwd becomes passwd, and a Windows System32 path becomes System32. Ordinary character names remain usable.\n\nRemove directory traversal, absolute-path components, and special characters; enforce a length limit.'
    # Step 1: retain only the basename, removing path components.
    safe_name = os.path.basename(name)

    # Step 2: remove path separators as defense in depth.
    safe_name = safe_name.replace('/', '_').replace('\\', '_')

    # Step 3: retain only safe characters.
    # Allow CJK characters (\u4e00-\u9fff), Latin letters, digits, underscores, and hyphens.
    safe_name = re.sub(r'[^\w\u4e00-\u9fff-]', '_', safe_name)

    # Step 4: collapse repeated underscores for readability.
    safe_name = re.sub(r'_+', '_', safe_name)

    # Step 5: enforce the length limit.
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]

    # Step 6: trim leading and trailing underscores.
    safe_name = safe_name.strip('_')

    # Step 7: ensure a nonempty result defensively.
    if not safe_name:
        safe_name = "unnamed_entity"

    return safe_name


def sanitize_commit_message(message: str, max_length: int = 200) -> str:
    'Sanitize Git commit messages against command injection (CWE-77).\n\nSecurity-critical: addresses injection in backup_manager.py.\n\nArgs:\n    message: Original message, possibly containing Git flags.\n    max_length: Maximum message length, default 200.\n\nReturn a message with dangerous flags and characters removed. Strip multiline injection, double-dash flags, quoting ambiguity, and leading single-letter flags.'
    # Step 1: remove newlines to prevent multiline argument injection.
    safe_msg = message.replace('\n', ' ').replace('\r', ' ')

    # Step 2: remove Git flag prefixes beginning with two hyphens.
    safe_msg = re.sub(r'--[\w-]+', '', safe_msg)

    # Step 3: remove quotes to prevent argument-delimiter confusion.
    safe_msg = safe_msg.replace("'", "").replace('"', '')

    # Step 4: remove leading hyphens to prevent single-letter flags such as -m.
    safe_msg = safe_msg.lstrip('-')

    # Step 5: collapse repeated spaces.
    safe_msg = re.sub(r'\s+', ' ', safe_msg)

    # Step 6: enforce the length limit.
    if len(safe_msg) > max_length:
        safe_msg = safe_msg[:max_length]

    # Step 7: trim surrounding whitespace.
    safe_msg = safe_msg.strip()

    # Step 8: ensure a nonempty result.
    if not safe_msg:
        safe_msg = "Untitled commit"

    return safe_msg


def create_secure_directory(path: str, mode: int = 0o700) -> Path:
    'Create a directory with owner-only access where supported.\n\nSecurity-critical: addresses missing permission configuration.\n\nArgs:\n    path: Directory path.\n    mode: Permission mode, default 0o700 (owner read/write/execute).\n\nReturn a Path. On Unix, restrict access to the owner rather than other group members. Windows uses its inherited permissions for compatibility.'
    path_obj = Path(path)

    # On Windows, passing mode can cause unexpected ACL behavior, including immediate loss of access.
    # Preserve inherited permissions on Windows; pass mode only on Unix-like platforms.
    if os.name == 'nt':
        os.makedirs(path, exist_ok=True)
    else:
        os.makedirs(path, mode=mode, exist_ok=True)

    # Explicitly set permissions as defense in depth; some systems ignore makedirs mode.
    if os.name != 'nt':  # Unix platforms: Linux and macOS.
        os.chmod(path, mode)

    return path_obj


def create_secure_file(file_path: str, content: str, mode: int = 0o600) -> None:
    'Create a file with owner-only read/write permissions where supported.\n\nArgs:\n    file_path: Destination path.\n    content: File contents.\n    mode: Permission mode, default 0o600.\n\nOn Unix, other users are denied access.'
    # Create the file.
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Set permissions on Unix only.
    if os.name != 'nt':
        os.chmod(file_path, mode)


def validate_integer_input(value: str, field_name: str) -> int:
    'Strictly validate and convert integer input.\n\nSecurity-critical: addresses weak validation in update_state.py.\n\nArgs:\n    value: Input string.\n    field_name: Field label for error messages.\n\nReturn the converted integer. Raise ValueError for invalid input. For example, 123 converts to integer 123; abc is rejected.'
    try:
        return int(value)
    except ValueError:
        print(f"❌ Error: {field_name} must be an integer; received: {value}", file=sys.stderr)
        raise ValueError(f"Invalid integer input for {field_name}: {value}")


# ============================================================================
# Git environment detection for graceful fallback.
# ============================================================================

# Cache Git availability.
_git_available: Optional[bool] = None


def is_git_available() -> bool:
    'Check whether Git is available.\n\nCache the boolean result to avoid repeated checks and support graceful fallback in environments without Git.'
    global _git_available

    if _git_available is not None:
        return _git_available

    import subprocess

    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        _git_available = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        _git_available = False

    return _git_available


def is_git_repo(path: Union[str, Path]) -> bool:
    'Return whether the specified directory is a Git repository.\n\nArgs:\n    path: Directory to inspect.'
    if not is_git_available():
        return False

    path = Path(path)
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def git_graceful_operation(
    args: list,
    cwd: Union[str, Path],
    *,
    fallback_msg: str = "Git unavailable; skipping version-control operation"
) -> tuple:
    'Run a Git operation, gracefully skipping it when Git is unavailable.\n\nArgs:\n    args: Git arguments without the git executable.\n    cwd: Working directory.\n    fallback_msg: Message shown when falling back.\n\nReturn (success, output, was_skipped), where was_skipped indicates Git was unavailable. For example, pass ["add", "."] with a project cwd and use a local fallback when skipped.'
    if not is_git_available():
        print(f"⚠️  {fallback_msg}", file=sys.stderr)
        return False, "", True

    import subprocess

    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )
        return result.returncode == 0, result.stdout, False
    except subprocess.TimeoutExpired:
        print(f"⚠️  Git operation timed out: git {' '.join(args)}", file=sys.stderr)
        return False, "", False
    except OSError as e:
        print(f"⚠️  Git operation failed: {e}", file=sys.stderr)
        return False, "", False


# ============================================================================
# Atomic file writes prevent concurrency conflicts and corruption.
# ============================================================================


class AtomicWriteError(Exception):
    'Exception raised when an atomic write fails.'
    pass


def _replace_with_retry(
    temp_path: Union[str, Path],
    file_path: Union[str, Path],
    *,
    attempts: int = 10,
    first_delay: float = 0.02,
    max_delay: float = 0.5,
) -> None:
    'Retry os.replace with backoff for PermissionError only.\n\nOn Windows, editors, antivirus tools, sync clients, and indexers may briefly hold a destination without FILE_SHARE_DELETE, causing WinError 5. Short retries bridge these millisecond-scale locks (issue #125). Raise the last PermissionError when retries are exhausted.'
    delay = first_delay
    for attempt in range(attempts):
        try:
            os.replace(temp_path, file_path)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(delay)
            delay = min(delay * 2, max_delay)


def atomic_write_json(
    file_path: Union[str, Path],
    data: Dict[str, Any],
    *,
    use_lock: bool = True,
    backup: bool = True,
    indent: int = 2
) -> None:
    'Atomically write JSON to prevent concurrent-write conflicts and corruption (CWE-362, CWE-367).\n\nSecurity-critical: protects state.json writes. Write a temporary file in the destination directory, optionally acquire an exclusive filelock and back up the original, then replace the destination atomically.\n\nArgs:\n    file_path: Destination path.\n    data: Dictionary to serialize.\n    use_lock: Enable file locking (requires filelock).\n    backup: Back up the original before writing.\n    indent: JSON indentation, default 2.\n\nRaise AtomicWriteError on failure. Temporary files protect against interrupted writes; filelock protects concurrency; backups support restoration.'
    file_path = Path(file_path)
    parent_dir = file_path.parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    # Prepare JSON content.
    try:
        json_content = json.dumps(data, ensure_ascii=False, indent=indent)
    except (TypeError, ValueError) as e:
        raise AtomicWriteError(f"JSON serialization failed: {e}")

    # Lock file path.
    lock_path = file_path.with_suffix(file_path.suffix + '.lock')
    backup_path = file_path.with_suffix(file_path.suffix + '.bak')

    # Place the temporary file beside the destination so os.replace stays on one filesystem.
    fd, temp_path = tempfile.mkstemp(
        suffix='.tmp',
        prefix=file_path.stem + '_',
        dir=parent_dir
    )

    try:
        # Step 1: write the temporary file.
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(json_content)
            f.flush()
            os.fsync(f.fileno())  # Ensure contents reach disk.

        # Step 2: acquire the lock if available and enabled.
        lock = None
        if use_lock and HAS_FILELOCK:
            lock = FileLock(str(lock_path), timeout=10)
            lock.acquire()

        try:
            # Step 3: back up an existing file if backups are enabled.
            if backup and file_path.exists():
                try:
                    import shutil
                    shutil.copy2(file_path, backup_path)
                except OSError:
                    pass  # Backup failure does not block the write.

            # Step 4: replace atomically, retrying transient Windows WinError 5 locks with backoff.
            try:
                _replace_with_retry(temp_path, file_path)
                temp_path = None  # Mark success so cleanup is unnecessary.
            except PermissionError:
                if os.environ.get("WEBNOVEL_TEST_RELAX_ATOMIC_REPLACE") != "1":
                    raise
                # Test sandboxes may permit writes but deny replacement/deletion; never enable this fallback in production.
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(json_content)
                    f.flush()
                    os.fsync(f.fileno())

        finally:
            if lock is not None:
                lock.release()

    except Exception as e:
        raise AtomicWriteError(f"Atomic write failed: {e}")

    finally:
        # Cleanup: remove a remaining temporary file after a failed write.
        if temp_path is not None:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def read_json_safe(
    file_path: Union[str, Path],
    default: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    "Read JSON safely with a default and error handling.\n\nArgs:\n    file_path: Source path.\n    default: Value returned for missing or invalid files.\n\nReturn parsed data or the default. Example: read_json_safe('.webnovel/state.json', {})."
    file_path = Path(file_path)
    if default is None:
        default = {}

    if not file_path.exists():
        return default

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️ Failed to read JSON ({file_path}): {e}", file=sys.stderr)
        return default


def restore_from_backup(file_path: Union[str, Path]) -> bool:
    "Restore a file from its backup.\n\nArgs:\n    file_path: Original file path.\n\nReturn whether restoration succeeded. Example: restore_from_backup('.webnovel/state.json')."
    file_path = Path(file_path)
    backup_path = file_path.with_suffix(file_path.suffix + '.bak')

    if not backup_path.exists():
        print(f"⚠️ Backup file not found: {backup_path}", file=sys.stderr)
        return False

    try:
        import shutil
        shutil.copy2(backup_path, file_path)
        print(f"✅ Restored from backup: {file_path}")
        return True
    except OSError as e:
        print(f"❌ Restore failed: {e}", file=sys.stderr)
        return False


# ============================================================================
# Built-in unit-test self-checks.
# ============================================================================

def _run_self_tests():
    'Run built-in security checks.'
    print("🔍 Running security utility self-tests...")

    # Test 1: sanitize_filename
    assert sanitize_filename("../../../etc/passwd") == "passwd", "Path traversal test failed"
    assert sanitize_filename("C:\\Windows\\System32") == "System32", "Windows path test failed"
    assert sanitize_filename("Élodie") == "Élodie", "Unicode test failed"
    assert sanitize_filename("/tmp/../../../../../etc/hosts") == "hosts", "Complex path traversal test failed"
    assert sanitize_filename("test///file...name") == "file_name", "Special character test failed"  # Dots are replaced.
    print("  ✅ sanitize_filename: All tests passed")

    # Test 2: sanitize_commit_message
    result = sanitize_commit_message("Test\n--author='Attacker'")
    assert "\n" not in result, "Newline was not removed"
    assert "--author" not in result, "Git flag was not removed"
    assert "Attacker" in result, "Content was incorrectly removed"

    assert sanitize_commit_message("--amend Chapter 1") == "Chapter 1", "Git flag test failed"  # --amend is removed entirely.
    assert "'" not in sanitize_commit_message("Test'message"), "Quote test failed"
    assert sanitize_commit_message("-m Test") == "m Test", "Single-letter flag test failed"  # Removing the leading hyphen from -m leaves m Test.
    print("  ✅ sanitize_commit_message: All tests passed")

    # Test 3: validate_integer_input
    assert validate_integer_input("123", "test") == 123, "Integer validation test failed"
    try:
        validate_integer_input("abc", "test")
        assert False, "Expected ValueError"
    except ValueError:
        pass
    print("  ✅ validate_integer_input: All tests passed")

    # Test 4: atomic_write_json
    import tempfile as tf
    test_dir = Path(tf.mkdtemp())
    test_file = test_dir / "test_state.json"

    # Test writing.
    test_data = {"chapter": 10, "unicode_key": "café"}
    atomic_write_json(test_file, test_data, use_lock=False, backup=False)
    assert test_file.exists(), "Atomic write did not create file"

    # Verify reading.
    with open(test_file, 'r', encoding='utf-8') as f:
        loaded = json.load(f)
    assert loaded == test_data, "Atomic write data mismatch"

    # Test backup.
    atomic_write_json(test_file, {"updated": True}, use_lock=False, backup=True)
    backup_file = test_file.with_suffix('.json.bak')
    assert backup_file.exists(), "Backup not created"

    # Test restoration.
    restore_from_backup(test_file)
    with open(test_file, 'r', encoding='utf-8') as f:
        restored = json.load(f)
    assert restored == test_data, "Restored data mismatch"

    # Cleanup.
    import shutil
    shutil.rmtree(test_dir)
    print("  ✅ atomic_write_json: All tests passed")
    if HAS_FILELOCK:
        print("  ℹ️  filelock available; file locking enabled")
    else:
        print("  ⚠️  filelock not installed; file locking unavailable")

    print("\n✅ All security utility tests passed!")


if __name__ == "__main__":
    # Configure Windows UTF-8 output before printing.
    if sys.platform == "win32":
        enable_windows_utf8_stdio()

    # Run self-checks.
    _run_self_tests()
