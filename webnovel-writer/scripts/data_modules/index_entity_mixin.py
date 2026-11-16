#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IndexEntityMixin extracted from IndexManager.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class IndexEntityMixin:
    def _register_alias_with_cursor(
        self, cursor: sqlite3.Cursor, alias: str, entity_id: str, entity_type: str
    ) -> bool:
        alias = str(alias).strip() if alias is not None else ""
        if not alias or not entity_id:
            return False

        cursor.execute(
            """
            INSERT OR IGNORE INTO aliases (alias, entity_id, entity_type)
            VALUES (?, ?, ?)
        """,
            (alias, entity_id, entity_type),
        )
        return cursor.rowcount > 0

    def _register_canonical_alias(
        self, cursor: sqlite3.Cursor, entity: EntityMeta
    ) -> None:
        canonical_name = str(entity.canonical_name).strip() if entity.canonical_name else ""
        if canonical_name and canonical_name != entity.id:
            self._register_alias_with_cursor(
                cursor, canonical_name, entity.id, entity.type
            )
        if entity.is_protagonist:
            for alias in self._protagonist_aliases(entity, canonical_name):
                self._register_alias_with_cursor(cursor, alias, entity.id, entity.type)

    def _protagonist_aliases(self, entity: EntityMeta, canonical_name: str) -> List[str]:
        aliases = ["protagonist", "protagonist"]
        compact_id = str(entity.id or "").replace("_", "").replace("-", "").strip()
        if compact_id and compact_id != entity.id:
            aliases.append(compact_id)
        if canonical_name:
            aliases.append(canonical_name)
        return list(dict.fromkeys(alias for alias in aliases if alias and alias != entity.id))

    def upsert_entity(self, entity: EntityMeta, update_metadata: bool = False) -> bool:
        'Insert or intelligently merge an entity. Insert new entities directly; for existing entities update current_json, last_appearance, and updated_at. With update_metadata=True also update canonical_name, tier, desc, is_protagonist, and is_archived. Return whether the entity is new.'
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Check whether it exists.
            cursor.execute(
                "SELECT id, current_json FROM entities WHERE id = ?", (entity.id,)
            )
            existing = cursor.fetchone()

            if existing:
                # Existing entity: intelligently merge current_json.
                old_current = {}
                if existing["current_json"]:
                    try:
                        old_current = json.loads(existing["current_json"])
                    except json.JSONDecodeError as exc:
                        logger.warning(
                            "failed to parse JSON in entities.current_json: %s",
                            exc,
                        )

                # Merge current state, with new values overriding old ones.
                merged_current = {**old_current, **entity.current}

                if update_metadata:
                    # Full update, including metadata
                    cursor.execute(
                        """
                        UPDATE entities SET
                            type = ?,
                            canonical_name = ?,
                            tier = ?,
                            desc = ?,
                            current_json = ?,
                            last_appearance = ?,
                            is_protagonist = ?,
                            is_archived = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """,
                        (
                            entity.type,
                            entity.canonical_name,
                            entity.tier,
                            entity.desc,
                            json.dumps(merged_current, ensure_ascii=False),
                            entity.last_appearance,
                            1 if entity.is_protagonist else 0,
                            1 if entity.is_archived else 0,
                            entity.id,
                        ),
                    )
                else:
                    # Update only current state and last_appearance.
                    cursor.execute(
                        """
                        UPDATE entities SET
                            current_json = ?,
                            last_appearance = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """,
                        (
                            json.dumps(merged_current, ensure_ascii=False),
                            entity.last_appearance,
                            entity.id,
                        ),
                    )
                self._register_canonical_alias(cursor, entity)
                conn.commit()
                return False
            else:
                # New entity: insert.
                cursor.execute(
                    """
                    INSERT INTO entities
                    (id, type, canonical_name, tier, desc, current_json,
                     first_appearance, last_appearance, is_protagonist, is_archived)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entity.id,
                        entity.type,
                        entity.canonical_name,
                        entity.tier,
                        entity.desc,
                        json.dumps(entity.current, ensure_ascii=False),
                        entity.first_appearance,
                        entity.last_appearance,
                        1 if entity.is_protagonist else 0,
                        1 if entity.is_archived else 0,
                    ),
                )
                self._register_canonical_alias(cursor, entity)
                conn.commit()
                return True

    def get_entity(self, entity_id: str) -> Optional[Dict]:
        'Get one entity, falling back to alias lookup when the ID is not found.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row, parse_json=["current_json"])

        alias_matches = self.get_entities_by_alias(entity_id)
        if alias_matches:
            return alias_matches[0]

        # ID-style fallback: if the caller passes 'lu_ming' but the registered ID is 'luming',
        # strip separators (underscores/hyphens) and retry direct ID lookup.
        compact = str(entity_id or "").replace("_", "").replace("-", "").strip()
        if compact and compact != entity_id:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM entities WHERE id = ?", (compact,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict(row, parse_json=["current_json"])
            alias_matches = self.get_entities_by_alias(compact)
            if alias_matches:
                return alias_matches[0]

        return None

    def get_entities_by_type(
        self, entity_type: str, include_archived: bool = False
    ) -> List[Dict]:
        'Get entities by type.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if include_archived:
                cursor.execute(
                    """
                    SELECT * FROM entities WHERE type = ?
                    ORDER BY last_appearance DESC
                """,
                    (entity_type,),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM entities WHERE type = ? AND is_archived = 0
                    ORDER BY last_appearance DESC
                """,
                    (entity_type,),
                )
            return [
                self._row_to_dict(row, parse_json=["current_json"])
                for row in cursor.fetchall()
            ]

    def get_entities_by_tier(self, tier: str) -> List[Dict]:
        'Get entities by importance tier: core, important, minor, or decorative.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM entities WHERE tier = ? AND is_archived = 0
                ORDER BY last_appearance DESC
            """,
                (tier,),
            )
            return [
                self._row_to_dict(row, parse_json=["current_json"])
                for row in cursor.fetchall()
            ]

    def get_core_entities(self) -> List[Dict]:
        'Get all core entities for full loading by the Context Agent.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM entities
                WHERE (tier IN ('core', 'major') OR is_protagonist = 1) AND is_archived = 0
                ORDER BY is_protagonist DESC, tier, last_appearance DESC
            """)
            return [
                self._row_to_dict(row, parse_json=["current_json"])
                for row in cursor.fetchall()
            ]

    def get_protagonist(self) -> Optional[Dict]:
        'Get the protagonist entity.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM entities WHERE is_protagonist = 1 LIMIT 1")
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row, parse_json=["current_json"])
            return None

    def update_entity_current(self, entity_id: str, updates: Dict) -> bool:
        'Incrementally update an entity\'s current field without overwriting other fields. Example: update_entity_current("xiaoyan", {"realm": "battle master"}).'
        with self._get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT current_json FROM entities WHERE id = ?", (entity_id,)
            )
            row = cursor.fetchone()
            if not row:
                return False

            current = {}
            if row["current_json"]:
                try:
                    current = json.loads(row["current_json"])
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "failed to parse JSON in update_entity_current current_json: %s",
                        exc,
                    )

            current.update(updates)

            cursor.execute(
                """
                UPDATE entities SET
                    current_json = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (json.dumps(current, ensure_ascii=False), entity_id),
            )
            conn.commit()
            return True

    def archive_entity(self, entity_id: str) -> bool:
        'Archive an entity by marking it rather than deleting it.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE entities SET is_archived = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (entity_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    # ==================== v5.1 Alias operations ====================

    def register_alias(self, alias: str, entity_id: str, entity_type: str) -> bool:
        'Register an alias with one-to-many support. The same alias can map to multiple entities, such as a sect name referring to both a place and a faction.'
        alias = str(alias).strip() if alias is not None else ""
        if not alias or not entity_id:
            return False

        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                inserted = self._register_alias_with_cursor(
                    cursor, alias, entity_id, entity_type
                )
                conn.commit()
                return inserted
            except sqlite3.IntegrityError:
                return False

    def get_entities_by_alias(self, alias: str) -> List[Dict]:
        'Find all entities matching an alias, including matches of different types.'
        alias = str(alias).strip() if alias is not None else ""
        if not alias:
            return []

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.*, a.entity_type as alias_type
                FROM entities e
                JOIN aliases a ON e.id = a.entity_id
                WHERE a.alias = ?
                ORDER BY
                    e.is_archived ASC,
                    e.is_protagonist DESC,
                    CASE e.tier
                        WHEN 'core' THEN 0
                        WHEN 'major' THEN 1
                        WHEN 'minor' THEN 2
                        ELSE 3
                    END,
                    e.last_appearance DESC,
                    e.id ASC
            """,
                (alias,),
            )
            return [
                self._row_to_dict(row, parse_json=["current_json"])
                for row in cursor.fetchall()
            ]

    def get_entity_aliases(self, entity_id: str) -> List[str]:
        'Get every alias for an entity.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT alias FROM aliases WHERE entity_id = ?", (entity_id,)
            )
            return [row["alias"] for row in cursor.fetchall()]

    def remove_alias(self, alias: str, entity_id: str) -> bool:
        'Remove an alias.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM aliases WHERE alias = ? AND entity_id = ?",
                (alias, entity_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    # ==================== v5.1 State-change operations ====================

    def record_state_change(self, change: StateChangeMeta) -> int:
        'Record a state change and return the record ID.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO state_changes
                (entity_id, field, old_value, new_value, reason, chapter)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    change.entity_id,
                    change.field,
                    change.old_value,
                    change.new_value,
                    change.reason,
                    change.chapter,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_entity_state_changes(self, entity_id: str, limit: int = 20) -> List[Dict]:
        "Get an entity's state-change history."
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM state_changes
                WHERE entity_id = ?
                ORDER BY chapter DESC, id DESC
                LIMIT ?
            """,
                (entity_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_state_changes(self, limit: int = 50) -> List[Dict]:
        'Get recent state changes.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM state_changes
                ORDER BY chapter DESC, id DESC
                LIMIT ?
            """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_chapter_state_changes(self, chapter: int) -> List[Dict]:
        'Get all state changes in a chapter.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM state_changes
                WHERE chapter = ?
                ORDER BY id
            """,
                (chapter,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # ==================== v5.1 Relationship operations ====================

    def upsert_relationship(self, rel: RelationshipMeta) -> bool:
        'Insert or update a relationship. An existing (from, to, type) updates description and chapter. Return whether the relationship is new.'
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Check whether it exists.
            cursor.execute(
                """
                SELECT id FROM relationships
                WHERE from_entity = ? AND to_entity = ? AND type = ?
            """,
                (rel.from_entity, rel.to_entity, rel.type),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """
                    UPDATE relationships SET
                        description = ?,
                        chapter = ?
                    WHERE id = ?
                """,
                    (rel.description, rel.chapter, existing["id"]),
                )
                conn.commit()
                return False
            else:
                cursor.execute(
                    """
                    INSERT INTO relationships
                    (from_entity, to_entity, type, description, chapter)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        rel.from_entity,
                        rel.to_entity,
                        rel.type,
                        rel.description,
                        rel.chapter,
                    ),
                )
                conn.commit()
                return True

    def get_entity_relationships(
        self, entity_id: str, direction: str = "both"
    ) -> List[Dict]:
        'Get an entity\'s relationships. direction is "from", "to", or "both".'
        with self._get_conn() as conn:
            cursor = conn.cursor()

            if direction == "from":
                cursor.execute(
                    """
                    SELECT * FROM relationships WHERE from_entity = ?
                    ORDER BY chapter DESC
                """,
                    (entity_id,),
                )
            elif direction == "to":
                cursor.execute(
                    """
                    SELECT * FROM relationships WHERE to_entity = ?
                    ORDER BY chapter DESC
                """,
                    (entity_id,),
                )
            else:  # both
                cursor.execute(
                    """
                    SELECT * FROM relationships
                    WHERE from_entity = ? OR to_entity = ?
                    ORDER BY chapter DESC
                """,
                    (entity_id, entity_id),
                )

            return [dict(row) for row in cursor.fetchall()]

    def get_relationship_between(self, entity1: str, entity2: str) -> List[Dict]:
        'Get all relationships between two entities.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM relationships
                WHERE (from_entity = ? AND to_entity = ?)
                   OR (from_entity = ? AND to_entity = ?)
                ORDER BY chapter DESC
            """,
                (entity1, entity2, entity2, entity1),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_relationships(self, limit: int = 30) -> List[Dict]:
        'Get recently established relationships.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM relationships
                ORDER BY chapter DESC, id DESC
                LIMIT ?
            """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # ==================== v5.5 Relationship events and graph ====================

    def _infer_relationship_polarity(self, rel_type: str) -> int:
        'Infer polarity from relationship type: -1 hostile, 0 neutral, 1 friendly.'
        t = str(rel_type or "")
        positive_keywords = ("ally", "friendly", "mentor-student", "companion", "family", "love", "cooperation")
        negative_keywords = ("enemy", "feud", "hatred", "opposition", "conflict", "betrayal", "pursuit")

        if any(k in t for k in negative_keywords):
            return -1
        if any(k in t for k in positive_keywords):
            return 1
        return 0

    def record_relationship_event(self, event: RelationshipEventMeta) -> int:
        'Record a relationship event and return its ID.'
        from_entity = str(getattr(event, "from_entity", "") or "").strip()
        to_entity = str(getattr(event, "to_entity", "") or "").strip()
        rel_type = str(getattr(event, "type", "") or "").strip()
        if not from_entity or not to_entity or not rel_type:
            return 0

        action = str(getattr(event, "action", "update") or "update").strip().lower()
        if action not in {"create", "update", "decay", "remove"}:
            action = "update"

        try:
            chapter = int(getattr(event, "chapter", 0) or 0)
        except (TypeError, ValueError):
            return 0
        if chapter <= 0:
            return 0
        try:
            scene_index = int(getattr(event, "scene_index", 0) or 0)
        except (TypeError, ValueError):
            scene_index = 0

        raw_polarity = getattr(event, "polarity", None)
        if raw_polarity is None:
            polarity = self._infer_relationship_polarity(rel_type)
        else:
            try:
                polarity = int(raw_polarity)
            except (TypeError, ValueError):
                polarity = 0
        if polarity > 1:
            polarity = 1
        elif polarity < -1:
            polarity = -1

        try:
            strength = float(getattr(event, "strength", 0.5) or 0.5)
        except (TypeError, ValueError):
            strength = 0.5
        strength = max(0.0, min(1.0, strength))

        description = str(getattr(event, "description", "") or "").strip()
        evidence = str(getattr(event, "evidence", "") or "").strip()
        try:
            confidence = float(getattr(event, "confidence", 1.0) or 1.0)
        except (TypeError, ValueError):
            confidence = 1.0
        confidence = max(0.0, min(1.0, confidence))

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO relationship_events
                (from_entity, to_entity, type, action, polarity, strength, description, chapter, scene_index, evidence, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    from_entity,
                    to_entity,
                    rel_type,
                    action,
                    polarity,
                    strength,
                    description,
                    chapter,
                    scene_index,
                    evidence,
                    confidence,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)

    def get_relationship_events(
        self,
        entity_id: str,
        direction: str = "both",
        from_chapter: Optional[int] = None,
        to_chapter: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        'Query relationship events by entity.'
        direction = str(direction or "both").lower()
        clauses: List[str] = []
        params: List[Any] = []

        if direction == "from":
            clauses.append("from_entity = ?")
            params.append(entity_id)
        elif direction == "to":
            clauses.append("to_entity = ?")
            params.append(entity_id)
        else:
            clauses.append("(from_entity = ? OR to_entity = ?)")
            params.extend([entity_id, entity_id])

        if from_chapter is not None:
            clauses.append("chapter >= ?")
            params.append(int(from_chapter))
        if to_chapter is not None:
            clauses.append("chapter <= ?")
            params.append(int(to_chapter))

        where_sql = " AND ".join(clauses) if clauses else "1=1"
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM relationship_events
                WHERE {where_sql}
                ORDER BY chapter DESC, id DESC
                LIMIT ?
            """,
                (*params, int(limit)),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_relationship_timeline(
        self,
        entity1: str,
        entity2: str,
        from_chapter: Optional[int] = None,
        to_chapter: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        'Query the relationship timeline between two entities.'
        clauses = [
            "((from_entity = ? AND to_entity = ?) OR (from_entity = ? AND to_entity = ?))"
        ]
        params: List[Any] = [entity1, entity2, entity2, entity1]

        if from_chapter is not None:
            clauses.append("chapter >= ?")
            params.append(int(from_chapter))
        if to_chapter is not None:
            clauses.append("chapter <= ?")
            params.append(int(to_chapter))

        where_sql = " AND ".join(clauses)
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM relationship_events
                WHERE {where_sql}
                ORDER BY chapter ASC, id ASC
                LIMIT ?
            """,
                (*params, int(limit)),
            )
            return [dict(row) for row in cursor.fetchall()]

    def _load_effective_relationship_edges(
        self,
        chapter: Optional[int] = None,
        relation_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        'Load valid relationship edges at a given chapter snapshot.'
        relation_types = [str(t) for t in (relation_types or []) if str(t).strip()]

        with self._get_conn() as conn:
            cursor = conn.cursor()
            if chapter is None:
                clauses = []
                params: List[Any] = []
                if relation_types:
                    placeholders = ",".join("?" for _ in relation_types)
                    clauses.append(f"type IN ({placeholders})")
                    params.extend(relation_types)

                where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
                cursor.execute(
                    f"""
                    SELECT from_entity, to_entity, type, description, chapter
                    FROM relationships
                    {where_sql}
                    ORDER BY chapter DESC, id DESC
                """,
                    tuple(params),
                )
                rows = cursor.fetchall()
                return [
                    {
                        "from": str(r["from_entity"]),
                        "to": str(r["to_entity"]),
                        "type": str(r["type"]),
                        "description": str(r["description"] or ""),
                        "chapter": int(r["chapter"] or 0),
                        "action": "snapshot",
                        "polarity": self._infer_relationship_polarity(str(r["type"])),
                        "strength": 0.5,
                        "evidence": "",
                        "confidence": 1.0,
                    }
                    for r in rows
                ]

            clauses = ["chapter <= ?"]
            params = [int(chapter)]
            if relation_types:
                placeholders = ",".join("?" for _ in relation_types)
                clauses.append(f"type IN ({placeholders})")
                params.extend(relation_types)

            cursor.execute(
                f"""
                SELECT *
                FROM relationship_events
                WHERE {' AND '.join(clauses)}
                ORDER BY chapter DESC, id DESC
            """,
                tuple(params),
            )
            event_rows = cursor.fetchall()

            # Legacy-data compatibility: if the event stream is incomplete, supplement edges from the relationships snapshot.
            snapshot_clauses = ["chapter <= ?"]
            snapshot_params: List[Any] = [int(chapter)]
            if relation_types:
                placeholders = ",".join("?" for _ in relation_types)
                snapshot_clauses.append(f"type IN ({placeholders})")
                snapshot_params.extend(relation_types)
            cursor.execute(
                f"""
                SELECT from_entity, to_entity, type, description, chapter
                FROM relationships
                WHERE {' AND '.join(snapshot_clauses)}
                ORDER BY chapter DESC, id DESC
            """,
                tuple(snapshot_params),
            )
            snapshot_rows = cursor.fetchall()

        # At a chapter snapshot, retain only the latest event for each relationship; remove means no longer valid.
        effective: List[Dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for row in event_rows:
            key = (
                str(row["from_entity"]),
                str(row["to_entity"]),
                str(row["type"]),
            )
            if key in seen:
                continue
            seen.add(key)
            action = str(row["action"] or "update")
            if action == "remove":
                continue
            effective.append(
                {
                    "from": key[0],
                    "to": key[1],
                    "type": key[2],
                    "description": str(row["description"] or ""),
                    "chapter": int(row["chapter"] or 0),
                    "action": action,
                    "polarity": int(row["polarity"] or 0),
                    "strength": float(row["strength"] or 0.5),
                    "evidence": str(row["evidence"] or ""),
                    "confidence": float(row["confidence"] or 1.0),
                }
            )

        # Fill missing event-stream entries from the relationship snapshot; existing keys keep the event's value.
        for row in snapshot_rows:
            key = (
                str(row["from_entity"]),
                str(row["to_entity"]),
                str(row["type"]),
            )
            if key in seen:
                continue
            effective.append(
                {
                    "from": key[0],
                    "to": key[1],
                    "type": key[2],
                    "description": str(row["description"] or ""),
                    "chapter": int(row["chapter"] or 0),
                    "action": "snapshot",
                    "polarity": self._infer_relationship_polarity(key[2]),
                    "strength": 0.5,
                    "evidence": "",
                    "confidence": 1.0,
                }
            )
        return effective

    def build_relationship_subgraph(
        self,
        center_entity: str,
        depth: int = 2,
        chapter: Optional[int] = None,
        top_edges: int = 50,
        relation_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        'Build a relationship subgraph around a central entity.'
        center_entity = str(center_entity or "").strip()
        depth = max(1, int(depth or 1))
        top_edges = max(1, int(top_edges or 1))

        edges_all = self._load_effective_relationship_edges(
            chapter=chapter,
            relation_types=relation_types,
        )
        edges_all.sort(key=lambda x: int(x.get("chapter", 0)), reverse=True)

        selected_edges: List[Dict[str, Any]] = []
        selected_keys: set[tuple[str, str, str]] = set()
        visited_nodes: set[str] = {center_entity} if center_entity else set()
        frontier: set[str] = {center_entity} if center_entity else set()

        for _ in range(depth):
            if not frontier:
                break
            next_frontier: set[str] = set()

            for edge in edges_all:
                from_entity = str(edge.get("from") or "")
                to_entity = str(edge.get("to") or "")
                if from_entity not in frontier and to_entity not in frontier:
                    continue

                key = (from_entity, to_entity, str(edge.get("type") or ""))
                if key in selected_keys:
                    continue
                selected_keys.add(key)
                selected_edges.append(edge)

                if from_entity and from_entity not in visited_nodes:
                    visited_nodes.add(from_entity)
                    next_frontier.add(from_entity)
                if to_entity and to_entity not in visited_nodes:
                    visited_nodes.add(to_entity)
                    next_frontier.add(to_entity)

                if len(selected_edges) >= top_edges:
                    break

            frontier = next_frontier
            if len(selected_edges) >= top_edges:
                break

        if center_entity and center_entity not in visited_nodes:
            visited_nodes.add(center_entity)

        # Query node details.
        entity_map: Dict[str, Dict[str, Any]] = {}
        if visited_nodes:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                placeholders = ",".join("?" for _ in visited_nodes)
                cursor.execute(
                    f"""
                    SELECT id, canonical_name, type, tier, last_appearance
                    FROM entities
                    WHERE id IN ({placeholders})
                """,
                    tuple(visited_nodes),
                )
                for row in cursor.fetchall():
                    entity_map[str(row["id"])] = {
                        "id": str(row["id"]),
                        "name": str(row["canonical_name"] or row["id"]),
                        "type": str(row["type"] or "unknown"),
                        "tier": str(row["tier"] or "decorative"),
                        "last_appearance": int(row["last_appearance"] or 0),
                    }

        nodes: List[Dict[str, Any]] = []
        for entity_id in sorted(
            visited_nodes,
            key=lambda eid: (
                0 if eid == center_entity else 1,
                -(entity_map.get(eid, {}).get("last_appearance", 0)),
                eid,
            ),
        ):
            if entity_id in entity_map:
                nodes.append(entity_map[entity_id])
            else:
                nodes.append(
                    {
                        "id": entity_id,
                        "name": entity_id or "unknown",
                        "type": "unknown",
                        "tier": "decorative",
                        "last_appearance": 0,
                    }
                )

        return {
            "center": center_entity,
            "depth": depth,
            "chapter": chapter,
            "nodes": nodes,
            "edges": selected_edges[:top_edges],
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }

    def _sanitize_mermaid_node_id(self, raw_id: str) -> str:
        safe = re.sub(r"[^0-9a-zA-Z_]", "_", str(raw_id or "node"))
        if not safe:
            safe = "node"
        if safe[0].isdigit():
            safe = f"n_{safe}"
        return safe

    def render_relationship_subgraph_mermaid(self, graph: Dict[str, Any]) -> str:
        'Render a relationship subgraph as Mermaid.'
        lines = ["```mermaid", "graph LR"]
        nodes = graph.get("nodes") or []
        edges = graph.get("edges") or []

        if not nodes:
            lines.append("    EMPTY[No relationship data]")
            lines.append("```")
            return "\n".join(lines)

        node_alias: Dict[str, str] = {}
        for node in nodes:
            entity_id = str(node.get("id") or "")
            if not entity_id:
                continue
            alias = self._sanitize_mermaid_node_id(entity_id)
            node_alias[entity_id] = alias
            label = str(node.get("name") or entity_id).replace('"', "'")
            lines.append(f'    {alias}["{label}"]')

        for edge in edges:
            from_entity = str(edge.get("from") or "")
            to_entity = str(edge.get("to") or "")
            if from_entity not in node_alias or to_entity not in node_alias:
                continue
            edge_type = str(edge.get("type") or "related")
            chapter = edge.get("chapter")
            chapter_suffix = f"@{chapter}" if chapter not in (None, "") else ""
            label = f"{edge_type}{chapter_suffix}".replace('"', "'")
            try:
                polarity = int(edge.get("polarity", 0) or 0)
            except (TypeError, ValueError):
                polarity = 0
            if polarity < 0:
                connector = "-.->"
            else:
                connector = "-->"
            lines.append(
                f"    {node_alias[from_entity]} {connector}|{label}| {node_alias[to_entity]}"
            )

        lines.append("```")
        return "\n".join(lines)

    # ==================== v5.3 Override Contract operations ====================


    def update_entity_field(self, entity_id: str, field: str, value: Any) -> bool:
        """Compatibility helper to update a single entity field in current_json."""
        return self.update_entity_current(entity_id, {field: value})
