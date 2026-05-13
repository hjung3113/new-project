---
name: workflow-architecture-decision
trigger: Use when the user asks for a design decision, ADR, boundary choice, tradeoff analysis, or invokes /adr.
description: Runs the architecture decision workflow for pipeline boundaries, state models, ADRs, and implementation plans. Use for design decisions or when the user invokes /adr.
---

# Workflow: Architecture Decision

## Steps

1. Gather context.
   - Read `AGENTS.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/codebase/**`, the active `.planning/phases/**` document set, `CONTEXT.md`, `docs/adr/`, relevant requirements, and current code.
   - Treat `.planning/codebase/**` and `.planning/phases/**` as first-class ADR inputs, not optional extras.
   - When adopting this harness into an existing repository, inspect the actual repository structure, README, build/test files, and existing ADR/planning artifacts before writing or updating decisions.
   - Use project vocabulary.
   - If `.planning/codebase/**` or active `.planning/phases/**` is missing, stale, unrelated to the current repository, or placeholder-only, stop ADR work and run `workflow-planning-hydration` first.
   - Stop if enough context is not available to name the actual decision.

2. Frame the decision.
   - State the problem, constraints, non-goals, and affected workflows.
   - For ETL, include ordering, state, idempotency, persistence, and operations.
   - State what this workflow will not decide.

3. Compare options.
   - Present 2-4 realistic options with tradeoffs.
   - Recommend one option and say why it fits pipeline-first Clean Architecture.

4. Record the decision.
   - Write or update an ADR when the decision is durable.
   - Include consequences, ownership, and test strategy.
   - Update `.planning/DECISIONS.md` or the active phase context/checkpoint when the decision affects project state.
   - Update the matching `.planning/codebase/**` note when the decision changes architecture, stack, structure, conventions, testing, integrations, or known concerns.
   - Call out when future work needs xUnit coverage or MSSQL integration coverage.

5. Convert to implementation work.
   - Produce vertical slices or local issue files when requested.
   - Assign recommended modes for each slice.
   - Keep implementation slices linked from the active phase plan/checkpoint when they belong to the current phase.
   - Do not implement the slices in this workflow.

## Existing Repository Planning Context

Do not fold existing-repository planning hydration into this workflow. Use `workflow-planning-hydration` first, then return to ADR once planning context is usable.

ADR may proceed only when:

- `.planning/codebase/**` describes the current repository.
- `.planning/phases/**` has an active phase document set relevant to the current work.
- `.planning/STATE.md`, `.planning/ROADMAP.md`, and `.scratch/phase-state.json` do not point at unrelated template or previous-project artifacts.

## Routing

- Primary owner: architecture/ADR work.
- Route missing/stale existing-project planning context to `workflow-planning-hydration` before ADR.
- ADR planning-memory work may update `.planning/DECISIONS.md`, active phase docs, and matching `.planning/codebase/**` notes after hydration is complete.
- Route Roo, slash-command, AGENTS.md, CLAUDE.md, `.roo/**`, and `.roomodes` changes to `harness-maintainer`.
- Route follow-up implementation slices to `tdd-code`, `etl-pipeline`, or `db-migration` based on the affected boundary.
- Route review-only follow-up to `review`.

## Hard Rules

- Architect mode does not implement application code.
- Do not skip `.planning/codebase/**` or `.planning/phases/**` during ADR work because those folders are the durable design and phase memory.
- Do not use ADR as a substitute for `workflow-planning-hydration` when the repo planning memory is absent, stale, or placeholder-only.
- Do not adopt frameworks only to make diagrams cleaner.
- Do not turn this workflow into sample project or domain implementation.
