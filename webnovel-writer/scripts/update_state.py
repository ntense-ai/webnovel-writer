#!/usr/bin/env python3
'Safely update state.json.\n\nProvide structured partial updates, validate JSON and schema integrity, back up with timestamps, and write atomically without affecting unrelated fields. Dry-run mode previews changes.\n\nUsage:\n  python update_state.py --protagonist-power "Golden Core" 3 "Lightning Tribulation"\n  python update_state.py --relationship "Li Xue" affection 95\n  python update_state.py --add-foreshadowing "The jade pendant\'s secret" active\n  python update_state.py --resolve-foreshadowing "The thunder fruit\'s location" 45\n  python update_state.py --progress 45 198765\n  python update_state.py --volume-planned 1 --chapters-range 1-100\n\nCombine update flags for one write. Backups use .backup_TIMESTAMP.json; failed writes support recovery through backups.'

import json
import os
import sys
import argparse
import shutil
from pathlib import Path

from runtime_compat import enable_windows_utf8_stdio
from datetime import datetime
from typing import Dict, Any, Optional

# ============================================================================
# Security fix: import secure utility functions (P1 MEDIUM).
# ============================================================================
from security_utils import create_secure_directory, atomic_write_json, restore_from_backup
from project_locator import resolve_state_file
from data_modules.state_validator import (
    normalize_foreshadowing_status,
    normalize_state_runtime_sections,
)

# Windows encoding compatibility.
if sys.platform == "win32":
    enable_windows_utf8_stdio()

class StateUpdater:
    'Safely update state.json.'

    def __init__(self, state_file: str, dry_run: bool = False):
        self.state_file = state_file
        self.dry_run = dry_run
        self.backup_file = None
        self.state = None

    def _validate_schema(self, state: Dict) -> bool:
        'Validate the basic state.json structure (introduced in v5.0; retained in v5.4).'
        required_keys = [
            "project_info",
            "progress",
            "protagonist_state",
            "relationships",
            "world_settings",
            "plot_threads",
            "review_checkpoints"
        ]

        for key in required_keys:
            if key not in state:
                print(f"❌ Missing required field: {key}")
                return False

        # Validate nested structures, accepting both nested and flat formats.
        ps = state["protagonist_state"]
        # Power supports power.realm or a direct realm field.
        has_nested_power = "power" in ps and isinstance(ps.get("power"), dict)
        has_flat_power = "realm" in ps
        if not (has_nested_power or has_flat_power):
            print(f"❌ Missing protagonist_state.power or protagonist_state.realm")
            return False

        # Location supports location.current or a direct location field.
        has_nested_location = isinstance(ps.get("location"), dict) and "current" in ps.get("location", {})
        has_flat_location = isinstance(ps.get("location"), str)
        if not (has_nested_location or has_flat_location):
            print(f"❌ Missing protagonist_state.location")
            return False

        # Validate and complete strand_tracker for older state.json files.
        tracker = state.get("strand_tracker")
        if tracker is None or not isinstance(tracker, dict):
            if tracker is None:
                print("⚠️ strand_tracker missing; added default structure")
            else:
                print("⚠️ Invalid strand_tracker type; reset to defaults")
            state["strand_tracker"] = {
                "last_quest_chapter": 0,
                "last_fire_chapter": 0,
                "last_constellation_chapter": 0,
                "current_dominant": "quest",
                "chapters_since_switch": 0,
                "history": [],
            }
        else:
            tracker.setdefault("last_quest_chapter", 0)
            tracker.setdefault("last_fire_chapter", 0)
            tracker.setdefault("last_constellation_chapter", 0)
            tracker.setdefault("current_dominant", "quest")
            tracker.setdefault("chapters_since_switch", 0)
            tracker.setdefault("history", [])

        normalize_state_runtime_sections(state)
        return True

    def load(self) -> bool:
        'Load and validate state.json.'
        if not os.path.exists(self.state_file):
            print(f"❌ State file not found: {self.state_file}")
            return False

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                self.state = json.load(f)

            if not self._validate_schema(self.state):
                print("❌ Incomplete state.json structure; please check")
                return False

            return True

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return False

    def backup(self) -> bool:
        'Back up the current state.json.'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(self.state_file).parent / "backups"
        # ============================================================================
        # Security fix: create directories securely (P1 MEDIUM).
        # Previous code: backup_dir.mkdir(exist_ok=True)
        # Vulnerability: OS-default permissions could be 755, exposing data to other users.
        # ============================================================================
        create_secure_directory(str(backup_dir))

        self.backup_file = backup_dir / f"state.backup_{timestamp}.json"

        try:
            shutil.copy2(self.state_file, self.backup_file)
            print(f"✅ Backed up: {self.backup_file}")
            return True
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    def save(self) -> bool:
        'Save updated state.json atomically.'
        if self.dry_run:
            print("\n⚠️  Dry-run mode; no files will be written")
            print("\n📄 Preview updated content：")
            print(json.dumps(self.state, ensure_ascii=False, indent=2))
            return True

        try:
            # Use centralized atomic writes with filelock and automatic backups.
            atomic_write_json(self.state_file, self.state, use_lock=True, backup=True)
            print(f"✅ Saved atomically: {self.state_file}")
            return True

        except Exception as e:
            print(f"❌ Save failed: {e}")
            # Attempt restoration from backup.
            if restore_from_backup(self.state_file):
                print(f"✅ Restored from backup")
            return False

    def update_protagonist_power(self, realm: str, layer: int, bottleneck: str):
        'Update protagonist power in nested or flat format.'
        ps = self.state["protagonist_state"]
        # Detect the current format.
        if "power" in ps and isinstance(ps.get("power"), dict):
            # Nested format.
            ps["power"] = {
                "realm": realm,
                "layer": layer,
                "bottleneck": bottleneck if bottleneck != "null" else None
            }
        else:
            # Flat format.
            ps["realm"] = realm
            ps["layer"] = layer
            ps["bottleneck"] = bottleneck if bottleneck != "null" else None
        print(f"📝 Update protagonist power: {realm}, level {layer}, bottleneck: {bottleneck}")

    def update_protagonist_location(self, location: str, chapter: int):
        'Update protagonist location in nested or flat format.'
        ps = self.state["protagonist_state"]
        # Detect the current format.
        if isinstance(ps.get("location"), dict):
            # Nested format.
            ps["location"] = {
                "current": location,
                "last_chapter": chapter
            }
        else:
            # Flat format.
            ps["location"] = location
            ps["location_since_chapter"] = chapter
        print(f"📝 Update protagonist location: {location} (chapter {chapter})")

    def update_golden_finger(self, name: str, level: int, cooldown: int):
        "Update the protagonist's special-advantage state."
        ps = self.state.setdefault("protagonist_state", {})
        golden_finger = ps.get("golden_finger")
        if not isinstance(golden_finger, dict):
            golden_finger = {}
            ps["golden_finger"] = golden_finger

        golden_finger.setdefault("skills", [])
        golden_finger["name"] = name
        golden_finger["level"] = level
        golden_finger["cooldown"] = cooldown
        print(f"📝 Update special ability: {name} Lv.{level}, cooldown: {cooldown} days")

    def update_relationship(self, char_name: str, key: str, value: Any):
        'Update relationships.'
        if char_name not in self.state["relationships"]:
            self.state["relationships"][char_name] = {}

        self.state["relationships"][char_name][key] = value
        print(f"📝 Update relationship: {char_name}.{key} = {value}")

    def add_foreshadowing(self, content: str, status: str = "unresolved"):
        'Add foreshadowing.'
        if "foreshadowing" not in self.state["plot_threads"]:
            self.state["plot_threads"]["foreshadowing"] = []

        # Check whether the entry already exists.
        for item in self.state["plot_threads"]["foreshadowing"]:
            if item.get("content") == content:
                print(f"⚠️  Foreshadowing already exists: {content}")
                return

        # Normalize status aliases such as active and pending so downstream filters do not miss entries.
        status = normalize_foreshadowing_status(status)

        planted_chapter = int(self.state.get("progress", {}).get("current_chapter", 0) or 0)
        if planted_chapter <= 0:
            planted_chapter = 1
            print("? No valid progress.current_chapter; defaulting planted_chapter to 1")

        target_chapter = planted_chapter + 100

        self.state["plot_threads"]["foreshadowing"].append({
            "content": content,
            "status": status,
            "added_at": datetime.now().strftime("%Y-%m-%d"),
            "planted_chapter": planted_chapter,
            "target_chapter": target_chapter,
            "tier": "subplot"
        })
        print(f"📝 Add foreshadowing: {content} ({status})")

    def resolve_foreshadowing(self, content: str, chapter: int):
        'Resolve foreshadowing.'
        if "foreshadowing" not in self.state["plot_threads"]:
            print(f"❌ Foreshadowing list not found")
            return

        for item in self.state["plot_threads"]["foreshadowing"]:
            if item.get("content") == content:
                item["status"] = "resolved"
                item["resolved_chapter"] = chapter
                item["resolved_at"] = datetime.now().strftime("%Y-%m-%d")
                normalize_state_runtime_sections(self.state)
                print(f"📝 Resolve foreshadowing: {content} (chapter {chapter})")
                return

        print(f"⚠️  Foreshadowing not found: {content}")

    def update_progress(self, current_chapter: int, total_words: int):
        'Update writing progress.'
        self.state["progress"]["current_chapter"] = current_chapter
        self.state["progress"]["total_words"] = total_words
        self.state["progress"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"📝 Update progress: chapter {current_chapter}, total words: {total_words}")

    def mark_volume_planned(self, volume: int, chapters_range: str):
        'Mark a volume as planned.'
        if "volumes_planned" not in self.state["progress"]:
            self.state["progress"]["volumes_planned"] = []

        # Check whether the entry already exists.
        for item in self.state["progress"]["volumes_planned"]:
            if item.get("volume") == volume:
                print(f"⚠️  Volume {volume} already planned; updating chapter range")
                item["chapters_range"] = chapters_range
                item["updated_at"] = datetime.now().strftime("%Y-%m-%d")
                return

        self.state["progress"]["volumes_planned"].append({
            "volume": volume,
            "chapters_range": chapters_range,
            "planned_at": datetime.now().strftime("%Y-%m-%d")
        })
        print(f"📝 Mark volume {volume} planned: chapters {chapters_range}")

    def add_review_checkpoint(self, chapters_range: str, report_file: str):
        'Add a review record.'
        if "review_checkpoints" not in self.state:
            self.state["review_checkpoints"] = []

        self.state["review_checkpoints"].append({
            "chapters": chapters_range,
            "report": report_file,
            "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        print(f"📝 Add review record: chapters {chapters_range} → {report_file}")

    def update_strand_tracker(self, strand: str, chapter: int):
        'Update the dominant plot strand in Strand Weave.'
        # Validate the strand argument.
        valid_strands = ["quest", "fire", "constellation"]
        if strand.lower() not in valid_strands:
            print(f"❌ Invalid strand: {strand} (valid: quest, fire, constellation)")
            return False

        strand = strand.lower()

        # Initialize strand_tracker if absent.
        if "strand_tracker" not in self.state:
            self.state["strand_tracker"] = {
                "last_quest_chapter": 0,
                "last_fire_chapter": 0,
                "last_constellation_chapter": 0,
                "current_dominant": None,
                "chapters_since_switch": 0,
                "history": []
            }

        tracker = self.state["strand_tracker"]

        # Update this strand's latest chapter.
        tracker[f"last_{strand}_chapter"] = chapter

        # Determine whether the strand changed.
        if tracker.get("current_dominant") != strand:
            tracker["current_dominant"] = strand
            tracker["chapters_since_switch"] = 1
        else:
            tracker["chapters_since_switch"] += 1

        # Append to history.
        tracker["history"].append({
            "chapter": chapter,
            "dominant": strand
        })

        # Retain only the last 50 chapters to limit file growth.
        if len(tracker["history"]) > 50:
            tracker["history"] = tracker["history"][-50:]

        print(f"✅ strand_tracker updated")
        print(f"   - Chapter {chapter} dominant strand: {strand}")
        print(f"   - This strand has continued for {tracker['chapters_since_switch']} chapters")

        return True

def main():
    parser = argparse.ArgumentParser(
        description="Safely update state.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_state.py --protagonist-power "Adept" 3 "Trial"
  python update_state.py --relationship "Alex" affection 95
  python update_state.py --progress 45 198765
  python update_state.py --volume-planned 1 --chapters-range "1-100"
"""
    )

    parser.add_argument(
        '--project-root',
        default=None,
        help='Project root containing .webnovel/state.json; auto-discovered if omitted (including webnovel-project/ and parent directories).'
    )

    parser.add_argument(
        '--state-file',
        default=None,
        help='Optional state.json path; defaults to .webnovel/state.json under the project root.'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview without writing files'
    )

    # Update protagonist state.
    parser.add_argument(
        '--protagonist-power',
        nargs=3,
        metavar=('REALM', 'LAYER', 'BOTTLENECK'),
        help='Update protagonist power (realm, level, bottleneck)'
    )

    parser.add_argument(
        '--protagonist-location',
        nargs=2,
        metavar=('LOCATION', 'CHAPTER'),
        help='Update protagonist location (location, chapter)'
    )

    parser.add_argument(
        '--golden-finger',
        nargs=3,
        metavar=('NAME', 'LEVEL', 'COOLDOWN'),
        help='Update special ability (name, level, cooldown days)'
    )

    # Update relationships.
    parser.add_argument(
        '--relationship',
        nargs=3,
        action='append',
        metavar=('CHAR_NAME', 'KEY', 'VALUE'),
        help='Update relationship (character, property, value)'
    )

    # Manage foreshadowing.
    parser.add_argument(
        '--add-foreshadowing',
        nargs=2,
        metavar=('CONTENT', 'STATUS'),
        help='Add foreshadowing (content, status)'
    )

    parser.add_argument(
        '--resolve-foreshadowing',
        nargs=2,
        metavar=('CONTENT', 'CHAPTER'),
        help='Resolve foreshadowing (content, chapter)'
    )

    # Update progress.
    parser.add_argument(
        '--progress',
        nargs=2,
        type=int,
        metavar=('CHAPTER', 'WORDS'),
        help='Update progress (current chapter, total words)'
    )

    # Plan volumes.
    parser.add_argument(
        '--volume-planned',
        type=int,
        metavar='VOLUME',
        help='Mark a volume planned (volume number)'
    )

    parser.add_argument(
        '--chapters-range',
        metavar='RANGE',
        help='Chapter range (e.g. "1-100")'
    )

    # Review records.
    parser.add_argument(
        '--add-review',
        nargs=2,
        metavar=('CHAPTERS_RANGE', 'REPORT_FILE'),
        help='Add review record (chapter range, report file)'
    )

    # Update Strand Tracker.
    parser.add_argument(
        '--strand-dominant',
        nargs=2,
        metavar=('STRAND', 'CHAPTER'),
        help='Update dominant strand (quest/fire/constellation, chapter)'
    )

    args = parser.parse_args()

    # Show help and exit when no update arguments were supplied.
    if not any([
        args.protagonist_power,
        args.protagonist_location,
        args.golden_finger,
        args.relationship,
        args.add_foreshadowing,
        args.resolve_foreshadowing,
        args.progress,
        args.volume_planned,
        args.add_review,
        args.strand_dominant
    ]):
        parser.print_help()
        sys.exit(1)

    # Resolve state.json, including when run from the repository root.
    state_file_path = resolve_state_file(args.state_file, explicit_project_root=args.project_root)

    # Create the updater.
    updater = StateUpdater(str(state_file_path), args.dry_run)

    # Load the state file.
    if not updater.load():
        sys.exit(1)

    # Back up unless this is a dry run.
    if not args.dry_run:
        if not updater.backup():
            sys.exit(1)

    print("\n📝 Updating...")

    # Perform updates.
    try:
        if args.protagonist_power:
            realm, layer, bottleneck = args.protagonist_power
            updater.update_protagonist_power(realm, int(layer), bottleneck)

        if args.protagonist_location:
            location, chapter = args.protagonist_location
            updater.update_protagonist_location(location, int(chapter))

        if args.golden_finger:
            name, level, cooldown = args.golden_finger
            updater.update_golden_finger(name, int(level), int(cooldown))

        if args.relationship:
            for char_name, key, value in args.relationship:
                # Try converting to a number.
                try:
                    value = int(value)
                except ValueError:
                    pass
                updater.update_relationship(char_name, key, value)

        if args.add_foreshadowing:
            content, status = args.add_foreshadowing
            updater.add_foreshadowing(content, status)

        if args.resolve_foreshadowing:
            content, chapter = args.resolve_foreshadowing
            updater.resolve_foreshadowing(content, int(chapter))

        if args.progress:
            chapter, words = args.progress
            updater.update_progress(chapter, words)

        if args.volume_planned:
            if not args.chapters_range:
                print("❌ --volume-planned requires --chapters-range")
                sys.exit(1)
            updater.mark_volume_planned(args.volume_planned, args.chapters_range)

        if args.add_review:
            chapters_range, report_file = args.add_review
            updater.add_review_checkpoint(chapters_range, report_file)

        # Update Strand Tracker.
        if args.strand_dominant:
            strand, chapter = args.strand_dominant
            updater.update_strand_tracker(strand, int(chapter))

        # Save updates.
        if not updater.save():
            sys.exit(1)

        print("\n✅ Update complete!")

        if not args.dry_run:
            print(f"\n💡 Tip:")
            print(f"  - Original file backed up: {updater.backup_file}")
            print(f"  - To roll back, copy the backup to {updater.state_file}")

    except Exception as e:
        print(f"\n❌ Update failed: {e}")
        if updater.backup_file and os.path.exists(updater.backup_file):
            print(f"🔄 Rolling back...")
            shutil.copy2(updater.backup_file, updater.state_file)
            print(f"✅ Rolled back to the backup version")
        sys.exit(1)

if __name__ == "__main__":
    main()
