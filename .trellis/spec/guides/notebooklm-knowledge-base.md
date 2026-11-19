# NotebookLM Knowledge Base Guide

> Instructions and best practices for storing, organizing, and retrieving technical knowledge using Google NotebookLM via the `gemini-notebook-mcp` MCP server and `nlm` CLI.

---

## Overview

NotebookLM serves as the **project's external brain and long-term memory**, while **Graphify** (`graphify-out/`) and **`agent-lsp`** act as **fast direct code locators** (never route code-location lookups through NotebookLM).

- **NotebookLM stores**: Architecture Decision Records (ADRs), feature PRDs/design rationale, library/SDK research (`/research`), external docs/RFCs, and debugging post-mortems.
- **Graphify + `agent-lsp` locate**: Exact files, modules, classes, callers, and dependency paths directly in the codebase.
- **`.trellis/scripts/notebook_sync.py` automates**: Tracking project notebook binding (`notebooklm.project_notebook` in `.trellis/config.yaml`), asking the user when no relevant notebook exists, and auto-syncing knowledge/spec/code changes to the bound notebook.

---

## Tooling Interfaces

Agents and developers have two equivalent interfaces to interact with NotebookLM:

### 1. MCP Tools (`gemini-notebook-mcp`)

Call via `call_mcp_tool` with `ServerName="gemini-notebook-mcp"`:

| Tool | Action / Parameters | Purpose |
|------|---------------------|---------|
| `notebook_list` | `{}` | List all accessible notebooks, source counts, and IDs. |
| `notebook_create` | `{"title": "..."}` | Create a new notebook for the project or topic. |
| `notebook_get` | `{"notebook_id": "<id-or-alias>"}` | Get metadata and source list of a notebook. |
| `notebook_query` | `{"notebook_id": "...", "query": "..."}` | Ask questions grounded in the notebook's sources. |
| `cross_notebook_query` | `{"notebook_ids": [...], "query": "..."}` | Search across multiple notebooks simultaneously. |
| `source_add` | `{"notebook_id": "...", "source_type": "text|url|file", ...}` | Ingest documents, web links, or raw text. |
| `note` | `{"notebook_id": "...", "action": "create|list|update|delete", ...}` | Store synthesis notes, bug analysis, or decisions. |
| `alias` | `{"action": "set", "alias": "project", "notebook_id": "..."}` | Define friendly shortcuts for notebook IDs. |

### 2. CLI Tool (`nlm`)

Execute via `run_command` using the `nlm` CLI binary (available on `PATH`):

```bash
# List all notebooks
nlm list notebooks

# Create a notebook and set a short alias
nlm create notebook "My Project Knowledge"
nlm alias set project <notebook-uuid>

# Query a notebook
nlm query <notebook-id-or-alias> "What authentication architecture did we choose and why?"

# Create a note
nlm note create <notebook> --title "ADR: Auth Session Flow" --content "Key decisions and trade-offs..."

# Add a web or local source
nlm source add <notebook> --url "https://example.com/docs"
nlm source add <notebook> --file "docs/architecture.md"
```

---

## Proactive Workflow Patterns

### 1. Pre-Development & Brainstorming Retrieval
Before designing a feature, starting a task, or answering domain/architecture questions:
1. List available notebooks: `notebook_list` (MCP) or `nlm list notebooks` (CLI).
2. Query relevant notebooks (`notebook_query` / `cross_notebook_query`) for existing design constraints, past decisions, or domain context.
3. Incorporate the grounded citations into `prd.md`, `design.md`, or your implementation plan.

### 2. Post-Implementation & Debug Knowledge Capture
When a task surfaces non-obvious knowledge, tricky bug fixes, or important design decisions:
1. Save a concise synthesis note in the project's notebook (`note` `action="create"` or `nlm note create`).
2. If external references or specs were consulted, attach them via `source_add` / `nlm source add`.

### 3. Automated Deep Research via `/research` Skill
When exploring a new library, SDK, or technical domain from scratch:
- Invoke `/research <topic>` or activate the [.agents/skills/research/SKILL.md](../../../.agents/skills/research/SKILL.md) skill.
- The skill queries Context7 and Web Search, locates or creates a topic/project notebook in NotebookLM, and commits all source links and structured synthesis notes.

---

## Best Practices & Guidelines

- **Use Human-Readable Aliases**: Assign concise aliases (e.g. `project`, `arch`, `research`) to avoid copying long UUIDs.
- **Atomic, Meaningful Notes**: Keep each note focused on one topic (e.g., "ADR: Payment Retry Strategy", "Post-Mortem: Webhook Idempotency").
- **Do Not Duplicate Code Specs**: Keep repo-specific coding conventions (file paths, naming rules) in `.trellis/spec/`; use NotebookLM for broader background research, architectural reasoning, and external references.
- **Auth Maintenance**: If queries return authentication errors, execute `nlm login` in the terminal to refresh Google credentials.
