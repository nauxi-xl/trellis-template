# Implementation Plan: Autonomous Self-Correction Loop

## Ordered Checklist

- [x] **Phase 1: Verification Runner Core Script**
  - [x] 1.1 Create `.trellis/scripts/verify.py` with:
    - Configuration reader for `.trellis/config.yaml` (`verification` block).
    - Auto-detection routines for Python (`pytest`, `mypy`/`pyright`, `ruff`), Node/TS (`npm test`, `tsc`, `eslint`), Rust (`cargo test/clippy/check`), Go (`go test`).
    - Staged runner: Typecheck → Lint → Tests.
    - Diagnostic parser extracting `file`, `line`, `error_type`, `message`.
    - Formatted output generator: standard terminal view, `--format json`, and `<self-healing-feedback>` block.
    - Iteration state persistence via `.trellis/tasks/<active-task>/.verify_state.json` (or `/tmp` fallback).
  - [x] 1.2 Make `.trellis/scripts/verify.py` executable (`chmod +x`).

- [x] **Phase 2: Configuration Schema & Settings**
  - [x] 2.1 Update `.trellis/config.yaml` with a documented `verification` configuration section:
    - `typecheck`, `lint`, `test`, `fail_fast`, `max_iterations`, and multi-package settings.

- [x] **Phase 3: Skill & Platform Integration**
  - [x] 3.1 Update `.agents/skills/trellis-check/SKILL.md`:
    - Incorporate automated `python3 .trellis/scripts/verify.py` as Step 3.
    - Add explicit self-healing repair protocol (3-attempt iteration cycle, Option A halt-and-yield rules).
  - [x] 3.2 Synchronize updated `trellis-check` skill to platform directories:
    - `.claude/skills/trellis-check/SKILL.md`
    - `.github/skills/trellis-check/SKILL.md`
  - [x] 3.3 Update [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md) with `verify.py` and self-healing verification documentation.

- [x] **Phase 4: Verification & Quality Testing**
  - [x] 4.1 Run `python3 .trellis/scripts/verify.py --help` and verify flag parsing.
  - [x] 4.2 Run `python3 .trellis/scripts/verify.py` on the repository to verify behavior when checks pass.
  - [x] 4.3 Test diagnostic formatting with a simulated failure.
  - [x] 4.4 Update code graph via `graphify update .`.

## Validation Commands

```bash
# 1. Test runner help and dry-run detection
python3 .trellis/scripts/verify.py --help
python3 .trellis/scripts/verify.py --dry-run

# 2. Test JSON format output
python3 .trellis/scripts/verify.py --format json

# 3. Verify skill mirror diffs
diff -u .agents/skills/trellis-check/SKILL.md .claude/skills/trellis-check/SKILL.md
diff -u .agents/skills/trellis-check/SKILL.md .github/skills/trellis-check/SKILL.md

# 4. Check git status
git status --short
```

## Risky Files & Rollback Points
- Changes add `.trellis/scripts/verify.py` and modify `.trellis/config.yaml`, `trellis-check` skills, and `AGENTS.md`.
- Rollback: `git checkout -- .trellis/config.yaml AGENTS.md CLAUDE.md .agents/skills/trellis-check/ .claude/skills/trellis-check/ .github/skills/trellis-check/ && rm -f .trellis/scripts/verify.py`.
