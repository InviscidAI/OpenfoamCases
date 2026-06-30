---
name: workflow-discovery
description: Use when working on CFD cases or tooling in this repo to discover, record, and promote repeatable workflows without copying already-discovered workflows from another repository.
---

# Workflow Discovery

Use this skill when a task may reveal a repeatable workflow in this repository.
The goal is to harvest reusable patterns from actual work, not to prebuild
tooling speculatively.

## Inputs

- The current task or case being worked.
- Existing repo files and conventions.
- The workflow-discovery records in `.codex/memory/`, `.codex/skills/`,
  `.codex/agents/`, and `.codex/evals/`.

## Process

1. Read `AGENTS.md` and `.codex/memory/MEMORY.md` before planning or editing.
2. Scan `Always Recall` and `Triggered Recall`; read every memory whose triggers match the task.
3. Check whether an existing local helper, skill, agent record, or memory applies.
4. Do the task using current repo conventions.
5. Notice repeatable units at both whole-case and sub-case granularity.
6. Record only discovery value:
   - per-case summary: `.codex/memory/` with `category: case`
   - lesson or guard: `.codex/memory/` with `category: guard`
   - unpromoted recurring step: `.codex/memory/` with
     `category: candidate-workflow`
   - proposed update to a promoted unit: `.codex/evals/<unit>.md`
7. Add or update the routing line in `.codex/memory/MEMORY.md` for every memory change.
8. Promote only after the rule of three is met.

## Promotion Rules

Promote the smallest unit that is actually reusable.

- Orchestrator procedure: create a Codex-discoverable skill under
  `.agents/skills/<name>/SKILL.md`.
- Delegable sub-step: create or update a record under `.codex/agents/`.
- Decision rule or lesson: keep it in `.codex/memory/`.
- Mechanical reusable behavior: put it in project code with a clear interface.

When promoting a unit, create `.codex/evals/<unit>.md` for future evolution
notes and retire the candidate-workflow memory after preserving useful history.

## Output

Return the task result and, when relevant, name the workflow-discovery records
that were added or updated.
