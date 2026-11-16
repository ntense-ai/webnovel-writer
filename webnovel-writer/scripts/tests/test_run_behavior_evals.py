#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import pytest
from pathlib import Path


def _ensure_scripts_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parents[1]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


_ensure_scripts_on_path()

from run_behavior_evals import EVALUATORS, load_suite, run_behavior_evals  # noqa: E402


def test_run_behavior_evals_fast_suite_passes_for_current_package():
    root = Path(__file__).resolve().parents[2]

    report = run_behavior_evals(root, suite="fast")

    assert report["ok"] is True
    assert report["total"] >= 5


# Keep the English prompt checks meaningful: removing any required clause must
# fail its evaluator, rather than making the whole-package smoke check vacuous.


_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
_SKILL_REQUIREMENTS = [
    (case, required)
    for case in load_suite(_PACKAGE_ROOT, "fast")["cases"]
    if case["type"] == "skill_contract"
    for required in case.get("required", [])
]


@pytest.mark.parametrize("case,required", _SKILL_REQUIREMENTS)
def test_english_skill_contract_rejects_missing_requirement(tmp_path, case, required):
    relative = Path("skills") / case["skill"] / "SKILL.md"
    source = (_PACKAGE_ROOT / relative).read_text(encoding="utf-8")
    assert required in source
    target = tmp_path / "webnovel-writer" / relative
    target.parent.mkdir(parents=True)
    target.write_text(source.replace(required, "REMOVED_CONTRACT"), encoding="utf-8")
    result = EVALUATORS["skill_contract"](tmp_path, case)
    assert result["passed"] is False
    assert required in result["evidence"]


@pytest.mark.parametrize("relative,clause,evaluator", [
    ("agents/data-agent.md", "Write three JSON files to `.webnovel/tmp/`", "data_agent_boundary"),
    ("agents/data-agent.md", "Do not directly write state/index/summaries/memory", "data_agent_boundary"),
    ("skills/webnovel-write/SKILL.md", "sole writer", "artifact_ownership"),
    ("skills/webnovel-write/SKILL.md", "The main workflow checks only file existence and schema", "artifact_ownership"),
    ("skills/webnovel-write/SKILL.md", "do not write directly to state/index/summaries/memory/vectors/projection", "artifact_ownership"),
])
def test_english_artifact_contract_rejects_missing_boundary(tmp_path, relative, clause, evaluator):
    paths = ["agents/data-agent.md", "agents/reviewer.md",
             "skills/webnovel-write/SKILL.md", "skills/webnovel-review/SKILL.md"]
    for name in paths:
        source = (_PACKAGE_ROOT / name).read_text(encoding="utf-8")
        if name == relative:
            assert clause in source
            source = source.replace(clause, "REMOVED_CONTRACT")
        target = tmp_path / "webnovel-writer" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    result = EVALUATORS[evaluator](tmp_path, {"id": "mutation", "type": evaluator})
    assert result["passed"] is False
    assert any(clause in evidence for evidence in result["evidence"])
