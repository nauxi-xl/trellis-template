#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply the Trellis Template into any target directory.

Copies framework files (`.agents/`, `.claude/`, `.github/`, `.trellis/`,
`AGENTS.md`, `CLAUDE.md`, `.mcp.json`, `.gitignore`, `USAGE.md`, etc.) while
excluding template-local runtime state and development history, optionally
initializes a Git repository (`git init`), and initializes the developer
identity (`.trellis/.developer` + `.trellis/workspace/<name>/`).

Usage:
    python3 scripts/apply-template.py /path/to/my-project --dev alice
    python3 scripts/apply-template.py ./existing-repo -d alice --commit
    python3 scripts/apply-template.py ./new-app --dry-run
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if sys.platform.startswith("win"):
    for _stream_name in ("stdin", "stdout", "stderr"):
        _stream = getattr(sys, _stream_name, None)
        if _stream and hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
            except Exception:
                pass


TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

_TRELLIS_BLOCK_RE = re.compile(
    r"<!-- TRELLIS:START -->.*?<!-- TRELLIS:END -->",
    re.DOTALL,
)

# Directories/files never copied from the template repository.
ALWAYS_EXCLUDE_TOP = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

ALWAYS_EXCLUDE_PATHS = {
    "README.md",
    ".trellis/.developer",
    ".trellis/.current-task",
    ".trellis/.runtime",
    ".trellis/.verify_state.json",
    ".trellis/.ralph-state.json",
    ".trellis/worktrees",
    "scripts/apply-template.py",
}

ALWAYS_EXCLUDE_PREFIXES = (
    ".trellis/.backup-",
)

# Project-customizable files: copied if missing, preserved if already present (unless --force).
PRESERVE_IF_EXISTS_FILES = {
    ".trellis/config.yaml",
    ".trellis/workspace/index.md",
    ".trellis/.template-hashes.json",
}

PRESERVE_IF_EXISTS_PREFIXES = (
    ".trellis/spec/backend/",
    ".trellis/spec/frontend/",
)


@dataclass
class ApplyStats:
    added: List[str] = field(default_factory=list)
    merged: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _norm_rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def _is_excluded(
    rel: str,
    *,
    include_history: bool,
    include_tests: bool,
    include_scripts: bool,
    include_mcp: bool,
) -> bool:
    parts = rel.split("/")
    if any(p in ALWAYS_EXCLUDE_TOP for p in parts):
        return True
    if any(rel.endswith(ext) for ext in (".pyc", ".pyo")):
        return True
    if rel in ALWAYS_EXCLUDE_PATHS:
        return True
    if any(rel.startswith(prefix) for prefix in ALWAYS_EXCLUDE_PREFIXES):
        return True

    # graphify-out/: keep only .gitkeep
    if rel == "graphify-out" or rel.startswith("graphify-out/"):
        return rel not in ("graphify-out", "graphify-out/.gitkeep")

    # .trellis/workspace/: keep index.md, skip template author's personal workspace dirs
    if not include_history and rel.startswith(".trellis/workspace/"):
        if rel != ".trellis/workspace/index.md":
            return True

    # .trellis/tasks/: keep .gitkeep files, skip template dev tasks/archives
    if not include_history and rel.startswith(".trellis/tasks/"):
        if rel not in (
            ".trellis/tasks/.gitkeep",
            ".trellis/tasks/archive",
            ".trellis/tasks/archive/.gitkeep",
        ):
            return True

    if not include_tests and (rel == "tests" or rel.startswith("tests/")):
        return True

    if not include_scripts and (rel == "scripts" or rel.startswith("scripts/")):
        return True

    if not include_mcp and rel == ".mcp.json":
        return True

    return False


def _collect_template_entries(
    template_root: Path,
    *,
    include_history: bool,
    include_tests: bool,
    include_scripts: bool,
    include_mcp: bool,
) -> List[Tuple[str, Path, bool]]:
    """Return sorted list of `(rel_path, src_path, is_symlink)` without traversing symlinks."""
    entries: List[Tuple[str, Path, bool]] = []

    def walk_dir(current: Path) -> None:
        for child in sorted(current.iterdir(), key=lambda p: p.name):
            rel = _norm_rel(child, template_root)
            if _is_excluded(
                rel,
                include_history=include_history,
                include_tests=include_tests,
                include_scripts=include_scripts,
                include_mcp=include_mcp,
            ):
                continue

            if child.is_symlink():
                entries.append((rel, child, True))
            elif child.is_dir():
                walk_dir(child)
            elif child.is_file():
                entries.append((rel, child, False))

    walk_dir(template_root)
    return entries


def _remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _copy_file_preserving_mode(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.is_dir():
        _remove_existing(dst)
    shutil.copy2(src, dst)


def _apply_symlink(
    rel: str,
    src: Path,
    dst: Path,
    *,
    force: bool,
    dry_run: bool,
    stats: ApplyStats,
) -> None:
    link_target = os.readlink(src)

    if dst.is_symlink():
        if os.readlink(dst) == link_target:
            stats.unchanged.append(rel)
            return
        if not force:
            stats.skipped.append(rel)
            stats.warnings.append(f"Skipped differing symlink '{rel}' (use --force to overwrite)")
            return
        if not dry_run:
            dst.unlink()
            _create_symlink_or_copy(src, dst, link_target, stats)
        stats.overwritten.append(rel)
        return

    if dst.exists():
        if not force:
            stats.skipped.append(rel)
            stats.warnings.append(f"Skipped existing '{rel}' (use --force to replace with symlink)")
            return
        if not dry_run:
            _remove_existing(dst)
            _create_symlink_or_copy(src, dst, link_target, stats)
        stats.overwritten.append(rel)
        return

    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        _create_symlink_or_copy(src, dst, link_target, stats)
    stats.added.append(rel)


def _create_symlink_or_copy(src: Path, dst: Path, link_target: str, stats: ApplyStats) -> None:
    try:
        os.symlink(link_target, dst)
    except OSError as exc:
        # Windows fallback when symlink privilege is unavailable
        resolved = src.resolve()
        if resolved.is_dir():
            shutil.copytree(resolved, dst)
        elif resolved.is_file():
            shutil.copy2(resolved, dst)
        else:
            raise exc
        stats.warnings.append(
            f"Created copy instead of symlink for '{dst.name}' ({exc})"
        )


def _merge_agents_md(src_text: str, dst_text: str) -> Tuple[str, str]:
    """Merge Trellis block into an existing AGENTS.md. Returns `(status, new_text)`."""
    if src_text == dst_text:
        return "unchanged", dst_text

    src_match = _TRELLIS_BLOCK_RE.search(src_text)
    if not src_match:
        return "skipped", dst_text

    trellis_block = src_match.group(0)
    dst_match = _TRELLIS_BLOCK_RE.search(dst_text)
    if dst_match:
        if dst_match.group(0) == trellis_block:
            return "unchanged", dst_text
        merged = _TRELLIS_BLOCK_RE.sub(lambda _: trellis_block, dst_text, count=1)
        return "merged", merged

    separator = "\n\n" if dst_text.strip() else ""
    merged = trellis_block + separator + dst_text.lstrip("\n")
    return "merged", merged


def _merge_gitignore(src_text: str, dst_text: str) -> Tuple[str, str]:
    """Append missing ignore patterns from template `.gitignore`."""
    existing_lines = {line.strip() for line in dst_text.splitlines() if line.strip()}
    missing: List[str] = []
    for raw_line in src_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped not in existing_lines:
            missing.append(stripped)

    if not missing:
        return "unchanged", dst_text

    base = dst_text.rstrip("\n")
    block = "\n\n# --- Trellis Template ---\n" + "\n".join(missing) + "\n"
    return "merged", (base + block) if base else block.lstrip("\n")


def _merge_mcp_json(src_text: str, dst_text: str) -> Tuple[str, str]:
    """Add missing `mcpServers` entries into an existing `.mcp.json`."""
    src_data = json.loads(src_text)
    dst_data = json.loads(dst_text)
    if not isinstance(src_data, dict) or not isinstance(dst_data, dict):
        return "skipped", dst_text

    src_servers = src_data.get("mcpServers")
    if not isinstance(src_servers, dict):
        return "unchanged", dst_text

    dst_servers = dst_data.get("mcpServers")
    if dst_servers is None:
        dst_servers = {}
        dst_data["mcpServers"] = dst_servers
    if not isinstance(dst_servers, dict):
        return "skipped", dst_text

    added_any = False
    for key, value in src_servers.items():
        if key not in dst_servers:
            dst_servers[key] = value
            added_any = True

    if not added_any:
        return "unchanged", dst_text

    return "merged", json.dumps(dst_data, indent=2, ensure_ascii=False) + "\n"


def _apply_regular_file(
    rel: str,
    src: Path,
    dst: Path,
    *,
    force: bool,
    dry_run: bool,
    stats: ApplyStats,
) -> None:
    if not dst.exists() and not dst.is_symlink():
        if not dry_run:
            _copy_file_preserving_mode(src, dst)
        stats.added.append(rel)
        return

    if dst.is_symlink() or dst.is_dir():
        if not force:
            stats.skipped.append(rel)
            stats.warnings.append(f"Skipped '{rel}' (existing symlink/directory; use --force to overwrite)")
            return
        if not dry_run:
            _copy_file_preserving_mode(src, dst)
        stats.overwritten.append(rel)
        return

    # Both src and dst are regular files
    src_bytes = src.read_bytes()
    dst_bytes = dst.read_bytes()
    if src_bytes == dst_bytes:
        stats.unchanged.append(rel)
        return

    if force:
        if not dry_run:
            _copy_file_preserving_mode(src, dst)
        stats.overwritten.append(rel)
        return

    # Smart merges for common project files
    if rel == "AGENTS.md":
        status, merged = _merge_agents_md(
            src_bytes.decode("utf-8", errors="replace"),
            dst_bytes.decode("utf-8", errors="replace"),
        )
        if status == "merged":
            if not dry_run:
                dst.write_text(merged, encoding="utf-8")
            stats.merged.append(rel)
        elif status == "unchanged":
            stats.unchanged.append(rel)
        else:
            stats.skipped.append(rel)
        return

    if rel == ".gitignore":
        status, merged = _merge_gitignore(
            src_bytes.decode("utf-8", errors="replace"),
            dst_bytes.decode("utf-8", errors="replace"),
        )
        if status == "merged":
            if not dry_run:
                dst.write_text(merged, encoding="utf-8")
            stats.merged.append(rel)
        else:
            stats.unchanged.append(rel)
        return

    if rel == ".mcp.json":
        try:
            status, merged = _merge_mcp_json(
                src_bytes.decode("utf-8", errors="replace"),
                dst_bytes.decode("utf-8", errors="replace"),
            )
        except json.JSONDecodeError:
            stats.skipped.append(rel)
            stats.warnings.append("Skipped invalid JSON in existing '.mcp.json'")
            return
        if status == "merged":
            if not dry_run:
                dst.write_text(merged, encoding="utf-8")
            stats.merged.append(rel)
        elif status == "unchanged":
            stats.unchanged.append(rel)
        else:
            stats.skipped.append(rel)
        return

    if rel in PRESERVE_IF_EXISTS_FILES or any(rel.startswith(p) for p in PRESERVE_IF_EXISTS_PREFIXES):
        stats.skipped.append(rel)
        return

    stats.skipped.append(rel)
    stats.warnings.append(f"Skipped modified '{rel}' (use --force to overwrite)")


def _run_git(args: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _ensure_git_init(target: Path, branch: str, dry_run: bool) -> str:
    if (target / ".git").exists():
        return f"Already initialized ({target / '.git'})"

    if dry_run:
        return f"Would run: git init -b {branch}"

    res = _run_git(["init", "-b", branch], target)
    if res.returncode != 0:
        # Fallback for older git versions without `init -b`
        res_fallback = _run_git(["init"], target)
        if res_fallback.returncode != 0:
            raise RuntimeError(f"git init failed: {res_fallback.stderr.strip() or res.stderr.strip()}")
        _run_git(["symbolic-ref", "HEAD", f"refs/heads/{branch}"], target)
    return f"Initialized new repository (branch: {branch})"


def _configure_upstream_remote(
    target: Path,
    upstream_url: str,
    *,
    force: bool,
    dry_run: bool,
) -> str:
    if dry_run:
        return f"Would configure git remote 'upstream' -> {upstream_url} and set framework_update.remote"

    if (target / ".git").exists():
        check = _run_git(["remote", "get-url", "upstream"], target)
        if check.returncode == 0:
            if force:
                res = _run_git(["remote", "set-url", "upstream", upstream_url], target)
                if res.returncode != 0:
                    raise RuntimeError(f"Failed to update 'upstream' remote: {res.stderr.strip()}")
                remote_status = f"Updated 'upstream' -> {upstream_url}"
            else:
                remote_status = f"Kept existing 'upstream' ({check.stdout.strip()})"
        else:
            res = _run_git(["remote", "add", "upstream", upstream_url], target)
            if res.returncode != 0:
                raise RuntimeError(f"Failed to add 'upstream' remote: {res.stderr.strip()}")
            remote_status = f"Added 'upstream' -> {upstream_url}"
    else:
        remote_status = "Skipped git remote (no .git directory)"

    config_path = target / ".trellis" / "config.yaml"
    if config_path.is_file():
        cfg_text = config_path.read_text(encoding="utf-8")
        updated = re.sub(
            r'(?m)^(framework_update:\s*\n(?:\s+.*\n)*?\s+remote:\s*)"origin"',
            r'\1"upstream"',
            cfg_text,
            count=1,
        )
        if updated != cfg_text:
            config_path.write_text(updated, encoding="utf-8")

    return remote_status


def _detect_default_developer(target: Path) -> str:
    if shutil.which("git"):
        cwd = target if target.is_dir() else Path.cwd()
        res = _run_git(["config", "user.name"], cwd)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    try:
        user = getpass.getuser().strip()
        if user:
            return user
    except Exception:
        pass
    return "developer"


def _validate_developer_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Developer name cannot be empty.")
    if cleaned in (".", "..") or any(sep in cleaned for sep in ("/", "\\", "\x00")):
        raise ValueError(f"Invalid developer name '{cleaned}': path separators are not allowed.")
    return cleaned


def _read_existing_developer(target: Path) -> Optional[str]:
    dev_file = target / ".trellis" / ".developer"
    if not dev_file.is_file():
        return None
    for line in dev_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("name="):
            val = line.split("=", 1)[1].strip()
            return val or None
    return None


def _resolve_developer_name(
    target: Path,
    dev_arg: Optional[str],
    *,
    non_interactive: bool,
) -> str:
    if dev_arg is not None:
        return _validate_developer_name(dev_arg)

    default_name = _detect_default_developer(target)
    if not non_interactive and sys.stdin.isatty():
        try:
            entered = input(f"Developer name [{default_name}]: ").strip()
        except EOFError:
            entered = ""
        return _validate_developer_name(entered or default_name)

    return _validate_developer_name(default_name)


def _init_developer(
    target: Path,
    dev_name: str,
    *,
    force: bool,
    dry_run: bool,
) -> str:
    existing = _read_existing_developer(target)
    if existing:
        if existing == dev_name:
            return f"Already initialized: {existing}"
        if not force:
            return f"Kept existing developer '{existing}' (use --force to switch to '{dev_name}')"
        if not dry_run:
            (target / ".trellis" / ".developer").unlink(missing_ok=True)

    if dry_run:
        return f"Would initialize developer: {dev_name}"

    init_script = target / ".trellis" / "scripts" / "init_developer.py"
    if not init_script.is_file():
        raise RuntimeError(f"Missing {init_script}; cannot initialize developer.")

    res = subprocess.run(
        [sys.executable, str(init_script), dev_name],
        cwd=str(target),
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        err = (res.stderr or res.stdout).strip()
        raise RuntimeError(f"init_developer.py failed: {err}")

    return f"Initialized developer: {dev_name}"


def _create_initial_commit(target: Path, message: str, *, no_git: bool, dry_run: bool) -> str:
    if no_git:
        return "Skipped commit (--no-git)"

    if dry_run:
        return f"Would stage all files and commit: {message!r}"

    if not (target / ".git").exists():
        return "Skipped commit (no .git repository)"

    status = _run_git(["status", "--porcelain"], target)
    if status.returncode != 0:
        raise RuntimeError(f"git status failed: {status.stderr.strip()}")
    if not status.stdout.strip():
        return "Nothing to commit (working tree clean)"

    add_res = _run_git(["add", "-A"], target)
    if add_res.returncode != 0:
        raise RuntimeError(f"git add failed: {add_res.stderr.strip()}")

    commit_res = _run_git(["commit", "-m", message], target)
    if commit_res.returncode != 0:
        detail = (commit_res.stderr or commit_res.stdout).strip()
        raise RuntimeError(
            f"git commit failed: {detail}\n"
            "Hint: configure git identity with `git config user.name` and `git config user.email`."
        )
    return f"Created commit: {message!r}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply Trellis Template to any target directory, run git init, and initialize developer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 scripts/apply-template.py /path/to/new-project --dev alice\n"
            "  python3 scripts/apply-template.py ../existing-app -d alice --commit\n"
            "  python3 scripts/apply-template.py ../my-app --dry-run -y\n"
        ),
    )
    parser.add_argument(
        "target",
        help="Target project directory (created automatically if it does not exist).",
    )
    parser.add_argument(
        "-d", "--dev",
        dest="dev",
        default=None,
        help="Developer name for .trellis/.developer and .trellis/workspace/<name>/ (default: git user.name or OS user).",
    )
    parser.add_argument(
        "--no-dev",
        action="store_true",
        help="Skip developer initialization.",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Skip git init.",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Initial branch name when running git init (default: main).",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Stage applied files and create an initial git commit.",
    )
    parser.add_argument(
        "--commit-message",
        default="chore: apply trellis template",
        help="Commit message used with --commit (default: 'chore: apply trellis template').",
    )
    parser.add_argument(
        "--upstream",
        default=None,
        help="Optional template git remote URL to add as 'upstream' for future framework updates.",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Do not create or merge .mcp.json (still copies .mcp.json.example).",
    )
    parser.add_argument(
        "--no-scripts",
        action="store_true",
        help="Do not copy scripts/install-tools.* into target.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Also copy tests/test_trellis_framework.py into target.",
    )
    parser.add_argument(
        "--include-history",
        action="store_true",
        help="Also copy existing .trellis/workspace/* and .trellis/tasks/archive/* from template.",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite conflicting files and reinitialize developer if already set.",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Preview all actions without modifying the target directory.",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Non-interactive mode; accept detected developer name without prompting.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print per-file actions (added, merged, overwritten, skipped).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not (TEMPLATE_ROOT / ".trellis").is_dir():
        print(f"[ERROR] Invalid template root: {TEMPLATE_ROOT} (missing .trellis/)", file=sys.stderr)
        return 1

    target = Path(args.target).expanduser().resolve()
    if target == TEMPLATE_ROOT:
        print("[ERROR] Target directory cannot be the template repository itself.", file=sys.stderr)
        return 1

    if not args.no_git and not shutil.which("git"):
        print("[ERROR] 'git' executable not found on PATH (or pass --no-git).", file=sys.stderr)
        return 1

    dev_name: Optional[str] = None
    if not args.no_dev:
        try:
            dev_name = _resolve_developer_name(target, args.dev, non_interactive=args.yes)
        except ValueError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1

    entries = _collect_template_entries(
        TEMPLATE_ROOT,
        include_history=args.include_history,
        include_tests=args.include_tests,
        include_scripts=not args.no_scripts,
        include_mcp=not args.no_mcp,
    )

    stats = ApplyStats()
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for rel, src, is_symlink in entries:
        dst = target / rel
        if is_symlink:
            _apply_symlink(
                rel,
                src,
                dst,
                force=args.force,
                dry_run=args.dry_run,
                stats=stats,
            )
        else:
            _apply_regular_file(
                rel,
                src,
                dst,
                force=args.force,
                dry_run=args.dry_run,
                stats=stats,
            )

    git_status = "Skipped (--no-git)"
    if not args.no_git:
        try:
            git_status = _ensure_git_init(target, args.branch, args.dry_run)
        except RuntimeError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1

    upstream_status: Optional[str] = None
    if args.upstream:
        try:
            upstream_status = _configure_upstream_remote(
                target,
                args.upstream,
                force=args.force,
                dry_run=args.dry_run,
            )
        except RuntimeError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1

    dev_status = "Skipped (--no-dev)"
    if dev_name is not None:
        try:
            dev_status = _init_developer(
                target,
                dev_name,
                force=args.force,
                dry_run=args.dry_run,
            )
        except RuntimeError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1

    commit_status: Optional[str] = None
    if args.commit:
        try:
            commit_status = _create_initial_commit(
                target,
                args.commit_message,
                no_git=args.no_git,
                dry_run=args.dry_run,
            )
        except RuntimeError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1

    mode_label = "[DRY-RUN] " if args.dry_run else ""
    print(f"{mode_label}Applied Trellis Template -> {target}")
    print(
        f"  Files: added={len(stats.added)}, merged={len(stats.merged)}, "
        f"overwritten={len(stats.overwritten)}, unchanged={len(stats.unchanged)}, "
        f"skipped={len(stats.skipped)}"
    )
    print(f"  Git: {git_status}")
    if upstream_status:
        print(f"  Upstream: {upstream_status}")
    print(f"  Developer: {dev_status}")
    if commit_status:
        print(f"  Commit: {commit_status}")

    if args.verbose or args.dry_run:
        for label, items in (
            ("ADD", stats.added),
            ("MERGE", stats.merged),
            ("OVERWRITE", stats.overwritten),
            ("SKIP", stats.skipped),
        ):
            for rel in items:
                print(f"  [{label}] {rel}")

    for warning in stats.warnings:
        print(f"  [WARN] {warning}")

    if not args.dry_run:
        print("\nNext steps:")
        print(f"  cd {target}")
        if not args.no_scripts:
            print("  ./scripts/install-tools.sh --check   # Verify AI/LSP toolchain")
        print("  python3 .trellis/scripts/get_context.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
