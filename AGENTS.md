# AGENTS.md

This file provides guidance to Codex when working in this repository.

## Workflow Discovery

This repo should be treated as both a working case repository and a place to
discover repeatable CFD workflows. The goal is not to prebuild a large framework
up front. Instead, build cases normally, notice which steps recur, and promote
only the parts that prove reusable.

Harvest repeatability at two levels:

- Whole-case procedures, such as a convergence study, parameter sweep, or
  benchmark validation.
- Sub-case steps that recur inside otherwise different cases, such as meshing,
  boundary-condition wiring, output parsing, error norms, convergence gates,
  post-processing, warm starts, and report generation.

Industrial cases often do not share a whole-case shape, so durable reuse is
usually found in sub-case steps. Treat those sub-steps as first-class workflow
candidates rather than incidental helper code.


## Mandatory Recall

For any case work, workflow/tooling change, or task that may touch CFD process,
read `.codex/memory/MEMORY.md` before planning or editing. Treat it as the
routing index for checked-in project memory. Follow every matching trigger in
the index and read the referenced memory files before re-deriving a procedure.

If the task is clearly unrelated to CFD workflow discovery, no memory lookup is
required. If you skip the lookup for that reason, say so briefly.

High-risk guards that must never be missed should also be duplicated here in
`AGENTS.md` as one-line rules, with the full rationale kept in `.codex/memory/`.

High-risk guard: Long CFD solver runs started by Codex require an active
blocking wait or bounded polling loop; monitor/status files alone do not wake
Codex.
High-risk guard: Before starting an OpenFOAM MPI job, check outside the sandbox
for existing solver processes when possible; sandboxed process checks can miss
live jobs.

## Codex Setup Layout

Use the Codex-facing setup under `.codex/` for workflow discovery artifacts:

```text
.codex/memory/   Git-tracked discovery memory: guards, lessons, per-case notes,
                 and candidate workflow records. MEMORY.md is the index.
.codex/skills/   Human-readable promoted workflow records, if useful.
.codex/agents/   Promoted delegable sub-steps with crisp input/output contracts.
.codex/evals/    Evaluation buffers for promoted units as they evolve.
.agents/skills/  Codex-discoverable repo skills. Each skill needs SKILL.md.
tmp/             Local scratch output. Keep generated scratch out of the repo root.
```

Keep this setup focused on discovery instructions. Do not copy discovered
workflows, case-specific facts, solver-specific notes, or harvested inventories
from another repository unless they are independently true for this one.

## Working Conventions

- Write scratch outputs to local `tmp/` when possible, not the repo root or
  `$HOME`.
- Before adding new tooling, read the existing repository structure and reuse
  local conventions.
- Keep generated artifacts out of source control unless the repository already
  establishes that they are checked in.
- Commit or push only when explicitly asked.
- When working in a dirty tree, preserve user changes and avoid unrelated
  cleanup.

## Discovery Process

After each meaningful case or workflow task, record only the discovery value:

- A per-case summary belongs in `.codex/memory/` with `category: case`.
- A distinct lesson or guard belongs in `.codex/memory/` with
  `category: guard`.
- A recurring step that is not yet promoted belongs in `.codex/memory/` with
  `category: candidate-workflow` and a list of cases where it appeared.
- A proposed change to an already-promoted skill or agent belongs in that unit's
  `.codex/evals/<unit>.md` buffer until another case reconfirms it.

Use the rule of three: promote a candidate workflow only after it appears in
three separate cases or tasks. Promotion can mean a `.codex/skills/` workflow record, a
Codex-discoverable `.agents/skills/` skill, a `.codex/agents/` agent, or
reusable project code. Mostly mechanical behavior is usually better as code with
a clear API than as a prose workflow.

On promotion:

- Create or update the skill, agent, or reusable code.
- Create `.codex/evals/<unit>.md` for future evolution notes.
- Retire the candidate-workflow memory after carrying its useful history into
  the promoted unit or its eval buffer.

## Granularity Rules

Promote the smallest unit that is actually reusable:

- Orchestrator workflows that compose several sub-steps belong in
  `.agents/skills/` when they should be invokable by Codex, with any supporting
  notes mirrored in `.codex/skills/` only if useful.
- Isolated, delegable sub-steps that are complex, high-variance, or produce a
  lot of output belong in `.codex/agents/`.
- Decision rules, contracts, and lessons worth auto-recall belong in
  `.codex/memory/`.
- Purely mechanical reusable behavior belongs in project code with a clear
  interface.

Each promoted unit should be subagent-consumable: explicit inputs, explicit
outputs, no hidden reliance on conversation state, and a clear pass/fail or
completion signal.

## Reuse Discipline

Before hand-rolling a procedure, check whether a matching local skill, agent, or
project helper already exists. Use promoted workflows aggressively; they are only
validated by being applied to later work. If a new case extends a promoted unit,
use the existing unit as the scaffold and record the delta in its eval buffer
until the change is reconfirmed.

Avoid promoting one-off observations. A single-case insight can be recorded as a
candidate or eval note, but it should not become canonical until repeated use
shows that it belongs.
