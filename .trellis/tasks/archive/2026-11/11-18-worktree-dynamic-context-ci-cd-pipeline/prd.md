# PRD: Git Isolated Worktree, Dynamic Context & CI/CD Pipeline

## 1. Problem Statement
As autonomous AI coding agents tackle larger, parallel tasks and complex codebases, three critical challenges emerge:
1. **Workspace Pollution & Concurrency Conflicts (Git Worktree)**:
   - Multiple agents or concurrent tasks modifying the same checkout create dirty working states, merge conflicts, and broken builds.
   - Without isolated task branches and dedicated worktrees, archiving tasks fails because `branch` and `base_branch` default to `main`.
2. **Static vs. Adaptive Context Overload (Dynamic Context)**:
   - Static context dumps inject excessive tokens (entire spec folders, unneeded guidelines) or miss crucial changes (staged files, LSP compiler diagnostics, topological dependencies from the knowledge graph).
   - Agents need contextual precision: dynamically resolving specs based on touched paths, surfacing LSP diagnostic deltas, and token-aware budgets.
3. **Absence of Automated Verification Gates (CI/CD)**:
   - There is no automated continuous integration to validate agent contributions, self-healing loop execution, task schema integrity, and LSP health before code is merged into `main`.

## 2. Goals & Objectives
1. **Git Isolated Worktree Manager**:
   - Provide a first-class `worktree.py` CLI and lifecycle automation.
   - Automatically provision `.trellis/worktrees/<task-id>` on a dedicated `task/<task-id>` branch.
   - Safely synchronize, verify, and merge task worktrees back to base branches with clean teardown.
2. **Dynamic Context Engine**:
   - Provide `dynamic_context.py` to assemble context dynamically:
     - Branch / worktree status and active diff.
     - Active task phase (PRD, design, implement, check).
     - Just-in-time spec injection matching only modified file paths and layers (frontend vs backend).
     - Active LSP language server status and diagnostics on modified files.
     - Code Graph (`graphify`) neighborhood context for touched modules.
3. **Comprehensive CI/CD Pipeline**:
   - Implement GitHub Actions workflows under `.github/workflows/`:
     - `ci.yml`: Full verification matrix (Python, Node, tests, self-healing runner, task validation, LSP doctor).
     - `pr-verify.yml`: Pull request sanity gate, branch compliance, spec consistency.
     - `nightly-health.yml`: Scheduled health check for tools, links, and dependencies.
4. **Framework Integration & Documentation**:
   - Trellis specifications and thinking guides under `.trellis/spec/guides/`.
   - Update `AGENTS.md` and `.trellis/spec/guides/index.md`.

## 3. Success Metrics & Verification
- `python3 .trellis/scripts/worktree.py create <task-id>` successfully spins up an isolated worktree and updates `task.json`.
- `python3 .trellis/scripts/dynamic_context.py` generates scoped, token-efficient dynamic context across text, JSON, and system-prompt formats.
- `.github/workflows/` contains valid YAML workflows passing linting and syntax checks.
- Self-healing verify loop and task validation pass with 0 errors.
