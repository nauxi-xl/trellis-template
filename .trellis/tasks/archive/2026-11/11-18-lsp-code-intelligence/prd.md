# PRD: Language Server Protocol (LSP) Code Intelligence Integration

## Problem Statement
Coding agents often rely purely on syntactic grep or manual file scanning to navigate code, discover references, inspect symbol definitions, or assess the ripple effects of code modifications. This leads to:
1. **Missed Usages**: Grep misses aliased, inherited, or dynamically imported symbols, and produces noise on common variable names.
2. **Blind Edits**: Modifying a function signature or renaming a variable across multiple files can introduce silent regressions in downstream callers without early warnings.
3. **No Speculative Verification**: Applying an edit directly to disk without previewing diagnostic diffs (syntax errors, missing parameters, type mismatches) increases iterative trial-and-error costs.

## Proposed Solution
Integrate **`agent-lsp`** (an MCP server orchestrating Language Server Protocols across 32+ languages) directly into `trellis-template`:
1. **MCP Integration**: Configure `agent-lsp` in `~/.gemini/config/mcp_config.json` (for Google Antigravity) and `.mcp.json` (for Claude Code, Cursor, Copilot, Codex).
2. **Rules & Guidance**: Add `.agents/rules/lsp.md` to establish clear code intelligence rules and tool precedence:
   - Prefer LSP tools (`find_references`, `inspect_symbol`, `blast_radius`, `find_callers`) over blind `grep`.
   - Prefer `preview_edit` and `safe_apply_edit` for impactful changes.
3. **Dedicated Skills & Workflow**:
   - Provide `.agents/skills/lsp/SKILL.md` (and mirror to `.claude/skills/lsp/` and `.github/skills/lsp/`).
   - Provide `.agents/workflows/lsp.md` for interactive symbol discovery, refactoring, and verification.
4. **Trellis Architectural Spec**: Add `.trellis/spec/guides/lsp-code-intelligence.md` detailing language server prerequisites, setup commands, and tool capabilities.
5. **Global Framework Documentation**: Update `AGENTS.md` and verification scripts with LSP awareness.

## Key Requirements & Acceptance Criteria
- [x] Prebuilt `agent-lsp` binary installed and operational in `~/.local/bin/agent-lsp`.
- [x] Auto-detection of language servers (e.g. `pyright`, `typescript-language-server`, `rust-analyzer`, `clangd`).
- [x] Rules in `.agents/rules/lsp.md` guiding agents on exact task-to-tool mappings.
- [x] Multi-agent skill definitions mirrored across `.agents/`, `.claude/`, and `.github/`.
- [x] Global configuration in `~/.gemini/config/mcp_config.json` and project `.mcp.json`.
- [x] Updated `AGENTS.md` and `.trellis/spec/guides/index.md`.
