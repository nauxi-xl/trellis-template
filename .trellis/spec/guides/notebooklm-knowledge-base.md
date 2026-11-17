# NotebookLM Knowledge Base Guide

> Instructions and best practices for storing, organizing, and retrieving technical knowledge using Google NotebookLM via the `gemini-notebook-mcp` MCP server and `nlm` CLI.

---

## Overview

NotebookLM serves as an external, grounded knowledge base for the project. While Trellis specs (`.trellis/spec/`) store immediate repository-level coding conventions and git tracks source code, NotebookLM stores:

- External research papers and graphics algorithm specifications (e.g. AMD FidelityFX CAS, Kawase Bloom, ACES tonemapping).
- Hardware vendor whitepapers (Vulkan Best Practices from ARM, NVIDIA, AMD, Khronos).
- Long-form troubleshooting post-mortems and profiling traces that are too large for git.
- Cross-session domain knowledge and project notes.

---

## Tooling Interfaces

Agents and developers have two equivalent interfaces to interact with NotebookLM:

### 1. MCP Tools (`gemini-notebook-mcp`)

Call via `call_mcp_tool` with `ServerName="gemini-notebook-mcp"`:

| Tool | Action / Parameters | Purpose |
|------|---------------------|---------|
| `notebook_list` | `{}` | List all accessible notebooks, source counts, and IDs. |
| `notebook_get` | `{"notebook_id": "<id-or-alias>"}` | Get metadata and source list of a notebook. |
| `notebook_query` | `{"notebook_id": "...", "query": "..."}` | Ask questions grounded in the notebook's sources. |
| `cross_notebook_query` | `{"notebook_ids": [...], "query": "..."}` | Search across multiple notebooks simultaneously. |
| `source_add` | `{"notebook_id": "...", "source_type": "text|url|file", ...}` | Ingest documents, web links, or raw text. |
| `note` | `{"notebook_id": "...", "action": "create|list|update|delete", ...}` | Store synthesis notes, bug analysis, or decisions. |
| `alias` | `{"action": "set", "alias": "vkgl", "notebook_id": "..."}` | Define friendly shortcuts for notebook IDs. |

### 2. CLI Tool (`nlm`)

Execute via `run_command` using the `/home/nauxi/.local/bin/nlm` binary:

```bash
# List all notebooks
nlm list notebooks

# Query a notebook
nlm query <notebook-id-or-alias> "How does Vulkan timeline semaphore synchronization work?"

# Create a note
nlm note create <notebook> --title "Draw Call Optimization Benchmark" --content "Findings from frame profiling..."

# Add a web or local source
nlm source add <notebook> --url "https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html"
nlm source add <notebook> --file "/path/to/research_paper.pdf"

# Set an alias
nlm alias set vkgl <notebook-uuid>
```

---

## Workflow Patterns

### 1. Pre-Development Research Phase
Before implementing complex graphics, memory, or pipeline features:
1. List available notebooks: `nlm list notebooks` or MCP `notebook_list`.
2. Check if a relevant notebook exists (e.g. dedicated to graphics, Vulkan, or project history).
3. Query the notebook for design constraints, algorithms, or past decisions:
   ```json
   {
     "ServerName": "gemini-notebook-mcp",
     "ToolName": "notebook_query",
     "Arguments": {
       "notebook_id": "vkgl",
       "query": "What are the required memory barrier flags when transitioning offscreen FBO textures to shader read?"
     }
   }
   ```
4. Integrate the grounded citations into your task `design.md` or implementation plan.

### 2. Post-Implementation Knowledge Capture
When a task surfaces non-obvious knowledge, novel bug fixes, or performance insights:
1. Create a structured note in the project's notebook:
   ```bash
   nlm note create vkgl --title "Post-Mortem: Avoiding waitIdle in Upload Ring" --content "..."
   ```
2. If new external specifications or papers were consulted, add them as permanent sources:
   ```bash
   nlm source add vkgl --url "<spec-url>"
   ```

---

## Best Practices & Guidelines

- **Use Human-Readable Aliases**: Assign concise aliases (e.g. `vkgl`, `vulkan`, `mod-compat`) to avoid copying long UUIDs.
- **Atomic, Meaningful Notes**: Keep each note focused on one topic (e.g., "Swapchain Recreation Invariants", "Flywheel Matrix Compatibility").
- **Do Not Duplicate Code Specs**: Keep repo-specific rules (file paths, method names) in `.trellis/spec/`; use NotebookLM for rich reference materials, background research, and external documentation.
- **Auth Maintenance**: If queries return authentication errors, execute `nlm login` in the terminal to refresh Google credentials.
