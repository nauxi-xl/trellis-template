---
name: trellis-finish-work
description: "Wrap up the current session: archive the active task (and any completed-but-unarchived tasks) and record the session journal. Run after committing code in workflow Phase 3.4."
---

# Finish Work

Wrap up the current session: archive the active task (and any other completed-but-unarchived tasks the user wants to clean up) and record the session journal. Code commits are NOT done here — those happen in workflow Phase 3.4 before you invoke this command.

## Step 1: Survey Current State

```bash
python3 ./.trellis/scripts/get_context.py --mode record
```

This prints:
- **My active tasks** — review whether any besides the current one are actually done and should be archived.
- **Git status** — quick visual on dirty paths.
- **Recent commits** — commit hashes for Step 4.

If other completed tasks surface, ask the user once: "These N tasks look done — archive them too? [y/N]".

## Step 2: Sanity Check — Classify Dirty Paths

Run:

```bash
git status --porcelain
```

Filter out paths under `.trellis/workspace/` and `.trellis/tasks/` (managed automatically).

For each remaining dirty path:
- Paths referenced in the current task's artifacts (`prd.md`, `implement.jsonl`, `check.jsonl`) → current task
- If uncommitted code from current task exists, bail out and ask user/AI to return to Phase 3.4 to commit them first.
- If paths belong to unrelated work, report them and continue to Step 3.

## Step 3: Archive Task(s)

```bash
python3 ./.trellis/scripts/task.py archive <task-name>
```

At minimum: the current active task (if any). Plus any extra tasks confirmed in Step 1.

## Step 4: Record Session Journal

```bash
python3 ./.trellis/scripts/add_session.py \
  --title "Session Title" \
  --commit "hash1,hash2" \
  --summary "Brief summary"
```

Use the work-commit hashes produced in Phase 3.4. This produces a `chore: record journal` commit.
