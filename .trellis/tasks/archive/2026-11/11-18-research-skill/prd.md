# Add /research skill combining NotebookLM and Context7

## Goal

Provide developers and AI agents with a specialized, autonomous `/research` capability that seamlessly unites **Context7** (for authoritative, up-to-date documentation on libraries, frameworks, SDKs, and APIs) and **Web Search** with **Google NotebookLM** (`gemini-notebook-mcp` / `nlm`) for persistent external storage, automatic notebook organization, and grounded synthesis notes.

## Confirmed Facts & Technical Context

- **NotebookLM Integration**:
  - The framework provides full integration with Google NotebookLM via the `gemini-notebook-mcp` MCP server and `nlm` CLI ([.agents/rules/notebooklm.md](.agents/rules/notebooklm.md) and [.trellis/spec/guides/notebooklm-knowledge-base.md](.trellis/spec/guides/notebooklm-knowledge-base.md)).
  - Supported MCP tools: `notebook_list`, `notebook_get`, `notebook_create`, `notebook_rename`, `source_add` (url/text/file), `note` (create/update/list), `alias`, and `notebook_query`.
  - Supported CLI commands: `nlm list notebooks`, `nlm query`, `nlm note create`, `nlm source add`, `nlm alias set`.
- **Context7 Integration**:
  - Global user rule enforces Context7 MCP tools (`resolve-library-id` followed by `query-docs`) for documentation on libraries, frameworks, SDKs, APIs, and cloud services.
- **Skill & Workflow Conventions**:
  - Canonical skills live under `.agents/skills/<skill-name>/SKILL.md` with backwards-compatible symlink `.agent -> .agents`.
  - Slash command workflows live under `.agents/workflows/<name>.md`.
  - Multi-platform synchronization covers Claude Code (`.claude/skills/`), GitHub Copilot (`.github/skills/`), and Cursor (`.cursor/skills/`).

## Requirements

- **REQ-1 (Skill Definition & Frontmatter)**: Create `.agents/skills/research/SKILL.md` with standard YAML frontmatter (`name: research`, `description: ...`), trigger conditions, step-by-step instructions, and tool usage rules.
- **REQ-2 (Workflow Entry Point)**: Create `.agents/workflows/research.md` defining the `/research` slash command workflow, guiding the agent to activate the skill and parse the user's research query.
- **REQ-3 (Notebook Discovery & Semantic Matching)**:
  - Query all accessible notebooks (`notebook_list` / `nlm list notebooks`).
  - Semantically match notebook titles, topics, and aliases against the requested research subject.
  - If a relevant notebook exists, target it for updates; if multiple match, select the closest match and reuse its alias/ID.
- **REQ-4 (Auto-Creation of Notebooks)**:
  - If no existing notebook relates to the requested topic, automatically invoke `notebook_create` (or `nlm`) with a clear, descriptive title (e.g. `Research: <Topic>`).
  - Automatically assign a concise, human-readable alias via `alias` (e.g. `res-<topic-slug>`) for persistent, ergonomic access.
- **REQ-5 (Hybrid Information Retrieval Pipeline)**:
  - *Primary (Libraries/APIs)*: Run `resolve-library-id` and `query-docs` via Context7 when the topic concerns software packages, frameworks, CLI tools, or cloud SDKs.
  - *Fallback / Complementary (Concepts/Algorithms/Architecture)*: When Context7 yields no matches, or when the topic is conceptual/algorithmic, run web search (`search_web`) or NotebookLM native research (`research_start` / `research_status`) to gather current whitepapers and articles.
- **REQ-6 (Source Ingestion & Synthesis Note Persistence)**:
  - Ingest retrieved URLs and text documentation into the resolved notebook via `source_add` (`source_type="url"` or `"text"`).
  - Generate an atomic, structured synthesis note via `note` (`action="create"`), structured with:
    1. Executive Summary & Problem Scope
    2. Key Architectural Mechanisms & Technical Specifications
    3. Code Samples, API Contracts, or Configuration Recipes
    4. Curated Bibliography & Source Links
- **REQ-7 (RAG Grounding & User Response)**:
  - Run a validation query (`notebook_query` / `nlm query`) to verify that the ingested knowledge is indexed and queryable.
  - Present the user with a concise research digest, cited facts, and clickable/named references to the notebook ID and alias.
- **REQ-8 (Multi-Platform Synchronization)**:
  - Mirror or symlink the new skill to `.claude/skills/research/`, `.github/skills/research/`, and reference it in [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md).

## Out of Scope

- Modifying existing core Trellis CLI binaries (`.trellis/scripts/*.py`).
- Automatic deletion or restructuring of unrelated existing NotebookLM notebooks.
- Interactive audio/video podcast generation (NotebookLM Studio artifacts) during basic `/research` runs unless explicitly asked by the user.

## Acceptance Criteria

- [x] `AC-1`: `.agents/skills/research/SKILL.md` is implemented, specifying the hybrid retrieval protocol and NotebookLM storage contracts.
- [x] `AC-2`: `.agents/workflows/research.md` is available and wired to trigger on `/research`.
- [x] `AC-3`: Notebook lookup correctly detects existing notebooks and creates a new one with an alias when no match is found.
- [x] `AC-4`: Context7 is invoked first for library topics, falling back gracefully to web search for non-library topics.
- [x] `AC-5`: Sources are ingested into the notebook (`source_add`) and a structured synthesis note is created (`note`).
- [x] `AC-6`: Multi-platform directories (`.claude/skills/`, `.github/skills/`) and master documentation (`AGENTS.md`, `CLAUDE.md`) are updated and synchronized.
- [x] `AC-7`: All validation checks and code graph updates pass cleanly.
