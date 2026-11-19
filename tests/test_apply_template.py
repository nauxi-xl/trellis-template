#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for scripts/apply-template.py."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APPLY_SCRIPT = REPO_ROOT / "scripts" / "apply-template.py"


class TestApplyTemplate(unittest.TestCase):
    """Verify applying trellis-template to arbitrary target directories."""

    def _run_apply(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(APPLY_SCRIPT), *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )

    def test_apply_to_new_directory_git_init_and_developer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "brand-new-app"
            res = self._run_apply(str(target), "--dev", "alice")
            self.assertEqual(res.returncode, 0, msg=res.stdout + res.stderr)

            # Git initialized on main
            self.assertTrue((target / ".git").is_dir())
            branch = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                cwd=str(target),
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(branch.stdout.strip(), "main")

            # Developer initialized
            dev_file = target / ".trellis" / ".developer"
            self.assertTrue(dev_file.is_file())
            self.assertIn("name=alice", dev_file.read_text(encoding="utf-8"))
            self.assertTrue((target / ".trellis" / "workspace" / "alice" / "index.md").is_file())
            self.assertTrue((target / ".trellis" / "workspace" / "alice" / "journal-1.md").is_file())

            # Template-local history and runtime excluded
            self.assertFalse((target / ".trellis" / ".runtime").exists())
            self.assertFalse((target / ".trellis" / "workspace" / "Nauxi").exists())
            self.assertFalse((target / ".trellis" / "tasks" / "archive" / "2026-11").exists())
            self.assertFalse((target / "scripts" / "apply-template.py").exists())
            self.assertFalse((target / "tests" / "test_trellis_framework.py").exists())

            # Core template assets & symlinks present
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue((target / ".trellis" / "workflow.md").is_file())
            self.assertTrue((target / "scripts" / "install-tools.sh").is_file())
            self.assertTrue((target / "graphify-out" / ".gitkeep").is_file())
            self.assertTrue((target / ".agent").is_symlink())
            self.assertEqual(os.readlink(target / ".agent"), ".agents")
            self.assertTrue((target / "CLAUDE.md").is_symlink())
            self.assertEqual(os.readlink(target / "CLAUDE.md"), "AGENTS.md")

            # Trellis scripts work in target
            get_dev = subprocess.run(
                [sys.executable, str(target / ".trellis" / "scripts" / "get_developer.py")],
                cwd=str(target),
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(get_dev.stdout.strip(), "alice")

    def test_apply_merges_existing_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "existing-app"
            target.mkdir()
            (target / "AGENTS.md").write_text("# My Existing App\n\nCustom rules.\n", encoding="utf-8")
            (target / ".gitignore").write_text("*.secret\n.env\n", encoding="utf-8")
            (target / ".mcp.json").write_text(
                json.dumps({"mcpServers": {"custom-mcp": {"command": "echo", "args": []}}}),
                encoding="utf-8",
            )
            subprocess.run(["git", "init"], cwd=str(target), check=True, capture_output=True)

            res = self._run_apply(str(target), "-d", "bob")
            self.assertEqual(res.returncode, 0, msg=res.stdout + res.stderr)

            agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("<!-- TRELLIS:START -->", agents_text)
            self.assertIn("# My Existing App", agents_text)
            self.assertIn("Custom rules.", agents_text)

            gitignore_text = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("*.secret", gitignore_text)
            self.assertIn(".trellis/worktrees/", gitignore_text)

            mcp_data = json.loads((target / ".mcp.json").read_text(encoding="utf-8"))
            self.assertIn("custom-mcp", mcp_data["mcpServers"])
            self.assertIn("agent-lsp", mcp_data["mcpServers"])

    def test_dry_run_does_not_create_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "never-created"
            res = self._run_apply(str(target), "--dev", "alice", "--dry-run", "--commit")
            self.assertEqual(res.returncode, 0, msg=res.stdout + res.stderr)
            self.assertIn("[DRY-RUN]", res.stdout)
            self.assertIn("Would stage all files and commit", res.stdout)
            self.assertFalse(target.exists())

    def test_upstream_and_initial_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "committed-app"
            # Pre-init git and set local user identity so commit succeeds in isolated CI environments
            target.mkdir()
            subprocess.run(["git", "init", "-b", "main"], cwd=str(target), check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(target), check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(target), check=True)

            upstream_url = "https://example.com/trellis-template.git"
            res = self._run_apply(
                str(target),
                "--dev", "charlie",
                "--upstream", upstream_url,
                "--commit",
            )
            self.assertEqual(res.returncode, 0, msg=res.stdout + res.stderr)

            remote_res = subprocess.run(
                ["git", "remote", "get-url", "upstream"],
                cwd=str(target),
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(remote_res.stdout.strip(), upstream_url)

            cfg_text = (target / ".trellis" / "config.yaml").read_text(encoding="utf-8")
            self.assertIn('remote: "upstream"', cfg_text)

            # .trellis/.developer must remain gitignored and untracked
            tracked = subprocess.run(
                ["git", "ls-files", ".trellis/.developer"],
                cwd=str(target),
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(tracked.stdout.strip(), "")

    def test_rejects_template_root_as_target(self) -> None:
        res = self._run_apply(str(REPO_ROOT), "--dev", "alice", "--dry-run")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("cannot be the template repository itself", res.stderr)


if __name__ == "__main__":
    unittest.main()
