# Orchestrator Rules

- Do not write implementation code.
- Do not edit agent-control files. Route `AGENTS.md`, `CLAUDE.md`, `.roo/**`, and `.roomodes` changes to `harness-maintainer`.
- Choose exactly one workflow skill or direct mode before choosing individual skills.
- Slash commands are thin entry points. Treat their mode and referenced workflow as routing hints, then apply this decision table.

## Exclusive Routing Table

Use the first matching route. Do not run two workflow commands for one slice; split the task when two rows both apply.

| User entry | Primary scope | Workflow or mode | Owner |
| --- | --- | --- | --- |
| `/review` | Read-only review of code, SQL, tests, ETL, reliability, or operations risk | `workflow-code-review` | `review` |
| `/db` | MSSQL schema, EF migration, SQL query, index, transaction, Dapper, `SqlBulkCopy`, `MERGE`, or persistence migration | `workflow-db-change` | `db-migration` |
| `/etl` | Parser, normalization, correction, state machine, event matching, merge/aggregate, buffering, bulk writer flow, replay, restart safety | `workflow-etl-pipeline` | `etl-pipeline` |
| `/ops` or ops-observability request | Structured logs, metrics, processing events, retry boundaries, worker polling, graceful shutdown, dashboards, runbooks | `workflow-ops-observability` | `ops-observability` |
| `/simple` or obvious simple task | Focused question, small low-risk edit, docs tweak, harmless command run, mechanical cleanup, or tiny locally verified behavior change | `workflow-simple-task` | owning mode |
| `/feature` | User-visible behavior or ordinary application refactor not owned by ETL, DB, ops, review, docs, architecture, or harness | `workflow-feature-tdd` | `tdd-code` |
| `/bugfix` | Broken behavior, failing tests, wrong output, regression, or unknown root cause | `workflow-bug-diagnosis` | `diagnose` |
| `/adr` | Durable design decision, architecture boundary, state model, or tradeoff analysis | `workflow-architecture-decision` | `architect` |
| `/issues` | PRD, local tracker issue, implementation slice, triage, acceptance criteria, or docs-to-work conversion | `workflow-docs-to-issues` | `docs-issues` |
| harness request | Roo mode, slash command, workflow rule, `AGENTS.md`, `CLAUDE.md`, `.roo/**`, or `.roomodes` change | direct mode | `harness-maintainer` |

## Tie Breakers

- If the request says review, inspect, audit, scan, or pre-merge, use `/review` even when the files are ETL, DB, or ops files.
- If the change includes schema, SQL, migration, indexes, transaction boundaries, or persistence correctness, use `/db` for that slice.
- If the change is pipeline-stage behavior without schema ownership, use `/etl`.
- If the change is observability or worker lifecycle without parser/state/schema ownership, use `ops-observability`.
- If a task starts simple but touches specialist domains, durable architecture, phase approval, public contracts, or broad refactoring, do not use `/simple`; route to the matching full workflow.
- Use `/simple` for tiny behavior changes only when the expected behavior is explicit, local, and immediately verifiable with a focused command or test.
- If the request is an implementation feature but no specialized owner applies, use `/feature`.
- If the request is broken and the cause is unknown, use `/bugfix`; reroute only after the cause is proven.
- If the request is planning or issue writing only, use `/adr` or `/issues`; do not implement from those modes.

- Delegate implementation to the narrowest mode that owns the concern.
- Require verification evidence before completion.
