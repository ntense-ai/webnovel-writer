#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"State Manager v5.4 manages state.json entity state, progress, and relationships. Changes introduced in v5.1 and retained in v5.4 integrate SQLStateManager for synchronized SQLite writes to index.db; state.json retains compact data while large collections migrate automatically to SQLite."

import json
import logging
import sys
import time
from copy import deepcopy
from pathlib import Path

from runtime_compat import enable_windows_utf8_stdio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import filelock

from .config import get_config
from .observability import safe_append_perf_timing, safe_log_tool_call


logger = logging.getLogger(__name__)


try:
    # When scripts is on sys.path, usually when running from scripts/
    from security_utils import atomic_write_json, read_json_safe
except ImportError:  # pragma: no cover
    # When running python -m scripts.data_modules... from the repository root
    from scripts.security_utils import atomic_write_json, read_json_safe


@dataclass
class EntityState:
    "Entity state."
    id: str
    name: str
    type: str  # Characters / locations / items / factions
    tier: str = "decorative"  # Core / important / secondary / decorative
    aliases: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    first_appearance: int = 0
    last_appearance: int = 0


@dataclass
class Relationship:
    "Entity relationship."
    from_entity: str
    to_entity: str
    type: str
    description: str
    chapter: int


@dataclass
class StateChange:
    "State change record."
    entity_id: str
    field: str
    old_value: Any
    new_value: Any
    reason: str
    chapter: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class _EntityPatch:
    "Pending entity delta patch for merging under the lock."
    entity_type: str
    entity_id: str
    replace: bool = False
    base_entity: Optional[Dict[str, Any]] = None  # Complete snapshot for a newly created entity, used to populate missing fields
    top_updates: Dict[str, Any] = field(default_factory=dict)
    current_updates: Dict[str, Any] = field(default_factory=dict)
    appearance_chapter: Optional[int] = None


def _unique_aliases(*groups: Any) -> List[str]:
    result = []
    seen = set()
    for group in groups:
        if not group:
            continue
        values = [group] if isinstance(group, str) else group
        for value in values:
            alias = str(value).strip() if value is not None else ""
            if alias and alias not in seen:
                seen.add(alias)
                result.append(alias)
    return result


class StateManager:
    "State manager using the v5.1 entities_v3 format and SQLite synchronization, retained in v5.4."

    # Entity types introduced in v5.0
    ENTITY_TYPES = ["character", "location", "item", "faction", "combat-move"]

    # Chapter state machine with monotonic progression
    CHAPTER_STATUS_ORDER = ["chapter_drafted", "chapter_reviewed", "chapter_committed"]
    REJECTED_CHAPTER_STATUS = "chapter_rejected"

    def __init__(self, config=None, enable_sqlite_sync: bool = True):
        "Initialize the state manager. config supplies configuration; enable_sqlite_sync enables SQLite synchronization and defaults to True."
        self.config = config or get_config()
        self._state: Dict[str, Any] = {}
        # Match security_utils.atomic_write_json: state.json.lock
        self._lock_path = self.config.state_file.with_suffix(self.config.state_file.suffix + ".lock")

        # SQLite synchronization introduced in v5.1
        self._enable_sqlite_sync = enable_sqlite_sync
        self._sql_state_manager = None
        if enable_sqlite_sync:
            try:
                from .sql_state_manager import SQLStateManager
                self._sql_state_manager = SQLStateManager(self.config)
            except ImportError:
                pass  # Silently fall back when SQLStateManager is unavailable

        # Pending deltas: reread, merge, and write while holding the lock
        self._pending_entity_patches: Dict[tuple[str, str], _EntityPatch] = {}
        self._pending_alias_entries: Dict[str, List[Dict[str, str]]] = {}
        self._pending_state_changes: List[Dict[str, Any]] = []
        self._pending_structured_relationships: List[Dict[str, Any]] = []
        self._pending_disambiguation_warnings: List[Dict[str, Any]] = []
        self._pending_disambiguation_pending: List[Dict[str, Any]] = []
        self._pending_progress_chapter: Optional[int] = None
        self._pending_progress_words_delta: int = 0
        self._pending_chapter_status: Dict[str, str] = {}
        self._pending_chapter_meta: Dict[str, Any] = {}

        # Cache data awaiting SQLite synchronization, introduced in v5.1
        self._pending_sqlite_data: Dict[str, Any] = {
            "entities_appeared": [],
            "entities_new": [],
            "state_changes": [],
            "relationships_new": [],
            "chapter": None
        }

        self._load_state()

    def _now_progress_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _ensure_state_schema(self, state: Dict[str, Any]) -> Dict[str, Any]:
        "Ensure state.json contains required runtime fields while preserving existing data where possible."
        if not isinstance(state, dict):
            state = {}

        state.setdefault("project_info", {})
        state.setdefault("progress", {})
        state.setdefault("protagonist_state", {})

        # relationships may be a legacy entity-relationship list; the v5.0 runtime uses a character/important-relationship dictionary.
        relationships = state.get("relationships")
        if isinstance(relationships, list):
            state.setdefault("structured_relationships", [])
            if isinstance(state.get("structured_relationships"), list):
                state["structured_relationships"].extend(relationships)
            state["relationships"] = {}
        elif not isinstance(relationships, dict):
            state["relationships"] = {}

        state.setdefault("world_settings", {"power_system": [], "factions": [], "locations": []})
        state.setdefault("plot_threads", {"active_threads": [], "foreshadowing": []})
        state.setdefault("review_checkpoints", [])
        state.setdefault("chapter_meta", {})
        state.setdefault(
            "strand_tracker",
            {
                "last_quest_chapter": 0,
                "last_fire_chapter": 0,
                "last_constellation_chapter": 0,
                "current_dominant": "quest",
                "chapters_since_switch": 0,
                "history": [],
            },
        )

        entities_v3 = state.get("entities_v3")
        # entities_v3, alias_index, state_changes, and structured_relationships migrated to index.db in v5.1.
        # Do not initialize or maintain these fields in state.json anymore.

        if not isinstance(state.get("disambiguation_warnings"), list):
            state["disambiguation_warnings"] = []

        if not isinstance(state.get("disambiguation_pending"), list):
            state["disambiguation_pending"] = []

        # Basic progress fields
        progress = state["progress"]
        if not isinstance(progress, dict):
            progress = {}
            state["progress"] = progress
        progress.setdefault("current_chapter", 0)
        progress.setdefault("total_words", 0)
        progress.setdefault("last_updated", self._now_progress_timestamp())

        return state

    def _load_state(self):
        "Load the state file."
        if self.config.state_file.exists():
            self._state = read_json_safe(self.config.state_file, default={})
            self._state = self._ensure_state_schema(self._state)
        else:
            self._state = self._ensure_state_schema({})

    def save_state(self) -> Dict[str, Any]:
        "Save state by rereading, merging, and atomically writing under the lock. Prevent concurrent agents' read-modify-write overwrites by acquiring the lock, rereading the latest state.json, merging only this instance's pending_* deltas, and writing atomically."
        # Avoid unnecessary overwrites when there are no deltas.
        has_pending = any(
            [
                self._pending_entity_patches,
                self._pending_alias_entries,
                self._pending_state_changes,
                self._pending_structured_relationships,
                self._pending_disambiguation_warnings,
                self._pending_disambiguation_pending,
                self._pending_chapter_meta,
                self._pending_progress_chapter is not None,
                self._pending_progress_words_delta != 0,
                self._pending_chapter_status,
            ]
        )
        if not has_pending:
            return {"saved": False, "sqlite_sync_ok": True}

        self.config.ensure_dirs()

        lock = filelock.FileLock(str(self._lock_path), timeout=10)
        try:
            with lock:
                disk_state = read_json_safe(self.config.state_file, default={})
                disk_state = self._ensure_state_schema(disk_state)

                # Merge progress using max(chapter) and accumulated words_delta.
                if self._pending_progress_chapter is not None or self._pending_progress_words_delta != 0:
                    progress = disk_state.get("progress", {})
                    if not isinstance(progress, dict):
                        progress = {}
                        disk_state["progress"] = progress

                    try:
                        current_chapter = int(progress.get("current_chapter", 0) or 0)
                    except (TypeError, ValueError):
                        current_chapter = 0

                    if self._pending_progress_chapter is not None:
                        progress["current_chapter"] = max(current_chapter, int(self._pending_progress_chapter))

                    if self._pending_progress_words_delta:
                        try:
                            total_words = int(progress.get("total_words", 0) or 0)
                        except (TypeError, ValueError):
                            total_words = 0
                        progress["total_words"] = total_words + int(self._pending_progress_words_delta)

                    progress["last_updated"] = self._now_progress_timestamp()

                if self._pending_chapter_status:
                    progress = disk_state.get("progress", {})
                    if not isinstance(progress, dict):
                        progress = {}
                        disk_state["progress"] = progress
                    chapter_status = progress.get("chapter_status")
                    if not isinstance(chapter_status, dict):
                        chapter_status = {}
                        progress["chapter_status"] = chapter_status

                    def _status_rank(value: str) -> int:
                        if value == self.REJECTED_CHAPTER_STATUS:
                            return -1
                        try:
                            return self.CHAPTER_STATUS_ORDER.index(value)
                        except ValueError:
                            return -1

                    for chapter, pending_status in self._pending_chapter_status.items():
                        current_status = str(chapter_status.get(chapter) or "")
                        if current_status == pending_status:
                            continue
                        if current_status and _status_rank(pending_status) < _status_rank(current_status):
                            continue
                        chapter_status[chapter] = pending_status
                    progress["last_updated"] = self._now_progress_timestamp()

                # Enforce SQLite mode and remove large data fields, introduced in v5.1.
                # Ensure these oversized fields are absent from state.json.
                for field in ["entities_v3", "alias_index", "state_changes", "structured_relationships"]:
                    disk_state.pop(field, None)
                # Mark as migrated
                disk_state["_migrated_to_sqlite"] = True

                # Append, deduplicate, and truncate disambiguation_warnings
                if self._pending_disambiguation_warnings:
                    warnings_list = disk_state.get("disambiguation_warnings")
                    if not isinstance(warnings_list, list):
                        warnings_list = []
                        disk_state["disambiguation_warnings"] = warnings_list

                    def _warn_key(w: Dict[str, Any]) -> tuple:
                        return (
                            w.get("chapter"),
                            w.get("mention"),
                            w.get("chosen_id"),
                            w.get("confidence"),
                        )

                    existing_keys = {_warn_key(w) for w in warnings_list if isinstance(w, dict)}
                    for w in self._pending_disambiguation_warnings:
                        if not isinstance(w, dict):
                            continue
                        k = _warn_key(w)
                        if k in existing_keys:
                            continue
                        warnings_list.append(w)
                        existing_keys.add(k)

                    # Keep only the latest N entries to bound file growth.
                    max_keep = self.config.max_disambiguation_warnings
                    if len(warnings_list) > max_keep:
                        disk_state["disambiguation_warnings"] = warnings_list[-max_keep:]

                # Append, deduplicate, and truncate disambiguation_pending
                if self._pending_disambiguation_pending:
                    pending_list = disk_state.get("disambiguation_pending")
                    if not isinstance(pending_list, list):
                        pending_list = []
                        disk_state["disambiguation_pending"] = pending_list

                    def _pending_key(w: Dict[str, Any]) -> tuple:
                        return (
                            w.get("chapter"),
                            w.get("mention"),
                            w.get("suggested_id"),
                            w.get("confidence"),
                        )

                    existing_keys = {_pending_key(w) for w in pending_list if isinstance(w, dict)}
                    for w in self._pending_disambiguation_pending:
                        if not isinstance(w, dict):
                            continue
                        k = _pending_key(w)
                        if k in existing_keys:
                            continue
                        pending_list.append(w)
                        existing_keys.add(k)

                    max_keep = self.config.max_disambiguation_pending
                    if len(pending_list) > max_keep:
                        disk_state["disambiguation_pending"] = pending_list[-max_keep:]

                # chapter_meta: overwrite by chapter number
                if self._pending_chapter_meta:
                    chapter_meta = disk_state.get("chapter_meta")
                    if not isinstance(chapter_meta, dict):
                        chapter_meta = {}
                        disk_state["chapter_meta"] = chapter_meta
                    chapter_meta.update(self._pending_chapter_meta)

                # Atomic write; the lock is already held, so do not acquire it again.
                atomic_write_json(self.config.state_file, disk_state, use_lock=False, backup=True)

                # Synchronize to SQLite; retain pending data on failure for retry (v5.1).
                sqlite_pending_snapshot = self._snapshot_sqlite_pending()
                sqlite_sync_ok = self._sync_to_sqlite()

                # Refresh memory from the latest disk snapshot
                self._state = disk_state

                # Clear state.json pending data after it has been persisted.
                self._pending_disambiguation_warnings.clear()
                self._pending_disambiguation_pending.clear()
                self._pending_chapter_meta.clear()
                self._pending_progress_chapter = None
                self._pending_progress_words_delta = 0
                self._pending_chapter_status.clear()

                # Clear SQLite pending data on success; restore its snapshot on failure to avoid silent loss.
                if sqlite_sync_ok:
                    self._pending_entity_patches.clear()
                    self._pending_alias_entries.clear()
                    self._pending_state_changes.clear()
                    self._pending_structured_relationships.clear()
                    self._clear_pending_sqlite_data()
                else:
                    self._restore_sqlite_pending(sqlite_pending_snapshot)

                return {"saved": True, "sqlite_sync_ok": sqlite_sync_ok}

        except filelock.Timeout:
            raise RuntimeError("Cannot acquire the state.json lock; try again later")

    def _sync_to_sqlite(self) -> bool:
        "Synchronize pending data to SQLite; introduced in v5.1 and retained in v5.4."
        if not self._sql_state_manager:
            return True

        # Method 1: data collected through process_chapter_result
        sqlite_data = self._pending_sqlite_data
        chapter = sqlite_data.get("chapter")

        # Track processed (entity_id, chapter) pairs to avoid duplicate appearance writes.
        processed_appearances = set()

        if chapter is not None:
            try:
                self._sql_state_manager.process_chapter_entities(
                    chapter=chapter,
                    entities_appeared=sqlite_data.get("entities_appeared", []),
                    entities_new=sqlite_data.get("entities_new", []),
                    state_changes=sqlite_data.get("state_changes", []),
                    relationships_new=sqlite_data.get("relationships_new", [])
                )
                # Mark appearance records as processed
                for entity in sqlite_data.get("entities_appeared", []):
                    if entity.get("id"):
                        processed_appearances.add((entity.get("id"), chapter))
                for entity in sqlite_data.get("entities_new", []):
                    eid = entity.get("suggested_id") or entity.get("id")
                    if eid:
                        processed_appearances.add((eid, chapter))
            except Exception as exc:
                logger.warning("SQLite sync failed (process_chapter_entities): %s", exc)
                return False

        # Method 2: deltas collected through add_entity/update_entity
        # Data is cached in _pending_entity_patches and related variables.
        try:
            return self._sync_pending_patches_to_sqlite(processed_appearances)
        except Exception as exc:
            logger.warning("SQLite sync failed (pending patches): %s", exc)
            return False

    def _sync_pending_patches_to_sqlite(self, processed_appearances: set = None) -> bool:
        "Synchronize _pending_entity_patches and related data to SQLite (v5.1, retained in v5.4). processed_appearances contains (entity_id, chapter) pairs already handled by process_chapter_entities, preventing duplicate appearance writes from overwriting mentions."
        if not self._sql_state_manager:
            return True

        if processed_appearances is None:
            processed_appearances = set()

        # Metadata fields must not be stored in current_json.
        METADATA_FIELDS = {"canonical_name", "tier", "desc", "is_protagonist", "is_archived"}

        try:
            from .sql_state_manager import EntityData
            from .index_manager import EntityMeta

            # Synchronize entity patches
            for (entity_type, entity_id), patch in self._pending_entity_patches.items():
                if patch.base_entity:
                    # New entity
                    entity_data = EntityData(
                        id=entity_id,
                        type=entity_type,
                        name=patch.base_entity.get("canonical_name", entity_id),
                        tier=patch.base_entity.get("tier", "decorative"),
                        desc=patch.base_entity.get("desc", ""),
                        current=patch.base_entity.get("current", {}),
                        aliases=patch.base_entity.get("aliases", []),
                        first_appearance=patch.base_entity.get("first_appearance", 0),
                        last_appearance=patch.base_entity.get("last_appearance", 0),
                        is_protagonist=patch.base_entity.get("is_protagonist", False)
                    )
                    self._sql_state_manager.upsert_entity(entity_data)

                    # Record the first appearance; skip processed entries to preserve mentions.
                    if patch.appearance_chapter is not None:
                        if (entity_id, patch.appearance_chapter) not in processed_appearances:
                            self._sql_state_manager._index_manager.record_appearance(
                                entity_id=entity_id,
                                chapter=patch.appearance_chapter,
                                mentions=[entity_data.name],
                                confidence=1.0,
                                skip_if_exists=True  # Important: do not overwrite existing records.
                            )
                else:
                    # Update an existing entity
                    has_metadata_updates = bool(patch.top_updates and
                                                 any(k in METADATA_FIELDS for k in patch.top_updates))

                    # Treat non-metadata top_updates as current-state updates.
                    # For example, realm, layer, location, and other state fields
                    non_metadata_top_updates = {
                        k: v for k, v in patch.top_updates.items()
                        if k not in METADATA_FIELDS
                    } if patch.top_updates else {}

                    # Merge current_updates with non-metadata top_updates
                    effective_current_updates = {**non_metadata_top_updates}
                    if patch.current_updates:
                        effective_current_updates.update(patch.current_updates)

                    if has_metadata_updates:
                        # For metadata changes, use upsert_entity(update_metadata=True).
                        existing = self._sql_state_manager.get_entity(entity_id)
                        if existing:
                            # Merge current state
                            current = existing.get("current_json", {})
                            if isinstance(current, str):
                                import json
                                current = json.loads(current) if current else {}
                            if effective_current_updates:
                                current.update(effective_current_updates)

                            new_canonical_name = patch.top_updates.get("canonical_name")
                            old_canonical_name = existing.get("canonical_name", "")

                            entity_meta = EntityMeta(
                                id=entity_id,
                                type=existing.get("type", entity_type),
                                canonical_name=new_canonical_name or old_canonical_name,
                                tier=patch.top_updates.get("tier", existing.get("tier", "decorative")),
                                desc=patch.top_updates.get("desc", existing.get("desc", "")),
                                current=current,
                                first_appearance=existing.get("first_appearance", 0),
                                last_appearance=patch.appearance_chapter or existing.get("last_appearance", 0),
                                is_protagonist=patch.top_updates.get("is_protagonist", existing.get("is_protagonist", False)),
                                is_archived=patch.top_updates.get("is_archived", existing.get("is_archived", False))
                            )
                            self._sql_state_manager._index_manager.upsert_entity(entity_meta, update_metadata=True)

                            # Automatically register a new canonical_name as an alias when renamed.
                            if new_canonical_name and new_canonical_name != old_canonical_name:
                                self._sql_state_manager.register_alias(
                                    new_canonical_name, entity_id, existing.get("type", entity_type)
                                )
                    elif effective_current_updates:
                        # Only current-state updates, including non-metadata top_updates
                        self._sql_state_manager.update_entity_current(entity_id, effective_current_updates)

                    # Update last_appearance and record the appearance
                    if patch.appearance_chapter is not None:
                        self._sql_state_manager._update_last_appearance(entity_id, patch.appearance_chapter)
                        # Add appearance records
                        # Use skip_if_exists=True to preserve mentions in existing records.
                        if (entity_id, patch.appearance_chapter) not in processed_appearances:
                            self._sql_state_manager._index_manager.record_appearance(
                                entity_id=entity_id,
                                chapter=patch.appearance_chapter,
                                mentions=[],
                                confidence=1.0,
                                skip_if_exists=True  # Important: do not overwrite existing records.
                            )

            # Synchronize aliases
            for alias, entries in self._pending_alias_entries.items():
                for entry in entries:
                    entity_type = entry.get("type")
                    entity_id = entry.get("id")
                    if entity_type and entity_id:
                        self._sql_state_manager.register_alias(alias, entity_id, entity_type)

            # Synchronize state changes
            for change in self._pending_state_changes:
                self._sql_state_manager.record_state_change(
                    entity_id=change.get("entity_id", ""),
                    field=change.get("field", ""),
                    old_value=change.get("old", change.get("old_value", "")),
                    new_value=change.get("new", change.get("new_value", "")),
                    reason=change.get("reason", ""),
                    chapter=change.get("chapter", 0)
                )

            # Synchronize relationships
            for rel in self._pending_structured_relationships:
                self._sql_state_manager.upsert_relationship(
                    from_entity=rel.get("from_entity", ""),
                    to_entity=rel.get("to_entity", ""),
                    type=rel.get("type", "acquaintance"),
                    description=rel.get("description", ""),
                    chapter=rel.get("chapter", 0)
                )

            return True

        except Exception as e:
            # Warn on SQLite synchronization failure without interrupting the main workflow.
            logger.warning("SQLite sync failed: %s", e)
            return False

    def _snapshot_sqlite_pending(self) -> Dict[str, Any]:
        "Snapshot pending SQLite data so the in-memory queue can be restored after synchronization failure."
        return {
            "entity_patches": deepcopy(self._pending_entity_patches),
            "alias_entries": deepcopy(self._pending_alias_entries),
            "state_changes": deepcopy(self._pending_state_changes),
            "structured_relationships": deepcopy(self._pending_structured_relationships),
            "sqlite_data": deepcopy(self._pending_sqlite_data),
        }

    def _restore_sqlite_pending(self, snapshot: Dict[str, Any]) -> None:
        "Restore pending SQLite data to avoid silent data loss after synchronization failure."
        self._pending_entity_patches = snapshot.get("entity_patches", {})
        self._pending_alias_entries = snapshot.get("alias_entries", {})
        self._pending_state_changes = snapshot.get("state_changes", [])
        self._pending_structured_relationships = snapshot.get("structured_relationships", [])
        self._pending_sqlite_data = snapshot.get("sqlite_data", {
            "entities_appeared": [],
            "entities_new": [],
            "state_changes": [],
            "relationships_new": [],
            "chapter": None,
        })

    def _clear_pending_sqlite_data(self):
        "Clear data pending SQLite synchronization."
        self._pending_sqlite_data = {
            "entities_appeared": [],
            "entities_new": [],
            "state_changes": [],
            "relationships_new": [],
            "chapter": None
        }

    # ==================== Progress management ====================

    def get_current_chapter(self) -> int:
        "Get the current chapter number."
        return self._state.get("progress", {}).get("current_chapter", 0)

    def update_progress(self, chapter: int, words: int = 0):
        "Update progress."
        if "progress" not in self._state:
            self._state["progress"] = {}
        self._state["progress"]["current_chapter"] = chapter
        if words > 0:
            total = self._state["progress"].get("total_words", 0)
            self._state["progress"]["total_words"] = total + words

        # Record deltas; merge under the lock using max(chapter) and accumulated words_delta.
        if self._pending_progress_chapter is None:
            self._pending_progress_chapter = chapter
        else:
            self._pending_progress_chapter = max(self._pending_progress_chapter, chapter)
        if words > 0:
            self._pending_progress_words_delta += int(words)

    # ==================== Chapter status management ====================

    def get_chapter_status(self, chapter: int) -> Optional[str]:
        "Query chapter status."
        statuses = self._state.get("progress", {}).get("chapter_status", {})
        return statuses.get(str(chapter))

    def set_chapter_status(self, chapter: int, status: str) -> None:
        "Set chapter status monotonically; backward transitions are prohibited."
        valid_statuses = set(self.CHAPTER_STATUS_ORDER + [self.REJECTED_CHAPTER_STATUS])
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {status}, valid values: {self.CHAPTER_STATUS_ORDER + [self.REJECTED_CHAPTER_STATUS]}"
            )

        current = self.get_chapter_status(chapter)
        if current is not None:
            current_idx = self._chapter_status_rank(current)
            new_idx = self._chapter_status_rank(status)
            if new_idx < current_idx:
                raise ValueError(
                    f"Chapter {chapter} status cannot move backward: {current} -> {status}"
                )
            if new_idx == current_idx:
                return  # Idempotent

        progress = self._state.setdefault("progress", {})
        chapter_status = progress.setdefault("chapter_status", {})
        chapter_status[str(chapter)] = status
        self._pending_chapter_status[str(chapter)] = status
        self.save_state()

    def _chapter_status_rank(self, status: str) -> int:
        if status == self.REJECTED_CHAPTER_STATUS:
            return -1
        try:
            return self.CHAPTER_STATUS_ORDER.index(status)
        except ValueError:
            return -1

    def _save_state(self) -> None:
        "Persist the current in-memory state directly to state.json without pending-delta merging."
        self.config.ensure_dirs()
        atomic_write_json(self.config.state_file, self._state, backup=False)

    # ==================== Entity management (v5.1 SQLite-first) ====================

    def get_entity(self, entity_id: str, entity_type: str = None) -> Optional[Dict]:
        "Get an entity, reading SQLite first as introduced in v5.1."
        # Read from SQLite first, introduced in v5.1.
        if self._sql_state_manager:
            entity = self._sql_state_manager.get_entity(entity_id)
            if entity:
                return entity

        # Fall back to in-memory state for projects not yet migrated.
        entities_v3 = self._state.get("entities_v3", {})
        if entity_type:
            return entities_v3.get(entity_type, {}).get(entity_id)

        # Search across all entity types
        for type_name, entities in entities_v3.items():
            if entity_id in entities:
                return entities[entity_id]
        return None

    def get_entity_type(self, entity_id: str) -> Optional[str]:
        "Get an entity's type."
        # Read from SQLite first, introduced in v5.1.
        if self._sql_state_manager:
            entity = self._sql_state_manager._index_manager.get_entity(entity_id)
            if entity:
                return entity.get("type")

        # Fall back to in-memory state
        for type_name, entities in self._state.get("entities_v3", {}).items():
            if entity_id in entities:
                return type_name
        return None

    def get_all_entities(self) -> Dict[str, Dict]:
        "Get all entities as a flattened view."
        # Read from SQLite first, introduced in v5.1.
        if self._sql_state_manager:
            result = {}
            for entity_type in self.ENTITY_TYPES:
                entities = self._sql_state_manager._index_manager.get_entities_by_type(entity_type)
                for e in entities:
                    eid = e.get("id")
                    if eid:
                        result[eid] = {**e, "type": entity_type}
            if result:
                return result

        # Fall back to in-memory state
        result = {}
        for type_name, entities in self._state.get("entities_v3", {}).items():
            for eid, e in entities.items():
                result[eid] = {**e, "type": type_name}
        return result

    def get_entities_by_type(self, entity_type: str) -> Dict[str, Dict]:
        "Get entities by type."
        # Read from SQLite first, introduced in v5.1.
        if self._sql_state_manager:
            entities = self._sql_state_manager._index_manager.get_entities_by_type(entity_type)
            if entities:
                return {e.get("id"): e for e in entities if e.get("id")}

        # Fall back to in-memory state
        return self._state.get("entities_v3", {}).get(entity_type, {})

    def get_entities_by_tier(self, tier: str) -> Dict[str, Dict]:
        "Get entities by tier."
        # Read from SQLite first, introduced in v5.1.
        if self._sql_state_manager:
            result = {}
            for entity_type in self.ENTITY_TYPES:
                entities = self._sql_state_manager._index_manager.get_entities_by_tier(tier)
                for e in entities:
                    eid = e.get("id")
                    if eid and e.get("type") == entity_type:
                        result[eid] = {**e, "type": entity_type}
            if result:
                return result

        # Fall back to in-memory state
        result = {}
        for type_name, entities in self._state.get("entities_v3", {}).items():
            for eid, e in entities.items():
                if e.get("tier") == tier:
                    result[eid] = {**e, "type": type_name}
        return result

    def add_entity(self, entity: EntityState) -> bool:
        "Add an entity using the v5.0 entities_v3 format, retained in v5.4."
        entity_type = entity.type
        if entity_type not in self.ENTITY_TYPES:
            entity_type = "character"

        if "entities_v3" not in self._state:
            self._state["entities_v3"] = {t: {} for t in self.ENTITY_TYPES}

        if entity_type not in self._state["entities_v3"]:
            self._state["entities_v3"][entity_type] = {}

        # Check whether the entity already exists
        if entity.id in self._state["entities_v3"][entity_type]:
            return False

        # Convert to v3 format
        v3_entity = {
            "canonical_name": entity.name,
            "tier": entity.tier,
            "desc": "",
            "current": entity.attributes,
            "aliases": list(entity.aliases),
            "first_appearance": entity.first_appearance,
            "last_appearance": entity.last_appearance,
            "history": []
        }
        self._state["entities_v3"][entity_type][entity.id] = v3_entity

        # Record a new-entity patch that fills only missing fields, preserving concurrent writes.
        patch = self._pending_entity_patches.get((entity_type, entity.id))
        if patch is None:
            patch = _EntityPatch(entity_type=entity_type, entity_id=entity.id)
            self._pending_entity_patches[(entity_type, entity.id)] = patch
        patch.replace = True
        patch.base_entity = v3_entity

        # Register aliases in index.db through SQLStateManager, introduced in v5.1.
        if self._sql_state_manager:
            self._sql_state_manager._index_manager.register_alias(entity.name, entity.id, entity_type)
            for alias in entity.aliases:
                if alias:
                    self._sql_state_manager._index_manager.register_alias(alias, entity.id, entity_type)

        return True

    def _register_alias_internal(self, entity_id: str, entity_type: str, alias: str):
        "Register an alias in index.db internally; introduced in v5.1."
        if not alias:
            return
        # Write directly to SQLite, introduced in v5.1.
        if self._sql_state_manager:
            self._sql_state_manager._index_manager.register_alias(alias, entity_id, entity_type)

    def update_entity(self, entity_id: str, updates: Dict[str, Any], entity_type: str = None) -> bool:
        "Update entity attributes; introduced in v5.0 and retained in v5.4."
        # v5.1+ SQLite-first:
        # entity_type may come from SQLite's entities table, while state.json no longer persists entities_v3.
        # Do not assume self._state["entities_v3"][type][id] exists; the issues7 log previously recorded a KeyError here.
        resolved_type = entity_type or self.get_entity_type(entity_id)
        if not resolved_type:
            return False
        if resolved_type not in self.ENTITY_TYPES:
            resolved_type = "character"

        # Update the in-memory snapshot only when a v3 entity exists; do not recreate it and inflate state.json.
        entities_v3 = self._state.get("entities_v3")
        entity = None
        if isinstance(entities_v3, dict):
            bucket = entities_v3.get(resolved_type)
            if isinstance(bucket, dict):
                entity = bucket.get(entity_id)

        # With SQLite enabled, record the patch even without an in-memory entity so current state reaches index.db incrementally.
        patch = None
        if self._sql_state_manager:
            patch = self._pending_entity_patches.get((resolved_type, entity_id))
            if patch is None:
                patch = _EntityPatch(entity_type=resolved_type, entity_id=entity_id)
                self._pending_entity_patches[(resolved_type, entity_id)] = patch

        if entity is None and patch is None:
            return False

        did_any = False
        for key, value in updates.items():
            if key == "attributes" and isinstance(value, dict):
                if entity is not None:
                    if "current" not in entity:
                        entity["current"] = {}
                    entity["current"].update(value)
                if patch is not None:
                    patch.current_updates.update(value)
                did_any = True
            elif key == "current" and isinstance(value, dict):
                if entity is not None:
                    if "current" not in entity:
                        entity["current"] = {}
                    entity["current"].update(value)
                if patch is not None:
                    patch.current_updates.update(value)
                did_any = True
            else:
                if entity is not None:
                    entity[key] = value
                if patch is not None:
                    patch.top_updates[key] = value
                did_any = True

        return did_any

    def update_entity_appearance(self, entity_id: str, chapter: int, entity_type: str = None):
        "Update an entity's appearance chapter."
        if not entity_type:
            entity_type = self.get_entity_type(entity_id)
        if not entity_type:
            return

        entities_v3 = self._state.get("entities_v3")
        if not isinstance(entities_v3, dict):
            entities_v3 = {t: {} for t in self.ENTITY_TYPES}
            self._state["entities_v3"] = entities_v3
        entities_v3.setdefault(entity_type, {})

        entity = entities_v3[entity_type].get(entity_id)
        if entity:
            if entity.get("first_appearance", 0) == 0:
                entity["first_appearance"] = chapter
            entity["last_appearance"] = chapter

            # Apply the patch under the lock with first=min(non-zero) and last=max.
            patch = self._pending_entity_patches.get((entity_type, entity_id))
            if patch is None:
                patch = _EntityPatch(entity_type=entity_type, entity_id=entity_id)
                self._pending_entity_patches[(entity_type, entity_id)] = patch
            if patch.appearance_chapter is None:
                patch.appearance_chapter = chapter
            else:
                patch.appearance_chapter = max(int(patch.appearance_chapter), int(chapter))

    # ==================== State change records ====================

    def record_state_change(
        self,
        entity_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
        reason: str,
        chapter: int
    ):
        "Record a state change."
        if "state_changes" not in self._state:
            self._state["state_changes"] = []

        change = StateChange(
            entity_id=entity_id,
            field=field,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            chapter=chapter
        )
        change_dict = asdict(change)
        self._state["state_changes"].append(change_dict)
        self._pending_state_changes.append(change_dict)

        # Also update entity attributes
        self.update_entity(entity_id, {"attributes": {field: new_value}})

    def get_state_changes(self, entity_id: Optional[str] = None) -> List[Dict]:
        "Get state-change history."
        changes = self._state.get("state_changes", [])
        if entity_id:
            changes = [c for c in changes if c.get("entity_id") == entity_id]
        return changes

    # ==================== Relationship management ====================

    def add_relationship(
        self,
        from_entity: str,
        to_entity: str,
        rel_type: str,
        description: str,
        chapter: int
    ):
        "Add a relationship."
        rel = Relationship(
            from_entity=from_entity,
            to_entity=to_entity,
            type=rel_type,
            description=description,
            chapter=chapter
        )

        # Store entity relationships in structured_relationships to avoid conflicting with the character-relationship dictionary (v5.0).
        if "structured_relationships" not in self._state:
            self._state["structured_relationships"] = []
        rel_dict = asdict(rel)
        self._state["structured_relationships"].append(rel_dict)
        self._pending_structured_relationships.append(rel_dict)

    def get_relationships(self, entity_id: Optional[str] = None) -> List[Dict]:
        "Get relationships."
        rels = self._state.get("structured_relationships", [])
        if entity_id:
            rels = [
                r for r in rels
                if r.get("from_entity") == entity_id or r.get("to_entity") == entity_id
            ]
        return rels

    # ==================== Batch operations ====================

    def _record_disambiguation(self, chapter: int, uncertain_items: Any) -> List[str]:
        "Record disambiguation feedback in state.json so Writer/Context agents can see risks. Confidence >= extraction_confidence_medium goes to disambiguation_warnings (accepted with warning); lower confidence goes to disambiguation_pending (requires human confirmation)."
        if not isinstance(uncertain_items, list) or not uncertain_items:
            return []

        warnings: List[str] = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in uncertain_items:
            if not isinstance(item, dict):
                continue

            mention = str(item.get("mention", "") or "").strip()
            if not mention:
                continue

            raw_conf = item.get("confidence", 0.0)
            try:
                confidence = float(raw_conf)
            except (TypeError, ValueError):
                confidence = 0.0

            # Candidates support either [{"type", "id"}, ...] or ["id1", "id2"].
            candidates_raw = item.get("candidates", [])
            candidates: List[Dict[str, str]] = []
            if isinstance(candidates_raw, list):
                for c in candidates_raw:
                    if isinstance(c, dict):
                        cid = str(c.get("id", "") or "").strip()
                        ctype = str(c.get("type", "") or "").strip()
                        entry: Dict[str, str] = {}
                        if ctype:
                            entry["type"] = ctype
                        if cid:
                            entry["id"] = cid
                        if entry:
                            candidates.append(entry)
                    else:
                        cid = str(c).strip()
                        if cid:
                            candidates.append({"id": cid})

            entity_type = str(item.get("type", "") or "").strip()
            suggested_id = str(item.get("suggested", "") or "").strip()

            adopted_raw = item.get("adopted", None)
            chosen_id = ""
            if isinstance(adopted_raw, str):
                chosen_id = adopted_raw.strip()
            elif adopted_raw is True:
                chosen_id = suggested_id
            else:
                # Compatible field names: entity_id / chosen_id
                chosen_id = str(item.get("entity_id") or item.get("chosen_id") or "").strip() or suggested_id

            context = str(item.get("context", "") or "").strip()
            note = str(item.get("warning", "") or "").strip()

            record: Dict[str, Any] = {
                "chapter": int(chapter),
                "mention": mention,
                "type": entity_type,
                "suggested_id": suggested_id,
                "chosen_id": chosen_id,
                "confidence": confidence,
                "candidates": candidates,
                "context": context,
                "note": note,
                "created_at": now,
            }

            if confidence >= float(self.config.extraction_confidence_medium):
                self._state.setdefault("disambiguation_warnings", []).append(record)
                self._pending_disambiguation_warnings.append(record)
                chosen_part = f" → {chosen_id}" if chosen_id else ""
                warnings.append(f"Disambiguation warning: {mention}{chosen_part} (confidence: {confidence:.2f})")
            else:
                self._state.setdefault("disambiguation_pending", []).append(record)
                self._pending_disambiguation_pending.append(record)
                warnings.append(f"Disambiguation requires manual confirmation: {mention} (confidence: {confidence:.2f})")

        return warnings

    def process_chapter_result(self, chapter: int, result: Dict) -> List[str]:
        "Process Data Agent chapter results (introduced in v5.1, retained in v5.4). Input fields are entities_appeared, entities_new, state_changes, and relationships_new, each containing its corresponding list. Return a list of warnings."
        warnings = []

        # Record the chapter number for SQLite synchronization (v5.1).
        self._pending_sqlite_data["chapter"] = chapter

        # Process appearing entities
        for entity in result.get("entities_appeared", []):
            entity_id = entity.get("id")
            entity_type = entity.get("type")
            if entity_id:
                self.update_entity_appearance(entity_id, chapter, entity_type)
                resolved_type = entity_type or self.get_entity_type(entity_id) or "character"
                for alias in _unique_aliases(entity.get("mentions", [])):
                    entries = self._pending_alias_entries.setdefault(alias, [])
                    alias_entry = {"type": resolved_type, "id": entity_id}
                    if alias_entry not in entries:
                        entries.append(alias_entry)
                # Cache for SQLite synchronization (v5.1).
                self._pending_sqlite_data["entities_appeared"].append(entity)

        # Process new entities
        for entity in result.get("entities_new", []):
            entity_id = entity.get("suggested_id") or entity.get("id")
            if entity_id and entity_id != "NEW":
                new_entity = EntityState(
                    id=entity_id,
                    name=entity.get("name", ""),
                    type=entity.get("type", "character"),
                    tier=entity.get("tier", "decorative"),
                    aliases=_unique_aliases(
                        entity.get("mentions", []), entity.get("aliases", [])
                    ),
                    first_appearance=chapter,
                    last_appearance=chapter
                )
                if not self.add_entity(new_entity):
                    warnings.append(f"Entity already exists: {entity_id}")
                # Cache for SQLite synchronization (v5.1).
                self._pending_sqlite_data["entities_new"].append(entity)

        # Process state changes
        for change in result.get("state_changes", []):
            self.record_state_change(
                entity_id=change.get("entity_id", ""),
                field=change.get("field", ""),
                old_value=change.get("old"),
                new_value=change.get("new"),
                reason=change.get("reason", ""),
                chapter=chapter
            )
            # Cache for SQLite synchronization (v5.1).
            self._pending_sqlite_data["state_changes"].append(change)

        # Process relationships
        for rel in result.get("relationships_new", []):
            self.add_relationship(
                from_entity=rel.get("from", ""),
                to_entity=rel.get("to", ""),
                rel_type=rel.get("type", ""),
                description=rel.get("description", ""),
                chapter=chapter
            )
            # Cache for SQLite synchronization (v5.1).
            self._pending_sqlite_data["relationships_new"].append(rel)

        # Process uncertain disambiguations; they do not block entity writes but must be visible to the Writer.
        warnings.extend(self._record_disambiguation(chapter, result.get("uncertain", [])))


        # Write chapter_meta: hook, pattern, and ending state
        chapter_meta = result.get("chapter_meta")
        if isinstance(chapter_meta, dict):
            meta_key = f"{int(chapter):04d}"
            self._state.setdefault("chapter_meta", {})
            self._state["chapter_meta"][meta_key] = chapter_meta
            self._pending_chapter_meta[meta_key] = chapter_meta
        # Update progress
        self.update_progress(chapter)

        # Synchronize protagonist state from entities_v3 to protagonist_state.
        self.sync_protagonist_from_entity()

        # Write long-term memory on a best-effort basis without blocking the main workflow.
        try:
            from .memory.writer import MemoryWriter

            writer = MemoryWriter(self.config)
            mem_result = writer.update_from_chapter_result(chapter, result)
            logger.info("memory_write: %s", mem_result)
        except Exception as exc:
            logger.warning("memory_write_failed: %s", exc)

        return warnings

    # ==================== Export ====================

    def export_for_context(self) -> Dict:
        "Export compact state for context; introduced in v5.0 and retained in v5.4."
        # Build a compact view from entities_v3
        entities_flat = {}
        for type_name, entities in self._state.get("entities_v3", {}).items():
            for eid, e in entities.items():
                entities_flat[eid] = {
                    "name": e.get("canonical_name", eid),
                    "type": type_name,
                    "tier": e.get("tier", "decorative"),
                    "current": e.get("current", {})
                }

        return {
            "progress": self._state.get("progress", {}),
            "entities": entities_flat,
            # alias_index moved to index.db in v5.1; return empty here for compatibility.
            "alias_index": {},
            "recent_changes": [],  # Query index.db, introduced in v5.1.
            "disambiguation": {
                "warnings": self._state.get("disambiguation_warnings", [])[-self.config.export_disambiguation_slice:],
                "pending": self._state.get("disambiguation_pending", [])[-self.config.export_disambiguation_slice:],
            },
        }

    # ==================== Protagonist synchronization ====================

    def get_protagonist_entity_id(self) -> Optional[str]:
        "Get the protagonist entity ID from is_protagonist or a SQLite query."
        # Method 1: query through SQLStateManager (v5.1)
        if self._sql_state_manager:
            protagonist = self._sql_state_manager.get_protagonist()
            if protagonist:
                return protagonist.get("id")

        # Method 2: look up aliases using protagonist_state.name
        protag_name = self._state.get("protagonist_state", {}).get("name")
        if protag_name and self._sql_state_manager:
            entities = self._sql_state_manager._index_manager.get_entities_by_alias(protag_name)
            for entry in entities:
                if entry.get("type") == "character":
                    return entry.get("id")

        return None

    def sync_protagonist_from_entity(self, entity_id: str = None):
        "Synchronize the protagonist entity into protagonist_state, reading SQLite in v5.1. This keeps consumers such as consistency-checker up to date."
        if entity_id is None:
            entity_id = self.get_protagonist_entity_id()
        if entity_id is None:
            return

        entity = self.get_entity(entity_id, "character")
        if not entity:
            return

        current = entity.get("current")
        if not isinstance(current, dict):
            current = entity.get("current_json", {})
        if isinstance(current, str):
            try:
                current = json.loads(current) if current else {}
            except (json.JSONDecodeError, TypeError):
                current = {}
        if not isinstance(current, dict):
            current = {}
        protag = self._state.setdefault("protagonist_state", {})

        # Synchronize cultivation realm
        if "realm" in current:
            power = protag.setdefault("power", {})
            power["realm"] = current["realm"]
            if "layer" in current:
                power["layer"] = current["layer"]

        # Synchronize location
        if "location" in current:
            loc = protag.setdefault("location", {})
            loc["current"] = current["location"]
            if "last_chapter" in current:
                loc["last_chapter"] = current["last_chapter"]

    def sync_protagonist_to_entity(self, entity_id: str = None):
        "Synchronize protagonist_state into the protagonist entity in entities_v3 after initialization or manual editing."
        if entity_id is None:
            entity_id = self.get_protagonist_entity_id()
        if entity_id is None:
            return

        protag = self._state.get("protagonist_state", {})
        if not protag:
            return

        updates = {}

        # Synchronize cultivation realm
        power = protag.get("power", {})
        if power.get("realm"):
            updates["realm"] = power["realm"]
        if power.get("layer"):
            updates["layer"] = power["layer"]

        # Synchronize location
        loc = protag.get("location", {})
        if loc.get("current"):
            updates["location"] = loc["current"]

        if updates:
            self.update_entity(entity_id, updates, "character")


# ==================== CLI ====================

def main():
    import argparse
    import sys
    from pydantic import ValidationError
    from .cli_output import print_success, print_error
    from .cli_args import normalize_global_project_root, load_json_arg
    from .schemas import validate_data_agent_output, format_validation_error, normalize_data_agent_output
    from .index_manager import IndexManager

    parser = argparse.ArgumentParser(description="State Manager CLI (v5.4)")
    parser.add_argument("--project-root", type=str, help="Project root")

    subparsers = parser.add_subparsers(dest="command")

    # Read progress
    subparsers.add_parser("get-progress")

    # Get an entity
    get_entity_parser = subparsers.add_parser("get-entity")
    get_entity_parser.add_argument("--id", required=True)

    # List entities
    list_parser = subparsers.add_parser("list-entities")
    list_parser.add_argument("--type", help="Filter by type")
    list_parser.add_argument("--tier", help="Filter by tier")

    # Process chapter results
    process_parser = subparsers.add_parser("process-chapter")
    process_parser.add_argument("--chapter", type=int, required=True, help="Chapter number")
    process_parser.add_argument("--data", required=True, help="Processing result as JSON")

    # Query chapter status
    status_get_parser = subparsers.add_parser("get-chapter-status")
    status_get_parser.add_argument("--chapter", type=int, required=True)

    # Set chapter status
    status_set_parser = subparsers.add_parser("set-chapter-status")
    status_set_parser.add_argument("--chapter", type=int, required=True)
    status_set_parser.add_argument("--status", required=True,
        choices=["chapter_rejected", "chapter_drafted", "chapter_reviewed", "chapter_committed"])

    argv = normalize_global_project_root(sys.argv[1:])
    args = parser.parse_args(argv)
    command_started_at = time.perf_counter()

    # Initialize
    config = None
    if args.project_root:
        # Accept a workspace root and resolve the actual book project_root, which must contain .webnovel/state.json.
        from project_locator import resolve_project_root
        from .config import DataModulesConfig

        try:
            resolved_root = resolve_project_root(args.project_root)
        except FileNotFoundError as exc:
            print_error(
                "INVALID_PROJECT_ROOT",
                str(exc),
                suggestion="Pass a book project root containing .webnovel/state.json, or resolve project_root with webnovel.py first.",
                )
            raise SystemExit(1) from exc
        config = DataModulesConfig.from_project_root(resolved_root)

    manager = StateManager(config)
    logger = IndexManager(config)
    json_base_dir = manager.config.project_root
    tool_name = f"state_manager:{args.command or 'unknown'}"

    def _append_timing(success: bool, *, error_code: str | None = None, error_message: str | None = None, chapter: int | None = None):
        elapsed_ms = int((time.perf_counter() - command_started_at) * 1000)
        safe_append_perf_timing(
            manager.config.project_root,
            tool_name=tool_name,
            success=success,
            elapsed_ms=elapsed_ms,
            chapter=chapter,
            error_code=error_code,
            error_message=error_message,
        )

    def emit_success(data=None, message: str = "ok", chapter: int | None = None):
        print_success(data, message=message)
        safe_log_tool_call(logger, tool_name=tool_name, success=True)
        _append_timing(True, chapter=chapter)

    def emit_error(code: str, message: str, suggestion: str | None = None, chapter: int | None = None):
        print_error(code, message, suggestion=suggestion)
        safe_log_tool_call(
            logger,
            tool_name=tool_name,
            success=False,
            error_code=code,
            error_message=message,
        )
        _append_timing(False, error_code=code, error_message=message, chapter=chapter)

    if args.command == "get-progress":
        emit_success(manager._state.get("progress", {}), message="progress")

    elif args.command == "get-entity":
        entity = manager.get_entity(args.id)
        if entity:
            emit_success(entity, message="entity")
        else:
            emit_error("NOT_FOUND", f"Entity not found: {args.id}")

    elif args.command == "list-entities":
        if args.type:
            entities = manager.get_entities_by_type(args.type)
        elif args.tier:
            entities = manager.get_entities_by_tier(args.tier)
        else:
            entities = manager.get_all_entities()

        payload = [{"id": eid, **e} for eid, e in entities.items()]
        emit_success(payload, message="entities")

    elif args.command == "process-chapter":
        data = load_json_arg(args.data, base_dir=json_base_dir)
        validated = None
        last_exc = None
        for _ in range(3):
            try:
                validated = validate_data_agent_output(data)
                break
            except ValidationError as exc:
                last_exc = exc
                data = normalize_data_agent_output(data)
        if validated is None:
            err = format_validation_error(last_exc) if last_exc else {
                "code": "SCHEMA_VALIDATION_FAILED",
                "message": "Data structure validation failed",
                "details": {"errors": []},
                "suggestion": "Check that data-agent output fields are complete and correctly typed",
            }
            emit_error(err["code"], err["message"], suggestion=err.get("suggestion"))
            return

        warnings = manager.process_chapter_result(args.chapter, validated.model_dump(by_alias=True))
        save_result = manager.save_state()
        if not save_result.get("sqlite_sync_ok", True):
            emit_error(
                "SQLITE_SYNC_FAILED",
                "Chapter state was written to state.json, but SQLite synchronization failed",
                suggestion=f"Run webnovel.py projections retry --chapter {args.chapter} to repair projections",
                chapter=args.chapter,
            )
            raise SystemExit(1)
        emit_success({"chapter": args.chapter, "warnings": warnings}, message="chapter_processed", chapter=args.chapter)

    elif args.command == "get-chapter-status":
        manager._load_state()
        status = manager.get_chapter_status(args.chapter)
        emit_success({"chapter": args.chapter, "status": status},
                     message="chapter_status")

    elif args.command == "set-chapter-status":
        manager._load_state()
        manager.set_chapter_status(args.chapter, args.status)
        emit_success({"chapter": args.chapter, "status": args.status},
                     message="chapter_status_set")

    else:
        emit_error("UNKNOWN_COMMAND", "No valid command specified", suggestion="See --help")


if __name__ == "__main__":
    if sys.platform == "win32":
        enable_windows_utf8_stdio()
    main()
