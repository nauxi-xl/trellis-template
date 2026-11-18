# Implementation Plan: `/research` Skill

## Ordered Checklist

- [x] **Phase 1: Skill Authoring**
  - [x] 1.1 Create `.agents/skills/research/SKILL.md` with:
    - YAML frontmatter: `name: research`, descriptive summary
    - Activation guidelines & user scenarios
    - Step-by-step execution protocol:
      - Step 1: Query analysis & scope isolation
      - Step 2: Notebook discovery & auto-creation logic
      - Step 3: Hybrid retrieval (Context7 primary + Web search fallback)
      - Step 4: NotebookLM source ingestion (`source_add`) and synthesis note authoring (`note`)
      - Step 5: Verification & user report formatting
  - [x] 1.2 Create reference guide `.agents/skills/research/references/retrieval-protocol.md` with detailed tool call examples (`gemini-notebook-mcp` tools and `context7` tools).

- [x] **Phase 2: Workflow & Command Integration**
  - [x] 2.1 Create `.agents/workflows/research.md` defining the `/research` slash command workflow.
  - [x] 2.2 Wire platform-specific commands:
    - `.claude/commands/trellis/research.md` (or relevant Claude command entrypoint)
    - Mirror to `.claude/skills/research/SKILL.md`
    - Mirror to `.github/skills/research/SKILL.md`

- [x] **Phase 3: Documentation & Knowledge Graph Update**
  - [x] 3.1 Update [AGENTS.md](file:///home/nauxi/projects/trellis-template/AGENTS.md) to document `/research` alongside SDLC discovery and NotebookLM rules.
  - [x] 3.2 Update [CLAUDE.md](file:///home/nauxi/projects/trellis-template/CLAUDE.md) to list the `/research` command and skill.
  - [x] 3.3 Update [.trellis/spec/guides/notebooklm-knowledge-base.md](file:///home/nauxi/projects/trellis-template/.trellis/spec/guides/notebooklm-knowledge-base.md) to mention the automated `/research` skill pattern.

- [x] **Phase 4: Verification & Quality Gate**
  - [x] 4.1 Validate skill markdown formatting, links, and YAML frontmatter.
  - [x] 4.2 Run `trellis-check` / validation scripts to ensure git cleanliness and spec compliance.
  - [x] 4.3 Update code graph with `graphify update .` to reflect the new skill nodes.

## Validation Commands

```bash
# 1. Verify files exist and YAML frontmatter is valid
head -n 10 .agents/skills/research/SKILL.md
head -n 10 .agents/workflows/research.md

# 2. Check platform mirrors
diff -u .agents/skills/research/SKILL.md .claude/skills/research/SKILL.md
diff -u .agents/skills/research/SKILL.md .github/skills/research/SKILL.md

# 3. Verify git status
git status --short

# 4. Update knowledge graph
graphify update .
```

## Risky Files & Rollback Points
- Changes are purely additive to `.agents/skills/research/`, `.agents/workflows/research.md`, platform skill mirrors, and documentation references in `AGENTS.md` and `CLAUDE.md`.
- Rollback: `git checkout -- AGENTS.md CLAUDE.md .trellis/spec/guides/notebooklm-knowledge-base.md && rm -rf .agents/skills/research .agents/workflows/research.md .claude/skills/research .github/skills/research`.
