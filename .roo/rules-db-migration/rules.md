# DB Migration Rules

- Use MSSQL-safe schema and query patterns.
- Use EF Core by default for normal data access and schema evolution unless the project has a documented different migration tool.
- Dapper is allowed only for explicit complex or performance-sensitive read-query exceptions. Do not use Dapper for write paths without documented reviewer approval.
- Use parameterized SQL for all dynamic values.
- String-concatenated SQL with dynamic values is forbidden.
- For ETL and high-volume writes, use SqlBulkCopy into staging then set-based MERGE/upsert.
- Use staging tables for bulk loads, validate staging constraints, and make MERGE keys and update semantics explicit.
- Review indexes for read patterns, join predicates, merge keys, foreign keys, uniqueness, retention, and reprocess paths.
- Define transaction boundaries before implementation: what is atomic, what can retry, and what is safe after partial failure.
- Test SQL, migrations, EF Core queries, Dapper queries, writers, restart safety, idempotency, and transaction behavior against real MSSQL containers using `testcontainers-dotnet`.
- Do not use in-memory providers, mocked repositories, SQLite, or unit-only tests as proof for MSSQL behavior.
- Define rollback or recovery behavior for risky data changes.
- Row-by-row ETL writes are forbidden except for a documented reviewer-approved exception with expected volume, failure handling, and follow-up plan.
