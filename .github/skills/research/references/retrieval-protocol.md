# Research Retrieval & Storage Protocol Reference

This document provides exact tool calling patterns and examples for the `/research` skill across both MCP servers and CLI environments.

---

## 1. Context7 Retrieval Patterns

### Step 1.1: Resolve Library ID
```json
{
  "ServerName": "context7",
  "ToolName": "resolve-library-id",
  "Arguments": {
    "libraryName": "prisma",
    "query": "client extensions and accelerating queries"
  }
}
```
*Selection criteria*: Exact match on library name, high reputation, recent benchmark score.

### Step 1.2: Query Documentation
```json
{
  "ServerName": "context7",
  "ToolName": "query-docs",
  "Arguments": {
    "libraryId": "/prisma/prisma",
    "query": "client extensions $extends method syntax and examples"
  }
}
```

---

## 2. Gemini NotebookLM Storage Patterns

### Step 2.1: List & Match Notebooks
```json
{
  "ServerName": "gemini-notebook-mcp",
  "ToolName": "notebook_list",
  "Arguments": {}
}
```

### Step 2.2: Create Notebook (When No Match Exists)
```json
{
  "ServerName": "gemini-notebook-mcp",
  "ToolName": "notebook_create",
  "Arguments": {
    "title": "Research: Prisma Client Extensions"
  }
}
```

### Step 2.3: Set Friendly Alias
```json
{
  "ServerName": "gemini-notebook-mcp",
  "ToolName": "alias",
  "Arguments": {
    "action": "set",
    "alias": "res-prisma-ext",
    "notebook_id": "c7a8b9d0-1234-5678-abcd-ef0123456789"
  }
}
```

### Step 2.4: Ingest Sources
```json
{
  "ServerName": "gemini-notebook-mcp",
  "ToolName": "source_add",
  "Arguments": {
    "notebook_id": "res-prisma-ext",
    "source_type": "url",
    "url": "https://www.prisma.io/docs/concepts/components/prisma-client/client-extensions"
  }
}
```

### Step 2.5: Save Synthesis Note
```json
{
  "ServerName": "gemini-notebook-mcp",
  "ToolName": "note",
  "Arguments": {
    "notebook_id": "res-prisma-ext",
    "action": "create",
    "title": "Synthesis: Prisma Client Extensions",
    "content": "# Synthesis: Prisma Client Extensions\n\n## 1. Executive Summary\nPrisma client extensions allow custom methods..."
  }
}
```

---

## 3. Alternative CLI Workflows (`nlm`)

When operating in terminal environments without lazy MCP calling:

```bash
# 1. Discover notebooks
nlm list notebooks

# 2. Create if missing & alias
nlm notebook create "Research: WebGPU Pipeline"
nlm alias set res-webgpu <notebook-uuid>

# 3. Ingest reference URL
nlm source add res-webgpu --url "https://www.w3.org/TR/webgpu/"

# 4. Save synthesis note
nlm note create res-webgpu \
  --title "Synthesis: WebGPU Compute Pipeline" \
  --content "Findings and memory layouts..."

# 5. Query grounded notebook
nlm query res-webgpu "What are the workgroup memory limits in WebGPU compute shaders?"
```
