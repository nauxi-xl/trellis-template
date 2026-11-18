#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trellis Remote Framework Updater.

Fetches updates to Trellis-managed framework files (`.agents/`, `.claude/`,
`.github/`, `.trellis/scripts/`, `.trellis/spec/guides/`, `USAGE.md`, etc.)
from a configured remote Git repository while protecting project-specific
data (`.trellis/tasks/`, `.trellis/workspace/`, `.trellis/config.yaml`, etc.).

Supports `--check`, `--dry-run`, `--force`, `--rollback`, and `--json`.
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
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Force UTF-8 streams on Windows
if sys.platform.startswith("win"):
    for _stream_name in ("stdin", "stdout", "stderr"):
        _stream = getattr(sys, _stream_name, None)
        if _stream and hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
            except Exception:
                pass


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Locate repository root containing `.trellis/` or `.git/`."""
    cur = (start or Path.cwd()).resolve()
    while cur != cur.parent:
        if (cur / ".trellis").is_dir() or (cur / ".git").is_dir() or (cur / ".git").is_file():
            return cur
        cur = cur.parent
    return (start or Path.cwd()).resolve()


REPO_ROOT = find_repo_root()
SCRIPTS_DIR = REPO_ROOT / ".trellis" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from common.trellis_config import read_trellis_config  # type: ignore[import-not-found]
except ImportError:
    def read_trellis_config(root: Optional[Path] = None) -> dict[str, Any]:
        return {}


MANAGED_PREFIXES: Tuple[str, ...] = (
    ".agents/",
    ".claude/",
    ".github/",
    ".trellis/scripts/",
    ".trellis/agents/",
    ".trellis/spec/guides/",
)

MANAGED_FILES = {
    ".trellis/workflow.md",
    ".trellis/.gitignore",
    ".trellis/.version",
    ".mcp.json.example",
    ".statusline.json.example",
    "USAGE.md",
    "tests/test_trellis_framework.py",
}

PROTECTED_PREFIXES: Tuple[str, ...] = (
    ".trellis/tasks/",
    ".trellis/workspace/",
    ".trellis/worktrees/",
    ".trellis/.runtime/",
    ".trellis/.backup-",
)

PROTECTED_FILES = {
    ".trellis/.developer",
    ".trellis/.current-task",
    ".trellis/.verify_state.json",
    ".trellis/.ralph-state.json",
    ".trellis/config.yaml",
    ".mcp.json",
}

PLATFORM_SYMLINKS: Tuple[Tuple[str, str], ...] = (
    (".agent", ".agents"),
    ("CLAUDE.md", "AGENTS.md"),
    (".claude/skills", "../.agents/skills"),
    (".github/skills", "../.agents/skills"),
    (".claude/hooks/pre-tool-priority.py", "../../.agents/hooks/pre-tool-priority.py"),
    (".github/copilot/hooks/pre-tool-priority.py", "../../../.agents/hooks/pre-tool-priority.py"),
)

_TRELLIS_BLOCK_RE = re.compile(
    r"<!-- TRELLIS:START -->.*?<!-- TRELLIS:END -->",
    re.DOTALL,
)
_MANIFEST_NAME = ".backup-manifest.json"
_HASHES_REL_PATH = ".trellis/.template-hashes.json"


def _run_git(
    args: List[str],
    cwd: Path,
    timeout: Optional[float] = None,
) -> Tuple[int, bytes, str]:
    """Execute a git command returning `(returncode, stdout_bytes, stderr_text)`."""
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return res.returncode, res.stdout, res.stderr.decode("utf-8", errors="replace").strip()
    except subprocess.TimeoutExpired:
        return 1, b"", f"git command timed out after {timeout}s"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _local_entry_bytes(path: Path) -> Optional[bytes]:
    """Return raw bytes for a local file or UTF-8 target bytes for a symlink."""
    if path.is_symlink():
        return os.readlink(path).encode("utf-8")
    if path.is_file():
        return path.read_bytes()
    return None


def _normalize_rel_path(rel_path: str) -> str:
    norm = rel_path.replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    return norm


def _is_protected_path(rel_path: str) -> bool:
    norm = _normalize_rel_path(rel_path)
    if norm in PROTECTED_FILES:
        return True
    return any(norm.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def is_managed_path(rel_path: str) -> bool:
    """Return True if `rel_path` is a framework-managed file (and not protected)."""
    norm = _normalize_rel_path(rel_path)
    if _is_protected_path(norm):
        return False
    if norm in MANAGED_FILES:
        return True
    return any(norm.startswith(prefix) for prefix in MANAGED_PREFIXES)


def _resolve_default_remote(root: Path, config: dict[str, Any]) -> str:
    env_remote = os.environ.get("TRELLIS_UPDATE_REMOTE", "").strip()
    if env_remote:
        return env_remote

    fu_cfg = config.get("framework_update")
    if isinstance(fu_cfg, dict):
        cfg_remote = fu_cfg.get("remote")
        if isinstance(cfg_remote, str) and cfg_remote.strip():
            return cfg_remote.strip()

    rc, out_bytes, _ = _run_git(["remote"], root)
    if rc == 0:
        remotes = {line.strip() for line in out_bytes.decode("utf-8", errors="replace").splitlines() if line.strip()}
        if "upstream" in remotes:
            return "upstream"
        if "template" in remotes:
            return "template"
        if "origin" in remotes:
            return "origin"
    return "origin"


def _resolve_default_branch(config: dict[str, Any]) -> str:
    env_branch = os.environ.get("TRELLIS_UPDATE_BRANCH", "").strip()
    if env_branch:
        return env_branch

    fu_cfg = config.get("framework_update")
    if isinstance(fu_cfg, dict):
        cfg_branch = fu_cfg.get("branch")
        if isinstance(cfg_branch, str) and cfg_branch.strip():
            return cfg_branch.strip()
    return "main"


def _load_template_hashes(root: Path) -> Tuple[dict[str, Any], dict[str, str]]:
    hashes_path = root / _HASHES_REL_PATH
    if not hashes_path.is_file():
        return {"__version": 2, "hashes": {}}, {}
    try:
        raw = json.loads(hashes_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            hashes = raw.get("hashes")
            if isinstance(hashes, dict):
                clean = {str(k): str(v) for k, v in hashes.items() if isinstance(v, str)}
                raw["hashes"] = clean
                return raw, clean
    except Exception:
        pass
    return {"__version": 2, "hashes": {}}, {}


def _save_template_hashes(root: Path, doc: dict[str, Any], hashes: dict[str, str]) -> None:
    hashes_path = root / _HASHES_REL_PATH
    hashes_path.parent.mkdir(parents=True, exist_ok=True)
    doc["__version"] = doc.get("__version", 2)
    doc["hashes"] = dict(sorted(hashes.items()))
    hashes_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _head_blob_hash(root: Path, rel_path: str) -> Optional[str]:
    rc, out, _ = _run_git(["show", f"HEAD:{rel_path}"], root)
    if rc == 0:
        return _sha256_bytes(out)
    return None


def _compute_agents_md_update(
    local_bytes: Optional[bytes],
    remote_bytes: bytes,
    recorded_hash: Optional[str],
    head_hash: Optional[str],
    force: bool,
) -> Tuple[str, Optional[bytes]]:
    """Return `(action, new_bytes)` for `AGENTS.md`: action in `added|updated|unchanged|skipped_modified`."""
    if local_bytes is None:
        return "added", remote_bytes

    if local_bytes == remote_bytes:
        return "unchanged", None

    local_hash = _sha256_bytes(local_bytes)
    baseline = recorded_hash or head_hash
    is_modified = baseline is not None and local_hash != baseline

    if not is_modified or force:
        return "updated", remote_bytes

    local_text = local_bytes.decode("utf-8", errors="replace")
    remote_text = remote_bytes.decode("utf-8", errors="replace")
    local_match = _TRELLIS_BLOCK_RE.search(local_text)
    remote_match = _TRELLIS_BLOCK_RE.search(remote_text)
    if local_match and remote_match:
        if local_match.group(0) == remote_match.group(0):
            return "unchanged", None
        merged = _TRELLIS_BLOCK_RE.sub(lambda _: remote_match.group(0), local_text, count=1)
        return "updated", merged.encode("utf-8")

    return "skipped_modified", None


def _parse_ls_tree(root: Path, ref: str) -> List[Tuple[str, str]]:
    """Return list of `(mode, rel_path)` for all blobs in `ref`."""
    rc, out_bytes, err = _run_git(["ls-tree", "-r", "-z", ref], root)
    if rc != 0:
        raise RuntimeError(f"git ls-tree failed: {err}")

    entries: List[Tuple[str, str]] = []
    for record in out_bytes.split(b"\x00"):
        if not record:
            continue
        meta_b, _, path_b = record.partition(b"\t")
        if not path_b:
            continue
        parts = meta_b.decode("utf-8", errors="replace").split()
        if len(parts) < 3:
            continue
        mode, obj_type, _ = parts[0], parts[1], parts[2]
        if obj_type == "blob":
            entries.append((mode, path_b.decode("utf-8", errors="replace")))
    return entries


def _create_backup_dir(root: Path) -> Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = root / ".trellis" / f".backup-{stamp}"
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
        return base
    idx = 1
    while True:
        candidate = root / ".trellis" / f".backup-{stamp}-{idx}"
        if not candidate.exists():
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        idx += 1


def _backup_entry(root: Path, backup_dir: Path, rel_path: str) -> None:
    src = root / rel_path
    if not src.exists() and not src.is_symlink():
        return
    dst = backup_dir / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_symlink():
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        os.symlink(os.readlink(src), dst)
    elif src.is_dir():
        shutil.copytree(src, dst, symlinks=True)
    else:
        shutil.copy2(src, dst)


def _write_entry(root: Path, rel_path: str, mode: str, content: bytes) -> None:
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.is_symlink():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)

    if mode == "120000":
        link_dest = content.decode("utf-8")
        os.symlink(link_dest, target)
    else:
        target.write_bytes(content)
        if mode == "100755":
            try:
                os.chmod(target, 0o755)
            except OSError:
                pass


def ensure_platform_symlinks(root: Path) -> List[str]:
    """Ensure canonical cross-platform symlinks exist when their targets exist."""
    repaired: List[str] = []
    for link_rel, target_rel in PLATFORM_SYMLINKS:
        link_path = root / link_rel
        if not link_path.parent.is_dir():
            continue
        resolved_target = (link_path.parent / target_rel).resolve()
        if not resolved_target.exists():
            continue
        if link_path.is_symlink():
            if os.readlink(link_path) == target_rel:
                continue
            link_path.unlink()
        elif link_path.exists():
            continue
        os.symlink(target_rel, link_path)
        repaired.append(link_rel)
    return repaired


def rollback_latest_backup(root: Path) -> Tuple[bool, str, List[str]]:
    """Restore files from the most recent `.trellis/.backup-*` directory."""
    trellis_dir = root / ".trellis"
    if not trellis_dir.is_dir():
        return False, "No .trellis directory found.", []

    backups = [
        p for p in trellis_dir.iterdir()
        if p.is_dir() and p.name.startswith(".backup-")
    ]
    if not backups:
        return False, "No backup directories found under .trellis/.", []

    backups.sort(key=lambda p: (p.stat().st_mtime, p.name), reverse=True)
    latest = backups[0]
    manifest_path = latest / _MANIFEST_NAME
    added_files: List[str] = []
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(manifest, dict) and isinstance(manifest.get("added"), list):
                added_files = [str(x) for x in manifest["added"]]
        except Exception:
            pass

    restored: List[str] = []
    for rel_added in added_files:
        added_target = root / rel_added
        if added_target.is_symlink() or added_target.is_file():
            added_target.unlink()
            restored.append(f"removed:{rel_added}")

    for src in sorted(latest.rglob("*")):
        rel = src.relative_to(latest).as_posix()
        if rel == _MANIFEST_NAME:
            continue
        if src.is_dir() and not src.is_symlink():
            continue
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink():
            dst.unlink()
        elif dst.is_dir():
            shutil.rmtree(dst)
        if src.is_symlink():
            os.symlink(os.readlink(src), dst)
        else:
            shutil.copy2(src, dst)
        restored.append(rel)

    shutil.rmtree(latest, ignore_errors=True)
    return True, latest.name, restored


def run_framework_update(
    root: Path,
    remote: str,
    branch: str,
    *,
    check_only: bool = False,
    dry_run: bool = False,
    force: bool = False,
    fetch_timeout: Optional[float] = None,
) -> dict[str, Any]:
    """Fetch remote branch and inspect or apply managed framework updates."""
    rc, _, err = _run_git(["fetch", remote, branch], root, timeout=fetch_timeout)
    if rc != 0:
        raise RuntimeError(f"Failed to fetch '{branch}' from '{remote}': {err}")

    rc_sha, sha_out, _ = _run_git(["rev-parse", "--short", "FETCH_HEAD"], root)
    remote_commit = sha_out.decode("utf-8", errors="replace").strip() if rc_sha == 0 else "unknown"

    tree_entries = _parse_ls_tree(root, "FETCH_HEAD")
    hash_doc, recorded_hashes = _load_template_hashes(root)

    added: List[str] = []
    updated: List[str] = []
    unchanged: List[str] = []
    skipped_modified: List[str] = []
    pending_writes: List[Tuple[str, str, bytes, str, str]] = []  # (rel, mode, content, action, new_hash)

    for mode, rel_path in tree_entries:
        if rel_path != "AGENTS.md" and not is_managed_path(rel_path):
            continue

        rc_blob, remote_bytes, blob_err = _run_git(["show", f"FETCH_HEAD:{rel_path}"], root)
        if rc_blob != 0:
            raise RuntimeError(f"Failed to read remote blob '{rel_path}': {blob_err}")

        remote_hash = _sha256_bytes(remote_bytes)
        local_path = root / rel_path
        local_bytes = _local_entry_bytes(local_path)

        if rel_path == "AGENTS.md":
            action, write_bytes = _compute_agents_md_update(
                local_bytes,
                remote_bytes,
                recorded_hashes.get(rel_path),
                _head_blob_hash(root, rel_path),
                force,
            )
            if action == "unchanged":
                unchanged.append(rel_path)
            elif action == "skipped_modified":
                skipped_modified.append(rel_path)
            elif write_bytes is not None:
                if action == "added":
                    added.append(rel_path)
                else:
                    updated.append(rel_path)
                pending_writes.append((rel_path, mode, write_bytes, action, remote_hash))
            continue

        if local_bytes is None and not local_path.is_dir():
            added.append(rel_path)
            pending_writes.append((rel_path, mode, remote_bytes, "added", remote_hash))
            continue

        if local_bytes is not None and local_bytes == remote_bytes:
            unchanged.append(rel_path)
            continue

        if local_bytes is not None:
            local_hash = _sha256_bytes(local_bytes)
            baseline = recorded_hashes.get(rel_path) or _head_blob_hash(root, rel_path)
            is_locally_modified = baseline is not None and local_hash != baseline
            if is_locally_modified and not force:
                skipped_modified.append(rel_path)
                continue

        updated.append(rel_path)
        pending_writes.append((rel_path, mode, remote_bytes, "updated", remote_hash))

    backup_rel: Optional[str] = None
    repaired_symlinks: List[str] = []

    if not check_only and not dry_run and pending_writes:
        backup_dir = _create_backup_dir(root)
        backup_rel = backup_dir.relative_to(root).as_posix()

        # Always back up template-hashes.json alongside modified files
        _backup_entry(root, backup_dir, _HASHES_REL_PATH)
        for rel_path, _, _, action, _ in pending_writes:
            if action == "updated":
                _backup_entry(root, backup_dir, rel_path)

        manifest = {
            "remote": remote,
            "branch": branch,
            "remote_commit": remote_commit,
            "added": [rel for rel, _, _, act, _ in pending_writes if act == "added"],
            "updated": [rel for rel, _, _, act, _ in pending_writes if act == "updated"],
        }
        (backup_dir / _MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        for rel_path, mode, content, _, new_hash in pending_writes:
            _write_entry(root, rel_path, mode, content)
            recorded_hashes[rel_path] = new_hash

        _save_template_hashes(root, hash_doc, recorded_hashes)
        repaired_symlinks = ensure_platform_symlinks(root)

    status = "up_to_date"
    if added or updated:
        status = "updates_available" if (check_only or dry_run) else "updated"
    elif skipped_modified:
        status = "skipped_modified_only"

    return {
        "status": status,
        "remote": remote,
        "branch": branch,
        "remote_commit": remote_commit,
        "added": added,
        "updated": updated,
        "unchanged": unchanged,
        "skipped_modified": skipped_modified,
        "backup_dir": backup_rel,
        "repaired_symlinks": repaired_symlinks,
    }


def build_session_start_update_prompt(root: Path, timeout: float = 5.0) -> str:
    """Return a `<framework-update-available>` prompt block if remote has updates."""
    if os.environ.get("TRELLIS_CHECK_REMOTE_ON_START") == "0":
        return ""

    config = read_trellis_config(root)
    fu_cfg = config.get("framework_update")
    if isinstance(fu_cfg, dict):
        if fu_cfg.get("check_on_session_start") is False:
            return ""
        cfg_timeout = fu_cfg.get("session_start_timeout")
        if isinstance(cfg_timeout, (int, float)) and cfg_timeout > 0:
            timeout = float(cfg_timeout)

    remote = _resolve_default_remote(root, config)
    branch = _resolve_default_branch(config)

    try:
        summary = run_framework_update(
            root,
            remote,
            branch,
            check_only=True,
            fetch_timeout=timeout,
        )
    except Exception:
        return ""

    if summary.get("status") != "updates_available":
        return ""

    added = list(summary.get("added") or [])
    updated = list(summary.get("updated") or [])
    added_count = len(added)
    updated_count = len(updated)
    total = added_count + updated_count
    changed = added + updated
    preview_items = changed[:5]
    preview = ", ".join(preview_items)
    if len(changed) > 5:
        preview += f" (+{len(changed) - 5} more)"

    remote_commit = summary.get("remote_commit") or "unknown"
    version_note = ""
    rc_ver, ver_bytes, _ = _run_git(["show", "FETCH_HEAD:.trellis/.version"], root, timeout=2.0)
    if rc_ver == 0:
        remote_ver = ver_bytes.decode("utf-8", errors="replace").strip()
        local_ver_path = root / ".trellis" / ".version"
        local_ver = local_ver_path.read_text(encoding="utf-8").strip() if local_ver_path.is_file() else ""
        if remote_ver and local_ver and remote_ver != local_ver:
            version_note = f" [version {local_ver} -> {remote_ver}]"
        elif remote_ver:
            version_note = f" [version {remote_ver}]"

    return (
        "<framework-update-available>\n"
        f"⚠️ FRAMEWORK UPDATE AVAILABLE ({remote}/{branch} @ {remote_commit}){version_note}: "
        f"{total} file(s) behind remote ({added_count} added, {updated_count} updated: {preview}).\n"
        "ACTION REQUIRED BEFORE STARTING WORK:\n"
        f"Before executing the user's task, inform the user that a newer version of the framework is available on `{remote}/{branch}` "
        f"and ask if they would like to update now (by running `python3 .trellis/scripts/update_framework.py --remote {remote} --branch {branch}`) "
        "or continue working with the current version.\n"
        "</framework-update-available>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Update Trellis framework files from a remote Git repository.")
    parser.add_argument("--remote", "-r", help="Remote name (origin, upstream, template) or Git URL")
    parser.add_argument("--branch", "-b", help="Target remote branch (default: config or main)")
    parser.add_argument("--check", action="store_true", help="Check if updates are available without modifying files")
    parser.add_argument("--dry-run", action="store_true", help="Preview files to be added/updated/skipped without writing")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite locally modified framework files (after backup)")
    parser.add_argument("--rollback", action="store_true", help="Restore files from the most recent .trellis/.backup-* directory")
    parser.add_argument("--skip-verify", action="store_true", help="Skip running verify.py after applying updates")
    parser.add_argument("--session-start-prompt", action="store_true", help="Emit <framework-update-available> block if remote updates exist")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    root = find_repo_root()
    config = read_trellis_config(root)

    if args.session_start_prompt:
        prompt_block = build_session_start_update_prompt(root)
        if prompt_block:
            print(prompt_block)
        return 0

    if args.rollback:
        ok, backup_name, restored = rollback_latest_backup(root)
        if args.json:
            print(json.dumps({
                "status": "rolled_back" if ok else "error",
                "backup_dir": backup_name if ok else None,
                "restored": restored,
                "message": None if ok else backup_name,
            }, indent=2))
        else:
            if ok:
                print(f"✔ Rolled back using .trellis/{backup_name} ({len(restored)} item(s) restored).")
            else:
                print(f"✖ Rollback failed: {backup_name}", file=sys.stderr)
        return 0 if ok else 1

    remote = args.remote or _resolve_default_remote(root, config)
    branch = args.branch or _resolve_default_branch(config)

    try:
        summary = run_framework_update(
            root,
            remote,
            branch,
            check_only=args.check,
            dry_run=args.dry_run,
            force=args.force,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        else:
            print(f"✖ Framework update failed: {exc}", file=sys.stderr)
        return 1

    verify_rc = 0
    if not args.check and not args.dry_run and not args.skip_verify and (summary["added"] or summary["updated"]):
        verify_script = root / ".trellis" / "scripts" / "verify.py"
        if verify_script.is_file():
            if not args.json:
                print("\n▶ Running post-update verification (verify.py)...")
            v_res = subprocess.run(
                [sys.executable, str(verify_script), "--stage", "all", "--format", "text"],
                cwd=str(root),
                stdout=subprocess.PIPE if args.json else None,
                stderr=subprocess.PIPE if args.json else None,
            )
            verify_rc = v_res.returncode
            summary["verification_passed"] = (verify_rc == 0)

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"=== Trellis Framework Updater ({remote}/{branch} @ {summary['remote_commit']}) ===")
        print(f"  Status           : {summary['status']}")
        print(f"  Added            : {len(summary['added'])}")
        print(f"  Updated          : {len(summary['updated'])}")
        print(f"  Unchanged        : {len(summary['unchanged'])}")
        print(f"  Skipped (local)  : {len(summary['skipped_modified'])}")
        if summary["backup_dir"]:
            print(f"  Backup           : {summary['backup_dir']}")

        if args.dry_run or args.check:
            for label, key in (("Added", "added"), ("Updated", "updated"), ("Skipped (modified)", "skipped_modified")):
                items = summary[key]
                if items:
                    print(f"\n{label}:")
                    for item in items:
                        print(f"  - {item}")
        elif summary["skipped_modified"]:
            print("\n⚠ Locally customized files preserved (re-run with --force to overwrite):")
            for item in summary["skipped_modified"]:
                print(f"  - {item}")

        if verify_rc != 0:
            print("\n✖ Post-update verification failed. You can revert with: python3 .trellis/scripts/update_framework.py --rollback", file=sys.stderr)

    return verify_rc


if __name__ == "__main__":
    sys.exit(main())
