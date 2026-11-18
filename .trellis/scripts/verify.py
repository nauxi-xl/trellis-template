#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trellis Autonomous Self-Correction Loop / Verification Runner.

Discovers and executes project typechecks, linters, and test suites.
Parses failure diagnostics into structured agent-actionable feedback,
and manages bounded self-healing iterations before task completion.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

# Force UTF-8 stream configuration
if sys.platform.startswith("win"):
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def find_trellis_root(start: Optional[Path] = None) -> Path:
    """Locate the repository root containing .trellis/."""
    cur = (start or Path.cwd()).resolve()
    while cur != cur.parent:
        if (cur / ".trellis").is_dir():
            return cur
        cur = cur.parent
    return (start or Path.cwd()).resolve()


# Setup imports from .trellis/scripts/common
REPO_ROOT = find_trellis_root()
SCRIPTS_DIR = REPO_ROOT / ".trellis" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from common.trellis_config import read_trellis_config
except ImportError:
    def read_trellis_config(root=None):
        return {}


@dataclass
class DiagnosticFailure:
    file: str
    line: Optional[int] = None
    column: Optional[int] = None
    rule: Optional[str] = None
    error_type: Optional[str] = None
    message: str = ""
    snippet: Optional[str] = None


@dataclass
class StageResult:
    stage: str
    command: str
    passed: bool
    returncode: int
    duration_s: float
    stdout: str
    stderr: str
    failures: List[DiagnosticFailure] = field(default_factory=list)


# ------------------------------------------------------------------------------
# Diagnostic Parsers
# ------------------------------------------------------------------------------

def parse_diagnostics(output: str) -> List[DiagnosticFailure]:
    """Parse common linter, compiler, and test errors from text output."""
    failures: List[DiagnosticFailure] = []
    seen = set()

    # Pattern 1: standard file:line:col: (error|warning): msg (tsc, gcc, ruff, eslint, mypy)
    p_standard = re.compile(
        r'^(?P<file>[a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+):(?P<line>\d+)(?::(?P<col>\d+))?:?\s+(?:(?P<rule>TS\d+|[A-Z]\d+|[\w\-]+):\s+)?(?P<msg>.+)$',
        re.MULTILINE
    )
    for m in p_standard.finditer(output):
        f = m.group("file").replace("\\", "/")
        line = int(m.group("line"))
        col = int(m.group("col")) if m.group("col") else None
        rule = m.group("rule")
        msg = m.group("msg").strip()
        key = (f, line, msg)
        if key not in seen:
            seen.add(key)
            failures.append(DiagnosticFailure(file=f, line=line, column=col, rule=rule, message=msg))

    # Pattern 2: pytest test failures: FAILED path/to/test.py::test_func - AssertionError: ...
    p_pytest = re.compile(
        r'^FAILED\s+(?P<file>[^:\n]+)::(?P<test>\w+)(?:\s+-\s+(?P<msg>.+))?$',
        re.MULTILINE
    )
    for m in p_pytest.finditer(output):
        f = m.group("file").strip().replace("\\", "/")
        test_name = m.group("test")
        msg = m.group("msg") or f"Test failed: {test_name}"
        key = (f, test_name, msg)
        if key not in seen:
            seen.add(key)
            failures.append(DiagnosticFailure(file=f, error_type=test_name, message=msg))

    # Pattern 3: Cargo errors: error[E0308]: ... --> src/main.rs:10:5
    p_cargo = re.compile(
        r'error(?:\[(?P<rule>[A-Z0-9]+)\])?:\s+(?P<msg>[^\n]+)\n\s+-->\s+(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+)',
        re.MULTILINE
    )
    for m in p_cargo.finditer(output):
        f = m.group("file").strip().replace("\\", "/")
        line = int(m.group("line"))
        col = int(m.group("col"))
        rule = m.group("rule")
        msg = m.group("msg").strip()
        key = (f, line, msg)
        if key not in seen:
            seen.add(key)
            failures.append(DiagnosticFailure(file=f, line=line, column=col, rule=rule, message=msg))

    return failures


# ------------------------------------------------------------------------------
# Auto-Detection Logic
# ------------------------------------------------------------------------------

def detect_verification_stack(root: Path) -> dict[str, Optional[str]]:
    """Inspect the codebase to infer typecheck, lint, and test commands."""
    config = read_trellis_config(root)
    custom = config.get("verification", {})
    if not isinstance(custom, dict):
        custom = {}

    typecheck_cmd = custom.get("typecheck")
    lint_cmd = custom.get("lint")
    test_cmd = custom.get("test")

    # 1. Node / TypeScript
    pkg_json = root / "package.json"
    tsconfig = root / "tsconfig.json"
    if pkg_json.is_file():
        try:
            pkg_data = json.loads(pkg_json.read_text(encoding="utf-8"))
            scripts = pkg_data.get("scripts", {})
            if not test_cmd and "test" in scripts:
                test_cmd = "npm test"
            if not lint_cmd and "lint" in scripts:
                lint_cmd = "npm run lint"
        except Exception:
            pass

    if tsconfig.is_file() and not typecheck_cmd:
        if shutil.which("npx"):
            typecheck_cmd = "npx tsc --noEmit"

    # 2. Python
    pyproject = root / "pyproject.toml"
    pytest_ini = root / "pytest.ini"
    tests_dir = root / "tests"
    has_python = pyproject.is_file() or any(root.glob("*.py")) or tests_dir.is_dir()

    if has_python:
        if not test_cmd and (pytest_ini.is_file() or tests_dir.is_dir() or shutil.which("pytest")):
            test_cmd = "pytest -q"
        if not lint_cmd and shutil.which("ruff"):
            lint_cmd = "ruff check ."
        elif not lint_cmd and shutil.which("flake8"):
            lint_cmd = "flake8"

        if not typecheck_cmd and shutil.which("mypy"):
            typecheck_cmd = "mypy ."
        elif not typecheck_cmd and shutil.which("pyright"):
            typecheck_cmd = "pyright"

    # 3. Rust
    cargo_toml = root / "Cargo.toml"
    if cargo_toml.is_file():
        if not typecheck_cmd:
            typecheck_cmd = "cargo check"
        if not lint_cmd:
            lint_cmd = "cargo clippy -- -D warnings"
        if not test_cmd:
            test_cmd = "cargo test"

    # 4. Go
    go_mod = root / "go.mod"
    if go_mod.is_file():
        if not test_cmd:
            test_cmd = "go test ./..."
        if not lint_cmd and shutil.which("golangci-lint"):
            lint_cmd = "golangci-lint run"

    return {
        "typecheck": typecheck_cmd,
        "lint": lint_cmd,
        "test": test_cmd,
    }


# ------------------------------------------------------------------------------
# State & Iteration Management
# ------------------------------------------------------------------------------

def get_state_file(root: Path) -> Path:
    """Return path to the active task's .verify_state.json or fallback in .trellis/."""
    tasks_dir = root / ".trellis" / "tasks"
    if tasks_dir.is_dir():
        for d in tasks_dir.iterdir():
            if d.is_dir() and d.name != "archive" and (d / "task.json").is_file():
                try:
                    data = json.loads((d / "task.json").read_text(encoding="utf-8"))
                    if data.get("status") == "in_progress":
                        return d / ".verify_state.json"
                except Exception:
                    pass
    return root / ".trellis" / ".verify_state.json"


def read_iteration_state(root: Path) -> dict:
    state_file = get_state_file(root)
    if state_file.is_file():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"iteration": 0, "history": []}


def write_iteration_state(root: Path, state: dict) -> None:
    state_file = get_state_file(root)
    try:
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


def reset_iteration_state(root: Path) -> None:
    state_file = get_state_file(root)
    if state_file.is_file():
        try:
            state_file.unlink()
        except Exception:
            pass


# ------------------------------------------------------------------------------
# Execution Core
# ------------------------------------------------------------------------------

def run_stage(stage_name: str, command: str, cwd: Path) -> StageResult:
    """Execute a verification command and record timing and diagnostics."""
    start_time = time.time()
    try:
        res = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        duration = round(time.time() - start_time, 2)
        combined = f"{res.stdout}\n{res.stderr}"
        failures = parse_diagnostics(combined)
        return StageResult(
            stage=stage_name,
            command=command,
            passed=(res.returncode == 0),
            returncode=res.returncode,
            duration_s=duration,
            stdout=res.stdout,
            stderr=res.stderr,
            failures=failures
        )
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        return StageResult(
            stage=stage_name,
            command=command,
            passed=False,
            returncode=1,
            duration_s=duration,
            stdout="",
            stderr=str(e),
            failures=[DiagnosticFailure(file="(execution)", message=str(e))]
        )


def format_feedback_envelope(
    results: List[StageResult],
    iteration: int,
    max_iterations: int,
    root: Path
) -> str:
    """Format an agent-actionable self-healing feedback block."""
    failed_stages = [r for r in results if not r.passed]
    if not failed_stages:
        return (
            "<self-healing-feedback status=\"passed\">\n"
            "✓ ALL VERIFICATION CHECKS PASSED\n"
            f"Executed {len(results)} stages successfully with zero failures.\n"
            "Proceed to Phase 3: Spec Update & Commit.\n"
            "</self-healing-feedback>"
        )

    lines = []
    is_exhausted = (iteration >= max_iterations)

    if is_exhausted:
        lines.append("<self-healing-feedback status=\"exhausted\" policy=\"option-a-halt-and-yield\">")
        lines.append("[SELF-HEALING EXHAUSTION: MAXIMUM RETRIES REACHED]")
        lines.append(f"Reached {iteration} of {max_iterations} allowed self-repair cycles. Halting automated loop.")
        lines.append("SAFETY ENFORCEMENT: Uncommitted changes have been preserved.")
        lines.append("ACTION REQUIRED: Present the root-cause diagnostics below to the user for human guidance.")
    else:
        lines.append(f"<self-healing-feedback status=\"failed\" iteration=\"{iteration}\" max_iterations=\"{max_iterations}\">")
        lines.append(f"[SELF-HEALING DIAGNOSTIC FAILURE — Iteration {iteration} of {max_iterations}]")
        lines.append("Do not stop or ask the user to fix this. Analyze the failures below, apply a targeted fix, and re-run verify.py.")

    lines.append("\n### Failed Stages & Diagnostics:")
    for r in failed_stages:
        lines.append(f"\n▶ Stage: `{r.stage}` | Command: `{r.command}` (Exit Code {r.returncode})")
        if r.failures:
            lines.append("Targeted Failure Sites:")
            for f in r.failures[:10]:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                rule = f" [{f.rule}]" if f.rule else ""
                lines.append(f"  • {loc}{rule}: {f.message}")
        else:
            sample = (r.stderr or r.stdout).strip().splitlines()[-10:]
            lines.append("Output Tail:\n  " + "\n  ".join(sample))

    lines.append("\n### Instructions for Coding Agent:")
    lines.append("1. Examine the exact failing files and assertion traces above.")
    lines.append("2. Cross-reference with recent git modifications (`git diff`).")
    lines.append("3. Fix the underlying implementation defect without deleting or weakening test assertions.")
    lines.append("4. Re-run `python3 .trellis/scripts/verify.py`.")
    lines.append("</self-healing-feedback>")
    return "\n".join(lines)


# ------------------------------------------------------------------------------
# CLI Main
# ------------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Trellis Autonomous Self-Correction & Verification Runner")
    parser.add_argument("--format", choices=["text", "json", "envelope"], default="text", help="Output format")
    parser.add_argument("--stage", choices=["all", "typecheck", "lint", "test"], default="all", help="Target stage")
    parser.add_argument("--fail-fast", action="store_true", default=None, help="Stop on first failing stage")
    parser.add_argument("--dry-run", action="store_true", help="Show detected commands without executing")
    parser.add_argument("--reset-iterations", action="store_true", help="Reset self-healing iteration counter")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max self-healing loop retries before Option A halt")
    args = parser.parse_args()

    root = find_trellis_root()

    if args.reset_iterations:
        reset_iteration_state(root)
        print("✓ Self-healing iteration counter reset.")
        return 0

    stack = detect_verification_stack(root)

    # Determine stages to run
    stages_to_run = []
    if args.stage in ("all", "typecheck") and stack.get("typecheck"):
        stages_to_run.append(("typecheck", stack["typecheck"]))
    if args.stage in ("all", "lint") and stack.get("lint"):
        stages_to_run.append(("lint", stack["lint"]))
    if args.stage in ("all", "test") and stack.get("test"):
        stages_to_run.append(("test", stack["test"]))

    if args.dry_run:
        print(f"=== Verification Stack Auto-Detection ({root.name}) ===")
        for name in ("typecheck", "lint", "test"):
            cmd = stack.get(name) or "(none detected)"
            print(f"  {name:<12}: {cmd}")
        lsp_bin = shutil.which("agent-lsp")
        lsp_status = f"available ({lsp_bin})" if lsp_bin else "not found in PATH (see .trellis/spec/guides/lsp-code-intelligence.md)"
        print(f"  {'agent-lsp':<12}: {lsp_status}")
        return 0

    if not stages_to_run:
        if args.format == "json":
            print(json.dumps({"status": "passed", "message": "No verification checks detected.", "stages": []}))
        else:
            print("ℹ No typecheck, lint, or test commands configured or detected in project.")
        return 0

    # Iteration tracking
    state = read_iteration_state(root)
    iteration = state.get("iteration", 0) + 1
    max_iter = args.max_iterations

    # Execution
    results: List[StageResult] = []
    fail_fast = args.fail_fast
    if fail_fast is None:
        config = read_trellis_config(root)
        fail_fast = bool(config.get("verification", {}).get("fail_fast", False))

    all_passed = True
    for stage_name, cmd in stages_to_run:
        if args.format == "text":
            print(f"▶ Running {stage_name}: `{cmd}`...", end="", flush=True)
        res = run_stage(stage_name, cmd, root)
        results.append(res)
        if res.passed:
            if args.format == "text":
                print(f" [PASS] ({res.duration_s}s)")
        else:
            all_passed = False
            if args.format == "text":
                print(f" [FAIL] (exit code {res.returncode}, {res.duration_s}s)")
            if fail_fast:
                break

    # Update state
    if not all_passed:
        state["iteration"] = iteration
        write_iteration_state(root, state)
    else:
        reset_iteration_state(root)

    # Output Formatting
    if args.format == "json":
        data = {
            "status": "passed" if all_passed else "failed",
            "iteration": iteration,
            "max_iterations": max_iter,
            "all_passed": all_passed,
            "stages": [
                {
                    "stage": r.stage,
                    "command": r.command,
                    "passed": r.passed,
                    "returncode": r.returncode,
                    "duration_s": r.duration_s,
                    "failures": [asdict(f) for f in r.failures]
                }
                for r in results
            ]
        }
        print(json.dumps(data, indent=2))
    elif args.format == "envelope" or not all_passed:
        envelope = format_feedback_envelope(results, iteration, max_iter, root)
        print("\n" + envelope)
    else:
        print("\n✓ All verification stages passed successfully.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
