# Git Isolated Worktrees Guide

> Specifications and best practices for creating, synchronizing, and merging isolated git worktrees per task in Trellis.

---

## Overview

When multiple agents collaborate or developers switch between feature branches, working in a single git checkout causes problems:
- Incomplete edits break parallel test runs.
- Committing on `main` causes task archiving failures (since `branch` and `base_branch` are identical).
- File lock collisions happen on build artifacts and dependencies.

Trellis solves this by dedicating a git worktree to each task under `.trellis/worktrees/<task-id>/`.

---

## Worktree Lifecycle

```
[task.py create] ──> [worktree.py create] ──> [Agent work in worktree] ──> [worktree.py merge] ──> [task.py archive]
```

### 1. Creation (`worktree.py create <task-id>`)
- Spawns branch `task/<task-id>` from `main`.
- Checks out files in `.trellis/worktrees/<task-id>/`.
- Records `worktree_path: ".trellis/worktrees/<task-id>"` and `branch: "task/<task-id>"` in `task.json`.

### 2. Inspection (`worktree.py list`)
- Formats porcelain output from `git worktree list`.
- Displays worktree type (`MAIN` vs `TREE`), branch, commit hash, dirty status, and bound task ID.

### 3. Synchronization (`worktree.py sync <task-id>`)
- Performs safe upstream fetches and rebase operations against the task's `base_branch`.

### 4. Merging & Teardown (`worktree.py merge <task-id> [--remove]`)
- Validates that the worktree has no uncommitted dirty files.
- Executes `python3 .trellis/scripts/verify.py` inside the worktree as a pre-merge gate.
- Merges `task/<task-id>` into `base_branch`.
- Prunes worktree directory and resets `worktree_path` in `task.json`.

---

## Command Reference

```bash
# Create worktree for active task
python3 .trellis/scripts/worktree.py create <task-id>

# List all active worktrees and their statuses
python3 .trellis/scripts/worktree.py list

# Sync worktree with latest changes from main
python3 .trellis/scripts/worktree.py sync <task-id>

# Run verification and merge into main, then clean up worktree
python3 .trellis/scripts/worktree.py merge <task-id> --remove

# Manually remove a worktree
python3 .trellis/scripts/worktree.py remove <task-id>
```
