# INTEGRATIONS - Harness Touchpoints

**Analysis date:** 2026-05-11

## Roo Code

- `.roomodes` defines project-local modes and edit scopes.
- `.roo/commands/*.md` are thin user entry points.
- `.roo/rules-*/rules.md` hold mode-specific behavior.
- `.roo/skills/workflow-*/SKILL.md` hold step-by-step workflows.

## Planning Memory

- `.planning/STATE.md` is the first durable restart file.
- `.planning/ROADMAP.md` owns phase boundaries and success criteria.
- `.planning/phases/` owns phase-local context, plans, checkpoints, review, verification, and summaries.
- `.planning/DECISIONS.md` records cross-phase decisions.

## Live Gate State

- `.scratch/phase-state.json` is the current gate.
- `.scratch/phase-state.schema.json` defines valid gate shape.
- `.scratch/phase-state.example.json` is the reference example for future states.

## Local Issue Tracker

- Issue and PRD files live under `.scratch/` per `docs/agents/issue-tracker.md`.
- Triage labels follow `docs/agents/triage-labels.md`.
- Domain docs are discovered through `docs/agents/domain.md`.

## External Enforcement Candidates

Phase 2 may add:

- A local validation script for phase-state JSON.
- A changed-path checker comparing git diff paths with `allowed_paths`.
- Pre-commit or CI checks.
- Documentation for bypass policy and known limitations.
