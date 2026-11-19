#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for .trellis/scripts/notebook_sync.py and hook/dynamic_context integration."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / ".trellis" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import notebook_sync  # type: ignore[import-not-found]


class TestNotebookSync(unittest.TestCase):
    """Verify missing-notebook prompt state, binding, change detection, and sync."""

    def _init_project(self, root: Path) -> None:
        (root / ".trellis" / "spec" / "guides").mkdir(parents=True)
        (root / ".trellis" / "config.yaml").write_text(
            'notebooklm:\n  enabled: true\n  project_notebook: ""\n  auto_sync: true\n  ask_if_missing: true\n',
            encoding="utf-8",
        )
        (root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (root / ".trellis" / "spec" / "guides" / "index.md").write_text("# Guides\n", encoding="utf-8")
        subprocess.run(["git", "init", "-b", "main"], cwd=str(root), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(root), check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(root), check=True)
        subprocess.run(["git", "add", "-A"], cwd=str(root), check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(root), check=True, capture_output=True)

    def test_missing_notebook_prompt_and_decline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_project(root)

            res = notebook_sync.sync_to_notebook(root=root)
            self.assertEqual(res["status"], "missing_notebook")
            self.assertTrue(res["ask_if_missing"])
            self.assertGreater(res["pending_count"], 0)

            hint = notebook_sync.format_prompt_hint(root)
            self.assertIn('status="missing"', hint)
            self.assertIn("ask the user", hint)

            notebook_sync.mark_prompted(declined=True, root=root)
            self.assertEqual(notebook_sync.format_prompt_hint(root), "")

    def test_bind_persists_config_and_tracks_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_project(root)

            st = notebook_sync.bind_notebook("my-brain", title="My Brain", root=root)
            self.assertEqual(st.bound_notebook, "my-brain")
            self.assertIn('project_notebook: "my-brain"', (root / ".trellis" / "config.yaml").read_text(encoding="utf-8"))

            # Mark synced -> 0 pending
            st_synced = notebook_sync.mark_synced(root)
            self.assertEqual(st_synced.pending_count, 0)
            self.assertIn('status="synced"', notebook_sync.format_prompt_hint(root))

            # Modify spec file + code file -> pending changes detected automatically
            (root / ".trellis" / "spec" / "guides" / "index.md").write_text("# Guides v2\n", encoding="utf-8")
            (root / "app.py").write_text("def hello():\n    return 1\n", encoding="utf-8")

            st_after = notebook_sync.get_status(root)
            paths = {c.path: c.category for c in st_after.pending_changes}
            self.assertEqual(paths.get(".trellis/spec/guides/index.md"), "knowledge")
            self.assertEqual(paths.get("app.py"), "code")

            pending_hint = notebook_sync.format_prompt_hint(root)
            self.assertIn('status="pending"', pending_hint)
            self.assertIn('notebook="my-brain"', pending_hint)

            # Dry-run sync produces structured note preview
            dry = notebook_sync.sync_to_notebook(root=root, summary="Updated guides & app", dry_run=True)
            self.assertEqual(dry["status"], "dry_run")
            self.assertIn(".trellis/spec/guides/index.md", dry["note_preview"])
            self.assertIn("app.py", dry["note_preview"])

    def test_sync_executes_nlm_and_clears_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_project(root)
            notebook_sync.bind_notebook("proj-alias", root=root)

            # Create fake `nlm` binary in temp bin dir
            bin_dir = root / "fake_bin"
            bin_dir.mkdir()
            capture_file = root / "nlm_called.txt"
            fake_nlm = bin_dir / "nlm"
            fake_nlm.write_text(
                f"#!/usr/bin/env python3\n"
                f"import sys\n"
                f"from pathlib import Path\n"
                f"Path({str(capture_file)!r}).write_text(' '.join(sys.argv[1:]), encoding='utf-8')\n"
                f"sys.exit(0)\n",
                encoding="utf-8",
            )
            fake_nlm.chmod(0o755)

            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}:{old_path}"
            try:
                res = notebook_sync.sync_to_notebook(root=root, summary="Auto sync check")
            finally:
                os.environ["PATH"] = old_path

            self.assertEqual(res["status"], "synced")
            self.assertTrue(capture_file.is_file())
            self.assertIn("note create proj-alias", capture_file.read_text(encoding="utf-8"))

            st_after = notebook_sync.get_status(root)
            self.assertEqual(st_after.pending_count, 0)

    def test_inject_workflow_state_includes_graphify_and_notebook_sync(self) -> None:
        hook_path = REPO_ROOT / ".agents" / "hooks" / "inject-workflow-state.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_project(root)
            (root / ".trellis" / "workflow.md").write_text("# Workflow\n", encoding="utf-8")

            res = subprocess.run(
                [sys.executable, str(hook_path)],
                input=json.dumps({"cwd": str(root), "prompt": "search architecture"}),
                cwd=str(root),
                capture_output=True,
                text=True,
                check=True,
            )
            out = json.loads(res.stdout)
            msg = out["injectSteps"][0]["systemMessage"]["systemMessage"]
            self.assertIn("graphify", msg)
            self.assertIn("NotebookLM", msg)
            self.assertIn('<notebook-sync status="missing">', msg)


if __name__ == "__main__":
    unittest.main()
