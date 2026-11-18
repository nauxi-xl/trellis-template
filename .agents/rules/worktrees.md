---
trigger: always_on
description: Manage and navigate isolated git worktrees for tasks using python3 .trellis/scripts/worktree.py.
---

## Git Isolated Worktrees (`worktree.py`)

In this framework, complex, multi-agent, or feature-driven tasks run in isolated git worktrees located under `.trellis/worktrees/<task-id>/`. This guarantees zero workspace pollution, avoids dirty tree collisions across parallel agents, and ensures clean branch segregation.

---

### Core Rules

1. **Task Worktree Lifecycle**:
   - When beginning a new task: create an isolated worktree via `python3 .trellis/scripts/worktree.py create <task-id>`.
   - Never write production code directly to `main` when working on a scoped task.
   - Worktree paths (`.trellis/worktrees/`) are automatically gitignored and safe from commits.
2. **Inspection & Status**:
   - Check all active worktrees and dirty states with `python3 .trellis/scripts/worktree.py list`.
3. **Synchronization**:
   - If `main` advances while a task is in progress: run `python3 .trellis/scripts/worktree.py sync <task-id>` to rebase against `main`.
4. **Verification & Merging**:
   - Before merging: run `python3 .trellis/scripts/worktree.py merge <task-id> --remove`.
   - The merge command automatically validates `python3 .trellis/scripts/verify.py` in the worktree before executing the merge.
