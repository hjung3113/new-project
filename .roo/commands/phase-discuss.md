---
description: Run phase discuss only (read-only)
argument-hint: <phase goal, blocker, or decision scope>
mode: architect
---

Use the `workflow-phase-gate` skill for $ARGUMENTS.

Apply `.roo/rules-orchestrator/rules.md` first. Use `/phase-discuss` for phase-local discovery only: clarify goals, define non-goals, capture repo-derived answers, and list user-preference questions before any plan is drafted.

Use this command for manual step-by-step operation. If you want one-pass automation, use a normal workflow command with `--chain` so discuss -> plan -> execute can continue automatically when gate conditions are met.
