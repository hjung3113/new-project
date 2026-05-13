---
name: workflow-etl-pipeline
trigger: Use when the user asks for parser, normalization, state machine, merge semantics, buffering, backpressure, restart-safety, or ETL write orchestration, or invokes /etl. Route SQL/schema writer mechanics to /db.
description: Runs the ETL pipeline workflow for source, parse, normalize, state, merge, buffer, write orchestration, observe, and restart-safety work. Use for ETL internals or when the user invokes /etl.
---

# Workflow: ETL Pipeline


## Execution Model

When invoked from `orchestrator`, do not execute this workflow inline.

The orchestrator must create a focused subtask in the owning mode and pass the required handoff packet from `.roo/rules-orchestrator/rules.md`.

The owning mode must reload durable context from `.planning/` and `.scratch/phase-state.json`, perform only its owned work, and return the required structured result.

If the task cannot proceed because planning context is missing, stale, placeholder-only, or outside the approved phase gate, return `needs-plan` instead of guessing.

## DB Context Snapshot

When the task depends on actual output tables, staging tables, merge keys, indexes, stored procedures, functions, SQL Agent jobs, writer behavior, idempotency, replay, reprocess, or restart-safety, read `.db-context/latest.json` before making conclusions.

Use `.db-context/routines.index.json` to locate writer-facing stored procedures, functions, and views. Use `.db-context/routines.sql` for exact SQL control-flow review. Use `.db-context/jobs.md` if ETL execution depends on SQL Agent jobs or schedules.

Do not connect to the database by default. If `.db-context/` exists, use it as the source of truth. Only run `python scripts/db_context_snapshot.py --refresh` when the user explicitly asks to refresh DB context.

If DB context is required but missing, stale, or insufficient, return `needs-db-context` instead of guessing or refreshing automatically.

The expected database model is one master database and many process databases. Process databases are expected to share the same schema shape; check `process_database_comparison` before assuming a process DB schema is representative.

## Steps

1. Define the data contract.
   - Run `workflow-phase-gate` first. Stop before implementation unless phase state is `execute`, `approved=true`, and tied to the approved `plan_id`.
   - Identify source format, normalized record, output table/model, and traceability fields.
   - Read process DB schema context when output table/model or writer assumptions depend on actual DB shape.
   - Include source traceability fields in the contract: source file, source line or offset, source record id when available, equipment/job identifiers, and processing stage.
   - Keep core pipeline records strongly typed.
   - Stop if the request is only architectural planning; route to `architecture-decision`.

2. Map pipeline stages.
   - Write the stage list in this exact canonical order: source -> parse -> normalize -> state -> merge -> buffer -> write -> observe.
   - Mark exactly which stage changes in this task.
   - Do not skip, rename, or reorder stages without documenting the reason and updating tests.

3. Decide ordering and state.
   - Specify lookahead, TTL, matching keys, state transitions, and restart behavior.
   - Make idempotency, duplicate handling, replay, and reprocess behavior explicit.
   - Cross-check matching keys, uniqueness, staging, and writer assumptions against `.db-context/` when available.
   - Define backpressure behavior before implementation: bounded buffers, flush size, flush interval, cancellation, retry boundaries, and failure visibility.
   - Define failure visibility and replay expectations before implementation.

4. Test first.
   - Run red tests before production edits and record the failing command, test name, and failure reason.
   - Add xUnit + FluentAssertions unit tests for pure parse, normalize, state, and merge behavior.
   - Add `testcontainers-dotnet` integration tests with real MSSQL containers for writer, schema, SQL, restart, idempotency, transaction, and migration behavior.
   - Use NSubstitute only for external collaborators that are not part of the ETL correctness path.
   - Do not use mocks, in-memory providers, or SQLite as proof for MSSQL behavior.
   - Stop if no red evidence exists; there is no "tests later" path for ETL behavior changes.

5. Implement.
   - Keep pipeline code in `etl-pipeline` ownership.
   - Hand off schema, index, and writer SQL changes to `db-migration`.
   - Hand off logs, metrics, retry, shutdown, and processing-event work to `ops-observability`.
   - Preserve deterministic stage order and explicit state transitions.
   - Use SqlBulkCopy into staging plus set-based MERGE/upsert for batch writes.
   - Keep write paths idempotent, restart-safe, and traceable to source records.

6. Review.
   - Check throughput, memory bounds, backpressure, cancellation, idempotency, duplicate handling, restart safety, source traceability, and failure visibility.
   - Check red evidence, green evidence, and refactor-after-green discipline.
   - Check process DB fingerprint/drift results before assuming all process DBs match the reference schema.
   - Run focused unit and integration tests for every changed stage.

## Hard Rules

- No row-by-row ETL writes by default.
- Row-by-row ETL writes require a documented reviewer-approved exception with volume limits, rationale, failure handling, and a follow-up plan.
- No hidden global state for processing context.
- No swallowed parse, normalize, state, merge, buffer, write, or observe errors without traceable diagnostics.
- No production edits before red evidence and no refactor before green evidence.
- Do not implement sample or unrelated domain features while running this workflow.
- Stop with `needs-db-context` when real DB shape is necessary but `.db-context/` is missing, stale, or insufficient.
