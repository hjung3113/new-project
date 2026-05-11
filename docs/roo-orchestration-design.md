# Roo Orchestration Design

This repository is a cloneable Roo Code template for low-reasoning in-house models working on C#/.NET 10 ETL systems backed by MSSQL.

It does not implement a parser or domain system. It defines modes, rules, slash commands, and workflow skills that make agents choose stable workflows instead of improvising from a large skill list.

## Fixed Stack

- Runtime: C# on .NET 10.
- Database: Microsoft SQL Server.
- Data access: EF Core by default; Dapper only for documented complex or performance-sensitive read-query exceptions.
- Tests: xUnit, FluentAssertions, NSubstitute.
- Database tests: `testcontainers-dotnet` with real MSSQL containers for SQL, migration, EF Core query, Dapper query, writer, restart-safety, idempotency, and transaction behavior.
- Mocked repositories, in-memory providers, and SQLite are not acceptable proof for MSSQL behavior.
- Architecture style: pipeline-first Clean Architecture.

## Modes

| Mode | Purpose | Writes Code |
| --- | --- | --- |
| `orchestrator` | Classify requests, choose workflow, delegate steps, verify completion | No |
| `architect` | Architecture decisions, ADRs, boundaries, state models, plans | Docs only |
| `tdd-code` | C# implementation through red-green-refactor | Yes |
| `etl-pipeline` | Parser, normalization, state machine, merge, buffering, bulk flush logic | Yes |
| `db-migration` | MSSQL schema, migration, indexing, bulk write, and query implementation | Yes |
| `diagnose` | Reproduce, minimize, hypothesize, instrument, root-cause, regression test | Yes |
| `review` | Code, SQL, tests, performance, reliability, operations review | No by default |
| `docs-issues` | PRD, issue breakdown, docs sync, tracker updates | Docs only |
| `ops-observability` | Logging, metrics, processing events, shutdown, worker operations | Yes |

## Workflow Skills

Use workflow skills as the main entry point. They sequence smaller concerns so the model does not need to infer orchestration.

| Workflow Skill | Slash Command | Primary Mode | Sequence |
| --- | --- | --- | --- |
| `workflow-feature-tdd` | `/feature` | `tdd-code` | scope -> red evidence -> implementation -> green evidence -> refactor -> review |
| `workflow-bug-diagnosis` | `/bugfix` | `diagnose` | reproduce -> minimize -> root cause -> red regression test -> fix -> green evidence |
| `workflow-etl-pipeline` | `/etl` | `etl-pipeline` | source -> parse -> normalize -> state -> merge -> buffer -> write -> observe -> tests |
| `workflow-db-change` | `/db` | `db-migration` | schema intent -> red MSSQL test -> migration/data access -> green evidence -> review |
| `workflow-ops-observability` | `/ops` | `orchestrator -> ops-observability` | phase gate -> observable contract -> red evidence -> green evidence -> refactor/verify |
| `workflow-architecture-decision` | `/adr` | `architect` | context -> options -> decision -> ADR -> implementation issues |
| `workflow-code-review` | `/review` | `review` | diff -> behavioral risks -> SQL risks -> tests -> operations |
| `workflow-docs-to-issues` | `/issues` | `docs-issues` | source docs -> PRD -> vertical slices -> issue files |

## Orchestration Rules

- Prefer workflow skills over individual skills for user-facing work.
- The orchestrator must not implement code.
- Architect mode must not implement code.
- All implementation workflows use TDD unless the user explicitly asks for read-only analysis.
- Production edits require red evidence first: a failing test or captured failing reproduction run before the edit. After implementation, record green evidence before refactoring.
- There is no "tests later" exception for behavior changes.
- For ETL work, model the canonical pipeline before touching code: source -> parse -> normalize -> state -> merge -> buffer -> write -> observe.
- ETL designs must specify idempotency, restart safety, source traceability, duplicate/replay behavior, backpressure, bounded buffers, and bulk-write behavior.
- For MSSQL writes, row-by-row ETL writes are forbidden by default. Use SqlBulkCopy to staging plus set-based MERGE/upsert patterns; any exception requires documented reviewer approval with volume limits and rationale.
- Row-by-row ETL writes require a documented reviewer-approved exception with expected volume, failure handling, and rationale.
- For database behavior, use real MSSQL container tests.
- Use parameterized SQL only. String-concatenated dynamic SQL is forbidden.
- Define indexes and transaction boundaries for schema, query, migration, and writer changes.
- Keep generated artifacts reusable across projects; avoid hardcoding the sample NewParser domain unless a target project explicitly adopts it.

## File Layout

```text
.roomodes
.roo/
  commands/
  rules/
  rules-architect/
  rules-db-migration/
  rules-diagnose/
  rules-docs-issues/
  rules-etl-pipeline/
  rules-ops-observability/
  rules-orchestrator/
  rules-review/
  rules-tdd-code/
  skills/
```
