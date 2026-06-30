# Codex Memory Routing Index

This is the checked-in routing index for project workflow memory. It is not
Codex's generated user-memory store. Codex agents must read this file before
case work, workflow/tooling changes, or tasks that may touch CFD process.

Use this file to decide which detailed memories to read. Keep entries short,
trigger-oriented, and cheap to scan. Do not paste full workflow bodies here.

## How To Use

1. Identify the current task's nouns, files, and workflow stage.
2. Scan `Always Recall` first.
3. Scan `Triggered Recall` for matching triggers.
4. Read every referenced memory file whose trigger matches.
5. If no trigger matches, proceed and record new discovery only if the task
   reveals a distinct reusable pattern, guard, or candidate workflow.

## Entry Format

Use one line per memory:

```text
- triggers: <comma-separated trigger words> | category: <case|guard|candidate-workflow> | file: <relative path> | recall: <why this matters>
```

Detailed memory files should use frontmatter like this:

```yaml
---
category: guard
triggers: [mesh, boundary, output]
status: active
cases: []
---
```

## Always Recall

No always-recall memories have been recorded yet.

## Triggered Recall

No triggered memories have been recorded yet.

## Candidate Workflow Counters

No candidate workflows have been recorded yet.

## Retired Memories

No memories have been retired yet.
