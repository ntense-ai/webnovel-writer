#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..prewrite_validator import PrewriteValidator
from ..project_phase import (
    PHASE_CHAPTER_CONTRACT_READY,
    PHASE_DRAFT_IN_PROGRESS,
    PHASE_READY_TO_COMMIT,
    resolve_project_phase,
)
from ..story_runtime_sources import load_runtime_sources
from . import gate_report, issue


ALLOWED_PREWRITE_PHASES = {
    PHASE_CHAPTER_CONTRACT_READY,
    PHASE_DRAFT_IN_PROGRESS,
    PHASE_READY_TO_COMMIT,
}


def _plot_structure(chapter_contract: dict[str, Any], review_contract: dict[str, Any]) -> dict[str, Any]:
    directive = chapter_contract.get("chapter_directive") if isinstance(chapter_contract, dict) else {}
    if not isinstance(directive, dict):
        directive = {}
    return {
        "mandatory_nodes": list(
            directive.get("must_cover_nodes")
            or directive.get("mandatory_nodes")
            or review_contract.get("must_cover_nodes")
            or review_contract.get("mandatory_nodes")
            or []
        ),
        "prohibitions": list(
            directive.get("forbidden_zones")
            or directive.get("prohibitions")
            or review_contract.get("blocking_rules")
            or []
        ),
    }


def run_prewrite_gate(project_root: Path, chapter: int) -> dict[str, Any]:
    snapshot = resolve_project_phase(project_root, chapter=chapter)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if snapshot.phase not in ALLOWED_PREWRITE_PHASES:
        errors.append(
            issue(
                "phase_not_ready_for_prewrite",
                message=f"phase {snapshot.phase} is not ready for prewrite",
                impact="The prewrite contract or project scaffold is incomplete; continuing risks stale context or missing constraints.",
                repair="Run project-status/doctor first, then follow next_action to complete initialization, planning, or Story System contracts.",
                details=snapshot.to_dict(),
            )
        )

    runtime = load_runtime_sources(project_root, chapter)
    contracts = runtime.contracts
    story_contract = {
        "master_setting": contracts.get("master") or {},
        "volume_brief": contracts.get("volume") or {},
        "chapter_brief": contracts.get("chapter") or {},
        "review_contract": contracts.get("review") or {},
    }
    review_contract = contracts.get("review") or {}
    plot_structure = _plot_structure(contracts.get("chapter") or {}, review_contract)

    validation = PrewriteValidator(project_root).build(
        chapter=chapter,
        review_contract=review_contract,
        plot_structure=plot_structure,
        story_contract=story_contract,
    )
    if validation.get("blocking"):
        errors.append(
            issue(
                "prewrite_validator_blocking",
                message="prewrite validator reported blocking issue(s)",
                impact="The current chapter writing input is not trustworthy.",
                repair="Follow blocking_reasons to complete contracts, resolve pending disambiguation, and fill relevant placeholders.",
                details=validation,
            )
        )
    elif runtime.fallback_sources:
        warnings.append(
            issue(
                "story_runtime_fallback",
                message="story runtime has fallback sources",
                severity="warning",
                impact="Writing context may lack the previous chapter's accepted commit.",
                repair="Confirm this is the first chapter, or supply the missing accepted commit before writing.",
                details=list(runtime.fallback_sources),
            )
        )

    return gate_report(
        stage="prewrite",
        project_root=project_root,
        chapter=chapter,
        phase=snapshot.phase,
        errors=errors,
        warnings=warnings,
        details={
            "phase": snapshot.to_dict(),
            "story_runtime": runtime.to_dict(),
            "prewrite_validation": validation,
        },
    )
