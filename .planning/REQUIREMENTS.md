# REQUIREMENTS - Document-Centered Continuity

## REQ-continuity

A fresh agent must be able to resume the project after session reset by reading tracked files only.

Acceptance:

- `.planning/STATE.md` identifies the current phase, current checkpoint, blocker state, and next action.
- `.planning/ROADMAP.md` lists every phase with status, dependencies, gates, and success criteria.
- The active phase folder contains enough context to continue without the previous chat transcript.
- Handoff documents reference `.planning/` artifacts instead of duplicating them.

## REQ-phase-checkpoints

Each phase must have explicit checkpoints that prevent hidden progress loss.

Acceptance:

- Every phase folder has a checkpoint file with named checkpoints.
- Each checkpoint records status, required evidence, and the next unblock action.
- Work may pause after any checkpoint with a clear restart instruction.

## REQ-decision-capture

Decisions made during work must be durable and discoverable.

Acceptance:

- Project-wide decisions live in `.planning/PROJECT.md`.
- Phase-local decisions live in the phase `*-CONTEXT.md`, `*-PLAN.md`, or `*-SUMMARY.md`.
- Cross-phase decisions are promoted to `PROJECT.md` or an ADR.
- Review findings are preserved in `*-REVIEW.md` or `*-ADVERSARIAL-REVIEW.md`.

## REQ-verification-chain

Completion claims must point to evidence.

Acceptance:

- Phase summaries map success criteria to verification artifacts.
- Verification docs include exact commands or review methods used.
- Failed checks remain visible with owner and next action.

## REQ-gate-alignment

The Roo phase gate must align with the document system.

Acceptance:

- `.scratch/phase-state.json` points to the active plan and checkpoint docs.
- `execute` state includes allowed paths and verification commands.
- Phase-gate documentation tells agents to read `.planning/STATE.md` before relying on the live state file.
