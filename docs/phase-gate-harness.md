# Phase Gate Harness

This harness gives Roo agents a small external state machine for work that must move through discussion, planning, execution, and completion without skipping approval. Implementation commands in this template must check the phase gate before editable work starts.

## State File

Use `.scratch/phase-state.schema.json` to validate phase state. A typical live state file should be named `.scratch/phase-state.json`. See `.scratch/phase-state.example.json` for a complete example.

The live state file is a gate, not the full project memory. Fresh sessions must read `.planning/STATE.md` first, then `.planning/ROADMAP.md`, then the active phase checkpoint file. The live state must point back to durable docs with:

- `state_path`
- `plan_path`
- `checkpoint_path`
- `current_checkpoint`
- `next_action`

The four phases are:

| Phase | Allowed work | Next step |
| --- | --- | --- |
| `discuss` | Read-only discovery: inspect files, search, ask questions, summarize options | Move to `plan` when enough is known |
| `plan` | Docs, ADRs, PRDs, checklists, and issue-plan files only | Ask for approval to enter `execute` |
| `execute` | Implementation and verification for the approved plan only | Move to `done` after verification |
| `done` | Final summary, rationale, verification, and follow-up candidates | Start a new `discuss` for new work |

## Execute Gate

Execution is allowed only when all of these are true:

- `phase` is `execute`.
- `approved` is `true`.
- `plan_id` is present.
- `state_path`, `plan_path`, `checkpoint_path`, `current_checkpoint`, and `next_action` are present.
- `allowed_paths` is non-empty.
- `verification` is non-empty.
- The requested implementation is inside the approved plan.

Every execute response must cite both:

```text
phase=execute
plan_id=<approved plan id>
```

If the work no longer matches the approved plan, stop implementation and return to `plan`.

## What Roo Can Enforce

The current Roo harness can mechanically help by:

- Loading workflow instructions from `.roo/skills/workflow-phase-gate/SKILL.md`.
- Loading prompt rules from `.roo/rules/phase-gate.md` when included by the mode or operator.
- Making low-reasoning models follow a visible checklist.
- Requiring the agent to state the current phase, plan id, approval status, allowed work, and next step.
- Making phase violations reviewable in the transcript.

## What Roo Cannot Enforce Alone

Roo skills and rules are not a file-system lock or policy engine. By themselves, they cannot:

- Stop a model or human from editing files during `discuss`.
- Reject a commit when `phase` is not `execute`.
- Validate JSON state against the schema.
- Confirm that changed paths match the approved plan unless an external diff checker is added.
- Prove that approval came from the intended human or system.

For hard enforcement, add separate tooling: JSON Schema validation, pre-commit checks, CI diff checks against `allowed_paths`, branch protection, or repository permissions.

## Document-Centered Continuity

Use this restart order after any session reset:

1. `AGENTS.md`
2. `.planning/STATE.md`
3. `.planning/ROADMAP.md`
4. Active phase `*-CHECKPOINTS.md`
5. `.scratch/phase-state.json`
6. Active phase `*-CONTEXT.md`
7. Latest relevant `*-SUMMARY.md` and `*-VERIFICATION.md`

For `plan`, `execute`, and `done`, the phase-state schema requires enough pointers to resume from durable docs. If those pointers are missing, treat the state as incomplete and return to `plan`.

## Low-Reasoning Model Checklist

At the start of gated work, the agent should fill this in:

```text
phase: <discuss|plan|execute|done>
plan_id: <id or none>
approved: <true|false>
allowed_work: <read-only|docs-plan-only|implementation|summary-only>
next_step: <one concrete next action>
```

Then follow only the matching phase rules.
