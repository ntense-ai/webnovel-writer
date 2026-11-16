#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_chapter_context.py - extract chapter writing context

Features:
- chapter outline snippet
- previous chapter summaries (prefers .webnovel/summaries)
- compact state summary
- ContextManager contract sections (reader_signal / genre_profile / writing_guidance)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from chapter_outline_loader import load_chapter_outline, load_chapter_plot_structure

from runtime_compat import enable_windows_utf8_stdio

try:
    from chapter_paths import find_chapter_file
except ImportError:  # pragma: no cover
    from scripts.chapter_paths import find_chapter_file


def _ensure_scripts_path():
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


_RAG_TRIGGER_KEYWORDS = (
    "relationship",
    "grievance",
    "conflict",
    "hostile",
    "alliance",
    "mentor-student",
    "identity",
    "clue",
    "foreshadowing",
    "payoff",
    "location",
    "faction",
    "truth",
    "origin",
    "relationship", "relationships", "feud", "feuds", "conflict", "conflicts",
    "enemy", "enemies", "hostility", "alliance", "alliances", "mentor", "mentors",
    "identity", "identities", "clue", "clues", "foreshadowing", "payoff", "payoffs",
    "location", "locations", "faction", "factions", "truth", "origin", "origins",
)


def _contains_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    """Match English whole words case-insensitively, retaining CJK substrings."""
    return any(
        bool(re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text, re.IGNORECASE))
        if keyword.isascii() else keyword in text
        for keyword in keywords
    )


def find_project_root(start_path: Path | None = None) -> Path:
    'Resolve the actual book project root containing .webnovel/state.json.'
    from project_locator import resolve_project_root

    if start_path is None:
        return resolve_project_root()
    return resolve_project_root(str(start_path))


def extract_chapter_outline(project_root: Path, chapter_num: int) -> str:
    """Extract chapter outline segment from volume outline file."""
    return load_chapter_outline(project_root, chapter_num, max_chars=1500)


def _load_summary_file(project_root: Path, chapter_num: int) -> str:
    """Load summary section from `.webnovel/summaries/chNNNN.md`."""
    summary_path = project_root / ".webnovel" / "summaries" / f"ch{chapter_num:04d}.md"
    if not summary_path.exists():
        return ""

    text = summary_path.read_text(encoding="utf-8")
    summary_match = re.search(r"##[ \t]*(?:Plot summary|Plot summary|Chapter summary|Summary)[ \t]*\r?\n(.+?)(?=\r?\n##|$)", text, re.DOTALL | re.IGNORECASE)
    if summary_match:
        return summary_match.group(1).strip()
    return ""


def extract_chapter_summary(project_root: Path, chapter_num: int) -> str:
    """Extract chapter summary, fallback to chapter body head."""
    summary = _load_summary_file(project_root, chapter_num)
    if summary:
        return summary

    chapter_file = find_chapter_file(project_root, chapter_num)
    if not chapter_file or not chapter_file.exists():
        return f"⚠️ Chapter {chapter_num} file not found"

    content = chapter_file.read_text(encoding="utf-8")

    summary_match = re.search(r"##[ \t]*(?:Chapter summary|Chapter summary|Summary)[ \t]*\r?\n(.+?)(?=\r?\n##|$)", content, re.DOTALL | re.IGNORECASE)
    if summary_match:
        return summary_match.group(1).strip()

    stats_match = re.search(r"##[ \t]*(?:Chapter statistics|Chapter statistics|Statistics)[ \t]*\r?\n(.+?)(?=\r?\n##|$)", content, re.DOTALL | re.IGNORECASE)
    if stats_match:
        return f"[No summary; statistics only]\n{stats_match.group(1).strip()}"

    lines = content.split("\n")
    text_lines = [line for line in lines if not line.startswith("#") and line.strip()]
    text = "\n".join(text_lines)[:500]
    return f"[Automatically excerpted first 500 characters]\n{text}..."


def extract_state_summary(project_root: Path) -> str:
    """Extract key fields from `.webnovel/state.json`."""
    state_file = project_root / ".webnovel" / "state.json"
    if not state_file.exists():
        return "⚠️ state.json not found"

    state = json.loads(state_file.read_text(encoding="utf-8"))
    summary_parts: List[str] = []

    if "progress" in state:
        progress = state["progress"]
        summary_parts.append(
            f"**Progress**: Chapter {progress.get('current_chapter', '?')} / {progress.get('total_words', '?')} words"
        )

    if "protagonist_state" in state:
        ps = state["protagonist_state"]
        power = ps.get("power", {})
        summary_parts.append(f"**Protagonist power**: {power.get('realm', '?')} Layer {power.get('layer', '?')}")
        summary_parts.append(f"**Current location**: {ps.get('location', '?')}")
        golden_finger = ps.get("golden_finger", {})
        summary_parts.append(
            f"**Special advantage**: {golden_finger.get('name', '?')} Lv.{golden_finger.get('level', '?')}"
        )

    if "strand_tracker" in state:
        tracker = state["strand_tracker"]
        history = tracker.get("history", [])[-5:]
        if history:
            items: List[str] = []
            for row in history:
                if not isinstance(row, dict):
                    continue
                chapter = row.get("chapter", "?")
                strand = row.get("strand") or row.get("dominant") or "unknown"
                items.append(f"Ch{chapter}:{strand}")
            if items:
                summary_parts.append(f"**Strands in the last 5 chapters**: {', '.join(items)}")

    plot_threads = state.get("plot_threads", {}) if isinstance(state.get("plot_threads"), dict) else {}
    foreshadowing = plot_threads.get("foreshadowing", [])
    if isinstance(foreshadowing, list) and foreshadowing:
        active = [row for row in foreshadowing if row.get("status") in {"active", "unresolved"}]
        urgent = [row for row in active if row.get("urgency", 0) > 50]
        if urgent:
            urgent_list = [
                f"{row.get('content', '?')[:30]}... (urgency:{row.get('urgency')})"
                for row in urgent[:3]
            ]
            summary_parts.append(f"**Urgent foreshadowing**: {'; '.join(urgent_list)}")

    return "\n".join(summary_parts)


def _normalize_outline_text(outline: str) -> str:
    text = str(outline or "")
    if not text or text.startswith("⚠️"):
        return ""
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_rag_query(outline: str, chapter_num: int, min_chars: int, max_chars: int) -> str:
    plain = _normalize_outline_text(outline)
    if not plain or len(plain) < min_chars:
        return ""

    if not _contains_keyword(plain, _RAG_TRIGGER_KEYWORDS):
        return ""

    if _contains_keyword(plain, ("relationship", "mentor-student", "hostile", "alliance", "relationship", "relationships",
                                 "mentor", "mentors", "enemy", "enemies", "hostility", "alliance", "alliances")):
        topic = "Character relationships and motivations"
    elif _contains_keyword(plain, ("location", "faction", "location", "locations", "faction", "factions")):
        topic = "Locations, factions, and scene constraints"
    elif _contains_keyword(plain, ("foreshadowing", "clue", "payoff", "foreshadowing", "clue", "clues", "payoff", "payoffs")):
        topic = "Foreshadowing and clues"
    else:
        topic = "Key plot evidence"

    clean_max = max(40, int(max_chars))
    return f"Chapter {chapter_num} {topic}: {plain[:clean_max]}"


def _search_with_rag(
    project_root: Path,
    chapter_num: int,
    query: str,
    top_k: int,
) -> Dict[str, Any]:
    _ensure_scripts_path()
    from data_modules.config import DataModulesConfig
    from data_modules.rag_adapter import RAGAdapter

    config = DataModulesConfig.from_project_root(project_root)
    adapter = RAGAdapter(config)
    intent_payload = adapter.query_router.route_intent(query)
    center_entities = list(intent_payload.get("entities") or [])

    results = []
    mode = "auto"
    fallback_reason = ""
    has_embed_key = bool(str(getattr(config, "embed_api_key", "") or "").strip())
    if has_embed_key:
        try:
            results = asyncio.run(
                adapter.search(
                    query=query,
                    top_k=top_k,
                    strategy="auto",
                    chapter=chapter_num,
                    center_entities=center_entities,
                )
            )
        except Exception as exc:
            fallback_reason = f"auto_failed:{exc.__class__.__name__}"
            mode = "bm25_fallback"
            results = adapter.bm25_search(query=query, top_k=top_k, chapter=chapter_num)
    else:
        mode = "bm25_fallback"
        fallback_reason = "missing_embed_api_key"
        results = adapter.bm25_search(query=query, top_k=top_k, chapter=chapter_num)

    hits: List[Dict[str, Any]] = []
    for row in results:
        content = re.sub(r"\s+", " ", str(getattr(row, "content", "") or "")).strip()
        hits.append(
            {
                "chunk_id": str(getattr(row, "chunk_id", "") or ""),
                "chapter": int(getattr(row, "chapter", 0) or 0),
                "scene_index": int(getattr(row, "scene_index", 0) or 0),
                "score": round(float(getattr(row, "score", 0.0) or 0.0), 6),
                "source": str(getattr(row, "source", "") or mode),
                "source_file": str(getattr(row, "source_file", "") or ""),
                "content": content[:180],
            }
        )

    return {
        "invoked": True,
        "query": query,
        "mode": mode,
        "reason": fallback_reason or ("ok" if hits else "no_hit"),
        "intent": intent_payload.get("intent"),
        "needs_graph": bool(intent_payload.get("needs_graph")),
        "center_entities": center_entities,
        "hits": hits,
    }


def _load_rag_assist(project_root: Path, chapter_num: int, outline: str) -> Dict[str, Any]:
    _ensure_scripts_path()
    from data_modules.config import DataModulesConfig

    config = DataModulesConfig.from_project_root(project_root)
    enabled = bool(getattr(config, "context_rag_assist_enabled", True))
    top_k = max(1, int(getattr(config, "context_rag_assist_top_k", 4)))
    min_chars = max(20, int(getattr(config, "context_rag_assist_min_outline_chars", 40)))
    max_chars = max(40, int(getattr(config, "context_rag_assist_max_query_chars", 120)))
    base_payload = {"enabled": enabled, "invoked": False, "reason": "", "query": "", "hits": []}

    if not enabled:
        base_payload["reason"] = "disabled_by_config"
        return base_payload

    query = _build_rag_query(outline, chapter_num=chapter_num, min_chars=min_chars, max_chars=max_chars)
    if not query:
        base_payload["reason"] = "outline_not_actionable"
        return base_payload

    vector_db = config.vector_db
    if not vector_db.exists() or vector_db.stat().st_size <= 0:
        base_payload["reason"] = "vector_db_missing_or_empty"
        return base_payload

    try:
        rag_payload = _search_with_rag(project_root=project_root, chapter_num=chapter_num, query=query, top_k=top_k)
        rag_payload["enabled"] = True
        return rag_payload
    except Exception as exc:
        base_payload["reason"] = f"rag_error:{exc.__class__.__name__}"
        return base_payload


def _load_contract_context(project_root: Path, chapter_num: int) -> Dict[str, Any]:
    """Build context via ContextManager and return selected sections."""
    _ensure_scripts_path()
    from data_modules.config import DataModulesConfig
    from data_modules.context_manager import ContextManager

    config = DataModulesConfig.from_project_root(project_root)
    manager = ContextManager(config)
    payload = manager.build_context(chapter=chapter_num, template="plot")

    return {
        "context_contract_version": (payload.get("meta") or {}).get("context_contract_version"),
        "context_weight_stage": (payload.get("meta") or {}).get("context_weight_stage"),
        "story_contract": payload.get("story_contract", {}),
        "runtime_status": payload.get("runtime_status", {}),
        "latest_commit": payload.get("latest_commit", {}),
        "prewrite_validation": payload.get("prewrite_validation", {}),
        "reader_signal": payload.get("reader_signal", {}),
        "genre_profile": payload.get("genre_profile", {}),
        "writing_guidance": payload.get("writing_guidance", {}),
        "plot_structure": payload.get("plot_structure", {}),
        "long_term_memory": payload.get("long_term_memory", {}),
        "scene": payload.get("scene", {}),
        "core": payload.get("core", {}),
    }


def build_chapter_context_payload(project_root: Path, chapter_num: int) -> Dict[str, Any]:
    """Assemble full chapter context payload for text/json output."""
    outline = extract_chapter_outline(project_root, chapter_num)

    prev_summaries = []
    for prev_ch in range(max(1, chapter_num - 2), chapter_num):
        summary = extract_chapter_summary(project_root, prev_ch)
        prev_summaries.append(f"### Chapter {prev_ch} summary\n{summary}")

    state_summary = extract_state_summary(project_root)
    contract_context = _load_contract_context(project_root, chapter_num)
    plot_structure = contract_context.get("plot_structure") or load_chapter_plot_structure(project_root, chapter_num)
    rag_assist = _load_rag_assist(project_root, chapter_num, outline)

    return {
        "chapter": chapter_num,
        "outline": outline,
        "previous_summaries": prev_summaries,
        "state_summary": state_summary,
        "context_contract_version": contract_context.get("context_contract_version"),
        "context_weight_stage": contract_context.get("context_weight_stage"),
        "story_contract": contract_context.get("story_contract", {}),
        "runtime_status": contract_context.get("runtime_status", {}),
        "latest_commit": contract_context.get("latest_commit", {}),
        "prewrite_validation": contract_context.get("prewrite_validation", {}),
        "reader_signal": contract_context.get("reader_signal", {}),
        "genre_profile": contract_context.get("genre_profile", {}),
        "writing_guidance": contract_context.get("writing_guidance", {}),
        "plot_structure": plot_structure,
        "long_term_memory": contract_context.get("long_term_memory", {}),
        "scene": contract_context.get("scene", {}),
        "core": contract_context.get("core", {}),
        "rag_assist": rag_assist,
    }


def _render_text(payload: Dict[str, Any]) -> str:
    'Serialize as JSON; context-agent handles text rendering.'
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Extract compact context for chapter drafting")
    parser.add_argument("--chapter", type=int, required=True, help="Target chapter number")
    parser.add_argument("--project-root", type=str, help="Project root")
    parser.add_argument("--format", choices=["json"], default="json",
                        help="Output format (always JSON; context-agent renders text)")

    args = parser.parse_args()

    try:
        project_root = (
            find_project_root(Path(args.project_root))
            if args.project_root
            else find_project_root()
        )
        payload = build_chapter_context_payload(project_root, args.chapter)
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    except Exception as exc:
        print(f"❌ Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if sys.platform == "win32":
        enable_windows_utf8_stdio()
    main()

