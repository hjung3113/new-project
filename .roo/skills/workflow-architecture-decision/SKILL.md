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
   - When adopting this harness into an existing repository, inspect the actual repository structure, README, build/test files, and existing ADR/planning artifacts before writing or updating templates.
   - Use project vocabulary.
   - Stop if enough context is not available to name the actual decision, unless the requested work is `project init`; in that case, create or hydrate the missing planning context first.

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

6. Handle `project init` for existing repositories (when requested).
   - Detect whether `.planning/`, `.planning/codebase/`, `.planning/phases/`, ADR docs, or historical planning artifacts already exist before writing templates.
   - If `.planning/codebase/` is missing or placeholder-only, create or hydrate at least: `ARCHITECTURE.md`, `STACK.md`, `STRUCTURE.md`, `CONVENTIONS.md`, `TESTING.md`, `INTEGRATIONS.md`, and `CONCERNS.md` from the real repository.
   - If `.planning/phases/` is missing, stale, or unrelated to the current repo, create or hydrate an active phase folder with context, plan, checkpoints, review, verification, and summary placeholders tied to the current request.
   - Run planning hydration for existing projects so `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/codebase/**`, and active phase checkpoints include current repository metadata instead of placeholders.
   - Reconcile stale planning artifacts by classifying each legacy file as keep, archive, or delete candidate; keep an explicit follow-up list for uncertain items.
   - Keep ordering deterministic: inventory existing context -> hydrate missing/stale planning memory -> record or update ADR decisions -> sync active phase checkpoint -> cleanup/reconcile stale planning artifacts.
   - Preserve idempotency: repeated init runs should converge without duplicating sections or reintroducing stale template content.

## Routing

- Primary owner: architecture/ADR work.
- ADR and `project init` planning-memory work may read and update `.planning/codebase/**` and `.planning/phases/**` through `architect` or `docs-issues`.
- Route Roo, slash-command, AGENTS.md, CLAUDE.md, `.roo/**`, and `.roomodes` changes to `harness-maintainer`.
- Route follow-up implementation slices to `tdd-code`, `etl-pipeline`, or `db-migration` based on the affected boundary.
- Route review-only follow-up to `review`.

## Hard Rules

- Architect mode does not implement application code.
- Do not skip `.planning/codebase/**` or `.planning/phases/**` during ADR/project-init work because those folders are the durable design and phase memory.
- Do not adopt frameworks only to make diagrams cleaner.
- Do not turn this workflow into sample project or domain implementation.
