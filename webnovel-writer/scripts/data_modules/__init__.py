#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data pipeline package with lazy public exports.

Lazy imports avoid runpy warnings when executing a submodule with python -m.
Direct imports such as ``from data_modules.index_manager import IndexManager``
are preferred. Package-level exports remain available for API consumers.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


__all__ = [
    # Config
    "DataModulesConfig",
    "get_config",
    "set_project_root",
    # API Client
    "ModalAPIClient",
    "get_client",
    # Entity Linker
    "EntityLinker",
    "DisambiguationResult",
    # State Manager
    "StateManager",
    "EntityState",
    "Relationship",
    "StateChange",
    # Index Manager
    "IndexManager",
    "ChapterMeta",
    "SceneMeta",
    "ReviewMetrics",
    "RelationshipEventMeta",
    # RAG Adapter
    "RAGAdapter",
    "SearchResult",
    "ContextManager",
    "ContextRanker",
    "QueryRouter",
    # Style Sampler
    "StyleSampler",
    "StyleSample",
    "SceneType",
    # Memory
    "ScratchpadManager",
    "MemoryWriter",
    "MemoryOrchestrator",
    # Memory Contract
    "MemoryContract",
    "MemoryContractAdapter",
]


_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # Config
    "DataModulesConfig": (".config", "DataModulesConfig"),
    "get_config": (".config", "get_config"),
    "set_project_root": (".config", "set_project_root"),
    # API Client
    "ModalAPIClient": (".api_client", "ModalAPIClient"),
    "get_client": (".api_client", "get_client"),
    # Entity Linker
    "EntityLinker": (".entity_linker", "EntityLinker"),
    "DisambiguationResult": (".entity_linker", "DisambiguationResult"),
    # State Manager
    "StateManager": (".state_manager", "StateManager"),
    "EntityState": (".state_manager", "EntityState"),
    "Relationship": (".state_manager", "Relationship"),
    "StateChange": (".state_manager", "StateChange"),
    # Index Manager
    "IndexManager": (".index_manager", "IndexManager"),
    "ChapterMeta": (".index_manager", "ChapterMeta"),
    "SceneMeta": (".index_manager", "SceneMeta"),
    "ReviewMetrics": (".index_manager", "ReviewMetrics"),
    "RelationshipEventMeta": (".index_manager", "RelationshipEventMeta"),
    # RAG Adapter
    "RAGAdapter": (".rag_adapter", "RAGAdapter"),
    "SearchResult": (".rag_adapter", "SearchResult"),
    "ContextManager": (".context_manager", "ContextManager"),
    "ContextRanker": (".context_ranker", "ContextRanker"),
    "QueryRouter": (".query_router", "QueryRouter"),
    # Style Sampler
    "StyleSampler": (".style_sampler", "StyleSampler"),
    "StyleSample": (".style_sampler", "StyleSample"),
    "SceneType": (".style_sampler", "SceneType"),
    # Memory
    "ScratchpadManager": (".memory.store", "ScratchpadManager"),
    "MemoryWriter": (".memory.writer", "MemoryWriter"),
    "MemoryOrchestrator": (".memory.orchestrator", "MemoryOrchestrator"),
    # Memory Contract
    "MemoryContract": (".memory_contract", "MemoryContract"),
    "MemoryContractAdapter": (".memory_contract_adapter", "MemoryContractAdapter"),
}


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name not in _LAZY_EXPORTS:
        raise AttributeError(name)

    module_path, attr = _LAZY_EXPORTS[name]
    module = import_module(module_path, __name__)
    value = getattr(module, attr)
    globals()[name] = value  # cache
    return value


def __dir__() -> list[str]:  # pragma: no cover
    return sorted(set(list(globals().keys()) + list(_LAZY_EXPORTS.keys())))
