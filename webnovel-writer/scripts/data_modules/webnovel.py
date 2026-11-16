#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
webnovel 统一入口（面向 skills / agents 的稳定 CLI）

设计目标：
- 只有一个入口命令，避免到处拼 `python -m data_modules.xxx ...` 导致参数位置/引号/路径炸裂。
- 自动解析正确的 book project_root（包含 `.webnovel/state.json` 的目录）。
- 所有写入类命令在解析到 project_root 后，统一前置 `--project-root` 传给具体模块。

典型用法（推荐，不依赖 PYTHONPATH / 不要求 cd）：
  python "<SCRIPTS_DIR>/webnovel.py" preflight
  python "<SCRIPTS_DIR>/webnovel.py" where
  python "<SCRIPTS_DIR>/webnovel.py" use "<PROJECT_ROOT>"
  python "<SCRIPTS_DIR>/webnovel.py" --project-root "<PROJECT_ROOT>" index stats
  python "<SCRIPTS_DIR>/webnovel.py" --project-root "<PROJECT_ROOT>" state process-chapter --chapter 100 --data @payload.json
  python "<SCRIPTS_DIR>/webnovel.py" --project-root "<PROJECT_ROOT>" extract-context --chapter 100 --format json

也支持（不推荐，容易踩 PYTHONPATH/cd/参数顺序坑）：
  python -m data_modules.webnovel where
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from runtime_compat import enable_windows_utf8_stdio, normalize_windows_path
from project_locator import resolve_project_root, write_current_project_pointer, update_global_registry_current_project

from .story_runtime_health import build_story_runtime_health


if sys.platform == "win32":
    enable_windows_utf8_stdio(skip_in_pytest=True)


def _scripts_dir() -> Path:
    # data_modules/webnovel.py -> data_modules -> scripts
    return Path(__file__).resolve().parent.parent


def _resolve_root(explicit_project_root: Optional[str]) -> Path:
    # 允许显式传入工作区根目录或书项目根目录
    raw = explicit_project_root
    if raw:
        return resolve_project_root(raw)
    return resolve_project_root()


def _strip_project_root_args(argv: list[str]) -> list[str]:
    """
    下游工具统一由本入口注入 `--project-root`，避免重复传参导致 argparse 报错/歧义。
    """
    out: list[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--project-root":
            i += 2
            continue
        if tok.startswith("--project-root="):
            i += 1
            continue
        out.append(tok)
        i += 1
    return out


PASSTHROUGH_TOOLS = {
    "index",
    "state",
    "rag",
    "style",
    "entity",
    "context",
    "memory",
    "migrate",
    "status",
    "update-state",
    "backup",
    "archive",
    "init",
    "story-system",
    "memory-contract",
    "project-memory",
}


def _passthrough_tail(argv: list[str], tool: str) -> list[str]:
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--project-root":
            i += 2
            continue
        if token.startswith("--project-root="):
            i += 1
            continue
        if token == tool:
            return list(argv[i + 1 :])
        i += 1
    return []


def _run_data_module(module: str, argv: list[str]) -> int:
    """
    Import `data_modules.<module>` and call its main(), while isolating sys.argv.
    """
    mod = importlib.import_module(f"data_modules.{module}")
    main = getattr(mod, "main", None)
    if not callable(main):
        raise RuntimeError(f"data_modules.{module} has no callable main()")

    old_argv = sys.argv
    try:
        sys.argv = [f"data_modules.{module}"] + argv
        try:
            main()
            return 0
        except SystemExit as e:
            return int(e.code or 0)
    finally:
        sys.argv = old_argv


def _run_script(script_name: str, argv: list[str]) -> int:
    """
    Run a script under `.claude/scripts/` via a subprocess.

    用途：兼容没有 main() 的脚本。
    """
    script_path = _scripts_dir() / script_name
    if not script_path.is_file():
        raise FileNotFoundError(f"Script not found: {script_path}")
    proc = subprocess.run([sys.executable, str(script_path), *argv])
    return int(proc.returncode or 0)


def cmd_where(args: argparse.Namespace) -> int:
    try:
        root = _resolve_root(args.project_root)
    except FileNotFoundError as exc:
        print(_project_root_diagnostic(args.project_root, exc), file=sys.stderr)
        return 1
    print(str(root))
    return 0


def _project_root_diagnostic(
    explicit_project_root: Optional[str], exc: FileNotFoundError
) -> str:
    if explicit_project_root:
        return (
            "Valid book project root not found (requires .webnovel/state.json): "
            f"{explicit_project_root}\n"
            f"detail: {exc}"
        )
    return (
        "No active book project in this workspace (.webnovel/state.json not found).\n"
        "Run webnovel init to create a project, or webnovel use <project_root> to select an existing project.\n"
        f"detail: {exc}"
    )


def _build_preflight_report(explicit_project_root: Optional[str]) -> dict:
    scripts_dir = _scripts_dir().resolve()
    plugin_root = scripts_dir.parent
    skill_root = plugin_root / "skills" / "webnovel-write"
    entry_script = scripts_dir / "webnovel.py"
    extract_script = scripts_dir / "extract_chapter_context.py"

    checks: list[dict[str, object]] = [
        {"name": "scripts_dir", "ok": scripts_dir.is_dir(), "path": str(scripts_dir)},
        {"name": "entry_script", "ok": entry_script.is_file(), "path": str(entry_script)},
        {"name": "extract_context_script", "ok": extract_script.is_file(), "path": str(extract_script)},
        {"name": "skill_root", "ok": skill_root.is_dir(), "path": str(skill_root)},
    ]

    project_root = ""
    project_root_error = ""
    story_runtime: dict = {}
    try:
        resolved_root = _resolve_root(explicit_project_root)
        project_root = str(resolved_root)
        checks.append({"name": "project_root", "ok": True, "path": project_root})
        story_runtime = build_story_runtime_health(resolved_root)
    except FileNotFoundError as exc:
        project_root_error = _project_root_diagnostic(explicit_project_root, exc)
        checks.append(
            {
                "name": "project_root",
                "ok": False,
                "path": explicit_project_root or "",
                "error": project_root_error,
            }
        )
    except Exception as exc:
        project_root_error = str(exc)
        checks.append({"name": "project_root", "ok": False, "path": explicit_project_root or "", "error": project_root_error})

    return {
        "ok": all(bool(item["ok"]) for item in checks),
        "project_root": project_root,
        "scripts_dir": str(scripts_dir),
        "skill_root": str(skill_root),
        "checks": checks,
        "project_root_error": project_root_error,
        "story_runtime": story_runtime,
    }


def cmd_preflight(args: argparse.Namespace) -> int:
    report = _build_preflight_report(args.project_root)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report["checks"]:
            status = "OK" if item["ok"] else "ERROR"
            path = item.get("path") or ""
            print(f"{status} {item['name']}: {path}")
            if item.get("error"):
                print(f"  detail: {item['error']}")
        story_runtime = report.get("story_runtime") or {}
        if story_runtime:
            print(
                "INFO story_runtime: "
                f"chapter={story_runtime.get('chapter')} "
                f"mainline_ready={story_runtime.get('mainline_ready')} "
                f"latest_commit_status={story_runtime.get('latest_commit_status')}"
            )
    return 0 if report["ok"] else 1


def cmd_project_status(args: argparse.Namespace) -> int:
    from .project_status import build_project_status, format_project_status

    try:
        root: Path | str | None = _resolve_root(args.project_root)
    except FileNotFoundError:
        root = args.project_root or None
    report = build_project_status(root, chapter=args.chapter)
    print(format_project_status(report, args.format))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    from .doctor import build_doctor_report, format_doctor_report

    preflight_report = _build_preflight_report(args.project_root)
    root: Path | str | None = preflight_report.get("project_root") or args.project_root or None
    report = build_doctor_report(
        root,
        chapter=args.chapter,
        deep=bool(args.deep),
        preflight_report=preflight_report,
    )
    print(format_doctor_report(report, args.format))
    return 0 if report.get("ok") else 1


def cmd_write_gate(args: argparse.Namespace) -> int:
    from .write_gates import format_gate_report, run_write_gate

    root = _resolve_root(args.project_root)
    report = run_write_gate(root, chapter=args.chapter, stage=args.stage)
    print(format_gate_report(report, args.format))
    return 0 if report.get("ok") else 1


def cmd_projections(args: argparse.Namespace) -> int:
    from .projections import format_projection_report, replay_projections, retry_projection

    root = _resolve_root(args.project_root)
    if args.projection_action == "retry":
        report = retry_projection(root, chapter=args.chapter)
    else:
        report = replay_projections(
            root,
            start_chapter=args.from_chapter,
            end_chapter=args.to_chapter,
        )
    print(format_projection_report(report, args.format))
    return 0 if report.get("ok") else 1


def cmd_user_report(args: argparse.Namespace) -> int:
    from .user_report import build_user_report, format_user_report

    root = _resolve_root(args.project_root)
    report = build_user_report(
        root,
        stage=args.stage,
        chapter=args.chapter,
        volume=args.volume,
    )
    print(format_user_report(report, args.format))
    return 0


def cmd_run_ledger(args: argparse.Namespace) -> int:
    from .run_ledger import (
        build_write_resume_plan,
        format_resume_plan,
        record_write_step,
    )

    root = _resolve_root(args.project_root)
    if args.ledger_action == "record-write-step":
        try:
            inputs = json.loads(args.inputs_json)
            outputs = json.loads(args.outputs_json)
            problems = json.loads(args.problems_json)
            auto_handled = json.loads(args.auto_handled_json)
        except json.JSONDecodeError as exc:
            print(f"Invalid ledger JSON argument: {exc}", file=sys.stderr)
            return 2
        if not isinstance(inputs, dict) or not isinstance(outputs, dict):
            print("inputs-json / outputs-json must be a JSON object", file=sys.stderr)
            return 2
        if not isinstance(problems, list) or not isinstance(auto_handled, list):
            print("problems-json / auto-handled-json must be a JSON list", file=sys.stderr)
            return 2
        entry = record_write_step(
            root,
            chapter=args.chapter,
            step=args.step,
            status=args.status,
            mode=args.mode,
            inputs={str(key): str(value) for key, value in inputs.items()},
            outputs={str(key): str(value) for key, value in outputs.items()},
            problems=[str(item) for item in problems],
            auto_handled=[str(item) for item in auto_handled],
            duration_ms=args.duration_ms,
        )
        if args.format == "json":
            print(json.dumps(entry, ensure_ascii=False, indent=2))
        else:
            print(f"{entry['step']}: {entry['status']}")
        return 0
    if args.ledger_action == "write-resume":
        report = build_write_resume_plan(
            root,
            chapter=args.chapter,
            mode=args.mode,
        )
        print(format_resume_plan(report, args.format))
        return 0
    return 2


def cmd_run_log(args: argparse.Namespace) -> int:
    from .run_logger import write_run_log

    try:
        root = _resolve_root(args.project_root)
    except FileNotFoundError:
        root = normalize_windows_path(args.project_root).expanduser()
        try:
            root = root.resolve()
        except Exception:
            root = root
    try:
        payload = json.loads(args.payload_json)
    except json.JSONDecodeError as exc:
        print(f"payload-json is not valid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("payload-json must be a JSON object", file=sys.stderr)
        return 2
    result = write_run_log(root, event=args.event, payload=payload, append=args.append)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["path"])
    return 0


def cmd_use(args: argparse.Namespace) -> int:
    project_root = normalize_windows_path(args.project_root).expanduser()
    try:
        project_root = project_root.resolve()
    except Exception as exc:
        import sys
        print(f"⚠️ path.resolve() failed ({project_root}): {exc}", file=sys.stderr)
        project_root = project_root

    workspace_root: Optional[Path] = None
    if args.workspace_root:
        workspace_root = normalize_windows_path(args.workspace_root).expanduser()
        try:
            workspace_root = workspace_root.resolve()
        except Exception as exc:
            import sys
            print(f"⚠️ path.resolve() failed ({workspace_root}): {exc}", file=sys.stderr)
            workspace_root = workspace_root

    # 1) 写入工作区指针（若工作区内存在 `.claude/`）
    pointer_file = write_current_project_pointer(project_root, workspace_root=workspace_root)
    if pointer_file is not None:
        print(f"workspace pointer: {pointer_file}")
    else:
        print("workspace pointer: (skipped)")

    # 2) 写入用户级 registry（保证全局安装/空上下文可恢复）
    reg_path = update_global_registry_current_project(workspace_root=workspace_root, project_root=project_root)
    if reg_path is not None:
        print(f"global registry: {reg_path}")
    else:
        print("global registry: (skipped)")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="webnovel unified CLI")
    parser.add_argument("--project-root", help="Book or workspace root (optional; auto-detected by default)")

    sub = parser.add_subparsers(dest="tool", required=True)

    p_where = sub.add_parser("where", help="Print the resolved project_root")
    p_where.set_defaults(func=cmd_where)

    p_preflight = sub.add_parser("preflight", help="Validate the unified CLI environment and project_root")
    p_preflight.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_preflight.set_defaults(func=cmd_preflight)

    p_project_status = sub.add_parser("project-status", help="Print a compact machine-readable project status")
    p_project_status.add_argument("--chapter", type=int, default=None, help="Target chapter number")
    p_project_status.add_argument("--format", choices=["summary", "json"], default="summary", help="Output format")
    p_project_status.set_defaults(func=cmd_project_status)

    p_doctor = sub.add_parser("doctor", help="Stage-aware read-only project health check")
    p_doctor.add_argument("--chapter", type=int, default=None, help="Target chapter number")
    p_doctor.add_argument("--deep", action="store_true", help="Include deeper checks such as the dashboard")
    p_doctor.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_doctor.set_defaults(func=cmd_doctor)

    p_write_gate = sub.add_parser("write-gate", help="Validate chapter-writing boundaries")
    p_write_gate.add_argument("--chapter", type=int, required=True, help="Target chapter number")
    p_write_gate.add_argument("--stage", choices=["prewrite", "precommit", "postcommit"], required=True, help="Validation stage")
    p_write_gate.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    p_write_gate.set_defaults(func=cmd_write_gate)

    p_projections = sub.add_parser("projections", help="Retry or replay projections from existing commits")
    projections_sub = p_projections.add_subparsers(dest="projection_action", required=True)
    p_projection_retry = projections_sub.add_parser("retry", help="Retry a single chapter projection")
    p_projection_retry.add_argument("--chapter", type=int, required=True, help="Target chapter number")
    p_projection_retry.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    p_projection_retry.set_defaults(func=cmd_projections)
    p_projection_replay = projections_sub.add_parser("replay", help="Replay projections over a chapter range")
    p_projection_replay.add_argument("--from-chapter", type=int, required=True, help="Starting chapter number")
    p_projection_replay.add_argument("--to-chapter", type=int, required=True, help="Ending chapter number")
    p_projection_replay.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    p_projection_replay.set_defaults(func=cmd_projections)

    p_user_report = sub.add_parser("user-report", help="Render an author-friendly final report")
    p_user_report.add_argument("--stage", choices=["init", "plan", "write", "review"], required=True, help="Report stage")
    p_user_report.add_argument("--chapter", type=int, default=None, help="Target chapter number")
    p_user_report.add_argument("--volume", type=int, default=None, help="Target volume number")
    p_user_report.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_user_report.set_defaults(func=cmd_user_report)

    p_run_ledger = sub.add_parser("run-ledger", help="Record or query chapter-writing resume state")
    run_ledger_sub = p_run_ledger.add_subparsers(dest="ledger_action", required=True)
    p_record_write_step = run_ledger_sub.add_parser("record-write-step", help="Record chapter-writing step status")
    p_record_write_step.add_argument("--chapter", type=int, required=True, help="Target chapter number")
    p_record_write_step.add_argument("--step", choices=["draft", "review", "data", "commit", "projection", "backup"], required=True)
    p_record_write_step.add_argument("--status", required=True)
    p_record_write_step.add_argument("--mode", default="default")
    p_record_write_step.add_argument("--inputs-json", default="{}")
    p_record_write_step.add_argument("--outputs-json", default="{}")
    p_record_write_step.add_argument("--problems-json", default="[]")
    p_record_write_step.add_argument("--auto-handled-json", default="[]")
    p_record_write_step.add_argument("--duration-ms", type=int, default=0)
    p_record_write_step.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    p_record_write_step.set_defaults(func=cmd_run_ledger)
    p_write_resume = run_ledger_sub.add_parser("write-resume", help="Print chapter-writing resume guidance")
    p_write_resume.add_argument("--chapter", type=int, required=True, help="Target chapter number")
    p_write_resume.add_argument("--mode", default="default", help="Writing mode")
    p_write_resume.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    p_write_resume.set_defaults(func=cmd_run_ledger)

    p_run_log = sub.add_parser("run-log", help="Write a redacted run log")
    p_run_log.add_argument("--event", required=True, help="Event name")
    p_run_log.add_argument("--payload-json", default="{}", help="JSON object to write to the log")
    p_run_log.add_argument("--append", action="store_true", help="Append to run_last.log instead of replacing it")
    p_run_log.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    p_run_log.set_defaults(func=cmd_run_log)

    p_use = sub.add_parser("use", help="Bind this workspace to a book project (write pointer/registry)")
    p_use.add_argument("project_root", help="Book root (must contain .webnovel/state.json)")
    p_use.add_argument("--workspace-root", help="Workspace root (optional; inferred from the environment)")
    p_use.set_defaults(func=cmd_use)

    # Pass-through to data modules
    p_index = sub.add_parser("index", help="Forward to index_manager")
    p_index.add_argument("args", nargs=argparse.REMAINDER)

    p_state = sub.add_parser("state", help="Forward to state_manager")
    p_state.add_argument("args", nargs=argparse.REMAINDER)

    p_rag = sub.add_parser("rag", help="Forward to rag_adapter")
    p_rag.add_argument("args", nargs=argparse.REMAINDER)

    p_style = sub.add_parser("style", help="Forward to style_sampler")
    p_style.add_argument("args", nargs=argparse.REMAINDER)

    p_entity = sub.add_parser("entity", help="Forward to entity_linker")
    p_entity.add_argument("args", nargs=argparse.REMAINDER)

    p_context = sub.add_parser("context", help="Forward to context_manager")
    p_context.add_argument("args", nargs=argparse.REMAINDER)

    p_memory = sub.add_parser("memory", help="Forward to memory.store")
    p_memory.add_argument("args", nargs=argparse.REMAINDER)

    p_migrate = sub.add_parser("migrate", help="Forward to migrate_state_to_sqlite")
    p_migrate.add_argument("args", nargs=argparse.REMAINDER)

    # Pass-through to scripts
    p_status = sub.add_parser("status", help="Forward to status_reporter.py")
    p_status.add_argument("args", nargs=argparse.REMAINDER)

    p_update_state = sub.add_parser("update-state", help="Forward to update_state.py")
    p_update_state.add_argument("args", nargs=argparse.REMAINDER)

    p_backup = sub.add_parser("backup", help="Forward to backup_manager.py")
    p_backup.add_argument("args", nargs=argparse.REMAINDER)

    p_archive = sub.add_parser("archive", help="Forward to archive_manager.py")
    p_archive.add_argument("args", nargs=argparse.REMAINDER)

    p_init = sub.add_parser("init", help="Forward to init_project.py (initialize project)")
    p_init.add_argument("args", nargs=argparse.REMAINDER)

    p_extract_context = sub.add_parser("extract-context", help="Forward to extract_chapter_context.py")
    p_extract_context.add_argument("--chapter", type=int, required=True, help="Target chapter number")
    p_extract_context.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    p_story_system = sub.add_parser("story-system", help="Forward to story_system.py")
    p_story_system.add_argument("args", nargs=argparse.REMAINDER)

    p_story_events = sub.add_parser("story-events", help="Forward to story_events.py")
    p_story_events.add_argument("--chapter", type=int, default=0, help="Target chapter number")
    p_story_events.add_argument("--limit", type=int, default=200, help="Result limit")
    p_story_events.add_argument("--health", action="store_true", help="Print event-chain health information")

    p_commit = sub.add_parser("chapter-commit", help="Forward to chapter_commit.py")
    p_commit.add_argument("--chapter", type=int, required=True, help="Target chapter number")
    p_commit.add_argument("--review-result", default="", help="review_result JSON file")
    p_commit.add_argument("--fulfillment-result", default="", help="fulfillment_result JSON file")
    p_commit.add_argument("--disambiguation-result", default="", help="disambiguation_result JSON file")
    p_commit.add_argument("--extraction-result", default="", help="extraction_result JSON file")

    p_memory_contract = sub.add_parser("memory-contract", help="Forward to memory_cli.py")
    p_memory_contract.add_argument("args", nargs=argparse.REMAINDER)

    p_project_memory = sub.add_parser("project-memory", help="Forward to project_memory.py")
    p_project_memory.add_argument("args", nargs=argparse.REMAINDER)

    p_review_pipeline = sub.add_parser("review-pipeline", help="Forward to review_pipeline.py")
    p_review_pipeline.add_argument("--chapter", type=int, required=True, help="Target chapter number")
    p_review_pipeline.add_argument("--review-results", required=True, help="Raw reviewer results JSON file")
    p_review_pipeline.add_argument("--metrics-out", default="", help="Metrics output file")
    p_review_pipeline.add_argument("--report-file", default="", help="Review report path")
    p_review_pipeline.add_argument("--save-metrics", action="store_true", help="Write directly to index.db")

    p_placeholder_scan = sub.add_parser("placeholder-scan", help="Scan outlines/settings for unfilled placeholders")
    p_placeholder_scan.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    p_master_outline_sync = sub.add_parser("master-outline-sync", help="Write minimal next-volume master-outline anchors after planning this volume")
    p_master_outline_sync.add_argument("--volume", type=int, required=True, help="Volume number whose planning is complete")
    p_master_outline_sync.add_argument("--writeback-file", default="", help="Explicit structured writeback JSON")
    p_master_outline_sync.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    knowledge_parser = sub.add_parser("knowledge", help="Temporal knowledge queries")
    knowledge_sub = knowledge_parser.add_subparsers(dest="knowledge_action")

    qs_parser = knowledge_sub.add_parser("query-entity-state", help="Query entity state at a chapter")
    qs_parser.add_argument("--entity", required=True, help="Entity ID")
    qs_parser.add_argument("--at-chapter", type=int, required=True, help="Target chapter number")

    qr_parser = knowledge_sub.add_parser("query-relationships", help="Query entity relationships at a chapter")
    qr_parser.add_argument("--entity", required=True, help="Entity ID")
    qr_parser.add_argument("--at-chapter", type=int, required=True, help="Target chapter number")

    # 兼容：允许 `--project-root` 出现在任意位置（减少 agents/skills 拼命令的出错率）
    from .cli_args import normalize_global_project_root

    argv = normalize_global_project_root(sys.argv[1:])
    args, unknown_args = parser.parse_known_args(argv)

    # where/use 直接执行
    if hasattr(args, "func"):
        if unknown_args:
            parser.error(f"unrecognized arguments: {' '.join(unknown_args)}")
        code = int(args.func(args) or 0)
        raise SystemExit(code)

    tool = args.tool
    if unknown_args and tool not in PASSTHROUGH_TOOLS:
        parser.error(f"unrecognized arguments: {' '.join(unknown_args)}")

    rest = _passthrough_tail(argv, tool) if tool in PASSTHROUGH_TOOLS else list(getattr(args, "args", []) or [])
    # argparse.REMAINDER 可能以 `--` 开头占位，这里去掉
    if rest[:1] == ["--"]:
        rest = rest[1:]
    rest = _strip_project_root_args(rest)

    # init 是创建项目，不应该依赖/注入已存在 project_root
    if tool == "init":
        raise SystemExit(_run_script("init_project.py", rest))

    # 其余工具：统一解析 project_root 后前置给下游
    project_root = _resolve_root(args.project_root)
    forward_args = ["--project-root", str(project_root)]

    if tool == "index":
        raise SystemExit(_run_data_module("index_manager", [*forward_args, *rest]))
    if tool == "state":
        raise SystemExit(_run_data_module("state_manager", [*forward_args, *rest]))
    if tool == "rag":
        raise SystemExit(_run_data_module("rag_adapter", [*forward_args, *rest]))
    if tool == "style":
        raise SystemExit(_run_data_module("style_sampler", [*forward_args, *rest]))
    if tool == "entity":
        raise SystemExit(_run_data_module("entity_linker", [*forward_args, *rest]))
    if tool == "context":
        raise SystemExit(_run_data_module("context_manager", [*forward_args, *rest]))
    if tool == "memory":
        raise SystemExit(_run_data_module("memory.store", [*forward_args, *rest]))
    if tool == "migrate":
        raise SystemExit(_run_data_module("migrate_state_to_sqlite", [*forward_args, *rest]))

    if tool == "status":
        raise SystemExit(_run_script("status_reporter.py", [*forward_args, *rest]))
    if tool == "update-state":
        raise SystemExit(_run_script("update_state.py", [*forward_args, *rest]))
    if tool == "backup":
        raise SystemExit(_run_script("backup_manager.py", [*forward_args, *rest]))
    if tool == "archive":
        raise SystemExit(_run_script("archive_manager.py", [*forward_args, *rest]))
    if tool == "extract-context":
        return_args = [*forward_args, "--chapter", str(args.chapter), "--format", str(args.format)]
        raise SystemExit(_run_script("extract_chapter_context.py", return_args))
    if tool == "story-system":
        raise SystemExit(_run_script("story_system.py", [*forward_args, *rest]))
    if tool == "story-events":
        return_args = [*forward_args, "--limit", str(args.limit)]
        if args.chapter:
            return_args.extend(["--chapter", str(args.chapter)])
        if args.health:
            return_args.append("--health")
        raise SystemExit(_run_script("story_events.py", return_args))
    if tool == "chapter-commit":
        return_args = [*forward_args, "--chapter", str(args.chapter)]
        if args.review_result:
            return_args.extend(["--review-result", str(args.review_result)])
        if args.fulfillment_result:
            return_args.extend(["--fulfillment-result", str(args.fulfillment_result)])
        if args.disambiguation_result:
            return_args.extend(["--disambiguation-result", str(args.disambiguation_result)])
        if args.extraction_result:
            return_args.extend(["--extraction-result", str(args.extraction_result)])
        raise SystemExit(_run_script("chapter_commit.py", return_args))
    if tool == "memory-contract":
        raise SystemExit(_run_script("memory_cli.py", [*forward_args, *rest]))
    if tool == "project-memory":
        raise SystemExit(_run_script("project_memory.py", [*forward_args, *rest]))
    if tool == "review-pipeline":
        return_args = [
            *forward_args,
            "--chapter", str(args.chapter),
            "--review-results", str(args.review_results),
        ]
        if args.metrics_out:
            return_args.extend(["--metrics-out", str(args.metrics_out)])
        if args.report_file:
            return_args.extend(["--report-file", str(args.report_file)])
        if args.save_metrics:
            return_args.append("--save-metrics")
        raise SystemExit(_run_script("review_pipeline.py", return_args))
    if tool == "placeholder-scan":
        raise SystemExit(_run_data_module("placeholder_scanner", [*forward_args, "--format", str(args.format)]))
    if tool == "master-outline-sync":
        return_args = [*forward_args, "--volume", str(args.volume), "--format", str(args.format)]
        if args.writeback_file:
            return_args.extend(["--writeback-file", str(args.writeback_file)])
        raise SystemExit(_run_script("update_master_outline.py", return_args))

    if tool == "knowledge":
        from .knowledge_query import KnowledgeQuery
        from .cli_output import print_success
        kq = KnowledgeQuery(project_root)
        if args.knowledge_action == "query-entity-state":
            result = kq.entity_state_at_chapter(args.entity, args.at_chapter)
            print_success(result, message="entity_state_at_chapter")
            raise SystemExit(0)
        elif args.knowledge_action == "query-relationships":
            result = kq.entity_relationships_at_chapter(args.entity, args.at_chapter)
            print_success(result, message="entity_relationships_at_chapter")
            raise SystemExit(0)

    raise SystemExit(2)


if __name__ == "__main__":
    main()
