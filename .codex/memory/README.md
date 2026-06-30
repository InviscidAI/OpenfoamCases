# Memory

Store Codex workflow-discovery memories here.

Memory should grow with distinct patterns and lessons, not with raw case count.
Do not copy discovered workflows from another repository into this one. Record a
memory only when the observation was encountered here or is independently true
for this repo.

This directory is checked-in project memory for workflow discovery. It is not
Codex's generated user memory store, which lives under the configured Codex home.

## Memory File Template

Use this shape for new memory files:

```markdown
---
category: guard | case | candidate-workflow
triggers: [short, trigger, words]
status: active | retired
cases: []
---

# Short Name

## Recall When

List the exact task cues that should cause an agent to read this memory.

## Rule Or Observation

State the reusable lesson, guard, or candidate workflow compactly.

## Evidence

Name the cases or tasks where this was encountered.

## Action

Say what Codex should do differently because this memory exists.
```

Every new memory must also add one routing line to `MEMORY.md`.
