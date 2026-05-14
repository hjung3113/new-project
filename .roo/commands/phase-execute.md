---
description: Route approved phase execute work to the owning implementation mode
argument-hint: <approved plan_id and implementation task>
mode: orchestrator
---

Use the `workflow-phase-gate` skill for $ARGUMENTS.

Apply `.roo/rules-orchestrator/rules.md` and `.roo/rules/phase-gate.md` first.

Use `/phase-execute` only when `.scratch/phase-state.json` is already `phase=execute`, `approved=true`, and points to the same `plan_id`.

The orchestrator must not implement inline. It must verify the execute gate, choose the narrowest owning mode, create the required handoff packet from `.roo/rules-orchestrator/rules.md`, and stop if `new_task` is unavailable.

Do not restate or weaken `--chain` safety rules here. The canonical conditions are the `workflow-phase-gate` Automation Flags and Stop Conditions.
