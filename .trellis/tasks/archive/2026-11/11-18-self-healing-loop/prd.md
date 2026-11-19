# Autonomous Self-Correction Loop (Self-Healing Test & Lint Runner)

## Goal

Provide AI coding agents in Trellis with an autonomous, self-correcting feedback loop that automatically executes project linters, type-checkers, and test suites, parses failure traces into structured diagnostic feedback, and guides the agent through bounded self-repair cycles before finishing or committing code.

## Confirmed Facts & Technical Context

- **Current State**:
  - `trellis-check` ([.agents/skills/trellis-check/SKILL.md](.agents/skills/trellis-check/SKILL.md)) defines a manual review checklist and instructs the agent to run project checks, but lacks an automated discovery runner, structured diagnostic parsing, and loop management.
  - `.trellis/config.yaml` holds project-level settings (session commit, packages, channel worker guard), but does not have a declarative `verification` section for test/lint commands.
  - Phase 2.2 in [.trellis/workflow.md](.trellis/workflow.md) states "If issues are found → fix → re-check, until green", but provides no automated diagnostic envelope.

## Key Decisions

- **Exhaustion Safety Policy**: Option A (Halt & Yield with Root-Cause Diagnostics). If the 3-attempt iteration limit is reached without achieving all-green checks, the runner preserves the uncommitted working tree, outputs a comprehensive root-cause analysis and failed test matrix, and yields control to the user rather than blindly rolling back or looping infinitely.
- **Auto-Discovery Hierarchy**: `verify.py` checks explicit definitions in `.trellis/config.yaml` first, falling back to auto-detecting language files (`pyproject.toml`/`setup.py`/`requirements.txt` for Python, `package.json` for JS/TS, `Cargo.toml` for Rust, `go.mod` for Go).

## Requirements

- **REQ-1 (Verification Runner Script)**:
  - Create `.trellis/scripts/verify.py` capable of:
    - Auto-detecting project verification commands (Python `pytest`/`ruff`/`mypy`, JS/TS `npm test`/`tsc`/`eslint`, Rust `cargo test`/`clippy`, Go `go test`).
    - Reading custom overrides from `.trellis/config.yaml` under a new `verification` block.
    - Executing checks systematically (Typecheck → Lint → Tests) with fail-fast or full-report modes.
- **REQ-2 (Structured Diagnostic Parsing & Feedback Envelope)**:
  - Parse compiler errors, linter violations, and test failure tracebacks into clean JSON and Markdown diagnostics (identifying failing file, line number, test name, and error message).
  - Format output as an actionable `<self-healing-feedback>` diagnostic block that gives the agent exact repair targets.
- **REQ-3 (Bounded Self-Healing Loop Management)**:
  - Implement loop guardrails with an iteration counter (default max 3 attempts) to prevent infinite loops and runaway token expenditure.
  - Provide differential diagnosis guidance: correlate failing tests with recent `git diff` changes.
  - Enforce Option A on exhaustion: halt, preserve work, and display root-cause diagnostics.
- **REQ-4 (Trellis Check & Workflow Integration)**:
  - Update `.agents/skills/trellis-check/SKILL.md` (and platform mirrors) to incorporate `verify.py` as the canonical verification runner.
  - Integrate with Phase 2.2 and Phase 3.4 so the agent automatically triggers the self-healing cycle before attempting to commit or finish work.
- **REQ-5 (Documentation & Configuration Schema)**:
  - Update `.trellis/config.yaml` with documented `verification` settings.
  - Document the self-healing loop in [AGENTS.md](AGENTS.md) and [.trellis/spec/guides/](.trellis/spec/guides/).

## Acceptance Criteria

- [x] `AC-1`: `.trellis/scripts/verify.py` executes successfully, auto-detecting or reading configured checks from `.trellis/config.yaml`.
- [x] `AC-2`: Running `python3 .trellis/scripts/verify.py --format json` produces structured diagnostics on failures.
- [x] `AC-3`: Running `python3 .trellis/scripts/verify.py` on a passing project prints a clean green verification report.
- [x] `AC-4`: `trellis-check` skill documentation directs agents to invoke the verification runner and follow the self-healing loop protocol.
- [x] `AC-5`: Exhaustion behavior halts execution and yields root-cause diagnostics without clobbering the working tree.
- [x] `AC-6`: `.trellis/config.yaml` has verified configuration examples for Python, Node/TS, Rust, and Go.
- [x] `AC-7`: Multi-platform skill mirrors and master instructions (`AGENTS.md`, `CLAUDE.md`) are synchronized.

## Out of Scope

- Installing third-party language runtimes or package managers if they are not already installed on the host.
- Automatically modifying tests to pass (tests are ground-truth contracts unless the PRD explicitly specifies changing test assertions).
