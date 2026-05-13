# Phase 3 Review - Harness Distribution and Enforcement

## Adversarial Review Summary

Three post-implementation review passes covered installer/security, Roo workflow fit, and documentation contamination.

## Findings Resolved

### P1 - `--chain` could be read as bypassing execute approval

- **Finding**: Initial wording treated `--chain` as approval to move from plan to execute without explicitly requiring live phase-state authorization.
- **Resolution**: `workflow-phase-gate`, command docs, README, AGENTS, and skeleton docs now require `.scratch/phase-state.json` to be verified or written with `phase=execute`, matching `plan_id`, `approved=true`, `automation_mode=chain`, durable pointers, non-empty `allowed_paths`, and non-empty `verification` before implementation.
- **Evidence**: `python3 scripts/harness.py check --worktree`; AJV validation for phase-state files.

### P1 - Live phase gate did not authorize alignment-hardening edits

- **Finding**: `.scratch/phase-state.json` still pointed at CP-03-05 and did not allow `.roo/**`, schema/example state, or phase-gate docs.
- **Resolution**: Live state now points at CP-03-06 and includes the harness rule, docs, schema, skeleton, and script paths touched by this slice.
- **Evidence**: `python3 scripts/harness.py check --worktree`.

### P2 - `auto_selected` was not auditable enough

- **Finding**: Plain string entries did not force low-reasoning models to explain what was auto-selected and why it was safe.
- **Resolution**: `auto_selected` is now an array of objects with `choice`, `selected_value`, `reason`, `evidence_path`, `risk_level`, `reversible`, `inside_allowed_paths`, and `stop_conditions_checked`; `scripts/harness.py check` validates the structure.
- **Evidence**: `test_phase_state_semantics_require_auditable_auto_selected_entries`.

### P2 - Phase-local discuss questions were too abstract

- **Finding**: The first draft listed dimensions but left weak models to invent the actual questions.
- **Resolution**: `workflow-phase-gate` now includes a concrete question template and blocks entry to `plan` until each question has `repo_answer`, `user_answer`, or `open_blocker`.

### P2 - Restart order drifted across docs

- **Finding**: `docs/phase-gate-harness.md` omitted `.planning/codebase/**` from restart order.
- **Resolution**: Phase-gate docs and handoff protocol now match AGENTS and workflow-phase-gate restart order.

### P3 - Clean skeleton missed a file of record

- **Finding**: `.planning/HANDOFF-PROTOCOL.md` was listed as a file of record but not distributed in the clean skeleton.
- **Resolution**: Added clean skeleton handoff protocol and manifest entry.

### P1 - Installed target could not run `check`

- **Finding**: Target-local `scripts/harness.py check` required source `harness/manifest.json`.
- **Resolution**: `check` now supports installed-target mode through `.harness/installed-manifest.json`.
- **Evidence**: `test_installed_target_can_run_check`.

### P1 - `init` could partially write before refusing conflicts

- **Finding**: `init` checked collisions one file at a time.
- **Resolution**: `init` now preflights all destinations before any write.
- **Evidence**: `test_init_refuses_to_overwrite_existing_project_file`.

### P1 - Manifest destination paths could escape target

- **Finding**: Source paths were contained, but destination paths were not.
- **Resolution**: `destination_path` rejects absolute paths, `..`, drive roots, and resolved paths outside target.
- **Evidence**: `test_manifest_destination_paths_cannot_escape_target`.

### P1 - Symlink destinations could overwrite outside target

- **Finding**: `shutil.copyfile` follows destination symlinks.
- **Resolution**: `write_copy` refuses symlink destinations and symlinked parent paths.
- **Evidence**: `test_write_copy_refuses_destination_symlink`.

### P2 - Upgrade could bootstrap uninitialized targets

- **Finding**: `upgrade` on an empty target could create a partial harness.
- **Resolution**: `upgrade` fails closed when no install state or existing manifest-owned files are present.
- **Evidence**: `test_upgrade_without_install_state_does_not_bootstrap_empty_target`.

### P2 - Live state still pointed at Phase 2

- **Finding**: `.planning/STATE.md` and `.scratch/phase-state.json` pointed to the previous DB snapshot phase.
- **Resolution**: Both now point to Phase 3 and plan `harness-distribution-03-01`.

### P2 - Harness maintainer ownership was too narrow

- **Finding**: `.roomodes` did not allow harness maintainer edits to `harness/**` or harness scripts.
- **Resolution**: `harness-maintainer` now owns distribution files and harness docs.

## Remaining Follow-Ups

- Managed-block merging for `AGENTS.md` and `README.md` remains deferred.
- CI/pre-commit wrappers around `scripts/harness.py check --base <ref>` remain deferred.
- Package-manager installation remains out of scope.
