# ARCHITECTURE - Planning and Roo Control Plane

**Analysis date:** 2026-05-11

## System Overview

```text
User request
  -> Roo slash command or mode selection
  -> .roo/rules-orchestrator/rules.md routing
  -> .roo/skills/workflow-*/SKILL.md sequence
  -> .roo/rules/phase-gate.md live gate check
  -> .planning/ durable state, roadmap, phase checkpoints
  -> target-project edits only when the approved phase allows them
```

## Ownership Boundaries

| Area | Purpose | Owner |
| --- | --- | --- |
| `.planning/` | Durable project memory, phase plans, checkpoints, verification | Planning / harness work |
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
4. Active phase `*-CHECKPOINTS.md`
5. `.scratch/phase-state.json`
6. Active phase context, summary, and verification docs

## Gate Flow

- `discuss`: read-only discovery.
- `plan`: planning documents, ADRs, PRDs, and issue plans only.
- `execute`: approved implementation scope only; must cite `phase=execute` and the approved `plan_id`.
- `done`: summary, verification, and follow-up candidates only.

## Design Constraint

The harness is prompt-level unless Phase 2 adds external checks. Roo instructions can route and checklist behavior, but they cannot mechanically block filesystem writes, commits, or path drift on their own.
