---
trigger: always_on
description: Use Google NotebookLM as the project's persistent knowledge brain (ask to create/bind if missing, auto-update on relevant changes), while using Graphify and agent-lsp directly for fast code location.
---

## NotebookLM Knowledge Base Integration (Project Brain)

This project treats Google NotebookLM as its **persistent project brain** — storing architecture decisions, feature PRDs/designs, domain knowledge, external research, and post-mortems across sessions.

### Clear Role Separation: NotebookLM vs. Graphify / LSP

- **NotebookLM (`gemini-notebook-mcp` / `nlm`) = Project Brain & Long-Term Memory**
  - Use for *why* and *what*: architectural decisions (ADRs), feature specifications, domain rules, research syntheses, external RFCs/docs, and debugging post-mortems.
- **Graphify (`graphify-out/` / `graphify`) + `agent-lsp` = Fast Direct Code Locator**
  - Use for *where* in the codebase: locating files, modules, classes, symbols, call hierarchies, and dependency paths.
  - **NEVER query NotebookLM as an intermediary just to locate code files or symbols** — query `graphify` (`graphify query`, `graphify path`, `graphify explain`) and `agent-lsp` directly.

---

### Tools Available
1. **MCP Server (`gemini-notebook-mcp`)**:
   - `notebook_list`, `notebook_get`, `notebook_describe`: Discover and inspect notebooks.
   - `notebook_query`, `cross_notebook_query`: Query project knowledge using RAG.
   - `notebook_create`, `alias`: Create a notebook and assign a short alias.
   - `note`: Create/update/list notes (`action="create"`, `title="..."`, `content="..."`).
   - `source_add`: Ingest URLs, files, or text (`source_type="url"|"text"|"file"|"drive"`).
2. **CLI (`nlm`) & Project Sync Script (`.trellis/scripts/notebook_sync.py`)**:
   - `python3 .trellis/scripts/notebook_sync.py --status`: Check bound notebook & pending changes.
   - `python3 .trellis/scripts/notebook_sync.py --bind <id-or-alias>`: Bind a notebook to this project (saved to `.trellis/config.yaml`).
   - `python3 .trellis/scripts/notebook_sync.py --sync`: Auto-sync pending knowledge/spec/code changes to the bound notebook.
   - `python3 .trellis/scripts/notebook_sync.py --mark-synced`: Mark current changes as synced after updating via `gemini-notebook-mcp`.

---

### Proactive Lifecycle Rules

1. **Retrieve & Ask-When-Missing (Search Protocol)**:
   - Before planning a feature, answering domain/architecture questions, or debugging recurring bugs, check `notebook_list` (or `nlm list notebooks`) and query matching notebooks (`notebook_query` / `cross_notebook_query`).
   - **If no relevant notebook exists** (and `notebooklm.project_notebook` is unbound):
     - **Ask the user** whether they want to create a new notebook (proposing a clear title & alias) or link an existing one.
     - If they agree: create/link it and immediately bind it with `python3 .trellis/scripts/notebook_sync.py --bind <id-or-alias>`.
     - If they decline: record the decision with `python3 .trellis/scripts/notebook_sync.py --mark-prompted --declined` so you do not keep asking.

2. **Auto-Update on Relevant Changes (Sync Protocol)**:
   - Whenever changes affect project knowledge — such as updating `.trellis/spec/`, task `prd.md`/`design.md`, `AGENTS.md`/`README.md`/`docs/`, architecture contracts, or resolving non-trivial bugs — **automatically update the bound notebook**:
     - Save a concise structured note via `note` (`action="create"`) or `source_add` and run `python3 .trellis/scripts/notebook_sync.py --mark-synced`, **OR**
     - Run `python3 .trellis/scripts/notebook_sync.py --sync --summary "<what changed and why>"`.
   - When `<notebook-sync status="pending" ...>` appears in context, treat syncing those pending changes as part of completing the task.

3. **Authentication & Graceful Degradation**:
   - If `gemini-notebook-mcp` / `nlm` reports missing authentication or expired credentials, inform the user once to run `nlm login` (or `nlm doctor`) and continue without looping on auth failures.
