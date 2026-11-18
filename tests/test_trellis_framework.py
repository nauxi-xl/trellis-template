#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zero-dependency unittest suite for the Trellis framework scripts and hooks."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / ".trellis" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import verify  # type: ignore[import-not-found]


class TestVerifyDiagnosticsAndEnvelope(unittest.TestCase):
    """Verify diagnostic parsing and bounded self-healing feedback envelopes."""

    def test_parse_diagnostics_standard_pytest_and_cargo(self) -> None:
        sample_output = "\n".join([
            "src/app.ts:12:5: TS2322: Type 'string' is not assignable to type 'number'.",
            "FAILED tests/test_auth.py::test_login - AssertionError: expected 200",
            "error[E0308]: mismatched types\n  --> src/main.rs:10:5",
        ])
        failures = verify.parse_diagnostics(sample_output)
        files = {f.file for f in failures}
        self.assertIn("src/app.ts", files)
        self.assertIn("tests/test_auth.py", files)
        self.assertIn("src/main.rs", files)

        ts_failure = next(f for f in failures if f.file == "src/app.ts")
        self.assertEqual(ts_failure.line, 12)
        self.assertEqual(ts_failure.column, 5)
        self.assertEqual(ts_failure.rule, "TS2322")

        pytest_failure = next(f for f in failures if f.file == "tests/test_auth.py")
        self.assertEqual(pytest_failure.error_type, "test_login")

        cargo_failure = next(f for f in failures if f.file == "src/main.rs")
        self.assertEqual(cargo_failure.line, 10)
        self.assertEqual(cargo_failure.rule, "E0308")

    def test_format_feedback_envelope_states(self) -> None:
        passed_stage = verify.StageResult(
            stage="lint",
            command="ruff check .",
            passed=True,
            returncode=0,
            duration_s=0.1,
            stdout="",
            stderr="",
        )
        passed_env = verify.format_feedback_envelope([passed_stage], 1, 3, REPO_ROOT)
        self.assertIn('status="passed"', passed_env)

        failed_stage = verify.StageResult(
            stage="test",
            command="pytest -q",
            passed=False,
            returncode=1,
            duration_s=0.2,
            stdout="",
            stderr="AssertionError",
            failures=[verify.DiagnosticFailure(file="tests/a.py", line=10, message="boom")],
        )
        failed_env = verify.format_feedback_envelope([failed_stage], 1, 3, REPO_ROOT)
        self.assertIn('status="failed"', failed_env)
        self.assertIn('iteration="1"', failed_env)

        exhausted_env = verify.format_feedback_envelope([failed_stage], 3, 3, REPO_ROOT)
        self.assertIn('status="exhausted"', exhausted_env)
        self.assertIn("option-a-halt-and-yield", exhausted_env)


class TestFrameworkCLIAndHooks(unittest.TestCase):
    """Integration checks for task validation, dynamic context, hooks, and symlinks."""

    def test_task_validate_no_args_exits_zero(self) -> None:
        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "task.py"), "validate"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, msg=res.stdout + res.stderr)

    def test_task_validate_active_and_invalid_in_temp_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            spec_file = tmp_root / ".trellis" / "spec" / "guides" / "index.md"
            spec_file.parent.mkdir(parents=True)
            spec_file.write_text("# Guides\n", encoding="utf-8")

            task_dir = tmp_root / ".trellis" / "tasks" / "11-18-sample"
            task_dir.mkdir(parents=True)
            (task_dir / "task.json").write_text(
                json.dumps({"id": "sample", "status": "planning"}),
                encoding="utf-8",
            )
            (task_dir / "implement.jsonl").write_text("", encoding="utf-8")
            (task_dir / "check.jsonl").write_text("", encoding="utf-8")

            res_invalid = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "task.py"), "validate"],
                cwd=str(tmp_root),
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_invalid.returncode, 1, msg=res_invalid.stdout + res_invalid.stderr)

            valid_entry = json.dumps({
                "file": ".trellis/spec/guides/index.md",
                "reason": "Guides index",
            }) + "\n"
            (task_dir / "implement.jsonl").write_text(valid_entry, encoding="utf-8")
            (task_dir / "check.jsonl").write_text(valid_entry, encoding="utf-8")

            res_valid = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "task.py"), "validate"],
                cwd=str(tmp_root),
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_valid.returncode, 0, msg=res_valid.stdout + res_valid.stderr)

    def test_dynamic_context_json(self) -> None:
        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "dynamic_context.py"), "--format", "json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        payload = json.loads(res.stdout)
        self.assertIn("git", payload)
        self.assertIn("scoped_specs", payload)
        self.assertIn("lsp", payload)

    def test_agy_workflow_state_hook_and_skip_keyword(self) -> None:
        hook_path = REPO_ROOT / ".agents" / "hooks" / "inject-workflow-state.py"

        normal_input = json.dumps({"cwd": str(REPO_ROOT), "prompt": "implement feature"})
        res_normal = subprocess.run(
            [sys.executable, str(hook_path)],
            input=normal_input,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_normal.returncode, 0, msg=res_normal.stderr)
        normal_out = json.loads(res_normal.stdout)
        self.assertTrue(normal_out.get("injectSteps"), msg="Expected non-empty injectSteps")

        skip_input = json.dumps({"cwd": str(REPO_ROOT), "prompt": "please run no-trellis here"})
        res_skip = subprocess.run(
            [sys.executable, str(hook_path)],
            input=skip_input,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_skip.returncode, 0, msg=res_skip.stderr)
        skip_out = json.loads(res_skip.stdout)
        self.assertEqual(skip_out.get("injectSteps"), [])

    def test_skill_directories_are_synced_symlinks(self) -> None:
        canonical = (REPO_ROOT / ".agents" / "skills").resolve()
        self.assertTrue(canonical.is_dir())
        for link_rel in (".claude/skills", ".github/skills"):
            link_path = REPO_ROOT / link_rel
            self.assertTrue(link_path.is_symlink(), msg=f"{link_rel} must be a symlink")
            self.assertEqual(link_path.resolve(), canonical)


if __name__ == "__main__":
    unittest.main()
