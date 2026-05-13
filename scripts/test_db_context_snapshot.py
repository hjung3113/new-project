#!/usr/bin/env python3
"""Focused tests for the DB context snapshot helper."""

from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db_context_snapshot as snap


class DbContextSnapshotTests(unittest.TestCase):
    def test_offline_refresh_is_rejected_before_connecting(self) -> None:
        with mock.patch.object(snap, "connect", side_effect=AssertionError("must not connect")):
            with self.assertRaisesRegex(SystemExit, "--offline cannot be combined with --refresh"):
                snap.main(["--refresh", "--offline"])

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
