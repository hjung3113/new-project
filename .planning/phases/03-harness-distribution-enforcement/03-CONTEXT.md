# Phase 3 Context - Harness Distribution and Enforcement

## Problem

The harness development repository contains real planning history for building the harness. Target projects need a clean starting point that does not inherit completed phase records, PR references, or previous project state.

## Goals

- Separate harness-owned files from project-owned planning memory.
- Provide a clean skeleton for first-time target project initialization.
- Provide manifest-based upgrade that preserves project-owned state.
- Add a local check command that catches stale phase references, skeleton contamination, malformed JSON, command/mode drift, and changed paths outside `allowed_paths`.
- Update README before PR so adopters understand init, upgrade, check, and ownership boundaries.

## Non-Goals

- Do not implement a package manager installer.
- Do not hydrate a real target project's planning docs in this phase.
- Do not add an example ETL slice; that remains Phase 5.
