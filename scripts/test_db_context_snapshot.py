#!/usr/bin/env python3
"""Focused tests for the DB context snapshot helper."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db_context_snapshot as snap


class DbContextSnapshotTests(unittest.TestCase):
    def test_config_loading_uses_cli_json_env_file_then_environment_without_mutating_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            env_file = tmp / ".env"
            env_file.write_bytes(
                "\ufeff# comment\r\n"
                'DB_CONTEXT_MASTER_CONNECTION="env-file-master"\r\n'
                "DB_CONTEXT_PROCESS_CONNECTIONS='{\"env-file\":\"env-file-process\"}'\r\n"
                "DB_CONTEXT_SNAPSHOT_SCOPE=shape\r\n"
                "DB_CONTEXT_INCLUDE_TABLES=dbo.EnvFile\r\n"
                .encode("utf-8")
            )
            config_file = tmp / "db-context.config.json"
            config_file.write_text(
                json.dumps(
                    {
                        "master_connection": "json-master",
                        "process_connections": {"json-process": "json-process-connection"},
                        "snapshot_scope": "selected",
                        "include_tables": ["dbo.Json"],
                        "include_procedures": "dbo.JsonProc",
                        "include_jobs": ["Json Job"],
                    }
                ),
                encoding="utf-8",
            )
            inherited = {
                "DB_CONTEXT_MASTER_CONNECTION": "inherited-master",
                "DB_CONTEXT_PROCESS_CONNECTIONS": '{"inherited":"inherited-process"}',
                "DB_CONTEXT_INCLUDE_TABLES": "dbo.Inherited",
            }

            args = snap.parse_args(
                [
                    "--config",
                    str(config_file),
                    "--env-file",
                    str(env_file),
                    "--master-connection",
                    "cli-master",
                    "--process-connection",
                    "cli-process::cli-process-connection",
                    "--include-procedures",
                    "dbo.CliProc",
                ]
            )
            effective = snap.resolve_config(args, environ=inherited)

        self.assertEqual("cli-master", effective.master_connection)
        self.assertEqual([("cli-process", "cli-process-connection")], snap.parse_process_connections(effective.process_connection))
        self.assertEqual("selected", effective.snapshot_scope)
        self.assertEqual(["dbo.Json"], effective.include_tables)
        self.assertEqual(["dbo.CliProc"], effective.include_procedures)
        self.assertEqual(["Json Job"], effective.include_jobs)
        self.assertEqual("inherited-master", inherited["DB_CONTEXT_MASTER_CONNECTION"])
        self.assertNotIn("DB_CONTEXT_SNAPSHOT_SCOPE", inherited)

    def test_config_loading_understands_env_file_comments_crlf_quotes_and_bom(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_bytes(
                b"\xef\xbb\xbf# ignored\r\n"
                b"DB_CONTEXT_MASTER_CONNECTION='quoted master'\r\n"
                b'DB_CONTEXT_PROCESS_CONNECTIONS="process-a::quoted process"\r\n'
                b"DB_CONTEXT_INCLUDE_TABLES=dbo.Orders,dbo.Customers # inline comment\r\n"
            )

            args = snap.parse_args(["--env-file", str(env_file)])
            effective = snap.resolve_config(args, environ={})

        self.assertEqual("quoted master", effective.master_connection)
        self.assertEqual([("process-a", "quoted process")], snap.parse_process_connections(effective.process_connection))
        self.assertEqual(["dbo.Orders", "dbo.Customers"], effective.include_tables)

    def test_collect_all_process_details_environment_key_sets_reference_only_false(self) -> None:
        args = snap.parse_args([])

        effective = snap.resolve_config(args, environ={"DB_CONTEXT_COLLECT_ALL_PROCESS_DETAILS": "true"})

        self.assertFalse(effective.process_reference_only)

    def test_default_process_reference_only_remains_true(self) -> None:
        effective = snap.resolve_config(snap.parse_args([]), environ={})

        self.assertTrue(effective.process_reference_only)

    def test_default_cache_mode_does_not_require_config_or_connect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            cached = {
                "tool_version": snap.TOOL_VERSION,
                "generated_at_utc": "2026-05-14T00:00:00+00:00",
                "mode": "refresh",
                "model": {},
                "safety_notes": [],
            }
            (output_dir / snap.LATEST_JSON).write_text(json.dumps(cached), encoding="utf-8")

            with mock.patch.object(snap, "connect", side_effect=AssertionError("must not connect")):
                result = snap.main(["--output-dir", str(output_dir), "--format", "json"])

        self.assertEqual(0, result)

    def test_offline_selected_snapshot_filters_cached_report_without_connecting(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            report = {
                "tool_version": snap.TOOL_VERSION,
                "generated_at_utc": "2026-05-14T00:00:00+00:00",
                "mode": "refresh",
                "model": {},
                "safety_notes": [],
                "master_database": self.database(
                    "master",
                    "full",
                    modules={
                        "procedures": [
                            {"schema_name": "dbo", "object_name": "KeepProc", "type": "P"},
                            {"schema_name": "dbo", "object_name": "DropProc", "type": "P"},
                        ],
                        "functions": [],
                        "views": [],
                    },
                ),
                "process_databases": [],
                "agent_jobs": {
                    "steps": [{"job_name": "KeepJob"}, {"job_name": "DropJob"}],
                    "schedules": [{"job_name": "KeepJob"}, {"job_name": "DropJob"}],
                    "warnings": [],
                },
            }
            report["master_database"]["tables"].append({"schema_name": "dbo", "table_name": "Drop", "temporal_type_desc": "NON_TEMPORAL_TABLE"})
            report["master_database"]["columns"].append({"schema_name": "dbo", "table_name": "Drop", "column_id": 1, "column_name": "Id"})
            (output_dir / snap.LATEST_JSON).write_text(json.dumps(report), encoding="utf-8")

            args = snap.resolve_config(
                snap.parse_args(
                    [
                        "--offline",
                        "--output-dir",
                        str(output_dir),
                        "--snapshot-scope",
                        "selected",
                        "--include-tables",
                        "dbo.Orders",
                        "--include-procedures",
                        "dbo.KeepProc",
                        "--include-jobs",
                        "KeepJob",
                    ]
                ),
                environ={},
            )
            with mock.patch.object(snap, "connect", side_effect=AssertionError("must not connect")):
                selected = snap.load_cached_report(Path(args.output_dir), args=args)

        self.assertEqual("cache", selected["mode"])
        self.assertEqual("selected", selected["collection_options"]["snapshot_scope"])
        self.assertEqual(["Orders"], [row["table_name"] for row in selected["master_database"]["tables"]])
        self.assertEqual(["KeepProc"], [row["object_name"] for row in selected["master_database"]["modules"]["procedures"]])
        self.assertEqual(["KeepJob"], [row["job_name"] for row in selected["agent_jobs"]["steps"]])

    def test_selected_snapshot_filters_collected_metadata_and_records_selection_options(self) -> None:
        database = self.database(
            "reference",
            "selected",
            modules={
                "procedures": [
                    {"schema_name": "dbo", "object_name": "WantedProc", "type": "P"},
                    {"schema_name": "dbo", "object_name": "OtherProc", "type": "P"},
                ],
                "functions": [],
                "views": [],
            },
            triggers=[
                {"parent_schema": "dbo", "parent_name": "Orders", "trigger_name": "tr_Wanted"},
                {"parent_schema": "dbo", "parent_name": "Other", "trigger_name": "tr_Other"},
            ],
        )
        database["tables"].append({"schema_name": "dbo", "table_name": "Other", "temporal_type_desc": "NON_TEMPORAL_TABLE"})
        database["columns"].append({"schema_name": "dbo", "table_name": "Other", "column_id": 1, "column_name": "Id"})
        database["primary_keys"].append({"schema_name": "dbo", "table_name": "Other", "constraint_name": "PK_Other"})
        database["indexes"].append({"schema_name": "dbo", "table_name": "Orders", "index_name": "IX_Orders"})
        database["indexes"].append({"schema_name": "dbo", "table_name": "Other", "index_name": "IX_Other"})
        database["parameters"] = [
            {"schema_name": "dbo", "object_name": "WantedProc", "parameter_name": "@Id"},
            {"schema_name": "dbo", "object_name": "OtherProc", "parameter_name": "@Id"},
        ]
        database["dependencies"] = [
            {"referencing_schema": "dbo", "referencing_name": "WantedProc", "referenced_schema_name": "dbo", "referenced_entity_name": "Wanted"},
            {"referencing_schema": "dbo", "referencing_name": "OtherProc", "referenced_schema_name": "dbo", "referenced_entity_name": "Other"},
        ]
        args = argparse.Namespace(
            redact=True,
            max_definition_chars=300_000,
            snapshot_scope="selected",
            include_tables=["dbo.Orders"],
            include_procedures=["dbo.WantedProc"],
            include_jobs=["Wanted Job"],
        )

        selected = snap.apply_selection(database, snap.selection_options(args))
        jobs = snap.filter_agent_jobs(
            {
                "steps": [{"job_name": "Wanted Job"}, {"job_name": "Other Job"}],
                "schedules": [{"job_name": "Wanted Job"}, {"job_name": "Other Job"}],
                "warnings": [],
            },
            snap.selection_options(args),
        )

        self.assertEqual(["Orders"], [row["table_name"] for row in selected["tables"]])
        self.assertEqual(["Orders"], [row["table_name"] for row in selected["columns"]])
        self.assertEqual(["Orders"], [row["table_name"] for row in selected["primary_keys"]])
        self.assertEqual(["Orders"], [row["table_name"] for row in selected["indexes"]])
        self.assertEqual(["WantedProc"], [row["object_name"] for row in selected["modules"]["procedures"]])
        self.assertEqual(["WantedProc"], [row["object_name"] for row in selected["parameters"]])
        self.assertEqual(["WantedProc"], [row["referencing_name"] for row in selected["dependencies"]])
        self.assertEqual(["tr_Wanted"], [row["trigger_name"] for row in selected["triggers"]])
        self.assertEqual(["Wanted Job"], [row["job_name"] for row in jobs["steps"]])
        self.assertEqual(["Wanted Job"], [row["job_name"] for row in jobs["schedules"]])
        self.assertEqual("selected", selected["collection_options"]["snapshot_scope"])
        self.assertEqual(["dbo.Orders"], selected["collection_options"]["include_tables"])

    def test_offline_refresh_is_rejected_before_connecting(self) -> None:
        with mock.patch.object(snap, "connect", side_effect=AssertionError("must not connect")):
            with self.assertRaisesRegex(SystemExit, "--offline cannot be combined with --refresh"):
                snap.main(["--refresh", "--offline"])

    def test_selected_refresh_with_procedures_requires_broad_catalog_ack_before_connecting(self) -> None:
        with mock.patch.object(snap, "connect", side_effect=AssertionError("must not connect")):
            with self.assertRaisesRegex(SystemExit, "--allow-broad-catalog-read"):
                snap.main(
                    [
                        "--refresh",
                        "--master-connection",
                        "master",
                        "--process-connection",
                        "process",
                        "--snapshot-scope",
                        "selected",
                        "--include-procedures",
                        "dbo.LoadOrders",
                    ]
                )

    def test_selected_refresh_with_jobs_requires_broad_catalog_ack_before_connecting(self) -> None:
        with mock.patch.object(snap, "connect", side_effect=AssertionError("must not connect")):
            with self.assertRaisesRegex(SystemExit, "--allow-broad-catalog-read"):
                snap.main(
                    [
                        "--refresh",
                        "--master-connection",
                        "master",
                        "--snapshot-scope",
                        "selected",
                        "--include-jobs",
                        "Nightly ETL",
                    ]
                )

    def test_selected_refresh_with_tables_requires_broad_catalog_ack_before_connecting(self) -> None:
        with mock.patch.object(snap, "connect", side_effect=AssertionError("must not connect")):
            with self.assertRaisesRegex(SystemExit, "--allow-broad-catalog-read"):
                snap.main(
                    [
                        "--refresh",
                        "--master-connection",
                        "master",
                        "--process-connection",
                        "process",
                        "--snapshot-scope",
                        "selected",
                        "--include-tables",
                        "dbo.Orders",
                    ]
                )

    def test_shape_mode_comparison_ignores_full_only_objects(self) -> None:
        reference = self.database(
            "reference",
            "full",
            modules={"procedures": [{"schema_name": "dbo", "object_name": "Sync", "type": "P"}], "functions": [], "views": []},
            triggers=[{"parent_schema": "dbo", "parent_name": "Orders", "trigger_name": "tr_Orders"}],
        )
        shape_only = self.database("shape-only", "shape")

        comparison = snap.compare_process_databases([reference, shape_only])

        item = comparison["comparisons"][0]
        self.assertTrue(item["matches_reference_fingerprint"])
        self.assertEqual([], item["missing_objects_vs_reference"])
        self.assertEqual([], item["extra_objects_vs_reference"])

    def test_redaction_handles_quoted_sql_literals_and_multiword_values(self) -> None:
        text = "Password='abc def'; SET @ApiKey = N'super secret'; Bearer abc.def-123"

        redacted = snap.redact_text(text, enabled=True)

        self.assertNotIn("abc def", redacted)
        self.assertNotIn("super secret", redacted)
        self.assertNotIn("abc.def-123", redacted)
        self.assertIn("Password=<redacted>", redacted)
        self.assertIn("@ApiKey = <redacted>", redacted)
        self.assertIn("Bearer <redacted>", redacted)

    def test_agent_job_warning_redacts_exception_text(self) -> None:
        cursor = mock.Mock()
        cursor.execute.side_effect = RuntimeError("Login failed; Password='abc def';")

        result = snap.collect_agent_jobs(cursor, redact=True, max_definition_chars=300_000)

        self.assertNotIn("abc def", result["warnings"][0])
        self.assertIn("Password=<redacted>", result["warnings"][0])

    def test_default_artifacts_are_ignored_by_gitignore(self) -> None:
        gitignore = Path(".gitignore").read_text(encoding="utf-8")

        self.assertIn(".db-context/", gitignore)
        self.assertIn("routines.sql", gitignore)
        self.assertIn("jobs.md", gitignore)
        self.assertIn("db-context.config.json", gitignore)
        self.assertIn("*.db-context.config.json", gitignore)
        self.assertIn(".env", gitignore)
        self.assertIn(".env.*", gitignore)
        self.assertIn("!.env.example", gitignore)

    def test_refresh_reuses_cached_database_when_change_markers_match(self) -> None:
        args = argparse.Namespace(redact=True, max_definition_chars=300_000, login_timeout_seconds=15, lock_timeout_ms=5_000)
        cached_database = self.database("reference", "full")
        cached_database["identity"] = {"server_name": "server-a", "database_name": "reference"}
        cached_database["collection_options"] = snap.collection_options(args)
        cached_database["change_markers"] = [{"kind": "table", "schema_name": "dbo", "object_name": "Orders", "modify_date": "2026-05-13T00:00:00"}]
        cached_database["change_marker_fingerprint"] = snap.digest(cached_database["change_markers"])

        connection = mock.Mock()
        connection.cursor.return_value = mock.Mock()

        with (
            mock.patch.object(snap, "connect", return_value=connection),
            mock.patch.object(snap, "configure_readonly_session"),
            mock.patch.object(snap, "collect_database_identity", return_value={"server_name": "server-a", "database_name": "reference"}),
            mock.patch.object(snap, "collect_change_markers", return_value=cached_database["change_markers"]),
            mock.patch.object(snap, "collect_tables", side_effect=AssertionError("heavy collection should be skipped")),
        ):
            database = snap.collect_database(
                snap.DbTarget("process", "reference", "Driver={ODBC Driver 18 for SQL Server};Server=.;Database=reference;"),
                args,
                full=True,
                cached_database=cached_database,
            )

        self.assertTrue(database["reused_from_cache"])
        connection.close.assert_called_once()

    def test_refresh_does_not_reuse_cache_with_different_redaction_options(self) -> None:
        args = argparse.Namespace(redact=True, max_definition_chars=300_000, login_timeout_seconds=15, lock_timeout_ms=5_000)
        cached_database = self.database("reference", "full")
        cached_database["identity"] = {"server_name": "server-a", "database_name": "reference"}
        cached_database["collection_options"] = {"redact": False, "max_definition_chars": 300_000}
        markers = [{"kind": "table", "schema_name": "dbo", "object_name": "Orders", "modify_date": "2026-05-13T00:00:00"}]
        cached_database["change_marker_fingerprint"] = snap.digest(markers)

        self.assertFalse(
            snap.can_reuse_cached_database(
                cached_database,
                identity={"server_name": "server-a", "database_name": "reference"},
                collection_scope="full",
                change_markers=markers,
                options=snap.collection_options(args),
            )
        )

    def test_refresh_does_not_reuse_cache_with_different_server_identity(self) -> None:
        args = argparse.Namespace(redact=True, max_definition_chars=300_000, login_timeout_seconds=15, lock_timeout_ms=5_000)
        cached_database = self.database("reference", "full")
        cached_database["identity"] = {"server_name": "server-a", "database_name": "reference"}
        cached_database["collection_options"] = snap.collection_options(args)
        markers = [{"kind": "table", "schema_name": "dbo", "object_name": "Orders", "modify_date": "2026-05-13T00:00:00"}]
        cached_database["change_marker_fingerprint"] = snap.digest(markers)

        self.assertFalse(
            snap.can_reuse_cached_database(
                cached_database,
                identity={"server_name": "server-b", "database_name": "reference"},
                collection_scope="full",
                change_markers=markers,
                options=snap.collection_options(args),
            )
        )

    def test_split_artifacts_replaces_stale_jobs_file_when_jobs_not_collected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "jobs.md").write_text("stale job command", encoding="utf-8")

            snap.split_artifacts({"master_database": self.database("master", "full"), "process_databases": []}, output_dir)

            self.assertIn("SQL Agent jobs were not collected", (output_dir / "jobs.md").read_text(encoding="utf-8"))

    @staticmethod
    def database(
        label: str,
        collection_scope: str,
        *,
        modules: dict[str, list[dict[str, object]]] | None = None,
        triggers: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        database: dict[str, object] = {
            "label": label,
            "collection_scope": collection_scope,
            "identity": {"database_name": label},
            "tables": [{"schema_name": "dbo", "table_name": "Orders", "temporal_type_desc": "NON_TEMPORAL_TABLE"}],
            "columns": [
                {
                    "schema_name": "dbo",
                    "table_name": "Orders",
                    "column_id": 1,
                    "column_name": "Id",
                    "type_schema": "sys",
                    "type_name": "int",
                    "max_length": 4,
                    "precision": 10,
                    "scale": 0,
                    "is_nullable": False,
                    "is_identity": True,
                    "is_computed": False,
                    "computed_definition": None,
                    "default_definition": None,
                }
            ],
            "primary_keys": [{"schema_name": "dbo", "table_name": "Orders", "constraint_name": "PK_Orders", "key_ordinal": 1, "column_name": "Id"}],
            "foreign_keys": [],
            "indexes": [],
            "modules": modules or {"procedures": [], "functions": [], "views": []},
            "triggers": triggers or [],
            "user_defined_types": [],
            "sequences": [],
            "synonyms": [],
        }
        database["schema_fingerprint"] = snap.schema_fingerprint(database, scope="shape")
        return database


if __name__ == "__main__":
    unittest.main()
