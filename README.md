# Roo C# ETL Orchestration Template

Clone this repository to start a Roo Code workspace for C#/.NET 10 ETL projects backed by Microsoft SQL Server.

This repo is an agent harness, not an application implementation. It provides Roo modes, slash commands, workflow skills, routing rules, phase gates, and durable planning docs so lower-reasoning models can work inside narrow, reviewable workflows.

## What This Template Enforces

- Route every request through one owning workflow instead of ad hoc implementation.
- Keep implementation behind a phase gate: `discuss -> plan -> execute -> done`.
- Require TDD for behavior changes: red evidence, smallest green change, then refactor.
- Use real MSSQL coverage through `testcontainers-dotnet` for database, writer, migration, transaction, restart, and idempotency behavior.
- Keep durable project memory under `.planning/` so a fresh Roo session can resume without chat history.
- Keep Roo configuration, planning docs, application code, and tracker files in separate mode ownership boundaries.

## Fresh Session Start

Read these in order before work:

1. [AGENTS.md](AGENTS.md)
2. [.planning/STATE.md](.planning/STATE.md)
3. [.planning/ROADMAP.md](.planning/ROADMAP.md)
4. The active `.planning/phases/**/**-CHECKPOINTS.md`
5. [.scratch/phase-state.json](.scratch/phase-state.json)

`.planning/` is the durable project memory. `.scratch/phase-state.json` is only the live gate for allowed work.

## Slash Commands And Workflows

| Command | Roo mode | Workflow skill | Use when |
| --- | --- | --- | --- |
| `/feature` | `orchestrator` | `workflow-feature-tdd` | Ordinary application behavior or refactoring when no narrower owner applies. |
| `/bugfix` | `orchestrator` | `workflow-bug-diagnosis` | Something is broken, a test fails, output is wrong, performance regressed, or root cause is unknown. |
| `/etl` | `orchestrator` | `workflow-etl-pipeline` | Parser, normalization, state, matching, merge, buffering, writer flow, replay, or restart-safety work. |
| `/db` | `orchestrator` | `workflow-db-change` | MSSQL schema, EF migration, SQL, indexes, transactions, Dapper exceptions, `SqlBulkCopy`, staging, or `MERGE`. |
| `/ops` | `orchestrator` | `workflow-ops-observability` | Logs, metrics, processing events, retry boundaries, worker polling, graceful shutdown, dashboards, or runbooks. |
| `/adr` | `architect` | `workflow-architecture-decision` | Durable design decisions, state models, tradeoffs, ADRs, and implementation planning. |
| `/review` | `review` | `workflow-code-review` | Read-only review of C#, SQL, ETL, tests, performance, reliability, or operations risk. |
| `/issues` | `docs-issues` | `workflow-docs-to-issues` | Convert requirements, design notes, or plans into PRDs and independently implementable issue slices. |

Slash commands are thin entry points. Routing decisions live in [.roo/rules-orchestrator/rules.md](.roo/rules-orchestrator/rules.md); execution sequences live in [.roo/skills/](.roo/skills/).

## Workflow Skill Catalog

| Skill | Primary owner | Purpose |
| --- | --- | --- |
| `workflow-phase-gate` | all implementation workflows | Reads `.planning` and `.scratch/phase-state.json`; blocks implementation unless `phase=execute`, `approved=true`, approved `plan_id`, `allowed_paths`, and `verification` are present. |
| `workflow-feature-tdd` | `tdd-code` | Implements feature behavior with red-green-refactor, xUnit, FluentAssertions, and scoped code changes. |
| `workflow-bug-diagnosis` | `diagnose` | Reproduce, minimize, prove root cause, add a failing regression test, fix, and verify. |
| `workflow-etl-pipeline` | `etl-pipeline` | Changes ETL stage behavior in the canonical order: source -> parse -> normalize -> state -> merge -> buffer -> write -> observe. |
| `workflow-db-change` | `db-migration` | Handles MSSQL schema, migrations, queries, indexes, transactions, `SqlBulkCopy`, staging, and set-based `MERGE` writes. |
| `workflow-ops-observability` | `ops-observability` | Adds or reviews operational behavior: structured logs, metrics, processing events, retries, worker lifecycle, and graceful shutdown. |
| `workflow-architecture-decision` | `architect` | Frames design options, records ADRs, and turns durable decisions into implementation slices. |
| `workflow-code-review` | `review` | Reviews correctness, SQL safety, ETL behavior, tests, performance, and operations risk without editing code. |
| `workflow-docs-to-issues` | `docs-issues` | Turns requirements and plans into PRDs and local issue slices with acceptance criteria and test expectations. |

## Mode Ownership

| Mode | Can edit | Must not edit |
| --- | --- | --- |
| `orchestrator` | read-only routing | implementation code, agent-control files |
| `architect` | `docs/`, `.planning/`, `.scratch/` tracker files | `.roomodes`, `.roo/**`, `AGENTS.md`, `CLAUDE.md`, `.scratch/phase-state*.json` |
| `docs-issues` | `docs/`, `.planning/`, `.scratch/` tracker files | agent-control files, phase approval JSON |
| `tdd-code` | application code allowed by the approved plan | docs, `.planning/`, `.scratch/`, Roo harness files |
| `etl-pipeline` | ETL/application code allowed by the approved plan | docs, `.planning/`, `.scratch/`, Roo harness files |
| `db-migration` | database/application code allowed by the approved plan | docs, `.planning/`, `.scratch/`, Roo harness files |
| `diagnose` | bugfix code allowed by the approved plan | docs, `.planning/`, `.scratch/`, Roo harness files |
| `ops-observability` | operations/application code allowed by the approved plan | docs, `.planning/`, `.scratch/`, Roo harness files |
| `review` | read-only | edits and mutation-capable commands |
| `harness-maintainer` | `.roomodes`, `.roo/**`, phase approval JSON, `AGENTS.md`, `CLAUDE.md` | application implementation |

The important boundary is that planning modes maintain `.planning/`; implementation modes do not.

## Phase Gate

Use `workflow-phase-gate` before implementation workflows.

| Phase | Allowed work |
| --- | --- |
| `discuss` | Read-only discovery, search, options, and questions. |
| `plan` | Docs, ADRs, PRDs, checklists, issue plans, acceptance criteria, and verification planning. |
| `execute` | Implementation only for the approved `plan_id` and only inside `allowed_paths`. |
| `done` | Summary, rationale, verification evidence, and follow-up candidates. |

See [docs/phase-gate-harness.md](docs/phase-gate-harness.md), [.roo/rules/phase-gate.md](.roo/rules/phase-gate.md), and [.scratch/phase-state.example.json](.scratch/phase-state.example.json).

## Engineering Defaults

- C# on .NET 10.
- Microsoft SQL Server.
- Pipeline-first Clean Architecture.
- EF Core by default.
- Dapper only for documented complex or performance-sensitive read-query exceptions.
- xUnit, FluentAssertions, and NSubstitute.
- `testcontainers-dotnet` with real MSSQL containers for SQL, migrations, EF Core queries, Dapper queries, writers, restart safety, idempotency, and transactions.
- ETL writes should be set-based: `SqlBulkCopy` to staging plus set-based `MERGE`/upsert.

## Repository Map

| Path | Purpose |
| --- | --- |
| [.roomodes](.roomodes) | Roo mode definitions and edit scopes. |
| [.roo/commands/](.roo/commands/) | Slash command entry points. |
| [.roo/rules/](.roo/rules/) | Global and phase-gate rules. |
| [.roo/rules-orchestrator/rules.md](.roo/rules-orchestrator/rules.md) | Exclusive routing table and tie breakers. |
| [.roo/skills/](.roo/skills/) | Workflow skill definitions. |
| [.planning/](.planning/) | Durable project memory, roadmap, state, checkpoints, review, and verification. |
| [.scratch/phase-state.json](.scratch/phase-state.json) | Live phase gate state. |
| [docs/phase-gate-harness.md](docs/phase-gate-harness.md) | Phase gate mechanics and limits. |
| [docs/roo-orchestration-design.md](docs/roo-orchestration-design.md) | Roo orchestration design notes. |

## Verification Commands

```bash
jq . .roomodes >/dev/null
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.json
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.example.json
```

For current project state and next actions, start at [.planning/STATE.md](.planning/STATE.md).
