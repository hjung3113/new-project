# Phase 2 Context - DB Context Snapshot

## Goal

Add a cache-first, read-only MSSQL metadata snapshot workflow so Roo skills can reason from real database shape without repeatedly connecting to database environments.

## Scope

- Add `scripts/db_context_snapshot.py` as a fixed-query catalog snapshotter.
- Add focused Python tests for safety-critical behavior.
- Document snapshot usage, refresh commands, cache reuse, redaction limits, and SQL Agent job collection.
- Teach DB, ETL, review, and ops workflows to use `.db-context/` before making database-shape claims.
- Align the orchestrator result contract with the new `needs-db-context` workflow status.

## Constraints

- Default command path must be offline and cache-first.
- Refresh must be explicit.
- Review mode must not claim it can execute refresh commands because it has no Roo command permission.
- Generated DB context artifacts are sensitive and must be ignored by git by default.
- Live DB verification requires human-provided credentials and explicit refresh approval.
