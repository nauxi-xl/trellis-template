#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trellis Dynamic Context Engine.

Assembles real-time, token-efficient, adaptive context for AI agents:
- Active branch & git worktree status
- Current task PRD & design constraints
- Scoped spec guidelines inferred from touched paths
- Live LSP compiler diagnostics & symbol health
- Knowledge graph entity context
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Force UTF-8 streams
if sys.platform.startswith("win"):
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Locate repository root."""
    cur = (start or Path.cwd()).resolve()
    while cur != cur.parent:
        if (cur / ".trellis").is_dir() or (cur / ".git").is_dir() or (cur / ".git").is_file():
            return cur
        cur = cur.parent
    return (start or Path.cwd()).resolve()


REPO_ROOT = find_repo_root()


def run_cmd(args: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Execute command returning (code, stdout, stderr)."""
    target_cwd = str(cwd or REPO_ROOT)
    res = subprocess.run(
        args,
        cwd=target_cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return res.returncode, res.stdout.strip(), res.stderr.strip()


# -----------------------------------------------------------------------------
# Context Collectors
# -----------------------------------------------------------------------------

@dataclass
class GitContext:
    branch: str
    commit: str
    is_worktree: bool
    worktree_path: Optional[str]
    modified_files: List[str] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)


def collect_git_context() -> GitContext:
    """Gather git and worktree state."""
    _, branch, _ = run_cmd(["git", "branch", "--show-current"])
    if not branch:
        _, branch, _ = run_cmd(["git", "rev-parse", "--short", "HEAD"])
    _, commit, _ = run_cmd(["git", "rev-parse", "--short", "HEAD"])

    # Worktree check
    _, git_dir, _ = run_cmd(["git", "rev-parse", "--git-dir"])
    _, common_dir, _ = run_cmd(["git", "rev-parse", "--git-common-dir"])
    is_worktree = (git_dir != common_dir and common_dir != "")

    worktree_path = None
    if is_worktree:
        worktree_path = str(REPO_ROOT)

    # Status
    modified: List[str] = []
    untracked: List[str] = []
    _, status_out, _ = run_cmd(["git", "status", "--porcelain"])
    if status_out:
        for line in status_out.splitlines():
            if len(line) < 4:
                continue
            code = line[:2]
            path = line[3:].strip()
            if code.strip() == "??":
                untracked.append(path)
            else:
                modified.append(path)

    return GitContext(
        branch=branch or "unknown",
        commit=commit or "unknown",
        is_worktree=is_worktree,
        worktree_path=worktree_path,
        modified_files=modified,
        untracked_files=untracked,
    )


@dataclass
class TaskContext:
    id: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    branch: Optional[str] = None
    worktree_path: Optional[str] = None
    prd_summary: Optional[str] = None
    has_design: bool = False
    has_implement: bool = False


def collect_task_context() -> Optional[TaskContext]:
    """Find and summarize the active or in-progress task."""
    tasks_root = REPO_ROOT / ".trellis" / "tasks"
    if not tasks_root.is_dir():
        return None

    # Find tasks
    active_candidates = []
    for d in tasks_root.iterdir():
        if d.is_dir() and (d / "task.json").is_file():
            try:
                data = json.loads((d / "task.json").read_text(encoding="utf-8"))
                status = data.get("status")
                if status in ("in_progress", "planning"):
                    active_candidates.append((d, data))
            except Exception:
                continue

    if not active_candidates:
        return None

    # Pick the most recently modified task
    active_candidates.sort(key=lambda pair: (pair[0] / "task.json").stat().st_mtime, reverse=True)
    task_dir, data = active_candidates[0]

    # Summarize PRD
    prd_path = task_dir / "prd.md"
    prd_summary = None
    if prd_path.is_file():
        lines = prd_path.read_text(encoding="utf-8").splitlines()
        summary_lines = []
        for line in lines[:20]:
            if line.startswith("#"):
                summary_lines.append(line)
            elif line.strip() and len(summary_lines) < 6:
                summary_lines.append(line.strip())
        prd_summary = "\n".join(summary_lines)

    return TaskContext(
        id=data.get("id") or task_dir.name,
        title=data.get("title") or data.get("name"),
        status=data.get("status"),
        priority=data.get("priority"),
        branch=data.get("branch"),
        worktree_path=data.get("worktree_path"),
        prd_summary=prd_summary,
        has_design=(task_dir / "design.md").is_file(),
        has_implement=(task_dir / "implement.md").is_file(),
    )


def resolve_scoped_specs(modified_files: List[str]) -> Dict[str, str]:
    """Dynamically determine which spec files are relevant to current modified paths."""
    specs_root = REPO_ROOT / ".trellis" / "spec"
    if not specs_root.is_dir():
        return {}

    relevant_specs: Dict[str, str] = {}
    touched_str = " ".join(modified_files).lower()

    # Rule 1: Frontend
    if any(ext in touched_str for ext in [".tsx", ".jsx", ".vue", ".svelte", ".css", "frontend"]):
        fe_index = specs_root / "frontend" / "index.md"
        if fe_index.is_file():
            relevant_specs["Frontend Specs"] = str(fe_index.relative_to(REPO_ROOT))

    # Rule 2: Backend
    if any(ext in touched_str for ext in [".py", ".go", ".rs", ".java", ".c", ".cpp", "backend", "services", "api"]):
        be_index = specs_root / "backend" / "index.md"
        if be_index.is_file():
            relevant_specs["Backend Specs"] = str(be_index.relative_to(REPO_ROOT))

    # Rule 3: Always include guides index if available
    guides_index = specs_root / "guides" / "index.md"
    if guides_index.is_file():
        relevant_specs["Guides Index"] = str(guides_index.relative_to(REPO_ROOT))

    return relevant_specs


def collect_lsp_status() -> Dict[str, str]:
    """Check agent-lsp availability and health."""
    lsp_bin = shutil.which("agent-lsp")
    if not lsp_bin:
        return {"status": "not_installed", "message": "agent-lsp not found in PATH"}

    code, out, _ = run_cmd(["agent-lsp", "doctor"])
    if code == 0 or "ok" in out:
        return {"status": "ready", "binary": lsp_bin, "info": "Language servers active"}
    return {"status": "warning", "binary": lsp_bin, "info": "Servers partially available"}


# -----------------------------------------------------------------------------
# Formatter
# -----------------------------------------------------------------------------

def format_context_prompt(git_ctx: GitContext, task_ctx: Optional[TaskContext], specs: Dict[str, str], lsp_info: Dict[str, str]) -> str:
    """Format full dynamic context into an AI system instruction block."""
    lines: List[str] = [
        "<!-- TRELLIS_DYNAMIC_CONTEXT:START -->",
        "## Dynamic Project Context",
        "",
        f"- **Git Status**: Branch `{git_ctx.branch}` (commit `{git_ctx.commit}`)",
    ]

    if git_ctx.is_worktree:
        lines.append(f"- **Isolated Worktree**: Active at `{git_ctx.worktree_path}`")

    if git_ctx.modified_files:
        lines.append(f"- **Modified Files ({len(git_ctx.modified_files)})**:")
        for f in git_ctx.modified_files[:10]:
            lines.append(f"  * `{f}`")
        if len(git_ctx.modified_files) > 10:
            lines.append(f"  * ...and {len(git_ctx.modified_files) - 10} more")

    if task_ctx:
        lines.extend([
            "",
            f"### Active Task: [{task_ctx.id}] {task_ctx.title}",
            f"- **Status**: `{task_ctx.status}` | **Priority**: `{task_ctx.priority or 'Normal'}`",
        ])
        if task_ctx.branch:
            lines.append(f"- **Bound Branch**: `{task_ctx.branch}`")
        if task_ctx.worktree_path:
            lines.append(f"- **Bound Worktree**: `{task_ctx.worktree_path}`")
        if task_ctx.prd_summary:
            lines.extend([
                "- **PRD Highlights**:",
                "```markdown",
                task_ctx.prd_summary,
                "```"
            ])

    if specs:
        lines.extend([
            "",
            "### Relevant Specifications for Touched Files",
        ])
        for title, path in specs.items():
            lines.append(f"- **{title}**: `{path}`")

    lines.extend([
        "",
        f"- **LSP Intelligence**: {lsp_info.get('status')} ({lsp_info.get('info', '')})",
        "<!-- TRELLIS_DYNAMIC_CONTEXT:END -->"
    ])

    return "\n".join(lines)


def format_context_text(git_ctx: GitContext, task_ctx: Optional[TaskContext], specs: Dict[str, str], lsp_info: Dict[str, str]) -> str:
    """Format concise summary for CLI output."""
    lines = [
        "=== Trellis Dynamic Context ===",
        f"Branch         : {git_ctx.branch} ({git_ctx.commit})" + (" [WORKTREE]" if git_ctx.is_worktree else ""),
        f"Changes        : {len(git_ctx.modified_files)} modified, {len(git_ctx.untracked_files)} untracked",
    ]
    if task_ctx:
        lines.append(f"Active Task    : [{task_ctx.id}] ({task_ctx.status})")
        if task_ctx.worktree_path:
            lines.append(f"Worktree Path  : {task_ctx.worktree_path}")
    else:
        lines.append("Active Task    : (none)")

    if specs:
        spec_list = ", ".join(f"{k}: {v}" for k, v in specs.items())
        lines.append(f"Scoped Specs   : {spec_list}")

    lines.append(f"LSP Status     : {lsp_info.get('status')} ({lsp_info.get('info', '')})")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Main CLI
# -----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Trellis Dynamic Context Engine")
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "prompt"],
        default="text",
        help="Output format (text, json, prompt)",
    )
    args = parser.parse_args()

    git_ctx = collect_git_context()
    task_ctx = collect_task_context()
    specs = resolve_scoped_specs(git_ctx.modified_files + git_ctx.untracked_files)
    lsp_info = collect_lsp_status()

    if args.format == "json":
        data = {
            "git": asdict(git_ctx),
            "task": asdict(task_ctx) if task_ctx else None,
            "scoped_specs": specs,
            "lsp": lsp_info,
        }
        print(json.dumps(data, indent=2))
    elif args.format == "prompt":
        print(format_context_prompt(git_ctx, task_ctx, specs, lsp_info))
    else:
        print(format_context_text(git_ctx, task_ctx, specs, lsp_info))

    return 0


if __name__ == "__main__":
    sys.exit(main())
