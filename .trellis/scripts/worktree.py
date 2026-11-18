#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trellis Git Worktree Lifecycle Manager.

Manages isolated git worktrees per task for parallel agent execution,
clean branch management, and zero-conflict multi-agent development.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
    """Locate the repository root containing .trellis/ or .git/."""
    cur = (start or Path.cwd()).resolve()
    while cur != cur.parent:
        if (cur / ".trellis").is_dir() or (cur / ".git").is_dir() or (cur / ".git").is_file():
            return cur
        cur = cur.parent
    return (start or Path.cwd()).resolve()


REPO_ROOT = find_repo_root()


def run_git(args: List[str], cwd: Optional[Path] = None, check: bool = False) -> Tuple[int, str, str]:
    """Execute a git command and return (returncode, stdout, stderr)."""
    target_cwd = str(cwd or REPO_ROOT)
    res = subprocess.run(
        ["git"] + args,
        cwd=target_cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def find_task_dir(task_identifier: str) -> Tuple[Path, dict]:
    """Resolve task directory and its parsed task.json."""
    tasks_root = REPO_ROOT / ".trellis" / "tasks"
    if not tasks_root.is_dir():
        raise FileNotFoundError(f"Tasks directory not found: {tasks_root}")

    # Check exact match
    direct = tasks_root / task_identifier
    if direct.is_dir() and (direct / "task.json").is_file():
        task_json = json.loads((direct / "task.json").read_text(encoding="utf-8"))
        return direct, task_json

    # Check by prefix / id match
    matches = []
    for d in tasks_root.iterdir():
        if d.is_dir() and (d / "task.json").is_file():
            try:
                data = json.loads((d / "task.json").read_text(encoding="utf-8"))
                if task_identifier in (d.name, data.get("id"), data.get("name")):
                    matches.append((d, data))
                elif task_identifier.lower() in d.name.lower():
                    matches.append((d, data))
            except Exception:
                continue

    if not matches:
        raise FileNotFoundError(f"Task '{task_identifier}' not found under {tasks_root}")
    if len(matches) > 1:
        # Prefer exact name or id
        for d, data in matches:
            if task_identifier in (d.name, data.get("id")):
                return d, data
        names = ", ".join(d.name for d, _ in matches)
        raise ValueError(f"Ambiguous task identifier '{task_identifier}', matches: {names}")

    return matches[0]


def update_task_json(task_dir: Path, updates: dict) -> None:
    """Safely update task.json with new fields."""
    task_json_path = task_dir / "task.json"
    data = json.loads(task_json_path.read_text(encoding="utf-8"))
    data.update(updates)
    task_json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@dataclass
class WorktreeInfo:
    path: Path
    branch: str
    commit: str
    is_bare: bool
    is_main: bool
    is_dirty: bool
    task_id: Optional[str] = None


def get_all_worktrees() -> List[WorktreeInfo]:
    """Parse git worktree list --porcelain."""
    code, out, _ = run_git(["worktree", "list", "--porcelain"])
    if code != 0 or not out:
        return []

    worktrees: List[WorktreeInfo] = []
    current_entry: Dict[str, str] = {}

    for line in out.splitlines():
        line = line.strip()
        if not line:
            if "worktree" in current_entry:
                w_path = Path(current_entry["worktree"]).resolve()
                branch = current_entry.get("branch", "").replace("refs/heads/", "")
                commit = current_entry.get("HEAD", "")[:7]
                is_bare = "bare" in current_entry
                is_main = len(worktrees) == 0

                # Check dirty
                is_dirty = False
                if w_path.is_dir() and not is_bare:
                    s_code, s_out, _ = run_git(["status", "--porcelain"], cwd=w_path)
                    is_dirty = bool(s_out)

                # Check task_id association
                task_id = None
                if ".trellis" in str(w_path) and "worktrees" in str(w_path):
                    task_id = w_path.name
                elif branch.startswith("task/"):
                    task_id = branch[len("task/") :]

                worktrees.append(
                    WorktreeInfo(
                        path=w_path,
                        branch=branch,
                        commit=commit,
                        is_bare=is_bare,
                        is_main=is_main,
                        is_dirty=is_dirty,
                        task_id=task_id,
                    )
                )
                current_entry = {}
            continue

        parts = line.split(" ", 1)
        key = parts[0]
        val = parts[1] if len(parts) > 1 else ""
        current_entry[key] = val

    if "worktree" in current_entry:
        w_path = Path(current_entry["worktree"]).resolve()
        branch = current_entry.get("branch", "").replace("refs/heads/", "")
        commit = current_entry.get("HEAD", "")[:7]
        is_bare = "bare" in current_entry
        is_main = len(worktrees) == 0
        is_dirty = False
        if w_path.is_dir() and not is_bare:
            s_code, s_out, _ = run_git(["status", "--porcelain"], cwd=w_path)
            is_dirty = bool(s_out)
        task_id = None
        if ".trellis" in str(w_path) and "worktrees" in str(w_path):
            task_id = w_path.name
        elif branch.startswith("task/"):
            task_id = branch[len("task/") :]

        worktrees.append(
            WorktreeInfo(
                path=w_path,
                branch=branch,
                commit=commit,
                is_bare=is_bare,
                is_main=is_main,
                is_dirty=is_dirty,
                task_id=task_id,
            )
        )

    return worktrees


# -----------------------------------------------------------------------------
# Subcommands
# -----------------------------------------------------------------------------

def cmd_create(args: argparse.Namespace) -> int:
    """Create an isolated worktree for a task."""
    task_dir, task_data = find_task_dir(args.task)
    task_id = task_data.get("id") or task_dir.name
    branch = args.branch or f"task/{task_id}"
    base_branch = args.base or task_data.get("base_branch") or "main"

    worktrees_dir = REPO_ROOT / ".trellis" / "worktrees"
    worktrees_dir.mkdir(parents=True, exist_ok=True)
    target_worktree = (worktrees_dir / task_id).resolve()

    if target_worktree.is_dir():
        if args.force:
            print(f"⚠ Removing existing worktree directory: {target_worktree}")
            run_git(["worktree", "remove", "--force", str(target_worktree)])
            if target_worktree.exists():
                shutil.rmtree(target_worktree, ignore_errors=True)
        else:
            print(f"Error: Worktree directory already exists: {target_worktree}")
            print("Use --force to overwrite or run `worktree.py remove <task>` first.")
            return 1

    # Check if branch exists
    code, _, _ = run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"])
    branch_exists = (code == 0)

    print(f"▶ Creating worktree for task '{task_id}'...")
    print(f"  Branch     : {branch} (exists: {branch_exists})")
    print(f"  Base       : {base_branch}")
    print(f"  Target Dir : {target_worktree}")

    if branch_exists:
        git_args = ["worktree", "add", str(target_worktree), branch]
    else:
        git_args = ["worktree", "add", "-b", branch, str(target_worktree), base_branch]

    rc, stdout, stderr = run_git(git_args)
    if rc != 0:
        print(f"✖ Failed to create git worktree: {stderr}")
        return 1

    # Ensure task.json is updated
    rel_worktree = os.path.relpath(target_worktree, REPO_ROOT).replace("\\", "/")
    update_task_json(
        task_dir,
        {
            "branch": branch,
            "base_branch": base_branch,
            "worktree_path": rel_worktree,
        },
    )

    print("✔ Worktree successfully created!")
    print(f"  To enter worktree: cd {target_worktree}")
    print(f"  Updated task.json: branch='{branch}', worktree_path='{rel_worktree}'")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all registered worktrees."""
    worktrees = get_all_worktrees()
    if not worktrees:
        print("No git worktrees found.")
        return 0

    if args.json:
        data = [
            {
                "path": str(w.path),
                "branch": w.branch,
                "commit": w.commit,
                "is_main": w.is_main,
                "is_dirty": w.is_dirty,
                "task_id": w.task_id,
            }
            for w in worktrees
        ]
        print(json.dumps(data, indent=2))
        return 0

    print("=== Git Worktrees ===")
    fmt = "{:<4} {:<32} {:<10} {:<8} {:<8} {}"
    print(fmt.format("Type", "Branch", "Commit", "Status", "Task", "Path"))
    print("-" * 88)
    for w in worktrees:
        kind = "MAIN" if w.is_main else ("BARE" if w.is_bare else "TREE")
        status = "DIRTY" if w.is_dirty else "clean"
        task_tag = w.task_id or "-"
        rel_path = os.path.relpath(w.path, REPO_ROOT).replace("\\", "/")
        print(fmt.format(kind, w.branch[:31], w.commit, status, task_tag[:8], rel_path))

    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """Sync a task worktree by rebasing from its base branch."""
    task_dir, task_data = find_task_dir(args.task)
    task_id = task_data.get("id") or task_dir.name
    worktree_path = task_data.get("worktree_path")
    base_branch = task_data.get("base_branch") or "main"

    if not worktree_path:
        target_dir = (REPO_ROOT / ".trellis" / "worktrees" / task_id).resolve()
        if target_dir.is_dir():
            worktree_path = str(target_dir)
        else:
            print(f"Error: Task '{task_id}' has no worktree configured.")
            return 1

    w_dir = (REPO_ROOT / worktree_path).resolve()
    if not w_dir.is_dir():
        print(f"Error: Worktree path does not exist: {w_dir}")
        return 1

    print(f"▶ Syncing worktree '{task_id}' with base branch '{base_branch}'...")
    # Fetch
    run_git(["fetch", "origin"], cwd=w_dir)
    # Rebase
    rc, out, err = run_git(["rebase", base_branch], cwd=w_dir)
    if rc != 0:
        print(f"✖ Rebase encountered conflicts or failed:\n{err or out}")
        print("Please resolve conflicts manually inside the worktree.")
        return rc

    print(f"✔ Successfully synced worktree with '{base_branch}'.")
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    """Verify and merge a task worktree into its base branch."""
    task_dir, task_data = find_task_dir(args.task)
    task_id = task_data.get("id") or task_dir.name
    branch = task_data.get("branch")
    base_branch = task_data.get("base_branch") or "main"
    worktree_path = task_data.get("worktree_path")

    if not branch:
        print(f"Error: Task '{task_id}' has no branch recorded in task.json.")
        return 1

    w_dir = (REPO_ROOT / worktree_path).resolve() if worktree_path else None

    # Step 1: Check dirty state
    if w_dir and w_dir.is_dir():
        _, dirty_out, _ = run_git(["status", "--porcelain"], cwd=w_dir)
        if dirty_out:
            print(f"✖ Error: Worktree at {w_dir} has uncommitted changes:")
            print(dirty_out)
            print("Commit or stash your changes before merging.")
            return 1

        # Step 2: Verification check if requested
        if not args.skip_verify:
            verify_script = REPO_ROOT / ".trellis" / "scripts" / "verify.py"
            if verify_script.is_file():
                print("▶ Running self-healing verification in worktree before merge...")
                v_res = subprocess.run([sys.executable, str(verify_script)], cwd=w_dir)
                if v_res.returncode != 0:
                    print("✖ Verification failed! Fix issues before merging.")
                    return v_res.returncode

    # Step 3: Merge in main repo
    print(f"▶ Merging branch '{branch}' into '{base_branch}' in main repository...")
    run_git(["checkout", base_branch], check=True)
    m_args = ["merge", "--no-ff", branch, "-m", f"feat({task_id}): merge {branch} into {base_branch}"]
    if args.rebase:
        m_args = ["rebase", branch]

    m_rc, m_out, m_err = run_git(m_args)
    if m_rc != 0:
        print(f"✖ Merge failed:\n{m_err or m_out}")
        return m_rc

    print(f"✔ Successfully merged '{branch}' into '{base_branch}'.")

    # Step 4: Optional teardown
    if args.remove and w_dir and w_dir.is_dir():
        print(f"▶ Removing worktree: {w_dir}")
        run_git(["worktree", "remove", str(w_dir)])
        run_git(["worktree", "prune"])
        update_task_json(task_dir, {"worktree_path": None})
        print("✔ Worktree removed and pruned.")

    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    """Remove a task worktree."""
    try:
        task_dir, task_data = find_task_dir(args.task)
        task_id = task_data.get("id") or task_dir.name
        worktree_path = task_data.get("worktree_path") or f".trellis/worktrees/{task_id}"
    except FileNotFoundError:
        task_dir = None
        task_id = args.task
        worktree_path = f".trellis/worktrees/{task_id}"

    w_dir = (REPO_ROOT / worktree_path).resolve()
    print(f"▶ Removing worktree for task '{task_id}' ({w_dir})...")

    cmd = ["worktree", "remove"]
    if args.force:
        cmd.append("--force")
    cmd.append(str(w_dir))

    rc, out, err = run_git(cmd)
    if rc != 0 and w_dir.is_dir():
        if args.force:
            shutil.rmtree(w_dir, ignore_errors=True)
        else:
            print(f"✖ Failed to remove worktree: {err or out}")
            print("Use --force to force removal.")
            return rc

    run_git(["worktree", "prune"])
    if task_dir is not None:
        update_task_json(task_dir, {"worktree_path": None})
    print(f"✔ Worktree removed for task '{task_id}'.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Trellis Git Worktree Lifecycle Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create an isolated worktree for a task")
    p_create.add_argument("task", help="Task ID or directory name")
    p_create.add_argument("--branch", "-b", help="Feature branch name (default: task/<task_id>)")
    p_create.add_argument("--base", help="Base branch (default: main)")
    p_create.add_argument("--force", "-f", action="store_true", help="Overwrite existing worktree dir")
    p_create.set_defaults(func=cmd_create)

    # list
    p_list = subparsers.add_parser("list", help="List all registered worktrees")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")
    p_list.set_defaults(func=cmd_list)

    # sync
    p_sync = subparsers.add_parser("sync", help="Sync task worktree from base branch")
    p_sync.add_argument("task", help="Task ID or directory name")
    p_sync.set_defaults(func=cmd_sync)

    # merge
    p_merge = subparsers.add_parser("merge", help="Verify and merge task worktree into base branch")
    p_merge.add_argument("task", help="Task ID or directory name")
    p_merge.add_argument("--rebase", action="store_true", help="Rebase instead of merge commit")
    p_merge.add_argument("--skip-verify", action="store_true", help="Skip running verify.py pre-merge")
    p_merge.add_argument("--remove", "-r", action="store_true", help="Remove worktree after successful merge")
    p_merge.set_defaults(func=cmd_merge)

    # remove
    p_remove = subparsers.add_parser("remove", help="Remove task worktree")
    p_remove.add_argument("task", help="Task ID or directory name")
    p_remove.add_argument("--force", "-f", action="store_true", help="Force removal even if uncommitted changes exist")
    p_remove.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
