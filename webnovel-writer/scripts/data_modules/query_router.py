#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Query router for RAG requests."""
from __future__ import annotations

import re
from typing import Any, Dict, List


class QueryRouter:
    def __init__(self):
        self.intent_patterns = {
            "relationship": [r"relationship", r"graph", r"timeline", r"who with whom", r"hostile", r"ally"],
            "entity": [r"person", r"character", r"who", r"identity", r"alias"],
            "scene": [r"location", r"scene", r"where", r"location"],
            "setting": [r"setting", r"rule", r"system", r"worldbuilding"],
            "plot": [r"plot", r"happened", r"event", r"course of events"],
        }
        self.patterns = {
            "entity": list(self.intent_patterns["entity"]),
            "scene": list(self.intent_patterns["scene"]),
            "setting": list(self.intent_patterns["setting"]),
            "plot": list(self.intent_patterns["plot"]),
        }

    def _extract_entities(self, query: str) -> List[str]:
        # Quoted names and capitalized Unicode names are conservative entity hints.
        candidates = re.findall(r'["\']([^"\']+)["\']', query)
        words = re.findall(r"\b[^\W\d_][\w'-]*\b", query, re.UNICODE)
        phrase = []
        for word in words + [""]:
            if word and word[0].isupper():
                phrase.append(word)
            else:
                if phrase:
                    candidates.append(" ".join(phrase))
                phrase = []
        stopwords = {
            "relationship",
            "graph",
            "timeline",
            "plot",
            "happened",
            "event",
            "character",
            "person",
            "setting",
            "worldbuilding",
            "location",
            "scene",
        }
        entities: List[str] = []
        for c in candidates:
            if c in stopwords:
                continue
            if c not in entities:
                entities.append(c)
        return entities[:4]

    def _extract_time_scope(self, query: str) -> Dict[str, Any]:
        m_range = re.search(r"\bchapters?\s+(\d+)\s*(?:[-~]|to)\s*(\d+)\b", query, re.IGNORECASE)
        if m_range:
            start = int(m_range.group(1))
            end = int(m_range.group(2))
            if start > end:
                start, end = end, start
            return {"from_chapter": start, "to_chapter": end}

        m_single = re.search(r"\bchapter\s+(\d+)\b", query, re.IGNORECASE)
        if m_single:
            chapter = int(m_single.group(1))
            return {"from_chapter": chapter, "to_chapter": chapter}

        return {}

    def route_intent(self, query: str) -> Dict[str, Any]:
        query = str(query or "")
        intent = "plot"
        for intent_name, patterns in self.intent_patterns.items():
            if any(re.search(r"\b(?:" + pat + r")\b", query, re.IGNORECASE) for pat in patterns):
                intent = intent_name
                break

        time_scope = self._extract_time_scope(query)
        entities = self._extract_entities(query)
        needs_graph = intent == "relationship" or "relationship" in query or "graph" in query
        return {
            "intent": intent,
            "entities": entities,
            "time_scope": time_scope,
            "needs_graph": needs_graph,
            "raw_query": query,
        }

    def plan_subqueries(self, intent_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        intent = str((intent_payload or {}).get("intent") or "plot")
        entities = list((intent_payload or {}).get("entities") or [])
        time_scope = dict((intent_payload or {}).get("time_scope") or {})
        needs_graph = bool((intent_payload or {}).get("needs_graph"))

        steps: List[Dict[str, Any]] = []
        if intent == "relationship":
            steps.append(
                {
                    "name": "relationship_graph",
                    "strategy": "graph_lookup",
                    "entities": entities,
                    "time_scope": time_scope,
                }
            )
            steps.append(
                {
                    "name": "relationship_evidence",
                    "strategy": "graph_hybrid",
                    "entities": entities,
                    "time_scope": time_scope,
                }
            )
            return steps

        if needs_graph and entities:
            steps.append(
                {
                    "name": "graph_enhanced_retrieval",
                    "strategy": "graph_hybrid",
                    "entities": entities,
                    "time_scope": time_scope,
                }
            )
            return steps

        strategy_map = {
            "entity": "hybrid",
            "scene": "bm25",
            "setting": "bm25",
            "plot": "hybrid",
        }
        steps.append(
            {
                "name": "default_retrieval",
                "strategy": strategy_map.get(intent, "hybrid"),
                "entities": entities,
                "time_scope": time_scope,
            }
        )
        return steps

    def route(self, query: str) -> str:
        return str(self.route_intent(query).get("intent") or "plot")

    def split(self, query: str) -> List[str]:
        parts = re.split(r"[,;]\s*|\s+and\s+", query)
        return [p.strip() for p in parts if p.strip()]
