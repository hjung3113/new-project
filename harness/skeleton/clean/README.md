# Roo Harness Project

This repository has been initialized with the reusable Roo harness.

## Start Here

1. Read `AGENTS.md`.
2. Read `.planning/STATE.md`.
3. Read `.planning/ROADMAP.md`.
4. Read `.scratch/phase-state.json`.

## Harness Commands

```bash
python3 scripts/harness.py check
```

The harness-owned files define Roo modes, rules, commands, and reusable workflows. Project-owned planning files describe this repository and should be hydrated from the actual project before implementation work starts.

Before ROADMAP phases, phase folders, ADR decisions, or phase success criteria are created, align with the user first. Ask one question at a time, include the recommended answer and reason, inspect the repository instead of asking when the repository can answer, and record an alignment summary with confirmed facts, inferred facts, user preferences, recommended defaults, open questions, and blocked decisions.

Every phase starts with its own `discuss` pass before `plan` or `execute`. Review phase and ADR drafts with two adversarial expert roles and three lenses each, including whether the questions are concrete enough for low-reasoning models. Use `--auto` only for recommended low-risk defaults with auditable `auto_selected` entries. Use `--chain` only for one reviewed phase after `.scratch/phase-state.json` is verified or written with `phase=execute`, matching `plan_id`, `approved=true`, `automation_mode=chain`, durable pointers, allowed paths, and verification.

To upgrade later, run the newer harness source against this project:

```bash
python3 /path/to/newer-harness/scripts/harness.py upgrade --target .
```
