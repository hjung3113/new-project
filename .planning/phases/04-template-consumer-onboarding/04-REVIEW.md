# Phase 4 Review - Harness Sync, Compatibility, and Doctor

## Design Review Status

Two pre-implementation adversarial reviews were completed:

1. Roo harness/workflow architect.
2. Cross-platform scripting + DB snapshot engineer.

## Findings and Reinforcements

### P1 - Roadmap/state sync is not mechanically enforced

- **Lens**: Correctness/invariants.
- **Concern**: ADR and planning workflows require `.planning/ROADMAP.md`, `.planning/STATE.md`, active checkpoints, and `.scratch/phase-state.json` to stay aligned, but `scripts/harness.py check` currently validates only JSON, command modes, paths, and stale phrases.
- **Acceptance/check**: Add at least two negative and one positive harness tests for roadmap/state drift. `check` or `doctor` must name stale files and the invariant.
- **Reinforcement**: Add explicit phase sync findings for roadmap total/completed counts, state frontmatter counts, active phase/checkpoint pointers, and live gate pointers.
- **Resolution**: Implemented for #17 in `scripts/harness.py` through reusable `find_roadmap_state_sync_findings(root)` and strict `check_roadmap_state_sync(root)`. Focused tests cover matching state, progress drift, and checkpoint pointer drift.

### P1 - DB config and selection must preserve cache-first behavior

- **Lens**: Compatibility/regression risk.
- **Concern**: Windows users should not need shell `source`/`export`, and config/doctor paths must not call `connect()` unless `--refresh` is explicit.
- **Acceptance/check**: Unit tests cover `.env`, JSON config, precedence, selected tables/procedures/jobs, full snapshot compatibility, default offline mode, and no `os.environ` mutation.
- **Reinforcement**: Implement Python config parsing with precedence `CLI > JSON config > .env > inherited environment`. Store selection in `collection_options` so cache reuse invalidates when selected objects change.
- **Resolution**: Implemented for issue #18. Added Python config loading for inherited environment, `.env`, JSON config, and CLI precedence without mutating `os.environ`; added `--config`, `--env-file`, `--snapshot-scope shape|selected|full`, `--include-tables`, `--include-procedures`, and `--include-jobs`; preserved `--collect-all-process-details` and `--include-agent-jobs`; kept default cache mode free of `connect()` calls; stored selection/config source metadata in `collection_options` and report metadata; added selected-mode filtering for cached offline reports and refreshed reports. Evidence: `python3 -m unittest scripts/test_db_context_snapshot.py` passed 16 tests; `python3 -m py_compile scripts/db_context_snapshot.py scripts/test_db_context_snapshot.py` exited 0.

### P2 - Doctor output needs stable low-reasoning fields

- **Lens**: Low-reasoning model usability.
- **Concern**: Plain `SystemExit` strings are insufficient for repair workflows. Low-reasoning agents need structured severity, cause, impact, fix, evidence, and mutation guidance.
- **Acceptance/check**: `python3 scripts/harness.py doctor` emits deterministic findings with `severity`, `code`, `path`, `cause`, `impact`, `fix`, and evidence. Doctor remains read-only.
- **Reinforcement**: Add a small finding object and reporter. Keep `check` strict, but make `doctor` the readable diagnostic entry point. Include dry-run/diff-before-mutation guidance.
- **Resolution**: Implemented for issue #19. Added `DoctorFinding`, `collect_doctor_findings`, JSON/Markdown renderers, `scripts/harness.py doctor`, Roo `/doctor`, and `workflow-harness-doctor`. Doctor is read-only and reports `severity`, `code`, `path`, `cause`, `impact`, `fix`, `evidence`, and `connects_to_db`.

### P2 - Snapshot scope vocabulary must be explicit

- **Lens**: Low-reasoning model usability.
- **Concern**: Current "full" means first-process-database detail rather than a clear user-facing snapshot scope.
- **Acceptance/check**: Add `--snapshot-scope shape|selected|full`, `--include-tables`, `--include-procedures`, `--include-jobs`, and preserve `--collect-all-process-details` compatibility.
- **Reinforcement**: Report selected/full scope in metadata and docs. Jobs are included only when `--include-agent-jobs` is set.
- **Resolution**: Implemented for issue #18. `docs/db-context-snapshot.md`, `.roo/commands/db.md`, and `.roo/skills/workflow-db-change/SKILL.md` now use the same connection/config and snapshot option vocabulary and include Bash and PowerShell examples for `.env`, JSON config, selected scope, table/procedure/job filters, `--collect-all-process-details`, and `--include-agent-jobs`.

## Final Adversarial Review

### P1 - Fresh installed targets reported generic roadmap/state sync errors

- **Reviewer**: Release/harness maintainer.
- **Resolution**: Fixed before PR. The clean skeleton now includes progress frontmatter, numeric Phase 0, an active checkpoint, durable phase-state pointers, and `.planning/phases/00-planning-hydration/00-CHECKPOINTS.md`. Added `test_installed_target_doctor_does_not_report_generic_sync_p1`.

### P1 - Offline selected snapshots ignored selection options

- **Reviewer**: Windows/Roo compatibility reviewer.
- **Resolution**: Fixed before PR. Cached offline reports now apply selected filters without calling `connect()`, update `collection_options`, and filter SQL Agent jobs. Added `test_offline_selected_snapshot_filters_cached_report_without_connecting`.

### P1 - `.env` was documented as a secret source but not gitignored

- **Reviewer**: Windows/Roo compatibility reviewer.
- **Resolution**: Fixed before PR. Added `.env`, `.env.*`, and `!.env.example` to root and clean skeleton `.gitignore`; extended gitignore tests and doctor required secret patterns.

### P2 - `/doctor` command was not skill-routed

- **Reviewer**: Windows/Roo compatibility reviewer.
- **Resolution**: Fixed. Added `.roo/skills/workflow-harness-doctor/SKILL.md`, updated `/doctor` command routing, and added it to the manifest.

### P2 - Windows verification equivalents were missing

- **Reviewer**: Windows/Roo compatibility reviewer.
- **Resolution**: Fixed. README now includes Python JSON validation and PowerShell temp-dir examples alongside Bash/JQ examples.

### P2 - Selected collection is output filtering, not query-level filtering

- **Reviewer**: Release/harness maintainer.
- **Resolution**: Accepted as a documented limitation for this slice. The implementation avoids arbitrary SQL and filters fixed catalog-query output. Query-level selected catalog predicates remain a follow-up candidate if large DB snapshot performance or sensitive unselected job command transfer becomes a problem.
