# Phase 4 Context - Harness Sync, Compatibility, and Doctor

## Problem

Remote issues #17, #18, and #19 identify gaps in the reusable Roo harness:

- #17: ADR-driven roadmap phase changes can leave `.planning/ROADMAP.md`, `.planning/STATE.md`, and `.scratch/phase-state.json` inconsistent.
- #18: DB context snapshot refresh is too Linux-oriented and too broad; Windows users need the same config and selection path as Linux/macOS users.
- #19: Harness users need a `doctor` function that diagnoses mismatches across planning docs, Roo commands/skills/rules, DB context settings, and execution assumptions before mutation.

Issue #16 is still open. It overlaps with command distribution and routing checks, but #17-#19 already cover the command/skill/doctor consistency needed for this slice. Docker-related work is explicitly out of scope.

## Phase-Local Discuss Summary

| Question | Answer |
| --- | --- |
| Who is blocked by this phase? | Maintainers and template consumers using ADR, DB snapshot, and harness check flows across macOS/Linux/Windows. |
| What is the smallest observable result? | `scripts/harness.py doctor` reports roadmap/state drift, command/mode drift, Roo workflow drift, DB snapshot config issues, and mutation guidance with severity/cause/impact/fix fields. |
| What must not change? | No Docker work, no app implementation, no package manager dependency, no database connection by default, no broad rewrite of Roo workflows. |
| Which files may change? | Harness scripts/tests, DB snapshot docs/tests, Roo command/skill docs, README, `.gitignore`, manifest, and active planning docs. |
| What proves completion? | Unit tests for harness and DB snapshot, Python compilation, `scripts/harness.py check`, `scripts/harness.py doctor`, `jq . .roomodes`, and docs/workflow drift checks. |
| Which answers came from repo evidence? | Current phase gate, allowed owners, scripts, manifest, command/skill layout, DB snapshot behavior, and gitignored DB artifacts were read from repo files. |

## Alignment Summary

### Confirmed Facts

- The repository is a Roo/Codex harness template, not an application implementation.
- `.planning/` is durable memory and `.scratch/phase-state.json` is a live gate pointer.
- The current live gate was `done` for Phase 3 before this phase began.
- Existing harness verification is Python `unittest`, `py_compile`, `scripts/harness.py check`, and `.roomodes` JSON parsing.
- DB context snapshot output is gitignored under `.db-context/`.
- The current DB snapshot refresh path reads connection strings from CLI arguments and environment variables, but not from `.env` or ignored JSON config.

### User Preferences

- Ignore docker-related issue content.
- Avoid step conflicts by reviewing after each major reinforcement and merging only after final review.
- Use independent workers for #17 and #18, while the main session owns #19 integration and PR preparation.

### Recommended Defaults Selected

- Treat Phase 4 as the home for these issues because the existing roadmap already reserved it for template consumer onboarding.
- Keep `doctor` read-only by default and make any patching a follow-up workflow with explicit diff-before-mutation review.
- Add DB context selection as catalog filters and output scope metadata, not arbitrary SQL.
- Use a gitignored JSON config plus `.env` loader to keep Windows, Linux, and macOS on the same Python code path.

### Open Questions

- None blocking.

### Issue #16 Managed-File Policy Decision

`AGENTS.md` and `README.md` will be treated as managed-block merge targets for harness upgrades: initial install creates the full files from the clean skeleton, and future upgrade support should refresh only explicitly marked harness-managed blocks while preserving target-repo edits outside those blocks.

This is a policy decision, not an implementation claim for this slice. Current `scripts/harness.py upgrade` behavior still treats manifest `managed` files as file-level conflict candidates. Full managed-block merge requires block markers, a merge algorithm, dry-run/diff reporting, rollback/conflict tests, and updated operator docs in the same future change.

Decision basis:

- Preserves target repo edits better than whole-file replacement or whole-file conflicts.
- Keeps Roo Code, Codex, and Claude instruction files compatible because each tool can keep local additions outside harness blocks.
- Supports low-reasoning agents by making harness-owned sections explicit and machine-checkable.
- Can be implemented with platform-neutral Python text processing and deterministic dry-run output.
- Aligns with the existing manifest distinction between `managed`, `harness-owned`, and `project-owned`.

Rejected alternatives:

- Whole-file protection for `AGENTS.md` and `README.md`: safer mechanically today, but it makes routine harness upgrades conflict with normal target-project customization.
- Unconditional whole-file overwrite on upgrade: unacceptable because it can erase project-specific instructions and onboarding text.

## Non-Goals

- Docker setup or container orchestration.
- New application code, package lockfiles, npm/dotnet dependencies, or CI integration.
- Automatic mutation by `doctor` without an explicit diff/review step.
- Arbitrary SQL execution or application table row reads.

## Design Invariants

- Roadmap/state sync is derived from `.planning/ROADMAP.md`; the script must not trust stale frontmatter counts when the roadmap disagrees.
- Phase counts, completed counts, and percent complete must update together.
- DB snapshot refresh remains opt-in through `--refresh`.
- Offline mode never connects to a database.
- Selected snapshot mode must be explicit in output metadata and summaries.
- Secret-bearing config files must stay ignored.
- Roo commands stay thin; detailed behavior belongs in workflow skills, docs, or scripts.
