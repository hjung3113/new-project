---
description: Run the ETL pipeline workflow
argument-hint: <pipeline task, parser area, or design doc>
mode: orchestrator
---

Use the `workflow-etl-pipeline` skill for $ARGUMENTS.

Apply `.roo/rules-orchestrator/rules.md` and `.roo/rules/phase-gate.md` first. Stay on `/etl` only for parser, normalization, state, matching, merge/aggregate, buffering, write orchestration, replay, or restart-safety work. Route writer SQL, schema, indexes, `SqlBulkCopy`, staging, and `MERGE` mechanics to `/db`.
