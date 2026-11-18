---
name: research
description: "Autonomous technical research using Context7 for authoritative documentation and Google NotebookLM for persistent notebook creation and source ingestion"
---

# Workflow: /research

This workflow activates the `research` skill to conduct grounded technical investigation on any library, API, algorithm, or architecture requested by the user.

---

## Step 1: Parse Research Subject
Read the user's prompt following `/research <topic>` or extract the technical question they want researched.
If no topic was provided, prompt the user:
> *"What technology, library, algorithm, or architectural topic would you like to research?"*

## Step 2: Activate the Research Skill
Load and follow all instructions in:
- `.agents/skills/research/SKILL.md`
- `.agents/skills/research/references/retrieval-protocol.md`

## Step 3: Execute Discovery, Retrieval & Storage
1. **Discover or Create Notebook**: Search existing notebooks via `notebook_list` (`nlm list notebooks`). If no matching notebook exists, create one via `notebook_create` (`Research: <Topic>`) and set a clean alias (`alias`).
2. **Retrieve Documentation**:
   - For libraries/APIs: Use Context7 (`resolve-library-id` → `query-docs`).
   - For concepts/algorithms: Fallback to web search (`search_web`).
3. **Ingest & Synthesize**:
   - Ingest reference URLs/texts into the notebook via `source_add`.
   - Author a structured synthesis note via `note(action="create")`.
4. **Verify & Respond**:
   - Run a validation `notebook_query`.
   - Deliver the synthesized executive summary, technical specifications, code snippets, and notebook reference links to the user.
