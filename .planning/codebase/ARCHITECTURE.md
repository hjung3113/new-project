# ARCHITECTURE - Planning and Roo Control Plane

**Analysis date:** 2026-05-11  
**Updated:** 2026-05-13

## System Overview

```text
User request
  -> Roo slash command or mode selection
  -> .roo/rules-orchestrator/rules.md routing
  -> .roo/skills/workflow-*/SKILL.md sequence
  -> .planning/ durable state, roadmap, codebase notes, phase checkpoints
  -> .roo/rules/phase-gate.md live gate check
  -> .scratch/phase-state.json live gate pointer
  -> target-project edits only when the approved phase allows them
```

## Ownership Boundaries

| Area | Purpose | Owner |
| --- | --- | --- |
| `.planning/` | Durable project memory, phase plans, checkpoints, verification | Planning / harness work |
| `.planning/codebase/` | Current repository architecture, stack, structure, conventions, testing, integrations, and concerns | Planning / ADR work |
| `.planning/phases/` | Active and historical phase context, plan, checkpoints, review, verification, and summary | Planning / ADR / docs-issues work |
| `.scratch/phase-state*.json` | Live gate state and examples | Harness maintainer |
| `.roo/` | Roo rules, commands, workflow skills | Harness maintainer |
| `.roomodes` | Roo mode definitions and write scopes | Harness maintainer |
| `docs/agents/` | Local issue tracker, triage, and domain-doc conventions | Planning skills |
| Target app source | Application implementation in projects that adopt the harness | Implementation modes only after execute approval |

## Continuity Flow

Fresh sessions do not infer state from chat. They read:

1. `AGENTS.md`
2. `.planning/STATE.md`
3. `.planning/ROADMAP.md`
4. `.planning/codebase/ARCHITECTURE.md`, `STACK.md`, `STRUCTURE.md`, `CONVENTIONS.md`, `TESTING.md`, `INTEGRATIONS.md`, and `CONCERNS.md`
5. Active phase `*-CHECKPOINTS.md`
6. Active phase context, plan, review, verification, and summary docs
7. `.scratch/phase-state.json`

## Gate Flow

- `discuss`: read-only discovery.
- `plan`: planning documents, ADRs, PRDs, issue plans, and existing-repository planning hydration only.
- `execute`: approved implementation scope only; must cite `phase=execute` and the approved `plan_id`.
- `done`: summary, verification, and follow-up candidates only.

## Existing-Repository Adoption Flow

When this harness is applied to a repository that already has source, docs, ADRs, or planning artifacts, the workflow must not treat `.planning/codebase/**` or `.planning/phases/**` as optional template residue.

Required sequence:

1. Inventory the repository: README, build/test files, source folders, docs, ADRs, and existing planning artifacts.
2. Hydrate `.planning/codebase/**` from the real repository before using ADR or phase gate output as authority.
3. Hydrate or create an active `.planning/phases/**` folder tied to the current request.
4. Record or update ADR decisions.
5. Sync `.planning/STATE.md`, `.planning/ROADMAP.md`, active checkpoints, and `.scratch/phase-state.json`.
6. Reconcile stale template or previous-project planning artifacts as keep/archive/delete candidates.

If steps 2 or 3 are missing, the gate is incomplete and must return to `plan`.

## Design Constraint

The harness is prompt-level unless Phase 2 adds external checks. Roo instructions can route and checklist behavior, but they cannot mechanically block filesystem writes, commits, or path drift on their own.
