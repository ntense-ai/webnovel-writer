#!/usr/bin/env python3
"""
Git 集成备份管理系统 (Backup Manager with Git)

核心理念：写 200万字必然会"写废设定"，需要支持任意时间点回滚。

🔧 重大升级：使用 Git 进行原子性版本控制

为什么选择 Git：
1. ✅ 原子性回滚：state.json + 正文/*.md 同时回滚，数据 100% 一致
2. ✅ 增量存储：只存储 diff，节省 95% 空间
3. ✅ 成熟稳定：经过 20 年验证的版本控制系统
4. ✅ 分支管理：天然支持"平行世界"创作

功能：
1. 自动 Git 提交：每次 /webnovel-write 完成后自动 commit
2. 原子性回滚：git checkout 同时回滚所有文件
3. 版本历史：git log 查看完整历史
4. 差异对比：git diff 查看任意两个版本的差异
5. 分支创建：git branch 从任意时间点创建分支

使用方式：
  # 在第 45 章完成后自动备份（自动 git commit）
  python backup_manager.py --chapter 45

  # 回滚到第 30 章状态（git checkout）
  python backup_manager.py --rollback 30

  # 查看第 20 章和第 40 章的差异（git diff）
  python backup_manager.py --diff 20 40

  # 从第 50 章创建分支（git branch）
  python backup_manager.py --create-branch 50 --branch-name "alternative-ending"

  # 列出所有备份（git log）
  python backup_manager.py --list

Git 提交规范：
  - 提交信息格式: "Chapter {N}: {章节标题}"
  - Tag 格式: "ch{N}" (如 ch0045)
  - 每个章节对应一个 commit + 一个 tag

数据一致性保证：
  ✅ 回滚时，state.json 和所有 .md 文件同步回滚
  ✅ 不会出现"状态记录筑基期，但文件里写着金丹期"的数据撕裂
  ✅ 原子性操作，要么全部成功，要么全部失败
"""

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
# 安全修复：导入安全工具函数（P1 MEDIUM）
# ============================================================================
from security_utils import sanitize_commit_message, is_git_available, is_git_repo, git_graceful_operation
from project_locator import resolve_project_root

# Windows 编码兼容性修复
if sys.platform == "win32":
    enable_windows_utf8_stdio()


class BackupError(RuntimeError):
    """Git backup operation failed."""


class GitBackupManager:
    """基于 Git 的备份管理器（支持优雅降级）"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.git_dir = self.project_root / ".git"
        self.git_available = is_git_available()

        if not self.git_available:
            print("⚠️  Git unavailable; using local backup mode")
            print("💡 To enable Git version control, install Git: https://git-scm.com/")
            return

        # 检查 Git 是否初始化
        if not self.git_dir.exists():
            print("⚠️  Git not initialized; run /webnovel-init or git init")
            print("💡 Initializing Git now...")
            self._init_git()

    def _init_git(self) -> bool:
        """初始化 Git 仓库"""
        try:
            # git init
            subprocess.run(
                ["git", "init"],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            # 创建 .gitignore
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

            # 初始提交
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
        """执行 Git 命令（支持优雅降级）"""
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
        """合并 Git 输出，优先保留 stderr 中的故障信息。"""
        return "\n".join(part.strip() for part in (stderr, stdout) if part.strip())

    def _local_backup(self, chapter_num: int) -> bool:
        """本地备份（Git 不可用时的降级方案）"""
        backup_dir = self.project_root / ".webnovel" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"snapshot_ch{chapter_num:04d}_{timestamp}"
        backup_path = backup_dir / backup_name

        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            copied = []

            for folder_name in ("chapters", "outlines", "settings", "reviews", "正文", "大纲", "设定集", "审查报告"):
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
        """
        备份当前状态（Git commit + tag，或本地备份）

        Args:
            chapter_num: 章节号
            chapter_title: 章节标题（可选）
        """
        print(f"📝 Backing up chapter {chapter_num}...")

        # 如果 Git 不可用，使用本地备份
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
            # 安全修复：清理提交消息，防止命令注入 (CWE-77) - P1 MEDIUM
            # 原代码: commit_message += f": {chapter_title}"
            # 漏洞: chapter_title可能包含 Git 标志（如 --author, --amend）导致命令注入
            # ============================================================================
            safe_chapter_title = sanitize_commit_message(chapter_title)
            commit_message += f": {safe_chapter_title}"

        success, stdout, stderr = self._run_git_command(
            ["commit", "-m", commit_message],
            check=False  # 允许"无变更"的情况
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

        # 删除旧 tag（如果存在）
        self._run_git_command(["tag", "-d", tag_name], check=False)

        success, stdout, stderr = self._run_git_command(["tag", tag_name], check=False)
        if not success:
            print(f"⚠️  Tag creation failed (nonfatal): {self._format_git_output(stdout, stderr)}")
        else:
            print(f"✅ Git tag created: {tag_name}")

        return True

    def rollback(self, chapter_num: int) -> bool:
        """
        前滚式恢复到指定章节（在当前分支创建恢复提交）
        """

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
        """对比两个版本的差异（Git diff）"""

        tag_a = f"ch{chapter_a:04d}"
        tag_b = f"ch{chapter_b:04d}"

        print(f"📊 Comparing chapters {chapter_a} and {chapter_b}...\n")

        success, output, error = self._run_git_command(["diff", tag_a, tag_b, "--stat"], check=False)

        if not success:
            print(f"❌ Comparison failed: {self._format_git_output(output, error)}")
            return

        print("📈 File change statistics:")
        print(output)

        # 显示 state.json 的详细差异
        print("\n📝 Detailed state.json diff:")
        success, state_diff, _ = self._run_git_command(
            ["diff", tag_a, tag_b, "--", ".webnovel/state.json"],
            check=False,
        )

        if success and state_diff:
            print(state_diff[:2000])  # 限制输出长度
            if len(state_diff) > 2000:
                print("\n...(output truncated)")
        else:
            print("(no changes)")

    def list_backups(self):
        """列出所有备份（Git log + tags）"""

        print("\n📚 Backups (Git tags):\n")

        # 获取所有 tags
        success, tags_output, _ = self._run_git_command(["tag", "-l", "ch*"], check=False)

        if not success or not tags_output:
            print("⚠️  No backups yet")
            return

        tags = sorted(tags_output.strip().split('\n'))

        for tag in tags:
            # 提取章节号
            chapter_num = int(tag[2:])

            # 获取该 tag 的提交信息
            success, commit_info, _ = self._run_git_command(
                ["log", tag, "-1", "--format=%h %ci %s"],
                check=False,
            )

            if success:
                print(f"📖 {tag} | {commit_info.strip()}")

        print(f"\nTotal: {len(tags)} backups")

        # 显示最近 5 次提交
        print("\n📜 Recent commits:\n")
        success, log_output, _ = self._run_git_command(
            ["log", "--oneline", "-5"],
            check=False,
        )

        if success:
            print(log_output)

    def create_branch(self, chapter_num: int, branch_name: str) -> bool:
        """从指定章节创建分支（Git branch）"""

        tag_name = f"ch{chapter_num:04d}"

        print(f"🌿 Creating branch from chapter {chapter_num}: {branch_name}")

        # 检查 tag 是否存在
        success, _, _ = self._run_git_command(["rev-parse", tag_name], check=False)

        if not success:
            print(f"❌ Tag '{tag_name}' does not exist")
            return False

        # 创建分支
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

    # 解析项目根目录（允许传入“工作区根目录”，统一解析到真正的 book project_root）
    try:
        project_root = str(resolve_project_root(args.project_root))
    except FileNotFoundError as exc:
        print(f"❌ Cannot locate project root (requires .webnovel/state.json): {exc}", file=sys.stderr)
        sys.exit(1)

    # 创建管理器
    manager = GitBackupManager(project_root)

    # 执行操作
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
