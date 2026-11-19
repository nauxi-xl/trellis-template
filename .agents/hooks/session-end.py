#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trellis SessionEnd / Stop hook.

Runs automatically when a session terminates or the agent stops.
Finds the active Trellis task and updates its `implement.md` with
the current progress checkpoint, git diff summary, and recent commits.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
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


def get_active_task_dir(root: Path) -> Path | None:
    scripts_dir = root / ".trellis" / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from common.active_task import resolve_active_task  # type: ignore[import-not-found]
        active = resolve_active_task(root, {}, platform="antigravity")
        if active and active.task_path:
            p = Path(active.task_path)
            if not p.is_absolute():
                p = root / p
            if p.is_dir():
                return p
    except Exception:
        pass

    # Fallback: scan .trellis/tasks for latest modified active/in_progress task
    tasks_dir = root / ".trellis" / "tasks"
    if not tasks_dir.is_dir():
        return None

    candidates: list[tuple[int, float, Path]] = []
    for d in tasks_dir.iterdir():
        if d.is_dir() and d.name != "archive":
            task_json = d / "task.json"
            if task_json.is_file():
                try:
                    data = json.loads(task_json.read_text(encoding="utf-8"))
                    status = data.get("status", "")
                    score = 2 if status == "in_progress" else (1 if status == "planning" else 0)
                    candidates.append((score, task_json.stat().st_mtime, d))
                except Exception:
                    pass

    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return candidates[0][2]

    return None


def get_git_info(root: Path) -> dict:
    info = {
        "branch": "unknown",
        "changed_files": [],
        "recent_commits": [],
    }
    try:
        # Branch
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            info["branch"] = res.stdout.strip()
        else:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                info["branch"] = res.stdout.strip()

        # Status porcelain
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            lines = res.stdout.strip().splitlines()
            info["changed_files"] = lines[:15]
            if len(lines) > 15:
                info["changed_files"].append(f"... and {len(lines) - 15} more uncommitted files")

        # Recent commits (last 3)
        res = subprocess.run(
            ["git", "log", "-n", "3", "--oneline"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            info["recent_commits"] = res.stdout.strip().splitlines()
    except Exception:
        pass

    return info


def update_implement_md(task_dir: Path, git_info: dict, timestamp: str) -> bool:
    implement_path = task_dir / "implement.md"
    task_json_path = task_dir / "task.json"
    status = "in_progress"
    task_name = task_dir.name

    if task_json_path.is_file():
        try:
            tdata = json.loads(task_json_path.read_text(encoding="utf-8"))
            status = tdata.get("status", status)
            task_name = tdata.get("title") or tdata.get("id") or task_name
        except Exception:
            pass

    content = ""
    if implement_path.is_file():
        content = implement_path.read_text(encoding="utf-8")
    else:
        # Seed minimal implement.md if not yet created
        content = (
            f"# Implementation Plan: {task_name}\n\n"
            f"Status: `{status}`\n\n"
            "## Tasks\n"
            "- [ ] Requirements & initial setup\n"
        )

    checkpoint_lines = [
        f"### Session Checkpoint: {timestamp}",
        f"- **Status**: `{status}` | **Branch**: `{git_info['branch']}`",
    ]

    if git_info["changed_files"]:
        checkpoint_lines.append(f"- **Working Directory Changes** ({len(git_info['changed_files'])}):")
        for f in git_info["changed_files"]:
            checkpoint_lines.append(f"  - `{f}`")
    else:
        checkpoint_lines.append("- **Working Directory**: Clean (no uncommitted changes)")

    if git_info["recent_commits"]:
        checkpoint_lines.append("- **Recent Commits**:")
        for c in git_info["recent_commits"]:
            checkpoint_lines.append(f"  - `{c}`")

    checkpoint_block = "\n".join(checkpoint_lines)

    header = "## Session Checkpoints"
    if header in content:
        parts = content.split(header, 1)
        prefix = parts[0].rstrip()
        rest = parts[1]

        # Extract previous checkpoints to retain up to 3 latest
        existing = re.findall(
            r"(### Session Checkpoint:.*?)(?=(?:### Session Checkpoint:)|(?:\n## )|\Z)",
            rest,
            re.DOTALL,
        )
        all_cps = [checkpoint_block] + [c.strip() for c in existing[:2]]
        new_content = prefix + "\n\n" + header + "\n\n" + "\n\n".join(all_cps) + "\n"
    else:
        new_content = content.rstrip() + "\n\n" + header + "\n\n" + checkpoint_block + "\n"

    try:
        implement_path.write_text(new_content, encoding="utf-8")
        return True
    except Exception:
        return False


def _auto_sync_notebook(root: Path) -> None:
    """Best-effort NotebookLM auto-sync on session end when a project notebook is bound."""
    scripts_dir = root / ".trellis" / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        import notebook_sync  # type: ignore[import-not-found]

        st = notebook_sync.get_status(root)
        if st.enabled and st.auto_sync and st.bound_notebook and st.nlm_available and st.pending_count > 0:
            notebook_sync.sync_to_notebook(root=root)
    except Exception:
        pass


def main() -> int:
    raw_input = ""
    try:
        if not sys.stdin.isatty():
            raw_input = sys.stdin.read()
    except Exception:
        pass

    root = find_trellis_root(Path(__file__))
    if not root:
        print(json.dumps({"decision": "allow"}))
        return 0

    task_dir = get_active_task_dir(root)
    if task_dir:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        git_info = get_git_info(root)
        update_implement_md(task_dir, git_info, now_str)

    _auto_sync_notebook(root)

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
