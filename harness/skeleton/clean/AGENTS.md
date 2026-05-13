## Agent Skills

Project-local Roo skills live under `.roo/skills/`. Keep project-specific skills in the target repository instead of installing them globally.

## Planning State

Fresh sessions must start with `.planning/STATE.md`, then `.planning/ROADMAP.md`, then `.planning/codebase/**`, then the active phase checkpoint under `.planning/phases/` when one exists. Use `.scratch/phase-state.json` as the live phase gate only after reading durable planning docs.

If `.scratch/phase-state.json` is not `phase=execute` with `approved=true`, do not modify application code. Documentation, harness, and setup changes are allowed only when explicitly requested.

## File Ownership

- `.roo/**`, `.roomodes`, phase-state schema files, and `scripts/harness.py` are harness-owned.
- `.planning/**` and `.scratch/phase-state.json` are project-owned after initialization.
- `AGENTS.md` and `README.md` may contain managed harness guidance plus project-specific sections.

## Coding Conduct

Use the minimum code needed to solve the requested problem. Keep edits scoped to the request, match existing project patterns, and verify the result with a focused command whenever practical.
