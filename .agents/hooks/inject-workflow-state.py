#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trellis per-turn breadcrumb hook for Antigravity CLI (agy) PreInvocation.

Runs before each agent turn. Resolves the active task through Trellis'
session-aware active task resolver (with fallback to latest in_progress task)
and emits a <workflow-state> block injected as a systemMessage step.
"""
from __future__ import annotations

import json
import os
import re
import sys
import queue
import threading
from pathlib import Path

# Force UTF-8 encoding
if sys.platform.startswith("win"):
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def find_trellis_root(start: Path) -> Path | None:
    cur = start.resolve()
    while cur != cur.parent:
        if (cur / ".trellis").is_dir():
            return cur
        cur = cur.parent
    return None


def _resolve_active_task(root: Path, input_data: dict):
    scripts_dir = root / ".trellis" / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from common.active_task import resolve_active_task  # type: ignore[import-not-found]
        return resolve_active_task(root, input_data, platform="gemini")
    except Exception:
        return None


def _get_fallback_in_progress_task(root: Path) -> tuple[str, str, str] | None:
    tasks_dir = root / ".trellis" / "tasks"
    if not tasks_dir.is_dir():
        return None

    in_progress = []
    for d in tasks_dir.iterdir():
        if d.is_dir() and d.name != "archive":
            task_file = d / "task.json"
            if task_file.is_file():
                try:
                    task_data = json.loads(task_file.read_text(encoding="utf-8"))
                    if task_data.get("status") == "in_progress":
                        in_progress.append((task_file.stat().st_mtime, task_data.get("id") or d.name, task_data.get("status")))
                except Exception:
                    pass

    if not in_progress:
        return None

    in_progress.sort(key=lambda x: x[0], reverse=True)
    _, task_id, status = in_progress[0]
    return task_id, status, "trellis"


def get_active_task(root: Path, input_data: dict) -> tuple[str, str, str] | None:
    active = _resolve_active_task(root, input_data)
    if active and active.task_path:
        task_dir = Path(active.task_path)
        if not task_dir.is_absolute():
            task_dir = root / task_dir
        if active.stale:
            return task_dir.name, f"stale_{active.source_type}", active.source

        task_json = task_dir / "task.json"
        if task_json.is_file():
            try:
                data = json.loads(task_json.read_text(encoding="utf-8"))
                task_id = data.get("id") or task_dir.name
                status = data.get("status", "")
                if status:
                    return task_id, status, active.source
            except Exception:
                return task_dir.name, "task_error", active.source

    # Fallback to scanning tasks directory for in_progress
    return _get_fallback_in_progress_task(root)


_TAG_RE = re.compile(
    r"\[workflow-state:([A-Za-z0-9_-]+)\]\s*\n(.*?)\n\s*\[/workflow-state:\1\]",
    re.DOTALL,
)


def load_breadcrumbs(root: Path) -> dict[str, str]:
    workflow = root / ".trellis" / "workflow.md"
    if not workflow.is_file():
        return {}
    try:
        content = workflow.read_text(encoding="utf-8")
    except OSError:
        return {}

    result: dict[str, str] = {}
    for match in _TAG_RE.finditer(content):
        status = match.group(1)
        body = match.group(2).strip()
        if body:
            result[status] = body
    return result


def build_breadcrumb(
    task_id: str | None,
    status: str,
    templates: dict[str, str],
    source: str | None = None,
) -> str:
    body = templates.get(status)
    if body is None:
        body = "Refer to workflow.md for current step."
    header = f"Status: {status}" if task_id is None else f"Task: {task_id} ({status})"
    return f"<workflow-state>\n{header}\n{body}\n</workflow-state>"


def _load_hook_input() -> dict:
    result_queue: "queue.Queue[str | Exception]" = queue.Queue(maxsize=1)

    def _read() -> None:
        try:
            result_queue.put(sys.stdin.read())
        except Exception as exc:
            result_queue.put(exc)

    reader = threading.Thread(target=_read, daemon=True)
    reader.start()
    try:
        raw = result_queue.get(timeout=0.2)
    except queue.Empty:
        return {}

    if isinstance(raw, Exception) or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def main() -> int:
    if os.environ.get("TRELLIS_HOOKS") == "0" or os.environ.get("TRELLIS_DISABLE_HOOKS") == "1":
        print(json.dumps({"injectSteps": []}))
        return 0

    data = _load_hook_input()
    cwd_str = data.get("cwd") or os.getcwd()
    cwd = Path(cwd_str)

    root = find_trellis_root(cwd)
    if root is None:
        print(json.dumps({"injectSteps": []}))
        return 0

    templates = load_breadcrumbs(root)
    task = get_active_task(root, data)
    if task is None:
        breadcrumb = build_breadcrumb(None, "no_task", templates)
    else:
        task_id, status, source = task
        breadcrumb = build_breadcrumb(task_id, status, templates, source)

    # AGY output contract: injectSteps with systemMessage
    output = {
        "injectSteps": [
            {
                "systemMessage": {
                    "systemMessage": breadcrumb
                }
            }
        ],
        "hookSpecificOutput": {
            "hookEventName": "PreInvocation",
            "additionalContext": breadcrumb,
        }
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
