# VERIFICATION - Global Evidence Ledger

| Date | Phase | Check | Result | Notes |
| --- | --- | --- | --- | --- |
| 2026-05-11 | Phase 1 | `.planning/` file tree exists | PASS | `find .planning -maxdepth 3 -type f \| sort` |
| 2026-05-11 | Phase 1 | Live phase state validates | PASS | `npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.json` |
| 2026-05-11 | Phase 1 | Example phase state validates | PASS | `npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.example.json` |
| 2026-05-11 | Phase 1 | Restart references exist | PASS | `rg -n "STATE.md|phase-state|checkpoint" AGENTS.md README.md docs/phase-gate-harness.md .planning` |
| 2026-05-11 | Phase 1 | `/ops` command routing docs aligned | PASS | Stale direct `ops-observability` command-mode references returned no hits in `.roo/commands` and `docs/roo-orchestration-design.md`. |

Add new rows when a phase closes or a cross-phase verification command becomes important.
