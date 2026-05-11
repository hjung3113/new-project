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

## Routing

- Primary owner: architecture/ADR work.
- Route follow-up implementation slices to `tdd-code`, `etl-pipeline`, or `db-migration` based on the affected boundary.
- Route review-only follow-up to `review`.

## Hard Rules

- Architect mode does not implement code.
- Do not adopt frameworks only to make diagrams cleaner.
- Do not turn this workflow into sample project or domain implementation.
