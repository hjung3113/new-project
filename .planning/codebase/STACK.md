# STACK - Roo Harness Template

**Analysis date:** 2026-05-11

## Runtime

- Roo Code workspace with project-local modes in `.roomodes`.
- Roo rules, commands, and workflow skills under `.roo/`.
- Durable planning memory under `.planning/`.
- Live phase-gate state under `.scratch/phase-state.json`.

## Target Project Defaults

This repository is a harness template, not an application. Its defaults are for target projects that adopt it:

- C# on .NET 10.
- Microsoft SQL Server.
- EF Core as the default data access path.
- Dapper only for documented complex or performance-sensitive read-query exceptions.
- xUnit, FluentAssertions, and NSubstitute.
- `testcontainers-dotnet` with real MSSQL containers for SQL, migrations, EF Core queries, Dapper queries, writers, restart safety, idempotency, and transaction behavior.
- Pipeline-first Clean Architecture for ETL workflows.

## Local Tooling

- JSON validation target: `.scratch/phase-state.schema.json`.
- JSON examples: `.scratch/phase-state.example.json` and live `.scratch/phase-state.json`.
- Mode validation: `.roomodes` is JSON and should be checked with `jq . .roomodes`.
- Future mechanical enforcement belongs to Phase 2 in `.planning/ROADMAP.md`.

## Non-Goals

- No target app source is owned by this repository.
- No parser, writer, database schema, or sample domain implementation should be added unless a later phase explicitly adopts an example slice.
