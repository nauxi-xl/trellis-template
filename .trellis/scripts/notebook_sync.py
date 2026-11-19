#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trellis NotebookLM Project Brain Sync & Binding Engine.

Treats NotebookLM (`gemini-notebook-mcp` / `nlm` CLI) as the project's
long-term knowledge brain while leaving direct code navigation to Graphify
and agent-lsp:
  - Tracks whether a project notebook is bound (`notebooklm.project_notebook`
    in `.trellis/config.yaml` or `.trellis/.runtime/notebook-sync-state.json`).
  - Detects knowledge-relevant changes (specs, PRDs, designs, docs, and
    modified source files) since the last NotebookLM sync.
  - Supports `--status`, `--bind`, `--mark-prompted`, `--mark-synced`,
    `--sync`, and `--prompt-hint`.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.platform.startswith("win"):
    for _stream_name in ("stdin", "stdout", "stderr"):
        _stream = getattr(sys, _stream_name, None)
        if _stream and hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
            except Exception:
                pass


def find_repo_root(start: Optional[Path] = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    while cur != cur.parent:
        if (cur / ".trellis").is_dir() or (cur / ".git").is_dir() or (cur / ".git").is_file():
            return cur
        cur = cur.parent
    return (start or Path.cwd()).resolve()


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from common.trellis_config import read_trellis_config  # type: ignore[import-not-found]
except ImportError:
    def read_trellis_config(root: Optional[Path] = None) -> dict[str, Any]:
        return {}


DEFAULT_TRACKED_PATHS: Tuple[str, ...] = (
    "AGENTS.md",
    "README.md",
    "USAGE.md",
    ".trellis/spec/",
    ".trellis/tasks/",
    "docs/",
)

_IGNORED_TASK_SUBPATHS = (".verify_state.json", ".ralph-state.json", ".plan-log")
_IGNORED_ARCHIVE_PREFIX = ".trellis/tasks/archive/"
_CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".rs", ".go", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".java", ".rb", ".cs", ".php", ".swift", ".kt", ".scala",
}


@dataclass
class PendingChange:
    path: str
    category: str  # "knowledge" | "code"
    reason: str


@dataclass
class NotebookSyncStatus:
    enabled: bool
    auto_sync: bool
    ask_if_missing: bool
    bound_notebook: Optional[str]
    bound_title: Optional[str]
    prompted_missing: bool
    declined_missing: bool
    last_sync_at: Optional[str]
    last_synced_commit: Optional[str]
    nlm_available: bool
    pending_changes: List[PendingChange] = field(default_factory=list)

    @property
    def pending_count(self) -> int:
        return len(self.pending_changes)


def _state_path(root: Path) -> Path:
    return root / ".trellis" / ".runtime" / "notebook-sync-state.json"


def _load_state(root: Path) -> dict[str, Any]:
    path = _state_path(root)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(root: Path, state: dict[str, Any]) -> None:
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _get_notebooklm_config(root: Path) -> dict[str, Any]:
    cfg = read_trellis_config(root)
    section = cfg.get("notebooklm") if isinstance(cfg, dict) else None
    raw = section if isinstance(section, dict) else {}

    tracked_raw = raw.get("tracked_paths")
    tracked: List[str]
    if isinstance(tracked_raw, list) and tracked_raw:
        tracked = [str(p).strip().replace("\\", "/") for p in tracked_raw if str(p).strip()]
    else:
        tracked = list(DEFAULT_TRACKED_PATHS)

    project_nb = raw.get("project_notebook")
    project_nb_str = str(project_nb).strip() if isinstance(project_nb, str) and project_nb.strip() else None

    return {
        "enabled": bool(raw.get("enabled", True)),
        "project_notebook": project_nb_str,
        "auto_sync": bool(raw.get("auto_sync", True)),
        "ask_if_missing": bool(raw.get("ask_if_missing", True)),
        "tracked_paths": tracked,
    }


def _run_git(root: Path, args: List[str], timeout: float = 5.0) -> Tuple[int, str, str]:
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as exc:
        return 1, "", str(exc)


def _git_head(root: Path) -> Optional[str]:
    rc, out, _ = _run_git(root, ["rev-parse", "--short", "HEAD"])
    return out if rc == 0 and out else None


def _sha256_file(path: Path) -> Optional[str]:
    try:
        if path.is_file():
            return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None
    return None


def _matches_tracked(rel_path: str, tracked_paths: List[str]) -> bool:
    norm = rel_path.replace("\\", "/").lstrip("./")
    if norm.startswith(_IGNORED_ARCHIVE_PREFIX):
        return False
    if any(norm.endswith(suf) for suf in _IGNORED_TASK_SUBPATHS):
        return False
    for pattern in tracked_paths:
        pat = pattern.lstrip("./")
        if pat.endswith("/"):
            if norm.startswith(pat):
                return True
        elif norm == pat:
            return True
    return False


def _collect_tracked_files(root: Path, tracked_paths: List[str]) -> List[Path]:
    found: Dict[str, Path] = {}
    for pattern in tracked_paths:
        pat = pattern.lstrip("./").rstrip("/")
        if not pat:
            continue
        candidate = root / pat
        if candidate.is_file():
            found[pat] = candidate
        elif candidate.is_dir():
            for child in sorted(candidate.rglob("*")):
                if not child.is_file():
                    continue
                rel = child.relative_to(root).as_posix()
                if _matches_tracked(rel, tracked_paths):
                    found[rel] = child
    return [found[k] for k in sorted(found)]


def _git_dirty_and_recent_files(
    root: Path,
    last_synced_commit: Optional[str],
) -> Dict[str, str]:
    """Return `{rel_path: reason}` from git working tree and commits since `last_synced_commit`."""
    changed: Dict[str, str] = {}

    rc, status_out, _ = _run_git(root, ["status", "--porcelain"])
    if rc == 0 and status_out:
        for line in status_out.splitlines():
            if len(line) < 4:
                continue
            rel = line[3:].strip()
            if " -> " in rel:
                rel = rel.split(" -> ", 1)[1].strip()
            rel = rel.strip('"').replace("\\", "/")
            if rel.startswith(".trellis/.runtime/") or rel.startswith(".trellis/worktrees/"):
                continue
            changed[rel] = "uncommitted change"

    if last_synced_commit:
        rc, diff_out, _ = _run_git(root, ["diff", "--name-only", f"{last_synced_commit}..HEAD"])
        if rc == 0 and diff_out:
            for line in diff_out.splitlines():
                rel = line.strip().replace("\\", "/")
                if rel and rel not in changed:
                    changed[rel] = f"committed since {last_synced_commit}"

    return changed


def collect_pending_changes(
    root: Path,
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> List[PendingChange]:
    tracked_paths: List[str] = cfg["tracked_paths"]
    synced_hashes = state.get("synced_hashes")
    if not isinstance(synced_hashes, dict):
        synced_hashes = {}

    last_synced_commit = state.get("last_synced_commit")
    if not isinstance(last_synced_commit, str) or not last_synced_commit.strip():
        last_synced_commit = None

    pending: Dict[str, PendingChange] = {}

    # 1. Knowledge/spec/task/doc files tracked by content hash
    for file_path in _collect_tracked_files(root, tracked_paths):
        rel = file_path.relative_to(root).as_posix()
        digest = _sha256_file(file_path)
        if digest is None:
            continue
        prev = synced_hashes.get(rel)
        if prev != digest:
            reason = "new knowledge file" if prev is None else "updated knowledge file"
            pending[rel] = PendingChange(path=rel, category="knowledge", reason=reason)

    # 2. Git-dirty or post-sync committed files (including significant code/architecture changes)
    git_changes = _git_dirty_and_recent_files(root, last_synced_commit)
    for rel, reason in git_changes.items():
        if rel in pending:
            continue
        if _matches_tracked(rel, tracked_paths):
            pending[rel] = PendingChange(path=rel, category="knowledge", reason=reason)
        elif Path(rel).suffix.lower() in _CODE_EXTENSIONS:
            pending[rel] = PendingChange(path=rel, category="code", reason=reason)

    return [pending[k] for k in sorted(pending)]


def get_status(root: Optional[Path] = None) -> NotebookSyncStatus:
    repo_root = (root or find_repo_root()).resolve()
    cfg = _get_notebooklm_config(repo_root)
    state = _load_state(repo_root)

    state_nb = state.get("bound_notebook")
    bound_nb = cfg["project_notebook"] or (str(state_nb).strip() if isinstance(state_nb, str) and state_nb.strip() else None)
    bound_title = state.get("bound_title") if isinstance(state.get("bound_title"), str) else None

    pending = collect_pending_changes(repo_root, cfg, state) if cfg["enabled"] else []

    return NotebookSyncStatus(
        enabled=cfg["enabled"],
        auto_sync=cfg["auto_sync"],
        ask_if_missing=cfg["ask_if_missing"],
        bound_notebook=bound_nb,
        bound_title=bound_title,
        prompted_missing=bool(state.get("prompted_missing", False)),
        declined_missing=bool(state.get("declined_missing", False)),
        last_sync_at=state.get("last_sync_at") if isinstance(state.get("last_sync_at"), str) else None,
        last_synced_commit=state.get("last_synced_commit") if isinstance(state.get("last_synced_commit"), str) else None,
        nlm_available=shutil.which("nlm") is not None,
        pending_changes=pending,
    )


def bind_notebook(
    notebook_id_or_alias: str,
    *,
    title: Optional[str] = None,
    root: Optional[Path] = None,
) -> NotebookSyncStatus:
    cleaned = notebook_id_or_alias.strip()
    if not cleaned:
        raise ValueError("Notebook ID or alias cannot be empty.")

    repo_root = (root or find_repo_root()).resolve()
    state = _load_state(repo_root)
    state["bound_notebook"] = cleaned
    if title and title.strip():
        state["bound_title"] = title.strip()
    state["prompted_missing"] = False
    state["declined_missing"] = False
    _save_state(repo_root, state)

    # Also persist project_notebook in .trellis/config.yaml if key is present
    config_path = repo_root / ".trellis" / "config.yaml"
    if config_path.is_file():
        cfg_text = config_path.read_text(encoding="utf-8")
        updated = re.sub(
            r'(?m)^(\s*project_notebook:\s*)(?:"[^"]*"|\'[^\']*\'|\S*)\s*(#.*)?$',
            lambda m: f'{m.group(1)}"{cleaned}"' + (f"  {m.group(2)}" if m.group(2) else ""),
            cfg_text,
            count=1,
        )
        if updated != cfg_text:
            config_path.write_text(updated, encoding="utf-8")

    return get_status(repo_root)


def mark_prompted(*, declined: bool = False, root: Optional[Path] = None) -> NotebookSyncStatus:
    repo_root = (root or find_repo_root()).resolve()
    state = _load_state(repo_root)
    state["prompted_missing"] = True
    state["declined_missing"] = declined
    _save_state(repo_root, state)
    return get_status(repo_root)


def mark_synced(root: Optional[Path] = None) -> NotebookSyncStatus:
    repo_root = (root or find_repo_root()).resolve()
    cfg = _get_notebooklm_config(repo_root)
    state = _load_state(repo_root)

    synced_hashes = state.get("synced_hashes")
    if not isinstance(synced_hashes, dict):
        synced_hashes = {}

    for file_path in _collect_tracked_files(repo_root, cfg["tracked_paths"]):
        rel = file_path.relative_to(repo_root).as_posix()
        digest = _sha256_file(file_path)
        if digest is not None:
            synced_hashes[rel] = digest

    state["synced_hashes"] = synced_hashes
    state["last_sync_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    head = _git_head(repo_root)
    if head:
        state["last_synced_commit"] = head
    _save_state(repo_root, state)
    return get_status(repo_root)


def _extract_markdown_headings(path: Path, limit: int = 5) -> List[str]:
    if path.suffix.lower() != ".md" or not path.is_file():
        return []
    headings: List[str] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                headings.append(stripped.lstrip("#").strip())
                if len(headings) >= limit:
                    break
    except OSError:
        pass
    return headings


def build_sync_note_content(
    repo_root: Path,
    pending: List[PendingChange],
    *,
    summary: Optional[str] = None,
) -> Tuple[str, str]:
    """Build `(note_title, markdown_body)` summarizing pending project changes."""
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    rc, branch, _ = _run_git(repo_root, ["branch", "--show-current"])
    branch_name = branch if rc == 0 and branch else "working-tree"

    title = f"Project Sync ({stamp} - {branch_name})"
    lines: List[str] = [
        f"# {title}",
        "",
        f"- **Repository**: `{repo_root.name}`",
        f"- **Branch**: `{branch_name}`",
    ]
    if summary:
        lines.extend(["", "## Summary", summary.strip()])

    knowledge_items = [c for c in pending if c.category == "knowledge"]
    code_items = [c for c in pending if c.category == "code"]

    if knowledge_items:
        lines.extend(["", f"## Updated Knowledge / Docs / Specs ({len(knowledge_items)})"])
        for item in knowledge_items[:20]:
            headings = _extract_markdown_headings(repo_root / item.path, limit=3)
            heading_hint = f" — sections: {', '.join(headings)}" if headings else ""
            lines.append(f"- `{item.path}` ({item.reason}){heading_hint}")

    if code_items:
        lines.extend(["", f"## Changed Code Modules ({len(code_items)})"])
        for item in code_items[:20]:
            lines.append(f"- `{item.path}` ({item.reason})")

    rc_diff, diff_stat, _ = _run_git(repo_root, ["diff", "--stat", "HEAD"])
    if rc_diff == 0 and diff_stat:
        lines.extend(["", "## Diff Summary", "```", diff_stat, "```"])

    return title, "\n".join(lines) + "\n"


def sync_to_notebook(
    *,
    root: Optional[Path] = None,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    repo_root = (root or find_repo_root()).resolve()
    status = get_status(repo_root)

    if not status.enabled:
        return {"status": "disabled", "pending_count": 0}

    if not status.bound_notebook:
        return {
            "status": "missing_notebook",
            "ask_if_missing": status.ask_if_missing,
            "prompted_missing": status.prompted_missing,
            "declined_missing": status.declined_missing,
            "pending_count": status.pending_count,
            "pending_changes": [asdict(c) for c in status.pending_changes],
            "message": (
                "No project notebook is bound. Ask the user if they want to create/bind one, "
                "then run `python3 .trellis/scripts/notebook_sync.py --bind <id-or-alias>`."
            ),
        }

    if not status.pending_changes:
        return {
            "status": "up_to_date",
            "bound_notebook": status.bound_notebook,
            "pending_count": 0,
        }

    note_title, note_body = build_sync_note_content(
        repo_root,
        status.pending_changes,
        summary=summary,
    )
    if title and title.strip():
        note_title = title.strip()

    if dry_run:
        return {
            "status": "dry_run",
            "bound_notebook": status.bound_notebook,
            "pending_count": status.pending_count,
            "note_title": note_title,
            "note_preview": note_body,
        }

    if not status.nlm_available:
        return {
            "status": "nlm_missing",
            "bound_notebook": status.bound_notebook,
            "pending_count": status.pending_count,
            "note_title": note_title,
            "message": (
                "`nlm` CLI not found on PATH. Update the notebook via `gemini-notebook-mcp` "
                "(`note` action='create') and then run `notebook_sync.py --mark-synced`."
            ),
        }

    try:
        res = subprocess.run(
            [
                "nlm", "note", "create", status.bound_notebook,
                "--title", note_title,
                "--content", note_body,
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except Exception as exc:
        return {
            "status": "sync_error",
            "bound_notebook": status.bound_notebook,
            "pending_count": status.pending_count,
            "error": str(exc),
        }

    if res.returncode != 0:
        err = (res.stderr or res.stdout).strip()
        auth_hint = "auth" in err.lower() or "login" in err.lower() or "token" in err.lower()
        return {
            "status": "auth_required" if auth_hint else "sync_error",
            "bound_notebook": status.bound_notebook,
            "pending_count": status.pending_count,
            "error": err,
        }

    mark_synced(repo_root)
    return {
        "status": "synced",
        "bound_notebook": status.bound_notebook,
        "synced_count": status.pending_count,
        "note_title": note_title,
    }


def format_prompt_hint(root: Optional[Path] = None) -> str:
    status = get_status(root)
    if not status.enabled:
        return ""

    if not status.bound_notebook:
        if status.ask_if_missing and not status.declined_missing:
            return (
                '<notebook-sync status="missing">\n'
                "No project NotebookLM notebook is bound yet. When searching NotebookLM and finding no relevant "
                "notebook, ask the user whether to create/bind one (`notebook_create` + `notebook_sync.py --bind <id>` "
                "or `--mark-prompted --declined`). Keep code-location queries directly on `graphify` / `agent-lsp`.\n"
                "</notebook-sync>"
            )
        return ""

    if status.pending_count > 0:
        sample = ", ".join(c.path for c in status.pending_changes[:5])
        if status.pending_count > 5:
            sample += f", +{status.pending_count - 5} more"
        return (
            f'<notebook-sync status="pending" notebook="{status.bound_notebook}" pending_count="{status.pending_count}">\n'
            f"{status.pending_count} change(s) since last NotebookLM sync ({sample}). "
            f"Auto-update notebook `{status.bound_notebook}` (`note`/`source_add` + `notebook_sync.py --mark-synced`, "
            f"or `python3 .trellis/scripts/notebook_sync.py --sync`).\n"
            "</notebook-sync>"
        )

    return f'<notebook-sync status="synced" notebook="{status.bound_notebook}" />'


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Trellis NotebookLM project brain binding and auto-sync helper.",
    )
    parser.add_argument("--root", default=None, help="Repository root path (defaults to auto-detect).")
    parser.add_argument("--status", action="store_true", help="Show binding and pending sync status.")
    parser.add_argument("--bind", metavar="NOTEBOOK", default=None, help="Bind a NotebookLM ID or alias to this project.")
    parser.add_argument("--title", default=None, help="Optional title for --bind or --sync note.")
    parser.add_argument("--summary", default=None, help="Optional summary text for --sync note.")
    parser.add_argument("--mark-prompted", action="store_true", help="Record that user was asked about missing notebook.")
    parser.add_argument("--declined", action="store_true", help="Use with --mark-prompted when user declined.")
    parser.add_argument("--mark-synced", action="store_true", help="Mark current tracked files and HEAD as synced.")
    parser.add_argument("--sync", action="store_true", help="Sync pending changes to the bound notebook via nlm CLI.")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync note without calling nlm.")
    parser.add_argument("--prompt-hint", action="store_true", help="Print compact <notebook-sync> prompt block.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout on non-error runs.")
    args = parser.parse_args(argv)

    repo_root = Path(args.root).resolve() if args.root else find_repo_root()

    if args.prompt_hint:
        hint = format_prompt_hint(repo_root)
        if hint and not args.quiet:
            print(hint)
        return 0

    if args.bind is not None:
        try:
            st = bind_notebook(args.bind, title=args.title, root=repo_root)
        except ValueError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1
        if args.json:
            payload = asdict(st)
            payload["pending_count"] = st.pending_count
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        elif not args.quiet:
            print(f"Bound project notebook: {st.bound_notebook} (pending={st.pending_count})")
        return 0

    if args.mark_prompted:
        st = mark_prompted(declined=args.declined, root=repo_root)
        if args.json:
            payload = asdict(st)
            payload["pending_count"] = st.pending_count
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        elif not args.quiet:
            print(f"Recorded missing-notebook prompt (declined={st.declined_missing})")
        return 0

    if args.mark_synced:
        st = mark_synced(repo_root)
        if args.json:
            payload = asdict(st)
            payload["pending_count"] = st.pending_count
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        elif not args.quiet:
            print(f"Marked NotebookLM sync checkpoint at {st.last_sync_at} (commit={st.last_synced_commit})")
        return 0

    if args.sync:
        result = sync_to_notebook(
            root=repo_root,
            title=args.title,
            summary=args.summary,
            dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif not args.quiet:
            print(f"NotebookLM sync status: {result.get('status')} ({result.get('message') or result.get('note_title') or ''})")
        return 0

    # Default: --status
    st = get_status(repo_root)
    if args.json:
        payload = asdict(st)
        payload["pending_count"] = st.pending_count
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif not args.quiet:
        print(f"NotebookLM enabled: {st.enabled} | auto_sync={st.auto_sync} | ask_if_missing={st.ask_if_missing}")
        print(f"Bound notebook: {st.bound_notebook or '(none)'}")
        print(f"Pending changes: {st.pending_count}")
        for ch in st.pending_changes[:15]:
            print(f"  - [{ch.category}] {ch.path} ({ch.reason})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
