# Phase 3 Checkpoints - Harness Distribution and Enforcement

## CP-03-01 - Adversarial review completed

- **Status**: Complete.
- **Evidence**: Three reviewer summaries in the current session.
- **Restart**: Continue from the synthesized risks in `03-CONTEXT.md`.

## CP-03-02 - Manifest and clean skeleton implemented

- **Status**: Complete.
- **Evidence**: `harness/manifest.json`, `harness/skeleton/clean/**`.
- **Restart**: Run `python3 -m unittest scripts/test_harness.py`.

## CP-03-03 - Init, upgrade, and check implemented

- **Status**: Complete.
- **Evidence**: `scripts/harness.py`, `scripts/test_harness.py`.
- **Restart**: Run the Phase 3 verification commands from `03-01-PLAN.md`.

## CP-03-04 - README updated

- **Status**: Complete.
- **Evidence**: `README.md`.
- **Restart**: Verify README mentions init, upgrade, check, ownership, and PR checks.

## CP-03-05 - Review and hardening complete

- **Status**: Complete.
- **Evidence**: `03-REVIEW.md`, `03-VERIFICATION.md`, `03-01-SUMMARY.md`.
- **Restart**: Address review findings before PR.

## CP-03-06 - ADR/init alignment hardening added

- **Status**: Complete.
- **Evidence**: `AGENTS.md`, `README.md`, `docs/phase-gate-harness.md`, `.roo/commands/README.md`, `.roo/commands/adr.md`, `.roo/rules/phase-gate.md`, `.roo/skills/workflow-architecture-decision/SKILL.md`, `.roo/skills/workflow-planning-hydration/SKILL.md`, `.roo/skills/workflow-phase-gate/SKILL.md`, `.scratch/phase-state.schema.json`, `scripts/harness.py`, `scripts/test_harness.py`, `harness/manifest.json`, `harness/skeleton/clean/**`.
- **Restart**: Run harness verification, then open a PR for `codex/harness-distribution-hardening`.

## CP-03-07 - README workflow prompt examples added

- **Status**: Complete.
- **Evidence**: `README.md`, `harness/skeleton/clean/README.md`.
- **Restart**: Run harness verification, then push the requested README onboarding update.
