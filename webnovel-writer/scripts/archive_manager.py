#!/usr/bin/env python3
'state.json archive manager.\n\nKeep long-running novels from growing state.json indefinitely. Archive inactive characters, resolved foreshadowing, and old reviews; check size/chapter triggers; back up safely and restore archived records.\n\nPolicy: supporting characters absent for over 50 chapters go to archive/characters.json; resolved foreshadowing older than 20 chapters goes to archive/plot_threads.json; reviews older than 50 chapters go to archive/reviews.json.\n\nUsage:\n  python archive_manager.py --auto-check  # Recommended after update_state.py\n  python archive_manager.py --force       # Ignore trigger conditions\n  python archive_manager.py --restore-character "Li Xue"\n  python archive_manager.py --stats\n  python archive_manager.py --auto-check --dry-run  # Preview only\n'

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

from runtime_compat import enable_windows_utf8_stdio

# ============================================================================
# Security fix: import secure utility functions (P1 MEDIUM).
# ============================================================================
from security_utils import create_secure_directory, atomic_write_json
from project_locator import resolve_project_root

# Introduced in v5.1: read entities through IndexManager.
try:
    from data_modules.index_manager import IndexManager
    from data_modules.config import get_config
except ImportError:
    from scripts.data_modules.index_manager import IndexManager
    from scripts.data_modules.config import get_config

# Windows UTF-8 encoding compatibility.
if sys.platform == "win32":
    enable_windows_utf8_stdio()


class ArchiveManager:
    'Manage archived state.json data.'

    def __init__(self, project_root=None):
        if project_root is None:
            # Use the current directory by default.
            project_root = Path.cwd()
        else:
            project_root = Path(project_root)

        self.project_root = project_root
        self.state_file = project_root / ".webnovel" / "state.json"
        self.archive_dir = project_root / ".webnovel" / "archive"

        # Introduced in v5.1: IndexManager reads entities.
        self._config = get_config(project_root)
        self._index_manager = IndexManager(self._config)

        # ============================================================================
        # Security fix: create directories securely (P1 MEDIUM).
        # Previous code: self.archive_dir.mkdir(parents=True, exist_ok=True)
        # Vulnerability: OS-default permissions could be 755, exposing data to other users.
        # ============================================================================
        create_secure_directory(str(self.archive_dir))

        # Archive file paths.
        self.characters_archive = self.archive_dir / "characters.json"
        self.plot_threads_archive = self.archive_dir / "plot_threads.json"
        self.reviews_archive = self.archive_dir / "reviews.json"

        # Archival policy configuration.
        self.config = {
            "character_inactive_threshold": 50,  # A character absent for more than 50 chapters is inactive.
            "plot_resolved_threshold": 20,       # Archive resolved foreshadowing after 20 chapters.
            "review_old_threshold": 50,          # Archive reviews after 50 chapters.
            "file_size_trigger_mb": 1.0,         # Force archival when state.json exceeds 1.0 MB.
            "chapter_trigger": 10                # Check every 10 chapters.
        }

    def load_state(self):
        'Load state.json.'
        if not self.state_file.exists():
            print(f"❌ state.json not found: {self.state_file}")
            sys.exit(1)

        with open(self.state_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_state(self, state):
        'Save state.json atomically.'
        # Use centralized atomic writes with automatic backups.
        atomic_write_json(self.state_file, state, use_lock=True, backup=True)
        print(f"✅ state.json updated atomically")

    def load_archive(self, archive_file):
        'Load an archive file.'
        if not archive_file.exists():
            return []

        with open(archive_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_archive(self, archive_file, data):
        'Save an archive file atomically.'
        atomic_write_json(archive_file, data, use_lock=True, backup=True)

    def check_trigger_conditions(self, state):
        'Check whether archiving should be triggered.'
        current_chapter = state.get("progress", {}).get("current_chapter", 0)

        # Trigger 1: file size exceeds the threshold.
        file_size_mb = self.state_file.stat().st_size / (1024 * 1024)
        size_trigger = file_size_mb >= self.config["file_size_trigger_mb"]

        # Trigger 2: chapter count is a multiple of the check interval.
        chapter_trigger = (current_chapter % self.config["chapter_trigger"]) == 0 and current_chapter > 0

        return {
            "should_archive": size_trigger or chapter_trigger,
            "file_size_mb": file_size_mb,
            "current_chapter": current_chapter,
            "size_trigger": size_trigger,
            "chapter_trigger": chapter_trigger
        }

    def identify_inactive_characters(self, state):
        'Identify inactive supporting characters (introduced in v5.1; retained in v5.4).'
        current_chapter = state.get("progress", {}).get("current_chapter", 0)
        threshold = self.config["character_inactive_threshold"]

        # Introduced in v5.1: get all character entities from SQLite.
        characters = self._index_manager.get_entities_by_type("character")

        inactive = []
        for char in characters:
            # Archive only supporting characters: decorative or subplot tiers.
            tier = str(char.get("tier", "")).strip()
            if tier == "core":
                continue

            # Check the last appearance chapter.
            last_appearance = char.get("last_appearance", 0)
            try:
                last_appearance = int(last_appearance)
            except (TypeError, ValueError):
                last_appearance = 0
            if last_appearance <= 0:
                continue

            inactive_chapters = current_chapter - last_appearance

            if inactive_chapters >= threshold:
                char_id = char.get("id", "")
                char_data = {
                    "id": char_id,
                    "name": char.get("canonical_name", char_id),
                    "tier": tier,
                    "last_appearance_chapter": last_appearance
                }
                char_data.update(char)
                inactive.append({
                    "character": char_data,
                    "inactive_chapters": inactive_chapters,
                    "last_appearance": last_appearance
                })

        return inactive

    def identify_resolved_plot_threads(self, state):
        'Identify resolved foreshadowing eligible for archival.'
        current_chapter = state.get("progress", {}).get("current_chapter", 0)
        plot_threads = state.get("plot_threads", {}) or {}
        foreshadowing = plot_threads.get("foreshadowing", []) or []
        resolved_legacy = plot_threads.get("resolved", []) or []
        threshold = self.config["plot_resolved_threshold"]

        archivable = []
        # New format: plot_threads.foreshadowing uses status to mark resolution.
        if isinstance(foreshadowing, list):
            for item in foreshadowing:
                if not isinstance(item, dict):
                    continue
                status = str(item.get("status", "")).strip()
                if status not in ["resolved", "resolved"]:
                    continue
                try:
                    resolved_chapter = int(item.get("resolved_chapter", 0))
                except (TypeError, ValueError):
                    continue
                chapters_since_resolved = current_chapter - resolved_chapter
                if chapters_since_resolved >= threshold:
                    archivable.append({
                        "thread": item,
                        "chapters_since_resolved": chapters_since_resolved,
                        "resolved_chapter": resolved_chapter
                    })

        # Legacy compatibility: plot_threads.resolved directly stores resolved entries.
        if isinstance(resolved_legacy, list):
            for item in resolved_legacy:
                if not isinstance(item, dict):
                    continue
                try:
                    resolved_chapter = int(item.get("resolved_chapter", 0))
                except (TypeError, ValueError):
                    continue
                chapters_since_resolved = current_chapter - resolved_chapter
                if chapters_since_resolved >= threshold:
                    archivable.append({
                        "thread": item,
                        "chapters_since_resolved": chapters_since_resolved,
                        "resolved_chapter": resolved_chapter
                    })

        return archivable

    def identify_old_reviews(self, state):
        'Identify old reviews eligible for archival.'
        current_chapter = state.get("progress", {}).get("current_chapter", 0)
        reviews = state.get("review_checkpoints", [])
        threshold = self.config["review_old_threshold"]

        def _parse_end_chapter(review: dict) -> int:
            # New format: {"chapters":"5-6","report":"...","reviewed_at":"..."}
            chapters = review.get("chapters")
            if isinstance(chapters, str):
                parts = [p.strip() for p in chapters.replace("—", "-").split("-") if p.strip()]
                if parts:
                    try:
                        return int(parts[-1])
                    except ValueError:
                        pass

            # Legacy format: {"chapter_range":[5,6], "date":"..."}
            cr = review.get("chapter_range")
            if isinstance(cr, (list, tuple)) and len(cr) >= 2:
                try:
                    return int(cr[1])
                except (TypeError, ValueError):
                    pass

            # Fallback: extract a chapter range from the report filename, including legacy names.
            report = review.get("report")
            if isinstance(report, str):
                import re
                m = re.search(r"Ch(\d+)[-–—](\d+)", report)
                if m:
                    try:
                        return int(m.group(2))
                    except ValueError:
                        pass
                m = re.search(r"Chapters? (\d+)[-–—](\d+)", report)
                if m:
                    try:
                        return int(m.group(2))
                    except ValueError:
                        pass

            return 0

        old_reviews = []
        for review in reviews:
            review_chapter = _parse_end_chapter(review)
            chapters_since_review = current_chapter - review_chapter

            if chapters_since_review >= threshold:
                old_reviews.append({
                    "review": review,
                    "chapters_since_review": chapters_since_review,
                    "review_chapter": review_chapter
                })

        return old_reviews

    def archive_characters(self, inactive_list, dry_run=False):
        'Archive inactive characters (v5.1: update status through IndexManager).'
        if not inactive_list:
            return 0

        # Load the existing archive.
        archived = self.load_archive(self.characters_archive)

        # Add a timestamp.
        timestamp = datetime.now().isoformat()
        for item in inactive_list:
            item["character"]["archived_at"] = timestamp
            archived.append(item["character"])

            # Introduced in v5.1: update entity status through IndexManager.
            if not dry_run:
                try:
                    entity_id = item["character"].get("id")
                    if entity_id:
                        # Add the archived flag to the entity's current_json.
                        self._index_manager.update_entity_field(
                            entity_id, "status", "archived"
                        )
                except Exception as e:
                    print(f"⚠️ Entity status update failed (archiving can continue): {e}")

        if not dry_run:
            self.save_archive(self.characters_archive, archived)

        return len(inactive_list)

    def archive_plot_threads(self, resolved_list, dry_run=False):
        'Archive resolved foreshadowing.'
        if not resolved_list:
            return 0

        # Load the existing archive.
        archived = self.load_archive(self.plot_threads_archive)

        # Add a timestamp.
        timestamp = datetime.now().isoformat()
        for item in resolved_list:
            item["thread"]["archived_at"] = timestamp
            archived.append(item["thread"])

        if not dry_run:
            self.save_archive(self.plot_threads_archive, archived)

        return len(resolved_list)

    def archive_reviews(self, old_reviews_list, dry_run=False):
        'Archive old reviews.'
        if not old_reviews_list:
            return 0

        # Load the existing archive.
        archived = self.load_archive(self.reviews_archive)

        # Add a timestamp.
        timestamp = datetime.now().isoformat()
        for item in old_reviews_list:
            item["review"]["archived_at"] = timestamp
            archived.append(item["review"])

        if not dry_run:
            self.save_archive(self.reviews_archive, archived)

        return len(old_reviews_list)

    def remove_from_state(self, state, inactive_chars, resolved_threads, old_reviews):
        'Remove archived data from state.json/SQLite (introduced in v5.1; retained in v5.4).'
        # Since v5.1 characters live in SQLite; archive_characters already updates their status.
        # Only foreshadowing and reviews in state.json need handling here.

        # Remove archived foreshadowing.
        if resolved_threads:
            thread_ids = {
                (item.get("thread", {}) or {}).get("content") or (item.get("thread", {}) or {}).get("description")
                for item in resolved_threads
            }
            thread_ids = {t for t in thread_ids if isinstance(t, str) and t.strip()}

            plot_threads = state.get("plot_threads", {}) or {}
            if isinstance(plot_threads.get("foreshadowing"), list):
                plot_threads["foreshadowing"] = [
                    t for t in plot_threads["foreshadowing"]
                    if not isinstance(t, dict) or (t.get("content") or t.get("description")) not in thread_ids
                ]
            if isinstance(plot_threads.get("resolved"), list):
                plot_threads["resolved"] = [
                    t for t in plot_threads["resolved"]
                    if not isinstance(t, dict) or (t.get("content") or t.get("description")) not in thread_ids
                ]
            state["plot_threads"] = plot_threads

        # Remove old reviews.
        if old_reviews:
            review_keys = set()
            for item in old_reviews:
                review = item.get("review", {}) or {}
                key = review.get("report") or review.get("reviewed_at") or review.get("date")
                if isinstance(key, str) and key.strip():
                    review_keys.add(key)

            state["review_checkpoints"] = [
                review for review in state.get("review_checkpoints", [])
                if (review.get("report") or review.get("reviewed_at") or review.get("date")) not in review_keys
            ]

        return state

    def run_auto_check(self, force=False, dry_run=False):
        'Run automatic archival checks.'
        state = self.load_state()

        # Check trigger conditions.
        trigger = self.check_trigger_conditions(state)

        if not force and not trigger["should_archive"]:
            print("✅ No archiving needed (trigger conditions not met)")
            print(f"   File size: {trigger['file_size_mb']:.2f} MB (threshold: {self.config['file_size_trigger_mb']} MB)")
            print(f"   Current chapter: {trigger['current_chapter']} (trigger every {self.config['chapter_trigger']} chapters)")
            return

        print("🔍 Checking archive eligibility...")
        print(f"   File size: {trigger['file_size_mb']:.2f} MB")
        print(f"   Current chapter: {trigger['current_chapter']}")

        # Identify data eligible for archival.
        inactive_chars = self.identify_inactive_characters(state)
        resolved_threads = self.identify_resolved_plot_threads(state)
        old_reviews = self.identify_old_reviews(state)

        # Display statistics.
        print(f"\n📊 Archive Statistics:")
        print(f"   Inactive characters: {len(inactive_chars)}")
        print(f"   Resolved foreshadowing: {len(resolved_threads)}")
        print(f"   Old review reports: {len(old_reviews)}")

        if not (inactive_chars or resolved_threads or old_reviews):
            print("\n✅ No archiving needed (no eligible data)")
            return

        # Dry-run mode.
        if dry_run:
            print("\n🔍 [Dry-run] Data to archive:")
            if inactive_chars:
                print("\n   Inactive characters:")
                for item in inactive_chars[:5]:  # Show only the first five.
                    print(f"   - {item['character']['name']} (absent for over {item['inactive_chapters']} chapters)")
            if resolved_threads:
                print("\n   Resolved foreshadowing:")
                for item in resolved_threads[:5]:
                    desc = item["thread"].get("content") or item["thread"].get("description") or ""
                    print(f"   - {str(desc)[:30]}... (resolved {item['chapters_since_resolved']} chapters ago)")
            if old_reviews:
                print("\n   Old review reports:")
                for item in old_reviews[:5]:
                    print(f"   - Ch{item['review_chapter']} ({item['chapters_since_review']} chapters ago)")
            return

        # Perform archival.
        chars_archived = self.archive_characters(inactive_chars, dry_run=dry_run)
        threads_archived = self.archive_plot_threads(resolved_threads, dry_run=dry_run)
        reviews_archived = self.archive_reviews(old_reviews, dry_run=dry_run)

        # Remove from state.json.
        state = self.remove_from_state(state, inactive_chars, resolved_threads, old_reviews)
        self.save_state(state)

        # Final statistics.
        print(f"\n✅ Archiving complete:")
        print(f"   Archived characters: {chars_archived} → {self.characters_archive.name}")
        print(f"   Archived foreshadowing: {threads_archived} → {self.plot_threads_archive.name}")
        print(f"   Archived reports: {reviews_archived} → {self.reviews_archive.name}")

        # Display file size after archival.
        new_size_mb = self.state_file.stat().st_size / (1024 * 1024)
        saved_mb = trigger["file_size_mb"] - new_size_mb
        print(f"\n💾 File size: {trigger['file_size_mb']:.2f} MB → {new_size_mb:.2f} MB (saved {saved_mb:.2f} MB)")

    def restore_character(self, name):
        'Restore an archived character (v5.1: restore status through IndexManager).'
        archived = self.load_archive(self.characters_archive)

        # Find the character.
        char_to_restore = None
        for char in archived:
            if char["name"] == name:
                char_to_restore = char
                break

        if not char_to_restore:
            print(f"❌ Character not found in archive: {name}")
            return False

        restored_character = dict(char_to_restore)
        restored_character.pop("archived_at", None)

        # Introduced in v5.1: restore to SQLite through IndexManager.
        char_id = restored_character.get("id", restored_character.get("name", "unknown"))
        try:
            # Set the entity status to active.
            self._index_manager.update_entity_field(char_id, "status", "active")
        except Exception as e:
            print(f"❌ Entity restore failed; archive preserved: {e}")
            return False

        archived = [char for char in archived if char.get("name") != name]
        try:
            self.save_archive(self.characters_archive, archived)
        except Exception as e:
            print(f"❌ Archive update failed; character restored but archive preserved: {e}")
            return False

        print(f"✅ Character restored: {name}")
        return True

    def show_stats(self):
        'Display archive statistics.'
        chars = self.load_archive(self.characters_archive)
        threads = self.load_archive(self.plot_threads_archive)
        reviews = self.load_archive(self.reviews_archive)

        print("📊 Archive Statistics:")
        print(f"   Archived characters: {len(chars)}")
        print(f"   Archived foreshadowing: {len(threads)}")
        print(f"   Archived reports: {len(reviews)}")

        # Calculate archive file sizes.
        total_size = 0
        for archive_file in [self.characters_archive, self.plot_threads_archive, self.reviews_archive]:
            if archive_file.exists():
                total_size += archive_file.stat().st_size

        print(f"   Archive size: {total_size / 1024:.2f} KB")

        # Display state.json size.
        state_size_mb = self.state_file.stat().st_size / (1024 * 1024)
        print(f"\n💾 state.json current size: {state_size_mb:.2f} MB")


def main():
    parser = argparse.ArgumentParser(description="state.json archive management")

    parser.add_argument("--auto-check", action="store_true", help="Check automatic archiving")
    parser.add_argument("--force", action="store_true", help="Force archiving (ignore trigger conditions)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (show eligible data only)")
    parser.add_argument("--restore-character", metavar="NAME", help="Restore an archived character")
    parser.add_argument("--stats", action="store_true", help="Show archive statistics")
    parser.add_argument("--project-root", metavar="PATH", help="Project root (defaults to current directory)")

    args = parser.parse_args()

    # Resolve the actual book project root; a workspace root is also accepted.
    try:
        project_root = str(resolve_project_root(args.project_root) if args.project_root else resolve_project_root())
    except FileNotFoundError as exc:
        print(f"❌ Cannot locate project root (requires .webnovel/state.json): {exc}", file=sys.stderr)
        sys.exit(1)

    manager = ArchiveManager(project_root=project_root)

    # Perform the operation.
    if args.auto_check or args.force:
        manager.run_auto_check(force=args.force, dry_run=args.dry_run)
    elif args.restore_character:
        manager.restore_character(args.restore_character)
    elif args.stats:
        manager.show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
