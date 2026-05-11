# STRUCTURE - Planning and Harness Files

## Durable Planning Memory

```text
.planning/
  PROJECT.md
  REQUIREMENTS.md
  ROADMAP.md
  STATE.md
  codebase/
  intel/
  phases/
```

Agents start at `.planning/STATE.md`, then follow links to roadmap and active phase files.

## Phase Folder Pattern

```text
.planning/phases/<NN-phase-slug>/
  NN-CONTEXT.md
  NN-01-PLAN.md
  NN-CHECKPOINTS.md
  NN-REVIEW.md
  NN-VERIFICATION.md
  NN-01-SUMMARY.md
```

Add more `NN-02-PLAN.md` and `NN-02-SUMMARY.md` files when a phase requires multiple independently resumable plans.

## Harness Files

```text
.roomodes
.roo/
  commands/
  rules/
  rules-*/
  skills/
.scratch/
  phase-state.schema.json
  phase-state.example.json
```

`.scratch/phase-state.json` should exist once a repo has an active or completed gated phase. It is the live gate pointer back to `.planning/`, not the full project memory.
