#!/usr/bin/env python3
"""Tests for harness distribution, upgrade, and contamination checks."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path, PurePosixPath

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import harness


class HarnessToolTests(unittest.TestCase):
    def test_init_installs_clean_project_state_without_live_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"

            result = harness.run(["init", "--target", str(target)])

            self.assertEqual(0, result)
            state = (target / ".planning/STATE.md").read_text(encoding="utf-8")
            phase_state = json.loads((target / ".scratch/phase-state.json").read_text(encoding="utf-8"))
            installed = json.loads((target / ".harness/installed-manifest.json").read_text(encoding="utf-8"))

            self.assertNotIn("DB context snapshot", state)
            self.assertNotIn("PR #", state)
            self.assertEqual("discuss", phase_state["phase"])
            self.assertFalse(phase_state["approved"])
            self.assertEqual(harness.HARNESS_VERSION, installed["version"])
            self.assertTrue((target / ".roo/skills/workflow-phase-gate/SKILL.md").exists())

    def test_init_refuses_to_overwrite_existing_project_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"
            state = target / ".planning/STATE.md"
            state.parent.mkdir(parents=True)
            state.write_text("existing project memory", encoding="utf-8")

            with self.assertRaisesRegex(SystemExit, "Refusing to overwrite"):
                harness.run(["init", "--target", str(target)])

            self.assertEqual("existing project memory", state.read_text(encoding="utf-8"))
            self.assertFalse((target / "AGENTS.md").exists())

    def test_init_dry_run_has_no_filesystem_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"

            result = harness.run(["init", "--target", str(target), "--dry-run"])

            self.assertEqual(0, result)
            self.assertFalse(target.exists())

    def test_manifest_destination_paths_cannot_escape_target(self) -> None:
        entry = harness.ManifestEntry(
            path=PurePosixPath("../outside.md"),
            source=PurePosixPath("README.md"),
            policy="harness-owned",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(SystemExit, "escapes target"):
                harness.destination_path(Path(tmpdir), entry)

    def test_write_copy_refuses_destination_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "source.txt"
            outside = root / "outside.txt"
            link = root / "target.txt"
            source.write_text("new", encoding="utf-8")
            outside.write_text("old", encoding="utf-8")
            link.symlink_to(outside)

            with self.assertRaisesRegex(SystemExit, "symlink"):
                harness.write_copy(source, link)

            self.assertEqual("old", outside.read_text(encoding="utf-8"))

    def test_write_copy_refuses_symlinked_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "source.txt"
            outside_dir = root / "outside"
            link_dir = root / "target/link"
            source.write_text("new", encoding="utf-8")
            outside_dir.mkdir()
            link_dir.parent.mkdir(parents=True)
            link_dir.symlink_to(outside_dir, target_is_directory=True)

            with self.assertRaisesRegex(SystemExit, "symlink"):
                harness.write_copy(source, link_dir / "nested/file.txt")

            self.assertFalse((outside_dir / "nested/file.txt").exists())

    def test_upgrade_preserves_project_owned_state_and_reports_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"
            harness.run(["init", "--target", str(target)])
            state = target / ".planning/STATE.md"
            state.write_text("real project state", encoding="utf-8")
            command = target / ".roo/commands/simple.md"
            command.write_text("local command edit", encoding="utf-8")

            result = harness.run(["upgrade", "--target", str(target)])

            self.assertEqual(1, result)
            self.assertEqual("real project state", state.read_text(encoding="utf-8"))
            self.assertEqual("local command edit", command.read_text(encoding="utf-8"))
            self.assertTrue((target / ".harness/conflicts/.roo/commands/simple.md.new").exists())

    def test_upgrade_without_install_state_conflicts_existing_harness_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"
            command = target / ".roo/commands/simple.md"
            command.parent.mkdir(parents=True)
            command.write_text("unknown local file", encoding="utf-8")

            result = harness.run(["upgrade", "--target", str(target)])

            self.assertEqual(1, result)
            self.assertEqual("unknown local file", command.read_text(encoding="utf-8"))
            self.assertTrue((target / ".harness/conflicts/.roo/commands/simple.md.new").exists())

    def test_upgrade_without_install_state_does_not_bootstrap_empty_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"
            target.mkdir()

            with self.assertRaisesRegex(SystemExit, "not initialized"):
                harness.run(["upgrade", "--target", str(target)])

            self.assertFalse((target / "AGENTS.md").exists())

    def test_installed_target_can_run_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"
            harness.run(["init", "--target", str(target)])

            completed = subprocess.run(
                ["python3", "scripts/harness.py", "check"],
                cwd=target,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual("", completed.stderr)
            self.assertEqual(0, completed.returncode)

    def test_check_rejects_contaminated_clean_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = {"version": harness.HARNESS_VERSION, "files": []}
            (root / "harness/skeleton/clean/.planning").mkdir(parents=True)
            (root / "harness").mkdir(exist_ok=True)
            (root / "harness/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "harness/skeleton/clean/.planning/STATE.md").write_text(
                "Current focus: DB context snapshot PR #12", encoding="utf-8"
            )

            with self.assertRaisesRegex(SystemExit, "contamination"):
                harness.check(root=root)

    def test_allowed_paths_use_exact_files_and_directory_prefixes(self) -> None:
        allowed = [".roo/", "README.md"]
        blocked = [".db-context/"]

        self.assertTrue(harness.path_allowed(".roo/skills/workflow-phase-gate/SKILL.md", allowed, blocked))
        self.assertTrue(harness.path_allowed("README.md", allowed, blocked))
        self.assertFalse(harness.path_allowed("README.md.bak", allowed, blocked))
        self.assertFalse(harness.path_allowed(".db-context/latest.json", allowed, blocked))

    def test_phase_state_semantics_require_auditable_auto_selected_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "phase-state.json"
            path.write_text(
                json.dumps(
                    {
                        "phase": "discuss",
                        "approved": False,
                        "automation_mode": "auto",
                        "auto_selected": ["too vague"],
                        "updated_at": "2026-05-14T00:00:00Z",
                        "updated_by": "test",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SystemExit, "auto_selected\\[0\\] must be an object"):
                harness.check_phase_state_semantics(path)


if __name__ == "__main__":
    unittest.main()
