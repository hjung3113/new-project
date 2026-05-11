---
description: Run the MSSQL database change workflow
argument-hint: <schema, migration, query, or writer task>
mode: orchestrator
---

Use the `workflow-db-change` skill for $ARGUMENTS.

Apply `.roo/rules-orchestrator/rules.md` and `.roo/rules/phase-gate.md` first. Stay on `/db` only for MSSQL schema, EF migration, SQL implementation, indexing, transaction, Dapper read-query exceptions, `SqlBulkCopy`, staging, `MERGE`, or persistence migration work. Route read-only SQL review to `/review`.
