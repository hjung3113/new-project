# PROJECT - Roo C# ETL Orchestration Template

## One-liner

Cloneable Roo Code agent harness for C#/.NET ETL projects that need disciplined routing, phase-gated execution, TDD, MSSQL safety, and document-centered continuity across fresh sessions.

## Tech Runtime

- Agent harness: Roo modes, commands, rules, and workflow skills.
- Target implementation stack: C# on .NET 10.
- Target database: Microsoft SQL Server.
- Test expectation: xUnit, FluentAssertions, NSubstitute, and `testcontainers-dotnet` for real MSSQL behavior.
- Planning system: `.planning/` is the canonical document-centered project memory.
- Issue tracker: local markdown files under `.scratch/`.

## Current Milestone

**Milestone 1: reusable low-reasoning Roo harness.**

Success means a fresh agent can:

1. Read `.planning/STATE.md` and know the current phase, checkpoint, blockers, next action, and files of record.
2. Follow `.planning/ROADMAP.md` to see phase boundaries and acceptance criteria.
3. Enter the active phase folder under `.planning/phases/` and find context, plan, checkpoints, decisions, review findings, and verification evidence.
4. Use `.scratch/phase-state.json` only as the live gate for allowed work, not as the only memory of project intent.
5. Continue after session reset without relying on chat transcript or hidden memory.

## Decisions

<decisions>

### DEC-0001 - `.planning/` is canonical project memory - ACCEPTED

- Source: `.planning/PROJECT.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`.
- The current handoff file is a temporary transition artifact. Durable decisions, checkpoints, and verification evidence belong under `.planning/`.

### DEC-0002 - `.scratch/phase-state.json` is a gate, not a plan - ACCEPTED

- Source: `docs/phase-gate-harness.md`, `.scratch/phase-state.schema.json`.
- The phase-state file controls whether implementation may begin. It must point to the plan and checkpoint docs, but it must not become the only source of project context.

### DEC-0003 - Every phase must close with summary and verification - ACCEPTED

- Source: `.planning/phases/01-document-centered-phase-continuity/01-CHECKPOINTS.md`.
- A phase is not complete until its summary maps acceptance criteria to evidence and records unresolved follow-ups.

</decisions>

## Constraint Authority

- `.planning/STATE.md` is the first file a new session reads.
- `.planning/ROADMAP.md` owns phase boundaries and phase-level success criteria.
- `.planning/REQUIREMENTS.md` owns durable harness requirements.
- `.planning/phases/<phase>/` owns phase-local context, plans, decisions, checkpoints, review findings, summaries, and verification evidence.
- `docs/phase-gate-harness.md` owns phase-gate mechanics.
- `docs/roo-orchestration-design.md` owns Roo mode/workflow design.
- `.scratch/phase-state.schema.json` owns live gate state shape.

## Out of Scope

- Hard filesystem enforcement for phase gates. This remains a follow-up requiring pre-commit, CI, or repository permission tooling.
- Target application source code for a specific ETL product.
- Replacing `.scratch/` issue tracking; `.planning/` references `.scratch/` issues when they exist.
