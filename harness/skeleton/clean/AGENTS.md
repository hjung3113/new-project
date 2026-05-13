## Agent Skills

Project-local Roo skills live under `.roo/skills/`. Keep project-specific skills in the target repository instead of installing them globally.

## Planning State

Fresh sessions must start with `.planning/STATE.md`, then `.planning/ROADMAP.md`, then `.planning/codebase/**`, then the active phase checkpoint under `.planning/phases/` when one exists. Use `.scratch/phase-state.json` as the live phase gate only after reading durable planning docs.

If `.scratch/phase-state.json` is not `phase=execute` with `approved=true`, do not modify application code. Documentation, harness, and setup changes are allowed only when explicitly requested.

Before creating or reshaping ROADMAP phases, phase folders, ADR decisions, or phase success criteria, run a `grill-me` style alignment pass: ask one question at a time, give the recommended answer and reason, inspect the repo instead of asking when the repo can answer, and record an alignment summary with confirmed facts, inferred facts, user preferences, recommended defaults, open questions, and blocked decisions. Do not turn unconfirmed preferences into phase commitments.

Every roadmap phase starts with its own `discuss` pass before `plan` or `execute`. Before finalizing ADR decisions or phase commitments, run an adversarial review with two relevant expert roles, three lenses each, and the mandatory lens of whether the questions are concrete enough for low-reasoning models. `--auto` may select recommended low-risk defaults and must record auditable `auto_selected` entries. `--chain` may continue through one phase's `discuss -> plan -> execute` only when `.scratch/phase-state.json` is verified or written with `phase=execute`, the same `plan_id`, `approved=true`, `automation_mode=chain`, durable pointers, allowed paths, verification, and review checks.

## File Ownership

- `.roo/**`, `.roomodes`, phase-state schema files, and `scripts/harness.py` are harness-owned.
- `.planning/**` and `.scratch/phase-state.json` are project-owned after initialization.
- `AGENTS.md` and `README.md` may contain managed harness guidance plus project-specific sections.

## Coding Conduct

Use the minimum code needed to solve the requested problem. Keep edits scoped to the request, match existing project patterns, and verify the result with a focused command whenever practical.
