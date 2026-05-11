# DECISIONS - Roo Harness Planning

Status values: `Proposed`, `Accepted`, `Locked`, `Superseded`.

| ID | Status | Decision | Source | Scope |
| --- | --- | --- | --- | --- |
| DEC-0001 | Accepted | `.planning/` is canonical project memory. | `.planning/PROJECT.md` | All phases |
| DEC-0002 | Accepted | `.scratch/phase-state.json` is a gate, not the plan. | `.planning/PROJECT.md`, `docs/phase-gate-harness.md` | Phase gate |
| DEC-0003 | Accepted | Every phase closes with summary and verification evidence. | `.planning/PROJECT.md`, `.planning/phases/01-document-centered-phase-continuity/01-CHECKPOINTS.md` | All phases |
| DEC-0004 | Accepted | New sessions start at `.planning/STATE.md`, then read live phase state. | `.planning/HANDOFF-PROTOCOL.md`, `AGENTS.md` | Continuity |
| DEC-0005 | Proposed | Phase 2 should add mechanical checks for phase-state validity and allowed-path drift. | `.planning/ROADMAP.md` | Enforcement |

## Promotion Rule

When a phase-local decision affects more than one phase, promote it here or into `docs/adr/` if it needs a full ADR.
