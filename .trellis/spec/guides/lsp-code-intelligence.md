# Language Server Protocol (LSP) Code Intelligence Guide

> Instructions and best practices for integrating, configuring, and leveraging Language Server Protocol (LSP) capabilities across coding agents using `agent-lsp`.

---

## Overview

Modern software development with autonomous AI coding agents requires precision beyond lexical text search (`grep` or regex). Text search cannot disambiguate variable names from property names, cannot navigate inheritance hierarchies, and cannot assess the blast radius of a change across dependent files.

In this framework, **`agent-lsp`** serves as a unified, warm Language Server Protocol orchestrator. It bridges standard language servers (`pyright`, `typescript-language-server`, `rust-analyzer`, `clangd`, `gopls`) with coding agents via the Model Context Protocol (MCP) and command-line interfaces.

---

## Architecture & Communication Flow

```
+-------------------------------------------------------------+
|                        Coding Agent                         |
|           (Antigravity, Claude Code, Copilot, Codex)        |
+------------------------------+------------------------------+
                               | MCP Protocol (stdio / JSON-RPC)
                               v
+-------------------------------------------------------------+
|                          agent-lsp                          |
|         - Multi-language session orchestrator               |
|         - 66 MCP tools (blast_radius, preview_edit, etc.)   |
|         - Warm indexing runtime                             |
+------------------------------+------------------------------+
                               | Stdio JSON-RPC
        +----------------------+----------------------+
        |                      |                      |
        v                      v                      v
+----------------+     +----------------+     +----------------+
| pyright-server |     | typescript-ls  |     | rust-analyzer  |
|    (Python)    |     |   (TS / JS)    |     |     (Rust)     |
+----------------+     +----------------+     +----------------+
```

---

## Tooling Interfaces

### 1. MCP Tools (`agent-lsp`)

When `agent-lsp` is registered as an MCP server, agents gain access to:

| Tool Category | Tool Name | Description & Usage |
|---------------|-----------|---------------------|
| **Impact Analysis** | `blast_radius` | Returns all exported symbols and callers partitioned into test vs non-test in one call. |
| **Inspection** | `inspect_symbol` | Fetches symbol documentation, type signatures, and container info. |
| **Outline** | `list_symbols` | Outlines top-level classes, functions, and interfaces in a file. |
| **Search** | `find_symbol` | Finds symbols across the workspace by name. |
| **Usages** | `find_references` | Finds all syntactic and semantic references to a symbol. |
| **Callers** | `find_callers` | Traces direct inbound callers leading to a function. |
| **Speculative Edit** | `preview_edit` | Simulates edits in memory and calculates before/after diagnostic delta without writing to disk. |
| **Safe Edit** | `safe_apply_edit` | Writes edits to disk only if preview succeeds and server is warm. |
| **Refactoring** | `replace_symbol_body` | Replaces an entire function or class body accurately. |
| **Safe Rename** | `rename_symbol` | Renames a symbol and all references across files synchronously. |
| **Diagnostics** | `get_diagnostics` | Retrieves active compiler and type-checker errors/warnings. |
| **Code Actions** | `suggest_fixes` | Retrieves quick fixes and automated code repairs from the language server. |

### 2. CLI Tooling (`agent-lsp`)

Agents or developers can run diagnostic commands via `run_command`:

```bash
# Verify health of all language servers in the current workspace
agent-lsp doctor

# Auto-detect language servers and generate tool configurations
agent-lsp init

# Update agent-lsp to the latest release
agent-lsp update
```

---

## Language Server Installation Matrix

`agent-lsp` automatically discovers language server executables in `PATH`. Install the relevant servers based on your project stack:

| Language | Recommended Language Server | Installation Method |
|----------|-----------------------------|---------------------|
| **Python** | `pyright` | `uv tool install pyright` or `npm install -g pyright` |
| **TypeScript / JavaScript** | `typescript-language-server` | `pnpm add -g typescript-language-server typescript` |
| **Rust** | `rust-analyzer` | `rustup component add rust-analyzer` |
| **C / C++** | `clangd` | System package manager (`apt install clangd` / `brew install llvm`) |
| **Go** | `gopls` | `go install golang.org/x/tools/gopls@latest` |
| **HTML / CSS / JSON** | `vscode-langservers-extracted` | `npm install -g vscode-langservers-extracted` |
| **YAML** | `yaml-language-server` | `npm install -g yaml-language-server` |

---

## Agent Configuration Setup

### 1. Project-Level MCP Configuration (`.mcp.json`)

Place at the root of the repository to enable support for Claude Code, Cursor, and Codex:

```json
{
  "mcpServers": {
    "agent-lsp": {
      "command": "agent-lsp",
      "args": []
    }
  }
}
```

### 2. Antigravity Global Configuration (`~/.gemini/config/mcp_config.json`)

Add `agent-lsp` to your active MCP servers:

```json
{
  "mcpServers": {
    "agent-lsp": {
      "command": "agent-lsp",
      "args": [],
      "disabled": false
    }
  }
}
```

---

## Operating Best Practices for AI Agents

1. **Hierarchy of Inspection**:
   - Use **LSP** for code logic, type checks, caller graphs, and refactorings.
   - Use **Graphify** (`graphify query`) for broad architectural patterns and cross-subsystem dependencies.
   - Use **Grep** only for raw text, documentation, comments, and unindexed configuration files.
2. **Never Edit Blindly**:
   - Before modifying any function used across packages, run `blast_radius`.
   - If blast radius affects test files, plan to execute those specific test suites.
3. **Speculative Previewing**:
   - When touching complex signatures, invoke `preview_edit` to ensure the diagnostic delta is strictly non-regressive before modifying disk.
