#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"Style Sampler manages high-quality chapter excerpts as style references, including storage, classification by scene type, and sample-selection strategies."

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from contextlib import contextmanager

from .config import get_config
from .observability import safe_append_perf_timing, safe_log_tool_call


class SceneType(Enum):
    "Scene type."
    BATTLE = "combat"
    DIALOGUE = "conversation"
    DESCRIPTION = "description"
    TRANSITION = "transition"
    EMOTION = "emotional-relationships"
    TENSION = "tension"
    COMEDY = "lighthearted"


@dataclass
class StyleSample:
    "Style sample."
    id: str
    chapter: int
    scene_type: str
    content: str
    score: float
    tags: List[str]
    created_at: str = ""


class StyleSampler:
    "Style sample manager."

    def __init__(self, config=None):
        self.config = config or get_config()
        self._init_db()

    def _init_db(self):
        "Initialize the database."
        self.config.ensure_dirs()
        with self._get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS samples (
                    id TEXT PRIMARY KEY,
                    chapter INTEGER,
                    scene_type TEXT,
                    content TEXT,
                    score REAL,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_samples_type ON samples(scene_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_samples_score ON samples(score DESC)")

            conn.commit()

    @contextmanager
    def _get_conn(self):
        "Get a database connection and ensure it closes, preventing Windows file-handle leaks that block temporary-directory cleanup."
        db_path = self.config.webnovel_dir / "style_samples.db"
        conn = sqlite3.connect(str(db_path))
        try:
            yield conn
        finally:
            conn.close()

    # ==================== Sample management ====================

    def add_sample(self, sample: StyleSample) -> bool:
        "Add a style sample."
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO samples
                    (id, chapter, scene_type, content, score, tags, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    sample.id,
                    sample.chapter,
                    sample.scene_type,
                    sample.content,
                    sample.score,
                    json.dumps(sample.tags, ensure_ascii=False),
                    sample.created_at or datetime.now().isoformat()
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_samples_by_type(
        self,
        scene_type: str,
        limit: int = 5,
        min_score: float = 0.0
    ) -> List[StyleSample]:
        "Get samples by scene type."
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, chapter, scene_type, content, score, tags, created_at
                FROM samples
                WHERE scene_type = ? AND score >= ?
                ORDER BY score DESC
                LIMIT ?
            """, (scene_type, min_score, limit))

            return [self._row_to_sample(row) for row in cursor.fetchall()]

    def get_best_samples(self, limit: int = 10) -> List[StyleSample]:
        "Get the highest-scoring samples."
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, chapter, scene_type, content, score, tags, created_at
                FROM samples
                ORDER BY score DESC
                LIMIT ?
            """, (limit,))

            return [self._row_to_sample(row) for row in cursor.fetchall()]

    def _safe_tags(self, raw) -> List[str]:
        if not raw:
            return []
        try:
            value = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return []
        return value if isinstance(value, list) else []

    def _row_to_sample(self, row) -> StyleSample:
        "Convert a database row into a sample object."
        return StyleSample(
            id=row[0],
            chapter=row[1],
            scene_type=row[2],
            content=row[3],
            score=row[4],
            tags=self._safe_tags(row[5]),
            created_at=row[6]
        )

    # ==================== Sample extraction ====================

    def extract_candidates(
        self,
        chapter: int,
        content: str,
        review_score: float,
        scenes: List[Dict]
    ) -> List[StyleSample]:
        "Extract candidate style samples from a chapter only when review_score >= 80."
        if review_score < 80:
            return []

        candidates = []

        for scene in scenes:
            scene_type = self._classify_scene_type(scene)
            scene_content = scene.get("content", "")

            # Skip scenes that are too short
            if len(scene_content) < 200:
                continue

            # Create a sample
            sample = StyleSample(
                id=f"ch{chapter}_s{scene.get('index', 0)}",
                chapter=chapter,
                scene_type=scene_type,
                content=scene_content[:2000],  # Limit length
                score=review_score / 100.0,
                tags=self._extract_tags(scene_content)
            )
            candidates.append(sample)

        return candidates

    def _classify_scene_type(self, scene: Dict) -> str:
        "Classify the scene type."
        summary = scene.get("summary", "").lower()
        content = scene.get("content", "").lower()

        # Simple keyword classification
        battle_keywords = ["combat", "attack", "strikes", "fist", "sword", "kill", "hit", "fight"]
        dialogue_keywords = ["said", "asked", "said with a smile", "said coldly", "conversation"]
        emotion_keywords = ["inwardly", "feels", "emotion", "tears", "pain", "joy"]
        tension_keywords = ["danger", "tension", "fear", "pressure"]

        text = summary + content

        if any(kw in text for kw in battle_keywords):
            return SceneType.BATTLE.value
        elif any(kw in text for kw in tension_keywords):
            return SceneType.TENSION.value
        elif any(kw in text for kw in dialogue_keywords):
            return SceneType.DIALOGUE.value
        elif any(kw in text for kw in emotion_keywords):
            return SceneType.EMOTION.value
        else:
            return SceneType.DESCRIPTION.value

    def _extract_tags(self, content: str) -> List[str]:
        "Extract content tags."
        tags = []

        # Simple tag extraction
        if "combat" in content or "attack" in content:
            tags.append("combat")
        if "cultivation" in content or "breakthrough" in content:
            tags.append("cultivation")
        if "conversation" in content or "said" in content:
            tags.append("conversation")
        if "description" in content or "scenery" in content:
            tags.append("description")

        return tags[:5]

    # ==================== Sample selection ====================

    def select_samples_for_chapter(
        self,
        chapter_outline: str,
        target_types: List[str] = None,
        max_samples: int = 3
    ) -> List[StyleSample]:
        "Select appropriate style samples for chapter writing by analyzing the outline's requirements."
        if target_types is None:
            # Infer required scene types from the outline
            target_types = self._infer_scene_types(chapter_outline)

        samples = []
        per_type = max(1, max_samples // len(target_types)) if target_types else max_samples

        for scene_type in target_types:
            type_samples = self.get_samples_by_type(scene_type, limit=per_type, min_score=0.8)
            samples.extend(type_samples)

        return samples[:max_samples]

    def _infer_scene_types(self, outline: str) -> List[str]:
        "Infer required scene types from the outline."
        types = []

        if any(kw in outline for kw in ["battle", "combat", "duel", "sparring", "exchange blows"]):
            types.append(SceneType.BATTLE.value)

        if any(kw in outline for kw in ["conversation", "conversation", "consult", "discuss"]):
            types.append(SceneType.DIALOGUE.value)

        if any(kw in outline for kw in ["emotional-relationships", "feelings", "psychology", "psychological", "emotional"]):
            types.append(SceneType.EMOTION.value)

        if not types:
            types = [SceneType.DESCRIPTION.value]

        return types

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        "Get sample statistics."
        with self._get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM samples")
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT scene_type, COUNT(*) as count
                FROM samples
                GROUP BY scene_type
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT AVG(score) FROM samples")
            avg_score = cursor.fetchone()[0] or 0

            return {
                "total": total,
                "by_type": by_type,
                "avg_score": round(avg_score, 3)
            }


# ==================== CLI ====================

def main():
    import argparse
    import sys
    from .cli_output import print_success, print_error
    from .cli_args import normalize_global_project_root, load_json_arg
    from .index_manager import IndexManager

    parser = argparse.ArgumentParser(description="Style Sampler CLI")
    parser.add_argument("--project-root", type=str, help="Project root")

    subparsers = parser.add_subparsers(dest="command")

    # Get statistics
    subparsers.add_parser("stats")

    # List samples
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--type", help="Filter by type")
    list_parser.add_argument("--limit", type=int, default=10)

    # Extract samples
    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("--chapter", type=int, required=True)
    extract_parser.add_argument("--score", type=float, required=True)
    extract_parser.add_argument("--scenes", required=True, help="Scene list as JSON")

    # Select samples
    select_parser = subparsers.add_parser("select")
    select_parser.add_argument("--outline", required=True, help="Chapter outline")
    select_parser.add_argument("--max", type=int, default=3)

    argv = normalize_global_project_root(sys.argv[1:])
    args = parser.parse_args(argv)
    command_started_at = time.perf_counter()

    # Initialize
    config = None
    if args.project_root:
        # Accept a workspace root and resolve the actual book project_root, which must contain .webnovel/state.json.
        from project_locator import resolve_project_root
        from .config import DataModulesConfig

        resolved_root = resolve_project_root(args.project_root)
        config = DataModulesConfig.from_project_root(resolved_root)

    sampler = StyleSampler(config)
    logger = IndexManager(config)
    tool_name = f"style_sampler:{args.command or 'unknown'}"

    def _append_timing(success: bool, *, error_code: str | None = None, error_message: str | None = None, chapter: int | None = None):
        elapsed_ms = int((time.perf_counter() - command_started_at) * 1000)
        safe_append_perf_timing(
            sampler.config.project_root,
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

    if args.command == "stats":
        stats = sampler.get_stats()
        emit_success(stats, message="stats")

    elif args.command == "list":
        if args.type:
            samples = sampler.get_samples_by_type(args.type, args.limit)
        else:
            samples = sampler.get_best_samples(args.limit)
        emit_success([s.__dict__ for s in samples], message="samples")

    elif args.command == "extract":
        scenes = load_json_arg(args.scenes, base_dir=sampler.config.project_root)
        candidates = sampler.extract_candidates(
            chapter=args.chapter,
            content="",
            review_score=args.score,
            scenes=scenes,
        )

        added = []
        skipped = []
        for c in candidates:
            if sampler.add_sample(c):
                added.append(c.id)
            else:
                skipped.append(c.id)
        emit_success({"added": added, "skipped": skipped}, message="extracted", chapter=args.chapter)

    elif args.command == "select":
        samples = sampler.select_samples_for_chapter(args.outline, max_samples=args.max)
        emit_success([s.__dict__ for s in samples], message="selected")

    else:
        emit_error("UNKNOWN_COMMAND", "No valid command specified", suggestion="See --help")


if __name__ == "__main__":
    main()
