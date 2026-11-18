#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zero-dependency unittest suite for the Trellis framework scripts and hooks."""
from __future__ import annotations

import json
import os
import shutil
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
        msg_text = normal_out["injectSteps"][0]["systemMessage"]["systemMessage"]
        self.assertIn("<tool-priority>", msg_text)
        self.assertIn("agent-lsp", msg_text)
        self.assertIn("context7", msg_text)

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

    def test_pre_tool_priority_hook_advisory_and_enforce(self) -> None:
        hook_path = REPO_ROOT / ".agents" / "hooks" / "pre-tool-priority.py"
        canonical_hook = hook_path.resolve()
        for link_rel in (
            ".claude/hooks/pre-tool-priority.py",
            ".github/copilot/hooks/pre-tool-priority.py",
        ):
            link_path = REPO_ROOT / link_rel
            self.assertTrue(link_path.is_symlink(), msg=f"{link_rel} must be a symlink")
            self.assertEqual(link_path.resolve(), canonical_hook)

        def run_hook(tmp_root: Path, payload: dict[str, object], mode: str = "advisory") -> dict[str, object]:
            env = dict(os.environ)
            env["TRELLIS_TOOL_PRIORITY_MODE"] = mode
            res = subprocess.run(
                [sys.executable, str(hook_path)],
                input=json.dumps({"cwd": str(tmp_root), **payload}),
                cwd=str(tmp_root),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            return json.loads(res.stdout)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            (tmp_root / ".trellis").mkdir(parents=True)

            # Advisory mode: grep, code edit, and search_web all allow with guidance
            grep_out = run_hook(tmp_root, {
                "conversationId": "adv-1",
                "toolCall": {"name": "run_command", "args": {"CommandLine": "grep -rn foo src/"}},
            })
            self.assertEqual(grep_out.get("decision"), "allow")
            self.assertIn("[Tool Priority: agent-lsp First]", str(grep_out.get("reason", "")))

            edit_out = run_hook(tmp_root, {
                "conversationId": "adv-1",
                "toolCall": {"name": "edit_file", "args": {"Path": "app.py"}},
            })
            self.assertEqual(edit_out.get("decision"), "allow")
            self.assertIn("[Tool Priority: agent-lsp First]", str(edit_out.get("reason", "")))

            web_out = run_hook(tmp_root, {
                "conversationId": "adv-1",
                "toolCall": {"name": "search_web", "args": {"query": "nextjs docs"}},
            })
            self.assertEqual(web_out.get("decision"), "allow")
            self.assertIn("[Tool Priority: Context7 First]", str(web_out.get("reason", "")))

            # Enforce mode: first raw web search / grep denied, second allowed (retry safety)
            deny_web = run_hook(
                tmp_root,
                {
                    "conversationId": "enf-1",
                    "toolCall": {"name": "search_web", "args": {"query": "react hooks"}},
                },
                mode="enforce",
            )
            self.assertEqual(deny_web.get("decision"), "deny")
            self.assertIn("[Tool Priority: Context7 First]", str(deny_web.get("reason", "")))

            retry_web = run_hook(
                tmp_root,
                {
                    "conversationId": "enf-1",
                    "toolCall": {"name": "search_web", "args": {"query": "react hooks"}},
                },
                mode="enforce",
            )
            self.assertEqual(retry_web.get("decision"), "allow")

            deny_grep = run_hook(
                tmp_root,
                {
                    "conversationId": "enf-1",
                    "toolCall": {"name": "run_command", "args": {"CommandLine": "grep -rn foo src/"}},
                },
                mode="enforce",
            )
            self.assertEqual(deny_grep.get("decision"), "deny")
            self.assertIn("[Tool Priority: agent-lsp First]", str(deny_grep.get("reason", "")))

            retry_grep = run_hook(
                tmp_root,
                {
                    "conversationId": "enf-1",
                    "toolCall": {"name": "run_command", "args": {"CommandLine": "grep -rn foo src/"}},
                },
                mode="enforce",
            )
            self.assertEqual(retry_grep.get("decision"), "allow")

            # Using Context7 and agent-lsp first allows immediate fallback without denial
            run_hook(
                tmp_root,
                {
                    "conversationId": "enf-2",
                    "toolCall": {"name": "call_mcp_tool", "args": {"ServerName": "context7", "ToolName": "query-docs"}},
                },
                mode="enforce",
            )
            run_hook(
                tmp_root,
                {
                    "conversationId": "enf-2",
                    "toolCall": {"name": "call_mcp_tool", "args": {"ServerName": "agent-lsp", "ToolName": "find_symbol"}},
                },
                mode="enforce",
            )
            allowed_web = run_hook(
                tmp_root,
                {
                    "conversationId": "enf-2",
                    "toolCall": {"name": "search_web", "args": {"query": "react hooks"}},
                },
                mode="enforce",
            )
            self.assertEqual(allowed_web.get("decision"), "allow")
            self.assertNotIn("reason", allowed_web)

            allowed_grep = run_hook(
                tmp_root,
                {
                    "conversationId": "enf-2",
                    "toolCall": {"name": "run_command", "args": {"CommandLine": "grep -rn foo src/"}},
                },
                mode="enforce",
            )
            self.assertEqual(allowed_grep.get("decision"), "allow")
            self.assertNotIn("reason", allowed_grep)

    def test_update_framework_check_apply_preserve_and_rollback(self) -> None:
        updater = SCRIPTS_DIR / "update_framework.py"

        def git(cwd: Path, *args: str) -> str:
            res = subprocess.run(
                ["git", *args],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                check=True,
            )
            return res.stdout.strip()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            upstream = tmp_path / "upstream"
            project = tmp_path / "project"
            upstream.mkdir()

            git(upstream, "init", "-b", "main")
            git(upstream, "config", "user.name", "Test")
            git(upstream, "config", "user.email", "test@example.com")

            (upstream / ".trellis" / "spec" / "guides").mkdir(parents=True)
            (upstream / ".trellis" / "tasks" / "11-18-local").mkdir(parents=True)
            (upstream / ".trellis" / ".version").write_text("0.6.17\n", encoding="utf-8")
            (upstream / ".trellis" / "spec" / "guides" / "index.md").write_text("# Guides v1\n", encoding="utf-8")
            (upstream / ".trellis" / "tasks" / "11-18-local" / "task.json").write_text('{"id": "upstream"}', encoding="utf-8")
            git(upstream, "add", "-A")
            git(upstream, "commit", "-m", "initial")

            subprocess.run(
                ["git", "clone", "-b", "main", str(upstream), str(project)],
                capture_output=True,
                text=True,
                check=True,
            )
            shutil.copytree(
                SCRIPTS_DIR,
                project / ".trellis" / "scripts",
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            (project / ".trellis" / "tasks" / "11-18-local" / "task.json").write_text(
                '{"id": "my-project-task"}', encoding="utf-8"
            )

            # Upstream publishes v2 managed files + touches protected tasks dir
            (upstream / ".trellis" / ".version").write_text("0.7.0\n", encoding="utf-8")
            (upstream / ".trellis" / "spec" / "guides" / "index.md").write_text("# Guides v2\n", encoding="utf-8")
            (upstream / ".trellis" / "tasks" / "11-18-local" / "task.json").write_text(
                '{"id": "upstream-overwrite-attempt"}', encoding="utf-8"
            )
            git(upstream, "add", "-A")
            git(upstream, "commit", "-m", "v2")

            dry_res = subprocess.run(
                [sys.executable, str(updater), "--remote", str(upstream), "--branch", "main", "--dry-run", "--json"],
                cwd=str(project),
                capture_output=True,
                text=True,
                check=True,
            )
            dry_json = json.loads(dry_res.stdout)
            self.assertEqual(dry_json["status"], "updates_available")
            self.assertIn(".trellis/spec/guides/index.md", dry_json["updated"])
            self.assertIn(".trellis/.version", dry_json["updated"])
            self.assertNotIn(".trellis/tasks/11-18-local/task.json", dry_json["updated"])
            self.assertEqual(
                (project / ".trellis" / "spec" / "guides" / "index.md").read_text(encoding="utf-8"),
                "# Guides v1\n",
            )

            apply_res = subprocess.run(
                [sys.executable, str(updater), "--remote", str(upstream), "--branch", "main", "--skip-verify", "--json"],
                cwd=str(project),
                capture_output=True,
                text=True,
                check=True,
            )
            apply_json = json.loads(apply_res.stdout)
            self.assertEqual(apply_json["status"], "updated")
            self.assertTrue(apply_json["backup_dir"])
            self.assertTrue((project / apply_json["backup_dir"]).is_dir())
            self.assertEqual(
                (project / ".trellis" / "spec" / "guides" / "index.md").read_text(encoding="utf-8"),
                "# Guides v2\n",
            )
            self.assertEqual((project / ".trellis" / ".version").read_text(encoding="utf-8"), "0.7.0\n")
            self.assertEqual(
                (project / ".trellis" / "tasks" / "11-18-local" / "task.json").read_text(encoding="utf-8"),
                '{"id": "my-project-task"}',
            )

            # Local customization is preserved unless --force is passed
            (project / ".trellis" / "spec" / "guides" / "index.md").write_text("# Guides custom\n", encoding="utf-8")
            (upstream / ".trellis" / "spec" / "guides" / "index.md").write_text("# Guides v3\n", encoding="utf-8")
            git(upstream, "add", "-A")
            git(upstream, "commit", "-m", "v3")

            skip_res = subprocess.run(
                [sys.executable, str(updater), "--remote", str(upstream), "--branch", "main", "--skip-verify", "--json"],
                cwd=str(project),
                capture_output=True,
                text=True,
                check=True,
            )
            skip_json = json.loads(skip_res.stdout)
            self.assertIn(".trellis/spec/guides/index.md", skip_json["skipped_modified"])
            self.assertEqual(
                (project / ".trellis" / "spec" / "guides" / "index.md").read_text(encoding="utf-8"),
                "# Guides custom\n",
            )

            force_res = subprocess.run(
                [sys.executable, str(updater), "--remote", str(upstream), "--branch", "main", "--force", "--skip-verify", "--json"],
                cwd=str(project),
                capture_output=True,
                text=True,
                check=True,
            )
            force_json = json.loads(force_res.stdout)
            self.assertIn(".trellis/spec/guides/index.md", force_json["updated"])
            self.assertEqual(
                (project / ".trellis" / "spec" / "guides" / "index.md").read_text(encoding="utf-8"),
                "# Guides v3\n",
            )

            # Rollback restores the custom file backed up before --force
            rb_res = subprocess.run(
                [sys.executable, str(updater), "--rollback", "--skip-verify", "--json"],
                cwd=str(project),
                capture_output=True,
                text=True,
                check=True,
            )
            rb_json = json.loads(rb_res.stdout)
            self.assertEqual(rb_json["status"], "rolled_back")
            self.assertEqual(
                (project / ".trellis" / "spec" / "guides" / "index.md").read_text(encoding="utf-8"),
                "# Guides custom\n",
            )

    def test_session_start_detects_outdated_framework_and_prompts_user(self) -> None:
        updater = SCRIPTS_DIR / "update_framework.py"
        agy_session_start = REPO_ROOT / ".agents" / "hooks" / "session-start.py"

        def git(cwd: Path, *args: str) -> str:
            res = subprocess.run(
                ["git", *args],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                check=True,
            )
            return res.stdout.strip()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            upstream = tmp_path / "upstream"
            project = tmp_path / "project"
            upstream.mkdir()

            git(upstream, "init", "-b", "main")
            git(upstream, "config", "user.name", "Test")
            git(upstream, "config", "user.email", "test@example.com")
            (upstream / ".trellis").mkdir(parents=True)
            (upstream / ".trellis" / ".version").write_text("0.6.17\n", encoding="utf-8")
            (upstream / ".trellis" / "workflow.md").write_text("# Workflow\n", encoding="utf-8")
            git(upstream, "add", "-A")
            git(upstream, "commit", "-m", "initial")

            subprocess.run(
                ["git", "clone", "-b", "main", str(upstream), str(project)],
                capture_output=True,
                text=True,
                check=True,
            )
            shutil.copytree(
                SCRIPTS_DIR,
                project / ".trellis" / "scripts",
                ignore=shutil.ignore_patterns("__pycache__"),
            )

            env = {
                k: v for k, v in os.environ.items()
                if not k.endswith("_PROJECT_DIR")
            }
            env["TRELLIS_UPDATE_REMOTE"] = str(upstream)
            env["TRELLIS_UPDATE_BRANCH"] = "main"

            # Up-to-date: no <framework-update-available> block
            cli_up_to_date = subprocess.run(
                [sys.executable, str(updater), "--session-start-prompt"],
                cwd=str(project),
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(cli_up_to_date.stdout.strip(), "")

            hook_up_to_date = subprocess.run(
                [sys.executable, str(agy_session_start)],
                input=json.dumps({"cwd": str(project)}),
                cwd=str(project),
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            hook_up_json = json.loads(hook_up_to_date.stdout)
            up_msg = hook_up_json["injectSteps"][0]["systemMessage"]["systemMessage"]
            self.assertNotIn("<framework-update-available>", up_msg)

            # Upstream bumps version -> SessionStart warns and asks user
            (upstream / ".trellis" / ".version").write_text("0.8.0\n", encoding="utf-8")
            git(upstream, "add", "-A")
            git(upstream, "commit", "-m", "bump 0.8.0")

            cli_outdated = subprocess.run(
                [sys.executable, str(updater), "--session-start-prompt"],
                cwd=str(project),
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("<framework-update-available>", cli_outdated.stdout)
            self.assertIn("0.8.0", cli_outdated.stdout)
            self.assertIn("1 file(s) behind remote", cli_outdated.stdout)

            hook_outdated = subprocess.run(
                [sys.executable, str(agy_session_start)],
                input=json.dumps({"cwd": str(project)}),
                cwd=str(project),
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            hook_out_json = json.loads(hook_outdated.stdout)
            out_msg = hook_out_json["injectSteps"][0]["systemMessage"]["systemMessage"]
            self.assertIn("<framework-update-available>", out_msg)
            self.assertIn("0.8.0", out_msg)
            self.assertIn("ask if they would like to update", out_msg)


if __name__ == "__main__":
    unittest.main()
