"""
Dashboard 启动脚本

用法：
    python -m dashboard.server --project-root /path/to/novel-project
    python -m dashboard.server                   # 自动从 .claude 指针读取
"""

import argparse
import os
import sys
import webbrowser
from pathlib import Path


def _resolve_project_root(cli_root: str | None) -> Path:
    """按优先级解析 PROJECT_ROOT：CLI > 环境变量 > .claude 指针 > CWD。"""
    if cli_root:
        return Path(cli_root).resolve()

    env = os.environ.get("WEBNOVEL_PROJECT_ROOT")
    if env:
        return Path(env).resolve()

    # 尝试从 .claude 指针读取
    cwd = Path.cwd()
    pointer = cwd / ".claude" / ".webnovel-current-project"
    if pointer.is_file():
        target = pointer.read_text(encoding="utf-8").strip()
        if target:
            p = Path(target)
            if p.is_dir() and (p / ".webnovel" / "state.json").is_file():
                return p.resolve()

    # 最终兜底：当前目录
    if (cwd / ".webnovel" / "state.json").is_file():
        return cwd.resolve()

    print("ERROR: Cannot locate PROJECT_ROOT (expected a directory containing .webnovel/state.json)", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Webnovel Dashboard Server")
    parser.add_argument("--project-root", type=str, default=None, help="Novel project root directory")
    parser.add_argument("--host", default="127.0.0.1", help="Listen address")
    parser.add_argument("--port", type=int, default=8765, help="Listen port")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically")
    args = parser.parse_args()

    project_root = _resolve_project_root(args.project_root)
    print(f"Project path: {project_root}")

    # 延迟导入，以便先处理路径
    import uvicorn
    from .app import create_app

    app = create_app(project_root)

    url = f"http://{args.host}:{args.port}"
    print(f"Dashboard started: {url}")
    print(f"API docs: {url}/docs")

    if not args.no_browser:
        webbrowser.open(url)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
