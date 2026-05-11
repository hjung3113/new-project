# Phase Gate Rule

Use `.scratch/phase-state.schema.json` for external phase state. Implementation workflows must pass this gate before editable work starts.

## Required Behavior

- Default to `discuss` when no phase state is present.
- Treat `discuss` as read-only discovery.
- Treat `plan` as documentation, ADR, PRD, checklist, or issue-plan work only.
- Treat `execute` as implementation only after the state cites the approved `plan_id`, has `approved=true`, defines non-empty `allowed_paths`, and defines non-empty `verification`.
- Treat `done` as summary and verification only.
- `/feature`, `/bugfix`, `/etl`, `/db`, and `/ops` must check this gate before implementation.
- Every execute response must explicitly cite `phase=execute` and the approved `plan_id`.
- If requested work exceeds the approved plan, stop and return to `plan`.

## Mechanical Limits

Roo skills and rules are prompt-level controls. They can instruct, route, and checklist model behavior, but they do not by themselves lock files, reject commits, validate JSON, or prevent another actor from editing implementation files.

For mechanical enforcement, add external tooling such as:

- JSON Schema validation for `.scratch/phase-state.json`.
- A pre-commit hook that rejects implementation diffs unless `phase=execute`, `approved=true`, and `plan_id` is present.
- CI checks that compare changed paths against the approved `allowed_paths`.
- Repository permissions or branch protection for human approval.
