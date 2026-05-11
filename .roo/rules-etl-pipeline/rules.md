# ETL Pipeline Rules

- Treat every change as part of this canonical pipeline, in order: source -> parse -> normalize -> state -> merge -> buffer -> write -> observe.
- Do not rename, skip, or reorder pipeline stages without documenting why and updating tests for the new behavior.
- Keep pipeline records strongly typed. Avoid bare dictionaries for core records.
- Make ordering, lookahead, TTL, state transitions, merge keys, and merge semantics explicit.
- Preserve source traceability through the full pipeline.
- Preserve source traceability in written records and diagnostics: source file, source line or offset, source record id when available, equipment/job identifiers, and processing stage.
- Make writes idempotent, restart-safe, and replay-safe. Define duplicate handling and reprocess behavior before implementation.
- Add focused xUnit + FluentAssertions unit tests for pure source, parse, normalize, state, merge, and buffer behavior.
- Use `testcontainers-dotnet` with real MSSQL containers for writer, restart, idempotency, transaction, migration, and SQL behavior.
- Model backpressure explicitly for buffers and writers: bounded memory, flush size, flush interval, cancellation, retry boundaries, and failure visibility.
- Use bulk write paths for batch persistence: SqlBulkCopy into staging plus set-based MERGE/upsert.
- Row-by-row ETL writes are forbidden except for a documented, reviewer-approved exception with volume limits and rationale.
- Avoid hidden global state. Prefer dependency injection and explicit processing context.
