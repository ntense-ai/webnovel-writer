#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Static prompt-integrity validation.

Validate structures, references, and CLI commands in agents/*.md and skills/*/SKILL.md.
No model calls are required; suitable for CI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AGENTS_DIR = PLUGIN_ROOT / "agents"
SKILLS_DIR = PLUGIN_ROOT / "skills"
REFERENCES_DIR = PLUGIN_ROOT / "references"
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"

AGENT_FILES = sorted(AGENTS_DIR.glob("*.md"))
SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))
ALL_PROMPT_FILES = AGENT_FILES + SKILL_FILES
AUTHOR_REPORT_SKILLS = (
    "webnovel-init",
    "webnovel-plan",
    "webnovel-write",
    "webnovel-review",
)
SUBAGENT_RUN_FIELDS = (
    '"status": "completed | partial | failed | skipped"',
    '"problems": []',
    '"auto_handled": []',
    '"needs_user_action": false',
    '"duration_ms": 0',
    '"outputs": []',
)
SUBAGENT_PROMPT_FILES = (
    "context-agent.md",
    "reviewer.md",
    "data-agent.md",
    "deconstruction-agent.md",
)

# webnovel.py registered subcommands (extracted from add_parser)
REGISTERED_CLI_SUBCOMMANDS = {
    "where", "preflight", "project-status", "doctor", "write-gate", "projections", "user-report",
    "run-ledger", "run-log", "use",
    "index", "state", "rag", "style", "entity", "context", "memory",
    "migrate", "status", "update-state", "backup", "archive",
    "init", "extract-context", "memory-contract", "project-memory", "review-pipeline",
    "placeholder-scan", "master-outline-sync",
    "story-system", "chapter-commit", "story-events", "knowledge",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter as a dictionary."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def _extract_referenced_paths(text: str, base_dir: Path) -> list[tuple[str, Path]]:
    """Extract referenced Markdown file paths (references/, skills/, agents/, etc.).

    Return a list of (raw_ref, resolved_path) pairs.
    """
    refs = []
    # Match relative paths such as `references/xxx.md`, `../../references/xxx.md`, and `skills/xxx`.
    for m in re.finditer(r'[`"]((?:\.\./)*(?:references|skills|agents)/[^\s`"]+\.md)[`"]', text):
        raw = m.group(1)
        resolved = (base_dir / raw).resolve()
        refs.append((raw, resolved))
    # Match unquoted paths listed in references sections.
    for m in re.finditer(r'^- `((?:\.\./)*(?:references|skills|agents)/[^\s`]+\.md)`', text, re.MULTILINE):
        raw = m.group(1)
        resolved = (base_dir / raw).resolve()
        refs.append((raw, resolved))
    return refs


def _extract_cli_subcommands(text: str) -> list[str]:
    """Extract subcommands invoked through webnovel.py in the prompt."""
    cmds = set()
    for m in re.finditer(r'webnovel\.py["\s]+--project-root\s+[^\s]+\s+([a-z][\w-]*)', text):
        cmd = m.group(1)
        cmds.add(cmd)
    return sorted(cmds)


# ---------------------------------------------------------------------------
# 1. Frontmatter integrity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent_file", AGENT_FILES, ids=lambda f: f.name)
def test_agent_frontmatter_complete(agent_file: Path):
    """Every agent requires name, description, and tools."""
    fm = _extract_frontmatter(_read_text(agent_file))
    assert "name" in fm, f"{agent_file.name}: Missing name"
    assert "description" in fm, f"{agent_file.name}: Missing description"
    assert "tools" in fm, f"{agent_file.name}: Missing tools"


@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=lambda f: f.parent.name)
def test_skill_frontmatter_complete(skill_file: Path):
    """Every skill requires name and description."""
    fm = _extract_frontmatter(_read_text(skill_file))
    assert "name" in fm, f"{skill_file.parent.name}: Missing name"
    assert "description" in fm, f"{skill_file.parent.name}: Missing description"


# ---------------------------------------------------------------------------
# 2. Agent template structure (at least four sections)
# ---------------------------------------------------------------------------

EXPECTED_AGENT_SECTIONS = [
    "1.",
    "2.",
    "3.",
    "4.",
]


@pytest.mark.parametrize("agent_file", AGENT_FILES, ids=lambda f: f.name)
def test_agent_template_structure(agent_file: Path):
    """Each agent needs at least four numbered sections; section 12.2 no longer forces eight empty sections merely to satisfy tests."""
    text = _read_text(agent_file)
    missing = []
    for section in EXPECTED_AGENT_SECTIONS:
        # Match headings such as "## 1. Identity and goals" or "## 2. Tools and scripts", allowing suffixes.
        pattern = rf"^## {re.escape(section)}"
        if not re.search(pattern, text, re.MULTILINE):
            missing.append(section)
    assert not missing, f"{agent_file.name}: Missing section {missing}"


# ---------------------------------------------------------------------------
# 3. Reference integrity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prompt_file", ALL_PROMPT_FILES, ids=lambda f: f.name)
def test_all_references_exist(prompt_file: Path):
    """Every file referenced by a prompt must exist."""
    text = _read_text(prompt_file)
    base_dir = prompt_file.parent
    refs = _extract_referenced_paths(text, base_dir)
    missing = []
    for raw, resolved in refs:
        if not resolved.exists():
            missing.append(raw)
    assert not missing, f"{prompt_file.name}: References missing files {missing}"


# ---------------------------------------------------------------------------
# 4. CLI command validity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prompt_file", ALL_PROMPT_FILES, ids=lambda f: f.name)
def test_cli_commands_valid(prompt_file: Path):
    """Every webnovel.py subcommand in a prompt must be registered."""
    text = _read_text(prompt_file)
    cmds = _extract_cli_subcommands(text)
    # Exclude known exceptions, such as the pending workflow-command refactor in webnovel-review.
    skill_name = prompt_file.parent.name
    exceptions = _KNOWN_CLI_EXCEPTIONS.get(skill_name, set())
    invalid = [c for c in cmds if c not in REGISTERED_CLI_SUBCOMMANDS and c not in exceptions]
    assert not invalid, f"{prompt_file.name}: Uses unregistered CLI subcommands {invalid}"


# ---------------------------------------------------------------------------
# 5. Review-schema consistency
# ---------------------------------------------------------------------------

def test_review_schema_consistency():
    """Reviewer output fields must match review_schema.py."""
    reviewer_text = _read_text(AGENTS_DIR / "reviewer.md")

    # Extract issue fields from reviewer.md JSON examples.
    issue_fields_in_prompt = set()
    json_block = re.search(r'"issues":\s*\[\s*\{([^}]+)\}', reviewer_text, re.DOTALL)
    if json_block:
        for m in re.finditer(r'"(\w+)":', json_block.group(1)):
            issue_fields_in_prompt.add(m.group(1))

    # Extract ReviewIssue fields from review_schema.py.
    schema_path = SCRIPTS_DIR / "data_modules" / "review_schema.py"
    schema_text = _read_text(schema_path)
    schema_fields = set()
    in_review_issue = False
    for line in schema_text.splitlines():
        if "class ReviewIssue" in line:
            in_review_issue = True
            continue
        if in_review_issue:
            if line.strip().startswith("class ") or line.strip().startswith("def "):
                break
            m = re.match(r"\s+(\w+):\s+", line)
            if m:
                schema_fields.add(m.group(1))

    # Reviewer prompt fields must be a subset of schema fields.
    assert issue_fields_in_prompt, "Cannot extract issue fields from reviewer.md"
    assert schema_fields, "Cannot extract fields from review_schema.py"
    extra = issue_fields_in_prompt - schema_fields
    assert not extra, f"reviewer.md contains fields absent from review_schema.py: {extra}"
    assert "blocking_count" in reviewer_text
    assert "issues_count" in reviewer_text


# ---------------------------------------------------------------------------
# 6. No stale references to deleted files
# ---------------------------------------------------------------------------

KNOWN_DELETED_FILES = [
    "step-1.5-contract.md",
    "step-3-review-gate.md",
    "step-5-debt-switch.md",
    "workflow-details.md",
    "checker-output-schema.md",
    "workflow_manager.py",
    "webnovel-resume",
    "golden_three_checker.py",
    "snapshot_manager.py",
]

_KNOWN_CLI_EXCEPTIONS = {}


@pytest.mark.parametrize("prompt_file", ALL_PROMPT_FILES, ids=lambda f: f.name)
def test_no_stale_references(prompt_file: Path):
    """Do not reference known deleted files."""
    text = _read_text(prompt_file)
    found = [name for name in KNOWN_DELETED_FILES if name in text]
    assert not found, f"{prompt_file.name}: Stale references to deleted files {found}"


def test_webnovel_review_skill_uses_unified_reviewer_pipeline():
    """webnovel-review and webnovel-write must share the reviewer + review-pipeline chain."""
    skill_text = _read_text(SKILLS_DIR / "webnovel-review" / "SKILL.md")

    assert "`reviewer`" in skill_text
    assert "Use the Agent tool to run `webnovel-writer:reviewer`" in skill_text
    assert "subagent_type:" not in skill_text
    assert "review-pipeline" in skill_text
    assert ".webnovel/tmp/review_results.json" in skill_text
    assert ".webnovel/tmp/review_metrics.json" in skill_text

    for legacy_agent in (
        "consistency-checker",
        "continuity-checker",
        "ooc-checker",
        "reader-pull-checker",
        "high-point-checker",
        "pacing-checker",
    ):
        assert legacy_agent not in skill_text

    assert " workflow " not in skill_text


def test_active_skills_use_agent_tool_name_not_legacy_task():
    """Claude Code 2.1.63+ renamed Task to Agent; active skills must not declare Task."""
    for skill_file in SKILL_FILES:
        text = _read_text(skill_file)
        fm = _extract_frontmatter(text)
        allowed_tools = fm.get("allowed-tools", "")
        assert "Task" not in allowed_tools, f"{skill_file.parent.name}: allowed-tools still declares Task"
        assert "Task invocation" not in text, f"{skill_file.parent.name}: still uses ambiguous Task invocation prose"
        assert "Must call through `Task`" not in text, f"{skill_file.parent.name}: still requires the obsolete Task tool name"


def test_webnovel_write_skill_uses_explicit_agent_invocation_templates():
    """Invoke required subagents through Agent using registered webnovel-writer:X names, not pseudo-function subagent_type blocks (plan 4.4.2/8.4)."""
    text = _read_text(SKILLS_DIR / "webnovel-write" / "SKILL.md")
    fm = _extract_frontmatter(text)

    assert "Agent" in fm.get("allowed-tools", "")
    for subagent in ("context-agent", "reviewer", "data-agent"):
        assert f"webnovel-writer:{subagent}" in text, f"Missing {subagent} explicit registered-name invocation"
    assert "subagent_type:" not in text, "Must not use pseudo-function subagent_type blocks"
    assert "the main workflow must not verbally substitute for subagent output" in text


@pytest.mark.parametrize("skill_name", AUTHOR_REPORT_SKILLS)
def test_main_skills_define_author_friendly_final_report_contract(skill_name: str):
    """The four main skills require an author-friendly overall status and three-part final report."""
    text = _read_text(SKILLS_DIR / skill_name / "SKILL.md")

    assert "Author-friendly final report contract" in text
    assert "Overall status: Completed / Partially completed / Needs your attention / Not completed" in text
    for section in (
        "1. Files produced and completion status",
        "2. Issues and unusually long steps encountered",
        "3. Recommended next steps",
    ):
        assert section in text, f"{skill_name}: Missing final-report section {section}"
    for issue_type in ("Automatically handled", "Suggested for confirmation", "Must address"):
        assert issue_type in text, f"{skill_name}: Missing issue classification {issue_type}"
    assert "task-oriented language" in text
    assert "copyable commands" in text
    assert "/webnovel-doctor" in text
    assert "Do not report token statistics" in text


def test_write_skill_final_report_covers_commit_projection_and_backup():
    """The writing report must cover prose, review, data artifacts, commit, projections, and backup."""
    text = _read_text(SKILLS_DIR / "webnovel-write" / "SKILL.md")
    for required in (
        "Chapter prose file path",
        "Review report path",
        ".webnovel/tmp/review_results.json",
        ".webnovel/tmp/fulfillment_result.json",
        ".webnovel/tmp/disambiguation_result.json",
        ".webnovel/tmp/extraction_result.json",
        ".story-system/commits/chapter_{NNN}.commit.json",
        "state / index / summary / memory / vector update status",
        "Backup status",
        "Whether writing can continue with the next chapter",
    ):
        assert required in text
    assert "chapter-commit rejected" in text
    assert "final status must not be “Completed”" in text
    assert "--fast" in text and "--minimal" in text
    assert "projection retry" in text


def test_review_skill_final_report_covers_metrics_and_blocking_decision():
    """The review report must cover reports, metrics, blocker counts, and user adjudication status."""
    text = _read_text(SKILLS_DIR / "webnovel-review" / "SKILL.md")
    for required in (
        "review report file",
        ".webnovel/tmp/review_results.json",
        ".webnovel/tmp/review_metrics.json",
        "review_metrics",
        "number of blocking issues",
        "status of the user's decision",
        "If there are no blockers, explicitly state that writing can continue",
    ):
        assert required in text
    assert "If blocking issues exist and the user has not selected a handling strategy" in text
    assert "final status is “Needs your attention”" in text


def test_main_skills_record_subagent_run_summaries_for_agent_calls():
    """After Agent calls, the main skill records SubagentRun summaries for the final report."""
    expected = {
        "webnovel-init": ("deconstruction-agent",),
        "webnovel-write": ("context-agent", "reviewer", "data-agent"),
        "webnovel-review": ("reviewer",),
    }

    for skill_name, agents in expected.items():
        text = _read_text(SKILLS_DIR / skill_name / "SKILL.md")
        assert "SubagentRun" in text, f"{skill_name}: Missing SubagentRun summary contract"
        for field in SUBAGENT_RUN_FIELDS:
            assert field in text, f"{skill_name}: Missing SubagentRun field {field}"
        for agent_name in agents:
            assert f'"name": "{agent_name}"' in text, (
                f"{skill_name}: Missing {agent_name} SubagentRun name"
            )
    plan_text = _read_text(SKILLS_DIR / "webnovel-plan" / "SKILL.md")
    assert "SubagentRun" not in plan_text, "webnovel-plan does not currently call Agent and must not invent SubagentRun"


@pytest.mark.parametrize("agent_file_name", SUBAGENT_PROMPT_FILES)
def test_agents_expose_subagent_run_summary_signals_without_changing_outputs(agent_file_name: str):
    """Agent prompts expose summary signals without adding SubagentRun to raw artifacts."""
    text = _read_text(AGENTS_DIR / agent_file_name)

    assert "Aggregatable SubagentRun Signals" in text
    for field in ("`status`", "`problems`", "`auto_handled`", "`needs_user_action`", "`duration_ms`", "`outputs`"):
        assert field in text, f"{agent_file_name}: Missing summarizable field {field}"
    assert "The main workflow records" in text

    if agent_file_name == "reviewer.md":
        assert "Do not include `SubagentRun` in reviewer JSON" in text
    elif agent_file_name == "data-agent.md":
        assert "Do not put `SubagentRun` in the three artifacts" in text
    elif agent_file_name == "deconstruction-agent.md":
        assert "Do not add `SubagentRun` to the `init_reference_research` top level" in text
    elif agent_file_name == "context-agent.md":
        assert "Do not include `SubagentRun` JSON in the brief" in text


@pytest.mark.parametrize("skill_name", AUTHOR_REPORT_SKILLS)
def test_main_skills_define_author_friendly_progress_and_recovery_contract(skill_name: str):
    """The four main skills require progress cues, minimal confirmations, recovery guidance, and log boundaries."""
    text = _read_text(SKILLS_DIR / skill_name / "SKILL.md")

    for required in (
        "Author-friendly progress and recovery contract",
        "progress update",
        "Minimize interruptions",
        "finite choices",
        "When stuck, explain",
        "blocker",
        "completed work",
        "recovery advice",
        ".webnovel/logs/run_last.log",
        "run-log",
        "user-report",
    ):
        assert required.casefold() in text.casefold(), f"{skill_name}: Missing progress/recovery contract {required}"
    assert "not raw JSON" in text or "do not output raw JSON" in text


def test_write_skill_progress_nodes_are_author_friendly_and_limited():
    """Writing progress must use no more than six author-friendly stages."""
    text = _read_text(SKILLS_DIR / "webnovel-write" / "SKILL.md")
    marker = "Writing progress milestones (at most six)"
    assert marker in text
    section = text[text.find(marker): text.find("## Sufficiency gate")]
    nodes = re.findall(r"^\d+\.\s+(.+)$", section, flags=re.MULTILINE)
    assert 1 <= len(nodes) <= 6
    for forbidden in ("write-gate", "chapter-commit", "projection_status", "artifact", "schema"):
        assert forbidden not in "\n".join(nodes)
    for friendly in ("Check project environment", "Organize writing context", "Draft chapter prose", "Writing check", "Save this chapter's story facts", "Commit and back up"):
        assert any(friendly in node for node in nodes), f"Missing author-friendly stage {friendly}"


def test_write_skill_resume_contract_uses_runtime_ledger_and_confirmation_boundaries():
    """Repeated writing must check trusted checkpoints and pause for confirmation before risky overwrites."""
    text = _read_text(SKILLS_DIR / "webnovel-write" / "SKILL.md")
    for required in (
        "run-ledger write-resume",
        "trustworthy checkpoint",
        "prose was manually edited",
        "outline was updated after the prose",
        "an accepted chapter is rerun",
        "keep current prose / redraft / view status only",
        "Never overwrite the author's manual edits",
    ):
        assert required in text


def test_story_system_runtime_contract_commands_exist():
    text = (SKILLS_DIR / "webnovel-write" / "SKILL.md").read_text(encoding="utf-8")
    assert "story-system" in text
    assert "--emit-runtime-contracts" in text


def test_webnovel_write_skill_uses_chapter_commit_as_step5_mainline():
    text = (SKILLS_DIR / "webnovel-write" / "SKILL.md").read_text(encoding="utf-8")
    assert "chapter-commit" in text
    assert "CHAPTER_COMMIT" in text
    assert "state process-chapter" not in text


def test_webnovel_write_skill_uses_project_root_backup_not_bare_git_add():
    text = (SKILLS_DIR / "webnovel-write" / "SKILL.md").read_text(encoding="utf-8")
    assert "webnovel.py" in text
    assert "--project-root \"${PROJECT_ROOT}\" backup" in text
    assert "git add ." not in text


def test_webnovel_query_skill_prefers_story_system_and_memory_contract():
    text = (SKILLS_DIR / "webnovel-query" / "SKILL.md").read_text(encoding="utf-8")
    assert "memory-contract load-context" in text
    assert ".story-system/" in text
    assert 'cat "$PROJECT_ROOT/.webnovel/state.json"' not in text


def test_context_agent_prefers_contract_and_latest_commit_mainline():
    text = (AGENTS_DIR / "context-agent.md").read_text(encoding="utf-8")
    assert "story_contracts" in text or ".story-system/" in text
    assert "CHAPTER_COMMIT" in text or "chapter-commit" in text
    assert "load-context" in text


def test_context_agent_loads_fixed_guides_and_outputs_writer_brief():
    text = (AGENTS_DIR / "context-agent.md").read_text(encoding="utf-8")
    # core-constraints and anti-ai-guide are incorporated into the Writing Laws section.
    assert "Writing Laws" in text or "Anti-AI" in text
    assert "writing brief" in text
    assert "Step 2 direct-writing prompt" not in text
    assert "Context Contract" not in text


def test_agents_do_not_name_nonexistent_writing_dna_files():
    for filename in ("context-agent.md", "reviewer.md"):
        text = (AGENTS_DIR / filename).read_text(encoding="utf-8")
        assert "P20_WRITING_DNA" not in text
        assert "WRITING_DNA.md" not in text
        assert ".claude/rules/P20_" not in text


def test_data_agent_is_described_as_extraction_only_not_direct_write_mainline():
    text = (AGENTS_DIR / "data-agent.md").read_text(encoding="utf-8")
    assert "chapter-commit" in text
    assert "extraction_result.json" in text
    assert "planned_nodes" in text
    assert "missed_nodes" in text
    assert "pending" in text
    assert "event_id" in text
    assert "event_type" in text
    assert "subject" in text
    assert "directly write index.db and state.json" not in text
    for forbidden in (
        "RAG vector indexing",
        "observability",
        "scene index written",
        "indexing failed",
    ):
        assert forbidden not in text, f"data-agent.md Must not retain projection-writing instructions: {forbidden}"
    # data-agent must not include runnable chapter-commit commands: the main workflow commits facts; data-agent only produces artifacts.
    assert not re.search(r"webnovel\.py[^\n]+chapter-commit", text), (
        "data-agent.md Must not contain a runnable webnovel.py ... chapter-commit command"
    )


# (Retired under plan section 12.2) test_webnovel_write_data_agent_prompt_requires_extraction_schema：
# The former test required inline data-artifact schema names, conflicting with criterion one. Schema coverage now belongs to
# the data-agent.md producer（test_data_agent_is_described_as_extraction_only_not_direct_write_mainline）
# + negative precommit cases (Task 7). Main skills no longer inline long schemas.


def test_dashboard_and_plan_skills_surface_story_runtime_mainline():
    dashboard_text = (SKILLS_DIR / "webnovel-dashboard" / "SKILL.md").read_text(encoding="utf-8")
    plan_text = (SKILLS_DIR / "webnovel-plan" / "SKILL.md").read_text(encoding="utf-8")
    assert "story-runtime/health" in dashboard_text
    assert ".story-system/" in plan_text


def test_webnovel_write_skill_routes_step2_through_writing_brief():
    text = (SKILLS_DIR / "webnovel-write" / "SKILL.md").read_text(encoding="utf-8")
    assert "writing brief" in text
    assert "context-agent" in text
    assert "Step 0.5" not in text
    assert 'cat "${SKILL_ROOT}/../../references/shared/core-constraints.md"' not in text
    assert 'cat "${SKILL_ROOT}/references/anti-ai-guide.md"' not in text


def test_context_agent_and_write_skill_form_isolated_write_chain():
    context_text = (AGENTS_DIR / "context-agent.md").read_text(encoding="utf-8")
    skill_text = (SKILLS_DIR / "webnovel-write" / "SKILL.md").read_text(encoding="utf-8")

    assert "writing brief" in context_text
    assert "writing brief" in skill_text
    assert "context-agent" in skill_text
    assert "Context Contract" not in context_text
    assert "Step 2 direct-writing prompt" not in context_text


def test_no_direct_state_writes_in_write_skill():
    """webnovel-write SKILL.md must not invoke set-chapter-status."""
    text = (SKILLS_DIR / "webnovel-write" / "SKILL.md").read_text(encoding="utf-8")
    assert "state set-chapter-status" not in text, (
        "webnovel-write must not directly invoke state set-chapter-status, "
        "chapter_status is advanced automatically by state_projection_writer at commit time"
    )


def test_no_direct_state_writes_in_agents():
    """Agent prompts must not directly write state or index."""
    for agent_file in AGENT_FILES:
        text = _read_text(agent_file)
        assert "state set-chapter-status" not in text, (
            f"{agent_file.name}: must not directly invoke state set-chapter-status"
        )


def test_deconstruction_agent_preserves_init_handoff_and_boundaries():
    """reference deconstruction must remain extraction-only and init-scoped."""
    text = _read_text(AGENTS_DIR / "deconstruction-agent.md")

    assert "init_reference_research" in text
    assert ".webnovel/tmp/reference_analyses/<safe-title>/" not in text
    assert "Write no files" in text
    assert "must not write `_progress.md`" in text
    assert "resume_state" in text
    assert "tools: Read, Grep, Bash" in text
    assert "Quick mode" in text
    assert "Deep mode" in text
    assert "opening three chapters" in text
    assert "plot points" in text
    assert "quality gates" in text
    assert "from memory/general knowledge" in text
    assert "conditional framework" in text
    assert "emotional chains" in text
    assert "boundaries of the core premise" in text

    for field in (
        "reader_promise",
        "opening_hook_patterns",
        "cool_point_loops",
        "protagonist_patterns",
        "antagonist_pressure_patterns",
        "pacing_notes",
        "borrowable_structures",
        "do_not_copy",
        "differentiation_requirements",
        "init_candidates",
        "quality",
        "resume_state",
        "orphan_plot_fallback",
        "canon_contamination_warnings",
    ):
        assert f'"{field}"' in text

    for forbidden_path in (
        ".story-system/",
        "settings/",
        "outlines/",
        "chapters/",
        ".webnovel/",
    ):
        assert forbidden_path in text

    assert "Do not write `idea_bank.json`" in text
    assert "after user confirmation" in text
    assert "MIT License attribution" not in text


def test_webnovel_init_deconstruction_wiring_keeps_confirmation_gate():
    """init may consume only confirmed, transformed reference patterns."""
    text = _read_text(SKILLS_DIR / "webnovel-init" / "SKILL.md")

    assert "Use the Agent tool to run `webnovel-writer:deconstruction-agent`" in text
    assert "subagent_type:" not in text
    assert "Step 1.5: Ask about inspiration sources" in text
    assert "Before collecting the story core" in text
    assert "Do not deconstruct books by default" in text
    assert "Where would you like to start with this book's inspiration" in text
    assert "init_reference_research" in text
    assert "init_reference_research JSON object" in text
    assert ".webnovel/tmp/reference_analyses/<safe-title>/" not in text
    assert "project_root=${PROJECT_ROOT" not in text
    assert "Do not write files" in text
    assert "The init main workflow must not substitute a verbal analysis for its results" in text
    assert "`quality`" in text
    assert "`quality.passed=false`" in text
    assert "`confidence < 0.85`" in text

    for handoff_field in (
        "reader_promise",
        "opening_hook_patterns",
        "cool_point_loops",
        "protagonist_patterns",
        "antagonist_pressure_patterns",
        "pacing_notes",
        "borrowable_structures",
        "differentiation_requirements",
        "init_candidates",
    ):
        assert handoff_field in text

    for forbidden_path in (
        "idea_bank.json",
        ".story-system",
        "settings",
        "outlines",
        "chapters",
        ".webnovel/state.json",
    ):
        assert forbidden_path in text

    assert "before explicit user confirmation" in text
    assert "Steps 2–6 may use only patterns the user has confirmed and that have been transformed into differentiated expressions for this book" in text
    assert "Summarize confirmed inspiration sources from Step 1.5" in text


# ---------------------------------------------------------------------------
# 7. Type-A cross-layer invariants: behavioral and contract assertions (Phase 0 guards)
#    These assertions guard implemented invariants and must pass. Prefer structural invariants
#    (command presence/order, node schemas, and variables carrying real arguments) over brittle wording checks.
# ---------------------------------------------------------------------------

# Invariant A2: plan and write must run placeholder-scan at required checkpoints.
def test_placeholder_scan_runs_in_both_plan_and_write_skills():
    """Invariant 2: both plan and write explicitly invoke placeholder-scan."""
    plan_text = _read_text(SKILLS_DIR / "webnovel-plan" / "SKILL.md")
    write_text = _read_text(SKILLS_DIR / "webnovel-write" / "SKILL.md")
    for name, text in (("webnovel-plan", plan_text), ("webnovel-write", write_text)):
        cmds = _extract_cli_subcommands(text)
        assert "placeholder-scan" in cmds, (
            f"{name}: Required checkpoint lacks placeholder-scan CLI invocation"
        )


# Invariant A3: chapter-level story-system refresh uses the actual CHAPTER_GOAL variable.
# Do not pass placeholder goals as positional queries.
@pytest.mark.parametrize("skill_name", ["webnovel-plan", "webnovel-write"])
def test_story_system_chapter_refresh_uses_real_goal_not_placeholder_query(skill_name: str):
    """Invariant 3: story-system receives ${CHAPTER_GOAL}, and placeholder queries are explicitly prohibited."""
    text = _read_text(SKILLS_DIR / skill_name / "SKILL.md")
    # Commands must pass a variable containing the actual goal as the query.
    assert 'story-system "${CHAPTER_GOAL}"' in text, (
        f"{skill_name}: story-system does not use the actual ${{CHAPTER_GOAL}} as the query argument"
    )
    # Placeholder queries must never be positional arguments to story-system.
    for placeholder in ("{chapter_outline_goal}", "Chapter N outline goal"):
        assert f'story-system "{placeholder}"' not in text, (
            f"{skill_name}: story-system must not pass placeholder text {placeholder} as the query"
        )
    # Require an explicit prohibition on placeholder queries without fixing its precise wording.
    assert "{chapter_outline_goal}" in text and "Chapter N outline goal" in text, (
        f"{skill_name}: Missing an explicit prohibition on placeholder queries"
    )


# Invariant A4: chapter refresh must use --persist and --emit-runtime-contracts.
@pytest.mark.parametrize("skill_name", ["webnovel-plan", "webnovel-write"])
def test_story_system_chapter_refresh_persists_runtime_contracts(skill_name: str):
    """Invariant 4: chapter refresh requires both --persist and --emit-runtime-contracts."""
    text = _read_text(SKILLS_DIR / skill_name / "SKILL.md")
    cmd_start = text.find('story-system "${CHAPTER_GOAL}"')
    assert cmd_start >= 0, f"{skill_name}: Missing chapter-level story-system invocation"
    # Inspect the command through the next blank line and assert both required flags.
    cmd_tail = text[cmd_start:cmd_start + 400]
    assert "--persist" in cmd_tail, f"{skill_name}: chapter-level story-system Missing --persist"
    assert "--emit-runtime-contracts" in cmd_tail, (
        f"{skill_name}: chapter-level story-system Missing --emit-runtime-contracts"
    )
    assert "--chapter" in cmd_tail, f"{skill_name}: chapter-level story-system Missing --chapter"


# Invariant A5: all write gates must appear in prewrite→precommit→postcommit order.
def test_write_skill_gate_stages_ordered_prewrite_precommit_postcommit():
    """Invariant 5: write-gate ordering is fixed."""
    text = _read_text(SKILLS_DIR / "webnovel-write" / "SKILL.md")
    prewrite = text.find("write-gate --chapter {chapter_num} --stage prewrite")
    precommit = text.find("write-gate --chapter {chapter_num} --stage precommit")
    postcommit = text.find("write-gate --chapter {chapter_num} --stage postcommit")
    assert prewrite >= 0, "Missing prewrite gate"
    assert precommit >= 0, "Missing precommit gate"
    assert postcommit >= 0, "Missing postcommit gate"
    assert prewrite < precommit < postcommit, (
        "write-gate gate order must be prewrite→precommit→postcommit"
    )


# Invariant A7: writing and review persist raw reviewer JSON through review-pipeline --save-metrics.
@pytest.mark.parametrize("skill_name", ["webnovel-write", "webnovel-review"])
def test_review_pipeline_persists_metrics_in_review_chain(skill_name: str):
    """Invariant 7: persist reviewer JSON through review-pipeline --save-metrics."""
    text = _read_text(SKILLS_DIR / skill_name / "SKILL.md")
    cmds = _extract_cli_subcommands(text)
    assert "review-pipeline" in cmds, f"{skill_name}: Missing review-pipeline CLI invocation"
    assert "--save-metrics" in text, f"{skill_name}: review-pipeline missing --save-metrics persistence"


# Invariant A10: postcommit verifies all five projections; failures use only projections retry.
def test_write_skill_postcommit_verifies_five_projections_and_retry_only():
    """Invariant 10: verify state/index/summary/memory/vector projections; only retry failed projections."""
    text = _read_text(SKILLS_DIR / "webnovel-write" / "SKILL.md")
    assert "state/index/summary/memory/vector" in text, (
        "Missing projection verification of all five projections (state/index/summary/memory/vector)"
    )
    # The sole recovery is projections retry; assert the literal multiline invocation.
    assert "projections retry --chapter {chapter_num}" in text, (
        "projection failure recovery must be projections retry --chapter {chapter_num}"
    )


# Invariant A12: plan covers beats, timeline, structured chapter nodes, master-outline writeback, and state updates.
def test_plan_skill_covers_outline_writeback_and_state_sync_contract():
    """Invariant 12: plan includes beats, timeline, nodes, writeback JSON, master-outline-sync, and update-state."""
    text = _read_text(SKILLS_DIR / "webnovel-plan" / "SKILL.md")
    # Beat-sheet and timeline artifacts
    assert "outlines/volume-{volume_id}-beats.md" in text
    assert "outlines/volume-{volume_id}-timeline.md" in text
    # Structured chapter-outline nodes
    for node in ("CBN", "CPNs", "CEN", "Must-cover nodes", "Chapter prohibitions"):
        assert node in text, f"plan MissingStructured chapter-outline nodesmarker {node}"
    # Structured master-outline writeback; never infer foreshadowing from free text.
    assert "outlines/volume-{volume_id}-master-outline-update.json" in text
    # Setting writeback and state synchronization commands
    cmds = _extract_cli_subcommands(text)
    assert "master-outline-sync" in cmds, "plan Missing master-outline-sync writeback command"
    assert "update-state" in cmds, "plan Missing update-state state-update command"


# ---------------------------------------------------------------------------
# 8. Type-B cross-layer contracts (plan 5.2-B / 4.5 write-ownership matrix)
#    Tools and persistence ownership already agree; guard with passing tests.
#    Originally the precommit read-only git diff scope check was missing; Task 5 (Phase 1) removes xfail once implemented.
# ---------------------------------------------------------------------------

def _agent_tools(agent_name: str) -> list[str]:
    """Parse an agent frontmatter tools list."""
    fm = _extract_frontmatter(_read_text(AGENTS_DIR / f"{agent_name}.md"))
    return [t.strip() for t in fm.get("tools", "").split(",") if t.strip()]


# Type-B invariant: write ownership matches tools, with a single writer.
# data-agent is the sole writer of three temporary artifacts and requires Write.
# reviewer/context-agent/deconstruction-agent return results for the main workflow to persist and must not have Write.
def test_agent_write_ownership_matches_tools_frontmatter():
    """Write-ownership invariant: only data-agent has Write, not the other three agents."""
    assert "Write" in _agent_tools("data-agent"), (
        "data-agent must have Write as the sole writer of the three temporary artifacts"
    )
    for agent_name in ("reviewer", "context-agent", "deconstruction-agent"):
        assert "Write" not in _agent_tools(agent_name), (
            f"{agent_name} must not have Write; it returns results for the main workflow to persist"
        )


# Type-B invariant: write SKILL performs a read-only git diff scope check before chapter-commit.
# Historical state: this step was absent and marked xfail until Phase 1 Task 5 implemented the hard guard.
# Type-B invariant: write SKILL performs a read-only git diff scope check before chapter-commit.
# Phase 1 Task 5 is implemented: enforce the hard guard without xfail.
def test_write_skill_has_readonly_git_diff_change_surface_check():
    """Precommit scope invariant: write SKILL runs read-only git diff before chapter-commit."""
    text = _read_text(SKILLS_DIR / "webnovel-write" / "SKILL.md")
    assert "diff --name-status" in text, (
        "write SKILL Missing precommit read-only git diff --name-status change-scope validation"
    )
    assert "diff --check" in text, (
        "write SKILL Missing git diff --check whitespace/conflict-marker validation"
    )


# Type-B prompt-ownership invariant: write/review explicitly declare ownership,
# cross-checked with frontmatter (test_agent_write_ownership_matches_tools_frontmatter) and the artifact_ownership behavioral eval.
def test_write_review_skills_state_artifact_ownership():
    """Reviewer returns JSON; the main workflow persists review_results.json; data-agent is the sole artifact writer."""
    write_text = _read_text(SKILLS_DIR / "webnovel-write" / "SKILL.md")
    review_text = _read_text(SKILLS_DIR / "webnovel-review" / "SKILL.md")
    for name, text in (("webnovel-write", write_text), ("webnovel-review", review_text)):
        assert re.search(r"main (?:workflow|flow)", text) and ".webnovel/tmp/review_results.json" in text, (
            f"{name}: Missing ownership declaration: reviewer returns results, main workflow writes review_results.json"
        )
    assert "sole writer" in write_text, "webnovel-write Missing declaration that data-agent is the sole writer"
    assert "The main workflow checks only file existence and schema" in write_text
    assert "do not write directly to state/index/summaries/memory/vectors/projection" in write_text


# Sections 9.3/12.3 guard removal of ReAct and reasoning-process narration: reviews specify outputs, not private reasoning.
def test_reviewer_has_no_react_meta_narrative():
    """reviewer.md must not retain ReAct or private-reasoning narration."""
    text = _read_text(AGENTS_DIR / "reviewer.md")
    assert "ReAct" not in text, "reviewer must not mention ReAct"
    assert "chain of thought" not in text.casefold(), "reviewer must not retain private-reasoning narration"
