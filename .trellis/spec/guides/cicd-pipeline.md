# Continuous Integration & Deployment (CI/CD) Guide

> Specifications and best practices for automated testing, pull request validation, and toolchain health monitoring in Trellis.

---

## Overview

The CI/CD pipeline protects repository integrity by verifying that every change adheres to project conventions, passes the self-healing verification suite, keeps task metadata consistent, and preserves code graph and LSP health.

---

## Workflows Breakdown

### 1. Main CI (`.github/workflows/ci.yml`)
- **Trigger**: Every push or pull request targeting `main`.
- **Matrix**: Tested against multiple Python (3.11, 3.12) and Node (20.x) versions.
- **Verification Stages**:
  1. Installs `agent-lsp` and project language servers (`pyright`, `typescript-language-server`).
  2. Runs `agent-lsp doctor` to check server registration.
  3. Executes the self-healing verification runner: `python3 .trellis/scripts/verify.py --stage all --format text`.
  4. Validates Trellis tasks and spec context manifests: `python3 .trellis/scripts/task.py validate`.
  5. Verifies the Dynamic Context Engine: `python3 .trellis/scripts/dynamic_context.py --format text`.

### 2. PR Sanity Gate (`.github/workflows/pr-verify.yml`)
- **Trigger**: Opening, updating, or reopening a PR.
- **Enforcement Rules**:
  - **Branch Naming**: PRs originating directly from `main` or `master` are blocked; work must occur in `task/*`, `feat/*`, `fix/*`.
  - **No Leaked Worktrees**: Fails immediately if `.trellis/worktrees/` directories or metadata are committed.
  - **Task Metadata Consistency**: Ensures tasks do not have identical `branch` and `base_branch` pointing to `main`.

### 3. Nightly Health Check (`.github/workflows/nightly-health.yml`)
- **Trigger**: Scheduled weekly on Mondays at 02:00 UTC or manual trigger.
- **Checks**: Scans for new upstream versions of `agent-lsp`, `trellis`, `graphifyy`, and verifies dry-run verification health.
