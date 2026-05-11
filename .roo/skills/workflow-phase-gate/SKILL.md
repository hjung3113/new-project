---
name: workflow-phase-gate
trigger: Use before any implementation workflow, when the user asks to gate work through discuss, plan, execute, or done phases, or when a task references phase-state approval.
description: Runs the external phase gate for low-reasoning models: discuss is read-only discovery, plan is docs or issue-plan only, execute requires approved plan_id, approved allowed_paths, verification, and phase=execute, and done records verification.
---

# Workflow: Phase Gate

Use this workflow before implementation to prevent accidental work before the user or orchestrator has approved a plan.

State lives outside the prompt in `.scratch/phase-state.json` or another file that follows `.scratch/phase-state.schema.json`. Durable project memory lives under `.planning/`; the live state file is a gate pointer, not the source of planning context.

## Required State Check

Before doing any work:

1. Read `AGENTS.md`.
2. Read `.planning/STATE.md`.
3. Read `.planning/ROADMAP.md`.
4. Read the active phase checkpoint file named in `.planning/STATE.md`.
5. Read the phase state file if one exists.
6. Identify `phase`, `plan_id`, `approved`, `state_path`, `plan_path`, `checkpoint_path`, `current_checkpoint`, `allowed_paths`, and `verification`.
7. For `plan`, `execute`, and `done`, read `state_path`, `plan_path`, and `checkpoint_path` before classifying allowed work. If any pointer is missing or stale, treat the state as incomplete and return to `plan`.
8. If there is no state file, start in `discuss`.
9. Do only the work allowed by the current phase.

## Phase Rules

### discuss

Allowed:

- Read files.
- Search the codebase.
- Ask clarifying questions.
- Summarize current behavior, risks, and options.

Forbidden:

- Editing files.
- Creating issue plans.
- Running formatters, migrations, generators, or tests that write files.
- Starting implementation.

Output:

- Findings.
- Open questions.
- Recommended next phase.

Next step:

- If enough is known, ask to move to `plan`.
- If not enough is known, stay in `discuss` and ask the smallest blocking question.

### plan

Allowed:

- Write or update docs, PRDs, ADRs, checklists, or local issue-plan files.
- Define acceptance criteria.
- Define test strategy and verification commands.
- Define exact implementation scope and file ownership.

Forbidden:

- Changing application behavior.
- Editing source code, migrations, generated artifacts, or tests unless the user explicitly classifies the test file as planning documentation.
- Installing dependencies.
- Running code generators that alter implementation files.

Output:

- A concrete plan with `plan_id`.
- Scope, non-goals, touched paths, acceptance criteria, and verification.
- Approval request to enter `execute`.

Next step:

- Stop and ask for approval. Do not execute until state has `phase=execute`, the same `plan_id`, and `approved=true`.

### execute

Allowed:

- Implement only the approved plan.
- Add or update tests required by the plan.
- Run verification commands.
- Update execution notes that cite the approved plan.

Required:

- Every execute response must cite `phase=execute`.
- Every execute response must cite the approved `plan_id`.
- Confirm the requested edits are inside `allowed_paths`.
- Confirm `verification` is non-empty before editing.
- If implementation scope changes, stop and return to `plan`.

Forbidden:

- Implementing work not covered by the approved `plan_id`.
- Reusing stale approval from a different plan.
- Silently expanding scope.

Output:

- Changed paths.
- Verification evidence.
- Any scope deviations, or `none`.

Next step:

- If verification passes and the work is complete, move to `done`.
- If verification fails, stay in `execute` and fix only issues inside the approved plan.

### done

Allowed:

- Summarize results.
- Record final verification.
- Identify follow-up work as new discuss or plan candidates.

Forbidden:

- More implementation under the completed `plan_id`.

Output:

- Final changed paths.
- Rationale.
- Verification.
- Follow-up candidates, if any.

Next step:

- Start a new `discuss` phase for new work.

## Low-Reasoning Checklist

Use this checklist at the top of every response:

```text
phase: <discuss|plan|execute|done>
plan_id: <id or none>
approved: <true|false>
allowed_work: <read-only|docs-plan-only|implementation|summary-only>
next_step: <one concrete next action>
```

## Stop Conditions

- Stop before editing if `phase=discuss`.
- Stop before implementation if `phase=plan`.
- Stop before implementation if `phase=execute` but `approved` is not `true`.
- Stop before implementation if `phase=execute` but `plan_id` is missing.
- Stop before implementation if `phase=execute` but `allowed_paths` is empty.
- Stop before implementation if `phase=execute` but `verification` is empty.
- Stop if the requested change is outside the approved plan.
