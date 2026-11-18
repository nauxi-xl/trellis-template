---
name: lsp
description: "Language Server Protocol (LSP) code intelligence, blast-radius analysis, and speculative safe editing"
---

# Workflow: /lsp

This workflow activates the `lsp` skill to perform AST-accurate code navigation, impact analysis, and speculative refactoring using `agent-lsp`.

---

## Step 1: Parse Target & Goal
Extract the target symbol, file path, or refactoring objective from the user's prompt (e.g., `/lsp inspect MyClass`, `/lsp blast-radius src/auth.py`, `/lsp rename oldFunc newFunc`).
If no target was specified, prompt the user:
> *"Which symbol, function, or file would you like to inspect, analyze, or refactor with LSP?"*

## Step 2: Verify Language Server Status
1. Check that `agent-lsp` has a working server for the relevant language by running `agent-lsp doctor` or invoking `detect_lsp_servers`.
2. If the language server is missing, refer the user or environment to the installation guide in `.trellis/spec/guides/lsp-code-intelligence.md`.

## Step 3: Semantic Analysis & Blast-Radius Calculation
1. **Symbol Inspection**: Call `inspect_symbol` or `list_symbols` on the target.
2. **Impact Assessment**: Call `blast_radius` on the file or symbol before any edits are planned to partition test vs non-test callers.
3. Review dependencies and summarize findings for the user.

## Step 4: Speculative Edit & Application
1. **Preview**: Run `preview_edit` to evaluate compiler/type-checker diagnostics before modifying disk.
2. **Apply**: If the diagnostic delta is clean or improves errors, proceed with `safe_apply_edit` or `replace_symbol_body`.

## Step 5: Post-Edit Diagnostics & Verification
1. Call `get_diagnostics` to verify zero new regressions from the language server.
2. If errors remain, inspect `suggest_fixes` for available code actions.
3. Run the project verification loop: `python3 .trellis/scripts/verify.py`.
