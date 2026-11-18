# Technical Design: Worktree, Dynamic Context & CI/CD Pipeline

## 1. Subsystem Architecture

```
+-------------------------------------------------------------------------------+
|                                Coding Agents                                  |
|                 (Antigravity CLI, Claude Code, Copilot, Codex)                |
+---------------------------------------+---------------------------------------+
                                        |
       +--------------------------------+--------------------------------+
       |                                |                                |
       v                                v                                v
+-----------------------+   +-----------------------+   +-----------------------+
|  Git Worktree Engine  |   | Dynamic Context Engine|   |    CI/CD Pipelines    |
| (scripts/worktree.py) |   | (dynamic_context.py)  |   |  (.github/workflows/) |
+-----------+-----------+   +-----------+-----------+   +-----------+-----------+
            |                           |                           |
            v                           v                           v
+-----------------------+   +-----------------------+   +-----------------------+
| - .trellis/worktrees/ |   | - Scoped Spec Resolver|   | - ci.yml              |
| - task/<id> branch    |   | - LSP Diagnostics Hook|   | - pr-verify.yml       |
| - Sync / Merge Engine |   | - Graphify Subgraph   |   | - nightly-health.yml  |
| - task.json linking   |   | - Token budget filter |   | - verify.py execution |
+-----------------------+   +-----------------------+   +-----------------------+
```

## 2. Component Design Details

### A. Git Worktree Engine (`.trellis/scripts/worktree.py`)
- **Isolation Boundary**: Worktrees are created under `.trellis/worktrees/<task-id>`, which is explicitly ignored by `safe_commit.py` and git.
- **Branch Strategy**: Branch names follow `task/<task-id>`. Base branch defaults to `main` (or user-specified).
- **Metadata Synchronization**: Reads and mutates `.trellis/tasks/<task-dir>/task.json`:
  - `worktree_path`: `.trellis/worktrees/<task-id>`
  - `branch`: `task/<task-id>`
  - `base_branch`: `<base-branch>`
- **Commands**:
  - `create <task_id> [--base <branch>] [--force]`: Creates worktree and branch.
  - `list`: Reports active worktrees, commit hash, branch, dirty status.
  - `sync <task_id>`: Rebase or merge base branch changes into task worktree.
  - `merge <task_id> [--rebase] [--remove]`: Verifies worktree with `verify.py`, merges into base branch, optionally removes worktree.
  - `remove <task_id> [--force]`: Prunes worktree and clears task worktree path.

### B. Dynamic Context Engine (`.trellis/scripts/dynamic_context.py`)
- **Inputs**:
  - Git diff (staged and unstaged files).
  - Active task status and metadata from `.trellis/tasks/`.
  - Touched file paths mapped to `.trellis/spec/<layer>/`.
  - Active LSP diagnostics and symbol signatures on modified files.
  - Code graph community IDs from `graphify-out/graph.json`.
- **Outputs**:
  - `--format text`: Human-readable summary for console / status lines.
  - `--format json`: Machine-readable payload for programmatic hooks.
  - `--format system-prompt`: Markdown payload ready for injection into AI context windows.
- **Hooks Integration**:
  - Wire into `.agents/hooks/session-start.py`, `.claude/hooks/session-start.py`, and workflow state injectors.

### C. CI/CD Pipeline (`.github/workflows/`)
- **`ci.yml`**:
  - Triggers on `push` to `main` and `pull_request` to `main`.
  - Jobs:
    1. `verify`: Sets up Python 3.12, Node.js 20, installs dependencies.
    2. Runs self-healing verification: `python3 .trellis/scripts/verify.py --stage all --format text`.
    3. Runs Trellis task validation: `python3 .trellis/scripts/task.py validate`.
    4. Runs `agent-lsp doctor` to ensure language server configs are valid.
- **`pr-verify.yml`**:
  - Validates PR title and branch convention (`task/*`, `feat/*`, `fix/*`).
  - Ensures tasks have matching `branch` and `base_branch` in `task.json`.
  - Checks for spec updates if core architectural files changed.
- **`nightly-health.yml`**:
  - Weekly or nightly run checking external tool releases (`agent-lsp`, `trellis`, `graphify`).

## 3. Specifications & Guides
- `.trellis/spec/guides/git-worktrees.md`
- `.trellis/spec/guides/dynamic-context.md`
- `.trellis/spec/guides/cicd-pipeline.md`
- Updates to `.trellis/spec/guides/index.md` and `AGENTS.md`.
