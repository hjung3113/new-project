---
name: workflow-db-change
trigger: Use when the user asks for MSSQL schema, EF Core migration, query, index, transaction, or bulk-write changes, or invokes /db.
description: Runs the MSSQL database change workflow for schema, EF Core migrations, Dapper read-query exceptions, indexes, transactions, and bulk writes. Use for database changes or when the user invokes /db; route read-only SQL review to /review.
---

# Workflow: DB Change


## Execution Model

When invoked from `orchestrator`, do not execute this workflow inline.

The orchestrator must create a focused subtask in the owning mode and pass the required handoff packet from `.roo/rules-orchestrator/rules.md`.

The owning mode must reload durable context from `.planning/` and `.scratch/phase-state.json`, perform only its owned work, and return the required structured result.

If the task cannot proceed because planning context is missing, stale, placeholder-only, or outside the approved phase gate, return `needs-plan` instead of guessing.

## DB Context Snapshot

When the task depends on actual MSSQL tables, columns, indexes, foreign keys, stored procedures, functions, views, triggers, SQL Agent jobs, MERGE keys, writer behavior, idempotency, or restart-safety, read `.db-context/latest.json` before making conclusions.

Use `.db-context/routines.index.json` to locate stored procedures, functions, and views. Use `.db-context/routines.sql` when exact SQL control flow, transaction boundaries, dynamic SQL, temp tables, cursor use, or MERGE semantics matter. Use `.db-context/jobs.md` when SQL Agent jobs or schedules may affect the change.

Do not connect to the database by default. If `.db-context/` exists, it is the source of truth for analysis. Only run `python scripts/db_context_snapshot.py --refresh` when the user explicitly asks to refresh DB context.

If DB context is required but missing, stale, or insufficient, return `needs-db-context` instead of guessing or refreshing automatically.

The expected database model is one master database and many process databases. Process databases are expected to share the same schema shape; check `process_database_comparison` before assuming a process DB schema is representative.

## Steps

1. State intent.
   - Run `workflow-phase-gate` first. Stop before implementation unless phase state is `execute`, `approved=true`, and tied to the approved `plan_id`.
   - Identify the data model, table, query, migration, or writer behavior being changed.
   - Read DB context snapshot files when real DB shape or routines matter.
   - Identify volume, concurrency, and reprocess expectations.
   - Stop if the request is only a review; route to `review`.

2. Design the database change.
   - Use EF Core migrations for schema and normal persistence changes.
   - Use Dapper only for documented complex or performance-sensitive read-query exceptions where EF Core is not the right fit.
   - Do not use Dapper for write paths without documented reviewer approval.
   - Plan indexes around filters, joins, merge keys, uniqueness, foreign keys, retention, and reprocess paths.
   - Define transaction, idempotency, and rollback expectations before writing code.
   - Define staging and MERGE semantics for bulk writes before implementation.
   - Cross-check planned table, index, SP, function, and job assumptions against `.db-context/` when available.

3. Test first.
   - Add xUnit coverage for behavior around the change and run it red before production edits.
   - Record red evidence: command, failing test name, and failure reason.
   - Add `testcontainers-dotnet` coverage with real MSSQL containers for SQL, migration, EF Core query, Dapper query, writer, restart-safety, idempotency, and transaction behavior.
   - Avoid mocked database tests, in-memory providers, and SQLite for persistence correctness.
   - Stop if no red evidence exists; there is no "tests later" path for database changes.

4. Implement safely.
   - Use parameterized SQL.
   - Do not concatenate dynamic values into SQL.
   - Use SqlBulkCopy to staging plus set-based MERGE/upsert for ETL writes.
   - Define transaction boundaries, isolation expectations, and retry behavior.
   - Keep ETL write paths set-based. Do not introduce row-by-row ETL persistence by default.
   - Row-by-row ETL writes require a documented reviewer-approved exception with expected volume, failure handling, and follow-up plan.

5. Review.
   - Check injection risk, locks, deadlocks, idempotency, restart safety, non-sargable predicates, missing indexes, staging correctness, MERGE safety, and rollback/recovery.
   - Check actual DB snapshot assumptions against the implementation when `.db-context/` is present.
   - Check red evidence, green evidence, and refactor-after-green discipline.
   - Run the focused tests and any impacted migration/query suites.

## Routing

- Use `db-migration` by default.
- Use `review` for read-only SQL review.
- Use `ops-observability` when the DB change affects retry or processing events.

## Stop Conditions

- Do not implement sample or domain features that are not required by the database change.
- Stop and split the work if the request also changes ETL stage logic or broad application behavior that should be owned elsewhere.
- Stop when a DB behavior change has no real MSSQL container coverage.
- Stop with `needs-db-context` when real DB shape is necessary but `.db-context/` is missing, stale, or insufficient.
