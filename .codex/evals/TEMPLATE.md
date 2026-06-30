# <Unit Name> Eval Buffer

## Unit

Path: `<skill-or-agent-path>`

## Candidate Changes

Use one entry per single-case observation. Fold the change into the unit only
after another case reconfirms it.

```text
- case: <case-or-task>
  observation: <what changed or failed>
  proposed_delta: <specific edit to the unit>
  reconfirm_when: <what a second case must show>
  status: pending | folded | rejected
```
