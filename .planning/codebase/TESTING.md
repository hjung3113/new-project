# TESTING - Harness Verification

**Analysis date:** 2026-05-11

## Current Verification Targets

Use these checks when planning or phase-gate files change:

```bash
jq . .roomodes >/dev/null
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.json
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.example.json
rg -n "STATE.md|phase-state|checkpoint" AGENTS.md README.md docs/phase-gate-harness.md .roo .planning
```

## What Counts As Evidence

- Planning structure: `find .planning -maxdepth 3 -type f | sort`.
- Gate schema validity: AJV validation against `.scratch/phase-state.schema.json`.
- Roo compatibility: `.roomodes` parses as JSON and changed command frontmatter remains consistent with `.roo/rules-orchestrator/rules.md`.
- Restart safety: `AGENTS.md`, Roo rules, docs, and `.planning/STATE.md` all point to the same restart order.

## Target Project Tests

When this harness is copied into an actual C# ETL project, implementation phases should use:

- xUnit + FluentAssertions for behavior.
- NSubstitute only at external collaborator boundaries.
- `testcontainers-dotnet` with real MSSQL for persistence, migration, writer, restart, idempotency, and transaction behavior.

Do not treat mocked repositories, EF InMemory, SQLite, or prompt-only reviews as proof of MSSQL behavior.
