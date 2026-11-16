#!/usr/bin/env python3
'Git-integrated backup manager.\n\nLong novels inevitably require setting revisions, so support restoring earlier states. Git provides coordinated versions of state.json and chapter Markdown, incremental storage, history, diffs, and branches for alternate storylines.\n\nFeatures: commit after /webnovel-write, restore chapter snapshots, inspect git log and git diff, and branch from earlier chapters.\n\nUsage:\n  python backup_manager.py --chapter 45\n  python backup_manager.py --rollback 30\n  python backup_manager.py --diff 20 40\n  python backup_manager.py --create-branch 50 --branch-name "alternative-ending"\n  python backup_manager.py --list\n\nCommit convention: "Chapter {N}: {chapter_title}"; tag convention: ch{N}, such as ch0045. Each chapter gets a commit and tag. Restoring coordinated state and Markdown avoids inconsistent cultivation levels between state records and chapter text.\n'

import subprocess
import json
import os
import sys
import shutil
from pathlib import Path

from runtime_compat import enable_windows_utf8_stdio
from datetime import datetime
from typing import Optional, List, Tuple

# ============================================================================
# Security fix: import secure utility functions (P1 MEDIUM).
# ============================================================================
from security_utils import sanitize_commit_message, is_git_available, is_git_repo, git_graceful_operation
from project_locator import resolve_project_root

# Windows encoding compatibility.
if sys.platform == "win32":
    enable_windows_utf8_stdio()


class BackupError(RuntimeError):
    """Git backup operation failed."""


class GitBackupManager:
    'Git-based backup manager with graceful fallback.'

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.git_dir = self.project_root / ".git"
        self.git_available = is_git_available()

        if not self.git_available:
            print("⚠️  Git unavailable; using local backup mode")
            print("💡 To enable Git version control, install Git: https://git-scm.com/")
            return

        # Check whether Git is initialized.
        if not self.git_dir.exists():
            print("⚠️  Git not initialized; run /webnovel-init or git init")
            print("💡 Initializing Git now...")
            self._init_git()

    def _init_git(self) -> bool:
        'Initialize the Git repository.'
        try:
            # git init
            subprocess.run(
                ["git", "init"],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            # Create .gitignore.
            gitignore_file = self.project_root / ".gitignore"
            if not gitignore_file.exists():
                with open(gitignore_file, 'w', encoding='utf-8') as f:
                    f.write("""# Python
__pycache__/
*.py[cod]
*.so

# Temporary files
*.tmp
*.bak
.DS_Store

# IDE
.vscode/
.idea/

# Don't ignore .webnovel (we need to track state.json)
# But ignore cache files
.webnovel/context_cache.json

# Env files
.env
.env.*
!.env.example
""")

            # Initial commit.
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            subprocess.run(
                ["git", "commit", "-m", "Initial commit: Project initialized"],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            print("✅ Git repository initialized")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Git initialization failed: {e}")
            return False

    def _run_git_command(self, args: List[str], check: bool = True) -> Tuple[bool, str, str]:
        'Run a Git command with graceful fallback.'
        if not self.git_available:
            return False, "", "Git unavailable"

        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60
            )
            ok = result.returncode == 0
            if check and not ok:
                message = (result.stderr or result.stdout).strip()
                raise BackupError(f"git {' '.join(args)} failed: {message}")
            return ok, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            if check:
                raise BackupError(f"git {' '.join(args)} failed: Git command timed out")
            return False, "", "Git command timed out"
        except OSError as e:
            if check:
                raise BackupError(f"git {' '.join(args)} failed: {e}")
            return False, "", str(e)

    @staticmethod
    def _format_git_output(stdout: str, stderr: str) -> str:
        'Combine Git output, preferring diagnostic information from stderr.'
        return "\n".join(part.strip() for part in (stderr, stdout) if part.strip())

    def _local_backup(self, chapter_num: int) -> bool:
        'Create a local backup when Git is unavailable.'
        backup_dir = self.project_root / ".webnovel" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"snapshot_ch{chapter_num:04d}_{timestamp}"
        backup_path = backup_dir / backup_name

        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            copied = []

            for folder_name in ("chapters", "outlines", "settings", "reviews"):
                source_dir = self.project_root / folder_name
                if source_dir.exists():
                    shutil.copytree(source_dir, backup_path / folder_name)
                    copied.append(folder_name)

            state_file = self.project_root / ".webnovel" / "state.json"
            if state_file.exists():
                target_state_dir = backup_path / ".webnovel"
                target_state_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(state_file, target_state_dir / "state.json")
                copied.append(".webnovel/state.json")

            snapshots = sorted(
                (path for path in backup_dir.glob("snapshot_ch*") if path.is_dir()),
                key=lambda path: path.name,
            )
            for old_snapshot in snapshots[:-10]:
                shutil.rmtree(old_snapshot)

            print(f"✅ Local backup complete: {backup_path}")
            if copied:
                print(f"📦 Backed up: {', '.join(copied)}")
            else:
                print("⚠️  No chapter, outline, setting, review, or state.json files found to back up")
            return True
        except OSError as e:
            print(f"❌ Local backup failed: {e}")
            return False

    def backup(self, chapter_num: int, chapter_title: str = "") -> bool:
        'Back up the current state using a Git commit/tag or a local copy.\n\nArgs:\n    chapter_num: Chapter number.\n    chapter_title: Optional chapter title.'
        print(f"📝 Backing up chapter {chapter_num}...")

        # Fall back to local backups if Git is unavailable.
        if not self.git_available:
            return self._local_backup(chapter_num)

        # Step 1: git add .
        success, stdout, stderr = self._run_git_command(["add", "."], check=False)
        if not success:
            print(f"❌ Backup failed: git add failed: {self._format_git_output(stdout, stderr)}")
            return False

        # Step 2: git commit
        commit_message = f"Chapter {chapter_num}"
        if chapter_title:
            # ============================================================================
            # Security fix: sanitize commit messages against command injection (CWE-77), P1 MEDIUM.
            # Previous code: commit_message += f": {chapter_title}"
            # Vulnerability: chapter_title could contain Git flags such as --author or --amend.
            # ============================================================================
            safe_chapter_title = sanitize_commit_message(chapter_title)
            commit_message += f": {safe_chapter_title}"

        success, stdout, stderr = self._run_git_command(
            ["commit", "-m", commit_message],
            check=False  # Allow the no-changes case.
        )
        commit_output = self._format_git_output(stdout, stderr)

        if not success and "nothing to commit" in commit_output.lower():
            print("⚠️  No chapter changes; skipping commit")
            return True
        elif not success:
            print(f"❌ Backup failed: git commit failed")
            if commit_output:
                print(commit_output)
            print("💡 First run: git config user.name \"Your Name\" && git config user.email \"you@example.com\"")
            return False

        print(f"✅ Git commit complete: {commit_message}")

        # Step 3: git tag
        tag_name = f"ch{chapter_num:04d}"

        # Delete the old tag if present.
        self._run_git_command(["tag", "-d", tag_name], check=False)

        success, stdout, stderr = self._run_git_command(["tag", tag_name], check=False)
        if not success:
            print(f"⚠️  Tag creation failed (nonfatal): {self._format_git_output(stdout, stderr)}")
        else:
            print(f"✅ Git tag created: {tag_name}")

        return True

    def rollback(self, chapter_num: int) -> bool:
        'Restore a chapter snapshot by creating a forward recovery commit on the current branch.'

        tag_name = f"ch{chapter_num:04d}"

        print(f"🔄 Restoring chapter {chapter_num}...")
        print("💾 A restore commit will be created on the current branch; history is preserved")

        success, _, error = self._run_git_command(["rev-parse", "--verify", tag_name], check=False)
        if not success:
            print(f"❌ Backup point {tag_name} does not exist")
            return False

        success, branch, branch_error = self._run_git_command(["symbolic-ref", "--short", "HEAD"], check=False)
        if not success or not branch.strip():
            print(f"❌ Not on a branch; cannot create a restore commit: {self._format_git_output(branch, branch_error)}")
            return False

        success, stdout, stderr = self._run_git_command(["checkout", tag_name, "--", "."], check=False)

        if not success:
            print(f"❌ Restore failed: {self._format_git_output(stdout, stderr)}")
            print(f"💡 Tip: ensure tag '{tag_name}' exists (run --list to view all backups)")
            return False

        success, stdout, stderr = self._run_git_command(["add", "-A"], check=False)
        if not success:
            print(f"❌ Restore failed: {self._format_git_output(stdout, stderr)}")
            return False

        success, stdout, stderr = self._run_git_command(
            ["commit", "-m", f"rollback: restore backup {tag_name}"],
            check=False,
        )
        commit_output = self._format_git_output(stdout, stderr)
        if not success and "nothing to commit" not in commit_output.lower():
            print(f"❌ Restore commit failed: {commit_output}")
            return False

        print(f"✅ Restored chapter {chapter_num} on branch {branch.strip()}!")
        print(f"\n💡 Tips:")
        print(f"  - All tracked files (state.json and chapter files) restored together")
        print(f"  - Commit history preserved; use git log to view the restore")

        return True

    def diff(self, chapter_a: int, chapter_b: int):
        'Compare two versions with Git diff.'

        tag_a = f"ch{chapter_a:04d}"
        tag_b = f"ch{chapter_b:04d}"

        print(f"📊 Comparing chapters {chapter_a} and {chapter_b}...\n")

        success, output, error = self._run_git_command(["diff", tag_a, tag_b, "--stat"], check=False)

        if not success:
            print(f"❌ Comparison failed: {self._format_git_output(output, error)}")
            return

        print("📈 File change statistics:")
        print(output)

        # Display detailed state.json differences.
        print("\n📝 Detailed state.json diff:")
        success, state_diff, _ = self._run_git_command(
            ["diff", tag_a, tag_b, "--", ".webnovel/state.json"],
            check=False,
        )

        if success and state_diff:
            print(state_diff[:2000])  # Limit output length.
            if len(state_diff) > 2000:
                print("\n...(output truncated)")
        else:
            print("(no changes)")

    def list_backups(self):
        'List backups using Git log and tags.'

        print("\n📚 Backups (Git tags):\n")

        # Get all tags.
        success, tags_output, _ = self._run_git_command(["tag", "-l", "ch*"], check=False)

        if not success or not tags_output:
            print("⚠️  No backups yet")
            return

        tags = sorted(tags_output.strip().split('\n'))

        for tag in tags:
            # Extract the chapter number.
            chapter_num = int(tag[2:])

            # Get this tag's commit message.
            success, commit_info, _ = self._run_git_command(
                ["log", tag, "-1", "--format=%h %ci %s"],
                check=False,
            )

            if success:
                print(f"📖 {tag} | {commit_info.strip()}")

        print(f"\nTotal: {len(tags)} backups")

        # Display the five most recent commits.
        print("\n📜 Recent commits:\n")
        success, log_output, _ = self._run_git_command(
            ["log", "--oneline", "-5"],
            check=False,
        )

        if success:
            print(log_output)

    def create_branch(self, chapter_num: int, branch_name: str) -> bool:
        'Create a branch from a specified chapter.'

        tag_name = f"ch{chapter_num:04d}"

        print(f"🌿 Creating branch from chapter {chapter_num}: {branch_name}")

        # Check whether the tag exists.
        success, _, _ = self._run_git_command(["rev-parse", tag_name], check=False)

        if not success:
            print(f"❌ Tag '{tag_name}' does not exist")
            return False

        # Create the branch.
        success, output, error = self._run_git_command(["branch", branch_name, tag_name], check=False)

        if not success:
            print(f"❌ Branch creation failed: {self._format_git_output(output, error)}")
            return False

        print(f"✅ Branch created: {branch_name}")
        print(f"\n💡 Switch to branch:")
        print(f"  git checkout {branch_name}")

        return True

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Git-integrated backup manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Back up chapter 45
  python backup_manager.py --chapter 45
  # Restore chapter 30 with a new commit, preserving history
  python backup_manager.py --rollback 30
  # Compare chapters 20 and 40
  python backup_manager.py --diff 20 40
  # Create a branch from chapter 50
  python backup_manager.py --create-branch 50 --branch-name alternate-story
  # List all backups
  python backup_manager.py --list
        """
    )

    parser.add_argument('--chapter', type=int, help='Chapter number to back up')
    parser.add_argument('--chapter-title', help='Chapter title (optional)')
    parser.add_argument('--rollback', type=int, metavar='CHAPTER', help='Restore the specified chapter')
    parser.add_argument('--diff', nargs=2, type=int, metavar=('A', 'B'), help='Compare two versions')
    parser.add_argument('--create-branch', type=int, metavar='CHAPTER', help='Create a branch from the specified chapter')
    parser.add_argument('--branch-name', help='Branch name')
    parser.add_argument('--list', action='store_true', help='List all backups')
    parser.add_argument('--project-root', default='.', help='Project root')

    args = parser.parse_args()

    # Resolve the actual book project root; a workspace root is also accepted.
    try:
        project_root = str(resolve_project_root(args.project_root))
    except FileNotFoundError as exc:
        print(f"❌ Cannot locate project root (requires .webnovel/state.json): {exc}", file=sys.stderr)
        sys.exit(1)

    # Create the manager.
    manager = GitBackupManager(project_root)

    # Perform the operation.
    if args.chapter:
        manager.backup(args.chapter, args.chapter_title or "")

    elif args.rollback:
        manager.rollback(args.rollback)

    elif args.diff:
        manager.diff(args.diff[0], args.diff[1])

    elif args.create_branch:
        if not args.branch_name:
            print("❌ Creating a branch requires --branch-name")
            sys.exit(1)
        manager.create_branch(args.create_branch, args.branch_name)

    elif args.list:
        manager.list_backups()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
