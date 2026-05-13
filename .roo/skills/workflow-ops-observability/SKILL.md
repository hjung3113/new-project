---
name: workflow-ops-observability
trigger: Use when the user asks for logging, metrics, processing events, retry boundaries, worker polling, graceful shutdown, dashboards, runbooks, or invokes /ops.
description: Runs the operations and observability workflow with phase-gate and TDD evidence for operational implementation.
---

# Workflow: Ops Observability


## Execution Model

When invoked from `orchestrator`, do not execute this workflow inline.

The orchestrator must create a focused subtask in the owning mode and pass the required handoff packet from `.roo/rules-orchestrator/rules.md`.

The owning mode must reload durable context from `.planning/` and `.scratch/phase-state.json`, perform only its owned work, and return the required structured result.

If the task cannot proceed because planning context is missing, stale, placeholder-only, or outside the approved phase gate, return `needs-plan` instead of guessing.

## Steps

1. Check phase gate.
   - Run `workflow-phase-gate` first.
   - Stop before implementation unless phase state is `execute`, `approved=true`, and tied to the approved `plan_id`.
   - Confirm requested edits are inside approved `allowed_paths`.

2. Classify operational behavior.
   - Identify whether the request changes structured logs, metrics, processing events, retry boundaries, worker polling, graceful shutdown, dashboards, or runbooks.
   - Route parser/state/schema/write mechanics back to `/etl` or `/db` when operations is not the primary owner.

3. Define observable contract.
   - Name stable log fields, metric names, event types, retry ownership, cancellation behavior, and failure visibility.
   - Define bounded queue, bounded retry, backlog, throughput, latency, and failure signals where relevant.

4. Red.
   - Write or identify the failing xUnit test first.
   - Record red evidence: command, failing test name, and failure reason.
   - Use `testcontainers-dotnet` with real MSSQL containers when processing events, retries, restart behavior, idempotency, or transaction behavior touches persistence.
   - Stop if no red evidence exists; there is no "tests later" path for operational behavior changes.

5. Green.
   - Implement the smallest change that satisfies the observable contract.
   - Preserve cancellation, bounded concurrency, and graceful shutdown behavior.
   - Do not hide failures with silent catches or unstructured logs.

6. Refactor and verify.
   - Refactor only after green evidence.
   - Run focused operational tests and any impacted integration tests.
   - Report changed paths, red evidence, green evidence, operational signals, and residual risks.

## Hard Rules

- No implementation before phase gate approval.
- No operational behavior change without red evidence.
- No unbounded queues, unbounded retries, silent drops, or swallowed exceptions.
- No persistence behavior proof using mocks, EF InMemory, or SQLite.
