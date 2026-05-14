---
description: Run phase plan only (docs and plan artifacts)
argument-hint: <approved discuss output or phase scope>
mode: architect
---

Use the `workflow-phase-gate` skill for $ARGUMENTS.

Apply `.roo/rules-orchestrator/rules.md` first. Use `/phase-plan` to produce or update the phase plan (`plan_id`, allowed paths, acceptance criteria, verification) and request execute approval. Do not implement behavior changes in this command.

Use this command for manual step-by-step operation. For one-pass automation, use `/fsd-phase <phase> --chain` or another phase-gated workflow command with `--chain`; canonical automation rules live in `workflow-phase-gate`.
