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

To upgrade later, run the newer harness source against this project:

```bash
python3 /path/to/newer-harness/scripts/harness.py upgrade --target .
```
