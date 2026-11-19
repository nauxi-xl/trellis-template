---
name: research
description: "Autonomous technical research combining Context7 (for up-to-date library, framework, SDK, and API documentation) and Web Search with Google NotebookLM (gemini-notebook-mcp / nlm) for persistent notebook creation, source ingestion, and synthesis note storage."
---

# /research — Autonomous Grounded Research Skill

This skill conducts deep technical research on any library, algorithm, framework, or architectural topic by uniting real-time documentation retrieval (**Context7** + Web Search) with persistent, grounded knowledge storage (**Google NotebookLM**).

---

## When to Use This Skill

* When the user runs the `/research <topic>` slash command or requests in-depth technical research on a technology, API, algorithm, or architecture.
* When planning non-trivial implementations that require authoritative documentation, external specifications, or library API verification.
* When you need to preserve research findings, vendor whitepapers, and synthesized decisions in persistent external project memory across sessions.

---

## Prerequisites & Tool Interfaces

The skill operates seamlessly using both MCP tools and CLI interfaces:

1. **Context7 (Real-Time Library Documentation)**:
   - MCP Server: `context7`
   - Tools: `resolve-library-id`, `query-docs`
2. **NotebookLM (Persistent Grounded Knowledge Base)**:
   - MCP Server: `gemini-notebook-mcp`
   - Tools: `notebook_list`, `notebook_create`, `notebook_get`, `source_add`, `note`, `alias`, `notebook_query`
   - Alternative CLI: `nlm` (available on `PATH`) for terminal environments.
3. **Web Search (Conceptual & General Research)**:
   - Native tool: `search_web` or NotebookLM `research_start` / `research_import`.

---

## 5-Step Execution Protocol

```
[1. Parse Topic] ──> [2. Match or Create Notebook] ──> [3. Hybrid Retrieval] ──> [4. Ingest & Synthesize] ──> [5. Verify & Report]
```

### Step 1: Query Analysis & Scope Formulation

1. Extract the core subject, sub-questions, and technical constraints from the user's prompt.
2. Determine whether the subject is:
   - **Library / Package / SDK / API**: (e.g., Next.js 15, Prisma, Tailwind, Vulkan, FastAPI, PyTorch).
   - **Conceptual / Algorithmic / Architectural**: (e.g., Raft consensus, OAuth 2.1 PKCE, graphics bloom shaders, memory barriers).

---

### Step 2: Notebook Discovery & Auto-Creation

Check available project notebooks to prevent fragmenting knowledge:

1. **List Existing Notebooks**:
   - Via MCP: Call `notebook_list`
   - Via CLI: Run `nlm list notebooks`
2. **Semantic Matching**:
   - Compare notebook titles, topics, and aliases against the target subject.
   - If a matching notebook already exists (e.g. `Research: Vulkan`, `vkgl`, or `auth-standards`):
     - Select it as the target notebook.
     - Optionally run `notebook_query` to check if the question was already researched.
3. **Missing Notebook Prompt & Binding**:
   - If no relevant notebook exists yet (and `notebooklm.project_notebook` in `.trellis/config.yaml` is empty):
     - **Ask the user** whether they want to create a new notebook for this project/topic (proposing title `"Research: <Clean Topic Name>"` or the project name and alias) or bind an existing notebook.
     - Once confirmed, create it via `notebook_create` / `nlm notebook create`, set an alias (`alias` / `nlm alias set`), and if it serves as the project brain, bind it via `python3 .trellis/scripts/notebook_sync.py --bind <alias-or-id>`.

---

### Step 3: Hybrid Information Retrieval Pipeline

Execute the hybrid retrieval strategy based on the topic type:

#### A. Primary Path: Software Libraries, SDKs, and APIs (Context7)
Always use Context7 whenever a software package or cloud service API is involved:
1. **Resolve Library ID**:
   - Call `resolve-library-id(libraryName="<name>", query="<what to look up>")`.
   - Select the highest-relevance `/org/project` ID matching the target version if specified.
2. **Query Documentation**:
   - Call `query-docs(libraryId="<id>", query="<specific concept or question>")`.
   - Make focused queries per concept rather than one diluted question.

#### B. Fallback / Complementary Path: Concepts & Specifications (Web Search)
If Context7 returns no matching library, or if the subject is an algorithm, mathematical formula, RFC, or hardware whitepaper:
1. Conduct targeted searches using `search_web` (e.g. `"Vulkan timeline semaphore synchronization spec site:khronos.org"` or `"Raft consensus paper pdf"`).
2. Collect the primary source URLs, official specification links, and representative code snippets.

---

### Step 4: Notebook Ingestion & Synthesis

Persist the collected knowledge permanently into the resolved notebook:

#### 1. Ingest Sources
Add all authoritative URLs and documentation extracts as permanent sources:
* **Via MCP**:
  ```json
  {
    "ServerName": "gemini-notebook-mcp",
    "ToolName": "source_add",
    "Arguments": {
      "notebook_id": "<notebook-id-or-alias>",
      "source_type": "url",
      "url": "<source-url>"
    }
  }
  ```
  *(If raw text/extract from web search or Context7 without a public URL: use `source_type="text"`, `text="..."`)*
* **Via CLI**:
  ```bash
  nlm source add <notebook-alias> --url "<source-url>"
  ```

#### 2. Author Synthesis Note
Create a comprehensive, structured synthesis note summarizing the findings:
* **Via MCP**: Call `note(action="create", notebook_id="<notebook-id-or-alias>", title="Synthesis: <Topic>", content="<markdown>")`
* **Via CLI**: Run `nlm note create <notebook-alias> --title "Synthesis: <Topic>" --content "<markdown>"`

**Synthesis Note Markdown Template**:
```markdown
# Research Synthesis: <Topic>

**Date**: <YYYY-MM-DD>
**Notebook**: <Notebook Title / Alias>
**Keywords**: <Tags>

## 1. Executive Summary
<2-3 concise paragraphs summarizing the solution, mechanism, or consensus>

## 2. Technical Specifications & Architecture
<Detailed breakdown: components, algorithms, API signatures, contracts, invariants>

## 3. Implementation Recipes & Code Examples
```<language>
// Concrete working example or configuration
```

## 4. Trade-offs & Operational Considerations
- **Advantages**: ...
- **Risks / Limitations**: ...

## 5. Bibliography & Source References
- [<Document Title>](<URL>) - <One-line relevance>
```

---

### Step 5: Verification & User Delivery

1. **Grounded Query Check**:
   - Verify the newly ingested material by executing a quick validation query:
     - MCP: `notebook_query(notebook_id="<id>", query="Summarize core mechanisms of <topic>")`
     - CLI: `nlm query <alias> "Summarize core mechanisms of <topic>"`
2. **Present Results to User**:
   - Provide a clean, markdown-formatted response with:
     - Direct answer and executive summary.
     - Code snippets and implementation guidance.
     - Reference to the target NotebookLM notebook title, ID, and alias.
     - Cited source URLs.

---

## Error Handling & Troubleshooting

* **Authentication Expired**: If NotebookLM calls fail with auth errors, notify the user:
  > *"NotebookLM authentication required. Please run `nlm login` in your terminal to authenticate your Google profile."*
* **Context7 No Results**: Seamlessly switch to Step 3B (Web Search) without blocking the user.
* **Large Corpus Warning**: Ingest only the top 3–5 highest-relevance sources per research query to prevent cluttering notebook sources.
