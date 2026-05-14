#!/usr/bin/env python3
"""Target-safe smoke tests for initialized Roo harness projects."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class TargetHarnessSmokeTests(unittest.TestCase):
    def test_harness_check_passes_in_target(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/harness.py", "check"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_phase_state_is_discuss_and_unapproved(self) -> None:
        state = json.loads(Path(".scratch/phase-state.json").read_text(encoding="utf-8"))

        self.assertEqual("discuss", state["phase"])
        self.assertFalse(state["approved"])

    def test_required_target_files_exist(self) -> None:
        for relative in (
            "AGENTS.md",
            "README.md",
            ".roo/commands/README.md",
            ".roo/skills/workflow-phase-gate/SKILL.md",
            ".planning/phases/00-planning-hydration/00-CHECKPOINTS.md",
            "scripts/harness.py",
        ):
            self.assertTrue(Path(relative).exists(), relative)


if __name__ == "__main__":
    unittest.main()
