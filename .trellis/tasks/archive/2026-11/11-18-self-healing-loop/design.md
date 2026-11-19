# Technical Design: Autonomous Self-Correction Loop

## Architecture & Flow Diagram

The Self-Correction Loop establishes an automated, closed-loop execution and verification harness between the coding agent and the project compiler/test suite.

```
                      +-----------------------------+
                      | Agent Completes Code Edit   |
                      | (Phase 2.1 Implementation)  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   trellis-check Initiated   |
                      |  Runs: verify.py [--fix]    |
                      +--------------+--------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                       verify.py Execution Engine                         |
|                                                                         |
|  1. Discovery: Load .trellis/config.yaml or auto-detect stack          |
|  2. Execution:                                                          |
|     Step A: Typecheck  (tsc / mypy / pyright / cargo check)             |
|     Step B: Lint       (eslint / ruff / cargo clippy)                   |
|     Step C: Tests      (npm test / pytest / cargo test / go test)       |
+------------------------------------+------------------------------------+
                                     |
                  +------------------+------------------+
                  |                                     |
               [PASS]                                [FAIL]
                  |                                     |
                  v                                     v
        +-------------------+           +-------------------------------+
        | All Checks Green  |           | Parse Diagnostics:            |
        | Proceed to Spec & |           | - File, line, error code      |
        | Phase 3 Commit    |           | - Failing assertion traceback |
        +-------------------+           +---------------+---------------+
                                                        |
                                                        v
                                        +-------------------------------+
                                        | Iteration Counter < 3?        |
                                        +-------+---------------+-------+
                                                |               |
                                              [YES]            [NO]
                                                |               |
                                                v               v
                        +-------------------------------+   +-----------+
                        | Emit <self-healing-feedback>  |   | OPTION A  |
                        | Agent inspects exact location |   | Halt &    |
                        | and applies targeted fix      |   | Yield to  |
                        +---------------+---------------+   | User with |
                                        |                   | Root-Cause|
                                        | (Loop back)       | Report    |
                                        +-----------------> +-----------+
```

## Detailed Component Specifications

### 1. Verification Runner (`.trellis/scripts/verify.py`)

#### A. Stack Auto-Detection & Priority
`verify.py` evaluates detection rules in order:
1. **Explicit Config (`.trellis/config.yaml`)**:
   ```yaml
   verification:
     typecheck: "mypy ."
     lint: "ruff check ."
     test: "pytest -q"
     fail_fast: true
   ```
2. **Auto-Detection Fallback**:
   * **Node / TypeScript**:
     - `tsconfig.json` → Typecheck: `npx tsc --noEmit`
     - `package.json` (`scripts.lint`) → Lint: `npm run lint`
     - `package.json` (`scripts.test`) → Test: `npm test`
   * **Python**:
     - `pyproject.toml` / `mypy.ini` → Typecheck: `mypy .` or `pyright`
     - `ruff` installed → Lint: `ruff check .`
     - `pytest.ini` / `tests/` → Test: `pytest`
   * **Rust**:
     - `Cargo.toml` → Typecheck: `cargo check`, Lint: `cargo clippy`, Test: `cargo test`
   * **Go**:
     - `go.mod` → Test: `go test ./...`

#### B. Diagnostic Parser
Extracts structured failure metadata:
```json
{
  "status": "failure",
  "stage": "test",
  "command": "pytest",
  "iteration": 1,
  "max_iterations": 3,
  "failures": [
    {
      "file": "tests/test_parser.py",
      "line": 42,
      "test_name": "test_invalid_syntax",
      "error_type": "AssertionError",
      "message": "Expected ValueError but nothing was raised",
      "snippet": "assert error is not None"
    }
  ]
}
```

#### C. Feedback Envelope
Prints human-readable and agent-optimized output:
```markdown
<self-healing-feedback iteration="1" max_iterations="3">
[VERIFICATION FAILURE]: Stage 'test' failed using command 'pytest'

Failing Target:
- tests/test_parser.py:42: AssertionError: Expected ValueError but nothing was raised

Required Action:
1. Inspect the source file matching the failure (tests/test_parser.py:42).
2. Compare with recent changes (git diff).
3. Apply a minimal, targeted patch to resolve the failure.
4. Re-run 'python3 .trellis/scripts/verify.py'. Do not finish the task until all checks are green.
</self-healing-feedback>
```

### 2. Safety & Loop Boundary Guardrails
* **Max Iterations**: Fixed at 3 attempts.
* **Option A Halt Protocol**: If iteration 3 fails, the script outputs `[SELF-HEALING EXHAUSTION: HALT & YIELD]`, displays the persistent failure trace, and instructs the agent to ask the user for guidance rather than modifying code blindly.
* **No Test Mutating**: The agent is strictly instructed never to delete or weaken test assertions unless explicitly requested by the user.

### 3. Skill & Workflow Integration
* **`trellis-check` Skill Update**:
  - Replaces manual instructions in Step 3 of [.agents/skills/trellis-check/SKILL.md](.agents/skills/trellis-check/SKILL.md) with executing `python3 ./.trellis/scripts/verify.py`.
  - Injects the iterative repair loop directly into the skill steps.
* **`AGENTS.md` and `CLAUDE.md` Update**:
  - Documents `verify.py` and the self-healing feedback loop as standard tooling under Project Knowledge & Tools.
