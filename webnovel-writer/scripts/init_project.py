#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'Initialize a webnovel project.\n\nCreate a runnable webnovel-project layout, create or update .webnovel/state.json with initialization metadata and compatible read models, and generate setting/outline templates for /webnovel-plan and /webnovel-write.\n\nThis script is the sole permitted file-generation entry point for /webnovel-init. Generated files are template scaffolds for later completion by the author or AI, but all essential files are guaranteed to exist.'

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from runtime_compat import enable_windows_utf8_stdio
from typing import Any, Dict, List
import re

# Security fix: import secure utility functions.
from security_utils import sanitize_commit_message, atomic_write_json, is_git_available
from project_locator import write_current_project_pointer
from project_paths import project_dir as resolve_project_dir, project_path as resolve_project_path
from genre_taxonomy import resolve_genre_input, resolve_template_stems, load_genre_taxonomy, _normalize_lookup_key


# Windows encoding compatibility.
if sys.platform == "win32":
    enable_windows_utf8_stdio()



def _validate_initial_genre_source(genre: str) -> str:
    normalized = str(genre or "").strip()
    if normalized and normalized.casefold() != "all":
        # Resolve individual labels so a partially recognized hybrid is not
        # silently accepted. Canonical schema keys are English.
        unresolved = [part for part in _split_genre_keys(normalized)
                      if _normalize_lookup_key(part) not in load_genre_taxonomy().lookup]
        if unresolved:
            raise SystemExit(
                "Unknown genre label(s): " + ", ".join(unresolved)
                + ". Use e.g. fantasy, science fiction, mystery, historical romance, or cultivation."
            )
    return normalized


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _write_text_if_missing(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(content, encoding="utf-8")


def _split_genre_keys(genre: str) -> list[str]:
    raw = (genre or "").strip()
    if not raw:
        return []
    # Support composite genres with plus signs and legacy localized separators.
    raw = re.sub(r"[＋/、,，|]", "+", raw)
    parts = [p.strip() for p in raw.split("+") if p.strip()]
    return parts or [raw]


def _normalize_genre_key(key: str) -> str:
    stems = resolve_template_stems(key)
    return stems[0] if stems else key





def _apply_label_replacements(text: str, replacements: Dict[str, str]) -> str:
    if not text or not replacements:
        return text
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        for label, value in replacements.items():
            if not value:
                continue
            labels = (label,)
            for candidate in labels:
                for punctuation in (":", "："):
                    prefix = f"- {candidate}{punctuation}"
                    if stripped.startswith(prefix):
                        leading = line[: len(line) - len(stripped)]
                        lines[i] = f"{leading}{prefix} {value}"
    return "\n".join(lines)


def _parse_tier_map(raw: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    if not raw:
        return result
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            key, val = part.split(":", 1)
            result[key.strip()] = val.strip()
    return result


def _needs_protagonist_group(protagonist_structure: str) -> bool:
    text = (protagonist_structure or "").strip().lower()
    return any(marker in text for marker in ("protagonist-team", "dual", "ensemble", "multiple", "multi-protagonist"))


def _needs_heroine_card(heroine_config: str, heroine_names: str) -> bool:
    text = (heroine_config or "").strip().lower()
    if text in {"none", "no heroine"}:
        return False
    return bool((heroine_names or "").strip() or text)


def _render_team_rows(names: List[str], roles: List[str]) -> List[str]:
    rows = []
    for idx, name in enumerate(names):
        role = roles[idx] if idx < len(roles) else ""
        rows.append(f"| {name} | {role or 'Main plot/subplot'} | | | |")
    return rows


def _ensure_state_schema(state: Dict[str, Any]) -> Dict[str, Any]:
    'Ensure state.json contains the v5.1 schema fields retained in v5.4.\n\nSince v5.1, entities_v3 and alias_index live in index.db; structured_relationships lives in its relationships table. Keep state.json compact (under 5 KB).'
    state.setdefault("project_info", {})
    state.setdefault("progress", {})
    state.setdefault("protagonist_state", {})
    state.setdefault("relationships", {})  # update_state.py requires this field.
    state.setdefault("disambiguation_warnings", [])
    state.setdefault("disambiguation_pending", [])
    state.setdefault("world_settings", {"power_system": [], "factions": [], "locations": []})
    state.setdefault("plot_threads", {"active_threads": [], "foreshadowing": []})
    state.setdefault("review_checkpoints", [])
    state.setdefault("chapter_meta", {})
    state.setdefault(
        "strand_tracker",
        {
            "last_quest_chapter": 0,
            "last_fire_chapter": 0,
            "last_constellation_chapter": 0,
            "current_dominant": "quest",
            "chapters_since_switch": 0,
            "history": [],
        },
    )
    # v5.1: entities_v3, alias_index, and structured_relationships moved to index.db.
    # Do not initialize those fields in state.json anymore.

    # progress schema evolution
    state["progress"].setdefault("current_chapter", 0)
    state["progress"].setdefault("total_words", 0)
    state["progress"].setdefault("last_updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    state["progress"].setdefault("volumes_completed", [])
    state["progress"].setdefault("current_volume", 1)
    state["progress"].setdefault("volumes_planned", [])

    # protagonist schema evolution
    ps = state["protagonist_state"]
    ps.setdefault("Name", "")
    ps.setdefault("power", {"realm": "", "layer": 1, "bottleneck": ""})
    ps.setdefault("location", {"current": "", "last_chapter": 0})
    ps.setdefault("golden_finger", {"Name": "", "level": 1, "cooldown": 0, "skills": []})
    ps.setdefault("attributes", {})

    return state


def _build_master_outline(target_chapters: int, *, chapters_per_volume: int = 50) -> str:
    volumes = (target_chapters - 1) // chapters_per_volume + 1 if target_chapters > 0 else 1
    lines: list[str] = [
        "# Master Outline",
        "",
        "> This master-outline scaffold is expanded into volume and chapter outlines by /webnovel-plan.",
        "",
        "## Volume Structure",
        "",
    ]

    for v in range(1, volumes + 1):
        start = (v - 1) * chapters_per_volume + 1
        end = min(v * chapters_per_volume, target_chapters)
        lines.extend(
            [
                f"### Volume {v} (Chapters {start}-{end})",
                "- Central conflict:",
                "- Key payoffs:",
                "- End-of-volume climax:",
                "- Main characters:",
                "- Key foreshadowing (setup/payoff):",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _inject_volume_rows(template_text: str, target_chapters: int, *, chapters_per_volume: int = 50) -> str:
    'Insert only the first volume into the master outline; later volumes are written back after planning.'
    lines = template_text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith(("| Volume number",)):
            header_idx = i
            break
    if header_idx is None:
        return template_text

    insert_idx = header_idx + 2 if header_idx + 1 < len(lines) else len(lines)
    end = min(chapters_per_volume, target_chapters) if target_chapters > 0 else chapters_per_volume
    rows = [f"| 1 | | Chapters 1-{end} | | |"]
    # Replace the first-volume placeholder rather than adding a duplicate row.
    lines = [line for i, line in enumerate(lines) if not (i >= insert_idx and re.match(r"^\|\s*1\s*\|\s*\|\s*\|", line))]

    # Avoid duplicate insertion if the template already has data rows.
    existing = {line.strip() for line in lines}
    rows = [r for r in rows if r.strip() not in existing]
    return "\n".join(lines[:insert_idx] + rows + lines[insert_idx:])


def init_project(
    project_dir: str,
    title: str,
    genre: str,
    *,
    protagonist_name: str = "",
    target_words: int = 2_000_000,
    target_chapters: int = 600,
    golden_finger_name: str = "",
    golden_finger_type: str = "",
    golden_finger_style: str = "",
    core_selling_points: str = "",
    protagonist_structure: str = "",
    heroine_config: str = "",
    heroine_names: str = "",
    heroine_role: str = "",
    co_protagonists: str = "",
    co_protagonist_roles: str = "",
    antagonist_tiers: str = "",
    world_scale: str = "",
    factions: str = "",
    power_system_type: str = "",
    social_class: str = "",
    resource_distribution: str = "",
    gf_visibility: str = "",
    gf_irreversible_cost: str = "",
    protagonist_desire: str = "",
    protagonist_flaw: str = "",
    protagonist_archetype: str = "",
    antagonist_level: str = "",
    target_reader: str = "",
    platform: str = "",
    currency_system: str = "",
    currency_exchange: str = "",
    sect_hierarchy: str = "",
    cultivation_chain: str = "",
    cultivation_subtiers: str = "",
) -> None:
    project_path = Path(project_dir).expanduser().resolve()
    if ".claude" in project_path.parts:
        raise SystemExit("Refusing to initialize a project inside .claude. Choose a different directory.")
    genre = _validate_initial_genre_source(genre)
    genre_resolution = resolve_genre_input(genre)
    canonical_genre = genre_resolution.canonical_genre or genre
    project_path.mkdir(parents=True, exist_ok=True)

    # Directory layout supports volume subdirectories and future expansion.
    directories = [
        ".webnovel/backups",
        ".webnovel/archive",
        ".webnovel/summaries",
        "settings",
        "outlines",
        "chapters",
        "reviews",
    ]
    for dir_path in directories:
        resolve_project_path(project_path, dir_path).mkdir(parents=True, exist_ok=True)

    # Create state.json or fill in missing fields incrementally.
    state_path = project_path / ".webnovel" / "state.json"
    if state_path.exists():
        try:
            state: Dict[str, Any] = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            corrupt_path = state_path.with_name(f"state.corrupt_{timestamp}.json")
            shutil.copy2(state_path, corrupt_path)
            print(f"Warning: damaged state.json was saved to {corrupt_path} for manual recovery")
            state = {}
    else:
        state = {}

    state = _ensure_state_schema(state)
    created_at = state.get("project_info", {}).get("created_at") or datetime.now().strftime("%Y-%m-%d")

    state["project_info"].update(
        {
            "title": title,
            "genre": canonical_genre,
            "genre_label": genre,
            "genre_tags": {
                "route": genre_resolution.route_tags,
                "trope": genre_resolution.trope_tags,
                "format": genre_resolution.format_tags,
                "templates": [Path(name).stem for name in genre_resolution.template_files],
            },
            "created_at": created_at,
            "target_words": int(target_words),
            "target_chapters": int(target_chapters),
            # The following initialization metadata does not affect runtime scripts.
            "golden_finger_name": golden_finger_name,
            "golden_finger_type": golden_finger_type,
            "golden_finger_style": golden_finger_style,
            "core_selling_points": core_selling_points,
            "protagonist_structure": protagonist_structure,
            "heroine_config": heroine_config,
            "heroine_names": heroine_names,
            "heroine_role": heroine_role,
            "co_protagonists": co_protagonists,
            "co_protagonist_roles": co_protagonist_roles,
            "antagonist_tiers": antagonist_tiers,
            "world_scale": world_scale,
            "factions": factions,
            "power_system_type": power_system_type,
            "social_class": social_class,
            "resource_distribution": resource_distribution,
            "gf_visibility": gf_visibility,
            "gf_irreversible_cost": gf_irreversible_cost,
            "target_reader": target_reader,
            "platform": platform,
            "currency_system": currency_system,
            "currency_exchange": currency_exchange,
            "sect_hierarchy": sect_hierarchy,
            "cultivation_chain": cultivation_chain,
            "cultivation_subtiers": cultivation_subtiers,
        }
    )

    if protagonist_name:
        state["protagonist_state"]["Name"] = protagonist_name

    gf_type_norm = (golden_finger_type or "").strip()
    if gf_type_norm in {"none", "no special advantage"}:
        state["protagonist_state"]["golden_finger"]["Name"] = "None"
        state["protagonist_state"]["golden_finger"]["level"] = 0
        state["protagonist_state"]["golden_finger"]["cooldown"] = 0
    elif golden_finger_name:
        state["protagonist_state"]["golden_finger"]["Name"] = golden_finger_name

    # Ensure golden_finger exists and remains editable.
    if not state["protagonist_state"]["golden_finger"].get("Name"):
        state["protagonist_state"]["golden_finger"]["Name"] = "Unnamed special advantage"

    state["progress"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    # Write atomically; initialization needs no backup of an old file.
    atomic_write_json(state_path, state, use_lock=True, backup=False)

    # Read bundled templates if available.
    script_dir = Path(__file__).resolve().parent
    templates_dir = script_dir.parent / "templates"
    output_templates_dir = templates_dir / "output"
    genre_key = (genre or "").strip()
    template_files = list(genre_resolution.template_files)
    if not template_files:
        template_files = [f"{_normalize_genre_key(k)}.md" for k in _split_genre_keys(genre_key)]
    genre_templates = []
    seen = set()
    for template_file in template_files:
        if not template_file or template_file in seen:
            continue
        seen.add(template_file)
        template_text = _read_text_if_exists(templates_dir / "genres" / template_file)
        if template_text:
            genre_templates.append(template_text.strip())
    genre_template = "\n\n---\n\n".join(genre_templates)
    output_worldview = _read_text_if_exists(output_templates_dir / "settings-worldbuilding.md")
    output_power = _read_text_if_exists(output_templates_dir / "settings-power-system.md")
    output_protagonist = _read_text_if_exists(output_templates_dir / "settings-protagonist.md")
    output_heroine = _read_text_if_exists(output_templates_dir / "settings-heroine.md")
    output_team = _read_text_if_exists(output_templates_dir / "settings-protagonist-team.md")
    output_outline = _read_text_if_exists(output_templates_dir / "outlines-master-outline.md")
    output_antagonist = _read_text_if_exists(output_templates_dir / "settings-antagonist.md")

    # Generate base files only if absent, preserving existing content.
    now = datetime.now().strftime("%Y-%m-%d")

    worldview_content = output_worldview.strip() if output_worldview else ""
    if not worldview_content:
        worldview_content = "\n".join(
            [
                "# Worldbuilding",
                "",
                f"> Project: {title} | Genre: {genre} | Created: {now}",
                "",
                "## World in One Sentence",
                "- Describe the world's core rules and appeal in one sentence.",
                "",
                "## Core Rules (Settings Are Physical Laws)",
                "- Rule 1:",
                "- Rule 2:",
                "- Rule 3:",
                "",
                "## Factions and Geography",
                "- Major factions:",
                "- Key locations:",
                "",
                "## Genre Reference Template (Editable/Optional)",
                "",
                (genre_template.strip() + "\n") if genre_template else "No genre template found; add your own reference.\n",
            ]
        ).rstrip() + "\n"
    else:
        worldview_content = _apply_label_replacements(
            worldview_content,
            {
                "Number of continents/planes": world_scale,
                "Major factions": factions,
                "Social classes": social_class,
                "Resource allocation rules": resource_distribution,
                "Sect/organization hierarchy": sect_hierarchy,
                "Currency system": currency_system,
                "Exchange rules": currency_exchange,
            },
        )
        if genre_template:
            worldview_content = (
                worldview_content.rstrip()
                + "\n\n## Genre Reference Template (Editable/Optional)\n\n"
                + genre_template.strip()
                + "\n"
            )
    _write_text_if_missing(
        resolve_project_path(project_path, "settings/worldbuilding.md"),
        worldview_content,
    )

    power_content = output_power.strip() if output_power else ""
    if not power_content:
        power_content = "\n".join(
            [
                "# Power System",
                "",
                f"> Project: {title} | Genre: {genre} | Created: {now}",
                "",
                "## Levels and Realms",
                "- List levels from weakest to strongest, including advancement requirements and costs.",
                "",
                "## Ability Rules",
                "- Acquisition:",
                "- Costs and side effects:",
                "- Advancement and combinations:",
                "",
                "## Limitations",
                "- Higher-level abilities require the corresponding level.",
                "- New abilities must be declared and recorded.",
                "",
            ]
        ).rstrip() + "\n"
    else:
        power_content = _apply_label_replacements(
            power_content,
            {
                "System type": power_system_type,
                "Typical realm progression (optional)": cultivation_chain,
                "Sub-realm stages": cultivation_subtiers,
            },
        )
    _write_text_if_missing(
        resolve_project_path(project_path, "settings/power-system.md"),
        power_content,
    )

    protagonist_content = output_protagonist.strip() if output_protagonist else ""
    if not protagonist_content:
        protagonist_content = "\n".join(
            [
                "# Protagonist Profile",
                "",
                f"> Protagonist: {protagonist_name or 'To be filled'} | Project: {title} | Created: {now}",
                "",
                "## Three Core Elements",
                f"- Desire: {protagonist_desire or 'To be filled'}",
                f"- Flaw: {protagonist_flaw or 'To be filled'}",
                f"- Archetype: {protagonist_archetype or 'To be filled'}",
                "",
                "## Initial State",
                "- Identity:",
                "- Resources:",
                "- Constraints:",
                "",
                "## Special Advantage",
                f"- Name: {golden_finger_name or 'To be filled'}",
                f"- Type: {golden_finger_type or 'To be filled'}",
                f"- Style: {golden_finger_style or 'To be filled'}",
                "- Growth curve:",
                "",
            ]
        ).rstrip() + "\n"
    else:
        protagonist_content = _apply_label_replacements(
            protagonist_content,
            {
                "Name": protagonist_name,
                "True desire (possibly unconscious)": protagonist_desire,
                "Personality flaws": protagonist_flaw,
            },
        )
    _write_text_if_missing(
        resolve_project_path(project_path, "settings/protagonist.md"),
        protagonist_content,
    )

    heroine_content = output_heroine.strip() if output_heroine else ""
    if heroine_content and _needs_heroine_card(heroine_config, heroine_names):
        heroine_content = _apply_label_replacements(
            heroine_content,
            {
                "Name": heroine_names,
                "Relationship to the protagonist (opponent/ally/co-conspirator/check on their actions)": heroine_role,
            },
        )
        _write_text_if_missing(resolve_project_path(project_path, "settings/heroine.md"), heroine_content)

    team_content = output_team.strip() if output_team else ""
    if team_content and _needs_protagonist_group(protagonist_structure):
        names = [n.strip() for n in co_protagonists.split(",") if n.strip()] if co_protagonists else []
        roles = [r.strip() for r in co_protagonist_roles.split(",") if r.strip()] if co_protagonist_roles else []
        if names:
            lines = team_content.splitlines()
            new_rows = _render_team_rows(names, roles)
            replaced = False
            out_lines: List[str] = []
            for line in lines:
                if line.strip().startswith(("| protagonistA", "| Protagonist A")):
                    out_lines.extend(new_rows)
                    replaced = True
                    continue
                if replaced and line.strip().startswith(("| protagonist", "| Protagonist ")):
                    continue
                out_lines.append(line)
            team_content = "\n".join(out_lines)
        _write_text_if_missing(
            resolve_project_path(project_path, "settings/protagonist-team.md"),
            team_content,
        )

    antagonist_content = output_antagonist.strip() if output_antagonist else ""
    if not antagonist_content:
        antagonist_content = "\n".join(
            [
                "# Antagonist Design",
                "",
                f"> Project: {title} | Created: {now}",
                "",
                f"- Antagonist tier: {antagonist_level or 'To be filled'}",
                "- Motivation:",
                "- Resources/factions:",
                "- Mirror relationship with protagonist:",
                "- Final fate:",
                "",
            ]
        ).rstrip() + "\n"
    else:
        tier_map = _parse_tier_map(antagonist_tiers)
        if tier_map:
            lines = antagonist_content.splitlines()
            out_lines = []
            for line in lines:
                if line.strip().startswith(("| minor", "| Minor antagonist")):
                    name = tier_map.get("Minor antagonist", tier_map.get("minor antagonist", tier_map.get("minor", "")))
                    out_lines.append(f"| Minor antagonist | {name} | Early stage | | |")
                    continue
                if line.strip().startswith(("| major", "| Mid-level antagonist")):
                    name = tier_map.get("Mid-level antagonist", tier_map.get("mid-level antagonist", tier_map.get("major", "")))
                    out_lines.append(f"| Mid-level antagonist | {name} | Middle stage | | |")
                    continue
                if line.strip().startswith(("| main", "| Major antagonist")):
                    name = tier_map.get("Major antagonist", tier_map.get("major antagonist", tier_map.get("main", "")))
                    out_lines.append(f"| Major antagonist | {name} | Late stage | | |")
                    continue
                out_lines.append(line)
            antagonist_content = "\n".join(out_lines)
    _write_text_if_missing(resolve_project_path(project_path, "settings/antagonist.md"), antagonist_content)

    outline_content = output_outline.strip() if output_outline else ""
    if outline_content:
        outline_content = _inject_volume_rows(outline_content, int(target_chapters)).rstrip() + "\n"
    else:
        outline_content = _build_master_outline(int(target_chapters))
    _write_text_if_missing(resolve_project_path(project_path, "outlines/master-outline.md"), outline_content)

    # Generate an environment template without real secrets.
    _write_text_if_missing(
        project_path / ".env.example",
        "\n".join(
            [
                "# Webnovel Writer example configuration (copy to .env and fill in)",
                "# Never commit .env files containing real API keys.",
                "",
                "# Embedding",
                "EMBED_BASE_URL=https://api-inference.modelscope.cn/v1",
                "EMBED_MODEL=Qwen/Qwen3-Embedding-8B",
                "EMBED_API_KEY=",
                "",
                "# Rerank",
                "RERANK_BASE_URL=https://api.jina.ai/v1",
                "RERANK_MODEL=jina-reranker-v3",
                "RERANK_API_KEY=",
                "",
            ]
        )
        + "\n",
    )

    # Initialize Git only when available and no .git exists in the project directory.
    git_dir = project_path / ".git"
    if not git_dir.exists():
        if not is_git_available():
            print("\nWarning: Git is unavailable; skipping version control initialization")
            print("Install Git to enable version control: https://git-scm.com/")
        else:
            print("\nInitializing Git repository...")
            try:
                subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True, text=True)

                gitignore_file = project_path / ".gitignore"
                if not gitignore_file.exists():
                    gitignore_file.write_text(
                        """# Python
__pycache__/
*.py[cod]
*.so

# Env (keep .env.example)
.env
.env.*
!.env.example

# Temporary files
*.tmp
*.bak
.DS_Store

# IDE
.vscode/
.idea/

# Don't ignore .webnovel (we need to track state.json)
# But ignore cache files
.webnovel/context_cache.json
.webnovel/*.lock
.webnovel/*.bak
""",
                        encoding="utf-8",
                    )

                subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
                # Security fix: sanitize title against command injection.
                safe_title = sanitize_commit_message(title)
                subprocess.run(
                    ["git", "commit", "-m", f"Initialize webnovel project: {safe_title}"],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                )
                print("Git initialized.")
            except subprocess.CalledProcessError as e:
                print(f"Git init failed (non-fatal): {e}")

    # Record the workspace's default project pointer without blocking execution.
    try:
        pointer_file = write_current_project_pointer(project_path)
        if pointer_file is not None:
            print(f"Default project pointer updated: {pointer_file}")
    except Exception as e:
        print(f"Default project pointer update failed (non-fatal): {e}")

    print(f"\nProject initialized at: {project_path}")
    print("Key files:")
    print(" - .webnovel/state.json")
    print(f" - {resolve_project_path(project_path, 'settings/worldbuilding.md').relative_to(project_path)}")
    print(f" - {resolve_project_path(project_path, 'settings/power-system.md').relative_to(project_path)}")
    print(f" - {resolve_project_path(project_path, 'settings/protagonist.md').relative_to(project_path)}")
    print(f" - {resolve_project_path(project_path, 'outlines/master-outline.md').relative_to(project_path)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a webnovel project, state.json, and templates")
    parser.add_argument("project_dir", help="Project directory (e.g. ./webnovel-project)")
    parser.add_argument("title", help="Novel title")
    parser.add_argument(
        "genre",
        help="Genre in English or Chinese; combine labels with + (e.g. fantasy+mystery)",
    )

    parser.add_argument("--protagonist-name", default="", help="Protagonist name")
    parser.add_argument("--target-words", type=int, default=2_000_000, help="Target word count (default: 2000000)")
    parser.add_argument("--target-chapters", type=int, default=600, help="Target chapters (default: 600)")

    parser.add_argument("--golden-finger-name", default="", help="Special advantage or system name")
    parser.add_argument("--golden-finger-type", default="", help="Special advantage type")
    parser.add_argument("--golden-finger-style", default="", help="Special advantage style")
    parser.add_argument("--core-selling-points", default="", help="Core selling points (comma separated)")
    parser.add_argument("--protagonist-structure", default="", help="Protagonist structure (single, dual, ensemble)")
    parser.add_argument("--heroine-config", default="", help="Female-lead configuration (none, single, multiple)")
    parser.add_argument("--heroine-names", default="", help="Female-lead names (comma separated)")
    parser.add_argument("--heroine-role", default="", help="Female-lead role")
    parser.add_argument("--co-protagonists", default="", help="Co-protagonist names (comma separated)")
    parser.add_argument("--co-protagonist-roles", default="", help="Co-protagonist roles (comma separated)")
    parser.add_argument("--antagonist-tiers", default="", help="Antagonist tiers (e.g. Minor antagonist:Alice;Major antagonist:Bob)")
    parser.add_argument("--world-scale", default="", help="World scale")
    parser.add_argument("--factions", default="", help="Major factions")
    parser.add_argument("--power-system-type", default="", help="Power-system type")
    parser.add_argument("--social-class", default="", help="Social classes")
    parser.add_argument("--resource-distribution", default="", help="Resource distribution")
    parser.add_argument("--gf-visibility", default="", help="Special advantage visibility")
    parser.add_argument("--gf-irreversible-cost", default="", help="Irreversible cost of special advantage")
    parser.add_argument("--currency-system", default="", help="Currency system")
    parser.add_argument("--currency-exchange", default="", help="Currency exchange and denominations")
    parser.add_argument("--sect-hierarchy", default="", help="Sect or organization hierarchy")
    parser.add_argument("--cultivation-chain", default="", help="Typical advancement progression")
    parser.add_argument("--cultivation-subtiers", default="", help="Sub-level stages")

    # Optional deep-mode arguments prefill templates.
    parser.add_argument("--protagonist-desire", default="", help="Protagonist core desire")
    parser.add_argument("--protagonist-flaw", default="", help="Protagonist personality flaw")
    parser.add_argument("--protagonist-archetype", default="", help="Protagonist archetype")
    parser.add_argument("--antagonist-level", default="", help="Antagonist tier")
    parser.add_argument("--target-reader", default="", help="Target reader")
    parser.add_argument("--platform", default="", help="Publishing platform")

    args = parser.parse_args()

    init_project(
        args.project_dir,
        args.title,
        args.genre,
        protagonist_name=args.protagonist_name,
        target_words=args.target_words,
        target_chapters=args.target_chapters,
        golden_finger_name=args.golden_finger_name,
        golden_finger_type=args.golden_finger_type,
        golden_finger_style=args.golden_finger_style,
        core_selling_points=args.core_selling_points,
        protagonist_structure=args.protagonist_structure,
        heroine_config=args.heroine_config,
        heroine_names=args.heroine_names,
        heroine_role=args.heroine_role,
        co_protagonists=args.co_protagonists,
        co_protagonist_roles=args.co_protagonist_roles,
        antagonist_tiers=args.antagonist_tiers,
        world_scale=args.world_scale,
        factions=args.factions,
        power_system_type=args.power_system_type,
        social_class=args.social_class,
        resource_distribution=args.resource_distribution,
        gf_visibility=args.gf_visibility,
        gf_irreversible_cost=args.gf_irreversible_cost,
        protagonist_desire=args.protagonist_desire,
        protagonist_flaw=args.protagonist_flaw,
        protagonist_archetype=args.protagonist_archetype,
        antagonist_level=args.antagonist_level,
        target_reader=args.target_reader,
        platform=args.platform,
        currency_system=args.currency_system,
        currency_exchange=args.currency_exchange,
        sect_hierarchy=args.sect_hierarchy,
        cultivation_chain=args.cultivation_chain,
        cultivation_subtiers=args.cultivation_subtiers,
    )


if __name__ == "__main__":
    main()
