---
trigger: always_on
description: Use Language Server Protocol (LSP) via agent-lsp for semantic code intelligence, symbol navigation, blast-radius analysis, and safe speculative refactoring.
---

## LSP Code Intelligence & Refactoring (`agent-lsp`)

This project integrates Language Server Protocol (LSP) tooling via **`agent-lsp`**. It provides IDE-grade semantic analysis and speculative code refactoring across Python, TypeScript, JavaScript, Rust, C/C++, Go, and other supported languages.

Always prefer semantic LSP tools over raw grep or manual file scanning when investigating code logic or modifying symbols.

---

### Code Intelligence Hierarchy

1. **LSP Tools (`agent-lsp`)**:
   - **Primary for code**: Use for exact symbol definitions, type signatures, caller hierarchies, usages, compiler diagnostics, and safe modifications.
2. **Code Graph (`graphify`)**:
   - **Architecture & relationships**: Use for broad module architecture, community detection, shortest dependency paths between distant files, and cross-layer topology.
3. **Grep & File Reading**:
   - **Fallback**: Reserved for non-code assets (specs, markdown, yaml configs, plain text) or unindexed patterns.

---

### Task-to-Tool Matrix

| Task | Primary LSP Tool / MCP | Avoid Doing |
|------|------------------------|-------------|
| **Analyze change impact** | `blast_radius` (returns all exports + callers partitioned into test vs non-test) | Manually scanning references |
| **Inspect symbol / type** | `inspect_symbol` (docstring, type signature, container) | Guessing or reading declaration file |
| **Find symbol by name** | `find_symbol` (workspace-wide symbol query) | Global grep for symbol name |
| **Find all callers** | `find_callers` (call hierarchy) | Searching function call patterns with grep |
| **Find all references** | `find_references` (all AST usages across codebase) | Grepping identifier across files |
| **Explore file structure** | `list_symbols` (outlines functions, classes, interfaces) | Reading entire file top-to-bottom |
| **Speculative edit preview**| `preview_edit` / `simulate_chain` (in-memory diagnostic delta) | Blind edits directly to disk |
| **Apply safe verified edit**| `safe_apply_edit` (only writes if preview succeeds and server is warm) | Edit and pray tests catch errors |
| **Replace function body** | `replace_symbol_body` | Fragile multi-line text replacements |
| **Safe symbol rename** | `rename_symbol` / `prepare_rename` | Text-based find & replace |
| **Safe dead-code removal**| `safe_delete_symbol` | Deleting lines without checking callers |
| **Diagnostics & fixes** | `get_diagnostics` & `suggest_fixes` | Running slow full builds on minor edits |

---

### Operating Rules

1. **Before Editing Any Exported Symbol or Public API**:
   - Always run `blast_radius` on the target file or symbol to understand downstream dependencies and test coverage before making changes.
2. **Speculative Execution for Non-Trivial Edits**:
   - Use `preview_edit` to evaluate the diagnostic delta (errors/warnings added or removed) before committing writes to disk.
3. **Post-Edit Verification**:
   - Call `get_diagnostics` to immediately confirm no new syntax or type errors were introduced, followed by the project self-healing verify loop (`python3 .trellis/scripts/verify.py`).
4. **CLI Fallback & Health**:
   - Run `agent-lsp doctor` to check the health and capabilities of configured language servers in the current environment.
   - Use `agent-lsp init` to automatically detect new language servers installed in the workspace.
