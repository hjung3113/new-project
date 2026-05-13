#!/usr/bin/env python3
"""Cache-first, read-only MSSQL context snapshotter.

Model:
- one master database
- many process databases that should share the same schema shape

Default behavior is cache-first: without --refresh this script reads
.db-context/latest.json and never opens a database connection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

TOOL_VERSION = "0.1.0"
DEFAULT_OUTPUT_DIR = ".db-context"
LATEST_JSON = "latest.json"
LATEST_MD = "latest.md"

SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)(\b(?:password|pwd)\b\s*=\s*)(?:N?'(?:''|[^'])*'|\"[^\"]*\"|[^;\r\n]+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(\b(?:user\s+id|uid)\b\s*=\s*)(?:N?'(?:''|[^'])*'|\"[^\"]*\"|[^;\r\n]+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(@?\b(?:access[_-]?token|api[_-]?key|secret)\b\s*[:=]\s*)(?:N?'(?:''|[^'])*'|\"[^\"]*\"|[^;,\r\n\s]+)"), r"\1<redacted>"),
    (re.compile(r"(?i)\b(bearer)\s+[a-z0-9._~+/=-]+"), r"\1 <redacted>"),
)


@dataclass(frozen=True)
class DbTarget:
    role: str
    label: str
    connection_string: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def redact_text(value: Any, enabled: bool) -> Any:
    if not enabled or not isinstance(value, str):
        return value
    redacted = value
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def truncate_text(value: Any, max_chars: int) -> Any:
    if not isinstance(value, str) or max_chars == 0 or len(value) <= max_chars:
        return value
    return value[:max_chars] + f"\n/* <truncated: original length {len(value)} chars> */"


def clean_cell(value: Any, *, redact: bool, max_definition_chars: int) -> Any:
    return truncate_text(redact_text(value, redact), max_definition_chars)


def row_to_dict(row: Any, *, redact: bool, max_definition_chars: int) -> dict[str, Any]:
    return {
        column[0]: clean_cell(getattr(row, column[0]), redact=redact, max_definition_chars=max_definition_chars)
        for column in row.cursor_description
    }


def fetch_dicts(cursor: Any, sql: str, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    cursor.execute(sql)
    return [row_to_dict(row, redact=redact, max_definition_chars=max_definition_chars) for row in cursor.fetchall()]


def parse_labeled_connection(raw: str, default_label: str) -> tuple[str, str]:
    if "::" in raw:
        label, connection_string = raw.split("::", 1)
        label = label.strip()
        connection_string = connection_string.strip()
        if label and connection_string:
            return label, connection_string
    return default_label, raw.strip()


def parse_process_connections(cli_values: list[str] | None) -> list[tuple[str, str]]:
    values: list[str] = []
    if cli_values:
        values.extend(cli_values)

    env_value = os.getenv("DB_CONTEXT_PROCESS_CONNECTIONS")
    if env_value:
        try:
            decoded = json.loads(env_value)
        except json.JSONDecodeError:
            decoded = None

        if isinstance(decoded, dict):
            values.extend(f"{label}::{connection}" for label, connection in decoded.items())
        elif isinstance(decoded, list):
            values.extend(str(item) for item in decoded)
        else:
            values.extend(line.strip() for line in env_value.splitlines() if line.strip())

    result: list[tuple[str, str]] = []
    for index, raw in enumerate(values, start=1):
        label, connection = parse_labeled_connection(raw, f"process_{index}")
        if connection:
            result.append((label, connection))
    return result


def connect(connection_string: str, *, login_timeout_seconds: int) -> Any:
    try:
        import pyodbc  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pyodbc is required for --refresh. Install it with `python3 -m pip install pyodbc` "
            "and ensure a Microsoft ODBC Driver for SQL Server is installed."
        ) from exc

    return pyodbc.connect(connection_string, timeout=login_timeout_seconds, autocommit=True)


def configure_readonly_session(cursor: Any, *, lock_timeout_ms: int) -> None:
    cursor.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
    cursor.execute(f"SET LOCK_TIMEOUT {lock_timeout_ms};")


def collect_database_identity(cursor: Any) -> dict[str, Any]:
    cursor.execute(
        """
        SELECT
            DB_NAME() AS database_name,
            CAST(SERVERPROPERTY('ServerName') AS nvarchar(256)) AS server_name,
            CAST(SERVERPROPERTY('Edition') AS nvarchar(256)) AS edition,
            CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(64)) AS product_version;
        """
    )
    row = cursor.fetchone()
    return {column[0]: getattr(row, column[0]) for column in row.cursor_description}


def collect_change_markers(cursor: Any) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT 'table' AS object_kind, s.name AS schema_name, t.name AS object_name,
               t.object_id, t.modify_date
        FROM sys.tables AS t
        INNER JOIN sys.schemas AS s ON s.schema_id = t.schema_id
        WHERE t.is_ms_shipped = 0
        UNION ALL
        SELECT 'module' AS object_kind, s.name AS schema_name, o.name AS object_name,
               o.object_id, o.modify_date
        FROM sys.objects AS o
        INNER JOIN sys.schemas AS s ON s.schema_id = o.schema_id
        WHERE o.is_ms_shipped = 0 AND o.type IN ('P', 'FN', 'IF', 'TF', 'V')
        UNION ALL
        SELECT 'trigger' AS object_kind, COALESCE(OBJECT_SCHEMA_NAME(tr.parent_id), '') AS schema_name,
               tr.name AS object_name, tr.object_id, tr.modify_date
        FROM sys.triggers AS tr
        WHERE tr.is_ms_shipped = 0
        ORDER BY object_kind, schema_name, object_name;
    """, redact=False, max_definition_chars=0)


def collect_tables(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT s.name AS schema_name, t.name AS table_name, t.object_id,
               t.temporal_type_desc, t.create_date, t.modify_date,
               COALESCE(SUM(CASE WHEN p.index_id IN (0, 1) THEN p.rows ELSE 0 END), 0) AS approx_row_count
        FROM sys.tables AS t
        INNER JOIN sys.schemas AS s ON s.schema_id = t.schema_id
        LEFT JOIN sys.partitions AS p ON p.object_id = t.object_id
        WHERE t.is_ms_shipped = 0
        GROUP BY s.name, t.name, t.object_id, t.temporal_type_desc, t.create_date, t.modify_date
        ORDER BY s.name, t.name;
    """, redact=redact, max_definition_chars=max_definition_chars)


def collect_columns(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT s.name AS schema_name, t.name AS table_name, c.column_id, c.name AS column_name,
               ts.name AS type_schema, ty.name AS type_name,
               CASE WHEN ty.name IN ('nvarchar', 'nchar') AND c.max_length > 0 THEN c.max_length / 2 ELSE c.max_length END AS max_length,
               c.precision, c.scale, c.is_nullable, c.is_identity, c.is_computed,
               cc.definition AS computed_definition, dc.definition AS default_definition, c.collation_name
        FROM sys.tables AS t
        INNER JOIN sys.schemas AS s ON s.schema_id = t.schema_id
        INNER JOIN sys.columns AS c ON c.object_id = t.object_id
        INNER JOIN sys.types AS ty ON ty.user_type_id = c.user_type_id
        INNER JOIN sys.schemas AS ts ON ts.schema_id = ty.schema_id
        LEFT JOIN sys.computed_columns AS cc ON cc.object_id = c.object_id AND cc.column_id = c.column_id
        LEFT JOIN sys.default_constraints AS dc ON dc.object_id = c.default_object_id
        WHERE t.is_ms_shipped = 0
        ORDER BY s.name, t.name, c.column_id;
    """, redact=redact, max_definition_chars=max_definition_chars)


def collect_primary_keys(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT s.name AS schema_name, t.name AS table_name, kc.name AS constraint_name,
               ic.key_ordinal, c.name AS column_name
        FROM sys.key_constraints AS kc
        INNER JOIN sys.tables AS t ON t.object_id = kc.parent_object_id
        INNER JOIN sys.schemas AS s ON s.schema_id = t.schema_id
        INNER JOIN sys.index_columns AS ic ON ic.object_id = t.object_id AND ic.index_id = kc.unique_index_id
        INNER JOIN sys.columns AS c ON c.object_id = t.object_id AND c.column_id = ic.column_id
        WHERE kc.type = 'PK'
        ORDER BY s.name, t.name, kc.name, ic.key_ordinal;
    """, redact=redact, max_definition_chars=max_definition_chars)


def collect_foreign_keys(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT fk.name AS foreign_key_name,
               ps.name AS parent_schema, pt.name AS parent_table, pc.name AS parent_column,
               rs.name AS referenced_schema, rt.name AS referenced_table, rc.name AS referenced_column,
               fkc.constraint_column_id, fk.delete_referential_action_desc, fk.update_referential_action_desc,
               fk.is_disabled, fk.is_not_trusted
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc ON fkc.constraint_object_id = fk.object_id
        INNER JOIN sys.tables AS pt ON pt.object_id = fk.parent_object_id
        INNER JOIN sys.schemas AS ps ON ps.schema_id = pt.schema_id
        INNER JOIN sys.columns AS pc ON pc.object_id = pt.object_id AND pc.column_id = fkc.parent_column_id
        INNER JOIN sys.tables AS rt ON rt.object_id = fk.referenced_object_id
        INNER JOIN sys.schemas AS rs ON rs.schema_id = rt.schema_id
        INNER JOIN sys.columns AS rc ON rc.object_id = rt.object_id AND rc.column_id = fkc.referenced_column_id
        WHERE pt.is_ms_shipped = 0 AND rt.is_ms_shipped = 0
        ORDER BY ps.name, pt.name, fk.name, fkc.constraint_column_id;
    """, redact=redact, max_definition_chars=max_definition_chars)


def collect_indexes(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT s.name AS schema_name, t.name AS table_name, i.name AS index_name, i.index_id,
               i.type_desc, i.is_unique, i.is_primary_key, i.is_unique_constraint, i.has_filter,
               i.filter_definition, ic.key_ordinal, ic.is_included_column, ic.is_descending_key,
               c.name AS column_name
        FROM sys.indexes AS i
        INNER JOIN sys.tables AS t ON t.object_id = i.object_id
        INNER JOIN sys.schemas AS s ON s.schema_id = t.schema_id
        LEFT JOIN sys.index_columns AS ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
        LEFT JOIN sys.columns AS c ON c.object_id = i.object_id AND c.column_id = ic.column_id
        WHERE t.is_ms_shipped = 0 AND i.index_id > 0 AND i.is_hypothetical = 0
        ORDER BY s.name, t.name, i.index_id, ic.is_included_column, ic.key_ordinal, ic.index_column_id;
    """, redact=redact, max_definition_chars=max_definition_chars)


def module_flags(definition: Any) -> dict[str, bool]:
    text = definition if isinstance(definition, str) else ""
    lowered = text.lower()
    return {
        "uses_dynamic_sql": "sp_executesql" in lowered or "exec(" in lowered or "execute(" in lowered,
        "uses_cursor": " cursor" in lowered or "\ncursor" in lowered,
        "uses_merge": " merge " in f" {lowered} ",
        "uses_transaction": "begin tran" in lowered or "begin transaction" in lowered,
        "uses_try_catch": "begin try" in lowered and "begin catch" in lowered,
        "uses_temp_table": "#" in text,
        "uses_cross_database_reference": bool(re.search(r"\b\w+\.\w+\.\w+\b", text)),
    }


def collect_modules(cursor: Any, *, redact: bool, max_definition_chars: int) -> dict[str, list[dict[str, Any]]]:
    rows = fetch_dicts(cursor, """
        SELECT s.name AS schema_name, o.name AS object_name, o.type, o.type_desc,
               o.create_date, o.modify_date, m.uses_ansi_nulls, m.uses_quoted_identifier, m.definition
        FROM sys.objects AS o
        INNER JOIN sys.schemas AS s ON s.schema_id = o.schema_id
        LEFT JOIN sys.sql_modules AS m ON m.object_id = o.object_id
        WHERE o.is_ms_shipped = 0 AND o.type IN ('P', 'FN', 'IF', 'TF', 'V')
        ORDER BY s.name, o.type, o.name;
    """, redact=redact, max_definition_chars=max_definition_chars)
    grouped: dict[str, list[dict[str, Any]]] = {"procedures": [], "functions": [], "views": []}
    for row in rows:
        row["definition_hash"] = digest(row.get("definition"))
        row["risk_flags"] = module_flags(row.get("definition"))
        if row["type"] == "P":
            grouped["procedures"].append(row)
        elif row["type"] in {"FN", "IF", "TF"}:
            grouped["functions"].append(row)
        elif row["type"] == "V":
            grouped["views"].append(row)
    return grouped


def collect_parameters(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT s.name AS schema_name, o.name AS object_name, o.type, p.parameter_id,
               p.name AS parameter_name, ts.name AS type_schema, ty.name AS type_name,
               p.max_length, p.precision, p.scale, p.is_output, p.has_default_value,
               CONVERT(nvarchar(max), p.default_value) AS default_value
        FROM sys.objects AS o
        INNER JOIN sys.schemas AS s ON s.schema_id = o.schema_id
        INNER JOIN sys.parameters AS p ON p.object_id = o.object_id
        INNER JOIN sys.types AS ty ON ty.user_type_id = p.user_type_id
        INNER JOIN sys.schemas AS ts ON ts.schema_id = ty.schema_id
        WHERE o.is_ms_shipped = 0 AND o.type IN ('P', 'FN', 'IF', 'TF')
        ORDER BY s.name, o.name, p.parameter_id;
    """, redact=redact, max_definition_chars=max_definition_chars)


def collect_dependencies(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT OBJECT_SCHEMA_NAME(d.referencing_id) AS referencing_schema,
               OBJECT_NAME(d.referencing_id) AS referencing_name,
               o.type AS referencing_type,
               d.referenced_server_name, d.referenced_database_name,
               d.referenced_schema_name, d.referenced_entity_name, d.is_ambiguous
        FROM sys.sql_expression_dependencies AS d
        INNER JOIN sys.objects AS o ON o.object_id = d.referencing_id
        WHERE o.is_ms_shipped = 0
        ORDER BY referencing_schema, referencing_name, referenced_database_name, referenced_schema_name, referenced_entity_name;
    """, redact=redact, max_definition_chars=max_definition_chars)


def collect_triggers(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    rows = fetch_dicts(cursor, """
        SELECT tr.name AS trigger_name, tr.parent_class_desc,
               OBJECT_SCHEMA_NAME(tr.parent_id) AS parent_schema, OBJECT_NAME(tr.parent_id) AS parent_name,
               tr.is_disabled, tr.is_instead_of_trigger, m.definition
        FROM sys.triggers AS tr
        LEFT JOIN sys.sql_modules AS m ON m.object_id = tr.object_id
        WHERE tr.is_ms_shipped = 0
        ORDER BY tr.parent_class_desc, parent_schema, parent_name, tr.name;
    """, redact=redact, max_definition_chars=max_definition_chars)
    for row in rows:
        row["definition_hash"] = digest(row.get("definition"))
    return rows


def collect_user_defined_types(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT s.name AS schema_name, ty.name AS type_name, base_ty.name AS base_type_name,
               ty.max_length, ty.precision, ty.scale, ty.is_nullable, ty.is_table_type
        FROM sys.types AS ty
        INNER JOIN sys.schemas AS s ON s.schema_id = ty.schema_id
        LEFT JOIN sys.types AS base_ty ON base_ty.user_type_id = ty.system_type_id AND base_ty.user_type_id = base_ty.system_type_id
        WHERE ty.is_user_defined = 1 OR ty.is_table_type = 1
        ORDER BY s.name, ty.name;
    """, redact=redact, max_definition_chars=max_definition_chars)


def collect_sequences(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT s.name AS schema_name, seq.name AS sequence_name, ty.name AS type_name,
               seq.start_value, seq.increment, seq.minimum_value, seq.maximum_value,
               seq.is_cycling, seq.cache_size, seq.current_value
        FROM sys.sequences AS seq
        INNER JOIN sys.schemas AS s ON s.schema_id = seq.schema_id
        INNER JOIN sys.types AS ty ON ty.user_type_id = seq.user_type_id
        ORDER BY s.name, seq.name;
    """, redact=redact, max_definition_chars=max_definition_chars)


def collect_synonyms(cursor: Any, *, redact: bool, max_definition_chars: int) -> list[dict[str, Any]]:
    return fetch_dicts(cursor, """
        SELECT s.name AS schema_name, syn.name AS synonym_name, syn.base_object_name
        FROM sys.synonyms AS syn
        INNER JOIN sys.schemas AS s ON s.schema_id = syn.schema_id
        ORDER BY s.name, syn.name;
    """, redact=redact, max_definition_chars=max_definition_chars)


def collect_agent_jobs(cursor: Any, *, redact: bool, max_definition_chars: int) -> dict[str, Any]:
    try:
        steps = fetch_dicts(cursor, """
            SELECT j.name AS job_name, j.enabled AS job_enabled, j.description AS job_description,
                   j.date_created, j.date_modified, s.step_id, s.step_name, s.subsystem,
                   s.database_name, s.command, s.on_success_action, s.on_fail_action
            FROM msdb.dbo.sysjobs AS j
            LEFT JOIN msdb.dbo.sysjobsteps AS s ON s.job_id = j.job_id
            ORDER BY j.name, s.step_id;
        """, redact=redact, max_definition_chars=max_definition_chars)
        schedules = fetch_dicts(cursor, """
            SELECT j.name AS job_name, sch.name AS schedule_name, sch.enabled AS schedule_enabled,
                   sch.freq_type, sch.freq_interval, sch.freq_subday_type, sch.freq_subday_interval,
                   sch.active_start_date, sch.active_start_time
            FROM msdb.dbo.sysjobs AS j
            INNER JOIN msdb.dbo.sysjobschedules AS js ON js.job_id = j.job_id
            INNER JOIN msdb.dbo.sysschedules AS sch ON sch.schedule_id = js.schedule_id
            ORDER BY j.name, sch.name;
        """, redact=redact, max_definition_chars=max_definition_chars)
        return {"steps": steps, "schedules": schedules, "warnings": []}
    except Exception as exc:  # noqa: BLE001 - msdb access varies by environment.
        message = redact_text(str(exc), redact)
        return {"steps": [], "schedules": [], "warnings": [f"Could not read SQL Agent metadata from msdb: {type(exc).__name__}: {message}"]}


def can_reuse_cached_database(cached_database: dict[str, Any] | None, *, identity: dict[str, Any], collection_scope: str, change_markers: list[dict[str, Any]]) -> bool:
    if not cached_database:
        return False
    if cached_database.get("collection_scope") != collection_scope:
        return False
    if cached_database.get("identity", {}).get("database_name") != identity.get("database_name"):
        return False
    return cached_database.get("change_marker_fingerprint") == digest(change_markers)


def collect_database(target: DbTarget, args: argparse.Namespace, *, full: bool, cached_database: dict[str, Any] | None = None) -> dict[str, Any]:
    connection = connect(target.connection_string, login_timeout_seconds=args.login_timeout_seconds)
    try:
        cursor = connection.cursor()
        configure_readonly_session(cursor, lock_timeout_ms=args.lock_timeout_ms)
        identity = collect_database_identity(cursor)
        change_markers = collect_change_markers(cursor)
        collection_scope = "full" if full else "shape"
        if can_reuse_cached_database(cached_database, identity=identity, collection_scope=collection_scope, change_markers=change_markers):
            reused = dict(cached_database or {})
            reused["identity"] = identity
            reused["change_markers"] = change_markers
            reused["change_marker_fingerprint"] = digest(change_markers)
            reused["reused_from_cache"] = True
            return reused
        database: dict[str, Any] = {
            "role": target.role,
            "label": target.label,
            "identity": identity,
            "tables": collect_tables(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars),
            "columns": collect_columns(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars),
            "primary_keys": collect_primary_keys(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars),
            "foreign_keys": collect_foreign_keys(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars),
            "indexes": collect_indexes(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars),
            "modules": {"procedures": [], "functions": [], "views": []},
            "parameters": [],
            "dependencies": [],
            "triggers": [],
            "user_defined_types": [],
            "sequences": [],
            "synonyms": [],
            "collection_scope": collection_scope,
            "change_markers": change_markers,
            "change_marker_fingerprint": digest(change_markers),
            "reused_from_cache": False,
        }
        if full:
            database["modules"] = collect_modules(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars)
            database["parameters"] = collect_parameters(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars)
            database["dependencies"] = collect_dependencies(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars)
            database["triggers"] = collect_triggers(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars)
            database["user_defined_types"] = collect_user_defined_types(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars)
            database["sequences"] = collect_sequences(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars)
            database["synonyms"] = collect_synonyms(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars)
        database["shape_fingerprint"] = schema_fingerprint(database, scope="shape")
        database["schema_fingerprint"] = schema_fingerprint(database, scope="full" if full else "shape")
        return database
    finally:
        connection.close()


def collect_master_agent_jobs(master: DbTarget, args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(master.connection_string, login_timeout_seconds=args.login_timeout_seconds)
    try:
        cursor = connection.cursor()
        configure_readonly_session(cursor, lock_timeout_ms=args.lock_timeout_ms)
        return collect_agent_jobs(cursor, redact=args.redact, max_definition_chars=args.max_definition_chars)
    finally:
        connection.close()


def schema_fingerprint(database: dict[str, Any], *, scope: str = "full") -> str:
    comparable = {
        "tables": sorted(({"schema": r["schema_name"], "table": r["table_name"], "temporal_type": r["temporal_type_desc"]} for r in database["tables"]), key=lambda r: (r["schema"], r["table"])),
        "columns": sorted(({k: r.get(k) for k in ("schema_name", "table_name", "column_id", "column_name", "type_schema", "type_name", "max_length", "precision", "scale", "is_nullable", "is_identity", "is_computed", "computed_definition", "default_definition")} for r in database["columns"]), key=lambda r: (r["schema_name"], r["table_name"], r["column_id"])),
        "primary_keys": database["primary_keys"],
        "foreign_keys": database["foreign_keys"],
        "indexes": database["indexes"],
    }
    if scope == "full":
        comparable.update({
            "modules": {kind: [{"schema_name": r["schema_name"], "object_name": r["object_name"], "type": r["type"], "definition_hash": r.get("definition_hash") or digest(r.get("definition"))} for r in rows] for kind, rows in database.get("modules", {}).items()},
            "triggers": [{"trigger_name": r["trigger_name"], "parent_schema": r["parent_schema"], "parent_name": r["parent_name"], "definition_hash": r.get("definition_hash") or digest(r.get("definition"))} for r in database.get("triggers", [])],
            "user_defined_types": database.get("user_defined_types", []),
            "sequences": database.get("sequences", []),
            "synonyms": database.get("synonyms", []),
        })
    return digest(comparable)


def object_set(database: dict[str, Any], *, scope: str = "full") -> set[str]:
    objects: set[str] = set()
    for row in database["tables"]:
        objects.add(f"table:{row['schema_name']}.{row['table_name']}")
    if scope == "shape":
        return objects
    for kind, rows in database.get("modules", {}).items():
        for row in rows:
            objects.add(f"{kind}:{row['schema_name']}.{row['object_name']}")
    for row in database.get("triggers", []):
        objects.add(f"trigger:{row.get('parent_schema')}.{row.get('parent_name')}.{row['trigger_name']}")
    return objects


def compare_process_databases(process_databases: list[dict[str, Any]]) -> dict[str, Any]:
    if not process_databases:
        return {"reference_label": None, "comparisons": []}
    reference = process_databases[0]
    reference_objects = object_set(reference, scope="shape")
    reference_shape_fingerprint = reference.get("shape_fingerprint") or schema_fingerprint(reference, scope="shape")
    comparisons = []
    for database in process_databases[1:]:
        objects = object_set(database, scope="shape")
        shape_fingerprint = database.get("shape_fingerprint") or schema_fingerprint(database, scope="shape")
        comparisons.append({
            "label": database["label"],
            "database_name": database["identity"]["database_name"],
            "matches_reference_fingerprint": shape_fingerprint == reference_shape_fingerprint,
            "schema_fingerprint": database["schema_fingerprint"],
            "shape_fingerprint": shape_fingerprint,
            "missing_objects_vs_reference": sorted(reference_objects - objects),
            "extra_objects_vs_reference": sorted(objects - reference_objects),
        })
    return {
        "reference_label": reference["label"],
        "reference_database_name": reference["identity"]["database_name"],
        "reference_schema_fingerprint": reference["schema_fingerprint"],
        "reference_shape_fingerprint": reference_shape_fingerprint,
        "process_database_count": len(process_databases),
        "comparisons": comparisons,
    }


def summarize_database(database: dict[str, Any]) -> dict[str, Any]:
    modules = database.get("modules", {})
    return {
        "label": database["label"],
        "database_name": database["identity"]["database_name"],
        "collection_scope": database["collection_scope"],
        "reused_from_cache": database.get("reused_from_cache", False),
        "schema_fingerprint": database["schema_fingerprint"],
        "table_count": len(database["tables"]),
        "column_count": len(database["columns"]),
        "index_column_count": len(database["indexes"]),
        "foreign_key_column_count": len(database["foreign_keys"]),
        "procedure_count": len(modules.get("procedures", [])),
        "function_count": len(modules.get("functions", [])),
        "view_count": len(modules.get("views", [])),
        "trigger_count": len(database.get("triggers", [])),
    }


def try_load_cached_report(output_dir: Path) -> dict[str, Any] | None:
    path = output_dir / LATEST_JSON
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def cached_database_by_role_label(cached_report: dict[str, Any] | None, role: str, label: str) -> dict[str, Any] | None:
    if not cached_report:
        return None
    if role == "master":
        database = cached_report.get("master_database")
        if isinstance(database, dict) and database.get("label") == label:
            return database
        return None
    for database in cached_report.get("process_databases", []):
        if isinstance(database, dict) and database.get("label") == label:
            return database
    return None


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    if not args.master_connection:
        raise SystemExit("Missing master DB connection string. Use --master-connection or DB_CONTEXT_MASTER_CONNECTION.")
    process_connections = parse_process_connections(args.process_connection)
    if not process_connections:
        raise SystemExit("Missing process DB connection string. Use --process-connection or DB_CONTEXT_PROCESS_CONNECTIONS. Repeat for every process DB.")

    master_target = DbTarget("master", args.master_label, args.master_connection)
    process_targets = [DbTarget("process", label, connection) for label, connection in process_connections]
    cached_report = try_load_cached_report(Path(args.output_dir))

    master_database = collect_database(master_target, args, full=True, cached_database=cached_database_by_role_label(cached_report, "master", master_target.label))
    process_databases = [
        collect_database(
            target,
            args,
            full=(index == 0 or not args.process_reference_only),
            cached_database=cached_database_by_role_label(cached_report, "process", target.label),
        )
        for index, target in enumerate(process_targets)
    ]

    report: dict[str, Any] = {
        "tool_version": TOOL_VERSION,
        "generated_at_utc": utc_now(),
        "mode": "refresh",
        "model": {
            "master_database_count": 1,
            "process_database_count": len(process_databases),
            "process_database_policy": "many process DBs are expected to share the same schema shape; first process DB is the detailed reference unless --collect-all-process-details is used",
        },
        "safety_notes": [
            "This tool executes read-only catalog queries only.",
            "Default mode is cache-first and does not connect to DB unless --refresh is provided.",
            "It does not read application table rows.",
            "Stored procedure/function/view/trigger definitions and SQL Agent job commands may contain sensitive values; redaction is best-effort only.",
            "Use a database principal with read-only metadata permissions whenever possible.",
            ".db-context output is ignored by git by default and should not be committed unless explicitly reviewed.",
        ],
        "master_database": master_database,
        "process_databases": process_databases,
        "process_database_comparison": compare_process_databases(process_databases),
    }
    if args.include_agent_jobs:
        report["agent_jobs"] = collect_master_agent_jobs(master_target, args)
    report["summary"] = {
        "master": summarize_database(master_database),
        "process": [summarize_database(database) for database in process_databases],
        "reused_database_count": sum(1 for database in [master_database, *process_databases] if database.get("reused_from_cache")),
        "agent_job_step_rows": len(report.get("agent_jobs", {}).get("steps", [])),
        "agent_job_schedule_rows": len(report.get("agent_jobs", {}).get("schedules", [])),
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DB Context Snapshot", "",
        f"Generated: {report.get('generated_at_utc', '-')}",
        f"Tool version: {report.get('tool_version', '-')}",
        f"Mode: {report.get('mode', '-')}", "",
        "This file is an AI-readable summary. Use `latest.json` for complete structured metadata and SQL module definitions.", "",
        "## Database Model", "",
        f"- Master DB count: {report.get('model', {}).get('master_database_count', 1)}",
        f"- Process DB count: {report.get('model', {}).get('process_database_count', len(report.get('process_databases', [])))}",
        "- Process DB policy: many process DBs are expected, and they should share the same schema shape.", "",
    ]

    def add_db(title: str, database: dict[str, Any]) -> None:
        summary = summarize_database(database)
        lines.extend([
            f"## {title}: {summary['label']}", "",
            f"- Database: `{summary['database_name']}`",
            f"- Collection scope: `{summary['collection_scope']}`",
            f"- Schema fingerprint: `{summary['schema_fingerprint']}`", "",
            "| Kind | Count |", "| --- | ---: |",
            f"| Tables | {summary['table_count']} |",
            f"| Columns | {summary['column_count']} |",
            f"| Index column rows | {summary['index_column_count']} |",
            f"| Foreign key column rows | {summary['foreign_key_column_count']} |",
            f"| Stored procedures | {summary['procedure_count']} |",
            f"| Functions | {summary['function_count']} |",
            f"| Views | {summary['view_count']} |",
            f"| Triggers | {summary['trigger_count']} |", "",
        ])

    if "master_database" in report:
        add_db("Master DB", report["master_database"])
    for database in report.get("process_databases", []):
        add_db("Process DB", database)

    comparison = report.get("process_database_comparison", {})
    lines.extend(["## Process DB Drift Check", "", f"- Reference: `{comparison.get('reference_label')}` / `{comparison.get('reference_database_name')}`", f"- Reference fingerprint: `{comparison.get('reference_schema_fingerprint')}`", ""])
    comparisons = comparison.get("comparisons", [])
    if not comparisons:
        lines.append("Only one process DB was provided, so there is no cross-process drift comparison.")
    else:
        lines.extend(["| Process DB | Matches reference | Missing objects | Extra objects |", "| --- | --- | ---: | ---: |"])
        for item in comparisons:
            lines.append(f"| {item['label']} | {item['matches_reference_fingerprint']} | {len(item['missing_objects_vs_reference'])} | {len(item['extra_objects_vs_reference'])} |")
    lines.append("")

    if "agent_jobs" in report:
        jobs = report["agent_jobs"]
        lines.extend(["## SQL Agent Jobs", "", f"- Job step rows: {len(jobs.get('steps', []))}", f"- Schedule rows: {len(jobs.get('schedules', []))}", ""])
        for warning in jobs.get("warnings", []):
            lines.append(f"- Warning: {warning}")
        lines.append("")

    lines.extend(["## Safety Notes", ""])
    for note in report.get("safety_notes", []):
        lines.append(f"- {note}")
    lines.extend(["", "## Next Best Files For Agents", "", "- `latest.json`: complete structured metadata.", "- `latest.md`: human/AI summary.", "- `routines.sql`: SQL source for procedures, functions, and views extracted from `latest.json`.", "- `routines.index.json`: procedure/function/view metadata without requiring a full-text scan.", "- `jobs.md`: SQL Agent job summary when `--include-agent-jobs` was used."])
    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def append_routines(database: dict[str, Any], index: list[dict[str, Any]], sql_parts: list[str]) -> None:
    db_name = database.get("identity", {}).get("database_name")
    label = database.get("label")
    for kind, rows in database.get("modules", {}).items():
        for row in rows:
            qualified = f"{row['schema_name']}.{row['object_name']}"
            index.append({"database_label": label, "database_name": db_name, "kind": kind, "qualified_name": qualified, "type": row.get("type"), "type_desc": row.get("type_desc"), "definition_hash": row.get("definition_hash"), "risk_flags": row.get("risk_flags", {})})
            if row.get("definition"):
                sql_parts.append(f"-- database: {db_name}\n-- object: {qualified}\n{row['definition']}")


def render_jobs_markdown(agent_jobs: dict[str, Any]) -> str:
    lines = ["# SQL Agent Jobs", ""]
    for warning in agent_jobs.get("warnings", []):
        lines.append(f"- Warning: {warning}")
    if agent_jobs.get("warnings"):
        lines.append("")
    for row in agent_jobs.get("steps", []):
        lines.extend([f"## {row.get('job_name')}", "", f"- Enabled: {row.get('job_enabled')}", f"- Step: {row.get('step_id')} - {row.get('step_name')}", f"- Database: `{row.get('database_name')}`", f"- Subsystem: `{row.get('subsystem')}`", "", "```sql", str(row.get("command") or ""), "```", ""])
    return "\n".join(lines)


def split_artifacts(report: dict[str, Any], output_dir: Path) -> None:
    write_text(output_dir / LATEST_MD, render_markdown(report))
    routines_index: list[dict[str, Any]] = []
    routines_sql_parts: list[str] = []
    if "master_database" in report:
        append_routines(report["master_database"], routines_index, routines_sql_parts)
    for database in report.get("process_databases", []):
        append_routines(database, routines_index, routines_sql_parts)
    write_text(output_dir / "routines.index.json", json.dumps(routines_index, ensure_ascii=False, indent=2, default=str) + "\n")
    write_text(output_dir / "routines.sql", "\n\nGO\n\n".join(part for part in routines_sql_parts if part).rstrip() + "\n")
    if "agent_jobs" in report:
        write_text(output_dir / "jobs.md", render_jobs_markdown(report["agent_jobs"]))


def load_cached_report(output_dir: Path) -> dict[str, Any]:
    path = output_dir / LATEST_JSON
    if not path.exists():
        raise SystemExit(f"No cached DB context snapshot found at {path}. Run with --refresh after explicit user approval.")
    with path.open("r", encoding="utf-8") as handle:
        report = json.load(handle)
    report["mode"] = "cache"
    return report


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cache-first read-only MSSQL context snapshotter.")
    parser.add_argument("--refresh", action="store_true", help="Explicitly connect to DBs and refresh .db-context snapshots.")
    parser.add_argument("--offline", action="store_true", help="Require cached snapshot and fail instead of connecting. This is the default unless --refresh is set.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Snapshot output directory.")
    parser.add_argument("--master-connection", default=os.getenv("DB_CONTEXT_MASTER_CONNECTION"), help="Master DB ODBC connection string. Env: DB_CONTEXT_MASTER_CONNECTION")
    parser.add_argument("--master-label", default="master", help="Label for the master DB section.")
    parser.add_argument("--process-connection", action="append", help="Process DB ODBC connection string. Repeat for every process DB. Use `label::connection-string` to name one.")
    parser.add_argument("--collect-all-process-details", dest="process_reference_only", action="store_false", help="Collect full modules/triggers/types for every process DB. Default collects full detail only for the first process DB and shape fingerprints for the rest.")
    parser.add_argument("--include-agent-jobs", action="store_true", help="Read SQL Agent job metadata from msdb through the master connection.")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown", help="Console output format.")
    parser.add_argument("--max-definition-chars", type=int, default=300_000, help="Max characters to keep per SQL definition or job command. Use 0 for unlimited.")
    parser.add_argument("--no-redact", dest="redact", action="store_false", help="Disable best-effort secret redaction for definitions and job commands.")
    parser.add_argument("--login-timeout-seconds", type=int, default=15, help="ODBC login timeout.")
    parser.add_argument("--lock-timeout-ms", type=int, default=5_000, help="SQL Server lock timeout for catalog reads.")
    parser.set_defaults(redact=True, process_reference_only=True)
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    if args.refresh and args.offline:
        raise SystemExit("--offline cannot be combined with --refresh.")
    output_dir = Path(args.output_dir)
    if not args.refresh:
        report = load_cached_report(output_dir)
    else:
        report = build_report(args)
        output_dir.mkdir(parents=True, exist_ok=True)
        split_artifacts(report, output_dir)
        write_text(output_dir / LATEST_JSON, json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n")
    if args.format == "json":
        sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n")
    else:
        sys.stdout.write(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
