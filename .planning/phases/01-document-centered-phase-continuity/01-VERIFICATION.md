# Phase 1 Verification

## Checks

```bash
find .planning -maxdepth 3 -type f | sort
test -f .planning/STATE.md
test -f .planning/phases/01-document-centered-phase-continuity/01-CHECKPOINTS.md
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.json
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.example.json
rg -n "STATE.md|phase-state|checkpoint" AGENTS.md README.md docs/phase-gate-harness.md .planning
```

## Expected Result

- `.planning/` contains project, requirement, roadmap, state, codebase, intel, and phase files.
- `AGENTS.md` instructs new sessions to start with `.planning/STATE.md`.
- `docs/phase-gate-harness.md` explains how the live phase state links to durable plan/checkpoint docs.
- `.scratch/phase-state.json` and `.scratch/phase-state.example.json` validate against the strengthened schema.

## Status

Passed on 2026-05-11.
