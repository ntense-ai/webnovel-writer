"""
Webnovel Dashboard - FastAPI application

GET endpoints only (strictly read-only); path_guard validates every file read against traversal.
"""

import asyncio
import json
import sqlite3
import sys
from datetime import datetime, timezone
from contextlib import asynccontextmanager, closing
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .path_guard import safe_resolve
from .watcher import FileWatcher

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_project_root: Path | None = None
_watcher = FileWatcher()

STATIC_DIR = Path(__file__).parent / "frontend" / "dist"
LOCAL_CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]


def _get_project_root() -> Path:
    if _project_root is None:
        raise HTTPException(status_code=500, detail="Project root is not configured")
    return _project_root


def _webnovel_dir() -> Path:
    return _get_project_root() / ".webnovel"


def _story_system_dir() -> Path:
    return _get_project_root() / ".story-system"


def _build_story_runtime_health_report(project_root: Path) -> dict:
    from data_modules.story_runtime_health import build_story_runtime_health

    return build_story_runtime_health(project_root)


def _ensure_scripts_dir_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    scripts_entry = str(scripts_dir)
    if scripts_entry not in sys.path:
        sys.path.insert(0, scripts_entry)


def _load_state_payload(*, required: bool = False) -> dict:
    state_path = _webnovel_dir() / "state.json"
    if not state_path.is_file():
        if required:
            raise HTTPException(404, "state.json not found")
        return {}

    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"Cannot read state.json: {exc}") from exc

    return payload if isinstance(payload, dict) else {}


def _parse_json_value(raw: object, default):
    if raw is None:
        return default
    if isinstance(raw, (dict, list)):
        return raw
    if not isinstance(raw, str):
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _resolve_volume_for_chapter(state: dict, chapter: int) -> int | None:
    progress = state.get("progress") if isinstance(state, dict) else {}
    if not isinstance(progress, dict):
        return None
    volumes_planned = progress.get("volumes_planned")
    if not isinstance(volumes_planned, list):
        return None

    best: tuple[int, int] | None = None
    for item in volumes_planned:
        if not isinstance(item, dict):
            continue
        volume = item.get("volume")
        if not isinstance(volume, int) or volume <= 0:
            continue
        chapter_range = str(item.get("chapters_range") or "").strip()
        if "-" not in chapter_range:
            continue
        left, _, right = chapter_range.partition("-")
        try:
            start = int(left.strip())
            end = int(right.strip())
        except ValueError:
            continue
        if start <= 0 or end <= 0 or start > end:
            continue
        if start <= chapter <= end:
            candidate = (start, volume)
            if best is None or candidate[0] > best[0] or (
                candidate[0] == best[0] and candidate[1] < best[1]
            ):
                best = candidate
    return best[1] if best else None


def _build_strand_map(state: dict) -> dict[int, str]:
    tracker = state.get("strand_tracker") if isinstance(state, dict) else {}
    history = tracker.get("history") if isinstance(tracker, dict) else []
    if not isinstance(history, list):
        return {}

    strand_map: dict[int, str] = {}
    for index, entry in enumerate(history, start=1):
        if not isinstance(entry, dict):
            continue
        chapter_value = entry.get("chapter", index)
        try:
            chapter = int(chapter_value)
        except (TypeError, ValueError):
            chapter = index
        strand = str(entry.get("strand") or entry.get("dominant") or "").strip().lower()
        if chapter > 0 and strand:
            strand_map[chapter] = strand
    return strand_map


def _extract_story_chapter(path: Path) -> int:
    stem = path.stem
    if "_" not in stem:
        return 0
    _, _, tail = stem.partition("_")
    try:
        return int(tail.split(".")[0])
    except ValueError:
        return 0


def _inspect_vector_db(project_root: Path) -> dict:
    from data_modules.config import DataModulesConfig

    cfg = DataModulesConfig.from_project_root(project_root)
    vector_db = cfg.vector_db
    exists = vector_db.is_file()
    size_bytes = vector_db.stat().st_size if exists else 0
    record_count = 0
    error = ""

    if exists and size_bytes > 0:
        try:
            with sqlite3.connect(str(vector_db)) as conn:
                cursor = conn.cursor()
                table_exists = cursor.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'vectors'"
                ).fetchone()
                if table_exists:
                    row = cursor.execute("SELECT COUNT(*) FROM vectors").fetchone()
                    record_count = int(row[0] or 0) if row else 0
        except sqlite3.Error as exc:
            error = str(exc)

    return {
        "path": str(vector_db),
        "exists": exists,
        "size_bytes": size_bytes,
        "record_count": record_count,
        "error": error,
    }


def _build_env_status(project_root: Path) -> dict:
    from data_modules.config import DataModulesConfig

    cfg = DataModulesConfig.from_project_root(project_root)
    vector_info = _inspect_vector_db(project_root)

    embed_ready = bool(str(cfg.embed_api_key or "").strip())
    rerank_ready = bool(str(cfg.rerank_api_key or "").strip())
    vector_ready = bool(vector_info["exists"] and vector_info["size_bytes"] > 0)

    if vector_ready and embed_ready and rerank_ready:
        rag_mode = "full"
    elif vector_ready and embed_ready:
        rag_mode = "embed_only"
    else:
        rag_mode = "bm25_only"

    return {
        "embed": {
            "base_url": cfg.embed_base_url,
            "model": cfg.embed_model,
            "api_key_present": embed_ready,
        },
        "rerank": {
            "base_url": cfg.rerank_base_url,
            "model": cfg.rerank_model,
            "api_key_present": rerank_ready,
        },
        "vector_db": vector_info,
        "rag_mode": rag_mode,
    }


def _projection_status_for_commit(project_root: Path, chapter: int, commit_payload: dict) -> tuple[dict, str, dict]:
    try:
        from data_modules.projection_log import latest_projection_run, projection_status_from_run

        latest_run = latest_projection_run(project_root, chapter=chapter)
    except Exception:
        latest_run = None

    if isinstance(latest_run, dict):
        projection_status = projection_status_from_run(latest_run)
        return (
            projection_status if isinstance(projection_status, dict) else {},
            "projection_log",
            {
                "run_id": str(latest_run.get("run_id") or ""),
                "status": str(latest_run.get("status") or ""),
                "created_at": str(latest_run.get("created_at") or ""),
                "commit_hash": str(latest_run.get("commit_hash") or ""),
            },
        )

    return commit_payload.get("projection_status") or {}, "commit", {}


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(project_root: str | Path | None = None) -> FastAPI:
    global _project_root

    if project_root:
        _project_root = Path(project_root).resolve()

    _ensure_scripts_dir_on_path()

    @asynccontextmanager
    async def _lifespan(_: FastAPI):
        webnovel = _webnovel_dir()
        story_system = _story_system_dir()
        if webnovel.is_dir() or story_system.is_dir():
            _watcher.start(
                watch_webnovel_dir=webnovel if webnovel.is_dir() else None,
                watch_story_system_dir=story_system if story_system.is_dir() else None,
                loop=asyncio.get_running_loop(),
            )
        try:
            yield
        finally:
            _watcher.stop()

    app = FastAPI(title="Webnovel Dashboard", version="0.1.0", lifespan=_lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=LOCAL_CORS_ORIGINS,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    # ===========================================================
    # API：Project metadata
    # ===========================================================

    @app.get("/api/project/info")
    def project_info():
        """Return all state.json content, read-only."""
        return _load_state_payload(required=True)

    @app.get("/api/story-runtime/health")
    def story_runtime_health():
        return _build_story_runtime_health_report(_get_project_root())

    # ===========================================================
    # API：Entity database (read-only index.db queries)
    # ===========================================================

    def _get_db() -> sqlite3.Connection:
        db_path = _webnovel_dir() / "index.db"
        if not db_path.is_file():
            raise HTTPException(404, "index.db not found")
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _fetchall_safe(conn: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
        """Run a read-only query; return an empty list if the table is absent."""
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc).lower() or "no such column" in str(exc).lower():
                return []
            raise HTTPException(status_code=500, detail=f"Database query failed: {exc}") from exc

    @app.get("/api/entities")
    def list_entities(
        entity_type: Optional[str] = Query(None, alias="type"),
        include_archived: bool = False,
    ):
        """List entities, optionally filtering by type."""
        with closing(_get_db()) as conn:
            q = "SELECT * FROM entities"
            params: list = []
            clauses: list[str] = []
            if entity_type:
                clauses.append("type = ?")
                params.append(entity_type)
            if not include_archived:
                clauses.append("is_archived = 0")
            if clauses:
                q += " WHERE " + " AND ".join(clauses)
            q += " ORDER BY last_appearance DESC"
            rows = conn.execute(q, params).fetchall()
            return [dict(r) for r in rows]

    @app.get("/api/entities/{entity_id}")
    def get_entity(entity_id: str):
        with closing(_get_db()) as conn:
            row = conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Entity not found")
            return dict(row)

    @app.get("/api/relationships")
    def list_relationships(entity: Optional[str] = None, limit: int = 200):
        with closing(_get_db()) as conn:
            if entity:
                rows = conn.execute(
                    "SELECT * FROM relationships WHERE from_entity = ? OR to_entity = ? ORDER BY chapter DESC LIMIT ?",
                    (entity, entity, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM relationships ORDER BY chapter DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    @app.get("/api/relationship-events")
    def list_relationship_events(
        entity: Optional[str] = None,
        from_chapter: Optional[int] = None,
        to_chapter: Optional[int] = None,
        limit: int = 200,
    ):
        with closing(_get_db()) as conn:
            q = "SELECT * FROM relationship_events"
            params: list = []
            clauses: list[str] = []
            if entity:
                clauses.append("(from_entity = ? OR to_entity = ?)")
                params.extend([entity, entity])
            if from_chapter is not None:
                clauses.append("chapter >= ?")
                params.append(from_chapter)
            if to_chapter is not None:
                clauses.append("chapter <= ?")
                params.append(to_chapter)
            if clauses:
                q += " WHERE " + " AND ".join(clauses)
            q += " ORDER BY chapter DESC, id DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(q, params).fetchall()
            return [dict(r) for r in rows]

    @app.get("/api/chapters")
    def list_chapters():
        with closing(_get_db()) as conn:
            rows = conn.execute("SELECT * FROM chapters ORDER BY chapter ASC").fetchall()
            normalized = []
            for row in rows:
                item = dict(row)
                item["characters"] = _parse_json_value(item.get("characters"), [])
                normalized.append(item)
            return normalized

    @app.get("/api/scenes")
    def list_scenes(chapter: Optional[int] = None, limit: int = 500):
        with closing(_get_db()) as conn:
            if chapter is not None:
                rows = conn.execute(
                    "SELECT * FROM scenes WHERE chapter = ? ORDER BY scene_index ASC", (chapter,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM scenes ORDER BY chapter ASC, scene_index ASC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    @app.get("/api/reading-power")
    def list_reading_power(limit: int = 50):
        with closing(_get_db()) as conn:
            rows = conn.execute(
                "SELECT * FROM chapter_reading_power ORDER BY chapter DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    @app.get("/api/review-metrics")
    def list_review_metrics(limit: int = 20):
        with closing(_get_db()) as conn:
            rows = conn.execute(
                "SELECT * FROM review_metrics ORDER BY end_chapter DESC LIMIT ?", (limit,)
            ).fetchall()
            normalized = []
            for row in rows:
                item = dict(row)
                item["dimension_scores"] = _parse_json_value(item.get("dimension_scores"), {})
                item["severity_counts"] = _parse_json_value(item.get("severity_counts"), {})
                item["critical_issues"] = _parse_json_value(item.get("critical_issues"), [])
                normalized.append(item)
            return normalized

    @app.get("/api/stats/chapter-trend")
    def chapter_trend(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
        state = _load_state_payload()
        strand_map = _build_strand_map(state)

        with closing(_get_db()) as conn:
            total_rows = _fetchall_safe(conn, "SELECT COUNT(*) AS count FROM chapters")
            latest_rows = _fetchall_safe(conn, "SELECT MAX(chapter) AS chapter FROM chapters")
            rows = _fetchall_safe(
                conn,
                """
                WITH selected_chapters AS (
                    SELECT chapter, title, location, word_count, characters, summary
                    FROM chapters
                    ORDER BY chapter DESC
                    LIMIT ? OFFSET ?
                )
                SELECT
                    c.chapter,
                    c.title,
                    c.location,
                    c.word_count,
                    c.characters,
                    c.summary,
                    rp.hook_type,
                    rp.hook_strength,
                    rp.is_transition,
                    rp.override_count,
                    rp.debt_balance,
                    rm.overall_score AS review_score,
                    rm.severity_counts
                FROM selected_chapters c
                LEFT JOIN chapter_reading_power rp ON rp.chapter = c.chapter
                LEFT JOIN review_metrics rm ON rm.end_chapter = c.chapter
                ORDER BY c.chapter ASC
                """,
                (limit, offset),
            )

        hook_strength_value = {"weak": 1, "medium": 3, "strong": 5}
        items = []
        for row in rows:
            chapter = int(row.get("chapter") or 0)
            hook_strength = str(row.get("hook_strength") or "").strip().lower()
            items.append(
                {
                    "chapter": chapter,
                    "title": row.get("title") or "",
                    "location": row.get("location") or "",
                    "word_count": int(row.get("word_count") or 0),
                    "characters": _parse_json_value(row.get("characters"), []),
                    "summary": row.get("summary") or "",
                    "review_score": row.get("review_score"),
                    "review_severity_counts": _parse_json_value(row.get("severity_counts"), {}),
                    "hook_type": row.get("hook_type") or "",
                    "hook_strength": hook_strength,
                    "hook_strength_value": hook_strength_value.get(hook_strength, 0),
                    "is_transition": bool(row.get("is_transition")),
                    "override_count": int(row.get("override_count") or 0),
                    "debt_balance": float(row.get("debt_balance") or 0.0),
                    "strand": strand_map.get(chapter, ""),
                    "volume": _resolve_volume_for_chapter(state, chapter),
                }
            )

        return {
            "items": items,
            "total": int(total_rows[0]["count"] or 0) if total_rows else 0,
            "latest_chapter": int(latest_rows[0]["chapter"] or 0) if latest_rows else 0,
            "limit": limit,
            "offset": offset,
        }

    @app.get("/api/commits")
    def list_commits(limit: int = Query(20, ge=1, le=200)):
        commits_dir = _story_system_dir() / "commits"
        if not commits_dir.is_dir():
            return {"items": [], "total": 0, "limit": limit}

        items = []
        for path in commits_dir.glob("chapter_*.commit.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            meta = payload.get("meta") if isinstance(payload, dict) else {}
            provenance = payload.get("provenance") if isinstance(payload, dict) else {}
            chapter = int((meta or {}).get("chapter") or _extract_story_chapter(path))
            projection_status, projection_source, projection_run = _projection_status_for_commit(
                _get_project_root(),
                chapter,
                payload if isinstance(payload, dict) else {},
            )
            items.append(
                {
                    "chapter": chapter,
                    "status": str((meta or {}).get("status") or "missing"),
                    "projection_status": projection_status,
                    "projection_source": projection_source,
                    "projection_run": projection_run,
                    "write_fact_role": str((provenance or {}).get("write_fact_role") or ""),
                    "contract_refs": payload.get("contract_refs") or {},
                    "path": path.name,
                    "updated_at": datetime.fromtimestamp(
                        path.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
            )

        items.sort(key=lambda item: item["chapter"], reverse=True)
        return {"items": items[:limit], "total": len(items), "limit": limit}

    @app.get("/api/contracts/summary")
    def contracts_summary():
        from data_modules.story_contracts import StoryContractPaths, read_json_if_exists

        project_root = _get_project_root()
        state = _load_state_payload()
        runtime = _build_story_runtime_health_report(project_root)
        chapter = int(runtime.get("chapter") or ((state.get("progress") or {}).get("current_chapter") or 0))
        current_volume = _resolve_volume_for_chapter(state, chapter) or int(
            ((state.get("progress") or {}).get("current_volume") or 1)
        )

        paths = StoryContractPaths.from_project_root(project_root)
        master_payload = read_json_if_exists(paths.master_json) or {}

        return {
            "chapter": chapter,
            "current_volume": current_volume,
            "master": {
                "exists": bool(master_payload),
                "primary_genre": str(((master_payload.get("route") or {}).get("primary_genre") or "")),
                "core_tone": str(
                    ((master_payload.get("master_constraints") or {}).get("core_tone") or "")
                ),
            },
            "counts": {
                "volumes": len(list(paths.volumes_dir.glob("volume_*.json"))) if paths.volumes_dir.is_dir() else 0,
                "chapters": len(list(paths.chapters_dir.glob("chapter_*.json"))) if paths.chapters_dir.is_dir() else 0,
                "reviews": len(list(paths.reviews_dir.glob("chapter_*.review.json"))) if paths.reviews_dir.is_dir() else 0,
                "commits": len(list(paths.commits_dir.glob("chapter_*.commit.json"))) if paths.commits_dir.is_dir() else 0,
            },
            "current_contracts": {
                "volume": paths.volume_json(current_volume).is_file(),
                "chapter": paths.chapter_json(chapter).is_file() if chapter > 0 else False,
                "review": paths.review_json(chapter).is_file() if chapter > 0 else False,
                "commit": paths.commit_json(chapter).is_file() if chapter > 0 else False,
            },
        }

    @app.get("/api/env-status")
    def env_status():
        return _build_env_status(_get_project_root())

    @app.get("/api/env-status/probe")
    def env_status_probe():
        status = _build_env_status(_get_project_root())
        runtime = _build_story_runtime_health_report(_get_project_root())
        vector_db = status["vector_db"]
        checks = [
            {
                "name": "embed_api_key",
                "ok": bool(status["embed"]["api_key_present"]),
                "detail": "Configured" if status["embed"]["api_key_present"] else "Not configured",
            },
            {
                "name": "rerank_api_key",
                "ok": bool(status["rerank"]["api_key_present"]),
                "detail": "Configured" if status["rerank"]["api_key_present"] else "Not configured",
            },
            {
                "name": "vector_db",
                "ok": bool(vector_db["exists"] and not vector_db["error"]),
                "detail": vector_db["error"]
                or f"{vector_db['record_count']} records · {vector_db['size_bytes']} bytes",
            },
            {
                "name": "story_runtime",
                "ok": bool(runtime.get("mainline_ready")),
                "detail": (
                    f"chapter={runtime.get('chapter')} "
                    f"status={runtime.get('latest_commit_status')} "
                    f"fallback={','.join(runtime.get('fallback_sources') or []) or 'none'}"
                ),
            },
        ]
        return {
            "ok": all(bool(item["ok"]) for item in checks),
            "rag_mode": status["rag_mode"],
            "checks": checks,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/api/state-changes")
    def list_state_changes(entity: Optional[str] = None, limit: int = 100):
        with closing(_get_db()) as conn:
            if entity:
                rows = conn.execute(
                    "SELECT * FROM state_changes WHERE entity_id = ? ORDER BY chapter DESC LIMIT ?",
                    (entity, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM state_changes ORDER BY chapter DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    @app.get("/api/aliases")
    def list_aliases(entity: Optional[str] = None):
        with closing(_get_db()) as conn:
            if entity:
                rows = conn.execute(
                    "SELECT * FROM aliases WHERE entity_id = ?", (entity,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM aliases").fetchall()
            return [dict(r) for r in rows]

    # ===========================================================
    # API：Additional tables（v5.3+ / v5.4+）
    # ===========================================================

    @app.get("/api/overrides")
    def list_overrides(status: Optional[str] = None, limit: int = 100):
        with closing(_get_db()) as conn:
            if status:
                return _fetchall_safe(
                    conn,
                    "SELECT * FROM override_contracts WHERE status = ? ORDER BY chapter DESC LIMIT ?",
                    (status, limit),
                )
            return _fetchall_safe(
                conn,
                "SELECT * FROM override_contracts ORDER BY chapter DESC LIMIT ?",
                (limit,),
            )

    @app.get("/api/debts")
    def list_debts(status: Optional[str] = None, limit: int = 100):
        with closing(_get_db()) as conn:
            if status:
                return _fetchall_safe(
                    conn,
                    "SELECT * FROM chase_debt WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
                    (status, limit),
                )
            return _fetchall_safe(
                conn,
                "SELECT * FROM chase_debt ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            )

    @app.get("/api/debt-events")
    def list_debt_events(debt_id: Optional[int] = None, limit: int = 200):
        with closing(_get_db()) as conn:
            if debt_id is not None:
                return _fetchall_safe(
                    conn,
                    "SELECT * FROM debt_events WHERE debt_id = ? ORDER BY chapter DESC, id DESC LIMIT ?",
                    (debt_id, limit),
                )
            return _fetchall_safe(
                conn,
                "SELECT * FROM debt_events ORDER BY chapter DESC, id DESC LIMIT ?",
                (limit,),
            )

    @app.get("/api/invalid-facts")
    def list_invalid_facts(status: Optional[str] = None, limit: int = 100):
        with closing(_get_db()) as conn:
            if status:
                return _fetchall_safe(
                    conn,
                    "SELECT * FROM invalid_facts WHERE status = ? ORDER BY marked_at DESC LIMIT ?",
                    (status, limit),
                )
            return _fetchall_safe(
                conn,
                "SELECT * FROM invalid_facts ORDER BY marked_at DESC LIMIT ?",
                (limit,),
            )

    @app.get("/api/rag-queries")
    def list_rag_queries(query_type: Optional[str] = None, limit: int = 100):
        with closing(_get_db()) as conn:
            if query_type:
                return _fetchall_safe(
                    conn,
                    "SELECT * FROM rag_query_log WHERE query_type = ? ORDER BY created_at DESC LIMIT ?",
                    (query_type, limit),
                )
            return _fetchall_safe(
                conn,
                "SELECT * FROM rag_query_log ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )

    @app.get("/api/tool-stats")
    def list_tool_stats(tool_name: Optional[str] = None, limit: int = 200):
        with closing(_get_db()) as conn:
            if tool_name:
                return _fetchall_safe(
                    conn,
                    "SELECT * FROM tool_call_stats WHERE tool_name = ? ORDER BY created_at DESC LIMIT ?",
                    (tool_name, limit),
                )
            return _fetchall_safe(
                conn,
                "SELECT * FROM tool_call_stats ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )

    @app.get("/api/checklist-scores")
    def list_checklist_scores(limit: int = 100):
        with closing(_get_db()) as conn:
            return _fetchall_safe(
                conn,
                "SELECT * FROM writing_checklist_scores ORDER BY chapter DESC LIMIT ?",
                (limit,),
            )

    @app.get("/api/story-events")
    def list_story_events(chapter: Optional[int] = None, limit: int = 200):
        with closing(_get_db()) as conn:
            if chapter is not None:
                rows = _fetchall_safe(
                    conn,
                    """
                    SELECT event_id, chapter, event_type, subject, payload_json, created_at
                    FROM story_events
                    WHERE chapter = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (chapter, limit),
                )
            else:
                rows = _fetchall_safe(
                    conn,
                    """
                    SELECT event_id, chapter, event_type, subject, payload_json, created_at
                    FROM story_events
                    ORDER BY chapter DESC, id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

        normalized = []
        for row in rows:
            payload = {}
            try:
                payload = json.loads(row.get("payload_json") or "{}")
            except json.JSONDecodeError:
                payload = {}
            normalized.append({**row, "payload": payload})
        return normalized

    @app.get("/api/story-events/health")
    def story_event_health():
        with closing(_get_db()) as conn:
            event_rows = _fetchall_safe(conn, "SELECT COUNT(*) AS count FROM story_events")
            proposal_rows = _fetchall_safe(
                conn,
                """
                SELECT COUNT(*) AS count
                FROM override_contracts
                WHERE record_type = 'amend_proposal' AND status = 'pending'
                """,
            )

        events_dir = _story_system_dir() / "events"
        file_count = len(list(events_dir.glob("chapter_*.events.json"))) if events_dir.is_dir() else 0
        return {
            "story_events": event_rows[0]["count"] if event_rows else 0,
            "pending_amend_proposals": proposal_rows[0]["count"] if proposal_rows else 0,
            "event_files": file_count,
        }

    # ===========================================================
    # API: read-only browsing of current and legacy project directories
    # ===========================================================

    @app.get("/api/files/tree")
    def file_tree():
        """List document trees without hiding files in legacy directories."""
        root = _get_project_root()
        result = {}
        for folder in _document_folders(root):
            folder_name = folder.name
            if not folder.is_dir():
                result[folder_name] = []
                continue
            result[folder_name] = _walk_tree(folder, root)
        return result

    @app.get("/api/files/read")
    def file_read(path: str):
        """Read only chapter, outline, setting, and review documents."""
        root = _get_project_root()
        resolved = safe_resolve(root, path)

        # Retain the directory allowlist after the traversal guard.
        allowed_parents = _document_folders(root)
        if not any(_is_child(resolved, p) for p in allowed_parents):
            raise HTTPException(403, "Only chapters, outlines, settings, and reviews (including legacy directories) can be read")

        if not resolved.is_file():
            raise HTTPException(404, "File not found")

        max_bytes = 2 * 1024 * 1024
        if resolved.stat().st_size > max_bytes:
            raise HTTPException(413, "File is too large to preview")

        # Read text files directly; otherwise return a placeholder.
        try:
            content = resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = "[Binary file cannot be previewed]"

        return {"path": path, "content": content}

    # ===========================================================
    # SSE：Live change notifications
    # ===========================================================

    @app.get("/api/events")
    async def sse():
        """Server-Sent Events endpoint for .webnovel/.story-system file changes."""
        q = _watcher.subscribe()

        async def _gen():
            try:
                while True:
                    msg = await q.get()
                    yield f"data: {msg}\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                _watcher.unsubscribe(q)

        return StreamingResponse(_gen(), media_type="text/event-stream")

    # ===========================================================
    # Frontend static-file hosting
    # ===========================================================

    if STATIC_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

        @app.get("/{full_path:path}")
        def serve_spa(full_path: str):
            """SPA fallback: return index.html for paths outside /api."""
            if full_path.startswith("api/"):
                raise HTTPException(404, "API route not found")
            index = STATIC_DIR / "index.html"
            if index.is_file():
                return FileResponse(str(index))
            raise HTTPException(404, "Frontend has not been built")
    else:
        @app.get("/")
        def no_frontend():
            return HTMLResponse(
                "<h2>Webnovel Dashboard API is running</h2>"
                "<p>Frontend has not been built. Run <code>npm run build</code> in <code>dashboard/frontend</code> first.</p>"
                '<p>API documentation: <a href="/docs">/docs</a></p>'
            )

    return app


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _document_folders(root: Path) -> list[Path]:
    """Return the canonical document directories allowed for browsing."""
    return [root / name for name in ("chapters", "outlines", "settings", "reviews")]


def _walk_tree(folder: Path, root: Path) -> list[dict]:
    items = []
    for child in sorted(folder.iterdir()):
        rel = str(child.relative_to(root)).replace("\\", "/")
        if child.is_dir():
            items.append({"name": child.name, "type": "dir", "path": rel, "children": _walk_tree(child, root)})
        else:
            items.append({"name": child.name, "type": "file", "path": rel, "size": child.stat().st_size})
    return items


def _is_child(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False
