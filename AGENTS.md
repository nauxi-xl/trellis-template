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
- **NotebookLM Knowledge Base**: Grounded research, technical specifications, and architectural notes are accessible via the `gemini-notebook-mcp` MCP server and `nlm` CLI. See [.agents/rules/notebooklm.md](.agents/rules/notebooklm.md) and [.trellis/spec/guides/notebooklm-knowledge-base.md](.trellis/spec/guides/notebooklm-knowledge-base.md).
- **Code Graph (Graphify)**: Architecture queries and code navigation are available via `graphify-out/` and `graphify query`. See [.agents/rules/graphify.md](.agents/rules/graphify.md).

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

Remember to ask user for any missing tools or configurations before proceeding with tasks. NotebookLM MCP and Context7 must be authenticated by user before use. Notify user if any of these tools are missing or not authenticated.