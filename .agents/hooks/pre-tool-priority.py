#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trellis PreToolUse priority hook for agent-lsp and Context7.

Intercepts tool calls before execution across Antigravity, Claude Code, and
GitHub Copilot to prioritize:
1. `agent-lsp` MCP tools for code search, symbol navigation, and safe edits.
2. `context7` MCP tools for library, framework, SDK, API, and CLI docs.

Supports two modes via `.trellis/config.yaml` (`tool_priority.mode`) or
`TRELLIS_TOOL_PRIORITY_MODE`:
- "advisory" (default): allows execution while injecting priority guidance.
- "enforce": denies the first un-prioritized raw grep/web-search in a session,
  records the nudge in `.trellis/.runtime/tool-priority-state.json`, and allows
  subsequent retries.
"""
from __future__ import annotations

import json
import os
import queue
import re
import sys
import threading
from pathlib import Path
from typing import Any

# Force UTF-8 streams on Windows
if sys.platform.startswith("win"):
    for _stream_name in ("stdin", "stdout", "stderr"):
        _stream = getattr(sys, _stream_name, None)
        if _stream and hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
            except Exception:
                pass


LSP_PRIORITY_MSG = (
    "[Tool Priority: agent-lsp First] Prefer agent-lsp MCP tools "
    "(find_symbol, find_references, find_callers, inspect_symbol, blast_radius, "
    "preview_edit, safe_apply_edit, get_diagnostics) before raw grep/find or direct code edits."
)

CONTEXT7_PRIORITY_MSG = (
    "[Tool Priority: Context7 First] Prefer Context7 MCP "
    "(resolve-library-id -> query-docs) for library/API docs and gemini-notebook-mcp "
    "(notebook_list -> notebook_query) for saved project knowledge before search_web/WebSearch; "
    "persist key research findings via note/source_add."
)

_CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".rs", ".go", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".java", ".rb", ".cs", ".php", ".swift", ".kt", ".scala",
}

_CODE_SEARCH_TOOLS = {"grep_search", "find_by_name", "Grep", "Glob"}
_CODE_EDIT_TOOLS = {"edit_file", "write_file", "Edit", "Write", "MultiEdit"}
_WEB_TOOLS = {"search_web", "read_url_content", "WebSearch", "WebFetch"}

_RAW_GREP_CMD_RE = re.compile(r"(?:^|[;&|\s])(?:grep|rg|ag|ack|find)\b")
_EXCLUDED_CMD_RE = re.compile(
    r"\b(?:agent-lsp|graphify|git|verify\.py|task\.py|worktree\.py|dynamic_context\.py|pyright|pytest|unittest)\b"
)
_WEB_FETCH_CMD_RE = re.compile(r"(?:^|[;&|\s])(?:curl|wget)\b")
_AGENT_LSP_CMD_RE = re.compile(r"\bagent-lsp\b")


def find_trellis_root(start: Path) -> Path | None:
    """Locate the nearest ancestor directory containing `.trellis/`."""
    cur = start.resolve()
    while cur != cur.parent:
        if (cur / ".trellis").is_dir():
            return cur
        cur = cur.parent
    return None


def _load_hook_input() -> dict[str, Any]:
    """Read stdin hook JSON with a short timeout so open pipes never hang."""
    result_queue: queue.Queue[str | Exception] = queue.Queue(maxsize=1)

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


def _read_tool_priority_config(root: Path) -> dict[str, Any]:
    """Load `tool_priority` config from `.trellis/config.yaml` with env overrides."""
    defaults: dict[str, Any] = {
        "enabled": True,
        "mode": "advisory",
        "prefer_lsp": True,
        "prefer_context7": True,
    }
    scripts_dir = root / ".trellis" / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from common.trellis_config import read_trellis_config  # type: ignore[import-not-found]
        cfg = read_trellis_config(root)
        if isinstance(cfg, dict):
            tp = cfg.get("tool_priority")
            if isinstance(tp, dict):
                if isinstance(tp.get("enabled"), bool):
                    defaults["enabled"] = tp["enabled"]
                if isinstance(tp.get("prefer_lsp"), bool):
                    defaults["prefer_lsp"] = tp["prefer_lsp"]
                if isinstance(tp.get("prefer_context7"), bool):
                    defaults["prefer_context7"] = tp["prefer_context7"]
                raw_mode = str(tp.get("mode", defaults["mode"])).strip().lower()
                if raw_mode in ("advisory", "enforce"):
                    defaults["mode"] = raw_mode
    except Exception:
        pass

    env_mode = os.environ.get("TRELLIS_TOOL_PRIORITY_MODE", "").strip().lower()
    if env_mode in ("advisory", "enforce"):
        defaults["mode"] = env_mode
    return defaults


def _extract_tool_call(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Normalize tool name and args across Antigravity, Claude Code, and Copilot."""
    tool_call = data.get("toolCall")
    if isinstance(tool_call, dict):
        name = str(tool_call.get("name") or "")
        args = tool_call.get("args")
        return name, args if isinstance(args, dict) else {}

    name = str(data.get("tool_name") or data.get("toolName") or "")
    raw_args = data.get("tool_input") if "tool_input" in data else data.get("toolArgs")
    if isinstance(raw_args, str):
        try:
            parsed = json.loads(raw_args)
            raw_args = parsed if isinstance(parsed, dict) else {}
        except Exception:
            raw_args = {}
    return name, raw_args if isinstance(raw_args, dict) else {}


def _get_session_id(data: dict[str, Any]) -> str:
    """Resolve a stable session key for runtime tool-usage tracking."""
    return str(
        data.get("conversationId")
        or data.get("session_id")
        or data.get("sessionId")
        or os.environ.get("TRELLIS_CONTEXT_ID")
        or "default"
    )


def _state_file_path(root: Path) -> Path:
    return root / ".trellis" / ".runtime" / "tool-priority-state.json"


def _load_state(state_path: Path) -> dict[str, dict[str, bool]]:
    if not state_path.is_file():
        return {}
    try:
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            return {
                str(k): v
                for k, v in loaded.items()
                if isinstance(v, dict)
            }
    except Exception:
        pass
    return {}


def _save_state(state_path: Path, state: dict[str, dict[str, bool]]) -> None:
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass


def _is_agent_lsp_call(name: str, args: dict[str, Any]) -> bool:
    if name == "call_mcp_tool" and str(args.get("ServerName", "")).strip().lower() == "agent-lsp":
        return True
    lowered = name.lower()
    if lowered.startswith(("mcp_agent-lsp", "mcp__agent-lsp")):
        return True
    if name in ("run_command", "Bash"):
        cmd = str(args.get("CommandLine") or args.get("command") or "")
        if _AGENT_LSP_CMD_RE.search(cmd):
            return True
    return False


def _is_context7_call(name: str, args: dict[str, Any]) -> bool:
    if name == "call_mcp_tool" and str(args.get("ServerName", "")).strip().lower() == "context7":
        return True
    lowered = name.lower()
    if lowered.startswith(("mcp_context7", "mcp__context7")):
        return True
    return False


def _is_notebooklm_call(name: str, args: dict[str, Any]) -> bool:
    if name == "call_mcp_tool" and str(args.get("ServerName", "")).strip().lower() == "gemini-notebook-mcp":
        return True
    lowered = name.lower()
    if lowered.startswith(("mcp_gemini-notebook-mcp", "mcp__gemini-notebook-mcp")):
        return True
    if name in ("run_command", "Bash"):
        cmd = str(args.get("CommandLine") or args.get("command") or "")
        if re.search(r"(?:^|[;&|\s])nlm\b", cmd):
            return True
    return False


def _classify_fallback_tool(name: str, args: dict[str, Any]) -> tuple[str | None, bool]:
    """Return `(category, enforceable)` where category is `'lsp'` | `'context7'` | None."""
    if name in _CODE_SEARCH_TOOLS:
        return "lsp", True

    if name in _CODE_EDIT_TOOLS:
        target = str(args.get("Path") or args.get("TargetFile") or args.get("file_path") or "")
        if Path(target).suffix.lower() in _CODE_EXTENSIONS:
            return "lsp", False

    if name in _WEB_TOOLS:
        return "context7", True

    if name in ("run_command", "Bash"):
        cmd = str(args.get("CommandLine") or args.get("command") or "")
        if _RAW_GREP_CMD_RE.search(cmd) and not _EXCLUDED_CMD_RE.search(cmd):
            return "lsp", True
        if _WEB_FETCH_CMD_RE.search(cmd) and ("http://" in cmd or "https://" in cmd):
            if "localhost" not in cmd and "127.0.0.1" not in cmd:
                return "context7", True

    return None, False


def _emit_decision(decision: str, reason: str | None = None, *, is_agy: bool = True) -> int:
    if is_agy:
        payload: dict[str, Any] = {"decision": decision}
        if reason:
            payload["reason"] = reason
    else:
        payload = {
            "decision": decision,
            "permissionDecision": decision,
        }
        if reason:
            payload["reason"] = reason
            payload["permissionDecisionReason"] = reason
            payload["hookSpecificOutput"] = {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
                "additionalContext": reason,
            }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def main() -> int:
    if os.environ.get("TRELLIS_HOOKS") == "0" or os.environ.get("TRELLIS_DISABLE_HOOKS") == "1":
        return _emit_decision("allow")

    data = _load_hook_input()
    is_agy = "tool_name" not in data and "toolName" not in data
    cwd = Path(data.get("cwd") or os.getcwd())
    root = find_trellis_root(cwd) or find_trellis_root(Path(__file__).resolve())
    if root is None:
        return _emit_decision("allow", is_agy=is_agy)

    cfg = _read_tool_priority_config(root)
    if not cfg.get("enabled", True):
        return _emit_decision("allow", is_agy=is_agy)

    tool_name, tool_args = _extract_tool_call(data)
    if not tool_name:
        return _emit_decision("allow", is_agy=is_agy)

    state_path = _state_file_path(root)
    state = _load_state(state_path)
    session_id = _get_session_id(data)
    session_state = state.setdefault(
        session_id,
        {
            "lsp_used": False,
            "context7_used": False,
            "notebooklm_used": False,
            "lsp_nudged": False,
            "context7_nudged": False,
        },
    )

    if _is_agent_lsp_call(tool_name, tool_args):
        session_state["lsp_used"] = True
        _save_state(state_path, state)
        return _emit_decision("allow", is_agy=is_agy)

    if _is_context7_call(tool_name, tool_args):
        session_state["context7_used"] = True
        _save_state(state_path, state)
        return _emit_decision("allow", is_agy=is_agy)

    if _is_notebooklm_call(tool_name, tool_args):
        session_state["notebooklm_used"] = True
        _save_state(state_path, state)
        return _emit_decision("allow", is_agy=is_agy)

    category, enforceable = _classify_fallback_tool(tool_name, tool_args)
    if category is None:
        return _emit_decision("allow", is_agy=is_agy)

    mode = cfg.get("mode", "advisory")

    if category == "lsp" and cfg.get("prefer_lsp", True):
        if session_state.get("lsp_used"):
            return _emit_decision("allow", is_agy=is_agy)
        if mode == "enforce" and enforceable and not session_state.get("lsp_nudged"):
            session_state["lsp_nudged"] = True
            _save_state(state_path, state)
            return _emit_decision("deny", LSP_PRIORITY_MSG, is_agy=is_agy)
        return _emit_decision("allow", LSP_PRIORITY_MSG, is_agy=is_agy)

    if category == "context7" and cfg.get("prefer_context7", True):
        if session_state.get("context7_used"):
            return _emit_decision("allow", is_agy=is_agy)
        if mode == "enforce" and enforceable and not session_state.get("context7_nudged"):
            session_state["context7_nudged"] = True
            _save_state(state_path, state)
            return _emit_decision("deny", CONTEXT7_PRIORITY_MSG, is_agy=is_agy)
        return _emit_decision("allow", CONTEXT7_PRIORITY_MSG, is_agy=is_agy)

    return _emit_decision("allow", is_agy=is_agy)


if __name__ == "__main__":
    sys.exit(main())
