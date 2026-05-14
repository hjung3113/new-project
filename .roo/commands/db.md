---
description: Run the MSSQL database change workflow
argument-hint: <schema, migration, query, or writer task>
mode: orchestrator
---

Use the `workflow-db-change` skill for $ARGUMENTS.

Apply `.roo/rules-orchestrator/rules.md` and `.roo/rules/phase-gate.md` first. Stay on `/db` only for MSSQL schema, EF migration, SQL implementation, indexing, transaction, Dapper read-query exceptions, `SqlBulkCopy`, staging, `MERGE`, or persistence migration work. Route read-only SQL review to `/review`.

DB context refresh, when explicitly requested by the user, uses `scripts/db_context_snapshot.py`. Connection/config options include `--config`, `--env-file`, `--master-connection`, `--master-label`, and repeated `--process-connection`. Snapshot options include `--snapshot-scope shape|selected|full`, `--include-tables`, `--include-procedures`, `--include-jobs`, `--collect-all-process-details`, and `--include-agent-jobs`.
