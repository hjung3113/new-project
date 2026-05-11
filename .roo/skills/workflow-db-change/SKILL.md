---
name: workflow-db-change
trigger: Use when the user asks for MSSQL schema, EF Core migration, query, index, transaction, or bulk-write changes, or invokes /db.
description: Runs the MSSQL database change workflow for schema, EF Core migrations, Dapper read-query exceptions, indexes, transactions, and bulk writes. Use for database changes or when the user invokes /db; route read-only SQL review to /review.
---

# Workflow: DB Change

## Steps

1. State intent.
   - Run `workflow-phase-gate` first. Stop before implementation unless phase state is `execute`, `approved=true`, and tied to the approved `plan_id`.
   - Identify the data model, table, query, migration, or writer behavior being changed.
   - Identify volume, concurrency, and reprocess expectations.
   - Stop if the request is only a review; route to `review`.

2. Design the database change.
   - Use EF Core migrations for schema and normal persistence changes.
   - Use Dapper only for documented complex or performance-sensitive read-query exceptions where EF Core is not the right fit.
   - Do not use Dapper for write paths without documented reviewer approval.
   - Plan indexes around filters, joins, merge keys, uniqueness, foreign keys, retention, and reprocess paths.
   - Define transaction, idempotency, and rollback expectations before writing code.
   - Define staging and MERGE semantics for bulk writes before implementation.

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
