# Technical Design: `/research` Skill (NotebookLM + Context7 Hybrid)

## Architecture & System Overview

The `/research` skill provides a unified knowledge retrieval and persistence loop for AI agents working in this project. It bridges two distinct knowledge layers:
1. **Dynamic Ephemeral Retrieval**: Real-time documentation querying via Context7 MCP (for libraries/SDKs) and web search (for conceptual/algorithmic topics).
2. **Persistent Grounded Storage**: Long-term external memory via Google NotebookLM (`gemini-notebook-mcp` and `nlm` CLI) for indexing sources and storing synthesis notes.

```
                  +-----------------------------------+
                  |           User Request            |
                  |     /research <topic/question>    |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------+-----------------+
                  |      Step 1: Topic Parsing        |
                  |  Extract Core Subject & Keywords  |
                  +-----------------+-----------------+
                                    |
                                    v
+-----------------------------------+-----------------------------------+
|               Step 2: Notebook Discovery & Resolution                 |
|  - List notebooks (notebook_list / nlm list notebooks)                |
|  - Check title/alias for semantic match to topic                      |
|    * MATCH FOUND: Target existing notebook                            |
|    * NO MATCH: Create new notebook (notebook_create) & set alias     |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------+-----------------------------------+
|                 Step 3: Hybrid Retrieval Pipeline                     |
|                                                                       |
|  [Is topic a Library / SDK / Framework / API?]                        |
|       |                                                               |
|      YES ──> Context7: resolve-library-id -> query-docs               |
|       |                                                               |
|       NO (or Context7 misses) ──> Web Search (search_web) /           |
|                                   NotebookLM research_start           |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------+-----------------------------------+
|            Step 4: Notebook Ingestion & Synthesis                     |
|  - Add reference URLs & documents via source_add                      |
|  - Author structured synthesis note via note (action="create")        |
|  - (Optional) Verify via notebook_query                               |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
                  +-----------------+-----------------+
                  |   Step 5: User Response & Summary |
                  |  Key findings, citations, links   |
                  +-----------------------------------+
```

## Detailed Component Specifications

### 1. Skill Contract & Directory Structure
- Skill location: `.agents/skills/research/SKILL.md`
- Workflow entrypoint: `.agents/workflows/research.md`
- Cross-platform distribution:
  - `.agent/skills/research` (symlinked)
  - `.claude/skills/research/SKILL.md` (mirrored)
  - `.github/skills/research/SKILL.md` (mirrored)

### 2. Notebook Discovery Algorithm
```python
# Conceptual matching logic in SKILL.md
1. notebooks = notebook_list()
2. topic_tokens = extract_keywords(user_query)
3. matched = None
   for nb in notebooks:
       if similarity(nb.title, user_query) > threshold or any(tok in nb.title.lower() for tok in topic_tokens):
           matched = nb
           break
4. if not matched:
       nb_title = f"Research: {clean_topic_title}"
       matched = notebook_create(title=nb_title)
       alias = generate_slug(clean_topic_title)
       alias(action="set", alias=f"res-{alias}", notebook_id=matched.id)
5. target_notebook = matched.id (or alias)
```

### 3. Hybrid Retrieval Rules
- **Rule 1 (Context7 First for Libraries)**: Whenever the topic contains a recognized software library, framework, tool, or cloud API (e.g., React, Prisma, Vulkan, Docker, Pandas, FastAPI, Next.js), agents must run:
  1. `resolve-library-id(libraryName, query)`
  2. `query-docs(libraryId, query)`
- **Rule 2 (Search Fallback for Conceptual Topics)**: If `resolve-library-id` returns no relevant library, or if the topic is inherently conceptual/algorithmic (e.g. distributed consensus, rendering pipeline theory, security standards):
  1. Perform targeted web search (`search_web` or Google NotebookLM `research_start`).
  2. Extract primary documentation URLs and core passages.

### 4. Storage & Note Synthesis Contract
Every `/research` execution must store:
1. **Sources**: Run `source_add` with `source_type="url"` for external links, or `source_type="text"` with extracted content if a direct URL is unavailable.
2. **Synthesis Note**: Run `note` with `action="create"`, `title="Synthesis: <Topic>"`. The note must adhere to this markdown format:
   ```markdown
   # Synthesis: <Topic>
   **Date**: <ISO-Date>
   **Target Topic**: <User Query>

   ## 1. Executive Summary
   <2-3 concise paragraphs summarizing the solution, mechanism, or consensus>

   ## 2. Technical Specifications & Architecture
   <Detailed breakdown: components, algorithms, API signatures, contracts>

   ## 3. Implementation Guidelines & Code Snippets
   <Working examples, configuration flags, or usage patterns>

   ## 4. References & Sources
   - [<Source Title>](<Source URL>)
   ```

### 5. Error Handling & Edge Cases
- **Auth Failure on NotebookLM**: If `notebook_list` or `source_add` returns an authentication error, output a helpful instruction pointing the user to run `nlm login` in the terminal, or fall back to local display while alerting the user.
- **Empty Retrieval**: If both Context7 and web search return minimal data, prompt the user with clarifying terms rather than creating an empty notebook.
- **Rate Limits / Quotas**: Cap retrieved documents at 3-5 high-value sources per research run to prevent context exhaustion.
