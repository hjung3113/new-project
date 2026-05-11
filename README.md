# Roo C# ETL Orchestration Template

Clone this repository to start a Roo Code workspace for C#/.NET 10 ETL projects backed by MSSQL.

This repository configures Roo modes, rules, workflow skills, and slash commands. It is not an implementation of NewParser or any other domain project.

## Planning State

Fresh sessions start at [.planning/STATE.md](.planning/STATE.md). Then read [.planning/ROADMAP.md](.planning/ROADMAP.md), the active phase checkpoint file, and finally [.scratch/phase-state.json](.scratch/phase-state.json) for the live gate state.

The `.planning/` tree is durable project memory. The `.scratch/phase-state.json` file controls whether the current work is in `discuss`, `plan`, `execute`, or `done`.

## Primary Entry Points

- `/feature` - feature work through TDD
- `/bugfix` - root-cause bug diagnosis and regression fix
- `/etl` - ETL pipeline internals
- `/db` - MSSQL schema, migration, query, index, and bulk-write changes
- `/ops` - logging, metrics, processing events, retry boundaries, worker lifecycle, and shutdown
- `/adr` - architecture decisions and ADRs
- `/review` - code, SQL, ETL, test, and operations review
- `/issues` - turn docs or plans into PRDs and issue slices

## Phase Gate Harness

Use `workflow-phase-gate` when work must move through `discuss -> plan -> execute -> done`.

- `discuss` is read-only discovery.
- `plan` is docs, ADR, PRD, checklist, or issue-plan work only.
- `execute` requires `phase=execute`, `approved=true`, and an approved `plan_id`.
- `done` records the final rationale and verification.

See [docs/phase-gate-harness.md](docs/phase-gate-harness.md), [.roo/rules/phase-gate.md](.roo/rules/phase-gate.md), and [.scratch/phase-state.example.json](.scratch/phase-state.example.json).

## Defaults

- C# on .NET 10
- MSSQL
- Pipeline-first Clean Architecture
- EF Core by default; Dapper only for documented complex or performance-sensitive read-query exceptions
- xUnit, FluentAssertions, NSubstitute
- testcontainers-dotnet with real MSSQL containers for SQL, migrations, EF Core queries, Dapper queries, writers, restart safety, idempotency, and transactions

See [docs/roo-orchestration-design.md](docs/roo-orchestration-design.md) and [.roo/README.md](.roo/README.md).
