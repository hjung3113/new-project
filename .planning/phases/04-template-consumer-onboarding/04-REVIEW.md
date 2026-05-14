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

## Issue #16 Design Adversarial Review

### Harness Distribution Architect

#### Lens 1 - Harness distribution and upgrade safety

- **Score**: 4/5.
- **Rationale**: Manifest coverage for every `.roo/commands/*.md` command except `README.md` directly closes the split-brain risk where source commands work but target installs miss them.
- **Failure scenario**: A future `.roo/commands/phase-review.md` exists in the source repo but is not shipped through `harness/manifest.json`.
- **Recommendation**: Test every real command file is manifest-owned and keep manifest source-existence checks.
- **Blocking**: No.
- **Resolution**: Added command coverage regression tests requiring Issue #16 commands to exist and every non-README command to be `harness-owned` in the manifest.

#### Lens 2 - Manifest policy consistency and managed-block decision

- **Score**: 2/5.
- **Rationale**: Saying "likely managed-block merge" is not a durable policy, and current `managed` behavior is still file-level conflict handling.
- **Failure scenario**: Docs claim managed-block upgrades while the script still conflicts or overwrites whole files, misleading target projects about preservation guarantees.
- **Recommendation**: Decide explicitly now; either defer managed-block implementation or fully implement markers, merge, dry-run, rollback, and tests.
- **Blocking**: Yes if upgrade semantics change in this slice; no if implementation is explicitly deferred.
- **Resolution**: Accepted `managed-block merge` as the future policy for `AGENTS.md` and `README.md`, while documenting that this slice does not change current file-level conflict behavior.

#### Lens 3 - Low-reasoning model safety

- **Score**: 4/5.
- **Rationale**: Explicit phase command routes reduce ambiguity only if `/phase-execute` and `/fsd-phase` cannot be read as inline implementation permission.
- **Failure scenario**: A low-reasoning agent invokes `/phase-execute`, sees `approved=true`, and mutates files directly from orchestrator.
- **Recommendation**: Route `/phase-execute` through execute-gate verification and owning-mode handoff; add a tie-breaker that phase commands do not override Subtask-First Execution.
- **Blocking**: No after wording is added.
- **Resolution**: Added explicit routing rows and tie-breaker language requiring verified execute gate fields and subtask-first handoff.

### Roo Code / Agent Workflow Reviewer

#### Lens 1 - Roo slash command compatibility

- **Score**: 4/5.
- **Rationale**: New command files fit the existing thin-command pattern if they use valid frontmatter, known modes, `$ARGUMENTS`, and `workflow-phase-gate`.
- **Failure scenario**: A command file embeds full workflow logic or references a missing mode, causing Roo routing drift.
- **Recommendation**: Validate command modes and list the commands in `.roo/commands/README.md` and `harness/manifest.json`.
- **Blocking**: No.
- **Resolution**: Added thin command files with valid existing modes and `workflow-phase-gate` references; existing mode validation covers unknown modes.

#### Lens 2 - Workflow phase-gate and subtask-first semantics

- **Score**: 3/5.
- **Rationale**: Phase commands must not become an escape hatch from the orchestrator's handoff-only role.
- **Failure scenario**: `/phase-execute` performs edits inline after gate verification instead of handing work to the owning implementation mode.
- **Recommendation**: Add phase rows before generic harness routing and state that the orchestrator emits or creates the handoff while the owning mode executes.
- **Blocking**: Yes until `/phase-execute` and `/fsd-phase` explicitly preserve subtask-first delegation.
- **Resolution**: Blocking item fixed in `.roo/rules-orchestrator/rules.md` and command wording.

#### Lens 3 - Command wording clarity for low-reasoning agents

- **Score**: 3/5.
- **Rationale**: The phase commands are semantically close; each command needs blunt boundaries and stop conditions.
- **Failure scenario**: `/phase-plan` edits implementation files, or `/fsd-phase --chain` skips review and approval evidence.
- **Recommendation**: Put concrete allowed work, forbidden work, required state, owner handoff, and stop condition language into the command files.
- **Blocking**: No after Lens 2 fix.
- **Resolution**: Added numbered checklists to each phase command.

## Issue #16 Implementation Adversarial Review

### Test / Regression Engineer

#### Lens 1 - Regression coverage quality

- **Score**: 3/5.
- **Rationale**: The first regression tests covered command existence, manifest ownership, and broad routing safety phrases, but did not protect command frontmatter or command-specific guardrails.
- **Failure scenario**: `/phase-execute.md` loses `mode: orchestrator` or no longer references `$ARGUMENTS`; filename and broad routing tests still pass.
- **Recommendation**: Add a table-driven test for expected command modes, `argument-hint`, `workflow-phase-gate`, `$ARGUMENTS`, and command-specific guardrails.
- **Blocking**: Yes.
- **Resolution**: Added `test_phase_command_files_keep_thin_workflow_contract`.

#### Lens 2 - Manifest/distribution test correctness

- **Score**: 3/5.
- **Rationale**: Manifest ownership was tested, but source/path identity was not.
- **Failure scenario**: `.roo/commands/phase-plan.md` has a manifest row with `source: .roo/commands/phase-discuss.md`, installing duplicate content under the wrong filename.
- **Recommendation**: Assert `entry.source == entry.path` for command files and smoke-test init installs the phase command files from those sources.
- **Blocking**: Yes.
- **Resolution**: Extended command manifest coverage to assert source identity and added `test_init_installs_phase_commands_from_manifest_sources`.

#### Lens 3 - Routing/subtask-first test adequacy

- **Score**: 2/5.
- **Rationale**: String presence did not prove exact routing rows, owners, workflow, or order before generic harness routing.
- **Failure scenario**: The generic `harness request` row moves above `/phase-execute`, or `/phase-execute` owner changes to `harness-maintainer`; broad safety text remains elsewhere.
- **Recommendation**: Parse the markdown routing table and assert exact rows for all four phase commands, workflow `workflow-phase-gate`, expected owners, and order before `harness request`.
- **Blocking**: Yes.
- **Resolution**: Replaced broad route checks with parsed routing-table assertions in `test_phase_commands_have_explicit_subtask_first_routing`.

### Harness Upgrade Safety Reviewer

#### Lens 1 - Upgrade/install safety

- **Score**: 4/5.
- **Rationale**: The four commands are present and manifest-owned, and the regression test catches future command files missing from the manifest.
- **Failure scenario**: A future command file is added under `.roo/commands/` but omitted from `harness/manifest.json`.
- **Recommendation**: Nonblocking: also keep `.roo/commands/README.md` intentionally shipped.
- **Blocking**: No.
- **Resolution**: Existing manifest already ships `.roo/commands/README.md`; command coverage excludes it by requirement only.

#### Lens 2 - Managed-block policy honesty vs implemented behavior

- **Score**: 4/5.
- **Rationale**: README, DECISIONS, and phase context separate the future managed-block policy from current file-level conflict behavior.
- **Failure scenario**: A target repo operator expects automatic block merging and is surprised by `.harness/conflicts/**/*.new`.
- **Recommendation**: Nonblocking: require marker, dry-run, local-edit, conflict, and rollback tests when block merging is implemented.
- **Blocking**: No.
- **Resolution**: Future managed-block implementation criteria are documented with the policy decision.

#### Lens 3 - Cross-target low-reasoning safety

- **Score**: 4/5.
- **Rationale**: Routing rows and command files explicitly state that `/phase-execute` and `/fsd-phase` create or output handoffs and stop if `new_task` is unavailable.
- **Failure scenario**: A low-reasoning agent treats `/fsd-phase --chain` as permission to implement inline.
- **Recommendation**: Nonblocking: tests should also assert command-file guardrails.
- **Blocking**: No.
- **Resolution**: Added command-file contract tests for the guardrails.

## Issue #16 Final Real-World Risk Analysis

### Roo Code / Agent Workflow Specialist

#### Lens 1 - Roo Code compatibility and routing

- **Score**: 4/5.
- **Rationale**: New phase commands follow thin command structure, use valid frontmatter modes, reference `workflow-phase-gate`, and preserve subtask-first handoff.
- **Failure scenario**: `/phase-execute` is interpreted as inline implementation permission.
- **Recommendation**: Keep explicit handoff wording and ensure new command files are included in the PR.
- **Blocking**: No for design; release hygiene requires tracked command files.
- **Resolution**: Command files are part of the working tree and will be included in the commit/PR.

#### Lens 2 - Workflow fit and DB access risk

- **Score**: 2/5.
- **Rationale**: Selected DB snapshot refresh filtered output after broad catalog reads, so selected procedure/job requests could still read unselected definitions.
- **Failure scenario**: A production-like selected refresh reads all routine or job definitions before output filtering.
- **Recommendation**: Push filters into catalog SQL or require an explicit broad-catalog-read acknowledgment.
- **Blocking**: Yes.
- **Resolution**: Added `--allow-broad-catalog-read` and rejected selected refresh before connecting unless the flag is present.

#### Lens 3 - Script corner cases and OS compatibility

- **Score**: 4/5.
- **Rationale**: Python path handling and config parsing are portable, but tests should not assume `python3` exists on every target OS.
- **Failure scenario**: Windows test runs fail because `python3` is not on PATH.
- **Recommendation**: Use `sys.executable` for installed-target test subprocesses.
- **Blocking**: No.
- **Resolution**: Updated installed-target harness test to use `sys.executable`.

### Harness Script / Cross-platform Engineer

#### Lens 1 - Script corner cases

- **Score**: 3/5.
- **Rationale**: `upgrade` previously proceeded against non-initialized targets when any manifest path existed, which could mutate arbitrary existing repos.
- **Failure scenario**: Running `upgrade --target /existing/repo` with a README but no install state writes harness files into that repo.
- **Recommendation**: Require `.harness/installed-manifest.json` for all upgrades; use a separate explicit adoption path later if needed.
- **Blocking**: Yes.
- **Resolution**: `upgrade` now always rejects targets without install state, including targets containing manifest paths.

#### Lens 2 - Windows/Linux/macOS compatibility

- **Score**: 3/5.
- **Rationale**: Core path handling is portable; command examples still lean on `python3` in some docs.
- **Failure scenario**: A Windows user follows a `python3` example where only `python` or `py -3` exists.
- **Recommendation**: Prefer Python-driven checks and include PowerShell equivalents where user-facing.
- **Blocking**: No for this Issue #16 slice.
- **Resolution**: Existing DB docs include PowerShell examples; installed-target test now uses `sys.executable`.

#### Lens 3 - Distribution/manifest robustness

- **Score**: 4/5 after tracked-file fix.
- **Rationale**: Manifest and init tests now cover command presence, source identity, routing, and copied target content.
- **Failure scenario**: Manifest references a new command file that is not committed.
- **Recommendation**: Include the new files in the PR and rely on source `check` plus command coverage tests.
- **Blocking**: Yes before PR if files are omitted.
- **Resolution**: Will include all four new command files in the commit/PR.

### Production Safety / Data Access Reviewer

#### Lens 1 - Operational DB access risk

- **Score**: 2/5 before final fix.
- **Rationale**: Selected table-only refresh still used the full metadata path and could read broad routine/trigger metadata before filtering.
- **Failure scenario**: `--refresh --snapshot-scope selected --include-tables dbo.Orders` reads broad catalog definitions without explicit broad-read acknowledgment.
- **Recommendation**: Require `--allow-broad-catalog-read` for every selected refresh until selected collection is truly least-collection.
- **Blocking**: Yes.
- **Resolution**: Tightened the guard so all selected refreshes require `--allow-broad-catalog-read` before connecting; added table-only, procedure, and job regression tests.

#### Lens 2 - Unsafe automation and user-edit loss

- **Score**: 4/5.
- **Rationale**: Upgrade refuses uninitialized targets and still conflicts local edits by default.
- **Failure scenario**: `upgrade --force` overwrites local harness-owned edits.
- **Recommendation**: Nonblocking: print overwritten paths or require dry-run review before `--force` in future.
- **Blocking**: No.
- **Resolution**: No immediate code change required for explicit force behavior.

#### Lens 3 - Roo workflow fit, script corners, and OS compatibility

- **Score**: 4/5 after final fix.
- **Rationale**: Phase gate is execute-approved, changed paths are inside allowed paths, doctor is read-only, and selected DB refresh wording now matches the broad-read guard.
- **Failure scenario**: Docs imply selected refresh is least-collection when it is output filtering.
- **Recommendation**: Keep docs precise about selected refresh requiring broad catalog acknowledgment.
- **Blocking**: No after final fix.
- **Resolution**: Updated DB docs, `/db` command, and DB workflow skill wording.
