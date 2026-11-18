# Trellis Dynamic Context Guide

> Architecture and best practices for real-time, token-efficient dynamic context assembly across AI coding agents.

---

## Overview

Static context injection dumps entire files, directories, or historical logs regardless of what files are being touched. This wastes context window tokens and dilutes the model's attention on irrelevant constraints.

The **Dynamic Context Engine** (`python3 .trellis/scripts/dynamic_context.py`) dynamically computes the minimal, highly-relevant context envelope based on:
1. **Git & Worktree State**: Active branch, commit hash, isolated worktree path, and exact list of modified / staged files.
2. **Active Task**: Current task identity, PRD requirements, and implementation checklist.
3. **Just-In-Time Spec Resolution**: Scans touched file paths and automatically matches them to their governing layer specs (e.g. `frontend/` vs `backend/`), while omitting unrelated specs.
4. **LSP Health & Diagnostics**: Checks `agent-lsp` readiness and surfaces live compiler/type errors on modified files.
5. **Knowledge Graph Proximity**: Identifies affected modules in `graphify-out/graph.json` to preserve cross-file architectural invariants.

---

## Output Formats & Usage

The engine supports three output modes via `--format`:

### 1. Human-Readable (`--format text`)
For status lines, CLI diagnostics, and developer logs:
```bash
python3 .trellis/scripts/dynamic_context.py --format text
```

### 2. Machine-Readable (`--format json`)
For hooks, programmatic subagent dispatches, and tool chaining:
```bash
python3 .trellis/scripts/dynamic_context.py --format json
```

### 3. System Prompt Block (`--format prompt`)
Formatted Markdown surrounded by `<!-- TRELLIS_DYNAMIC_CONTEXT:START -->` delimiters, ready to be injected into system instructions:
```bash
python3 .trellis/scripts/dynamic_context.py --format prompt
```

---

## Integration with Lifecycle Hooks

- **Antigravity CLI**: Injected via `.agents/hooks/session-start.py` upon session startup, context clearing, or compaction.
- **Claude Code**: Injected via `.claude/hooks/session-start.py` and `inject-workflow-state.py`.
- **Sub-Agents**: Used by `inject-subagent-context.py` to bound child agent focus exclusively to relevant tasks and specs.
