"""
Watchdog file-change monitoring and SSE delivery

Monitor writes to key files under PROJECT_ROOT/.webnovel/ and .story-system/.
Notify connected frontend clients through SSE to refresh their data.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import AsyncGenerator

from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from watchdog.observers import Observer


def _is_relative_to(path: Path, root: Path | None) -> bool:
    if root is None:
        return False
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


class _WebnovelFileHandler(FileSystemEventHandler):
    """Watch key .webnovel files and .story-system JSON changes."""

    WATCH_NAMES = {"state.json", "index.db", "workflow_state.json"}

    def __init__(
        self,
        notify_callback,
        *,
        watch_webnovel_dir: Path | None,
        watch_story_system_dir: Path | None,
    ):
        super().__init__()
        self._notify = notify_callback
        self._watch_webnovel_dir = Path(watch_webnovel_dir).resolve() if watch_webnovel_dir else None
        self._watch_story_system_dir = (
            Path(watch_story_system_dir).resolve() if watch_story_system_dir else None
        )

    def _should_notify(self, path: Path) -> bool:
        if _is_relative_to(path, self._watch_webnovel_dir):
            return path.name in self.WATCH_NAMES
        if _is_relative_to(path, self._watch_story_system_dir):
            return path.suffix.lower() == ".json"
        return False

    def _handle(self, event, kind: str):
        path = Path(event.src_path)
        if self._should_notify(path):
            self._notify(event.src_path, kind)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._handle(event, "modified")

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle(event, "created")


class FileWatcher:
    """Manage the watchdog Observer and SSE subscriptions."""

    def __init__(self):
        self._observer: Observer | None = None
        self._subscribers: list[asyncio.Queue] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    # --- Subscription management ---

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=64)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass

    # --- Delivery ---

    def _on_change(self, path: str, kind: str):
        """Called from the watchdog thread to dispatch notifications to the main event loop."""
        msg = json.dumps({"file": Path(path).name, "kind": kind, "ts": time.time()})
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._dispatch, msg)

    def _dispatch(self, msg: str):
        dead: list[asyncio.Queue] = []
        for q in self._subscribers:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.append(q)
        for dq in dead:
            self.unsubscribe(dq)

    # --- Lifecycle ---

    def start(
        self,
        *,
        watch_webnovel_dir: Path | None,
        watch_story_system_dir: Path | None,
        loop: asyncio.AbstractEventLoop,
    ):
        """Start the watchdog observer for both .webnovel and .story-system."""
        self.stop()
        self._loop = loop
        handler = _WebnovelFileHandler(
            self._on_change,
            watch_webnovel_dir=watch_webnovel_dir,
            watch_story_system_dir=watch_story_system_dir,
        )
        self._observer = Observer()
        has_watch_target = False
        if watch_webnovel_dir and Path(watch_webnovel_dir).is_dir():
            self._observer.schedule(handler, str(watch_webnovel_dir), recursive=False)
            has_watch_target = True
        if watch_story_system_dir and Path(watch_story_system_dir).is_dir():
            self._observer.schedule(handler, str(watch_story_system_dir), recursive=True)
            has_watch_target = True
        if not has_watch_target:
            self._observer = None
            return
        self._observer.daemon = True
        self._observer.start()

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=3)
            self._observer = None
