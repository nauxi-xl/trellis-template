# Technical Design: LSP Code Intelligence & Refactoring Architecture

## Architecture Overview

```
                      +-----------------------------+
                      |       Coding Agents         |
                      | Antigravity / Claude Code / |
                      |    Copilot / Codex / IDE    |
                      +--------------+--------------+
                                     | MCP Protocol / CLI
                                     v
                      +-----------------------------+
                      |          agent-lsp          |
                      |  MCP Server & Orchestrator  |
                      | (66 tools, warm background) |
                      +--------------+--------------+
                                     | JSON-RPC (stdio)
        +----------------------------+----------------------------+
        |                            |                            |
        v                            v                            v
+------------------+         +------------------+         +------------------+
|      pyright     |         | typescript-ls    |         |  rust-analyzer / |
|     (Python)     |         | (TS / JS / Node) |         |  clangd / gopls  |
+------------------+         +------------------+         +------------------+
```

## Tooling Hierarchy

In `trellis-template`, code comprehension follows a 3-tier hierarchy:
1. **LSP Tools (`agent-lsp`)**:
   - Primary for AST-accurate semantic queries: definition, callers, usages, type information, diagnostic validation, and speculative in-memory edits.
2. **Code Graph (`graphify`)**:
   - High-level architecture, module clustering, god nodes, cross-file conceptual paths, and high-level structural overviews.
3. **File Scanning & Grep**:
   - Fallback for non-code assets (markdown, yaml, json, regex matching across unindexed text).

## Core LSP Tools Mapping

| Task | LSP MCP Tool | Fallback / Alternative |
|------|--------------|------------------------|
| Impact / Blast Radius | `blast_radius` | Manual search of callers |
| List File Outline | `list_symbols` | Manual reading of whole file |
| Find Symbol by Name | `find_symbol` | Grep for identifier |
| Find All Usages | `find_references` | Grep across project |
| Inspect Symbol & Type | `inspect_symbol` | Reading type definition files |
| Direct Callers | `find_callers` | Grep for invocation |
| Speculative Edit | `preview_edit` / `safe_apply_edit` | Direct edit & hope tests pass |
| Quick Fixes | `suggest_fixes` | Manual compilation fixes |
| Safe Rename | `rename_symbol` | Manual search & replace |

## Configuration Strategy
1. **Project-level**: `.mcp.json` exposing `agent-lsp` with auto-detected servers.
2. **User Global (Antigravity CLI)**: `~/.gemini/config/mcp_config.json` registering `agent-lsp`.
3. **Multi-Agent Skills**: Unified `lsp` skill in `.agents/skills/lsp/SKILL.md`, `.claude/skills/lsp/SKILL.md`, and `.github/skills/lsp/SKILL.md`.
