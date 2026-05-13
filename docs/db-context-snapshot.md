# DB Context Snapshot Design

This document defines the read-only database context snapshot used by Roo skills before they reason about MSSQL tables, stored procedures, functions, jobs, ETL writers, migrations, or restart-safety.

## Goal

The goal is to give agents an AI-readable view of the real database shape without letting routine analysis repeatedly connect to production-like databases. The tool is a context snapshotter, not a general SQL runner.

The database estate is modeled as two logical database roles.

First, there is exactly one master database. It contains global configuration, metadata, or process coordination information for the application estate.

Second, there are many process databases. Process databases are expected to share the same schema shape. The snapshotter therefore treats the first supplied process database as the detailed reference database by default and compares every additional process database against that reference using schema fingerprints and object drift checks.

## Default Behavior

The default behavior is cache-first and offline. If `.db-context/latest.json` exists, agents and local commands must read that file and must not connect to the database.

A database connection is allowed only when the user explicitly asks to refresh database context. The command for that path is:

```bash
python scripts/db_context_snapshot.py --refresh
```

If a task requires database context and no snapshot exists, the correct workflow result is `needs-db-context`, not a guessed answer and not an automatic database connection.

## Snapshot Files

The snapshot directory is `.db-context/`. It is ignored by git because schema, stored procedure text, job commands, server names, and object names may be sensitive.

The primary files are:

```text
.db-context/
  latest.json
  latest.md
  routines.index.json
  routines.sql
  jobs.md
```

`latest.json` is the source of truth for agents. It contains structured metadata for tables, columns, keys, indexes, routines, dependencies, triggers, user-defined types, sequences, synonyms, SQL Agent jobs, summary counts, and process database comparisons.

`latest.md` is an AI and human summary. It contains counts, fingerprints, drift status, and guidance about which files to read next.

`routines.index.json` is a compact index for stored procedures, functions, and views. It includes object names, definition hashes, and risk flags such as dynamic SQL, cursor use, MERGE use, transactions, TRY/CATCH, temp tables, and cross-database references.

`routines.sql` contains SQL definitions for procedures, functions, and views. JSON is better for searching and comparing, but SQL source is still required for accurate review of control flow, transaction boundaries, MERGE semantics, dynamic SQL, and error handling.

`jobs.md` contains SQL Agent job steps when `--include-agent-jobs` is used. SQL Agent metadata is read from `msdb` through the master connection.

## Inputs

Connection strings must not be committed. They are provided by environment variables or CLI arguments.

```bash
export DB_CONTEXT_MASTER_CONNECTION="Driver={ODBC Driver 18 for SQL Server};Server=...;Database=MasterDb;..."
export DB_CONTEXT_PROCESS_CONNECTIONS='{
  "process-a": "Driver={ODBC Driver 18 for SQL Server};Server=...;Database=ProcessA;...",
  "process-b": "Driver={ODBC Driver 18 for SQL Server};Server=...;Database=ProcessB;..."
}'
```

The CLI also accepts repeated process connections:

```bash
python scripts/db_context_snapshot.py \
  --refresh \
  --master-connection "$DB_CONTEXT_MASTER_CONNECTION" \
  --process-connection "process-a::$PROCESS_A_CONNECTION" \
  --process-connection "process-b::$PROCESS_B_CONNECTION"
```

## Process Database Policy

Process databases are many, not one. The default collection policy is designed for that shape.

The first process connection is the reference process database. The tool collects full metadata and routine definitions from it.

Every additional process database is collected in shape mode by default. Shape mode collects tables, columns, primary keys, foreign keys, and indexes so that the tool can compute a schema fingerprint and compare drift without duplicating every stored procedure body from every process database.

If a task needs full stored procedure and function definitions from every process database, use:

```bash
python scripts/db_context_snapshot.py --refresh --collect-all-process-details
```

A drift report is always produced when more than one process database is supplied. It records whether each process database matches the reference fingerprint and lists missing or extra objects by object kind.

## Read-only Boundaries

The snapshotter is intentionally not a query workbench. It executes fixed catalog queries only. It does not read application table rows and does not execute stored procedures.

Allowed sources include:

```text
sys.tables
sys.columns
sys.types
sys.indexes
sys.index_columns
sys.key_constraints
sys.foreign_keys
sys.foreign_key_columns
sys.objects
sys.sql_modules
sys.parameters
sys.sql_expression_dependencies
sys.triggers
sys.sequences
sys.synonyms
msdb.dbo.sysjobs
msdb.dbo.sysjobsteps
msdb.dbo.sysjobschedules
msdb.dbo.sysschedules
```

The tool sets `READ UNCOMMITTED` and a lock timeout before catalog reads. It should still be run with a read-only database principal whenever possible.

## Security and Redaction

The snapshot may still contain sensitive information. Stored procedure definitions and SQL Agent job commands sometimes include secrets, file paths, server names, linked server names, or business-sensitive object names.

The tool applies best-effort redaction for common password, token, key, and bearer-token patterns. Redaction is not a security boundary. Snapshot files should be treated as sensitive local artifacts.

The repository ignores:

```gitignore
.db-context/
*.db-context.json
*.db-context.md
```

Agents must not ask to commit `.db-context/` unless a human explicitly reviews and approves the contents.

## How Roo Skills Use The Snapshot

The database, ETL, review, and operations skills should consult `.db-context/` whenever a conclusion depends on real database shape.

The expected sequence is:

```text
1. Read .db-context/latest.json when DB shape, SP/function logic, SQL Agent jobs, writer behavior, migration risk, MERGE keys, idempotency, or restart-safety matters.
2. Use routines.index.json to locate relevant stored procedures, functions, and views.
3. Use routines.sql for exact SQL control-flow review.
4. Use jobs.md when SQL Agent schedules or job steps matter.
5. Return needs-db-context if the required snapshot is missing or insufficient.
6. Refresh only when the user explicitly asks for fresh DB context.
```

## Adversarial Review Findings and Mitigations

An adversarial reviewer should assume an agent may misuse this tool unless the design makes safe behavior the easiest path.

The first risk is accidental production database access. The mitigation is that the default command path is cache-first and never connects to the database unless `--refresh` is present.

The second risk is silent over-trust in one process database. The mitigation is that process databases are modeled as many databases. The tool computes fingerprints and drift checks for every supplied process database.

The third risk is leaking secrets through SQL module definitions or job commands. The mitigation is best-effort redaction, gitignore defaults, and documentation that snapshot files are sensitive and should not be committed.

The fourth risk is turning the tool into a general SQL runner. The mitigation is fixed catalog queries only. The tool does not accept arbitrary data queries or execute procedures.

The fifth risk is huge snapshots. The mitigation is reference-only process collection by default and `--max-definition-chars` truncation for long SQL definitions or job commands.

The sixth risk is stale data. The mitigation is explicit generated timestamps and a workflow rule: if the snapshot is stale or insufficient for the task, return `needs-db-context` instead of guessing.

## Implementation Plan

The implementation is intentionally small and separated into documentation, tooling, workflow integration, and verification.

First, add this design document so future agents know the expected behavior, threat model, and process database policy.

Second, add `scripts/db_context_snapshot.py`. It provides cache-first reads, explicit `--refresh`, one master database, many process databases, process fingerprint comparison, JSON and Markdown output, routine SQL extraction, SQL Agent job extraction, and best-effort redaction.

Third, add `.gitignore` entries for `.db-context/` and standalone DB context artifacts.

Fourth, update the DB, ETL, review, and ops workflow skills so they read `.db-context/` before drawing conclusions that depend on actual database shape. They must not refresh DB context unless the user explicitly requests it.

Fifth, verify the script without connecting to a database by running Python compilation and help/offline paths. Real database verification requires a human-approved refresh command and environment variables.
