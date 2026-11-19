# Implementation: Language Server Protocol (LSP) Code Intelligence Integration

## Implemented Changes

1. **Installed & Verified `agent-lsp`**:
   - Downloaded and verified standalone `agent-lsp` v0.24.2 binary in `~/.local/bin/agent-lsp`.
   - Verified JSON-RPC stdio initialization and 66 code intelligence tools across 32 languages.
   - Installed `pyright` and `typescript-language-server` for language-specific analysis.

2. **Core Agent Rules (`.agents/rules/lsp.md`)**:
   - Added `lsp.md` with `always_on` trigger.
   - Defined 3-tier inspection hierarchy: LSP (primary for code) -> Graphify (architecture & high-level relationships) -> Grep/Read (fallback).
   - Documented task-to-tool matrix for `blast_radius`, `inspect_symbol`, `find_callers`, `preview_edit`, `safe_apply_edit`, `rename_symbol`, `suggest_fixes`.

3. **Multi-Agent Skills & Workflows**:
   - Authored `.agents/skills/lsp/SKILL.md` specifying the 4-Phase Safe Code Protocol (Explore -> Impact -> Speculate -> Verify).
   - Mirrored to `.claude/skills/lsp/SKILL.md` and `.github/skills/lsp/SKILL.md`.
   - Created workflow `.agents/workflows/lsp.md` for `/lsp` interactive execution.

4. **Trellis Architectural Guide & Specs**:
   - Authored `.trellis/spec/guides/lsp-code-intelligence.md` detailing communication flow, tool parameters, language server installation matrix, and operating best practices.
   - Registered guide in `.trellis/spec/guides/index.md`.

5. **MCP Client Configurations**:
   - Created root `.mcp.json` for Claude Code, Cursor, and Codex with `agent-lsp`.
   - Configured global Antigravity MCP settings in `~/.gemini/config/mcp_config.json`.

6. **Self-Healing Loop Integration**:
   - Updated `.trellis/scripts/verify.py` to auto-detect and report `agent-lsp` availability in stack inspections.
   - Updated `AGENTS.md` with LSP tooling and prerequisites.
