#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trellis SessionStart hook for Antigravity CLI (agy).

Wraps the canonical Trellis session-start logic and outputs the
injected context formatted as AGY's required `injectSteps` schema.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    raw_input = ""
    try:
        if not sys.stdin.isatty():
            raw_input = sys.stdin.read()
    except Exception:
        pass

    repo_root = Path(__file__).resolve().parent.parent.parent
    canonical_hook = repo_root / ".claude" / "hooks" / "session-start.py"

    if not canonical_hook.is_file():
        print(json.dumps({"injectSteps": []}))
        return 0

    try:
        res = subprocess.run(
            [sys.executable, str(canonical_hook)],
            input=raw_input,
            text=True,
            capture_output=True,
            timeout=15,
        )
    except Exception:
        print(json.dumps({"injectSteps": []}))
        return 0

    if res.returncode != 0:
        print(json.dumps({"injectSteps": []}))
        return 0

    try:
        data = json.loads(res.stdout)
        context_text = (
            data.get("hookSpecificOutput", {}).get("additionalContext")
            or data.get("additional_context")
            or ""
        )

        dynamic_script = repo_root / ".trellis" / "scripts" / "dynamic_context.py"
        dynamic_block = ""
        if dynamic_script.is_file():
            try:
                d_res = subprocess.run(
                    [sys.executable, str(dynamic_script), "--format", "prompt"],
                    cwd=str(repo_root),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if d_res.returncode == 0 and d_res.stdout.strip():
                    dynamic_block = d_res.stdout.strip()
            except Exception:
                pass

        if dynamic_block:
            context_text = f"{context_text}\n\n{dynamic_block}" if context_text else dynamic_block

        out = {
            "injectSteps": [
                {
                    "systemMessage": {
                        "systemMessage": context_text
                    }
                }
            ] if context_text else [],
            "hookSpecificOutput": data.get("hookSpecificOutput", {}),
        }
        print(json.dumps(out, ensure_ascii=False))
    except Exception:
        print(json.dumps({"injectSteps": []}))

    return 0


if __name__ == "__main__":
    sys.exit(main())
