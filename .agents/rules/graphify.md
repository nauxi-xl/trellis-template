---
trigger: always_on
description: Consult the graphify knowledge graph at graphify-out/ for fast, direct codebase navigation without routing code-location queries through NotebookLM.
---

## graphify

This project has a graphify knowledge graph at `graphify-out/`. Use it (together with `agent-lsp`) as your **fast, direct code locator** to jump straight to relevant files, classes, functions, and dependency paths — **without routing code-location lookups through NotebookLM**.

Rules:
- For codebase structure, file locations, or module relationships, when `graphify-out/graph.json` exists, first run `graphify query "<question>"` (CLI) or `query_graph` (MCP). Use `graphify path "<A>" "<B>"` / `shortest_path` for relationships and `graphify explain "<concept>"` / `get_node` for focused concepts. These return a scoped subgraph, usually much smaller than `GRAPH_REPORT.md` or raw grep output.
- If `graphify-out/graph.json` does not exist, you can ask the user to generate it with `graphify .` (AST-only, no API cost).
- If `graphify-out/wiki/index.md` exists, navigate it instead of reading raw files.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost).
