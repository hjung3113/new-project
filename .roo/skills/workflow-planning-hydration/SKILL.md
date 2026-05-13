---
name: workflow-planning-hydration
trigger: Use when applying this harness to an existing repository, when planning docs are missing/stale/placeholder-only, when ADR work needs project context first, or when the user asks to fill `.planning/` from an existing project.
description: Hydrates durable `.planning/` memory for an existing repository without overlapping with generic project init. It inventories the repo, fills codebase notes, creates or reconciles phase docs, updates state/roadmap pointers, and classifies stale planning artifacts before ADR or implementation work continues.
---

# Workflow: Planning Hydration

This workflow is the existing-repository adoption path. It is intentionally **not** named `project init` because it does not create a brand-new project. It hydrates and reconciles `.planning/` from a repository that already exists.

## Goal

Make the repository self-resumable before ADR, issue planning, or implementation work continues.

After this workflow, a fresh agent should be able to read:

1. `AGENTS.md`
2. `.planning/STATE.md`
3. `.planning/ROADMAP.md`
4. `.planning/codebase/**`
5. the active `.planning/phases/**` document set
6. `.scratch/phase-state.json`

…and understand the current project, current phase, next action, verification expectations, and stale artifact status without chat history.

## When to Use

Use this workflow when any of these are true:

- A user says this harness was applied to an existing project.
- A user asks for ADR work but `.planning/codebase/**` or `.planning/phases/**` is missing, stale, or placeholder-only.
- `.planning/STATE.md`, `.planning/ROADMAP.md`, or `.scratch/phase-state.json` points to template content or a previous project.
- Existing planning files are present but appear unrelated to the current repo.
- The task looks like `project init`, but the repository already has code, docs, ADRs, issues, or planning history.

Do not use this workflow for a truly empty repository where no project context exists yet. In that case, use the normal planning/ADR flow to discover the project first.

## Inputs to Read

Read in this order:

1. `AGENTS.md`
2. `README.md`
3. Build/test/package files, such as solution files, project files, package manifests, lockfiles, Docker/CI files, or scripts.
4. Source and test folder names.
5. Existing docs: `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/**`, `docs/adr/**`.
6. Existing `.planning/**` and `.scratch/phase-state.json`.
7. Recent issue/PR notes if available in `.scratch/**`.

## Output Files

Hydrate or create these files when they are missing or placeholder-only:

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/DECISIONS.md`
- `.planning/VERIFICATION.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STACK.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/CONVENTIONS.md`
- `.planning/codebase/TESTING.md`
- `.planning/codebase/INTEGRATIONS.md`
- `.planning/codebase/CONCERNS.md`
- `.planning/phases/<NN-current-phase>/NN-CONTEXT.md`
- `.planning/phases/<NN-current-phase>/NN-01-PLAN.md`
- `.planning/phases/<NN-current-phase>/NN-CHECKPOINTS.md`
- `.planning/phases/<NN-current-phase>/NN-REVIEW.md`
- `.planning/phases/<NN-current-phase>/NN-VERIFICATION.md`
- `.planning/phases/<NN-current-phase>/NN-01-SUMMARY.md`

Update `.scratch/phase-state.json` only when the user explicitly asks for harness/planning-control changes or when the current task is already scoped to phase-state repair. Keep it in `discuss` or `plan` unless implementation has been explicitly approved.

## Steps

### 1. Inventory the repository

Create a concise inventory:

- project name and repository path
- detected language/runtime/frameworks
- source directories
- test directories and test runner
- build, lint, and verification commands if discoverable
- docs and ADR locations
- external services, databases, queues, APIs, or deployment surfaces
- current `.planning/` and `.scratch/` state

Do not invent missing commands. Mark them as unknown when the repo does not prove them.

### 2. Detect planning state

Classify existing planning memory as one of:

- `absent`: files are missing
- `template-only`: files exist but still contain placeholders
- `stale`: files describe a previous project or old phase
- `partial`: some files are valid but required sections are missing
- `usable`: files describe the current project and can be updated incrementally

### 3. Hydrate codebase notes

Populate `.planning/codebase/**` from observed repository facts.

Minimum expectations:

- `ARCHITECTURE.md`: system overview, ownership boundaries, known flows
- `STACK.md`: runtime, frameworks, package/build/test tooling
- `STRUCTURE.md`: major directories and responsibilities
- `CONVENTIONS.md`: naming, testing, branching, doc, and phase conventions
- `TESTING.md`: known commands, test gaps, external dependencies
- `INTEGRATIONS.md`: databases, APIs, queues, files, auth, CI/CD
- `CONCERNS.md`: risks, unknowns, migration hazards, operational concerns

### 4. Hydrate phase docs

Ensure there is exactly one active phase folder for the current work.

Required pattern:

```text
.planning/phases/<NN-phase-slug>/
  NN-CONTEXT.md
  NN-01-PLAN.md
  NN-CHECKPOINTS.md
  NN-REVIEW.md
  NN-VERIFICATION.md
  NN-01-SUMMARY.md
```

For adoption work, prefer a phase name like:

```text
01-existing-project-planning-hydration
```

Do not overwrite valuable historical phase evidence. Move stale content to an archive candidate list unless the user explicitly requests deletion.

### 5. Reconcile stale artifacts

Create a reconciliation section in the active phase review or context with three buckets:

- `keep`: valid project memory
- `archive`: old but useful historical evidence
- `delete candidate`: template residue or unrelated previous-project content
- `needs-human`: ambiguous files that require confirmation

Never silently delete ambiguous planning files.

### 6. Sync state and roadmap

Update:

- `.planning/STATE.md`: current phase, checkpoint, blocker, next action, files of record
- `.planning/ROADMAP.md`: phase list and success criteria
- `.planning/DECISIONS.md`: decisions already in force
- `.planning/VERIFICATION.md`: known commands and evidence gaps
- `.scratch/phase-state.json`: only when explicitly in scope

### 7. Stop before implementation

This workflow is planning-only. It can prepare implementation plans, but it must not modify application behavior.

If implementation is needed, produce the next workflow route and required approval state.

## Adversarial Verification

Before finishing, challenge the result with these checks:

1. **Wrong-project check**: Do any `.planning/**` files still name a previous project, template-only project, or unrelated phase?
2. **Placeholder check**: Do required planning docs still contain `<name>`, empty success criteria, or generic template text where repository-specific facts are available?
3. **ADR bypass check**: Could `/adr` proceed without reading `.planning/codebase/**` and active phase docs?
4. **Phase bypass check**: Could `phase=execute` be accepted while active phase docs are missing, stale, or empty?
5. **Permission check**: Are implementation modes still prevented from editing `.planning/**`?
6. **Deletion safety check**: Were ambiguous legacy planning files preserved or marked `needs-human` instead of silently deleted?
7. **Idempotency check**: If this workflow runs again, will it converge without duplicating sections or recreating archived stale content?
8. **Verification honesty check**: Are missing commands marked unknown instead of invented?
9. **Resume check**: Can a new session follow `AGENTS.md -> STATE -> ROADMAP -> codebase -> active phase -> phase-state` and continue?

Record failed checks in the active phase review with owner and next action.

## Output Format

When reporting completion, include:

```text
phase: plan
planning_context: <absent|template-only|stale|partial|usable> -> <usable|needs-human>
active_phase: <path>
updated_files:
  - <path>
stale_artifacts:
  keep:
  archive:
  delete_candidate:
  needs_human:
next_step: <one concrete action>
```

## Routing

- Primary owner: `architect` or `docs-issues`.
- Route changes to `.roo/**`, `.roomodes`, `AGENTS.md`, or `CLAUDE.md` to `harness-maintainer`.
- Route application implementation to the narrowest implementation workflow only after phase-gate approval.

## Hard Rules

- Do not call this `project init` in user-facing instructions.
- Do not implement application code.
- Do not overwrite or delete historical planning artifacts without classification.
- Do not mark planning context usable while codebase notes or active phase docs are placeholder-only.
- Do not invent repository facts that were not observed.
