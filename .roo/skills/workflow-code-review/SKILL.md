---
name: workflow-code-review
trigger: Use when the user asks for a review, PR review, risk scan, or invokes /review.
description: Runs the review workflow for C#/.NET, async, SQL, ETL correctness, tests, performance, and operations risks. Use for reviews or when the user invokes /review.
---

# Workflow: Code Review

## Steps

1. Identify review scope.
   - Read changed files, tests, and relevant docs.
   - Determine whether the change touches C#, ETL, MSSQL, operations, or docs.
   - Stop if the user actually wants implementation instead of review.

2. Review correctness.
   - Check behavior, edge cases, cancellation, concurrency, idempotency, restart safety, and source traceability.
   - For ETL changes, verify the canonical flow: source -> parse -> normalize -> state -> merge -> buffer -> write -> observe.
   - Check backpressure, bounded buffers, duplicate handling, replay behavior, and failure visibility.

3. Review SQL and persistence.
   - Check EF Core usage by default and Dapper only for documented complex or performance-sensitive read-query exceptions.
   - Check parameterized SQL, injection risk, bulk write safety, staging tables, indexes, transactions, MERGE semantics, and non-sargable predicates.
   - Check SqlBulkCopy into staging plus set-based MERGE/upsert for high-volume ETL writes.
   - Flag row-by-row ETL writes unless there is a documented reviewer-approved exception with volume limits and rationale.

4. Review tests.
   - Check for missing red evidence before production edits, missing green evidence after implementation, weak assertions, excessive mocks, and refactor-before-green work.
   - Confirm xUnit + FluentAssertions usage is clear and NSubstitute is not replacing required integration coverage.
   - Confirm `testcontainers-dotnet` with real MSSQL containers covers SQL, EF Core query, Dapper query, migration, writer, restart-safety, idempotency, and transaction behavior.
   - Treat mocks, in-memory providers, SQLite, or unit-only tests as insufficient proof for MSSQL behavior.

5. Review operations.
   - Check logs, metrics, processing events, retry boundaries, and shutdown behavior.

6. Report findings.
   - Lead with findings ordered by severity.
   - Include file/line references when possible.
   - Keep summary secondary.

## Routing

- Primary owner: `review`.
- Route implementation requests discovered during review to the correct implementation workflow instead of fixing them inside the review.

## Hard Rules

- Do not rewrite code unless explicitly asked.
- If no findings exist, state residual risks and test gaps.
- Do not expand the task into feature implementation or sample project construction.
