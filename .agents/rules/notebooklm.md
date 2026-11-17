---
trigger: always_on
description: Use NotebookLM via gemini-notebook-mcp MCP server and nlm CLI for storing and retrieving project knowledge, research, and technical notes.
---

## NotebookLM Knowledge Base Integration

This project uses Google NotebookLM as an external knowledge base for research, architectural notes, technical documentation, and long-term memory retrieval.

### Tools Available
1. **MCP Server (`gemini-notebook-mcp`)**: Lazy-loaded MCP tools called via `call_mcp_tool`:
   - `notebook_list`, `notebook_get`, `notebook_describe`: Discover and inspect notebooks.
   - `notebook_query`, `cross_notebook_query`: Query sources inside notebooks using RAG.
   - `note`: Create, update, list, and delete notes inside notebooks (`action="create"`, `title="..."`, `content="..."`).
   - `source_add`: Ingest documentation, web links, papers, or raw text (`source_type="url"|"text"|"file"|"drive"`).
   - `alias`: Assign human-readable shortcuts to notebook UUIDs.
   - `research_start`, `research_status`, `research_import`: Research and import web sources into notebooks.
2. **CLI (`nlm`)**: Full-featured CLI located at `/home/nauxi/.local/bin/nlm`:
   - `nlm list notebooks`: List all accessible notebooks.
   - `nlm query <notebook-id-or-alias> "<question>"`: Query sources directly.
   - `nlm note create <notebook> --title "..." --content "..."`: Save notes.
   - `nlm source add <notebook> --file <path>` or `--url <url>`: Add sources.
   - `nlm alias set <alias> <notebook-id>`: Create shortcuts.

---

### Operating Rules

1. **Retrieval Protocol (Querying Knowledge)**:
   - When asked about research papers, external graphics algorithms, Vulkan specifications, or project-related study notes, check available notebooks first (`notebook_list` or `nlm list notebooks`).
   - Query the relevant notebook using `notebook_query` or `nlm query <notebook> "<query>"`.
   - Incorporate cited facts and source quotes into your plan or response.

2. **Storage Protocol (Persisting Knowledge)**:
   - When completing non-trivial research, debugging complex driver bugs, profiling benchmarks, or discovering important technical patterns, persist the findings into an appropriate project notebook.
   - Use `note` (action `create`) or `nlm note create` for synthesis notes, contracts, and summaries.
   - Use `source_add` or `nlm source add` to ingest full reference documents, shader papers, or specification text.

3. **Authentication & Profile Health**:
   - If authentication fails, run `nlm login` via `run_command` or inspect `nlm doctor`.
   - Use `server_info` or `profile` to verify the active Google account.
