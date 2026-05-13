---
name: workflow-architecture-decision
trigger: Use when the user asks for a design decision, ADR, boundary choice, tradeoff analysis, or invokes /adr.
description: Runs the architecture decision workflow for pipeline boundaries, state models, ADRs, and implementation plans. Use for design decisions or when the user invokes /adr.
---

# Workflow: Architecture Decision

## Steps

1. Gather context.
   - Read AGENTS.md, CONTEXT.md, docs/adr, relevant requirements, and current code.
   - Use project vocabulary.
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
   - Call out when future work needs xUnit coverage or MSSQL integration coverage.

5. Convert to implementation work.
   - Produce vertical slices or local issue files when requested.
   - Assign recommended modes for each slice.
   - Do not implement the slices in this workflow.

6. Handle `project init` for existing repositories (when requested).
   - Detect whether `.planning/`, ADR docs, or historical planning artifacts already exist before writing templates.
   - Run planning hydration for existing projects so `.planning/STATE.md`, `.planning/ROADMAP.md`, and active phase checkpoints include current repository metadata instead of placeholders.
   - Reconcile stale planning artifacts by classifying each legacy file as keep, archive, or delete candidate; keep an explicit follow-up list for uncertain items.
   - Keep ADR-first ordering deterministic: generate/update ADR decisions first, then hydrate planning docs, then cleanup/reconcile stale planning artifacts.
   - Preserve idempotency: repeated init runs should converge without duplicating sections or reintroducing stale template content.

## Routing

- Primary owner: architecture/ADR work.
- Route follow-up implementation slices to `tdd-code`, `etl-pipeline`, or `db-migration` based on the affected boundary.
- Route review-only follow-up to `review`.

## Hard Rules

- Architect mode does not implement code.
- Do not adopt frameworks only to make diagrams cleaner.
- Do not turn this workflow into sample project or domain implementation.
