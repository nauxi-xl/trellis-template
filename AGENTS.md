<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — active and archived tasks (PRDs, research, jsonl context)

If a Trellis command is available on your platform (e.g. `/trellis-finish-work`, `/trellis-continue`), prefer it over manual steps.

If you're using Antigravity, Claude Code, Codex, or another agent tool:
- `.agents/skills/` — reusable Trellis & UI design skills
- `.agents/hooks/` — lifecycle context injectors and statusline runner
- `.agents/rules/` — knowledge base & code graph rules

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.
<!-- TRELLIS:END -->

# Project Knowledge & Tools

- **SDLC Adaptive Discovery**: Interactive 5-dimensional elicitation loop, SDLC model decision matrix (Agile, Waterfall, TDD, Spiral, Kanban), and specialized hybrid agent councils. See [.agents/skills/sdlc-adaptive-discovery/SKILL.md](.agents/skills/sdlc-adaptive-discovery/SKILL.md) and workflow `/sdlc-discovery`.
- **Autonomous Research (/research)**: Combines Context7 (for up-to-date library/API docs) and Web Search with Google NotebookLM for persistent notebook creation, source ingestion, and synthesis note storage. See [.agents/skills/research/SKILL.md](.agents/skills/research/SKILL.md) and workflow `/research`.
- **Self-Healing Verification Loop**: Autonomous compiler, type-checker, and test execution harness with bounded repair cycles and structured `<self-healing-feedback>` diagnostic envelopes via `python3 .trellis/scripts/verify.py`. See [.agents/skills/trellis-check/SKILL.md](.agents/skills/trellis-check/SKILL.md).
- **NotebookLM Knowledge Base**: Grounded research, technical specifications, and architectural notes are accessible via the `gemini-notebook-mcp` MCP server and `nlm` CLI. See [.agents/rules/notebooklm.md](.agents/rules/notebooklm.md) and [.trellis/spec/guides/notebooklm-knowledge-base.md](.trellis/spec/guides/notebooklm-knowledge-base.md).
- **Code Graph (Graphify)**: Architecture queries and code navigation are available via `graphify-out/` and `graphify query`. See [.agents/rules/graphify.md](.agents/rules/graphify.md).
- **LSP Code Intelligence & Refactoring (/lsp)**: IDE-grade semantic analysis, type-aware code navigation, blast-radius analysis, and speculative safe edits across 30+ languages via the `agent-lsp` MCP server and CLI. See [.agents/skills/lsp/SKILL.md](.agents/skills/lsp/SKILL.md), [.agents/rules/lsp.md](.agents/rules/lsp.md), and [.trellis/spec/guides/lsp-code-intelligence.md](.trellis/spec/guides/lsp-code-intelligence.md).
- **Git Isolated Worktrees**: Multi-agent concurrent task isolation, automated branching, and safe rebase/merge verification via `python3 .trellis/scripts/worktree.py`. See [.agents/rules/worktrees.md](.agents/rules/worktrees.md) and [.trellis/spec/guides/git-worktrees.md](.trellis/spec/guides/git-worktrees.md).
- **Dynamic Context Engine**: Token-efficient adaptive context assembler that maps git diffs, active task state, and LSP/Graphify signals to scoped specs via `python3 .trellis/scripts/dynamic_context.py`. See [.trellis/spec/guides/dynamic-context.md](.trellis/spec/guides/dynamic-context.md).
- **Automated CI/CD Pipelines**: Production GitHub Actions workflows for continuous integration, self-healing verification matrix, and PR branch compliance. See [.github/workflows/ci.yml](.github/workflows/ci.yml) and [.trellis/spec/guides/cicd-pipeline.md](.trellis/spec/guides/cicd-pipeline.md).

# Multi-Agent & Platform Entry Points

This template is configured to be universal and work out-of-the-box with all major coding agents:

- **Universal Standard**: [AGENTS.md](AGENTS.md) (canonical master instruction file for Antigravity, OpenAI Codex, Amp, Aider, Cline, Roo Code).
- **Google Antigravity**: Uses `.agents/` with unified skills, rules, workflows, and lifecycle hooks (`.agent` is symlinked to `.agents` for zero-friction backwards compatibility).
- **Claude Code**: Native configuration in `.claude/` (`settings.json`, `commands/`, `agents/`, `hooks/`, `skills/`) with root fallback [CLAUDE.md](CLAUDE.md).
- **Cursor IDE**: Native configuration in `.cursor/` (`rules/`, `commands/`, `skills/`, `hooks.json`) with root fallback [.cursorrules](.cursorrules).
- **OpenAI Codex**: Native configuration in `.codex/` (`config.toml`, `hooks.json`, `agents/`) consuming shared `.agents/skills/`.
- **GitHub Copilot**: Native configuration in `.github/` (`copilot-instructions.md`, `skills/`, `agents/`, `prompts/`).
- **Gemini CLI**: Native configuration in `.gemini/` (`settings.json`, `commands/`, `agents/`) with root fallback [GEMINI.md](GEMINI.md).
- **Windsurf / Devin**: Native configuration in `.devin/` with root fallback [.windsurfrules](.windsurfrules).
- **Other Supported Agents**: `.opencode/`, `.kiro/`, `.trae/`, `.qoder/`, `.codebuddy/`, `.pi/`, `.kimi-code/`, `.grok/`.

# Required Tools

This template assumes you have the following tools installed and configured:

- **Node.js**: For running the Trellis CLI and other Node-based tools. Install via your package manager or from [nodejs.org](https://nodejs.org/).
- **Python 3**: For running Python scripts and tools. Install via your package manager or from [python.org](https://www.python.org/).
- **Git**: For version control and collaboration. Install via your package manager or from [git-scm.com](https://git-scm.com/).
- **uv** (Optional): For easy Python workspace management. Install via your package manager or from [uv.dev](https://uv.dev/).
- **Trellis CLI**: For task management, workflow commands, and context injection. Install via `npm install -g @mindfoldhq/trellis@latest`.
- **Graphify**: For knowledge graph queries and code navigation. Install via `uv tool install graphifyy`.
- **NotebookLM MCP**: For accessing the NotebookLM knowledge base. Install via `uv tool install notebook-mcp-cli`.
- **Context7**: For up-to-date document researches and context retrieval. Install via `npm install -g context7`.
- **agent-lsp**: For semantic Language Server Protocol code intelligence and speculative refactoring. Install via `curl -fsSL https://raw.githubusercontent.com/blackwell-systems/agent-lsp/main/install.sh | sh` (or download to `~/.local/bin/agent-lsp`).
- **Language Servers**: Project-specific language servers: `pyright` for Python (`uv tool install pyright`), `typescript-language-server` for TS/JS (`pnpm add -g typescript-language-server typescript`), `rust-analyzer` for Rust, `clangd` for C/C++, `gopls` for Go.

Remember to ask user for any missing tools or configurations before proceeding with tasks. NotebookLM MCP and Context7 must be authenticated by user before use. Notify user if any of these tools are missing or not authenticated.