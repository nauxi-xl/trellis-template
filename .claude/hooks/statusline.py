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

Color Customization Pattern:
  Users can customize colors in 4 ways:
    1. Preset themes via environment variable: STATUSLINE_THEME="tokyo-night"
    2. Config file (.statusline.json or .trellis/statusline.json):
       {"theme": "tokyo-night", "colors": {"branch": "bold cyan", "developer": "#73daca"}}
    3. Fine-grained environment overrides:
       STATUSLINE_COLOR_BRANCH="bold cyan"
       STATUSLINE_COLORS='{"branch": "magenta", "developer": "yellow"}'
    4. Direct edits in the THEMES table below.

Supported color formats:
  - Named ANSI: "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"
  - Bright ANSI: "gray" / "bright_black", "bright_red", "bright_green", etc.
  - 256 Colors: "123", "color:123", "256:123"
  - TrueColor Hex: "#RRGGBB" or "#RGB" (e.g. "#7aa2f7")
  - Text Styles: "bold", "dim", "italic", "underline" (can combine: "bold cyan")
  - None / Off: "default", "none", ""
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

# ==============================================================================
# Theme & Color Configuration Pattern
# ==============================================================================

THEMES: dict[str, dict[str, str]] = {
    # Classic default Trellis statusline
    "default": {
        "task_priority": "cyan",
        "task_title": "default",
        "task_status": "yellow",
        "task_source": "gray",
        "separator": "gray",
        "model": "default",
        "ctx_label": "default",
        "ctx_low": "green",
        "ctx_med": "yellow",
        "ctx_high": "red",
        "branch": "magenta",
        "duration": "default",
        "developer": "green",
        "task_count": "default",
        "rate_limit": "default",
        "reset_time": "gray",
    },
    # Tokyo Night (dark blue / purple aesthetic)
    "tokyo-night": {
        "task_priority": "#7aa2f7",
        "task_title": "#c0caf5",
        "task_status": "#e0af68",
        "task_source": "#565f89",
        "separator": "#565f89",
        "model": "#7dcfff",
        "ctx_label": "#9aa5ce",
        "ctx_low": "#9ece6a",
        "ctx_med": "#e0af68",
        "ctx_high": "#f7768e",
        "branch": "#bb9af7",
        "duration": "#9aa5ce",
        "developer": "#73daca",
        "task_count": "#b4f9f8",
        "rate_limit": "#7dcfff",
        "reset_time": "#565f89",
    },
    # Catppuccin Mocha (pastel soft aesthetic)
    "catppuccin": {
        "task_priority": "#89b4fa",
        "task_title": "#cdd6f4",
        "task_status": "#f9e2af",
        "task_source": "#6c7086",
        "separator": "#6c7086",
        "model": "#89dceb",
        "ctx_label": "#bac2de",
        "ctx_low": "#a6e3a1",
        "ctx_med": "#f9e2af",
        "ctx_high": "#f38ba8",
        "branch": "#cba6f7",
        "duration": "#bac2de",
        "developer": "#94e2d5",
        "task_count": "#fab387",
        "rate_limit": "#89dceb",
        "reset_time": "#6c7086",
    },
    # Dracula (vibrant dark)
    "dracula": {
        "task_priority": "#8be9fd",
        "task_title": "#f8f8f2",
        "task_status": "#f1fa8c",
        "task_source": "#6272a4",
        "separator": "#6272a4",
        "model": "#bd93f9",
        "ctx_label": "#f8f8f2",
        "ctx_low": "#50fa7b",
        "ctx_med": "#ffb86c",
        "ctx_high": "#ff5555",
        "branch": "#ff79c6",
        "duration": "#f8f8f2",
        "developer": "#50fa7b",
        "task_count": "#8be9fd",
        "rate_limit": "#bd93f9",
        "reset_time": "#6272a4",
    },
    # Nord (arctic icy aesthetic)
    "nord": {
        "task_priority": "#88c0d0",
        "task_title": "#eceff4",
        "task_status": "#ebcb8b",
        "task_source": "#4c566a",
        "separator": "#4c566a",
        "model": "#81a1c1",
        "ctx_label": "#d8dee9",
        "ctx_low": "#a3be8c",
        "ctx_med": "#ebcb8b",
        "ctx_high": "#bf616a",
        "branch": "#b48ead",
        "duration": "#d8dee9",
        "developer": "#8fbcbb",
        "task_count": "#d08770",
        "rate_limit": "#81a1c1",
        "reset_time": "#4c566a",
    },
    # Monokai (warm high contrast)
    "monokai": {
        "task_priority": "#66d9ef",
        "task_title": "#f8f8f2",
        "task_status": "#e6db74",
        "task_source": "#75715e",
        "separator": "#75715e",
        "model": "#66d9ef",
        "ctx_label": "#f8f8f2",
        "ctx_low": "#a6e22e",
        "ctx_med": "#fd971f",
        "ctx_high": "#f92672",
        "branch": "#ae81ff",
        "duration": "#f8f8f2",
        "developer": "#a6e22e",
        "task_count": "#fd971f",
        "rate_limit": "#66d9ef",
        "reset_time": "#75715e",
    },
    # Plain (no colors / minimal output)
    "plain": {
        "task_priority": "default",
        "task_title": "default",
        "task_status": "default",
        "task_source": "default",
        "separator": "default",
        "model": "default",
        "ctx_label": "default",
        "ctx_low": "default",
        "ctx_med": "default",
        "ctx_high": "default",
        "branch": "default",
        "duration": "default",
        "developer": "default",
        "task_count": "default",
        "rate_limit": "default",
        "reset_time": "default",
    },
}

ANSI_COLORS: dict[str, str] = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "bright_black": "90",
    "gray": "90",
    "grey": "90",
    "bright_red": "91",
    "bright_green": "92",
    "bright_yellow": "93",
    "bright_blue": "94",
    "bright_magenta": "95",
    "bright_cyan": "96",
    "bright_white": "97",
}

ANSI_STYLES: dict[str, str] = {
    "bold": "1",
    "dim": "2",
    "italic": "3",
    "underline": "4",
}


def parse_color(spec: str) -> str:
    """Parse a flexible color specification into an ANSI escape sequence."""
    if not spec or os.environ.get("NO_COLOR"):
        return ""
    spec = spec.strip()
    if not spec or spec.lower() in ("default", "none", "reset", "off", "inherit"):
        return ""
    if spec.startswith(("\033[", "\x1b[")):
        return spec

    tokens = spec.split()
    codes: list[str] = []
    for tok in tokens:
        low = tok.lower()
        if low in ANSI_STYLES:
            codes.append(ANSI_STYLES[low])
        elif low in ANSI_COLORS:
            codes.append(ANSI_COLORS[low])
        elif low.startswith("#") and len(low) in (4, 7):
            hex_val = low[1:]
            if len(hex_val) == 3:
                hex_val = "".join(c * 2 for c in hex_val)
            try:
                r = int(hex_val[0:2], 16)
                g = int(hex_val[2:4], 16)
                b = int(hex_val[4:6], 16)
                codes.append(f"38;2;{r};{g};{b}")
            except ValueError:
                pass
        else:
            digits = low
            if digits.startswith("color:"):
                digits = digits[6:]
            elif digits.startswith("256:"):
                digits = digits[4:]
            if digits.isdigit() and 0 <= int(digits) <= 255:
                codes.append(f"38;5;{digits}")

    if not codes:
        return ""
    return f"\033[{';'.join(codes)}m"


def colorize(text: str, spec: str) -> str:
    """Wrap text in ANSI escape sequence if color specification is given."""
    if not text:
        return ""
    code = parse_color(spec)
    return f"{code}{text}\033[0m" if code else text


def load_statusline_colors(cwd: Path | str | None = None) -> dict[str, str]:
    """
    Resolve colors from base theme, JSON configuration files, and environment variables.
    Precedence (lowest to highest):
      1. Default theme ("default")
      2. Preset theme from config or STATUSLINE_THEME
      3. Custom color map from .statusline.json or .trellis/statusline.json
      4. JSON object in STATUSLINE_COLORS
      5. Individual component variables STATUSLINE_COLOR_<NAME>
    """
    colors = dict(THEMES["default"])
    theme_name = os.environ.get("STATUSLINE_THEME", "").strip().lower()

    # Discover configuration files
    cfg_candidates: list[Path] = []
    if os.environ.get("STATUSLINE_CONFIG"):
        cfg_candidates.append(Path(os.environ["STATUSLINE_CONFIG"]).resolve())

    start_dir = Path(cwd).resolve() if cwd else Path.cwd().resolve()
    for parent in [start_dir, *start_dir.parents]:
        cfg_candidates.append(parent / ".statusline.json")
        cfg_candidates.append(parent / ".trellis" / "statusline.json")

    cfg_candidates.append(Path.home() / ".config" / "statusline" / "config.json")

    cfg_data: dict = {}
    for cand in cfg_candidates:
        if cand.is_file():
            try:
                text = cand.read_text(encoding="utf-8").strip()
                if text:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        cfg_data = parsed
                        break
            except Exception:
                pass

    # Select theme
    if not theme_name and isinstance(cfg_data.get("theme"), str):
        theme_name = cfg_data["theme"].strip().lower()

    if theme_name in THEMES:
        colors.update(THEMES[theme_name])

    # Apply colors from config file
    file_colors = cfg_data.get("colors") if isinstance(cfg_data.get("colors"), dict) else cfg_data
    if isinstance(file_colors, dict):
        for k, v in file_colors.items():
            if k in colors and isinstance(v, str):
                colors[k] = v

    # Apply env STATUSLINE_COLORS (JSON format)
    env_colors = os.environ.get("STATUSLINE_COLORS", "").strip()
    if env_colors:
        try:
            parsed_env = json.loads(env_colors)
            if isinstance(parsed_env, dict):
                for k, v in parsed_env.items():
                    if k in colors and isinstance(v, str):
                        colors[k] = v
        except Exception:
            pass

    # Apply env STATUSLINE_COLOR_<COMPONENT>
    for k in colors:
        env_key = f"STATUSLINE_COLOR_{k.upper()}"
        if env_key in os.environ:
            colors[k] = os.environ[env_key]

    return colors


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


def _rate_limit_part(label: str, window: dict, now: int, colors: dict[str, str]) -> str:
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

    pct_text = f"{label} {pct}%"
    part = colorize(pct_text, colors.get("rate_limit", "default"))

    # Reset duration: prefer direct reset_in_seconds if given
    reset_in_secs = window.get("reset_in_seconds")
    reset_text = ""
    if isinstance(reset_in_secs, (int, float)) and reset_in_secs > 0:
        remaining = _format_remaining(int(reset_in_secs))
        if remaining:
            reset_text = f"(reset {remaining})"
    else:
        reset_val = window.get("resets_at") or window.get("reset_at") or window.get("reset_time")
        reset_epoch = _parse_resets_at(reset_val)
        if reset_epoch > now:
            remaining = _format_remaining(reset_epoch - now)
            if remaining:
                reset_text = f"(reset {remaining})"

    if reset_text:
        part += f" {colorize(reset_text, colors.get('reset_time', 'gray'))}"

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

    # Load component colors
    colors = load_statusline_colors(cwd_str)
    sep_char = colorize("·", colors.get("separator", "gray"))
    SEP = f" {sep_char} "

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
    model_str = colorize(model_label, colors.get("model", "default"))

    # Context % with color thresholds
    if ctx_pct >= 90:
        ctx_val_str = colorize(f"{ctx_pct}%", colors.get("ctx_high", "red"))
    elif ctx_pct >= 70:
        ctx_val_str = colorize(f"{ctx_pct}%", colors.get("ctx_med", "yellow"))
    else:
        ctx_val_str = colorize(f"{ctx_pct}%", colors.get("ctx_low", "green"))

    ctx_label_str = colorize("ctx", colors.get("ctx_label", "default"))

    # Build parts of info line
    parts = [
        model_str,
        f"{ctx_label_str} {ctx_val_str}",
    ]
    if branch:
        parts.append(colorize(branch, colors.get("branch", "magenta")))
    if duration:
        parts.append(colorize(duration, colors.get("duration", "default")))
    if dev:
        parts.append(colorize(dev, colors.get("developer", "green")))
    if task_count:
        parts.append(colorize(f"{task_count} task(s)", colors.get("task_count", "default")))

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
                        part = _rate_limit_part(label, candidate, now, colors)
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
                part = _rate_limit_part(label, matched_window, now, colors)
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
        
        prio_str = colorize(f"[{priority}]", colors.get("task_priority", "cyan"))
        title_str = colorize(title, colors.get("task_title", "default"))
        status_str = colorize(f"({status})", colors.get("task_status", "yellow"))
        
        source_suffix = ""
        if source_tag:
            source_suffix = f" {colorize(f'[{source_tag}]', colors.get('task_source', 'gray'))}"
        print(f"{prio_str} {title_str} {status_str}{source_suffix}")

    # Width wrapping
    width = _terminal_width(session_data)
    if width is not None and rate_parts and _visible_len(info_line) > width:
        print(SEP.join(parts))
        print(SEP.join(rate_parts))
    else:
        print(info_line)


if __name__ == "__main__":
    main()
