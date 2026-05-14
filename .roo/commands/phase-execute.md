---
description: Run phase execute only (approved plan required)
argument-hint: <approved plan_id and implementation task>
mode: orchestrator
---

Use the `workflow-phase-gate` skill for $ARGUMENTS.

Apply `.roo/rules-orchestrator/rules.md` and `.roo/rules/phase-gate.md` first. Use `/phase-execute` only when `.scratch/phase-state.json` is already `phase=execute`, `approved=true`, and points to the same `plan_id`.

This command is for manual step-by-step operation. With `--chain`, execute can be entered automatically only after discuss/plan artifacts and execute gate conditions are satisfied.
