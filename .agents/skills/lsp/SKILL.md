---
name: lsp
description: "Language Server Protocol (LSP) code intelligence and refactoring using agent-lsp for semantic navigation, type inspection, blast-radius analysis, and speculative safe edits."
user-invocable: true
---

# /lsp — Language Server Protocol Code Intelligence & Refactoring Skill

This skill provides IDE-grade semantic analysis, type-aware code navigation, blast-radius analysis, and safe speculative refactoring across 30+ programming languages powered by **`agent-lsp`**.

---

## When to Use This Skill

* When the user runs `/lsp`, `/lsp-explore`, `/lsp-refactor`, `/lsp-impact`, or asks questions about code structure, definitions, or references.
* Before modifying any exported function, class, or public API: analyze callers and blast radius to prevent regressions.
* When navigating unfamiliar or complex codebases: inspect symbols, outline files, or find implementations without manual file reading.
* When refactoring or renaming symbols across multiple files safely.
* When verifying compiler/type-checker diagnostics and applying automated quick fixes.

---

## Prerequisites & Tool Interfaces

The skill operates via the `agent-lsp` MCP server and CLI:

1. **MCP Server (`agent-lsp`)**:
   - Access tools: `blast_radius`, `preview_edit`, `safe_apply_edit`, `get_diagnostics`, `list_symbols`, `find_symbol`, `find_references`, `inspect_symbol`, `find_callers`, `rename_symbol`, `replace_symbol_body`, `safe_delete_symbol`, `suggest_fixes`.
2. **CLI Runner (`agent-lsp`)**:
   - Binary located at `$HOME/.local/bin/agent-lsp`.
   - `agent-lsp doctor`: Inspect configured language servers and health status.
   - `agent-lsp init`: Auto-detect installed language servers in the workspace.
   - `agent-lsp update`: Self-update the binary.

---

## 4-Phase Safe Code Protocol

```
[Phase 1: Explore & Inspect] ──> [Phase 2: Blast-Radius Analysis] ──> [Phase 3: Speculative Edit] ──> [Phase 4: Verify & Fix]
```

### Phase 1: Semantic Exploration & Symbol Inspection

Instead of scanning whole files with `Read` or grepping:
1. **File Outline**: Call `list_symbols` on the file to inspect classes, functions, interfaces, and methods.
2. **Symbol Deep-Dive**: Call `inspect_symbol` to fetch exact type signatures, docstrings, and container details.
3. **Trace Invocations**: Call `find_callers` to construct the direct call hierarchy leading into a function.

### Phase 2: Impact & Blast-Radius Analysis

Before editing any function, type, or exported contract:
1. Call `blast_radius` on the target file or symbol.
2. Review the partitioned output:
   - **Non-test Callers**: Production code paths affected by this change.
   - **Test Callers**: Existing test suites that validate this symbol and must be re-run or updated.
3. If changing an interface or abstract class: call `find_implementations` to identify all concrete types that must adhere to the change.

### Phase 3: Speculative Execution & Safe Editing

1. **Preview in Memory**: Call `preview_edit` with the proposed changes.
   - Evaluates the change against the warm language server without touching disk.
   - Returns the exact diagnostic delta (errors/warnings created vs fixed).
2. **Safe Application**:
   - For localized changes: Use `safe_apply_edit` or `replace_symbol_body`.
   - For renames: Call `rename_symbol` to propagate updates across all files atomically.
   - For removing deprecated code: Call `safe_delete_symbol` (aborts if references still exist).

### Phase 4: Diagnostic Validation & Self-Healing

1. **LSP Diagnostics**: Call `get_diagnostics` immediately after changes to catch syntax and type errors.
2. **Quick Fixes**: If compiler diagnostics remain, call `suggest_fixes` to inspect and apply server-provided code actions.
3. **Self-Healing Loop**: Execute `python3 .trellis/scripts/verify.py` to run project-wide typechecks, linters, and unit tests with structured diagnostics.

---

## Tool Reference Matrix

| Task | Primary LSP Tool | Notes |
|------|------------------|-------|
| Analyze change blast radius | `blast_radius` | Partitioned test vs non-test callers in 1 call |
| Inspect symbol & types | `inspect_symbol` | Returns docstring, signature, line position |
| Find workspace symbol | `find_symbol` | Search by identifier name across workspace |
| Find all usages | `find_references` | AST-grounded references across files |
| Direct call hierarchy | `find_callers` | Upstream functions that invoke this target |
| Speculative edit preview | `preview_edit` | Memory preview; returns diagnostic diff |
| Safe apply edit | `safe_apply_edit` | Writes to disk only if preview succeeds |
| Replace function body | `replace_symbol_body`| Exact AST body replacement |
| Rename symbol | `rename_symbol` | Multi-file synchronized rename |
| Fetch active diagnostics | `get_diagnostics` | Real-time compiler/type errors |
| Apply quick fixes | `suggest_fixes` | Language server automated code actions |

---

## Language Server Setup Guide

| Language | Language Server Package | Installation Command |
|----------|-------------------------|----------------------|
| **Python** | `pyright` | `uv tool install pyright` or `npm i -g pyright` |
| **TypeScript / JS** | `typescript-language-server` | `pnpm add -g typescript-language-server typescript` |
| **Rust** | `rust-analyzer` | `rustup component add rust-analyzer` |
| **C / C++** | `clangd` | `apt install clangd` or via LLVM toolchain |
| **Go** | `gopls` | `go install golang.org/x/tools/gopls@latest` |
