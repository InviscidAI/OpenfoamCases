---
category: guard
triggers: [long-run, overnight, solver, OpenFOAM, polling, monitor, blocking-wait]
status: active
cases: [cases/cylinderRe3900_LES]
---

# Long Run Blocking Wait Guard

For long CFD solver processes started by Codex, do not only launch and return.
Use a blocking wait or bounded polling loop in the active turn, with an explicit
timeout appropriate to the requested investigation window.

Minimum expectations:

- Run a foreground or managed solver process when practical.
- Poll logs/status during the active turn until completion, timeout, or failure.
- If a process must continue beyond the active turn, leave a monitor/status file
  and state clearly that it will not wake Codex by itself.
- For tuning loops, use bounded waits such as `timeout 10m ...` and inspect the
  result before launching longer runs.
- Before launching an OpenFOAM MPI job in this sandboxed Codex environment,
  check for existing `mpirun`/solver processes outside the sandbox when possible;
  sandboxed `pgrep` can miss already-running jobs and a duplicate run can write
  the same case concurrently.
