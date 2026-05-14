---
description: Route one full phase lifecycle through the canonical phase gate
argument-hint: <phase number or phase slug> [--chain]
mode: orchestrator
---

Use the `workflow-phase-gate` skill for $ARGUMENTS.

Apply `.roo/rules-orchestrator/rules.md` and `.roo/rules/phase-gate.md` first.

`/fsd-phase` is the recommended one-command entry point for phase workflows, but it must stay subtask-first:

1. Route the phase-local `discuss` pass to the owning planning mode.
2. Route the phase `plan` work to the owning planning mode so it records `plan_id`, `allowed_paths`, acceptance criteria, and `verification`.
3. Enter `execute` only through the canonical `workflow-phase-gate` chain checks and then create the owning implementation-mode handoff; the orchestrator does not implement inline.

Usage examples:

- `/fsd-phase 1 --chain`
- `/fsd-phase 03-harness-distribution-enforcement --chain`

Do not restate or weaken `--chain` safety rules here. The canonical conditions are the `workflow-phase-gate` Automation Flags and Stop Conditions. If any required condition fails, stop before execute and request approval/state correction instead of forcing implementation.
