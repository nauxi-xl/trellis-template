---
trigger: always_on
description: Proactively retrieve and persist project knowledge, architecture decisions, research syntheses, and bug post-mortems in Google NotebookLM via gemini-notebook-mcp and nlm CLI.
---

## NotebookLM Knowledge Base Integration

This project uses Google NotebookLM as its persistent external memory and grounded knowledge base across sessions.

### Tools Available
1. **MCP Server (`gemini-notebook-mcp`)**: Lazy-loaded MCP tools called via `call_mcp_tool`:
   - `notebook_list`, `notebook_get`, `notebook_describe`: Discover and inspect notebooks.
   - `notebook_query`, `cross_notebook_query`: Query sources inside notebooks using RAG.
   - `note`: Create, update, list, and delete notes inside notebooks (`action="create"`, `title="..."`, `content="..."`).
   - `source_add`: Ingest documentation, web links, papers, or raw text (`source_type="url"|"text"|"file"|"drive"`).
   - `notebook_create`, `alias`: Create project/topic notebooks and assign human-readable shortcuts.
   - `research_start`, `research_status`, `research_import`: Research and import web sources into notebooks.
2. **CLI (`nlm`)**: Full-featured CLI (`nlm` available on `PATH`, installed via `notebooklm-mcp-cli`):
   - `nlm list notebooks`: List all accessible notebooks.
   - `nlm query <notebook-id-or-alias> "<question>"`: Query sources directly.
   - `nlm note create <notebook> --title "..." --content "..."`: Save notes.
   - `nlm source add <notebook> --file <path>` or `--url <url>`: Add sources.
   - `nlm alias set <alias> <notebook-id>`: Create shortcuts.

---

### Proactive Lifecycle Rules

1. **Retrieve Before Planning, Researching, or Debugging (Proactive Read)**:
   - Before designing a non-trivial feature, answering an architectural/domain question, researching a library/topic, or investigating a recurring bug, check `notebook_list` (or `nlm list notebooks`) to see if a relevant project or topic notebook exists.
   - Query matching notebooks (`notebook_query` or `cross_notebook_query`) for prior decisions, constraints, research notes, or post-mortems, and weave cited facts into your plan or response.

2. **Persist After Research, Key Decisions, Bug Fixes, or Task Wrap-Up (Proactive Write)**:
   - When completing `/research`, resolving a complex/non-obvious bug, making an architectural decision, or finishing a task (`/trellis-finish-work`), save a concise synthesis note (`note` with `action="create"`, or `nlm note create`) into the project's notebook (or create/alias a project notebook if none exists).
   - When external docs, RFCs, specs, or reference URLs were critical to the work, ingest them with `source_add` (or `nlm source add`).
   - Keep repo-local coding rules (file paths, lint/type conventions) in `.trellis/spec/`; keep broader domain knowledge, research syntheses, ADRs, and post-mortems in NotebookLM.

3. **Authentication & Graceful Degradation**:
   - If `gemini-notebook-mcp` / `nlm` reports missing authentication or expired credentials, inform the user once to run `nlm login` (or inspect `nlm doctor`) and continue the task without looping on auth failures.
   - Use `server_info` or `profile` to verify the active Google account when troubleshooting.
