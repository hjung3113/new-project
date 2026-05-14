---
description: Run one full phase lifecycle with recommended defaults
argument-hint: <phase number or phase slug> [--chain]
mode: architect
---

Use the `workflow-phase-gate` skill for $ARGUMENTS.

Apply `.roo/rules-orchestrator/rules.md` and `.roo/rules/phase-gate.md` first.

`/fsd-phase` is the recommended one-command path for phase workflows.

Expected behavior:

1. Start with the phase-local `discuss` pass.
2. Build the phase `plan` with `plan_id`, `allowed_paths`, and `verification`.
3. Continue to `execute` in the same phase only when chain conditions are satisfied (`phase=execute`, `approved=true`, matching `plan_id`, and `automation_mode=chain`).

Usage examples:

- `/fsd-phase 1 --chain`
- `/fsd-phase 03-harness-distribution-enforcement --chain`

If chain safety conditions are not satisfied, stop after planning and request approval/state correction instead of forcing execute.
