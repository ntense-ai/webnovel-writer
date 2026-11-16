#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'Memory contract types and Protocol definitions. Consumers such as context-agent, data-agent, and reviewer depend only on these types and protocols, not concrete StateManager, IndexManager, or ScratchpadManager implementations. See memory_contract_adapter.py for the implementation.'
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Contract return types
# ---------------------------------------------------------------------------

@dataclass
class CommitResult:
    'Return value of commit_chapter.'
    chapter: int
    entities_added: int = 0
    entities_updated: int = 0
    state_changes_recorded: int = 0
    relationships_added: int = 0
    memory_items_added: int = 0
    summary_path: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EntitySnapshot:
    'Return value of query_entity.'
    id: str
    name: str
    type: str = "character"
    tier: str = "core"
    aliases: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    first_appearance: int = 0
    last_appearance: int = 0
    recent_state_changes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Rule:
    'An item returned by query_rules.'
    id: str
    subject: str
    field: str
    value: str
    domain: str = ""
    source_chapter: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OpenLoop:
    'An item returned by get_open_loops.'
    id: str
    content: str
    status: str = "active"
    planted_chapter: int = 0
    expected_payoff: str = ""
    urgency: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineEvent:
    'An item returned by get_timeline.'
    event: str
    chapter: int = 0
    time_hint: str = ""
    event_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContextPack:
    'Return value of load_context. Callers interpret the structure of sections.'
    chapter: int
    sections: Dict[str, Any] = field(default_factory=dict)
    budget_used_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Contract Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class MemoryContract(Protocol):
    'Unified memory-module contract. Higher-level consumers depend on this Protocol rather than concrete implementation classes.'

    def commit_chapter(self, chapter: int, result: dict) -> CommitResult:
        'Post-writing commit: write chapter-processing results to every store.'
        ...

    def load_context(self, chapter: int, budget_tokens: int = 4000) -> ContextPack:
        'Pre-writing read: load the chapter context package.'
        ...

    def query_entity(self, entity_id: str) -> Optional[EntitySnapshot]:
        'Query a single entity snapshot.'
        ...

    def query_rules(self, domain: str = "") -> List[Rule]:
        'Query world rules, optionally filtered by domain.'
        ...

    def read_summary(self, chapter: int) -> str:
        'Read chapter-summary text.'
        ...

    def get_open_loops(self, status: str = "active") -> List[OpenLoop]:
        'Query unresolved foreshadowing and suspense threads.'
        ...

    def get_timeline(self, from_ch: int, to_ch: int) -> List[TimelineEvent]:
        'Query timeline events within a chapter range.'
        ...
