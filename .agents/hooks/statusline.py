#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trellis StatusLine — Project-level status display for Antigravity CLI (agy) & Claude Code.

Reads session JSON from stdin + Trellis task data from filesystem.
Outputs 1-2 lines:
  With active task:  [P1] Task title (status)  +  info line
  Without task:      info line only
Info line: model · ctx% · branch · duration · developer · tasks · rate limits
When COLUMNS is too narrow for the info line, rate limits move to their own line.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Hook hosts send UTF-8 JSON regardless of process locale
_stdin_reconfigure = getattr(sys.stdin, "reconfigure", None)
if callable(_stdin_reconfigure):
    try:
        _stdin_reconfigure(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        pass

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, PermissionError, OSError):
        return ""


def _read_json(path: Path) -> dict:
    text = _read_text(path)
    if not text:
        return {}
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}


def _normalize_task_ref(task_ref: str) -> str:
    normalized = task_ref.strip()
    if not normalized:
        return ""

    path_obj = Path(normalized)
    if path_obj.is_absolute():
        return str(path_obj)

    normalized = normalized.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]

    if normalized.startswith("tasks/"):
        return f".trellis/{normalized}"

    return normalized


def _resolve_task_dir(trellis_dir: Path, task_ref: str) -> Path:
    normalized = _normalize_task_ref(task_ref)
    path_obj = Path(normalized)
    if path_obj.is_absolute():
        return path_obj
    if normalized.startswith(".trellis/"):
        return trellis_dir.parent / path_obj
    return trellis_dir / "tasks" / path_obj


def _find_trellis_dir(start_dir: Path | str | None = None) -> Path | None:
    """Walk up from cwd or start_dir to find .trellis/ directory."""
    current = Path(start_dir).resolve() if start_dir else Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / ".trellis"
        if candidate.is_dir():
            return candidate
    return None


def _get_current_task_for_input(trellis_dir: Path, session_data: dict) -> dict | None:
    """Load current task info through Trellis active task resolver with fallback."""
    scripts_dir = trellis_dir / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from common.active_task import resolve_active_task  # type: ignore[import-not-found]
        active = resolve_active_task(trellis_dir.parent, session_data, platform="gemini")
        if active and active.task_path:
            task_path = _resolve_task_dir(trellis_dir, active.task_path)
            if active.stale:
                return {
                    "title": task_path.name,
                    "status": "stale",
                    "priority": "P?",
                    "source": active.source,
                }
            task_data = _read_json(task_path / "task.json")
            if task_data:
                return {
                    "title": task_data.get("title") or task_data.get("name") or "unknown",
                    "status": task_data.get("status", "unknown"),
                    "priority": task_data.get("priority", "P2"),
                    "source": active.source,
                }
    except Exception:
        pass

    # Fallback for non-session-tracked platforms (e.g. AGY standalone or fresh session):
    # Scan .trellis/tasks/ for the latest task in 'in_progress' state.
    return _get_fallback_in_progress_task(trellis_dir)


def _get_fallback_in_progress_task(trellis_dir: Path) -> dict | None:
    tasks_dir = trellis_dir / "tasks"
    if not tasks_dir.is_dir():
        return None

    in_progress_tasks = []
    for d in tasks_dir.iterdir():
        if d.is_dir() and d.name != "archive":
            task_file = d / "task.json"
            if task_file.is_file():
                task_data = _read_json(task_file)
                if task_data.get("status") == "in_progress":
                    mtime = task_file.stat().st_mtime
                    in_progress_tasks.append((mtime, task_data))

    if not in_progress_tasks:
        return None

    # Pick the most recently updated task
    in_progress_tasks.sort(key=lambda x: x[0], reverse=True)
    latest_task = in_progress_tasks[0][1]
    return {
        "title": latest_task.get("title") or latest_task.get("name") or "unknown",
        "status": latest_task.get("status", "in_progress"),
        "priority": latest_task.get("priority", "P2"),
        "source": "trellis",
    }


def _count_active_tasks(trellis_dir: Path) -> int:
    """Count non-archived task directories with valid task.json."""
    tasks_dir = trellis_dir / "tasks"
    if not tasks_dir.is_dir():
        return 0
    count = 0
    for d in tasks_dir.iterdir():
        if d.is_dir() and d.name != "archive" and (d / "task.json").is_file():
            count += 1
    return count


def _get_developer(trellis_dir: Path) -> str:
    content = _read_text(trellis_dir / ".developer")
    if not content:
        return "unknown"
    for line in content.splitlines():
        if line.startswith("name="):
            return line[5:].strip()
    return content.splitlines()[0].strip() or "unknown"


def _get_git_branch(cwd: Path | str | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=3,
            cwd=cwd or None,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def _format_ctx_size(size: int) -> str:
    if size >= 1_000_000:
        return f"{size // 1_000_000}M"
    if size >= 1_000:
        return f"{size // 1_000}K"
    return str(size) if size > 0 else ""


def _format_duration(ms: int) -> str:
    if ms <= 0:
        return ""
    secs = ms // 1000
    hours, remainder = divmod(secs, 3600)
    mins = remainder // 60
    if hours > 0:
        return f"{hours}h{mins}m"
    return f"{mins}m"


def _format_remaining(secs: int) -> str:
    if secs <= 0:
        return ""
    days, remainder = divmod(secs, 86400)
    hours, remainder = divmod(remainder, 3600)
    mins = remainder // 60
    if days > 0:
        return f"{days}d{hours}h"
    if hours > 0:
        return f"{hours}h{mins}m"
    return f"{mins}m"


def _parse_resets_at(value: object) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value:
        try:
            return int(float(value))
        except ValueError:
            pass
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return int(parsed.timestamp())
        except ValueError:
            pass
    return 0


def _rate_limit_part(label: str, window: dict, now: int) -> str:
    if not isinstance(window, dict):
        return ""
    if window.get("disabled") is True:
        return ""

    pct_val = (
        window.get("used_percentage")
        or window.get("percent_used")
        or window.get("percentage")
        or window.get("pct")
    )
    if pct_val is None:
        rem_frac = window.get("remaining_fraction")
        if rem_frac is not None:
            try:
                pct_val = round((1.0 - float(rem_frac)) * 100)
            except (TypeError, ValueError):
                pass
        else:
            used_frac = window.get("used_fraction")
            if used_frac is not None:
                try:
                    pct_val = round(float(used_frac) * 100)
                except (TypeError, ValueError):
                    pass
            else:
                rem_pct = window.get("remaining_percentage")
                if rem_pct is not None:
                    try:
                        pct_val = round(100.0 - float(rem_pct))
                    except (TypeError, ValueError):
                        pass

    if pct_val is None:
        return ""
    try:
        pct = max(0, min(100, int(round(float(pct_val)))))
    except (TypeError, ValueError):
        return ""

    part = f"{label} {pct}%"

    # Reset duration: prefer direct reset_in_seconds if given
    reset_in_secs = window.get("reset_in_seconds")
    if isinstance(reset_in_secs, (int, float)) and reset_in_secs > 0:
        remaining = _format_remaining(int(reset_in_secs))
        if remaining:
            part += f" \033[90m(reset {remaining})\033[0m"
    else:
        reset_val = window.get("resets_at") or window.get("reset_at") or window.get("reset_time")
        reset_epoch = _parse_resets_at(reset_val)
        if reset_epoch > now:
            remaining = _format_remaining(reset_epoch - now)
            if remaining:
                part += f" \033[90m(reset {remaining})\033[0m"
    return part


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _visible_len(s: str) -> int:
    """Length of string with ANSI escape sequences stripped."""
    return len(_ANSI_RE.sub("", s))


def _terminal_width(session_data: dict | None = None) -> int | None:
    if session_data and isinstance(session_data, dict):
        tw = session_data.get("terminal_width")
        if isinstance(tw, (int, float)) and tw > 0:
            return int(tw)
    try:
        width = int(os.environ.get("COLUMNS", ""))
    except ValueError:
        return None
    return width if width > 0 else None


def main() -> None:
    raw_input = ""
    try:
        raw_input = sys.stdin.read()
    except Exception:
        pass

    # Optional debug capture if requested
    if os.environ.get("TRELLIS_DEBUG_STATUSLINE") or os.path.exists("/tmp/.trellis_capture_statusline"):
        try:
            with open("/tmp/trellis_statusline_stdin.json", "w", encoding="utf-8") as f:
                f.write(raw_input)
        except Exception:
            pass

    session_data = {}
    if raw_input.strip():
        try:
            session_data = json.loads(raw_input)
        except (json.JSONDecodeError, ValueError):
            session_data = {}

    cwd_str = (
        session_data.get("cwd")
        or (session_data.get("workspace") or {}).get("project_dir")
        or (session_data.get("workspace") or {}).get("current_dir")
    )
    trellis_dir = _find_trellis_dir(cwd_str)
    SEP = " \033[90m·\033[0m "

    # --- Trellis data ---
    task = _get_current_task_for_input(trellis_dir, session_data) if trellis_dir else None
    dev = _get_developer(trellis_dir) if trellis_dir else ""
    task_count = _count_active_tasks(trellis_dir) if trellis_dir else 0

    # --- Model extraction (AGY + Claude) ---
    model_obj = session_data.get("model")
    if isinstance(model_obj, dict):
        model = (
            model_obj.get("display_name")
            or model_obj.get("model_name")
            or model_obj.get("id")
            or model_obj.get("name")
            or "?"
        )
    elif isinstance(model_obj, str) and model_obj:
        model = model_obj
    else:
        model = session_data.get("model_name") or session_data.get("modelId") or "?"

    # --- Context extraction (AGY + Claude) ---
    cw = (
        session_data.get("context_window")
        or session_data.get("contextWindow")
        or session_data.get("context")
        or {}
    )
    if not isinstance(cw, dict):
        cw = {}
    ctx_pct = int(
        cw.get("used_percentage")
        or cw.get("percent_used")
        or cw.get("percentage")
        or 0
    )
    ctx_size_int = (
        cw.get("context_window_size")
        or cw.get("size")
        or cw.get("total_tokens")
        or cw.get("max_tokens")
        or 0
    )
    ctx_size = _format_ctx_size(int(ctx_size_int))

    # --- Duration extraction ---
    cost_obj = session_data.get("cost")
    dur_ms = 0
    if isinstance(cost_obj, dict):
        dur_ms = cost_obj.get("total_duration_ms") or 0
    if not dur_ms:
        dur_ms = session_data.get("duration_ms") or session_data.get("total_duration_ms") or 0
    duration = _format_duration(int(dur_ms))

    # --- VCS / Branch extraction ---
    vcs_obj = session_data.get("vcs")
    branch = ""
    if isinstance(vcs_obj, dict):
        branch = vcs_obj.get("branch") or ""
    if not branch:
        branch = session_data.get("branch") or _get_git_branch(cwd_str)

    # Format model label
    if ctx_size and not re.search(r"\d+[KMG]\b", model, re.IGNORECASE):
        model_label = f"{model} ({ctx_size})"
    else:
        model_label = model

    # Context % with color
    if ctx_pct >= 90:
        ctx_color = "\033[31m"  # red
    elif ctx_pct >= 70:
        ctx_color = "\033[33m"  # yellow
    else:
        ctx_color = "\033[32m"  # green

    # Build parts of info line
    parts = [
        model_label,
        f"ctx {ctx_color}{ctx_pct}%\033[0m",
    ]
    if branch:
        parts.append(f"\033[35m{branch}\033[0m")
    if duration:
        parts.append(duration)
    if dev:
        parts.append(f"\033[32m{dev}\033[0m")
    if task_count:
        parts.append(f"{task_count} task(s)")

    # --- Rate limits / Quotas extraction ---
    now = int(time.time())
    rate_limits = (
        session_data.get("rate_limits")
        or session_data.get("quota")
        or session_data.get("quota_buckets")
        or {}
    )

    is_3p = any(
        k in model.lower()
        for k in ("claude", "gpt", "sonnet", "opus", "haiku", "o1", "o3", "3p", "openai", "anthropic")
    )
    provider_prefixes = ["3p-", "3p_"] if is_3p else ["gemini-", "gemini_"]
    alt_prefixes = ["gemini-", "gemini_"] if is_3p else ["3p-", "3p_"]

    targets = [
        (
            "5h",
            [p + "5h" for p in provider_prefixes]
            + ["five_hour", "5h", "hourly", "short_term"]
            + [p + "5h" for p in alt_prefixes],
        ),
        (
            "7d",
            [p + "weekly" for p in provider_prefixes]
            + [p + "7d" for p in provider_prefixes]
            + ["seven_day", "7d", "one_week", "1w", "weekly", "long_term"]
            + [p + "weekly" for p in alt_prefixes]
            + [p + "7d" for p in alt_prefixes],
        ),
    ]

    rate_parts: list[str] = []
    if isinstance(rate_limits, dict):
        for label, keys in targets:
            for k in keys:
                if k in rate_limits:
                    candidate = rate_limits[k]
                    if isinstance(candidate, dict) and not candidate.get("disabled"):
                        part = _rate_limit_part(label, candidate, now)
                        if part:
                            rate_parts.append(part)
                            break
    elif isinstance(rate_limits, list):
        for label, keys in targets:
            matched_window = None
            for k in keys:
                for item in rate_limits:
                    if isinstance(item, dict):
                        name = str(
                            item.get("name")
                            or item.get("label")
                            or item.get("id")
                            or item.get("key")
                            or ""
                        ).lower()
                        if name == k.lower() or (k.lower() in name):
                            if not item.get("disabled"):
                                matched_window = item
                                break
                if matched_window:
                    break
            if matched_window:
                part = _rate_limit_part(label, matched_window, now)
                if part:
                    rate_parts.append(part)

    info_line = SEP.join(parts + rate_parts)

    # Output: Task line (if active)
    if task:
        priority = task.get("priority", "P2")
        title = task.get("title", "")
        status = task.get("status", "")
        source = str(task.get("source") or "")
        source_tag = "session" if source.startswith("session:") else source
        source_suffix = f" \033[90m[{source_tag}]\033[0m" if source_tag else ""
        print(f"\033[36m[{priority}]\033[0m {title} \033[33m({status})\033[0m{source_suffix}")

    # Width wrapping
    width = _terminal_width(session_data)
    if width is not None and rate_parts and _visible_len(info_line) > width:
        print(SEP.join(parts))
        print(SEP.join(rate_parts))
    else:
        print(info_line)


if __name__ == "__main__":
    main()
